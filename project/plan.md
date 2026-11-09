# Working analysis plan — HDB charger placement and cost-effectiveness

Updated 9 November 2026 from the full meeting transcript. Detailed internal working document; concise report outline is in `report_skeleton.md`. This supersedes the 31 October plan, preserved in `archive/planning/2026-10-31/`. Decisions versus proposed modelling defaults are distinguished below. Research and profiling are complete for this pass; the optimisation pipeline described here is **planned, not implemented or solved**.

## 1. Decision and storyline

**Question:** Where should additional slow charging points be installed in Singapore's HDB carparks, and how much additional charging demand and access does each level of investment deliver?

The two angles belong in one capacitated facility-location model: sites and integer quantities determine cost and service jointly. The decision maker is an HDB infrastructure planner evaluating network cost-effectiveness; expenditure is infrastructure investment across participating parties, not automatically government spending. Existing public HDB supply is fixed. Private estates, other-agency investment, carbon, carbon tax and petrol savings are excluded. Existing non-HDB public supply is an optional external-access sensitivity, never an investment candidate or an assumed free substitute for all HDB need.

Narrative to test, not a predetermined finding:
1. National adoption is increasing, but national point totals do not reveal local adequacy.
2. Match HDB supply to HDB demand proxies, exposing uncertainty and growing estates.
3. Establish what existing infrastructure can serve before recommending more.
4. Compare a simple deployment rule with an optimised allocation under the same assumptions.
5. Show the extra service gained per investment increment and which decisions remain useful when assumptions change.
6. Recommend a staged, conditional shortlist with explicit data and engineering checks.

If an equal/proportional rule performs almost as well, report that. The meeting's concern about a trivial slow-charger allocation is a testable question, not a reason to invent heterogeneous costs or force fast chargers into the core model.

**Confirmed:** all HDB carparks; one slow type in the base; fast-charger extension; no carbon scope; report not slides; report skeleton by 15 November, 11 a.m. Singapore time.

**Proposed defaults, not team decisions:** 7.4 kW AC additions, current 2026 benchmark, 2027 planning case, 2030 outlook; 400 m straight-line catchment; capex budget scenarios; service-first then lifecycle-cost optimisation. Sensitivity ranges are recorded in `data/08_costs/cost_parameters.csv`.

## 2. Data selection after inspection

Use the complete file-level inventory and gap register in `data/09_research_audit/` as the evidence ledger. The following maps each input family to a decision; collecting a file does not mean using it in the model.

