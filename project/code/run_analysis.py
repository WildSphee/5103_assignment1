"""Reproduce the frozen national analysis, comparisons, and fixed-plan stresses."""
import argparse
from dataclasses import asdict, replace
from pathlib import Path
import hashlib
import json
import platform
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import pandas as pd
import highspy
from model import Parameters, build_instance, optimise, allocate, summarise, save_result, investments
from baselines import simple_rule, greedy_rule
from prepare_data import INPUTS, OUT


def cache_key(inst, budget, target, relaxation, fixed_zero, implementation=None):
    source = implementation or ''.join(hashlib.sha256(Path(__file__).with_name(p).read_bytes()).hexdigest() for p in ['model.py','prepare_data.py','baselines.py'])
    source += (INPUTS/'source_hashes.json').read_text()
    return hashlib.sha256((source + json.dumps([asdict(inst.p), budget, target, relaxation, fixed_zero], sort_keys=True)).encode()).hexdigest()


def solve(inst, name, budget=np.inf, target=None, relaxation=False, fixed_zero=None):
    key = cache_key(inst, budget, target, relaxation, fixed_zero)
    folder = OUT/'runs'/name
    if (folder/'metrics.json').exists() and (folder/'arrays.npz').exists():
        old = json.loads((folder/'metrics.json').read_text())
        compatible = json.loads(Path(__file__).with_name('cache_compatibility.json').read_text())['compatible_implementation_fingerprints']
        keys = [key] + [cache_key(inst,budget,target,relaxation,fixed_zero,implementation=v) for v in compatible]
        if old.get('cache_key') in keys:
            old.update(dict(np.load(folder/'arrays.npz')))
            print('CACHED',name,flush=True)
            return old
    print('SOLVE', name, 'budget', budget, 'target', target, flush=True)
    r = optimise(inst, budget, target, name, relaxation, fixed_zero)
    r['cache_key'] = key
    save_result(inst, r)
    if 'x' in r:
        np.savez_compressed(folder/'arrays.npz', **{k:v for k,v in r.items() if isinstance(v,np.ndarray)})
        print('RESULT',name,round(r['service_fraction']*100,3),'%',round(r['capital']),[(s['status'],round(s['seconds'],2),s['gap']) for s in r['stages']],flush=True)
    else:
        print('INFEASIBLE/NO INCUMBENT',name,r['stages'],flush=True)
    return r


def flat(r):
    out = {k:v for k,v in r.items() if np.isscalar(v) and k not in ['cache_key']}
    if 'stages' in r:
        for j, st in enumerate(r['stages'],1):
            out.update({f'pass{j}_{k}': v for k,v in st.items() if k in ['status','gap','bound','seconds']})
    return out


def target_solve(inst, fraction):
    """Try a constructive minimum-cost certificate before a harder target MILP.

    Every new AC point can add at most q service. Thus at least
    ceil((target-S0)/q) points are needed, even with perfect placement.
    Nonnegative opening/upgrade costs imply capex >= that count * point cost.
    A feasible plan attaining this cost proves minimum capex independently
    of branch-and-bound. If unattainable, use the general target MILP.
    """
    f0,_=allocate(inst,distance=False)
    target=fraction*inst.demand.sum()
    count=max(0,int(np.ceil((target-f0.sum()-1e-7)/inst.p.q)))
    bound=count*inst.p.ac_cost
    trial=solve(inst,f'target_{int(fraction*100)}_capacity_bound',budget=bound)
    if trial.get('feasible') and trial['served']>=target-1e-5:
        r=trial.copy();r['name']=f'target_{int(fraction*100)}'
        r['target_fraction']=fraction;r['target_kwh_day']=target
        r['minimum_capex_proof']='Feasible plan attains ceil((target-S0)/q)*c lower bound; no upgrade/opening premium'
        r['minimum_capex_bound']=bound;r['certified_target_capex']=True
        r['stages']=trial['stages']+[{'stage':'target_capex_lower_bound_certificate','status':'Optimal','objective':bound,'bound':bound,'gap':0.,'nodes':0,'seconds':0.}]
        save_result(inst,r)
        return r
    return solve(inst,f'target_{int(fraction*100)}',target=target)


