from pathlib import Path
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]

def test_supplier_pdf_is_two_a4_pages_and_marks_unresolved_parts():
    pdf=PdfReader(ROOT/'GUNCEL/ALISVERIS/FIGBOT_HIRDAVATCI_ALISVERIS_LISTESI_A4.pdf')
    assert len(pdf.pages)==2
    for page in pdf.pages:
        assert abs(float(page.mediabox.width)-595.276)<.1
        assert abs(float(page.mediabox.height)-841.89)<.1
        text=page.extract_text()
        assert all(t in text for t in ['Gerekli','İstenen','Var','Yok','Verilen'])
    text='\n'.join(p.extract_text() for p in pdf.pages)
    assert 'ISO7379-4-M3-6' not in text and '625 ZZ' in text
    assert 'M3 × 6' in text and 'M2 × 14' in text
    assert 'Metal burç alınmayacak' in text
    assert 'yüklü kullanım onayı verilmemiştir' in text
    assert 'TORNACI' not in text
