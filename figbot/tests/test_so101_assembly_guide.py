import hashlib
import json
import unittest
from scripts.build_so101_assembly_guide import STEPS, assembly
from scripts.package_so101 import PLATES, source_path
from scripts.project_paths import CAD

class AssemblyGuideTests(unittest.TestCase):
    def test_complete_unique_part_and_motor_mapping(self):
        codes=[c for s in STEPS for c in s[1]]
        expected=[row[0] for rows in list(PLATES.values())[1:] for row in rows]
        self.assertCountEqual(codes,expected)
        self.assertEqual([m for s in STEPS for m in s[2]],list(range(1,7)))
        self.assertEqual(sum(s[3] for s in STEPS),24)
        self.assertEqual(sum(s[4] for s in STEPS),50)

    def test_official_meshes_identified(self):
        self.assertEqual(set(assembly()),{f'P{i:02}' for i in range(1,12)}|{f'M{i}' for i in range(1,7)})

    def test_published_references_match_print_sources(self):
        folder=CAD/'MONTAJ'
        data=json.loads((folder/'KAYNAKLAR.json').read_text(encoding='utf-8'))
        for p in data['parts']:
            self.assertEqual(hashlib.sha256(source_path(p['stem']).read_bytes()).hexdigest(),p['sha256'])
        doc=(folder/'MONTAJ.html').read_text(encoding='utf-8')
        for i in range(1,7):
            self.assertIn(f'id="adim{i}"',doc)
            self.assertTrue((folder/f'ADIM_{i:02}.png').is_file())
        self.assertEqual(doc.count('<video controls preload="none"'),6)
        self.assertIn('kalibrasyonu',doc)

if __name__=='__main__':unittest.main()
