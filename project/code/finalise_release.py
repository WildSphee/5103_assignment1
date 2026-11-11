"""Write the human-readable execution record and final artifact hashes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import pandas as pd
from prepare_data import ROOT, OUT


def main():
    base=json.loads((OUT/'runs/base/metrics.json').read_text())
    summary=json.loads((OUT/'analysis_summary.json').read_text())
    layout=json.loads((OUT/'document_layout.json').read_text())
    sensitivity=pd.read_csv(OUT/'sensitivity.csv')
    validation=pd.read_csv(OUT/'validation_checks.csv')
    assert validation.status.eq('PASS').all()
    comparisons=pd.read_csv(OUT/'baseline_comparison.csv').set_index('name')
    certified=int((sensitivity.certified_service & sensitivity.certified_cost).sum())
    unit=base['annual_cost']/(365*summary['incremental_served'])
    text=f'''# Execution summary — HDB EV charging project

Completed 11 November 2026. The 9 November plan has been implemented using frozen
source data and its proposed scenario assumptions. No live data refresh, field
verification, external communication, commit or push was performed for this work.

## Deliverables

- [Report (DOCX)](HDB_EV_Charging_Report.docx) and [checked PDF](HDB_EV_Charging_Report.pdf).
- [Excel analysis workbook](HDB_EV_Charging_Analysis.xlsx), at the project root.
- [Python implementation and reproduction guide](code/README.md), including
  [requirements.txt](code/requirements.txt), the created `code/venv/`, model export,
  source hashes, numerical outputs, solver logs and figure assets.
- [Release checks](code/outputs/VALIDATION.md),
  [unit-test output](code/outputs/unit_test_results.txt), and
  [specific shortlist review](code/outputs/shortlist_desk_review.csv).

The report has **{layout['narrative_pages']} narrative pages**, one references page,
one cover page and appendices: {layout['total_pdf_pages']} pages overall. It follows
the seven-section skeleton, uses the supplied assignment's navy/blue visual style,
and includes formula pictures, five analytical figures and the complete computational
code appendix. Main body style is 12-point Times, double spacing and one-inch margins;
tables, captions and compact technical notes use smaller consistent styles.

## Main numerical findings

| Measure | Base result |
|---|---:|
| Candidate HDB sites | 2,273 |
| Estimated 2027 demand | {base['demand']:,.2f} kWh/day |
| Existing-only modelled service | {100*summary['no_build_fraction']:.2f}% |
| Additional AC points | {int(base['ac_points']):,} |
| Selected sites in the frozen base solution | {base['sites_selected']} |
| Capital investment | S${base['capital']:,.0f} |
| Demand served after additions | {100*base['service_fraction']:.2f}% |
| Incremental service | {summary['incremental_served']:,.2f} kWh/day |
| Annual infrastructure cost | S${base['annual_cost']:,.2f}/year |
| Annual cost / extra annual service | S${unit:.4f}/kWh, excluding electricity |

The 80%, 90% and 95% service targets have minimum-capex certificates at
**S$9.9125m, S$15.158m and S$17.784m**, respectively. Feasible plans attain the
point-count lower bound implied by the maximum service each new point can add.
These are scenario planning envelopes, not approved government budgets or quotes.

Equal allocation serves {100*comparisons.loc['equal','service_fraction']:.2f}%;
proportional allocation serves {100*comparisons.loc['proportional','service_fraction']:.2f}%;
greedy serves {100*comparisons.loc['greedy','service_fraction']:.2f}%.
**Greedy matches the MILP's base service at the same spend.** The MILP therefore
provides a certificate and an extensible formulation rather than an extra base-case
service gain over this greedy rule. Matched-spend comparison solves are retained.

## What was executed

1. An all-site register, labelled capacity imputation, address/distance supply
   crosswalk, registration-level power bounds, demand weights, stock scenarios,
   projected-distance arcs and source hashes.
2. A capacitated location MILP, continuous transportation LP, sequential service/cost
   objectives, fixed-investment minimum-distance allocation and LP service bound.
3. No-build, equal, proportional, exact-marginal greedy and MILP comparisons;
   target costs, physical maximum service and a six-point budget frontier.
4. **{len(sensitivity)} stress cases**, including demand, spatial proxies, supply matching,
   shared power, capacity, access, price, electrical headroom, lifecycle assumptions,
   AC/DC and 2030 outlook. Each includes a fixed-base-plan evaluation.
5. Scenario selection frequency, equal-budget shortlist replacement, repeated-input
   reproducibility, alternate seeds and a source-record review of the shortlist.
6. **9 expected-answer tests and {len(validation)} release checks**, including independent
   saved-flow/cost/feasibility reconciliation, source hashes, Excel formula caches,
   absence of spreadsheet error cells and PDF layout/page-count checks. All pass.

## Interpretation and unresolved evidence

The base supply is address-supported, not operator-confirmed. All 11,489 source
points remain in the crosswalk; provisional and unresolved records are not silently
treated as absent infrastructure. The 276 missing and two zero parking capacities
are retained with explicit assumptions and stress cases.

Main shortlist frequency uses the **{certified} cases with both objective passes
certified**, with all-feasible frequency shown separately. A solver's `Optimal`
status is within the declared relative gap, not a claim of exact arithmetic.
Time-limited service and cost incumbents retain their bounds and gaps. Some stressed
secondary cost gaps are substantial; those annual costs are attained costs, not
asserted minima. Regret intervals use valid service bounds and are only reported
when the fixed plan meets the scenario's construction limits and budget.

**JM18 and JM13** have stronger address evidence for proceeding to surveys.
**U15, J98M and U13** are supply-reconciliation holds: nearby points have unresolved
block/site identities. All still require electrical, access and installed-cost
verification. Replacement and alternate-seed checks show that the particular
site list is much less stable than the total service/cost result.

The 2030 figures are independent outlook cases, not a cumulative construction
schedule. The AC/DC extension selects zero new DC points under the tested base
costs; no fast-charging quota was invented. Queueing, stochastic recourse, a joint
multiyear programme and a dynamic programme were not needed for the agreed base
decision and are not falsely presented as completed extensions.

The workbook's input formulas expose demand arithmetic. Editing them does not
re-solve frozen optimisation outputs; use the Python reproduction workflow for
updated decisions. Existing research sources and assignment examples are preserved.
'''
    (ROOT/'EXECUTION_SUMMARY.md').write_text(text)
    artifacts=[ROOT/'HDB_EV_Charging_Report.docx',ROOT/'HDB_EV_Charging_Report.pdf',ROOT/'HDB_EV_Charging_Analysis.xlsx',ROOT/'EXECUTION_SUMMARY.md']
    manifest={'finalised_at_utc':datetime.now(timezone.utc).isoformat(),
              'note':'Numerical run_manifest.json preserves the solve-time snapshot. These hashes describe final document-generation code and released artifacts.',
              'artifacts':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in artifacts],
              'final_code_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')},
              'requirements_sha256':hashlib.sha256(Path(__file__).with_name('requirements.txt').read_bytes()).hexdigest()}
    (OUT/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Release summary and final artifact hashes saved.')


if __name__=='__main__':
    main()
