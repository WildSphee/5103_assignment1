"""Fetch the public evidence added after the 9 Nov meeting; no credentials required.
Run with requests + beautifulsoup4. Keeps downloads immutable unless --refresh is given.
The manifest records source URLs, response types, hashes, and failures.
"""
import argparse, csv, hashlib, io, json, zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

DATA = Path(__file__).resolve().parents[1] / 'data'
SOURCES = [
('pop2026','04_demographics_demand_proxies/updates_2026-11-09/population_dwelling_2026.zip','https://www.singstat.gov.sg/files/c6755f50-4bfb-4bfa-b7d3-00259b9509ed.zip','Resident population by planning area/subzone, age, sex and dwelling type; June 2026'),
('pop2025','04_demographics_demand_proxies/updates_2026-11-09/population_dwelling_2025.zip','https://www.singstat.gov.sg/files/d7c71675-612f-4ee8-926b-f81d0e9304cc.zip','Same resident population series; June 2025'),
('pop2024','04_demographics_demand_proxies/updates_2026-11-09/population_dwelling_2024.zip','https://www.singstat.gov.sg/files/08022f5e-e664-4274-bd17-a052be52c478.zip','Same resident population series; June 2024'),
('pop2020_24','04_demographics_demand_proxies/updates_2026-11-09/population_floor_area_2020_2024.csv','https://www.singstat.gov.sg/files/2246b94f-9c6b-412f-aa67-1869be0e193e.csv','Resident population by planning area/subzone, age, sex and floor area; 2020-2024'),
('dwell2026','04_demographics_demand_proxies/updates_2026-11-09/dwellings_type_2026.zip','https://www.singstat.gov.sg/files/54005c85-aee8-433e-a8dd-64aa5e7c6f2a.zip','Residential dwellings by planning area/subzone and dwelling type; June 2026'),
('dwell2025','04_demographics_demand_proxies/updates_2026-11-09/dwellings_type_2025.zip','https://www.singstat.gov.sg/files/c1539548-49f4-4dd5-a82c-2eec26b11b5a.zip','Same dwelling stock series; June 2025'),
('dwell2020_24','04_demographics_demand_proxies/updates_2026-11-09/dwellings_floor_area_2020_2024.csv','https://www.singstat.gov.sg/files/82dbbe42-7ecb-4ea3-a2e6-96e18bbeb99f.csv','Dwelling stock by planning area/subzone and floor area; 2020-2024'),
('geography_catalog','04_demographics_demand_proxies/updates_2026-11-09/SingStat_geographic_distribution.html','https://www.singstat.gov.sg/find-data/explore-data-themes/population/geographic-distribution/latest-news-data','Download catalog and definitions'),
('ghs2025','06_reports_and_policy/updates_2026-11-09/SingStat_GHS2025.pdf','https://www.singstat.gov.sg/files/1559c94a-efc1-4262-84fd-042c9bd96e68.pdf','General Household Survey 2025 report; released 30 June 2026'),
('poptrends2026','06_reports_and_policy/updates_2026-11-09/SingStat_Population_Trends_2026.pdf','https://www.singstat.gov.sg/files/5645f043-4bb7-4181-a3a8-c36da5cd1b12.pdf','Population Trends 2026; released 25 September 2026'),
('mot_utilisation','06_reports_and_policy/updates_2026-11-09/MOT_2026-09-10_utilisation.html','https://www.mot.gov.sg/news-resources/newsroom/utilisation-rates-of-ev-charging-points-at-petrol-kiosks-relative-to-public-car-parks/','Public carparks average five hours/day January-August 2026; NOT HDB-specific or energy utilisation'),
('sg_vendor','08_costs/sources/Electric_SG_charger_hardware_2026-11-09.html','https://www.electric.com.sg/ev-charger/','Singapore vendor hardware prices excluding installation and GST; not a public HDB installed quote'),
('sg_install','08_costs/sources/GoElectric_standard_installation_2026-11-09.html','https://goelectric.com.sg/Product/Accessories/Standard-Installation-of-EV-Charger','Standard installation scope and price; residential comparator only'),
('afdc_om','08_costs/sources/AFDC_operations_maintenance_2026-11-09.html','https://afdc.energy.gov/fuels/electricity-infrastructure-maintenance-and-operation','US operations and maintenance benchmark; not Singapore evidence'),
('afdc_capex','08_costs/sources/AFDC_procurement_installation_2026-11-09.html','https://afdc.energy.gov/fuels/electricity-infrastructure-development','US equipment and installation benchmarks; applicability restrictions'),
('gurobi_multiobjective','10_methodology/Gurobi_multiple_objectives_2026-11-09.html','https://docs.gurobi.com/projects/optimizer/en/current/features/multiobjective.html','Hierarchical objectives and numerical tolerance handling'),
('church_revelle','10_methodology/Church_ReVelle_1974_publisher.html','https://onlinelibrary.wiley.com/doi/10.1111/j.1435-5597.1974.tb00902.x','Original maximal covering paper; publisher metadata, full text may be blocked'),
('facility_example','10_methodology/Gurobi_facility_example.html','https://docs.gurobi.com/projects/examples/en/current/examples/python/facility.html','Capacitated facility-location implementation reference'),
('ev_location_paper','10_methodology/Brandstaetter_Leitner_Ljubic_2018_EV_location.pdf','https://optimization-online.org/wp-content/uploads/2017/03/5933.pdf','Author manuscript: location and capacity planning in electric car sharing; related application, not an HDB model'),
('ghs_tables_catalog','06_reports_and_policy/updates_2026-11-09/SingStat_GHS2025_catalog.html','https://www.singstat.gov.sg/publication-resources/general-household-survey-2025','Full report and statistical table links embedded in page hydration'),
('ghs_transport_tables','04_demographics_demand_proxies/updates_2026-11-09/GHS2025_transport_download.html','https://tablebuilder.singstat.gov.sg/statistical-tables/downloadMultiple/HT3s_HeubkYYEgje1d8vRQ','Detailed transport tables; browser download route, may be blocked'),
('hdb_season_parking','06_reports_and_policy/updates_2026-11-09/MOT_2024-11-11_EV_season_parking.html','https://www.mot.gov.sg/news-resources/newsroom/written-reply-to-parliamentary-question-on-statistics-of-evs-registered-for-season-parking-in-hdb-carparks-and-increasing-charging-lots-for-carparks-with-more-ev-season-parkings-registered/','Historical HDB season-parking calibration; EV category comparability requires caution'),
]

