"""Source-traceable purchasing candidates for one L1; not an inventory ledger."""
from pathlib import Path
from collections import defaultdict
import json

ROOT=Path(__file__).resolve().parents[1]
from scripts.project_paths import SHOPPING
OUT=SHOPPING/'VERI'
ROWS=[]
def add(code,part,qty,buy,where,url,usage,status,price=None,currency='TRY',pack=1,note=''):
    ROWS.append(dict(code=code,part=part,required=qty,buy_quantity=buy,supplier=where,url=url,usage=usage,
                     status=status,price_per_pack=price,currency=currency,pack_quantity=pack,note=note))

add('I35','M3 pirinç ısı inserti; dış Ø4,5 × boy5 mm',30,40,'Robotizmo','https://www.robotizmo.net/insert-cakma-somun-m3-yukseklik-5mm','16 motor kulağı +4 taban tutucu +4 rotor/tabla +4 üst kol bağları +2 önkol bağı','Sayfa 4799 stok gösteriyor',.13,'USD',note='CAD delik Ø4,2 ×5; ürün dış çapı delik çapıyla aynı olmak zorunda değildir. Isı yerleştirme denemesi gerekli. Uzunluğu 5,7/6 mm insert alma.')
add('I34','M3 pirinç ısı inserti; dış Ø4,5 × boy4 mm',1,5,'Robotizmo','https://www.robotizmo.net/insert-cakma-somun-m3-yukseklik-4mm','Tahrik krankı uç bağlantısı','Sayfa 4517 stok gösteriyor',.12,'USD',note='Krank deliği Ø4,2 ×4,5; 5 mm uzun insert bu yuvaya sığmaz.')
add('I24','M2 pirinç ısı inserti; dış Ø3,2 × boy4 mm',18,25,'Robotizmo','https://www.robotizmo.net/insert-cakma-somun-m2-yukseklik-4mm','12 yıldız kapağı +4 mikro motor kulağı +2 bilek köprüsü','Sayfa 1216 stok gösteriyor',.11,'USD',note='CAD çoğunlukla Ø2,9 delik. Isı yerleştirme denemesi gerekli; 5 mm ürünle değiştirme.')
add('I23','M2 pirinç ısı inserti; dış Ø3,2 × boy3 mm',9,15,'Robotizmo','https://www.robotizmo.net/insert-cakma-somun-m2-yukseklik-3mm','6 rulman kapağı +3 parmak sabit kulağı','Sayfa 1777 stok gösteriyor',.10,'USD',note='Rulman kapağı yatağı yalnız3,5 mm derin; burada4 mm insert kullanılmaz. Parmak kulağı4 mm kalın;3 mm insert aday olarak seçildi.')
add('S38','M3×8 silindirik başlı imbus vida',16,20,'Robocombo','https://www.robocombo.com/m3x8-imbus-civata-beyaz-din912-2883','Dört MG996R motorun kendi montaj kulakları','Sayfa 1954 stok gösteriyor',1.32)
add('S310','M3×10 silindirik başlı imbus vida',10,15,'Robocombo','https://www.robocombo.com/m3x10-imbus-civata-beyaz-din912-3158','4 üst kol bağı +2 önkol bağı +4 motor tablası','Sayfa 2510 stok gösteriyor',1.43,note='Bağlantı baş oturma yüzeyi/insert diş tutuşu montajda kontrol edilir; kör deliğin dibine bastırma.')
add('S320','M3×20 silindirik başlı imbus vida',4,6,'Robocombo','https://www.robocombo.com/m3x20-imbus-civata-beyaz-din912-3161','Taban sabit tutucu yarımları','Sayfa 1910 stok gösteriyor',2.03,note='Eski2,5 mm ara pullar bu bağlantıya eklenmez; nominal diş tutuşu4,5 mm.')
add('S26','M2×6 yıldız silindir başlı vida DIN7985',22,30,'GoBarNet','https://www.gobarnet.com/m2-x-6-yildiz-basli-ysb-vida','12 yıldız kapağı +4 mikro servo kulağı +6 rulman kapağı','Satış sayfası var; adet stoğu doğrulanamadı',2.40,note='Havşa başlı veya sac vidası değil, metrik düz uçlu vida.')
add('S28','M2×8 yıldız silindir başlı vida DIN7985',2,10,'Komponentci','https://www.komponentci.net/m2x8mm-ysb-vida-din7985-yildiz-silindir-basli-civata-10-adet-pmu12172','Bilek köprüsü iki yan bağlantısı','Sayfa Stok Var gösteriyor',8.57,pack=10,note='1 paket=10 adet; ürün açıklamasında5mm şeklinde kopya metin hatası var; başlık/teknik ölçü8mm. Gelen ürünü ölç.')
add('B625','625ZZ rulman — 5×16×5 mm, flanşsız',2,2,'Rulmanal','https://www.rulmanal.com.tr/urun/625-zz-kwc-5-16-5-rulman','Dirsek ekseninde sağ/sol yatak','Sayfa 8560 stok gösteriyor',29.10,note='F625 flanşlı model alma. Sayfa başlığında BGR, URLde KWC var; gelen marka değişebilir, ölçü aynı seçilmeli.')
add('BALL8','Ø8 mm çelik bilye',24,50,'Rulmanal','https://www.rulmanal.com.tr/urun/50-adet-8mm-celik-bilye-sapan-mermisi-cok-amacli-tane-demir-misket-rulman-bilya-8-mm','Tabandaki basılı bilye kafesi','Sayfa 649 stok gösteriyor',39.90,pack=50,note='1 paket=50 adet. Tolerans/yuvarlaklık sınıfı sayfada yok; prototip adayıdır. Eldeki24 uygun bilye varsa tekrar alma.')
add('FINGER_SCREW','M2×14 silindir başlı parmak eksen vidası',3,5,'TME','https://www.tme.eu/en/details/m2x14_d7985/bolts/kraftberg/','Üç parmak; vida metal burcun içinde','Katalog eşleşmesi; stok/paket minimumu doğrulanamadı',note='14 mm CAD adayıdır; minimum satış adedi5 olduğu iddia edilmiyor. Eksen sıkıldığında parmak serbestliği ve insert tutuşu denenmeli.')
add('ROD_SCREW','M3×14 silindirik başlı bağlantı vidası',2,4,'TME','https://www.tme.eu/tr/tr/details/b3x14_bn610/civatalar/bossard/1111329/','Bağlantı çubuğunun iki ucu','Katalog eşleşmesi; stok/paket minimumu doğrulanamadı',note='CAD sadeleştirilmiş eksen gösteriyor; standart tam diş vida ancak burç üzerinden taşıyıp dönen parçayı sıkıştırmayan düzen doğrulanırsa kullanılır. Şimdilik sipariş adayı.')
add('FINGER_TUBE','Pirinç boru dış Ø3 / iç Ø2 mm',3,None,'ARGECİMETAL / n11','https://www.n11.com/urun/3-mm-pirinc-boru-ince-boru-ic-cap-2-mm-443201353-26049510','3 adet6 mm uzun parmak burcu','Ürün sayfası var; boy seçeneği ve fiyat teyidi gerekli',note='En kısa stok boyundan kesilir; yüzeyler çapaksız. İçØ2 nominal olduğundan gerçek M2 vida serbest geçişi kontrol edilmeli.')
add('ROD_TUBE','Pirinç boru dış Ø4 / iç Ø3 mm',2,None,'ARGECİMETAL / n11','https://www.n11.com/urun/4-mm-pirinc-boru-ic-cap-3-mm-437662777-26049256','2 adet4 mm uzun çubuk burcu','Ürün sayfası var; boy seçeneği ve fiyat teyidi gerekli',note='En kısa boydan kesilir; içØ3 nominal, vida serbest geçişi kontrol edilir. Kesim/tolerans işi dahil değil.')
add('ELBOW_AXLE','Dirsek ekseni Ø5; CAD gövde boyu65 mm / uç tutma TBD',1,None,'Tornacı / hassas mil tedariki',None,'İki625 rulman arasındaki ana eksen','ÖLÇÜ VE TUTMA DÜZENİ TAMAMLANMADAN SİPARİŞ VERME',note='CAD, kullanılacak standart cıvatanın tam dişsiz boyunu ve somun/segman düzenini tamamlamıyor.65 mm normal M5 vida doğrudan eşdeğer değildir. Sağdaki Ø7 yuva standart M5 somun için yeterli olduğu varsayılamaz.')
add('ELBOW_SLEEVES','Alüminyum basma burcu; dışØ8 / içØ5,3 mm',3,None,'Tornacı',None,'1 adet28 mm +2 adet4 mm','Özel işleme adayı; tolerans/eksen tutma doğrulanmalı',note='Ölçüler CADden. İç bileziğe basıp conta/dış bileziğe sürtmemesi kontrol edilmeli. Rastgele altıgen dişli distans eşdeğer değildir.')
add('ROD_NUT','M3 somun ve ince ayar pulları',1,None,'Cıvatacı',None,'Önkol kuyruk ucunda Ø3,3 geçiş deliğinin karşı tarafı','Tutma/sürtünme düzeni doğrulanmalı',note='Krank ucu insertli, önkol kuyruk ucu insertli değil. Somun adayı1; pul kalınlığı/adedi TBD. Bastırarak mafsalı kilitleme.')
add('FRAME_FIX','M4 taban sabitleme vidaları ve karşılıkları',4,None,'Cıvatacı',None,'100×100 mm taban montaj delikleri','Şasi/tezgâh kalınlığına göre boy TBD',note='4 vida gerekli; boy ve insert/somun tercihi montaj yüzeyine bağlı. Mevcut baskı paketine araç şasisi dahil değil.')
add('CORD','Ø0,8 mm çekme ipi, prototip deneme adayı',3,1,'Yıldız Boncuk','https://yildizboncuk.com/urun/parasut-ipi-siyah-p0033/','Üç ayrı parmak çekme hattı; kesim boyu montajda','Satış sayfası var; stok miktarı doğrulanamadı',70.00,note='1 makara90m; yalnız deneme için gereğinden fazladır, eldeki uygun ipi kullan. Malzeme naylon/plastik karışımı; uzama/aşınma/kuvvet doğrulanmış değildir.3 sayısı hat adedidir, metre değildir.')
add('ELASTIC','Ø1 mm esnek ip — deneme adayı',6,1,'Hobi Dünya','https://www.hobidunya.com/tesbih-malzemeleri/tesbih-ipleri/esnek-misina-lastik-ip.html','3 geri açma +3 esnek dengeleme hattı','Satış sayfası var; stok/fiyat/nihai sertlik doğrulanmadı',note='6 ayrı kısa hat; kesim boyu ve ön germe TBD.1 makara önerisi. Sertlik ve meyve sıkma kuvveti deneyle belirlenir; onaylanmış yay eşdeğeri değil.')
add('PADS','4 mm yumuşak silikon levha veya mevcut TPU',3,None,'GTEEK','https://www.gteek.com/tr/seffaf-gida-guvenli-silikon-levha-40-shore-a-fda-onayli-p869-tr-tr','3 adet yaklaşık4×10×13 mm ped','Sayfa stok gösteriyor; özel kesim/minimum sipariş teyidi gerekli',note='40 Shore A ürün yalnız adaydır. Küçük artık parça iste; tam rulo alma. TPU ile tabla05 basılırsa bu levhayı ayrıca alma. Sabitleme yöntemi/uygun yapıştırıcı ve meyvede iz bırakma testi TBD; gıda teması üretici beyanı ayrıca doğrulanır.')

