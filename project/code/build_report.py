"""Concise report in the supplied assignment style, with equations as pictures."""
import json
from pathlib import Path
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from prepare_data import ROOT, OUT, INPUTS

NAVY='19384B'; BLUE='347594'; FIG=OUT/'figures'


def shade(cell,fill):
    el=OxmlElement('w:shd');el.set(qn('w:fill'),fill);cell._tc.get_or_add_tcPr().append(el)


def link(paragraph,label,url):
    rel=paragraph.part.relate_to(url,'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True)
    h=OxmlElement('w:hyperlink');h.set(qn('r:id'),rel)
    r=OxmlElement('w:r');pr=OxmlElement('w:rPr');col=OxmlElement('w:color');col.set(qn('w:val'),BLUE);pr.append(col);r.append(pr)
    t=OxmlElement('w:t');t.text=label;r.append(t);h.append(r);paragraph._p.append(h)


def main():
    base=json.loads((OUT/'runs/base/metrics.json').read_text())
    summary=json.loads((OUT/'analysis_summary.json').read_text())
    audit=json.loads((INPUTS/'data_audit.json').read_text())
    comparisons=pd.read_csv(OUT/'baseline_comparison.csv').set_index('name')
    frontier=pd.read_csv(OUT/'budget_frontier.csv')
    sens=pd.read_csv(OUT/'sensitivity.csv').set_index('name')
    replacement=pd.read_csv(OUT/'shortlist_replacement.csv')
    desk=pd.read_csv(OUT/'shortlist_desk_review.csv')
    robust=pd.read_csv(OUT/'site_robustness.csv').set_index('car_park_no')
    sites=pd.read_csv(OUT/'runs/base/site_decisions.csv')
    areas=pd.read_csv(OUT/'runs/base/area_results.csv').sort_values('ac_additions',ascending=False)
    reproducibility=json.loads((OUT/'reproducibility.json').read_text())
    manifest=json.loads((OUT/'run_manifest.json').read_text())
    targets=pd.read_csv(OUT/'service_targets.csv')
    d=Document();sec=d.sections[0]
    sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)
    sec.top_margin=sec.bottom_margin=sec.left_margin=sec.right_margin=Inches(1)
    sec.header_distance=sec.footer_distance=Inches(.4)
    sec.different_first_page_header_footer=True
    styles=d.styles
    normal=styles['Normal'];normal.font.name='Times New Roman';normal.font.size=Pt(12)
    normal.paragraph_format.line_spacing=2;normal.paragraph_format.space_after=Pt(5)
    normal.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    for name,size in [('Title',27),('Heading 1',17),('Heading 2',13)]:
        styles[name].font.name='Arial';styles[name].font.size=Pt(size);styles[name].font.color.rgb=RGBColor.from_string(NAVY)
        styles[name].paragraph_format.line_spacing=1.1
        styles[name].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT
        styles[name].paragraph_format.space_after=Pt(9)
    for name,size,font in [('Caption',9,'Arial'),('Small',10,'Times New Roman'),('Code',7.2,'Courier New')]:
        if name not in styles:styles.add_style(name,1)
        st=styles[name];st.font.name=font;st.font.size=Pt(size)
        st.paragraph_format.line_spacing=1;st.paragraph_format.space_after=Pt(5 if name!='Code' else 0)
    styles['Caption'].font.color.rgb=RGBColor.from_string('647580')
    h=sec.header.paragraphs[0];h.text='DBA5103  |  OPERATIONS RESEARCH AND ANALYTICS'
    h.style='Caption';h.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    foot=sec.footer.paragraphs[0];foot.alignment=WD_ALIGN_PARAGRAPH.CENTER
    run=foot.add_run();field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');run._r.addnext(field)

    def para(text,style=None):return d.add_paragraph(text,style)
    def page(title):d.add_page_break();d.add_heading(title,level=1)
    def picture(name,width=6.15,caption=None):
        p=d.add_paragraph();p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(2);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(FIG/f'{name}.png'),width=Inches(width))
        if caption:
            p=para(caption,'Caption');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    def table(headers,rows,widths=None):
        t=d.add_table(rows=1,cols=len(headers));t.autofit=False
        if widths:
            for c,w in zip(t.columns,widths):c.width=Inches(w)
        for j,h in enumerate(headers):
            t.rows[0].cells[j].text=str(h);shade(t.rows[0].cells[j],NAVY)
        for i,row in enumerate(rows):
            cells=t.add_row().cells
            for c,v in zip(cells,row):c.text=str(v)
            if i%2==0:
                for c in cells:shade(c,'EEF3F5')
        for i,row in enumerate(t.rows):
            pr=row._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(5);p.paragraph_format.space_before=Pt(5)
                    for r in p.runs:
                        r.font.name='Arial';r.font.size=Pt(9)
                        if i==0:r.font.bold=True;r.font.color.rgb=RGBColor(255,255,255)
            if widths:
                for c,w in zip(row.cells,widths):c.width=Inches(w)
        return t
    def callout(text):
        t=d.add_table(rows=1,cols=1);shade(t.cell(0,0),'EDF3F6')
        p=t.cell(0,0).paragraphs[0];p.paragraph_format.line_spacing=1.35
        r=p.add_run(text);r.bold=True;r.font.color.rgb=RGBColor.from_string(NAVY);r.font.size=Pt(12)
    money=lambda x:f'S${x/1e6:.3f}m'
    pct=lambda x:f'{100*x:.1f}%'

    p=para('');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    logo=ROOT.parent/'sources/assignment 1/nus_logo.png'
    if logo.exists():p.add_run().add_picture(str(logo),width=Inches(2.8))
    p=para('DBA5103');p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.runs[0].bold=True
    p=para('Operations Research and Analytics');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p=para('HDB EV Charging','Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p=para('Placement and Cost-Effectiveness');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    para('')
    p=para('A capacitated facility-location study\n2027 planning case and 2030 outlook');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    para('')
    p=para('Semester I, Academic Year 2026/2027\nMSBA | National University of Singapore\n11 November 2026');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    para('Reproducible model results for team review. Source vintages, assumptions and numerical certificates are preserved in the companion workbook and Python appendix.','Small')

    page('1. Problem and decision')
    para('National charger counts do not establish whether residents can charge near home. This study asks where additional slow charging points should be installed in HDB carparks, and how much extra charging service each investment level delivers. The decision concerns infrastructure expenditure across participating parties; it is not a government budget proposal.')
    para('The analysis retains all 2,273 HDB carparks. Existing address-supported supply is fixed, including existing DC equipment. New base-case additions are 7.4 kW AC points. A capacitated location model combines integer investment choices with continuous energy allocation between nearby carparks. Non-HDB investment, carbon valuation and petrol savings are outside scope.')
    callout(f'Base result: {int(base["ac_points"]):,} additional AC points at {money(base["capital"])} serve {pct(base["service_fraction"])} of estimated 2027 demand, versus {pct(summary["no_build_fraction"])} using matched existing supply alone.')
    para('This result is conditional on proxy demand, incomplete supply identification and assumed access and electrical capacity. The analysis therefore compares simple allocation rules, varies the principal assumptions, and evaluates the proposed investment while holding its locations fixed. The output is a reviewable planning framework and conditional shortlist, rather than an installation-ready design.')

    page('2. Data and demand estimation')
    table(['Input','Frozen evidence / treatment'],[
        ('HDB candidate sites [1]','2,273 unique IDs; projected SVY21 coordinates.'),
        ('Car-lot snapshot [1]','31 Oct 2026; 706,663 matched lots; 276 missing and 2 zero records.'),
        ('Public charger register [2]',f'Sep 2026; 11,489 unique points, 9,279 registrations; {audit["match_counts"]["address_supported"]:,} base matched points.'),
        ('Vehicle stock / flows [3]','Cars/Electric only; Sep 2026 stock 74,887. Other fuels retained only in the all-car denominator.'),
        ('Housing / population [4]','2025 with MP2019 geography; 2026 with MP2025 separately.'),
        ('Costs and operation [5–7]','Vendor components and historical public-carpark usage inform scenarios; no site-level HDB quote or utilisation panel.')], [1.8,4.35])
    para('Base supply requires a unique literal block and normalised street match within 150 metres, with non-HDB-looking buildings excluded. Registration conflicts are not assigned. The broader sensitivity adds block-range and same-street candidates. A 48-location desk sample checks the source records; neither this check nor proximity establishes ownership on site.')
    para(f'Missing or zero lot counts use an area/carpark-type median with at least five observations, falling back to type and then national medians. This adds {audit["imputed_lots"]:,.1f} assumed lots. All demand remains represented; no-build at unknown-capacity sites and 0.5×/1.5× imputations test the effect. The complete exceptions and match ledgers accompany the workbook.')

    page('2.1 Demand, capacity and scenario assumptions')
    picture('formula_demand',6.05,'Demand D is grid-side kWh/day. Spatial weights sum to one; lots are not vehicle counts.')
    table(['Parameter','Base','Interpretation'],[
        ('National EV stock E','117,116.83','2027 assumption from stock-flow identity'),
        ('HDB share h / dependence β','0.40 / 0.80','HDB-associated EVs / energy sought here'),
        ('Mileage m / intensity e','16,200 / 0.16','km/year / battery kWh per km'),
        ('Efficiency η','0.90','Battery energy divided by grid energy'),
        ('Catchment / lot share','400 m / 10%','Straight-line access / assumed space limit'),
        ('Spare power / upgrade','44.4 / 88.8 kW','Incremental power beyond existing load')],[2.1,1.3,2.75])
    para(f'The base allocates {base["parameters"]["stock"]*.4:,.0f} estimated HDB-associated EVs by normalised car-lot weights, yielding {base["demand"]:,.0f} kWh/day. The 0.40 share is only weakly anchored by 8,800 HDB season-parking EVs versus 21,796 national electric cars in September 2024 [5]. Housing and population weights provide alternatives.')
    picture('formula_capacity',6.05,'Registration maximum-port power is the conservative bound; summed port power is a sensitivity.')
    para('Effective hours, uptime and accepted-power factors are design assumptions. The public-carpark average of about five hours/day in 2026 does not measure HDB-only delivered energy [6]. Charging losses enter demand once; the power factor represents accepted charging rate. Capacity does not guarantee short queues.','Small')

    page('3. Model and methodology')
    para('This capacitated facility-location model extends coverage planning with energy flows, existing facilities, integer point counts and optional electrical upgrades [8,9]. Demand nodes i and candidate sites j are HDB carparks. An arc exists only within the assumed catchment; cross-area arcs remain permitted.')
    table(['Symbol','Meaning'],[('xⱼ; zⱼ; yⱼ','AC points; activation binary; upgrade binary'),('fᵢⱼ; sᵢ','Served and unmet grid-side kWh/day'),('Q⁰ⱼ; q','Existing and per-new-point effective daily capacity'),('Mⱼ; L̄ⱼ; b⁰ⱼ','Addition bound; total bay limit; existing occupied bays')],[1.7,4.45])
    picture('formula_model',5.2)
    para('The rows conserve demand, limit service capacity, link binary and integer decisions, enforce incremental power and parking space, and impose a capital budget. The bay limit is max(existing bays, floor(0.10 × lots)); existing installations are grandfathered. One connector per existing bay is a conservative base assumption, tested against deduplicated floor/lot labels.','Small')
    para('Unmet demand preserves feasibility even when access or capacity is insufficient. The implementation eliminates s as demand minus outgoing flow, without changing the model. No observed spare-power capacity is claimed.','Small')

    page('3.1 Objectives, cost and numerical checks')
    picture('formula_objectives',5.7)
    para(f'Pass 1 maximises served energy. Pass 2 minimises annual infrastructure cost while retaining service within ε = {base["service_lock_epsilon"]:.6f} kWh/day. These are sequential deterministic objectives, not stochastic two-stage recourse. A fixed-investment transportation LP then minimises energy-weighted travel distance without losing service.')
    picture('formula_cost',6.05)
    para('Base capex is S$6,500 per AC point, including ordinary installation; no extra mobilisation fee is added. Annual maintenance and network reserves total S$580 per point. A 10-year life and 5% rate annualise capital. Upgrade cost is S$50,000 per site. All are constant 2026 scenario dollars excluding GST; electricity, sunk investment and operator revenue are excluded [7].')
    para('A useful certificate follows from network flow: each new point adds at most q kWh/day. A service target therefore needs at least ceil((target − existing-only service)/q) points. Feasible plans attaining that count with no upgrade premium certify minimum capex. Tiny expected-answer cases test integrality, upgrades, sharing, disconnected demand and infeasibility; national runs check constraint residuals and service locks.','Small')

    page('4. Placement results')
    picture('placement_map',6.2,'Figure 1. Existing address-supported supply and one optimal base allocation. Circle area indicates point quantity.')
    para(f'The base plan adds {int(base["ac_points"]):,} AC points across {base["sites_selected"]:,} sites, with {base["upgrades"]} modelled upgrades. It delivers an additional {summary["incremental_served"]:,.0f} kWh/day. Existing matched capacity and nearby sharing jointly determine the additions; a site’s point count alone is not its marginal system benefit.')
    table(['Planning area','New points','Capital','Demand served'],[
        (r.area_2019.title(),f'{int(r.ac_additions):,}',money(r.capex),pct(r.served_kwh_day/r.demand_kwh_day)) for r in areas.head(5).itertuples()],[2.1,1.0,1.3,1.75])
    para(f'Imputed-capacity sites receive {pct(base["imputed_investment_share"])} of base expenditure. These locations require capacity verification before implementation. The map shows one tied solution; it does not imply that every selected site is indispensable.','Small')

    page('4.1 Comparison with simple rules')
    picture('comparators',6.05,'Figure 2. Same modelled demand and feasibility rules. Actual expenditure is reported below.')
    table(['Allocation','Capital','AC points','Served'],[
        (label,money(comparisons.loc[name,'capital']),f'{int(comparisons.loc[name,"ac_points"]):,}',pct(comparisons.loc[name,'service_fraction']))
        for name,label in [('equal','Equal'),('proportional','Proportional'),('greedy','Greedy'),('base','MILP')]],[2.0,1.45,1.2,1.5])
    prop=comparisons.loc['proportional'];greedy=comparisons.loc['greedy']
    gain=100*(base['service_fraction']-prop.service_fraction)
    para(f'The MILP improves service over proportional placement by {gain:.2f} percentage points. Equal allocation cycles through eligible site IDs; proportional allocation uses largest remainders and feasibility repair. Neither rule directly accounts for overlapping catchments or unused existing capacity.')
    greedy_conclusion='Greedy matches the MILP to numerical tolerance in this base case; the MILP chiefly supplies an optimum certificate here.' if abs(greedy.service_fraction-base['service_fraction'])<1e-5 else 'The numerical gap measures what the MILP adds beyond this practical greedy rule.'
    para(f'Greedy placement chooses additional served energy per step dollar, including upgrade thresholds and full flow reassignment. Its service is {pct(greedy.service_fraction)}, versus {pct(base["service_fraction"])} for the MILP. {greedy_conclusion} The workbook also reoptimises each rule’s actual spend; time-limited comparison incumbents retain their gaps.','Small')

    page('5. Cost-effectiveness and budget choices')
    picture('budget_frontier',6.1,'Figure 3. Discrete actual-spend frontier. Points are computed scenarios, not a smooth forecast.')
    table(['Service target','Minimum capital','Certificate'],[
        (f'{int(float(r.name.split("_")[-1]))}%',money(r.capital),'Capacity lower bound attained' if getattr(r,'certified_target_capex',False)==True else 'See solver gap')
        for r in targets.itertuples()],[1.2,1.65,3.3])
    unit=base['annual_cost']/(365*summary['incremental_served'])
    para(f'At the base budget, annualised infrastructure cost is {money(base["annual_cost"])}/year, or S${unit:.3f} per additional annual kWh served. This excludes electricity and is not a charging tariff or a social benefit-cost ratio. It divides incremental annual infrastructure cost by service above the fixed existing-only baseline.')
    marginal=frontier.marginal_capex_per_extra_annual_kwh.dropna()
    para(f'Across the computed budget intervals, marginal capex per extra annual kWh ranges from S${marginal.min():.3f} to S${marginal.max():.3f}. A nearly constant slope is possible while each added point remains fully useful; diminishing returns must be observed, not presumed. The physically bounded maximum service is {pct(summary["maximum_physical_fraction"])} under the base assumptions.','Small')

    page('6. Sensitivity and fixed-plan performance')
    picture('sensitivity',6.15,'Figure 4. Selected stresses at the base nominal budget. *Fixed-plan capacity is derated where power/space assumptions invalidate operation; repriced capex may exceed budget.')
    broad=sens.loc['broad_supply'];lowhours=sens.loc['hours_4'];selfonly=sens.loc['self_site_only']
    para(f'Broader supply matching changes reoptimised service to {pct(broad.service_fraction)}. Four effective charging hours reduce it to {pct(lowhours.service_fraction)}; restricting service to the home carpark gives {pct(selfonly.service_fraction)}. These differences show why supply identification, usable hours and access rules must be checked before converting model outputs into construction decisions.')
    count=len(sens);limited=int(sens.pass1_status.ne('Optimal').sum())
    para(f'The workbook contains {count} specified stress cases, each with a fixed-plan evaluation and reoptimisation. {limited} service solves lack optimal status; bounds and gaps remain visible. Secondary cost gaps can be larger, so stressed annual costs are attained costs, not automatically minimum costs. Feasible fixed-plan regret is bounded using the scenario incumbent and service bound. Scenario frequencies are not probabilities.','Small')

    page('6.1 Growth, technology and conditional shortlist')
    picture('outlook',6.05,'Figure 5. Independent stock scenarios at the same budget. These are an outlook, not a cumulative construction schedule.')
    dc=sens.loc['ac_dc_extension']
    para(f'The 2027 base uses 15 months of the Jan–Sep 2026 mean electric-car registrations, less an assumed 2% exit fraction. The 2030 cases use 25/35/45% of the frozen 651,003-car fleet; they are not official forecasts. The mixed AC/DC extension selects {int(dc.dc_points)} new 50 kW DC points and serves {pct(dc.service_fraction)}. Substitutable energy demand provides no evidence for forcing a fast-charging quota.')
    table(['Review candidate','AC points','Selection frequency'],[
        (f'{r.site_id} · {robust.loc[r.site_id,"area_2019"].title()}',int(r.base_additions),pct(r.selection_fraction)) for r in replacement.itertuples()],[3.3,1.0,1.85])
    para(f'Candidates have observed capacity and night parking. Frequencies use {int(robust.scenario_count.iloc[0])} stress cases with both objectives certified; unfinished cost minimisations are excluded from ranking. Equal-budget replacement losses appear in the workbook. Alternate seeds yield a site-set overlap of {pct(reproducibility["alternate_seed_site_jaccard"])} (Jaccard); review equivalent alternatives alongside these candidates.','Small')

    page('7. Recommendations and limitations')
    para(f'Use {money(base["capital"])} as the conditional 90%-service planning envelope for this demand and supply specification. The lower-bound certificate supports the point count and budget, while the baseline comparisons test whether optimisation materially improves placement. Do not interpret the envelope as an approved appropriation or a universal optimum.')
    table(['Before construction','Why it can change the decision'],[
        ('Confirm supply and access','Check existing HDB ownership, shared cabinet output, bay labels, walking routes and parking entitlement.'),
        ('Measure local demand','Obtain resident EV counts, session energy and occupation patterns; update spatial weights and effective hours.'),
        ('Survey electrical feasibility','Verify spare headroom and obtain a site-specific upgrade design and installed-cost quotation.'),
        ('Stage and rerun','Prioritise observed-capacity review candidates; verify uncertain sites before committing their allocations. Reoptimise after measured changes.')],[2.1,4.05])
    ready=', '.join(desk.loc[desk.review_gate.str.startswith('Source-supported'),'site_id'])
    held=', '.join(desk.loc[~desk.review_gate.str.startswith('Source-supported'),'site_id'])
    para(f'The desk review supports taking {ready} forward for surveys. Hold {held} for supply reconciliation. At J98M, six points share an address with two HDB IDs. A missing base match is not evidence of no supply. Equal-budget replacement solves recover nearly all service, so these candidates are not indispensable locations.')
    para('Demand remains a spatial proxy. Conservative matching can inflate apparent need, and uniform headroom, costs and charging hours cannot replace site evidence. Straight-line access can overstate feasible parking and walking connections.','Small')
    para('The current model does not estimate queues, reliability at peak times or adoption causality. Its strongest contribution is a reproducible chain from dated inputs to feasible decisions, comparison rules and sensitivity tests. LP allocation, integer investment, relaxation bounds and finite budget differences supply the relevant analytical foundation; an additional dynamic programme is unnecessary for this static decision.')

    page('References')
    refs=[
        ('[1] HDB. Carpark Information; carpark availability snapshot, 31 October 2026. Local master and lot files frozen for this analysis.','HDB dataset','https://data.gov.sg/datasets/d_23f946fa557947f93a8043bbef41dd09/view'),
        ('[2] LTA. Public EV charging point register, September 2026. Unique point IDs and registration-level power bounds.','LTA DataMall','https://datamall.lta.gov.sg/content/datamall/en/static-data.html'),
        ('[3] LTA. Monthly vehicle population by fuel; new car registrations; annual private vehicle mileage. September 2026 / 2025 vintages.','Vehicle statistics','https://www.lta.gov.sg/content/ltagov/en/who_we_are/statistics_and_publications/statistics.html'),
        ('[4] Singapore Department of Statistics. Resident population and dwelling stock by planning area/subzone and dwelling type, 2025 and 2026. URA MP2019/MP2025 boundaries.','SingStat geographic distribution','https://www.singstat.gov.sg/find-data/explore-data-themes/population/geographic-distribution/latest-news-data'),
        ('[5] Ministry of Transport. EVs registered for season parking in HDB carparks. Parliamentary reply, 11 November 2024.','Historical calibration reply','https://www.mot.gov.sg/news-resources/newsroom/written-reply-to-parliamentary-question-on-statistics-of-evs-registered-for-season-parking-in-hdb-carparks-and-increasing-charging-lots-for-carparks-with-more-ev-season-parkings-registered/'),
        ('[6] Ministry of Transport. Utilisation rates of EV charging points at petrol kiosks relative to public carparks. 10 September 2026.','Utilisation reply','https://www.mot.gov.sg/news-resources/newsroom/utilisation-rates-of-ev-charging-points-at-petrol-kiosks-relative-to-public-car-parks/'),
        ('[7] Electric Pte Ltd. EV charger hardware and maintenance schedule; archived 9 November 2026. Commercial comparator, not an HDB installed-cost contract.','Vendor evidence','https://www.electric.com.sg/ev-charger/'),
        ('[8] Gurobi Optimization. Facility-location example and Multiple Objectives documentation, archived 9 November 2026. Structural references; this implementation uses HiGHS.','Facility-location example','https://docs.gurobi.com/projects/examples/en/current/examples/python/facility.html'),
        ('[9] Church, R. and ReVelle, C. (1974). The maximal covering location problem. Papers of the Regional Science Association, 32, 101–118. Bibliographic context; original full text was not retrieved.','DOI','https://doi.org/10.1111/j.1435-5597.1974.tb00902.x'),
        ('[10] Huangfu, Q. and Hall, J. A. J. (2018). Parallelizing the dual revised simplex method. Mathematical Programming Computation, 10, 119–142. HiGHS solver documentation accessed 10 November 2026.','HiGHS documentation','https://ergo-code.github.io/HiGHS/dev/'),
        ('[11] DBA5103 Project Guideline. Semester I, 2026/2027, NUS. Local course document: sources/references/Project_Guideline.pdf.','',None),
    ]
    for text,label,url in refs:
        p=para(text+' ','Small')
        if url:link(p,label,url)
    para('Full file paths, collection timestamps, source URLs, parameter evidence and SHA-256 hashes are retained in the workbook and local research manifest. All numerical results use frozen local inputs, rather than a live data refresh.','Small')

    page('Appendix A. Model audit and reproducibility')
    table(['Item','Audit result'],[
        ('Model size',f'{len(sites):,} sites; {summary["arcs"]:,} allowable service arcs; continuous flows plus integer and binary investment decisions.'),
        ('Source points',f'11,489 unique IDs; {audit["match_counts"]["address_supported"]:,} address-supported; remaining classes stay separate.'),
        ('Capacity imputation',f'278 sites; {audit["imputed_lots"]:,.1f} lots. Base total {audit["total_lots_after_imputation"]:,.1f}.'),
        ('Solver',f'HiGHS {manifest["highs_version"]}; Python {manifest["python"]}; one thread; seed 17.'),
        ('Tolerances','Base relative MIP gap 0.0001; stresses 0.001. Feasibility tolerance 1e-7. Service lock max(1e-6, 1e-8 × total demand).'),
        ('Runtime limits','Base 45 seconds per MILP pass; sensitivity 25 seconds. Actual elapsed times and overshoot appear in logs.'),
        ('Repeatability',f'Identical-input repeat: additions identical = {reproducibility["repeat_identical_additions"]}; service difference {reproducibility["repeat_service_difference"]:.6f} kWh/day.'),
        ('Artifacts','HDB_EV_Charging_Analysis.xlsx; code/outputs/runs, solver_logs, inputs, figures; code/requirements.txt; code/venv/.')],[1.65,4.5])
    para('Space and power residuals, demand conservation, nonnegative flows, cost reconciliation, service locks and integrality are checked before saving integer results. A mathematical lower bound certifies the service-target budgets when attained. An LP relaxation provides an upper bound on service, but its fractional decisions are not installable. Marginal investment comparisons use finite differences, not MILP shadow prices.','Small')
    para('Fixed-plan stress holds investment and upgrade binaries constant. If the scenario allows fewer bays or less power, usable added energy is derated by the tighter proportional limit, while sunk point counts remain unchanged. Such plans are flagged as construction-infeasible; repriced plans can also exceed the scenario budget. Their difference from a same-budget optimum is not labelled feasible-plan regret.','Small')
    para('The 2027 stock path assumes the Jan–Sep 2026 mean registration flow persists for 15 months; exits are a stated fraction of these additions. It is not a fitted forecast, so no statistical confidence interval or forecasting back-test is claimed. Existing DC uses the same declared effective-hours base while retaining recorded power.','Small')

    page('Appendix B. Execution and AI-use declaration')
    para('From the repository root, use the commands below. The environment already exists in code/venv/; requirements.txt pins the installed libraries. LibreOffice is used only to render the DOCX to a checked PDF and is a system dependency.','Small')
    for command in ['python3 -m venv project/code/venv','project/code/venv/bin/python -m pip install -r project/code/requirements.txt',
                    'project/code/venv/bin/python project/code/prepare_data.py','project/code/venv/bin/python project/code/test_models.py',
                    'project/code/venv/bin/python project/code/run_analysis.py --mode all','project/code/venv/bin/python project/code/review_shortlist.py','project/code/venv/bin/python project/code/audit_outputs.py',
                    'project/code/venv/bin/python project/code/build_figures.py','project/code/venv/bin/python project/code/build_workbook.py',
                    'project/code/venv/bin/python project/code/build_report.py']:
        para(command,'Code')
    para('AI assistance: OpenAI Codex assisted with Python implementation, analysis checks, drafting and document formatting. No external party was contacted and no site verification was performed. The submitting authors remain responsible for reviewing the assumptions, evidence and final submission.','Small')
    para('The following appendix attaches the complete data preparation, model, comparison, scenario and test code. Office-document and plotting generators are also supplied as Python files in code/. Machine-readable outputs and solver logs accompany the report rather than being repeated as long printed tables.','Small')
    for filename in ['prepare_data.py','model.py','baselines.py','run_analysis.py','test_models.py']:
        page('Appendix C. Python — '+filename)
        text=(Path(__file__).parent/filename).read_text()
        for lineno,line in enumerate(text.splitlines(),1):
            p=para(f'{lineno:03d}  {line}','Code')
            p.paragraph_format.keep_with_next=False;p.paragraph_format.widow_control=False
    target=ROOT/'HDB_EV_Charging_Report.docx';d.save(target)
    print('Saved',target)


if __name__=='__main__':
    main()
