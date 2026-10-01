# Klipsli servo başlığı bağlantısı — SNAP-01

Tarih: 2026-09-07. Durum: KAVRAM / PHYSICAL VALIDATION REQUIRED.
Bu plan bir STL veya baskı onayı değildir. AERO V3 CAD, kritik ölçüler, BOM ve motor yazılımı değiştirilmedi.

Uygulama notu (DEC-045): `cad/prototype_arm/snap01` altında ayrı klips deneme dosyaları üretildi. Referansın cebi dairesel çıktığından bu ilk numune aşağıdaki yıldızlı tork bağlantısını henüz gerçekleştirmez. Yalnız kapak/başlık tutma denemesidir, motorlu veya yüklü kullanım yasaktır. Oturan yıldız biçimi bekleniyor; ana kol geometrisi değiştirilmedi.

## Amaç ve mevcut kanıt

Kullanıcı, indirilen iki referans parçanın kendi plastik servo başlıklarına iyi oturduğunu bildirdi. Bu bir kullanıcı uyum gözlemidir; hangi yıldızın hangi yuvaya oturduğu, eksenel boşluk, gerçek ölçüler ve yük altında davranış henüz kaydedilmedi. Amaç küçük horn deliklerine vida takmadan başlığı baskı gövdesinde tutmaktır.

## Önerilen düzen

1. Kol bağlantısıyla bütünleşen sert ana gövde: yıldızın kollarını çevreleyen biçimli cep. Dönme kuvveti geniş cep yanaklarından aktarılır. Baskı spline kullanılmaz; orijinal plastik başlık korunur.
2. Motor tarafındaki tutucu kapak: başlığın arka yüzünü çevreleyen, merkez göbeğe açıklık bırakan parça. Gövdedeki iki karşılıklı ray/dudak içine yandan kayar. Eksenel ayrılma kuvvetinin ana yolu bu geniş raylardır; yalnız ince klipslere yüklenmez.
3. Kapağın geri kaymasını engelleyen, erişilebilir iki esnek mandal. Birlikte basılarak sökülebilir; kökleri yuvarlatılır, aşırı esnemeyi sınırlayan durdurucu düşünülür. Mandallar kilitlenince sürekli büyük esneme altında bırakılmaz. Kırılan kapak ayrı basılabilmelidir.
4. Gövde önünde tornavida ve servo merkez vidası için erişim kanalı. Motor miline orijinal başlığı tutan merkez vidası ilk prototipte korunur. İki baskı parçasını birbirine kilitlemek, bütün başlığın motor milinden sıyrılmasını engellemez.

Bu düzen kullanıcının iki parçalı kapsül fikridir; yalnız düz bastırılan tırnaklar yerine ray + mandal kullanılarak yük yolu ayrılır. Tamamen vidasız motor mili bağlantısı bu aşamada kabul edilmez. Bunun için bağımsız eksenel tutma/yataklama ve yeniden doğrulama gerekir.

## Montaj sırası

Motor enerjisiz ve başlık motordan ayrı iken yıldız ana gövde cebine yerleştirilir. Arka kapak raylarına sürülüp mandallar kilitlenir. Motor göbeği açıklığı ve ön vida erişimi kontrol edilir. Servo önceden güvenli nötr konuma alınmış ve tekrar enerjisi kesilmiş olmalıdır. Kapsül içindeki başlık, zorlanmadan motor miline yerleştirilir; uygun orijinal merkez vidası öndeki kanaldan takılır. Başlık merkez vidası bulunmuyorsa ölçüsü bilinmeyen vida kullanılmaz ve motorlu test yapılmaz. Arka kapak dönerken motor kasasına sürtmemelidir.

## Neleri klipsli yapacağız?

| Bölüm | Plan |
|---|---|
| Başlığı tutan kapak | İlk ayrı SNAP-01 denemesi: ray + mandal |
| Dekoratif kapak / kablo kılavuzu | Sonraki basit klips adayları |
| Motor gövdesi montajı | Mevcut vidalı tutucu korunur; ayrı yük denemesi olmadan kaldırılmaz |
| Omuz/dirsek karşı eksenleri ve profil bağlantıları | Mevcut mekanik bağlantılar korunur; tüm kola toplu klips dönüşümü yok |
| Servo milindeki merkez vidası | Korunur |

## CAD öncesi gerekenler

- Oturan başlık ve baskı parça birlikte üstten/yandan fotoğraf; hangi dosya olduğu.
- Başlık kol kalınlığı, merkez göbek çapı/çıkıntısı, yıldız biçimi, servo üst kapağıyla açıklık: TBD.
- Merkez vidasının varlığı, baş çapı, dişi ve kullanılabilir boyu: TBD; fotoğraftan kesin ölçü atanmaz.
- Cep boşluğu, ray boşluğu, mandal boyu/kalınlığı/kanca bindirmesi, ön yüz kalınlığı: TBD; ölçülmüş başlık ve malzemeye göre küçük kuponlarla belirlenir. MG90S, MG996R tasarımının körlemesine ölçeklenmiş kopyası olmayacaktır.
- Referansın oturan geometrisi ölçüm karşılaştırması içindir. EEZY CC BY-NC tasarımını ticari CAD'e doğrudan kopyalama izni varsayılmaz.

## Malzeme ve doğrulama

Mevcut PLA ile ilk boyut ve montaj denemesi yapılabilir; bu tekrarlı klips ömrünü kanıtlamaz. PETG esnek mandal için adaydır, kullanıcının elinde olduğu varsayılmaz. Kesin filament profili/katman yönü/tolerans ve sünme-yorgunluk performansı UNVERIFIED. FDM katman ayrılmasını artıran mandal yönlerinden kaçınılacak, kök yarıçapı ve baskı yönü ayrı incelenecek.

İlk olarak yalnız kapsül basılacak. Enerjisiz halde montaj/söküm, tam kilitlenme, boşluk, beyazlama/çatlak ve motor kasasına sürtme incelenecek. Önerilen ilk tarama 20 tak-çıkar çevrimidir; ömür sertifikası değildir. Motor mili yüklenmeden uygun ayrı bir fikstürde eksenel tutma ve iki yönde tork davranışı ölçülecek; kuvvet/tork eşikleri eklem yük hesabından belirlenecek (TBD). Ardından yüksüz yavaş hareket, sonra kontrollü yük basamakları yapılacak. Klipsin açılması, çatlak, ray ayrılması veya artan boşluk durdurma sebebidir. Hızlı salınım/fırlatma ve tam kol kullanımına bu plan onay vermez.

CAD aşamasına geçilirse ayrı varyantta montaj, ihraç dosyaları, renderlar, etkilenen URDF ve testler yeniden üretilecek. Geçerli AERO geometrisi doğrulanmadan değiştirilmez.

## Kaynaklar

- Formlabs, snap-fit tasarım prensipleri (sayfadaki SLA/SLS sayısal toleransları FDM'e doğrudan taşınmaz): https://formlabs.com/uk/blog/designing-3d-printed-snap-fit-enclosures/
- Prusa PETG malzeme rehberi: https://help.prusa3d.com/article/petg_2059
