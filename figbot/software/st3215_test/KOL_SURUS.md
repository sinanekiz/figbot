Güncel eşzamanlı sürüş ve XYZ kullanımı: [AKICI_SURUS.md](AKICI_SURUS.md). Aşağıdaki küçük adım bölümleri önceki elle sürüş yolunu da anlatır.

# Gözetimli kol sürüşü

Başlatıcı: GUNCEL/YAZILIM/Kol_Kontrollu_Surus.cmd. Kamera ve seri portu kullanan
diğer FIGBOT panelini önce kapat. Uygulama kendiliğinden motorları etkinleştirmez.
Bağlan yalnız okur. Konumu tutmayı aç, altı motorun mevcut konumunu önce hedefe
yazar ve geri okur. Bu motorlarda hedef yazmak torku da açabildiğinden, bu işlem
etkinleştirme sayılır; tork hâlâ kapalıysa ayrıca açılır. Her küçük hareketten sonra bütün eklemler
konum tutmayı sürdürür. DUR mevcut ölçülen konuma hedef koyar; SERBEST BIRAK
torku kapatır ve kol ağırlığını taşımaz. Tork kapatma ayrı ayrı geri okunur.

Bu sürüm yalnız bu SO-101/COM5/1Mbaud ve 2026-09-20 ölçüm oturumu içindir.
ID2 ofseti -813; diğerleri85. Genel ST3215 varsayılan kalibrasyonu değildir.
Kamera2 DirectShow. Mevcut yazılımda tek adım en çok114 enkoder sayımı (~10°);
hız kaydı3072 (~270°/sn sayısal profil), ivme10. Bunlar önceki57/57/1
deneme profilinden farklıdır; gerçek hız veya incir toplama onayı değildir.
Hedefe20 sayım yaklaşma deneme toleransıdır, hassasiyet iddiası değildir.
Manuel kayıttan türetilen aralıklar çarpışmasız çalışma hacmi değildir.

ARM_CONTROL/status.json durum, camera.jpg son kare, command.json kısa ömürlü
yerel komut dosyasıdır. Komut session, artan seq, created_unix ve op içerir;
jog ayrıca joint/delta içerir. Başka süreç seri portu açmamalıdır. Kayıtlar
KAYITLAR/SURUS_... içinde saklanır. Tüm komutlar tek seri işçiden geçer.
3 saniye geçmiş komutlar ve eski oturumlar reddedilir. Hareket kuyruğu birikmez.
`connect` yalnız bağlantı açar ve okur. `attach`, zaten torku açık altı
motorun sabit tutmasını geri okuyarak devralır; kapalı motorun torkunu açmaz.
`recover` / Eksik tutmayı aç, tüm motorların model/mod/ofsetini ve sabitliğini
kontrol eder; zaten tutanların hedefini değiştirmeden yalnız serbest motorlara
o anda ölçülen konumu yazar. Yazma tork açabilir. Hata halinde yalnız bu işlemde
etkinleştirilmesi denenen motorlar serbest bırakılır; önceden tutanlar korunur.
Bu işlem deneme aralıklarını genişletmez, XYZ kalibrasyonu yerine geçmez.
Başlangıç tutma tamamlama profili hız57/ivme1'dir; bu sırada yeni açılan
eklem12 sayımdan fazla saparsa veya hızı50'yi aşarsa yeni hedef göndermeden
tork kapatılır. `probe`, aynı hareket sınırlarını koruyan en çok23 sayım
(~2°), hız57/ivme1 yön denemesidir; `joint` ve `delta` gerektirir.
`step` aynı sınırlar içinde en çok57 sayım (~5°), hız57/ivme1 ile ilerler.
`retreat_probe` mevcut konum eski deneme aralığının dışındaysa, yalnız o aralığa
yaklaşan en çok23 sayımlık yavaş dönüşe izin verir; dışarı doğru hareket,
aralık genişletme veya enkoder sıfırı geçişi yapmaz. Bu işlem de görüntüyle
gözetim gerektirir ve tüm hareket aralığını doğrulamaz.
Durum dosyasındaki `updated_unix` eskiyse panel çalışıyor veya kol serbest
varsayılmaz. Kamera yeni kare verse bile bağlantı logosu/bekleme görüntüsü
gerçek kol görüntüsü değildir; gözetimli hareket için kol görünmelidir.

Kamera akışı kesildiğinde, beklenmeyen konumda veya iletişim hatasında eski hareketi
sürdürmek yerine taze konumda tutma denenir. Yazım ve geri okuma tek başına
durma kanıtı sayılmaz: 0,35 saniye sonra gerçek hız/konum yeniden kontrol edilir.
Hâlâ hareket eden eklemin torku kapatılır (FAULT_STOPPED). Tutma yazımı veya
durma geri bildirimi doğrulanamazsa tüm torklar kapatılmaya çalışılır.
Tork kapatma da doğrulanamazsa FAULT_UNCONFIRMED gösterilir. Yerçekimine
karşı mekanik fren garantisi yoktur. Hata DUR/Devam ile temizlenmez.
55°C ve ham akım150 deneme eşikleridir; akım amper olarak kalibre edilmemiştir.
Sıcaklık/akım hatasında kol desteklenip besleme kapatılarak neden araştırılmalıdır.
Sabit kadrajlı kalibrasyonda piksel farkı güvenilir bir donma ölçütü değildir;
burada yalnız yeni kamera çerçevesi aranır. Kamera görüntüsü nesne/çarpışma
algılayan otomatik güvenlik sistemi değildir. Telefon koordinatıyla hedefe
gitme için ayrı, taze telefon gözlemi ve mekanik kalibrasyon gerekir.
20 Eylül 2026: canlı kamera gözetiminde kuru incir kavrandı ve masadan kaldırıldı.
Fotoğraf ve konum kaydı: `KAYITLAR/SURUS_20260920T192232Z/incir_kaldirma_basarili.*`.
Bu tek başarılı denemedir; otomatik tekrar, kavrama kuvveti, tam hareket aralığı
ve hız optimizasyonu henüz doğrulanmadı. Kayıtlı ham konumlar körlemesine oynatılmaz.

Aynı oturumun devamında incir sağdaki bant rulosunun içine bırakıldı ve kıskaç
boş olarak yukarı çekildi. Kanıt: `KAYITLAR/SURUS_20260920T195145Z/incir_bant_icine_birakildi.*`.
Tabanın eski sayacı4095 sınırına denk geliyordu. Üreticinin `CalibrationOfs`
işlevi (register40=128) ile mevcut taban duruşu2048 yapıldı. ID1 ofseti85'ten
4080'e (işaretli değer−2032) değişti; koordinat kayması−1979 sayım, aynı fiziksel
deneme aralığı yeni sayımda721–3277. `base_reference.json` açılışta donanımla
doğrulanır. Eski ham taban hedefleri artık kullanılmaz. Diğer eklemlerin ofsetleri
değişmedi. `center_base` yalnız açıkça çağrılan, kayıt tutan bakım işlemidir;
normal sürüşte veya uygulama açılışında yeniden merkezleme yapılmaz.
İlk geri okuma karşılaştırması1 sayımlık enkoder farkında durdu; taban kapalı
kaldı, diğer eklemler tuttu. Ofsetten hesaplanan tam dönüşüm ve en çok8 sayım
ölçüm toleransı ile eşleştirildi; tutma ve sağa dönüş fiziksel olarak doğrulandı.
Kaynaklar: https://raw.githubusercontent.com/ftservo/FTServo_Arduino/main/src/SMS_STS.cpp
ve https://files.waveshare.com/upload/f/f4/ST3215_Servo_User_Manual.pdf .