| Input | Exact use / transformation | Status and restriction |
|---|---|---|
| `01_ev_charging_supply/LTA_EV_charging_points_Sep2026.csv` | Deduplicate `evCpId`, preserve registration group, plug, power, address, coordinates, floor and lot. Build confirmed HDB site assignments and simultaneous-power bounds. | Core. 11,489 point rows; 9,279 registrations. All publicly accessible, not all HDB. 17,011 was a repeated-field sum, not an outlet total. Registration date is not proven commissioning/uptime history. |
| `03_…/HDB_carpark_information.csv` | Candidate IDs/coordinates/type; SVY21→WGS84; tag MP2019 and MP2025 areas separately. | Core. 2,273 rows, unique IDs. Night-parking flag informs a residential eligibility check, not an automatic interpretation of season-parking rights. |
| `03_…/HDB_carpark_lots_snapshot_2026-10-31.csv` | Select `lot_type=C`; one-to-one ID join; total lots for spatial weights and space limits. | Core, partial. 1,997 matches, 276 missing, 2 zeros. Ignore one-time vacancy as average car demand. Ten snapshot IDs absent from master require review. |
| HDB outlines | Inspect spatial context for doubtful matches. | Supplementary: 30,748 features, no carpark ID. Not a ready site crosswalk. |
| URA parking capacity, JTC carparks, NParks lots, parking-standards shapefile | None in base site set. | Retained background, outside agreed placement scope. |
| `02_…/LTA_M09_monthly_vehicle_population_by_fuel.csv` | Filter Cars and Electric for stock series; separately compute total Cars with consistent categories. | Core national adoption input through Sep 2026. Strings/NA markers require numeric coercion audit; hybrids/PHEVs/taxis/buses must not be silently pooled. |
| `02_…/LTA_M03_monthly_new_car_registrations_by_make_fuel.csv` | Sum comparable electric passenger-car registrations by month; distinguish new sales share from fleet share. | Forecast scenario evidence; stock identity requires retirement/export assumptions. |
| `02_…/LTA_annual_private_vehicle_mileage.csv` | Latest Cars mileage: 16,200 km/year for 2025; vary to represent HDB driving. | Core energy-demand proxy, not observed EV mileage. |
| Annual fuel/car/make registrations and original XLSX | Reconcile monthly aggregates with complete years; source-format checks. | Validation only; avoid counting annual and monthly tables twice. |
| Monthly all-vehicle population / SingStat vehicle totals | Denominator and category cross-checks. | Validation only. |
| COE bids/PQP, taxi fleet, NEA green vehicles | Context only; no causal demand regression. | Omit from base. NEA “green” includes categories other than battery EVs. |
| Census2020 households by dwelling | HDB household shares and historical cross-check. | Optional demand robustness, not latest HDB stock. Table has 32 rows including totals/grouped geography; do not pretend it covers 55 individual areas. |
| Census2020 car-only commuting | Normalised alternative location weights after checking named and grouped areas. | Sensitivity only. Commuters include passengers and are not unique car owners. Taxi/private-hire-only is not car ownership. |
| Census income / workplace | Income as descriptive context; workplace excluded from residential base. | Avoid unestimated causal income→EV multiplier. Working-place demand would duplicate resident energy unless allocated explicitly. |
| Census2020 subzone population by dwelling | Historical HDB distribution, after removing parent-area totals and national totals. | 388 rows include levels; do not sum all rows. |
| HDB property blocks | Residential blocks / dwelling stock and completion year by HDB town code; new-town plausibility check. | 13,392 rows; no coordinates. Construction completion ≠ actual occupancy. Geocoding required before site joins. HDB towns ≠ planning areas. |
| New SingStat population by dwelling, 2024/2025 | Sum four HDB dwelling types by `(PA,SZ,Time)`; compare same-vintage local changes. | Core spatial validation, MP2019. Cell counts rounded to nearest 10. |
| New population by floor area, 2020–2024 | Sum mutually exclusive cells; long-run all-resident trend by area/subzone. | Not HDB-specific. 2024 overlaps the dwelling-type table; choose one, do not stack totals. |
| New dwelling stock by dwelling, 2025 | HDB stock weights and missing-lot/new-town checks. | Core cross-check; dwellings ≠ occupied households or persons. |
| New population/dwelling stock 2026 | Separate MP2025 layer; rerun allocation at planning-area level after geography check. | Robustness. Source notes establish a geography break; do not concatenate raw subzone growth. |
| New dwellings by floor area, 2020–2024 | Independent historical housing-stock trend; cross-check rapid growth. | All dwelling types; cannot be filtered to HDB from floor area alone. |
| GHS2025 PDF | Chapter 8 geography, chapter 9 transport, table 9.1 housing/commuting comparison. | Full report acquired. Detailed transport workbook NOT acquired; landing page is not data. |
| Population Trends 2026 PDF | Latest definitions, rounded population totals and geographic context. | Context and consistency checks; no population-to-EV causal forecast. |
| MP2019 PA and subzone; MP2025 PA | Maps, spatial joins and separate vintage checks. | Core. Match on `(planning area, subzone)`, not subzone name alone. MP2025 subzone crosswalk remains unavailable in this collection. |
| Original `07_derived/planning_area_summary.csv` | Exploratory all-public supply comparison only. | Not HDB analysis; outlets corrected. Must rebuild a new HDB-specific summary before citing siting conclusions. |
| New review CSVs under `07_derived/` | Capacity-ready site register; population/housing aggregates with source and geography columns. | Audit products, not fitted demand or recommendations. |
| MOT/LTA releases, driver guide and policy PDFs | Utilisation calibration, scope, eligible charging infrastructure and institutional constraints. | Cite official source; historical figures retain date and population definition. Old Wikipedia/news are discovery/context only. |
| Cost table, vendor pages, ICCT, AFDC | Separate quoted component costs, installed-cost assumptions, recurring cost and site upgrades. | See §6. No residential/private-condo or heavy-vehicle grants in HDB base. |

## 3. Data readiness and reproducible pipeline

