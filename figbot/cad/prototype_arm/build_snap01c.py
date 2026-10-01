"""Opposed half covers around a protruding horn hub. Dry fit only.

Circular pocket retains the EEZY-derived CC BY-NC provenance; no torque key.
"""
from functools import lru_cache
from pathlib import Path
import hashlib,json,zipfile
import xml.etree.ElementTree as ET
import cadquery as cq
import numpy as np
import trimesh
from cad.prototype_arm import build_snap01 as prev
from cad.utils import export_shape

OUT=prev.OUT/'REV_C'
LID_Z=prev.LID_Z

@lru_cache(None)
def build():
    body=prev.box(40,38,prev.DECK,(0,0,prev.DECK/2)).edges('|Z').fillet(1.5)
    body=body.cut(prev.pocket_solid(prev.POCKET_DEPTH+.05).translate((0,0,prev.FLOOR)))
    body=body.cut(cq.Workplane('XY').circle(3.5).extrude(12))
    for side in [-1,1]:
        wall=prev.box(4,38,4.1,(side*18,0,6.95))
        lip=prev.box(6.2,38,1.8,(side*16.9,0,8.1))
        rail=wall.union(lip)
        for end in [-1,1]:
            rail=rail.cut(prev.box(6,3.2,2.15,(side*18.5,end*4.2,6.025)))
        # Independent positive stops; each cover stops before the mid-plane.
        rail=rail.union(prev.box(5,1,2.3,(side*13.5,0,6.05)))
        body=body.union(rail)
    # Both ends of the body remain open. No closed hole traverses the hub.
    half=prev.box(31.4,16.2,prev.LID_T,(0,-8.9,prev.LID_T/2)).edges('|Z').fillet(.35)
    for side in [-1,1]:
        groove=prev.box(2.2,11.5,4,(side*13.6,-8.25,1))
        groove=groove.union(cq.Workplane('XY').center(side*13.6,-14).circle(1.1).extrude(4))
        # Free end of flexure, separated from the rigid leading rail shoulder.
        release=prev.box(5,.7,4,(side*15,-2.15,1))
        half=half.cut(groove.union(release))
        hook=[(side*x,y) for x,y in [(15.5,-5.5),(17,-5.5),(17,-4.4),(15.5,-3)]]
        half=half.union(cq.Workplane('XY').polyline(hook).close().extrude(prev.LID_T))
    half=half.cut(cq.Workplane('XY').circle(7).extrude(4))
    return body,half

def pose_halves(half,travel=0):
    # travel>=0 means opened away from centre, along opposite Y directions.
    return [half.translate((0,-travel,LID_Z)),
            half.rotate((0,0,0),(0,0,1),180).translate((0,travel,LID_Z))]

def hub(diameter):
    return cq.Workplane('XY').circle(diameter/2).extrude(12).translate((0,0,prev.DECK))

