import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

import numpy as np
import trimesh
from scripts.prepare_so101_slicer import WORK, PLATES, MACHINE, settings, placed_mesh
from scripts import publish_so101_slicing as pub
from scripts.audit_so101_slicing import parse


class SlicingTests(unittest.TestCase):
    def test_native_projects_preserve_all_original_meshes(self):
        ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
        for plate,items in PLATES.items():
            with zipfile.ZipFile(WORK/plate/'DILIMLENMIS.3mf') as z:
                cfg=json.loads(z.read('Metadata/project_settings.config'))
                self.assertEqual(cfg['printer_settings_id'],MACHINE)
                self.assertEqual(cfg['nozzle_temperature'],['225'])
                self.assertEqual(cfg['nozzle_diameter'],['0.4'])
                self.assertEqual(cfg['enable_support'],'0' if plate.startswith('00') else '1')
                files=[n for n in z.namelist() if n.startswith('3D/Objects/') and n.endswith('.model')]
                self.assertEqual(len(files),len(items))
                for code,name,x,y in items:
                    path=next(n for n in files if Path(n).name.startswith(code+'_'))
                    root=ET.fromstring(z.read(path))
                    vertices=[[float(v.get(k)) for k in ('x','y','z')] for v in root.findall('.//m:vertex',ns)]
                    faces=[[int(v.get(k)) for k in ('v1','v2','v3')] for v in root.findall('.//m:triangle',ns)]
                    mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
                    original,_=placed_mesh(name,x,y)
                    self.assertEqual(len(mesh.faces),len(original.faces))
                    self.assertAlmostEqual(mesh.volume/original.volume,1,places=5)
                    np.testing.assert_allclose(mesh.extents,original.extents,atol=0.0001)
                    if code=='P10':self.assertTrue(any(p.volume<0 for p in mesh.split()))
                self.assertEqual(z.read('Metadata/plate_1.gcode'),(WORK/plate/'plate_1.gcode').read_bytes())

    def test_actual_toolpaths_machine_temperature_bounds_and_support(self):
        for plate in PLATES:
            folder=WORK/plate
            segments,c,counts=parse(folder/'plate_1.gcode')
            pts=np.array([p for a,b,r in segments for p in (a,b)])
            self.assertTrue(np.all(pts>=0) and np.all(pts<256))
            self.assertFalse(np.any((pts[:,0]>=246)&(pts[:,1]<=20)))
            self.assertEqual(c['nozzle_temperature'],'225')
            self.assertEqual(c['textured_plate_temp'],'60')
            self.assertEqual(c['wall_loops'],'4')
            self.assertEqual(c['sparse_infill_density'],'25%')
            self.assertEqual(c['support_style'],'snug') if not plate.startswith('00') else None
            self.assertEqual((folder/'cli.log').read_text().strip(),'')
            text=(folder/'plate_1.gcode').read_text()
            self.assertIn('CC2_START',text)
            self.assertIn('M83',text)
            self.assertTrue(any(k.startswith('Support') for k in counts)) if not plate.startswith('00') else None

    def test_general_and_arm_preserve_oem_machine_macros(self):
        general,arm=settings(False),settings(True)
        self.assertEqual(general['enable_support'],'0')
        self.assertEqual(general['wall_loops'],'3')
        self.assertEqual(arm['wall_loops'],'4')
        self.assertEqual(general['machine_start_gcode'],arm['machine_start_gcode'])
        self.assertIn('CC2_START',arm['machine_start_gcode'])
        self.assertEqual(arm['enable_pressure_advance'],['0'])

    def test_preservation_rejects_changed_geometry_before_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);current=base/'current';stage=base/'stage'
            current.mkdir();stage.mkdir()
            (stage/'part.stl').write_bytes(b'new')
            (current/'DILIMLEME_KONTROL.json').write_text(json.dumps({'stl_hashes':{'part.stl':hashlib.sha256(b'old').hexdigest()}}))
            with patch.object(pub,'PRINTS',current):
                with self.assertRaisesRegex(RuntimeError,'Geometry changed'):pub.preserve_current(stage)

    def test_archive_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);file=root/'prior.3mf';file.write_bytes(b'prior-profile-and-model')
            archive=root/'old.zip'
            with patch.object(pub,'CURRENT',root),patch.object(pub,'ARCHIVE',archive):pub.archive([file])
            with zipfile.ZipFile(archive) as z:self.assertEqual(z.read(z.namelist()[0]),file.read_bytes())

if __name__=='__main__':unittest.main()