Research scripts already supplied: `fetch_research_sources.py` (URLs, hashes, failures), `audit_research_data.py` (profiles, capacity joins, candidate supply match queue, demographic aggregates). Install dependencies using `requirements-research.txt`. No credentials are needed. Record raw-file hashes in each model run so later source changes do not silently alter results.

Planned build order and outputs:

1. **Site register → `sites.csv`.** Start from all 2,273 HDB IDs. Standardise types; retain original and projected coordinates. Join lots, inspect duplicate/retired/missing IDs; mark observed/imputed capacity separately. Keep excluded sites with reasons in an exceptions table. Do not drop their associated demand without reporting it.
2. **Supply crosswalk → `hdb_charger_crosswalk.csv`, `existing_supply.csv`.** Standardise postal codes as six-character strings. Compare block/street/building, distance and carpark geometry. Exact address evidence outranks nearest neighbour. Review every multiple-candidate or non-HDB-looking location, plus a sample of high-confidence matches. Each point maps to at most one site. Uncertain and non-HDB points remain separate. Use the supplied 2,884-location review queue; vary 50/100/150 m only as candidate-generation radii, not evidence of ownership.
3. **Capacity gaps.** Publish 276 missing and 2 zero records. Base analysis may use a labelled median from observed sites in the same planning area and carpark type (minimum sample five; fall back to type then national median), but never call it observed capacity. Compare no-build at unknown sites and 0.5×/1.5× imputation cases. Where excluding sites also removes demand, report excluded estimated demand and maintain an alternative housing-weight allocation. Return to source if the result concentrates on imputed sites.
4. **Demographics → `area_demand_weights.csv`.** Select 2025/MP2019 for base. Keep all 55 areas, including missing/grouped older-census cells. Missing is not zero. Check HDB stock and residents against block completions. For 2026 rerun with MP2025 PA joins and do not rely on a nonexistent subzone crosswalk.
5. **National scenarios → `ev_stock_scenarios.csv`.** Freeze the stock/registration vintage; show observed versus assumed values; explicit 2027 and 2030 scenario paths and calibration errors. Do not re-download live data mid-run.
6. **Demand → `demand.csv`.** Formula in §4; all demands in grid-side kWh/day. Include input provenance, site weights, HDB EV total, charging dependence and zero/missing flags.
7. **Service arcs → `arcs.csv`.** Distance in EPSG:3414 metres or verified geodesic calculation; sparse arcs within radius, including self-arcs. Retain disconnected nodes. Avoid treating Euclidean distance as actual walking distance; test barriers at shortlisted sites and a path-inflation factor. Preserve planning-area-boundary-crossing service arcs.
8. **Parameters → `scenario_parameters.csv`.** Validate units, evidence category, all cost components and assumed grid headroom. Freeze before solving; no tuning to obtain preferred estates.
9. **Optimisation → `run_manifest.json`, `site_decisions.csv`, `demand_flows.csv`, `scenario_metrics.csv`, solver logs.** Record objective priorities, bounds, tolerances, Gurobi version, seed/time limit, solve status and achieved gap. No recommendation can be called optimal from a time-limited feasible solution alone.
10. **Report assets.** Maps, service/cost curves, baseline comparisons and robustness summaries. Store plotting data alongside charts. Use no unsupported numerical placeholders in report prose.

## 4. Demand without pretending lots are EV ownership

Let `E_t` be national battery-electric passenger-car stock, `h_t` the share associated with HDB residents/season parking, and `w_i,t` nonnegative spatial weights summing to one. Set:

```
HDB_EV_t   = E_t * h_t
EV_i,t    = HDB_EV_t * w_i,t
D_i,t     = EV_i,t * public_dependence * (annual_km / 365)
            * battery_kWh_per_km / charging_efficiency
```

`D` is grid-side kWh/day sought from the modelled HDB network. Public dependence is specifically the share of this energy sought at HDB chargers, not all publicly accessible chargers; otherwise excluding mall charging would overstate HDB demand. Base spatial weight is car lots divided by total included/imputed HDB car lots. Alternative weights allocate an area's share from 2025 HDB residents/dwellings and distribute within area by lots. Blend or select alternative proxy specifications, rather than multiplying raw proxies and unknowingly double-counting growth.