REUSE=[('MG996R',4),('MG90S',2),('Motorlarla gelen orijinal yıldız ve merkez vidası',6),('Arduino UNO / PCA9685 / HC-05 / kablolar',1)]

# L1.1 supersedes the original candidates above; historic quotes retained only
# where the exact product is unchanged. No unverified price is invented.
ROWS[:]=[r for r in ROWS if r['code'] not in {'ROD_SCREW','ROD_TUBE','ROD_NUT'}]
index={r['code']:r for r in ROWS}
index['I34'].update(required=2,usage='Krank ve önkol arka mafsalı',note='M3×4 insert, uç yüzü yeni yuva yüzeyiyle aynı hizada; ISO7379 omuzu metal yüzüne oturur.')
index['S38'].update(required=2,buy_quantity=6,usage='YALNIZ önkol enine bağı',note='0,5 mm pul ile3,5 mm nominal tutuş. Motor kulaklarında M3×8 KULLANMA.')
index['S310'].update(required=8,buy_quantity=12,usage='4 üst kol bağı +4 motor tablası',note='0,5 mm pul ile4,5 mm nominal insert tutuşu.')
index['S320']['note']='0,5 mm pul ile4 mm nominal tutuş. Eski2,5 mm ara pulları ekleme.'
index['S26']['note']='Yalnız4 mikro motor kulağı vidasında0,3 mm pul kullan; nominal tutuş3,5 mm. Kapaklarda ek pul öngörülmedi.'
index['S28']['note']='0,3 mm pul ile3,7 mm nominal tutuş. Ürün sayfasındaki kopya metin hatası nedeniyle gelen boy8 mm ölçülmeli.'
index['B625']['price_per_pack']=28.99
index['ELBOW_AXLE'].update(part='M5×70 KISMİ DİŞLİ ISO4762/DIN912 vida',buy_quantity=2,supplier='Cıvatacı / Würth ölçü kaynağı',url='https://eshop.wuerth.de/Hexagon-Socket-Head-Cap-Screw-ISO-4762-zinc-plated-109-steel-with-thick-layer-passivation-VZD-SCR-CYL-ISO4762-109-HS4-VZD-M5X70/415055%2070.sku/en/US/EUR/',status='L1.1 nominal ölçü belirlendi; yerel stok doğrulanmadı',note='Boy70, nominal diş22, düz48 mm. Geçiş bölgesi hariç en az47 mm kesintisiz düz mil yüzeyi gerekli. Rulmandan zorlamadan geçmeli. Tam dişli veya M5×65 eşdeğer değil.')
index['ELBOW_SLEEVES'].update(status='L1.1 boy hedefi tanımlı; ilk numunede kontrol',note='DışØ8/içØ5,3; 28±0,05 mm bir adet ve4±0,05 mm iki adet. Yüzler dik, paralel, çapaksız; yalnız iç bileziğe basmalı. Standart dişli distans eşdeğer değil.')
index['FINGER_TUBE'].update(part='Pirinç burç dışØ3 / içØ2,2 × boy6 mm',note='Linkteki boru içØ2 mm HAM MALZEMEDİR; M2 vidaya serbest geçiş için içØ2,2 işlenecek, üç adet6 mm kesilecek. Hazır uyumlu parça diye satın alma.')
add('S36','M3×6 silindirik başlı vida',16,20,'Cıvatacı',None,'Dört MG996R motorun kulakları','L1.1',note='0,5 mm pul ve2,2 mm nominal motor kulağı ile3,3 mm tutuş. Gerçek kulak ölçüsü kontrol edilir.')
add('W3','M3 pul iç3,2/dış7/kalınlık0,5 mm',30,40,'Cıvatacı',None,'16 motor +4 üst bağ +2 ön bağ +4 tabla +4 tutucu','L1.1',note='Kalınlık vida boyu hesabının parçasıdır.')
add('W2','M2 pul iç2,2/dış5/kalınlık0,3 mm',6,10,'Cıvatacı',None,'4 mikro motor +2 bilek','L1.1',note='Diğer M2 kapak/parmak vidalarına bu listede pul eklenmez.')
add('W5','M5 pul iç5,3/dış10/kalınlık1 mm',2,4,'Cıvatacı',None,'Dirsek milinin iki dış yüzü','L1.1',note='DIN125 ölçüsü; birer adet.')
add('N5','M5 DIN985 fiberli kilit somun',1,2,'Cıvatacı',None,'Sağ önkol dışı','L1.1',note='Anahtar ağzı8, yaklaşık yükseklik5 mm. Yeni sağ plaka düz; somun dışarıda erişilebilir.')
add('ROD_SHOULDER','ISO7379-4-M3-6 omuzlu vida',2,3,'Elesa+Ganter / cıvatacı','https://www.elesa.com/siteassets/PDF/TR/ISO%207379.pdf','İki çubuk mafsalı','Ölçü doğrulandı; yerel stok/fiyat doğrulanmadı',note='Düz omuzØ4×6, dişM3×7, başØ7×3 mm. Normal M3×14 veya farklı omuz boyuyla değiştirme.')
add('W4','M4 pul iç4,3/dış9/kalınlık0,8 mm',4,6,'Cıvatacı',None,'Her çubuk mafsalında iki yanda','L1.1',note='Çubuk4 + iki pul1,6 =5,6 mm; omuz6 mm. Nominal dönme boşluğu0,4 mm.')
for row in ROWS:row['order_hold']=False
for code,part,usage in [('ELBOW_SLEEVES','Baskı: PLA dirsek burçları','L1-23:1 adet28mm; L1-24:2 adet4mm; dış8/iç5,3'),('FINGER_TUBE','Baskı: PLA parmak burçları','L1-25:3 adet6mm; dış4,8/iç2,4; yalnız yeni L1-17 parmaklarla')]:
    index[code].update(part=part,usage=usage,buy_quantity=None,supplier='Mevcut filament',url=None,price_per_pack=None,order_hold=True,status='L1.4 BASILACAK; fiziksel doğrulama bekliyor',note='Metal burç alınmayacak, tornacı işi yok. GUNCEL/BASKI/06_PLASTIK_BURCLAR. Yalnız yüksüz uyum denemesi; PLA sünmesi ve sıkma ayarı doğrulanmadı.')
