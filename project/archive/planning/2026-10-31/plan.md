# Project plan — Where to put Singapore's next EV chargers, at what cost and benefit

_Draft v1, 2026-10-31. For discussion at the 9 Nov sync._

## 1. The question we answer

> **Given the EV fleet expected by 2030, where should Singapore add public charging points (and of which type, slow AC or fast DC), so that EV owners' charging needs are met at the lowest cost? What is the total cost, and what benefits does it deliver?**

The report delivers four things:
1. **Where:** recommended new charging points per carpark/planning area, split into slow (7.4 kW AC) and fast (50–100 kW DC), shown on a map.
2. **Cost:** total capex, grid-upgrade cost and annualised cost, plus cost per kWh delivered.
3. **Benefit:** demand served, operator margin/NPV, CO₂ avoided and its value, and the shorter distance EV owners travel to a charger.
4. **Trade-off:** a budget vs. benefit curve, i.e. how much more demand each extra $10M serves, and the point of diminishing returns. Sensitivity analysis on the uncertain inputs.

Why it matters: EVs are 63% of new cars in 2026, but HDB residents (~80% of the population) can't charge at home. Utilisation is already 61% at peak in Tengah. Public chargers are spread unevenly: Bedok/Sengkang have ~5–6 per 1,000 households vs ~18 in Jurong East. The government targets 40k public points by 2030 but hasn't published where they should go.

## 2. Model at a glance

```
             DEMAND SIDE                                  SUPPLY SIDE
 EV fleet 2030 (scenario) ──┐                 Existing chargers (LTA register)──┐
 Cars per HDB carpark ──────┼─► EV charging   Candidate sites (HDB carparks) ───┼─► capacity per site
 Census: dwelling, income ──┤   demand (kWh/   Car lots, power limits ──────────┘
 Mileage, kWh/km ───────────┘   day) per node
                                      │                         │
                                      └──► distance matrix ◄────┘
                                                 │
            Costs (capex, grid upgrade) ──► MILP in Gurobi ◄── Benefits (margin, CO₂, access)
                                                 │
                           Where + how many │ total cost │ benefits │ sensitivity
```

- **Demand nodes:** HDB carparks. Their resident cars are the core of public-charging demand, and car lots are a good proxy for cars parked there. Optional extra layer: condo/landed demand per subzone from Census 2020, with a lower dependence on public charging.
- **Candidate sites:** the same ~2,000 HDB carparks, optionally plus URA/JTC/NParks carparks.
- **Decisions:** how many new slow and fast points to add at each site, and whether to pay for a grid upgrade at a site.

## 3. Data: what we have vs. still need

| # | Data item | Status | File / source |
|---|---|---|---|
| D1 | Existing public chargers (location, kW, operator) | ✅ | `data/01_ev_charging_supply/LTA_EV_charging_points_Sep2026.csv` |
| D2 | EV fleet and registration trend | ✅ | `data/02_…/LTA_M09_…`, `LTA_M03_…` |
| D3 | Car mileage (16,200 km/yr in 2025) | ✅ | `data/02_…/LTA_annual_private_vehicle_mileage.csv` |
| D4 | HDB carparks: coordinates, type, decks | ✅ | `data/03_…/HDB_carpark_information.csv` (SVY21) |
| D5 | Car lots per HDB carpark | ✅ | `data/03_…/HDB_carpark_lots_snapshot_2026-10-31.csv` (1,997 matched) |
| D6 | Households by dwelling type, car commuters, income per planning area | ✅ (2020) | `data/04_…/Census2020_*` |
| D7 | Subzone / planning-area boundaries | ✅ | `data/05_geospatial_boundaries/` |
| D8 | Capex per point, prices, tariff, grants | ✅ (capex research-based) | `data/08_costs/cost_parameters.csv` |
| D9 | Utilisation evidence (20% avg, 36% peak, Tengah 61%) | ✅ | `data/06_…/MOT_parliamentary_replies_…md` |
| D10 | Calibration: 8,800 EVs held HDB season parking (Sep 2024), when 21,796 electric cars existed → ~40% of EVs park at HDB | ✅ | same |
| **N1** | **Grid CO₂ emission factor (kg CO₂/kWh)** | ❌ to collect | EMA Singapore Energy Statistics |
| **N2** | **Carbon tax / carbon price (S$/t CO₂)** | ❌ to collect | NEA / MOF carbon tax page |
| **N3** | **Petrol car CO₂ (g/km) and EV efficiency (kWh/km)** | ❌ to collect | LTA fuel-economy / VES data; manufacturer specs (e.g. BYD Atto 3) |
| **N4** | **Petrol pump price (S$/L)**, for fuel savings to drivers | ❌ to collect | Motorist / SPC / Shell price boards |
| **N5** | Charger O&M cost (% of capex per year) | ❌ assumption + source | ICCT / industry reports |
| N6 | SingStat June 2025 population by subzone (updates Census 2020 for new towns) | optional | SingStat website (manual download) |
| N7 | Electrical spare capacity per carpark | ❌ not public | assumption, tested in sensitivity |

