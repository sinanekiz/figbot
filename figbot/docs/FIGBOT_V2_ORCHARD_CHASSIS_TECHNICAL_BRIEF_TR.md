# FIGBOT V2 Bahçe Şasisi — Teknik Görselleştirme ve Ön Tasarım Brifi

Belge kimliği: `FIGBOT-V2-CHASSIS-CONCEPT-01`  
Tarih: `2026-08-27`  
Dil: Türkçe  
Durum: **ÖN KONSEPT / ÜRETİM İÇİN SERBEST BIRAKILMADI / FİZİKSEL DOĞRULAMA GEREKLİ**

## 1. Bu belgenin amacı

Bu belge, FIGBOT kuru incir toplama robotunun önerilen arazi şasisini:

1. başka bir ChatGPT veya görsel üretim sistemine eksiksiz tarif etmek,
2. izometrik görünüş, teknik görünüş ve patlatılmış montaj görselleri üretmek,
3. tedarikçi parçaları seçilmeden önce mekanik yerleşimi tartışmak

için hazırlanmıştır.

Bu belge bir imalat resmi, dayanım onayı veya satın alma izni değildir. Aşağıdaki
`GÖRSELLEŞTİRME NOMİNALİ` değerleri tutarlı resim üretmek içindir. Nihai delikler,
motor bağlantıları, süspansiyon pivotları, batarya kutusu ve yük kapasitesi;
tedarikçi STEP dosyaları, bahçe ölçümü ve fiziksel test olmadan dondurulamaz.

Mevcut FIGBOT P0 Rev-C şasisi yaklaşık 600 x 450 mm çerçeve ve 10 inç tekerli
ayrı bir düz-zemin prototipidir. Bu V2 belgesi P0 temel çizgisini değiştirmez.

## 2. Görev tanımı

Araç, incir bahçesinde kuru ve hurda incirleri yerde tespit eden kamera ile
çalışacak; kol ile inciri yerden alıp şasi üzerindeki yumuşak sepete bırakacaktır.
Şasi düşük hızda ilerleyecek, incir bulunan teker koridoruna girmeden önce
duracak ve inciri toplayacaktır.

Temel öncelikler:

- düşük maliyet,
- standart ve değiştirilebilir parçalar,
- yüksek yerden açıklık,
- alçak ağırlık merkezi,
- kolay tamir,
- toprakta yeterli çekiş,
- incir üzerinde pivot/tank dönüşü yapmama,
- kol, batarya, sepet ve kameranın açık yük yollarıyla bağlanması.

## 3. Koordinat sistemi

Tüm koordinatlar milimetredir.

- Orijin: zeminde, dört tekerin oluşturduğu dikdörtgenin geometrik merkezi.
- `+X`: aracın ileri yönü.
- `+Y`: aracın sol tarafı.
- `+Z`: zeminden yukarı.
- Ön tekerler: pozitif X tarafında.
- Kol: şasinin ön-orta bölümünde.
- Sepet: kolun hemen arkasında.
- Batarya: merkezde ve mümkün olan en alçak güvenli konumda.

## 4. Dış görünüş ve tasarım dili

Şasi ağır bir askerî araç gibi değil, kompakt bir tarım robotu gibi görünmelidir.
Ana görünüş özellikleri:

- dört büyük, havalı ve düşük basınçlı arazi lastiği,
- palet veya Mecanum teker yok,
- ana gövde 40 x 80 mm alüminyum sigma profillerden cıvatalı dikdörtgen,
- her köşede ayrı motor-teker ve salıncak modülü,
- her köşede küçük ATV/go-kart tipi yay-amortisör,
- düz, değiştirilebilir alt koruma plakası,
- ön-ortada sökülebilir robot kol kaidesi,
- kaidenin arkasında geniş ağızlı yumuşak sepet,
- iki direkli kamera köprüsü ve ileri-aşağı bakan kamera,
- kapalı batarya kutusu ve kapalı elektronik kutusu,
- iki erişilebilir kırmızı acil durdurma butonu,
- açıkta zincir, kayış, kablo veya korunmasız elektronik bulunmaması.

Renk önerisi yalnız görselleştirme içindir:

- alüminyum profiller: doğal eloksal/gümüş,
- koruma plakaları ve elektronik kutusu: mat koyu gri,
- güvenlik parçaları: sarı,
- acil durdurma butonları: kırmızı,
- sepet: açık bej veya turuncu yumuşak astarlı,
- lastikler: siyah.

## 5. Çizim için nominal geometri

