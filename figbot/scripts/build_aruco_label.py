"""Exact-size paper tool marker; no robot calibration is asserted by this asset."""
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from scripts.project_paths import ROOT, CURRENT, SOFTWARE, ARCHIVE

DICT_NAME = 'DICT_4X4_50'
MARKER_ID = 0
SIDE_MM = 36
MARGIN_MM = 6


def marker_pixels():
    dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, DICT_NAME))
    cells = cv2.aruco.generateImageMarker(dictionary, MARKER_ID, 6, borderBits=1)
    return np.pad(np.repeat(np.repeat(cells, 100, axis=0), 100, axis=1), 100,
                  constant_values=255)


def build(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont('Label', 'C:/Windows/Fonts/arial.ttf'))
    pdfmetrics.registerFont(TTFont('LabelBold', 'C:/Windows/Fonts/arialbd.ttf'))
    c = canvas.Canvas(str(destination/'ARUCO_KISKAC_A4.pdf'), pagesize=(210*mm, 297*mm))
    c.setTitle('FIGBOT - Kıskaç için gerçek ölçekte ArUco etiketi')

    def text(x, y, value, size=11, bold=False):
        c.setFont('LabelBold' if bold else 'Label', size)
        c.drawString(x*mm, y*mm, value)

    text(20, 277, 'FIGBOT / KAMERA TAKİP ETİKETİ', 20, True)
    text(20, 263, 'A4 kağıt · Siyah-beyaz · %100 / Gerçek boyut', 13, True)
    text(20, 252, '“Sayfaya sığdır” kapalı. Çift taraflı baskı yapma.')
    text(20, 242, 'Alttaki kontrol çizgisini cetvelle ölç: tam 50 mm olmalı.')
    # Exact cut square 48 mm, with 6 mm of white on every side of 36 mm marker.
    outer_x, outer_y = 81, 167
    x, y = outer_x+MARGIN_MM, outer_y+MARGIN_MM
    pixels = marker_pixels()[100:700,100:700][::100,::100]
    c.setFillColorRGB(0,0,0)
    for row in range(6):
        for col in range(6):
            if pixels[row,col] == 0:
                c.rect((x+col*6)*mm, (y+(5-row)*6)*mm, 6*mm, 6*mm, stroke=0, fill=1)
    # Crop marks outside white area; no line through quiet zone.
    c.setLineWidth(.3)
    for xx in (outer_x,outer_x+48):
        for yy in (outer_y,outer_y+48):
            sx = -1 if xx==outer_x else 1
            sy = -1 if yy==outer_y else 1
            c.line((xx+sx)*mm,yy*mm,(xx+sx*4)*mm,yy*mm)
            c.line(xx*mm,(yy+sy)*mm,xx*mm,(yy+sy*4)*mm)
    text(70, 153, 'Kesilecek parça: 48 × 48 mm', 12, True)
    text(65, 144, 'Siyah dış kare: 36 × 36 mm · ID 0')
    text(77, 136, 'Sözlük: DICT_4X4_50', 10)
    c.line(80*mm,122*mm,130*mm,122*mm)
    for xx in (80,130): c.line(xx*mm,120*mm,xx*mm,124*mm)
    text(91, 113, '50 mm kontrol', 10)
    lines = [
        '1. Köşe kesim işaretlerinden kes; beyaz kenarları koru.',
        '2. İnce, düz ve sert bir kartona yapıştır. Bükülmesin.',
        '3. Kıskacın arkasındaki sabit parçaya, kameraya dönük tak.',
        '    Açılıp kapanan çeneye takma; hareket yoluna taşmasın.',
        '4. Desenin üstünü parlak bantla kaplama; arkadan sabitle.',
        '5. Yapıştırınca kolun tamamını ve etiketi gösteren fotoğraf gönder.',
    ]
    for i,line in enumerate(lines): text(20,96-i*7,line,11)
    text(20,43,'Bu etiket tek başına otomatik kalibrasyonu etkinleştirmez.',10,True)
    text(20,36,'Kamera desteği ve etiket-kavrama merkezi eşlemesi ayrıca kurulacaktır.',10)
    text(20,23,'Doğrulama: PDF deseni yazılımla okunur; gerçek kamera/baskı testi bekleniyor.',9)
    c.showPage(); c.save()
    cv2.imwrite(str(destination/'ARUCO_KISKAC_ONIZLEME.png'), marker_pixels())
    metadata = dict(dictionary=DICT_NAME, id=MARKER_ID, marker_side_mm=SIDE_MM,
                    white_margin_mm=MARGIN_MM, cut_side_mm=48, border_bits=1,
                    marker_to_grasp_transform='TBD', physical_validation='REQUIRED',
                    note='Pose marker length is 36 mm, not the 48 mm paper cut size.')
    (destination/'ARUCO_KISKAC.json').write_text(json.dumps(metadata,indent=2),encoding='utf8')


def publish():
    stage=ROOT/'tmp/pdfs/aruco_label'
    build(stage)
    payloads={SOFTWARE/'KALIBRASYON'/p.name:p.read_bytes() for p in stage.iterdir()
              if p.name in ('ARUCO_KISKAC_A4.pdf','ARUCO_KISKAC_ONIZLEME.png','ARUCO_KISKAC.json')}
    changed={p:p.read_bytes() for p,data in payloads.items() if p.exists() and p.read_bytes()!=data}
    if changed:
        ARCHIVE.parent.mkdir(exist_ok=True)
        prefix='ARUCO_ONCEKI/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'/'
        with zipfile.ZipFile(ARCHIVE,'a',zipfile.ZIP_DEFLATED) as z:
            for p,data in changed.items():z.writestr(prefix+p.relative_to(CURRENT).as_posix(),data)
        with zipfile.ZipFile(ARCHIVE) as z:
            for p,data in changed.items():
                assert hashlib.sha256(z.read(prefix+p.relative_to(CURRENT).as_posix())).digest()==hashlib.sha256(data).digest()
    for p,data in payloads.items():
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        assert p.read_bytes()==data
    records=[dict(path=p.relative_to(CURRENT).as_posix(),bytes=p.stat().st_size,
                  sha256=hashlib.sha256(p.read_bytes()).hexdigest())
             for p in sorted(CURRENT.rglob('*')) if p.is_file() and p.name!='DOSYA_LISTESI.json' and '__pycache__' not in p.parts]
    (CURRENT/'DOSYA_LISTESI.json').write_text(json.dumps(records,indent=2),encoding='utf8')
    print(str(SOFTWARE/'KALIBRASYON/ARUCO_KISKAC_A4.pdf'))
