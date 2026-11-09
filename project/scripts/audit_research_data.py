"""Profile input files and build review tables; does not fit demand or solve a model.
Run: python3 project/scripts/audit_research_data.py
Dependencies: pandas, numpy, shapely, pyproj, openpyxl, xlrd.
"""
import csv, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

DATA=Path(__file__).resolve().parents[1]/'data'
OUT=DATA/'09_research_audit';OUT.mkdir(exist_ok=True)
DER=DATA/'07_derived';DER.mkdir(exist_ok=True)

def profile():
    records=[]
    for p in sorted(DATA.rglob('*')):
        if not p.is_file() or '09_research_audit' in p.parts:continue
        row=dict(path=str(p.relative_to(DATA)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),rows='',columns='',null_cells='',duplicate_rows='',detail='')
        try:
            if p.suffix=='.csv' and 'Notes_' not in p.name:
                d=pd.read_csv(p,low_memory=False)
                row.update(rows=len(d),columns=' | '.join(d.columns),null_cells=int(d.isna().sum().sum()),duplicate_rows=int(d.duplicated().sum()))
                for col in ['month','year','Year','Time']:
                    if col in d: row['detail']+=f'{col}: {d[col].min()} to {d[col].max()}; '
            elif p.suffix=='.geojson':
                j=json.loads(p.read_text());fs=j['features']
                missing=sum(f.get('geometry') is None for f in fs)
                row.update(rows=len(fs),columns=' | '.join(fs[0]['properties']),detail='Geometry types: '+str(sorted({f['geometry']['type'] for f in fs if f.get('geometry') is not None}))+f'; null geometries: {missing}')
            elif p.suffix=='.xlsx':
                x=pd.ExcelFile(p);row['detail']='Sheets: '+' | '.join(x.sheet_names)
            else: row['detail']='Supporting source / archive / notes; not a model input table'
        except Exception as e:row['detail']='READ ERROR: '+str(e)
        records.append(row)
    pd.DataFrame(records).to_csv(OUT/'file_inventory.csv',index=False)

def geography(sites, year):
    raw=json.loads((DATA/f'05_geospatial_boundaries/URA_MP{year}_planning_area_boundary.geojson').read_text())['features']
    gs=[shape(f['geometry']) for f in raw];tree=STRtree(gs)
    names=[]
    for lon,lat in zip(sites.longitude,sites.latitude):
        p=Point(lon,lat);hit=next((int(i) for i in tree.query(p) if gs[i].covers(p)),None)
        names.append(raw[hit]['properties']['PLN_AREA_N'] if hit is not None else None)
    sites[f'planning_area_mp{year}']=names