Bu bölümdeki sayılar **GÖRSELLEŞTİRME NOMİNALİDİR**. Görsellerin birbirini
tutması için aynen kullanılmalıdır; imalat ölçüsü olarak kabul edilmemelidir.

| Özellik | Nominal değer | Durum |
|---|---:|---|
| Toplam lastikten lastiğe uzunluk | 960 mm | GÖRSELLEŞTİRME NOMİNALİ |
| Toplam lastikten lastiğe genişlik | 800 mm | GÖRSELLEŞTİRME NOMİNALİ |
| Ana profil çerçevesi | 720 x 520 mm | GÖRSELLEŞTİRME NOMİNALİ |
| Dingil mesafesi | 560 mm | GÖRSELLEŞTİRME NOMİNALİ |
| Teker merkez izi | 680 mm | GÖRSELLEŞTİRME NOMİNALİ |
| Teker zarfı | çap 400 x genişlik 120 mm | GÖRSELLEŞTİRME NOMİNALİ; kesin SKU TBD |
| Teker merkezi Z | 200 mm | GÖRSELLEŞTİRME NOMİNALİ |
| Alt koruma altında statik açıklık | 200 mm | HEDEF; yüklü test gerekli |
| Ana profil | 40 x 80 mm | ÖNERİLEN STANDART SINIF |
| Ana çerçeve alt kotu | Z = 210 mm | GÖRSELLEŞTİRME NOMİNALİ |
| Ana çerçeve üst kotu | Z = 290 mm | GÖRSELLEŞTİRME NOMİNALİ |
| Normal yazılım hız sınırı | 0,15–0,50 m/s | HEDEF; fren testi gerekli |

### 5.1 Ana nokta koordinatları

| Parça / nokta | X | Y | Z | Açıklama |
|---|---:|---:|---:|---|
| Ön-sol teker merkezi | +280 | +340 | 200 | Nominal teker zarfı |
| Ön-sağ teker merkezi | +280 | -340 | 200 | Nominal teker zarfı |
| Arka-sol teker merkezi | -280 | +340 | 200 | Nominal teker zarfı |
| Arka-sağ teker merkezi | -280 | -340 | 200 | Nominal teker zarfı |
| Kol kaidesi merkezi | +170 | 0 | 300 | Profil üstüne oturan sökülebilir adaptör |
| Sepet merkezi | -150 | 0 | 445 | Sepet hacminin yaklaşık merkezi |
| Kamera optik merkezi | +355 | 0 | 720 | İleri-aşağı bakış |
| Batarya kutusu merkezi | -80 | 0 | 300 | Çerçeve içinde/alçakta |
| Elektronik kutusu merkezi | +80 | -175 | 365 | Sağ servis tarafı |

### 5.2 Üst ekipman zarfları

| Ekipman | Nominal zarf | Konum / not |
|---|---|---|
| Kol adaptör plakası | 160 x 160 x 10 mm | X=+170, Y=0; delik düzeni seçilen kola göre TBD |
| Kol hareket hacmi | 650 mm yarıçaplı yarım-küre yaklaşımı | Çizim kolaylığı için; gerçek kol modeliyle çarpışma analizi gerekli |
| Sepet | 380 x 360 x 250 mm | Kolun arkasında; geniş ağızlı ve yumuşak astarlı |
| Batarya kutusu | 400 x 260 x 150 mm | 48 V sınıfı için yer tutucu; kapasite ve SKU TBD |
| Elektronik kutusu | 260 x 180 x 140 mm | Toz/sıçrama korumalı; konektörler servis tarafında |
| Kamera köprüsü dış genişliği | 440 mm | İki dikey direk ve çapraz destek |
| Kamera yüksekliği | 720 mm optik merkez | Gerçek FOV ve titreşim testi gerekli |

## 6. Ana mekanik mimari

### 6.1 Çerçeve

- İki adet boyuna 40 x 80 mm ağır/kapalı sigma profil.
- En az üç adet enine 40 x 80 mm profil: ön, orta ve arka.
- Birleşimler katalog köşebent, T-somun ve cıvatalı bağlantı plakalarıyla yapılır.
- Ana gövde kaynaklı tek parça yapılmaz; hasarlı profil sahada değiştirilebilir.
- Bağlantı plakaları 6–8 mm 5083, 5754 veya 6061 alüminyum düz plaka sınıfıdır.
- Kesin alaşım, plaka kalınlığı ve cıvata sınıfı `TBD — MEKANİK İNCELEME GEREKLİ`.

### 6.2 Teker ve tahrik