Historical weak calibration: the MOT reply gives about 8,800 EVs with HDB season parking in September 2024; the local LTA electric-car series has 21,796 in that month. The ratio is about 0.404 but the categories may differ (e.g. commercial vehicles/PHVs), and season parking is not a full residency census. Treat 0.40 as a scenario anchor, not a measured current HDB adoption rate. Test 0.30/0.40/0.55 and compare predictions against aggregate utilisation only with consistent charger counts and dates. Calibration to one aggregate cannot establish geographic accuracy.

National stock forecast uses `E_(t+1) = E_t + new_electric_cars_t - retirements_or_exports_t` subject to total-car stock. New registration share is not stock share. Fit/display recent history, back-test a held-out period if extrapolation is attempted, and otherwise present low/base/high paths as assumptions without statistical confidence intervals. Retain 2030 fleet-share cases 25/35/45% only as illustrative stress cases, not official targets or forecasts. Do not estimate future all-car stock from population growth alone because Singapore's vehicle controls matter.

For local growth, use 2020–2025 all-resident/stock changes as a reasonableness check and 2024–2025 HDB changes for short-run spatial redistribution. Cap speculative extrapolation, renormalise weights, and use absolute increases/housing stock for zero-base towns. Do not compound Tengah's short growth rate mechanically. The 2026 layer is a robustness check after the geography break is addressed.

## 5. Capacity, access and modelling limits

A point serves one vehicle at a time, but daily kWh capacity is not a queue guarantee. For new 7.4 kW AC points, use `q = 7.4 * H * a * rho` with effective scheduled charging hours `H`, availability `a`, and mean delivered-power/rated-power factor `rho`. Proposed values: 6 h/day, 0.97 availability, 0.85 power factor, giving about 36.6 kWh/day. These are design assumptions. Charging conversion losses are accounted for in demand; `rho` represents charging-rate/taper behaviour, not a second charging-efficiency loss. Stress `H` at 4/6/8 and uptime separately.

Existing capacity is built registration by registration. If simultaneous output is undocumented, compute conservative maximum-rated-port and optimistic sum-of-port bounds; retain connector counts separately for space and occupancy. The AC base concerns **new additions**, so existing confirmed DC infrastructure should be preserved with type-appropriate capacity assumptions, or removed only in a clearly labelled AC-only comparison. Do not erase installed fast capacity merely to simplify the decision variables.

A 400 m Euclidean catchment is a proposal, not a legal accessibility standard or actual route. Test 250/400/800 m, non-transferability between season carparks, and path inflation. Cross-site service assumes a resident can park at the destination. MOT's historical note about season-parking transfer does not mean unrestricted simultaneous access. Self-site-only service is a useful lower-bound/access restriction case.

Existing connector rows can share a physical bay or repeat a multi-lot label. Review floor/lot identifiers; do not equate connectors with parking bays. New base AC points assume one dedicated bay each. Keep existing bay occupancy `b0_j` separate from existing connectors. Until validated, a point-equals-bay assumption is explicitly conservative and tested.

Total space cap: use `max(existing_bays, floor(alpha * car_lots))` so a policy scenario does not make already installed supply infeasible. `alpha=0.10` is an assumption, not HDB regulation. Unknown grid headroom stays unknown; scenario `G_j` is **spare incremental kW after existing load**, with upgrade increment `U_j`. It must not be treated as total power with existing chargers ignored. No-charger sites are not automatically grid-constrained. Planned and commissioned infrastructure are tracked separately if later obtained.

## 6. Costs and benefits

`data/08_costs/cost_parameters.csv` is the active parameter register. The old table is archived; source evidence and assumptions are explicitly distinguished. Values in low/base/high columns are scenarios, not confidence intervals.

Electric's advertised 7 kW hardware range is S$1,500–2,800 excluding GST and installation; its 22 kW and DC schedule allows technology comparisons. Public network connectivity, payment/backend support, civil works, distribution cabling, metering, approval and warranty terms are not established by these retail figures. Go Electric's S$856 example only covers a short run from an already supplied electrical point; do not apply it as HDB site installation cost. Electric's AC maintenance figure of S$380/year is a local non-restricted-use comparator; it is not an HDB all-in operating contract. AFDC/ICCT are external checks and must retain year/currency/location limitations.

