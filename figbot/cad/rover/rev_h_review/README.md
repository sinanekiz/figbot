> **DEC-039: Tam kol ve kıskaç baskısı beklemede; iç montaj hataları bulundu. Güncel inceleme: cad/prototype_arm/aero_v2/SON_BASKI_KONTROLU.md.**

# FIGBOT Rev-H2 — çift kol, bağlı yürüyen aksam, 15° sepet

Güncel istek iki ön tekerin üstüne kol ve daha alçak sepet girişidir. Kolun mevcut Aero V2 baskı parçaları değiştirilmedi; aynı parçalar iki konumda kullanılıyor. Sağ kol, üretilemeyecek ayna parçalarla değil aynı kolun ters yaw yönü ve farklı montaj konumuyla gösterildi. Tasarım iki kolludur; satın alma kaydı değildir.

## Güncel yerleşim

- Kol tabanları: (380, +/-415, 280) mm. Nominal 254 mm lastik üstünden taban seviyesine 26 mm. Bu sayı tüm parçaların minimum çalışma açıklığı değildir.
- Sepet tabanı: 15°, 600 x 660 mm yatay izdüşüm. Arka 145 mm, ön 305,77 mm. Eski 30° modelin önü 486,41 mm idi; giriş 180,64 mm alçaldı. Arkadaki 5 mm artış redüktörlere yer açar.
- Sepet giriş dudağı 95 mm öne uzanır. Örnek bırakma noktası 610 yerine 440 mm yüksekte. Gerçek atış/hasar/kayma ölçülmedi.
- Kamera: (330,0,240) mm, ön girişin altında. Batarya, bilgisayar ve güç elektroniği daha alçak sepetin altına yeniden yerleştirildi. Hacimler seçilmiş ürün ölçüsü değildir; kontrol edilmelidir.

## Yürüyen aksam

- Arka iki teker ayrı redüktörlü DC motorlarla sürülüyor. Modelde motor, redüktör, çıkış mili, basamaklı kaplin, iki yatakla desteklenen mil, kama, teker göbeği, rondela ve somun birbirine bağlı.
- Teker yükü doğrudan motor çıkış yatağına bırakılmıyor: her arka milde iki ayrı şasiye bağlı yatak var.
- Ön tekerler serbest dönen çift rulmanlı göbeklerde. Mafsal taşıyıcıları, dikey direksiyon pimleri, direksiyon kolları, rot ve lineer aktüatörün düz konumdaki bağlantıları gösteriliyor.
- Ön kolun eski dikmesi lastikten geçiyordu. Yeni dikmeler tekerin gerisinde; üst taşıyıcılar lastiğin üzerinden geçiyor. Arka yatak konsolları şasiye, motorlar şekilli beşiklere bağlandı. Güverteye motor servis cepleri açıldı.
- Jantlar, göbeklere bağlı altı kollu yapıda; dış jant halkası lastik oturma yüzeyine ulaşıyor. Tekerler artık boşlukta bağımsız şekiller olarak durmuyor.

## Doğrulamanın kapsamı

`REVIEW.json` iki kolun üç örnek pozunu ve 18 ara poz kontrolünü içerir. `RUNNING_GEAR_REVIEW.json` motor-teker bağlantı boşluklarını, yürüyen aksamın sepet/elektronik/kamera ile çakışma kontrolünü ve her ön lastiğin -30/-15/0/15/30 derece konumlarındaki hacim kontrolünü içerir. Bu son kontrol, rot/aktüatörün tam hareket çözümü değildir.

Bütün kontroller dijital geometridir. Motor/redüktör, mil, rulman, kama, cıvata, motor gücü, aktüatör stroku, frenleme, imalat toleransı ve taşıma kapasitesi UNVERIFIED / PHYSICAL VALIDATION REQUIRED. Gerçek parçalar seçilmeden bu geometriden araç imal edilmemeli.

Sabit bileğin örnek yerden alma pozunda yaklaşık 69,8° eğik olması ve en alt parçanın düz zeminden sadece 5,6 mm yüksekliği devam ediyor. Gerçek incir kavrama, yük altında hız, kol iç çarpışmaları, kablolar ve engebeli arazi doğrulanmadı. İki kolun aynı anda çalışması için yazılım sınırları ayrıca uygulanmalıdır.

## Görüntüleme ve dosyalar

Yerel sayfa: http://127.0.0.1:5175/rev-h.html . Yerden alma / yükseltme / bırakma menüsü ve Alt aksamı göster seçeneği bulunur.

- pickup.glb, lift.glb, release.glb: çift kollu renkli pozlar.
- FIGBOT_REV_H_REVIEW.step: güncel genel montaj.
- layout_section.png: 15° sepet ve yeni yükseklikler.
- review_fixed.urdf + review_scene.stl: sabit inceleme sahnesi, kontrol modeli değil. STL baskı siparişine verilmemeli.
- FIGBOT_REV_H_REVIEW_NOT_FOR_PRINT.zip: yerleşim inceleme paketi.

Mevcut tek kol baskı paketi ayrı yerde korunur: cad/prototype_arm/aero_v2/FIGBOT_MG996R_AERO_V2_FULL_BENCH_PROTOTYPE_STL.zip . DEC-039 tam set baskı hazırlığı değerlendirmesini düzeltir; DEC-038 yalnızca araç yerleşimini tanımlar.