- Dört tekerden çekiş ön konseptidir.
- Referans motor sınıfı: 15–16 inç, 48 V, 250–500 W BLDC göbek motoru.
- Her motor enkoderli olmalı; kesin tip, çözünürlük ve haberleşme protokolü TBD.
- Toplam sürekli motor gücü hedef sınıfı 1–2 kW'tır; gerçek güç, eğim ve termal
  test yapılmadan yeterli kabul edilmez.
- Lastik, geniş ve düşük basınçlı tarla deseni olmalı; teslim edilen gerçek genişlik
  ve yuvarlanma yarıçapı ölçülmelidir.
- Araç incir bölgesinde kendi ekseni etrafında skid/pivot dönüş yapmamalıdır.

### 6.3 Süspansiyon

- Her köşede ayrı salıncak ve katalog yay-amortisör gösterilir.
- Amortisör üst bağlantısı ana çerçeveye, alt bağlantısı salıncağa bağlanır.
- Görselde bütün pivotlar, cıvatalar ve yük yolları görünür olmalıdır.
- Salıncak boyu, pivot çapı, yay katsayısı, strok ve tam yükte çökme miktarı TBD'dir.
- Motor kablosu tam süspansiyon hareketinde gerilmemeli ve lastiğe sürtmemelidir.

### 6.4 Alt koruma

- Ana çerçevenin altında sökülebilir düz koruma plakası bulunur.
- Aday malzeme: 3 mm 5754 alüminyum veya 6 mm HDPE.
- Plakanın altında vida başı, kablo veya batarya çıkıntısı gösterilmez.
- En düşük nokta hedefi nominal Z=200 mm'dir.

## 7. Yerleşim mimarisi

### 7.1 Robot kolu

- Kol ön-ortada, sökülebilir düz adaptör plakası üzerinde gösterilir.
- Kol tabanı doğrudan enine ve boyuna profillere yük aktaran plakaya bağlanır.
- Kol yalnız ince üst kapak sacına bağlanmış gibi çizilmez.
- Görsel kol yaklaşık 560–605 mm erişim sınıfında dört veya beş eksenli kompakt
  bir toplama kolu olabilir.
- Uçta küçük, yumuşak silikon parmaklı incir tutucu gösterilir.

### 7.2 Sepet

- Sepet kolun hemen arkasındadır; kolun uzun geri hareket yapması gerekmez.
- Ağız geniş, iç yüzey yumuşak ve düşme yüksekliği azdır.
- Sepet dört dikme veya belirgin bir taşıyıcı çerçeveyle ana şasiye bağlanır.
- Görselde sepet havada yüzüyor gibi çizilmez.

### 7.3 Batarya ve elektronik

- Batarya araç merkezine yakın ve alçakta yerleştirilir.
- Batarya iki mekanik kayış/kelepçe ve kapalı bir tepsiyle tutulur.
- Elektronik kutusu motor sıçrama bölgesinden uzakta, servis kapağı erişilebilir konumdadır.
- Yüksek akım motor kabloları kamera/enkoder kablolarından ayrı güzergâhta gösterilir.
- Batarya kimyası, kapasitesi, BMS ve çalışma süresi TBD'dir.

### 7.4 Kamera

- Kamera, iki dikmeli ve çapraz destekli rijit bir köprü üzerindedir.
- Kamera aracın önündeki zemine ve iki gelecek teker koridoruna bakar.
- Kamera bağlantısı dekoratif ince bir çubuk değildir; titreşime dayanacak üçgenli
  destekleri bulunur.
- Optik eksen görselde yaklaşık 35–50 derece aşağı eğimli gösterilebilir;
  kesin açı kalibrasyon ve FOV testinden sonra dondurulur.

## 8. Elektrik ve güvenlik görünür öğeleri

Görsellerde aşağıdakiler bulunmalıdır:

- iki kırmızı mantar tip acil durdurma butonu,
- ana batarya sigortası ve kontaktör kutusu,
- fiziksel ana güç ayırıcısı,
- ön ve arka durum lambaları,
- kablo rakorları ve kapalı konektörler,
- tampon/temas şeridi için ayrılmış ön bağlantı,
- motor enerjisini yazılımdan bağımsız kesen güvenlik zinciri için kutu.

Tam bir otonom emniyet sistemi doğrulanmış değildir. Çizimde LiDAR, GNSS veya başka
sensörler gösterilirse bunlar `OPSİYONEL / PAKETLEME ZARFI` olarak etiketlenmelidir.

## 9. Görsel üretimde yapılmaması gerekenler

