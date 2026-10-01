"""Printable paper templates for a SHORT cardboard experiment, not AERO CAD."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('Arial',r'C:\Windows\Fonts\arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBold',r'C:\Windows\Fonts\arialbd.ttf'))
P=ParagraphStyle('p',fontName='Arial',fontSize=10,leading=14,textColor=HexColor('#24333b'))
C=canvas.Canvas(str(OUT/'KARTON_KOL_KISA_DENEME.pdf'),pagesize=A4)
C.setTitle('FIGBOT — kısa karton kol kesim ve montaj kılavuzu')


def text(x,y,s,size=10,bold=False,color='#24333b'):
    C.setFillColor(HexColor(color));C.setFont('ArialBold' if bold else 'Arial',size);C.drawString(x*mm,y*mm,s)


def paragraph(y,s,width=180):
    p=Paragraph(s,P);_,h=p.wrap(width*mm,200*mm);p.drawOn(C,15*mm,y*mm-h);return y-h/mm-4


def rect(x,y,w,h):
    C.setLineWidth(.7);C.setStrokeColor(HexColor('#24333b'));C.rect(x*mm,y*mm,w*mm,h*mm)


def line(x1,y1,x2,y2,dash=False):
    C.setStrokeColor(HexColor('#bd6827') if dash else HexColor('#24333b'))
    C.setDash(4,3) if dash else C.setDash()
    C.line(x1*mm,y1*mm,x2*mm,y2*mm);C.setDash()


def header(n,title):
    text(15,279,'FIGBOT / KARTON ÖN DENEME',10,True,'#a85d27')
    text(15,267,title,18,True)
    text(15,12,f'{n} / 4  •  07.09.2026  •  Tam boy robot kolunun dayanım/hız doğrulaması değildir.',8)


def ruler(y):
    line(15,y,115,y)
    for x in range(15,116,10):line(x,y-1.5,x,y+1.5)
    text(15,y+4,'Kontrol çizgisi: tam 100 mm olmalı.',9,True)


header(1,'İki motorla kısa bir deney kolu')
y=paragraph(252,'<b>Amaç:</b> Yazıcı gelene kadar hafif nesneyi kavrama, birkaç santimetre kaldırma ve bırakma denemesi. 1 × MG996R kaldırır; 1 × MG90S tutucuyu açıp kapatır. Kol motor milinden nesne merkezine en fazla yaklaşık 120 mm olsun.')
y=paragraph(y,'<b>Malzeme:</b> Kuru, ezilmemiş oluklu koli kartonu; koli bezi/ambalaj bandı; cetvel; makas veya kesim altlığıyla maket bıçağı; mevcut kablo bağları; sağlam ip/diş ipi; iki motorun kendi hornları ve merkez vidaları. Varsa beyaz tutkal ve ince plastik ambalaj parçalarıyla delikleri güçlendir. Tutkalın tamamen kurumasını bekle.')
y=paragraph(y,'<b>Taşıma garantisi yok:</b> Kartonun kalınlığı, oluk yönü ve bandın tutuşu bilinmiyor. Önce yüksüz, sonra sünger/kâğıt top; düzenek bozulmuyorsa tartılmış 10–20 g ve en son yaklaşık 40 g ile yavaş deneme. Bu bantlı düzende 100 g yük, hızlı savurma ve atış deneme.')
# Concept elevation. Cardboard stand is a placeholder fixed to a rigid support.
rect(22,125,43,43);text(24,145,'Sabit destek',9,True)
rect(52,146,25,17);text(23,117,'Bant + iki ayrı bağ',9)
C.setFillColor(HexColor('#bb8654'));C.rect(75*mm,152*mm,79*mm,9*mm,fill=1,stroke=1)
text(83,167,'Kutu kesitli kısa kol',9,True)
rect(148,146,16,20);text(145,137,'MG90S',9)
line(147,149,147,120);line(165,149,172,121)
C.setFillColor(HexColor('#8db497'));C.circle(158*mm,122*mm,5*mm,fill=1,stroke=0)
text(22,103,'Şema ölçeksizdir. MG996R mili sayfaya dik; kol yukarı-aşağı döner.',9)
y=paragraph(94,'<b>Sabit taban:</b> 200 × 200 mm kartondan iki katı, oluk yönleri birbirine dik olacak şekilde birleştir. Bunu sert bir tahta/tepsi üstüne sabitle. Motoru boş ve ezilen bir kutuya asma; sert bir blok veya içerisi kartonla doldurulmuş küçük kutuya iki ayrı bağla tuttur. Tabanı devrilmeyecek şekilde sabitle; ağır desteği hareketli kola yükleme.')
paragraph(y,'<b>Bu sürümün sınırı:</b> Tek kaldırma ekseni vardır; tutucu kol ile birlikte eğilir, otomatik dik kalmaz. Tam XYZ toplama veya sabit aşağı bakan bilek yerine geçmez. İlk testte nesne yerini sabitle, kol kalktıktan sonra altına alçak bir kap koyarak bırakmayı dene.')
C.showPage()

header(2,'Kesim şablonu • kutu kol ve kök plakası')
paragraph(253,'A4, <b>%100 / gerçek boyut</b> yazdır. “Sayfaya sığdır” seçme. Düz çizgi kesim, kesik turuncu çizgi katlama. Önce 100 mm kontrol çizgisini ölç. Yazıcın yoksa aşağıdaki ölçüleri cetvelle doğrudan kartona çiz.')
# 120 x 110 mm developed net, four25 faces and one10 tab.
rect(20,103,120,110)
for off in (25,50,75,100):line(20,103+off,140,103+off,True)
for yy in (115,140,165,190):text(38,yy,'25 mm yüz • oluklar 120 mm yönünde',8)
text(39,206,'10 mm bant / yapıştırma payı',8)
text(145,168,'110 mm',9,True)
text(60,96,'120 mm',10,True)
paragraph(89,'Karton kalınlığı nedeniyle bitmiş ölçü yaklaşık olur. Kat çizgisini cetvelle ez; kartonu tamamen kesme. Dört yüzü kare tüp yap, 10 mm payı içe bindir. Boyuna ek yerini bantla; kök, orta ve uç çevresine ayrıca birer tur bant sar. Düz tek şerit kullanma.')
for x in (20,72):
    rect(x,28,40,40);C.circle((x+20)*mm,48*mm,4*mm,stroke=1,fill=0)
text(124,56,'Kök plakası: 40 × 40 mm, 2 kat',9,True)
text(124,49,'Ortadaki erişim deliği: Ø8 mm',8)
text(124,42,'Horn deliklerini kendinden işaretle.',8)
text(124,35,'Oluk yönlerini çapraz birleştir.',8)
# Last label width must stay within page.
C.showPage()

header(3,'Kesim şablonu • hafif tutucu')
paragraph(253,'<b>Önce uç tutucuyu tek başına kur.</b> MG90S gövdesi avuç plakasına sabitlenir; hareketli parmak yalnız orijinal horn ile döner. Diğer parmak sabittir. Servo gövdesini ve dönen hornu birbirine bantlama.')
for x in (20,100):
    rect(x,165,60,45);text(x,215,'Avuç: 60 × 45 mm',9,True)
    text(x+4,185,'İki katı çapraz birleştir.',8)
text(20,156,'Motor ve bağ yerlerini gerçek MG90S ile işaretle; önceden kör delik açma.',9)
for x in (20,100):
    rect(x,113,65,20);line(x+20,113,x+20,133,True)
    text(x,140,'Sabit parmak: 65 × 20 mm',9,True)
text(20,104,'20 mm bölüm avuca bağlanır; kalan 45 mm aşağı bakar. İki kat + bant.',9)
for x in (20,100):
    rect(x,69,45,15);text(x,90,'Hareketli: 45 × 15 mm',9,True)
paragraph(62,'Hareketli parmağın iki katını birleştir; gerekiyorsa dondurma çubuğuyla destekle. Küçük hornun mevcut deliklerinden ip ile iki ayrı noktadan bağla. Sabit parmağın konumunu nesneye göre ayarla. İki temas yüzüne ince sünger koy; meyveyi ezmeden tutacak kadar kapat. Hornu fiziksel sona zorlayan açı verme.')
ruler(25)
C.showPage()

header(4,'Birleştirme ve ilk çalıştırma sırası')
y=252
steps=[
('1 — Önce motorları boşta merkezle', 'Horn ve karton bağlı değilken mevcut panelden tek motorun yönünü ve orta konumunu gözle kontrol et. İlk açılışta sıçrama olabilir. Gücü kes; orijinal hornu istediğin başlangıç yönünde, kendi merkez vidasıyla tak. Mil dişlerini kartonla taklit etme.'),
('2 — Hornu kök plakasına mekanik olarak bağla', 'Hornun merkezini Ø8 mm erişim deliğine hizala; en az iki çevre deliğini kartona işaretle. Delik çevresini bant/ince plastikle güçlendir. Mevcut deliklerden sağlam ipi birkaç kez geçirip düğümle veya uygun kısa vida-pul kullan. Bant yalnız yardımcıdır; torku sadece yapışkan taşımasın. Motora delik açma, uzun merkez vidası takma.'),
('3 — Kök plakasını kutu kola bağla', 'Plakayı tüpün kök tarafındaki yan yüzüne, mil merkezi uçtan yaklaşık 20 mm içeride kalacak şekilde bağla. Merkez vidasına tornavida erişimi bırak. Plakayı ve tüpü çepeçevre bantla; ip/bağ için takviye edilmiş iki ayrı bağlantı kullan. Kolu elle destekleyerek bağlantının kaymadığını kontrol et; servo milini zorla çevirme.'),
('4 — Tutucuyu uca sabitle', 'Avuç plakasını tüpün ucuna bağla; MG90S gövdesini iki bant/bağla sabitle. Kabloda küçük bir gevşek halka bırak, kabloyu hareketli horn ve keskin karton kenarından uzak tut. İnci̇r merkezi ile MG996R mili arası yaklaşık 120 mm sınırını aşmasın.'),
('5 — Önce küçük ve yavaş hareket', 'Karton destekliyken başla. İlk denemede orta konum çevresinde yaklaşık ±10° gözlenen hareket; tam180° veya hızlı test düğmesi yok. Eğilme, delik büyümesi, bant kayması, titreme ya da motor ısınmasında dur. Güç kesilince kol düşebilir; altına yumuşak destek koy.'),
('6 — Güç bağlantısını ayrı doğrula', 'Servoları Arduino5V pininden veya bilgisayar USB’sinden topluca besleme. Akü varsa12V doğrudan servoya verilmez; sigortalı ve önceden ölçülmüş uygun regüle hat gerekir. Mevcut5V/2A powerbank iki servonun birlikte çalışması için doğrulanmış değildir. Ortak GND gerekir. Mevcut panel tek servo içindir; ikinci motor için ayrı kanal/kod gerekir.'),
('7 — Yazılımı modüller halinde ilerlet', 'Kamera algılama, komut/yanıt, hareket sırası, aç-kapat sınırı, zaman aşımı ve durdurma mantığı denenebilir. Önce sabit nesne konumuyla çalış. XYZ–eklem kalibrasyonu, gerçek kol geometrisi, dik bilek, hızlı atış, yükte hız ve ömür bu maketle tamamlanmış sayılmaz. Bu kılavuz motor çalıştırmaz ve firmware değiştirmez.')]
for title,body in steps:
    y=paragraph(y,f'<b>{title}</b><br/>{body}')
if y<23:raise RuntimeError(f'Last page overflow: {y}')
C.showPage();C.save()
print(OUT/'KARTON_KOL_KISA_DENEME.pdf')
