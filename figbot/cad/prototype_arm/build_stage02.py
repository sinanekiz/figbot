"""Independent AERO V3 stage-02 bench fixture and cable clip fit experiment.

No nominal horn interface is adopted. No changes to the AERO arm geometry.
"""
from pathlib import Path
from functools import lru_cache
import hashlib,json,zipfile
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh
from cad.utils import ROOT,export_shape
from cad.prototype_arm import build_aero_v3 as a

OUT=ROOT/'cad/prototype_arm/stage02'
STATUS='DRY FIT BENCH EXPERIMENT; PHYSICAL VALIDATION REQUIRED; NOT A COMPLETE ARM'

@lru_cache(None)
def stand():
    # Original mount interface, same servo axis/origin and original clamp pattern.
    centre=-.2*a.MG[0]
    floor_top=-6-a.MG[2]-3
    base=a.rb(76,60,5,5,(centre,0,floor_top-2.5))
    for sx in [-1,1]:
        for sy in [-1,1]:base=a.hole(base,centre+sx*31,sy*24,4.5)
    s=base.union(a.mount_plate())
    # Posts outside the body, inside the mounting plate; keep underside nut access.
    top=-18
    for side in [-1,1]:
        s=s.union(a.rb(6,16,top-floor_top,1,(centre+side*28.3,0,(top+floor_top)/2)))
    return s

@lru_cache(None)
def cable_clip():
    # Profile axis X; this is a cable retainer only, never a structural tube joint.
    outer=cq.Workplane('YZ').rect(24.2,24.2).extrude(5,both=True).edges('|X').fillet(1.4)
    inner=cq.Workplane('YZ').rect(20.6,20.6).extrude(8,both=True)
    s=outer.cut(inner)
    # Open top; 19mm throat must flex over 20mm tube. Root walls stay 1.8mm.
    s=s.cut(a.box(20,19,6,(0,0,12)))
    # Two chamfered entry lips: 45 degree relief for pushing onto the tube.
    for sign in [-1,1]:
        poly=[(sign*9.5,10.6),(sign*9.5,12.5),(sign*11.4,12.5)]
        s=s.cut(cq.Workplane('YZ').polyline(poly).close().extrude(8,both=True))
    # Open U cable trough alongside the tube; avoid crushing connectors/wires.
    trough=a.rb(10,9,10,1,(0,15.6,0),long_axis='X')
    trough=trough.cut(a.box(14,5.4,12,(0,15.6,3)))
    s=s.union(trough)
    return s

def put_on_bed(shape,rotation=None):
    if rotation:shape=shape.rotate((0,0,0),rotation[0],rotation[1])
    b=shape.val().BoundingBox()
    return shape.translate((0,0,-b.zmin))

def build_parts():
    return {
      'ST2_01_MG996R_SEHPA':(put_on_bed(stand()),1),
      'ST2_02_MG996R_KELEPCE':(put_on_bed(a.clamp_bar()),2),
      # Cross section flat on bed so spring flex stays in the layer plane.
      'ST2_03_PROFIL_KABLO_KILAVUZU':(put_on_bed(cable_clip(),((0,1,0),90)),1),
    }

def components():
    parts=[('stand',stand(),'ST2_01_MG996R_SEHPA',(.13,.55,.66)),
           ('motor_REFERENCE_NOT_PRINT',a.servo_case(),'REFERENCE',(.2,.2,.2))]
    for side in [-1,1]:
        p=a.clamp_bar().translate((-.2*a.MG[0]+side*(a.MG[0]/2+4),0,-13.6))
        parts.append((f'clamp_{side}',p,'ST2_02_MG996R_KELEPCE',(.96,.57,.16)))
    return parts

def export_assembly(parts,folder,title):
    folder.mkdir(exist_ok=True,parents=True)
    assembly=cq.Assembly(name=title)
    scene=trimesh.Scene()
    robot=ET.Element('robot',name=title+'_FIXED_REVIEW_ONLY')
    manifest=[]
    for idx,(name,part,part_id,color) in enumerate(parts):
        assembly.add(part,name=name,color=cq.Color(*color))
        export_shape(part,folder,name,['stl'])
        mesh=trimesh.load_mesh(folder/f'{name}.stl')
        mesh.visual.face_colors=np.array([*color,1])*255
        scene.add_geometry(mesh,node_name=name)
        link=ET.SubElement(robot,'link',name=name)
        for tag in ['visual','collision']:
            g=ET.SubElement(ET.SubElement(link,tag),'geometry')
            ET.SubElement(g,'mesh',filename=f'{name}.stl',scale='0.001 0.001 0.001')
        if idx:
            j=ET.SubElement(robot,'joint',name='fixed_'+name,type='fixed');ET.SubElement(j,'parent',link=parts[0][0]);ET.SubElement(j,'child',link=name)
        manifest.append({'name':name,'print_part':part_id,'color':color})
    assembly.save(str(folder/f'{title}.step'))
    scene.export(folder/f'{title}.glb')
    ET.indent(robot);ET.ElementTree(robot).write(folder/f'{title}.urdf',encoding='utf-8',xml_declaration=True)
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