- Paletli araç çizme.
- Mecanum veya küçük depo/AGV tekeri kullanma.
- Altı teker veya üç teker ekleme.
- Kabinsiz ATV, traktör ya da oyuncak araba görünümü verme.
- Kaynaklı boru kafes ana şasi çizme.
- Süspansiyonsuz, tekerleri doğrudan profile yapıştırılmış gösterme.
- Bataryayı yüksek bir kuleye koyma.
- Sepeti kolun önüne veya kameranın görüşünü kapatacak yere koyma.
- Robot kolu yalnız ince bir sac kapağa bağlama.
- Açıkta dönen zincir, kayış veya korunmasız yüksek akım terminali çizme.
- Ölçü tablosuyla çelişen oranlar üretme.
- Belirsiz teknik değerleri üretim için doğrulanmış gibi etiketleme.

## 10. Görsel üretim için makine-okunabilir özet

```yaml
project: FIGBOT
concept: V2_ORCHARD_CHASSIS_CONCEPT_01
status: CONCEPT_ONLY_PHYSICAL_VALIDATION_REQUIRED
units: mm
coordinate_system:
  origin: ground_center_of_wheel_rectangle
  x_positive: forward
  y_positive: left
  z_positive: up
visualization_nominal:
  overall_footprint: {length: 960, width: 800}
  frame: {length: 720, width: 520, profile: "40x80 aluminium T-slot"}
  wheelbase: 560
  wheel_track: 680
  wheels:
    count: 4
    type: pneumatic_low_pressure_field_tread
    diameter: 400
    width: 120
    centers:
      front_left:  [280, 340, 200]
      front_right: [280, -340, 200]
      rear_left:   [-280, 340, 200]
      rear_right:  [-280, -340, 200]
  ground_clearance_under_guard: 200
  drive: {layout: 4WD, motor_class: "48V 250-500W BLDC hub with encoder", exact_sku: TBD}
  suspension: independent_trailing_arm_with_compact_coilover_each_corner
  arm_mount:
    center: [170, 0, 300]
    adapter_plate: [160, 160, 10]
    arm_reach_class: "560-605"
  basket:
    center: [-150, 0, 445]
    envelope: [380, 360, 250]
    lining: soft_padded
  battery:
    center: [-80, 0, 300]
    envelope: [400, 260, 150]
    voltage_class: 48V
    chemistry_capacity: TBD
  electronics:
    center: [80, -175, 365]
    envelope: [260, 180, 140]
  camera:
    optical_center: [355, 0, 720]
    mount: two_post_braced_bridge
    direction: forward_down
  safety_visible:
    emergency_stops: 2
    main_fuse: true
    contactor: true
    master_disconnect: true
forbidden_visual_features:
  - tracks
  - mecanum_wheels
  - small_indoor_AGV_wheels
  - floating_arm_mount
  - floating_basket
  - exposed_chain_or_belt
  - exposed_high_current_terminals
```

## 11. ChatGPT'ye verilecek ana çizim komutu

Aşağıdaki komut bu belgenin tamamıyla birlikte görsel üreten ChatGPT'ye verilebilir:

> Ekli `FIGBOT V2 Bahçe Şasisi — Teknik Görselleştirme ve Ön Tasarım Brifi`
> belgesini tek teknik kaynak olarak kullan. Önce belgede çelişki olup olmadığını
> kontrol et; belirsiz değerleri uydurma. `GÖRSELLEŞTİRME NOMİNALİ` ölçülerini
> oran ve yerleşim için aynen kullan. Aynı tasarımın birbiriyle tutarlı beş ayrı
> görselini üret: (1) önden-sol üstten izometrik ürün görünüşü, (2) üst-ön-yan
> ortografik teknik pafta, (3) motor-teker, salıncak, amortisör, profil, alt koruma,
> batarya, elektronik kutusu, kol kaidesi, sepet ve kamera köprüsünü gösteren
> patlatılmış montaj, (4) alttan tahrik ve koruma görünüşü, (5) incir bahçesinde
> çalışma yerleşimi. Palet, Mecanum veya küçük AGV tekeri kullanma. Bütün taşıyıcı
> parçaların şasiye bağlantısını göster. Teknik paftada milimetre ölçüleri ve
> `CONCEPT ONLY — PHYSICAL VALIDATION REQUIRED` uyarısını yaz.

## 12. Ayrı görsel komutları

### 12.1 İzometrik mühendislik görseli

