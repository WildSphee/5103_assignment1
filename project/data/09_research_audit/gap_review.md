# Data and methodology gap review — 9 November 2026

This is a research and readiness audit, not an optimisation result. `file_inventory.csv` profiles the locally available tables, spatial files, workbooks and source documents; `audit_metrics.json` and review CSVs can be regenerated with `scripts/audit_research_data.py`. The website's “data tab” is interpreted as this repository's existing `project/data/` collection; no separate application is present.

## Findings that change the old plan

| Finding | Evidence and action |
|---|---|
| HDB scope is not implemented in the old planning-area summary | All 11,489 public register points were aggregated, including malls and commercial premises. Do not label that ratio HDB supply or use it to declare an estate underserved. Rebuild after an audited HDB match. |
| Repeated outlet count | 9,279 registration codes, 11,489 unique `evCpId`s. Every registration's row count equals its stated outlet count. Summing the repeated outlet column gives 17,011; deduplicating by registration gives 11,489. Use unique point IDs; do not multiply point power by the outlet column. |
| Two public charger points do not map to an MP2019 planning area | The legacy area summary accounts for 11,487 points/outlets plus 2 unmapped points retained in `public_chargers_without_planning_area.csv`. The register total is still 11,489; do not silently equate grouped totals with the complete register. |
| Shared power remains unknown | 2,081 registrations have multiple point rows. Port count does not prove simultaneous cabinet output. Bound capacity using the largest point rating per registration versus sum of point ratings, unless a charger specification establishes the shared limit. |
| Charger-to-carpark matches are ambiguous | 2,884 exact coordinate locations; 1,958 within 100 m of an HDB site, of which 543 have multiple HDB sites nearby. `charger_location_hdb_match_candidates.csv` is a review queue, NOT confirmed HDB membership. Use address/block/street evidence and manual review; nearest distance alone can assign mall or petrol-station chargers to HDB. |
| Capacity coverage incomplete | 2,273 HDB sites; 1,997 match a car-lot record, 276 missing, 2 matched with zero. Matched capacity totals 706,663 car lots. All snapshot car lots sum to 708,242, including 10 IDs outside the HDB master. Do not quietly drop missing sites or regard all 708,242 lots as matched HDB capacity. |
| Lots are not owned cars | At 85% occupancy, 706,663 lots imply about 600,664 parked cars before EV share, an implausibly large HDB allocation relative to the national passenger-car fleet. Normalise spatial lot weights to a separately calibrated HDB EV total. A one-time `lots_available` snapshot is not average occupancy or charger utilisation. |
| Geometry is not a site crosswalk | HDB outline GeoJSON has 30,748 features and no `car_park_no`. It is not a simple one-polygon-per-carpark table; use only supplementary visual evidence after interpreting the feature schema. HDB block table has no coordinates/postcodes; block-to-site geocoding is extra work. |
| Current demographics now available | Downloaded population by dwelling type for 2024/2025/2026, annual population by floor area 2020–2024, dwelling stock 2025/2026 and dwelling stock by floor area 2020–2024. Population and dwellings are different units. Four HDB flat categories define the HDB subset; HUDC and other dwelling types are excluded. |
| Geography break | Source notes say June 2025 uses MP2019; June 2026 uses MP2025. All existing carpark points retain the same planning-area label across the two supplied polygon sets, but that does not establish comparable subzone boundaries. Base spatial proxies use 2025/MP2019; 2026 is a separately mapped robustness check. |
| Growth is not EV adoption | Local demographic growth changes spatial weights; LTA electric-car stock and registrations inform national EV scenarios. Do not multiply population growth into both the total EV forecast and local allocation. New areas with a zero 2020 base cannot use CAGR. |
| Capacity ≠ observed utilisation | 36% is utilisation during a three-hour peak, not a safe 24-hour charging duty factor; 61% is a local peak, not a national design parameter. Five hours/day from September 2026 MOT evidence covers public carparks, not HDB alone. Taper, shared power, downtime and overnight occupation matter. |
| Policy is not a carpark constraint | 40,000 public-carpark points is not an HDB-only requirement. Tender deployment quantities (3–12 points) are not physical maximum capacities. A hub of 6+ points must be co-located: six scattered town points do not constitute a hub. No-charger status does not identify the 139 reported carparks or prove zero spare power. |
| Cost-benefit accounting needs a single perspective | Measure extra service/access per infrastructure dollar. Operator receipts are not social benefits; electricity and charging prices need consistent GST treatment. Retail household tariff is not an operator supply contract. Do not add revenue, avoided petrol expenditure and customer benefits together. |

