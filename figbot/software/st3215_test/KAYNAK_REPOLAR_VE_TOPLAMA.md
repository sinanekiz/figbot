# FIGBOT — kaynaklardan alınan toplama yaklaşımı

İnceleme: 29 Eylül 2026. Bu belge ve uygulanan planlayıcı değişikliği, yedi
projenin tüm yeteneklerinin SO-101'e kurulduğu veya bir sinir ağının eğitildiği
anlamına gelmez. İnceleme README ve seçilmiş algılama/kontrol kaynaklarıyla
sınırlıdır: 22 dosya, 7 sabit commit. Kaynak dökümleri, dosya SHA256 değerleri ve
tekrarlanabilir model deneyi `reports/upstream_pickup_review/` altındadır.
Kaynak kodları inceleme amacıyla saklandı; yabancı motor sürücüleri çalıştırılmadı.

## Kaynak → FIGBOT karşılığı

| Kaynak ve incelenen sürüm | Yararlı yaklaşım | FIGBOT'a aktarım ve sınır |
|---|---|---|
| [SPARC / nlp-pnp](https://github.com/sahilrajpurkar03/nlp-pnp-robotic-arm/tree/79156f61c770f7dbf9373a45c62faecac3d67d81) | OBB yönü, algılama mesajı, aşamalı alma/bırakma, tamamlanmamış Kartezyen yolu reddetme | Algı ve hareketi ayır; hedefi çevrim boyunca kilitle. LLM motor döngüsüne eklenmedi. SO-101'in pasif bilek dönüşüne UR5 yön komutu taşınmaz. |
| [ColorsLab xArm](https://github.com/colors-lab/xarm-pick-place-with-yolo-tutorial/tree/d22f216b022619d45ce923d95c87cad7a2666254) | Kutu altından zemin temas noktası, kamera ışını/düzlem kesişimi, yaklaş–kapat–kaldır | Ölçülü zemin ve ayrı kavrama yüksekliği kullan. Kaynaktaki sabit XY düzeltmesi, limon modeli, 80/130 mm yollar ve xArm sürücüsü bizim kola uygulanmadı. |
| [my-robotic-arm](https://github.com/munn33b/my-robotic-arm/tree/e29eb901bd929da27dd90311100d3bc73ac7064e) | ROS/CoppeliaSim, durum geri bildirimi, tekrarlanabilirlik değerlendirmesi | Gerçek enkoderi hedef komutundan ayır; simülasyon başarısını fiziksel kanıt sayma. Kaynaktaki 3 eksen/4 Hz arayüz ve derece dönüşümleri SO-101 sürücüsü değildir. |
| [MoveIt 2](https://github.com/moveit/moveit2/tree/a2117df217dc3620b6f1a5d2d150a20e40aa7c7c) | Plan isteği/sonucu doğrulama zinciri, hız ve ivme sınırlarıyla zamanlama | Bu değişiklik tüm çevrim adaylarını denetleyip nominal süresine göre seçer. Mevcut C2 yörünge korunur; MoveIt veya TOTG portu değildir. Tam çarpışma sahnesi henüz yok. |
| [Robotisim ROS2](https://github.com/Robotisim/robotic_arms_ROS2/tree/4f6f516c833fe5bcdec4e4312889e3755a8b78ff) | Başarılı plandan sonra yürütme; kol ve kıskaç denetleyicilerini ayırma | Tüm yol hazır olmadan ilk hareket verilmez. Kuka SRDF, eklem adları ve kontrolcü yapılandırması SO-101'e kopyalanmadı. |
| [AI Sorting Arm](https://github.com/newtonjeri/AI-based-Sorting-Robotic-Arm/tree/ee162b143c4ec0ec14f176c6f5ff21eca590c04d) | Sınıf → bırakma yeri, TF dönüşümleri, URDF tabanlı IK | Algılanan sınıf ile ölçülü robot koordinatını ayrı tut. Örnek test scriptindeki koordinat indeksleri doğrudan kullanılmamalı; FIGBOT şu anda tek incir adayı sınıfını kullanır. |
| [IsaacGymEnvs](https://github.com/isaac-sim/IsaacGymEnvs/tree/aeed298638a1f7b5421b38f5f3cc2d1079b6d9c3) | Ayrı yaklaşma/kaldırma/yerleştirme başarı ölçütleri, fizik ve gözlem değişkenliğiyle eğitim | Kıskaç kapandı bilgisini nesne kaldırıldı sanma. Bu çalışmada iki zemin seviyesinde 112 deterministik kinematik durum denetlendi; Isaac fizik simülasyonu veya RL eğitimi yapılmadı. |

Lisans kaydı: MoveIt BSD-3-Clause, Robotisim GPL-3.0, AI Sorting MIT.
Diğer üç örneğin GitHub metadata kaydında lisans yok; IsaacGymEnvs metadata
NOASSERTION döndürdü. Bunlar yeniden dağıtım izni varsaymak için kullanılmaz.
Çalışan FIGBOT değişikliği bağımsız yazılmıştır; yabancı kontrol kodu eklenmedi.

## Uygulanan değişiklik

`PickupCycle.plan` aynı yedi yaklaşma açısını (0, −15, −30, −45, −60, −75,
−85 derece) tam çevrim olarak sınar. Her açı için yaklaşma, yerleştirme,
kapanma, kaldırma, kayıtlı sepete taşıma ve açılma denetlenir. Önceki kodun
ilk yaklaşmada durması nedeniyle sonraki aşamada reddedilen bir hedef için
artık diğer açılar da değerlendirilir. Gerçekte kullanılmayan, yerleştirmeden
önceki kaldırma şartı tam çevrim seçiminden çıkarılmıştır; gerçek kaldırma
yolu her adayda denetlenmeye devam eder.

15 mm yatay yerleştirme tercih edilir; yalnız tamamlanamıyorsa 10 mm denenir.
Geçerli adaylar arasında nominal toplam süresi en kısa olan seçilir; eşitlikte
aynı sıra korunur. Hedef, eklem sınırları, masa yüksekliği, sıcaklık ve takip
eşikleri, pasif ID5, kıskaç uç değerleri değiştirilmez. Temas aşamalarında
mevcut 600 sayım/s üst sınırı sürer. Kıskaç kapanırken ölçülmüş kol duruşu
korunur; temas sonrası açıklık kaldırma ve taşımada korunur.

Bu seçim yalnız mevcut kinematik modele göre geçerlidir. 20 ms aralıklı TCP
zemin kontrolü, bütün parmakların/kolların veya çevredeki engellerin çarpışma
denetimi değildir. Yerleştirme/kaldırma uç noktaları Kartezyen olarak hesaplanır,
ancak aradaki C2 eklem yolu tam düz Kartezyen hareket garantisi vermez.
15/10 mm yerleştirme ve 25 mm kavrama yüksekliği ölçülmüş incir geometrisi değildir.

## Model deneyi

`PickupCandidateAudit.java` aynı başlangıç duruşu ve 1200 sayım/s seçiminde,
zemin Z=0 ve −65 mm için 112 hedefi önceki algoritmayla karşılaştırır.

- Önceki tam yol: 107/112; yeni tam yol: 110/112. Kurtarılan 3, kaybedilen 0.
- Ortak 107 hedefin nominal toplam süreleri: 668,133 → 649,053 saniye
  (yaklaşık %2,86 azalma). Bunlar art arda fiziksel toplama süreleri değildir.
- Masaüstünde 20 ısınmış tekrarın ortalama plan hesabı yaklaşık 57,8 ms;
  Android telefon gecikmesi değildir.
- Örnek yükseltilmiş zemin çevrimi: nominal 6,227 s; IO, yerleşme, görüntü,
  olası konum düzeltmesi ve gerçek kavrama ölçülmedi.

293 JVM testi ve Android lint geçti. Başarılı yol, seçilen hızın korunması,
geçersiz koordinatların reddi, eski ilk-açı çıkmazları ve değişmez çevrim
listesi regresyon testleriyle kapsanır. Bu kanıtlar fiziksel toplama başarısı
yerine geçmez. Deney kaynak ve çıktısı aynı rapor dizinindedir.

## Yerden nesne toplama doğrulama sırası

1. Tek oturum COM portuna ve telefona sahip olur. Güncel enkoder/sıcaklık,
   duruşta tutma, sabit kamera ve etiketin görünürlüğü doğrulanır.
2. Onarım sonrası etiket–model eşlemesi bağımsız kontrol duruşlarında geçer.
   Bir duruşta kalibrasyon geçmesi tüm çalışma alanının doğruluğunu kanıtlamaz.
3. Zemin temas noktasının görüntüden hesaplanan yeri ve fiziksel kavrama
   merkezi bağımsız ölçülür. Yükseltilmiş bu düzenek için kayıtlı taban
   yüksekliği 65 mm'dir; önceki başarısız denemeler buna bağlanmaz.
4. Sabit ve erişilebilir tek incir seçilir, tüm çevrim planlanır. Önce yavaş
   alma/kaldırma denemesiyle parmak–incir hizası ve açıklığı gözlenir.
5. Nesnenin yerden ayrıldığı görüntüyle doğrulanır. Akım veya kapanma tek başına
   yeterli değildir. Bırakma yerinin geçerli olduğu ayrıca doğrulanır.
6. Tekrarlı başarıdan sonra orta/hızlı profiller karşılaştırılır: gerçek başarı
   oranı, kavrama konum hatası, çevrim süresi p50/p95, takip hatası ve durma
   nedenleri kaydedilir. Başarısız denemeler sonuçlardan çıkarılmaz.

Mevcut fiziksel durum: kullanıcı ID1 üzerindeki boşluğu giderdiğini bildirdi.
Diğer sohbetin onarım sonrası kısa taraması geçse de daha sonra 13,5 mm / 6°
model–etiket farkı reddedildi. Kamera–etiket 23,4 cm, kullanıcı cetvel ölçümü
yaklaşık 23 cm; ölçüm belirsizliği bilinmiyor. Bu bilgiler bağımsız incir
konumunu, gerçek kavrama merkezini veya başarılı yeni toplamayı doğrulamaz.
Eşik yükseltmek veya sabit yazılım ofseti uygulamak bu açığı kapatmaz.

## Sonraki yeteneklerin koşulları

Tam ROS2/MoveIt entegrasyonu için SO-101'e özgü URDF/SRDF, çarpışma geometrisi,
ros2_control/ST3215 arayüzü, ölçülmüş eklem/TCP dönüşümleri ve gerçek sahne
gereklidir. OBB/segmentasyon için incir verisi ve bağımsız değerlendirme gerekir.
RL için meyve/kıskaç temas modeli, yük-sürtünme dağılımları ve gerçek test
verisi gereklidir. Bu işler ve üçüncü taraf modeller henüz kurulmuş/eğitilmiş
olarak gösterilmez. Doğal dil yalnız hedef niyeti üretmeli; motor komutu her
zaman aynı deterministik doğrulama ve durdurma yolundan geçmelidir.


## v34 teslim ve canlı doğrulama sonucu

Birleşik v34 (0.34.0-pickup-candidates) publish_current üzerinden yayımlandı ve
Xiaomi2d9cc5ea cihazına kuruldu. Build ve iki GUNCEL APK SHA256:
8FDE15C5594FB12AE24F90476E754F69B3B54A8235D0485133EACBBD76ED7BC3.
293 JVM testi, Android lint ve4 Python yayın testi geçti.

Kamera sohbetinde kullanıcı etiket23,4cm/ yaklaşık23cm cetvel karşılaştırmasını
ve bir incirin38,8cm zemin mesafesini yaklaşık onayladı. Bu iki tek-nokta sonucu
tüm XYZ doğruluğunun veya tüm çalışma alanının onayı değildir.

04:08:31'de v34 eski kaydı taze etiket/enkoderle doğruladı; altı motor HOLDING.
300sayım/s seçilerek Hedefe Git başlatıldı, ancak kararlı kullanılabilir hedef
oluşmadı; motorlar hareket etmeden DUR verildi, deneme geçmişi silinmedi.
Daha sonra bu sohbetin başlatmadığı başlangıca dönüş ve üç kısa tarama loglandı.
Kullanıcı yeni açık konuma incir koyup elini çektiğini doğruladı.

Bu sohbetin açıkça başlattığı04:12:14–22 kontrollü dört-duruş taraması reddedildi:
öğrenme RMS2,4mm, bağımsız kontrol RMS15,5mm/max21,2mm. Son çiftte model dönüşü
0,703°, gözlenen etiket dönüşü6,163°. Sabit kamera ve rijit etiket bağlantısı
varsayımında bu açıların uyuşması gerekir. Bu hesap tek başına etiket esnemesi,
görüntü poz hatası veya mekanik/enkoder hatasının hangisi olduğunu göstermez.
Sabit extrinsic/ofset veya daha hızlı yol planlaması bu tutarsızlığı açıklamaz.

Kayıtlar: reports/upstream_pickup_review/v34_pick_live.log,
v34_scan_result.png ve v34_scan_diagnosis.json. Son DUR sonrası04:13:09 geri
bildirimi: HOLDING, durgun,33–37°C. Toplama/kaldırma/bırakma başarısı yok.
Yeni hareket için önce bağımsız etiket/gerçek kol hareketi karşılaştırması
gerekir; kalibrasyon eşiği büyütülmedi ve başarısız kayıt etkinleştirilmedi.


# Yanal açıya duyarlı etiket doğrulaması — v0.35 / 29 Eylül 2026

Etiketin düzlem normali ile kameradan etikete giden ışın arasındaki açı ölçülür;
görüntünün kendi içindeki dönmesi ile yanal bakış ayrılır. Kare perspektif
modeli korunur. Dört köşenin yalnızca piksel uyumu yeterli sayılmaz: görüntüdeki
en dar genişlik ve köşe hatasının 3B konum/yöne etkisi ayrıca değerlendirilir.
Kalibrasyon ve hedef hesabı yalnız taze, tek anlamlı, bu kontrolden geçen
ölçümleri kullanır. Tarama yolları aynı görüş kalitesini öngörerek süzülür.
Kararlı karelerin yönleri artık tek kareden alınmaz; SO(3) üzerinde birleştirilir.

Menüde etiket satırı görüş açısını gösterir. Hedefe Git'e uzun bas → Kamera
mesafesini kontrol et ekranında da açı ve ölçüme uygunluk görünür.
Yetersiz açıda metrik ölçüm sunulmaz; daha karşıdan görüş istenir.

301 JVM testi, lint ve telefonda 8 native test geçti. Native testte 20/40/60/70°
yanal açı × 0/45/90° görüntü dönüşü = 12 sentetik görünüşün hepsi geçti:
en büyük konum farkı 0,637 mm, yön farkı 0,179°. Bunlar fiziksel kol doğruluğu
veya gerçek kamera için genel hata sınırı değildir.

Mevcut gerçek yan görünüş yaklaşık 63,2°; 33,6 piksel dar genişlikle ölçüme
uygun/kararlı bulundu. 14–23 ms örnek görüntü işleme süreleri görüldü; kontrollü
hız karşılaştırması yapılmadı. v34'te bu durağan görünüş zaten kararlıydı:
32 kayıtlı karede konum standart sapmaları yaklaşık 0,028/0,014/0,096 mm.
Dolayısıyla önceki 15,5 mm RMS / 21,2 mm en büyük kamera–kol eşleme farkının
tek başına açıdan kaynaklandığı veya bu sürümle giderildiği kanıtlanmadı.
Yeni fiziksel eşleme/toplama yapılmadı; kalibrasyon kabul sınırları değişmedi.
Kurulumdan önce bağlantı kesildi ve köprü mevcut konum tutmasını doğruladı;
uygulama kamera modunda açık, motor bağlantısı kapalıdır.