## 4. Pipeline: how the data chains together

Each step produces one clean file in `data/07_derived/` that the next step reads. Suggested scripts go in `scripts/`.

### Step 1: Geography (`01_build_sites.py`)
- Convert HDB carpark SVY21 x/y → lat/lon (`pyproj`, EPSG:3414 → 4326).
- Join D5 lots on `car_park_no`. Tag each carpark with its subzone and planning area (point-in-polygon, D7). Map HDB carparks to their town.
- **Output:** `sites.csv` with car_park_no, lat, lon, planning_area, subzone, town, type, decks, car_lots.

### Step 2: Existing supply per site (`02_existing_supply.py`)
- Match each LTA charger (D1) to the nearest HDB carpark within ~100 m. Unmatched chargers (malls, condos, offices, petrol stations) stay as "other public supply" points.
- For each site, count existing slow/fast points, total kW and existing capacity (kWh/day) = Σ kW × 24 × u_max.
- Flag the ~139 carparks with no charger. These likely have power constraints, so a grid upgrade is required there.
- **Output:** `existing_supply.csv` (per site) and `other_public_chargers.csv`.

### Step 3: Demand per node (`03_demand.py`)
Chain of multiplications for each HDB carpark *j* and scenario *s*:

```
EVs_j        = car_lots_j × occupancy (~0.85) × EV_fleet_share_s × income_adj_PA(j)
public_dep   = share of those EVs relying on public charging (HDB ≈ 0.9; sensitivity 0.6–1.0)
kWh/day_j    = EVs_j × public_dep × (16,200 km/365) × kWh/km (~0.16)
             = EVs_j × public_dep × ~7.1 kWh/day
split        = slow share (~80%) vs fast share (~20%, incl. taxis/PHVs)
```
- **EV fleet scenarios for 2030:**
  - Today: 74,887 electric cars ≈ 11.5% of ~651k cars.
  - Rough projection: about 50k new cars/yr with an EV share rising from 63% to ~90% gives **≈ 240k EVs (~37%) by end-2030**.
  - Scenarios: low 25%, base 35%, high 45%. Build this from D2 in a small notebook.
- **income_adj (optional):** planning-area index from D6 (share of households earning S$20k+ relative to the national figure), normalised so the national total is unchanged.
- **Calibration check:** apply the method to Sep 2024 and compare the total EVs at HDB with the reported 8,800. Compare implied current load with ~20% average utilisation of existing chargers.
- Optional non-HDB layer: condo/landed demand per subzone from D6 with public_dep ≈ 0.3/0.1.
- **Output:** `demand.csv` with node_id, lat, lon, kWh/day per scenario, slow/fast split.

