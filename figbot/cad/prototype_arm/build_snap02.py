"""Six-arm positive-key coupling; isolated personal bench prototype.

Horn contour: InterSideraVersor, thing:4816510, CC BY-NC-SA 4.0.
Original horn is NOT a printed part. Dimensions of physical horn unverified.
"""
from pathlib import Path
from functools import lru_cache
import hashlib, json, zipfile
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union
from cad.utils import ROOT, export_shape, shape_mesh

OUT=ROOT/'cad/prototype_arm/snap02'
REF=ROOT/'references/servo_horn_trials/originals/USER_20260907'
SOURCE=REF/'MG996R_Standard_Servo_Horn_6_Arm.stl'
FLOOR=2.0
DECK=4.0
CAP_Z=4.2
CAP_T=1.4
ROOF_Z=5.8
TOP=6.8
CLEARANCE=.20

def box(x,y,z,c):
    return cq.Workplane('XY').box(x,y,z).translate(c)

@lru_cache(None)
def profile():
    m=trimesh.load_mesh(SOURCE)
    # Union multiple actual external sections, without using holes/facet lines.
    ps=[]
    for z in [4.81,5.5,6.29,6.5,6.69]:
        loops=m.section(plane_origin=[0,0,z],plane_normal=[0,0,1]).discrete
        ps.append(max((Polygon(x[:,:2]) for x in loops),key=lambda p:p.area))
    return unary_union(ps).simplify(.003,preserve_topology=True)

def prism(poly,h,z=0):
    return cq.Workplane('XY').polyline(list(poly.exterior.coords)[:-1]).close().extrude(h).translate((0,0,z))

@lru_cache(None)
def horn_envelope():
    # Conservative solid outside envelope: small screw holes omitted.
    plate=prism(profile(),1.9,FLOOR)
    hub=cq.Workplane('XY').circle(5.91).extrude(3.1).translate((0,0,FLOOR+1.9))
    return plate.union(hub).cut(cq.Workplane('XY').circle(1.5).extrude(8))

def caps_pose(cap,travel=0):
    return [cap.translate((0,-travel,CAP_Z)),
            cap.rotate((0,0,0),(0,0,1),180).translate((0,travel,CAP_Z))]

@lru_cache(None)
def build():
    body=box(46,44,DECK,(0,0,DECK/2)).edges('|Z').fillet(2)
    # Integral low test arm: a visible torque output, not a floating capsule.
    tongue=box(18,32,3,(0,36,1.5)).edges('|Z').fillet(3)
    body=body.union(tongue)
    for y in [34,44]:
        body=body.cut(cq.Workplane('XY').center(0,y).circle(1.65).extrude(6))
    pocket=prism(profile().buffer(CLEARANCE,quad_segs=4),DECK-FLOOR+.1,FLOOR)
    # Small flared mouth, only final 0.2mm of depth; remaining wall transmits torque.
    mouth=prism(profile().buffer(.40,quad_segs=4),.3,DECK-.2)
    body=body.cut(pocket.union(mouth))
    body=body.cut(cq.Workplane('XY').circle(4).extrude(10))
    for side in [-1,1]:
        # 45-degree dovetail underside grows 0.2mm inward per 0.2mm layer.
        # No flat cantilever roof or trapped support material.
        points=[(side*x,z) for x,z in [(20,DECK),(23,DECK),(23,TOP),(17.2,TOP)]]
        rail=cq.Workplane('XZ').polyline(points).close().extrude(44).translate((0,22,0))
        for end in [-1,1]:
            # Exterior window exposes each hook for deliberate release.
            rail=rail.cut(box(7,3.0,1.8,(side*20.5,end*4.3,4.9)))
        rail=rail.union(box(3,1,ROOF_Z-DECK,(side*18.5,0,(ROOF_Z+DECK)/2)))
        body=body.union(rail)
    cap=box(39.4,20.3,CAP_T,(0,-10.85,CAP_T/2)).edges('|Z').fillet(.35)
    taper=cq.Workplane('XZ').polyline([(-19.6,0),(19.6,0),(18.2,CAP_T),(-18.2,CAP_T)]).close().extrude(60).translate((0,30,0))
    cap=cap.intersect(taper)
    for side in [-1,1]:
        slot=box(1.2,14,4,(side*16.4,-10,1))
        slot=slot.union(cq.Workplane('XY').center(side*16.4,-17).circle(.6).extrude(4))
        release=box(7,.7,4,(side*20,-2.65,1))
        cap=cap.cut(slot.union(release))
        raw=[(19.2,-5.4),(20.3,-5.4),(20.3,-4.5),(19.2,-3.1)]
        pts=[(side*x,y) for x,y in raw]
        upper=[(side*(x-CAP_T),y) for x,y in raw]
        hook=cq.Workplane('XY').polyline(pts).close().workplane(offset=CAP_T).polyline(upper).close().loft()
        cap=cap.union(hook)
    # The notch opens toward the centre; no closed hole passes over the hub.
    cap=cap.cut(cq.Workplane('XY').circle(8).extrude(4))
    return body,cap