Keep S$6,500 installed AC capex as a provisional scenario, with 4,500/10,000 bounds. It is **not** the observed sum of validated HDB components. Show hardware separately; the residual is unverified installation/network provisioning. Do not add full installation twice when introducing fixed site costs. Base mobilisation is zero when included in per-point capex; a separate fixed-cost sensitivity requires an explicit cost-scope reconciliation. Grid-upgrade cost remains 0/50,000/250,000 per affected site as a scenario, not a quote or a flag inferred from the 139-carpark aggregate.

Infrastructure annualised cost:

```
Ccap = sum(c_j*x_j + F_j*z_j + K_j*y_j)
CRF(r,n) = r / (1 - (1+r)^(-n)); CRF(0,n) = 1/n
Cann = CRF * Ccap + sum(maintenance_j*x_j + network_j*x_j)
```

Use separate lifetimes for upgrades if justified; the simple base uses one lifetime and discloses that approximation. Existing capex is sunk. Existing fixed O&M is unchanged and excluded from incremental cost. Report electricity separately; if included in whole-network operating-cost differences, use `365*e*(served_new - served_baseline)` with consistent energy definitions. Annual recurring cost and upfront capex have different units; do not compare annualised cost directly to a capital budget.

Primary benefits: additional grid-side kWh/day served, coverage increase, demand-weighted distance, and cost per additional annual kWh served. Service means energy delivered in this stylised allocation, not emissions saved or guaranteed queue reductions. Calculate increments against a fixed no-build baseline; distinguish redistribution of existing load from extra demand enabled by new infrastructure. A site's stand-alone capacity is not its marginal system benefit because catchments overlap.

For each shortlisted site, remove/fix out its additions and reoptimise at a comparable budget to estimate replacement value, noting network interaction. For the budget frontier report `delta capital / (365*delta served)` and annualised equivalents. If incremental service is zero, the ratio is undefined, not zero. Optional operator gross margin is labelled a financial scenario using tax-consistent prices, electricity, losses, maintenance and network fees; do not call gross margin profit or society's benefit. NPV/payback is optional appendix work only, not core scope.

## 7. Base MILP and two sequential solves

This is a **capacitated facility-location / maximal-service extension**: continuous energy flows, integer charger additions, optional binary site activation and power upgrade. It adapts the facility-location structure, not the exact uncapacitated binary-coverage MCLP. See `data/10_methodology/README.md` for references.

Sets: demand nodes `i`, candidate HDB sites `j`, allowable arcs `A={(i,j): distance<=R and access permitted}`. Parameters: demand `D_i`; existing effective capacity `Q0_j`; new-point capacity `q`; existing occupied charging bays `b0_j`; physical bay limit `Lbar_j`; spare headroom `G_j`; upgrade power `U_j`; capex `c_j`, site mobilisation `F_j`, upgrade `K_j`; budget `B`. A tight integer upper bound `M_j = max(0, Lbar_j-b0_j)` comes from space, not an arbitrary huge constant.

Variables: `x_j` nonnegative integer additions; `z_j` binary activation for additions; `y_j` binary upgrade; `f_ij >= 0` delivered kWh/day; `s_i >= 0` unmet kWh/day.

```
sum_j f_ij + s_i = D_i                       each demand node
sum_i f_ij <= Q0_j + q*x_j                    each site
x_j <= M_j*z_j; z_j <= x_j                    activate iff at least one point is added
7.4*x_j <= G_j + U_j*y_j                      incremental electrical capacity
x_j + b0_j <= Lbar_j                          space
 y_j <= z_j                                 upgrade only when adding points
sum_j(c_j*x_j + F_j*z_j + K_j*y_j) <= B        capital budget
f_ij exists only for (i,j) in A
```

`z<=x` and `y<=z` can be dropped/reformulated if upgrades independently improve existing capacity; that is not the base case. Preserve demand at nodes without arcs using `s_i`, keeping the model feasible. Existing power uncertainty is absorbed into `Q0`, not falsely corrected with new grid headroom.

**Pass 1:** maximise `S = sum_ij f_ij` under a stated budget. No monetary unmet-demand penalty is required.

**Pass 2:** add `S >= S_star - epsilon` and minimise `Cann` (or capex for the capex-only comparison). Keep the same budget and constraints. Set epsilon explicitly in kWh/day using numerical tolerance, e.g. `max(1e-6,1e-8*sum(D))`; report it. The equality is only valid as an optimal-service lock after pass 1 reaches an acceptable certified gap. A time-limited incumbent gives an approximate priority solution; record its bound and do not claim exact lexicographic optimality. Optional pass 3 locks cost within tolerance and minimises `sum(distance*f)` to avoid arbitrary long allocations. This tertiary tie-break is for reproducible access metrics.

