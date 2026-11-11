# HDB EV charging model

This folder contains the complete Python implementation, its virtual environment,
frozen model inputs, solver logs, scenario results, report images and validation.
The readable deliverables are one level above this folder:

- `HDB_EV_Charging_Report.docx` and the visually checked PDF.
- `HDB_EV_Charging_Analysis.xlsx` (formulas, results and audit ledgers).

The main showcase is `Area_Deployment_2027`: 28 planning areas receiving additional
AC points for the **end-2027 base demand case**, with a 90% national service target.
`Year_Outlook` separates the September 2026 EV-stock benchmark, end-2027 scenarios
and 2030 demand stresses. Shortfall means modelled unmet grid energy, not observed
missing charger counts. Future supply is either the frozen existing register or
that register plus the same 2027 additions, with no further expansion. The five
site-review examples are appendix evidence, not the island-wide deployment list.

## Run

The supplied environment is `project/code/venv/`. Python 3.14 is the tested runtime.
All installed packages are pinned in `requirements.txt`; HiGHS requires no licence.
LibreOffice is a system dependency only for DOCX-to-PDF rendering.

From the repository root:

```bash
python3 -m venv project/code/venv
project/code/venv/bin/python -m pip install -r project/code/requirements.txt
project/code/venv/bin/python project/code/reproduce.py
```

The complete scenario study can take tens of minutes. Completed numerical solves
are cached using source hashes, parameters, budget, objectives and implementation
fingerprints. Original statuses and gaps remain attached to cached incumbents.
`cache_compatibility.json` explicitly records a solver-only implementation change
that preserves the mathematical model; it does not turn old incumbents into
optimal solutions. Delete `outputs/runs/` to request a fresh solve of every case.

Individual stages can also be run with the same environment:

```bash
project/code/venv/bin/python project/code/prepare_data.py
project/code/venv/bin/python project/code/test_models.py
project/code/venv/bin/python project/code/run_analysis.py --mode all
project/code/venv/bin/python project/code/review_shortlist.py
project/code/venv/bin/python project/code/audit_outputs.py
project/code/venv/bin/python project/code/build_figures.py
project/code/venv/bin/python project/code/build_workbook.py
project/code/venv/bin/python project/code/build_report.py
```

`--mode core` runs targets, the frontier, comparisons and the LP bound.
`--mode sensitivity` runs stresses, fixed-plan evaluation, replacement and repeat
checks; it uses the same target/base setup. The default is three independent solver
processes with one thread each; `--workers 1` runs scenarios serially. `--mode finalize`
rebuilds the shortlist and reproducibility checks from completed scenario files.
`reproduce.py` also renders the PDF,
checks page count and workbook caches, then includes the final checks in Excel.

## Files and methods

| File | Role |
|---|---|
| `prepare_data.py` | Source validation, HDB register, address/distance crosswalk, capacity bounds, demographic and national stock scenarios |
| `model.py` | Continuous max-flow/min-distance LP and integer AC/DC location model, sequential objectives, residual checks |
| `baselines.py` | Equal allocation, Hamilton proportional allocation with repair, exact reassigned-flow marginal greedy |
| `run_analysis.py` | Service-target certificates, budget frontier, sensitivity, fixed-plan stress, site replacement and repeatability |
| `test_models.py` | Hand-solvable model and source-reconciliation tests |
| `audit_outputs.py` | Independent saved-flow, cost, feasibility, source-hash and Office-artifact checks |
| `review_shortlist.py` | Specific source-record findings and supply-reconciliation holds for the five candidates |
| `build_figures.py` | Matplotlib charts and formula pictures |
| `build_workbook.py` | Excel tables, cached formulas and native chart |
| `build_report.py` | Concise report and complete computational code appendix |
| `reviews/match_sample.csv` | Frozen 48-location desk review; not field verification |

The existing research scripts and raw sources in `project/data/` are preserved.
New outputs go only to `code/outputs/`, except the final DOCX, PDF and XLSX in
`project/`. The virtual environment is ignored by Git. No external messages,
account registrations or data refreshes are part of this pipeline.

## Interpretation and modelling choices

