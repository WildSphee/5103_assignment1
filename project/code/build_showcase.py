"""Planning-area showcase and dated energy shortfalls, from frozen solved results."""
import json
import numpy as np
import pandas as pd
from prepare_data import OUT, INPUTS


def build_top100():
    """Deterministic review ranking within the saved 2027 solution, not a new solve."""
    sites=pd.read_csv(OUT/'runs/base/site_decisions.csv')
    robustness=pd.read_csv(OUT/'site_robustness.csv')
    eligible=robustness.loc[(robustness.base_additions>0)&~robustness.imputed&robustness.night_parking.eq('YES')]
    ranked=eligible.sort_values(['selection_fraction','base_additions','car_park_no'],ascending=[False,False,True]).head(100)
    ranked=ranked.merge(sites[['car_park_no','longitude','latitude','x_coord','y_coord','capacity_status']],on='car_park_no',validate='one_to_one')
    ranked.insert(0,'rank',range(1,len(ranked)+1))
    ranked['demand_horizon']='End-2027 base scenario'
    ranked.to_csv(OUT/'top_100_recommended_sites.csv',index=False)
    features=[{'type':'Feature','geometry':{'type':'Point','coordinates':[r.longitude,r.latitude]},
        'properties':{'rank':int(r.rank),'car_park_no':r.car_park_no,'address':r.address,
        'planning_area':r.area_2019,'additional_ac_points':int(r.base_additions),
        'certified_scenario_selection_fraction':r.selection_fraction}} for r in ranked.itertuples()]
    (OUT/'top_100_recommended_sites.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},indent=2))
    return ranked


def build_tables():
    sites=pd.read_csv(OUT/'runs/base/site_decisions.csv')
    base=json.loads((OUT/'runs/base/metrics.json').read_text())
    summary=json.loads((OUT/'analysis_summary.json').read_text())
    sensitivity=pd.read_csv(OUT/'sensitivity.csv').set_index('name')
    stocks=pd.read_csv(INPUTS/'ev_stock_scenarios.csv').set_index('scenario')
    selected=sites[sites.ac_additions+sites.dc_additions>0]
    area=selected.groupby('area_2019').agg(selected_carparks=('car_park_no','size'),
        additional_ac_points=('ac_additions','sum'),additional_dc_points=('dc_additions','sum'),
        capital_sgd=('capex','sum')).reset_index().rename(columns={'area_2019':'planning_area'})
    area=area.sort_values(['additional_ac_points','planning_area'],ascending=[False,True]).reset_index(drop=True)
    area['share_of_new_ac_points']=area.additional_ac_points/area.additional_ac_points.sum()
    area['demand_horizon']='End-2027 base scenario'
    area['national_service_target']=.9
    area['national_capital_budget_sgd']=base['budget']
    area.to_csv(OUT/'planning_area_deployment_2027.csv',index=False)
    rows=[]
    definitions=[('current_2026','stock_current_2026','Sep 2026 benchmark'),
        ('2027_low','stock_2027_low','End 2027 — low'),('2027_base','base','End 2027 — base'),
        ('2027_high','stock_2027_high','End 2027 — high'),('2030_low','outlook_2030_low','2030 — low'),
        ('2030_base','outlook_2030_base','2030 — central'),('2030_high','outlook_2030_high','2030 — high')]
    for scenario,run,label in definitions:
        if run=='base':
            demand=base['demand'];existing=summary['no_build_served'];fixed=base['served']
        else:
            r=sensitivity.loc[run];demand=r.demand;existing=r.no_build_served;fixed=r.fixed_served
        if scenario=='current_2026':
            # Do not present future construction as available in the current benchmark.
            fixed=np.nan
        rows.append({'scenario':scenario,'demand_period':label,'national_electric_cars':stocks.loc[scenario,'stock'],
            'demand_kwh_day':demand,'existing_service_kwh_day':existing,
            'existing_shortfall_kwh_day':demand-existing,'existing_shortfall_fraction':1-existing/demand,
            'fixed_2027_plan_service_kwh_day':fixed,'fixed_2027_plan_shortfall_kwh_day':demand-fixed,
            'fixed_2027_plan_shortfall_fraction':1-fixed/demand,
            'demand_evidence':'Observed national EV stock; modelled HDB demand' if scenario=='current_2026' else 'Assumed national EV-stock scenario; not a fitted forecast',
            'supply_basis':'Frozen Sep-2026 matched supply; future column adds the same 2,332 AC points, with no further expansion',
            'shortfall_unit':'Grid-side kWh/day; not an observed charger-count deficit'})
    years=pd.DataFrame(rows)
    years.to_csv(OUT/'year_shortfalls.csv',index=False)
    assert len(area)==selected.area_2019.nunique() and area.selected_carparks.sum()==base['sites_selected']
    assert area.additional_ac_points.sum()==base['ac_points']
    assert np.isclose(area.capital_sgd.sum(),base['capital'])
    assert np.allclose(years.existing_service_kwh_day+years.existing_shortfall_kwh_day,years.demand_kwh_day)
    future=years.fixed_2027_plan_service_kwh_day.notna()
    assert np.allclose(years.loc[future,'fixed_2027_plan_service_kwh_day']+years.loc[future,'fixed_2027_plan_shortfall_kwh_day'],years.loc[future,'demand_kwh_day'])
    return area,years


if __name__=='__main__':
    area,years=build_tables()
    print(area.to_string(index=False))
    print(years[['demand_period','existing_shortfall_fraction','fixed_2027_plan_shortfall_fraction']].to_string(index=False))
