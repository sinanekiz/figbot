"""Independent sampled horizontal-roof coverage check on final fused print mesh."""
import json,numpy as np,trimesh
from shapely.geometry import Polygon,GeometryCollection
from cad.prototype_arm import build_breakaway_v4 as b
from cad.prototype_arm import export_aero_v4 as ex
from cad.prototype_arm import build_aero_v4 as a
from cad.utils import shape_mesh

def layer(mesh,z):
 s=mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1])
 if s is None:return GeometryCollection()
 result=GeometryCollection()
 for loop in s.discrete:
  p=Polygon(loop[:,:2]).buffer(0)
  if p.area>1e-7:result=result.symmetric_difference(p)
 return result.buffer(0)

def main():
 result=[]
 for _,pids in b.GROUPS:
  for pid in pids:
   original=trimesh.Trimesh(*shape_mesh(ex.oriented(pid,a.PARTS[pid][0]())))
   mesh=trimesh.load_mesh(b.OUT/'TEKIL'/f'{pid}_DESTEKLI.stl')
   ts=original.triangles[original.face_normals[:,2]<-.99]
   heights=sorted(set(round((np.floor((np.mean(t[:,2])-.1)/.2)+1)*.2+.1,4) for t in ts if np.ptp(t[:,2])<.005 and np.mean(t[:,2])>.3))
   rows=[]
   for h in heights:
    current=layer(mesh,h);prev=layer(mesh,h-.2)
    missing=current.difference(prev.buffer(1.5))
    ps=b.polygons(missing)
    large=[p for p in ps if p.area>3]
    rows.append({'z':h,'missing_area':sum(p.area for p in ps),'largest':max([p.area for p in ps],default=0),'large_bounds':[list(p.bounds) for p in large]})
   result.append({'part':pid,'samples':rows})
   print(pid,'heights',len(rows),'max unbacked area',max([r['largest'] for r in rows],default=0),flush=True)
 (b.OUT/'ROOF_LAYER_AUDIT.json').write_text(json.dumps({'method':'0.2mm mid-layer contours at horizontal model undersides; previous layer expanded1.5mm. Flags only, not physical bridge proof.','results':result},indent=2))
if __name__=='__main__':main()
