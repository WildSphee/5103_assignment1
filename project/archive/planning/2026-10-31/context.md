# Project context — Optimising EV charging point placement in Singapore

_Last updated: 2026-10-31_. Full analysis plan, data pipeline and model: see `plan.md`.

## The assignment
- **Course:** MSBA group project (DBA5103), 6 members.
- **Deliverables:** mathematical model → linear/integer optimisation in **Python + Gurobi** → **sensitivity analysis** → **8–10 page double-spaced report**.
- **Hard deadline:** Sun **22 Nov 2026**.
- **Topic chosen:** Option A — where to place new EV charging points across Singapore. Rejected ideas: e-commerce, bank branch locations, government funding allocation.

## Team and timeline
Names come from the auto-transcribed meeting summary, which garbled some speaker tags, so confirm in the group chat.

| When | What | Who |
|---|---|---|
| ASAP | Share links/datasets from meeting chat to WhatsApp group | Sandra |
| ASAP | Poll for 9 Nov and 14 Nov meeting times | unassigned |
| by **9 Nov** (Mon) | Preliminary research: find EV demand + charging data sources | Aish, Reagan, +1 ("Speaker 3") |
| **9 Nov** | Data sync: review gathered data, refine problem statement, set data framework | data team (Sandra, Reagan, …) |
| **14 Nov** (Sat) | Full group (all 6): modelling, Gurobi implementation, report writing | everyone |
| **22 Nov** (Sun) | Submit | — |

Work is staged around Deepavali: 4 people do data first, then the full group builds the model and report.

## Background facts (for the report intro)
**EV adoption is accelerating**
- Electric cars: ~10.0k (Sep 2023), 21.8k (Sep 2024), 41.7k (Sep 2025), **74.9k (Sep 2026)**. That is ≈ 11.5% of ~651k cars. Source: LTA M09.
- All EVs (incl. taxis, buses, goods vehicles, motorcycles): ~85k (Sep 2026). LTA quoted 82,100 for Aug 2026.
- EV share of new car registrations: 6.9% (2022), 18.1% (2023), 33.6% (2024), 45.0% (2025), **63.1% (Jan–Sep 2026)**. Source: LTA M03.
- Policy: Singapore Green Plan 2030. All new car registrations must be cleaner-energy models from 2030. ICE vehicles are to be phased out by 2040. EV Early Adoption Incentive (ARF rebate, now capped at $7,500) **ends 1 Jan 2027**.

**Charging supply**
- National total: 13,800 points (Aug 2024), 30,500 (Mar 2026), **34,700 (Sep 2026)**.
- **Target: 60,000 by 2030**, split 40,000 in public carparks and 20,000 in private premises.
- LTA public register (our main dataset): **11,489 public charging points**, 9,279 chargers, 17,011 outlets, ~2,880 locations (Sep 2026).
  - ~85% are slow AC chargers (3.7–22 kW). ~14% are DC fast chargers (CCS2, 30–480 kW).
  - Top operators: SP Mobility, Charge+, ComfortDelGro ENGIE, Shell, Strides YTL.
- HDB carparks: the 2022 LTA tender (TD116) covers ~2,000 carparks with 3–12 points each, two operators per region. As of Mar 2026, **139 HDB carparks (7%) still have no charger** because of power constraints or community requests to delay.
- Plan: **at least one fast-charging hub (6–8 × 50 kW) in every HDB town by end-2027**.
- Most HDB chargers sit on the 3rd deck of multi-storey carparks.

**Demand / utilisation (only aggregate figures are public)**
- HDB charger utilisation was <10% (2024), ~10% (Sep 2025) and **~20% (May 2026)**, highest at night. JTC carparks are ~9%, highest by day.
- Peak 3-hour utilisation (Feb 2026): **36% across HDB carparks, 61% in Tengah**. Tengah, Punggol and Sengkang are highest. Bidadari slow chargers run at ~40%.
- ~8,800 EVs held HDB season parking (Sep 2024).
- LTA siting criteria: utilisation, **electrical capacity**, availability of parking lots, nearby charging options. These map directly to model constraints.

Full sources: `data/06_reports_and_policy/` (parliamentary replies, LTA releases, news).

