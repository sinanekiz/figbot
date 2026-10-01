# PartGo doğrudan yükleme talimatı

Bu paket ZIP yüklemek için değildir. Klasörü açın ve ilgili CAD dosyalarını
PartGo yükleme alanına **tek tek** sürükleyin.

## Hangi klasör yüklenir?

1. `01_CNC_STEP_DOGRUDAN_YUKLE`: CNC freze/torna fiyatı için `.step` dosyaları.
2. `02A_3D_BASKI_STL_DOGRUDAN_YUKLE`: Gerçekten basılabilir prototip ve kalıp dosyaları.
3. `02B_GEOMETRI_REFERANSI_MALZEME_FINAL_DEGIL`: Silikon dökülecek parçaların yalnız
   geometri referanslarıdır. STL fiyatı nihai silikon parçanın fiyatı değildir.
4. `03_SAC_DXF_TEKLIF`: DXF dosyaları. ELE-001 cihaz delikleri teslim edilen
   elektronikler ölçülmeden kesin değildir; yalnız yaklaşık teklif alın.
5. `04_REFERANS_PARTGOYA_YUKLEME`: Montajlar, VIS-001 çok parçalı referansı ve teknik
   resimlerdir. PartGo anlık parça fiyatlayıcısına yüklemeyin.

## Önemli

- Her STEP/STL/DXF bir parçayı temsil eder; montaj STEP dosyasını parça gibi sipariş etmeyin.
- `PART_INDEX.csv` içindeki adet, malzeme ve durum alanlarını kontrol edin.
- `RFQ_ONLY` yalnız fiyat/DFM incelemesi içindir; fiyat ekranından doğrudan siparişe geçmeyin.
- ARM-007/008 miller ve ELE-001 için durum `QUOTE_ONLY_NOT_RELEASED` olarak işaretlidir.
- Ölçü birimi milimetredir.
- Malzeme, adet ve yüzey işlemini dosya adından değil `PART_INDEX.csv` kaydından seçin.

PartGo formatları: CNC için STEP/STP, 3B baskı için STL, sac için DXF.

