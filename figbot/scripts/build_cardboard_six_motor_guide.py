"""CARD-02: illustrated household prototype manual, NOT manufacturing CAD.

All template dimensions are proposed blank cuts in mm. Servo/horn fit is marked
from delivered hardware. Output is a vector A4 PDF plus a QA geometry manifest.
"""
from pathlib import Path
import math, json
import numpy as np
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf/FIGBOT_KARTON_6_MOTOR_MONTAJ_KILAVUZU.pdf'
QA = ROOT / 'tmp/pdfs/card02'
INK='#203139'; ORANGE='#C6672C'; BLUE='#237A9D'; PALE='#F3F0E9'
KRAFT='#C9A16D'; DARK='#38464D'; GREEN='#4B8165'
for name, file in [('A','arial.ttf'),('AB','arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(Path('C:/Windows/Fonts')/file)))
C=None; PAGE=0; MANIFEST=[]; TEXT_CHECK=[]

def txt(x,y,s,size=10,bold=False,color=INK):
    C.setFillColor(HexColor(color)); C.setFont('AB' if bold else 'A',size)
    width=pdfmetrics.stringWidth(s,'AB' if bold else 'A',size)/mm
    assert x >= 8 and x+width <= 202, (PAGE,s,x+width)
    C.drawString(x*mm,y*mm,s)
    TEXT_CHECK.append((PAGE,x,y,width,s))

def para(x,y,s,w=180,size=10,leading=None,color=INK):
    style=ParagraphStyle('p',fontName='A',fontSize=size,leading=leading or size*1.4,
                         textColor=HexColor(color))
    p=Paragraph(s,style); _,h=p.wrap(w*mm,400*mm)
    assert y-h/mm>=17, (PAGE,'paragraph overflows',s)
    p.drawOn(C,x*mm,y*mm-h)
    return y-h/mm

def line(x1,y1,x2,y2,color=INK,dash=False,width=.75):
    C.setStrokeColor(HexColor(color)); C.setLineWidth(width)
    C.setDash(3,2) if dash else C.setDash()
    C.line(x1*mm,y1*mm,x2*mm,y2*mm); C.setDash()

def rect(x,y,w,h,fill=None,stroke=INK,dash=False):
    C.setStrokeColor(HexColor(stroke));C.setLineWidth(.75)
    if fill:C.setFillColor(HexColor(fill))
    C.setDash(3,2) if dash else C.setDash()
    C.rect(x*mm,y*mm,w*mm,h*mm,stroke=1,fill=bool(fill));C.setDash()

def circle(x,y,r,fill=None,stroke=INK,dash=False):
    C.setStrokeColor(HexColor(stroke));C.setLineWidth(.75)
    if fill:C.setFillColor(HexColor(fill))
    C.setDash(3,2) if dash else C.setDash()
    C.circle(x*mm,y*mm,r*mm,stroke=1,fill=bool(fill));C.setDash()

def arrow(x1,y1,x2,y2,color=ORANGE):
    line(x1,y1,x2,y2,color,width=1.4)
    a=math.atan2(y2-y1,x2-x1)
    for sign in [-1,1]:
        line(x2,y2,x2-3*math.cos(a+sign*.5),y2-3*math.sin(a+sign*.5),color,width=1.4)

def badge(x,y,label):
    circle(x,y,4.2,ORANGE,ORANGE)
    C.setFillColor(HexColor('#FFFFFF'));C.setFont('AB',9)
    C.drawCentredString(x*mm,(y-1.1)*mm,str(label))

def header(title,section='MONTAJ',sub=None):
    global PAGE
    if PAGE: C.showPage()
    PAGE+=1
    txt(15,281,'FIGBOT   /   CARD-02',10,True,ORANGE)
    txt(145,281,section,8,True)
    txt(15,268,title,20,True)
    line(15,261,195,261,color='#D7D9D5')
    if sub:para(15,255,sub,size=9.5)
    txt(15,10,'07.09.2026  |  Karton deney düzeneği  |  Fiziksel doğrulama gerekli',7)
    txt(185,10,f'{PAGE:02d}',9,True)

def note(y,s):
    rect(15,y-17,180,17,PALE,PALE)
    para(19,y-3,s,172,9)

def steps(items,top=115):
    y=top
    for n,(title,body) in enumerate(items,1):
        badge(20,y-3,n)
        yy=para(29,y,f'<b>{title}</b> {body}',165,9.8)
        y=yy-6
    assert y>=20,(PAGE,'steps too long',y)

def ruler():
    line(15,27,115,27)
    for i in range(0,101,10):line(15+i,25,15+i,29)
    txt(15,33,'100 mm kontrol çizgisi',8,True)
    txt(126,26,'%100 / Gerçek boyut',8,True,ORANGE)
    MANIFEST.append({'page':PAGE,'kind':'ruler','length_mm':100,'x':15,'y':27})

def cross(x,y):
    line(x-2,y,x+2,y,BLUE);line(x,y-2,x,y+2,BLUE)

def blank(id,x,y,w,h,count,label,folds=()):
    assert 12<=x and x+w<=198 and 40<=y and y+h<=241,(PAGE,id)
    rect(x,y,w,h)
    for off in folds:line(x,y+off,x+w,y+off,ORANGE,True)
    txt(x,y+h+4,f'{id}  |  {w:g} x {h:g} mm  |  {count} kes',9,True)
    para(x+3,y+h-5,label,w-6,8)
    MANIFEST.append({'page':PAGE,'kind':'rectangle','id':id,'x':x,'y':y,'w':w,'h':h,'count':count,'folds':list(folds)})

def window(x,y,w,h):
    rect(x,y,w,h,stroke=BLUE,dash=True)

def shade(hexcol,factor):
    c=HexColor(hexcol);return Color(min(c.red*factor,1),min(c.green*factor,1),min(c.blue*factor,1))

class Scene:
    """Illustrative vector isometric solids. Not a CAD fit/collision model."""
    def __init__(self):self.faces=[];self.tags=[];self.axes=[];self.routes=[]
    def face(self,pts,color=KRAFT,factor=1):self.faces.append((pts,color,factor))
    def prism(self,pts,z0,z1,color=KRAFT):
        a=[(x,y,z0) for x,y in pts]; b=[(x,y,z1) for x,y in pts]
        self.face(b,color,1.10)
        for i in range(len(a)):self.face([a[i],a[(i+1)%len(a)],b[(i+1)%len(a)],b[i]],color,.78+.14*(i%3))
    def box(self,x,y,z,w,d,h,color=KRAFT):
        self.prism([(x,y),(x+w,y),(x+w,y+d),(x,y+d)],z,z+h,color)
    def cyl(self,x,y,z,r,length,axis='z',color=DARK):
        pts=[]; pts2=[]
        for i in range(24):
            a=i*math.tau/24;u=r*math.cos(a);v=r*math.sin(a)
            if axis=='z':p=(x+u,y+v,z);q=(x+u,y+v,z+length)
            elif axis=='y':p=(x+u,y,z+v);q=(x+u,y+length,z+v)
            else:p=(x,y+u,z+v);q=(x+length,y+u,z+v)
            pts.append(p);pts2.append(q)
        self.face(pts,color,.8);self.face(pts2,color,1.15)
        for i in range(24):self.face([pts[i],pts[(i+1)%24],pts2[(i+1)%24],pts2[i]],color,.9)
    def ring(self,x,y,z,ro,ri,h,color=KRAFT):
        for i in range(48):
            a=i*math.tau/48;b=(i+1)*math.tau/48
            pts=[(x+ro*math.cos(a),y+ro*math.sin(a)),(x+ro*math.cos(b),y+ro*math.sin(b)),
                 (x+ri*math.cos(b),y+ri*math.sin(b)),(x+ri*math.cos(a),y+ri*math.sin(a))]
            self.prism(pts,z,z+h,color)
    def beam(self,a,b,side=25,color=KRAFT):
        dx=b[0]-a[0];dz=b[2]-a[2];L=math.hypot(dx,dz)
        nx=-dz/L*side/2;nz=dx/L*side/2
        corners=[]
        for p in [a,b]:
            corners.extend([(p[0]-nx,p[1]-side/2,p[2]-nz),(p[0]+nx,p[1]-side/2,p[2]+nz),
                            (p[0]+nx,p[1]+side/2,p[2]+nz),(p[0]-nx,p[1]+side/2,p[2]-nz)])
        for inds,f in [([0,1,2,3],.8),([4,5,6,7],1),([0,1,5,4],.85),([1,2,6,5],1.1),([2,3,7,6],.9),([3,0,4,7],.7)]:
            self.face([corners[i] for i in inds],color,f)
    def motor(self,x,y,z,micro=False,vertical=False,tag=None):
        w,d,h=(23,29,13) if micro else (41,43,20)
        if vertical:
            self.box(x-w/2,y-h/2,z-d,w,h,d,DARK)
            self.box(x-w/2-6,y-h/2,z-5,w+12,h,3,DARK)
            self.cyl(x-8,y,z,3,6,'z','#D3AE4D')
        else:
            self.box(x-w/2+8,y,z-h/2,w,d,h,DARK)
            # Negative-Y motors face inward: their output is on the +Y face.
            front=y+d if y<0 else y
            self.box(x-w/2+2,front-3 if y<0 else front,z-h/2,w+12,3,h,DARK)
            self.cyl(x,front if y<0 else front-6,z,3,6,'y','#D3AE4D')
        if tag:self.tags.append(((x,y,z+20),tag))
    def tag(self,p,s):self.tags.append((p,s))
    def axis(self,a,b):self.axes.append((a,b))
    def draw(self,x=20,y=131,w=170,h=108):
        def proj(p):return (.866*(p[0]+p[1]),p[2]-.5*(p[0]-p[1]))
        allp=[proj(p) for f,_,_ in self.faces for p in f]+[proj(p) for p,_ in self.tags]
        lo=[min(p[j] for p in allp) for j in [0,1]];hi=[max(p[j] for p in allp) for j in [0,1]]
        scale=min((w-12)/(hi[0]-lo[0]),(h-10)/(hi[1]-lo[1]))
        ox=x+(w-(hi[0]-lo[0])*scale)/2-lo[0]*scale
        oy=y+(h-(hi[1]-lo[1])*scale)/2-lo[1]*scale
        def pp(p):u,v=proj(p);return ox+scale*u,oy+scale*v
        # Per-pixel depth prevents broad deck faces and small ring segments from
        # being incorrectly painter-sorted. Cut templates remain vector 1:1.
        pxmm=7
        W,H=math.ceil(w*pxmm),math.ceil(h*pxmm)
        pixels=np.full((H,W,3),255,dtype=np.uint8)
        depths=np.full((H,W),-np.inf,dtype=float)
        edges=[]
        for pts,col,f in self.faces:
            q=[]
            for p in pts:
                u,v=pp(p);q.append(((u-x)*pxmm,(y+h-v)*pxmm,p[0]-p[1]+p[2]))
            color=shade(col,f);rgb=np.array([color.red,color.green,color.blue])*255
            for j in range(1,len(q)-1):
                a,b,d=np.array([q[0],q[j],q[j+1]])
                xmin=max(0,math.floor(min(a[0],b[0],d[0])));xmax=min(W-1,math.ceil(max(a[0],b[0],d[0])))
                ymin=max(0,math.floor(min(a[1],b[1],d[1])));ymax=min(H-1,math.ceil(max(a[1],b[1],d[1])))
                den=(b[1]-d[1])*(a[0]-d[0])+(d[0]-b[0])*(a[1]-d[1])
                if abs(den)<1e-8 or xmin>xmax or ymin>ymax:continue
                xx,yy=np.meshgrid(np.arange(xmin,xmax+1)+.5,np.arange(ymin,ymax+1)+.5)
                aa=((b[1]-d[1])*(xx-d[0])+(d[0]-b[0])*(yy-d[1]))/den
                bb=((d[1]-a[1])*(xx-d[0])+(a[0]-d[0])*(yy-d[1]))/den
                cc=1-aa-bb;zz=aa*a[2]+bb*b[2]+cc*d[2]
                view=depths[ymin:ymax+1,xmin:xmax+1]
                mask=(aa>=-1e-6)&(bb>=-1e-6)&(cc>=-1e-6)&(zz>view)
                view[mask]=zz[mask];pixels[ymin:ymax+1,xmin:xmax+1][mask]=rgb
            for j in range(len(q)):edges.append((q[j],q[(j+1)%len(q)]))
        for a,b in edges:
            n=max(2,int(math.hypot(b[0]-a[0],b[1]-a[1])*1.5))
            t=np.linspace(0,1,n);xx=np.rint(a[0]+t*(b[0]-a[0])).astype(int);yy=np.rint(a[1]+t*(b[1]-a[1])).astype(int)
            zz=a[2]+t*(b[2]-a[2]);valid=(xx>=0)&(xx<W)&(yy>=0)&(yy<H)
            xx,yy,zz=xx[valid],yy[valid],zz[valid]
            visible=zz>=depths[yy,xx]-.65
            pixels[yy[visible],xx[visible]]=[70,69,61]
        im=Image.fromarray(pixels)
        C.drawImage(ImageReader(im),x*mm,y*mm,w*mm,h*mm,mask='auto')
        for a,b in self.axes:
            p=pp(a);q=pp(b);line(*p,*q,BLUE,True)
        for route in self.routes:
            for a,b in zip(route,route[1:]):line(*pp(a),*pp(b),BLUE,width=1.6)
        for p,s in self.tags:
            px,py=pp(p);badge(px,py,s)
        txt(15,y-5,'3D montaj şeması - ölçekli CAD veya çarpışma kontrolü değildir.',7,color=BLUE)

def full_arm():
    s=Scene();s.box(-90,-90,0,180,180,9)
    s.box(-30,-30,9,60,60,60);s.motor(0,0,76,vertical=True)
    for x,y in [(50,0),(-50,0),(0,50),(0,-50)]:s.box(x-8,y-8,9,16,16,65)
    s.ring(0,0,74,60,40,4);s.box(-70,-70,80,140,140,9)
    for y in [-26,22]:s.box(-35,y,89,65,4,65)
    s.motor(0,-68,140);s.motor(0,27,140)
    for y in [-23,19]:s.cyl(0,y,140,18,4,'y',ORANGE)
    s.beam((0,0,140),(86,0,190));s.box(65,-23,166,45,4,43)
    s.box(65,19,166,45,4,43);s.motor(86,-63,190)
    s.cyl(86,-18,190,17,4,'y',ORANGE)
    s.beam((86,8,190),(158,8,161),20)
    s.box(145,-12,145,37,3,32);s.box(145,20,145,37,3,32)
    s.motor(158,-42,161,True);s.cyl(158,-8,161,10,3,'y',ORANGE)
    s.box(151,0,131,42,35,4);s.motor(177,-12,129,True)
    s.beam((154,10,131),(154,10,93),8)
    s.beam((183,10,131),(177,10,93),8)
    s.box(151,7,90,6,8,6,GREEN);s.box(174,7,90,6,8,6,GREEN)
    return s

def build():
    global C
    OUT.parent.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    C=canvas.Canvas(str(OUT),pagesize=A4,pageCompression=1)
    C.setTitle('FIGBOT CARD-02 | Altı motorlu karton kol | Kesim ve montaj')
    C.setAuthor('FIGBOT - Sinan Ekiz için deney kılavuzu')

    header('Altı motorlu karton kol','KILAVUZ',
           'Kes, katla, güçlendir, kuru montaj yap. Yazıcı gelene kadar kısa bir masaüstü deney düzeneği.')
    s=full_arm();s.draw(18,117,176,123)
    txt(15,101,'4 x MG996R  +  2 x MG90S',17,True)
    para(15,90,'Taban dönüşü, iki motorlu omuz, dirsek, aktif bilek ve tutucu. Bu kılavuz önceki iki motorlu karton denemesini genişletir; AERO V3 baskı dosyalarını değiştirmez.',size=10.5)
    note(62,'<b>Deney sürümü:</b> Kartonun dayanımı, bağlantıların ömrü ve motorların yük altında hızı doğrulanmadı. İlk amaç hareket sırası ve yazılım geliştirmedir; hızlı atış değildir.')
    para(15,39,'<b>Nasıl kullanılır?</b> Önce 2-4. sayfaları oku. 5-13: gerçek boy kesim şablonları. 14-22: montaj. 23-26: besleme, kalibrasyon ve test. 27-28: bağlantı yakın planları.',size=9)

    header('Hangi motor, hangi görev?','01 / HAZIRLIK')
    motors=[('M1','MG996R','Tabanı sağa-sola çevirir.'),('M2','MG996R','Omzun bir tarafını kaldırır.'),
            ('M3','MG996R','M2 ile aynı eksende omzu destekler.'),('M4','MG996R','Dirseği açıp kapatır.'),
            ('M5','MG90S','Bileği döndürür; tutucuyu aşağı yönlendirir.'),('M6','MG90S','Bir parmağı açıp kapatır.')]
    y=246
    for code,kind,body in motors:
        rect(15,y-22,180,22,PALE,PALE);txt(20,y-9,code,15,True,ORANGE)
        txt(39,y-8,kind,11,True);txt(39,y-16,body,9);y-=26
    para(15,82,'<b>6 motor, 5 işlev:</b> M2 ve M3 aynı omuz eksenini sürer. İkisi ayrı kalibre edilir; aynı sayısal açı komutunun aynı fiziksel yöne karşılık geldiği varsayılmaz.',size=10)
    para(15,57,'<b>Elindeki siyah parçalar:</b> Bunlar servo başlığı (horn). Milin dişine orijinal horn oturur; karton bu horna bağlanır. Kartondan dişli mil yuvası yapma. Her motorun kendi merkez vidasını sakla.',size=10)
    note(33,'<b>Ölçü sınırı:</b> Aşağıdaki rakamlar karton kesim ölçüleridir. Bitmiş mafsal aralıkları motor, horn ve karton kalınlığıyla yerinde ölçülecek: TBD.')

    header('Masaya koyacakların','02 / HAZIRLIK')
    y=247
    groups=[('Karton ve birleştirme','Kuru oluklu koli kartonu; beyaz tutkal veya kartona uygun yapıştırıcı; güçlü ambalaj / bez bant; kablo bağları; ince sağlam ip veya diş ipi. Katları bastırmak için düz kitaplar.'),
            ('Kesim ve ölçüm','Cetvel, kalem, makas; gerekiyorsa kesim altlığı üzerinde maket bıçağı. Delik için biz veya uygun küçük matkap ucu; varsa kumpas. Parmaklarını kesme hattından uzak tut.'),
            ('Motora ait parçalar','4 MG996R + 2 MG90S; her biri için uygun orijinal horn ve merkez vidası. Hornun küçük deliklerine uyan vida-somun-pul veya ince sağlam bağ ipi. Kablo bağı her horn deliğine sığmayabilir.'),
            ('İki karşı yatak','Dirsek ve bileğin boş tarafı için 2 adet uygun cıvata, somun, pul ve serbest dönen plastik burç. M4 adaydır; boyu ve burç çapı kuru montajdan sonra belirlenir. Bunların elinde olduğu varsayılmıyor.'),
            ('Taban ve temas yüzleri','Tabanı bağlayacağın sert tahta / tepsi; kaymayan sabitleme veya kelepçe. İnce düzgün plastik ambalaj parçası kayma halkasına; yumuşak sünger tutucuya. Ağırlığı hareketli kola değil sabit tabana koy.'),
            ('Elektronik','Uno, PCA9685, mevcut regülatörler, sigortalı kablolar ve multimetre. Altı motorun beslemesi ayrıca doğrulanmalı; tek motoru çeviren powerbank tüm kol için yeterlilik kanıtı değildir.')]
    for title,body in groups:
        txt(15,y,title,11,True,ORANGE);y=para(15,y-5,body,size=9.3)-9
    note(37,'<b>Eksik karşı destek varsa:</b> Tüm motorları ayrı ayrı test edebilirsin. Yük taşıyan tam kol denemesini, uygun destek ve bağlantı hazır olmadan yapma.')

    header('Çizgileri böyle okuyacaksın','03 / HAZIRLIK')
    line(20,242,65,242);txt(75,239,'Düz siyah: dış hattı kes.',10,True)
    line(20,226,65,226,ORANGE,True);txt(75,223,'Kesik turuncu: ez ve katla.',10,True)
    line(20,210,65,210,BLUE,True);txt(75,207,'Mavi: motorla ölç, sonra kes.',10,True)
    cross(42,194);txt(75,191,'Artı: mil / delik işaretleme referansı.',10,True)
    s=Scene()
    for i in range(3):s.box(0,0,i*14,65,45,4,KRAFT if i!=1 else '#DDC6A1')
    s.tag((80,20,34),'1');s.draw(20,120,75,59)
    para(104,177,'<b>Katmanları çaprazla.</b><br/>Bir katın olukları boyuna, diğerinin enine. Düz zeminde bastır; yapıştırıcının üretici kuruma süresine uy. Islak tutkal üstünde montaj yapma.',86,9.5)
    para(15,112,'<b>Kutu kesitli kollar:</b> Tüm kol boyunca karton yığmak yerine dört yüzlü boş tüp yap. Motor taşıyıcılarında 3 kat; bağlantı plakalarında 2 kat kullan. Çok kalın karton küçük mafsalları büyütür; önce bir küçük numune katla.',size=10)
    para(15,80,'<b>Delikler en son.</b> Şablondaki motor penceresi yalnız referanstır. Gerçek motoru koy, mil merkezini hizala, gövdeyi çiz. Küçük başlayıp kademeli genişlet. Vida ve bağ yerlerini sağlam kenardan geçir; motor kablosunu sıkıştırma.',size=10)
    note(46,'<b>A4 yazdırma:</b> %100 / gerçek boyut. “Sığdır” kapalı. Her şablon sayfasının 100 mm çizgisini cetvelle kontrol et. Kesilecek adet, katmanlar dahil toplam ham parçadır.')

    header('B01 / Sabit taban','KESİM 1:1','3 ham parça = 1 adet üç kat taban. Tamamı sert tahta / tepsiye sabitlenecek.')
    blank('B01',15,50,180,180,3,'SABİT TABAN<br/><br/>Motor kaidesinin merkezini burada belirle.<br/>Oluk yönlerini katlar arasında çapraz çevir.')
    cross(105,140);txt(77,130,'Merkez referansı',9,color=BLUE);ruler()

    header('B04 / Dönen tabla','KESİM 1:1','B04: 3 ham parça = 1 tabla. Motor başlığı tablanın altında, merkez vidası üstten erişilebilir olacak.')
    blank('B04',25,93,140,140,3,'DÖNEN TABLA<br/>Dış köşeleri istersen kesimden sonra hafif yuvarla.')
    circle(95,163,4,stroke=BLUE,dash=True);cross(95,163)
    txt(40,144,'Merkez vidaya erişim: Ø8 mm aday',8,color=BLUE)
    txt(40,137,'Horn deliklerini kendi parçandan aktar.',8,color=BLUE)
    para(15,77,'<b>Merkez:</b> Hornu alt yüze bağla. Merkez vidaya üstten tornavida ulaşmalı; deliği gerçek başlığa göre ayarla. Mili kartona sürterek yataklama.',size=9.5)
    ruler()

    header('B03 + B05 / Kapak ve halka','KESİM 1:1','B03 iki kat kapak; B05 iki kat kayma halkası. Halka içi boşaltılır; motor gövdesine sürtmemeli.')
    circle(85,178,60);circle(85,178,40)
    txt(29,245,'B05  |  dış Ø120 / iç Ø80 mm  |  2 kes',9,True)
    txt(52,176,'İçini çıkar',10,True)
    MANIFEST.append({'page':PAGE,'kind':'ring','id':'B05','outer_d':120,'inner_d':80,'count':2})
    blank('B03',20,40,70,70,2,'KAİDE KAPAĞI')
    window(33.5,64,43,22);cross(63,75)
    para(101,102,'Mavi pencere 43 x 22 mm referans. MG996R gövdesini yerinde çiz. Kapak, motorun montaj kulaklarını taşımalı; pencere kulakları yutacak kadar büyümemeli.',91,9)
    ruler()

    header('B02 + B06 / Katlanan kaide','KESİM 1:1','B02 iki L parça birleşince yaklaşık 60 x 60 mm kaide oluşur. B06 dört küçük destek sütunudur.')
    blank('B02',20,171,130,60,2,'KAİDE YARISI<br/>60 + 60 + 10 mm')
    for off in [60,120]:line(20+off,171,20+off,231,ORANGE,True)
    blank('B06',20,63,90,80,4,'HALKA SÜTUNU<br/>Yükseklik en son<br/>kesilip ayarlanır.')
    for off in [20,40,60,80]:line(20+off,63,20+off,143,ORANGE,True)
    para(119,140,'Dört 20 mm yüz + 10 mm kapama payı. 80 mm ham yüksekliktir; nihai yükseklik değildir.<br/><br/>Halka + tabla, takılı horn seviyesine göre kuru montajda ayarlanır.',76,9)
    txt(20,155,'B02: dik çizgiler kat; son 10 mm yapıştırma payı.',8,color=ORANGE)
    ruler()

    header('S01-S03 / Omuz ayakları','KESİM 1:1','S01: 6 kes -> 2 üç kat dikme. S02: 6 kes -> 2 üç kat ayak. S03: 12 kes -> 4 üç kat payanda.')
    blank('S01',20,150,95,80,6,'OMUZ DİKMESİ')
    window(38,194,43,22);cross(67.5,205)
    para(124,224,'Mil referansı:<br/>soldan 47,5 mm<br/>alttan 55 mm.<br/><br/>İki dikmede eşleştir. Motorları dış yüze yerleştir.',70,9)
    blank('S02',20,97,95,30,6,'AYAK / alt kenara dik bağlanır')
    C.setStrokeColor(HexColor(INK));p=C.beginPath();p.moveTo(20*mm,48*mm);p.lineTo(50*mm,48*mm);p.lineTo(20*mm,78*mm);p.close();C.drawPath(p)
    txt(60,72,'S03  |  30 x 30 mm dik üçgen',9,True)
    txt(60,64,'12 kes. Her dikmeye 2 payanda.',9)
    MANIFEST.append({'page':PAGE,'kind':'triangle','id':'S03','legs':[30,30],'count':12})
    ruler()

    header('A01 + A02 / İçi boş kollar','KESİM 1:1','70 ve 50 mm tüp boylarıdır; motor eksenleri arası mesafe değildir. Kısa deney geometrisi için öneridir.')
    blank('A01',20,125,70,110,1,'ÜST KOL',folds=(25,50,75,100))
    blank('A02',115,125,50,110,1,'ÖN KOL',folds=(25,50,75,100))
    txt(20,116,'4 x 25 mm yüz + 10 mm kapama payı',9,True)
    blank('J03',20,71,100,20,12,'BAĞLANTI ŞERİDİ - gerektiği yerde kısalt')
    para(15,61,'J03: mafsal köprüleri, tüp bağlantıları ve destek yamaları için ham stok. Nihai boylar kuru montajda belirlenir. Oluklar tüpün 70 / 50 mm boyuna paralel olsun.',size=8.5)
    ruler()

    header('J01 + A03 / Dirsek ve plakalar','KESİM 1:1','J01: her şekilden 2 kes -> 2 çift kat yanak. A03: 8 kes -> 4 çift kat plaka (2 omuz, 2 dirsek).')
    blank('J01-A',20,180,70,55,2,'MOTOR TARAFI')
    window(30.5,199,43,22);cross(60,210)
    blank('J01-B',115,180,70,55,2,'KARŞI DESTEK')
    cross(155,210)
    para(15,169,'Her iki yanağın ekseni: soldan 40 mm, alttan 30 mm. Mavi pencereyi gerçek motorla düzelt. Karşı deliği seçtiğin cıvata / burç çapına göre aç.',size=9.5)
    blank('A03',20,72,45,45,8,'ÇİFT KAT<br/>bağlantı')
    circle(42.5,94.5,4,stroke=BLUE,dash=True)
    para(82,121,'Üç plaka orijinal hornlara bağlanır: iki omuz + bir dirsek. Dördüncü plaka dirseğin karşı pivotudur; buna körlemesine Ø8 delik açma.<br/><br/>Horn delik aralıklarını fotoğraftan değil, elindeki parçadan aktar.',111,9.3)
    ruler()

    header('J02 + A04 / Hafif bilek','KESİM 1:1','J02: her şekilden 2 kes -> 2 çift kat yanak. A04: 4 kes -> 2 çift kat plaka, biri motor biri karşı pivot.')
    blank('J02-A',20,195,50,40,2,'MG90S tarafı')
    window(33.5,208,24,14);cross(50,215)
    blank('J02-B',120,195,50,40,2,'Karşı destek')
    cross(150,215)
    para(15,182,'Mil referansı: soldan 30 mm, alttan 20 mm. 24 x 14 mm pencere yalnız gövde referansıdır. Kulaklar kartona basmalı. Motor başlığı dönerken yanağa değmemeli.',size=9.5)
    blank('A04',20,101,35,35,4,'BİLEK<br/>PLAKASI')
    cross(37.5,118.5)
    para(75,138,'Aktif plaka: küçük horn ve merkez vidasına erişim için yerinde delik aç.<br/><br/>Pasif plaka: burç / cıvata merkezini aynı eksene getir. Karton deliği tek başına yatak değildir; pul ve burçla destekle.',118,9.5)
    note(71,'<b>Hafif tut:</b> Bilekte büyük MG996R yerine MG90S kullanılıyor. Gereksiz karton katı, uzun vida ve fazla yapıştırıcıyı uçta biriktirme.')
    ruler()

    header('G01-G03 / Aşağı bakan tutucu','KESİM 1:1','Bir sabit ve bir hareketli parmak. M6 yalnız hareketli parmağı sürer; ikinci parmak motor gövdesine bağlı değildir.')
    blank('G01',20,190,60,45,2,'AVUÇ / 2 kat')
    para(98,231,'MG90S gövdesi avucun yanına bağlanır. Hornun dönüş düzlemi parmakla aynı düzlemde olmalı.',96,9.5)
    blank('G02',20,135,65,20,2,'20 mm ayak + 45 mm parmak')
    line(40,135,40,155,ORANGE,True)
    blank('G03',20,89,45,15,2,'Hareketli parmak')
    para(98,158,'G02: iki katı kat yerinde sertleştirip kilitleme; önce L biçimini ver, sonra ayağı avuca bağla.<br/><br/>G03: hornun en az iki ayrı deliğinden bağla. Motor merkez vidası da yerinde olmalı.',96,9.2)
    para(15,74,'<b>Sünger:</b> Yaklaşık 15 x 15 mm iki yumuşak temas parçası kes; kavrama yüzlerine yapıştır. Açıklığı nesneye göre kuru montajda ayarla. 45 mm parmak boyu bir kavrama çapı garantisi değildir.',size=9.3)
    ruler()

    header('01 / Tabanı ve kaideyi kur','MONTAJ','Gereken: B01 x3, B02 x2, B03 x2; M1, kendi hornu, bağlar ve sabit sert altlık.')
    s=Scene();s.box(-90,-90,0,180,180,9)
    s.box(-30,-30,30,60,3,60);s.box(-30,-30,30,3,60,60)
    s.box(-30,27,30,60,3,60);s.box(27,-30,30,3,60,60)
    s.box(-35,-35,111,70,70,6);s.motor(0,0,145,vertical=True)
    s.tag((-70,-70,12),'1');s.tag((35,30,75),'2');s.tag((37,35,120),'3');s.draw()
    steps([('Tabanı katla değil, lamine et.','B01 katlarının oluklarını çaprazla; kuruduktan sonra sert altlığa bağla.'),
           ('Kaideyi kapat.','B02 parçalarını 60 mm çizgilerden L yap; 10 mm paylarla kare kutuya birleştir. Alt kenarları bant ve köşe yamalarıyla tabana tuttur.'),
           ('Motoru kapakta taşı.','B03 gövde penceresini M1 ile işaretle. Kulaklar kapağa otursun; motoru iki ayrı bağ / uygun vida ile sabitle. Mil yukarı baksın.'),
           ('Kabloyu dışarı çıkar.','Kapağı kapatmadan kablo için küçük bir yan geçiş aç. Kablo ezilmesin. Motor kasasını sökme veya delme.')])

    header('02 / Tabla yalnız mile asılmasın','MONTAJ','Gereken: B04 x3, B05 x2, B06 x4; M1 hornu. Destek yüksekliği yerinde ayarlanır.')
    s=Scene();s.box(-90,-90,0,180,180,8);s.box(-30,-30,8,60,60,60);s.motor(0,0,74,vertical=True)
    for x,y in [(50,0),(-50,0),(0,50),(0,-50)]:s.box(x-10,y-10,8,20,20,65)
    s.ring(0,0,100,60,40,6);s.cyl(-8,0,135,14,3,'z',DARK)
    s.box(-70,-70,164,140,140,9);s.axis((-8,0,74),(-8,0,188))
    s.tag((68,0,67),'1');s.tag((63,0,107),'2');s.tag((70,65,176),'3');s.draw()
    steps([('Dört sütunu katla.','B06 tüplerini kaidenin etrafına koy. 80 mm ham boyu henüz son yükseklik kabul etme.'),
           ('Halkayı destekle.','B05 üstüne ince, düzgün plastik bant / ambalaj yüzeyi koy. Halka kaideye ve motora değmeden dört sütuna otursun.'),
           ('Tabla-horn bağlantısı.','Orijinal hornu tablanın altına en az iki noktadan bağla; merkez vida erişimini açık bırak. Motoru nötrlemeden hornu nihai sıkma.'),
           ('Yüksekliği kuru ayarla.','Tabla takılı horn seviyesinde halkaya hafifçe otursun. Sütunları kısalt / şimle; motoru yukarı itmesin. Horn ayrıyken tabla sürtünmesini kontrol et.')])

    header('03 / İki omuz motorunu hizala','MONTAJ','Gereken: S01 x6, S02 x6, S03 x12; M2 + M3. Bu aşamada ortak kolu iki motora kilitleme.')
    s=Scene();s.box(-70,-70,0,140,140,8)
    for y in [-32,27]:
        s.box(-47.5,y,8,95,5,80);s.box(-47.5,y-12,8,95,30,6)
        s.box(-40,y-10,14,18,12,20)
    s.motor(0,-78,63);s.motor(0,36,63)
    s.cyl(0,-24,63,16,3,'y',ORANGE);s.cyl(0,20,63,16,3,'y',ORANGE)
    s.axis((0,-95,63),(0,88,63));s.tag((-45,-45,90),'1');s.tag((0,60,105),'2');s.draw()
    steps([('Dikmeleri hazırla.','S01, S02 ve S03 üçer kat olur. Ayakları dikmelere 90° bağla; her dikmede iki üçgen payanda kullan.'),
           ('Motorlar dışarı, miller içeri.','Her motora kendi hornunu geçici tak. İki mil merkezini aynı çizgiye getir; dikmeler paralel dursun.'),
           ('Aralığı motor belirlesin.','Araya iki A03 plaka ve üst kolu kuru yerleştir. Horn / vida / karton boşluğu ölçülmeden sabit bir yanak aralığı yapıştırma.'),
           ('Önce ayrı kalibrasyon.','M2 ve M3 yönleri ile sıfırlarını ayrı dene. Ortak parçayı bağlamadan 25. sayfadaki eşleme adımını uygula; aksi halde motorlar birbirini zorlayabilir.')])

    header('04 / Kutuyu katla, kökü bağla','MONTAJ','Gereken: A01 x1, omuz için A03 x4 ham parça; J03 şeritleri ve iki motorun orijinal hornları.')
    s=Scene();s.box(0,-12,0,70,25,3);s.box(0,-12,22,70,25,3);s.box(0,-12,3,70,3,19);s.box(0,10,3,70,3,19)
    for y in [-42,40]:s.box(-17,y,-9,45,3,45);s.cyl(5,y-4,13,14,3,'y',DARK)
    s.box(8,-12,25,20,25,2,'#DCB989');s.box(48,-12,25,15,25,2,'#DCB989')
    s.axis((5,-56,13),(5,57,13));s.tag((72,10,33),'1');s.tag((-12,-42,40),'2');s.draw()
    steps([('Dört yüzü kapat.','A01 kat çizgilerini ez; kare tüp yap. 10 mm payı içeri bindir; boyuna ek yerini ve iki ucu bantla. Kesit yaklaşık 25 x 25 mm olur.'),
           ('Kökü iki taraftan taşı.','İki çift kat A03 plakayı tüpün iki yanında J03 şeritleriyle bağla. Hornların oturduğu yüzleri düz tut; merkez vidalar erişilebilir kalsın.'),
           ('İp / vida bağlantısını ayır.','Horn kartona deliklerinden tutturulur. Tüp plakaya ayrı bant ve bağlarla tutunur. Yalnız horn üstüne sürülen yapıştırıcıya güvenme.'),
           ('Son boyu ölç.','70 mm tüp, 100 mm mafsal aralığı demek değildir. Dirsek kurulunca iki mil arası gerçek L1 ölçülür. Çarpışıyorsa daha kısa hareket aralığı seç; zorlayarak kapatma.')])

    header('05 / Dirsek: motor + karşı yatak','MONTAJ','Gereken: J01-A/B ikişer kat, M4, dirsek için A03 x4 ham parça, uygun karşı pivot donanımı.')
    s=Scene();s.box(-30,-18,0,30,36,25);s.box(-5,-26,0,70,4,55);s.box(-5,24,0,70,4,55)
    s.motor(35,-75,30);s.cyl(35,-15,30,15,3,'y',ORANGE)
    s.box(12,-11,8,45,3,45);s.box(12,16,8,45,3,45)
    s.cyl(35,20,30,3,24,'y','#AAB4B8');s.cyl(35,32,30,7,2,'y','#AAB4B8')
    s.axis((35,-83,30),(35,61,30));s.tag((-5,-75,62),'1');s.tag((62,40,60),'2');s.draw()
    steps([('Çatalı üst kola bağla.','J01 yanakları A01 ucunda birbirine paralel dursun. J03 köprülerini dönme alanının arkasına koy; horn yolunu kapatma.'),
           ('M4 aktif tarafta.','Gövde dışarı, mil içeri. Horn ile bir A03 plaka dönsün. Karşı A03 aynı hareketli ön kola bağlı olacak.'),
           ('Boş tarafı destekle.','Sabit yanakta cıvata, hareketli plakada serbest burç kullan. Pullar kartonu yayarak desteklesin; somun dönen parçayı sıkıştırmasın. Kesin boylar yerinde ölçülür.'),
           ('Aynı ekseni doğrula.','M4 mil merkezi ile karşı pivot aynı doğru üzerinde olmalı. Motor hornu ayrıyken bağlantı serbest çalışmalı; boşlukta asılı plaka bırakma.')])

    header('06 / Ön kol ve bilek çatalı','MONTAJ','Gereken: A02, J02-A/B, J03, M5. Küçük motor bilekte; büyük motor dirsekte kalır.')
    s=Scene();s.box(-15,-22,0,45,4,45);s.box(-15,18,0,45,4,45)
    s.beam((6,0,22),(70,0,22));s.box(70,-20,2,50,4,40);s.box(70,18,2,50,4,40)
    s.motor(100,-58,22,True);s.cyl(100,-10,22,11,3,'y',ORANGE);s.cyl(100,21,22,3,20,'y','#AAB4B8')
    s.axis((100,-70,22),(100,51,22));s.tag((37,0,48),'1');s.tag((119,22,52),'2');s.draw()
    steps([('A02 tüpünü yap.','A01 gibi dört 25 mm yüzü kapat; 50 mm boyuna ek yerini bantla. Dirseğin iki hareketli plakasına bağla.'),
           ('Katlanma alanı bırak.','Üst ve ön tüp uçları birbirini biçmesin. Kuru montajda tüp / motor / köprü çarpışmalarını kontrol et; gerekirse şerit bağlantısını kaydır.'),
           ('Bilek çatalını kur.','J02 yanakları ön kola bağlanır. M5 gövdesi dışarı; küçük horn içeri. Aynı eksende karşı cıvata-burç desteği ekle.'),
           ('L2 ölçüsünü kaydet.','Dirsek mili ile bilek mili arasını ölç. 50 mm tüp boyu L2 değildir. Kılavuzdaki kısa düzenek, aracın gerçek erişim mesafesini temsil etmez.')])

    header('07 / Tutucuyu masada birleştir','MONTAJ','Gereken: G01 x2, G02 x2, G03 x2; M6, küçük horn, ince bağlar ve iki sünger temas yüzeyi.')
    s=Scene();s.box(0,0,60,60,45,5)
    s.box(0,0,15,6,20,45);s.box(0,0,60,20,20,4)
    s.motor(49,-32,56,True);s.cyl(49,-6,56,9,3,'y',DARK)
    s.beam((49,-1,56),(40,-1,14),8)
    s.box(4,0,14,5,18,12,GREEN);s.box(35,-4,14,5,12,12,GREEN)
    s.tag((8,40,74),'1');s.tag((55,-32,84),'2');s.tag((4,10,5),'3');s.draw()
    steps([('Avucu lamine et.','G01 iki kat. G02 sabit parmağın 20 mm ayağını avuca bağla; 45 mm kısmı aşağı baksın. L köşeyi küçük bir karton payandayla güçlendir.'),
           ('M6 gövdesini sabitle.','Gövde avuca iki ayrı bağla tutunsun. Horn dışarıda ve parmakla aynı düzlemde olsun; gövdeyi ve hornu birlikte bantlama.'),
           ('Hareketli parmağı bağla.','G03 iki katı horna en az iki delikten bağla. Parmak ve sabit çene uçları aynı yükseklikte olsun; açıklığı nesneye göre ayarla.'),
           ('Sünger ve sınır.','Temas yüzlerini yumuşat. Önce sünger / kağıt top tut. Kapanma açısını zorlayarak sıkıştırma; motor uğulduyorsa gücü kesip sınırı azalt.')])

    header('08 / Tutucu bileğe nasıl bağlanır?','MONTAJ','Gereken: iki çift kat A04 plaka; M5 hornu, karşı burç / pul ve tutucunun avucu.')
    s=Scene();s.box(-55,-12,60,50,25,25)
    s.box(-10,-23,43,50,4,40);s.box(-10,22,43,50,4,40)
    s.motor(20,-59,63,True);s.cyl(20,-15,63,10,3,'y',DARK)
    s.box(2,-11,46,35,3,35);s.box(2,15,46,35,3,35)
    s.box(0,-8,37,60,24,4);s.box(0,-8,0,5,15,37)
    s.motor(48,-29,33,True);s.beam((48,-3,33),(42,-3,0),7)
    s.cyl(20,23,63,3,19,'y','#AAB4B8');s.axis((20,-67,63),(20,54,63))
    s.tag((29,25,93),'1');s.tag((60,0,38),'2');s.draw()
    steps([('İki hareketli plaka.','Bir A04 küçük horna, öteki karşı burca bağlanır. İkisini J03 şeritleriyle tutucu avcuna bağla; avuç her iki taraftan taşınsın.'),
           ('Tutucu asılı kalmasın.','M5 yalnız yönlendirme yapar; karşı pivot ikinci taşıma noktasıdır. Burç ekseni şaşıksa kartonu eğerek zorla oturtma.'),
           ('Aşağı bakma konumu.','İlk pozda avuç yaklaşık yatay, parmaklar aşağı olsun. Elektrik verilmeden kolu destekle; servoyu elle zorlayarak çevirmeden horn açısını ayarla.'),
           ('Diklik yazılımla korunur.','Omuz ve dirsek değişince bilek açısı da değişir. M5 tek başına tutucuyu sürekli dik tutmaz; kalibre edilmiş üç açı birlikte kullanılmalı.')])

    header('09 / Tüm kol ve kablo yolu','MONTAJ','Motorları etiketle: M1-M6. Bu çizim parçaların görevini gösterir; gerçek eklem aralıklarını ölçmen gerekir.')
    s=full_arm();s.tag((-25,-65,101),'1');s.tag((80,0,218),'2');s.tag((170,0,195),'3')
    s.routes.append([(177,-13,133),(168,-25,139),(169,-27,161),(158,-28,176),
                     (144,-28,169),(114,-28,181),(99,-30,187),(95,-33,206),
                     (79,-33,209),(70,-33,195),(39,-34,174),(13,-35,156),
                     (3,-39,139),(-17,-42,134),(-29,-49,150),(-46,-51,134),
                     (-49,-60,90),(-70,-72,20)])
    s.draw();txt(15,120,'Mavi çizgi: önerilen kablo yolu; mafsallarda gevşek pay bırak.',8,color=BLUE)
    steps([('Kabloyu sabit tarafta tut.','M2/M3 kabloları omuz dikmesinden, M4 kablosu üst kol boyunca; M5/M6 kabloları ön kol boyunca ilerlesin.'),
           ('Her mafsalda gevşek yay.','Kabloda küçük bir U payı bırak. Tam harekette gerilmesin; çatalın içine sarkıp sıkışmasın. Bağı servo kablosunu ezecek kadar sıkma.'),
           ('Taban sonsuz dönmez.','M1 için kablonun izin verdiği dar bir deneme aralığı kullan. Bu düzende kayar elektrik bileziği yok; tam tur dönüş yapma.'),
           ('Sabitle ve destekle.','Taban sert altlığa bağlansın. İlk enerjilendirmede kolun altına yumuşak destek koy; enerji kesilince kol düşebilir. Elini mafsal ve çenelerden uzak tut.')])

    header('Besleme: altı motor, ayrı güç','ELEKTRONİK','Bu sayfa güç mimarisidir; teslim alınan modüller ve akım kapasitesi ölçülmeden nihai kablolama onayı değildir.')
    # Deliberately architecture-only: no invented terminal topology/current rating.
    rect(18,202,47,27,PALE);para(22,223,'<b>Bilgisayar USB</b><br/>Arduino Uno',39,10)
    rect(114,202,76,27,PALE);para(119,223,'<b>PCA9685 mantık</b><br/>Uno ile I2C + ortak GND',66,10)
    arrow(67,215,111,215,BLUE)
    rect(18,137,67,37,PALE);para(22,169,'<b>Akü / uygun DC kaynak</b><br/>Sigorta + kesme düzeni<br/>Regülatör(ler)',59,9.5)
    rect(119,137,71,37,PALE);para(124,169,'<b>M1-M6 servo gücü</b><br/>Motorlara uygun gerilim<br/>Doğrulanmış akım payı',61,9.5)
    arrow(88,155,116,155,ORANGE);arrow(151,199,151,177,BLUE)
    txt(94,180,'Sinyaller',8,True,BLUE)
    steps([('Arduino motorları beslemez.','Uno 5V pininden, bilgisayar USB portundan veya 5V/2A powerbankten altı motora güç dağıtma.'),
           ('12V doğrudan servoya gitmez.','Regülatör çıkışını motorlar bağlı değilken ölç. Gerilimi her motorun doğrulanmış sınırına göre seç; kablo rengini tek başına ölçüm sayma.'),
           ('Çıkışları birleştirme.','Birden çok regülatörün artı çıkışlarını paralelleme. Ortak GND gerekir. PCA9685 üzerindeki V+ hattını iki kaynaktan aynı anda besleme.'),
           ('Güç kapasitesi ölçülecek.','Servo güçlerini uygun dağıtım üzerinden ver; jumper / ince kart izlerine tüm akımı yükleme. INA219 modül sınırını aşan motor grubunu onun üzerinden geçirme.')],top=121)

    header('İlk hareket: bir motorla başla','DEVREYE ALMA','Bu PDF hiçbir motoru çalıştırmaz ve çok kanallı firmware yüklemez. Mevcut tek motor paneli tüm kol kontrolü değildir.')
    s=Scene();s.motor(0,0,20);s.cyl(0,-22,20,16,3,'y',ORANGE);s.box(-40,-35,-2,90,95,4)
    s.tag((0,-32,51),'1');s.draw(30,165,145,72)
    steps([('Önce hornlar serbest.','M1, M2, M3, M4, M5 ve M6 için sırayla küçük açı değişimleri dene. Mil üzerindeki kısa işaretçiyle yönü gör; mekanizmayı tam yükle başlatma.'),
           ('Nötrü ve yönü kaydet.','Her servonun orta konumu, artı yönü ve dar deneme sınırını ayrı kaydet. Paneldeki 90° gerçek eklem sıfırı değildir.'),
           ('Hornu konuma tak.','Gücü kes; mekanizmayı destekle. Orijinal hornu en yakın dişte uygun açıya yerleştir ve kendi merkez vidasıyla tuttur. Son düzeltme yazılım sıfırındadır.'),
           ('Küçük adımlarla genişlet.','Önce birkaç derecelik yavaş hareket. Sürtünme, takılma, aşırı uğultu, ısınma veya karton ezilmesinde gücü kes. 0-180° komutunu körlemesine tarama.')],top=146)
    note(38,'<b>Durmak için:</b> Güç kesme erişilebilir olsun; kesince kol düşebileceğinden altına destek koy. Çalışan kolu elinle yakalamaya veya motoru zorla durdurmaya çalışma.')

    header('Çift omuz ve yazılım eşlemesi','KALİBRASYON')
    # Explicit front elevation of mirrored pair and shared axis.
    rect(24,211,32,26,DARK);rect(154,211,32,26,DARK)
    line(57,224,153,224,BLUE,True);rect(71,212,68,23,PALE)
    txt(28,244,'M2',12,True);txt(162,244,'M3',12,True)
    txt(80,221,'Ortak üst kol',10,True)
    arrow(44,205,76,198);arrow(165,205,133,198)
    para(15,185,'<b>Eşleme sırası:</b> İki motorun hornları ortak parçaya bağlı değilken ayrı ayrı nötrle. Aynı kol duruşunda hornlar zorlanmadan takılmalı. Küçük bir pozitif omuz komutunda iki tarafın aynı fiziksel kaldırma yönüne gitmesini doğrula; sonra mekanik bağlantıyı tamamla.',size=10)
    para(15,151,'<b>Komut modeli:</b> Her servo için ayrı sıfır, yön ve ölçek kullan. M3 için yön genellikle M2’nin tersidir; ölçmeden varsayma. Ortak kola bağlı motorlardan birini tek başına döndürme. İki motora eşleşmiş hedefler birlikte gönderilmeli.',size=10)
    rect(15,96,180,30,PALE,PALE)
    txt(20,115,'servo_komutu = sıfır + yön x ölçek x eklem_açısı',11,True)
    txt(20,103,'Aşağı bakan bilek: q_bilek = sabit_yön - q_omuz - q_dirsek',9,True)
    para(15,86,'Formül aynı düzlemdeki ideal eklem açıları içindir; servo ekranındaki ham dereceler değildir. Gerçek sıfırlar, yönler, çalışma sınırları ve bileğin mekanik montaj ofseti kalibre edilir.',size=9.5)
    note(56,'<b>Yazılımda ayrı profil:</b> CARD-02 için L1, L2, omuz yüksekliği ve tutucu ofsetini kaydet. Karton deneyinin değerlerini AERO V3 araç geometrisinin üzerine yazma.')
    para(15,32,'Kamera / hedef seçimi / komut sırası geliştirilebilir. Gerçek yük hızı, hassasiyet, tam araç erişimi ve atış zamanlaması bu düzenekle kesinleşmez.',size=9)

    header('Kontrol et, ölç, sonra dene','SON KONTROL')
    rows=[('Karton kalınlığı / kat sayısı','________ mm / ________'),('L1: omuz mili - dirsek mili','________ mm'),
          ('L2: dirsek mili - bilek mili','________ mm'),('Omuz mili - masa yüksekliği','________ mm'),
          ('Bilek mili - kavrama merkezi ofseti','________ mm (yönü çiz)'),('Besleme / tarih / profil adı','________ V / ________ / CARD-02')]
    y=247
    for a,b in rows:
        rect(15,y-16,180,16,PALE if int(y)%2 else '#FFFFFF',stroke='#D4D8D5')
        txt(19,y-10,a,9);txt(120,y-10,b,8.5);y-=16
    para(15,141,'<b>Başlamadan:</b> Taban sabit; merkez vidalar takılı; karşı yataklar bağlı; yapıştırıcı kuru; kablolar serbest; omuz eşlemesi doğru; güç kesme erişilebilir; kolun altında destek var.',size=9.8)
    para(15,114,'<b>Test sırası:</b> Yüksüz yavaş hareket -> kağıt / sünger nesne -> tartılmış 10-20 g -> yalnız bağlantılar ve motorlar kararlıysa yaklaşık 40 g. İlk denemede nesneyi birkaç santimetre kaldır, yakındaki alçak kaba bırak. 100 g ve hızlı fırlatma için onay yok.',size=9.8)
    para(15,80,'<b>Sorun varsa:</b> Titreme / uğultu: gücü kes, omuz eşlemesini ve sıkışmayı kontrol et. Tabla zor dönüyor: halka yüksekliği / sürtünmesini kontrol et. Karton delik uzuyor: bağlantıyı yeniden yap. İncir kayıyor: sıkmayı artırmadan önce çene hizası ve süngeri düzelt.',size=9.8)
    note(44,'<b>Bu kılavuzun sonucu:</b> Tamamlanmış bir montaj tarifi ve gerçek boy kesim şablonları. Fiziksel uyum, taşıma gücü, çevrim hızı ve dayanım: PHYSICAL VALIDATION REQUIRED.')

    header('Yakın plan / Horn-karton bağlantısı','DETAY A','Motorun içinden çıkan orijinal başlık kullanılır. Çizim sökülmüş / aralıklı görünüş; motor montajı için ölçü şablonu değildir.')
    s=Scene();s.motor(0,-60,25)
    s.cyl(0,-3,25,16,3,'y',DARK)
    s.box(-22,23,3,45,6,45)
    s.cyl(0,42,25,3,18,'y','#AAB4B8');s.cyl(0,58,25,6,2,'y','#AAB4B8')
    s.axis((0,-30,25),(0,80,25));s.tag((-18,-57,59),'1');s.tag((18,-3,52),'2');s.tag((22,25,56),'3');s.draw(20,140,170,99)
    steps([('Mil -> orijinal horn.','Dişli mil yalnız uygun horn içine girer. Kartonun ortasındaki büyük delik spline değildir; vida ve tornavida erişimi içindir.'),
           ('Horn -> karton.','Başlığı kartona koyup en az iki uzak deliği işaretle. Delik kenarlarını ince plastik yama / pul ile güçlendir; küçük uygun vidalarla veya sağlam ip halkalarıyla bağla.'),
           ('Merkez vida.','Motorun kendi merkez vidası hornu mile tutar. Karton kalınlığını bu vida ile telafi etmeye çalışma; erişim deliği kullan. Vida boyunu rastgele uzatma.'),
           ('Karton -> tüp.','Plakayı tüpe J03 şeritleri, tutkal ve çevre bandıyla bağla. Bağlar dönme hattında çıkıntı yapmasın. Kuru montajdan sonra hafifçe kontrol et; kayma varsa çalıştırma.')],top=122)

    header('Yakın plan / Karşı pivot desteği','DETAY B','Dirsekte ve bilekte aynı ilke kullanılır. Aşağıdaki kesit ölçeksizdir; donanımın kesin boyu elindeki parçalarla belirlenir.')
    # Side section: fixed axle, stationary cheek, rotating plate with sleeve.
    line(24,210,185,210,BLUE,True)
    rect(40,181,10,58,KRAFT);rect(117,184,12,52,KRAFT)
    rect(27,206,137,8,'#B8C4CA');rect(22,199,6,22,'#7E9098')
    for xx in [35,53,109,132]:rect(xx,197,3,26,'#ACB8BD')
    rect(116,202,15,5,BLUE);rect(116,214,15,5,BLUE)
    rect(58,200,10,20,'#7E9098');rect(143,200,10,20,'#7E9098')
    txt(27,243,'Sabit yanak',10,True);txt(109,243,'Dönen plaka',10,True)
    arrow(125,174,125,200,BLUE);txt(102,167,'Burç: plakayla döner',9,True,BLUE)
    txt(23,157,'Cıvata sabit. Dönüş, burç ile cıvata arasında gerçekleşir.',9)
    steps([('Önce gerçek boşluğu ölç.','Cıvata başı, sabit yanak, pullar, somunlar ve hareketli plakanın toplam kalınlığını ölç. M4 yalnız aday çap; uygun boy ve burç netleşmeden delik açma.'),
           ('Sabiti sık, hareketliyi sıkma.','İç somun cıvatayı sabit yanağa tutar. Dış tutucu somun hareketli plakayı ezmez; pul ile burç yanında serbest dönme payı kalır. Gevşeyip düşmeye karşı uygun somun kullan.'),
           ('İki ekseni çakıştır.','Motor çıkış mili ile bu cıvatanın merkezi aynı doğru üzerinde olmalı. Yanakları yamultarak boşluğu kapatma. Önce horn ayrıyken serbestliği kontrol et.'),
           ('Karton aşınmasını izle.','Burç karton içinde dönüp deliği büyütmemeli; plaka ile birlikte dönmeli. Delik uzuyor, pul gömülüyor veya cıvata eğiliyorsa denemeyi durdur.')],top=140)
    C.save()
    (QA/'manifest.json').write_text(json.dumps({'pages':PAGE,'templates':MANIFEST,'output':str(OUT),'scope':'CARD-02 only; not AERO CAD'},indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'Created {PAGE} pages: {OUT}')

if __name__=='__main__':build()
