"""Explicit removable print scaffolds; functional AERO V4 solids unchanged.
Units mm. Geometry-only manufacturing assemblies, NOT printer G-code.
"""
from pathlib import Path
import json,hashlib,zipfile
from dataclasses import dataclass
from PIL import Image,ImageDraw,ImageFont
import numpy as np
import trimesh
import cadquery as cq
from shapely.geometry import Polygon,box,GeometryCollection
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import affinity,set_precision
from cad.utils import ROOT,shape_mesh
from cad.prototype_arm import build_aero_v4 as a
from cad.prototype_arm import export_aero_v4 as ex
OUT=ROOT/'cad/prototype_arm/aero_v4_supported'
PITCH=2.4
WALL=.8
TIP=.42
GAP=0.0
SIDE_GAP=.3
NECK=.6
# Explicit geometric bridge exception: only small circular-hole crown spans.
SMALL_BRIDGE=4.5
GROUPS=[('02_DESTEKLI_TABAN',['A4-01-BASE']),
 ('03_DESTEKLI_OMUZ',['A4-02-SHOULDER-DECK','A4-14-SHOULDER-TOWER-R','A4-15-SHOULDER-TOWER-L']),
 ('04_DESTEKLI_UST_KOL',['A4-04-UPPER-CARRIER','A4-06-ELBOW-YOKE']),
 ('05_DESTEKLI_ON_KOL',['A4-07-FORE-CARRIER','A4-09-WRIST-YOKE']),
 ('06_DESTEKLI_TUTUCU',['A4-10-PALM-FIXED-FINGER','A4-11-MOVING-FINGER'])]

def polygons(g):
 if g.is_empty:return []
 if isinstance(g,Polygon):return [g]
 return [p for s in g.geoms for p in polygons(s)]

def section(m,y):
 s=m.section(plane_origin=[0,y,0],plane_normal=[0,1,0])
 if s is None:return GeometryCollection()
 result=GeometryCollection()
 for loop in s.discrete:
  p=Polygon(loop[:,[0,2]]).buffer(0)
  if p.area>1e-7:result=result.symmetric_difference(p)
 return result.buffer(0)

def padding(g,x,z):
 if g.is_empty:return g
 if z==0:return unary_union([affinity.translate(g,xoff=d) for d in [-x,0,x]])
 return affinity.scale(affinity.scale(g,xfact=1/x,yfact=1/z,origin=(0,0)).buffer(1,quad_segs=3),xfact=x,yfact=z,origin=(0,0))

def shadow(poly):
 shapes=[]
 for p in polygons(poly):
  p=orient(p,1)
  for ring in [p.exterior,*p.interiors]:
   pts=np.array(ring.coords)
   for (x0,z0),(x1,z1) in zip(pts[:-1],pts[1:]):
    dx=x1-x0
    # CCW exterior: edge left to right has its outward normal down.
    if dx>1e-5 and abs(z1-z0)<=dx*1.05 and max(z0,z1)>.3:
     q=Polygon([(x0,0),(x1,0),(x1,z1),(x0,z0)]).buffer(0)
     if q.area>1e-6:shapes.append(q)
 return unary_union(shapes)

def extrude(g,y,width):
 out=[]
 for p in polygons(set_precision(g,.001).buffer(0).simplify(.0001,preserve_topology=True)):
  if p.area<.025:continue
  mesh=trimesh.creation.extrude_polygon(p,height=width,engine='triangle',triangle_args='p')
  v=mesh.vertices.copy();mesh.vertices=np.column_stack((v[:,0],y+width/2-v[:,2],v[:,1]))
  mesh.merge_vertices(digits_vertex=7);mesh.remove_unreferenced_vertices();mesh.fix_normals()
  if not mesh.is_volume:
   raise ValueError(f"Bad extrusion area={p.area} valid={p.is_valid} closed={mesh.is_watertight} volume={mesh.volume}")
  out.append(mesh)
 return out