def render():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(12,6),facecolor='#f4f6f7')
    for index,(folder,title) in enumerate([('stand_assembly','MG996R sabit govde sehpası'),('clip_assembly','20mm profil kablo kilavuzu')]):
        ax=fig.add_subplot(1,2,index+1,projection='3d')
        meta=json.loads((OUT/folder/'manifest.json').read_text());vertices=[];triangles=[];colors=[]
        for item in meta:
            mesh=trimesh.load_mesh(OUT/folder/(item['name']+'.stl'));vertices.append(mesh.vertices)
            light=np.array([-.4,-.6,1]);light/=np.linalg.norm(light)
            shade=.5+.45*np.abs(mesh.face_normals@light)
            triangles.extend(mesh.triangles);colors.extend(np.array(item['color'])[None,:]*shade[:,None])
        ax.add_collection3d(Poly3DCollection(triangles,facecolors=colors,edgecolors='none'))
        v=np.vstack(vertices);lo=v.min(0);hi=v.max(0);d=hi-lo
        ax.set_xlim(lo[0]-3,hi[0]+3);ax.set_ylim(lo[1]-3,hi[1]+3);ax.set_zlim(lo[2]-3,hi[2]+3)
        ax.set_box_aspect(d+6);ax.view_init(elev=28,azim=-55);ax.set_axis_off();ax.set_title(title,fontsize=12)
    fig.suptitle('STAGE-02 | Kuru montaj denemesi - gri motor/profil BASILMAYACAK',fontsize=13)
    fig.tight_layout();fig.savefig(OUT/'MONTAJ.png',dpi=160);plt.close(fig)

def main():
    OUT.mkdir(exist_ok=True,parents=True)
    report={'status':STATUS,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'aero_source_sha256':hashlib.sha256(Path(a.__file__).read_bytes()).hexdigest(),
            'horn_interface':'NOT INCLUDED; awaiting physical horn identification',
            'fasteners':'Existing nominal M3 clamp arrangement retained; hardware ownership/fit UNVERIFIED',
            'parts':{},'stand_intersections_mm3':[]}
    for name,(part,qty) in build_parts().items():
        assert part.val().isValid() and len(part.solids().vals())==1
        export_shape(part,OUT/'PRINT',name,['stl','step'])
        m=trimesh.load_mesh(OUT/'PRINT'/f'{name}.stl')
        report['parts'][name]={'qty':qty,'bounds_mm':m.bounds.tolist(),'volume_mm3':float(m.volume),'full_solid_mass_PLA_1_24_g_cm3_ESTIMATE_g':float(m.volume)*.00124,'watertight':bool(m.is_watertight),'bodies':int(m.body_count),'sha256':hashlib.sha256((OUT/'PRINT'/f'{name}.stl').read_bytes()).hexdigest()}
    parts=components()
    for i,c in enumerate(parts):
        for d in parts[i+1:]:
            v=c[1].intersect(d[1]).val().Volume()
            report['stand_intersections_mm3'].append([c[0],d[0],v]);assert v<1e-5,(c[0],d[0],v)
    tube=cq.Workplane('YZ').rect(20,20).rect(17,17).extrude(22,both=True)
    v=cable_clip().intersect(tube).val().Volume();report['clip_tube_closed_intersection_mm3']=v;assert v<1e-6
    report['stand_servo_bottom_clearance_mm']=3
    report['clip_inner_width_mm']=20.6;report['clip_throat_mm']=19
    report['clip_flex_capacity']='UNVERIFIED; requires at least0.5mm lateral deflection per side for nominal20mm tube'
    export_assembly(parts,OUT/'stand_assembly','ST2_STAND')
    export_assembly([('clip',cable_clip(),'ST2_03_PROFIL_KABLO_KILAVUZU',(.12,.62,.52)),('tube_REFERENCE_NOT_PRINT',tube,'REFERENCE',(.65,.67,.7))],OUT/'clip_assembly','ST2_CLIP')
    render()
    (OUT/'AUDIT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    with zipfile.ZipFile(OUT/'STAGE02_DENEME.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in build_parts():z.write(OUT/'PRINT'/f'{name}.stl',f'{name}.stl')
        for name in ['ONCE_OKU.md','MONTAJ.png','AUDIT.json']:
            if (OUT/name).exists():z.write(OUT/name,name)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