These are sequential deterministic objectives, **not stochastic two-stage recourse**. Scenario re-solves are sensitivity analysis. A true stochastic extension would require probabilities, shared first-stage investments and scenario-specific recourse; it is unnecessary for the agreed base.

For no-build `S0`, fix `x=y=z=0` and solve the same allocation problem. Hold demand, capacity assumptions and catchments fixed. Budget cases must include zero. As an alternative when the team prefers a service mandate, minimise cost subject to `S >= tau*sum(D)` for `tau=0.80/0.90/0.95`; report infeasibility rather than forcing full service.

## 8. Budget frontier and comparison rules

No government budget was established. First solve the unconstrained-budget maximum service under physical bounds and the minimum cost to reach selected service targets. If 90% is feasible, call that cost `B90` and evaluate budgets `0, .25, .5, .75, 1, 1.25` times `B90`, displaying actual SGD amounts. If it is infeasible, anchor the grid to the minimum cost of near-maximum physically feasible service and explain the shortfall. Refine budgets around discrete jumps; no fabricated smooth curve or single “optimal budget” without an explicit preference.

Compare at identical **actual spend and constraints**, or show cost-service pairs where integer increments prevent equal spend:
- No build / optimally assigned existing capacity.
- Equal incremental allocation across eligible sites, with deterministic ID order and budget/space/power feasibility checks.
- Proportional allocation by lot weights, using largest-remainder rounding, then feasibility repair and published unspent budget.
- Greedy best incremental served-demand per extra dollar, including activation/upgrade step costs and reassignment of existing flows after each addition.
- MILP allocation.

If optimiser chooses mainly larger carparks, quantify gain over proportional allocation. Explain why a capacity/catchment model is or is not materially better than the simple rule. Do not use unrealistic cost variation to obtain a more interesting map.

## 9. Sensitivity, robustness and extensions

Run base plus one-at-a-time changes first, followed by a small joint scenario set (low-demand/cheap-capacity; base; high-demand/expensive-grid; access-restricted). Do not run the full Cartesian product or assign unsupported scenario probabilities.

Core dimensions: national EV stock; HDB share; HDB charging dependence; mileage and energy intensity; missing-site treatment; lot vs housing spatial weights; conservative vs optimistic supply match/power; effective hours and availability; catchment; capex ± ranges; spare grid and upgrade cost; budget; 8/10/12-year lifetime and 3/5/8% discount rate. Hold separately fixed the price-year/GST convention.

Metrics: total/incremental service; investment and annual cost; unmet demand by area; demand-weighted distance; site count and points; share of investment at imputed or uncertain sites; binding constraints; solver runtime/gap. Define robustness as fraction of specified scenarios selecting a site, **not a probability it is optimal**. Evaluate the base investment fixed under alternative demand/capacity, alongside reoptimised scenario outcomes; otherwise sensitivity only describes different worlds and not how the proposed plan withstands change. Report regret/shortfall against each scenario optimum and sensitivity of conclusions to tie-breaking. LP-relaxation duals may illustrate bounds, but MILP budgets have discrete marginal changes; use finite differences for investment decisions.

**Fast extension:** allow 7.4 kW AC plus 50 kW DC increments with separate costs, effective capacities and power requirements. Do not mandate a separate fast-demand fraction without evidence; use substitutable energy demand first and an explicitly assumed preference sensitivity second. If exploring the HDB-town hub policy, use town boundaries/crosswalk and a binary hub per site with a co-located minimum number of DC points; a planning area is not a town and scattered points are not a hub. Compare DC ability to relieve specific constrained catchments against its extra cost. Keep AC-only base complete even if DC extension is dropped.

**Phasing extension:** year-index additions `x_j,t` and cumulative installed quantity `sum_(tau<=t)x_j,tau`; investments cannot disappear in later years. Use explicit annual/cumulative budgets, upgrade-once binaries and discounted costs. If time is short, simulate a documented rolling yearly decision rule and distinguish it from joint multiyear optimisation. A chart of independently optimal 2027 and 2030 sites is an outlook, not a construction schedule.

