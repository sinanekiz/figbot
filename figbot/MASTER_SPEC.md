

## Stationary-camera range check — 2026-09-29
KolActivity fig ranges/targets now use validated camera-to-ground projection
only; unavailable geometry must not fall back to ARCore depth/plane/feature
hits. A read-only known-size ID0 range dialog is available without motor
connection or camera movement. On stationary restart, the user confirmed about
23 cm against the displayed 23.4 cm marker range, and confirmed the displayed
38.8 cm range to one foreground fig's ground contact. These are approximate
range checks, not certified full XYZ accuracy or successful grasp evidence.
See reports/diagnostics_20260929/stationary_camera_check.md.

## Work-surface chronology correction — 2026-09-29
The user clarified that the 65 mm base elevation was newly added to resemble
field testing; it was absent during earlier failed pickup attempts. The earlier
same-level setup must not retrospectively be treated as a 65 mm plane error.
Use Z=-65 mm only for the raised setup. The exact transition relative to logged
attempts is not established. Earlier pickup failures remain unresolved; the
later elevation is not evidence of their cause. See ASSUMPTIONS.md.

## DEC-088 SAMM confirmation — 2026-09-18
User confirmed SAMM as motor supplier. Conversation catalog match: Waveshare 22414 / MP03422 ST3215 12 V 30 kg.cm; catalog dimensions 45.22 x 35 x 24.72 mm. Official Waveshare SO-ARM101 assembly lists six ST3215 for follower. Nominal original 01-03 print geometry therefore retained, printing before arrival is reasonable; 00 physical gauge is optional, not a blocker. No hole or critical dimension changed. Physical tolerances, received SKU/package contents, paid total and screw head clearance remain UNVERIFIED. SAMM lists one horn while manufacturer assembly uses front/rear horns; verify the 11 required horns without automatically ordering more. Use the motor-pack pointed case screws rather than assuming existing M2 machine screws are equivalent. See manufacturing/so101_samm_check.md.
## Android PC bağlantısı — 2026-09-23

APK v0.14 üçüncü seçenek: telefon ve motor kartı ayrı USB hatlarıyla PC’ye bağlanır.
Telefon mevcut kamera/kalibrasyon/rota/kontrol akışını yürütür; loopback TCP8873
ve ADB reverse üzerinden PC tek seri-port sahibi olarak ST3215 paketlerini aktarır.
Doğrudan telefon USB ve eski Arduino/Bluetooth seçenekleri korunur. PC köprüsü
EEPROM yazmaz, bağlantıda motor etkinleştirmez, kopuşta değiştirilmiş oturum için
ölçülen konumda tutmayı dener; belirsiz duruşu doğrulanmış diye bildirmez.
PC modu fiziksel çevrim ve gecikmesi UNVERIFIED; kalibrasyon kapıları korunur.
Kılavuz: GUNCEL/YAZILIM/ST3215_TEST/PC_ILE_TOPLAMA.md. CAD ölçüsü değişmedi.

# Fiziksel sürüş durumu — 2026-09-20

Devam denemesinde aynı incir sağdaki bant rulosunun içine bırakıldı; kıskaç boş
olarak yukarı çekildi. Tabanın eski4095 sınırı, mevcut duruşu üretici merkezleme
işleviyle2048 yapılarak çalışma alanından çıkarıldı. ID1 yeni ofset4080 (−2032),
aynı fiziksel deneme aralığının yeni gösterimi721–3277; açılışta doğrulanan
`GUNCEL/YAZILIM/ST3215_TEST/base_reference.json` geçerlidir. Eski ham taban
konumları tekrar oynatılmaz. Kanıt: aynı paket altında
`KAYITLAR/SURUS_20260920T195145Z/incir_bant_icine_birakildi.*`.

Aktif SO-101 follower altı ST3215 motoruyla COM5 üzerinden sürüldü. Canlı kamera
gözetiminde kuru incir kavranıp masadan kaldırıldı; tek deneme görsel olarak
doğrulandı. Kanıt ve ham konum kaydı:
`GUNCEL/YAZILIM/ST3215_TEST/KAYITLAR/SURUS_20260920T192232Z/incir_kaldirma_basarili.*`.
Bu sonuç tekrarlanabilir otonom toplama, yük kapasitesi veya tam hareket aralığı
doğrulaması değildir. Eklem işaretleri/kamera dönüşümü ve önceki ID5 tutma
anomalisinin kök nedeni UNVERIFIED; ASSUMPTIONS.md geçerlidir. CAD ölçüsü değişmedi.

# Aktif teslim: resmi SO-101 follower — DEC-088 (2026-09-18)

Kullanıcı altı motor sipariş etti; tam SKU, satıcı ve ödenen bedel TBD. Bir 12 V 5 A masa tipi adaptör 321,25 TL bedelle satın alındı. Önceki vida/insert alımı 600 TL ve mevcut Type-C kablo korunur. Bilinen toplam harcama 9.696,15 TL, motorların bilinmeyen bedeli hariçtir. USB bus adaptör kartının satın alındığı bildirilmedi.

Aktif CAD/baskı kaynağı TheRobotStudio/SO-ARM100 commit `eecbe3e0a9ebb23e25ad7b2759b03884c6660903`, Apache-2.0. Tek follower: 11 parça; iki resmi motor uyum mastarı eklenir. Orijinal motor/başlık/delik geometrisi değiştirilmez; yalnız rijit baskı yönü ve tabla konumu uygulanır. Elimizdeki M2×6/M3×6, uygun baş tipi ve adedi kontrol edilerek kullanılır; orijinal tasarım gerektirmediği için ısı inserti eklenmez. Merkez vidalarında motor paketinin uygun vidası tercih edilir.

Teslim `GUNCEL/BASKI` içinde 00 uyum denemesi ve 01–03 ana tablalar; 256×256×256 mm yazıcı, ölçek %100, 0,4 mm nozzle. Genel 3MF/STL dosyaları dilimleyici profili/G-code içermez. STEP, kaynak manifesti, URDF ve montaj referansı `GUNCEL/CAD` içindedir. Eski LINKA CAD/baskı/listeleri SHA256 doğrulanan arşive alınır. Yayın `scripts.publish_current --so101-print` üzerinden yapılır; varsayılan yenileme aktif SO-101'i korur.

PHYSICAL VALIDATION REQUIRED: motor varyantı/başlık, vida başı ve vida boyu uygunluğu, baskı toleransı, montaj, yük, kavrama ve güç bütçesi. Standart kıskaç incire özel kepçe değildir. Eski UNO/PCA9685 yazılımı yeni kol için kullanılmaz. Önceki web görüntüsü SO-101 teslimi değildir. Aşağıdaki önceki tasarım ve satın alma bölümleri tarihsel bağlamdır, aktif teslimi belirlemez.

# SO-101 satın alma yönü — DEC-087 (2026-09-17)

Kullanıcı, başarısız özel kol yerine videodaki hazır açık kaynak kol yönünü seçti ve mevcut alımları kullanarak eksik listesini istedi. Satın alma planı: tek SO-101 follower, altı STS3215-C047 12 V / 1:345 ve bir USB bus adaptörü. Leader ilk aşamada isteğe bağlıdır; mevcut MG996R/MG90S/PCA9685 yeni kola birebir uyumlu kabul edilmez. Gerçek alım dayanağı arşivdeki FIGBOT_SATIN_ALMA_MALIYET_TAKIBI_V6.xlsx / Alınanlar sayfasıdır: 7 MG996R, 2 MG90S, 2 PCA9685 kaydı vardır; kalan fiziksel stok bilinmiyor.

Yeni liste `GUNCEL/ALISVERIS/SO101_ALISVERIS_LISTESI.md` ve CSV'lerdir. Önceki LINKA listeleri bu plan için kullanılmaz. Bu değişiklik yalnız satın alma hazırlığıdır; aşağıdaki eski tasarım notları, mevcut CAD, baskılar ve yazılım SO-101 teslimi değildir. Kritik ölçü, CAD veya motor komutu değişmedi. Güç bütçesi, aksesuar paket içeriği ve mobil montaj henüz doğrulanmadı; maliyet tamamlanmış teslim fiyatı değildir.

# Active delivery — DEC-084 / TABLA-01 (prototype) 

**Current design prototype — DEC-084 (2026-09-15):** three rigid1.2mm scoop shells with5.5mm roots; one existing G1MG90S drives a rack and three rigid links. No tendon/return elastic. Canonical review CAD is `GUNCEL/CAD/TUTUCU/`; viewer `/kol.html` shows this prototype. Seven new printed types/17 instances; retain original motor star/closure and three L1-25 pivot bushes. Listed spare quantities cover proposed additional fasteners IF the previous buy quantities were actually obtained; actual inventory unknown. `BASKI` now contains the DEC-084 prototype layout: reuse unchanged plates01/02/03/06, retained links/covers on04, new mechanism07 and scoops/bushes08. Full arm47 PLA instances; previously printed arm requires only17 new instances on07/08. Physical approval remains false. This update supersedes the prior FinRay/two-jaw design direction. Physical grip and manufacturing approval remain pending.

**Design study update — DEC-083 (2026-09-15):** user prefers three rigid scoop fingers operated positively in both directions without tendons. The Fin Ray photo illustrates opening/closing layout, NOT a requirement for flexible fingers. Investigate one existing G1 servo, pinion/rack, common guided slider and three rigid links. Two-jaw gear CAD is comparison-only; it is not the selected replacement or a new print release. L1.5 files remain the prior delivered geometry, not a solution to the reported tendon/assembly problems. New drive dimensions, motor load, mass and physical grip are TBD.

Only L1-17 fingers and L1-18 liners change from L1.4: tip extends10mm, broad49.19mm scoop, nominal1.6mm radial wall, new1mm TPU inner liner. Root/bores/fasteners/bushes unchanged. Reprint04A and05 only if L1.4 already printed. Candidate closure12deg; sampled minimum finger gap1.1447mm. Physical grasp, fruit fit, strength and liner attachment UNVERIFIED. Earlier current-revision statements below are historical. See DEC-082.

# Güncel dosya yolu — 2026-09-14

