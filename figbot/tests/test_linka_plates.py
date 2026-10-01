import csv
import json
import zipfile
from collections import Counter
from itertools import combinations
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
from scripts.package_linka_plates import OUT, SOURCE, Q

def manifest():
    return json.loads((OUT/'TABLA_LISTESI.json').read_text())

def test_inventory_materials_and_individual_packages():
    with (SOURCE/'PRINT_BOM.csv').open() as f: bom={r['id']:r for r in csv.DictReader(f)}
    if manifest()['revision'].startswith(('DEC-084','DEC-085')):
        from scripts.package_tripod_plates import REMOVED,NEW
        bom={k:v for k,v in bom.items() if k not in REMOVED}
        counts=Counter(row[0] for layout in NEW.values() for row in layout)
        bom.update({pid:{'count':n,'material':'PLA'} for pid,n in counts.items()})
    actual=Counter()
    for p in manifest()['plates']:
        with zipfile.ZipFile(OUT/(p['name']+'.zip')) as z:
            assert {p['name']+'.3mf',p['name']+'.stl',p['name']+'.png','BASLAMADAN_ONCE.md'}==set(z.namelist())
        for e in p['instances']:
            actual[e['id']]+=1
            assert bom[e['id']]['material']==p['material']
    assert actual==Counter({pid:int(row['count']) for pid,row in bom.items()})

def test_build_volume_and_spacing():
    for p in manifest()['plates']:
        for e in p['instances']:
            b=np.array(e['bounds'])
            assert np.all(b[0,:2]>=8-1e-5)
            assert np.all(b[1,:2]<=248+1e-5)
            assert abs(b[0,2])<1e-5 and b[1,2]<=256
        for a,b in combinations(p['instances'],2):
            a,b=np.array(a['bounds']),np.array(b['bounds'])
            gap=np.maximum(a[0,:2]-b[1,:2],b[0,:2]-a[1,:2])
            assert np.max(gap)>=8-1e-5,(p['name'],a,b)

def test_stl_preserves_original_geometry_and_volume():
    for p in manifest()['plates']:
        m=trimesh.load_mesh(OUT/p['name']/(p['name']+'.stl'))
        sources=[trimesh.load_mesh(SOURCE/('TUTUCU/PROTOTIP_STL' if e['id'].startswith('RT-') else 'PRINT_STL')/(e['id']+'.stl')) for e in p['instances']]
        assert m.is_watertight and m.is_winding_consistent
        assert np.isclose(m.volume,sum(s.volume for s in sources),rtol=1e-5)
        assert len(m.faces)==sum(len(s.faces) for s in sources)

def test_3mf_preserves_each_mesh_and_local_modifier_settings():
    for p in manifest()['plates']:
        if p['name'].startswith(('07_','08_','09_','10_')):
            continue  # Geometry-only 3MF checked independently in test_tripod_print_plates.
        with zipfile.ZipFile(OUT/p['name']/(p['name']+'.3mf')) as z:
            root=ET.fromstring(z.read('3D/3dmodel.model'))
            cfg=ET.fromstring(z.read('Metadata/Slic3r_PE_model.config'))
        objects=root.find(Q+'resources').findall(Q+'object')
        assert len(objects)==len(p['instances'])==len(root.find(Q+'build'))
        for obj,oc,e in zip(objects,cfg.findall('object'),p['instances']):
            with zipfile.ZipFile(SOURCE/'3MF'/(e['id']+'.3mf')) as z:
                sr=ET.fromstring(z.read('3D/3dmodel.model'))
                sc=ET.fromstring(z.read('Metadata/Slic3r_PE_model.config'))
            verts=lambda r:np.array([[float(v.get(k)) for k in ('x','y','z')] for v in r.iter(Q+'vertex')])
            rotation=np.array(e.get('rotation',np.eye(3)))
            assert np.allclose(rotation.T @ rotation,np.eye(3)) and np.isclose(np.linalg.det(rotation),1)
            assert np.allclose(verts(obj),verts(sr) @ rotation.T+e['translation'])
            assert [t.attrib for t in obj.iter(Q+'triangle')]==[t.attrib for t in sr.iter(Q+'triangle')]
            assert [ET.tostring(v) for v in oc.findall('volume')]==[ET.tostring(v) for v in sc.find('object').findall('volume')]
            settings=lambda c:{m.get('key'):m.get('value') for m in c.findall('metadata') if m.get('key')!='name'}
            assert settings(oc)==settings(sc.find('object'))
