"""Render an unpowered physical-reference guide from the vendor mesh geometry."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import numpy as np
from .so101_kinematics import SO101Model, origin_transform, rotation


def reference_angles():
    a=np.arctan2(.028,.11257); b=np.arctan2(.0052,.1349)
    return np.array([0,-a,a+b,-b,0])


def render(urdf, directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    import trimesh
    path=Path(urdf); out=Path(directory);out.mkdir(parents=True,exist_ok=True)
    m=SO101Model(path); q=reference_angles(); frames=m.forward(q)
    root=ET.parse(path).getroot(); links={'base_link':np.eye(4)}
    for j in root.findall('joint'):
        if j.get('name') in frames: links[j.find('child').get('link')]=frames[j.get('name')]
    links['gripper_frame_link']=frames['gripper_frame']
    j=next(x for x in root.findall('joint') if x.get('name')=='gripper')
    turn=np.eye(4);turn[:3,:3]=rotation([0,0,1],.5)
    links[j.find('child').get('link')]=links[j.find('parent').get('link')]@origin_transform(j.find('origin'))@turn
    fig,ax=plt.subplots(figsize=(12,7),dpi=140)
    fig.patch.set_facecolor('#f6f8fa');ax.set_facecolor('#f6f8fa');meshes=[]
    for link in root.findall('link'):
        if link.get('name') not in links: continue
        for visual in link.findall('visual'):
            node=visual.find('geometry/mesh')
            if node is None: continue
            mesh=trimesh.load_mesh(path.parent/node.get('filename'),process=False)
            mesh.apply_transform(links[link.get('name')]@origin_transform(visual.find('origin')))
            tris=mesh.triangles*1000
            color='#51626c' if visual.find('material').get('name')=='sts3215' else '#72aaa6'
            meshes.append((tris[:,:,1].mean(),tris,color))
    for _,triangles,color in sorted(meshes,key=lambda x:-x[0]):
        order=np.argsort(-triangles[:,:,1].mean(axis=1))
        ax.add_collection(PolyCollection(triangles[order][:,:,[0,2]],facecolors=color,edgecolors='none'))
    p={k:t[:3,3]*1000 for k,t in frames.items()}
    labels=[('shoulder_lift','OMUZ MERKEZİ',(-50,-33)),('elbow_flex','DİRSEK MERKEZİ',(-53,42)),('wrist_flex','BİLEK MERKEZİ',(-9,42))]
    for k,label,offset in labels:
        v=p[k];ax.scatter([v[0]],[v[2]],s=55,color='#cf5639',zorder=15)
        ax.annotate(label,(v[0],v[2]),xytext=offset,textcoords='offset points',fontsize=10,fontweight='bold',arrowprops={'arrowstyle':'-','color':'#a64430'},zorder=20)
    u,v,w=p['shoulder_lift'],p['elbow_flex'],p['wrist_flex']
    ax.plot([u[0],v[0],w[0]],[u[2],v[2],w[2]],'--',color='#cf5639',lw=2,zorder=14)
    ax.text(18,173,'İki merkez\nüst üste',fontsize=11,ha='center',color='#9c3b23')
    ax.text(145,294,'İki merkez aynı yükseklikte',fontsize=11,ha='center',color='#9c3b23')
    ax.annotate('+X / ÖN',xy=(380,28),xytext=(275,28),fontsize=12,fontweight='bold',arrowprops={'arrowstyle':'->','lw':2},va='center')
    ax.axhline(0,color='#858f96',lw=1)
    ax.set_xlim(-20,420);ax.set_ylim(-12,307);ax.set_aspect('equal');ax.axis('off')
    fig.suptitle('SO-101 • Bir kez alınacak referans duruş',fontsize=19,fontweight='bold',y=.98)
    fig.text(.5,.03,'Yandan görünüş. Hizalamayı plastik kenarlardan değil, eklem merkezlerinden yap.\nKolu destekleyerek ve motor torku kapalıyken elle konumlandır; direnç varsa zorlama.',ha='center',fontsize=11)
    fig.tight_layout(rect=[0,.07,1,.94]);fig.savefig(out/'REFERANS_DURUS.png',facecolor=fig.get_facecolor());plt.close(fig)
    (out/'REFERANS_DURUS.json').write_text(json.dumps(dict(urdf_sha256=m.sha256,
        reference_joint_radians=q.tolist(), reference_joint_degrees=np.rad2deg(q).tolist(),
        reference_raw_encoder=None, motor_direction_signs=None,
        user_origin_to_urdf=None, physical_reference_status='AWAITING_PHYSICAL_POSITION',
        motion_authorized=False),indent=2),encoding='utf8')