def supports(m,extra_rows=()):
 fins=[];rows=[]
 ymax=m.bounds[1,1]
 for y in sorted(set([*np.arange(.6,ymax-.1,PITCH),*extra_rows])):
  secs=[section(m,float(y+d)) for d in [-WALL/2,0,WALL/2]]
  centre=secs[1]
  solid=unary_union(secs)
  sh=shadow(centre)
  free=sh.difference(padding(solid,SIDE_GAP,GAP)).intersection(box(-1,0,m.bounds[1,0]+1,m.bounds[1,2]+1))
  # Drop short tiny circular-hole crowns, which are bridged across <=4.5mm.
  free=unary_union([p for p in polygons(free) if p.area>1 and not (p.bounds[2]-p.bounds[0]<SMALL_BRIDGE and p.bounds[3]-p.bounds[1]<4.5)])
  # Subdivide into <=8mm peelable strips; no closed cage is generated.
  for x in np.arange(0,m.bounds[1,0],8.4):
   region=free.intersection(box(x,0,x+8,m.bounds[1,2]+1))
   if region.area<1:continue
   bulk=region.difference(padding(solid,SIDE_GAP,GAP+NECK))
   chunks=extrude(bulk,y,WALL)+extrude(region,y,TIP)
   if not chunks:continue
   fin=trimesh.boolean.union(chunks,engine='manifold') if len(chunks)>1 else chunks[0]
   for f in fin.split():
    if f.volume<.15:continue
    assert f.is_watertight
    fins.append(f)
   rows.append({'y':float(y),'x_start':float(x),'roof_area':float(region.area)})
 # Shallow orthogonal interface ribs catch roof extrusion in either direction.
 # They bridge only one main-fin pitch, rather than the entire original opening.
 rotated=m.copy();v=m.vertices
 rotated.vertices=np.column_stack((v[:,1],m.bounds[1,0]-v[:,0],v[:,2]))
 for y in np.arange(.6,rotated.bounds[1,1]-.1,PITCH):
  centre=section(rotated,float(y))
  solid=unary_union([section(rotated,float(y+d)) for d in [-TIP/2,0,TIP/2]])
  sh=shadow(centre)
  strip=sh.difference(affinity.translate(sh,yoff=-NECK))
  free=strip.difference(padding(solid,SIDE_GAP,GAP))
  for x in np.arange(0,rotated.bounds[1,0],8.4):
   region=free.intersection(box(x,0,x+8,rotated.bounds[1,2]+1))
   for f in extrude(region,y,TIP):
    if f.volume<.05:continue
    v=f.vertices.copy();f.vertices=np.column_stack((m.bounds[1,0]-v[:,1],v[:,0],v[:,2]));f.fix_normals()
    fins.append(f)
 return fins,rows

def cq_from_mesh(m):
 # Support STEP uses explicit triangular BRep shells; exported geometry is exact to mesh.
 faces=[]
 for tri in m.triangles:
  wire=cq.Wire.makePolygon([cq.Vector(*v) for v in tri],close=True)
  faces.append(cq.Face.makeFromWires(wire))
 return cq.Solid.makeSolid(cq.Shell.makeShell(faces))

def build_part(pid,s):
 m=trimesh.Trimesh(*shape_mesh(s));m.fix_normals()
 fins,rows=supports(m,extra_rows=[14.] if pid=='A4-02-SHOULDER-DECK' else [])
 # No hidden model cutting or dimensional edits allowed.
 allsupport=trimesh.util.concatenate(fins) if fins else None
 overlap=0
 if fins:
  collision=trimesh.boolean.intersection([m,allsupport],engine='manifold')
  overlap=float(abs(collision.volume))
  assert overlap<.005,(pid,overlap)
 combined=trimesh.boolean.union([m,*fins],engine='manifold') if fins else m.copy()
 # STL welds coincident edge-only contacts. Add tiny sacrificial finite-area ties
 # at any detected singular support contact, then re-union and re-open the STL.
 import io
 ties=[]
 for iteration in range(3):
  reopened=trimesh.load_mesh(io.BytesIO(combined.export(file_type='stl')),file_type='stl')
  if reopened.is_watertight and reopened.is_winding_consistent:break
  counts=np.bincount(reopened.edges_unique_inverse)
  assert not np.any(counts==1), 'Unexpected open surface, not an edge-only contact'
  edges=reopened.edges_unique[counts>2]
  assert len(edges)<30,'Too many singular contacts'
  patches=[]
  for edge in edges:
   pts=reopened.vertices[edge];size=np.ptp(pts,axis=0)+.15
   patch=trimesh.creation.box(extents=size,transform=trimesh.transformations.translation_matrix(pts.mean(0)))
   patches.append(patch)
  ties.extend(patches);fins.extend(patches)
  combined=trimesh.boolean.union([combined,*patches],engine='manifold')
 assert reopened.is_watertight and reopened.is_winding_consistent
 assert combined.is_watertight and combined.is_volume
 tie_volume=sum(t.volume for t in ties)
 overlap=float(abs(trimesh.boolean.intersection([m,trimesh.util.concatenate(fins)],engine='manifold').volume)) if fins else 0
 assert overlap<tie_volume+.005
 report={'part':pid,'contact_tie_count':len(ties),'contact_tie_volume_mm3':tie_volume,'support_pieces':len(fins),'support_volume_mm3':sum(f.volume for f in fins),
  'functional_volume_mm3':float(m.volume),'support_model_overlap_mm3':overlap,'bounds_mm':combined.bounds.tolist(),
  'original_sha256':hashlib.sha256(m.export(file_type='stl')).hexdigest(),'support_fin_rows':rows,
  'physical_breakaway_force':'UNVERIFIED; coupon test required'}
 return m,fins,combined,report

