# Data index — HDB EV charger placement and cost-effectiveness

Updated **9 November 2026**, with execution note added **10 November**. Original collection was downloaded 31 October; new source snapshots have their own timestamps and hashes in [source_manifest_2026-11-09.csv](09_research_audit/source_manifest_2026-11-09.csv). Scope: HDB placement, slow base model, fast extension; no carbon analysis. The frozen research files are preserved. Completed optimisation outputs are separate in [../code/outputs/](../code/outputs/); see the [execution summary](../EXECUTION_SUMMARY.md).

Start with [gap_review.md](09_research_audit/gap_review.md), [file_inventory.csv](09_research_audit/file_inventory.csv) and [the working plan](../plan.md). Inventory includes schema, rows, null counts, duplicate rows, ranges where available, sizes and hashes. Raw files are retained with derived tables separate. Official open data should be cited to its agency; vendor material is labelled commercial evidence.

## 01_ev_charging_supply

`LTA_EV_charging_points_Sep2026.csv` — [LTA DataMall static data](https://datamall.lta.gov.sg/content/datamall/en/static-data.html), September 2026 register; 11,489 unique `evCpId` rows and 9,279 registration codes. Fields include operator, connector, power, address, floor/lot, public accessibility, WGS84 coordinates and registration date. The public-access column has a source typo (`Yesblicly`). Type of parking lot is entirely empty.

**Counting correction:** `No. of Charging Outlets` repeats the registration's outlet count on every point row. Sum once per registration: **11,489**, not 17,011. Do not multiply point ratings by this field. Multiple connectors may share cabinet power; simultaneous supply is unverified. Public access does not identify HDB ownership. The file cannot by itself identify site utilisation, all private chargers, actual commissioning dates or site electrical capacity.

DataMall live availability requires an account key and repeated observation; no account/key requested. Availability is not delivered kWh or EV ownership.

## 02_ev_population_and_registrations

| Files | Role |
|---|---|
| `LTA_M09_monthly_vehicle_population_by_fuel.csv` | Core national stock series through Sep 2026; filter Cars/Electric, separately define total-car denominator. |
| `LTA_M03_monthly_new_car_registrations_by_make_fuel.csv` | National registration flow and adoption scenarios; sales share is not fleet share. |
| `LTA_annual_private_vehicle_mileage.csv` | Cars average 16,200 km/year in 2025; not EV-only or HDB-only mileage. |
| `LTA_MVP01-4_…`, `LTA_MVP01-6_…`, both `LTA_MVP02-2_…`, `xlsx_originals/` | Annual/source-format checks; not additional independent demand. |
| `LTA_M06_…`, `SingStat_monthly_motor_vehicle_population_by_type.csv` | National vehicle denominator checks. |
| Both `LTA_M11_COE_…`, `LTA_monthly_taxi_fleet.csv`, `NEA_green_vehicles.csv` | Retained background, not core model inputs. “Green” is not synonymous with battery electric. |

Primary sources: [LTA vehicle statistics](https://www.lta.gov.sg/content/ltagov/en/who_we_are/statistics_and_publications/statistics.html), DataMall and SingStat. Local Sep 2026 electric-car stock is 74,887; Sep 2024 is 21,796. These are dated inputs, not a claim of live totals. No carpark-level EV ownership was obtained.

## 03_carparks_candidate_sites

| File | Inspection and use |
|---|---|
| `HDB_carpark_information.csv` | [HDB open dataset](https://data.gov.sg/datasets/d_23f946fa557947f93a8043bbef41dd09/view); 2,273 unique carpark IDs, address/type/decks/parking fields, SVY21 coordinates. Core candidates. |
| `HDB_carpark_lots_snapshot_2026-10-31.csv` | 2,428 records across lot types; select C. 2,007 carpark car-lot records, 1,997 match master, 276 missing in master join, 2 matched zeros. Matched capacity 706,663; all snapshot capacity 708,242 includes 10 unmatched IDs. `lots_available` is not average occupancy. |
| `HDB_carpark_outlines.geojson` | 30,748 features, no `car_park_no`; supplementary geometry, not one polygon per site. |
| `URA_parking_places_capacity.geojson`, `JTC_carpark_information.csv`, `NParks_carpark_lots.geojson`, `LTA_ParkingStandardsZone_Sep2026_shp/` | Retained original collection; outside HDB placement scope. |

Convert **EPSG:3414 x/y → EPSG:4326 lon/lat** before joining to WGS84 register/boundaries. Review both missing lots and eligibility; do not silently drop sites. An absent charger does not prove power constraints.

## 04_demographics_demand_proxies

Original five `Census2020_*` tables cover households by dwelling, car-only commuting, income, workplace and subzone population by dwelling. Geographic rows include totals/grouped areas and different levels; strip or handle them before aggregation. Use residential data as alternative demand weights, income descriptively, workplace outside base. `HDB_property_information_blocks.csv` has 13,392 rows, dwelling units/town codes/completion year, but no coordinates; it cannot directly geocode demand nodes.

**New `updates_2026-11-09/`:** downloaded from [SingStat geographic-distribution catalog](https://www.singstat.gov.sg/find-data/explore-data-themes/population/geographic-distribution/latest-news-data).

| File family | Contents / use |
|---|---|
| `population_dwelling_2024/2025/2026.zip` plus extracted `__respopagesextod*.csv` and `__Notes_*.csv` | 100,928 rows/year; 55 areas, 332 area/subzone pairs. Columns PA, SZ, AG, Sex, TOD, Pop, Time. Filter four HDB flat categories; sum mutually exclusive cells. |
| `population_floor_area_2020_2024.csv` | 315,400 rows, annual population by area/subzone/age/sex/floor area. All-dwelling trend, not HDB-specific. 2024 overlaps the other population file; do not add both. |
| `dwellings_type_2025/2026.zip` plus extracted `__hsetod*.csv` and notes | 2,656 rows/year; HDB stock check and alternative weights. Dwellings are not people or occupied households. |
| `dwellings_floor_area_2020_2024.csv` | 8,300 rows; all-dwelling housing-stock trend. Floor area does not establish HDB tenure. |
| `GHS2025_car_only_commuting_by_HDB_dwelling.csv` | Eight manually extracted values: 2020/2025 car-only commuting percentages for four HDB flat groups, official report table 9.1, printed p. 74. Not a vehicle ownership rate or complete GHS workbook. |
| `SingStat_geographic_distribution.html/.txt` | Local catalog snapshot and download context. |
| `GHS2025_transport_download.html/.txt` | **Only a JavaScript app shell. Detailed workbook not obtained.** Link retained for follow-up, excluded from model data. |

Source notes: **2025 MP2019; 2026 MP2025**. Cells rounded to nearest 10; sums are approximate. Keep source/vintage in every summary. The 2026 layer cannot be naively joined to old subzone growth just because names match.

## 05_geospatial_boundaries

`URA_MP2019_planning_area_boundary.geojson` (55 areas), `URA_MP2019_subzone_boundary.geojson` (332 subzones), `URA_MP2025_planning_area_boundary.geojson` (55 areas). MP2019 supports 2025 base demographic weights; MP2025 supports the separate 2026 check. No MP2025 subzone crosswalk has been collected. HDB town and planning area are not interchangeable.

## 06_reports_and_policy

Original MOT parliamentary compilation, LTA roadmap, 2022 HDB tender release, 2024 deployment release and driver guide provide dated policy/context. News/Wikipedia remain background, not primary model evidence. Key interpretation: the national 40,000-public-point goal is not an HDB quota; tender quantities are not space maxima; reported peak utilisation is not a full-day energy factor.

New `updates_2026-11-09/` contains:

- `SingStat_GHS2025.pdf` — [full official survey report](https://www.singstat.gov.sg/files/1559c94a-efc1-4262-84fd-042c9bd96e68.pdf), geography and transport chapters; catalog snapshot also saved.
- `SingStat_Population_Trends_2026.pdf` — [full official annual report](https://www.singstat.gov.sg/files/5645f043-4bb7-4181-a3a8-c36da5cd1b12.pdf), definitions/latest population context.
- `MOT_2026-09-10_utilisation.html/.txt` — [public-carpark usage evidence](https://www.mot.gov.sg/news-resources/newsroom/utilisation-rates-of-ev-charging-points-at-petrol-kiosks-relative-to-public-car-parks/); about five hours/day in Jan–Aug 2026, not HDB-specific or kWh delivery.
- `MOT_2024-11-11_EV_season_parking.html/.txt` — [historical HDB calibration](https://www.mot.gov.sg/news-resources/newsroom/written-reply-to-parliamentary-question-on-statistics-of-evs-registered-for-season-parking-in-hdb-carparks-and-increasing-charging-lots-for-carparks-with-more-ev-season-parkings-registered/), about 8,800 EVs at Sep 2024. Category and timing limitations apply.

## 07_derived

| File | Status |
|---|---|
| `charging_points_with_planning_area.csv`, `planning_area_summary.csv` | Legacy **all-public**, MP2019/Census2020 aggregates; outlet overcount fixed. Area totals contain 11,487 points; two unmapped points are listed in the audit exceptions. `total_kw` is summed point ratings, not verified shared capacity. Do not use as HDB siting results. |
| `hdb_sites_capacity_review.csv` | All HDB sites with observed capacity status, converted coordinates and both planning-area vintages; no imputation performed. |
| `population_dwelling_subzone_review.csv` | 6,640 aggregate rows, with metric, scope, source and geography vintage. |
| `population_dwelling_planning_area_review.csv` | 1,100 area aggregate rows; overlapping source series remain separate. |

The review tables are inputs for human checking, not fitted demand or recommendations.

## 08_costs

Active `cost_parameters.csv` has labelled scenario bounds, units, sources and cautions; original table is archived under `project/archive/planning/2026-10-31/`. `vendor_cost_evidence_2026-11-09.csv` separates actual posted components from installed-cost assumptions.

New snapshots: [Electric Pte Ltd hardware/maintenance](https://www.electric.com.sg/ev-charger/), [Go Electric standard installation](https://goelectric.com.sg/Product/Accessories/Standard-Installation-of-EV-Charger), and US DOE AFDC [maintenance](https://afdc.energy.gov/fuels/electricity-infrastructure-maintenance-and-operation) / [installation](https://afdc.energy.gov/fuels/electricity-infrastructure-development). Local posted prices are not HDB site quotes; international benchmarks are not Singapore observations. S$6,500 installed AC base, site upgrades, lifetime and discount rate remain assumptions.

Retained ICCT 2019, LTA grant PDFs, official price/tariff notes and secondary guides are background/cross-checks. No condo or heavy-vehicle grants deducted from HDB base cost. No carbon/fuel inputs are required. Keep price year, GST, unit (cabinet vs connector), ordinary installation and grid upgrade distinct; avoid double charging installation costs.

## 09_research_audit and 10_methodology

Audit folder: meeting decisions with timestamps, gap review, source manifest, full file inventory, computed metrics, missing/zero capacity queue, charger registration unit audit, and nearest-HDB location review candidates. The 543 locations with multiple HDB sites within 100 m need disambiguation; proximity is not HDB confirmation.

Methodology folder: official Gurobi facility and multiobjective documentation plus related author-hosted EV location manuscript. [Reference notes](10_methodology/README.md) explain applicability and the blocked Church–ReVelle original full-text download. No fabricated bibliography/full-text claim.

## Reproduce this research pass

From the repository root, install `project/requirements-research.txt` in a virtual environment, then run:

```bash
python3 project/scripts/audit_research_data.py
python3 project/scripts/build_planning_area_summary.py
```

Optional re-download: `python3 project/scripts/fetch_research_sources.py` reuses existing files; `--refresh` replaces them and updates provenance. Refresh deliberately, not during a frozen model run. Audit after any changed inputs. The download tool logs failed/landing-page-only sources rather than pretending they are datasets. Source PDFs, raw ZIPs and their notes are preserved.
