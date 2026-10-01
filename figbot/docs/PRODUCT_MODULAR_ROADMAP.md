# FIGBOT düşük maliyetli modüler ürün yol haritası

Tarih: 2026-08-20  
Durum: `CONCEPT BASELINE — PHYSICAL VALIDATION REQUIRED`

## Yönetici kararı

FIGBOT tek seferde arazi aracı, robot kol, otonom navigasyon, hassas algılama ve
ürün güvenliği çözen tek bir prototip olarak bütçelenmeyecektir. Ürün üç bağımsız
modül ve bir entegrasyon aşaması olarak geliştirilecektir:

| Aşama | Ürün | İlk başarı ölçütü | Tek-adet hedef bütçe |
|---|---|---|---:|
| P0 | Düz-zemin kameralı, önden yönlendirmeli sürüş platformu | Manuel kamera sürüşü, Ackermann dönüş, duruş, hat/AprilTag takibi | yaklaşık 82.000 TL |
| P1 | Sabit tezgâh robot kolu | Tek inciri algıla, kavra ve kasaya bırak | 25.000–45.000 TL |
| P2 | Modüler beyin | Araç ve kolu aynı görev makinesiyle yönet; log ve watchdog | 10.000–25.000 TL ek |
| P3 | Birleşik saha prototipi | P0+P1+P2; kademeli dış ortam ve arazi yükseltmesi | Test sonuçlarına göre |

Bu değerler perakende web fiyatları ve `ESTIMATE` girdileridir; teklif değildir.

## P0 neden önce gelir?

- Araç yürüyemiyorsa kol ve incir yapay zekâsı için saha verisi toplanamaz.
- Arkadaki iki teker tahrik edilir; öndeki iki eş teker Ackermann geometrisiyle yönlendirilir. Bu nedenle araç yerinde dönmez.
- RTK, LiDAR, Jetson, Pixhawk ve robot kol P0 maliyetine dahil edilmez.
- Kamera, motor sürücüsü, akü, E-stop ve temel kontrol ayrı ayrı test edilir.
- P0 şasisi sonraki aşamada kol taşıyabilecek 20 kg faydalı yük rezerviyle tasarlanır;
  bu kapasite henüz doğrulanmış değildir.

## Modül arayüzleri

| Arayüz | P0 | P1/P2 geleceği |
|---|---|---|
| Ana enerji | 24 VDC | Kol için ayrı sigortalı 12 V DC/DC eklenebilir |
| Düşük seviye kontrol | ESP32; PWM/direction, encoder, watchdog | Aynı seri/CAN mesaj şeması korunur |
| Yüksek seviye kontrol | Raspberry Pi 5; kamera ve görev | Gerekirse yalnız bilgisayar Jetson'a yükseltilir |
| Mekanik | 600 x 450 mm başlangıç zarfı; 30x30 profil; dört eş 10 inç teker | Ön aks gerisinde standart M8 kanala bağlı sökülebilir kol tablası; hemen arkasında sepet |
| Güvenlik | Donanımsal E-stop motor kontaktörünü keser | Kol enerji kesmesi ayrı kontaktör dalına eklenir |

## Ürünleştirme ilkesi

Geliştirme aletleri, ilk numune yedekleri, dış mühendislik hizmeti ve risk
kontenjanı araç başı malzeme maliyetine yazılmayacaktır. Bunlar ayrı `NRE/AR-GE`
bütçesinde tutulur. Satış maliyeti yalnız araçta kalan parça, montaj işçiliği,
test, ambalaj, garanti rezervi ve sevki içerir.
