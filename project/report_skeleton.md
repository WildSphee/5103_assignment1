# Where should HDB add EV chargers, and what does each investment level deliver?

**Working report skeleton — 9 November 2026.** Seven main sections, approximately 11 narrative pages, plus references and appendices; adjust to the guideline's flexible 8–14-page suggestion. 12-point Times, double spacing, 1-inch margins. For review **15 November 2026, 11 a.m. Singapore time**. This is a structure, not a results report; no optimisation has been run.

## 1. Problem and decision (0.75 page)
Explain HDB residential charging and the two connected questions: where/how many additional points, and incremental service per investment dollar. Define all-HDB scope, one slow type in base, current supply and proposed 2027/2030 scenarios. Briefly motivate local adequacy without using all-public points as HDB supply. No carbon or petrol-savings angle.

## 2. Data and demand estimation (2 pages)
Compact source/assumptions table. Describe audited charger-to-HDB matching, unique point counts, missing capacity, normalised lot weights, national EV scenario calibration and grid-side energy demand. Explain population-geography vintages and why people, dwellings, parking lots and EVs are different units. Show observed/derived/assumed inputs separately. Reviewers: Sara/Sarah and Sandra.

## 3. Model and methodology (2 pages)
Cite facility-location/coverage literature. Define sets, variables and budget, power, space, access and demand constraints. Explain service-first then cost-minimising solves without an unmet-demand price. Explain why this is deterministic sequential optimisation. State what makes it different from a simple proportional deployment rule. Reviewers: Erica and Udhaya; build lead: Regan/Reagan.

## 4. Placement results and baseline comparison (2 pages)
**Awaiting validated model outputs.** Map confirmed existing and proposed HDB points. Table of site/area additions, spend and service. Compare no-build, equal allocation, proportional allocation, greedy and MILP under the same constraints. Report excluded/imputed data shares and solve status. If optimisation offers little improvement, state that.

## 5. Cost-effectiveness and budget choices (1.5 pages)
**Awaiting validated model outputs.** Plot incremental service versus capital spend; show annual cost and cost per extra annual kWh. Identify diminishing returns and budget alternatives without calling scenario amounts government budgets. Separate financial receipts from service benefits; no aggregate social benefit-cost ratio.

## 6. Sensitivity and extensions (2 pages)
**Awaiting validated model outputs.** Demand/cost/grid/access uncertainty, proxy and matching robustness; evaluate the proposed plan held fixed as well as scenario reoptimisation. Add AC/DC comparison if base model is complete. Show future demand outlook or a genuinely cumulative phased schedule, clearly distinguished. Reviewer: Aish; second reviewer/name duplication unresolved.

## 7. Recommendations and limitations (0.75 page)
**Awaiting validated model outputs.** Conditional shortlist and investment alternatives. Name the site-specific data needed before deployment: electrical survey, actual use, charger sharing limits, installed-cost quote and access checks. Explain model limitations without overstating queueing, observed demand or engineering feasibility. Integration owner remains to be assigned.

## References and appendices

Source URLs and dates; parameter evidence ledger; mathematical detail; data-quality/matching exceptions; complete Python/Gurobi code and run manifests; extra scenarios; any required AI-use declaration. Detailed implementation plan is `plan.md`; research findings are `data/09_research_audit/gap_review.md`.
