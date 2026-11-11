"""Auditable Excel deliverable with cached formulas and frozen solver tables."""
import json
from dataclasses import asdict
import math
from pathlib import Path
import numpy as np
import pandas as pd
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
from model import Parameters
from prepare_data import ROOT, INPUTS, OUT


def main():
    path=ROOT/'HDB_EV_Charging_Analysis.xlsx'
    wb=xlsxwriter.Workbook(path,{'nan_inf_to_errors':False,'strings_to_urls':False})
    wb.set_properties({'title':'HDB EV Charging: Placement and Cost-Effectiveness','subject':'Frozen 2027 scenario; reproducible Python optimisation','author':'DBA5103 Project','comments':'Generated from validated local model outputs. Input edits do not re-solve the MILP.'})
    navy='#19384B';blue='#347594'
    title=wb.add_format({'bold':True,'font_size':18,'font_color':navy})
    note=wb.add_format({'font_size':10,'font_color':'#647580','text_wrap':True})
    number=wb.add_format({'num_format':'#,##0.00;[Red](#,##0.00)'})
    integer=wb.add_format({'num_format':'#,##0'})
    percent=wb.add_format({'num_format':'0.0%'})
    formula_fmt=wb.add_format({'num_format':'#,##0.00','font_color':blue,'bg_color':'#EDF5F8'})
    wrap=wb.add_format({'text_wrap':True,'valign':'top'})
    head=wb.add_format({'bold':True,'bg_color':navy,'font_color':'white','text_wrap':True,'valign':'vcenter'})
    sheets={}

    def table(name,df,subtitle='',widths=None):
        df=df.copy().replace([np.inf,-np.inf],np.nan)
        ws=wb.add_worksheet(name);sheets[name]=(ws,df)
        ws.hide_gridlines(2);ws.set_tab_color(blue)
        ws.merge_range(0,0,0,max(3,min(len(df.columns)-1,7)),name.replace('_',' '),title)
        ws.merge_range(1,0,1,max(3,min(len(df.columns)-1,7)),subtitle,note);ws.set_row(1,32)
        for j,col in enumerate(df):
            ws.write(3,j,col,head)
            width=min(38,max(13,len(col)+2)) if widths is None else widths.get(col,18)
            ws.set_column(j,j,width,number if pd.api.types.is_numeric_dtype(df[col]) else None)
        ws.set_row(3,32)
        for i,row in enumerate(df.itertuples(index=False,name=None),4):
            for j,value in enumerate(row):
                if pd.isna(value):
                    ws.write_blank(i,j,None)
                elif isinstance(value,(bool,np.bool_)):
                    ws.write_boolean(i,j,bool(value))
                elif isinstance(value,(int,float,np.number)):
                    ws.write_number(i,j,float(value))
                else:
                    ws.write_string(i,j,str(value))
        if len(df):
            ws.add_table(3,0,3+len(df),len(df.columns)-1,{'name':'T_'+name,'style':'Table Style Medium 2',
                'columns':[{'header':str(c)} for c in df.columns]})
        ws.freeze_panes(4,1);ws.set_landscape();ws.fit_to_pages(1,0);ws.repeat_rows(0,3)
        return ws

    readme=pd.DataFrame([
        ('Purpose','Where and how many additional AC points; service delivered per infrastructure dollar.'),
        ('Scope','All 2,273 HDB candidate sites. Existing supply is address-supported, not field-verified.'),
        ('Base period','2027 planning scenario, based on Sep-2026 vehicle/charger stock and Oct-2026 parking lots.'),
        ('How to read','Dashboard → Frontier / Comparison → Sensitivity → Base_Sites and Shortlist. Full scenario flows are in code/outputs/runs/.'),
        ('Editable formulas','Parameters and Demand_Calculator expose demand arithmetic. Dashboard and frontier ratios have cached Excel formula values.'),
        ('Re-solving','Changing spreadsheet inputs does not update frozen optimisation results. Edit Python Parameters/scenario definitions and rerun code/run_analysis.py.'),
        ('Money','Constant 2026 scenario SGD excluding GST. Infrastructure annual cost excludes electricity and sunk existing investment.'),
        ('Uncertainty','Input assumptions and supply exclusions are explicit. Scenario selection frequency is not a probability of optimality.'),
        ('Fixed-plan stress','Hold AC counts and upgrades fixed. Derate usable capacity if power/space limits tighten. Flag over-budget and physically noncompliant plans.'),
        ('Solver','HiGHS MILP, service first then annual cost. Fixed-investment LP minimises distance after preserving service. Status, bounds and gaps are retained.'),
        ('Code','code/requirements.txt, code/venv/, code/README.md; all new Python and generated assets remain in code/.'),
        ('Reproducibility','Source SHA-256 values, exact parameters, logs and all numerical outputs are under code/outputs/.'),
        ('Interpretation','Service is modelled grid-side kWh/day, not observed use, waiting-time performance, or an engineering feasibility certificate.'),
    ],columns=['Topic','Explanation'])
    ws=table('Read_Me',readme,'Workbook guide and interpretation',{'Topic':25,'Explanation':105});ws.set_column(1,1,105,wrap)
    for row in range(4,len(readme)+4):ws.set_row(row,34)
    base=json.loads((OUT/'runs/base/metrics.json').read_text())
    p=base['parameters']
    pars=pd.DataFrame([{'parameter':k,'base':v,'classification':'Design/scenario assumption' if k not in ['seed','time_limit','mip_gap'] else 'Solver control'} for k,v in p.items()])
    pws=table('Parameters',pars,'Model base parameters. Units and source evidence are in Cost_Evidence.',{'parameter':28,'base':22,'classification':40})
    pref={k:f"'Parameters'!$B${i+5}" for i,k in enumerate(pars.parameter)}
    source=pd.read_csv(INPUTS/'parameter_evidence.csv');table('Cost_Evidence',source,'Evidence categories distinguish source observations from model assumptions.')
    s=pd.read_csv(OUT/'runs/base/site_decisions.csv')
    site_columns=['car_park_no','address','area_2019','capacity_status','total_lots','lots','imputed','night_parking',
                  'demand_kwh_day','served_kwh_day','unmet_kwh_day','existing_capacity','capacity_used',
                  'ac_additions','dc_additions','upgrade','capex','annual_cost','space_slack','power_slack_kw','longitude','latitude']
    site=s[site_columns]
    table('Base_Sites',site,'Frozen investment and allocation results; no matched supply does not prove no installed chargers.')
    def srange(col):
        letter=xl_col_to_name(site.columns.get_loc(col));return f"'Base_Sites'!${letter}$5:${letter}${len(site)+4}"
    summary=json.loads((OUT/'analysis_summary.json').read_text())
    metrics=[('Demand',f'=SUM({srange("demand_kwh_day")})',base['demand'],'kWh/day'),
             ('Served',f'=SUM({srange("served_kwh_day")})',base['served'],'kWh/day'),
             ('Service fraction','=B6/B5',base['service_fraction'],'fraction'),
             ('New AC points',f'=SUM({srange("ac_additions")})',base['ac_points'],'points'),
             ('Selected sites',f'=COUNTIF({srange("ac_additions")},">0")',base['sites_selected'],'sites'),
             ('Capital cost',f'=SUM({srange("capex")})',base['capital'],'SGD upfront'),
             ('Annual infrastructure cost',f'=SUM({srange("annual_cost")})',base['annual_cost'],'SGD/year'),
             ('Existing-only service',None,summary['no_build_served'],'kWh/day'),
             ('Incremental service','=B6-B12',summary['incremental_served'],'kWh/day'),
             ('Cost per additional annual kWh','=IF(B13>0,B11/(365*B13),"")',base['annual_cost']/(365*summary['incremental_served']),'SGD/kWh'),
             ('New-point daily capacity',f'={pref["ac_power"]}*{pref["hours"]}*{pref["availability"]}*{pref["power_factor"]}',summary['q_new_ac'],'kWh/day'),
             ('Service arcs',None,summary['arcs'],'arcs')]
    ws=table('Dashboard',pd.DataFrame([(a,c,d) for a,b,c,d in metrics],columns=['Measure','Value','Unit']),summary['anchor_reason'],{'Measure':36,'Value':24,'Unit':22})
    for row,(_,formula,value,unit) in enumerate(metrics,4):
        if formula:ws.write_formula(row,1,formula,percent if unit=='fraction' else formula_fmt,value)
    calc=pd.DataFrame({'site_id':s.car_park_no,'area':s.area_2019,'observed_lots':s.total_lots,'model_lots':s.lots,'imputed':s.imputed,
                       'lot_weight':s.lots/s.lots.sum(),'estimated_hdb_evs':p['stock']*p['hdb_share']*s.lots/s.lots.sum(),
                       'calculated_grid_kwh_day':s.demand_kwh_day,'frozen_model_kwh_day':s.demand_kwh_day,'difference':0.})
    ws=table('Demand_Calculator',calc,'Live arithmetic for lot-weight demand; edited inputs do not re-solve investments.')
    for i,row in calc.iterrows():
        rr=i+5
        formulas={5:f'=D{rr}/SUM($D$5:$D${len(calc)+4})',6:f'={pref["stock"]}*{pref["hdb_share"]}*F{rr}',
                  7:f'=G{rr}*{pref["dependence"]}*{pref["annual_km"]}/365*{pref["intensity"]}/{pref["efficiency"]}',9:f'=H{rr}-I{rr}'}
        for col,formula in formulas.items():ws.write_formula(i+4,col,formula,formula_fmt,float(row.iloc[col]))
    f=pd.read_csv(OUT/'budget_frontier.csv')
    cols=['name','budget','capital','demand','served','service_fraction','incremental_kwh_day','annual_cost','annual_infrastructure_cost_per_extra_kwh',
          'marginal_capex_per_extra_annual_kwh','ac_points','sites_selected','pass1_status','pass1_gap','pass2_status','pass2_gap']
    df=f.reindex(columns=cols)
    ws=table('Frontier',df,'Actual cost-service points; the budget is illustrative, not a government appropriation.')
    for i,row in df.iterrows():
        rr=i+5
        ws.write_formula(i+4,5,f'=E{rr}/D{rr}',percent,row.service_fraction)
        ws.write_formula(i+4,6,f'=E{rr}-$E$5',formula_fmt,row.incremental_kwh_day)
        val=row.annual_infrastructure_cost_per_extra_kwh
        ws.write_formula(i+4,8,f'=IF(G{rr}>0,H{rr}/(365*G{rr}),"")',formula_fmt,float(val) if pd.notna(val) else '')
        if i>0:
            val=row.marginal_capex_per_extra_annual_kwh
            ws.write_formula(i+4,9,f'=IF(E{rr}>E{rr-1},(C{rr}-C{rr-1})/(365*(E{rr}-E{rr-1})),"")',formula_fmt,float(val) if pd.notna(val) else '')
    chart=wb.add_chart({'type':'scatter','subtype':'straight_with_markers'})
    chart.add_series({'name':'MILP service frontier','categories':['Frontier',4,2,len(df)+3,2],'values':['Frontier',4,5,len(df)+3,5],
                      'line':{'color':navy},'marker':{'type':'circle','size':5}})
    chart.set_title({'name':'Service gained by investment'});chart.set_x_axis({'name':'Capital expenditure (SGD)'})
    chart.set_y_axis({'name':'Demand served','num_format':'0%'});chart.set_legend({'none':True});chart.set_size({'width':700,'height':350})
    sheets['Dashboard'][0].insert_chart('E5',chart)
    comp=pd.read_csv(OUT/'baseline_comparison.csv');table('Comparison',comp.reindex(columns=['name','budget','capital','unspent','ac_points','sites_selected','served','service_fraction','annual_cost','distance_m','pass1_status','pass1_gap']),
        'Equal/proportional/greedy and MILP at their actual spend; matched_* rows reoptimise the same spend.')
    table('Service_Targets',pd.read_csv(OUT/'service_targets.csv'),'Target-cost certificates and solver status; see minimum_capex_proof when a constructive bound is attained.')
    sens=pd.read_csv(OUT/'sensitivity.csv')
    fields=['name','demand','served','service_fraction','capital','annual_cost','ac_points','dc_points','upgrades','sites_selected',
            'fixed_served','fixed_fraction','fixed_repriced_capital','fixed_over_budget','fixed_derated_sites','fixed_construction_feasible',
            'reoptimised_minus_fixed_kwh','feasible_fixed_plan_regret_kwh','regret_lower_bound_kwh','regret_upper_bound_kwh','no_build_served','imputed_investment_share','pass1_status','pass1_gap','pass2_status','pass2_gap']
    table('Sensitivity',sens.reindex(columns=fields),'Same nominal capital budget. Fixed-plan regret is blank when that plan breaches scenario budget or construction limits.')
    table('Scenario_Parameters',pd.read_csv(OUT/'scenario_parameters.csv'),'Exact inputs for each sensitivity run; 2026 geography is mapped separately.')
    table('Site_Robustness',pd.read_csv(OUT/'site_robustness.csv'),'Main frequency uses cases with both objectives certified; all-feasible frequency is separate. Neither is a probability.')
    table('Shortlist',pd.read_csv(OUT/'shortlist_replacement.csv'),'Exclude each candidate and reoptimise at equal budget; negative/tiny losses may reflect tolerances.')
    if (OUT/'shortlist_desk_review.csv').exists():
        table('Shortlist_Review',pd.read_csv(OUT/'shortlist_desk_review.csv'),'Specific source-record gates: two survey candidates; three supply-reconciliation holds. No field confirmation.')
    table('Existing_Supply',pd.read_csv(INPUTS/'existing_supply.csv'),'Registration maximum-port and sum-port bounds; bay counts are separate from supply power.')
    cross=pd.read_csv(INPUTS/'hdb_charger_crosswalk.csv',dtype={'PostalCode':str})
    table('Charger_Crosswalk',cross[['evCpId','EV Charger Registration Code','PostalCode','Block/House No','Street Name','Building Name','charging Speed','plugType','site_id','match_status','match_distance_m','match_reason']],
        'Complete 11,489-point ledger; address-supported does not mean field-verified.')
    table('Capacity_Exceptions',pd.read_csv(INPUTS/'site_exceptions.csv'),'Missing/zero capacity and residential-review flags; all sites remain in base scope.')
    table('Stock_Scenarios',pd.read_csv(INPUTS/'ev_stock_scenarios.csv'),'Assumed stock-flow scenarios and 2030 fleet-share stress cases; not statistical forecasts.')
    table('Area_Weights',pd.read_csv(INPUTS/'area_demand_weights.csv'),'Population and dwelling alternatives; base 2025/MP2019 and separate 2026/MP2025.')
    table('Area_Results',pd.read_csv(OUT/'runs/base/area_results.csv'),'Area aggregates of base demand, service and investment.')
    table('Base_Flows',pd.read_csv(OUT/'runs/base/demand_flows.csv'),'Nonzero modelled energy flows after minimum-distance allocation.')
    table('Sources',pd.DataFrame(json.loads((INPUTS/'source_hashes.json').read_text())),'Frozen source-file hashes; original URLs and collection dates are in data/README.md and the research manifest.')
    desk=INPUTS/'desk_review_sample.csv'
    if desk.exists():table('Desk_Review',pd.read_csv(desk),'48 stratified source-record checks; no operator or field verification.')
    checks=OUT/'validation_checks.csv'
    if checks.exists():table('Validation',pd.read_csv(checks),'Automated checks of source totals, feasibility, certificates, report and workbook.')
    wb.close()
    print('Saved',path)


if __name__=='__main__':
    main()
