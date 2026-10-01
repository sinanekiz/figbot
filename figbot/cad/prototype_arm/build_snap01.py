"""Isolated, noncommercial circular horn retention/clip fit experiment.

Pocket derived from daGHIZmo EEZYbotARM MK2 gearservo, CC BY-NC 4.0.
Original profile preserved within 0.002 mm simplification tolerance.
"""
from pathlib import Path
import functools, hashlib, json, zipfile
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh
from shapely.geometry import Polygon
from cad.utils import ROOT, export_shape, shape_mesh

OUT=ROOT/'cad/prototype_arm/snap01'
SOURCE=ROOT/'references/servo_horn_trials/originals/EEZYbotARM_MK2/EBAmk2_010_gearservo.STL'
FLOOR=2.4
POCKET_DEPTH=2.5
DECK=FLOOR+POCKET_DEPTH
LID_Z=5.15
LID_T=1.8
STATUS='CLIP AND RETENTION FIT ONLY; CIRCULAR POCKET DOES NOT TRANSMIT TORQUE; NO POWERED OR LOADED USE'

def box(x,y,z,c):
    return cq.Workplane('XY').box(x,y,z).translate(c)

@functools.lru_cache(None)
def profile():
    mesh=trimesh.load_mesh(SOURCE)
    loops=mesh.section(plane_origin=[0,0,3],plane_normal=[0,0,1]).discrete
    polygons=[Polygon(a[:,:2]) for a in loops]
    pocket=min(polygons,key=lambda p:p.area)
    minx,miny,maxx,maxy=pocket.bounds
    centre=np.array([(minx+maxx)/2,(miny+maxy)/2])
    simple=pocket.simplify(.002,preserve_topology=True)
    return np.asarray(simple.exterior.coords)[:-1]-centre,pocket,simple

def pocket_solid(height=POCKET_DEPTH):
    pts,_,_=profile()
    return cq.Workplane('XY').polyline(pts.tolist()).close().extrude(height)

@functools.lru_cache(None)
def build():
    body=box(40,38,DECK,(0,0,DECK/2)).edges('|Z').fillet(1.5)
    body=body.cut(pocket_solid(POCKET_DEPTH+.05).translate((0,0,FLOOR)))
    body=body.cut(cq.Workplane('XY').circle(3.5).extrude(12))
    for side in [-1,1]:
        wall=box(4,38,4.1,(side*18,0,6.95))
        lip=box(6.2,38,1.8,(side*16.9,0,8.1))
        rail=wall.union(lip)
        window=box(6,4.5,2.15,(side*18.5,-5.85,6.025))
        body=body.union(rail.cut(window))
    body=body.union(box(32,1.8,2.3,(0,18.1,6.05)))

    # Flat printed cover. Broad front/rear shoulders engage the rails;
    # flexible side beams only latch against withdrawal.
    lid=box(31.4,34,LID_T,(0,0,LID_T/2)).edges('|Z').fillet(.5)
    for side in [-1,1]:
        slot=box(1.6,19,4,(side*13.3,-.5,1))
        slot=slot.union(cq.Workplane('XY').center(side*13.3,9).circle(.8).extrude(4))
        free=box(4,2,4,(side*14.5,-9,1))
        lid=lid.cut(slot.union(free))
        hook=[(side*x,y) for x,y in [(15.5,-7.8),(17.1,-7.8),(17.1,-6.4),(15.5,-4.0)]]
        lid=lid.union(cq.Workplane('XY').polyline(hook).close().extrude(LID_T))
    lid=lid.cut(cq.Workplane('XY').circle(7).extrude(4))
    return body,lid

def render(body,lid,out=OUT):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(12,6.8),facecolor='#f5f6f7')
    body_view=('SNAP01_01_GOVDE',(0,0,0),'#168bb0')
    lid_view=('SNAP01_02_KAPAK',(0,0,0),'#ee982b')
    scenes=[('1  GOVDE / dairesel referans yuvasi',[body_view]),
            ('2  KAPAK / raylar ve mandallar',[lid_view]),
            ('3  KAPALI / motor tarafindan',[body_view,('SNAP01_02_KAPAK',(0,0,LID_Z),'#ee982b')]),
            ('4  MONTAJ / yandan kaydir',[body_view,('SNAP01_02_KAPAK',(0,-30,LID_Z),'#ee982b')])]
    for i,(title,parts) in enumerate(scenes):
        ax=fig.add_subplot(2,2,i+1,projection='3d')
        arrays=[];all_tri=[];all_colors=[]
        for filename,offset,color in parts:
            mesh=trimesh.load_mesh(out/'PRINT'/f'{filename}.stl')
            v=mesh.vertices+np.array(offset);f=mesh.faces;arrays.append(v)
            from matplotlib.colors import to_rgb
            tri=v[f];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
            light=np.array([-.4,-.6,1.]);light/=np.linalg.norm(light)
            intensity=.45+.50*np.abs(normal@light)
            colors=np.array(to_rgb(color))[None,:]*intensity[:,None]
            all_tri.extend(tri);all_colors.extend(colors)
        ax.add_collection3d(Poly3DCollection(all_tri,facecolors=all_colors,edgecolors='none'))
        v=np.vstack(arrays);mi=v.min(0);ma=v.max(0);c=(ma+mi)/2;r=max(ma-mi)/2+2
        ax.set_xlim(c[0]-r,c[0]+r);ax.set_ylim(c[1]-r,c[1]+r);ax.set_zlim(-2,18)
        ax.set_box_aspect((2*r,2*r,20));ax.view_init(elev=48,azim=-60);ax.set_axis_off();ax.set_title(title,fontsize=11)
    fig.suptitle('SNAP-01 | Klips denemesi - donme kilidi YOK - motoru calistirmayin',fontsize=14)
    fig.tight_layout();fig.savefig(out/'MONTAJ_ONIZLEME.png',dpi=160);plt.close(fig)

