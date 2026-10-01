"""A4 supplier checklist derived from the L1.1 purchasing BOM; no BOM changes."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT=Path(__file__).resolve().parents[1]
from scripts.project_paths import SHOPPING
OUT=SHOPPING/'FIGBOT_HIRDAVATCI_ALISVERIS_LISTESI_A4.pdf'
DATA=json.loads((SHOPPING/'VERI/MALZEMELER.json').read_text(encoding='utf-8'))
ROWS={r['code']:r for r in DATA['rows']}
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialB','C:/Windows/Fonts/arialbd.ttf'))
STYLE=ParagraphStyle('cell',fontName='Arial',fontSize=9.2,leading=11.8)
W,H=A4;M=32;CW=[22,262,42,49,30,30,W-2*M-435]
used=[]

def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(OUT),pagesize=A4)
    c.setTitle('FIGBOT - Hırdavatçı için gruplu alışveriş listesi - DEC-086')
    def text(x,y,s,size=10,bold=False):
        c.setFont('ArialB' if bold else 'Arial',size);c.drawString(x,y,s)
    def page(n,title):
        text(M,H-38,'FIGBOT  /  ALINACAK MALZEMELER',16,True)
        text(M,H-57,title,11,True)
        text(M,H-75,'1 kol takımı • DEC-086 • 17.09.2026 • Tüm ölçüler mm',9)
        text(M,H-92,'Gerekli: montaj adedi. İstenen: yedek dahil. Var/Yok satıcı doldurur.',9)
        text(M,H-111,'Firma: ........................................   Tarih: ....................   Tel: ........................',9)
        c.setLineWidth(.5);c.line(M,39,W-M,39)
        text(M,25,'Ölçü/boy farklıysa eşdeğer diye vermeyiniz; farkı not ediniz. Vida boyu baş altından.',8)
        text(W-74,12,f'{n} / 2',8)
        return H-124
    def group(y,title):
        c.setFillGray(.88);c.rect(M,y-22,W-2*M,22,fill=1,stroke=0);c.setFillGray(0)
        text(M+6,y-15,title,10,True)
        y-=22
        x=M
        for width,label in zip(CW,['No','Malzeme / tam ölçü','Gerekli','İstenen','Var','Yok','Verilen']):
            c.setFillGray(.96);c.rect(x,y-22,width,22,fill=1,stroke=0);c.setFillGray(0)
            text(x+4,y-15,label,8,True);x+=width
        return y-22
    def row(y,code,description,need=None,buy=None):
        r=ROWS[code];used.append(code)
        need=str(r['required']) if need is None else str(need)
        buy=str(r['buy_quantity']) if buy is None else str(buy)
        p=Paragraph(description,STYLE);_,ph=p.wrap(CW[1]-10,200)
        height=max(27,ph+11)
        assert y-height>47,(code,y,height)
        x=M
        c.setStrokeGray(.65);c.setLineWidth(.35)
        for i,width in enumerate(CW):
            c.rect(x,y-height,width,height,fill=0,stroke=1)
            if i==0:text(x+4,y-height/2-3,str(len(used)),8)
            elif i==1:p.drawOn(c,x+5,y-(height+ph)/2)
            elif i in (2,3):
                c.setFont('ArialB' if i==3 else 'Arial',9);c.drawCentredString(x+width/2,y-height/2-3,need if i==2 else buy)
            elif i in (4,5):c.rect(x+(width-9)/2,y-height/2-4.5,9,9,fill=0,stroke=1)
            elif i==6:text(x+5,y-height/2-3,'.........',9)
            x+=width
        c.setStrokeGray(0)
        return y-height

    y=page(1,'CIVATACI / HIRDAVATÇI - standart bağlantı malzemeleri')
    y=group(y,'A. Cıvatalar - metrik diş, havşa başlı OLMAYACAK')
    for code,desc in [
        ('S36','<b>M3 × 6</b> silindirik başlı imbus cıvata, DIN 912'),
        ('S38','<b>M3 × 8</b> silindirik başlı imbus cıvata, DIN 912'),
        ('S310','<b>M3 × 10</b> silindirik başlı imbus cıvata, DIN 912'),
        ('S320','<b>M3 × 20</b> silindirik başlı imbus cıvata, DIN 912'),
        ('S26','<b>M2 × 6</b> yıldız silindir başlı vida, DIN 7985'),
        ('S28','<b>M2 × 8</b> yıldız silindir başlı vida, DIN 7985'),
        ('FINGER_SCREW','<b>M2 × 14</b> yıldız silindir başlı vida, DIN 7985')]:y=row(y,code,desc)
    y=group(y-9,'B. Düz pullar ve kilit somun - pul kalınlığı önemli')
    for code,desc in [
        ('W2','<b>M2 düz pul:</b> iç Ø2,2 / dış Ø5 / kalınlık 0,3'),
        ('W3','<b>M3 düz pul:</b> iç Ø3,2 / dış Ø7 / kalınlık 0,5'),
        ('W5','<b>M5 düz pul:</b> iç Ø5,3 / dış Ø10 / kalınlık 1'),
        ('N5','<b>M5 fiberli kilit somun</b>, DIN 985, anahtar ağzı 8')]:y=row(y,code,desc)
    y=group(y-9,'C. Pirinç ısı inserti - plastik içine havya ile gömülen tırtıllı somun')
    for code,desc in [
        ('I35','<b>İç diş M3 / dış Ø4,5 / boy 5</b> - pirinç insert'),
        ('I34','<b>İç diş M3 / dış Ø4,5 / boy 4</b> - pirinç insert'),
        ('I24','<b>İç diş M2 / dış Ø3,2 / boy 4</b> - pirinç insert'),
        ('I23','<b>İç diş M2 / dış Ø3,2 / boy 3</b> - pirinç insert')]:y=row(y,code,desc)
    text(M,y-16,'Insertler perçin somun değildir. Dış çap ve boy değişirse ayrıca teyit gerekir.',8.5)
    c.showPage()

    y=page(2,'ÖZEL CIVATA / RULMANCI / HOBİ - hazır malzemeler')
    y=group(y,'D. Özel cıvatalar - aşağıdaki ölçüler mutlaka kontrol edilecek')
    y=row(y,'ELBOW_AXLE','<b>M5 × 70 KISMİ DİŞLİ imbus cıvata</b>, ISO 4762 / DIN 912.<br/>Nominal diş boyu 22, düz gövde 48. Geçiş bölgesi hariç en az 47 düz mil gerekli. <b>Tam dişli verilmez.</b>')
    y=group(y-9,'E. Rulmancı')
    y=row(y,'B625','<b>625 ZZ rulman:</b> iç Ø5 / dış Ø16 / genişlik5.<br/>İki tarafı metal kapaklı, <b>flanşsız</b>. F625 verilmez.')
    y=row(y,'BALL8','<b>Ø8 çelik bilye</b>, rulmanda kullanılabilecek düzgün yüzeyli.<br/>Elde 24 uygun bilye varsa tekrar alınmaz.')
    y=group(y-9,'F. Çubuk bağlantısı - plastik burç basılacak')
    y=row(y,'ROD_BUSH','<b>L1-26 burç: dış Ø6 / iç Ø3,3 / boy6.</b><br/>09 tablasında 2 adet; yeni çubuk ile kullanılır. Vida metal M3×10, pul0,5mm; yukarıdaki adetlere dahil.',buy='BASKI')
    y=group(y-9,'G. Bekleyen kalemler - SATIN ALINMAYACAK / İMAL ETTİRİLMEYECEK')
    y=row(y,'ELBOW_SLEEVES','<b>Dirsek ara burçları:</b> L1-23/24 plastik deneme baskısı.<br/>06 tablasında. Metal burç alınmayacak.',need='-',buy='ALMA')
    y=row(y,'FINGER_TUBE','<b>Pasif kepçe burcu:</b> TS-BUSH dış6/iç2,4/boy8.<br/>07 tablasında1 adet basılır. Eski L1-25 kullanılmaz; metal boru alınmayacak.',need='-',buy='ALMA')
    y=row(y,'FRAME_FIX','<b>M4 taban sabitleme cıvataları ve karşılıkları.</b><br/>Boy / somun tipi şasi kalınlığı ölçülünce belirlenecek.',buy='bekle')
    text(M,y-16,'Not / bulunamayan ölçü: ...................................................................................................',8.5)
    text(M,y-32,'Bu belge hazır malzeme alışverişidir; plastik burçlar için yüklü kullanım onayı verilmemiştir.',8)
    assert set(used)==set(ROWS),set(ROWS)-set(used)
    c.save()
    print(OUT)

if __name__=='__main__':main()