def main():
 OUT.mkdir(exist_ok=True,parents=True);(OUT/'TEKIL').mkdir(exist_ok=True)
 reports=[];built={}
 for _,pids in GROUPS:
  for pid in pids:
   s=ex.oriented(pid,a.PARTS[pid][0]())
   m,fins,combined,r=build_part(pid,s);built[pid]=(s,m,fins,combined);reports.append(r)
   combined.export(OUT/'TEKIL'/f'{pid}_DESTEKLI.stl')
   ex.write_3mf([(pid+'_WITH_BREAKAWAY',combined)],OUT/'TEKIL'/f'{pid}_DESTEKLI.3mf')
   print(pid,'support pieces',len(fins),'overlap',r['support_model_overlap_mm3'],flush=True)
 (OUT/'SUPPORT_AUDIT.json').write_text(json.dumps(reports,indent=2))
 return built,reports

def render_meshes(meshes,path,title,az=-60,el=23,w=1400,h=940):
    az,el=np.radians([az,el])
    right=np.array([-np.sin(az),np.cos(az),0])
    up=np.array([-np.sin(el)*np.cos(az),-np.sin(el)*np.sin(az),np.cos(el)])
    look=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    matrix=np.stack([right,up,look],axis=1)
    p=np.vstack([m.vertices@matrix for m,c in meshes]);lo=p.min(0);hi=p.max(0);center=(lo+hi)/2
    scale=min((w-100)/(hi[0]-lo[0]),(h-165)/(hi[1]-lo[1]))
    pixels=np.full((h,w,3),248,dtype=np.uint8);depth=np.full((h,w),-np.inf)
    light=np.array([-.4,-.5,1]);light/=np.linalg.norm(light)
    for m,color in meshes:
        shades=.58+.4*np.abs(m.face_normals@light)
        coords=m.vertices@matrix
        coords[:,0]=(coords[:,0]-center[0])*scale+w/2
        coords[:,1]=h/2+15-(coords[:,1]-center[1])*scale
        for k,face in enumerate(m.faces):
            t=coords[face];aa,b,c=t
            x0=max(0,int(np.floor(t[:,0].min())));x1=min(w-1,int(np.ceil(t[:,0].max())))
            y0=max(0,int(np.floor(t[:,1].min())));y1=min(h-1,int(np.ceil(t[:,1].max())))
            det=(b[1]-c[1])*(aa[0]-c[0])+(c[0]-b[0])*(aa[1]-c[1])
            if abs(det)<1e-9 or x1<x0 or y1<y0:continue
            yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
            u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/det
            v=((c[1]-aa[1])*(xx-c[0])+(aa[0]-c[0])*(yy-c[1]))/det
            q=1-u-v;z=u*aa[2]+v*b[2]+q*c[2]
            target=depth[y0:y1+1,x0:x1+1];mask=(u>=-1e-7)&(v>=-1e-7)&(q>=-1e-7)&(z>target)
            target[mask]=z[mask];pixels[y0:y1+1,x0:x1+1][mask]=np.array(color)*shades[k]*255
    im=Image.fromarray(pixels);d=ImageDraw.Draw(im)
    font=lambda n:ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
    d.text((w/2,25),title,font=font(28),fill='#16323d',anchor='mt')
    d.text((w/2,h-48),'Mavi: korunacak parça  |  Turuncu: baskıdan sonra sökülecek destek',font=font(20),fill='#16323d',anchor='mt')
    d.text((w/2,h-23),'Destek ayrılması fiziksel deneme gerektirir — tek malzeme ile basılabilir.',font=font(16),fill='#5a6470',anchor='mt')
    path.parent.mkdir(parents=True,exist_ok=True);im.save(path)

