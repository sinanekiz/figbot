"""Digital release checks; no physical strength/fit certification."""
import hashlib,json,math,zipfile
import xml.etree.ElementTree as ET
import numpy as np
import pytest,trimesh,cadquery as cq
from cad.prototype_arm import build_forma_v6 as a
from cad.prototype_arm import export_forma_v6 as exporter


def test_measured_yaw_body_shaft_and_race_share_correct_axis():
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_Cylinder,GeomAbs_Torus
    j1=next(i.shape for i in a.local_items() if i.name=='J1 servo')
    case=j1.intersect(a.box(100,100,1,(0,0,25))).val().BoundingBox()
    assert abs(case.xlen-39.9)<1e-6
    assert abs((case.xmin+case.xmax)/2+9.8)<1e-6
    assert abs(case.xmax-10.15)<1e-6
    shafts=[]
    for f in j1.faces().vals():
        s=BRepAdaptor_Surface(f.wrapped)
        if s.GetType()==GeomAbs_Cylinder and abs(s.Cylinder().Radius()-2.85)<1e-6:
            shafts.append(s.Cylinder().Axis().Location())
    assert shafts and all(abs(p.X())<1e-6 and abs(p.Y())<1e-6 for p in shafts)
    races=[]
    for f in a.base().faces().vals():
        s=BRepAdaptor_Surface(f.wrapped)
        if s.GetType()==GeomAbs_Torus and abs(s.Torus().MajorRadius()-45)<1e-6:
            races.append(s.Torus().Location())
    assert races and all(abs(p.X())<1e-6 and abs(p.Y())<1e-6 for p in races)
    assert abs(case.xmax-2.85-7.3)<1e-6
    # One measured specimen must not rewrite unmeasured shoulder/elbow profiles.
    assert a.MG['length']==40.7 and a.MG['offset']==-10.15


def test_measured_yaw_cavity_and_ear_pockets_follow_specimen():
    base=a.base().val()
    # DEC-073: retain ALL of the pre-measurement opening (-30.9 .. 10.6).
    for x in [-30.85,10.55]:assert not base.isInside(cq.Vector(x,0,35))
    for x in [-30.95,10.65]:assert base.isInside(cq.Vector(x,0,35))
    for y in [-10.2,10.2]:assert not base.isInside(cq.Vector(-10.15,y,35))
    for y in [-10.3,10.3]:assert base.isInside(cq.Vector(-10.15,y,35))
    coupon=a.yaw_fit_coupon().val()
    for x in [-30.85,10.55]:assert not coupon.isInside(cq.Vector(x+9.8,0,4))
    for x in [-34.55,14.95]:
        for y in [-5,5]:
            assert not base.isInside(cq.Vector(x,y,36))
            assert base.isInside(cq.Vector(x,y,32.25))
    assert sum(s.Volume() for s in a.base().intersect(a.servo(spec=a.YAW_MG).translate((0,0,50))).solids().vals())<1e-5
    assert a.yaw_fit_coupon().val().isValid() and len(a.yaw_fit_coupon().solids().vals())==1


def test_yaw_installation_swept_envelope_preserves_race_and_seats():
    # Continuous union envelope for body, flange and shaft along a 60mm lift.
    # Upper assembly/cage/balls and ear bolts are removed first. Cable is NOT
    # included: boot, connector and bend geometry still require measurements.
    p=a.YAW_MG
    body=a.rounded(p['length'],p['width'],p['height']+60,1,(p['offset'],0,50-p['height']/2+30))
    flange=a.rounded(p['ear_pitch']+6,p['width'],62.2,.7,(p['offset'],0,50+p['ear_z']+1.1+30))
    swept=body.union(flange).union(a.cz(2.85,50,65))
    assert sum(s.Volume() for s in swept.intersect(a.base()).solids().vals())<1e-5
    # All race faces outsideR40.8 remain as designed after the local entry relief.
    race=a.ring(38,55,43,5).cut(a.cq.Workplane(obj=a.cq.Solid.makeTorus(45,4.2,(0,0,50))))
    outer=race.intersect(a.ring(40.8,56,42,8))
    assert sum(s.Volume() for s in outer.cut(a.base()).solids().vals())<1e-5


