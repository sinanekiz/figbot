# FIGBOT P0 — önden yönlendirmeli düz-zemin araç ve entegrasyon yerleşimi

Tarih: 2026-08-20  
Durum: `DESIGN CONCEPT — NOT PHYSICALLY VERIFIED`

CAD revizyonu: `REV-C`. Rev-C dört lastiği gerçek 60 mm toplam genişlikte,
lastik/jant/göbek olarak ayrı gösterir; ön kingpin, rot, lineer aktüatör, arka
motor/redüktör ve muhafazaları görünür kılar. Kol geometrisi Waveshare'ın resmî
`RoArm-M3_STEP_260310.zip` dosyasından alınmıştır. 670 mm teker izine sahip
Rev-C, tam direksiyon süpürme boşluğunu hesaplar ve kamerayı iki ayaklı üst
köprüye taşır. Önceki kaba P0 ve Rev-B görselleri aktif tasarım değildir.

## Görev ve sınır

P0 aracı kuru, düz veya düzgün sıkıştırılmış zeminde düşük hızda ilerler. Dört
teker aynı nominal çapta; arka çift tahrikli, ön çift Ackermann bağlantısıyla
yönlendirilmiştir. Kamera öne ve zemine bakar.

`FIGBOT_P0_ROVER.step` ayrıca düşmüş inciri zeminden alacak sökülebilir kolun ve
hemen arkasındaki sepetin **yerleşim zarfını** gösterir. Bu, kolun P0 araç testleri
bitmeden takılacağı anlamına gelmez: DEC-011 gereği araç, kol ve beyin önce ayrı
test edilir. Ağaç dalından meyve koparma kapsam dışıdır.

## Kontrollü başlangıç geometrisi

| Parametre | Başlangıç değeri | Durum |
|---|---:|---|
| Çerçeve dış zarfı | 600 x 450 mm | `ESTIMATE` |
| Teker | 4 x aynı nominal 254 x 60 mm | `SUPPLIER DIMENSION GATE` |
| Düzen | arka 2WD + ön Ackermann | DEC-014 |
| Teker izi / dingil mesafesi | 670 / 430 mm | Rev-C `CALCULATED PACKAGING` |
| Yaklaşık toplam dış genişlik | 730 mm | 670 mm iz + 60 mm lastik |
| Şasi alt açıklığı | 75 mm hedef | `PHYSICAL VALIDATION REQUIRED` |
| Ön direksiyon sınırı | +/-30 derece | `COMMISSIONING GATE` |
| Kol tabanı | X=105, Y=0 mm; ön aksın 110 mm gerisi | Resmî aday STEP / `INCOMING INSPECTION REQUIRED` |
| Sepet | 300 x 270 x 105 mm; alt kot Z=232 mm, dört ayakla akünün üzerinde | `PACKAGING ASSUMPTION` |
| Kamera | X=270, Y=0, Z=575 mm; iki direkli köprü Z=600 mm | `PACKAGING ASSUMPTION` |
| İlk yer toplama bölgesi | X=320..620, Y=-190..190, Z=0..80 mm | `SIMULATION REQUIRED` |
| Faydalı yük rezervi | 20 kg | `PHYSICAL VALIDATION REQUIRED` |
| Yazılım hız sınırı | 0,20–0,50 m/s | Testte kademeli |

Koordinat sistemi `+X ileri, +Y sol, +Z yukarı`dır. Tüm sayılar
`cad/config/parameters.py` üzerinden CAD ve yerleşim JSON'una aktarılır.

## Mekanik mimari

1. Ana çerçeve boy kesilmiş 30x30 Kanal-8 sigma profil, katalog köşebent ve M8
   kanal somunuyla kurulur. Büyük blok CNC veya kaynaklı monokok yoktur.
2. İki 24 V 250 W fırçalı redüktörlü motor, ayrı yataklanan arka tekerleri
   zincirle sürer. Çıkış devri/mili görülmeden dişli delikleri serbest bırakılmaz.
3. Ön teker göbekleri mafsallı porya/kingpin taşıyıcılarında döner. Sağ ve sol
   açıları eşit değildir; iç teker daha fazla döner. Rot kolları ve Ackermann
   noktaları numune porya ölçüsüne göre nihai CAD'de belirlenir.
4. İlk direksiyon kuvvet elemanı 24 V, 100 mm strok, geri beslemeli lineer
   aktüatör sınıfıdır. F1Depo'daki 1000 N / 12 mm/s / IP43 aday yalnız boyut ve
   maliyet başlangıcıdır; dış ortam, boşluk, gerçek strok ve görev çevrimi test
   edilmeden seçilmiş parça sayılmaz.