def fetch(item, refresh=False):
    sid, rel, url, purpose = item
    p=DATA/rel; p.parent.mkdir(parents=True,exist_ok=True)
    row=dict(source_id=sid,path=rel,url=url,purpose=purpose,retrieved_at_utc=datetime.now(timezone.utc).isoformat(),status='',content_type='',bytes='',sha256='',notes='')
    try:
        if p.exists() and not refresh:
            raw=p.read_bytes(); row['status']='already_present'
        else:
            r=requests.get(url,timeout=60,headers={'User-Agent':'Academic EV infrastructure research (public sources)'})
            row['content_type']=r.headers.get('Content-Type','');r.raise_for_status();raw=r.content
            if p.suffix=='.pdf' and not raw.startswith(b'%PDF'): raise ValueError('Response is not a PDF')
            if p.suffix=='.zip' and not zipfile.is_zipfile(io.BytesIO(raw)): raise ValueError('Response is not a ZIP')
            if p.suffix=='.csv' and b'<html' in raw[:300].lower(): raise ValueError('HTML returned instead of CSV')
            p.write_bytes(raw);row['status']='downloaded'
        row['bytes']=len(raw);row['sha256']=hashlib.sha256(raw).hexdigest()
        if p.suffix=='.zip':
            names=[]
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                for n in z.namelist():
                    if n.lower().endswith('.csv') and not n.startswith('__MACOSX'):
                        out=p.parent/(p.stem+'__'+Path(n).name);out.write_bytes(z.read(n));names.append(out.name)
            row['notes']='Extracted: '+'; '.join(names)
        elif p.suffix=='.html':
            soup=BeautifulSoup(raw,'html.parser')
            for tag in soup(['script','style','nav','footer','header']):tag.decompose()
            p.with_suffix('.txt').write_text('Source: '+url+'\nRetrieved: '+row['retrieved_at_utc']+'\n\n'+soup.get_text('\n',strip=True))
    except Exception as e:
        row['status']='failed';row['notes']=str(e)
    return row

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--refresh',action='store_true');args=ap.parse_args()
    with ThreadPoolExecutor(max_workers=5) as pool: rows=list(pool.map(lambda x:fetch(x,args.refresh),SOURCES))
    out=DATA/'09_research_audit/source_manifest_2026-11-09.csv'
    if out.exists():
        old={r['source_id']:r for r in csv.DictReader(out.open())}
        rows=[old[r['source_id']] if r['status']=='already_present' and r['source_id'] in old else r for r in rows]
    for r in rows:
        if r['source_id']=='ghs_transport_tables' and r['status']!='failed':
            r['status']='landing_page_only'
            r['notes']='JavaScript application shell only; detailed transport workbook NOT acquired. First direct attempt also returned HTTP 403.'
    with out.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    for r in rows:print(r['source_id'],r['status'],r['bytes'],r['notes'][:150])
if __name__=='__main__':main()