def test_retainer_inner_roof_clearance_and_uplift_capture():
    band=a.ring(53.2,54.8,57,8)
    # The corner ledges reach Z60.4, above the annular flange's Z60 surface.
    moving_edge=a.rotor().intersect(a.ring(53.2,54.8,57,3.5))
    flange=a.rotor().intersect(a.box(1,1,4,(54,0,59)))
    for side in [-1,1]:
        cap=a.retainer_half(side)
        roof=cap.intersect(band)
        assert abs(roof.val().BoundingBox().zmin-moving_edge.val().BoundingBox().zmax-1.)<1e-6
        assert abs(roof.val().BoundingBox().zmin-flange.val().BoundingBox().zmax-1.4)<1e-6
        assert roof.val().BoundingBox().zlen>=2.59
        for angle in range(0,360,45):
            raised=a.rotor().rotate((0,0,0),(0,0,1),angle).translate((0,0,.9))
            assert sum(s.Volume() for s in raised.intersect(cap).solids().vals())<1e-5
        assert sum(s.Volume() for s in a.rotor().translate((0,0,1.6)).intersect(cap).solids().vals())>1

@pytest.mark.parametrize('pid',list(a.PARTS))
def test_exported_parts(pid):
    fn,n,frame=a.PARTS[pid];s=fn()
    assert s.val().isValid() and len(s.solids().vals())==1
    f=a.OUT/'PRINT_STL'/(pid+'.stl');m=trimesh.load_mesh(f)
    assert m.is_watertight and m.is_winding_consistent and m.volume>0
    assert len(m.split())==1 and max(m.extents)<=246
    assert m.bounds[0].min()>-1e-4
    restored=cq.importers.importStep(str(a.OUT/'PART_STEP'/(pid+'.step')))
    assert restored.val().isValid() and len(restored.solids().vals())==1
    # Smooth lofts need adaptive integration: the kernel's default quadrature
    # differs before/after STEP reparameterization. Keep the export tolerance.
    assert abs(restored.val().Volume(1e-8)/s.val().Volume(1e-8)-1)<1e-4
    with zipfile.ZipFile(a.OUT/'3MF'/(pid+'.3mf')) as z:
        root=ET.fromstring(z.read('Metadata/Slic3r_PE_model.config'))
        mods=root.findall(".//metadata[@value='ParameterModifier']")
        assert len(mods)==len(exporter.modifier_regions(pid))
    manifest=json.loads((a.OUT/'MANIFEST.json').read_text())
    row=next(r for r in manifest if r['part']==pid)
    assert row['stl_sha256']==hashlib.sha256(f.read_bytes()).hexdigest()

def test_sampled_collision_and_ik_report():
    from cad.prototype_arm.validate_forma_v6 import source_hashes
    r=json.loads((a.OUT/'VALIDATION.json').read_text())
    assert r['sources']==source_hashes()
    assert not r['neutral_hits']
    assert len(r['targets'])==5 and len(r['path'])==12 and len(r['gripper_sweep'])==6
    for row in list(r['targets'].values())+r['path']:
        assert not row['hits'] and not row['vehicle']['hits'],row
        assert row['vehicle']['min_arm_z_mm']>0 and row['vehicle']['fruit_bottom_mm']>=-1e-6
    assert max(row['error_mm'] for row in r['targets'].values())<1e-6
    assert all(not row['hits'] for row in r['gripper_sweep']+r['steering'])
    assert r['horizontal_screen']['modeled_mass_g']['elbow']<150

def test_factory_ear_insert_access_and_back_wall():
    # Pilot is open from factory ear face; no obstruction / through-hole below.
    for micro in [False,True]:
        p=a.MICRO if micro else a.MG;s=a.mount_region(micro).val()
        for x,y in a.ear_points(micro):
            assert not s.isInside(cq.Vector(x,y,p['ear_z']-1))
            assert s.isInside(cq.Vector(x,y,p['ear_z']-p['insert_depth']-.75))

