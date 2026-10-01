"""Recover the native display mesh; never use the invalid STEP conversion.

Input decode.json is produced locally with:
cadmpeg dump MG90servo_gear.SLDPRT -o decode.json
This performs no downloads and never executes source-file content.
"""
import hashlib
import json
import numpy as np
import trimesh
from cad.utils import ROOT

REF=ROOT/'references/servo_horn_trials/originals/MG90_USER_20260907'
EXPECTED='85f05176c11f71af6b85e8cc53521cc6ddb7e375404e59b1347a8fb39e0e5aa7'

def extract():
    assert hashlib.sha256((REF/'MG90servo_gear.SLDPRT').read_bytes()).hexdigest()==EXPECTED
    data=json.loads((REF/'decode.json').read_text(encoding='utf-8'))
    assert data['units']['length']=='millimeter'
    meshes=[]
    for t in data['model']['tessellations']:
        vertices=np.array([[v[k] for k in ('x','y','z')] for v in t['vertices']])
        meshes.append(trimesh.Trimesh(vertices,t['triangles']))
    m=trimesh.util.concatenate(meshes)
    m.merge_vertices(digits_vertex=5)
    m.update_faces(m.unique_faces());m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices();m.fix_normals()
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
    assert np.allclose(m.extents,[35,4.85,16.3],atol=.001)
    assert 466<m.volume<469
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0]))
    m.export(REF/'MG90_native_display.stl')
    # Load exported precision, then rotate: identical to original build workflow.
    canonical=trimesh.load_mesh(REF/'MG90_native_display.stl')
    canonical.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,0,1]))
    canonical.export(REF/'MG90_canonical.stl')
    return canonical

if __name__=='__main__':
    mesh=extract()
    print({'size_mm':mesh.extents.tolist(),'volume_mm3':float(mesh.volume),'watertight':mesh.is_watertight})