Aktif teslim kökü **GUNCEL/**: BASKI, CAD, ALISVERIS, YAZILIM. Revizyon klasör adına eklenmez. Tarihsel `releases/...` çıktıları ARSIV/ESKI_SURUMLER.zip içindedir; baskı için güncel klasörü kullan. Teknik kaynak kodlarının yerleri korunmuştur. Ayrıntı: PROJE_HARITASI.md.

# FIGBOT Master Specification

**Current correction — LINKA L1.2 / DEC-079 (2026-09-14):** only L1-06 motor deck changes relative to L1.1. Continuous146×120mm floor centred(-39,-6), Z75..80; outward12mm-wide triangular root buttresses support all six columns. Prior J3 foot had no direct floor and J2A feet only15.9% direct support. Other21 part types, all motor/fastener axes and hardware dimensions unchanged. Use `GUNCEL/BASKI/02A_YALNIZ_YENI_MOTOR_TABLASI.zip` for the single replacement. Section/contact and collision checks are not physical strength certification. Machined spacer procurement remains suspended under the user's ready-made/3D-print preference.

**Current assembly correction — LINKA L1.1 / DEC-078 (2026-09-14):** actual CAD at `GUNCEL/CAD/`, source `build_linka_v1.py`, viewer `http://127.0.0.1:5173/kol.html`. Preserve the already-printing plate01 and plate02 retainer halves. Replace plate02 motor deck and affected downstream parts. Upper150/fore120mm and shoulderZ110 remain; J3 local origin(-65,-38,105), crank/coupler/tail65/185/35mm replace the colliding L1 layout. Revised625 backing/caps, external M5 axle retention, ISO7379 rod pivots and corrected screw/washer stacks follow DEC-078. Old L1 plate03/04 must not be mixed with new mating parts. Physical fit, strength, grasp, cable travel, motor limits and sustained torque remain validation items. Do not run old firmware against this linkage.

**Historical R6 status — DEC-076 (2026-09-13): R6 full-arm print recommendation ON HOLD.** User confirms R6 has not been printed; figs40–50g are the operating scenario,100g remains a separate upper requirement. `reports/engineering_20260913/TASARIM_KARARI.md` and `scripts/arm_engineering_review.py` establish explicit mass, torque, reach and fruit-contact gates. At that decision150/120mm compact links and40g complete tool were study targets. Later L1/L1.1 implements150/120mm links, but does not achieve the40g complete-tool target. Existing R6 artifacts below are retained for comparison, not a printing recommendation.

Historical FORMA V6 revision R6 (2026-09-13, DEC-075): six-arm MG996R and asymmetric four-arm MG90 original source horns seat in matching keyed pockets. Each pocket is closed by an external printed motor-facing enclosure half (F6-20/F6-21) and two M2x6 screws into inserts outside the star. All original peripheral holes stay unmodified and unused; original shaft centre screws remain. This supersedes R5 large-star through-hole screws and micro rim washers. Trial side/axial clearance0.20/0.15mm; printed closure2mm. R6 tapers root/end reinforcements and shoulder posts while retaining motor openings, axes and bearing clearances. Actual strength/fit remain PHYSICAL VALIDATION REQUIRED. F6-18/F6-19 coupons must be tried WITH their matching closures.

R5 local load-path revision: non-J1 ear seats gain2mm each lateral side and1.5mm blind-bottom thickness; root webs4→6mm inward; distal fork rounded sections6x16mm instead of4x12; shoulder posts12x9mm and integral lower gussets. Hollow33x32/26x26mm midspan envelopes and2/1.8mm walls,180/140mm axes and motor count unchanged. Recut insert/tool/pocket voids after unions. Central rotor web4.5mm, outer capture flange unchanged. Fixed retainer now inside original rounded120x120mm base footprint; upper roofZ66.5, inner undersideZ61.4 (5.1mm roof), reliefR58 to retain a2mm cardinal outer land; corner gap1.0mm/flange gap1.4mm unchanged. M3x20retainer screws omit the old2.5mm spacers to preserve4.5mm nominal engagement. Use the matched R5base/rotor/retainer geometry; no old PB02 compatibility. DEC-073J1 aperture and race preserved. Updated spool lanes are above the microhorn backing; cord holes do not cross insert bosses. Strength, cable access, physical horn correspondence and assembly remain PHYSICAL VALIDATION REQUIRED. Viewer forma-v6.html shows R5 and a dedicated horn-connection scene.

J1 mounting-access correction (2026-09-12, DEC-073): measured body and shaft remain39.9/5.7mm with body-centreX=-9.8. Restore full old aperture41.5x20.5mm centredX=-10.15; do not narrow a previously fitting cavity based on body-only readings. Relieve only the fixed ring's inner entry edge for the factory-ear swept envelope; preserve rolling surfaces, inserts and retainer. Cable boot/connector/bend geometry and real assembly access remain TBD. The dedicated viewer is `http://127.0.0.1:5173/forma-v6.html`; it displays actual exported CAD and is not a live robot controller. Other servo mounts are not newly physically validated.

Measured J1 geometry applied (2026-09-12, DEC-072): FORMA V6 taban motoru uses39.9mm case length,5.7mm shaft OD and signed case-centreX=-9.80mm relative to shaft/raceXY=(0,0); near case face to axis10.15mm. F6-01 cavity/supports follow this specimen; new F6-17-YAW-FIT coupon. Earlier measurement-record-only note below is superseded for J1 V6. Other servos, actual ear pattern/height/width, horn fit and physical concentricity remain unverified. Retainer clearance DEC-071 retained; PB02 repair package motor interfaces unchanged.

Retainer clearance revision (2026-09-12, DEC-071): user reports inner upper retainer rubbing. PB02 replacement side caps (`release_02_clearance`) have1.0mm axial flange gap, previously0.4. FORMA V6 retainer halves have1.0mm minimum gap above rotor corner ledges (previously0.1),1.4mm above plain flange (previously0.5). Recess only inner underside; preserve race/ball/shaft positions and external fastening. Remaining roof thickness2.4mm PB02 /2.6mm V6; physical rotation, tilt and retention remain unverified. The two designs' caps are NOT interchangeable.

Base-servo measurement update (2026-09-12, USER-REPORTED; ASM-20260912-BASE-MEASURED): main case length excluding ears39.9mm; nearest short case face to near spline outer edge7.3mm; spline outside diameter5.7mm. Derived near-face-to-shaft-centre10.15mm and longitudinal body-centre offset9.80mm. Physical locating/ear interfaces and assembled concentricity remain unverified. Existing PB02/V6 CAD offsets8.14/10.15mm are historical design assumptions; no CAD dimension or export changed by this measurement record.

Active redesign — FORMA V6 (DEC-070, 2026-09-11): user explicitly REJECTED AERO V5. V5 is historical and no longer a print recommendation. Restart independently from the FABRI Creator4.1 video reference, with integrated original-servo-ear seats and heat-set insert fasteners; no old clamp bars, tongue capsules, separate beam sockets or plastic locking pins. Retain PB02's24×8mm ball /45mm pitch-radius base concept, yaw, existing4MG996R+2MG90S,100g maximum object, PLA print context,180/140mm axis spans and direct wheel-front-to-side-basket task. V6 is a dimensional prototype until actual ear/horn/insert interfaces and load trials pass.

V6 proposed base-to-shoulder100mm on existing66mm mounting plane gives166mm shoulder height. New compact three-finger tendon palm has proposed wrist-to-fruit(38,0,-66)mm. Servo-ear pitch49.5×10mm(MG996R) and28mm(MG90S), ear height, original horn screw spacing and insert pockets are explicitly UNVERIFIED layout candidates, not measured user hardware. No finished production fit or strength follows from CAD. Detailed assumptions and validation are in cad/prototype_arm/forma_v6/.

V6 R5 integration candidate: pickup(740,415,20)mm; base120x120mm, fixed bearing retainer within the same rounded120x120mm footprint (DEC-074 supersedes the original140mm diameter), mounting100x100mm M4. Optional receiver132x142x10 with topZ66; frame attachment stillTBD. Rendering and clearances use one arm and the recorded Rev-I rover/basket context. CAD dimensions and paths are not live servo commands.

### Superseded V5 record — retained for traceability only

REJECTED historical arm candidate — AERO V5 (2026-09-11, DEC-069): detailed prototype at `cad/prototype_arm/aero_v5/`, generated by `build_aero_v5.py` and `export_aero_v5.py`. Supersedes the Rev-I arm envelopes below for this print trial. Keep4 MG996R +2 MG90S per arm, base yaw, paired shoulder,180/140mm axis spans and direct side-basket transfer. Integrated split oval shells replace the separate beam/root joint; metal through-bolts, compression sleeves and three identical sliding fingers with soft pads.20 unique part types /45 instances include optional replacement horn adapters and3 pads requiring TPU or cut silicone. Regional Prusa-compatible3MF modifiers specify100% infill/7 perimeters at roots and fasteners; ordinary shell regions use30%/5.

Detailed packaging: mounting surfaceZ66, base-to-shoulder124, shoulder(550,+/-415,190)mm. Wrist-to-fruit local vector(34,0,-110)mm. Vehicle mounting plate candidate132x142x6,100x86 M4 pattern, lower bracing clear of itsZ60 underside. These replace Rev-I placeholder shoulder160/tool60 and plate104x142 only in V5. Vehicle views and single-arm review URDF are integration references; printable parts and BOM quantities are for one bench arm, not a fabricated rover chassis. No second owned motor set assumed.

V5 is an engineering print prototype, NOT load-certified or ready for automatic movement. The new three-finger mechanism adds moving material relative to the old two-finger V4; benefit comes mainly from shorter lever arms and repairable load paths, not a proven whole-arm weight reduction. Full-density static screening at full horizontal extension with100g payload is about15.5kgf.cm at the shoulder pair before dynamics: this is not an approved working pose. Actual PLA properties, motor/horn fit, paired torque sharing, sleeve tolerances, grasp force, fatigue, thermal duty, battery sag and acceleration-limited control remain PHYSICAL VALIDATION REQUIRED. Current UNO V5/Android v0.11 pulse mapping and360deg/s settings must not be presumed compatible with this geometry. No firmware, movement, printer job, purchase or purchase-ledger change in this CAD work.

Active design direction — Rev-I direct side basket (2026-09-11, DEC-068): user returns to the integrated vehicle with existing MG996R/MG90S, no conveyors, pickup ahead of the front tires and direct placement into an adjacent basket beginning above tire height. The specialized fleet below (DEC-067) and conveyor branch (DEC-066) are deferred. Two symmetric locations retain the integrated architecture, not an inventory claim. Separate new spatial CAD: cad/rover/build_rev_i_direct_basket.py and cad/rover/rev_i_direct_basket/. Proposed shoulder axis(550,+/-415,160)mm,180/140mm links,60mm tool offset; side-entry floor305mm. Old Rev-H2/V4 geometry remains unchanged as a hardware reference. Short links, supported yaw/pitch and three-finger geometry are study candidates; actual horn fits, three-finger transmission, self-clearances, load duty, prints and calibrated servo travel remain unverified. No new firmware, purchase or live actuation. See reports/20260911_REV_I_DIRECT_BASKET_TR.md.

Specialized-fleet alternative (2026-09-11, DEC-067): assess single-arm mini pickers, nearby removable trays, passive cart exchange stations and a shared transport vehicle. Study uses the recorded30-decare, estimated380 trees/13,000 figs per day, assumed40g mean and100g maximum object. No production count or one-carrier capacity is established. Prefer staged one-picker then two-picker/one-carrier trials before scaling. Existing REQ-SYS-010 three integrated vehicles, onboard-basket requirements and DEC-066 conveyors remain reference alternatives, not silently implemented replacements. Full plan and explicit arithmetic scenarios: reports/20260911_SPECIALIZED_FLEET_PLAN_TR.md and reports/20260911_SPECIALIZED_FLEET_SCENARIOS.json. No CAD/BOM/firmware/purchase changes; physical and commercial validation remains required.

Low-arm/conveyor architecture study (2026-09-11, DEC-066): proposed next layout uses two arms ahead of the front wheels, shoulder pitch axes nominally near wheel-centre height127mm, each feeding an adjacent inboard incline conveyor to the common basket. Recommend one fixed work camera per side, first tested on a single module with existing camera. Proposed task chain is ground → gripper → low belt inlet → basket. This is the candidate successor to direct arm-to-basket delivery, not an implemented replacement of Rev-H2 CAD. Exact geometry, belt drives, steering/terrain clearances, camera coverage, fruit damage and power remain unverified.100g target retained. See reports/20260911_LOW_ARMS_CONVEYORS_LAYOUT_TR.md; existing high-arm geometry below remains historical/current hardware reference until rebuild.

Planning-input clarification (2026-09-11): lightweight-arm study reuses recorded100g maximum object,40g mean and PLA0.4mm nozzle/0.2mm layer context. Ground-to-basket task remains mandatory. Existing Rev-H2 base280mm plus V4 shoulder124mm gives404mm shoulder height if that mounting is retained. The30/36cm illustrative bench arms are not validated rover solutions; derive reach from stored rover geometry before selecting a shorter arm or proposing a lower mount. See DEC-065 plan correction.

Lightweight-arm feasibility plan (2026-09-11, DEC-065): see reports/20260911_LIGHT_ARM_FEASIBILITY_PLAN_TR.md. Plan one supported bench arm with current4MG996R+2MG90S, explicit yaw, low distal mass and local print reinforcement; compare actual transmission/mass gains before freezing CAD. Power sag, required reach/payload, joint strength and continuous-duty torque remain open. Scenario lengths are not new dimensions; current300/220mm CAD unchanged. Imagegen10 is an explanatory concept, not a validated geared-base assembly. No physical trial, firmware/BOM/CAD change or purchase in this planning step.

Metal-fastener preference (2026-09-11): user requests real metal screws/heat-set inserts and adds an oval-arm reference. References04–08 and purchase candidates are recorded in references/user_arm_preferences_20260911/README_TR.md. Consider inserts for light removable parts and through-bolted, load-spreading, compression-limited fixed shoulder joints; rotating joints require separate shaft/bearing design. Exact fastener dimensions and physical strength remain TBD. No critical dimensions or CAD/BOM changes.

Visual preference update (2026-09-11): user likes the three screenshots preserved in references/user_arm_preferences_20260911/README_TR.md. Use slender linkage-arm morphology of references2/3 and compact compliant three-finger gripper intent as redesign inputs. Dimensions, reach, payload and exact mechanisms remain unverified; no automatic copying, suction substitution or CAD freeze follows. Electrical failure and damaged-root review remain open.

## Physical failure review and redesign requirements — 2026-09-11

User reports PC-powered operation stable, battery-fed5V collapsing to2V when the servo driver is connected, horizontal extended arm unable to lift a fig but able when elbow folds, and fracture at the shoulder-to-long-beam intermediate connection. Exact electrical isolation, amperage, moving masses, fracture surface and print conditions remain unverified. Treat the broken assembly as unavailable for powered trials. See reports/20260911_ARM_POWER_REVIEW_TR.md and calculations JSON. Diagnosis must separate converter IN/OUT/PCA terminal readings with servos removed; no software root cause is established. Existing battery/input12.6V reports do not prove usable battery capacity or converter output health.

New design intent: lower distal mass, shorter reach if task permits, stronger supported shoulder connection, compliant three-finger fig gripper and acceleration-limited motion. Closed hollow oval/box beams and tendon-driven proximal actuation are candidates; hexagonal skeleton is not presumed superior. Existing beams already20x20 with16x16 void. Required reach, actual masses and fig size must determine dimensions/actuator sizing. No CAD, BOM, firmware, purchase or live-device change made by this review. DEC-064 records the review direction; critical dimensions remain300/220mm until a documented redesign.

## Live slider tracking after reported breakage — DEC-063 (2026-09-10)

Installation update: fresh user confirmation received (motor supply off, arm supported, phone USB). v0.11 installed in place successfully and package manager verifies versionCode11 / 0.11.0-live-sliders. UNO V5 unchanged. No assistant motion command or powered mechanism test performed; physical damage/repair remains unverified.

User reports abrupt release-triggered motion broke the arm and requests continuous updates while dragging. Android v0.11 sends user-originated, enabled slider changes immediately to the existing coalescing queue; release sends no additional command. Link retains maximum10 command transmissions/second and newest pending target per joint. Programmatic slider changes do not send motion; explicit centre is still one command. UI move entry also rejects disabled, rearming, disconnected and uncentred non90 paired targets. V5 firmware, range500–2500 and selected/default360 command deg/s unchanged. Stop/disable/watchdog remain; this is not velocity feedback, acceleration limiting or a guarantee against abrupt motion. A track tap or rapid drag can still request a large target step, and release can leave the last target pending/in progress. No motor-powered test or repair of the broken arm is implied.17 Android tests pass; deployment requires fresh motor-off/supported-arm state after reported breakage.

## Slider-only Android defaults — DEC-062 (2026-09-10)

Deployment update: user again confirmed motor supply disconnected and arm supported. APK v0.10 installed in place successfully; phone package manager verified versionCode10 / 0.10.0-simple-controls. UNO V5 remains unchanged. User then reports approximate270-degree travel when turned by hand; this does not establish electrically controllable travel or specific servo variant, so broader physical capability remains UNVERIFIED.

Android v0.10 keeps installed UNO V5 protocol unchanged. User reports 500–2500 us works and explicitly requests that default for every motor. New rows default to 360 command deg/s, paired min500/max2500 and individual wide=true. Main rows show slider/target and accessible gear-icon settings; numeric target and Go removed. Centre button is shown only for enabled, inactive/rearmed shoulder pairs and disappears after activation. Initial pair centre remains explicit; no connection-time position command. Broad-range success is user-reported, not measured validation of every servo or coupled endpoint. User additionally asks for broader pulse ranges and 360-degree testing; no expansion beyond500–2500 or positional0–180 is implemented because model-specific support is unverified and TowerPro specifies MG996R Robot servo as180-degree. Do not represent 360 command deg/s as360-degree travel. Android16 tests pass, lint0errors/35warnings. APK installation pending fresh disconnected-supply confirmation after user-reported motion testing.

## Android simplified controls and shoulder range calibration — DEC-061 (2026-09-10)

Installation update: user freshly confirmed motor supply disconnected and arm supported. HC-05 V5 was installed on UNO COM3 using paced upload; all 9874 application bytes passed per-page/full readback and independent avrdude verification. Android v0.9 was installed in place on the connected phone; package manager confirms versionCode 9 / 0.9.0-shoulder-calibration. No position command was issued. On-device screen and Bluetooth handshake checks are pending; physical range/speed validation remains required. This supersedes deployment-pending statements below.

User confirms 360 selected, slider 0..180 producing about 90 physical degrees, with slow observed motion. Android v0.9 and UNO V5/STATUS5 add stepped symmetric shoulder pulse ranges: 1000..2000 (default), 900..2100, 800..2200, 700..2300, 600..2400, 500..2500 us. Five-field S/PAIR frames carry min/max. Firmware rejects invalid/asymmetric ranges and range changes while active; re-arm and explicit centre-first are required. All paired outputs retain one complementary ramp/transaction and 360 command-speed ceiling. Each specimen's endpoints must be physically calibrated unloaded; the widest option is not a guaranteed safe 180-degree range or validated torque fix.

Per latest user instruction, Android main view contains motion controls and a per-joint Settings button. Default speed is 360 for all joints. Every fresh validated connection queues enable commands for all ten logical joints (12 channels), once only; enabling emits FULL_OFF, no position command. Stop/disable is respected for the session and no automatic reconnect/rearm follows timeout or stop. Pair first-centre motion remains explicit. Settings contains speed, reverse, pulse range and enabled state. Slider release sends one target rather than continuous finger tracking, and typed target + Go enables a single-command speed trial. Arm-tab changes affect visibility only; other joints can continue toward their last explicit target. Watchdog, background shutdown and global stop retained. Desktop client updated for V5 with its existing UI/defaults and narrow shoulder commands. Builds/tests are not installation or physical validation; v0.9/V5 deployment pending supported arm, disconnected motor supply and phone connection.

## Command speed 360 deg/s — DEC-060 (2026-09-10)

Installation update: unchanged HC-05 V4 release is now flashed to UNO COM4 with motor power confirmed disconnected and arm supported. All 9680 application bytes pass per-page/full readback and independent avrdude verification. Standard bulk uploads had isolated corrupt bytes; paced STK500v1 transmission succeeded. Exact root cause remains unverified. Phone reconnection/STATUS4 and physical operation remain pending; see ASM-V4-FLASH-VERIFIED. D8/D9 wiring remains unchanged; normal build has no USB trace.

User requests a 360 deg/s option for both shoulder pairs and other joints. Android v0.8, the USB desktop panel and UNO V4/STATUS4 now accept 10..360 command deg/s, with choices 10/30/60/90/120/150/180/240/300/360 and default 30. New clients reject the older V3/STATUS3 controller so a 360 request cannot silently target the 180-limited build. The first paired target remains 90 degrees; the shared complementary 1000..2000 us trajectory, follower rejection, disabled startup, stop and watchdog are retained. Command angles remain 0..180, not measured physical shaft degrees. No torque authority setting exists, and increased ramp rate does not establish lifting capacity or enlarge pulse travel. Firmware and APK must both be updated with servo power disconnected and the mechanism supported; build/test completion does not mean hardware deployment or loaded validation.

Power update: user reports 5 V unloaded, 3.44 V with one servo, 2.40 V with two, but 12.6 V at the battery and converter input under the reported load. User reports the same system works correctly on powerbank. This implicates the converter/output path or load interaction more strongly than battery charge depletion; actual converter OUT measurement and controlled comparison remain pending. MT-4012C operation with a simultaneous robot load is UNVERIFIED; disconnect robot load for charging until manufacturer suitability is established. See ASM-SPEED360 and ASM-POWER-COMPARISON.

## Shoulder self-weight lifting failure reported (2026-09-10)

User reports paired shoulder servos cannot raise the assembled arm's own weight with the XL4016 supply. Visible thin jumper-type converter-to-PCA motor feed must be replaced/verified before inferring a voltage setting or torque fix. Actual load voltage, mechanical centre/direction matching, friction and current arm mass/centre of gravity remain unverified. Do not increase shared servo V+ speculatively or force a stalled pair. Preserve D8/D9 communication and V3 pair safeguards; first inspect/fix the feed with power removed and arm supported, then validate pair alignment and delivered voltage before another lifting attempt. See ASM-SHOULDER-LIFT-FAIL. No CAD/firmware change follows solely from this report.

## HC-05 transport correction (2026-09-10; supersedes DEC-059 pin mapping)

Latest physical result: user confirms actual motor movement followed by disconnection. The 00:41:52 observation captured malformed input and ERR FRAME; the earlier idle pass does not validate powered operation. Servo supply source, load voltage and grounding are unverified. Powered trials are paused for power-path identification and a same-firmware test with servo power removed; see ASM-HC05-POWERED-FAIL. Keep D8/D9 and do not relax frame validation/watchdog to mask the fault.

Physical update at 00:36:52: user reports Android ready after D8/D9 wiring. USB observation captured 181 heartbeats and 180 complete disabled STATUS3 replies, no captured error reply or unexpected RX byte. Idle phone/HC-05/UNO/PCA handshake passes this observation; previous pending-handshake statements below are superseded. Servo/battery power and loaded motion remain unverified. No motor command was issued. See ASM-HC05-ALT-PASS.

Current HC-05 controller uses AltSoftSerial 1.4.0, fixed UNO D8 RX / D9 TX at 9600 baud. HC-05 TXD connects directly to D8; D9 connects to HC-05 RXD through the existing 1k/2k divider. D10/D11 below describe the earlier build only. Timer1 is reserved for serial timing; no Servo/TimerOne or D9/D10 analogWrite is permitted in this firmware. PCA9685 PWM remains external over I2C. Core protocol, watchdog and disabled startup remain byte-identical to USB V3. The receive-only diagnostic captured clean commands, while prior bidirectional traces contained malformed bytes; exact cause remains UNVERIFIED. AltSoftSerial trace build uploaded and flash verified; new-pin wiring and Android handshake remain pending. See ASM-HC05-ALT and the HC-05 firmware README. Battery/servo power stays off during diagnosis.

## Android HC-05 control menus — DEC-059 (2026-09-09)

Android v0.7 adds HomeActivity with camera-collection observations and MotorTestActivity. HC-05 Classic SPP is explicitly user-confirmed. Motor screen exposes ten joint controls across two arms, V3 mirrored shoulders,10–180command deg/s, acknowledged enablement, centre-first shoulders and explicit stop. Camera scanner/depth/base-frame export remains observation-only; real pick/throw execution is NOT implemented pending physical servo-angle registration, limits and path checks. No assumed IK-to-servo conversion. Background/screen change disconnects and discards queued motor commands; no auto-reconnect/rearm. HC-05 firmware uses D10RX/D11TX at assumed9600baud; shared core generated from USB V3 with byte-equivalence tests, USB is not a simultaneous command owner. Build/tests completed; hardware upload and physical phone/HC-05 operation still pending. See `software/android/figbot-scanner/HC05_KULLANIM.md`. Battery powering UNO remains a later, separately verified wiring step.


## Isolated PB01 printed bearing experiment (2026-09-09)



At user request, DEC-056 adds `cad/prototype_arm/build_plastic_bearing.py` and the `plastic_bearing_pb01` print package: full8mm plastic balls, separate cage, paired thrust races, radial guide and bayonet uplift retainer. Latest user instruction skips the6-ball small coupon: print the24-ball large candidate first, then test by hand. It is NOT an AERO replacement; arm mounting adapters and altered support load path remain TBD. Current AERO base/deck/horns, spans, viewer and purchases remain unchanged. No load rating or motor-driven use is authorized by this geometry trial. See ASM-081 and `cad/prototype_arm/plastic_bearing_pb01/BUYUK_YATAK_BASKI.md`. Geometry-only3MF requires slicer support settings, especially for full spheres; custom integrated supports remain withdrawn.



## PCA9685 bench control update (2026-09-09)



`Motor_Kontrolu.cmd` starts `software/servo_panel/pca_app.py`, backed by V3 `firmware/uno_pca9685/uno_pca9685.ino` (compiled; hardware upload pending servo-power-off confirmation) on UNO. Two tabs expose10 joint controls driving12 channels; shoulders1+2 and7+8 each use a single logical trajectory and mirrored commands (DEC-055). Single-channel shoulder position commands are rejected. Startup/connect/enable commands do not request movement; paired first target must be90degrees. Default pulse range1000..2000us; non-shoulder channels retain optional500..2500us. These are command scales, not calibrated physical180degrees. Shoulder command speed is selectable10–180degrees/s (DEC-058), default30; this is not measured shaft speed; individual physical centre/gain/torque matching and loaded operation remain UNVERIFIED. See ASM-079/080 and `software/servo_panel/PCA9685_KULLANIM.md`. Main CAD/BOM unchanged. Legacy D9 files are retained.



Version: 0.16.0 | Date: 2026-09-07 | Status: AERO V4 PIN/SOCKET DIGITAL BENCH PROTOTYPE — PHYSICAL VALIDATION REQUIRED; V2 PRINT HOLD



## Active AERO V4 pin/socket bench design (DEC-050)



At the user's request, `cad/prototype_arm/build_aero_v4.py` now implements the remaining full bench arm using the unchanged, user-tried SNAP02/SNAP03 horn connections. Printed rectangular/square sockets carry load; slotted headed locking pins retain the assemblies. Optional M3 assembly screws/M6 passive pivot hardware can replace those pins. Six original servo centre screws and external bench restraint are still required. This is a digital prototype release for staged fit and unloaded testing, not verified screw-free load capacity or a production release.



Print source: `cad/prototype_arm/aero_v4/ONCE_OKU.md`, PRINT_MANIFEST.json, TABLA_LISTESI.json and FINAL_AUDIT.json. The new set has75 printed instances, including50 small locking pins, on6 geometry-only plates. Reuse4 large and2 micro horn sets; do not print old V3 bodies or duplicate fitted horn parts. Main spans300/220mm, shoulder height124mm and beam offsets-18/+18mm remain. Prototype beams are hollow20mm square prints, lengths204.6/128.6mm, not the V3 metal cut lengths.



V4 includes separate keyed shoulder towers to permit original horn screw installation before mounting, supported elbow/wrist pivots, a downward wrist/palm and one driven finger. G1 origin is(30,0,-66)mm in tool coordinates. Motor counts4MG996R+2MG90S remain. CAD assembly, individual STEP/STL exports, rendered views, review-only URDF, material estimate and tests are rebuilt together. No firmware, vehicle Rev-H geometry, purchased inventory, printer job or real motor command changed. Actual torque capacity, pin retention, print profile, centre screw dimensions, horn stack/shimming, wiring and paired-servo calibration remain PHYSICAL VALIDATION REQUIRED.



## Previous AERO V3 bench design (DEC-041; retained as history)



Physical feedback (2026-09-07): user reports the MG996R connection "doğru çalıştı" and is printing other connections. Record SNAP02 as USER-REPORTED initial functional success, not independently measured fit/load validation. Exact applied load, rotation range, case clearance, latch endurance and test conditions were not supplied. MG90 SNAP03 result is still pending. No dimensions or full-arm release changed.



Additional isolated MG90 connection trial: SNAP-03 (DEC-049), `cad/prototype_arm/snap03_mg90/ONCE_OKU.md`. Uses the user-supplied SLDPRT native display mesh, with asymmetric four-arm keyed pocket and two opposed retaining covers. Failed STEP conversion is explicitly excluded. Full clip-only arm remains NOT IMPLEMENTED; see `docs/KLIPSLI_TAM_KOL_BASKI_DURUMU.md`. No printer command or full-arm print release follows from this trial.



Active isolated connection trial: SNAP-02 (DEC-048) captures the user-supplied six-arm MG996R reference contour, with two opposed retaining covers and an integral short output tongue. See `cad/prototype_arm/snap02/ONCE_OKU.md`. This is a staged physical bench print, not a released full-arm joint or validated load rating. The four-arm STEP is a different interface and is not used in this print. Main AERO geometry/BOM are unchanged.



PRINT HOLD: SNAP01 A/B/C must not be used as a functional torque coupling; DEC-047 supersedes further round-capsule trials.



Separate 2026-09-07 SNAP-01 (DEC-045) is only a clip/retention coupon, not an AERO replacement or a functioning torque interface. Its source pocket is circular, not star-shaped. No powered or loaded use; exact user horn geometry remains unverified. See `cad/prototype_arm/snap01/ONCE_OKU.md`. Main arm requirements and dimensions below are unchanged.



V3 supersedes the V2 arm geometry for the new bench trial. `cad/prototype_arm/build_aero_v3.py` uses four MG996R plus two MG90S per arm, with a powered downward-facing wrist and one fixed/one moving jaw. Joint spans remain 300/220 mm; shoulder height is 124 mm above base. Tube offsets are -18/+18 mm; nominal 20x20x1.5 mm metal tube cuts are 235/161 mm. Base bolt pattern is 100x86 mm; yaw-deck/shoulder connection 40x28 mm. Idler sleeves, washers, opposite supports and an accessible detachable wrist drive plate are explicitly included.



The source of current print files and conditions is `cad/prototype_arm/aero_v3/ONCE_OKU_MONTAJ.md`. Confirm its geometry/mesh reports match the current source before printing. A successful digital check permits staged fit/bench printing, not a calibrated machine profile, validated load rating or production release. Original horn fit and hardware/print tolerances still need physical trials. The roughly 13 kgf.cm estimated shoulder gravity demand at 100 g excludes important real-world effects; begin unloaded and at low speed, then 40 g. Do not claim 100 g high-speed operation without measurement and any needed counterbalance/drive changes.



The V3 wrist requires coordinated software pitch compensation; existing servo-panel angles are not calibrated robot joint angles. V3 does not command real motors. The older fixed-wrist requirements and V2 FreeCAD files below remain historical, not the active V3 print recommendation. Vehicle packaging and 15-degree basket are retained, with updated arm mounting holes. Purchased inventory is unchanged.



## Active print audit correction (2026-09-05, DEC-039)



The final assembly audit supersedes earlier full-set print-readiness statements. Full Aero V2 arm and gripper sets are on HOLD: J1 shaft is 46.45 mm from the yaw deck, both jaws intersect the palm, J2/J3 horn reference planes/interfaces are incorrect, and the nominal hollow tubes intersect their root hubs. These are digital assembly defects, not uncertainty about delivered clone body dimensions. User acceptance of nominal servo dimensions is retained. FIT-001..007 remain isolated dimensional trial parts, not proof of a complete working arm. Existing legacy tests and Rev-H obstacle checks do not cover these failures. See `cad/prototype_arm/aero_v2/FINAL_PRINT_AUDIT.json` and `SON_BASKI_KONTROLU.md`.



300/220 mm remain joint-centre spans; metal tube saw-cut lengths must be recalculated with corrected end insertion. Supplied MG996R horn forms are visible in the user's photos, but hole pitch, hub height, screws and spline count cannot be measured from them. No new purchases or changed inventory are recorded. Geometry is unchanged by this audit; no validated replacement full-arm design is claimed.



## FreeCAD editing interface (DEC-040)



`cad/freecad/FIGBOT_ROVER_PARAMETRIC.FCStd` and `FIGBOT_ARM_PARAMETRIC.FCStd` expose a limited generator-driven dimension panel while retaining the controlled baseline. This requires the local CadQuery environment and FIGBOT FreeCAD module; it is not independent native sketch history. Experimental changes and their exports stay in `cad/freecad/variants`. See `cad/freecad/README_TR.md`. DEC-039 print HOLD remains in force.



## Product and milestones



| ID | Requirement | Verification |

|---|---|---|

| REQ-SYS-001 | Prioritize low cost, speed, simplicity, manufacturability, repairability, and standard parts. | Design review |

| REQ-SYS-002 | Deliver V0 bench prototype digitally before detailed V1 or V2 investment. | Release audit |

| REQ-SYS-003 | V1 shall be manually pushed and carry a 15 kg crate; V2 autonomy is deferred. | Future physical test |

| REQ-SYS-004 | Every unverified engineering value shall be marked `ESTIMATE`, `UNVERIFIED`, `TBD`, or `PHYSICAL VALIDATION REQUIRED`. | Repository validation |

| REQ-SYS-005 | Purchased actuators, camera, compute, bearings, couplings, home switches, fasteners, cables, connectors, and protection devices shall have controlled part numbers or an explicitly blocked selection gate. | BOM/interface audit |

| REQ-SYS-006 | Product development shall be separated into P0 flat-ground camera rover, P1 independent bench arm, P2 modular brain, and P3 integration; development cost shall not be mixed into per-unit COGS. | Roadmap/BOM audit |

| REQ-SYS-007 | P0 vehicle validation shall omit RTK, LiDAR, Pixhawk, Jetson, suspension, and four-wheel independent drive. The integrated CAD may reserve an arm envelope, but arm installation occurs only after P0/P1/P2 gates pass. | P0 BOM/integration audit |

| REQ-SYS-008 | P0 Rev-G single-unit cost shall be refreshed for the 650 x 600 mm frame, 830 mm track, two lightweight task-specific arms/controllers and sloped front basket. The former 82,154.17 TRY vehicle subtotal is historical and shall not be presented as the Rev-G total. | P0 BOM/cost review |

| REQ-SYS-009 | The current supplier package is a preliminary V1 demonstration and feasibility design. Successful validation may lead to production of hundreds of units, but no series commitment exists before first-article acceptance. | RFQ/release audit |

| REQ-SYS-010 | Fleet planning shall use the user-stated 30-decare total area and three identical vehicles, one planned 10-decare operating zone per vehicle. This is a feasibility baseline rather than a production-capacity claim. | Timed full-zone field trial |



## Active Rev-H2 integration study (2026-09-05)



DEC-038 supersedes the one-arm/30-degree candidate in DEC-037. The current packaging has two identical Aero V2 arm instances at (380, +/-415, 280) mm above the front tires, two independently driven rear wheels and free-running front steering hubs. Frame 650 x 600 mm, wheel diameter 254 mm and 830 mm track are retained. The basket floor spans X=-280..320 mm, Y=+/-330 mm at 15 degrees front-high/rear-low, rear Z=145 mm and front Z=305.77 mm. Its forward apron extends 95 mm. The 5 mm rear-floor adjustment clears rear drive envelopes; the front entry is about 181 mm lower than Rev-H1. Camera envelope moves to (330,0,240) mm under the entry.



Motor, gearbox, shaft, bearing and steering-actuator geometry is UNVERIFIED packaging, not selected purchasing specifications. Rear force path: motor, reducer, stepped coupling, 20 mm keyed stub axle, two bearing supports, wheel hub. Front: overhead bridge, fixed kingpin carrier, steering knuckle, stub spindle and two hub bearings. The steering tie rod and actuator are connected in the straight-ahead pose; full linkage kinematics/stroke remain TBD. Wheel attachment and all sampled clearances do not establish structural strength, braking or motion safety.



Under-basket planning reserves are now battery 180 x 100 x 100 mm at (170,110,161), computer 200 x 140 x 60 mm at (30,-100,141) and power electronics 140 x 100 x 55 mm at (200,-100,138.5). These are packaging envelopes only; existing purchases/BOM are unchanged.



Arm printable interfaces and controlled lengths remain unchanged. Geometry and sampled checks are in `cad/rover/rev_h_review/REVIEW.json` and `RUNNING_GEAR_REVIEW.json`. The fixed-wrist pickup still has about 5.6 mm flat-plane clearance and unverified graspability; two installed arm instances are a design request, not a record that a second set was purchased. The nominal-dimension assumption of DEC-036 is retained; DEC-039 supersedes full-set print readiness. Rev-G remains a historical baseline below.



## Mechanics and handling



| ID | Requirement | Verification |

|---|---|---|

| REQ-MECH-001 | The immediate Aero V2 bench arm shall expose powered J1 base yaw, J2 shoulder, J3 elbow and G1 gripper. Its first print release uses a two-pin fixed-angle wrist to minimize moving parts; pickup/release poses shall constrain forearm angle. A passive self-leveling wrist remains a later field-work option. | CAD inspection + constrained-pose physical test |

| REQ-MECH-002 | Reach shall be optimized over candidate geometries; 550-650 mm shall not be assumed necessary. | Geometry report |

| REQ-MECH-003 | Main links shall be lightweight aluminium; printed parts are limited to housings, noncritical brackets, guides, and tooling. | BOM/inspection |

| REQ-MECH-004 | Rev-G shall minimize moving mass with 20 x 20 x 1.5 mm light-alloy tube candidates, no wrist motor and an adjustable shoulder counterbalance. Each arm uses one MG996R at J1, two mechanically coupled MG996R units at J2 and one MG996R at J3; delivered bracket, spline, paired-servo load sharing and duty performance remain PHYSICAL VALIDATION REQUIRED. | Design review + incoming inspection + timed thermal test |

| REQ-MECH-005 | Joint torque requirements shall include gravity and estimated acceleration components. | Calculation test |

| REQ-MECH-006 | The drop point shall be close to the arm with a short, wide, padded funnel and low drop height. | CAD/review |

| REQ-MECH-007 | V0 shall include a bench base, camera mount, target zone, funnel, and crate interface. | Assembly review |

| REQ-MECH-008 | P0 Rev-G rover retains an approximately 650 x 600 mm bolt-together frame, four equal nominal 10-inch pneumatic wheels, two rear driven wheels and two front Ackermann-steered wheels for dry level or firm smooth ground. | P0 CAD/physical test |

| REQ-MECH-009 | P0 shall reserve an estimated 20 kg payload, but no load capability may be claimed until static, traction, braking, thermal, and one-hour tests pass. | Physical validation |

| REQ-MECH-010 | P0 Rev-G integration packaging shall place a padded 400 x 350 x 180 mm basket at the front-centre and two 110 mm removable arm adapters at X=120 mm, Y=+/-250 mm directly beside its left/right walls. Each basket side shall have a 150 mm front-side drop opening centred at X=220 mm adjacent to its arm. Targets shall be divided into left/right work regions. Collection is from the ground and excludes branch picking. | P0 CAD/assembly review + physical sweep test |

| REQ-MECH-011 | At the full +/-30 degree steering limit, a conservative tyre swept-envelope check shall retain at least 20 mm digital clearance to the structural frame and camera supports. Battery, basket, electronics and camera shall have explicit load paths/mounting trays in CAD. | Automated geometry test + CAD review |

| REQ-MECH-012 | The arm shall collect camera-localized objects from ground level and place them in the onboard basket. Maximum handled-object mass for the V1 demo is 0.10 kg; the arm shall favor low mass, speed and low cost over unnecessary payload capacity. | Supplier design review + physical payload test |

| REQ-MECH-013 | The basket floor shall descend from the front release region toward the rear so filling begins at the rear. Rev-G retains the Rev-F 8 degree `ESTIMATE` inside an adjustable 5-12 degree prototype range, a removable low-friction food-contact liner and a soft rear stop. Reliable transport and acceptable object damage remain `PHYSICAL VALIDATION REQUIRED`. | Adjustable-rig feed, jam and damage test |

| REQ-MECH-014 | Printable arm V1 shall use nominal MG996R 40.7 x 19.7 x 42.9 mm and MG90S 22.8 x 12.2 x 28.5 mm body envelopes with replaceable clamp bars and an initial 0.8 mm total body clearance. Clone-specific flange holes and supplied horn geometry shall not be treated as controlled; six small fit coupons shall pass before full structural printing. | CAD tests + delivered-servo/tube fit check |



## Gripper



| ID | Requirement | Verification |

|---|---|---|

| REQ-GRP-001 | Produce GRP-A soft two-finger, GRP-B medium two-finger, and GRP-C alternate three-finger prototype variants. | CAD/BOM audit |

| REQ-GRP-002 | Silicone contact parts shall be replaceable and mold tooling shall be provided. | CAD inspection |

| REQ-GRP-003 | Grip force shall be limited through passive compliance plus measurable actuator current; exact limits remain `UNVERIFIED`. | Physical test |

| REQ-GRP-004 | Food-contact material suitability requires supplier documentation and human review. | Purchasing review |



## Vision and AI



| ID | Requirement | Verification |

|---|---|---|

| REQ-VIS-001 | Classes: `dry_fig_collect`, `green_fig_ignore`, `stone_avoid`, `leaf_ignore`, `branch_avoid`; semi-dry shall be extensible. | Dataset schema test |

| REQ-VIS-002 | Calibration shall transform camera observations into robot-base XYZ. | Calibration test |

| REQ-VIS-003 | RGB and RGB-D options shall be compared; V0 architecture shall support both. | Design review |

| REQ-VIS-004 | The Android field-scanner experiment shall label phone-derived coordinates unverified, register observations to `base_link`, and transmit observations without authorizing arm motion. | Android unit test + physical control-point test |

| REQ-VIS-005 | The Android experiment shall require manual selection only for the base origin and +X direction; detected dry-fig candidates shall be boxed automatically and show base-frame XYZ when a usable AR hit exists. Fresh/green figs shall be treated as negatives. | Android unit test + phone field test |

| REQ-AI-001 | Evaluation shall report precision, recall, confusion matrix, and class-specific false-positive rates. | Evaluation output |

| REQ-AI-002 | Green/soft fig collected as dry is a critical false-positive. | Test plan |



## Control, simulation, and performance



| ID | Requirement | Verification |

|---|---|---|

| REQ-CTL-001 | Provide FK, IK, joint limits, trajectory generation, and ROS 2-control-compatible interfaces. | Unit tests |

| REQ-CTL-002 | Provide a deterministic Pico 2 step/direction controller with CRC-framed commands, heartbeat timeout, alarm/safety latch, homing, joint limits, and host-side configuration. | Unit test + firmware bench test |

| REQ-CTL-003 | Hardware-dependent direction, home offsets, current limits, gripper positions, and force/damage thresholds shall remain commissioning gates rather than guessed defaults. | Commissioning record |

| REQ-CTL-004 | P0 shall convert speed/yaw commands to separate front-left/front-right Ackermann angles and rear wheel velocities, enforce steering limits, reject pivot-in-place requests and stop on invalid/stale commands. | Unit test + hardware commissioning |

| REQ-CTL-005 | Supplier-integrated controllers, motor drivers, compute and sensor hardware shall remain reprogrammable by the buyer after delivery, with documented electrical interfaces and available protocol/API/SDK or firmware-loading access; vendor-locked control is unacceptable. | Interface/BOM review + commissioning test |

| REQ-CTL-006 | Dual-arm control shall assign normal targets by vehicle Y half-plane, prevent simultaneous entry into any shared swept volume, and arbitrate overlap targets without allowing an arm-to-arm collision. | Coordinator unit test + slow-speed physical sweep test |

| REQ-SIM-001 | Provide a Gazebo V0 world with ground/table, dry fig, green fig, stone, leaf, and funnel proxies. | File/runtime review |

| REQ-SIM-002 | Run at least 100 randomized virtual targets and record reachability, IK, collision, travel distance, and theoretical cycle time. | CSV/report test |

| REQ-PERF-001 | The former 3-5 s arm-cycle study is a historical comparison, not the current RFQ throughput target; simulated values shall remain labelled `SIMULATED`. | Simulation report |

| REQ-PERF-002 | The user-requested system throughput objective is 50-100 successful ground-object deposits per minute within a 5 m2 test area (3000-6000/hour equivalent). This supersedes the earlier 300/hour stationary-demo proposal. Feasibility is UNVERIFIED; the supplier shall assess the architecture and state an achievable first-demo rate. | Supplier feasibility study + timed physical test |

| REQ-PERF-003 | Peak-day fleet planning shall use 13,000 objects/day at an assumed mean 0.04 kg/object: approximately 4,333 objects and 173.3 kg per vehicle. With a nominal 20 kg basket this is nine unloading events per vehicle, including the final partial load. The user target is 30 successful objects/minute per vehicle; with six minutes per unloading event the calculated daily duration is approximately 3.31 hours. | Weighed multi-day count + timed full-zone field trial |

| REQ-COL-001 | Check self, base/stand, camera, funnel, ground and dual-arm shared-volume collision proxies without violating joint limits. Dynamic two-arm CAD sweep remains required before motion release. | Automated tests + CAD sweep |



## Electrical and safety



| ID | Requirement | Verification |

|---|---|---|

| REQ-ELE-001 | V0 shall use modular electronics; custom PCB is not mandatory. | Architecture review |

| REQ-ELE-002 | Separate V0 bench and V1 mobile power budgets; compare 12/24/48 V before final selection. | Power report |

| REQ-ELE-003 | Mobile battery capacity shall be selected from measured 24 V bus Wh, average and peak current during at least 30 minutes of representative full-payload driving with both arms active. Until measured, the 24 V 18 Ah runtime and full-day pack counts are scenario estimates only. | Logged power test + BMS/charger datasheet review |

| REQ-SAFE-001 | A physical E-stop shall interrupt motor-drive energy independently of software. | HUMAN ENGINEERING REVIEW + physical test |

| REQ-SAFE-002 | Electrical protection shall include documented fusing, cabling, connectors, grounding, and controlled restart. | Human electrical review |



## CAD, manufacturing, and configuration



| ID | Requirement | Verification |

|---|---|---|

| REQ-CAD-001 | CadQuery/Python is the master geometry source and uses `cad/config/parameters.py`; magic dimensions are prohibited. | Source audit |

| REQ-CAD-002 | Printed parts: STEP+STL+drawing/preview; CNC/turned: STEP+drawing; laser: STEP+DXF+drawing where applicable. | Validation script |

| REQ-CAD-003 | Unique part families: CHA, ARM, GRP, VIS, FUN, ELE, COV, PUR. | Validation script |

| REQ-CAD-004 | Provide V0, conceptual V1 and P0 front-steer packaging STEP assemblies plus named GLB/GLTF; FCStd is optional when FreeCAD is available. | Build audit |

| REQ-CAD-005 | P0 Rev-G arm packaging shall use two instances of the task-specific MG996R F/P prototype-arm assembly. The earlier official RoArm-M3 STEP remains a historical comparison reference only. Tyre width shall represent total physical width, and camera/steering/basket components shall show connected load paths rather than floating decorative proxies. | CAD/source audit |

| REQ-MFG-001 | Required tolerances need a reason and mating reference; otherwise mark `TBD - MANUFACTURING REVIEW REQUIRED`. | Drawing review |

| REQ-MFG-002 | Every custom part folder shall contain source, outputs as applicable, and manufacturing metadata README. | Validation script |

| REQ-MFG-003 | PartGo quote inputs shall use STEP/STP for CNC, DXF for sheet work, and STL for additive parts; release status shall distinguish RFQ-only from blocked and production-approved. | RFQ manifest audit |

| REQ-MFG-004 | The mechanical series-production RFQ shall be staged as design freeze/DFM, first article and validation, then controlled production pricing; packaging geometry shall never be presented as a production release. | Mechanical RFQ package audit |

| REQ-MFG-005 | External mechanical RFQ packages shall contain only mechanical/electromechanical requirements and selected CAD outputs, with file hashes and explicit release states. | Mechanical RFQ manifest test |



## Documentation and release



| ID | Requirement | Verification |

|---|---|---|

| REQ-DOC-001 | Maintain BOM splits, motor requirements, electrical documents, risk/decision/assumption registers, assembly and physical test manuals. | Repository audit |

| REQ-DOC-002 | Purchasing research shall use current official/reputable sources, dated URLs, no order action, and uncertain price labels. | Human review |

| REQ-REL-001 | Release `V0-PROTOTYPE` shall contain only current prototype artifacts and state `PROTOTYPE - NOT YET PRODUCTION VALIDATED`. | Release audit |

| REQ-REL-002 | A series-production unit price may be requested before validation, but no series build may be released until the first article, interface register and applicable physical validation gates are accepted. | Production-release audit |



## Isolated MG90 correction pending fit — DEC-051 (2026-09-08)



`cad/prototype_arm/snap03b_mg90/ONCE_OKU.md` is a single-body fit correction; retain old SNAP03 covers. The previous general good-fit report must not be interpreted as verified MG90 fit. User now reports asymmetric horn interference. Active V4 and its print packages remain unchanged pending this physical trial. No full-arm reprint requested.



## Manufacturing support correction — DEC-052 (2026-09-08)



User physical failure supersedes any broad print-ready interpretation of the unsupported V4 complex plates. `cad/prototype_arm/aero_v4_supported` adds sacrificial support meshes to ten complex components only. Direct horn couplers, locking pins, clamps, washer and straight beams are not reprinted in this replacement set. Functional arm dimensions are unchanged. A small support coupon must establish separability/adhesion before the five larger replacement plates; digital mesh checks and offline generic slicing are not physical print validation. See SUPPORT_AUDIT.json, OFFLINE_SLICE_AUDIT.json and ONCE_OKU.md. Do not use offline QA G-code on the printer.



## Solid pin fit alternative — DEC-053 (2026-09-09)



`cad/prototype_arm/solid_pins_v4` contains48 unslotted/unbarbed replacement trials for P1/P2/P3/P4/P6 and5 diameter coupons. P5 thick axle and all mating parts remain unchanged. Same-length/3.05mm full set preserves requested dimensions but is not guaranteed to grip3.3/3.4mm nominal holes. Choose friction fit only from physical coupon results. This isolated trial does not certify clip-free axial retention or replace servo centre screws.



## Custom support withdrawal — DEC-054 (2026-09-09)



The user rejects the integrated support trials. `aero_v4_supported` and its packages are WITHDRAWN / DO NOT PRINT, retained only as history. Use original AERO V4 part geometry (unchanged) with appropriate slicer-generated support reviewed before printing. Current arm-v4 viewer already shows original functional geometry without custom supports. Solid replacement pins (DEC053) remain a separate active fit trial.



## Integrated experimental bearing base — DEC-057 (2026-09-09)



`cad/prototype_arm/motor_bearing_pb02/release_01` is the current digital bearing-base prototype. PB01 is a standalone trial, not the motorized arm base. PB02 preserves existing servo/horn/shoulder coordinates and uses a closed shoulder plate with integrated proven star pocket, detachable fixed race/pedestal and two side-entry retainers. Five print plates contain39 new pieces; original horn, two SNAP02 caps, centre screw, motor clamps and shoulder towers are reused. No other arm parts need reprinting. Physical fit, axial load sharing, friction and strength remain unverified. First assembly is unpowered without shoulder towers/payload. Review assembly STEP/GLB and URDF are updated; historical arm-v4 browser scene is not automatically replaced. Geometry-only3MF files require explicit slicer support settings; never use generic offline QA G-code on the printer.

# Current cable-access candidate — LINKA L1.3 / DEC-080

2026-09-14 measurement addendum: user-reported boot dimensions7×3.9mm and outward projection5.5mm are now recorded. Window geometry unchanged at12mm width; exit end and boot lower-edge datum remain unverified. Conditional0.5mm-clearance envelope test covers assembly lower-edgeZ4.5..17.6 on both short ends. The earlier statement that boot dimensions are unknown is superseded only for these three measurements.

Only L1-01 gains central cable-level windows in both J1 short-end support walls. Width12mm, floorZ4, arched roofZ28; physical cable dimensions and exit end still UNVERIFIED. Ear seats, screw axes, floor and bearing track remain. L1.2 motor deck and other21 part types unchanged. Do not treat this candidate as a measured-fit print release before actual cable clearance is checked.
# Aktif mekanik ek — LINKA L1.4 / DEC-081

Plastik burç deneme sürümü: L1-23 OD8/ID5,3/L28×1, L1-24 OD8/ID5,3/L4×2; L1-25 OD4,8/ID2,4/L6×3. PLA. L1-17 parmak pivot deliği5,1mm (önce3,2); üç parmak yeniden basılır. Diğer21 mevcut parça türü ve tüm metal vida/insert/rulmanlar korunur. Güncel yollar GUNCEL/BASKI/06_PLASTIK_BURCLAR ve04A_YALNIZ_YENI_PARMAKLAR. Metal dirsek/parmak burçları satın alınmaz. Yalnız yüksüz uyum denemesi; fiziksel sıkma/ömür/dayanım ve kolun yüklü çalışması onaylanmış değildir. Önceki metal burç ifadelerinin yerine geçer.

## Aktif çubuk mafsalı — DEC-085 (2026-09-16)

Omuzlu vida yerine2 standart M3x10 çelik vida,2 M3 pul (3,2/7/0,5mm),2 basılı L1-26 (6/3,3/6mm) kullanılır. L1-15 uçlarıOD14,kalınlık5,6,delik6,3mm;185mm eksen aralığı korunur. Mevcut krank/önkol veM3L4 insert yuvaları değişmez. Yalnız09_CUBUK_VE_BURCLAR yeniden basılır;03'te çubuk yoktur. Tüm kol49 baskı parçası. GUNCEL/CAD/CUBUK_MAFSALI güncel ölçü/montaj kaydıdır. DEC-084 ipsiz tutucu korunur; yapısal kırılganlık incelemesi açık. Dijital uyum üretim/dayanım onayı değildir.

## Aktif tutucu ve taban kapağı — DEC-086 (2026-09-17)

DEC-084 üç parmak yerine tek mevcutMG90S ile iki karşılıklı modül1,25/28 dişli kepçe. Cidar2,6mm; kök10×6mm. Dört ince tekil dikme yerine6mm pencere boşluklu yan duvarlar. Kepçe şasisi bilek yıldızından32mm ileri alınır,12mm perde ile bağlanır. TS-FRAME/BRIDGE/JAW-DRIVE/JAW-PASSIVE/BUSH beş parça. J1-CAPTURE-CUP altıncı yeni parça, yalnız J1 yıldız kapağını değiştirir; rulman/motor merkezleri korunur.07/08/10 yeni tablalar; önce basılan01/02/03/09 değişmez. Tam takım34 baskı parçası. DEC-085 çubuk mafsalı korunur.

Güncel imalat ve montaj kaynağı GUNCEL/CAD/TUTUCU/OKU.md, parça adetleri PRINT_BOM.csv, donanım GUNCEL/ALISVERIS/VERI/MALZEMELER.json. Dijital geometri adaylarıdır: fiziksel üretim/dayanım/tork onayı verilmez. Tutucu kütlesi CAD tahmini72,33→100,18g; yük azalması iddia edilmez. Gerçek taban arızasının oturma/hiza türü UNVERIFIED; merkez ölçüleri tahminle değiştirilmez.


## Active arm and slicing — DEC-088 / DEC-089 (2026-09-18)
Current deliverable is the original SO-101 follower, not prior LINKA geometry. Eleven main parts across 01_TABAN_OMUZ, 02_KOL_BILEK, 03_KISKAC; 00_MOTOR_UYUM_DENEMESI optional. GUNCEL/BASKI contains native ElegooSlicer TABLA.3mf plus matching G-code, using Centauri Carbon 2 Combo / 0.4 mm / user PLA+ 225 C / Textured PEI A 60 C. 0.20 mm, four walls, 25% gyroid; actual normal Snug supports and toolpaths audited. Source dimensions unchanged. Digital slicing is not physical fit or load validation. Canonical publication: scripts.publish_current --so101-slicer; see GUNCEL/BASKI/ONCE_BUNU_OKU.md.

## ST3215 bench software — 2026-09-19
`software/st3215_test` is a standalone Windows Tk panel for one detached 12 V ST3215 and Bus Servo Adapter (A), USB jumpers B, default 1 Mbaud. Canonical delivery: `GUNCEL/YAZILIM/ST3215_Motor_Test.cmd` and `ST3215_TEST/OKU.md`, published via `scripts.publish_current --servo-test`. Read/connect does not write motor state. Explicit arming preloads and verifies current position with torque disabled before enabling. Test range is current position ±30 degrees, clipped by motor EEPROM limits; 15/30/60 deg/s, acceleration register 10. These are bench limits, not SO-101 joint calibration. Stop releases torque on the bus and clears pending commands; it is not a mechanical brake. EEPROM writes are limited to explicit single-motor ID assignment with readback and relock. Real COM5 readback succeeded (ID1/model777/mode0); motion and hardware ID changes remain physically unverified. CAD, prints and old UNO software unchanged.

User-requested ST3215-TEST-2 supersedes the initial speed/range policy above: selectable 60/180/270-degree total travel, default270; window shifted within the EEPROM/encoder limits to include current position without a startup move. Speed menu15/30/60/120/180/270deg/s plus Maximum=3400steps/s per official Waveshare ST3215 example. Default15deg/s and acceleration10 retained. Maximum is a command, not guaranteed shaft speed. No full-arm joint limit or continuous rotation mode is introduced.

ST3215-TEST-3 supersedes TEST-2's maximum/default speed policy at the user's explicit request for the fastest profile: default Maximum now sends speed register0 and acceleration register0 (manufacturer maximum sentinels in position mode). Numeric speeds retain acceleration10. The initial current-position preload remains speed171/acceleration10 with torque disabled. Position-mode gating,270deg travel default, user arming and separate torque-off remain. No automatic movement is introduced; measured maximum shaft speed and loaded operation are not certified.

## SO-101 base calibration input — 2026-09-19
USER_REPORTED base zero reading: 234; end reading: 113. Interpreted as displayed motor degrees, pending confirmation of travel direction. Decreasing directly gives 121 degrees; increasing across 360/0 gives 239 degrees. Do not activate a travel range, change EEPROM offsets, or issue movement from these endpoints alone. This is an input record, not completed calibration. Intended joint: shoulder_pan / base rotation; physical motor ID assignment remains unverified.

Direction confirmed by user: increasing from234 through360/0 to113, total239degrees. This supersedes the pending-direction text above. Saved in software/st3215_test/so101_calibration.json and published to GUNCEL/YAZILIM/ST3215_TEST. Joint0..239 maps to unwrapped motor234..473 (display modulo360). Bench software does not consume this profile; wrap-aware joint control, physical ID verification and hardware calibration remain pending. No movement or EEPROM write performed.

## Assembled-arm observation preparation — 2026-09-20
User reports assembly and electrical connection complete, arm folded, unique IDs unknown. `software/st3215_test/observe.py` provides user-started local OpenCV camera preview and read-only telemetry; `GUNCEL/YAZILIM/Kol_Kamera_Konum.cmd` is the launcher. Protocol gateway permits only individual PING/READ. No motion, torque changes, EEPROM writes or automatic connection. Reading requires user confirmation of one electrically isolated motor or previously verified unique IDs. Camera/telemetry snapshots carry separate age/time information and are not synchronized calibration. Full-arm motion/calibration remains unimplemented.

## Manual camera/encoder session recording — 2026-09-20
Observer now offers bounded8minute local AVI+JSONL recording of camera frames and asynchronous six-ID telemetry. Recording requires fresh camera/all six readings and all torque registers0. Stale/missing readings or enabled torque terminate recording; unchanged pixels flag possible frozen image, not proof. No serial writes added; no inferred endpoint limits applied. Hardware IDs1-6 individually assigned/verified and read together three rounds. Optional CLI camera/port/read flags require explicit invocation; standard launcher remains manual. Real joint calibration remains pending.


## Physical motion diagnostic / partial reference update — 2026-09-20
Six-ID manual session saved, but its extrema are observations, not safe joint limits. ID2 homing offset is now-813 (previous85), verified readback with torque off and lock1; other offsets unchanged. See software/st3215_test/so101_calibration.json. Two positive shoulder micro-goals produced a small negative displacement and were stopped by position guard. Whole-arm powered sweeps/picking are not validated; startup behavior requires diagnosis. No mechanical dimensions or PID/torque limits changed.

Post-power-cycle ID2 positive micro-probe passed after retained offset normalization; earlier unexpected-direction issue was not reproduced in that probe, root cause still UNVERIFIED. Separate ID3 passive return and ID4 communication/cleanup anomaly prevent treating single-joint torque-release probes as a picking controller. All six individually read torque0 after recovery. Motion implementation must verify cleanup despite ambiguous acknowledgments and retain coordinated joint holding during approach.


Supervised holding-controller work 2026-09-20: source arm_control.py / arm_console.py, delivery Kol_Kontrollu_Surus.cmd. Commands expire after3s, single serial owner, bounded step57, speed57/acc1. Readback of goal/acc/speed required; no blind write retry. Goal writes were observed enabling torque on IDs3/4/5 despite prior ID6-only negative observation. Treat all goal writes as potentially energizing. Response-level8=1 on all IDs; intermittent ID4 ACK loss root cause UNVERIFIED.

First holding-controller base fault (SURUS_20260920T015321Z): after user manually repositioned base across raw zero, current-target264 write led to decreasing base motion rather than hold, despite mode0 and correct target readback. Initial freeze goal226 did not stop rotation. Agent subsequently released all six; torque0 verified, base ended2677. This exposed inadequate stop verification: latched fault had not monitored actual stopping. New source adds STARTING stationary verification and after-stop actual position/velocity check within0.35s; persistent motion disables affected joint, unverifiable stop disables all. Gravity support remains necessary. Fake-bus regression tests cover this failure; revised physical stopping behavior is PHYSICAL VALIDATION REQUIRED. Do not describe stop-goal ACK as proof the robot stopped. Encoder wrap/internal-turn state is a hypothesis, not a diagnosed cause. Blue-object pickup remains incomplete.


## Phone XYZ observation bridge — 2026-09-20
Android FIGBOT v0.11 and ARCore1.56 on connected Xiaomi17Pro produced an actual export with depth_api_supported=true, ARCORE_DEPTH_HIT and one dry_fig_candidate, confidence0.8897, XYZ(267.546,-2.852,-69.046)mm. Original packet is in GUNCEL/YAZILIM/ST3215_TEST/KAYITLAR/figbot-scan-1789872665239.json. User selected an origin on the upper side of the base motor; negative target Z can therefore be correct. Exact datum and AR-to-URDF transform are UNVERIFIED. Nominal vendor URDF shoulder_pan origin relative to base_link is (38.8353,0,62.4)mm; an arbitrary tapped top surface is not automatically this datum. A tested localhost target_receiver logs v2 observations only; no hardware control. V2 lacks capture timestamps/tracking state, so receiver time cannot establish capture freshness. Continuous phone streaming and calibrated coordinate-to-joint motion remain unimplemented.


2026-09-20: User confirmed all three displayed target coordinates X211.085/Y-130.223/Z-53.157mm as correct ("hepsi dogru"). This is USER_CONFIRMED_SINGLE_TARGET_COORDINATES, not independently measured precision, a workspace-wide validation, or a transform to the vendor URDF. The exact confirmation and source observation are recorded in GUNCEL/YAZILIM/ST3215_TEST/KAYITLAR/phone_target_user_confirmation.json.


2026-09-20 Android 0.12 coordinate-stream: V3 observation-only USB HTTP streaming, at most one request in flight, 500ms send timer. Capture/depth timestamps and local capture age exported; >750ms old data, duplicate camera image timestamps, lost tracking or >3mm/>0.5deg camera pose change suppress target XYZ. Image-depth association remains STATIONARY_SCENE_APPROXIMATION, not synchronized depth or verified moving-object tracking. Session/calibration revision and world origin/+X/camera pose are exported. Keep-screen-on only in scanner; backgrounding stops streaming and clears observations. User single-point confirmation is retained in records, not transplanted to a new AR session or promoted to a robot URDF calibration. No serial commands added. Publication scripts.publish_current --android-app archives prior APKs with SHA256 checks.


2026-09-20 SO101 offline kinematics: vendor new-calibration URDF parsed directly; FK/position+approach-axis IK and explicit local encoder mapping implemented, no serial/motion commands. Reference pose derived from joint-centre geometry: qdeg=[0,-13.96796008,16.17545169,-2.20749161,0]. Aligns shoulder/elbow centres vertically and elbow/wrist centres horizontally. Hardware encoder reference, direction signs and camera-origin transform remain UNVERIFIED. Model limits are not collision-free workspace; no pickup achieved. V3 live phone HTTP receipt verified, actual sample X217.091/Y-134.133/Z-60.118mm.


2026-09-20 reference pose capture: user confirmed the geometric reference pose and controller readback after release recorded raw encoders {'1': 3973, '2': 1907, '3': 3823, '4': 1872, '5': 211, '6': 1391}. All six torque registers were 0 at capture and voltages 12.2–12.4V. This file is a physical reference observation, not complete calibration: IDs1–5 direction signs, exact mechanical joint zero, camera base transform, gripper jaw angle, collision-free range and target motion remain UNVERIFIED; no motor movement or EEPROM write performed.


2026-09-20 supported reference direct read: user confirmed holding/supporting the geometric reference pose while tork remained off. Direct COM5 read-only (no writes) captured encoders {'1': 3975, '2': 1824, '3': 3107, '4': 1878, '5': 112, '6': 1392}; all stationary, 12.2–12.3V. Earlier status values {'1': 3973, '2': 1907, '3': 3823, '4': 1872, '5': 211, '6': 1391} are INVALIDATED because duplicate-controller/stale status conflict and gravity settling made them non-authoritative. This reference still lacks encoder direction signs for IDs1–5, exact camera-to-URDF datum transform, gripper jaw angle, collision validation and motion authorization.


## Concurrent SO101 control and local XYZ — 2026-09-20 evening
The active console now uses feetech-servo-sdk 1.0.0 GroupSyncWrite, the SDK family used by LeRobot. Multiple joint position/speed/acceleration profiles are sent in one address41 broadcast; individual register readback and motion supervision remain. move_pose/play_sequence support firmware-ramped concurrent moves, not per-joint jog chains. Physical telemetry confirmed 2 then 4 simultaneously moving joints. Empty pick-place replay measured10.47s excluding initial return,14.00s including return. Neither new replay picked the fig. Source coordinated.py, cartesian.py, motion_library.py; current guide GUNCEL/YAZILIM/ST3215_TEST/AKICI_SURUS.md.
Local XYZ now solves the vendor-URDF position and tool pitch using axes1-4, holds wrist roll, and dispatches the resulting joint pose through the same sync controller. Two supervised local Cartesian trials were executed (+40mm model Z and30mm radial inward); directions observed, physical distances/absolute accuracy UNVERIFIED. cartesian_reference.json is explicitly LOCAL_GEOMETRIC_ESTIMATE_SUPERVISED_VALIDATION, not full calibration. Camera-to-base transform remains UNVERIFIED; no automatic phone target motion. The old descriptions of offline-only IK and single-joint-only control are historical, superseded for this console. Joint paths are not Cartesian straight lines; coarse table-plane sampling is not full collision checking. No EEPROM, dimensions, PID or torque limits changed in this revision.


## Maksimum sayısal profil — 2026-09-20
Kullanıcının isteğiyle eşzamanlı sürüşün hız sınırı3072 ->3400 sayım/s,
ivme kayıt sınırı10 ->150 yapıldı. Kaynak: https://www.waveshare.com/wiki/ST3215_Servo
SyncWritePosEx örneği. Varsayılan duruş/XYZ isteği ve kayıtlı çevrim süre istekleri
0.25s oldu; planlayıcı mesafe/hız/ivmeye göre gerekli daha uzun süreyi hesaplar.
Kısa mesafede bütün motorların3400 hızına ulaşacağı anlamına gelmez; hedef süreye
uyum için her motorun profili ayrı hesaplanır. Sıfır/sınırsız profil kullanılmaz.
Konum/akım/sıcaklık/kamera/komut tazeliği/durma kontrolleri değiştirilmedi.
101 ilgili test geçti. Bu profilin fiziksel denemesi kamera geri gelene kadar
PENDING_CAMERA durumundadır; önceki10.47/14.00/12.99s ölçümleri eski ivme10
profiliyle alınmıştır. Yeni profilin ölçümü henüz yoktur.


## Fiziksel maksimum profil sonucu — 2026-09-20 son güncelleme
Başlangıç duruşundan alma-bırakma hareket dizisi5.640s içinde tamamlandı;
başlangıca dönüş bu ölçüme dahil değildir. İncir bantın dışında kaldı.
103 ilgili test geçti. Motorların fabrika Maximum_Acceleration kaydı85,
1bayttır ve altı motorda50 okundu;86 ayrı çarpandır ve1 okundu.
LeRobot resmi STS tablosu bunu doğrular:
https://github.com/huggingface/lerobot/blob/main/src/lerobot/motors/feetech/tables.py
150 gönderildiğinde hedef hız/konum korunurken ivme50'ye kısıldığı için
sıkı geri okuma denetimi hareketi iptal etmişti. 53->50 gözleminin10'luk
basamak yuvarlaması olduğu hipotezi GEÇERSİZDİR ve bu geçici kod kaldırıldı.
Planlayıcı artık her program öncesi85 kaydını salt okur, bütün motorların
ortak en düşük fabrika sınırıyla süre/ivme hesaplar; fabrika kaydını değiştirmez.
Etkin üst sınırlar hız3400 ve donanımdan okunan ivme50'dir; yazılım sayısal
ivme tavanı150 olsa da bu donanımda50 üstü gönderilmez. Önceki PENDING_CAMERA
notu bu başarılı hareket denemesiyle güncellenmiştir. XYZ fiziksel doğruluğu
ve otomatik nesne kavrama hâlâ doğrulanmış değildir.


## Kapalı başlangıç ve sürekli çevrim — 2026-09-21
Kullanıcının elle gösterdiği kapalı başlangıç enkoderleri: ID1..6 =
2033, 782, 3946, 2729, 3127, 949. Ofsetler değişmedi. Konum tutma yerinde
etkinleştirildi. İlk kapalı-başla/kapalı-bitir denemesi7.556s, son hata en çok3
sayım. Kalıcı kütüphane ARM_CONTROL/motion_library.json; al_birak çevrimi
kapali_baslangic duruşuyla başlamayı zorunlu kılar ve oraya döner.
Genel jog/XYZ aralıkları değiştirilmedi; yalnız kayıtlı başlangıç rotasında
ID2/4 için ölçülmüş duruşa uzantı kullanılır; iç ara noktalar eski aralıkta.

smooth_path.py, C1 sürekli şekil-koruyan kübik eklem yörüngesi oluşturur.
Ara noktalarda varış/duruş beklemesi yoktur. Analitik hız/ivme sınırı hesabı
hız3400 ve donanımdan okunan ivme50 sınırlarına göre zamanı ölçekler.
Tüm hareketli eklemlerin Goal_Position kayıtları SDK GroupSyncWrite ile ortak
zamanda güncellenir. Bilek dönüşü ID5 sabit tutulur. Kıskaç yaklaşırken kapanır;
kaldırma/taşıma ve bırakma/geri dönüş hareketleri örtüşür. Kuvvet kontrollü
kavrama veya nesnenin alındığını algılama henüz yoktur.

Gerçek sürekli çevrim6.360s tamamlandı;191 güncelleme, en büyük güncelleme
aralığı78ms, en büyük zamanlanmış konum takip farkı73sayım. Kapalı başlangıca
son hata en çok3sayım. İncirin alınıp banda konulduğu doğrulanmadı; simülasyon.
Kayıt: SURUS_20260920T205942Z/first_continuous_result.json.

5.510s zamanlama denemesi açılma sırasında ileri hedef/ölçüm farkı192sayım
sınırını aştığı için iptal oldu (takip hatası76sayım). Eski DUR kodu ivmeyi
50'den10'a düşürüyordu;350ms durma kontrolü tutmayı doğrulamayınca ID2/4/6
torkunu kapattı. Kayıt SURUS_20260920T210246Z/optimized_attempt_fault.json.
Kod artık 192sayım sınırını değiştirmeden ileri bakış zamanını azaltır;
DUR, doğrulanmış mevcut ivme sınırını korur. Bu iki düzeltmenin fiziksel
kontrolü PENDING_SUPPORTED_RECOVERY. Ani durmanın fiziksel davranışı
UNVERIFIED; hızlandırılmış deneme başarılı sayılmaz. 120 ilgili test ve4
alt test geçti. Üç saniye hedefi karşılanmadı. Tam çarpışma modeli yoktur.


## Kullanıcının çevrim süresi tanımı — 2026-09-21
Üç saniye hedefi, önceki incir bırakıldıktan sonra bir sonraki incire doğru
ilk fiziksel hareketin başlamasından yeni incirin sepete fiziksel olarak
bırakılmasına kadardır. İlk kapalı duruştan açılma ve iş sonundaki katlanma
bu metriğe dahil değildir. İş sırasında her incir arasında kapalı duruşa
uğranmaz. Bırakma ile sonraki hareket arasındaki boş süre ayrıca raporlanır.
Kıskaç açma komutu gerçek incirin sepete bırakıldığına kanıt sayılmaz.
Önceki6.36s kapalı-başla/kapalı-bitir ölçümü bu metrikle karşılaştırılmamalı.

Birak -> alma_yaklasma -> kavra -> tasima_gecisi -> birak rotası, aynı
3400 hız/50 fabrika ivme sınırı ve sürekli yörünge hesabıyla çevrimdışı
2.72255s hesaplandı. Bu fiziksel ölçüm veya başarılı toplama kanıtı değildir;
yeni sepetten-sepete çevrim donanımda çalıştırılmadı. Tahmini model uç yüksekliği
en az21.04mm; tam çarpışma kontrolü yok. Fiziksel kavrama, bırakma ve süre
PHYSICAL VALIDATION REQUIRED. Yeni rapor ARM_CONTROL/harvest_cycle_metric.json.
Motorların önceki hata sonrası ID2/4/6 torku0 durumu değiştirilmedi;
kullanıcının destek onayı ve tutmanın geri açılması bekleniyor.


## Elle yol öğretme — 2026-09-21
Kullanıcı en uzak incir ve yandaki yüksek araç sepeti arasındaki yolu elle
gösterecek. teaching.py, altı motorun torku0 iken mevcut tek seri port
sahibinin yaklaşık12Hz geri bildiriminden altı enkoderi, kıskaç hareketini,
zamanı ve işaretleri ARM_CONTROL/TEACHING/*.jsonl dosyasına yazar.
Arayüzde kayıt başlat/bitir ve incire ulaştım/kavradım/sepete ulaştım/bıraktım
butonları var. Kayıt açıkken motor etkinleştirme/hareket komutları engellenir.
Tork değişimi kaydı iptal eder; enkoder sıçraması ve geri bildirim boşluğu
inceleme bayrağıdır. Kayıt otomatik sürüş onayı veya çarpışmasız yol kanıtı
değildir. Elle gösterim bekleniyor; yeni uzak hedef/yüksek sepet çevrim süresi
TBD, PHYSICAL VALIDATION REQUIRED. Kapalı konumdan açılma/iş sonunda kapanma
hasat metriğinden ayrıdır. 51 kayıt/kumanda/yayın testi geçti.


## Elle öğretilen uzak incir / yüksek sepet tekrarı — 2026-09-21
TEACH_20260920T211710_1dac69.jsonl tamamlandı:728 örnek, en uzun aralık0.413s,
enkoder sıçrama bayrağı yok. İlk başarısız öğretim kullanıcı isteğiyle
INVALIDATED_BY_USER_RESTART işaretlendi. Yeni kayıtta kavrama ve bırakma
buton işaretleri yok; olaylar kıskaç izinden çıkarıldı (INFERRED).

Taught replay yalnız SHA256 doğrulanan, tamamlanmış ve geçersiz işaretlenmemiş
pasif kaydın gerçek örneklerini kullanır. Ofset/başlangıç duruşu denetlenir;
ID5 gürültüsü hareket olarak tekrarlanmaz. Yerel hareket aralığı kayıtlı yolun
ölçümlerinden gelir; genel jog/XYZ aralıkları genişletilmez. Sürekli yörüngeler
128 düğüme kadar önceden doğrulanabilir; küçük zaman aralıkları nihai kübik
hız/ivme hesabına tabidir. Motor fabrika ivme50/hız3400 sınırları korunur.

İlk elle gösterilen tam yol15.797s içinde fiziksel olarak tekrarlandı. Ardından
aynı kaydın taşıma geçişlerini ters yönde kullanarak iki sepet-incir-sepet
çevrimi eklendi; dönüşte kıskaç açık, son yaklaşmada kapanır, yüksek bırakma
noktasında açılır. Katlanma iki çevrimin sonundadır. İki çevrimli tam program
24.109s tamamlandı; kullanıcı beğenip yeniden istedi, aynı program24.156s
tekrar tamamlandı. Bu toplamlar hasat süresi metriği değildir.

Her sepetten çıkış-yeniden sepet noktası çevriminin program zamanı4.174s.
200ms telemetride fiziksel hareket başlangıcı ve sepet duruşunda açık kıskaç
koşuluyla yaklaşık4.0s/4.0s bulundu; bu enkoder simülasyon ölçümüdür, gerçek
nesnenin sepete düştüğünün ölçümü değildir. Üç saniye hedefi karşılanmadı.
Canlı görüntüde kıskaçta taşınan incir görüldü; gerçek sepete başarılı bırakma
UNVERIFIED. Son tekrar697 güncelleme, en uzun aralık78ms, en büyük zamanlı
izleme farkı111sayım; altı motor konum tutuyor, kol katlı duruşta.

Güncel rota ARM_CONTROL/TEACHING/replay_plan.json; kayıtlar
KAYITLAR/SURUS_20260920T212903Z/harvest_cycle_measurements.json ve
requested_repeat_005.json. 128 ilgili testin ardından kıskaç zamanlama
örtüşmesi için5 taught_replay testi ayrıca geçti. Takip mesafesini aşmadan
ileri bakış kısaltma, bu tekrarlar sırasında kullanıldı; yüksek hızlı acil
DUR davranışının özel fiziksel doğrulaması hâlâ yapılmadı.


## Güncel akıcı sürüş ve erken bırakma düzeltmesi — 2026-09-21

Bu bölüm önceki hız denemelerinin güncel durumunu değiştirir. 3.60s C2 denemesi
taban takip hatası306 sayım ile durdu; motorlar tutmayı korudu. Ardından3.92s
zamanlanan sürüş tamamlandı ancak kullanıcı incirin erken bırakıldığını bildirdi.
Bu sürüm başarılı toplama veya doğru bırakma sayılmaz; c2_early_release_rejected.json
olarak işaretlendi. Kıskacı sepetten önce açarak süre kısaltma kaldırıldı.

Güncel replay_plan.json: hız ve ivmesi sürekli quintic C2 eklem yörüngesi.
Ara taşıma duruşları sonraki kayda doğru dört kol ekseninde en çok64 sayım
yuvarlanır; alma/bırakma duruşları ve ID5 değiştirilmez. Bu hesaplanan geçiş
düzeltmesi tam çarpışma planlaması değildir. Tüm hareketli hedefler aynı
GroupSyncWrite paketinde gider. Genel jog/XYZ limitleri, fabrika ivme50,
sonlu hız3400, takip/ileri hedef192 sayım sınırları değişmedi.

Bırakma, açık kıskaç komutundan önce ölçülen sepet konumuna bağlıdır: kol
eklemleri22 sayım içinde ve hızları en çok100 sayım/s olmalı. Önceki20 sayım
koşulu, yerçekimi altındaki omuzun20/21 sayım sınırındaki ölçüm oynamasıyla
0.472s ek bekleme üretmişti;22 sayım koşulu2 sayımlık ölçüm payı içerir.
Bırakma sonrası kıskaç açıklığı20 sayım içinde doğrulanmadan yola çıkılmaz.
Bu koşullar en çok0.75s bekler, karşılanmazsa sürüş iptal edilir; yörünge
zamanı bekleme süresince dondurulur ve daha sonra ileri sıçramaz. Kıskaç açma
hareketinin kendisi yaklaşık0.55s sürer; bu süre gizlenmez veya nesne bırakma
algılandı diye raporlanmaz. Sıfır toplam duruş/jerk sürekliliği vaat edilmez.

Windows/Python3.12 üzerinde eski monotonic saati GetTickCount64/15.625ms idi.
Event.wait(3ms)20 örnekte ortalama15.59ms, time.sleep(3ms)3.37ms ölçüldü.
Artık QueryPerformanceCounter tabanlı perf_counter ve son tarihe göre,
en çok20ms bekleme kullanılır. JPEG kodlama/dosya yazımı kamera iş parçacığına
taşındı. Tork40 ve geri bildirim56–70 tek31 baytlık okumada alınır; motor
başına ayrı iki okuma kaldırıldı. COM5'in tek sahibi korunur. Firmware veya
Windows genel zamanlayıcı ayarları değiştirilmedi.

Son fiziksel tekrar: iki ardışık simülasyon çevrimi ve kapalı başlangıca dönüş
tamamlandı. Sonlu hedef yörüngesi ayrıca sayısal1430 sayım/s tavanıyla zamanlandı.
Programlanan hasat çevrimleri4.135s/4.135s; açık kıskaç ölçümleri arasındaki
gerçek süreler4.181s/4.158s. 200ms telemetride ilk taban ayrılışından açık
kıskaç geri bildirimine3.87s/4.01s bulundu (ENCODER_SIMULATION_PROXY).
Gerçek incirin sepete düştüğü doğrulanmadı. Üç saniye hedefi karşılanmadı.

Tam açılma/iki çevrim/katlanma22.932s;1082 hedef güncellemesi, ortalama47.18Hz,
en uzun aralık46.64ms, en büyük takip farkı123 sayım. Son iki çevrimli programda
ek bırakma doğrulama beklemesi toplam0.0685s. Önceki düzeltilmiş sürümde31.83Hz,
94ms ve0.4719s idi. Bu fark fiziksel hızın yüzde50 arttığı anlamına gelmez;
komut akışı daha sık ve düzenlidir. Son durumda altı motor tutuyor, kol kapalı.

Kanıt: GUNCEL/YAZILIM/ST3215_TEST/KAYITLAR/SURUS_20260920T220749Z/
flow_optimized_measurements.json, flow_optimized_status.json, sync_005.json.
140 ilgili test ve4 alt test geçti. Bir sonraki hız denemesinde gerçek
kavrama/bırakma ve sepet hacmi ayrıca gözlenmeli; nesne/kuvvet algılama,
tam çarpışma modeli ve3s altı gerçek toplama PHYSICAL VALIDATION REQUIRED.


## Yaklaşma sırasında kıskaç açma — 2026-09-21

Kullanıcı, incir doğru bölgeye ulaştığı sürece kıskaç açılmasının sepet
yaklaşmasıyla örtüşmesini açıkça istedi. Güncel kayıtlı rotada açılma için
0.18s yaklaşma penceresi var; bunun yanında gerçek kol konumları bırakma
duruşuna en çok64 sayım, sabit bilek dönüşü22 sayım uzaklıkta olmalı ve kol
hedeften uzaklaşmamalı. Bu, yalnız bu kayıtlı yol için denenmiş bir eklem
yakınlığı koşuludur; hesaplanmış balistik atış açısı/sepet hacmi modeli değildir.

Kıskaç kendi C2 zamanlamasını ölçülen açma koşulunun sağlandığı anda başlatır.
Öngörü bu koşulu atlayamaz. Koşul geç sağlanırsa açılma eğrisine ortadan
atlanmaz; kol yaklaşmaya devam eder, kıskaç kapalı tutulur. Açılma süresinden
0.18s kol yaklaşmasına taşındı; kıskaç hız/ivme limitleri değiştirilmedi.
Tam açık geri bildirimi gelmeden sepetten ayrılma engeli korunur. Bırakma
sonunda kol22/kıskaç20 sayım ölçüm payı kullanılır; taşıma/takip limitleri aynı.

İki fiziksel çevrim tamamlandı: açık kıskaç ölçümleri arası3.9778s ve3.9824s.
Program zamanı çevrim başına3.9776s; ilk açılma ve son katlanma hariçtir.
Açılma nominal sepet varışından0.10–0.17s önce başladı; varıştan açık kıskaç
ölçümüne kalan süre0.398–0.403s oldu (önce yaklaşık0.55s). Ek konum/kıskaç
doğrulama beklemesi0s. Bu zamanlar enkoder ölçümüdür, meyvenin uçuş veya
düşüş zamanını ölçmez. Kullanıcı son deneme için “Doğru bölgede bıraktı”
yanıtını verdi: USER_CONFIRMED_CORRECT_RELEASE_REGION. Otomatik nesne/kuvvet
algılaması ve3s altı toplama hâlâ doğrulanmadı.

Tam program22.4644s,1052 güncelleme, en büyük takip farkı160 sayım. En uzun
tek güncelleme aralığı0.223s görüldü;0.25s iptal eşiği aşılmadı. Bu nedenle
kesintisiz zamanlama garantisi verilmez. Son durum altı motor tutuyor,
kol kapalı başlangıçta.151 test ve15 alt test geçti. Güncel rota
GUNCEL/YAZILIM/ST3215_TEST/ARM_CONTROL/TEACHING/replay_plan.json.
Kanıt KAYITLAR/SURUS_20260920T222241Z/approach_release_measurements.json,
approach_release_status.json ve sync_004.json. Önceki sabit yerde açma rotası
verified_stationary_release.json adıyla geri dönüş için saklandı.


## Doğrudan hedef rotası — 2026-09-21 (güncel)

Kullanıcının isteğiyle elle tarif edilen ara rota kaldırıldı. Yeni direct_goals
planlayıcısı yalnız kapalı başlangıç (örnek417), kavrama hedefi (232) ve sepet
açık hedefini (324) kullanır. Eklemler birlikte C2 beşinci derece eğriyle sürülür;
hesaplanan orta düğümde durulmaz. Omuz için64 sayımlık sınırlı açıklık yayı
üretilir. Bilek dönüşü ID5 sabit kalır. Bu, eklem uzayında hedeflerden üretilen
rotadır; görüntüden öğrenilmiş politika veya engelleri algılayan yol planlayıcı
değildir. Mutlak Kartezyen model/table plane kalibrasyonu UNVERIFIED.

Güncel aktarım tepe hız ayarı1200 sayım/s; ilk açılma ve son kapanışta omuz/dirsek
ayrıca1000 sayım/s ile sınırlandırılır. Donanım sonlu profil3400/ivme50 olarak
kalır; gerçek yörünge bu daha düşük tepe hızlara göre zamanlanır. Kıskaç yaklaşırken
kapanır, sepet yaklaşmasının son0.18s bölümünde ölçülen yakınlık koşulu sağlanırsa
açılır. Bırakma konumu/kıskaç geri bildirim koşulları ve192 sayımlık hedef/takip
sınırları korunur. Gerçek kavrama/nesne tutma algısı yoktur.

İlk1550 denemesi ilk açılmada omuz takip farkı196 sayımda durdu.1000 açılma
sınırıyla sonraki deneme ilk taşımanın taban takibinde199 sayımda durdu.1200
aktarımı denemesinde181ms ana bilgisayar aralığı sonrası193 sayım omuz takip
hatası oluştu. Bunlar başarılı çevrim değildir; ilk2.932s hesap fiziksel olarak
başarılamadı. Eski sabit0.35s durdurma doğrulaması, hareketli motor durup yakalanan
hedefe geri gelirken tutmayı erken kesiyordu. Artık ölçülen başlangıç hızına göre
0.35–0.9s sonlu yerleşme payı var;192 sayımdan fazla sapma anında ilgili motoru
durdurur, son12 sayım/50 sayım/s doğrulaması aynıdır. Bu süre fiziksel frenleme
garantisi değildir. Otomatik yeniden tork açma veya eski rotaya devam yoktur.

80–250ms örnekleme boşluğunda yörünge zamanı en çok40ms ilerler; kayıp süre
raporlanır, özgün bitiş süresi uzatılmaz.250ms üzeri kesinti hâlâ iptal eder.
Başarılı son koşuda bu telafi gerekmedi. İki gerçek kol simülasyon çevrimi
3.6641693s ve3.6964537s sürdü (açık kıskaç ölçümünden sonraki açık kıskaç ölçümüne;
ilk açılma/son kapanış hariç). Önceki3.9778/3.9824s ortalamaya göre yaklaşık%7.5
azalma. İlk açılma ve son kapanış dahil program15.581737s;741 güncelleme,
47.56Hz ortalama,44.30ms en büyük aralık,77 sayım en büyük takip hatası.
Ek konum doğrulama veya zamanlama beklemesi0s. Son konum kapalı; altı motorun
tutması doğrulandı. Üç saniyenin altı ve donanımın gerçek maksimum hızı henüz
kanıtlanmadı. Gerçek incirin yeni rotada tutulup sepete bırakılması PHYSICAL
VALIDATION REQUIRED; önceki rota için kullanıcı onayı bu yeni rotaya aktarılmaz.

Güncel plan: GUNCEL/YAZILIM/ST3215_TEST/ARM_CONTROL/TEACHING/replay_plan.json.
Başarılı yedek: verified_direct_goals.json. Önceki kullanıcı onaylı yaklaşarak
bırakma rotası verified_approach_taught_route.json içinde korunur. Kanıt:
KAYITLAR/SURUS_20260920T225245Z/direct_goal_measurements.json,
direct_goal_status.json ve sync_003.json.171 test ve75 alt test geçti.

Deneme sırasında C: dolduğu için bazı kayıt yazımları başarısız oldu. Güncel
APK ile SHA256 eşliği doğrulanan143884632 baytlık build/outputs/apk/debug
önbellek kopyası temizlendi; güncel APK korundu. Android build/intermediates
silinmeden NTFS sıkıştırıldı (292450219→197733465 bayt). Başarılı son durum ve
ölçüm dosyaları yeniden yazılıp doğrulandı; bu işlem eski hata anının eksik
kamera kaydını yeniden üretmez.

## Güncel fiziksel engel — 2026-09-29

Kullanıcı, masa kelepçesi sağlamken en alttaki ID1 motorunun üzerindeki dönen
gövdede gözle görülür sağ-sol boşluk olduğunu doğruladı. İncelenen görüntülerde
arka plan sabit; bağımsız PnP hesabı etiketin gerçek görüntü hareketini doğruluyor.
Bu örnekte modelde görünmeyen yaklaşık 6° taban dönmesi, 34,400 mm uç
uyuşmazlığını açıklıyor: 6,038° yaw uygulanınca hesapta kalan konum farkı
3,366 mm, yön farkı 1,283° oluyor. Bu, yazılıma uygulanacak bir düzeltme değildir.

Enkoderin ölçmediği mekanik boşluk, tek bir kamera kalibrasyonu veya sabit açı
ofsetiyle güvenilir biçimde telafi edilmiş sayılamaz. Gevşek servo horn/gövde
bağlantısı ile motor iç dişli boşluğu henüz ayrılmadı; kesin gevşek parça TBD.
Yeni motor hareket denemeleri, bu boşluk fiziksel olarak giderilip etiket–model
eşlemesi ve kavrama yeniden doğrulanana kadar durduruldu. Torkun serbest
bırakıldığı veya fiziksel onarımın yapıldığı varsayılmaz. Başarılı yeni otomatik
incir toplama yok; v33 geometrik hedef filtresi geliştirme aşamasındadır,
derlenmiş veya telefonda doğrulanmış sürüm olarak kaydedilmez.

Sayısal kanıtlar: `reports/diagnostics_20260929/scan33_base_yaw_explanation.json`
ve `reports/diagnostics_20260929/scan33_axis_diagnosis.json`. Kaynakların SHA256
eşliği doğrulanarak kalıcı rapor dizinine kopyalandı. Önceki 65 mm yükseltme,
kullanıcının sonradan eklediği ayrı düzenek değişikliğidir; eski denemelerin
başarısızlığının geriye dönük açıklaması olarak kullanılmaz.

## Onarım bildirimi ve v33 teslimi — 2026-09-29

Kullanıcı dönen bağlantıyı sıktıktan sonra “Boşluk giderildi; 12 V kapalı” dedi,
ardından destekli tutma için beslemeyi yeniden açtığını doğruladı. Bu, kullanıcı
onarım bildirimidir; tamir edilen parçanın kimliği ve boşluğun tüm çalışma
duruşlarında giderildiği bağımsız doğrulanmış değildir.

v33, aynı çalışma alanındaki FigTargetGeometry değişiklikleri dahil derlendi;
290 JVM testi ve lint geçti, Xiaomi'de sürüm33 doğrulandı ve yayın betiğiyle
teslim edildi. 03:56:45–03:56:53 ikinci kısa tarama sonrası yeşil robot XYZ
görünmesi ara gözlemdir: 03:57:07'de 13,5 mm / 6,0° etiket–model uyuşmazlığı
yeniden kaydedildi. Başarılı fiziksel kavrama veya kalıcı eşleme doğrulaması yok.

DUR ardından yaklaşık 03:57:30'da açıkça bağlantı kesildi; köprü ölçülen
konumda tutmayı doğrulayıp kapandı. Bu sohbetin hareket/ADB işlemleri durdu ve
telefonun tek kontrolü kamera çalışmasını yapan diğer sohbete bırakıldı.
Kanıt: `reports/diagnostics_20260929/repair33_live.log` ve
`reports/diagnostics_20260929/repair33_stop.png`. Onarım öncesi kayıtlar korunur;
bu güncelleme önceki “v33 henüz derlenmedi” ve “onarım bildirilmedi” durumunu yeniler.

Onarım sonrası çevrimdışı hesap ikinci taramada fit RMS 0,708 mm, bağımsız
kontrol RMS 5,185 / en büyük 6,377 mm ve en büyük yön hatası 0,312° verdi.
Son geçişte açıklanamayan yaw 0,294°; bu, önceki farklı duruştaki yaklaşık 6°
sapmaya kıyasla yerel iyileşmedir, aynı yolun kontrollü tekrar deneyi değildir.
İlk taramanın başlangıcındaki 7,814° açıklanamayan dönme ve daha sonraki
13,5 mm / 6,0° ret korunur; tüm alan ve fiziksel toplama doğrulanmış değildir.
Kanıt: `reports/diagnostics_20260929/repair33_after_tightening_analysis.json`.


## Güncel yazılım ve fiziksel doğrulama — 29 Eylül 2026, v34
Kullanıcı ID1 üstü boşluğun onarıldığını bildirdi. v34 tam çevrim aday araması
ve eşzamanlı kamera düzeltmeleri293JVM+lint ile doğrulandı, güncelAPK yayımlandı
ve telefona kuruldu. Kaynak rehberi:
GUNCEL/YAZILIM/ST3215_TEST/KAYNAK_REPOLAR_VE_TOPLAMA.md.
04:12 kontrollü kısa eşleme15,5mm RMS/21,2mm max ile reddedildi. Yeni gerçek
incir toplama yok; kol DUR sonrası HOLDING. Onarım tüm çalışma alanının
doğruluğunu kanıtlamadı; kamera/etiket/enkoder fiziksel karşılaştırması gerekiyor.
Mevcut ölçüler,65mm taban yüksekliği ve hareket sınırları değiştirilmedi.


## Yanal görüş doğrulaması — 29 Eylül 2026, v35
Etiket konum ölçümü görüş açısı, perspektifte daralan görüntü genişliği ve
3B ölçüm duyarlılığıyla süzülür; kararlı yön ölçümleri çok karede birleştirilir.
Kalibrasyon kabul eşikleri korunur.301JVM+lint ve8native test geçti;12sentetik
20–70° görünüşte max0,637mm/0,179°. Gerçek63° yan görünüş kararlı/ölçüme uygun.
Bu, önceki15,5/21,2mm kamera–kol uyuşmazlığının çözüldüğünü veya fiziksel
kavramayı doğrulamaz. Uygulama kamera modunda; son köprü kapanışı ölçülen
konumda tutmayı doğruladı. Yeni hareket yapılmadı. Ayrıntı: ANDROID_OKU.md.


## 2026-09-29 — v35 physical pickup request: full fit rejected
User explicitly requested collecting the figs. Exclusive device control was
verified; other two FIGBOT chats idle, no other bridge found. Reopened v35 with
lift-only test mode, started COM5 bridge and connected. Fresh saved-calibration
reuse rejected60.8mm/15.1deg. No pickup command or target approach was executed.
Independent static comparison to the earlier v34 stopped pose: encoder change
only1count onID3, marker translation0.815mm/rotation1.815deg;170 background
features median displacement norm0.311px. This does not support a large new
camera move between these two captures; it does not validate the older saved fit.

Since repeated short fits preserved the old mount transform, performed ONE
bounded300count/s full12-pose calibration estimating both camera and marker
mount.04:41:09–46 scan completed all12 measurements but was REJECTED:
fitRMS7.2mm, heldRMS15.6mm/max20.5mm. No thresholds, encoder zero, model dimensions
or old calibration record were changed. This is physical calibration movement,
not physical grasp success. The previous v35 no-motion status is superseded
for this pickup-request turn only.

DUR then explicit disconnect issued. Last measured04:42:05 all motorsHOLDING,
stationary, positions[1907,923,3786,2730,1152,794],33–36C. Bridge subsequently
confirmed measured-position hold and exited. No automatic restart/retry.
Adjacent relative-rotation invariants differ5.28deg(samples7→8) and7.25deg
(samples9→10); one constant camera/mount transform cannot remove those
inconsistencies. Camera/marker estimation bias, attachment flex and mechanical
model/encoder error remain unseparated; no exact failed part is asserted.
Evidence: reports/pickup_v35_live/{full_scan_live.log,full_scan_frames.tar,
full_scan_analysis.json,static_comparison.json,after_scan.png,bridge_stdout.log}.


## Görsel elle öğretim başlangıcı — 29 Eylül 2026, v36
Kullanıcı sabit yan kamera ve elle gösterim istedi; destek/yerleşim onayı alındı.
Ham RGB kamera ve altı enkoder yaklaşık10Hz pasif kayda bağlandı. Kayıt öncesi
altı motorun torku zaten0; bu oturumda tork/hareket komutu verilmedi. İlk gösterim
kameraya en yakın incir için başlatıldı.303JVM+lint+16Python testi geçti.
Kayıt, eğitilmiş politika veya doğrulanmış otomatik tekrar değildir. Kaynak rehber:
GUNCEL/YAZILIM/ST3215_TEST/ELLE_GORSEL_OGRETIM.md. Otomatik hareket kapıları korunur.


First manual demonstration closed:82.453s,800 RGB frames and800 encoder/timing
rows; all800 video frames decode. All recorded torque states0; max camera/encoder
estimated separation130.2ms, max transport half-RTT31ms. User corrected the initial
FAILED response: fig was held in the gripper and transported to the drop location.
outcome.json preserves that correction and marks SUCCESSFUL_MANUAL_DEMONSTRATION.
Frames around40/44/48s show approach/closure/lift; no powered grasp or autonomous
replay was performed. Approximate initial target pixel226,360 was annotated from
initial.jpg, not a measured robotXYZ. First record remains local withSHA256.
Second separate record is being prepared for the middle fig; no trained policy yet.

Second manual demonstration closed: 102.704s, 1007 RGB frames and matching
encoder/timing rows; all video frames decode. User confirmed gripper pickup and
transport to the drop location. All measured torque states remained 0; maximum
estimated camera/encoder separation was 140.7ms. Together the first two records
contain 1807 frames over 185.157s. Success refers to user-confirmed hand-guided
demonstrations, not autonomous operation or a trained policy.

Default phone_teaching transport now permits only servo READ packets addressed
to IDs 1-6; a unit test verifies rejected writes do not reach serial I/O.
The third setup recording DEMO_20260929T020913Z aborted after 107 frames due to
the camera timing gate, before the user was told to begin. Exclude it from
successful training examples. Camera recovery diagnostics were blocked by tool
review without a detailed reason; third demonstration remains pending.

## Manual demonstration session closed — 2026-09-29
User repositioned the two distant figs after reporting they were unreachable.
DEMO_20260929T021205Z stopped on user request with 1362 frames and is labelled
UNREACHABLE_TARGET, excluded from successful demonstrations. The resumed left
fig episode DEMO_20260929T021731Z contains 679 frames over 69.406s. The right
fig episode DEMO_20260929T021941Z contains 740 frames over 75.515s. User explicitly
confirmed gripper pickup and transport to the drop location for both episodes.
Both videos decode completely with matching encoder and timing row counts;
all measured torque states were 0. Four successful hand-guided demonstrations
now contain 3226 frames. All recordings are stopped; no automatic torque-enable
or motion command was sent. Camera recovery succeeded on the user's continuation.
Summary: GUNCEL/YAZILIM/ST3215_TEST/ARM_CONTROL/TEACHING/TEACHING_SUMMARY.json.
Policy training and autonomous generalization remain unverified and incomplete.

## Four-object demonstration and offline learning — 2026-09-29
User required open-before-approach with a constant approach opening, correction
of manual drops/deviations, and improved fig/basket routes. Continuous episode
DEMO_20260929T022613Z closed normally:1282 decoded frames and matching encoder/
timing rows over131.75s, all torque0. User confirmed four successful transfers.
All five accepted episodes total4508 frames; earlier single-object episodes are
excluded from this training experiment pending late-opening review.

Corrected targets preserve raw RGB/state observations, limit arm jitter edits
to3counts, standardize approach opening to observed1559counts (synthetic target,
NOT physically validated jaw clearance), preserve measured per-fig held widths,
and exclude suspect spans with full history/action windows.660 samples remain.
Separate fourth-pickup test:497 training/163 held out within the SAME recording.
CNN/joint-history policy trained60epochs:held-out MAE69.245counts vs40.768counts
hold-position baseline. Deployment REJECTED. Separate full-data checkpoint fit
MAE32.108counts is not a generalization result. No autonomous execution occurred.

Independent route extraction preserves source phase endpoints, keeps arm still
while opening/grasping/releasing, and approach grip constant. Suspect internal
spans are omitted; proposed bridges are UNVERIFIED. Reviewed route candidates
at300/600/900counts/s yield132.880/77.086/60.302s respectively, compared to75s
reviewed demonstration task span. Numeric continuity/open/rest and sampled speed/
acceleration checks passed. These are offline estimates, not measured cycle times.
Collision clearance, floor clearance and powered grasp remain unverified.
No critical dimensions, motion gates, joint offsets or live motor settings changed.
14 affected-module/publication tests passed. Source and results published through
scripts.publish_current; teaching guide links all artifacts under GUNCEL/YAZILIM.

## First supervised empty physical route — 2026-09-29
User authorized low-speed empty validation and confirmed the table clear/hands
out. Current offsets matched recorded reference:ID1=4080,ID2=2861,others85;
mode0/model777. First recovered current-position hold, then opened ID6 to1559
(measured1556), without moving other joints. Used the demonstrated raw route,
not the rejected neural policy or900count/s optimized candidate. Session-local
taught envelopes were derived from recorded ranges; permanent limits unchanged.

Eight bounded approach waypoints completed in23.019s at requested<=200counts/s.
Final measured[2193,2858,2997,1276,1155,1556], max target error3counts, all stationary.
Jaw stayed1556 throughout. User explicitly confirmed no table contact/scraping.
Empty lifting/basket route then stopped at waypoint3:ID2 target2405, actual2428,
stationary for about1s, outside existing20count settling criterion. Timeout caused
FAULT_HOLD; neither tolerance nor timeout was widened and route did not resume.
Basket arrival and physical grasp remain UNVERIFIED. Last three read-only checks
confirmed all six torque1, speed0, movingfalse and goal error<=12. Last measured
[2192,2434,3039,1445,1155,1556]; current-position hold remains active.
Evidence:reports/first_taught_dry_run. Three offline harness tests passed.

## Bounded shoulder settling correction — 2026-09-29
User explicitly requested correction and continuation. Added opt-in ID2-only
settle_joint: verify all six stationary holds and fresh camera, initial residual
<=64counts, nominal SRAM goal plus at most3 corrections of<=12counts, total trim
<=36counts, speed60/acceleration1, bounded8s operation. Other-joint movement,
camera loss, STOP, feedback limits and excursion guards stop the operation.
After measured error<=8, establish a fresh hold and verify original20count
arrival criterion. No EEPROM/PID/offset/deadband setting or tolerance changed.

Physical sequence at desired2405: command2405 -> measured2428; command2393 ->
2417; command2381 ->2404. Measured hold settled at2409 (error4counts). This
demonstrates bounded compensation of a stationary residual at this pose, not
identification/repair of its mechanical or internal-controller cause.

Continued the raw empty carry route from recorded37s; remaining five dispatched
waypoints completed in11.851s, final[3214,1715,3203,2022,1152,1556], maximum
encoder target error12counts, all torque1/speed0/movingfalse. Jaw stayed open.
Recorded basket pose reached; physical grasp/container geometry remain unverified.
New small red object appeared on table in final camera image; user identification
requested before any additional motion. Evidence:reports/shoulder_settling and
reports/first_taught_dry_run/carry_remaining*.13 related tests passed.

## First supervised fig closure and short lift — 2026-09-29
User identified the red item as an unrelated object, then confirmed first fig
placed and hands withdrawn. Open-jaw reverse taught route and descent completed;
measured grasp pose [2191,2856,2995,1272,1153,1556]. New supervised_grasp helper
closes ID6 in at most24count increments at speed60/acceleration1, never below the
observed935count first-grasp target. Fresh camera, stationary other joints,
feedback, STOP and time gates apply. Early residual/raw-current rise stops are
contact candidates only; force is not calibrated and grasp must be observed.

First closure stopped at its initial28step budget with jaw947; measured hold
confirmed, no extra squeeze commanded. Corrected offline step-budget accounting
to allow small measured servo residuals without changing935floor or40s deadline.
Short taught lift preserved jaw947, measured [2192,2777,3001,1277,1152,947], all
stationary torque1. ID2 target2757 error20 is at existing arrival criterion.
Camera occludes the fig behind fingers; asked user whether fig actually lifted.
Loaded carry/release NOT executed or verified at this checkpoint. Evidence:
reports/first_fig_pick. Neural deployment remains rejected; this is a supervised
recorded route. The synchronized SDK is available in .venv-camera, the required
hardware runtime; an earlier .venv attempt failed before synchronized motion.

User subsequently confirmed actual first-fig lift. Carry then reached the
recorded basket encoder pose [3215,1716,3204,2022,1151,947], but the fruit was
visible separately on the table: FAILED_RETENTION_DURING_CARRY. Jaw stayed947
throughout, current_raw0 throughout; this does not measure grip force. Shoulder
correction reached2412 against2405 target. STOP file was set upon observing
separation, but the process had already completed. No release was commanded.
Do not equate COMPLETED_HOLDING in the motor log with successful fruit transport.
Split the next attempt into low lift, high lift, then turn; enforce the preceding
lift endpoint before turning. User asked to reposition the fruit; motion held.

## First successful supervised single-fig cycle — 2026-09-29
Second attempt: user repositioned the fig into the open fingers' approach area.
Open approach completed; corrected closure reached commanded935/measured939.
Short and then high lift executed separately. User confirmed firm retention
after high lift; turn image also visibly showed fig in gripper. Turn/carry
requested speed parameter120counts/s (profile cap200), with existing acceleration
and readback gates. Shoulder bounded correction again verified desired2405 at
measured2414. Jaw stayed939 throughout turn/carry. Basket encoder endpoint
[3215,1718,3203,2023,1152,939] reached, then jaw opened to1559/measured1556.
User explicitly confirmed fruit inside basket. Outcome:
SUCCESS_USER_CONFIRMED_BASKET_DELIVERY. Basket is outside camera; containment
evidence is user report, not automatic vision verification.

Three subsequent read-only checks recorded current hold; final all torque1,
speed0/movingfalse at[3215,1718,3203,2022,1151,1557].25 related tests passed.
Evidence:reports/first_fig_pick (attempt_01_evidence preserves failure).
This validates one manually positioned fruit with supervision and fixed setup;
does not validate arbitrary image-to-robot localization, all four targets,
unattended picking, neural policy, or optimized high-speed routes. Placement,
closure endpoint and speed changed together; no isolated cause for improvement
is established. Keep successful parameters as a supervised baseline only.

## Faster four-fig trial in progress — 2026-09-29
Opening1283 tested (measured1280–1286), closure935/measured939. First target
received a23count supervised base adjustment before descent, preserved through
lift and removed at high transfer. Camera visibly showed held fig at high lift
and after faster turn. Reached common basket endpoint and opened to1283; basket
containment not yet user-confirmed for this trial. Three figs remain on table.
Recorded spans excluding setup/inspection: approach12.695s, closure10.953s,
turn4.553s, carry6.415s, release3.284s. These are stage telemetry spans, not total
four-fruit throughput or guaranteed performance.

Second approach stopped on camera freshness fault near recorded52s checkpoint.
Five distinct fresh frames verified camera recovery; all motors held. Explicit
resume accepts only that exact camera fault and unchanged measured hold, then
completes nearby endpoint before continuing at90counts/s. Resumed approach
reached [2391,2807,3095,1181,1152,1280]. Camera showed user's head near the arm;
movement remains paused awaiting withdrawal. No second grasp yet. Evidence:
reports/four_fig_pick. No fault thresholds or EEPROM settings changed.

Four-fig trial continuation: user withdrew from arm area. Second closure reached
940 but fruit slid forward and remained on table after lift. Marked failed;
subsequent second-route turn/carry were EMPTY RETURN, not fruit transport.
Third approach completed; lower stage stopped on another camera freshness fault.
Live camera endpoint then returned503 and Android logged rejected105ms CPU skew.
Raw teaching export was still queued through marker processing alongside YOLO.

Android v37 isolates teaching export from ArUco/YOLO scheduling at50ms request
interval, retaining existing100ms CPU skew,300ms PC age,250ms transport limits.
Full Android unit tests and debug APK build passed. Installed v37 in camera-only
mode while serial owner was closed and measured motor hold unchanged. Eighty
consecutive distinct camera frames had no HTTP failures; final40 samples had
max age94.924ms and max RTT47ms. This is a bounded recovery observation, not an
unconditional reliability guarantee. Source:KolActivity.scheduleTeachingExport.

Explicit third-lower resume verified unchanged stopped encoders and original
planned segment before finishing at[2614,2994,2775,1261,1251,1280]. Fresh image
shows open gripper in front of the remaining figs, not enclosing a target;
NO third closure command sent. Fourth route is offline only. Three figs remain
on table; first basket containment for this trial still needs user confirmation.
Exact video frames were rechecked by sample.frame_index (not time*videoFPS).
Current geometry does not match all taught object locations; cause not established.
Do not deploy these four fixed encoder corridors as an autonomous localization
solution. Waiting for user's side-view description of the failed second grasp.

Follow-up: user did not witness the failed contact and said it appears the fig
was pushed slightly forward. Record this as an uncertain impression, not a
confirmed contact direction. Recorded image displacement still does not identify
finger depth/height error. On the next read-only reconnect attempt the camera
HTTP endpoint timed out and `adb devices -l` returned no attached phone. No motor
motion was issued. User asked to reconnect the phone and report any camera/base
movement before further live validation. Four-fruit task remains incomplete.
