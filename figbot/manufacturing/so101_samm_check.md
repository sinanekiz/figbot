# SAMM motoru / SO-101 baskı teyidi — 18 Eylül 2026

**Sonuç: konuştuğumuz SAMM 22414 / MP03422, ST3215 12 V–30 kg·cm ürünü için mevcut 01–03 SO-101 baskılarına motorlar gelmeden başlanabilir.** Bu, katalog ve resmi model uyumluluğu kararıdır; ölçülmüş fiziksel geçme veya dayanım garantisi değildir.

| Kontrol | Dayanak / sonuç |
|---|---|
| Satıcı | Kullanıcı SAMM'den aldığını bildirdi. Sipariş faturası görülmedi; ürün eşlemesi konuşmadaki 22414 / MP03422 sayfasına dayanır. |
| Katalog boyutu | SAMM ve Waveshare: 45,22 × 35 × 24,72 mm. Bu özet dış ölçüdür; bütün çıkıntı ve vida eksenlerini tek başına tarif etmez. |
| Modelin kol için kullanımı | Waveshare'in resmi SO-ARM101 montaj kılavuzu follower için 6 ST3215 belirtir; bu nedenle yalnız benzer dış boyuttan uyumluluk çıkarılmadı. |
| Baskı kaynağı | TheRobotStudio/SO-ARM100, eecbe3e0a9ebb23e25ad7b2759b03884c6660903. Orijinal SO101 follower parçaları; özel LINKA yuvaları yok. |
| Ölçüler | Motor yuvaları, başlık oturma yerleri ve vida delikleri değiştirilmedi. Her çıktı, kaynak geometrinin yalnız rijit döndürülmüş/taşınmış halidir. |
| Dijital kontroller | 11 ana parça, kaynak SHA256, kapalı ağ, değişmeyen geometri/hacim, 256 mm tabla sınırı, parça ayrımı ve 3MF aktarımı kontrol edildi. |
| Paket başlıkları | SAMM metni motor başına 1 metal başlık listeliyor; Waveshare kol kılavuzu dişli ön ve düz arka başlık kullanıyor. 11 başlık ihtiyacı var; gerçek paket sayısı teslimde/satıcıdan teyit edilmeli. Bu belirsizlik baskı ölçülerini değiştirmiyor. |
| Vidalar | Gövde bağlantısında motor paketinin uygun sivri uçlu vidaları tercih edilir. Mevcut M2×6 makine vidası aynı diş biçimi kabul edilmez. Başlık bağlantılarında uygun M3×6; merkezde paket vidası. DIN912 baş yüksekliğinin çarpışmaması montajda kontrol edilir. |

## Baskıya başlama

GUNCEL/BASKI içindeki 01_TABAN_OMUZ, 02_KOL_BILEK ve 03_KISKAC paketlerini kullan.
00 mastarları isteğe bağlı ölçü kontrolüdür; motorları beklemek baskı için zorunlu tutulmuyor.
256 mm yazıcı profili, 0,4 mm nozzle, %100 ölçek, 0,20 mm katman. %20 dolgu ve 3 duvar başlangıç ayarıdır; destek ve ilk katmanı dilim önizlemesinde kontrol et. Filament sıcaklığını kendi kalibre edilmiş profilinden al. Mevcut 3MF yazıcı ayarı/G-code içermez. P11 Waveshare Bus Servo Adapter (A) kart tablasıdır; başka kart kullanılırsa değiştirilir.

Fiziksel baskı toleransı, vida başı açıklığı ve teslim edilen motorun katalogdaki ürünle aynı olması henüz ölçülmedi. Hiçbir deliğe rastgele insert eritilmez. Bu kontrol tutma kuvveti, incir kavrama veya kırılmazlık iddiası değildir.

Kaynaklar:
- [SAMM 22414 / MP03422](https://market.samm.com/serial-bus-yuksek-hassasiyetli-programlanabilir-servo-motor---30kg)
- [Waveshare ST3215](https://www.waveshare.com/wiki/ST3215_Servo)
- [Waveshare SO-ARM101 montajı](https://www.waveshare.com/wiki/SO-ARM100/101_Kit_Aassembly)
- [Orijinal SO-101 CAD](https://github.com/TheRobotStudio/SO-ARM100/tree/eecbe3e0a9ebb23e25ad7b2759b03884c6660903)