## Data we have
See `data/README.md` for the full index. In short:

| Need | Have? | File(s) |
|---|---|---|
| Existing charger locations, power, operator | ✅ | `01_ev_charging_supply/LTA_EV_charging_points_Sep2026.csv` |
| Total EVs, trend, adoption rate | ✅ national only | `02_…/LTA_M09_…`, `LTA_M03_…` |
| EVs by location (town / postal code) | ❌ not published | must estimate with proxies |
| Candidate sites + capacity | ✅ | `03_…/HDB_carpark_information.csv` + `HDB_carpark_lots_snapshot_2026-10-31.csv` |
| Demand proxies by planning area | ✅ (2020) | `04_…/Census2020_*` (households by dwelling type, car-only commuters, income, workplace) |
| Boundaries for aggregation / maps | ✅ | `05_geospatial_boundaries/` |
| Chargers per planning area vs demand proxies | ✅ derived | `07_derived/planning_area_summary.csv` |
| Charger utilisation per site | ❌ | only national / estate figures in parliamentary replies |
| Electrical capacity per carpark | ❌ | not public; model as an assumption with a sensitivity range |
| Private chargers (~23k) | ❌ | only the total; the register is public chargers only |
| Charger capex (slow AC vs DC fast) | ⚠️ research-based | `08_costs/cost_parameters.csv`: base S$6.5k per 7 kW AC point, S$60k per 50 kW DC, S$120k per 100–150 kW DC. Uses ICCT, because SG doesn't publish these |
| Charging price, electricity cost, grants | ✅ official | `08_costs/`: median S$0.66/kWh at HDB, tariff 28.59¢/kWh, ECCG and EHVCG grant caps |
| Electrical / grid upgrade cost per site | ❌ assumption | base S$50k per site needing an upgrade (range 0–250k), from international evidence only |

**Early observation from `planning_area_summary.csv`:** large HDB towns have the fewest public points per 1,000 households. Examples: Bedok 4.7, Pasir Ris 4.9, Sengkang 5.9, Hougang 6.1, Punggol 6.7. Compare Jurong East 17.7 and Queenstown 13.4. Sengkang and Punggol also have high car-commuter counts and high reported utilisation, so they are natural "under-served" candidates. Caveat: this uses 2020 census households, so new towns like Tengah are under-counted.

## Possible model framing (to refine on 9 Nov)
- **Decision:** how many slow and fast charging points to add at each candidate site (HDB carparks, maybe URA/JTC/NParks carparks). Integer variables, plus a binary for whether a site is opened.
- **Demand nodes:** planning areas or subzones. Estimate EV demand as base car-ownership proxy (car-only commuters or households × car rate), × EV share (national 11.5% now, projected to 2030), × kWh per EV (from annual mileage × ~0.15–0.2 kWh/km), × share relying on public charging (high for HDB, low for landed).
- **Objective options:** (a) minimise cost to meet demand, or (b) maximise covered demand within a budget (maximal covering), or (c) p-median minimising EV-owner travel distance.
- **Constraints:**
  - Demand coverage within X km.
  - Points per carpark ≤ a share of car lots, and 3–12 per the tender.
  - Electrical capacity in kW per site.
  - Budget.
  - Reach the 40k public-carpark target by 2030.
  - At least 1 fast hub per HDB town.
  - Existing chargers count toward supply.
- **Sensitivity analysis:** EV adoption growth, budget, charger cost (slow vs fast), coverage radius, electrical capacity, utilisation target (20% → 36% → 61%), and the share of demand served by private chargers.

## Open questions for the team
1. Unit of analysis: planning area (55), subzone (332), or individual carparks (~2,000)?
2. Scope: all public carparks, or only HDB (where ~80% of residents live and home charging isn't possible)?
3. Time horizon: plan for 2030 (60k target) or the current gap?
4. Agree on cost parameters (`data/08_costs/cost_parameters.csv`): accept the ICCT-based capex, and choose charger lifetime, discount rate and grid-upgrade assumptions.
5. Should we request a free LTA DataMall API key for live charger availability (a utilisation proxy)?
6. Download SingStat June 2025 population by planning area/subzone manually to update the 2020 census figures?