### Step 4: Distances (`04_distances.py`)
- Haversine distance between every demand node and every candidate site. Keep only pairs within the radius: R_slow ≈ 400 m (walk from the carpark you park at overnight) and R_fast ≈ 3 km (short drive).
- **Output:** `arcs.csv` with node, site, distance_m. Expect ~2,000 × ~20 ≈ 40k arcs, which is small for Gurobi.

### Step 5: Cost and benefit parameters (`05_params.py`)
- From `08_costs/cost_parameters.csv` (base, low, high) plus N1–N5.
- Annualised capex per point: c_k × CRF, where CRF = r/(1−(1+r)^−n) (10 yrs, 5% base).
- **Output:** `params.json`, one per scenario.

### Step 6: Optimisation (`06_model.py`, Gurobi)
See §5.

### Step 7: Scenarios and sensitivity (`07_scenarios.py`)
See §7.

### Step 8: Outputs for the report (`08_outputs.ipynb`)
Maps, tables and charts. See §8.

## 5. Optimisation model (draft formulation)

**Sets**
- *i*: demand nodes (HDB carparks)
- *j*: candidate sites
- *k*: charger types {slow 7.4 kW, fast 50 kW}
- *A*: allowed arcs (i, j, k) with d_ij ≤ R_k

**Parameters**
| Symbol | Meaning | Source |
|---|---|---|
| D_ik | demand kWh/day at node i for type k | Step 3 |
| e_jk | existing points at site j | Step 2 |
| q_k | kWh/day one point can deliver = P_k × 24 × u_max (u_max ≈ 0.36 peak-safe) | D9 + assumption |
| c_k | annualised capex per point | D8 |
| F_j | annualised grid-upgrade cost at site j | D8 assumption (S$50k base) |
| G_j | spare electrical capacity at j (kW); assume ~0 for the 139 no-charger carparks | N7 assumption |
| U | extra kW unlocked by an upgrade | assumption |
| L_j | car lots at j; α = max share of lots that can be EV lots (e.g. 10%) | D5 |
| m_k | operator margin per kWh (S$0.37 slow / S$0.60 fast) | D8 |
| v | value of unmet demand per kWh (penalty, e.g. fuel cost saved, or a high number) | N4 |
| B | budget (optional) | scenario |

**Decision variables**
- x_jk ∈ ℤ⁺: new points of type k at site j
- y_j ∈ {0,1}: grid upgrade at site j
- f_ijk ≥ 0: kWh/day of node i's demand served at site j
- s_ik ≥ 0: unmet demand

**Objective (version A, minimise total annual cost to society):**
```
min  Σ_jk c_k x_jk + Σ_j F_j y_j + 365 · v · Σ_ik s_ik
```

**Constraints**
1. Demand balance: Σ_j f_ijk + s_ik = D_ik ∀ i,k
2. Site capacity: Σ_i f_ijk ≤ q_k (e_jk + x_jk) ∀ j,k
3. Power: Σ_k P_k x_jk ≤ G_j + U·y_j ∀ j
4. Space: Σ_k (e_jk + x_jk) ≤ α L_j ∀ j
5. Fast hub per town: Σ_{j∈town t} (e_j,fast + x_j,fast) ≥ 6 ∀ t (policy)
6. Optional national target: Σ_jk (e_jk + x_jk) + other public points ≥ 40,000
7. Optional budget: Σ c_k x_jk + Σ F_j y_j ≤ B

**Variants for the report**
- **B, max benefit under a budget:** max Σ m_k · served − cost s.t. budget B. Varying B gives the cost–benefit frontier.
- **C, coverage-only (LP relaxation):** use the duals of the capacity and budget constraints to show the marginal value of one more charger or one more dollar at each site. Good OR content for the report.

## 6. Cost and benefit accounting

