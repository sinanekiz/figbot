"""Check new local bench fixture/cable retainer; not strength validation."""
import hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import cadquery as cq
import trimesh
from cad.prototype_arm import build_stage02 as s
from cad.prototype_arm import build_aero_v3 as a

def test_print_parts_single_closed_volume_and_on_bed():
    audit=json.loads((s.OUT/'AUDIT.json').read_text())
    assert audit['source_sha256']==hashlib.sha256(Path(s.__file__).read_bytes()).hexdigest()
    for name,(shape,qty) in s.build_parts().items():
        m=trimesh.load_mesh(s.OUT/'PRINT'/f'{name}.stl')
        assert shape.val().isValid() and len(shape.solids().vals())==1
        assert m.is_watertight and m.is_winding_consistent and m.body_count==1
        assert abs(m.bounds[0,2])<1e-5
        assert audit['parts'][name]['qty']==qty
        assert audit['parts'][name]['sha256']==hashlib.sha256((s.OUT/'PRINT'/f'{name}.stl').read_bytes()).hexdigest()

def test_servo_and_clamps_do_not_intersect_fixture():
    parts=s.components()
    for i,c in enumerate(parts):
        for d in parts[i+1:]:assert c[1].intersect(d[1]).val().Volume()<1e-6

def test_nominal_nut_and_driver_access_remains_open():
    # Plate is z=-20..-16, clamp top is z=-10.6. Four original axes retained.
    body=s.stand()
    for x,y in a.clamp_points():
        nut=cq.Workplane('XY').center(x,y).circle(3.2).extrude(4).translate((0,0,-24))
        driver=cq.Workplane('XY').center(x,y).circle(2.8).extrude(15).translate((0,0,-10.6))
        assert body.intersect(nut).val().Volume()<1e-6
        assert a.servo_case().intersect(driver).val().Volume()<1e-6

def test_clip_closed_clearance_and_positive_lips():
    solid_tube=cq.Workplane('YZ').rect(20,20).extrude(15,both=True)
    assert s.cable_clip().intersect(solid_tube).val().Volume()<1e-6
    # Tube cannot move rigidly through the top throat: elastic flex is required.
    assert s.cable_clip().intersect(solid_tube.translate((0,0,2))).val().Volume()>0

def test_reference_meshes_not_in_print_zip_and_urdfs_fixed():
    import zipfile
    with zipfile.ZipFile(s.OUT/'STAGE02_DENEME.zip') as z:
        stls=[n for n in z.namelist() if n.endswith('.stl')]
        assert len(stls)==3 and all(n.startswith('ST2_') for n in stls)
    for folder,title,count in [('stand_assembly','ST2_STAND',4),('clip_assembly','ST2_CLIP',2)]:
        r=ET.parse(s.OUT/folder/(title+'.urdf')).getroot()
        assert len(r.findall('link'))==count
        assert all(j.attrib['type']=='fixed' for j in r.findall('joint'))

def test_keeps_aero_mount_dimensions_and_no_horn_adoption():
    assert a.UPPER==300 and a.FORE==220 and a.SHOULDER_Z==124
    audit=json.loads((s.OUT/'AUDIT.json').read_text())
    assert audit['horn_interface'].startswith('NOT INCLUDED')
    assert audit['aero_source_sha256']==hashlib.sha256(Path(a.__file__).read_bytes()).hexdigest()