def finish(built,reports):
 import xml.etree.ElementTree as ET
 import csv
 tables=OUT/'TABLALAR';tables.mkdir(exist_ok=True)
 rows=[]
 for name,pids in GROUPS:
  entries=[];x=y=10.;rowheight=0
  for pid in pids:
   m=built[pid][3].copy();dx,dy,dz=m.extents
   if x+dx>246:x=10;y+=rowheight+8;rowheight=0
   assert y+dy<=246 and dz<246
   m.apply_translation([x,y,0]);entries.append((pid+'_SUPPORT_KEEP_TOGETHER',m));x+=dx+8;rowheight=max(rowheight,dy)
  ex.write_3mf(entries,tables/(name+'.3mf'))
  trimesh.util.concatenate([m for _,m in entries]).export(tables/(name+'.stl'))
  rows.append({'file':name+'.3mf','functional_parts':len(entries),'parts':pids})
 # A small nonfunctional test uses exactly the same support interface algorithm.
 coupon=cq.Workplane('XY').box(28,16,2,centered=(False,False,False))
 for x in [0,25]:coupon=coupon.union(cq.Workplane('XY').box(3,16,16,centered=(False,False,False)).translate((x,0,0)))
 coupon=coupon.union(cq.Workplane('XY').box(28,16,2,centered=(False,False,False)).translate((0,0,16)))
 m,fins,combined,r=build_part('SUPPORT_COUPON_NOT_ARM_PART',coupon)
 combined.apply_translation([15,15,0])
 ex.write_3mf([('SUPPORT_COUPON_KEEP_TOGETHER',combined)],tables/'00_ONCE_DESTEK_DENEMESI.3mf')
 combined.export(tables/'00_ONCE_DESTEK_DENEMESI.stl')
 (OUT/'COUPON_AUDIT.json').write_text(json.dumps(r,indent=2))
 render_meshes([(m,a.BLUE),(trimesh.util.concatenate(fins),a.GOLD)],OUT/'00_DENEME.png','Önce bu küçük parçayı basın — destek ayrılma denemesi',el=30,w=1000,h=750)
 for pid in ['A4-01-BASE','A4-02-SHOULDER-DECK','A4-06-ELBOW-YOKE','A4-10-PALM-FIXED-FINGER']:
  sh,m,fins,combined=built[pid]
  render_meshes([(m,a.BLUE),(trimesh.util.concatenate(fins),a.GOLD)],OUT/(pid+'_DESTEK.png'),pid+' — sökülecek destekler turuncu',el=25)
 # Manufacturing scene + fixed URDF include scaffolds; not robot moving mass.
 scene=trimesh.Scene();robot=ET.Element('robot',name='PRINT_SCAFFOLDS_FIXED_REVIEW_NOT_ROBOT')
 ET.SubElement(robot,'link',name='print_bed')
 for idx,(pid,(s,m,fins,combined)) in enumerate(built.items()):
  t=np.eye(4);t[:3,3]=[(idx%3)*250,(idx//3)*200,0]
  for name,mesh,color in [('PART',m,a.BLUE),('REMOVE_SUPPORT',trimesh.util.concatenate(fins),a.GOLD)]:
   mesh=mesh.copy();mesh.visual.face_colors=np.array([*color,1])*255;scene.add_geometry(mesh,node_name=pid+'_'+name,transform=t)
  link=ET.SubElement(robot,'link',name=pid)
  for tag in ['visual','collision']:
   g=ET.SubElement(ET.SubElement(link,tag),'geometry');ET.SubElement(g,'mesh',filename='TEKIL/'+pid+'_DESTEKLI.stl',scale='.001 .001 .001')
  j=ET.SubElement(robot,'joint',name=pid+'_fixed',type='fixed');ET.SubElement(j,'parent',link='print_bed');ET.SubElement(j,'child',link=pid)
  ET.SubElement(j,'origin',xyz=f'{t[0,3]/1000} {t[1,3]/1000} 0',rpy='0 0 0')
 scene.export(OUT/'DESTEKLI_BASKI_MONTAJI.glb');ET.indent(robot);ET.ElementTree(robot).write(OUT/'DESTEKLI_BASKI_INCELEME.urdf',encoding='utf-8',xml_declaration=True)
 (OUT/'TABLA_LISTESI.json').write_text(json.dumps(rows,indent=2))
 (OUT/'MALZEME_TAHMINI.json').write_text(json.dumps({'support_solid_PLA_g':sum(r['support_volume_mm3'] for r in reports)*.00124,
  'functional_solid_PLA_g':sum(r['functional_volume_mm3'] for r in reports)*.00124,'density_assumption_g_mm3':.00124,
  'filament_price_TRY_kg':None,'cost_TRY':None,'actual_slicer_infill_and_waste':'TBD','BOM_unchanged':True},indent=2))
 print('plates and renders done',flush=True)

if __name__=='__main__':finish(*main())

