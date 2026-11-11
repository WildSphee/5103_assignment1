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
    from build_showcase import build_tables, build_top100
    area_showcase,years=build_tables()
    top100=build_top100()
    saved=pd.read_csv(OUT/'runs/base/site_decisions.csv').set_index('car_park_no')
    ranked=pd.read_csv(OUT/'site_robustness.csv')
    eligible=ranked[(ranked.base_additions>0)&~ranked.imputed&ranked.night_parking.eq('YES')]
    expected=eligible.sort_values(['selection_fraction','base_additions','car_park_no'],ascending=[False,False,True]).head(100)
    check('Top 100 deterministic review ranking',len(top100)==100 and top100.car_park_no.is_unique and top100.car_park_no.tolist()==expected.car_park_no.tolist(),
          f'100 unique sites from {len(eligible)} eligible base-selected sites; certified frequency, additions, ID ordering')
    mapped=saved.loc[top100.car_park_no]
    check('Top 100 coordinates and additions',np.allclose(top100[['longitude','latitude']],mapped[['longitude','latitude']]) and np.allclose(top100.base_additions,mapped.ac_additions) and mapped.longitude.between(103,105).all() and mapped.latitude.between(1,2).all(),
          f'{int(top100.base_additions.sum())} proposed AC points across {top100.area_2019.nunique()} planning areas; coordinates match frozen model')
    geo=json.loads((OUT/'top_100_recommended_sites.geojson').read_text())['features']
    check('Map data reconciles to top 100',len(geo)==100 and [f['properties']['car_park_no'] for f in geo]==top100.car_park_no.tolist() and np.allclose([f['geometry']['coordinates'] for f in geo],top100[['longitude','latitude']]),'GeoJSON contains every ranked site in longitude/latitude order')
    check('Planning-area deployment reconciles',area_showcase.selected_carparks.sum()==base['sites_selected'] and area_showcase.additional_ac_points.sum()==base['ac_points'] and abs(area_showcase.capital_sgd.sum()-base['capital'])<1e-5,
          f'{len(area_showcase)} areas; {area_showcase.selected_carparks.sum()} carparks; {area_showcase.additional_ac_points.sum()} additional AC points for end-2027')
    future=years.fixed_2027_plan_service_kwh_day.notna()
    check('Dated energy-shortfall balances',np.allclose(years.existing_service_kwh_day+years.existing_shortfall_kwh_day,years.demand_kwh_day) and np.allclose(years.loc[future,'fixed_2027_plan_service_kwh_day']+years.loc[future,'fixed_2027_plan_shortfall_kwh_day'],years.loc[future,'demand_kwh_day']),
          'Existing-only and fixed-2027-plan service plus unmet energy reconcile to each scenario demand')
    check('No future supply presented as installed in 2026',years.loc[years.scenario.eq('current_2026'),'fixed_2027_plan_service_kwh_day'].isna().all(),
          '2026 future-plan cells are blank; benchmark uses Sep-2026 national EV stock and modelled HDB demand')
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
        area_rows=list(wb['Area_Deployment_2027'].iter_rows(min_row=5,values_only=True))
        map_rows=list(wb['Top_100_Sites'].iter_rows(min_row=5,values_only=True))
        check('Workbook top 100 map register',len(map_rows)==100 and [r[1] for r in map_rows]==top100.car_park_no.tolist(),'All 100 map candidates, in rank order, with coordinates and scenario evidence')
        check('Workbook planning-area showcase',len(area_rows)==len(area_showcase) and sum(r[1] for r in area_rows)==base['sites_selected'] and sum(r[2] for r in area_rows)==base['ac_points'],
              'All 28 areas and all additions are visible in Area_Deployment_2027; dated shortfalls are in Year_Outlook')
        dc=wb['Demand_Calculator'];diffs=[float(row[9].value or 0) for row in list(dc.iter_rows())[4:]]
        check('Demand calculator reconciles to frozen model',max(map(abs,diffs))<1e-6,max(map(abs,diffs)))
        wb.close()
        doc=Document(ROOT/'HDB_EV_Charging_Report.docx')
        check('Report body typography',doc.styles['Normal'].font.name=='Times New Roman' and doc.styles['Normal'].font.size.pt==12,'12-point Times New Roman')
        report_styles=['Normal','Title','Heading 1','Heading 2','Caption','Small']
        check('Report consistent typography',all(doc.styles[name].font.name=='Times New Roman' and doc.styles[name].font.size.pt==12 for name in report_styles),'12-point Times New Roman for headings, body, captions and notes; monospace code appendix exception')
        check('Report double spacing',all(doc.styles[name].paragraph_format.line_spacing==2 for name in report_styles),'Double-spaced report text, as specified on page 1 of Project_Guideline.pdf')
        table_paragraphs=[p for t in doc.tables for row in t.rows for cell in row.cells for p in cell.paragraphs if p.text.strip()]
        check('Report table typography',all(p.paragraph_format.line_spacing in (None,2) and all(r.font.name in (None,'Times New Roman') and (r.font.size is None or r.font.size.pt==12) for r in p.runs) for p in table_paragraphs),'12-point Times and double spacing in tables and callouts')
        check('Report margins',all(abs(getattr(doc.sections[0],a).inches-1)<1e-4 for a in ['top_margin','bottom_margin','left_margin','right_margin']),'1 inch on all sides')
        check('Formula images embedded',len(doc.inline_shapes)>=11,len(doc.inline_shapes))
        pdf=pymupdf.open(ROOT/'HDB_EV_Charging_Report.pdf')
        starts=[i for i,p in enumerate(pdf) if 'Appendix A. Model audit' in p.get_text()]
        first_appendix=starts[0] if starts else -1
        reference_starts=[i for i,p in enumerate(pdf) if any(line.strip()=='References' for line in p.get_text().splitlines())]
        first_reference=reference_starts[0] if reference_starts else -1
        narrative_pages=first_reference-1 # exclude cover and all reference pages
        reference_pages=first_appendix-first_reference
        check('No sparse narrative spillover pages',all(len(pdf[i].get_text().split())>=60 for i in range(1,first_reference)),'Every narrative page has at least 60 words alongside its figures/tables')
        check('Report section pagination',1<first_reference<first_appendix,{'narrative_pages':narrative_pages,'reference_pages':reference_pages,'total_pages':len(pdf),'guideline':'8–14 narrative pages suggested; explicitly no strict page limit'})
        outside=[]
        for i,page in enumerate(pdf):
            for x0,y0,x1,y1,text,*_ in page.get_text('blocks'):
                if x0 < 30 or x1 > page.rect.width-20 or y0<15 or y1>page.rect.height-15:
                    outside.append((i+1,text[:65]))
        check('Rendered content within page bounds',not outside,outside[:20])
        (OUT/'document_layout.json').write_text(json.dumps({'narrative_pages':narrative_pages,'reference_pages':reference_pages,'appendix_starts_pdf_page':first_appendix+1,'total_pdf_pages':len(pdf)},indent=2))
    df=pd.DataFrame(checks);df.to_csv(OUT/'validation_checks.csv',index=False)
    (OUT/'VALIDATION.md').write_text('# Release validation\n\n'+ '\n'.join(f'- **{r.status}** {r.check}: {r.evidence}' for r in df.itertuples())+'\n')
    print(df[['check','status']].to_string(index=False))
    if (df.status=='FAIL').any():raise SystemExit('Validation failures require correction')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--office',action='store_true');main(parser.parse_args().office)