def fixed_plan(inst, base, budget):
    x, d, y = base['x'], base['dc'], base['y']
    power = inst.p.ac_power*x + inst.p.dc_power*d
    available = inst.p.headroom + inst.p.upgrade_kw*y
    scale = np.minimum(1., np.divide(available, power, out=np.ones(inst.n), where=power>0))
    scale = np.minimum(scale, np.divide(inst.maximum, x+d, out=np.ones(inst.n), where=x+d>0))
    q = inst.q0 + scale*(inst.p.q*x + inst.p.qdc*d)
    f, _ = allocate(inst, q_override=q)
    cap = inst.p.ac_cost*x + inst.p.dc_cost*d + inst.p.fixed_cost*(x+d>0) + inst.p.upgrade_cost*y
    return {'fixed_served': float(f.sum()), 'fixed_fraction': float(f.sum()/inst.demand.sum()),
            'fixed_repriced_capital': float(cap.sum()), 'fixed_over_budget': bool(cap.sum()>budget+1e-5),
            'fixed_derated_sites': int((scale<1-1e-7).sum()),
            'fixed_construction_feasible': bool(np.all(scale>=1-1e-7) and cap.sum()<=budget+1e-5)}


def sensitivity_case(name,delta,p,base,budget):
    pp=replace(p,**delta,time_limit=25,mip_gap=.001)
    si=build_instance(pp)
    r=solve(si,name,budget=budget)
    params={'scenario':name,**asdict(pp)}
    if not r.get('feasible'):
        return flat(r),None,params
    fixed=fixed_plan(si,base,budget)
    zero,_=allocate(si,distance=False)
    row={**flat(r),**fixed,'no_build_served':float(zero.sum()),'reoptimised_minus_fixed_kwh':r['served']-fixed['fixed_served']}
    row['feasible_fixed_plan_regret_kwh']=max(0.,row['reoptimised_minus_fixed_kwh']) if fixed['fixed_construction_feasible'] else np.nan
    return row,(r['x']+r['dc'])>0,params


def finish_outputs(inst,base,budget):
    """Rank only certified scenario allocations; retain all-case frequency separately."""
    sensitivity=pd.read_csv(OUT/'sensitivity.csv')
    all_selected=[];certified=[]
    for row in sensitivity.itertuples():
        s=pd.read_csv(OUT/'runs'/row.name/'site_decisions.csv').set_index('car_park_no').reindex(inst.sites.car_park_no)
        chosen=(s.ac_additions.to_numpy()+s.dc_additions.to_numpy())>0
        all_selected.append(chosen)
        if row.certified_service and row.certified_cost:certified.append(chosen)
    assert certified,'No certified scenario set available for shortlist frequency'
    rob=inst.sites[['car_park_no','address','area_2019','imputed','night_parking']].copy()
    rob['selection_fraction']=np.mean(certified,axis=0)
    rob['scenario_count']=len(certified)
    rob['all_feasible_selection_fraction']=np.mean(all_selected,axis=0)
    rob['all_feasible_scenario_count']=len(all_selected)
    rob['base_additions']=base['x'];rob['base_upgrade']=base['y']
    rob['base_capex']=investments(inst,base['x'],base['dc'])[2]
    rob.sort_values(['selection_fraction','base_additions','car_park_no'],ascending=[False,False,True]).to_csv(OUT/'site_robustness.csv',index=False)
    shortlist=rob[rob.base_additions.gt(0)&~rob.imputed&rob.night_parking.eq('YES')].sort_values(['selection_fraction','base_additions'],ascending=False).head(5)
    replacement=[]
    for j,row in shortlist.iterrows():
        rr=solve(inst,f'remove_{row.car_park_no}',budget=budget,fixed_zero=[int(j)])
        replacement.append({'site_id':row.car_park_no,'base_additions':row.base_additions,'selection_fraction':row.selection_fraction,
                            'certified_scenario_count':len(certified),
                            'replacement_service_loss_kwh_day':base['served']-rr.get('served',np.nan),
                            'status':rr['stages'][0]['status'],'service_gap':rr['stages'][0]['gap']})
    pd.DataFrame(replacement).to_csv(OUT/'shortlist_replacement.csv',index=False)
    alternate=solve(build_instance(replace(inst.p,seed=29)), 'alternate_seed',budget=budget)
    repeat=solve(inst,'repeat_base',budget=budget)
    again=solve(inst,'repeat_current_2',budget=budget)
    overlap=lambda a,b: float(np.sum((a['x']>0)&(b['x']>0))/max(1,np.sum((a['x']>0)|(b['x']>0))))
    (OUT/'reproducibility.json').write_text(json.dumps({'repeat_service_difference':again['served']-repeat['served'],
       'repeat_identical_additions':bool(np.array_equal(again['x'],repeat['x'])),
       'alternate_seed_service_difference':alternate['served']-repeat['served'],
       'alternate_seed_site_jaccard':overlap(alternate,repeat),'repeat_site_jaccard':overlap(again,repeat),
       'frozen_base_vs_current_implementation_jaccard':overlap(base,repeat)},indent=2))


