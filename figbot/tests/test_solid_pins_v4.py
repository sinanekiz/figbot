import json,math,zipfile,xml.etree.ElementTree as ET
import numpy as np
import trimesh
import cadquery as cq
from cad.prototype_arm import build_solid_pins_v4 as s
from cad.prototype_arm import build_aero_v4 as old

def test_unchanged_length_head_and_no_barb_or_split():
 for grip,_ in s.SPECS.values():
  p=s.pin(grip);b=p.val().BoundingBox();o=old.locking_pin(grip).val().BoundingBox()
  assert p.val().isValid() and len(p.solids().vals())==1
  assert abs(b.zlen-o.zlen)<1e-6 and abs(b.xlen-o.xlen)<1e-6
  # A full axial cylinder fits inside the entire formerly split shank.
  core=cq.Workplane('XY').circle(3.05/2).extrude(grip).translate((0,0,1.6))
  assert abs(core.val().Volume()-p.intersect(core).val().Volume())<1e-6
  nose=p.intersect(cq.Workplane('XY').box(15,15,1.19).translate((0,0,1.6+grip+.6)))
  assert nose.val().BoundingBox().xlen<=3.05+1e-6

def test_full_plate_has_exactly_48_closed_pins_no_axles():
 m=trimesh.load_mesh(s.OUT/'48_ADET_DOLU_PIN_D305.stl')
 assert m.is_watertight and len(m.split())==48
 assert 'P5' not in s.SPECS
 assert sum(n for _,n in s.SPECS.values())==48
 assert max(m.extents)<236

def test_diameter_trials_preserve_heads_and_length():
 for d in s.DIAMETERS:
  p=s.pin(9.6,d);b=p.val().BoundingBox()
  assert abs(b.zlen-12.4)<1e-6 and abs(b.xlen-6.05)<1e-6
  probe=cq.Workplane('XY').box(20,20,1).translate((0,0,5))
  assert abs(p.intersect(probe).val().Volume()-math.pi*(d/2)**2)<1e-6

def test_3mf_counts_and_manifest_consistent():
 ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
 for name,n in [('48_ADET_DOLU_PIN_D305.3mf',48),('ONCE_DENE_5_CAP.3mf',5)]:
  with zipfile.ZipFile(s.OUT/name) as z:
   assert z.testzip() is None
   root=ET.fromstring(z.read('3D/3dmodel.model'))
   assert len(root.findall('m:build/m:item',ns))==n
 r=json.loads((s.OUT/'MANIFEST.json').read_text());assert r['qty']==48 and r['cost_TRY'] is None