index['FINGER_SCREW']['usage']='Üç parmak; M2x14 vida yeni plastik burcun içinden geçer'
index['FINGER_SCREW']['note']='L1.4 yeni L1-17 parmak ve L1-25 burçla; pul eklenmez. Sıkınca parmak serbest dönmeli; gerçek insert tutuşu kontrol edilmeli.'

index['PADS'].update(part='Baskı: 1mm kavisli TPU iç astar',usage='L1-18; üç yeni kepçe parmağın iç yüzeyi',supplier='Mevcut TPU filament',url=None,buy_quantity=None,price_per_pack=None,order_hold=True,status='L1.5 BASILACAK; fiziksel doğrulama bekliyor',note='05 tablasında üç adet. Eski4mm düz silikon ped kullanılmaz. TPU sertliği, destek sökümü, uygun yapıştırıcı/sabitleme ve meyvede iz bırakma testi TBD; gerçek maliyet ve gıda teması UNVERIFIED.')

# DEC-085: publish the current rigid gripper and standard-screw rod hardware.
ROWS[:]=[r for r in ROWS if r['code'] not in {'ROD_SHOULDER','W4','CORD','ELASTIC','PADS'}]
index={r['code']:r for r in ROWS}
for code,delta in {'S28':6,'S26':4,'I23':6,'I24':4}.items():
    index[code]['previous_required']=index[code]['required']
    index[code]['required']+=delta
    index[code]['usage']+='; DEC-084 dişli tutucu ilave bağlantıları'
