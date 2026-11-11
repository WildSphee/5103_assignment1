"""Course-formatted report: 12-point Times, double spacing, one-inch margins."""
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


def set_font(style, name='Times New Roman', size=12):
    """Override Word theme fonts as well as the Latin font slots."""
    style.font.name=name;style.font.size=Pt(size)
    fonts=style.element.get_or_add_rPr().rFonts
    for attr in ('asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme'):
        fonts.attrib.pop(qn('w:'+attr),None)
    for attr in ('ascii','hAnsi','eastAsia','cs'):
        fonts.set(qn('w:'+attr),name)


def shade(cell,fill):
    el=OxmlElement('w:shd');el.set(qn('w:fill'),fill);cell._tc.get_or_add_tcPr().append(el)


def link(paragraph,label,url):
    rel=paragraph.part.relate_to(url,'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True)
    h=OxmlElement('w:hyperlink');h.set(qn('r:id'),rel)
    r=OxmlElement('w:r');pr=OxmlElement('w:rPr');col=OxmlElement('w:color');col.set(qn('w:val'),BLUE);pr.append(col);r.append(pr)
    t=OxmlElement('w:t');t.text=label;r.append(t);h.append(r);paragraph._p.append(h)


def main():
    from build_showcase import build_tables, build_top100
    area_showcase,years=build_tables()
    top100=build_top100()
    year_index=years.set_index('scenario')
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
    normal=styles['Normal'];set_font(normal)
    normal.paragraph_format.line_spacing=2;normal.paragraph_format.space_after=Pt(4)
    normal.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    for name in ['Title','Heading 1','Heading 2']:
        set_font(styles[name]);styles[name].font.bold=True;styles[name].font.color.rgb=RGBColor.from_string(NAVY)
        styles[name].paragraph_format.line_spacing=2
        styles[name].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT
        styles[name].paragraph_format.space_after=Pt(6)
    for name,size,font in [('Caption',12,'Times New Roman'),('Small',12,'Times New Roman'),('Code',7.2,'Courier New')]:
        if name not in styles:styles.add_style(name,1)
        st=styles[name];set_font(st,font,size)
        st.paragraph_format.line_spacing=1 if name=='Code' else 2;st.paragraph_format.space_after=Pt(5 if name!='Code' else 0)
        st.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT if name in ('Caption','Code') else WD_ALIGN_PARAGRAPH.JUSTIFY
    styles['Caption'].font.color.rgb=RGBColor.from_string('647580')
    h=sec.header.paragraphs[0];h.text='DBA5103  |  OPERATIONS RESEARCH AND ANALYTICS'
    h.style='Caption';h.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    foot=sec.footer.paragraphs[0];foot.alignment=WD_ALIGN_PARAGRAPH.CENTER
    run=foot.add_run();field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');run._r.addnext(field)

    def para(text,style=None):return d.add_paragraph(text,style)
    def page(title):
        p=d.add_heading(title,level=1)
        # Let the double-spaced narrative flow instead of forcing sparse spillovers.
        p.paragraph_format.page_break_before=title.startswith(('1. ','References','Appendix'))
    def picture(name,width=6.15,caption=None):
        p=d.add_paragraph();p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(2);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(FIG/f'{name}.png'),width=Inches(width))
        if caption:
            p.paragraph_format.keep_with_next=True
            p=para(caption,'Caption');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    def formula_panel():
        # Separate adjacent Word tables and keep both equation columns together.
        spacer=d.add_paragraph();spacer.paragraph_format.space_after=Pt(0)
        spacer.paragraph_format.line_spacing=Pt(2)
        t=d.add_table(rows=1,cols=2);t.autofit=False
        t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        for cell,label,names in zip(t.rows[0].cells,['Constraints','Objectives and annual cost'],
                [[('formula_model',3.0)],[('formula_objectives',2.8),('formula_cost',2.9)]]):
            cell.width=Inches(3.075)
            p=cell.paragraphs[0];p.style='Caption';p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p.add_run(label).bold=True
            for name,width in names:
                p=cell.add_paragraph();p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(3)
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                p.add_run().add_picture(str(FIG/f'{name}.png'),width=Inches(width))
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
            if i==0:pr.append(OxmlElement('w:tblHeader'))
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.line_spacing=2;p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(3)
                    p.paragraph_format.keep_with_next=i==0
                    for r in p.runs:
                        r.font.name='Times New Roman';r.font.size=Pt(12)
                        if i==0:r.font.bold=True;r.font.color.rgb=RGBColor(255,255,255)
            if widths:
                for c,w in zip(row.cells,widths):c.width=Inches(w)
        return t
    def callout(text):
        t=d.add_table(rows=1,cols=1);shade(t.cell(0,0),'EDF3F6')
        p=t.cell(0,0).paragraphs[0];p.paragraph_format.line_spacing=2
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
    para('This study asks where HDB carparks need additional slow charging and how much service each investment level delivers. National charger counts cannot establish local access. Infrastructure expenditure covers participating parties, not a proposed government budget.')
    para('All 2,273 HDB carparks are retained. Existing address-supported AC/DC supply is fixed; new base additions are 7.4 kW AC points. Integer investment decisions and continuous energy allocation link nearby carparks. Non-HDB investment, carbon valuation and petrol savings are excluded.')
    callout(f'Base result: {int(base["ac_points"]):,} additional AC points at {money(base["capital"])} serve {pct(base["service_fraction"])} of estimated 2027 demand, versus {pct(summary["no_build_fraction"])} using matched existing supply alone.')
    para('The allocation is designed for end-2027 demand. The September 2026 benchmark has a modelled energy shortfall of 17.0%; unchanged supply leaves 38.9% unmet in 2027. The proposed additions reduce the 2027 gap to 10.0%. These are estimated energy gaps, not observed charger shortages. Planning-area allocations are the main decision output; individual sites remain implementation details requiring verification.')

    d.add_heading('2. Data and demand estimation',level=1)
    table(['Input','Frozen evidence / treatment'],[
        ('HDB candidate sites [1]','2,273 unique IDs; projected SVY21 coordinates.'),
        ('Car-lot snapshot [1]','31 Oct 2026; 706,663 matched lots; 276 missing and 2 zero records.'),
        ('Public charger register [2]',f'Sep 2026; 11,489 unique points, 9,279 registrations; {audit["match_counts"]["address_supported"]:,} base matched points.'),
        ('Vehicle stock / flows [3]','Cars/Electric only; Sep 2026 stock 74,887. Other fuels retained only in the all-car denominator.'),
        ('Housing / population [4]','2025 with MP2019 geography; 2026 with MP2025 separately.'),
        ('Costs and operation [5–7]','Vendor components and historical public-carpark usage inform scenarios; no site-level HDB quote or utilisation panel.')], [1.8,4.35])
    para('Base supply requires a unique literal block and normalised street match within 150 metres, with non-HDB-looking buildings excluded. Registration conflicts are not assigned. The broader sensitivity adds block-range and same-street candidates. A 48-location desk sample checks the source records; neither this check nor proximity establishes ownership on site.','Small')
    para(f'Missing or zero lot counts use an area/carpark-type median with at least five observations, falling back to type and then national medians. This adds {audit["imputed_lots"]:,.1f} assumed lots. All demand remains represented; no-build at unknown-capacity sites and 0.5×/1.5× imputations test the effect. The complete exceptions and match ledgers accompany the workbook.','Small')

    page('2.1 Demand, capacity and scenario assumptions')
    picture('formula_stock',5.75,'Stock scenarios: 15 months of average registrations with assumed 2% exits; 2030 uses 25/35/45% of the frozen car fleet. Displayed inputs are rounded.')
    picture('formula_demand',4.5,'Demand D is grid-side kWh/day. Spatial weights sum to one; lots are not vehicle counts.')
    table(['Parameter','Base','Interpretation'],[
        ('National EV stock E','117,116.83','2027 assumption from stock-flow identity'),
        ('HDB share h / dependence β','0.40 / 0.80','HDB-associated EVs / energy sought here'),
        ('Mileage m / intensity e','16,200 / 0.16','km/year / battery kWh per km'),
        ('Efficiency η','0.90','Battery energy divided by grid energy'),
        ('Catchment / lot share','400 m / 10%','Straight-line access / assumed space limit'),
        ('Spare power / upgrade','44.4 / 88.8 kW','Incremental power beyond existing load')],[2.1,1.3,2.75])
    para(f'The base allocates {base["parameters"]["stock"]*.4:,.0f} estimated HDB-associated EVs by normalised car-lot weights, yielding {base["demand"]:,.0f} kWh/day. The 0.40 share is only weakly anchored by 8,800 HDB season-parking EVs versus 21,796 national electric cars in September 2024 [5]. Housing and population weights provide alternatives.')
    picture('formula_capacity',4.8,'Registration maximum-port power is the conservative bound; summed port power is a sensitivity.')
    para('Effective hours, uptime and accepted-power factors are design assumptions. The public-carpark average of about five hours/day in 2026 does not measure HDB-only delivered energy [6]. Charging losses enter demand once; the power factor represents accepted charging rate. Capacity does not guarantee short queues.','Small')

    page('3. Model and methodology')
    para('The facility-location model combines integer investment and continuous energy flows [8,9]. HDB carparks are both demand nodes i and candidate sites j. Catchment arcs may cross planning-area boundaries.')
    table(['Symbol','Meaning'],[('xⱼ; zⱼ; yⱼ','AC points; activation binary; upgrade binary'),('fᵢⱼ; sᵢ','Served and unmet grid-side kWh/day'),('Q⁰ⱼ; q','Existing and per-new-point effective daily capacity'),('Mⱼ; L̄ⱼ; b⁰ⱼ','Addition bound; total bay limit; existing occupied bays')],[1.7,4.45])
    formula_panel()
    para('Constraints conserve demand and enforce capacity, activation, power, space and budget. The bay limit is max(existing bays, floor(0.10 × lots)); existing bays are grandfathered. One connector per existing bay is tested against deduplicated bay labels.','Small')
    para('Unmet demand preserves feasibility; s is implemented as demand minus outgoing flow. Spare headroom is assumed.','Small')

    d.add_heading('3.1 Objectives, cost and numerical checks',level=2)
    para(f'Pass 1 maximises served energy. Pass 2 minimises annual infrastructure cost while retaining service within ε = {base["service_lock_epsilon"]:.6f} kWh/day. A subsequent fixed-investment LP minimises energy-weighted travel distance. Objectives are sequential and deterministic.')
    para('Costs [7]: S$6,500/AC point including ordinary installation; S$580/point/year maintenance and network reserves; S$50,000/site upgrade. Capital uses a 10-year life and 5% rate. Constant 2026 SGD excludes GST, electricity, sunk investment and revenue.')
    para('Each point adds at most q kWh/day: at least ceil((target − existing-only service)/q) points are needed. Attaining this bound without upgrades certifies minimum capex. Expected-answer tests cover integrality, upgrades, sharing and infeasibility; national runs check residuals and service locks.','Small')

    page('4. Planning-area allocation for end-2027')
    para(f'The 90%-service plan adds {int(base["ac_points"]):,} AC points across {base["sites_selected"]:,} carparks in {len(area_showcase)} planning areas, at {money(base["capital"])}. These are new additions for end-2027 demand, not total installed supply or a 2030 build plan.')
    picture('planning_area_allocation',5.65,'Figure 1. End-2027 base allocation by planning area. The final bar combines 16 areas.')
    chosen_names=['YISHUN','JURONG WEST','TAMPINES','BEDOK','SENGKANG','ANG MO KIO','WOODLANDS','PUNGGOL']
    showcase=area_showcase.set_index('planning_area')
    area_rows=[(a.title(),int(showcase.loc[a,'selected_carparks']),int(showcase.loc[a,'additional_ac_points'])) for a in chosen_names]
    other=area_showcase[~area_showcase.planning_area.isin(chosen_names)]
    area_rows.extend([(f'Other {len(other)} planning areas',int(other.selected_carparks.sum()),int(other.additional_ac_points.sum())),
                      ('Total',int(area_showcase.selected_carparks.sum()),int(area_showcase.additional_ac_points.sum()))])
    table(['Selected planning areas','Carparks receiving additions','Additional AC points'],area_rows,[2.65,1.75,1.75])
    para(f'The workbook lists all 28 areas. Site coordinates and verification examples are retained in the appendix and detailed sheets. Imputed-capacity sites receive {pct(base["imputed_investment_share"])} of expenditure and require confirmation.','Small')

    page('4.1 Top 100 carparks for site review')
    para(f'The map highlights 100 review candidates within the saved end-2027 plan: {int(top100.base_additions.sum()):,} proposed AC points across {top100.area_2019.nunique()} planning areas. The full national plan remains 549 carparks and 2,332 points.')
    picture('top100_map',6.1,'Figure 2. Orange: top 100 ranked carparks. Grey: other 449 selected carparks. Locations use source coordinates transformed to WGS84; boundaries are URA MP2019.')
    table(['Ranking step','Rule'],[
        ('Eligibility','Base-selected carparks with observed parking capacity and night parking.'),
        ('Primary order','Selection frequency across 37 scenarios with both objective passes certified, descending.'),
        ('Ties','More AC additions in the base solution first, then carpark ID alphabetically.'),
        ('Traceability','Top_100_Sites in Excel gives all 100 ranks, addresses, planning areas, latitude and longitude.')],[1.3,4.85])
    para(f'These sites appear in {100*top100.selection_fraction.min():.1f}–{100*top100.selection_fraction.max():.1f}% of certified scenarios. Selection frequency measures recurrence under the tested assumptions; it is not a probability or a marginal-benefit score. No geographic quota was applied.','Small')
    para('This is a transparent review shortlist, not a separately optimised 100-site deployment. The 90% service result applies to the entire national plan. Existing chargers, local demand, access and electrical headroom still require confirmation at every highlighted site.','Small')

    page('4.2 Comparison with simple rules')
    picture('comparators',5.5,'Figure 3. Same modelled demand and feasibility rules. Actual expenditure is reported below.')
    table(['Allocation','Capital','AC points','Served'],[
        (label,money(comparisons.loc[name,'capital']),f'{int(comparisons.loc[name,"ac_points"]):,}',pct(comparisons.loc[name,'service_fraction']))
        for name,label in [('equal','Equal'),('proportional','Proportional'),('greedy','Greedy'),('base','MILP')]],[2.0,1.45,1.2,1.5])
    prop=comparisons.loc['proportional'];greedy=comparisons.loc['greedy']
    gain=100*(base['service_fraction']-prop.service_fraction)
    para(f'The MILP improves service over proportional placement by {gain:.2f} percentage points. Equal allocation cycles through eligible site IDs; proportional allocation uses largest remainders and feasibility repair. Neither rule directly accounts for overlapping catchments or unused existing capacity.')
    greedy_conclusion='Greedy matches the MILP to numerical tolerance in this base case; the MILP chiefly supplies an optimum certificate here.' if abs(greedy.service_fraction-base['service_fraction'])<1e-5 else 'The numerical gap measures what the MILP adds beyond this practical greedy rule.'
    para(f'Greedy placement chooses additional served energy per step dollar, including upgrade thresholds and full flow reassignment. Its service is {pct(greedy.service_fraction)}, versus {pct(base["service_fraction"])} for the MILP. {greedy_conclusion} The workbook also reoptimises each rule’s actual spend; time-limited comparison incumbents retain their gaps.','Small')

    page('5. Cost-effectiveness and budget choices')
    picture('budget_frontier',5.5,'Figure 4. Discrete actual-spend frontier. Points are computed scenarios, not a smooth forecast.')
    table(['Service target','Minimum capital','Certificate'],[
        (f'{int(float(r.name.split("_")[-1]))}%',money(r.capital),'Capacity lower bound attained' if getattr(r,'certified_target_capex',False)==True else 'See solver gap')
        for r in targets.itertuples()],[1.2,1.65,3.3])
    unit=base['annual_cost']/(365*summary['incremental_served'])
    para(f'At the base budget, annualised infrastructure cost is {money(base["annual_cost"])}/year, or S${unit:.3f} per additional annual kWh served. This excludes electricity and is not a charging tariff or a social benefit-cost ratio. It divides incremental annual infrastructure cost by service above the fixed existing-only baseline.')
    marginal=frontier.marginal_capex_per_extra_annual_kwh.dropna()
    para(f'Across the computed budget intervals, marginal capex per extra annual kWh ranges from S${marginal.min():.3f} to S${marginal.max():.3f}. A nearly constant slope is possible while each added point remains fully useful; diminishing returns must be observed, not presumed. The physically bounded maximum service is {pct(summary["maximum_physical_fraction"])} under the base assumptions.','Small')

    page('6. Sensitivity and fixed-plan performance')
    picture('sensitivity',5.75,'Figure 5. Selected stresses at the base nominal budget. *Fixed-plan capacity is derated where power/space assumptions invalidate operation; repriced capex may exceed budget.')
    broad=sens.loc['broad_supply'];lowhours=sens.loc['hours_4'];selfonly=sens.loc['self_site_only']
    para(f'Broader supply matching changes reoptimised service to {pct(broad.service_fraction)}. Four effective charging hours reduce it to {pct(lowhours.service_fraction)}; restricting service to the home carpark gives {pct(selfonly.service_fraction)}. These differences show why supply identification, usable hours and access rules must be checked before converting model outputs into construction decisions.')
    count=len(sens);limited=int(sens.pass1_status.ne('Optimal').sum())
    para(f'The workbook contains {count} specified stress cases, each with a fixed-plan evaluation and reoptimisation. {limited} service solves lack optimal status; bounds and gaps remain visible. Secondary cost gaps can be larger, so stressed annual costs are attained costs, not automatically minimum costs. Feasible fixed-plan regret is bounded using the scenario incumbent and service bound. Scenario frequencies are not probabilities.','Small')

    page('6.1 Current and future energy shortfalls')
    picture('outlook',5.65,'Figure 6. Energy shortfalls under frozen supply and the fixed 2027 additions. Future additions are not shown as installed in 2026.')
    labels=[('current_2026','Sep 2026 benchmark'),('2027_base','End 2027 base'),('2030_low','2030 low'),('2030_base','2030 central'),('2030_high','2030 high')]
    table(['Demand period','Demand (MWh/day)','Unmet: existing only','Unmet: +2027 plan'],[
        (label,f'{year_index.loc[key,"demand_kwh_day"]/1000:.1f}',pct(year_index.loc[key,'existing_shortfall_fraction']),
         '—' if key=='current_2026' else pct(year_index.loc[key,'fixed_2027_plan_shortfall_fraction'])) for key,label in labels],[1.8,1.35,1.5,1.5])
    para('The 2026 benchmark uses observed September national EV stock but estimated HDB energy demand. The 2027 base extends registration flows for 15 months with assumed exits. The 2030 cases assume 25/35/45% of the frozen car fleet is electric; they are scenarios, not fitted forecasts. Existing supply stays frozen, and the second supply case adds the same 2,332 AC points with no further expansion.','Small')
    para('The central 2030 case leaves 67.5% unmet under existing supply, or 52.6% with the 2027 plan. Meeting 90% in 2027 therefore does not establish adequacy in 2030. A separate 2030 target-cost investment plan has not been solved.','Small')
    dc=sens.loc['ac_dc_extension']
    para(f'The 2027 AC/DC extension selects {int(dc.dc_points)} new DC points and serves {pct(dc.service_fraction)}; the tested costs provide no case for forcing a fast-charging quota.','Small')

    page('7. Recommendations and limitations')
    para(f'Use the 28-area allocation and {money(base["capital"])} envelope to discuss a conditional end-2027 plan serving 90% of estimated energy demand. Yishun, Jurong West and Tampines receive the largest point allocations. The lower-bound certificate supports the national point count and budget; it does not make each area allocation uniquely optimal.')
    table(['Before construction','Why it can change the decision'],[
        ('Confirm supply and access','Check existing HDB ownership, shared cabinet output, bay labels, walking routes and parking entitlement.'),
        ('Measure local demand','Obtain resident EV counts, session energy and occupation patterns; update spatial weights and effective hours.'),
        ('Survey electrical feasibility','Verify spare headroom and obtain a site-specific upgrade design and installed-cost quotation.'),
        ('Stage and rerun','Prioritise observed-capacity review candidates; verify uncertain sites before committing their allocations. Reoptimise after measured changes.')],[2.1,4.05])
    para('Keep the three time horizons distinct: the 2026 modelled benchmark, the end-2027 investment decision, and the 2030 demand stress. The proposed plan leaves a deliberate 10% energy gap in 2027 and requires further expansion as demand grows. Update area-level budgets when better local demand and confirmed supply become available.')
    para(f'Individual locations are less stable: alternate seeds produce only {pct(reproducibility["alternate_seed_site_jaccard"])} site-set overlap at near-equivalent service. The five reviewed sites are examples in the appendix, not the national deployment list or a geographically balanced priority ranking.','Small')
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

    page('Appendix A.1 Site-level verification examples')
    para('The main recommendation is the 28-area allocation. The five examples below were chosen by scenario selection frequency among base-selected sites with observed capacity and night parking; no geographical-diversity constraint was applied. Their western concentration does not represent the island-wide deployment.','Small')
    picture('placement_map',5.2,'Appendix figure. Existing matched supply and all 549 selected carparks; not only the five review examples.')
    table(['Review example','Added AC','Source-record review gate'],[
        (f'{r.site_id} · {robust.loc[r.site_id,"area_2019"].title()}',int(r.base_additions),desk.set_index('site_id').loc[r.site_id,'review_gate']) for r in replacement.itertuples()],[1.9,1.0,3.25])
    para(f'Frequencies use {int(robust.scenario_count.iloc[0])} certified stress cases. Supply uncertainties remain explicit holds; all locations require electrical and access surveys. Equal-budget replacement solves recover nearly all service. Full addresses, coordinates, quantities and review findings remain in the workbook.','Small')

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