def main(mode='all',workers=3):
    OUT.mkdir(parents=True,exist_ok=True)
    p = Parameters()
    stock = pd.read_csv(INPUTS/'ev_stock_scenarios.csv').set_index('scenario').stock
    p = replace(p, stock=float(stock['2027_base']))
    inst = build_instance(p)
    pd.DataFrame({'demand_site':inst.sites.car_park_no.iloc[inst.ii].to_numpy(),
                  'supply_site':inst.sites.car_park_no.iloc[inst.jj].to_numpy(), 'distance_m':inst.distances}).to_csv(INPUTS/'arcs.csv',index=False)
    pd.DataFrame({'site_id':inst.sites.car_park_no,'weight':inst.demand/inst.demand.sum(),'hdb_evs':p.stock*p.hdb_share*inst.demand/inst.demand.sum(), 'demand_kwh_day':inst.demand}).to_csv(INPUTS/'demand.csv',index=False)
    f0, _ = allocate(inst)
    baseline = summarise(inst,np.zeros(inst.n),np.zeros(inst.n),f0,0,'no_build')
    save_result(inst,baseline)
    max_x = np.minimum(inst.maximum,np.floor((p.headroom+p.upgrade_kw)/p.ac_power+1e-8))
    maxflow,_=allocate(inst,max_x)
    maximum=float(maxflow.sum())
    target_rows=[]
    for target in [.8,.9,.95]:
        r=target_solve(inst,target)
        target_rows.append(flat(r))
        if target==.9:
            anchor=r
    pd.DataFrame(target_rows).to_csv(OUT/'service_targets.csv',index=False)
    if anchor.get('feasible') and anchor['capital']>0:
        budget=anchor['capital']; anchor_reason='Minimum-capex 90% service target (solver status/gap retained)'
    else:
        near=solve(inst,'target_near_maximum',target=max(baseline['served'],maximum*.995))
        budget=near['capital']; anchor_reason='90% is already met or infeasible; 99.5% of physical maximum instead'
    base=solve(inst,'base',budget=budget)
    if not base.get('feasible'):
        raise RuntimeError('No base investment incumbent')
    base['no_build_served']=baseline['served']
    base['incremental_served']=base['served']-baseline['served']
    info={'anchor_reason':anchor_reason,'budget':budget,'maximum_physical_service':maximum,
          'maximum_physical_fraction':maximum/inst.demand.sum(), 'no_build_served':baseline['served'],
          'no_build_fraction':baseline['service_fraction'],'base_served':base['served'],
          'incremental_served':base['incremental_served'], 'q_new_ac':p.q,'arcs':len(inst.ii)}
    (OUT/'analysis_summary.json').write_text(json.dumps(info,indent=2))
    if mode in ['all','core']:
        frontier=[flat(baseline)]
        for multiple in [.25,.5,.75,1.,1.25]:
            r=base if multiple==1 else solve(inst,f'frontier_{multiple:g}',budget=budget*multiple)
            row=flat(r);row['budget_multiple']=multiple;frontier.append(row)
        df=pd.DataFrame(frontier).sort_values('budget')
        df['incremental_kwh_day']=df.served-baseline['served']
        df['annual_infrastructure_cost_per_extra_kwh']=df.annual_cost/(365*df.incremental_kwh_day.replace(0,np.nan))
        df['marginal_capex_per_extra_annual_kwh']=df.capital.diff()/(365*df.served.diff())
        df.to_csv(OUT/'budget_frontier.csv',index=False)
        assert np.all(np.diff(df.served)>-max(1e-3,inst.demand.sum()*p.mip_gap)), 'Nonmonotone frontier beyond solver tolerance'
        comparisons=[flat(baseline),flat(base)]
        for kind in ['equal','proportional','greedy']:
            if kind=='greedy':
                print('GREEDY exact reassignment starting',flush=True)
                r,trace=greedy_rule(inst,budget)
                pd.DataFrame(trace).to_csv(OUT/'greedy_steps.csv',index=False)
            else:
                r=simple_rule(inst,budget,kind)
            save_result(inst,r)
            comparisons.append(flat(r))
            print('COMPARISON',kind,r['capital'],r['service_fraction'],flush=True)
            matched=solve(inst,f'matched_{kind}',budget=r['capital'])
            comparisons.append(flat(matched))
        pd.DataFrame(comparisons).to_csv(OUT/'baseline_comparison.csv',index=False)
        relaxation=solve(inst,'lp_relaxation',budget=budget,relaxation=True)
        (OUT/'lp_bound.json').write_text(json.dumps({'lp_service_upper_bound':relaxation['served'],
            'integer_service':base['served'], 'absolute_bound_gap_kwh_day':relaxation['served']-base['served']},indent=2))
    if mode in ['all','sensitivity']:
        changes={
            'stock_current_2026':{'stock':stock['current_2026']},
            'stock_2027_low':{'stock':stock['2027_low']},'stock_2027_high':{'stock':stock['2027_high']},
            'outlook_2030_low':{'stock':stock['2030_low']},'outlook_2030_base':{'stock':stock['2030_base']},'outlook_2030_high':{'stock':stock['2030_high']},
            'hdb_share_30':{'hdb_share':.3},'hdb_share_55':{'hdb_share':.55},
            'dependence_60':{'dependence':.6},'dependence_100':{'dependence':1.},
            'mileage_12000':{'annual_km':12000},'mileage_20000':{'annual_km':20000},
            'intensity_014':{'intensity':.14},'intensity_020':{'intensity':.2},
            'efficiency_085':{'efficiency':.85},'efficiency_095':{'efficiency':.95},
            'unknown_no_build':{'unknown_no_build':True},'imputed_half':{'impute_factor':.5},'imputed_150':{'impute_factor':1.5},
            'housing_2025':{'weights':'housing_2025'},'population_2025':{'weights':'population_2025'},
            'housing_2026':{'weights':'housing_2026'},'population_2026':{'weights':'population_2026'},
            'broad_supply':{'matching':'broad'},'sum_port_power':{'power_bound':'upper'},
            'hours_4':{'hours':4},'hours_8':{'hours':8},
            'availability_90':{'availability':.9},'availability_99':{'availability':.99},
            'mean_power_70':{'power_factor':.7},'mean_power_100':{'power_factor':1.},
            'radius_250':{'radius':250},'radius_800':{'radius':800},'self_site_only':{'radius':0},
            'path_inflation_140':{'path_inflation':1.4},
            'capex_4500':{'ac_cost':4500},'capex_10000':{'ac_cost':10000},
            'headroom_148':{'headroom':14.8},'headroom_888':{'headroom':88.8},
            'upgrade_free':{'upgrade_cost':0},'upgrade_250k':{'upgrade_cost':250000},
            'lifetime_8':{'lifetime':8},'lifetime_12':{'lifetime':12},
            'discount_03':{'discount':.03},'discount_08':{'discount':.08},
            'lot_share_05':{'lot_share':.05},'lot_share_15':{'lot_share':.15},
            'deduplicated_bays':{'deduplicate_bays':True},
            'ac_dc_extension':{'dc_enabled':True},
            'joint_low':{'stock':stock['2027_low'],'ac_cost':4500,'hours':8},
            'joint_high':{'stock':stock['2027_high'],'hdb_share':.55,'ac_cost':10000,'headroom':14.8,'upgrade_cost':250000},
            'joint_access':{'radius':0,'unknown_no_build':True},
        }
        rows=[];selected=[]
        params=[]
        with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
            futures=[pool.submit(sensitivity_case,name,delta,p,base,budget) for name,delta in changes.items()]
            for future in as_completed(futures):
                row,selection,parameter=future.result()
                rows.append(row);params.append(parameter)
                if selection is not None:selected.append(selection)
                pd.DataFrame(rows).to_csv(OUT/'sensitivity.csv',index=False)
        order={name:k for k,name in enumerate(changes)}
        rows.sort(key=lambda row:order[row['name']]);params.sort(key=lambda row:order[row['scenario']])
        pd.DataFrame(rows).to_csv(OUT/'sensitivity.csv',index=False)
        pd.DataFrame(params).to_csv(OUT/'scenario_parameters.csv',index=False)
    if mode in ['all','sensitivity','finalize']:
        finish_outputs(inst,base,budget)
    manifest={'executed_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'python':platform.python_version(),
              'highs_version':highspy.Highs().version(),'base_parameters':asdict(p),'mode':mode,
              'solver_threads':1,'sensitivity_worker_processes':workers,'stock_paths':'assumed, not fitted','monetary_basis':'2026 scenario SGD excluding GST; constant real costs',
              'code_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(__file__).parent.glob('*.py')}}
    (OUT/'run_manifest.json').write_text(json.dumps(manifest,indent=2))
    print('COMPLETE',mode,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['all','core','sensitivity','finalize'],default='all')
    parser.add_argument('--workers',type=int,default=3)
    args=parser.parse_args();main(args.mode,args.workers)