index['S310'].update(required=10,usage='4 üst kol bağı +4 motor tablası +2 çubuk mafsalı',note='Çubukta 6mm plastik burç ve0,5mm M3 pul ile nominal3,5mm insert tutuşu. Diğer kullanımda önceki ölçüler korunur.')
index['W3'].update(required=32,usage='Önceki30 bağlantı +2 çubuk mafsalı')
index['I34']['note']='Mevcut M3×4 insert; yüzü yuvayla aynı hizada. Plastik burcun oturma yüzeyi korunur. Gerçek vida tutuşu ve kör dip ölçülmeli.'
index['FINGER_TUBE']['usage']='Mevcut L1-25: üç parmak pivot burcu; yeni RT-FINGER ile tekrar kullanılır'
index['FINGER_SCREW']['note']='Mevcut M2x14 ve L1-25 burçlar DEC-084 tutucuda tekrar kullanılır; fiziksel uyum doğrulanmalı.'
add('ROD_BUSH','Baskı: PLA çubuk mafsal burcu Ø6/3,3 ×6 mm',2,None,'Mevcut filament',None,'L1-26; 09 tablasında iki adet','DEC-085 PHYSICAL VALIDATION REQUIRED',note='Vida metal M3×10; yalnız çevresindeki burç basılır. Yeni L1-15 çubuk gerekir. Sıkma ve PLA sünmesi doğrulanmadı.')
ROWS[-1]['order_hold']=True
for row in ROWS:
    if row.get('url'):row['status']='Önceki kaynak/fiyat kaydı; güncel stok ve fiyat UNVERIFIED'