- All 2,273 HDB sites remain as demand nodes and investment candidates. The 276
  missing and two zero capacities are flagged and imputed, with separate tests.
- Base supply is **address-supported**, not confirmed by operators or site visits.
  Range/near-street matches remain sensitivity-only; unresolved records are retained.
- Existing supply uses the largest port rating per registration. Sum-port power is
  an alternative, not verified simultaneous output. Existing DC is retained.
- The 2027 stock path is a stated stock-flow scenario, not a fitted forecast.
  The 2030 25/35/45% fleet cases are illustrative. Housing/geography vintages stay
  separate. Parking lots weight geography; they do not estimate car ownership.
- All base monetary amounts are constant 2026 scenario SGD excluding GST. Ordinary
  installation is already included in per-point cost; no fixed mobilisation cost
  is added. Existing sunk investment, electricity and operator receipts are excluded.
- The model applies LP/network flow, MILP and relaxation bounds. Dynamic programming
  is not needed for this static placement problem. The growth plots are an outlook,
  not a jointly optimised multiyear build schedule.
- Service is kWh/day, not measured use or queue performance. Straight-line distance
  and cross-carpark parking access are assumptions. Site engineering is unverified.

## Numerical certification

HiGHS runs with one thread, fixed seed, base relative MIP gap 0.0001 and sensitivity
gap 0.001. Limits are per solve; occasional solver heuristic overshoot is logged.
`Optimal` means certified within the declared solver tolerances. A time-limited
incumbent stays labelled as such. The second objective preserves the first incumbent
within `max(1e-6, 1e-8 * total demand)` kWh/day; if the first solve lacks a certificate,
the result is an approximate priority solution.

For the AC-only service targets, each added point can supply at most `q`. At least
`ceil((target - existing_only_max_service) / q)` points are therefore necessary.
When an actual feasible plan reaches that count with no upgrade premium, its capex
attains a global lower bound. This separately certifies minimum target capex even
if a secondary location tie-break is time-limited.

Fixed-plan evaluations hold base additions and upgrade binaries constant. Tightened
power/space assumptions derate usable added energy; investment counts are retained.
Construction violations and repriced budget violations are flagged. Regret is only
reported for a fixed plan feasible under the comparison scenario; other differences
are descriptive shortfalls. Regret lower and upper bounds use the attained service
and the solver's service bound; a time-limited incumbent is not treated as the exact
scenario optimum. Main shortlist frequency uses scenarios with both objective passes
certified, with all-feasible frequency retained separately. Selection frequency is not
a probability. The shortlist also requires observed capacity and night parking.

The complete workbook is an audit and presentation artifact. Editing Parameters
updates demand arithmetic but **does not re-solve the optimisation**. Change the
Python parameters/scenario definitions and rerun to produce revised recommendations.

## Remaining deployment evidence

Operator-confirmed charger/site membership and sharing limits; actual residential EV
counts, sessions and energy; walking and parking access; spare electrical headroom;
site-specific installation and upgrade quotes. These are explicit limits of the
decision-support result, not fabricated observations.

### Compact report and top-100 map

The report follows page 1 of `sources/references/Project_Guideline.pdf`: 12-point Times New Roman, double spacing and one-inch margins. Headings, body text, tables, captions and notes share that typography. Code listings retain 7.2-point, single-spaced Courier New for indentation; figure labels use Times-style serif lettering and scale with their images. On render hosts without Times New Roman, LibreOffice uses the metrically compatible Liberation Serif substitute. The suggested 8–14 narrative pages are not a strict limit. All analytical figures remain; equations are images.

`build_showcase.build_top100()` filters the saved end-2027 selection to observed parking capacity and night parking, then ranks by certified-scenario selection frequency (descending), base additions (descending), and carpark ID (ascending). The top 100 contain 528 proposed AC points across 21 planning areas. This is a site-review order, not a new 100-site optimisation or a probability ranking. `outputs/top_100_recommended_sites.csv` and `.geojson` preserve every address and WGS84 coordinate; `Top_100_Sites` in Excel mirrors the map. The 90% service claim applies only to the full 549-site plan.
