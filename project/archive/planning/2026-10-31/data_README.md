# Data index — EV Charging Station Optimisation (Singapore)

All files downloaded 2026-10-31. Sources are official Singapore government open data unless marked otherwise.
Open Data Licence (data.gov.sg / LTA DataMall) — cite the agency in the report.

Coordinate systems: LTA charger file and URA boundaries use **WGS84 lat/lon**. HDB/JTC carpark files use **SVY21 (EPSG:3414) x/y in metres** — convert before joining.

---

## 01_ev_charging_supply — where the chargers are today

| File | Source | Coverage | What it is |
|---|---|---|---|
| `LTA_EV_charging_points_Sep2026.csv` | [LTA DataMall static data](https://datamall.lta.gov.sg/content/datamall/en/static-data.html) → "EV Charging Points" (`EVChargingPoints.zip`) | Registrations Feb 2024 – 30 Sep 2026 | **The main dataset from the meeting.** 11,489 rows = one per charging point (`evCpId`). 9,279 charger registration codes, 17,011 outlets, ~2,880 unique locations. Columns: operator, outlets, plug type (Type 2 / CCS2 / CHAdeMO), charging speed kW (3.7–480), postal code, block, street, building, floor, lot, public-access flag, lat/lon, registration date. **Public chargers only** (all rows `Yes`) — the ~23,000 private chargers (condos, landed homes, offices) in LTA's 34,700 total are not in here. Column "Is the charger Yesblicly accessible?" is a typo in the source. "Type of Parking Lot" is empty. |

Not downloaded: LTA DataMall **EV Charging Points API** (`EVCBatch`, live availability) — needs a free DataMall account key ([request here](https://datamall.lta.gov.sg/content/datamall/en/request-for-api.html)). OpenStreetMap charging stations — Overpass servers were overloaded; can retry later.

## 02_ev_population_and_registrations — how many EVs, how fast it's growing

| File | Source | Coverage | What it is |
|---|---|---|---|
| `LTA_M09_monthly_vehicle_population_by_fuel.csv` | LTA DataMall | Jan 2016 – Sep 2026, monthly | **Key file.** Vehicle population by category (Cars, Taxis, Buses, Goods, Motorcycles) × fuel (Petrol, Diesel, Electric, Petrol-Electric, plug-in hybrids…). |
| `LTA_M03_monthly_new_car_registrations_by_make_fuel.csv` | LTA DataMall | Jan 2016 – Sep 2026, monthly | New car registrations by make × fuel type × body type. EV split starts 2022 (before that EVs are inside "Others"). |
| `LTA_MVP01-4_annual_vehicle_population_by_fuel.csv` | LTA DataMall | 2006 – 2025, annual | Annual version of M09. |
| `LTA_MVP01-6_annual_car_population_by_make_fuel.csv` | LTA DataMall | 2005 – 2025, annual | Car population by make × fuel. |
| `LTA_MVP02-2_annual_new_car_registrations_by_make[_fuel_type].csv` | LTA DataMall | 2005/2015 – 2025 | Annual new registrations by make (and by fuel/body type). |
| `LTA_M06_monthly_vehicle_population_by_type.csv` | LTA DataMall | 2012 – 2026, monthly | Total vehicle population by vehicle type (cars, rental, taxis, PHV…). |
| `LTA_annual_private_vehicle_mileage.csv` | LTA DataMall | 2005 – 2025 | Average annual km per vehicle type → converts EV count into kWh demand. |
| `LTA_monthly_taxi_fleet.csv` | LTA DataMall | 2005 – Dec 2025 | Taxi fleet by company (high-mileage segment that needs fast charging). |
| `LTA_M11_COE_bidding_results.csv`, `LTA_M11_COE_prevailing_quota_premium.csv` | LTA DataMall | 2010 – 2026 | COE prices (affects car ownership / EV adoption scenarios). |
| `SingStat_monthly_motor_vehicle_population_by_type.csv` | [data.gov.sg](https://data.gov.sg/datasets/d_206838bdc92c07ab495af49475563da5/view) | to Aug 2026 | SingStat cross-check of vehicle totals (wide format). |
| `NEA_green_vehicles.csv` | data.gov.sg | 2003 – 2014 | Historical green vehicle count (background only). |
| `xlsx_originals/` | LTA DataMall | — | Formatted Excel versions of the LTA tables above (same data). |

**Headline numbers (from M09/M03):** electric cars 9,998 (Sep 2023) → 21,796 (Sep 2024) → 41,732 (Sep 2025) → **74,887 (Sep 2026) ≈ 11.5% of 651k cars**. All-vehicle EVs ≈ 85,000 (Sep 2026). EV share of new car registrations: 6.9% (2022), 18.1% (2023), 33.6% (2024), 45.0% (2025), **63.1% (Jan–Sep 2026)**. Top EV makes 2025–26: BYD, Tesla, GAC, MG, BMW.

**No dataset gives EV ownership by location** (town / planning area / postal code). Only national totals exist publicly → see demand proxies in 04.

## 03_carparks_candidate_sites — where new chargers could go

| File | Source | What it is |
|---|---|---|
| `HDB_carpark_information.csv` | [data.gov.sg](https://data.gov.sg/datasets/d_23f946fa557947f93a8043bbef41dd09/view) | 2,273 HDB carparks: ID, address, **SVY21 x/y**, type (multi-storey/surface/basement), decks, night parking, gantry height. Natural **candidate-site list**. |
| `HDB_carpark_lots_snapshot_2026-10-31.csv` | data.gov.sg carpark-availability API | Snapshot (31 Oct 2026, 21:42) of total & available lots per HDB carpark by lot type (C = car, Y = motorcycle, H = heavy). ~2,000 carparks, 708k car lots. Use `total_lots` as **capacity**; join on `car_park_no`. |
| `HDB_carpark_outlines.geojson` (44 MB) | data.gov.sg | Polygon outlines of HDB carparks. |
| `URA_parking_places_capacity.geojson` | data.gov.sg | URA public carparks with lot capacity. |
| `NParks_carpark_lots.geojson` | data.gov.sg | Carparks in parks (destination charging candidates). |
| `JTC_carpark_information.csv` | data.gov.sg | 28 JTC industrial carparks (SVY21). |
| `LTA_ParkingStandardsZone_Sep2026_shp/` | LTA DataMall | Shapefile of LTA parking standards zones (central/transit-rich areas have lower parking provision). |

## 04_demographics_demand_proxies — who might need charging, where

| File | Source | What it is |
|---|---|---|
| `Census2020_households_by_planning_area_dwelling_type.csv` | data.gov.sg (SingStat) | Households per planning area by HDB flat size / condo / landed. HDB residents rely on public chargers; landed homes can charge at home. |
| `Census2020_employed_residents_by_planning_area_mode_of_transport_to_work.csv` | data.gov.sg (SingStat) | **Car-only commuters per planning area** — best available proxy for car ownership by area. |
| `Census2020_households_by_planning_area_household_income.csv` | data.gov.sg (SingStat) | Household income bands per planning area (EV adoption correlates with income). |
| `Census2020_population_by_planning_area_subzone_dwelling_type.csv` | data.gov.sg (SingStat) | Population at subzone level by dwelling type (finer demand nodes). |
| `Census2020_employed_residents_by_planning_area_of_workplace.csv` | data.gov.sg (SingStat) | Workers by planning area of **workplace** (daytime / destination charging demand). |
| `HDB_property_information_blocks.csv` | data.gov.sg | Every HDB block: town code, year completed, dwelling units by flat type, whether it has a multi-storey carpark. Use to compute dwelling units per town / build newer-town demand. |

Census 2020 is the latest small-area census. It **under-counts new towns** (Tengah, parts of Punggol/Sengkang/Bidadari). SingStat publishes June 2025 *population by planning area/subzone* on its website ([Population Trends / geographic distribution](https://www.singstat.gov.sg/find-data/search-by-theme/population/geographic-distribution)) — download manually if needed (automated download failed).

## 05_geospatial_boundaries

| File | Source | What it is |
|---|---|---|
| `URA_MP2019_planning_area_boundary.geojson` | data.gov.sg (URA) | 55 planning areas (matches Census 2020 names). |
| `URA_MP2019_subzone_boundary.geojson` | data.gov.sg (URA) | 332 subzones. |
| `URA_MP2025_planning_area_boundary.geojson` | data.gov.sg (URA) | Latest Master Plan 2025 planning areas. |

## 06_reports_and_policy — context, targets, utilisation figures

| File | What it is |
|---|---|
| `MOT_parliamentary_replies_EV_charging_2024-2026.md` | 9 parliamentary replies: utilisation rates (HDB avg ~20%, peak-3h 36%, Tengah 61%, Bidadari 40%), 139 HDB carparks without chargers, 60k target split, siting criteria, fast hub per town by 2027, 8,800 EVs with HDB season parking (Sep 2024). |
| `news_2026-09_LTA_34700_chargers_82100_EVs_AsiaOne.txt` | World EV Day 2026: 34,700 charging points, 82,100 EVs (Aug 2026), 63% of new cars, EEAI ends 1 Jan 2027. |
| `news_2026-05_30500_chargers_BTO_deployment_Yahoo.txt` | Straits Times via Yahoo: 30,500 points (Mar 2026), BTO charger timing, Tengah, 139 carparks without chargers. |
| `news_2026-01_EVs_45pct_of_2025_registrations.txt` | 2025 full-year EV share 45%. |
| `LTA_our_EV_roadmap.txt` | LTA EV Roadmap page (incentives, HDB EV-ready by 2025, fast-charging plans). |
| `LTA_2024-08_expanding_EV_charging_infra.txt` | LTA Aug 2024: 13,800 points, ~1,000 HDB carparks equipped. |
| `LTA_2022-11_HDB_carpark_tender_12000_points.txt` | LTA Nov 2022: large-scale tender, ~2,000 HDB carparks, 12,000 points by 2025. |
| `LTA_Electric_Vehicle_Guide_for_Drivers.pdf` | LTA driver guide (charger types, speeds). |
| `Wikipedia_plugin_EVs_in_Singapore.txt` | Overview / timeline (secondary source — verify before citing). |

## 08_costs — capex, prices, grants (for the objective / budget)

| File | What it is |
|---|---|
| `cost_parameters.csv` | **Model-ready table** of low/base/high values with unit, source, and `source_type` for each parameter: capex per point (7 kW AC, 22 kW AC, 50 kW DC, 100–150 kW DC), site grid-upgrade cost, charging prices, electricity cost, margin, utilisation, energy per point per day, grants, FX, lifetime, discount rate. |
| `sources/official_SG_cost_and_price_sources.md` | Verbatim official figures: MOT median price S$0.66/kWh (HDB) and S$0.74 (private), SP tariff Q4 2026, Tengah fast hub (8 × 100 kW DC + 6 × 7.4 kW AC), EVe hub contracts, grant rules. |
| `sources/ICCT_2019_EV_charging_infrastructure_costs_US_metros.pdf` | ICCT working paper: per-charger hardware (Table 2) and installation by chargers per site (Tables 3–4). **Main basis for capex.** |
| `sources/LTA_ECCG_Guidelines_and_FAQs.pdf`, `sources/LTA_charger_grants_page.txt` | LTA grant rules (ECCG condo chargers; EHVCG heavy-vehicle chargers capped at S$30k). |
| `sources/Motorist_2026_SG_charging_price_index.txt`, `sources/Kakilist_2026_SG_charger_cost_guide.txt` | SG secondary sources: operator AC/DC prices (Sep 2026) and home install costs. |
| `sources/LTA_2022_EV_ecosystem_feedback_annex.pdf` | LTA 2022 consultation annex (context only; no cost figures). |

**Read `source_type` before using a number.** Singapore has **not published** the capital cost of a public charging point or of carpark electrical upgrades. Capex is therefore based on ICCT (2019 USD × 1.28) and checked against SG secondary figures. Grid upgrade, charger lifetime and discount rate are **team assumptions** and must go into the sensitivity analysis. NREL's 2030 network report couldn't be downloaded (site unreachable from here).

## 07_derived — built by `../scripts/build_planning_area_summary.py`

| File | What it is |
|---|---|
| `charging_points_with_planning_area.csv` | LTA charger file + planning area, region, subzone (point-in-polygon on MP2019), `is_fast` (≥43 kW). |
| `planning_area_summary.csv` | Per planning area: charging points, chargers, outlets, fast points, locations, total kW, Census 2020 households (HDB/condo/landed), car-only commuters, high-income households, points per 1,000 households / car commuters. |

Re-run: `python scripts/build_planning_area_summary.py` from `project/` (needs pandas + shapely).