> Beyaz arka plan üzerinde FIGBOT V2 kuru incir toplama robotunun temiz, gerçekçi
> CAD tarzı izometrik mühendislik görselini çiz. Dört adet 400 x 120 mm havalı
> tarla lastiği, 680 mm teker izi, 560 mm dingil mesafesi, 720 x 520 mm 40x80
> alüminyum profil çerçeve, dört bağımsız salıncak ve yay-amortisör kullan. Ön-ortada
> sökülebilir robot kolu, hemen arkasında yumuşak sepet, merkezde alçak batarya,
> iki direkli destekli kamera köprüsü ve ileri-aşağı bakan kamera göster. Kablolar
> korumalı, bağlantılar cıvatalı ve mekanik olarak inandırıcı olsun. Palet ve
> Mecanum teker kullanma. Görselin altında `FIGBOT V2 CONCEPT — NOT FOR PRODUCTION`
> yazsın.

### 12.2 Ölçülü teknik pafta

> FIGBOT V2 şasisinin üst, sol yan, ön ve izometrik görünüşlerini aynı A3 yatay
> teknik paftada çiz. Milimetre cinsinden toplam 960 x 800 mm ayak izini, 560 mm
> dingil mesafesini, 680 mm teker izini, 400 mm teker çapını, 120 mm teker
> genişliğini ve 200 mm alt açıklığı ölçülendir. Koordinat eksenlerini +X ileri,
> +Y sol, +Z yukarı olarak göster. Kol, sepet, batarya, elektronik kutusu ve kamera
> merkezlerini belge koordinatlarına göre işaretle. Üretim toleransı uydurma;
> `VISUALIZATION NOMINAL / PHYSICAL VALIDATION REQUIRED` notunu ekle.

### 12.3 Patlatılmış montaj

> FIGBOT V2 şasisinin numaralı patlatılmış montaj görünüşünü çiz. Ana 40x80 profil
> çerçeveyi merkezde tut; dört motorlu tekeri, dört salıncağı, dört amortisörü,
> 6–8 mm düz bağlantı plakalarını, alt koruma plakasını, batarya tepsisini,
> elektronik kutusunu, kol adaptörünü, sepet taşıyıcılarını ve kamera köprüsünü
> ayrı katmanlar halinde göster. Her parçaya ok ve kısa Türkçe etiket ekle. Özel
> üç boyutlu CNC bloklar çizme; standart profil ve düz lazer kesim plakalar kullan.

### 12.4 Bahçede çalışma görseli

> FIGBOT V2 robotunu kuru incir bahçesinde düşük hızda çalışırken göster. Kamera
> yerden yaklaşık 720 mm yüksekte ileri-aşağı bakıyor olsun. Robot kolu ön tekerlerin
> önündeki kuru inciri yumuşak parmaklarla alsın ve arkasındaki sepete bıraksın.
> Tekerler incirlerin üzerinden geçmesin; algılanan teker koridorları ince yarı
> saydam yeşil şeritlerle gösterilsin. Araç kompakt, yaklaşık 800 mm geniş ve dört
> büyük havalı lastikli olsun. Görsel gerçekçi fakat ürün henüz prototip durumunda
> görünsün; insan veya hayvan yakınında otonom çalışma gösterme.

## 13. Çizimden imalata geçiş kapıları

Bu konseptten üretim CAD'ine geçmeden önce aşağıdakiler tamamlanmalıdır:

1. En dar bahçe geçidi, maksimum yan/uzunlamasına eğim, taş ve çukur ölçümü.
2. Dört teker adayının kesin SKU, STEP, ağırlık, tork, enkoder, kablo ve IP verisi.
3. Seçilen amortisörün ölçülü çizimi, yay katsayısı ve yüklü çökme testi.
4. Batarya SKU, kütle, BMS, akım, bağlantı ve muhafaza ölçüsü.
5. Kolun kesin taban delikleri, kütlesi, maksimum erişimi ve dinamik taban momenti.
6. Statik yük, çekiş, fren, eğim, termal, titreşim ve devrilme testleri.
7. Tam yüklü minimum yerden açıklık ölçümü.
8. Kamera görüş alanı ve iki teker koridoru için gerçek bahçe testi.
9. Acil durdurma, kontaktör, sigorta ve kontrollü yeniden başlatma doğrulaması.
10. Nihai kritik ölçülerin `DECISIONS.md`, `ASSUMPTIONS.md`, ana CAD parametreleri
    ve BOM içerisinde kontrollü olarak yayımlanması.

Bu kapılar kapanmadan oluşturulan görseller ve CAD modelleri yalnız konsepttir.
