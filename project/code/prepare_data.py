"""Freeze auditable HDB inputs from the supplied local source vintage."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = Path(__file__).resolve().parent / 'outputs'
INPUTS = OUT / 'inputs'
USED = set()


def read(rel, **kw):
    p = DATA / rel
    USED.add(p)
    return pd.read_csv(p, **kw)


def normal(text):
    s = str(text).upper() if pd.notna(text) else ''
    for a, b in {'AVE': 'AVENUE', 'ST': 'STREET', 'RD': 'ROAD',
                 'DR': 'DRIVE', 'CRES': 'CRESCENT', 'CTRL': 'CENTRAL',
                 'BT': 'BUKIT', 'NTH': 'NORTH', 'STH': 'SOUTH',
                 'UPP': 'UPPER', 'TG': 'TANJONG', 'JLN': 'JALAN',
                 'CL': 'CLOSE', 'PL': 'PLACE', 'TER': 'TERRACE',
                 'KG': 'KAMPONG', 'LOR': 'LORONG', 'GDNS': 'GARDENS'}.items():
        s = re.sub(r'\b' + a + r'\b', b, s)
    return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s).split())


def address_parts(address):
    s = str(address).upper()
    m = re.match(r'(?:BLKS?\s*)?(\d+[A-Z]?(?:\s*[/,&-]\s*\d+[A-Z]?)*)\s+([A-Z].*)', s)
    if not m:
        return set(), '', []
    blocks = set(re.findall(r'\d+[A-Z]?', m[1]))
    ranges = []
    for a, b in re.findall(r'(\d+)\s*[/\-]\s*(\d+)(?![A-Z])', m[1]):
        if 0 <= int(b) - int(a) <= 60:
            ranges.append((int(a), int(b)))
    street = re.sub(r'\b(?:MULTI.?STOREY|BASEMENT|SURFACE|CAR PARK|CARPARK|MSCP).*', '', m[2]).strip()
    return blocks, normal(street), ranges


def geotag(sites, year):
    p = DATA / f'05_geospatial_boundaries/URA_MP{year}_planning_area_boundary.geojson'
    USED.add(p)
    fs = json.loads(p.read_text())['features']
    gs = [shape(f['geometry']) for f in fs]
    tree = STRtree(gs)
    names = []
    for lon, lat in zip(sites.longitude, sites.latitude):
        pt = Point(lon, lat)
        hits = [int(k) for k in tree.query(pt) if gs[k].covers(pt)]
        names.append(fs[hits[0]]['properties']['PLN_AREA_N'] if hits else 'UNMAPPED')
    sites[f'area_{year}'] = names


def build_sites():
    s = read('03_carparks_candidate_sites/HDB_carpark_information.csv').sort_values('car_park_no').reset_index(drop=True)
    l = read('03_carparks_candidate_sites/HDB_carpark_lots_snapshot_2026-10-31.csv')
    l = l[l.lot_type.eq('C')]
    assert s.car_park_no.is_unique and l.car_park_no.is_unique
    s = s.merge(l[['car_park_no', 'total_lots']], how='left', validate='one_to_one')
    s['capacity_status'] = np.select([s.total_lots.isna(), s.total_lots.eq(0)], ['missing', 'zero'], default='observed')
    s['imputed'] = s.capacity_status.ne('observed')
    tr = Transformer.from_crs(3414, 4326, always_xy=True)
    s['longitude'], s['latitude'] = tr.transform(s.x_coord.to_numpy(), s.y_coord.to_numpy())
    for y in (2019, 2025):
        geotag(s, y)
    observed = s[~s.imputed]
    s['lots'] = s.total_lots.copy()
    s['imputation_basis'] = 'observed'
    for i in s.index[s.imputed]:
        r = s.loc[i]
        group = observed[(observed.area_2019 == r.area_2019) & (observed.car_park_type == r.car_park_type)]
        basis = 'area/type median'
        if len(group) < 5:
            group = observed[observed.car_park_type == r.car_park_type]
            basis = 'type median'
        if len(group) < 5:
            group, basis = observed, 'national median'
        s.loc[i, 'lots'] = float(group.total_lots.median())
        s.loc[i, 'imputation_basis'] = basis
    s['residential_review_flag'] = s.night_parking.ne('YES')
    # All HDB sites remain in the agreed base scope; night-parking is a review flag.
    assert len(s) == 2273 and s.lots.gt(0).all()
    s.to_csv(INPUTS / 'sites.csv', index=False)
    s[s.imputed | s.residential_review_flag].to_csv(INPUTS / 'site_exceptions.csv', index=False)
    return s


def build_crosswalk(s):
    cp = read('01_ev_charging_supply/LTA_EV_charging_points_Sep2026.csv', dtype={'PostalCode': str, 'Lot No': str, 'Floor No': str, 'Block/House No': str})
    assert cp.evCpId.is_unique and len(cp) == 11489
    cp['PostalCode'] = cp.PostalCode.str.zfill(6)
    tr = Transformer.from_crs(4326, 3414, always_xy=True)
    xy = np.column_stack(tr.transform(cp.longitude.to_numpy(), cp.latitude.to_numpy()))
    tree = cKDTree(s[['x_coord', 'y_coord']])
    parsed = [address_parts(a) for a in s.address]
    excluded = re.compile(r'\b(MALL|PETROL|SHELL|ESSO|CALTEX|SPC|HOSPITAL|HOTEL|CONDOMINIUM|UNIVERSITY|POLYTECHNIC|INDUSTRIAL|BUSINESS|JTC|IKEA|MUSEUM|AIRPORT|SHOPPING|SCHOOL|PLAZA|COMMUNITY CLUB|COMMUNITY CENTRE)\b')
    records = []
    # Explicit address evidence outranks nearest distance. Range/near-street matches stay provisional.
    for i, r in cp.iterrows():
        candidates = tree.query_ball_point(xy[i], 150)
        block, street, building = str(r['Block/House No']).upper(), normal(r['Street Name']), normal(r['Building Name'])
        exact, ranged, near = [], [], []
        for j in candidates:
            blocks, st, ranges = parsed[j]
            if st != street:
                continue
            dist = float(np.linalg.norm(xy[i] - s.loc[j, ['x_coord', 'y_coord']].to_numpy(dtype=float)))
            near.append((dist, j))
            if block in blocks:
                exact.append((dist, j))
            elif block.isdigit() and any(a <= int(block) <= b for a, b in ranges):
                ranged.append((dist, j))
        status, pick, reason = 'unresolved', None, 'No unique exact block/street match within 150 m'
        if excluded.search(building):
            status, reason = 'excluded_non_hdb_evidence', 'Building name indicates non-HDB use; conservative exclusion'
        elif len(exact) == 1:
            status, pick, reason = 'address_supported', exact[0], 'Unique literal block + normalised street + distance <=150 m'
        elif len(exact) > 1:
            reason = 'Multiple exact address candidates; no base assignment'
        elif len(ranged) == 1:
            status, pick, reason = 'provisional_range', ranged[0], 'Block lies in short master-address range; sensitivity only'
        elif len(near) == 1 and near[0][0] <= 100:
            status, pick, reason = 'provisional_street', near[0], 'Unique same-street candidate within 100 m; sensitivity only'
        elif not candidates:
            status, reason = 'outside_candidate_radius', 'No HDB candidate within 150 m'
        records.append({'evCpId': r.evCpId, 'match_status': status,
                        'site_id': s.loc[pick[1], 'car_park_no'] if pick else '',
                        'site_index': pick[1] if pick else np.nan,
                        'match_distance_m': pick[0] if pick else np.nan,
                        'nearby_candidates_50m': len(tree.query_ball_point(xy[i], 50)),
                        'nearby_candidates_100m': len(tree.query_ball_point(xy[i], 100)),
                        'nearby_candidates_150m': len(candidates), 'match_reason': reason})
    c = cp.merge(pd.DataFrame(records), on='evCpId', validate='one_to_one')
    # A registration must not split across sites; unresolved members exclude that registration from base.
    for _, g in c.groupby('EV Charger Registration Code'):
        assigned = g.site_id[g.site_id.ne('')].unique()
        if len(assigned) > 1 or (g.match_status.eq('address_supported').any() and not g.match_status.eq('address_supported').all()):
            c.loc[g.index, 'match_status'] = 'registration_conflict'
            c.loc[g.index, ['site_id', 'site_index']] = ['', np.nan]
    c.to_csv(INPUTS / 'hdb_charger_crosswalk.csv', index=False)
    loc = c.groupby(['longitude', 'latitude', 'match_status', 'site_id'], dropna=False).agg(
        point_count=('evCpId', 'size'), block=('Block/House No', 'first'), street=('Street Name', 'first'),
        building=('Building Name', 'first'), distance_m=('match_distance_m', 'first')).reset_index()
    loc.to_csv(INPUTS / 'location_review_queue.csv', index=False)
    supply = pd.DataFrame({'site_id': s.car_park_no})
    for label, statuses in [('strict', ['address_supported']), ('broad', ['address_supported', 'provisional_range', 'provisional_street'])]:
        subset = c[c.match_status.isin(statuses)].copy()
        subset['power'] = pd.to_numeric(subset['charging Speed'], errors='raise')
        assert subset.power.ge(0).all()
        subset['is_dc'] = ~subset.plugType.eq('Type 2')
        reg = subset.groupby(['site_id', 'EV Charger Registration Code']).agg(
            power_lower=('power', 'max'), power_upper=('power', 'sum'), points=('evCpId', 'size'), dc=('is_dc', 'max')).reset_index()
        reg['scope'] = label
        reg.to_csv(INPUTS / f'registration_capacity_{label}.csv', index=False)
        by = reg.groupby('site_id').agg(kw_lower=('power_lower', 'sum'), kw_upper=('power_upper', 'sum'),
                                      points=('points', 'sum'), dc_registrations=('dc', 'sum'))
        for col in by:
            supply[f'{label}_{col}'] = supply.site_id.map(by[col]).fillna(0)
    # Distinct floor + single lot is an alternative bay estimate; multi-lot/absent labels use points.
    sub = c[c.match_status.eq('address_supported')].copy()
    sub['bay_key'] = [f'{fl}:{lot}' if re.fullmatch(r'\d+[A-Z]?', str(lot)) and pd.notna(fl)
                      else f'unknown:{pid}' for fl, lot, pid in zip(sub['Floor No'], sub['Lot No'], sub.evCpId)]
    bays = sub.groupby('site_id').bay_key.nunique()
    supply['strict_bays_deduplicated'] = supply.site_id.map(bays).fillna(0)
    supply.to_csv(INPUTS / 'existing_supply.csv', index=False)
    return c, supply


def build_demographics():
    frames = []
    for year in (2025, 2026):
        for kind, value in [('population', 'Pop'), ('dwellings', 'HSE')]:
            stem = f'population_dwelling_{year}__respopagesextod{year}.csv' if kind == 'population' else f'dwellings_type_{year}__hsetod{year}.csv'
            d = read('04_demographics_demand_proxies/updates_2026-11-09/' + stem)
            assert value in d, (stem, list(d.columns))
            d = d[d.TOD.str.startswith('HDB ')].copy()
            d[value] = pd.to_numeric(d[value], errors='raise')
            a = d.groupby('PA', as_index=False)[value].sum().rename(columns={value: 'value'})
            a['area'] = a.PA.str.upper()
            a['year'], a['metric'], a['source_file'] = year, kind, stem
            frames.append(a)
    a = pd.concat(frames, ignore_index=True)
    a.to_csv(INPUTS / 'area_demand_weights.csv', index=False)
    return a


def build_stock():
    v = read('02_ev_population_and_registrations/LTA_M09_monthly_vehicle_population_by_fuel.csv')
    v = v[v.category.eq('Cars')].copy()
    v['numeric'] = pd.to_numeric(v.number, errors='coerce')
    v[v.numeric.isna()].to_csv(INPUTS / 'vehicle_numeric_exceptions.csv', index=False)
    ev = v[v.type.eq('Electric')].set_index('month').numeric
    fleet = v.groupby('month').numeric.sum(min_count=1)
    r = read('02_ev_population_and_registrations/LTA_M03_monthly_new_car_registrations_by_make_fuel.csv')
    r['numeric'] = pd.to_numeric(r.number, errors='coerce')
    reg = r[r.fuel_type.eq('Electric')].groupby('month').numeric.sum(min_count=1)
    hist = pd.DataFrame({'ev_stock': ev, 'all_car_stock': fleet, 'new_electric_cars': reg}).sort_index()
    hist['implied_net_exits'] = hist.ev_stock.shift() + hist.new_electric_cars - hist.ev_stock
    hist.to_csv(INPUTS / 'ev_history.csv', index_label='month')
    last = hist.loc['2026-09']
    monthly = hist.loc['2026-01':'2026-09', 'new_electric_cars'].mean()
    rows = [{'scenario': 'current_2026', 'year': 2026, 'stock': last.ev_stock, 'basis': 'Observed September 2026 Cars/Electric', 'monthly_registrations': np.nan, 'exit_fraction': np.nan}]
    for name, factor, exits in [('low', .75, .05), ('base', 1., .02), ('high', 1.25, 0.)]:
        stock = min(last.all_car_stock, last.ev_stock + 15 * monthly * factor * (1 - exits))
        rows.append({'scenario': f'2027_{name}', 'year': 2027, 'stock': stock, 'basis': '15 months of assumed registrations less exits; not fitted forecast', 'monthly_registrations': monthly * factor, 'exit_fraction': exits})
    for name, share in [('low', .25), ('base', .35), ('high', .45)]:
        rows.append({'scenario': f'2030_{name}', 'year': 2030, 'stock': last.all_car_stock * share, 'basis': f'{share:.0%} of frozen Sep-2026 all-car stock; illustrative stress case', 'monthly_registrations': np.nan, 'exit_fraction': np.nan})
    scenarios = pd.DataFrame(rows)
    scenarios.to_csv(INPUTS / 'ev_stock_scenarios.csv', index=False)
    # Historical anchor consistency, not a validation of spatial demand.
    anchor = {'sep2024_electric_cars': float(ev.loc['2024-09']), 'hdb_season_parking_evs': 8800,
              'historical_hdb_ratio': float(8800 / ev.loc['2024-09']),
              'stock_path_kind': 'assumed scenarios; no fitted extrapolation or confidence interval',
              '2026_registration_missing_rows': int(r[(r.month >= '2026-01') & r.fuel_type.eq('Electric')].numeric.isna().sum())}
    (INPUTS / 'stock_calibration.json').write_text(json.dumps(anchor, indent=2))
    return scenarios


def main():
    INPUTS.mkdir(parents=True, exist_ok=True)
    s = build_sites()
    c, supply = build_crosswalk(s)
    build_demographics()
    scenarios = build_stock()
    read('08_costs/cost_parameters.csv').to_csv(INPUTS / 'parameter_evidence.csv', index=False)
    manifest = [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size} for p in sorted(USED)]
    (INPUTS / 'source_hashes.json').write_text(json.dumps(manifest, indent=2))
    audit = {'sites': len(s), 'missing_capacity': int(s.capacity_status.eq('missing').sum()),
             'zero_capacity': int(s.capacity_status.eq('zero').sum()), 'imputed_lots': float(s.loc[s.imputed, 'lots'].sum()),
             'observed_lots': float(s.total_lots.sum()), 'total_lots_after_imputation': float(s.lots.sum()),
             'charger_points': len(c), 'match_counts': c.match_status.value_counts().to_dict(),
             'strict_sites': int(supply.strict_points.gt(0).sum()),
             'strict_dc_registrations': int(supply.strict_dc_registrations.sum()),
             'unmapped_hdb_sites': int(s.area_2019.eq('UNMAPPED').sum())}
    (INPUTS / 'data_audit.json').write_text(json.dumps(audit, indent=2))
    print(json.dumps(audit, indent=2), flush=True)
    print(scenarios.to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
