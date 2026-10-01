# SO-101 — Türkiye tedarik karşılaştırması

Güncelleme: Kullanıcı önceki vidaları ve pirinç insertleri **600 TL toplamla aldığını**, Type-C kablosunun da bulunduğunu bildirdi. Bunlar tekrar sipariş edilmeyecek. Gönderilen ürün görselinde iki başlık var; gerçek kutular aynıysa altı motorun 12 başlığı yeterlidir. Aşağıdaki eski tek başlık mağaza açıklamasıyla görsel arasındaki fark teslim paketinde teyit edilir.

Kontrol: 17 Eylül 2026. Tek follower kol; satın alma yapılmadı. Fiyatlar anlık sayfa değeridir. Ana plandaki C047 teknik seçimi değişmedi; aşağıdaki Waveshare 22414 yerel muadil adayıdır, C047 / 1:345 ve başlık uyumu yazılı teyit bekler.

| Ürün / satıcı | Adet fiyatı, KDV dahil | Görülen stok | Karar |
|---|---:|---|---|
| [SAMM — ST3215 12 V / 30 kg.cm, 22414 / MP03422](https://market.samm.com/serial-bus-yuksek-hassasiyetli-programlanabilir-servo-motor---30kg) | 1.649,95 TL | 12 adet, canlı tarayıcı | 6 adet için en uygun doğrulanmış yerel aday |
| [Robot Sepeti — aynı 22414](https://www.robotsepeti.com/st3215-yuksek-tork-ve-hassasiyetli-servo) | 1.913,10 TL | Stokta; 6 adet miktarı belirsiz | Yedek satıcı |
| [Direnç — WS22414](https://www.direnc.net/serial-bus-yuksek-hassasiyetli-programlanabilir-servo-motor-30kg) | 1.819,99 TL | Kategori sayfası tükendi diyor | Şu an alınabilir kabul edilmedi |
| [Akımla — 30 kg ST3215](https://www.akimla.com/st3215-serial-bus-yuksek-hassasiyetli-programlanabilir-servo-motor-30kg) | 2.168,95 TL | Stok yok | Seçilmedi |
| [SAMM — Bus Servo Adapter (A), 25514 / MP03890](https://market.samm.com/seri-bus-servo-surucu-ve-kontrol-karti) | 321,23 TL | 54 adet, canlı tarayıcı | 1 adet; arama dizinindeki eski 318,70 TL kullanılmadı |
| [Robomalzeme — aynı adaptör](https://robomalzeme.com/urun/71) | Yaklaşık 343 TL | Stok yok | Seçilmedi |

**Yerel aday ürün toplamı: 6 × 1.649,95 + 321,23 = 10.220,93 TL.** Yalnız motor ve USB kartıdır; tam kol maliyeti değildir. SAMM sayfası 1.500 TL üzeri ücretsiz kargo bildiriyor; ödeme ekranı nihai tutarı belirler. Robot Sepeti motorları + aynı SAMM kartı 11.799,83 TL: motorlarda fark 1.578,90 TL.

## Sipariş içeriğini tamamlamak

- **6 motor, 1 USB kartı:** yukarıdaki SAMM bağlantıları. 7,4 V / 19,5 kg.cm ve ST3215-HS seçilmez.
- **6 bus kablosu:** SAMM motor sayfasında motor başına bir kablo yazıyor; kablo boyu ve pin dizilimi doğrulanır. Uygunsa ayrı kablo alımı yok.
- **11 motor başlığı:** SO-101 için toplam ihtiyaç; SAMM yalnız motor başına bir yuvarlak metal kol listeliyor. Paketler gerçekten tek başlıklıysa beş ek uygun arka destek başlığı gerekir. Düz milli flanşı, 25T tahrik başlığı ve serbest arka başlıkla aynı kabul etme. Ayrı, ölçüsü doğrulanmış yerel satın alma bağlantısı henüz yok; motor satıcısından uygun takım iste.
- **24 M2×6 ve 50 M3×6:** paketlerden ve eldeki stoktan düşülür. Tamamsa yeniden alınmaz. Eksikse örnek baş/diş ile cıvatacıdan tamamlanır; motor kasası için gelen özel/sivri vidanın yerine rastgele makine vidası zorlanmaz.
- **USB-C kablo elde var; yeni alım yok. Önceki fiyat referansı:** [Robotistan, ürün 23081](https://www.robotistan.com/type-c-to-usb-data-transfer-kablosu), sayfa 63,20 TL. Mevcut telefon veri kablosu uygunsa tekrar alma.
- **1 regüle 12 V / 5 A masa adaptörü, uygun kaynak yoksa:** [Robotnom DRL-12VADP-01](https://www.robotnom.com/urun/12-volt-5-amper-masatipi-adaptor-12v-5a-adaptor), sayfa 319,83 TL. Fiş ölçüsü 5,5×2,1 mm, merkez artı ve AC kablosu dahil oluşu teyit bekliyor; koşulsuz satın alma onayı değildir. Alternatif [Polat Store 12 V / 5 A](https://polatstore.com/switch-mode-dc-12v-5a-adaptor) sayfasında 5,5×2,1 uç ve şebeke kablosu açıkça var; fiyat ve merkez artı kutuplama teyit edilmeli. SAMM 12 V / 5 A adaptörü stok dışı ve 5,5×2,5 uçlu olduğu için seçilmedi.
- **2 masa işkencesi, elde yoksa:** [150 mm mini işkence örneği](https://www.koctas.com.tr/fixonic-fixonic-bhd-bhd00430-50x150mm-mini-iskence/p/5002840689). Masanın ve tabanın toplam kalınlığına göre açıklık kontrol edilir. Elde sabitleme çözümü varsa yeniden alma.
- **Filament ve montaj sarfı:** eldeki uygun malzeme kullanılır; baskı dilimlenmeden yeni makara miktarı belirlenmez.

Robotnom adayı ayrıca alınırsa motor + kart + adaptör ürün ara toplamı **10.540,76 TL**; USB kablosu mevcut olduğu için yeni bütçeye eklenmez. Bunlar başlık/vida eksiği, kelepçe, filament ve diğer mağazaların kargosunu içermez. Adaptörün uygunluğu hâlâ koşulludur.

## Yurt dışı fiyat referansı

| Kaynak | Ürün fiyatı | Türkiye teslim durumu |
|---|---:|---|
| [Seeed STS3215-C047 12 V / 1:345](https://www.seeedstudio.com/STS3215-30KG-Serial-Servo-p-6340.html) | 23,99 USD/adet; 6 adet 143,94 USD | Adrese özel kargo ve ithalat toplamı doğrulanmadı |
| [Waveshare ST3215](https://www.waveshare.com/product/modules/st3215-servo.htm) | Sayfa 16,99–21,99 USD aralığı | İki voltaj seçeneği var; 12 V seçeneğinin fiyatı doğrulanamadığı için alt sınırla toplam hesaplanmadı |
| [Waveshare Bus Servo Adapter (A)](https://www.waveshare.com/product/modules/motors-servos/bus-servo-adapter-a.htm) | 4,99 USD | Kargo/ithalat dahil değil; yerel SAMM alternatifi bulundu |

Yurt dışı seçenekler Türkiye'ye teslimi kesinleşmiş teklif değildir; bu nedenle “teslim dahil en ucuz” diye sunulmaz. Seeed motorlar + Waveshare kartının 148,93 USD toplamı iki ayrı satıcıdaki çıplak ürünlerin toplamıdır. Yerel stok bulunmuşken ilk tercih yerel paket teklifi almaktır.

## Satıcıya iletilecek kısa teyit metni

“SO-101 follower için 6 adet Waveshare 22414 ST3215 ve 1 adet 25514 USB kartı istiyorum. Motorlar 12 V, 1:345 oranlı, Feetech STS3215-C047 ile mekanik ve protokol olarak uyumlu mu? SO-101 için gereken ön tahrik ve arka serbest destek başlıkları dahil mi? Altı motor için toplam 11 uygun başlık, 6 bus kablosu, 24 M2×6 ve 50 M3×6 vida ihtiyacının hangileri kutulardan çıkıyor? Eksikleriyle birlikte fotoğraflı paket ve KDV/kargo dahil toplam teklif rica ederim.”

Bu metin gönderilmedi. Paket teyidi tamamlanmadan 10.220,93 TL eksiksiz montaj paketi sayılmaz. Kartın güç yolu en fazla 5 A; 12 V / 5 A önerisi ilk masa kurulumu içindir, altı motorun eşzamanlı tam yük performansını garanti etmez. [Üretici kart sınırı](https://docs.waveshare.com/Bus_Servo_Adapter_A/FAQ).