5. Satın alınmış kısa kol ön aksın biraz gerisindeki merkezî kanala sökülür-takılır
   bağlanır. Sepet hemen arkasındadır; kol ürünü alıp kısa bir geri dönüşle sepete
   bırakır. Uzun arka kol veya sağ-sol asimetrik yerleşim kullanılmaz.
6. Akü arka güvertede ve sepetin altında, elektronik kutu erişilebilir yan bölgede;
   zincir aktarmaları tamamen kapalıdır. Kamera görüşü kol ve sepetle birlikte
   fiziksel kalibrasyonda kontrol edilir.
7. Akü merkezi `(X=-125,Y=0,Z=166)` mm'dir; 260 x 175 x 110 mm zarf, tepsi ve iki
   kayışla gösterilir. Elektronik tepsi `(X=160,Y=-120)` mm'de 200 x 140 x 70 mm
   servis zarfıdır; Pi 5, ESP32, MDDS30, DC/DC ve çekiş kontaktörü ayrı gövdeler
   halinde görünür. Kesin delikler ancak ürün kodları dondurulunca işlenir.

## Direksiyon ve sürüş kontrol zinciri

```text
Raspberry Pi görev hızı + dönüş hızı
  -> software/rover/ackermann.py
      -> sol/sağ ön teker açı hedefi -> ESP32 -> direksiyon sürücüsü -> aktüatör
      -> sol/sağ arka teker hızı     -> ESP32 -> MDDS30 -> 2 x 250 W motor

Direksiyon açı sensörü + teker enkoderleri -> ESP32 kapalı çevrim
Tampon / RC failsafe / E-stop             -> güvenli duruş
```

Seçilen geometri yerinde dönüş yapamaz. Sıfır ileri hızla dönüş isteği veya geçersiz
geometri `stopped_command` üretir. Donanımsal E-stop yazılıma bağlı olmadan çekiş
kontaktörünü bırakır; direksiyonun enerji kesilince güvenli mekanik durumda kalması
ayrıca doğrulanır.

## Üretilecek dijital çıktılar

- `cad/assembly/FIGBOT_P0_ROVER.step`: çok-gövdeli yerleşim montajı
- `cad/assembly/FIGBOT_P0_ROVER.FCStd`: FreeCAD içe aktarma doğrulaması sonrası
- `viewer/public/models/FIGBOT_P0_ROVER.glb`: isimlendirilmiş web/sanal model
- `renders/FIGBOT_P0_ROVER_*.png`: üst, ön, yan ve izometrik kontrol resimleri
- `cad/rover/FIGBOT_P0_LAYOUT.json`: koordinatlar ve hareket mimarisi
- `reports/P0_REV_C_PACKAGING_CLEARANCE_REPORT.md`: bileşen koordinatları ve sayısal boşluk raporu
- `simulation/ros2/figbot_description/urdf/figbot_p0_rover.urdf.xacro`: dört teker ve direksiyon eklemleri

STEP üzerindeki porya, rot, aktüatör ve hazır kol geometrileri kontrollü zarftır;
delik yerleri veya imalat resmi değildir.

## Satın alma ve doğrulama kapıları

- `P0-GATE-01`: motor çıkış devri, sürekli tork, stall akımı, sıcaklık, görev çevrimi ve mil resmi.
- `P0-GATE-02`: seçilen dört tekerin aynı lastik/jant olduğu; göbek deliği ve yük değeri.
- `P0-GATE-03`: ön porya/kingpin, rot başı ve direksiyon kolunun ölçülü numunesi.
- `P0-GATE-04`: aktüatör gerçek strok, potansiyometre/enkoder çıkışı, boşluk, hız ve IP testi.
- `P0-GATE-05`: tam turda lastik-şasi, rot, kol, kamera ve zincir muhafazası çarpışma kontrolü.
- `P0-GATE-06`: 20 kg yükle fren, E-stop, 60 dakika çalışma, motor ve aktüatör sıcaklık testi.
- `P0-GATE-07`: kol takılıyken statik devrilme, ani fren, öne uzanma ve sepet dolu kütle merkezi testi.
- `P0-GATE-08`: gerçek incirde kavrama, düşürme, ezme ve zeminden alma başarı testi.

## Maliyet sınırı

Aktif araç BOM'u dört eş teker ve ön direksiyon parçalarıyla yaklaşık
**82.154,17 TL**'dir. Bu, yalnız P0 araç/temel beyin maliyetidir; hazır kol ve
entegrasyon parçaları ayrı P1/P3 maliyetidir. Önceki 71.435,37 TL değer iki casterlı
eski DEC-012 düzenine aitti ve artık aktif değildir. Fiyatlar teklif değil,
2026-08-20 tarihli web fiyatı/`ESTIMATE` karışımıdır.
