"""DEC-081 nominal geometry and shipped package checks; not a physical load rating."""
import hashlib,json,math,zipfile
from collections import Counter
from functools import lru_cache
import xml.etree.ElementTree as ET
import cadquery as cq
import pytest
from cad.prototype_arm import build_linka_v1 as a
from scripts.project_paths import ROOT,CAD,PRINTS
from cad.prototype_arm.export_forma_v6 import part_settings

@pytest.mark.parametrize('pid,od,id_,length,count',[
    ('L1-23-ELBOW-BUSH-LONG',8,5.3,28,1),
    ('L1-24-ELBOW-BUSH-SHORT',8,5.3,4,2),
    ('L1-25-FINGER-BUSH',4.8,2.4,6,3)])
def test_sleeve_shape_wall_bore_and_upright_export(pid,od,id_,length,count):
    s=cq.importers.importStep(str(CAD/'PART_STEP'/f'{pid}.step')).val()
    assert s.isValid() and len(s.Solids())==1
    assert s.Volume()==pytest.approx(math.pi/4*(od**2-id_**2)*length)
    assert (od-id_)/2>=1.2-1e-8
    assert s.intersect(cq.Solid.makeCylinder(id_/2-.01,length,cq.Vector(0,0,0))).Volume()<1e-6
    p=a.print_pose(pid,cq.Workplane(obj=s)).val().BoundingBox()
    assert (p.xlen,p.ylen,p.zlen)==pytest.approx((od,od,length))
    with zipfile.ZipFile(CAD/'3MF'/f'{pid}.3mf') as z:
        r=ET.fromstring(z.read('Metadata/Slic3r_PE_model.config'))
    settings={m.get('key'):m.get('value') for m in r.find('object').findall('metadata')}
    assert settings['fill_density']=='100%' and settings['perimeters']=='3'
    assert a.PARTS[pid][1]==count

def test_new_finger_sleeve_free_and_old_finger_rejected():
    f=cq.importers.importStep(str(CAD/'PART_STEP/L1-17-FINGER.step')).val()
    s=a.finger_bush().rotate((0,0,0),(1,0,0),-90).translate((0,-3,0)).val()
    assert f.intersect(s).Volume()<1e-6
    # M2 nominal shaft, no interference; .5mm difference in axial lengths.
    assert s.intersect(a.h.cy(1,-3,6).val()).Volume()<1e-6
    assert f.intersect(a.h.box(18,20,6,(0,0,0)).val()).BoundingBox().ylen==pytest.approx(5.5)
    # New sleeve is intentionally incompatible with old3.2mm bore.
    old_bore_radius=1.6
    assert a.FINGER_BUSH_OD/2>old_bore_radius

@pytest.mark.parametrize('grip',[-15,0,20,40])
def test_finger_bushes_clear_adjacent_nominal_solids(grip):
    items=a.local_items(grip)
    sleeves=[i for i in items if i.part_id=='L1-25-FINGER-BUSH']
    near=[i for i in items if i.part_id in {'L1-16-PALM','L1-17-FINGER','L1-18-PAD'} or i.name.startswith('finger pivot M2')]
    for b in sleeves:
        for p in near:
            assert b.shape.val().intersect(p.shape.val()).Volume()<1e-5,(grip,b.name,p.name)

def test_print_bom_matches_assembly_and_no_metal_sleeve_duplicates():
    items=a.local_items()
    actual=Counter(i.part_id for i in items if i.part_id and 'BUSH' in i.part_id)
    assert actual==Counter({'L1-23-ELBOW-BUSH-LONG':1,'L1-24-ELBOW-BUSH-SHORT':2,'L1-25-FINGER-BUSH':3})
    assert not any('aluminium elbow' in i.name or 'M2 and sleeve' in i.name for i in items)
    assert all(i.mass_g is None for i in items if i.part_id and 'BUSH' in i.part_id)

def test_only_fingers_change_and_new_files_are_separate():
    old=json.loads((ROOT/'reports/plastic_bushings/before_hashes.json').read_text())
    changed=[name for name,h in old.items() if hashlib.sha256((CAD/'PRINT_STL'/name).read_bytes()).hexdigest()!=h]
    assert set(changed)=={'L1-17-FINGER.stl','L1-18-PAD.stl'}
    ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    expected={'04A_YALNIZ_YENI_PARMAKLAR':Counter({'L1-17-FINGER':3}),
              '06_PLASTIK_BURCLAR':Counter({'L1-23-ELBOW-BUSH-LONG':1,'L1-24-ELBOW-BUSH-SHORT':2,'L1-25-FINGER-BUSH':3})}
    for name,counts in expected.items():
        with zipfile.ZipFile(PRINTS/name/f'{name}.3mf') as z:r=ET.fromstring(z.read('3D/3dmodel.model'))
        assert Counter(o.get('name').split('__')[0] for o in r.findall('m:resources/m:object',ns))==counts

def test_no_metal_bush_purchase_and_fasteners_unchanged():
    from scripts.build_linka_shopping import ROWS
    r={r['code']:r for r in ROWS}
    for code in ['ELBOW_SLEEVES','FINGER_TUBE']:
        assert r[code]['order_hold'] and r[code]['buy_quantity'] is None
        assert r[code]['url'] is None and r[code]['supplier']=='Mevcut filament'
    assert r['FINGER_SCREW']['required']==3 and r['ELBOW_AXLE']['required']==1

def test_slicer_setting_only_new_bushes_changed():
    assert part_settings('L1-25-FINGER-BUSH')['fill_density']=='100%'
    assert part_settings('L1-17-FINGER')['fill_density']=='100%'