def reference_audit():
    m=trimesh.load_mesh(SOURCE)
    four=cq.importers.importStep(str(REF/'mg996_arm_4pad.step'))
    b=four.val().BoundingBox()
    return {'six_arm':{'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'bounds_mm':m.bounds.tolist(),'watertight':bool(m.is_watertight),'components':len(m.split()),
        'plate_thickness_mm':1.9,'total_thickness_mm':5.,'hub_outer_diameter_envelope_mm':11.82,
        'source':'https://www.thingiverse.com/thing:4816510','license':'CC BY-NC-SA 4.0'},
        'four_arm':{'sha256':hashlib.sha256((REF/'mg996_arm_4pad.step').read_bytes()).hexdigest(),
        'size_mm':[b.xlen,b.ylen,b.zlen],'valid':four.val().isValid(),'solids':len(four.solids().vals()),
        'source_license':'User supplied; source/license UNVERIFIED; not used in print geometry'},
        'finding':'Different shapes and sizes, NOT interchangeable. Neither proves physical supplied-horn fit.'}

def audit_geometry():
    body,cap=build();horn=horn_envelope();caps=caps_pose(cap)
    audit={'status':'DIGITAL BENCH PRINT; PHYSICAL FIT/STRENGTH REQUIRED',
        'dimensions':{'body_mm':[46,74,TOP],'radial_clearance_mm':CLEARANCE,
        'floor_mm':FLOOR,'star_wall_depth_mm':2.,'lid_z_mm':CAP_Z,'lid_thickness_mm':CAP_T,
        'latch_window_top_z_mm':ROOF_Z,'rail_underside_deg':45,'hub_aperture_mm':16,'axial_horn_play_mm':.3},
        'references':reference_audit(),'checks':{}}
    def vol(a,b):return max(0,a.intersect(b).val().Volume())
    audit['checks']['closed_pair_overlaps_mm3']={
        'body_horn':vol(body,horn),'body_cap_A':vol(body,caps[0]),'body_cap_B':vol(body,caps[1]),
        'horn_cap_A':vol(horn,caps[0]),'horn_cap_B':vol(horn,caps[1]),'cap_A_cap_B':vol(*caps)}
    assert max(audit['checks']['closed_pair_overlaps_mm3'].values())<1e-6
    # Rigid plate can slide; hooks are tested separately because they flex.
    rigid=cap.intersect(box(33.8,60,4,(0,0,1)))
    max_hub=0.;max_rigid=0.;max_latch=0.
    for t in np.linspace(0,46,47):
        for moving in caps_pose(cap,float(t)):
            max_hub=max(max_hub,vol(moving,horn))
            max_latch=max(max_latch,vol(moving,body))
        for moving in caps_pose(rigid,float(t)):max_rigid=max(max_rigid,vol(moving,body))
    audit['checks']['insertion']={'samples_each_side':47,'horn_overlap_mm3':max_hub,
        'rigid_plate_overlap_mm3':max_rigid,'intentional_hook_overlap_mm3':max_latch,
        'hook_required_inward_deflection_mm':.5,'flex_force_and_fatigue':'UNVERIFIED'}
    assert max_hub<1e-6 and max_rigid<1e-6
    audit['checks']['torque_stop_overlap_at_rotation_mm3']={str(a):vol(body,horn.rotate((0,0,0),(0,0,1),a)) for a in [-3,3]}
    assert min(audit['checks']['torque_stop_overlap_at_rotation_mm3'].values())>1
    audit['checks']['horn_lift_stop_mm3']=sum(vol(horn.translate((0,0,.5)),s) for s in caps)
    assert audit['checks']['horn_lift_stop_mm3']>1
    audit['checks']['cap_lift_stop_mm3']=[vol(body,s.translate((0,0,.5))) for s in caps]
    audit['checks']['cap_pullout_stop_mm3']=[vol(body,s) for s in caps_pose(cap,1)]
    assert min(audit['checks']['cap_lift_stop_mm3'])>1 and min(audit['checks']['cap_pullout_stop_mm3'])>0
    # Explicit proposed installation constraint, NOT inferred servo dimensions.
    # All rotating print geometry below Z6.8; motor non-shaft keepout starts Z7.
    keepout=box(60,70,42,(0,10,28))
    audit['checks']['motor_keepout']={'assumption':'Motor non-shaft structure starts at Z7mm, verify physical gap; shaft/spline engagement not certified',
        'required_face_clearance_from_horn_end_mm':0,'printed_top_to_plane_gap_mm':.2,
        'angles_deg':list(range(-90,91,15)),
        'overlap_mm3':max(vol(body.rotate((0,0,0),(0,0,1),a),keepout) for a in range(-90,91,15))}
    assert audit['checks']['motor_keepout']['overlap_mm3']<1e-6
    # Horn drops axially into the open body without being trapped by rails.
    audit['checks']['horn_installation_overlap_mm3']=max(vol(body,horn.translate((0,0,z))) for z in np.linspace(0,15,16))
    assert audit['checks']['horn_installation_overlap_mm3']<1e-6
    return audit

