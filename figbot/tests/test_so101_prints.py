import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import trimesh
from scripts.package_so101 import (PLATES, STAGE, ROOT, placed_mesh, source_path,
    check_plate, verify_sources, write_3mf)


class So101PrintTests(unittest.TestCase):
    def test_upstream_sources_are_pinned_and_unchanged(self):
        self.assertGreater(len(verify_sources()['files']), 20)

    def test_follower_is_complete_without_leader_or_duplicate_parts(self):
        names=[name for plate,items in PLATES.items() if not plate.startswith('00')
               for _,name,_,_ in items]
        self.assertEqual(len(names),11)
        self.assertEqual(len(set(names)),11)
        self.assertNotIn('Wrist_Roll_SO101',names)
        self.assertIn('Wrist_Roll_Follower_SO101',names)
        self.assertIn('Moving_Jaw_SO101',names)

    def test_all_parts_keep_source_geometry_and_fit_without_overlap(self):
        for plate,items in PLATES.items():
            meshes={}
            for code,name,x,y in items:
                source=trimesh.load_mesh(source_path(name))
                mesh,tf=placed_mesh(name,x,y)
                recovered=trimesh.transform_points(mesh.vertices,np.linalg.inv(tf))
                np.testing.assert_allclose(recovered,source.vertices,atol=1e-6)
                np.testing.assert_array_equal(mesh.faces,source.faces)
                self.assertAlmostEqual(mesh.volume/source.volume,1,places=6)
                meshes[code]=mesh
            check_plate(meshes)

    def test_bed_and_overlap_failures_are_rejected(self):
        a,_=placed_mesh('Base_SO101',12,12)
        with self.assertRaises(AssertionError):check_plate({'a':a,'overlap':a.copy()})
        a.apply_translation([200,0,0])
        with self.assertRaises(AssertionError):check_plate({'outside':a})

    def test_3mf_roundtrip_preserves_cavity_volume_units_and_separate_objects(self):
        a,_=placed_mesh('Moving_Jaw_SO101',12,12)
        b,_=placed_mesh('WaveShare_Mounting_Plate_SO101',136,12)
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'plate.3mf';write_3mf(file,{'jaw':a,'board':b})
            with zipfile.ZipFile(file) as z:
                root=ET.fromstring(z.read('3D/3dmodel.model'))
            ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
            self.assertEqual(root.get('unit'),'millimeter')
            objects=root.findall('m:resources/m:object',ns)
            self.assertEqual(len(objects),2)
            for obj,original in zip(objects,[a,b]):
                vertices=[[float(v.get(k)) for k in ['x','y','z']] for v in obj.findall('m:mesh/m:vertices/m:vertex',ns)]
                faces=[[int(v.get(k)) for k in ['v1','v2','v3']] for v in obj.findall('m:mesh/m:triangles/m:triangle',ns)]
                rebuilt=trimesh.Trimesh(vertices=vertices,faces=faces)
                self.assertTrue(rebuilt.is_watertight)
                self.assertAlmostEqual(rebuilt.volume/original.volume,1,places=6)
            self.assertTrue(any(part.volume<0 for part in a.split()))

    def test_staged_delivery_has_resolvable_urdf_and_consistent_zip_payloads(self):
        self.assertTrue((STAGE/'CAD/VALIDATION.json').is_file(),'Run package_so101 before testing staged output')
        audit=json.loads((STAGE/'BASKI/TABLA_LISTESI.json').read_text(encoding='utf-8'))
        self.assertEqual(len(audit),13)
        for plate,items in PLATES.items():
            out=STAGE/'BASKI'/plate
            with zipfile.ZipFile(STAGE/'BASKI'/(plate+'.zip')) as z:
                self.assertEqual(z.read(plate+'/TABLA.3mf'),(out/'TABLA.3mf').read_bytes())
            mesh=trimesh.load_mesh(out/'TABLA.stl')
            expected=sum(r['volume_mm3'] for r in audit if r['plate']==plate)
            self.assertAlmostEqual(mesh.volume/expected,1,places=5)
        urdf=STAGE/'CAD/URDF/so101_new_calib.urdf'
        for element in ET.parse(urdf).getroot().iter('mesh'):
            self.assertTrue((urdf.parent/element.get('filename')).is_file())


if __name__=='__main__':unittest.main()
