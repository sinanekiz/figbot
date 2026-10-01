import json
import numpy as np
import trimesh
from shapely.geometry import box
from cad.prototype_arm import build_breakaway_v4 as b
from cad.prototype_arm import build_aero_v4 as a
from cad.prototype_arm import export_aero_v4 as ex
from cad.utils import shape_mesh

def test_scope_excludes_successful_horns_pins_and_small_hardware():
 pids=[p for _,ps in b.GROUPS for p in ps]
 assert len(pids)==10 and len(set(pids))==10
 assert not any('CLAMP' in p or 'BEAM' in p or p.startswith(('S0','A4-P')) for p in pids)

def test_through_opening_gets_support_but_top_does_not():
 # 20mm wide bridge on two feet, section coordinate X,Z.
 shape=box(0,0,3,15).union(box(17,0,20,15)).union(box(0,13,20,15))
 sh=b.shadow(shape).difference(shape)
 assert sh.covers(box(4,1,16,12))
 assert sh.intersection(box(0,15.1,20,18)).area==0

def test_pack_parts_unchanged_and_closed():
 report=json.loads((b.OUT/'SUPPORT_AUDIT.json').read_text())
 assert len(report)==10
 for r in report:
  pid=r['part'];m=trimesh.load_mesh(b.OUT/'TEKIL'/f'{pid}_DESTEKLI.stl')
  assert m.is_watertight and m.is_winding_consistent
  assert np.all(m.extents<256)
  assert r['support_model_overlap_mm3']<r.get('contact_tie_volume_mm3',0)+.005
  original=trimesh.Trimesh(*shape_mesh(ex.oriented(pid,a.PARTS[pid][0]())))
  # Boolean support union may retessellate contacts, but must not cut original material.
  removed=trimesh.boolean.difference([original,m],engine='manifold')
  assert abs(removed.volume)<.01

def test_3mf_quantities_and_whole_objects_preserved():
 import zipfile,xml.etree.ElementTree as ET
 ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
 for name,pids in b.GROUPS:
  with zipfile.ZipFile(b.OUT/'TABLALAR'/(name+'.3mf')) as z:
   assert z.testzip() is None
   root=ET.fromstring(z.read('3D/3dmodel.model'))
   assert len(root.findall('m:build/m:item',ns))==len(pids)
 # Support bodies remain in the same object as each original part, preventing bed-drop.

def test_contact_neck_and_coupon_no_bulk_overlap():
 assert b.GAP==0 and .4<=b.TIP< b.WALL and b.NECK==.6
 r=json.loads((b.OUT/'COUPON_AUDIT.json').read_text())
 assert r['support_pieces']>0 and r['support_model_overlap_mm3']<.005


def test_independent_layer_checker_sees_real_empty_space():
 from cad.prototype_arm.check_support_layers import layer
 import cadquery as cq
 shape=cq.Workplane('XY').rect(20,20).rect(10,10).extrude(5)
 m=trimesh.Trimesh(*shape_mesh(shape))
 p=layer(m,2.5)
 assert abs(p.area-300)<.01
 assert not p.contains(__import__('shapely').geometry.Point(0,0))