**Peak/reliability extension:** day/night periods or session occupation constraints if data support them. Without charging-session data, show capacity stress tests and say waiting time is unestimated. No M/M/c queue formula without validated arrival/service assumptions.

**Equity extension:** minimum area service fraction or a maximum shortfall rate at an additional cost, chosen transparently. Do not automatically favour wealthy areas using income-based weights.

## 10. Verification before any report conclusions

Data checks: ID uniqueness; no negative capacities/demand; source dates; coordinate range; one assignment per point; HDB eligibility; population subtotal handling; missing-data counts; population/EV totals; flow input units. Audit a stratified manual sample (dense estates, new towns, mixed-use malls, multi-storey sites, missing capacities) and all shortlisted uncertain sites. Housing/lot proxies should be checked against plausible totals, not fitted until they recreate preferred answers.

Meaningful optimisation checks: zero budget reproduces no-build service; zero demand buys nothing; a tiny hand-solvable two-node instance verifies sharing, fixed upgrade cost and integrality; nodes without arcs remain unmet; unmet falls/nonincreases as budget rises for fixed inputs; cheaper cost or more capacity cannot worsen maximum service; no point/port double-counting; cost components reconcile; pass 2 preserves service; full-service infeasibility is handled. Round display values only, not solver input or constraint residual checks. Re-solve identical frozen inputs to assess reproducibility and alternate-optimum variation. Stop expanding tests once these checks pass unless new changes require it.

Do not state capacity claims for unverified cabinet limits, site feasibility without an electrical survey, or investment causality from a proxy allocation. A model recommendation is a conditional decision-support result.

## 11. Final report: seven main sections, about 11 pages

Detailed prompts and empty result slots are in `report_skeleton.md`. Suggested allocations exclude appendices and can be adjusted to the guideline's flexible 8–14 narrative pages:

1. **Problem and policy decision** (0.75 page): HDB-only placement and cost-effectiveness; current challenge; research questions.
2. **Data, demand and assumptions** (2 pages): source/method table, supply matching, calibrated lot weights, unknowns and dates.
3. **Model and methodology** (2 pages): literature, formulation, sequential objectives, why nontrivial; capacity/access assumptions.
4. **Placement results and baseline comparison** (2 pages): existing vs recommended map, area/site table, service/spend and baseline gains.
5. **Cost-effectiveness and budget choices** (1.5 pages): incremental-service frontier, marginal investment value, saturation and alternatives.
6. **Sensitivity, fast-charger and growth extensions** (2 pages): robust sites and fixed-plan stress, AC/DC comparison if completed, 2027/2030 outlook.
7. **Recommendations and limitations** (0.75 page): conditional shortlist, evidence needed for deployment, principal limitations.

Four main figures: paired supply/placement map; budget/service frontier with comparator; sensitivity/robustness plot; phased/outlook or AC/DC comparison. Two compact main tables: inputs/assumptions and base/scenario performance. Avoid charts that merely repeat text. Appendix: mathematical detail, all source URLs/dates, data audit, parameter evidence, exact model and plotting code, run manifests, additional scenarios and any required AI-use disclosure. Never invent results to fill the skeleton.

## 12. Owners and delivery sequence

| Workstream | Reviewer(s) from notes | Proposed completion |
|---|---|---|
| Build pipeline/model and coordinate assumptions | Regan/Reagan | Draft inputs/model 12–14 Nov |
| Data/source/matching review | Sara/Sarah and Sandra | Before skeleton meeting; shortlist review after first solve |
| Model/formulation/reference review | Erica and Udhaya | Before first reported result |
| Cost sensitivity and robustness | Aish; duplicated name unresolved | 16–18 Nov |
| Narrative integration and reference consistency | Owner still to assign; all review | Draft 19–20 Nov; final check 21 Nov |

Confirmed meeting: **15 November 2026, 11 a.m. Asia/Singapore**, skeleton ready. Working submission deadline retained from prior context: **22 November 2026**. Proposed internal dates are planning suggestions, not commitments transcribed from the meeting.

Next modelling gates: accept the scenario horizon/budget/service convention; finish HDB supply crosswalk and missing-capacity treatment; freeze assumptions; then solve the base, compare simple rules, and add extensions only if the core results are verified. No additional data hunt is required for carbon/fuel savings. The user subsequently authorised committing and pushing this research update on 9 November 2026.