## What was obtained

See `source_manifest_2026-11-09.csv` for exact URLs, timestamps, status, bytes and SHA-256. Raw ZIPs, extracted CSVs, notes, PDF reports and source snapshots are saved in their subject folders.

- **SingStat:** GHS 2025 full report and Population Trends 2026; downloadable small-area population and housing series. GHS chapter 9/table 9.1 distinguishes car-only commuting from taxi/private-hire rides and includes 2020/2025 comparisons. It is a proxy, not a vehicle ownership census.
- **Singapore commercial evidence:** Electric Pte Ltd hardware and maintenance schedule; Go Electric standard-installation scope and advertised price. These improve component-level cost evidence, but neither is a public HDB site quotation.
- **MOT:** September 2026 public-carpark utilisation reply and direct verification of the November 2024 HDB season-parking reply.
- **Methodology:** Gurobi facility-location example, hierarchical-objective documentation, and an author-hosted EV facility-location manuscript. The latter concerns car sharing, so its trip/battery model is not copied into the HDB base model.
- **US DOE AFDC:** installation and maintenance references for external plausibility checks; not Singapore cost estimates.

## Remaining gaps and workable fallback

| Missing input | Where it could be obtained | Plan now / release condition |
|---|---|---|
| Site EV counts, sessions and delivered kWh | HDB/LTA/EVe or charging operators; DataMall availability API with account key | Use normalised lot weights and scenario totals. Historical 8,800 HDB season-parking EVs is a weak calibration anchor, not current counts. A live availability feed alone does not identify kWh or resident ownership. No account requested or third party contacted. |
| Spare electrical capacity and upgrade quote | EVe/HDB electrical survey, licensed electrical worker or operator | Explicit low/base/high headroom scenarios. No engineering-feasibility claim. Missing grid data must not be inferred from charger absence. |
| Audited HDB supply and sharing limits | Register addresses plus operator maps/specifications/site verification | Review queue supplied. Conservative/optimistic matching and power bounds until verified. All unresolved points remain visibly unresolved. |
| Missing car-lot capacities | HDB capacity records or further dated availability snapshots | Retain the 276 sites. Compare exclusion with labelled within-area/type median imputation; publish demand and site coverage under each. Zero-capacity records need investigation. |
| GHS 2025 detailed transport workbook | GHS report catalog → Transport → Table Builder bulk-download link | Full PDF obtained; bulk route returned 403 in one attempt and only a JavaScript app shell in another. **Workbook not obtained.** Use 2020 area tables as a sensitivity proxy and extract limited verified 2025 PDF statistics. |
| Actual HDB installed/O&M/network/concession cost | Public tender schedules/award cost breakdowns, comparable public procurement, written commercial site quote | No usable HDB cost breakdown found in inspected sources. Use transparent component scenarios, preserving vendor limitations; no unexplained markup or grant subtraction. |
| Original Church–ReVelle full text | DOI / publisher through university library | Publisher download returned 403. Bibliographic metadata and DOI located; full text not downloaded. Gurobi example and downloaded related research support reviewable formulation meanwhile. |
| Agreed budget, horizon and service target | Team modelling choices | Proposed 2027 base, 2030 outlook; illustrative budget frontier and 80/90/95% service targets. These are proposals, not meeting commitments or government appropriations. |
| Reviewer spellings and integration owner | Team notes/group confirmation | Preserve provisional names; do not infer speaker identities. No messages sent. |

## Freeze and provenance

Existing vehicle/charger/lot inputs are retained at September/October 2026 vintages for reproducibility; no claim that they are the latest live data. Downloaded demographic source dates and geography vintages are separate from download date. All counts derived from rounded population cells are approximate. Overlapping 2024 population files are alternatives, never additive. The source manifest records one inaccessible publisher item and the GHS landing page separately from usable datasets. No optimisation has been run and no locations have been recommended yet.
