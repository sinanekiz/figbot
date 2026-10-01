# SO-101 koordinat hesabı ve referans duruş

`so101_kinematics.py`, yayımlanan SO101_MODEL.urdf üzerinden ileri/ters kinematik hesaplar. Metre/radyan kullanır. Seri porta erişmez; çarpışma, fiziksel motor sıfırı veya yük kapasitesi onayı vermez.

REFERANS_DURUS.png gerçek vendor STL geometrisinden çizildi. Omuz–dirsek eksen merkezleri düşey, dirsek–bilek merkezleri yataydır. Bunlar plastik parçaların dış kenarları değildir. Bilekten sonraki motor/çene gövdesi çizimdeki gibi öne bakar; taban yönü telefonda seçilmiş +X ile hizalanır. Kıskaç açıklığı bu beş eklem kalibrasyonundan ayrıdır.

Kolu destekle, PC'deki FIGBOT kontrollü kol panelinden SERBEST BIRAK seç, torkun kapandığını gör ve yalnız sonra elle referans duruşa getir. Dirençte zorlama. Destekli konumda bırak. Kaydedilecek motor sayıları mekanik referansla eşlenecek; bilinmeyen yön işaretleri ve kamera orijininin gerçek dönme eksenine dönüşümü ayrıca doğrulanır. Gösterilen poz kalibrasyon hedefidir, çalışır motora doğrudan verilecek komut değildir.

Mevcut ham sayılarla XYZ komutu oluşturmak için henüz yeterli kalibrasyon yoktur. Önceki el kayıtları yeniden tüm uçlara gitmeyi gerektirmez; referans ve yön kontrolünde kullanılacaktır.

Resmi yöntem de fiziksel kalibrasyon ister: https://huggingface.co/docs/lerobot/so101 . Burada seçilen merkez hizalama duruşu bizim geometriden türetilmiş referansımızdır; resmi LeRobot standart duruşuyla birebir aynı olduğu iddia edilmez.
