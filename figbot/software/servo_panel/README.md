# FIGBOT motor kontrol paneli — V4 kadran ve hız

Güncel kullanım: Bağlan, yarım daire kadranına tıkla veya mavi tutamacı sürükle.
0 sağ uç, 90 merkez, 180 sol uç komutudur. Bu ölçek 1000–2000 µs sinyal aralığına
eşlenir; gerçek mil açısının 180 derece olduğu henüz doğrulanmamıştır.

`En hızlı (rampa yok)` hedefi doğrudan gönderir. İşareti kaldırıldığında hız
kaydırıcısı 30–360 komut derecesi/saniye arasında yazılımsal rampa uygular.
Bu sayı ölçülmüş fiziksel hız veya servo hız garantisi değildir. İlk yavaş hareket
son gönderilmiş konumdan (kart yeni açıldıysa 90 komut derecesinden) hesaplanır;
servonun gerçek başlangıç açısı bilinmediği için ilk tutunma hareketi sıçrayabilir.

Sürükleme hedefleri en fazla yaklaşık 60 ms aralıklarla gönderilir, kuyrukta
yalnızca en yeni hedef tutulur. Durdur bekleyen hedefi siler. Klavye sol/sağ
okları, kadran odaktayken hedefi bir komut derecesi değiştirir.
Hızlı üç tur testi, hız kaydırıcısından bağımsız ve rampasızdır.

Protokol: `P<açı>,<hız>\n`; açı 0–180, hız 0 veya 30–360. V4 kart kimliği
zorunludur. Geçersiz/uzun/yarım çerçeveler hareket başlatmaz. 10 saniyelik
komutsuz kapanma ve hızlı test sırasında yalnızca durdurma davranışı korunur.

Tek, yüksüz MG996R'nin küçük hareket testini kullanıcının düğmelere basarak
başlatması için yerel Windows/Tk arayüzü. `firmware/uno_servo_check` yazılımını
kullanır. Seri port açılırken UNO yeniden başlar; panel bağlanınca hareket göndermez.

`Motor_Kontrolu.cmd` dosyasını çift tıkla. COM3 varsayılandır; listeden başka
bağlı USB seri port seçilebilir. Bağlan; konum veya hızlı test düğmesine doğrudan bas.
Sol/sağ düğmeleri kullanıcı gözlemine göre sırasıyla sabit 1600/1400 µs komutlarıdır; art arda basmak
hareket aralığını büyütmez. Gerçek açı ve yön kalibre edilmemiştir.

`3 tur hızlı test`, `t` komutuyla 1000–2000 µs arasında üç gidiş-dönüş
gönderir. Hedefler rampasızdır; uç hedefler arasında 700 ms beklenir. Sonunda 1500 µs
merkez komutundan sonra sinyal kapanır. Bu bekleme süresi motorun ölçülmüş hızı
değildir; gerçek mekanik hareket 180 derece olarak doğrulanmamıştır. Test yüksüzdür.
Hızlı test sırasında yalnızca Sinyali kapat kullanılabilir; konum düğmeleri
yanlışlıkla diziyi iptal etmesin diye devre dışıdır. Eski firmware kabul edilmez; V4 gerekir.
Kart yanıtları `.codex_artifacts/arduino/panel-commands.log` dosyasına kaydedilir.

Sinyali kapat düğmesi ve pencereyi kapatma `x` gönderir. Kart son hareket komutundan
10 saniye sonra sinyali kapatır. Bunlar motor beslemesini fiziksel olarak kesmez.
Arayüz kartın cevaplarını gösterir; servo milinin konumunu ölçmez.

Arduino USB ile bilgisayardan, tek servo 5 V / 2 A powerbank çıkışından beslenir.
Servo eksi ve Arduino GND ortaktır; sinyal D9'dadır. Powerbank güç durumu,
yük altında voltaj ve fiziksel hareket kullanıcı tarafından kontrol edilir.

Bağımlılık: Python 3.12 + tkinter ve pyserial 3.5. Bu çalışma alanında özel
Python ortamı `.codex_artifacts/servo-ui-venv` altında oluşturulmuştur.

Test: özel ortamdaki python ile `-m pytest software/servo_panel/test_controller.py -q`.


## V5 provisional wider dial mapping (2026-09-05)
User reports approximately 90 degrees over 1000–2000 us and requests remapping. The dial now maps 0/90/180 to 500/1500/2500 us. This is a provisional linear extrapolation, NOT physically calibrated endpoints. Begin unloaded at centre and approach endpoints gradually; stop and remove servo power if motion stops with buzzing. Initial ramp is 60 command degrees/s; unrestricted mode remains selectable. The automatic three-cycle test deliberately remains 1000–2000 us (narrow range) pending physical verification. Connecting does not command motion.