def main(out=OUT, part_builder=build, extra_audit=None):
    out.mkdir(parents=True,exist_ok=True)
    body,lid=part_builder()
    parts={'SNAP01_01_GOVDE':body,'SNAP01_02_KAPAK':lid}
    audit={'status':STATUS,'source':str(SOURCE.relative_to(ROOT)),
           'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
           'license':'CC BY-NC 4.0; pocket derived from daGHIZmo EEZYbotARM MK2',
           'source_url':'https://www.thingiverse.com/thing:1454048',
           'source_pocket_depth_mm':2.5,'pocket_type':'circular, nominal diameter20.8mm; NOT a star torque pocket',
           'torque_transfer':'NOT PROVIDED; exact user horn shape needed',
           'lid_underface_gap_to_deck_mm':LID_Z-DECK,
           'hub_opening_mm':14,'front_screw_access_mm':7,'parts':{}}
    if extra_audit: audit.update(extra_audit)
    for name,part in parts.items():
        assert part.val().isValid() and len(part.solids().vals())==1,name
        export_shape(part,out/'PRINT',name,['stl','step'])
        mesh=trimesh.load_mesh(out/'PRINT'/f'{name}.stl')
        assert mesh.is_watertight and mesh.body_count==1
        audit['parts'][name]={'size_mm':mesh.extents.tolist(),'volume_mm3':float(mesh.volume),'watertight':bool(mesh.is_watertight),'bodies':int(mesh.body_count),'minimum_z_mm':float(mesh.bounds[0,2]),'sha256':hashlib.sha256((out/'PRINT'/f'{name}.stl').read_bytes()).hexdigest()}
    assembled_lid=lid.translate((0,0,LID_Z))
    overlap=body.intersect(assembled_lid).val().Volume()
    audit['closed_overlap_mm3']=overlap
    assert overlap<1e-5,overlap
    assembly=cq.Assembly(name='SNAP01_FIT_ONLY')
    assembly.add(body,name='body',color=cq.Color(.08,.55,.69))
    assembly.add(assembled_lid,name='lid',color=cq.Color(.94,.6,.16))
    assembly.save(str(out/'SNAP01_ASSEMBLY.step'))
    scene=trimesh.Scene()
    for name,file in [('body','SNAP01_01_GOVDE'),('lid','SNAP01_02_KAPAK')]:
        m=trimesh.load_mesh(out/'PRINT'/f'{file}.stl')
        if name=='lid':m.apply_translation((0,0,LID_Z))
        m.visual.face_colors=([30,145,180,255] if name=='body' else [240,155,40,255]);scene.add_geometry(m,node_name=name)
    scene.export(out/'SNAP01_ASSEMBLY.glb')
    robot=ET.Element('robot',name='snap01_fixed_fit_review_only')
    for name,file in [('body','SNAP01_01_GOVDE'),('lid','SNAP01_02_KAPAK')]:
        link=ET.SubElement(robot,'link',name=name)
        for tag in ['visual','collision']:
            geom=ET.SubElement(ET.SubElement(link,tag),'geometry')
            ET.SubElement(geom,'mesh',filename=f'PRINT/{file}.stl',scale='0.001 0.001 0.001')
    j=ET.SubElement(robot,'joint',name='lid_fixed_review',type='fixed');ET.SubElement(j,'parent',link='body');ET.SubElement(j,'child',link='lid');ET.SubElement(j,'origin',xyz=f'0 0 {LID_Z/1000}',rpy='0 0 0')
    ET.indent(robot);ET.ElementTree(robot).write(out/'SNAP01_FIXED_REVIEW.urdf',encoding='utf-8',xml_declaration=True)
    render(body,lid,out)
    (out/'AUDIT.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    with zipfile.ZipFile(out/'SNAP01_ILK_BASKI.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in parts:z.write(out/'PRINT'/f'{name}.stl',f'{name}.stl')
        for name in ['ONCE_OKU.md','MONTAJ_ONIZLEME.png','AUDIT.json']:
            if (out/name).exists():z.write(out/name,name)
    print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
