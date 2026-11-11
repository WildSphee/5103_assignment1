"""Independent release checks against saved flows, investments, sources and Office files."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd
from prepare_data import ROOT, INPUTS, OUT


def main(office=False):
    checks=[]
    def check(name,condition,detail):
        checks.append({'check':name,'status':'PASS' if bool(condition) else 'FAIL','evidence':str(detail)})
        if not condition:print('FAIL',name,detail,flush=True)
    for item in json.loads((INPUTS/'source_hashes.json').read_text()):
        actual=hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()
        check('Source hash: '+item['path'],actual==item['sha256'],actual)
    sites=pd.read_csv(INPUTS/'sites.csv')
    cp=pd.read_csv(INPUTS/'hdb_charger_crosswalk.csv')
    raw=cp.groupby('EV Charger Registration Code').agg(count=('evCpId','size'),stated=('No. of Charging Outlets','first'))
    check('Unique source IDs',cp.evCpId.is_unique and sites.car_park_no.is_unique,f'{len(cp)} points; {len(sites)} sites')
    check('Outlet counting',raw['count'].equals(raw.stated) and raw.stated.sum()==len(cp),f'{len(raw)} registrations; {raw.stated.sum()} deduplicated outlets')
    check('Missing-capacity retention',len(sites)==2273 and sites.imputed.sum()==278,f'{sites.imputed.sum()} imputed; {sites.total_lots.sum()} observed lots')
    strict=cp[cp.match_status.eq('address_supported')]
    check('Base assignment evidence',strict.site_id.notna().all() and strict.match_distance_m.le(150.00001).all(),f'{len(strict)} points; max {strict.match_distance_m.max():.3f} m')
    check('Registration consistency',strict.groupby('EV Charger Registration Code').site_id.nunique().max()==1,'Each assigned registration belongs to at most one site')
    existing=pd.read_csv(INPUTS/'existing_supply.csv')
    check('Power bounds',existing.strict_kw_lower.le(existing.strict_kw_upper+1e-8).all(),'Maximum-port bound never exceeds sum-port bound')
    demand=pd.read_csv(INPUTS/'demand.csv')
    check('Normalised demand weights',abs(demand.weight.sum()-1)<1e-10,demand.weight.sum())
    errors=[];count=0;limited=[]
    for folder in sorted((OUT/'runs').iterdir()):
        if not (folder/'metrics.json').exists():continue
        m=json.loads((folder/'metrics.json').read_text())
        if not m.get('feasible',True) or m.get('relaxation',False):continue
        s=pd.read_csv(folder/'site_decisions.csv').set_index('car_park_no')
        f=pd.read_csv(folder/'demand_flows.csv')
        p=m['parameters'];x=s.ac_additions;dc=s.dc_additions;y=s.upgrade
        served=f.groupby('demand_site').kwh_day.sum().reindex(s.index,fill_value=0)
        used=f.groupby('supply_site').kwh_day.sum().reindex(s.index,fill_value=0)
        cap=p['ac_cost']*x+p['dc_cost']*dc+p['fixed_cost']*(x+dc>0)+p['upgrade_cost']*y
        crf=p['discount']/(1-(1+p['discount'])**(-p['lifetime'])) if p['discount'] else 1/p['lifetime']
        ann=crf*cap+(p['ac_maintenance']+p['network'])*x+(p['dc_maintenance']+p['network'])*dc
        radius=p['radius']
        residual=max(float(np.max(np.abs(served-s.served_kwh_day))),float(np.max(np.abs(used-s.capacity_used))),
                     float(np.maximum(served-s.demand_kwh_day,0).max()),float(np.maximum(-f.kwh_day,0).max()) if len(f) else 0,
                     float(np.maximum(-s.space_slack,0).max()),float(np.maximum(-s.power_slack_kw,0).max()),
                     abs(float(cap.sum()-m['capital'])),abs(float(ann.sum()-m['annual_cost'])),
                     max(0,float(cap.sum()-m['budget'])),
                     float(np.abs(x-np.rint(x)).max()),float(np.abs(dc-np.rint(dc)).max()),
                     max(0,float(f.distance_m.max()-radius)) if len(f) else 0)
        q=p['ac_power']*p['hours']*p['availability']*p['power_factor']
        qdc=p['dc_power']*p['dc_hours']*p['availability']*p['dc_power_factor']
        residual=max(residual,float(np.maximum(used-s.existing_capacity-q*x-qdc*dc,0).max()))
        if residual>1e-4:errors.append((folder.name,residual))
        count+=1
        if any(st['status']!='Optimal' for st in m.get('stages',[])):
            limited.append(folder.name)
    check('Independent saved-flow/cost/feasibility audit',not errors,f'{count} integer results checked; violations {errors}')
    check('Solver status transparency',True,f'{len(limited)} runs include a time-limited pass; names retained in solver_status_audit.json')
    (OUT/'solver_status_audit.json').write_text(json.dumps({'checked_runs':count,'non_optimal_pass_runs':limited,'violations':errors},indent=2))
    frontier=pd.read_csv(OUT/'budget_frontier.csv').sort_values('budget')
    check('Budget-service monotonicity',np.all(np.diff(frontier.served)>=-.02),frontier.served.tolist())
    base=json.loads((OUT/'runs/base/metrics.json').read_text())
    no=json.loads((OUT/'runs/no_build/metrics.json').read_text())
    check('No-build = zero-budget frontier',abs(frontier.iloc[0].served-no['served'])<1e-7,no['served'])
    targets=pd.read_csv(OUT/'service_targets.csv')
    q=base['parameters']['ac_power']*base['parameters']['hours']*base['parameters']['availability']*base['parameters']['power_factor']
    # Reconstruct exact S0 before the distance LP's small service tolerance.
    from model import build_instance,allocate
    inst=build_instance();f0,_=allocate(inst,distance=False)
    for r in targets.itertuples():
        t=int(r.name.split('_')[-1])/100
        lower=max(0,int(np.ceil((t*base['demand']-f0.sum()-1e-7)/q)))*base['parameters']['ac_cost']
        check('Minimum-capex certificate '+r.name,r.served>=t*base['demand']-1e-4 and abs(r.capital-lower)<1e-5,f'Feasible cost {r.capital}; lower bound {lower}')
    lp=json.loads((OUT/'lp_bound.json').read_text())
    check('LP bound dominates integer service',lp['lp_service_upper_bound']+1e-4>=base['served'],lp)
    repro=json.loads((OUT/'reproducibility.json').read_text())
    check('Identical-input reproduction',abs(repro['repeat_service_difference'])<.02,repro)
    sensitivity=pd.read_csv(OUT/'sensitivity.csv')
    feasible=sensitivity.fixed_construction_feasible
    sensitivity['regret_lower_bound_kwh']=np.where(feasible,np.maximum(0,sensitivity.served-sensitivity.fixed_served),np.nan)
    sensitivity['regret_upper_bound_kwh']=np.where(feasible,np.maximum(0,-sensitivity.pass1_bound-sensitivity.fixed_served),np.nan)
    check('Regret interval consistency',bool((sensitivity.loc[feasible,'regret_lower_bound_kwh']<=sensitivity.loc[feasible,'regret_upper_bound_kwh']+.02).all()),'Only physically and budget-feasible fixed plans have regret bounds')
    sensitivity.to_csv(OUT/'sensitivity.csv',index=False)
    tests=subprocess.run([sys.executable,str(Path(__file__).with_name('test_models.py'))],capture_output=True,text=True)
    (OUT/'unit_test_results.txt').write_text(tests.stdout+tests.stderr)
    check('Expected-answer model tests',tests.returncode==0,tests.stderr.strip().splitlines()[-1])
    # Record audited sample as a frozen desk-review artifact; it is not operator verification.
    review=Path(__file__).parent/'reviews/match_sample.csv'
    if review.exists():
        (INPUTS/'desk_review_sample.csv').write_bytes(review.read_bytes())
    if office:
        import openpyxl
        from docx import Document
        import pymupdf
        xlsx=ROOT/'HDB_EV_Charging_Analysis.xlsx'
        wb=openpyxl.load_workbook(xlsx,data_only=True,read_only=True)
        dashboard=wb['Dashboard']
        expected={'B5':base['demand'],'B6':base['served'],'B7':base['service_fraction'],'B8':base['ac_points'],
                  'B10':base['capital'],'B11':base['annual_cost'],'B12':no['served'],'B13':base['served']-no['served']}
        check('Workbook formula caches',all(abs(float(dashboard[cell].value)-value)<1e-5 for cell,value in expected.items()),expected)
        error_cells=[]
        for ws in wb:
            for row in ws.iter_rows():
                for cell in row:
                    if cell.data_type=='e':error_cells.append(f'{ws.title}!{cell.coordinate}: {cell.value}')
        check('Workbook error cells',not error_cells,error_cells)
        dc=wb['Demand_Calculator'];diffs=[float(row[9].value or 0) for row in list(dc.iter_rows())[4:]]
        check('Demand calculator reconciles to frozen model',max(map(abs,diffs))<1e-6,max(map(abs,diffs)))
        wb.close()
        doc=Document(ROOT/'HDB_EV_Charging_Report.docx')
        check('Report body typography',doc.styles['Normal'].font.name=='Times New Roman' and doc.styles['Normal'].font.size.pt==12,'12-point Times New Roman')
        check('Report margins',all(abs(getattr(doc.sections[0],a).inches-1)<1e-4 for a in ['top_margin','bottom_margin','left_margin','right_margin']),'1 inch on all sides')
        check('Formula images embedded',len(doc.inline_shapes)>=11,len(doc.inline_shapes))
        pdf=pymupdf.open(ROOT/'HDB_EV_Charging_Report.pdf')
        starts=[i for i,p in enumerate(pdf) if 'Appendix A. Model audit' in p.get_text()]
        first_appendix=starts[0] if starts else -1
        narrative_pages=first_appendix-2 # exclude cover and references page
        check('Narrative length',8<=narrative_pages<=14,{'narrative_pages':narrative_pages,'non_appendix_pages_including_cover_references':first_appendix,'total_pages':len(pdf)})
        outside=[]
        for i,page in enumerate(pdf):
            for x0,y0,x1,y1,text,*_ in page.get_text('blocks'):
                if x0 < 30 or x1 > page.rect.width-20 or y0<15 or y1>page.rect.height-15:
                    outside.append((i+1,text[:65]))
        check('Rendered content within page bounds',not outside,outside[:20])
        (OUT/'document_layout.json').write_text(json.dumps({'narrative_pages':narrative_pages,'appendix_starts_pdf_page':first_appendix+1,'total_pdf_pages':len(pdf)},indent=2))
    df=pd.DataFrame(checks);df.to_csv(OUT/'validation_checks.csv',index=False)
    (OUT/'VALIDATION.md').write_text('# Release validation\n\n'+ '\n'.join(f'- **{r.status}** {r.check}: {r.evidence}' for r in df.itertuples())+'\n')
    print(df[['check','status']].to_string(index=False))
    if (df.status=='FAIL').any():raise SystemExit('Validation failures require correction')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--office',action='store_true');main(parser.parse_args().office)