def render(parts,reference):
    # Orthographic CPU depth buffer: prevents long STL triangles from showing
    # through closer surfaces (a painter-sorted Matplotlib preview artifact).
    from PIL import Image, ImageDraw, ImageFont
    canvas=Image.new('RGB',(1500,1120),'white');draw=ImageDraw.Draw(canvas)
    font=lambda n:ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
    draw.text((750,28),'SNAP-02 · Altı kollu başlığı kavrayan bağlantı',font=font(32),fill='#172d38',anchor='mt')
    body,cap=parts
    for idx,(title,travel,raise_horn) in enumerate([
        ('1  Yıldızı şekilli yuvaya bırak',30,13),
        ('2  İki kapağı karşılıklı kaydır',13,0),
        ('3  Kilitli bağlantı / motor tarafı',0,0),
        ('4  Gerçek altı kollu yuva / kapaksız',None,0)]):
        meshes=[]
        v,f=shape_mesh(body);meshes.append((trimesh.Trimesh(v,f),[.10,.53,.65]))
        if travel is not None:
            for i,c in enumerate(caps_pose(cap,travel)):
                v,f=shape_mesh(c);meshes.append((trimesh.Trimesh(v,f),[.93,.51,.13] if i==0 else [.54,.38,.69]))
            h=reference.copy();h.apply_translation((0,0,FLOOR-4.8+raise_horn));meshes.append((h,[.22,.24,.27]))
        az=np.radians(-55);el=np.radians(52)
        right=np.array([-np.sin(az),np.cos(az),0])
        up=np.array([-np.sin(el)*np.cos(az),-np.sin(el)*np.sin(az),np.cos(el)])
        look=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
        matrix=np.stack([right,up,look],axis=1)
        projected=np.vstack([m.vertices@matrix for m,c in meshes]);lo=projected.min(0);hi=projected.max(0)
        w,h=700,420;scale=min((w-40)/(hi[0]-lo[0]),(h-35)/(hi[1]-lo[1]))
        center=(lo+hi)/2
        pixels=np.full((h,w,3),255,dtype=np.uint8);depth=np.full((h,w),-np.inf)
        for m,color in meshes:
            light=np.array([-.4,-.5,1]);light/=np.linalg.norm(light)
            shades=.55+.4*np.abs(m.face_normals@light)
            coords=m.vertices@matrix
            coords[:,0]=(coords[:,0]-center[0])*scale+w/2
            coords[:,1]=h/2-(coords[:,1]-center[1])*scale
            for k,face in enumerate(m.faces):
                t=coords[face];a,b,c=t
                x0=max(0,int(np.floor(t[:,0].min())));x1=min(w-1,int(np.ceil(t[:,0].max())))
                y0=max(0,int(np.floor(t[:,1].min())));y1=min(h-1,int(np.ceil(t[:,1].max())))
                det=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(det)<1e-9 or x1<x0 or y1<y0:continue
                yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
                u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/det
                v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/det
                q=1-u-v;z=u*a[2]+v*b[2]+q*c[2]
                target=depth[y0:y1+1,x0:x1+1]
                mask=(u>=-1e-7)&(v>=-1e-7)&(q>=-1e-7)&(z>target)
                target[mask]=z[mask]
                pixels[y0:y1+1,x0:x1+1][mask]=np.array(color)*shades[k]*255
        px=25+(idx%2)*750;py=115+(idx//2)*455
        draw.text((px+w/2,py-32),title,font=font(23),fill='#172d38',anchor='mt')
        canvas.paste(Image.fromarray(pixels),(px,py))
    draw.text((750,1050),'Mavi: gövde  |  Turuncu + mor: aynı kapaktan 2 adet  |  Gri: orijinal yıldız (basılmayacak)',font=font(22),fill='#172d38',anchor='mt')
    draw.text((750,1083),'Merkez vidası alttaki Ø8 erişim deliğinden takılır. Eski SNAP-01 parçaları kullanılmaz.',font=font(20),fill='#172d38',anchor='mt')
    canvas.save(OUT/'MONTAJ.png')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    audit=audit_geometry();body,cap=build()
    audit['generator_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    audit['print_parts']={}
    for name,shape,qty in [('S02_01_YILDIZ_GOVDE',body,1),('S02_02_YARIM_KAPAK',cap,2)]:
        assert shape.val().isValid() and len(shape.solids().vals())==1
        export_shape(shape,OUT/'PRINT',name,['stl','step'])
        m=trimesh.load_mesh(OUT/'PRINT'/f'{name}.stl')
        assert m.is_watertight and len(m.split())==1
        audit['print_parts'][name]={'qty':qty,'size_mm':m.extents.tolist(),'volume_mm3':float(m.volume),'watertight':bool(m.is_watertight)}
    # One plate file already contains one body plus two covers at Z0.
    plate=[]
    for name,delta in [('S02_01_YILDIZ_GOVDE',(0,0,0)),('S02_02_YARIM_KAPAK',(51,-3,0)),('S02_02_YARIM_KAPAK',(51,24,0))]:
        m=trimesh.load_mesh(OUT/'PRINT'/f'{name}.stl');m.apply_translation(delta);plate.append(m)
    layout=trimesh.util.concatenate(plate);layout.export(OUT/'S02_TEK_TABLA_3_PARCA.stl')
    assert len(layout.split())==3 and layout.is_watertight
    audit['print_layout']={'components':3,'bounds_mm':layout.bounds.tolist(),'size_mm':layout.extents.tolist()}
    original=trimesh.load_mesh(SOURCE)
    positioned=original.copy();positioned.apply_translation((0,0,FLOOR-4.8))
    scene=trimesh.Scene();assembly=cq.Assembly(name='SNAP02_SIX_ARM')
    items=[('body',body,'S02_01_YILDIZ_GOVDE',(0,0,0),0,(.1,.53,.65)),
        ('cap_A',caps_pose(cap)[0],'S02_02_YARIM_KAPAK',(0,0,CAP_Z),0,(.93,.51,.13)),
        ('cap_B',caps_pose(cap)[1],'S02_02_YARIM_KAPAK',(0,0,CAP_Z),np.pi,(.54,.38,.69))]
    robot=ET.Element('robot',name='SNAP02_FIXED_REVIEW_NOT_CONTROL')
    for name,s,file,xyz,angle,color in items:
        assembly.add(s,name=name,color=cq.Color(*color))
        v,f=shape_mesh(s);m=trimesh.Trimesh(v,f);m.visual.face_colors=np.array([*color,1])*255;scene.add_geometry(m,node_name=name)
        link=ET.SubElement(robot,'link',name=name)
        for tag in ['visual','collision']:
            geom=ET.SubElement(ET.SubElement(link,tag),'geometry');ET.SubElement(geom,'mesh',filename=f'PRINT/{file}.stl',scale='0.001 0.001 0.001')
        if name!='body':
            j=ET.SubElement(robot,'joint',name='fixed_'+name,type='fixed');ET.SubElement(j,'parent',link='body');ET.SubElement(j,'child',link=name)
            ET.SubElement(j,'origin',xyz=' '.join(str(x/1000) for x in xyz),rpy=f'0 0 {angle}')
    export_shape(horn_envelope(),OUT/'REFERENCE_ONLY','HORN_ENVELOPE',['step','stl'])
    assembly.add(horn_envelope(),name='original_horn_envelope_reference',color=cq.Color(.22,.24,.27))
    positioned.visual.face_colors=[55,60,65,255];scene.add_geometry(positioned,node_name='original_horn_reference')
    link=ET.SubElement(robot,'link',name='original_horn_reference')
    geom=ET.SubElement(ET.SubElement(link,'visual'),'geometry');ET.SubElement(geom,'mesh',filename='REFERENCE_ONLY/HORN_ENVELOPE.stl',scale='0.001 0.001 0.001')
    j=ET.SubElement(robot,'joint',name='fixed_horn',type='fixed');ET.SubElement(j,'parent',link='body');ET.SubElement(j,'child',link='original_horn_reference')
    ET.indent(robot);ET.ElementTree(robot).write(OUT/'S02_FIXED_REVIEW.urdf',encoding='utf-8',xml_declaration=True)
    assembly.save(str(OUT/'S02_MONTAJ.step'));scene.export(OUT/'S02_MONTAJ.glb')
    render((body,cap),original)
    (OUT/'AUDIT.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    with zipfile.ZipFile(OUT/'SNAP02_ALTI_KOLLU_BAGLANTI.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in ['S02_TEK_TABLA_3_PARCA.stl','ONCE_OKU.md','MONTAJ.png','AUDIT.json']:
            z.write(OUT/name,name)
        for f in (OUT/'PRINT').glob('*.stl'):z.write(f,'AYRI_PARCA/'+f.name)
    print(json.dumps({'output':str(OUT),'checks':audit['checks'],'print_parts':audit['print_parts']},indent=2))

if __name__=='__main__':main()
