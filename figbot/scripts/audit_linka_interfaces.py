"""Broad nominal hard-part collision screen; no physical or strength approval."""
import json
from itertools import combinations
from pathlib import Path
import numpy as np
from cad.prototype_arm import build_linka_v1 as a
from scripts.arm_engineering_review import TARGETS

OUT=Path('reports/linka_l1r1_audit')

def overlap(bb,cc):
    return all(min(getattr(bb,k+'max'),getattr(cc,k+'max'))-max(getattr(bb,k+'min'),getattr(cc,k+'min'))>1e-5 for k in 'xyz')

def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=OUT)
    output=parser.parse_args().out
    items=a.local_items();checks=0;hits=[]
    qs=[a.ik(t) for t in TARGETS.values()]
    poses=[('display',[0,-60,95,-35])]
    poses += [(f'transfer{j}_{t:.2f}',(1-t)*np.array(q)+t*np.array(r)) for j,(q,r) in enumerate(zip(qs,qs[1:])) for t in np.linspace(0,1,5)]
    # Prints must not interpenetrate. Metal fastener/servo bodies screened too;
    # heat-set inserts are deliberate interference fits; cords are flexible.
    fixed=[i for i in items if not any(s in i.name.lower() for s in ['cord','elastic','brass ear','insert'])]
    seen_static=set()
    for pname,q in poses:
        fs=a.frames(q)
        solids=[a.h.move(i.shape,fs[i.frame]).val() for i in fixed]
        boxes=[s.BoundingBox() for s in solids]
        for j,k in combinations(range(len(fixed)),2):
            aa,bb=fixed[j],fixed[k]
            if aa.frame==bb.frame:
                if (j,k) in seen_static:continue
                seen_static.add((j,k))
            if not aa.part_id and not bb.part_id:continue
            # Adhesive pad overlaps intended contact surface; not a hard part.
            if 'L1-18' in aa.name or 'L1-18' in bb.name:continue
            if not overlap(boxes[j],boxes[k]):continue
            checks+=1;v=solids[j].intersect(solids[k]).Volume()
            if v>.05:
                row=dict(pose=pname,a=aa.name,b=bb.name,mm3=round(v,6));hits.append(row);print(row,flush=True)
        print(pname,'done',flush=True)
    output.mkdir(parents=True,exist_ok=True)
    result=dict(revision=a.REVISION,poses=len(poses),boolean_checks=checks,hits=hits,threshold_mm3=.05,
        exclusions=['heat-set insert interference','flexible cords/elastic','adhesive pad overlap','metal-metal pairs'],
        status='FAIL' if hits else 'PASS NOMINAL SAMPLED SCREEN ONLY')
    (output/'COLLISIONS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(result['status'],flush=True)

if __name__=='__main__':main()