def test_urdf_independent_forward_kinematics():
    root=ET.parse(a.OUT/'URDF/FORMA_V6_REVIEW.urdf').getroot()
    for q in [(0,-35,85,-50),(-118,-96,72,24)]:
        vals={n:math.radians(v) for n,v in zip(['yaw','shoulder','elbow','wrist'],q)}
        fs={'base':np.eye(4)}
        for j in root.findall('joint')[:4]:
            o=j.find('origin');t=trimesh.transformations.euler_matrix(*np.fromstring(o.get('rpy'),sep=' '))
            t[:3,3]=np.fromstring(o.get('xyz'),sep=' ')*1000
            r=trimesh.transformations.rotation_matrix(vals[j.get('name')],np.fromstring(j.find('axis').get('xyz'),sep=' '))
            fs[j.find('child').get('link')]=fs[j.find('parent').get('link')]@t@r
        for name,t in a.frames(q).items():assert np.allclose(t,fs[name],atol=1e-8)
    assert len(root.findall("joint[@type='revolute']"))==7
    mount=ET.parse(a.OUT/'URDF/FORMA_V6_ROVER_REVIEW.urdf').getroot().find("joint[@name='mount']/origin")
    assert np.allclose(np.fromstring(mount.get('xyz'),sep=' ')*1000,a.BASE_WORLD)

def test_cost_unknowns_and_motor_reuse():
    from scripts.build_forma_v6_hardware import main
    r=main()
    assert r['historical_existing_motors_TRY']=='1135.49'
    assert r['total_build_cost_TRY'] is None and r['unpriced_lines']>0
    assert not r['new_motor_purchase_required'] and not r['purchase_ledger_changed']

def test_motor_count_and_critical_interfaces():
    motors=[i for i in a.local_items() if i.name.endswith(' servo')]
    assert len(motors)==6 and sum(i.mass_g==55 for i in motors)==4
    assert len([i for i in a.local_items() if i.name.startswith('PB02 ball')])==24
    assert a.UPPER==180 and a.FORE==140 and a.RACE_R==45
    assert np.allclose(a.FRUIT,[38,0,-66])

def test_offline_slicer_accepts_final_files_and_local_density():
    r=json.loads((a.OUT/'OFFLINE_SLICE_AUDIT.json').read_text())
    assert not r['printer_commands_sent'] and len(r['results'])==len(a.PARTS)
    for row in r['results']:
        f=a.OUT/'3MF'/(row['part']+'.3mf')
        assert row['input_sha256']==hashlib.sha256(f.read_bytes()).hexdigest()
        assert row['returncode']==row['roundtrip_returncode']==0
        assert row['modifiers_preserved'] and not row['warnings']
        assert all(all(int(v)==0 for v in repair.values()) for repair in row['mesh_repairs'])

def test_assembly_step_and_glb_placement():
    restored=cq.importers.importStep(str(a.OUT/'FORMA_V6_ASSEMBLY.step'))
    solids=restored.solids().vals()
    assert solids and all(s.isValid() and s.Volume()>0 for s in solids)
    cad=cq.Compound.makeCompound([i.shape.val() for i in a.assembly()]);expected=cad.BoundingBox()
    actual=restored.val().BoundingBox()
    assert max(abs(getattr(expected,k)-getattr(actual,k)) for k in ['xmin','xmax','ymin','ymax','zmin','zmax'])<1e-4
    scene=trimesh.load(a.OUT/'FORMA_V6_ASSEMBLY.glb',force='scene')
    # Vertex colors are bytes; float0..255 used to clamp every component white.
    colors=np.concatenate([m.visual.vertex_colors for m in scene.geometry.values()])
    assert colors[:,:3].min()<60 and len(np.unique(colors[:,:3],axis=0))>=5
    lo,hi=scene.bounds
    assert np.allclose(lo,[expected.xmin,expected.ymin,expected.zmin],atol=.5)
    assert np.allclose(hi,[expected.xmax,expected.ymax,expected.zmax],atol=.5)