def site_supply_audit():
    h=pd.read_csv(DATA/'03_carparks_candidate_sites/HDB_carpark_information.csv',dtype={'car_park_no':str})
    lots=pd.read_csv(DATA/'03_carparks_candidate_sites/HDB_carpark_lots_snapshot_2026-10-31.csv')
    c=lots[lots.lot_type=='C'].copy();assert not c.car_park_no.duplicated().any();assert not h.car_park_no.duplicated().any()
    sites=h.merge(c[['car_park_no','total_lots','update_datetime']],on='car_park_no',how='left',validate='one_to_one')
    sites['capacity_status']=np.select([sites.total_lots.isna(),sites.total_lots.eq(0)],['missing','zero'],default='observed_positive')
    tr=Transformer.from_crs(3414,4326,always_xy=True);sites['longitude'],sites['latitude']=tr.transform(sites.x_coord.to_numpy(),sites.y_coord.to_numpy())
    for y in [2019,2025]:geography(sites,y)
    sites.to_csv(DER/'hdb_sites_capacity_review.csv',index=False)
    sites[sites.capacity_status!='observed_positive'].to_csv(OUT/'hdb_missing_or_zero_capacity.csv',index=False)
    cp=pd.read_csv(DATA/'01_ev_charging_supply/LTA_EV_charging_points_Sep2026.csv',dtype={'PostalCode':str})
    cp['PostalCode']=cp.PostalCode.str.zfill(6)
    reg=cp.groupby('EV Charger Registration Code').agg(point_rows=('evCpId','size'),outlets_min=('No. of Charging Outlets','min'),outlets_max=('No. of Charging Outlets','max'),power_values=('charging Speed','nunique'),sum_point_kw=('charging Speed','sum'),max_point_kw=('charging Speed','max'))
    reg.to_csv(OUT/'charger_registration_unit_audit.csv')
    loc=cp.groupby(['longitude','latitude'],dropna=False).agg(point_rows=('evCpId','size'),example_id=('evCpId','first'),postal_code=('PostalCode','first'),block=('Block/House No','first'),street=('Street Name','first'),building=('Building Name','first')).reset_index()
    tr=Transformer.from_crs(4326,3414,always_xy=True);xx,yy=tr.transform(loc.longitude.to_numpy(),loc.latitude.to_numpy());xy=np.column_stack([xx,yy]);hxy=sites[['x_coord','y_coord']].to_numpy()
    near=[];dist=[];alternatives=[]
    for p in xy:
        ds=np.sqrt(((hxy-p)**2).sum(axis=1));i=int(ds.argmin());near.append(i);dist.append(float(ds[i]));alternatives.append(int((ds<=100).sum()))
    loc['nearest_hdb_id']=sites.iloc[near].car_park_no.to_numpy();loc['nearest_hdb_address']=sites.iloc[near].address.to_numpy();loc['distance_m']=np.round(dist,2);loc['hdb_sites_within_100m']=alternatives
    loc['status']='unconfirmed_candidate_only';loc.to_csv(OUT/'charger_location_hdb_match_candidates.csv',index=False)
    stats=dict(hdb_sites=len(h),capacity_carpark_records=len(c),matched_capacity=int(sites.total_lots.notna().sum()),missing_capacity=int(sites.total_lots.isna().sum()),zero_capacity=int(sites.total_lots.eq(0).sum()),matched_car_lots=int(sites.total_lots.sum()),all_snapshot_car_lots=int(c.total_lots.sum()),non_hdb_snapshot_ids=sorted(set(c.car_park_no)-set(h.car_park_no)),charger_point_rows=len(cp),unique_point_ids=int(cp.evCpId.nunique()),unique_registrations=len(reg),naive_outlet_sum=int(cp['No. of Charging Outlets'].sum()),registration_deduplicated_outlets=int(reg.outlets_max.sum()),registrations_rows_equal_reported_outlets=int((reg.point_rows==reg.outlets_max).sum()),multi_point_registrations=int((reg.point_rows>1).sum()),exact_coordinate_locations=len(loc),locations_near_hdb_100m=int(loc.distance_m.le(100).sum()),locations_with_multiple_hdb_within_100m=int(loc.hdb_sites_within_100m.gt(1).sum()),unmatched_mp2019=int(sites.planning_area_mp2019.isna().sum()),unmatched_mp2025=int(sites.planning_area_mp2025.isna().sum()),sites_changing_planning_area=int((sites.planning_area_mp2019.fillna('')!=sites.planning_area_mp2025.fillna('')).sum()))
    (OUT/'audit_metrics.json').write_text(json.dumps(stats,indent=2)+'\n');print(json.dumps(stats,indent=2))

def demographics():
    upd=DATA/'04_demographics_demand_proxies/updates_2026-11-09';parts=[]
    for p in sorted(upd.glob('*.csv')):
        if 'Notes_' in p.name:continue
        d=pd.read_csv(p)
        if not {'PA','SZ','Time'}.issubset(d.columns):continue
        keys=['PA','SZ','Time'];metric='Pop' if 'Pop' in d else 'HSE'
        for col in keys:assert d[col].notna().all()
        vals=pd.to_numeric(d[metric],errors='raise');assert vals.ge(0).all();d[metric]=vals
        total=d.groupby(keys,as_index=False)[metric].sum().rename(columns={metric:'value'})
        total['metric']='resident_population' if metric=='Pop' else 'dwelling_stock';total['scope']='all_dwelling_types'
        frames=[total]
        if 'TOD' in d:
            z=d[d.TOD.str.startswith('HDB ')].groupby(keys,as_index=False)[metric].sum().rename(columns={metric:'value'})
            z['metric']=total.metric.iloc[0];z['scope']='hdb_only';frames.append(z)
        for f in frames:
            f['source_file']=p.name;f['geography_vintage']=np.where(f.Time==2026,'MP2025','MP2019');parts.append(f)
    combined=pd.concat(parts,ignore_index=True)
    # Two different 2024 population classifications are deliberately separate, not summed together.
    combined.to_csv(DER/'population_dwelling_subzone_review.csv',index=False)
    pa=combined.groupby(['PA','Time','metric','scope','source_file','geography_vintage'],as_index=False).value.sum()
    pa.to_csv(DER/'population_dwelling_planning_area_review.csv',index=False)
    print('Demographic summaries:',len(combined),'subzone rows;',len(pa),'area rows')
    print(pa[(pa.PA=='Tengah')&(pa.scope=='hdb_only')][['Time','metric','value','geography_vintage']].to_string(index=False))

def main():
    site_supply_audit();demographics()
    legacy=DER/'charging_points_with_planning_area.csv'
    if legacy.exists():
        points=pd.read_csv(legacy)
        points[points.PLN_AREA_N.isna()].to_csv(OUT/'public_chargers_without_planning_area.csv',index=False)
    profile()
if __name__=='__main__':main()