| | Metric | How |
|---|---|---|
| **Cost** | Capex | Σ x_jk × capex_k (undiscounted total), plus grid upgrades Σ y_j × F |
| | Annualised cost | capex × CRF + O&M (N5) |
| | Cost per kWh delivered | annual cost ÷ annual kWh served |
| **Benefit (financial)** | Operator gross margin | kWh served × (price − electricity cost) = S$0.37/kWh slow, S$0.60 fast |
| | NPV / payback | margin − O&M − capex over 10 yrs at 5% |
| **Benefit (users)** | Demand served (% of EV need) | 1 − Σs/ΣD |
| | Access | average distance from demand node to assigned charger, before vs after |
| | Driver fuel savings | EV-km enabled × (petrol cost/km − electricity cost/km), using N3/N4 |
| **Benefit (society)** | CO₂ avoided | EV-km × petrol g/km − kWh × grid EF (N1, N3) |
| | Value of CO₂ | t CO₂ × carbon price (N2) |
| **Summary** | Benefit-cost ratio | (margin + fuel savings + CO₂ value) ÷ annualised cost |

Caveat for the report: chargers *enable* EV use but don't cause all of it. Present user and society benefits as "attributable to served demand", not as fully caused by the chargers.

## 7. Scenarios and sensitivity

| Parameter | Low | Base | High |
|---|---|---|---|
| EV share of car fleet 2030 | 25% | 35% | 45% |
| Public-charging dependence (HDB) | 0.6 | 0.9 | 1.0 |
| Capex (all types) | −30% | base | +30% |
| Grid upgrade per site | S$0 | S$50k | S$250k |
| u_max (peak-safe utilisation) | 0.20 | 0.36 | 0.61 |
| Slow coverage radius | 250 m | 400 m | 800 m |
| Fast share of demand | 10% | 20% | 35% |
| Budget B | sweep S$10M → S$300M | | |

Report: which recommendations stay the same across scenarios (robust sites) vs which change, plus a tornado chart of the effect on total cost/benefit and the cost–benefit frontier.

## 8. Report outputs (8–10 pages, double-spaced)

1. Introduction and problem (½ p): adoption trend, uneven supply, 2030 target
2. Data and demand estimation (1½ p): pipeline diagram, assumptions table
3. Model formulation (2 p): sets, parameters, variables, objective, constraints
4. Results (2 p): map of new points; table by planning area; cost and benefit totals; comparison with an "even spread" baseline
5. Sensitivity (1½ p): tornado chart, budget frontier, robust sites
6. Recommendations and limitations (1 p)
7. Appendix: code (Gurobi), data sources, AI declaration

## 9. Work split and timeline (6 people)

| Workstream | Steps | People | Due |
|---|---|---|---|
| Geo and supply | 1, 2, 4 | 2 | 12 Nov |
| Demand | 3 (+ N6) | 1 | 12 Nov |
| Cost and benefit params | 5 (+ N1–N5) | 1 | 12 Nov |
| Model (Gurobi) | 6, 7 | 2 (start formulation now, code on 14 Nov) | 17 Nov |
| Report | 8 | everyone writes their own section | draft 20 Nov, final 22 Nov |

- **9 Nov (Mon) sync:** confirm the question, the model choice (A or B), units, and owners.
- **14 Nov (Sat) full group:** pipeline outputs ready → run base model together.
- **15–19 Nov:** scenarios, sensitivity, figures.
- **20–21 Nov:** write and edit.
- **22 Nov (Sun):** submit.

## 10. Decisions needed on 9 Nov

1. Demand node: HDB carparks only (recommended, simpler) or also condo/landed subzones?
2. Objective: A (min cost to meet demand) or B (max benefit within budget)? Recommendation: A for the base solution, B for the frontier.
3. Horizon: 2030 (base) or 2027?
4. Accept the cost assumptions in `cost_parameters.csv`, including grid upgrade, lifetime and discount rate?
5. Who collects N1–N5 (one person, ~2 hours)?
