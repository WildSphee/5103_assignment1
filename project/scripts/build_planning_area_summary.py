"""Aggregate LTA public EV charging points to URA planning areas and join Census 2020 demand proxies.

Usage: python scripts/build_planning_area_summary.py   (run from project/)
Requires: pandas, shapely
Outputs:
  data/07_derived/charging_points_with_planning_area.csv  - every charging point tagged with planning area / subzone
  data/07_derived/planning_area_summary.csv                - one row per planning area
"""
import json
from pathlib import Path

import pandas as pd
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

DATA = Path(__file__).resolve().parent.parent / "data"
OUT = DATA / "07_derived"
OUT.mkdir(exist_ok=True)

FAST_KW = 43  # >= 43 kW treated as fast (DC / high-power AC); slow = 3.7-22 kW AC


def load_polygons(path, name_keys):
    feats = json.loads(path.read_text())["features"]
    geoms = [shape(f["geometry"]) for f in feats]
    attrs = [{k: f["properties"][k] for k in name_keys} for f in feats]
    return geoms, attrs


def tag(points, geoms, attrs):
    tree = STRtree(geoms)
    out = []
    for p in points:
        hit = next((i for i in tree.query(p) if geoms[i].covers(p)), None)
        out.append(attrs[hit] if hit is not None else {k: None for k in attrs[0]})
    return pd.DataFrame(out)


cp = pd.read_csv(DATA / "01_ev_charging_supply/LTA_EV_charging_points_Sep2026.csv", encoding="utf-8-sig")
cp = cp.rename(columns={"Is the charger Yesblicly accessible?": "is_public", "charging Speed": "charging_speed_kw"})
pts = [Point(xy) for xy in zip(cp.longitude, cp.latitude)]

pa_geoms, pa_attrs = load_polygons(DATA / "05_geospatial_boundaries/URA_MP2019_planning_area_boundary.geojson",
                                   ["PLN_AREA_N", "REGION_N"])
sz_geoms, sz_attrs = load_polygons(DATA / "05_geospatial_boundaries/URA_MP2019_subzone_boundary.geojson",
                                   ["SUBZONE_N"])
cp = pd.concat([cp, tag(pts, pa_geoms, pa_attrs), tag(pts, sz_geoms, sz_attrs)], axis=1)
cp["is_fast"] = cp.charging_speed_kw >= FAST_KW
cp["location_key"] = cp.latitude.round(5).astype(str) + "," + cp.longitude.round(5).astype(str)
cp.to_csv(OUT / "charging_points_with_planning_area.csv", index=False)

pa = cp.groupby(["PLN_AREA_N", "REGION_N"]).agg(
    charging_points=("evCpId", "count"),
    chargers=("EV Charger Registration Code", "nunique"),
    outlets=("No. of Charging Outlets", "sum"),
    fast_points=("is_fast", "sum"),
    locations=("location_key", "nunique"),
    total_kw=("charging_speed_kw", "sum"),
).reset_index()

# Census 2020 demand proxies (planning-area names are Title Case there)
def census(fname, cols):
    df = pd.read_csv(DATA / "04_demographics_demand_proxies" / fname)
    df = df[df.Number != "Total"].copy()
    df["PLN_AREA_N"] = df.Number.str.replace(" - Total", "", regex=False).str.upper().str.strip()
    return df[["PLN_AREA_N"] + list(cols)].rename(columns=cols)

hh = census("Census2020_households_by_planning_area_dwelling_type.csv",
            {"Total": "households_2020", "HDBDwellings_Total": "hdb_households_2020",
             "CondominiumsandOtherApartments": "condo_households_2020", "LandedProperties": "landed_households_2020"})
mode = census("Census2020_employed_residents_by_planning_area_mode_of_transport_to_work.csv",
              {"Total": "employed_residents_2020", "CarOnly": "car_only_commuters_2020"})
inc = census("Census2020_households_by_planning_area_household_income.csv",
             {"20_000andOver": "households_income_20k_plus_2020"})

# Planning-area landmass from URA (m^2) for density
area = pd.DataFrame([{"PLN_AREA_N": f["properties"]["PLN_AREA_N"], "area_km2": f["properties"]["SHAPE.AREA"] / 1e6}
                     for f in json.loads((DATA / "05_geospatial_boundaries/URA_MP2019_planning_area_boundary.geojson").read_text())["features"]])

summary = (area.merge(pa, on="PLN_AREA_N", how="left")
           .merge(hh, on="PLN_AREA_N", how="left")
           .merge(mode, on="PLN_AREA_N", how="left")
           .merge(inc, on="PLN_AREA_N", how="left"))
num = ["charging_points", "chargers", "outlets", "fast_points", "locations", "total_kw"]
summary[num] = summary[num].fillna(0)
summary["points_per_1000_households"] = (1000 * summary.charging_points / summary.households_2020).round(2)
summary["points_per_1000_car_commuters"] = (1000 * summary.charging_points / summary.car_only_commuters_2020).round(2)
summary = summary.sort_values("charging_points", ascending=False)
summary.to_csv(OUT / "planning_area_summary.csv", index=False)

print(f"{len(cp)} points, untagged: {cp.PLN_AREA_N.isna().sum()}")
print(summary.head(15).to_string(index=False))
