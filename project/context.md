# Project context — HDB EV charging placement and cost-effectiveness

_Last updated: 9 November 2026, after rereading the corrected full meeting transcript._

**Execution note — 10 November 2026:** The analysis, report and workbook have now been produced. See [EXECUTION_SUMMARY.md](EXECUTION_SUMMARY.md) and [code/README.md](code/README.md). The research-only statements below preserve the earlier planning context; they no longer describe implementation status.

**Presentation preference — 11 November 2026:** The user prefers planning-area allocations as the main showcase. The 28-area table describes **additional chargers for the end-2027 base demand scenario**, at a 90% service target. Current (September 2026 stock benchmark) and future (2027/2030) modelled energy shortfalls are now explicit. The five western site-review examples are appendix evidence, not the national deployment list. Future shortfalls hold the 2027 plan fixed with no further expansion; a separate 2030 target-cost plan has not been solved.

## Agreed direction

1. **Where and how many charging points to add in HDB carparks throughout Singapore.** Private estates and other-agency placement are outside scope.
2. **Cost-effectiveness of each investment level:** extra charging demand served and access achieved per infrastructure dollar.

These are two questions answered by one facility-location model. Base additions use one slow charger type; fast chargers are an enhancement/sensitivity. Carbon, carbon tax and petrol-savings analysis are removed. Do not revive the old social benefit-cost ratio or unsupported unmet-demand penalty.

The full transcript confirms these decisions at 00:09:56–00:15:57 and 00:16:20–00:18:02. At 00:25:04–00:26:41 the team prefers investigating two optimisation steps to avoid guessing an unmet-demand price. Proposed approach: maximise demand served within each illustrative budget, then minimise cost while preserving service. This is **deterministic sequential/lexicographic optimisation**, not automatically stochastic two-stage recourse.

## Deliverable and dates

- DBA5103 group report, with defined mathematical model, methodology, citations, results/sensitivity and code appendix; Python/Gurobi remains the intended implementation.
- Course guideline suggests **8–14 narrative pages**, with no strict page limit; 12-point Times, double-spaced, 1-inch margins. Previous “8–10-page requirement” was inaccurate.
- **Next meeting: Sunday 15 November 2026, 11:00 a.m. Singapore time. Report skeleton ready then.** The transcript's final agreement at 00:34:06–00:34:31 and 00:35:51 supersedes the previous 14 November slot and handwritten “15th 10am”.
- Submission deadline retained from earlier project context: **22 November 2026**; not independently established by the guideline PDF.
- Final deliverable is a report, not a presentation.

## Current work and entry points

- [Detailed internal plan](plan.md): selected datasets, cleaning/join rules, demand calibration, formulation, cost accounting, comparisons, sensitivity, phasing, checks and proposed workflow. Current planning defaults (7.4 kW, 2027 base/2030 outlook, budgets/radius) remain proposals rather than meeting decisions.
- [Report skeleton](report_skeleton.md): seven main sections, approximately 11 narrative pages; result slots deliberately unfilled.
- [Data index](data/README.md): original files plus new official population/housing series, GHS 2025 and Population Trends 2026 PDFs, Singapore vendor cost evidence, MOT evidence and methodological sources.
- [Gap review](data/09_research_audit/gap_review.md), [meeting reconciliation](data/09_research_audit/meeting_decisions.md), [source manifest](data/09_research_audit/source_manifest_2026-11-09.csv), and [file inventory](data/09_research_audit/file_inventory.csv).
- Research scripts: `scripts/fetch_research_sources.py`, `scripts/audit_research_data.py`; dependencies in `requirements-research.txt`. Review tables are in `data/07_derived/` and `data/09_research_audit/`.
- **Research, profiling and planning have been done; optimisation and final report results have not.** HDB supply matches remain review candidates, not confirmed assignments.

## Important evidence and corrections

- HDB master: **2,273 sites**. Car-lot data match **1,997**, with **276 missing** and **2 zero** capacities. Matched car lots total **706,663**; do not treat parking lots as unique cars or EVs.
- Public charger file: **11,489 unique point IDs**, **9,279 registration codes**. The previous 17,011 outlet total double-counted a registration-level field repeated on each point row; corrected total is **11,489**. Legacy summary script and outputs are corrected, but still cover **all public chargers**, not HDB-only supply. Two points fall outside the MP2019 area join (11,487 mapped + 2 exceptions). Summed point kW is not verified simultaneous cabinet capacity.
- Nearest-site matching is insufficient: **543 exact-coordinate charger locations have multiple HDB sites within 100 m**. Use address evidence and manual review. Do not label “no matched charger” as “no charger” or as zero grid headroom.
- Demand should normalise spatial lot weights to a separately estimated HDB EV total. Historical 8,800 HDB season-parking EVs (Sep 2024) is a weak calibration anchor, not a current or site-level count.
- New official small-area tables close much of the demographic gap. **2025 uses MP2019; 2026 uses MP2025.** Keep vintages explicit. Population, housing stock, households and cars have different denominators; rounded demographic cells are approximate.
- Site utilisation, spare electrical power and actual installed HDB cost remain unobserved. Vendor hardware/maintenance prices support cost scenarios but do not establish an HDB installed quote. Peak three-hour utilisation is not a full-day energy-capacity factor.
- The 40,000-public-point target is not an HDB-only constraint; old tender quantities are not engineering maxima. Condo/heavy-vehicle grants do not belong in the base model.
- GHS full report obtained; detailed transport workbook was not retrieved (blocked/app-shell response). Original Church–ReVelle publisher full text was blocked; metadata located, alternative official methodology and related author manuscript downloaded.

## Team review responsibilities

Provisional spellings from the notes: Regan/Reagan builds and coordinates; Sara/Sarah and Sandra review data; Erica and Udhaya review the model; Aish reviews sensitivity. “Aish, Aish” is duplicated in the notes and does not establish a second reviewer. Report integration owner remains unassigned. Do not infer names from speaker numbers.

## Archive and version-control state

Both meeting files are preserved unchanged under [archive/meetings/2026-11-09/](archive/meetings/2026-11-09/), with SHA-256 hashes. The updated transcript is the full 32,742-byte version, not the duplicate summary originally seen. Previous plan/context/cost table/data index are in `archive/planning/2026-10-31/` and are historical only.

**Version control:** The user subsequently authorised committing and pushing this research update on 9 November 2026; this supersedes the earlier hold.

**Compact presentation update, 11 November:** Retain all analytical figures at smaller sizes; keep planning areas as the main showcase and add a top-100 review-candidate map. Following the typography review, report text, headings, tables, captions and notes use 12-point Times New Roman, double spacing and one-inch margins, as specified by the guideline; code listings retain monospace formatting. The map is a deterministic ranking within the end-2027 base selection, not a separately optimised build plan.
