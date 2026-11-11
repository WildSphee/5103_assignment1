"""Publish the 10-Nov-2026 source-record desk review for the selected candidates."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from pyproj import Transformer
from prepare_data import ROOT, OUT, INPUTS

NOTES={
    'JM18':('Source-supported; electrical/access survey','Three points at 629A match JM18. Three neighbouring 635A points correctly remain at JM14.'),
    'JM13':('Source-supported; electrical/access survey','Three 7 kW points at 601A match JM13; master and register addresses agree, distance 11.75 m.'),
    'U15':('HOLD: resolve six provisional points','Six register points at block 238 lie at the site coordinates, but the master lists 231/237. Broad-supply sensitivity includes them; the base does not.'),
    'J98M':('HOLD: resolve duplicate-address supply','Six register points at 647A compete between J98M (multi-storey, night parking) and JS5L (surface, no night parking). Building-name evidence favours J98M but level/ownership confirmation is needed.'),
    'U13':('HOLD: resolve nearby address mismatch','Six nearby points use 223/223A Bukit Batok East Avenue 3; the master lists 212/230 Bukit Batok Street 21. They remain unassigned; absence of a match is not evidence of no supply.'),
}


def main():
    frozen=json.loads(Path(__file__).with_name('reviews').joinpath('review_source_hashes.json').read_text())
    for item in frozen:
        p=ROOT.parent/item['path']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:
            raise RuntimeError('Source changed; the frozen desk review must be renewed: '+str(p))
    shortlist=pd.read_csv(OUT/'shortlist_replacement.csv')
    sites=pd.read_csv(INPUTS/'sites.csv').set_index('car_park_no')
    cp=pd.read_csv(INPUTS/'hdb_charger_crosswalk.csv')
    tr=Transformer.from_crs(4326,3414,always_xy=True)
    xy=np.column_stack(tr.transform(cp.longitude.to_numpy(),cp.latitude.to_numpy()))
    tree=cKDTree(xy);rows=[]
    for r in shortlist.itertuples():
        s=sites.loc[r.site_id]
        nearby=cp.iloc[tree.query_ball_point([s.x_coord,s.y_coord],150)]
        gate,note=NOTES.get(r.site_id,('Desk review pending','Candidate differs from the frozen reviewed shortlist.'))
        rows.append({'site_id':r.site_id,'address':s.address,'observed_lots':s.total_lots,
                     'base_ac_additions':r.base_additions,'review_gate':gate,'desk_finding':note,
                     'nearby_register_points_150m':len(nearby),'night_parking':s.night_parking,
                     'review_date':'2026-11-10','review_scope':'Local source-record review only; no field/operator verification'})
    pd.DataFrame(rows).to_csv(OUT/'shortlist_desk_review.csv',index=False)
    print(pd.DataFrame(rows)[['site_id','review_gate']].to_string(index=False))


if __name__=='__main__':
    main()
