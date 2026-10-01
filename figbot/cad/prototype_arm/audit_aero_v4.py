"""Static interference checks; contact is allowed, solid penetration is not."""
import json
from cad.prototype_arm import build_aero_v4 as a

def overlaps(items,eps=.002,between_frames_only=False):
    boxes=[x.shape.val().BoundingBox() for x in items]
    hits=[]
    for i,x in enumerate(items):
        b=boxes[i]
        for j in range(i):
            if between_frames_only and items[j].frame==x.frame:continue
            c=boxes[j]
            if any(min(getattr(b,k+'max'),getattr(c,k+'max'))-max(getattr(b,k+'min'),getattr(c,k+'min'))<1e-5 for k in 'xyz'):continue
            v=x.shape.intersect(items[j].shape).val().Volume()
            if v>eps:hits.append({'a':items[j].name,'b':x.name,'mm3':round(v,5),'frames':[items[j].frame,x.frame]})
    return hits

if __name__=='__main__':
    a.OUT.mkdir(parents=True,exist_ok=True)
    hits=overlaps(a.assembly())
    (a.OUT/'DEVELOPMENT_COLLISIONS.json').write_text(json.dumps(hits,indent=2))
    print('collisions',len(hits))
    for h in hits:print(h['a'],'/ ',h['b'],h['mm3'])