def render():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(12,8),facecolor='#f4f6f8')
    bm=trimesh.load_mesh(OUT/'PRINT/SNAP01C_GOVDE.stl')
    hm=trimesh.load_mesh(OUT/'PRINT/SNAP01C_YARIM_KAPAK.stl')
    for index,(title,travel) in enumerate([('1  AYNI KAPAKTAN IKI ADET',None),('2  KARSILIKLI IKI GİRİŞ',22),('3  MERKEZE DOGRU KAYDIR',8),('4  IKI KAPAK AYRI KILITLENIR',0)]):
        ax=fig.add_subplot(2,2,index+1,projection='3d');tri=[];colors=[];vs=[]
        meshes=[]
        if travel is None:
            for x,c in [(-20,[.94,.57,.16]),(20,[.56,.39,.75])]:
                m=hm.copy();m.apply_translation((x,0,0));meshes.append((m,c))
        else:
            meshes.append((bm.copy(),[.08,.55,.7]))
            for side,c in [(1,[.94,.57,.16]),(-1,[.56,.39,.75])]:
                m=hm.copy()
                if side==-1:m.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[0,0,1]))
                m.apply_translation((0,-side*travel,LID_Z));meshes.append((m,c))
            # Schematic obstacle envelope only. Not an inferred physical hub size.
            obstacle=trimesh.creation.cylinder(radius=5,height=9,sections=48)
            obstacle.apply_translation((0,0,prev.DECK+4.5));meshes.append((obstacle,[.25,.28,.33]))
        for m,c in meshes:
            vs.append(m.vertices);tri.extend(m.triangles)
            light=np.array([-.4,-.6,1]);light/=np.linalg.norm(light)
            shade=.5+.45*np.abs(m.face_normals@light);colors.extend(np.array(c)[None,:]*shade[:,None])
        ax.add_collection3d(Poly3DCollection(tri,facecolors=colors,edgecolors='none'))
        v=np.vstack(vs);lo=v.min(0);hi=v.max(0);d=hi-lo
        ax.set_xlim(lo[0]-2,hi[0]+2);ax.set_ylim(lo[1]-2,hi[1]+2);ax.set_zlim(-1,16)
        ax.set_box_aspect((d[0]+4,d[1]+4,17));ax.view_init(elev=53,azim=-55);ax.set_axis_off();ax.set_title(title,fontsize=11)
    fig.suptitle('SNAP-01C | Cift kapak | Yalniz kuru montaj denemesi',fontsize=16)
    fig.text(.5,.018,'Gri silindir: temsili baslik cikintisi; olculmus motor parcasi degildir. Donme kilidi henuz yok.',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.04,1,.96));fig.savefig(OUT/'MONTAJ.png',dpi=160);plt.close(fig)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    body,half=build();caps=pose_halves(half)
    audit={'revision':'SNAP-01C opposed half covers','status':'DRY FIT ONLY; NO POSITIVE TORQUE KEY; NO POWERED/LOADED USE',
           'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'license':'CC BY-NC4.0; circular pocket derived from daGHIZmo EEZYbotARM MK2',
           'reference':'https://www.thingiverse.com/thing:1454048',
           'body_changed':True,'old_body_compatible':False,'hub_diameter_test_envelopes_mm':[8,10,12,13.5],
           'nominal_half_gap_mm':1.6,'central_stops_y_mm':[-.5,.5],
           'cover_z_mm':LID_Z,'hub_opening_mm':14,'parts':{},'hub_path_max_overlap_mm3':0}
    for name,shape,qty in [('SNAP01C_GOVDE',body,1),('SNAP01C_YARIM_KAPAK',half,2)]:
        assert shape.val().isValid() and len(shape.solids().vals())==1
        export_shape(shape,OUT/'PRINT',name,['stl','step'])
        m=trimesh.load_mesh(OUT/'PRINT'/f'{name}.stl');assert m.is_watertight and m.body_count==1
        audit['parts'][name]={'qty':qty,'size_mm':m.extents.tolist(),'volume_mm3':float(m.volume),'watertight':bool(m.is_watertight),'sha256':hashlib.sha256((OUT/'PRINT'/f'{name}.stl').read_bytes()).hexdigest()}
    for d in audit['hub_diameter_test_envelopes_mm']:
        for travel in np.linspace(0,38,39):
            for cap in pose_halves(half,float(travel)):
                v=cap.intersect(hub(d)).val().Volume();audit['hub_path_max_overlap_mm3']=max(v,audit['hub_path_max_overlap_mm3']);assert v<1e-6
    parts=[('body',body,'SNAP01C_GOVDE'),('cover_A',caps[0],'SNAP01C_YARIM_KAPAK'),('cover_B',caps[1],'SNAP01C_YARIM_KAPAK')]
    audit['closed_intersections_mm3']=[]
    assembly=cq.Assembly(name='SNAP01C_FIT_ONLY');scene=trimesh.Scene()
    for i,(name,shape,file) in enumerate(parts):
        color=[(.08,.55,.7),(.94,.57,.16),(.56,.39,.75)][i]
        assembly.add(shape,name=name,color=cq.Color(*color))
        m=trimesh.load_mesh(OUT/'PRINT'/f'{file}.stl')
        if i==2:m.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[0,0,1]))
        if i:m.apply_translation((0,0,LID_Z))
        m.visual.face_colors=np.array([*color,1])*255;scene.add_geometry(m,node_name=name)
        for n2,s2,_ in parts[i+1:]:
            v=shape.intersect(s2).val().Volume();audit['closed_intersections_mm3'].append([name,n2,v]);assert v<1e-6
    assembly.save(str(OUT/'SNAP01C_ASSEMBLY.step'));scene.export(OUT/'SNAP01C_ASSEMBLY.glb')
    robot=ET.Element('robot',name='SNAP01C_FIXED_REVIEW')
    for i,(name,shape,file) in enumerate(parts):
        link=ET.SubElement(robot,'link',name=name)
        for tag in ['visual','collision']:
            geom=ET.SubElement(ET.SubElement(link,tag),'geometry');ET.SubElement(geom,'mesh',filename=f'PRINT/{file}.stl',scale='0.001 0.001 0.001')
        if i:
            j=ET.SubElement(robot,'joint',name='fixed_'+name,type='fixed');ET.SubElement(j,'parent',link='body');ET.SubElement(j,'child',link=name)
            ET.SubElement(j,'origin',xyz=f'0 0 {LID_Z/1000}',rpy=f'0 0 {np.pi if i==2 else 0}')
    ET.indent(robot);ET.ElementTree(robot).write(OUT/'SNAP01C_FIXED_REVIEW.urdf',encoding='utf-8',xml_declaration=True)
    render();(OUT/'AUDIT.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    with zipfile.ZipFile(OUT/'SNAP01C_IKI_YANDAN.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in audit['parts']:z.write(OUT/'PRINT'/f'{name}.stl',f'{name}.stl')
        for name in ['ONCE_OKU.md','MONTAJ.png','AUDIT.json']:
            if (OUT/name).exists():z.write(OUT/name,name)
    print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
