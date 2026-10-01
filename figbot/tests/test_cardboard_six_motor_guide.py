"""Check delivered CARD-02 PDF, including physical print scale (not strength)."""
import json
import unittest
from pathlib import Path
import pdfplumber
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'output/pdf/FIGBOT_KARTON_6_MOTOR_MONTAJ_KILAVUZU.pdf'
MM=72/25.4

class CardboardGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader=PdfReader(PDF)
        cls.doc=pdfplumber.open(PDF)
        cls.manifest=json.loads((ROOT/'tmp/pdfs/card02/manifest.json').read_text(encoding='utf-8'))

    @classmethod
    def tearDownClass(cls):cls.doc.close()

    def test_all_pages_a4_and_text_inside(self):
        self.assertEqual(len(self.reader.pages),28)
        for p in self.doc.pages:
            self.assertAlmostEqual(p.width/MM,210,places=3)
            self.assertAlmostEqual(p.height/MM,297,places=3)
            self.assertGreater(len(p.extract_text()),250)
            for ch in p.chars:
                self.assertGreaterEqual(ch['x0'],7*MM)
                self.assertLessEqual(ch['x1'],203*MM)
                self.assertGreaterEqual(ch['top'],5*MM)
                self.assertLessEqual(ch['bottom'],292*MM)

    def test_actual_pdf_template_rectangles_at_one_to_one_scale(self):
        for part in self.manifest['templates']:
            if part['kind']!='rectangle':continue
            page=self.doc.pages[part['page']-1]
            matches=[r for r in page.rects if abs(r['x0']/MM-part['x'])<.02
                     and abs(r['y0']/MM-part['y'])<.02
                     and abs(r['width']/MM-part['w'])<.02
                     and abs(r['height']/MM-part['h'])<.02]
            self.assertTrue(matches,part['id'])

    def test_all_nine_template_pages_have_exact_100mm_ruler(self):
        for n in range(5,14):
            p=self.doc.pages[n-1]
            matches=[l for l in p.lines if abs(l['x0']/MM-15)<.02
                     and abs(l['x1']/MM-115)<.02
                     and abs(l['y0']/MM-27)<.02 and abs(l['y1']/MM-27)<.02]
            self.assertTrue(matches,f'page {n}')

    def test_required_parts_counts_and_full_motor_scope(self):
        parts={p['id']:p for p in self.manifest['templates'] if 'id' in p}
        expected={'B01':3,'B02':2,'B03':2,'B04':3,'B05':2,'B06':4,
                  'S01':6,'S02':6,'S03':12,'A01':1,'A02':1,'A03':8,'A04':4,
                  'J01-A':2,'J01-B':2,'J02-A':2,'J02-B':2,'J03':12,
                  'G01':2,'G02':2,'G03':2}
        self.assertEqual({k:p['count'] for k,p in parts.items()},expected)
        text='\n'.join(p.extract_text() for p in self.doc.pages)
        for code in ('M1','M2','M3','M4','M5','M6','PHYSICAL VALIDATION REQUIRED','CARD-02','%100'):
            self.assertIn(code,text)
        self.assertEqual(parts['A01']['folds'],[25,50,75,100])
        self.assertEqual(parts['A02']['folds'],[25,50,75,100])

if __name__=='__main__':unittest.main()