# DEC-086: two integral scoop gears and circular J1 horn retaining cup.
index={r['code']:r for r in ROWS}
index['I24'].update(required=23,usage='12 yıldız kapağı +4 mikro servo kulağı +2 bilek bağlantısı +4 tutucu köprü ayağı +1 pasif kepçe ekseni')
index['I23'].update(required=6,usage='Yalnız6 rulman kapağı bağlantısı',note='M2L3, mevcut rulman kapağı yuvaları. Yeni tutucuda M2L3 kullanılmaz.')
index['S26'].update(required=24,usage='10 yıldız kapağı +4 mikro servo kulağı +6 rulman kapağı +4 tutucu köprüsü')
index['S28'].update(required=4,usage='2 bilek bağlantısı +2 taban yıldız kapağı',note='Bilekte0,3mm pul korunur; taban kapağında pul eklenmez. Taban kapağı4mm ve nominal4mm diş tutuşu; gerçek kör dip kontrol edilir.')
index['FINGER_SCREW'].update(required=1,part='M2×14 silindir başlı pasif kepçe eksen vidası',usage='TS-BUSH üzerinden pasif dişli kepçe',note='8mm baskı burcu ve3mm köprü sonrası nominal3mm M2L4 insert tutuşu; pul yok. Sıkıldığında kepçe serbest dönmeli.')
index['FINGER_TUBE'].update(required=1,part='Baskı: TS-BUSH kepçe burcu Ø6/2,4 ×8 mm',usage='07 tablasında1 adet; eski L1-25 kullanılmaz',status='DEC-086 BASILACAK; fiziksel doğrulama gerekli',note='Metal boru alınmaz; mevcut PLA ile basılır. Gerçek serbest dönme, sıkma ve sünme denenmeli.')

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    data=dict(revision='DEC-086',date='2026-09-17',scope='ONE ARM; procurement requirements, NOT purchase records',reuse=REUSE,rows=ROWS)
    (OUT/'MALZEMELER.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    totals=defaultdict(float)
    md='# DEC-085 — güncel kol alışveriş listesi\n\n16 Eylül 2026. Çubuk mafsallarında 2 standart M3×10 metal vida +2 M3 pul (0,5mm) +2 basılı L1-26 burç kullanılır. Omuzlu vida ve M4 mafsal pulları artık alınmaz. Dirsek/parmak/çubuk burçları basılır; tornacı işi yok. Yeni dişli tutucu için ip, lastik ve eski TPU astar alınmaz. Önceki kaynak ve fiyatlar güncel teklif veya stok teyidi değildir. Motorlar ve orijinal yıldızları tekrar kullanılır.\n\n| Parça | Bir kolda | Yedekli alım | Kaynak | Kullanıldığı yer |\n|---|---:|---:|---|---|\n'
    for r in ROWS:
        if r['price_per_pack'] is not None and r['buy_quantity'] is not None:totals[r['currency']]+=r['price_per_pack']*r['buy_quantity']/r['pack_quantity']
    cost=dict(revision=data['revision'],date=data['date'],status='PARTIAL CANDIDATE SUBTOTAL ONLY',known_subtotals={k:round(v,2) for k,v in totals.items()},total_try=None,shipping=None,machining=None,exchange_rate=None,excluded=[r['code'] for r in ROWS if r['price_per_pack'] is None or r['buy_quantity'] is None],note='Spare quantities included; TRY/USD separate. No purchase; NOT full assembly cost.')
    (OUT/'MALIYET.json').write_text(json.dumps(cost,ensure_ascii=False,indent=2),encoding='utf-8')
    for r in ROWS:
        link=f"[{r['supplier']}]({r['url']})" if r['url'] else r['supplier']
        md+=f"| {r['part']} | {r['required']} | {r['buy_quantity'] if r['buy_quantity'] is not None else ('BASILACAK' if r['code'] in {'ELBOW_SLEEVES','FINGER_TUBE','ROD_BUSH'} else 'bekle')} | {link} | {r['usage']} |\n"
    md+='\n## Ölçü ve montaj notları\n\n'
    for r in ROWS:md+=f"- **{r['part']}:** {r['note']} Durum: {r['status']}.\n"
    md+='\n## Elden temin\n\n- [Meko Rulman](https://mekorulman.com/iletisim/): İMES A Blok108 Sokak29, Ümraniye;0216 364 63 54.\n- [Karaca Hırdavat](https://www.hirdavatiste.com/iletisim): DES-1 Cad. D02 Blok21, Ümraniye;0531 494 28 79.\n- [Robotizmo](https://www.robotizmo.net/iletisim): Karaköy Tersane Cad. Selanik Pasajı5/B;0212 293 75 74.\n\nAdresler kontrol edildi; bütün ölçülerin mağaza raf stoğu doğrulanmadı. Özellikle omuzlu vida kodunu ve insert dış çap/boyunu telefonla sor.\n\n## Maliyet\n\n'
    md=md.replace('Özellikle omuzlu vida kodunu ve insert dış çap/boyunu telefonla sor.','Insert dış çap/boyunu ve standart vida/pul ölçülerini teyit et.')
    md+=f"Önceki fiyatlarla yedekli kalemler **{totals['TRY']:.2f} TL + {totals['USD']:.2f} USD**; güncel teklif veya tam maliyet değil. Eksikler MALIYET.json içinde. Gerçek stok ve filament maliyeti bilinmiyor. Satın alma yapılmadı.\n\n"
    md+='Adet ve nominal montaj hesabı L1.1 CAD ile eşleştirilir. Baskı çekmesi, gerçek motor kulağı/yıldızı, insert diş derinliği, yatak sıkılığı, kablo/tendon ve yük deneyi fiziksel kontrol gerektirir. Dijital testler dayanım sertifikası değildir.\n'
    md=md.replace('DEC-085','DEC-086').replace('16 Eylül 2026','17 Eylül 2026')
    md+='\nDEC-086: iki kepçeli tutucu. Tabanın yeni çevreleyen kapağında2 M2×8 kullanılır. Eski M2×14lerden yalnız1 adet pasif kepçeye gerekir. M2L4 toplam23, M2L3 toplam6. Önceki yedekli alım adetleri yeterli olabilir; gerçek sahip olunan stok UNVERIFIED.\n'
    (OUT/'SATIN_ALMA_LISTESI.md').write_text(md,encoding='utf-8')
    print(json.dumps(cost,ensure_ascii=False))

if __name__=='__main__':build()

