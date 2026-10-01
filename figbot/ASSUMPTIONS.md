## Sıfırdan takip uygulaması — APK v0.17 / 2026-09-26

- Takip kararları FollowBrain'da (saf Java, 5 birim testi): turuncu = kamera hareketli,
  hedef saniyede en fazla bir kez yeniden nişanlanır ve yalnız ≥8 mm kayarsa; yeşil =
  tek düzgün bacak. Varış, enkoder geri bildiriminden 15 mm yarıçapla doğrulanır.
  0,7 s poz penceresinde ≤3 mm/0,5° hareket = sabit kabul (ObservationTiming eşikleri);
  bu eşikler titreşimli araç montajında yeniden ayar gerektirebilir (UNVERIFIED).
- Turuncu uyum "dur → planla → git" şeklindedir; hareketli hedefe akış (streaming) YOK.
  Her yeniden nişan bir bacağı durdurur, bu yüzden ~1 Hz'den sık olmaz ve sarsıntılı
  görünebilir; bilinçli tasarım kararıdır.
- Hedef Z'si kameradan değil sabit GRIP_Z=10 mm (kullanıcı ölçümü: incir tutma noktası
  zeminin 1 cm üstü); kamera derinlik Z'si yalnız ekranda gösterilir. Zemin kol taban
  düzlemiyle aynı varsayıldı (groundZ=0) — UNVERIFIED.
- Eski ekranlar (HomeActivity/MainActivity/PhoneHarvest) manifestten çıkarıldı; kod
  arşiv amaçlı derlenmeye devam eder. Manuel kamera noktası, uç ölçümü, sepet ağzı
  doğrulaması ve 3-incir otonom akışı bu sürümde yoktur.
- "ID1 is not stationary" hatası: bağlanma anında taban motoru hız>50 veya hareketli
  okunduğunda çıkar; v0.17 sekiz 200 ms denemeyle geçici yerleşmeyi bekler, kalıcı
  sürerse 12 V beslemeyi kapat-aç veya kolu destekle (kayıtlı önceki çözüm).

## Hedef test modu — APK v0.16 / 2026-09-26

Kullanıcı, karmaşık kurulum kapılarını kaldırıp "kayıtlı başlangıçtan kameranın gördüğü
konuma git, sapmayı ölçeyim" akışını istedi. v0.16 bunu uygular:

- Hareket izni, 2026-09-20/21 oturumlarında kullanıcı onaylı fiziksel IK sürüşleriyle
  doğrulanmış KAYITLI enkoder haritasına dayanır (withRecordedSessionValidation). Taze
  uç-konum ölçümü YAPILMADI; bu, ölçüm değil kayıtlı oturum kanıtıdır. Harita birebir
  korunur (ofset 4080/2861/85, referans, yön işaretleri, duruşlar değişmez).
- İlk açılışta ölçüler varsayılanlarla otomatik kaydedilir (sepet -100/+100/100 mm, üst
  150 mm, kavrama 10 mm, incir 20–40 mm). Bunlar kullanıcı anlatımı + tahminlerden
  türetildi; sepet iç yarıçapı 100 mm TAHMİN. Gerçek ölçümle düzeltilene kadar UNVERIFIED.
- Test modunda fig yükseklik aralık filtresi uygulanmaz: hedef XY'si kameradan, Z'si
  zemin+kavrama yüksekliğinden gelir. Yanlış kamera montaj açısı bu sayede ölçülebilir
  kalır; hedefler sessizce düşmez. Kavrama yok — kıskaç açık gider, fiziksel sapma
  gözlemlenir. Kullanıcı sapmayı bildirince montaj matrisi/asset düzeltilecek.
- Hızlar 300/700/1200 sayım/s; omuz/dirsek bacakları ayrıca 1000 sınırıyla yumuşatılır.
  RobotController'ın tüm çalışma zamanı kapıları (zarf, takip 192, ivme 50, DUR) aynen
  geçerli. Bu sürüm otonom toplama DEĞİLDİR; sepet/kavrama akışı v0.14 kodunda korunur.

## Sabit kamera montajı — APK v0.15 / 2026-09-26

Telefon kol tabanına sabit monte edildiği kurulum için v0.15, kamera–taban dönüşümünü
uygulama göması olarak getirir (assets/camera_calibration.json). Manuel 4 eşleme + 3
kontrol noktası ve üç zemin dokunuşu bu montajda istenmez; ARCore kamera pozu her karede
T_B_W = T_B_C @ inverse(T_W_C) ile birleşir.

- Kamera konumu KULLANICI ÖLÇÜMÜDÜR: taban arka ortasından +Y 200 mm, +Z 150 mm;
  sepet duvar üst kenarının ~1 cm altı olarak tanımlandı. Montaj yüksekliği 140–150 mm
  aralığı belirsizliğini korur; lens optik merkezi ile telefon gövde referansı aynı kabul edildi.
- Kamera bakış yönü (yaw -30°, pitch -45°, roll 0°) TASARIM TAHMİNİDİR; kullanıcı ölçmedi.
  Yön hatası, kamera konumu etrafında dönme hatası olarak tüm hedeflere geçer; 10° hata
  ~30 cm mesafede ~5 cm yer değiştirme üretir ve 2 mm IK doğruluğunu aşar. İlk fiziksel
  denemede bilinen ölçülmüş bir noktayla doğrulanmalı ve gerekiyorsa asset güncellenmelidir.
- Dönüşüm matematiği 6 birim testiyle doğrulandı (özellikle: sabit montaj pozu değişince
  rigidlik korunur). Fiziksel doğruluk, ARCore izleme kalitesi ve montaj sertlığı UNVERIFIED.
- Ölçüler diyaloğundaki ön dolu varsayılanlar (sepet merkez X -100/Y +100 mm, üst kenar
  Z 150 mm, kavrama payı 10 mm, incir yüksekliği 20–40 mm) kullanıcı anlatımından
  türetilmiştir; sepet iç yarıçapı 100 mm ve iç taban Z 100 mm TAHMİNDİR. Kaydetmeden
  önce gerçek ölçülerle değiştirilmelidir. Eğimli sepet tabanı tek düz zemin olarak modellenmez;
  bırakma duruşu elle öğretilir, sepet hacmi yalnız bırakma doğrulaması içindir.
- Kol uç-doğrulaması (3 bağımsız ölçüm), duruş öğretme ve tutma kapıları değişmedi.
  Bu sürüm tam çarpışma modeli içermez; ilk PC çevrimi ve gerçek kavrama/bırakma
  PHYSICAL VALIDATION REQUIRED.

## Android PC bridge — 2026-09-23

PC mode preserves the existing measured-calibration and controller limits. ADB
USB round-trip latency at continuous motor rate, disconnect hold on the physical
loaded arm, complete collision clearance, camera-to-arm accuracy, and autonomous
fruit success remain PHYSICAL VALIDATION REQUIRED. Loopback tests are not physical
validation. Bridge idle/partial-packet deadline is a provisional 0.5 s; hardware
only receives the controller's bounded nearby goals. Loss of serial communication
means stop cannot be confirmed; the bridge does not auto-release gravity joints.
Only one authorized Android device and one selected motor COM owner are supported.

## SO-101 supervised picking session — 2026-09-20

Follow-up completed: the held dried fig was carried right, released inside the
tape roll, and the empty gripper lifted clear. Visual evidence and final pose:
GUNCEL/YAZILIM/ST3215_TEST/KAYITLAR/SURUS_20260920T195145Z/incir_bant_icine_birakildi.*.
At the user's request to correct the software base limit, vendor CalibrationOfs
(register40=128) recentered ID1 in place. Old raw4026, new raw2048, old offset85,
new encoded offset4080 (−2032). The1-count discrepancy is encoder quantization;
exact coordinate shift from offsets is−1979, yielding the same physical recorded
trial interval as raw721–3277. First strict comparison stopped before reenable;
only base torque was off. New coordinates, subsequent hold and right rotation
to raw2541 were observed. Canonical base_reference.json is now required for this
hardware offset; pre-change raw base targets and references are historical.
No short-route4095/0 command, mode change, or other joint offset write was used.
This validates one supervised transfer, not general autonomous manipulation.

The following paragraphs describe the earlier phase before base recentering:

ID5 moved unexpectedly after a same-position hold request at raw3692; the
supervisor cut its torque and stationary raw4022 was read. Root cause UNVERIFIED.
The user power-cycled12 V; same-position holding then passed and subsequent
supervised negative roll steps followed their targets. This is not proof of a
permanent repair. EEPROM/model limits were not changed.

The user explicitly requested joystick-like visual control with meaningful
steps and direction reversal where needed. Local observed behavior: ID2 positive
lowers the tool in the present folded pose; ID3 negative raises/advances it;
ID4 negative extends the jaws forward; ID5 negative rotates their opening plane;
ID6 positive opens. These are local visual observations, not verified global
URDF direction signs or camera calibration. The user confirmed visible physical
link movement. Wrist poses initially outside old manual envelopes were returned
toward them with bounded slow steps; the old envelopes were not enlarged and
encoder zero was not crossed. The high raw branch of ID5 remains uncalibrated.

First close/lift attempt left the fig on the table. A later supervised attempt
successfully gripped the dried fig and lifted it clear of the table, visually
confirmed at command136 in session f08eedc6364149a0bbf45f4dcd571248.
Evidence: GUNCEL/YAZILIM/ST3215_TEST/KAYITLAR/SURUS_20260920T192232Z/
incir_kaldirma_basarili.jpg and .json. Measured lifted pose (IDs1–6):
4083,1978,3776,1276,3128,787; gripper target780. These raw values are a
historical observation, not a replay command or universally safe target.
Grip force, repeatable pickup and autonomous phone-to-robot motion remain
PHYSICAL VALIDATION REQUIRED. One tabletop pickup does not establish a payload rating.

## SO-101 payload screening — 2026-09-19

Controlled infill comparison (reports/SO101_INFILL_COMPARISON_20260919.md): 25% to 15%, retaining four walls and all other settings, reduces total sliced filament from 486.63 to 452.75 g across plates 01–03. Includes support/brim. Estimated reduction in shoulder-lift downstream parts is 22.19 g, approximately 4.8% of prior modelled moving assembly including motors. Slicer density 1.25 g/cm3 and extrusion-based per-part mass are estimates, not measured weight or strength. Existing print files and settings were not changed.

Comparison follow-up: Waveshare RoArm-M2-GA documents five servos, dual shoulder drive, 3+1 DOF, carbon fibre/5052 aluminium construction and 0.5 kg at 0.5 m (https://www.waveshare.com/product/roarm-m2-ga.htm; https://docs.waveshare.com/RoArm-M2-GA). Candidate only: reuse six existing motors as base 1, shoulder 2, elbow 1, wrist pitch 1, gripper 1; remove independent wrist roll. No CAD decision or print change. Dividing a hypothetical 14 kgf.cm joint load between two motors gives 7 kgf.cm each ONLY with ideal equal sharing; real mounts, changed moving mass, alignment/calibration, control, elbow/gripper limits, supply and thermal duty remain UNVERIFIED / PHYSICAL VALIDATION REQUIRED. Manufacturer 500 g claim is not adopted as our payload rating; prior 50–100 g estimate is not a measured maximum.

See reports/SO101_PAYLOAD_SCREENING_20260919.md. Sliced extrusion and official URDF imply approximately 0.46 kg downstream of shoulder lift and 10 kgf.cm self-weight torque at approximately 41 cm horizontal extension. Mesh-centroid mass distribution, 55 g motor masses, actual fruit lever arm and C047 rated-torque equivalence to ordered Waveshare ST3215 are UNVERIFIED. Fasteners/cables and dynamics are omitted. 50–100 g in suitable folded poses is a development estimate, not a rated payload. Printed strength, fatigue, thermal duty, power and collision-free useful workspace remain PHYSICAL VALIDATION REQUIRED. No geometry or print setting changed.

## DEC-084 print layout

Recorded ELEGOO256x256 bed/0.4mm nozzle reused. Actual current printer configuration, exclusion zones, PLA/support removability, first-layer adhesion and thin-shell strength remain UNVERIFIED / PHYSICAL VALIDATION REQUIRED. Generic0.16mm/4walls/100% fill/5mm brim is offline screening only. No machine G-code delivered.

# DEC-084 — Rigid tripod prototype / 2026-09-15

- USER REQUEST: thin rigid scoops; retain fruit after grasping; avoid new purchases where possible.
- CANDIDATE:1.2mm scoop wall,5.5mm root,28mm radial pivots,12mm cranks,24mm links,8mm slider anchors,0..35deg aperture,7.7717mm slider stroke,28-tooth module1.25 gear. These are design dimensions, not measured fruit fit or strength.
- PLA density1.24g/cm3 for CAD estimates only. Infill, printed weight, creep, fatigue and friction UNVERIFIED. Thin surfaces require slicer inspection and a sample print. No TPU required in this rigid-finger variant.
- New use of6 M2x8,6 M2L3,4 M2x6,4 M2L4 fits the PREVIOUS LIST'S buy quantities; actual owned quantities are UNVERIFIED. No purchase executed; no new metal shaft/bearing/motor type.
- Geometric fit of source MG90S horn is not proof of physical specimen fit. New drive has no force feedback; torque under motion and allowable fruit pressure remain PHYSICAL VALIDATION REQUIRED.
- Tool orientation/reach and old firmware need a new calibration; geometry-only URDF must not control the robot. This release is a CAD review, not a new print authorization.

# DEC-083 — Three rigid fingers / 2026-09-15

- USER CONFIRMED: photo illustrates mechanism, flexible Fin Ray fingers not required. Existing rigid scoop form is acceptable; no strings; simplicity and distal mass remain priorities.
- USER REPORTED: fig mass40–50g. Fruit diameter/height and allowable pressure remain UNVERIFIED.
- CANDIDATE ONLY: one G1 MG90S drives a rack/common slider and three rigid links. Pivot spacing, rack module, stroke, mechanical advantage, guide friction, cover access and mass are TBD; no physical torque or strength approval.
- Two-jaw comparison geometry is NOT the selected three-finger mechanism. Approximately72.60g complete tool vs71.61g previous tool is CAD/assigned-density only; cable/adhesive and actual material density are not weighed.
- Two-jaw sampled CAD collision checks and straight insertion checks do not establish continuous swept clearance, physical gear meshing, durability or safe fruit pressure. Review URDF has zero effort/velocity and is not a controller configuration.

# L1.5 scoop assumptions — DEC-082

Fruit width/height, TPU hardness/density/food contact, liner adhesive and safe grip force are UNKNOWN. 40–50g fruit does not establish its diameter. 1.6mm radial scoop wall and1mm TPU liner are prototype design choices; minimum normal loft wall may differ from radial section thickness. At12deg CAD closure sampled finger gap is1.1447mm, not zero; no promise of no dropped fruit. Finger/liner support removal and loaded PLA creep/strength PHYSICAL VALIDATION REQUIRED. No hardware or firmware increase is authorized by this CAD revision.

# Assumptions

- ASM-20260914-J1-CABLE-MEASURED (DEC-080 addendum): user reports boot width7mm, height3.9mm, outward protrusion5.5mm. These three dimensions supersede UNKNOWN in the prior cable entry; measurement uncertainty is unreported. Boot lower-edge distance above servo case bottom, lateral centre, exit end, connector and flexible bend envelope remain UNVERIFIED. Existing12mm window is retained: centred boot has nominal2.5mm clearance per width side. A0.5mm expanded envelope is checked conditionally for boot lower edge at assemblyZ4.5..17.6 on either short end. This is a positional range, not a measured installed position or print-fit approval.

- ASM-20260914-J1-CABLE / DEC-080: physical cable boot width, height, protrusion, connector/bend envelope and exit end are UNKNOWN; requested from user.12mm width / Z4..28 rounded-top windows in both J1 short-end walls are an UNVERIFIED candidate. Threading the flexible lead through the window is required; no claim of straight-drop insertion, strength approval or final fit. Remaining floor4mm and intact insert seat geometry are digital facts, not a load rating.

- ASM-20260914-DECK-ROOTS / DEC-079: L1.2 motor deck floor146x120x5mm and six outward triangular ribs are a geometry correction, not a load rating. Each nominal foot has over90% direct floor contact atZ75.9 (the audit threshold is geometric, not a material strength criterion). PLA layer adhesion, creep, fatigue, insert pullout, cable clearance and actual mounting remain PHYSICAL VALIDATION REQUIRED. About30.92g extra CAD solid-equivalent mass belongs to yaw, with shoulder downstream mass unchanged. No new hardware sizes; pending stock/printed bushing alternatives remain unresolved.

- ASM-20260913-ENGINEERING-RESET (DEC-076): User confirms R6 NOT PRINTED and figs40–50g. Fruit width/height, material allowables, continuous servo capability and grip damage threshold are UNKNOWN.100g remains a separate requirement.150/120mm links/tool30,-45mm and65/70/45/23.4/40g grouped mass budgets are explicit study assumptions, NOT new CAD/measurements. Candidate point reach does not establish physical travel or collision clearance. Stall derating/share fractions are sensitivity inputs, not rated capacities. R6 fruit-contact control sphere30–60mm is illustrative;50g does not imply a40mm fig. See reports/engineering_20260913/.

- ASM-20260913-FORMA-R6 / DEC-075: enclosure closures replace ALL horn peripheral fasteners and rim washers. Original source contours are not metrology of user's specimens. Trial lateral/axial play0.20/0.15mm; external M2x6 screws, L4 inserts,2mm printed closure and revised transition profiles are UNVERIFIED physical interfaces. Captive-pocket contact tests do not prove load rating, fatigue, layer adhesion or pullout. Robotizmo candidate inserts have stated OD3.2/L4 (M2) and OD4.5/L5 (M3); current2.9/4.2 pilot holes still require coupon testing. No real screw-head, cable boot or tool insertion envelope measured.
- ASM-20260912-FORMA-R5 / DEC-074 (historical, fastening superseded by DEC-075): original source profiles are not measurements of physical horns; spline, centre screw and servo envelopes remain approximations. R5 used large through-hole M2x5 and micro OD8 rim washers; R6 removes those arrangements.
- R5 structural candidates:6x16mm rounded fork section,6mm root webs,5.6mm upper motor-seat rails,12x9mm shoulder posts/gussets and4.5mm rotorweb. No FEA/materialtest supports a rated payload or fatigue life. Added local material increases modeled moving mass versus earlierV6; regenerated mass/moments are reported explicitly. Retainer footprint120x120mm, roof5.1mm andR58relief preserve existing capture/clearances digitally. Newretainer androtor must be used asmatchedR5parts, old2.5mmretainingscrewspacers removed. Free yaw/tilt/retention, motor/cable passage and real printed loadpath remain PHYSICAL VALIDATION REQUIRED.

- ASM-20260912-J1-CABLE-ACCESS / DEC-073: user says prior motor aperture was tight with cable; preserve the complete old41.5x20.5mm opening centredX=-10.15 independently of measured39.9mm case atX=-9.8. Supersedes0.4mm-per-end opening in DEC-072. Boot protrusion/width/height/exit location, connector envelope, bend radius and wire service loop are TBD. Nominal no-cable vertical insertion clipped the ring at5mm lift; local entry relief addresses that rigid interference only. Actual complete assembly/removal, all moving cables and screwdriver access remain PHYSICAL VALIDATION REQUIRED. No claim that every mount is optimized or ready to print as a validated full arm.

- ASM-20260912-J1-APPLIED: DEC-072 applies user-reported39.9mm case length,5.7mm spline OD and derived9.80mm longitudinal case-centre offset to FORMA V6 J1 and F6-01/F6-17 only. Supersedes the earlier 'recorded, CAD unchanged' status for this specimen only. Width19.7mm, height42.9mm,49.5x10mm ear pitch, earZ=-12, ear symmetry, transverse shaft position, horn and physical mount concentricity remain UNVERIFIED.0.4mm clearance per cavity side is an explicit print-fit candidate. Other MG996R specimens not measured; no global interface substitution.

- ASM-20260912-RETAINER-RUB: USER-REPORTED rubbing of outer bearing frame's inner upper surface against rotating plate, making rotation difficult. No contact photograph or feeler-gauge clearance measured; active physical print inferred PB02 from recent base discussion. DEC-071 supplies separate PB02 replacement-cap candidates and applies a minimum1.0mm roof clearance to active FORMA V6. Stock PB02 nominal gap0.4mm; V6 gap0.5mm above flange and only0.1mm above low pillar corner ledges. New PB02 flange gap1.0mm; V6 corner gap1.0mm/flange gap1.4mm with relief extending toR60. Remaining roof thickness2.4mm PB02/2.6mm V6 are UNVERIFIED print-fit/strength candidates. Original radial capture, race/ball geometry, shaft axes and fastening are preserved. Rubbing/strength/tilt must be physically checked on unloaded, supported, de-energized assembly; no powered test occurred.

- ASM-20260912-BASE-MEASURED: USER-REPORTED caliper readings using numbered guide `reports/20260912_TABAN_MOTORU_3_OLCU.png`: main case length L=39.9mm excluding mounting ears; nearest short case face to near outer spline edge g=7.3mm; same spline outside diameter d=5.7mm. Derived near-face-to-shaft-centre a=g+d/2=10.15mm; longitudinal case-centre-to-shaft offset L/2-a=9.80mm. This supersedes the unknown status of these three specimen measurements in ASM-20260912-BASE-AXIS, not physical assembly validation. Difference from PB02 assumed body-centre offset8.14mm is1.66mm; difference from FORMA V6 assumed10.15mm is0.35mm. These are parameter differences, NOT measured installed eccentricities: actual locating faces, ear-hole locations, seating clearance and transverse shaft offset remain unverified. TowerPro MG996R product specification lists nominal40.7x19.7x42.9mm (https://towerpro.com.tw/product/mg996R/, accessed2026-09-12); reported case length is0.8mm shorter. Do not infer a faulty/counterfeit motor or measurement error from this alone. No dimensional tolerance or accuracy uncertainty established. CAD/exports/BOM/firmware unchanged.

- ASM-20260912-BASE-AXIS: User reports apparent eccentric motor placement in the prior ball-bearing base. Source CAD surface-axis audit finds PB02 and FORMA V6 motor output / race axes both at XY(0,0), nominal radial error0mm. This is NOT a physical mounting verdict. PB02 inherits unmeasured case-centre offset8.14mm from `-.2*40.7`; V6 uses unmeasured10.15mm. Their2.01mm difference can materially affect the real shaft location in a body-locating seat. Actual body length, near-end-to-shaft centre distance, orientation and print seating remain PHYSICAL VALIDATION REQUIRED. V6 is not proven to correct the earlier physical problem. No CAD dimension changed in this audit. See reports/20260912_TABAN_EKSEN_KONTROLU.md.


- FORMA V6 actual servo-ear/horn dimensions and brass insert stock: **UNVERIFIED**. Proposal MG996R ear pitch49.5x10mm, MG90S28mm; M3 insert pilot4.2x5mm and M2 pilot2.9x4mm. These are explicit design trial values, not user measurements. R5 horn interfaces use recovered source-profile holes for MG996R and external rim-washer axes for MG90; the former24/12mm horn-pitch assumptions are obsolete (DEC-074). Most blind-hole bottoms>=1.5mm; finger ear M2 pocket has1.6mm back wall and must be coupon-checked; final boss diameter/fit/install temperature/torque TBD by insert manufacturer and coupon tests.
- V6 integration: wrist-to-fruit(38,0,-66)mm, ground pickupX740; base mounting100x100 M4, optional receiver pilot5.6x6. Actual chassis connection and printed plate load capacity are TBD. Gripper cord lines in CAD are schematic paths and excluded from rigid collision screening; their spool wraps/deflection and return-elastic routing are not simulated. Not every fastener is represented as a CAD solid; 25g additional moving-hardware scenario is not a proven bound.
- V6 base100mm shoulder height,166mm on rover,180/140mm links,66mm nominal fruit drop below wrist are proposed geometry per DEC-070. Rolling friction/axial stack/retainer clearance, original servo horn fit and insert retention are PHYSICAL VALIDATION REQUIRED.24x8mm ball geometry is inherited as a concept from PB02; printed ball quality and available stock not certified.
- V6 strength/dynamics: CAD solid volume x1.24g/cm3 is a full-material mass estimate, not weighed mass or actual slicer result. Hardware/cord/wire allowance reported separately.100g maximum object retained; no manufacturer continuous-duty rating available. Tendon friction, return elements, fruit diameter/pressure, paired torque sharing, actual pulse/angle relation, acceleration-limited motion and the earlier5V->2V battery-fed power fault remain open. V5 explicitly rejected, not current print recommendation.

- ASM-20260911-AERO-V5: Nominal V4 motor interfaces and user horn contours retained. MG996R55g/MG90S13.4g and PLA1.24g/cm3 are screening inputs, not weighed clones.25g extra hardware/wire allowance is provisional. Printed clearances, M3/M2 lengths,6x1mm aluminium sleeves cut30mm,6mm shoulder screws with16mm smooth sections,9.2mm brass cam followers and actual washer/nut thickness require bench fit. Hollow cavities and local slicer settings are not measured anisotropic strength. No FEA/fatigue test. Dense CAD volume is not actual sliced part mass. New three-finger tool adds material compared with V4; shorter lever arms and folded transfer are the torque-reduction strategy, not a claim of lower distal mass.

- ASM-20260911-AERO-V5-GRIP: Fingers move synchronously, not independently. Cam r=26-0.28q mm at q=-25..25deg;14mm radial stroke per finger, approximate contact diameter22..50mm with4mm pads. Actual fruit sizes and compliance UNVERIFIED. Empty closed pose is not a command to compress a40mm fig. Guide8.6mm/stem7.6mm and groove3.8mm/follower3mm are trial fits. User MG90 Arm03 contour remains pending physical confirmation. Food contact, force, contamination and bruising TBD.

- ASM-20260911-AERO-V5-MOUNT: Shoulder190mm and fruit offset(34,0,-110) supersede Rev-I placeholders in this branch. Plate132x142x6 with100x86 M4 centres and lower braces are integration geometry, not validated metal fabrication. Flat ground,20mm fruit radius, discrete joint/steering samples; not a continuous sweep. Wiring, terrain, actual wheels, camera visibility, physical strength and dimensions require verification. Full-horizontal100g load is not an approved duty point. Battery/converter5-to2V sag and prior broken arm remain unresolved. No powered action.

- ASM-20260911-REV-I: User explicitly returns to existing-servo direct-to-onboard-basket design, no conveyor or separate carrier. Rev-I180/140mm links, shoulder(550,+/-415,160)mm,60mm tool offset, basket side-entry floor305mm and example20mm fruit radius are provisional spatial study parameters, not hardware measurements or a print release. Stored254mm wheels/830mm track retained. Two symmetric arm instances retain the old integrated architecture; only one physical motor set is established. New closed hollow links, motor envelopes, metal pivot references and three-finger gripper geometry require detailed mechanical fit/drive design. Nominal body masses and PLA volume estimates are not weighed assembly loads. Sampled CAD clearances, ideal IK and static torque are not continuous collision, structural, thermal or motion validation. Power sag and broken-root repair remain unresolved physical gates. New arm coordinates are CAD angles, not current firmware servo commands.

- ASM-20260911-SPECIALIZED-FLEET: New user-proposed branch separates single-arm pickers and shared cart transport. Existing30-decare/estimated380-tree/estimated13,000-fruit/assumed40g inputs imply520kg/day and mean1.37kg/tree/day, not measured distribution.4/6/10/20 pickers at5/10 effective successful figs/min each, carrier actual20/60kg loads and10/20min complete tours with0.70 availability,100kg buffer,0.5–1kg local tray and2–4-tree stations are hypothetical comparison inputs, NOT selected capacities/dimensions or production quantities. Effective pick rate includes search, local driving, retry, local exchange and ordinary downtime; excludes extra carrier starvation and final depot delivery. Carrier scenario includes all nominal tour/handling legs;0.70 must not double-count observed delays.60kg is not the current vehicle's validated payload. Actual fruit type, safe tray filling, daily fall timing, orchard interconnection, route grade, complete autonomy/communications, towing/braking/parking/docking, measured rates, costs and damage thresholds TBD / UNVERIFIED / PHYSICAL VALIDATION REQUIRED. Existing three-vehicle requirements remain the old architecture reference pending alternative selection.

- ASM-20260911-LOW-ARMS-BELTS: User's wheel-radius-height proposal is interpreted as SHOULDER PITCH AXIS near127mm on the254mm-wheel concept, not pedestal bottom; final coordinates TBD. Paired inboard belts and two fixed work cameras are layout recommendations, not fitted/owned hardware. Belt inlet/outlet/width/angle, fruit diameter, camera FOV/depth, motor torque/current, mounting strength, steering/terrain clearance and food-contact/bruise performance UNVERIFIED. Example240mm lift and30/40deg slopes are scenarios only. Two ordinary cameras are not assumed a calibrated stereo pair.100g design payload and40g mean retained. No CAD/BOM or automation implementation; PHYSICAL VALIDATION REQUIRED.

- ASM-20260911-LIGHT-ARM-PLAN: Known planning baseline:100g max object REQ-MECH-012,40g mean REQ-PERF-003/ASM-031, PLA0.4mm nozzle/0.2mm layers ASM-076/081, ground-to-basket task. Unknowns are weighed distal components, fruit diameter distribution, actual filament/process performance, joint play, working-duty servo output and power transients. Rev-H2 base280mm plus V4 shoulder124mm gives404mm geometric shoulder height if the mount is retained.30/36cm total-reach scenarios are bench illustrations and not ground-reaching rover solutions. New scenarios use synthetic50/100/35/65g component masses,18/14cm or15/12cm links and4/3cm tool offsets, not adopted dimensions.40% stall screening is not continuous rating.90–105g distal print target/modifier settings are experiments. Hardware ownership and remote-gripper net benefit UNVERIFIED; PHYSICAL VALIDATION REQUIRED.

- ASM-20260911-METAL-FASTENERS: User requests metal screw/insert joints and purchase links, with an additional oval-arm reference. Photo insert internal thread, screw size/length, selected insert OD/length/pilot hole, soldering-iron tip compatibility and required joint loads remain TBD/UNVERIFIED. Product links in references/user_arm_preferences_20260911/README_TR.md are candidates, not owned or purchased BOM entries. Through-bolt/compression-limiter fixed joints and two-sided shaft/bearing pivots are proposed for review, not dimensioned or physically validated designs. No CAD/BOM changes.

- ASM-20260911-ARM-REFERENCES: User supplied three preferred reference screenshots, retained in references/user_arm_preferences_20260911. Preference supports a slender linkage-arm visual/mechanical direction and compact gripper; exact source kinematics, actuator model, dimensions, payload, licensing and material are UNVERIFIED. First screenshot is not assumed to be exactly three fingers. Prior explicit three-finger fig-gripper requirement remains; suction screenshot is not authorization to replace it with vacuum. No CAD or motor changes.

- ASM-20260911-FAILURE-REVIEW: USER-REPORTED: PC supply stable, battery-fed5V→2V upon driver connection; horizontal extended arm cannot lift fig, elbow folded succeeds; shoulder beam intermediate connection fractured during abrupt motion; additional print defects. Servo-free isolation, actual amperage, battery/converter OUT meter readings, fracture part identity and print process TBD. A4-04-UPPER-CARRIER is a candidate identification, not confirmed. Current CAD source spans300/220mm and hollow20/16mm square beam verified. Manifest-derived per-part PLA full-density masses are estimates, not weighed prints; whole assembly mass is not shoulder-moving mass.100g/52cm and36cm examples are explanatory scenarios, not measured fig or selected redesign. Three-finger low-distal-mass design requested; fruit diameter and minimum reach TBD. No live control, CAD, BOM or firmware changes; powered use of broken assembly on hold.

- ASM-V011-INSTALLED (2026-09-10): User freshly confirms phone connected, motor supply off, arm supported. Update-in-place succeeded and installed versionCode11 / 0.11.0-live-sliders verified. UNO unchanged; no assistant position command. Physical dragging behavior under load and broken-part repair remain UNVERIFIED. Supersedes deployment-pending state in ASM-V011-BREAKAGE.

- ASM-V011-BREAKAGE (2026-09-10): User reports abrupt motion broke the arm; affected part, cause, repair state and loading UNVERIFIED. Do not treat prior motor-off confirmation as current after this new physical trial. Prepare live-drag Android v0.11 and tests offline; ask fresh motor supply disconnected/support confirmation before install because replacement interrupts the active controller. No powered test or physical repair performed. Latest target continues after release until reached;10Hz coalescing and unchanged360 speed cannot guarantee smooth acceleration or prevent damage from large target steps.

- ASM-V010-INSTALLED (2026-09-10): User freshly confirms supply off and arm supported. APK v0.10 installed in place; package versionCode10 / 0.10.0-simple-controls verified. UNO firmware unchanged. No assistant motor command issued. User reports approximately270-degree manual travel; actual commandable range/model variant remains UNVERIFIED. Manual travel alone is not pulse endpoint calibration. Do not infer continuous360 capability.

- ASM-V010-DEFAULTS (2026-09-10): User reports500–2500us works, without identifying every tested servo or measured angle/load; record as USER-REPORTED, not all-channel endpoint validation. At explicit request Android defaults every joint to500–2500us and360 command deg/s, removes manual numeric target/Go and replaces Settings text with gear icon. User also requests broader ranges and360-degree testing; no supported broader pulse limits or360-position model identified. Retain current firmware bounds and explain unsupported physical capability. v0.9 installed phone screen and HC-05 V5 handshake were observed (saved screenshot/XML); user target acknowledgements visible, but assistant issued no target. v0.10 build and16 unit tests pass; installation needs fresh motor-off/support confirmation because user reports subsequent movement.

- ASM-V5-INSTALLED (2026-09-10): Fresh user confirmation: motor supply disconnected, arm supported, UNO and phone USB connected. UNO CH340 now COM3. Paced V5 upload and independent avrdude verify both passed all 9874 application bytes; binary SHA256 4281d15c012238b9f1ba9dfea43c53bd83b9086bcbd1e2e67b5f3217fe0f64f9. APK update-in-place succeeded on phone 2d9cc5ea, package versionCode 9 / 0.9.0-shoulder-calibration verified. No motor position command sent. UI inspection initially blocked by phone lock screen and Android INJECT_EVENTS permission; no permission bypass attempted. User asked to open the motor screen for read-only inspection. Bluetooth V5 handshake and physical movement remain UNVERIFIED; installation supersedes pending deployment in ASM-V5-CONTROLS.

- ASM-V5-CONTROLS (2026-09-10): User explicitly confirms shoulder speed360 selected and observed physical travel about90degrees for full0..180 slider motion. Also requests maximum default speed, all joints enabled by default, manual disabling and main-screen motion-only controls with Settings per joint. Implement v0.9/V5 with default360 and one-time enable-all after valid handshake, no auto-position at connection. Distinguish command speed from actual velocity and torque. Physical travel may reflect narrow1000..2000us mapping; actual stall, tracking time and supply remain UNVERIFIED. Add staged symmetric range selector, default unchanged until the user calibrates, and send slider target on release plus numeric Go to distinguish finger-tracking from point-to-point speed. All range steps/software paths tested, physical endpoints PHYSICAL VALIDATION REQUIRED. Previous motor-power-off confirmation preceded subsequent physical trials and is not reused for a new upload. V5 hardware and APK installation pending fresh disconnected-supply/supported-arm state and phone USB connection. No physical motion/reset was issued during implementation.

- ASM-V4-SHOULDER-TRAVEL (2026-09-10): After verified V4 upload, user reports paired shoulders still move slowly and cover only about 90 physical degrees. Code inspection confirms both Android sliders still allow 0..180 command units, speed choices reach 360 but default to 30 on Activity creation, and both shoulder pairs retain 1000..2000 us across that full scale. At selected 360 the nominal software interpolation traverses the full span in 500 ms; actual shaft response is not measured. Whether user has selected 360 and whether the 90-degree report describes physical full-slider travel or UI restriction are pending questions. Pulse/angle calibration, supply during this trial and loaded motion time remain UNVERIFIED. Do not assume the physical specimens tolerate 500..2500 us or widen coupled endpoints without calibration. No live serial port/reset/upload or motor command performed during this inspection.

- ASM-V4-FLASH-VERIFIED (2026-09-10; supersedes ASM-V4-FLASH-VERIFY-FAIL device state): User confirms USB reconnected with motor supply still off and mechanism supported; CH340 re-enumerates as COM4. Standard avrdude 8.0 and 6.3 writes continue to corrupt a single byte at varying addresses with page offset 0x2e; separate readback confirms one actual mismatch, not merely an untrusted upload report. Exact electrical/driver root cause remains UNVERIFIED. tools/uno_paced_upload.py implements bounded application-only STK500v1 transfers in 16-byte chunks with 4 ms pauses, ATmega328P signature and release SHA256 checks, per-page verification and complete final readback. Its three mock tests passed before use. Paced upload of the unchanged V4 release succeeds for all 9680 application bytes (binary SHA256 badfbdadbbf503b4b5c7dc2b6ec53bdc93b4910ac12307cdbc000d877e70b006). An independent avrdude 8.0 verify-only pass also verifies all 9680 bytes with exit 0. Logs: hc05-v4-speed360-upload-20260910-paced.log and hc05-v4-speed360-verify-20260910-final.log. V4 installation is now VERIFIED, but phone reconnect/STATUS4 handshake and physical 360-command-speed operation remain pending. No motor position/enable command issued; normal HC-05 build is installed (USB trace disabled). Bootloader, fuses and EEPROM were not programmed by the paced uploader.

- ASM-V4-FLASH-VERIFY-FAIL (2026-09-10): User explicitly confirms motor battery/powerbank supply disconnected and arm supported before flashing COM3 (CH340 VID 1A86/PID 7523). Release HC-05 V4 HEX SHA256 1057ca2ddb8849ad5daf4e7d619edeb9939b71257ecc4a9847d0b49d2c72c258 matches the tested package. Three avrdude uploads identify ATmega328P correctly and write 9680 bytes but fail readback at different addresses: 0x1aae (95 vs 91), 0x25ae (01 vs f2), 0x1b2e (bc vs db). A separate verify after attempt 2 confirms the same 0x25ae mismatch, so success must not be inferred. Current device image is UNVERIFIED, not a confirmed working V3 or V4. Motor power must remain disconnected. User requested to power-cycle USB and try another direct USB port/data cable before retry; serial/upload path, board supply and flash condition remain unverified. Logs: .codex_artifacts/arduino/hc05-v4-speed360-upload-20260910*.log and hc05-v4-speed360-verify-20260910.log. No motor command issued.

- ASM-SPEED360 (2026-09-10): User requests highest speed access and 360 degrees/second for the two-arm controller, attributing weak lift and roughly 90-degree slow rotation to a speed permission. Existing code is limited to 180 command deg/s with default 30; the paired pulse span is fixed 1000..2000 us. No separate torque authority parameter exists. Physical shaft travel, loaded speed and servo torque sharing remain PHYSICAL VALIDATION REQUIRED. Implement option 360 in both clients and UNO V4; retain default 30 and independent angle/pulse safeguards. Firmware upload and APK installation are pending disconnected motor supply/supported mechanism; no physical command or reset has been issued by this change.

- ASM-POWER-COMPARISON (2026-09-10): User reports unloaded converter output indication 5 V, 3.44 V with one motor and 2.40 V with two. Reports 12.6 V both unloaded and loaded at battery terminals, and 12.6 V at converter IN under load. Subsequently reports everything works correctly on powerbank. These are USER-REPORTED measurements/observations; converter OUT versus display calibration, equal loads between sources, contact resistance and actual current remain UNVERIFIED. Battery depletion is not established and is less supported than a converter/output-path or load interaction under these reported conditions. Do not label the battery or converter definitively faulty. User asks whether charging and use can be simultaneous. Manufacturer catalogue lists MT-4012C as 13.8..14.2 V, 2 A, but simultaneous load operation/charge termination behavior has not been verified. Recommend disconnected robot load during charging pending exact manufacturer guidance. Sources: https://mervesanteknoloji.com/statics/file/Mervesan_24__KTLG_Son_FiyatsYz_.pdf and https://www.yuasa.co.uk/info/industrial-applications/1213-2 . No new purchase.

- ASM-PCA-LOAD-COLLAPSE (2026-09-10): User reports converter indication falls from about 5 V unloaded to about 2 V immediately when the new thicker feed is connected to PCA9685, whereas the prior thin feed did not show this same symptom. Photos b5730e5c/767cf2bb show disconnected stripped output leads, visibly splayed copper strands and some servo plugs still attached to the PCA board. Red-to-V+ is the correct intended polarity, but end-to-end polarity, clamp seating and absence of stray-strand bridging remain unverified. Thicker wire itself does not explain increased resistive voltage drop; changed contact/short circuit, downstream motor load, input supply collapse and converter behavior remain possible. The previously requested all-servos-disconnected test has not been established by these photos. Next isolation test removes ALL servo and logic leads from PCA with all supplies off, corrects terminations, verifies unloaded output/polarity with a multimeter, then briefly powers only PCA V+/GND. Stop immediately if voltage collapses again. Do not diagnose a burned board or raise the converter setpoint on this evidence. No serial port was opened and no motion/reset/upload was performed.

- ASM-SHOULDER-ALIGNMENT-REPORTED (2026-09-10): User confirms both shoulder centres and cooperative direction were checked unloaded before coupling. Treat gross centre/direction verification as USER-REPORTED complete, superseding the pending confirmation in ASM-SHOULDER-LIFT-FAIL. This does not measure loaded torque sharing or binding. Prioritize the visibly thin common motor feed and load-voltage measurement next; do not keep asking the same alignment question.

- ASM-SHOULDER-LIFT-FAIL (2026-09-10): User reports the coupled shoulder servos cannot lift the arm's own weight after switching motor supply to the XL4016 setup. Photos c1c93385/6d5a6ca2/5a29b4ae/571fd08e show thick converter input leads but thin red/black jumper-type output leads with multiple inline/header contacts feeding PCA9685's motor terminal. Their resistance/contact quality and the voltage at the servo under load are UNVERIFIED; a converter display reading is not proof of delivered servo voltage. Actual display value is not treated as a multimeter measurement. Prior thin-feed issue remains physically visible. First correction is a short appropriately terminated 14 AWG positive/negative feed from OUT to PCA V+/GND, using already purchased wire, with power removed and mechanism supported. Shared V+ presently supplies mixed MG996R/MG90S; do not raise it speculatively. Firmware pair mapping is complementary around nominal 1500 us and has no per-servo centre/gain trim; horn alignment and cooperative motion are still awaiting user confirmation. Binding, damaged servos and insufficient gravity torque remain alternatives. Current moving mass/centre of gravity have not been measured; historical V3 mass estimates do not establish this assembly's demand. No reset, flash, motor command, CAD dimension change or purchase was performed. TowerPro original MG996R reference lists stall torque 9.4 kgf.cm at 4.8 V and 11 kgf.cm at 6 V (not continuous torque or validation of the user's specimens): https://towerpro.com.tw/product/mg995-robot-servo-180-rotation/ .

- ASM-FUSE-INVENTORY-CONFIRMED (2026-09-10): Read-only inspection of FIGBOT_SATIN_ALMA_MALIYET_TAKIBI_V6.xlsx, sheet Alınanlar, confirms row 46: 10 A blade fuses x3; row 47: waterproof 14 AWG inline blade-fuse holders x3; row 48: 7.5 A blade fuses x3. All three rows are marked Teslim Edildi from Motorobit. Rows 44 and 50 record respectively 2 x 1 m red and 3 x 1 m black 14 AWG silicone wire. Therefore suitable-type fuse-holder and heavy-wire purchases are recorded, contrary to earlier unresolved inventory uncertainty. Actual physical holder assembly, installed fuse and battery lead terminations still need identification; no need to infer a new purchase. Workbook was not edited. A fused supply lead means battery-positive routed through the inline holder near the battery, then to converter IN+; it is assembled from these parts rather than necessarily a separately purchased ready-made cable.

- ASM-XL4016-PHOTO (2026-09-10): Photo codex-clipboard-bdf5a35c-3a5f-4d1a-ace8-8a680e3b57be.png shows a W-263 V3.0.1 display buck module consistent with the user's XL4016 purchase. In the shown orientation, left terminal is IN and right is OUT, bottom terminals are marked + and upper terminals are negative (OUT minus clearly visible). Blue lower-right Radj potentiometer is the intended voltage adjustment, distinct from the small RW1 adjustment. Next stage is load-disconnected adjustment/measurement of 5.0 V across OUT using a multimeter; output must not yet feed PCA/UNO/servos. Existing 12 V battery is user inventory; input fuse/lead suitability, actual output setting, current capacity and thermal performance remain UNVERIFIED. Do not infer continuous 8 A capability or full-arm suitability from seller marketing. Supplier reference: https://www.robotistan.com/xh4016-voltaj-regulator-modulu . No hardware connection, energization, firmware upload or motor command was performed by the assistant.

- ASM-SERVO-POWERBANK-LABEL (2026-09-10): Photo codex-clipboard-0971b180-e094-4936-92cb-28dde347bee6.png identifies Samsung EB-P1100C. Label states OUTPUT 2 x 5.0 V / 2.0 A (MAX 3.0 A), plus 9.0 V / 1.67 A MAX and 12.0 V / 1.25 A MAX; internal battery 3.85 V, 10.0 Ah, 38.5 Wh. Interpret 5 V output as up to 2 A per port, up to 3 A combined, not 10 A output and not permission to parallel ports. Actual negotiated output and voltage under servo load remain UNVERIFIED. Current budget is a plausible limitation for the multi-servo arm but does not prove cause; motor-power-off isolation also leaves wiring/ground/contact/interference possibilities. 9/12 V must not be applied directly to servo V+. Existing 12 V battery / XL4016 is a potential regulated supply path pending module identification, output adjustment with load disconnected, wiring/protection and current/thermal validation; do not promise full-arm capacity from an advertised module rating.

- ASM-SERVO-POWER-PHOTOS (2026-09-10): New photos show the PCA9685 logic header with V+ and OE unused, olive/brown at VCC, red at SDA, orange at SCL and yellow at GND; UNO ends appear consistent with 5V/GND/A4/A5 but continuity is not proven by photos. The PCA motor screw terminal is fed by red/black leads with black Dupont-style housings very close to the clamp entrances; exact clamped conductor, contact quality, cable cross-section and connector ratings are UNVERIFIED. Do not declare reversed polarity or a proven loose contact from the image. Distribution block shows white incoming leads and red/black/olive outgoing leads, but complete endpoint routing, block internal continuity and polarity are not visible. No powerbank model/output label was included. Request label values and correct/verify the motor-current terminal connection with all supplies disconnected; do not infer that the powerbank alone is faulty. Source photos: 5b59b404, e3db1c92, 5d2245b3, c816385f clipboard images in the user's Temp directory.

- ASM-SERVO-POWER-ISOLATION (2026-09-10): Following the instruction to remove the Samsung powerbank motor supply while keeping UNO USB/logic/D8/D9, user reports the phone remains connected. The 00:55:06 snapshot of hc05-trace-20260910-004152.log contains further P/S motion commands and ongoing STATUS3 replies without a later captured ERR. Exact physical power-removal timestamp is not logged, so all accumulated heartbeat counts must not be attributed to the power-off interval. This strengthens a motor-power/load/interference association but does not distinguish powerbank current limitation, cable voltage drop, shared-ground routing, radiated interference or mechanical stall. Powerbank model/output rating and actual PCA supply/ground wiring remain UNVERIFIED. Stop/disarm before restoring servo supply; latest status has channels enabled/active despite motors being unpowered. No automatic reconnect of motor power is authorized by this successful isolation test.

- ASM-SERVO-POWERBANK (2026-09-10): User identifies the actual motor power source as a Samsung 10000 mAh powerbank, not the previously discussed battery/XL4016 plan. Exact model, USB output voltage/current rating, cable resistance, routing to PCA9685 V+, any shared UNO power path and loaded voltage remain UNVERIFIED. Capacity alone does not establish output-current capability. Next physical isolation test removes only motor power while preserving UNO USB, PCA logic power/common ground and D8/D9, then repeats slider commands without actual motor movement. No replacement supply or current rating was assumed.

- ASM-HC05-POWERED-FAIL (2026-09-10): User now confirms motors physically move before communication drops; earlier assumptions that servo power remained off no longer apply. Log hc05-trace-20260910-004152.log has one startup header and later malformed RX containing byte 0x02, followed by ERR FRAME and OFF ALL. Thus the observed failure is malformed serial input during a powered-motor trial, not a proven UNO reset. Best-effort logging can omit bytes, but cannot account for generating the captured 0x02 itself. Exact power source, voltage under load, ground routing and electrical interference are UNVERIFIED. User was instructed to support the mechanism, switch off motor supply and retain USB/D8/D9; power-source clarification and a same-firmware trial with only servo power removed are required before further powered movement. No firmware upload, UNO reset, timeout relaxation or motor command was performed during this investigation. Logged commands include wide pulse ranges and full-range movement; these are not physical calibration evidence.

- ASM-HC05-RECONNECT-OBS (2026-09-10): User later reported UNO response timeout. The old 00:32:15 log stopped updating after stop commands, but the monitor printed every byte to an unattended stdout pipe, which can block the reader; absence of later records cannot establish absence of radio traffic. Monitor now records bytes only to file; a 20,000-record mocked test verifies complete file capture and bounded stdout. Reopening COM3 resets UNO. The 00:40:55 log subsequently shows successful user-originated E0/E5 and P0/P5 commands, STATUS3 33,33 and no captured ERR. Physical motion/power was not observed. The observer was restarted again at 00:41:52 to apply the logging fix, resetting UNO and its outputs; this may cause an additional phone timeout distinct from the original report. Current firmware remains the verified AltSoftSerial D8/D9 build. Initial timeout cause and loaded operation remain UNVERIFIED; avoid further reset/upload while user may be exercising motors.

- ASM-HC05-ALT-PASS (2026-09-10): After the user reported moving UNO ends to D8/D9, Android showed ready. Snapshot at 00:36:52 of hc05-trace-20260910-003215.log recorded 181 H/LF heartbeats, 180 complete STATUS3 0,0 replies, zero captured ERR replies and no unexpected received bytes. USB trace is best-effort and can skip records under buffer pressure, so counts are not a lossless radio audit. This confirms a successful idle roundtrip in the observed test with channels disabled; it does not establish the exact prior fault or operation under servo load. Keep D8/D9, AltSoftSerial and the divider. Battery power, loaded motion and long-duration reliability remain PHYSICAL VALIDATION REQUIRED.

- ASM-HC05-ALT (2026-09-10): Receive-only SoftwareSerial log hc05-trace-20260910-002621.log contains only valid X/LF and H/LF packets and no overflow report after the user's attempts. This narrows the investigation but does not prove the full electrical path or a specific software bug; library and transmit behavior both differed from the failing build. HC-05 controller transport now uses AltSoftSerial 1.4.0 at 9600 baud on fixed D8 RX / D9 TX, reserving Timer1. PCA9685 output remains external I2C, with unchanged V3 parser/watchdog and disabled startup. Trace build compiled and was uploaded to COM3 with 10902 bytes verified; physical move from D10/D11 to D8/D9 and successful Android handshake remain PHYSICAL VALIDATION REQUIRED. Keep battery/servo power off. No APK or motor-core changes.

- ASM-HC05-RX-ONLY (2026-09-10): User corrected the D10 jumper after reporting it connected to A14. Subsequent trace hc05-trace-20260910-002306.log still contains malformed RX AC/LF and ERR FRAME among valid H/LF packets. Contact, grounding, timing and software origin remain UNVERIFIED. A temporary receive-only SoftwareSerial diagnostic was compiled, tested and uploaded to COM3 (5340 bytes verified); it disables all PCA outputs at startup, has no motor parser and never replies over Bluetooth. Android timeout is expected for this diagnostic and is not evidence of a new failure. A user connection attempt is required to capture receive-only behavior; normal motor firmware must be restored before future motor testing.

- ASM-HC05-RX-TRACE (2026-09-10): Live USB observation log hc05-trace-20260910-000944.log captured received bytes 52 E1 48 0A 48 0A 56 21 29 E1 48 0A FF. Two STATUS3 0,0 replies were followed by ERR FRAME. This confirms malformed input reaching the firmware receive stream while channels were disabled, not its electrical or software origin. Correct H/LF pairs also arrived, so the receive path is not completely disconnected; reliability, actual baud and signal timing remain UNVERIFIED. Next physical isolation step is a direct HC-05 TXD-to-UNO D10 jumper bypassing breadboard contacts, with USB disconnected during rewiring and servo/battery power off. No motor command or protocol relaxation was made. The earlier 180-second observation window may not have covered the user's retry and cannot prove absence of received data during it.

- ASM-HC05-ERRFRAME (2026-09-09): User reports correct isolated 1k/2k/3k divider measurements, successful Android HC-05 pairing, then ERR FRAME after verified COM3 upload. Pairing does not validate UART baud or every wiring connection. Stock AVR SoftwareSerial masks receive interrupts during replies while Android can transmit back-to-back startup commands; this is a source-confirmed failure mechanism, not a captured proof of the user's specific fault. NeoSWSerial 3.0.5 replaces only that transport on D10/D11 at 9600 baud, with the shared motor protocol/watchdog unchanged. Post-update phone-to-UNO readiness and electrical UART timing remain UNVERIFIED; motor power stays off for testing.

- ASM-083 (2026-09-09): Purchase tracker V6 adds the user-reported Fideco 150 mm carbon-fiber digital caliper at the displayed 252.00 TRY, preserving all 65 V5 rows. Quantity is not shown; one unit is assumed (UNVERIFIED). Recorded total becomes 8,774.90 TRY. VAT inclusion and the inherited 20% rate remain UNVERIFIED; seller, purchase date, order number, shipping and final payment are TBD. EK-20260909-02 is a recording group only. Source: codex-clipboard-5972a38e-f1de-481c-b569-f6ae80c303dd.png.

- ASM-082 (2026-09-09): User states the two new purchase screenshots are additional to existing purchases. Purchase tracker V5 preserves all 44 V4 transaction rows and appends 21 rows totaling 1,735.61 TRY, making the recorded total 8,522.90 TRY. Displayed prices are treated as line totals including VAT, following the existing ledger convention; VAT inclusion and the inherited 20% rate remain UNVERIFIED. Seller, purchase date, order number, final order payment, shipping and delivery status are TBD. EK-20260909 is an internal recording group, not a supplier order number. Adet10:10 / Adet50:50 are interpreted as individual piece counts; the resistor kit is one 500-piece kit and PLA is two sets, with total filament length/weight UNVERIFIED. The F-M jumper overlapping both screenshots is recorded once. The additional PCA9685 increases purchased stock from one to two. No engineering BOM or CAD change is implied.

- ASM-074 (2026-09-07): User again reports good motor fit; V4 preserves the fitted SNAP02/SNAP03 parts and nominal accepted servo cases. The latest report supplies no numerical gap/force/load measurements. All newly designed pin/socket/key dimensions are proposed prototype values in DEC050, not measured hardware data. Material shrinkage,0.8mm split-pin tips, barb force/retention/fatigue, beam stiffness, tower/key strength, actual centre screw/thread, bearing-stack fit/shims, cable routing, external bench restraint, electrical power and paired-shoulder alignment remain UNVERIFIED / PHYSICAL VALIDATION REQUIRED. New printed beam lengths204.6/128.6mm do not replace the V3 metal cut lengths. Discrete CAD motion checks are not proof of every continuous pose. PLA density0.00124g/mm3 is an estimate input; actual slicer/support mass and filament TRY/kg remain TBD. No purchase, motor action or printer job performed.

- ASM-073 (2026-09-07): User reports "MG996R doğru çalıştı diger kolları da basıyorum şimdi" following SNAP02/SNAP03 discussion. Treat as user-reported initial MG996R connection success; do not repeat that no physical feedback exists. Exact sample identification, load, speed, travel, centre screw installation, measured clearance, backlash and latch endurance remain UNVERIFIED. MG90 result not yet reported. Other prints in progress are user activity, not confirmed completed or agent-commanded prints. Full-arm structural integration and validation remain outstanding; no CAD/BOM change.

- ASM-072 (2026-09-07): SNAP03 uses native DisplayLists from user MG90servo_gear.SLDPRT, read with cadmpeg0.5.5. The four-arm envelope is a nominal source reference, not physical measurement or proof of MG90S spline compatibility. Mesh is closed/consistent after welding vertices to1e-5mm; faulty STEP topology excluded. Source license UNVERIFIED. Floor/pocket/latch dimensions are experimental DEC049 values. Motor planeZ5.75,0.25mm print clearance, actual shaft engagement, centre screw, material, slicer tolerances, hook flex/creep/fatigue and load rating are PHYSICAL VALIDATION REQUIRED. Full arm remains bolt/profile-based; source horn fit alone does not establish full clip assembly. No active printer state, empty bed, current filament or automatic part removal confirmed, and no printer command sent.

All values below are changeable parameters, not verified facts.

| ID | Assumption | Status / validation |
|---|---|---|
| ASM-001 | V0 target region is approximately 700 x 500 mm beside/in front of the base. | ESTIMATE - bench layout test required |
| ASM-002 | Upper/fore links begin at 300/220 mm and aluminium rectangular tubes. | ESTIMATE - optimization and physical review required |
| ASM-003 | Picked object design mass is 0.10 kg including uncertainty/adhesion allowance. | ESTIMATE - weigh representative fruit/debris |
| ASM-004 | Gripper/tool moving mass target is 0.22 kg. | ESTIMATE - update from produced BOM |
| ASM-005 | Joint trajectory limits are conservative digital-prototype values. | UNVERIFIED - actuator validation required |
| ASM-006 | Funnel is placed on the base-left side to shorten return travel. | ESTIMATE - camera/FOV and collision review required |
| ASM-007 | V0 uses Camera Module 3 Wide over a controlled planar work surface; RGB-D is a later upgrade if height uncertainty fails testing. | PHYSICAL CALIBRATION REQUIRED |
| ASM-008 | Silicone hardness candidates are nominal 10A, 20A, and geometry variant; suitability and food contact are supplier/test dependent. | PHYSICAL VALIDATION REQUIRED |
| ASM-009 | Published motor/gearbox envelopes and mounting dimensions represent delivered revisions. | Verify incoming parts against controlled drawings before machining mounts |
| ASM-010 | The J2 10:1 gearbox may carry short peaks above its 6 N.m permissible torque but below its 12 N.m published momentary torque. | PHYSICAL VALIDATION REQUIRED; counterbalance and acceleration derating required |
| ASM-011 | P0 Rev-G retains the approximately 650 x 600 mm frame, 830 mm wheel-centre track and 510 mm wheelbase; overall tyre width is approximately 890 mm. | REV-G CALCULATED PACKAGING - supplier parts, transport width and stability layout required |
| ASM-012 | Two 24 V 250 W brushed geared motors can move the P0 platform and an estimated 20 kg payload. | PHYSICAL VALIDATION REQUIRED; output rpm, torque, stall current, shaft and duty data absent |
| ASM-013 | The final chain ratio can cap a 254 mm drive wheel near 0.5 m/s after the selected motor output rpm is measured. | CALCULATED DESIGN TARGET; sprockets remain TBD |
| ASM-014 | A 24 V 18 Ah LiFePO4 set provides at least 60 minutes for the P0 duty cycle. | PHYSICAL VALIDATION REQUIRED; verify BMS current, usable Wh and cut-off |
| ASM-015 | Raspberry Pi 5 can run the first wide-camera line/AprilTag/large-obstacle pipeline at the required low speed without an AI accelerator. | BENCHMARK REQUIRED |
| ASM-016 | P0 cost is a single-unit retail estimate and excludes engineering labor, commercial certification, margin, warranty reserve and volume discount. | COST MODEL BOUNDARY |
| ASM-017 | P0 packaging uses four equal nominal 254 x 60 mm wheels, 510 mm wheelbase, 830 mm track, +/-30 degree steering limit and a 24 V 100 mm-stroke linear-actuator class. | REV-E ESTIMATE - delivered hubs, knuckles, linkage and actuator must be measured before bracket/hole release |
| ASM-018 | A 400 x 350 x 180 mm front-centre basket and two removable arm bases at X=100 mm, Y=+/-260 mm provide a workable side-by-side ground-pick/drop layout on a 650 x 600 mm frame. | REV-E DIGITAL PACKAGING ONLY - stability, collision, reach and mass-property tests required |
| ASM-019 | Each Rev-G arm can collect only after the vehicle places the target in its side lane: X=420..600 mm and Y=180..320 mm left / -320..-180 mm right, Z=0..80 mm. It then folds inward to the adjacent basket opening. | UNVERIFIED - the sampled lane is 100% analytic-IK reachable and avoids the basket in the representative straight approach, but full dynamic dual-arm/wheel/basket sweep and physical validation remain required |
| ASM-020 | Two lightweight MG996R prototype arms can be mounted at `(120,+250)` and `(120,-250)` mm on separate 110 x 110 mm adapter plates. | DIGITAL PACKAGING ONLY; published 40.7 x 19.7 x 42.9 mm body is controlled, while delivered tabs, spline/horn fit, bracket stack, horn zero and cable bend remain INCOMING INSPECTION REQUIRED |
| ASM-021 | An ARCore/Depth-capable Android phone or tablet can provide useful handheld target observations after two-point `base_link` registration. | UNVERIFIED — compare repeated observations with independently measured 3D control points; not authorized for arm motion |
| ASM-022 | A public-data detector adapted with 18 supplied phone scenes and synthetic small-object compositions can recognize representative collectable ground figs, including bruised/purple/dark `hurda incir`, from the planned approximately 600 mm camera height. | UNVERIFIED — v0.6 fits all 54 unique labelled collectable figs across the defined supplied-scene audit views at threshold 0.35 with no extra boxes, but every scene was used for adaptation; collect new raw phone/FIGBOT frames for an independent test |
| ASM-023 | Two instances of the Rev-G 605 mm lightweight servo arm can replace the earlier purchased-arm packaging references on removable adapters beside the front basket. | DIGITAL INTEGRATION AND PHYSICAL STABILITY VALIDATION REQUIRED; delivered adapter patterns, mass properties, power and interacting full sweeps remain open |
| ASM-024 | The earlier 50-100 objects/minute objective in a 5 m2 area remains a stretch study beyond the first Rev-G acceptance target. | UNVERIFIED; first acceptance is 30/minute/vehicle per DEC-032, while 50-100/minute would require 1.2-2.4 s per arm cycle or a different intake architecture |
| ASM-025 | A 150 mm long front-side opening in each basket wall can accept the 100 g object and gripper release path without jamming, bouncing out or damaging the object. | PHYSICAL VALIDATION REQUIRED; final object envelope, opening height and soft liner remain TBD |
| ASM-026 | Left/right half-plane assignment permits useful parallel work from two arms; overlap arbitration and short shared-volume interlocks do not erase the theoretical throughput gain. | UNVERIFIED - coordinated motion simulation and timed physical trials required |
| ASM-027 | Representative irregular objects will move from the front release zone to the rear on a removable liner within an adjustable 5-12 degree slope range; 8 degrees is the initial CAD setting. | ESTIMATE / PHYSICAL VALIDATION REQUIRED - measure feed reliability, pile-up, impact speed, marking and cleanability with representative objects |
| ASM-028 | A task-specific arm using fewer driven axes, standard tube/plate construction and encoder bus servos may reduce repeated-unit hardware cost versus two complete development arms. | UNVERIFIED - `reports/CUSTOM_ARM_MAKE_OR_BUY_STUDY.md`; obtain NRE plus 1/10/100/500-unit quotes and validate torque, speed, life and serviceability before selecting make versus buy |
| ASM-029 | The user estimates that approximately 13,000 figs fall per day across the three marked gardens during the peak period. With the satellite-image estimate of 380 trees, this corresponds to an aggregate mean near 34 figs/tree/day; the five annotated tree counts of 50, 20, 60, 80 and 100 are treated as local samples rather than a garden-wide mean. | USER ESTIMATE / PHYSICAL VALIDATION REQUIRED - confirm with several consecutive days of weighed or counted collection; the 380 count includes possible saplings and uncertain/merged crowns, and daily fall varies with tree age, weather and collection timing |
| ASM-030 | The earlier screenshot-derived polygon estimate was approximately 22.8 gross decares, but the user subsequently stated that the total area is 30 decares. The 30-decare user value supersedes the screenshot estimate for fleet feasibility only. | USER-STATED / CADASTRAL VALIDATION REQUIRED - neither value is a title-deed or cadastral measurement |
| ASM-031 | The 30-decare area is divided evenly among three vehicles, one 10-decare zone per vehicle. Peak daily fall is 13,000 figs across the fleet, each fig averages 0.04 kg, and each vehicle carries a nominal 20 kg basket load. | USER INPUT / PHYSICAL VALIDATION REQUIRED - weigh daily harvest and verify payload stability |
| ASM-032 | Each vehicle sustains the user-targeted 30 successful collections/minute including perception, local repositioning, gripping, deposit and retries but excluding basket-unloading trips. Each of nine unloading events takes six minutes total, and the daily work window is seven hours. | USER TARGET / UNVERIFIED - requires 15 successful objects/minute per arm on the current two-arm concept; timed 30-minute, 60-minute and full-zone tests required |
| ASM-033 | A 24 V 18 Ah LiFePO4 pack provides 80% usable nominal energy and operations preserve a further 15% reserve. Mobile average-power scenarios are 120, 150, 200 and 320 W; 150 W is a design target rather than a measured value. Charger current is provisionally 3 A at 90% efficiency. | UNVERIFIED - log bus Wh/current and verify the delivered BMS and charger specifications before purchase |
| ASM-034 | The 10-decare vehicle zone is represented as a 100 x 100 m equivalent square with 8 m orchard-row spacing, 13 row passes, a 1.10 turning/avoidance factor, and nine additional 100 m unloading-return traversals. The resulting 2.33 km route is driven at 0.4 m/s. Traction is estimated at 45 Wh/km, equivalent to 64.8 W while moving; during collection both arms average 40 W; Pi/camera and control/power electronics average 12 W and 5 W respectively. | ROUTE/POWER ESTIMATE - the 45 Wh/km value is deliberately above the 12–22 Wh/km implied by a current 648 Wh, 30–55 km e-bike example; replace with mapped GPS route and logged 24 V Wh |
| ASM-035 | One MG996R at J1, two mechanically coupled MG996R units at J2, one MG996R at J3 and an adjustable shoulder counterbalance can meet the 4.0 s average cycle required for 15 successful picks/minute/arm. | UNVERIFIED - 0.15 s/60 degree at 6 V is a no-load catalogue value and 11 kg.cm is stall torque; paired hobby servos may fight each other if horn zero or linkage stiffness differs. Run loaded current, temperature, repeatability and 10,000-cycle tests before accepting the architecture |
| ASM-036 | Delivered MG996R/MG90S clone bodies will enter nominal openings with 0.8 mm total clearance, the supplied horns will match the radial-slot adapter and purchased 20 mm tube will enter a 20.5 mm socket. | UNVERIFIED / FIRST-PRINT FIT GATE - print FIT-001 through FIT-007, including the horizontal MG90S cradle coupon, measure all delivered parts and revise the parameters before structural printing if any part binds or has excessive play |
| ASM-037 | Aero V2's nominal 0.8 mm hollow PETG fairings, estimated at 78.5 g total from CAD volume, will provide the desired finished appearance without materially preventing the four-second arm-cycle study. | UNVERIFIED / PHYSICAL VALIDATION REQUIRED - compare timed current, temperature, vibration and cycle tests with all fairings removed and installed; omit them for the lightest first motion test |
| ASM-038 | Aero V2 uses a body-length-times-0.20 output-shaft offset only to position the visual MG996R reference bodies on the joint axes. | UNVERIFIED VISUAL PROXY ONLY - do not derive bracket geometry from this value; measure the delivered body-to-spline centre offset before structural print release |
| ASM-039 | The requester accepts the specified nominal MG996R/MG90S clone dimensions as standard and directs the first bench prototype to proceed without delivered-sample metrology. | USER-AUTHORIZED PROTOTYPE ASSUMPTION - dimensional fit remains physically unverified and any clone deviation may require reprint |
| ASM-040 | Initial incoming-servo check uses one unloaded servo, an externally regulated and measured 5.0 V supply, USB-powered UNO, and 1400/1500/1600 us signal commands. | PHYSICAL VALIDATION REQUIRED - delivered clone pulse-to-angle mapping, power-component arrival, wiring and loaded supply performance are UNVERIFIED; these pulses are test commands, not calibrated joint limits. |
| ASM-041 | User reported reversed left/right on 2026-09-05. Bench firmware V2 maps left to 1600 us and right to 1400 us. Fast test sends unramped 1000/2000 us targets with 700 ms dwell for three round trips, returns to 1500 us and disables signal. | USER-OBSERVED DIRECTION CORRECTION / PHYSICAL VALIDATION REQUIRED - 1000/2000 us are test command limits, not calibrated 0/180 degree endpoints. Dwell is not measured travel time. Actual speed, sweep angle and 5 V/2 A powerbank transient capability remain UNVERIFIED. |
| ASM-042 | Bench V3 lets a fresh c/l/r/t command re-enable a detached servo; boot and completed-test states remain signal-off. Only x can interrupt a running fast sequence. User reported approximately 5 V at motor terminals and intermittent then working motion. | UI BEHAVIOR VERIFIED IN SOFTWARE / PHYSICAL VALIDATION REQUIRED - static multimeter reading does not capture short supply dips; actual motion speed, powerbank shutdown and connector integrity remain unverified. |
| ASM-043 | V4 GUI uses a 0–180 nominal command dial mapped linearly to the existing 1000–2000 us envelope. Speed 0 means unramped; 30–360 nominal command degrees/s limits generated PWM position slew. | PHYSICAL VALIDATION REQUIRED - dial is not measured shaft angle; rate is not measured mechanical speed. Ramp starts at last emitted pulse (1500 us after boot), not actual shaft feedback. |

- ASM-044 (2026-09-05): User reports ~90 degrees physical travel with V4 1000–2000 us and authorizes remapping. V5 uses provisional 500–2500 us for UI 0–180, inferred by doubling pulse span around 1500 us. Clone endpoint clearance and actual 180-degree travel remain UNVERIFIED / PHYSICAL VALIDATION REQUIRED. Default manual ramp 60 command deg/s; automatic test retains narrower 1000–2000 us. No automatic wide sweep is commanded at startup.

- ASM-045 (2026-09-05): Rev-H dimensions in DEC-037 are provisional placement assumptions, including 30-degree rearward slope, 26 mm nominal tire-to-base height gap and camera/equipment envelopes. Single-arm hardware is modeled; no second arm purchase is assumed.
- ASM-046 (2026-09-05): Rev-H pickup pad midpoint Z=30 mm is an example object-contact target, not a measured fig dimension. The fixed wrist tilts approximately 69.84 degrees from its reference at this pose; lowest arm solid is about 5.62 mm above an ideal flat plane. Ground irregularities, print flex, jaw opening and successful grasp are PHYSICAL VALIDATION REQUIRED. Motion samples do not establish continuous clearance or machine safety.
- ASM-047 (2026-09-05): Release is a direct drop onto a front apron. Reliable gravity feed at 30 degrees, fruit damage, timed throwing, payload retention, camera intrinsics/FOV and loaded servo motion remain UNVERIFIED. Firmware nominal 0-180 mapping must not be equated with the CAD joint coordinate conventions.

- ASM-048 (2026-09-05): Rev-H2 follows the user's two-arm and half-slope request: 15-degree basket. Motor/gearbox/bearing dimensions in rev_h_running_gear.py are UNVERIFIED placeholders. 20 mm shafts and 6 mm reference keys are not a strength-verified selection. No purchased running-gear model or output torque is assumed known.
- ASM-049 (2026-09-05): Under-floor envelopes were repacked for a 305.77 mm entry and 240 mm camera height. Battery 180x100x100 mm, computer 200x140x60 mm and power 140x100x55 mm are space reservations. Verify actual delivered battery and enclosure dimensions before manufacture.
- ASM-050 (2026-09-05): Front tire collision checks sample five steering angles per wheel against fixed geometry. They do not solve steering linkage closure/Ackermann tracking, actuator stroke or cable motion. Straight-ahead link contacts and separate wheel-bearing support paths are modeled. Entire drivetrain, brakes, outdoor dirt protection, load ratings and manufacturing tolerances need physical/component validation.

- ASM-051 (2026-09-05): User photos establish an MG996R-labelled servo and several supplied black output-horn forms. They do not establish spline tooth count, hole pitch, hub height, strength or centre-screw thread. Retain nominal clone body assumptions; prefer supplied spline interfaces over printed splines.
- ASM-052 (2026-09-05): User states ordered printer ELEGOO Centauri Carbon 2 Combo. Manufacturer manual specifies 256x256x256 mm and included 0.4 mm nozzle. Delivered configuration, filament, tuning and slicing remain UNVERIFIED. No filament purchase is inferred.
- ASM-053 (2026-09-05): Passing STL/legacy geometry tests is not assembly readiness. DEC-039 documents measured digital defects independently of motor body tolerance. Tube cut lengths, horn mounting stacks and working gripper kinematics remain TBD.

- ASM-054 (2026-09-05): FreeCAD editing bridge uses the installed FreeCAD 1.1.3 and existing local CadQuery environment. Seven editable dimensions are a limited design-exploration interface, not fully reconstructed native sketch histories. Altered arm lengths preserve pickup joint angles, changing end-effector position; bracket connectivity, collision, mechanical suitability and print readiness of edits are UNVERIFIED. Default geometry retains all DEC-039 defects.

- ASM-055 (2026-09-06): AERO V3 supplied-horn references use nominal radius-8 mm MG996R and radius-6 mm MG90S mounting holes and the user's accepted body dimensions. Photo scale does not establish actual horn pitch, spline, centre thread or flange stack. Test the provided coupons and use each servo's supplied horn/centre screw; never force a mismatched spline.
- ASM-056 (2026-09-06): V3 printed journal sleeves/thrust washers are consumable low-cost bench parts with nominal 0.4 mm diameter and axial play. Fit, wear, friction and nut-trap strength are PHYSICAL VALIDATION REQUIRED. Full sets are not a calibrated ELEGOO slicer profile; filament is still unspecified.
- ASM-057 (2026-09-06): V3 mass/gravity calculations use full CAD PETG volume, nominal servo weights, aluminium profiles and a 100 g object aligned at wrist X. Actual object CG, printer mass, fasteners/cables, acceleration, static friction, elastic deflection and servo thermal duty remain UNVERIFIED. Small computed wrist gravity moment must not be treated as measured or guaranteed loaded performance.

- ASM-058 (2026-09-06): `simulation/aero_v3_feasibility.py` evaluates unchanged V3. Wrist pickup Z=102 mm and fruit CG 86 mm below wrist are calculation references, not measured fruit geometry. The 42.33 cm ground reach from shoulder is a straight-link kinematic upper bound, not a usable collision-/torque-certified radius. Five additional poses were checked discretely, not their connecting paths.
- ASM-059 (2026-09-06): Camera optical reference is approximated by CAD lens front (367.5,0,230) mm. Existing CAD lens faces horizontally. Pi Camera Module 3 Wide 102H x67V and 35-degree downward tilt are analysis candidates only; no camera purchase, actual calibration or CAD tilt modification is implied. Pinhole FOV excludes real distortion, cropping and occlusion.
- ASM-060 (2026-09-06): At user request, at-shot constant loaded speed is evaluated as a counterfactual. Published MG996R main-table 0.19/0.15 s per60deg and 9.4/11 kgf.cm stall at4.8/6V are reference values only. Manufacturer page has inconsistent legacy speed entries. The actual clone speed/torque curve and continuous rating remain UNVERIFIED. Stall torque and unloaded speed cannot be simultaneously assumed available.
- ASM-061 (2026-09-06): Throw scenario starts fruit CG at (600,415,360) mm and aims at (300,250,326.41) mm, 20 degrees elevation, assumed fruit radius20 mm independent of fruit mass. Rigid-body calculation uses CAD inertia and nominal servo mass distributed uniformly in its reference body; unknown screws/cables, rotor inertia, friction, deformation, air drag, grip impulse and thermal limits excluded. Acceleration times0.1/0.2s define instantaneous load scenarios, not simulated peak trajectory loads. Friction and stop-latency examples in the report are hypothetical; physical validation required.

- ASM-062 (2026-09-06): Front-mount study compares unchanged AERO V3 at candidate base X=520 mm versus current380, with base Z=280/200/160 mm, same ground pickup wrist(650,415,102) mm. These are study coordinates, not accepted CAD dimensions. Lowering the same long arm can increase elbow/wrist demands. A candidate release(540,275,460) requires an extended catch apron and new chassis-fixed carrier; neither is designed or manufactured. Static torque reduction applies at the SAME fruit and vehicle position, not simultaneously to a vehicle shifted140mm back. Stability, complete wheel steering sweep, new carrier strength, cables and continuous motions remain UNVERIFIED.

- ASM-063 (2026-09-06): Height study keeps arm base X380/Y415 and compares Z280/260/220/180mm at same wrist pickup(650,415,102). Lowered arm references at Z220 and180 intersect the existing straight front tyre. Z260 arm-only clearance is not carrier/steering approval. Chassis lower edge75mm must not be confused with shoulder height404mm. Smaller-wheel example254->200mm gives27mm axle/chassis height reduction only under unchanged axle-relative attachments; no wheel selected, purchased or CAD dimensions changed. See reports/aero_v3_height_study.

- ASM-064 (2026-09-07): CARD-01 is a separate disposable household bench experiment, not a substitute full-scale AERO arm. One fixed MG996R and one distal MG90S; proposed motor-axis-to-object distance at most about120mm; folded120x110mm board net, four25mm faces and10mm closure tab. Cardboard thickness/grade/moisture, adhesive, ties and horn attachment strength are unknown. Test unloaded, then soft object, measured10–20g and only if stable about40g; no100g/high-speed throwing approval. One lift axis tilts the gripper; no XYZ reach or automatic vertical wrist. Templates do not update CAD, BOM or firmware, and existing single-servo panel is not a two-channel controller.

- ASM-065 (2026-09-07): CARD-02 extends the cardboard learning fixture to4MG996R+2MG90S. All blank cuts in the PDF are proposed experimental dimensions, not measured hardware-fit dimensions. Cardboard thickness/grade, adhesive, tie/horn strength, dry-assembly fork spacing, pivot bolts/bushes and clearances, finished L1/L2, shoulder height, sliding-ring friction, motor pairing and power capability remain TBD / UNVERIFIED / PHYSICAL VALIDATION REQUIRED.70/50mm tube blanks do not establish100/80mm joint spans. Opposite pivot hardware is not assumed purchased.3D figures are illustrative and do not certify fit, collision-free motion or load rating. Current single-servo software is not a commissioned six-channel controller. No high-speed throwing or100g approval; measure actual geometry into a separate CARD-02 profile. AERO V3 and inventory unchanged.

- ASM-066 (2026-09-07): User reports imperfect supplied-horn versus printed coupon hole alignment. Cause remains UNVERIFIED; nominal hole pattern, horn variant and printing tolerances must be distinguished. Third-party reference files are isolated in references/servo_horn_trials. EEZYbotARM MK2 gearservo is designed for the author's MG995/946, not verified for delivered MG996R; Z1 claw_gear_horn is a micro-servo interface candidate for the project's MG90S. Both selected meshes are watertight, but horn fit, fasteners, retention and strength require PHYSICAL VALIDATION. Z1 turntable mesh is not watertight and is excluded from the trial ZIP. Source licenses retained (EEZY CC BY-NC 4.0; Z1 CC BY 4.0); no commercial design adoption, AERO geometry change, BOM change or motor operation.

- ASM-067 (2026-09-07): User reports both reference horn interfaces fit well; exact horn-to-file mapping and measured fit remain UNVERIFIED. SNAP-01 is a proposed shaped pocket and sliding rail/latch retaining cover. Horn geometry/thickness, hub clearance, centre screw, latch dimensions, filament, printing orientation, creep, fatigue, torque and pull-out capacity are TBD / PHYSICAL VALIDATION REQUIRED. Retain centre screws and structural fasteners. No CAD or BOM changes. See docs/KLIPSLI_SERVO_BAGLANTI_PLANI.md.

- ASM-068 (2026-09-07): Actual EEZY gearservo source section is a circular diameter20.8mm pocket, depth2.5mm; previous star-pocket interpretation was incorrect. SNAP-01 is an isolated retention/clip coupon without positive torque transfer, not a working servo-to-arm connection. User horn identity, axial thickness, hub clearance, centre screw and motor-case clearance remain UNVERIFIED. Coupon dimensions in DEC-045 are experimental, with unvalidated latch flex/force/creep/fatigue. No powered/loaded use. Main AERO/BOM unchanged; physical horn image is needed for the keyed revision.

- ASM-069 (2026-09-07): STAGE-02 is an independent nominal MG996R bench fixture and20mm-tube cable-guide experiment. Actual servo cable exit, fastening hardware ownership/length, workbench attachment, cable bundle dimensions, clip flex/creep/fatigue and support removal remain UNVERIFIED / PHYSICAL VALIDATION REQUIRED. No load rating, powered trial or full-arm integration approval. New dimensions are proposed experiments in DEC-046; AERO geometry and BOM unchanged. Functional horn capsule still awaits exact horn identification/thickness.

- ASM-070 (2026-09-07): Original SNAP01 closed-hole sliding lid cannot traverse the protruding horn hub. B/C sampled hub envelopes (8/10/12/13.5mm) are synthetic tests, not measurements. All circular capsule variants remain HOLD due to missing torque key. Original MG996R star contour, asymmetric arm lengths/widths, thickness and hub dimensions remain UNVERIFIED. The downloaded FT90R Wheel.stl cross pocket is a mechanism reference, not a compatible MG996R print. Centre screw fit and structural retention require physical validation.

- ASM-071 (2026-09-07): SNAP02 uses the user-supplied six-arm STL shape as a nominal reference. Physical horn contour/thickness, printer shrinkage/elephant foot, centre screw presence/thread/length, shaft engagement, motor collar clearance, latch flex/strength/creep and dynamic loading are UNVERIFIED / PHYSICAL VALIDATION REQUIRED. Digital dimensions are recorded in DEC048 and AUDIT.json. Motor keepout starts atZ7mm by explicit assumption; clearance to print top is0.2mm and must be checked without using the screw to force engagement. STL reference envelope fills small holes for conservative collision checks; it is not a manufactured replacement horn. Four-arm STEP differs in geometry and is not compatible with this pocket. The short integral tongue only demonstrates torque output and does not complete full-arm integration. Full-scale CAD/BOM unchanged. Printed-spline substitution, hammering, high-speed movement and throwing are not approved by this print release.

- ASM-075 (2026-09-08): MG90 physical horn is reported asymmetric and old pocket too small on one side. New Arm03 provided model has unequal arm lengths; identity with hardware UNVERIFIED. 6/7-hole wording is user description, not a measured hole pitch. SNAP03B adds contour clearance while preserving old cap/floor. Actual axial play, key backlash, hub/case clearance and loaded retention PHYSICAL VALIDATION REQUIRED. F3D history not decoded.

- ASM-076 (2026-09-08): Photograph shows collapsed filament under ring and complex arm geometry. Exact original job/G-code unavailable; missing/ineffective supports are consistent with photo, not independently proved sole failure cause. User reports direct motor couplers and pins/screws printed successfully; these remain unchanged. Integrated support contact0.42mm/0.6mm neck,0mm Z-gap,0.3mm side gap and other DEC052 parameters are experimental manufacturing values, not measured break forces. PLA0.4mm/0.2mm layers based on user's screenshot. Layer bonding, support peelability, support access, actual Elegoo Arachne/classic behavior, bed adhesion and loaded part strength PHYSICAL VALIDATION REQUIRED. First small coupon before complex jobs.

- ASM-077 (2026-09-09): User reports thin pins breaking at split and largest pins surviving. Treat largest as P5 nominal6mm axle based on existing design; no measured failure load or material fault diagnosis. Solid pins remove split stress concentration but strength and axial pullout resistance remain PHYSICAL VALIDATION REQUIRED. User asks same dimensions: full replacement set remains3.05mm; nominal clearance does not establish friction fit. Actual printed bores, shrinkage, press force and coupon retention unknown. Do not hammer oversized test pins into structural parts.

- ASM-078 (2026-09-09): User reports custom supports did not work; exact failure mode, contact force and sliced file unknown. Record user-reported failure, not successful support validation. No further custom-support design requested; preserve original part geometry and use separately reviewed slicer support settings for complex parts.

- ASM-079 (2026-09-09): Replacement PCA9685 physically responds on UNO COM3 at default I2C 0x40. User reports one servo connected; assume channel0 per wiring instructions, actual motor identity/mechanical attachment UNVERIFIED. Proposed mapping per arm: base, shoulder1, shoulder2, elbow (MG996R), wrist, gripper (MG90S), channels0..5 and6..11. No second-arm inventory claim. Panel0..180 is command scale, default1000..2000us; optional500..2500us requires individual physical endpoint checks. Oscillator25MHz, resulting pulse accuracy, actual position/speed/torque, paired-shoulder calibration and powerbank current capability PHYSICAL VALIDATION REQUIRED. No synchronized loaded-arm operation. Software heartbeat shutdown cannot guarantee stop after I2C failure; OE hardware interlock not fitted. Power remains on after PWM off and unsupported arms may fall.


- ASM-080 (2026-09-09): User reports opposing shoulder motors mechanically facing each other. Nominal A=theta/B=180-theta assumes corresponding1500us centres and symmetric travel. Actual horn orientation, centre offset, gain, backlash, load sharing, endpoint range and dual-servo supply remain UNVERIFIED / PHYSICAL VALIDATION REQUIRED. V2 provides paired commands, not measured mechanical synchronization. Do not energize coupled unaligned servos. User explicitly confirmed motor power removed, UNO USB retained for update. Prior active panel mask15 was software state only, not a count of physically connected motors.

- ASM-081 (2026-09-09): PB01 all-plastic bearing is user-requested despite ready-bearing alternatives. PLA/0.4mm nozzle follows prior print context; exact loaded filament, extrusion calibration, sphere roundness/support scars, race shrinkage, elephant foot, lubrication compatibility, cage drag, creep, wear, bayonet/pin strength and retention under vibration remain UNVERIFIED / PHYSICAL VALIDATION REQUIRED. Printed8mm spheres require slicer-generated supports; STL/3MF contain geometry only. Their surface may prevent useful rolling even if CAD is perfect. Main arm integration, load capacity and friction torque are TBD; large candidate must not be bolted to the arm or powered from this release. Small unit is for hand testing without an arm/payload. Filament price and actual sliced mass/support waste are unknown; report only full-solid volume-based PLA estimate using assumed1.24g/cm3, no purchasing ledger change.

- ASM-082 (2026-09-09): PB02 replaces the missing digital adapter but does not establish physical performance. Horn/caps reused from reported successful SNAP02 fit; exact servo case dimensions, shaft axial stack and original screw length remain UNVERIFIED. Nominal seated-ball geometry is not proof all arm load bypasses the motor: manufacturing error, horn seating and printed ball roundness may load the servo axially. Split-retainer seam/pin strength, square-foot bearing stress, PLA creep, sphere support scars and friction torque PHYSICAL VALIDATION REQUIRED. Pin6.2/bore6.3mm nominal clearance does not guarantee friction retention. No arm/payload until hand fit/retention checks; no throwing trials from this release. No assumption that previously printed PB01 parts are in the user's possession. Filament cost TBD; material estimate uses1.24g/cm3 assumed PLA and full-solid volume, not actual spool usage.

- ASM-083 (2026-09-09):180deg/s is command-ramp rate, not measured shaft motion; linked shoulder loading, physical180degree travel, friction and powerbank current limitation are unverified. User suspects weak powerbank; no sag/current capture proves cause.12V9Ah battery and two XL4016 come from purchase history, not current measured wiring. Actual converter revision, output adjustment, terminal polarity, fusing and current capability PHYSICAL VALIDATION REQUIRED. Initial bench converter output5.0V is a proposed setting to be measured disconnected from all servos. No assumption that an old power-off confirmation remains true in this session; V3 firmware upload awaits current confirmation.

- ASM-084 (2026-09-09): User confirms HC-05 but no module/carrier photo. VCC regulator presence, input voltage rating, RX protection and configured data-mode UART baud UNVERIFIED.9600baud is a source default, not measured fact;1k/2k RX divider components are not assumed present. Android SDK build/unit/lint checks do not establish real permission, RFCOMM, radio latency, camera UI or motor behavior; no adb device attached. Camera base registration does not determine actual servo zero/sign/scale or collision-free path. Real autonomous collection is PHYSICAL VALIDATION REQUIRED / NOT IMPLEMENTED in v0.7; manual control and camera observation are distinct. Battery-powered UNO wiring not yet commissioned; do not connect raw12V to5V or parallel USB/regulator outputs.
# LINKA L1 / DEC-077 additions — 2026-09-13

- Actual figs40–50g are user-reported;100g remains separate upper requirement. Diameter/height TBD;40mm illustrative CAD fruit is not a measured size.
- New150/120 spans,55/185/35 linkage and110mm shoulder elevation are explicit CAD design choices, not measurements. Motor/cable/insert fits other than existing J1 measurements remain UNVERIFIED.
- MeArm and EEZYbotARM are mechanism references. L1 is not their tested lightweight edition and has no comparable payload certification.
- CAD mass uses solid volume x1.24g/cm3 PLA, assigned55g/13.4g motor masses and indicated hardware allowances. Slicer mass, cables, printing and assembly must be weighed; continuous torque unavailable. Moving J3 stator to yaw trades distal mass for extra base structure.
- Three independent elastic tendon links and return bands require stiffness/preload/travel characterization. Soft pad material is silicone or TPU; PLA pads are not acceptable substitutes. Fruit bruise pressure TBD.
- Two625 bearings, metal pivot sleeves, M5 pivot hardware and insert dimensions are nominal design candidates, not an assertion of inventory. Prices TBD; no purchase is made. Clearance and swept-volume screening do not certify printed strength.

## LINKA L1 plate packaging — 2026-09-13

- Layout uses the recorded ASM-052 ELEGOO Centauri Carbon 2 Combo 256 × 256 × 256 mm build volume. An 8 mm edge margin and 8 mm minimum projected bounding-box separation are packaging choices, not measured printer exclusion zones. Actual slicer profile, supports and brim clearance remain UNVERIFIED.
- Four PLA plates conserve all 29 existing PLA instances; a separate fifth plate contains the three TPU_OR_CUT_SILICONE pads. Cut silicone substitutes omit plate 05. Existing print poses, geometry, BOM and source 3MF local modifiers are unchanged. No G-code is supplied; ELEGOO slicer modifier compatibility requires verification.

## LINKA L1 procurement reconciliation — 2026-09-14

- Shopping candidates are derived from current CAD, not purchased inventory. Insert product outer diameters and lengths require physical fit checks; unknown prices, machining and shipping remain TBD. Elbow axle retention and linkage fastening are not fully specified in current CAD, so standard bolts cannot be asserted equivalent.
- User reminded us that bearings were intended to be printed. Earlier PB01/PB02 record printed balls and races; current L1 instead contains 24 metal balls and two 625 bearings. This is an unresolved design discrepancy, not approval to buy metal bearings. Both metal bearing rows are placed on order hold and excluded from the procurement subtotal. Geometry and print packages remain unchanged. A fully printed L1 bearing arrangement has NOT been validated or exported.


- 2026-09-14 follow-up: user accepts purchasing bearings necessary for current L1. Earlier procurement hold for two625ZZ and24 Ø8 metal balls is superseded; both restored as recommendations. No purchase or CAD change. Existing printed race wear/load performance and axle retention remain unverified.


## LINKA L1 ongoing print / hardware audit — 2026-09-14

- User reports plate01 TABAN printing at100 percent. Packaging conservation tests passed, not proof of physical fit. No export geometry was changed during this audit.
- Direct STEP check: nominal J1 ear topZ40.2 and insert seatZ38, hole depth5. M3x8 shaft intersects printed base by5.654867mm3 (0.8mm excessive reach); M3x6 shows zero nominal intrusion,3.8mm engagement. Actual ear thickness, insert inner thread and head fit remain UNVERIFIED. M3x8 procurement suspended; do not assert shorter screw is physically validated.
- Nominal625 bodies (OD16, ID5, width5) have zero solid intrusion in both exported upper plates. Pocket diameter16.15 is nominal only; printed fit unverified. Elbow axial retention, sleeve stack and horn physical fit remain open. User advised to defer plates02-04 pending resolution; no demonstrated need to cancel plate01 from this audit.


## L1.1 / DEC-078 physical limits — 2026-09-14

- Broader hard-part audit found collisions omitted by previous narrow tests. Prior passing tests did not establish assembly feasibility. User was advised to stop plate02 motor-deck object; plate01 and plate02 retainers are preserved. New digital clearance results only apply to the sampled path and nominal hard shapes, excluding flexible cords and actual cables.
- Actual insert profiles/internal blind depth, washer thicknesses, servo flange thickness/pattern, horn fit, bearing tolerances and square sleeve ends remain PHYSICAL VALIDATION REQUIRED. M5x70 screw requires at least47mm uninterrupted smooth bearing land, including thread-runout allowance. Nominal two625 outer-ring0.2mm axial float and shoulder-screw0.4mm axial float are trial design clearances, not tested fits.
- Elastic cord routing can be defined in CAD, but fruit-size/stiffness/bruise and 3D-print anisotropic strength cannot be closed by geometry tests. No material strength values or motor current/continuous torque are invented.

# L1.4 plastik burç varsayımları — 2026-09-14

DEC-081 ölçüleri tasarım adayıdır. PLA,0,4mm nozzle,1,2/1,35mm nominal et ve3 duvar/100% dolgu hedefi gerçek yazıcı kalibrasyonu değildir. Malzeme sünmesi, katman yapışması, aşınma, sürtünme, baskı deliğinin daralması ve güvenli sıkma torku UNVERIFIED / PHYSICAL VALIDATION REQUIRED. Yüklü motor testi onayı verilmez. Eski parmak burcu metal çapı artık yeni plastik parçayı tarif etmez; yeni L1-17 gerekir. Görsel ip çizgileri ve Imagegen düğüm şeması fiziksel montaj doğrulaması sayılmaz.

## DEC-085 — fiziksel doğrulama sınırları

Basılı burç OD6/ID3,3/L6, çubuk deliği6,3 ve uç5,6mm nominaldir. Gerçek baskı delik daralması, PLA sünmesi, sıkma torku, insert yüzü/diş derinliği, vida ve pul ölçüleri UNVERIFIED. Önce enerjisiz elle serbestlik kontrolü; sıkışmayı vidayı gevşek bırakarak giderme. Güvenli yük/ömür belirlenmedi. Önceki listede12 M3x10 ve40 M3 pul alınmışsa yeni toplam10/32 ihtiyacı karşılar; gerçek stok bilinmiyor. Tutucunun kırılganlığı çözülmemiştir.

## DEC-086 fiziksel belirsizlikler
İncir ağırlığı40–50g kullanıcı beyanı; çapı ve sıkma kuvveti UNVERIFIED. İki kepçenin2,6mm cidarı ve geniş kökü mukavemet adayıdır, dayanım sonucu değildir. Gerçek motor torku, akım, baskı katman bağı, dişli boşluğu, sürtünme, temas izi, PLA sünmesi ve servo kalibrasyonu PHYSICAL VALIDATION REQUIRED. Taban yıldızının mevcut yuvada çıkması ile eksen/yükseklik uyumsuzluğu henüz ayırt edilmedi.

## DEC-086 ek koşullar — 2026-09-17

Taban yıldızı mevcut yuvaya ulaşıyor ve geometrik olarak oturuyor varsayımı UNVERIFIED. Yeni kapak yalnız bu durumda eksenel kaçmayı sınırlar; yetişmeme, hizasızlık veya yanlış spline sorununu çözmez. Kullanıcının açıklama sorusuna yanıt bekleniyor. Önce gerçek motor yıldızıyla enerjisiz oturma denemesi. Kalibrasyon uçları değiştirilmedi. Kepçeler24° açılma adayı;43mm kapalı iç ağız meyve çapı yerine kabul edilmez. Bilek32mm uzatma ve100g grup için sürekli motor torku/ısınma ve tüm yol çarpışması onaylanmadı.5 kayıtlı poz sadece anlık CAD denemesidir; eski hedef koordinatları yeni kepçe merkezini tanımlamaz. İnsert/vida sıkılığı, yazıcı profili ve malzeme dayanımı ölçülmemiştir.

## DEC-087 — SO-101 satın alma belirsizlikleri

- Kapsam varsayımı: maliyeti azaltmak için bir follower; leader ertelendi. Bu bir alışveriş planı, yeni fiziksel kapasite garantisi değildir.
- Excel satın alınan adetleri gösterir; teslim/sağlamlık/kalan stok ayrı doğrulanacak. Kumpas adedi kaynakta 1 varsayılmıştır. Daha önce önerilmiş insert, rulman ve vidalar satın alınmış sayılmadı.
- C047 ticari paketinde başlık/vida/kablo bulunması UNVERIFIED; satıcıdan içerik istenecek. Kılavuz sayımı 24 M2×6, 50 M3×6, 11 başlık; kart, masa ve araç bağlantısı dahil değil.
- Mevcut akünün sağlık durumu, XL4016 gerilim düşmesinin nedeni, kullanılabilir filament gramajı, USB-C veri kablosu ve masa kelepçesi stoğu UNVERIFIED. Aküden doğrudan kullanım ve şarj sırasında çalışma onayı yok.
- Kart üzerinden en fazla 5 A geçebilir. Altı C047 motorun nominal akım toplamı 5,4 A; kilitlenme toplamı 16,2 A hesap değeridir, normal işletme hedefi değildir. Gereken eşzamanlı görev akımı ölçülmedi. Ayrı güç dağıtımı ihtiyacı ve sigorta değeri TBD / PHYSICAL VALIDATION REQUIRED.
- Türkiye teslimatı, kargo, vergi, kur ve teslim stoku TBD; 148,93 USD yalnız motor+kart sayfa fiyatlarının ara toplamıdır. Robotnom 12 V / 5 A kaynak adayı 319,83 TL; fiş/polarite ve AC kablo içeriği UNVERIFIED, kesin alım değildir. Otonomi için kamera/işlemci ve mobil araç montajı bu bütçeye dahil değildir.


## DEC-087 tedarik taraması eki — 2026-09-17

SAMM 22414 12 V motor canlı sayfası 1.649,95 TL ve 12 stok; 25514 kart 321,23 TL ve 54 stok gösterdi. Yerel motorun C047 / 1:345 eşdeğerliği ve SO-101 başlık takımı UNVERIFIED. Paket sayfası motor başına yalnız bir başlık, bir kablo, bir vida seti listeler; 11 başlığın tamamı dahil varsayılmaz. Yurt dışı adrese teslim ve ithalat toplamı TBD. Yerel fiyat senaryosu fiziksel uyum onayı veya tamamlanmış BOM değildir.


## Kullanıcı alım bildirimi — 2026-09-17
Önceki talep listesindeki bütün vidalar ve pirinç insertler kullanıcı beyanıyla alındı, toplu tutar 600 TL. Ölçü başına fiyat ve kalan miktar TBD; pul/rulman alımı çıkarımı yapılmadı. Type-C kablo mevcut, veri kabiliyeti UNVERIFIED. Ürün görselinde iki başlık görülüyor; gerçek sevkiyat içeriği ayrıca doğrulanır. Kaynak Excel 66 satır/8.774,90 TL korunur; 600 TL ek kayıtla toplam bilinen bedel 9.374,90 TL olur. USB kablonun geçmiş fiyatı bilinmiyor.


## DEC-088 — Physical and order uncertainties (2026-09-18)
- Six motors ordered: USER_REPORTED; exact C047 12 V / 1:345 variant, supplier, package contents, delivery and paid cost TBD. Geometry is original STS3215-based SO101, not confirmed against the arriving motors.
- Desktop PSU purchased: one 12 V 5 A, TRY 321.25 USER_REPORTED. Supplier/model, delivery, output regulation, DC connector and polarity UNVERIFIED. USB bus adapter purchase not confirmed.
- Previous screw/insert purchase acknowledged at TRY 600. Per-size remaining counts and head clearance UNVERIFIED. Original mechanism does not require heat inserts; available inserts stay in stock. M3 DIN912 head height may differ from motor-pack screws.
- Printer and nozzle inherited from ASM-052: ELEGOO Centauri Carbon 2 Combo 256 mm bed, 0.4 mm nozzle. PLA in user inventory; spool remaining weight, calibrated process and shrinkage UNVERIFIED. Initial local slicing suggestion 0.20 mm layer, 20% infill, 3 walls is not tested strength.
- Physical fit, torque/load, grip and dynamic clearance PHYSICAL VALIDATION REQUIRED. Digital watertightness and bed checks are not a load test. Official URDF has known base collision/gripper-mapping limitations; reference scene is not motion approval. New electronics have no installed compatible control software in this change.


## DEC-088 SAMM confirmation — 2026-09-18
User confirmed SAMM as motor supplier. Conversation catalog match: Waveshare 22414 / MP03422 ST3215 12 V 30 kg.cm; catalog dimensions 45.22 x 35 x 24.72 mm. Official Waveshare SO-ARM101 assembly lists six ST3215 for follower. Nominal original 01-03 print geometry therefore retained, printing before arrival is reasonable; 00 physical gauge is optional, not a blocker. No hole or critical dimension changed. Physical tolerances, received SKU/package contents, paid total and screw head clearance remain UNVERIFIED. SAMM lists one horn while manufacturer assembly uses front/rear horns; verify the 11 required horns without automatically ordering more. Use the motor-pack pointed case screws rather than assuming existing M2 machine screws are equivalent. See manufacturing/so101_samm_check.md.


## DEC-089 — Slicer setup limitations (2026-09-18)
- USER_REPORTED: PLA+ 210–235 C label; 225 C works. Brand, remaining spool mass, drying condition UNVERIFIED.
- CC2 Combo / physical 0.4 mm nozzle per existing printer specification. Installed slicer was on mismatched profile; corrected to CC2 0.4.
- 60 C Textured PEI A is OEM-based starting value. OEM filament glass-transition warning remains; no fabricated temperature used to suppress it.
- Flow ratio 1 and pressure advance disabled are starting settings, not physical calibration. Shrinkage/holes/support removal and strength PHYSICAL VALIDATION REQUIRED.
- CANVAS spool-slot mapping is physical user state. Projects use one material; user must select the slot actually holding PLA+. No printer upload/start performed.
- Predicted time/material from slicer is an estimate; UI rounding may differ. Optional 00 gauges are not additional required arm parts.

## ST3215 delivery and bench test — 2026-09-19
- USER_REPORTED: motors and adapter arrived. User calls motors Waveshare ST3215; previous order corresponds to SAMM 12 V model. Adapter description (USB-C, black DC jack, green terminal, A/B jumpers) matches Bus Servo Adapter (A). USB VID/PID 1A86:55D3, CH343 observed on COM5.
- VERIFIED READ-ONLY: ID1 responds at 1,000,000 baud; model register777, mode0, position3235/4096, voltage12.4V, temperature32C, torque0, min/max0/4095. These are a single instant, not a capacity/endurance test. No motion/torque/EEPROM writes were sent in this readback check.
- Exact motor SKU, gearing, current scale, every motor's identity and bench mechanical arrangement are not inferred from model777. PHYSICAL VALIDATION REQUIRED for motion, ID programming and full-arm calibration/load.
- Software 9–12.6V and <60C gates, ±30deg and 15/30/60deg/s are conservative bench policy choices, not revised manufacturer ratings. Feedback current remains labeled raw pending variant validation. Motor IDs may initially collide: connect only one for assigning IDs.
- Supersedes earlier uncertainty about motor/adapter arrival only. Costs, mechanical print dimensions and inventory quantities are not changed by this software task.
- ST3215-TEST-2: user requested maximum speed selection and270deg travel. These supersede initial±30deg and60deg/s limits. Official Waveshare example3400steps/s used for Maximum; no claim of3400steps/s actual motion. Acceleration10 remains deliberate bench policy. GUI showed user-enabled test and changing real motor positions; this is not a calibrated physical speed or270deg sweep validation.
- ST3215-TEST-3: explicit user request "en hızlı olabilecek sekilde ayarla" authorizes Maximum as default with speed0/acceleration0 maximum-profile sentinels. Source: official Waveshare08_Sub-controller_JSON_Command_Set ST bus-servo position commands; these zero values are not stop commands. Prior soft acceleration no longer applies to Maximum. Numeric selections and current-position preload keep acceleration10. PHYSICAL VALIDATION REQUIRED for actual speed, acceleration and stopping distance on the received motor; no automatic hardware sweep performed.

## SO-101 illustrated assembly guide — 2026-09-19
GUNCEL/CAD/MONTAJ matches the pinned SO-101 follower print source. Motor-pack screw dimensions and physical seating require comparison with delivered hardware; P11 controller-board mounting screw length is UNVERIFIED and not prescribed. Motor IDs 1–6 are the required mapping, not a claim that all six have been configured. Assembled-arm joint calibration and physical assembly remain PHYSICAL VALIDATION REQUIRED. No CAD or slicing changes.

## Base endpoint input — 2026-09-19
User provided zero=234 and end=113. Degrees of the existing motor display are the contextual interpretation, not independently measured joint angles. Direction (decreasing 121 degrees versus increasing across zero 239 degrees) is TBD. Endpoints are recorded only; neither software motion limits nor hardware calibration have been applied. Installed horn phase and physical motor identity must remain unchanged for eventual use of this reading pair.

User subsequently confirmed increasing via360/0, total239degrees; direction is no longer TBD. Actual zero-crossing motion and physical clearance remain PHYSICAL VALIDATION REQUIRED. Recorded display mapping is not an instruction to jump directly between raw234 and113 targets.

## Assembled arm observation — 2026-09-20
USER_REPORTED: assembly complete, folded pose, electrical connections ready; six unique IDs not assigned or uncertain. COM5 CH343 enumerates, but no bus query or motor-state write performed in preparation. Actual ID uniqueness, camera framing and joint mapping UNVERIFIED. Camera-and-telemetry viewer is preparation only; it does not implement full-arm calibration or autonomous picking.

Camera diagnostic 2026-09-20: HKCU webcam/NonPackaged Value was Deny while general webcam values were Allow. User enabled desktop-camera permission. Actual Xiaomi17Pro stream then observed in FIGBOT (DirectShow index2) showing assembled folded arm; permission was the demonstrated access blocker. Project headless OpenCV also lacked MSMF; dedicated .venv-camera standard OpenCV4.14.0.94 adds that optional backend without replacing main project packages. Motor rows were timeout errors; no ID uniqueness or calibration inferred from user checking the GUI box. No motor state writes made during camera diagnosis.


Single base motor diagnostic 2026-09-20: USER_REPORTED only the base motor electrically connected (supersedes earlier two-motor clarification). VERIFIED three consecutive READ responses on COM5 at 1000000 baud: ID1, encoder96 (8.4375 motor degrees), voltage12.4V, temperature32C, speed0, torque register0. Physical identity relies on user isolation; these readings are not joint calibration or a loaded power test. Other five IDs remain UNVERIFIED; duplicate IDs are suspected, not established. No goal, torque or EEPROM writes sent. Port closed after readback.

Second motor ID assignment 2026-09-20: USER_REPORTED only second/shoulder motor directly connected. Three READs initially returned ID1, encoder686, 12.3V, torque0; together with previous isolated base ID1 this establishes duplicate IDs under the user-confirmed physical mapping. Assigned isolated shoulder ID1->2 using only EEPROM lock55 and ID5 writes. Read back ID2, lock1, torque0; three feedback samples encoder686,12.3V,34C; old ID1 no longer responded. No motion, torque or calibration-offset commands sent. Power-cycle persistence still requires verification; remaining four IDs unknown.

Third motor ID assignment 2026-09-20: USER_REPORTED third/elbow motor connected following isolated-motor instructions. Initial readback ID1, torque0. Assigned ID1->3 using only EEPROM lock55 and ID5 writes. Verified ID3, lock1, torque0 and three feedback samples encoder3855,12.3-12.4V,31C; ID1 no longer responded. No motion, torque or offset writes. Physical joint identity relies on user isolation; power-cycle persistence and calibration pending. IDs4-6 remain unknown.

Fourth motor ID assignment 2026-09-20: USER_REPORTED fourth/wrist-flex motor connected following isolated-motor instructions. Initial readback ID1, torque0. Assigned ID1->4 using only EEPROM lock55 and ID5 writes. Verified ID4, lock1, torque0 and three feedback samples encoder2488,12.2-12.3V,30C; ID1 no longer responded. No motion, torque or offset writes. Physical joint identity relies on user isolation; power-cycle persistence and calibration pending. IDs5-6 remain unknown.

Fifth motor ID assignment 2026-09-20: USER_REPORTED fifth/wrist-roll motor connected following isolated-motor instructions. Initial readback ID1, torque0. Assigned ID1->5 using only EEPROM lock55 and ID5 writes. Verified ID5, lock1, torque0 and three feedback samples encoder3342,12.4V,30C; ID1 no longer responded. No motion, torque or offset writes. Physical joint identity relies on user isolation; power-cycle persistence and calibration pending. Sixth motor ID remains unknown.

Sixth motor ID assignment 2026-09-20: USER_REPORTED only sixth/gripper motor connected. Initial readback ID1, torque0. Assigned ID1->6 using only EEPROM lock55 and ID5 writes. Verified ID6, lock1, torque0 and three feedback samples encoder1162,12.3V,31C; ID1 no longer responded. No motion, torque or offset writes. All six physical motors now individually identified by user isolation: base1, shoulder2, elbow3, wrist-flex4, wrist-roll5, gripper6. All originally responded as ID1. Full-chain readback after power cycle and joint calibration remain pending; this is not completed motion calibration.

Full-chain verification 2026-09-20: user reconnected all six motors after instructed power-off. COM5 at1Mbaud returned all IDs1-6 successfully for three complete rounds. ID registers matched addressed IDs, EEPROM locks1, position modes0, torque0 on all six. Encoder positions96,4032,3919,2707,2326,788; voltages12.2-12.3V; temperatures31-34C. Saved raw reads in GUNCEL/YAZILIM/ST3215_TEST/KAYITLAR/chain_readback_20260920_031549.json. Duplicate-ID communication failure resolved for this check. This is unloaded communication verification, not loaded power capacity or joint calibration. Camera close-up did not show full arm; no movement performed.

First assembled gripper micro-motion 2026-09-20: user explicitly requested camera-guided drive and confirmed fixed base, supported arm, hands clear. Only ID6 enabled after current-position preload and readback. Command encoder788->811 (+23 steps), speed23, acceleration1; measured encoder810 (~1.93deg net). Voltage12.2V,36C. ID6 torque disabled and readback0 after test; no commands to energize other joints. Log GUNCEL/YAZILIM/ST3215_TEST/KAYITLAR/gripper_micro_20260920_032624.json. Opening/closing direction not yet physically confirmed; actual speed units/calibration not established by this short test. Full arm calibration and object pickup pending.

Gripper reverse direction probe 2026-09-20: user could not distinguish first2deg motion. ID6 only commanded encoder810->753 (-57steps~5deg), speed register23,acc1. Measured final760 (~4.39deg net), 7steps short of target at3.5s timeout; target_reached false at4step tolerance. Tork disabled and readback0; voltage12.2V,36C. No other joint enabled. Cause of residual error UNVERIFIED (do not increase torque or force endpoint). Log gripper_reverse_20260920_032911.json. Visual/user direction confirmation pending.

User confirmed reverse/decreasing ID6 encoder motion closes jaws; increasing opens. Gripper opening probe logged at gripper_open_20260920_033044.json. Result {"time": "2026-09-20T00:30:42.531890+00:00", "id": 6, "requested_delta_steps": 114, "direction": "opening per user confirmed previous decreasing motion closes", "speed_register": 23, "before": {"position": 760, "speed": 0, "voltage": 12.2, "temperature": 37, "current_raw": 0, "moving": false}, "target_reached_within_8_steps": true, "torque_after": 0, "after": {"position": 872, "speed": 0, "voltage": 12.2, "temperature": 36, "current_raw": 0, "moving": false}}. Opening/closing endpoints still UNVERIFIED; no whole-arm calibration inferred.

Manual shoulder observation 2026-09-20: user confirmed supported manual shoulder raise and return with all six torque registers0; no drive writes during recording. Log manual_shoulder_20260920_033437.jsonl. ID2 increased from4005 across4095/0 to unwrapped4360(raw264), observed span31.20deg; final4041. This is an observed motion span, NOT full permitted travel or calibrated joint angle. ID4 also changed2709->2607 (8.96deg span); ID3 changed21steps (1.85deg). User-described raise maps to increasing unwrapped shoulder encoder; wrist variation prevents attributing all tip displacement to shoulder. Motor2 requires validated zero-crossing/offset handling before powered range traversal. Gripper increasing encoder confirmed visually opens after prior+114step probe. ID4 positive23step probe ended2709 from2694, direction not independently calibrated because camera/base framing changed.

Manual elbow observation 2026-09-20: user confirmed two manually demonstrated positions; log manual_elbow_20260920_033737.jsonl. Multiple joints moved; ID3 observed1748..3928 (~191.60deg), ID2 crossed encoder zero, ID4 varied ~172deg. These are observed spans only, NOT safe workspace limits or powered motion authorization to endpoints. Final camera frame clipped wrist/gripper at top; full sweep collision clearance UNVERIFIED. No drive commands during recording. Summary manual_elbow_20260920_033737.summary.json.


Manual six-joint record 2026-09-20: ELLE_20260920T005024258275Z closed with831 video frames over100.891s; AVI reopened successfully, all sampled torque registers0. Observed unwrapped spans ID1..6:232.56,220.52,192.74,174.81,338.99,126.04 motor degrees. These are NOT validated collision-free operating ranges. Endpoint imagery includes hand occlusion, coupled motion and gripper below table edge. See analysis/observed_ranges.json and endpoints.jpg. User later confirmed manually rotating ID5 between powered gripper probes; its3218->36 change was not a drive command.

Powered probes 2026-09-20: ID6 opening769->818->1040->1262->1484 (~62.8deg) visually confirmed; each command at speed57/acc1, other joints monitored, torque off after each. ID3 attempted3967->3910 stopped3925 at3s timeout (target not reached), then return command from3930->3972 reached3964 within8step tolerance. No diagnosed cause for residual error. ID2 positive57step probe144->201 instead moved to130 and position guard stopped within0.32s. Goal register201 verified, mode0, all torque0 afterward.

ID2 coordinate-only normalization 2026-09-20: explicit arm calibration authorization; backed up all motor registers in after_shoulder_guard_diagnostic.json. Offset-only guarded writes changed homing85 to-813 (sign-magnitude2861), EEPROM re-locked1, all torque0. Observed arc now793..3302; old130 readnew1028 as predicted, other joint positions unchanged. This is NOT mechanical zero or completed calibration. Positive57step retest1028->1085 moved1014; guard stopped. Cause UNVERIFIED; offset normalization did not resolve observed reverse initial movement. User asked to power-cycle12V while supported. Do not reuse pre-normalization ID2 raw targets.


Post-power-cycle probe 2026-09-20: user confirmed12V cycle, goal register2 reset0, retained offset2861(-813). ID2 positive57step command1015->1072 reached1064 within8step tolerance, unlike earlier reverse transient. One successful probe is not full-range validation and does not establish root cause. ID3 next3964->3850 reached3865 with15step residual then, after torque-off, was read3959 at the next probe: passive return ~8.3deg. This invalidates sequential release-after-each-jog as a picking controller.

ID4 probe 20260920_041952 returned a transaction timeout and torque readback1 in cleanup; independent immediate individual torque-off writes toall six withreadback verified0. Do not rely on only an 'armed' boolean for fault cleanup; ambiguous writes must be treated as possibly applied, cleanup always individually verified. Exact failed transaction not established by this log. Subsequent ID6 current-position goal-only diagnostic confirmed torque remained0, so goal writes automatically energizing the motor is NOT established. Full closed-loop multi-joint hold/controlled-stop software remains required before autonomous pickup. No blue-object pickup achieved.


Supervised holding-controller work 2026-09-20: source arm_control.py / arm_console.py, delivery Kol_Kontrollu_Surus.cmd. Commands expire after3s, single serial owner, bounded step57, speed57/acc1. Readback of goal/acc/speed required; no blind write retry. Goal writes were observed enabling torque on IDs3/4/5 despite prior ID6-only negative observation. Treat all goal writes as potentially energizing. Response-level8=1 on all IDs; intermittent ID4 ACK loss root cause UNVERIFIED.

First holding-controller base fault (SURUS_20260920T015321Z): after user manually repositioned base across raw zero, current-target264 write led to decreasing base motion rather than hold, despite mode0 and correct target readback. Initial freeze goal226 did not stop rotation. Agent subsequently released all six; torque0 verified, base ended2677. This exposed inadequate stop verification: latched fault had not monitored actual stopping. New source adds STARTING stationary verification and after-stop actual position/velocity check within0.35s; persistent motion disables affected joint, unverifiable stop disables all. Gravity support remains necessary. Fake-bus regression tests cover this failure; revised physical stopping behavior is PHYSICAL VALIDATION REQUIRED. Do not describe stop-goal ACK as proof the robot stopped. Encoder wrap/internal-turn state is a hypothesis, not a diagnosed cause. Blue-object pickup remains incomplete.


2026-09-20 phone datum: user states AR origin selected at upper side of base motor. Exact point, fixed/rotating surface, height and transform to vendor base_link remain UNVERIFIED. Earlier display Z+11mm versus exported Z-69mm cannot be attributed to drift without establishing calibration continuity. Depth support and ARCORE_DEPTH_HIT are device-verified; metric accuracy is not verified.

2026-09-20 user reports +X reference point 18 cm from origin. Recorded as180mm, not applied as scale calibration. Horizontal versus direct point-to-point distance and exact physical origin remain UNVERIFIED. Current Android BaseFrameCalibration normalizes the horizontal direction; it does not compare the AR-measured separation to this user measurement.


2026-09-20: User confirmed all three displayed target coordinates X211.085/Y-130.223/Z-53.157mm as correct ("hepsi dogru"). This is USER_CONFIRMED_SINGLE_TARGET_COORDINATES, not independently measured precision, a workspace-wide validation, or a transform to the vendor URDF. The exact confirmation and source observation are recorded in GUNCEL/YAZILIM/ST3215_TEST/KAYITLAR/phone_target_user_confirmation.json.


2026-09-20 Android 0.12 coordinate-stream: V3 observation-only USB HTTP streaming, at most one request in flight, 500ms send timer. Capture/depth timestamps and local capture age exported; >750ms old data, duplicate camera image timestamps, lost tracking or >3mm/>0.5deg camera pose change suppress target XYZ. Image-depth association remains STATIONARY_SCENE_APPROXIMATION, not synchronized depth or verified moving-object tracking. Session/calibration revision and world origin/+X/camera pose are exported. Keep-screen-on only in scanner; backgrounding stops streaming and clears observations. User single-point confirmation is retained in records, not transplanted to a new AR session or promoted to a robot URDF calibration. No serial commands added. Publication scripts.publish_current --android-app archives prior APKs with SHA256 checks.


2026-09-20 SO101 offline kinematics: vendor new-calibration URDF parsed directly; FK/position+approach-axis IK and explicit local encoder mapping implemented, no serial/motion commands. Reference pose derived from joint-centre geometry: qdeg=[0,-13.96796008,16.17545169,-2.20749161,0]. Aligns shoulder/elbow centres vertically and elbow/wrist centres horizontally. Hardware encoder reference, direction signs and camera-origin transform remain UNVERIFIED. Model limits are not collision-free workspace; no pickup achieved. V3 live phone HTTP receipt verified, actual sample X217.091/Y-134.133/Z-60.118mm.


2026-09-20 reference pose capture: user confirmed the geometric reference pose and controller readback after release recorded raw encoders {'1': 3973, '2': 1907, '3': 3823, '4': 1872, '5': 211, '6': 1391}. All six torque registers were 0 at capture and voltages 12.2–12.4V. This file is a physical reference observation, not complete calibration: IDs1–5 direction signs, exact mechanical joint zero, camera base transform, gripper jaw angle, collision-free range and target motion remain UNVERIFIED; no motor movement or EEPROM write performed.


2026-09-20 supported reference direct read: user confirmed holding/supporting the geometric reference pose while tork remained off. Direct COM5 read-only (no writes) captured encoders {'1': 3975, '2': 1824, '3': 3107, '4': 1878, '5': 112, '6': 1392}; all stationary, 12.2–12.3V. Earlier status values {'1': 3973, '2': 1907, '3': 3823, '4': 1872, '5': 211, '6': 1391} are INVALIDATED because duplicate-controller/stale status conflict and gravity settling made them non-authoritative. This reference still lacks encoder direction signs for IDs1–5, exact camera-to-URDF datum transform, gripper jaw angle, collision validation and motion authorization.

2026-09-20 supervised hold adjustment: a stationary, manually placed pose may be accepted only to preload and hold its current encoder readings, even when one reading is outside the narrow powered-jog envelope. This does not extend the jog envelope or validate the pose for movement. The change was made after physical ID4 read 2659 exceeded its former start gate 2534 by125 counts while all torque registers were0. Powered movement remains bounded separately and direction/calibration remains UNVERIFIED.

2026-09-20 hold-controller revision: live telemetry after a short ID2 probe showed 12.2V, 37°C and current raw1–4, but a single intervening feedback sample latched FAULT_HOLD. The controller now preserves hold through fewer than three consecutive invalid feedback or passive-drift samples, reports the transient condition, and requires three consecutive samples before faulting. A new no-write "adopt existing hold" path permits a restarted console to take over an already torque-enabled stationary chain after independent goal/torque/readback checks. This tolerance reduces false stops; it does not diagnose the intermittent bus feedback, validate collision clearance, or authorize autonomous pickup. The powered profile is now a bounded10° increment at a numeric270°/s request (not the unlimited zero speed/acceleration profile); actual speed remains load-dependent and PHYSICAL VALIDATION REQUIRED.


2026-09-20 concurrent/XYZ revision: direction signs+1 for IDs1-4 are inferred from vendor URDF axes, visually observed pan/lift/fold/wrist motions and side-view geometry. They are not a metrological calibration. ID5 sign+1 and explicit reference branch4208=112+4096 are provisional; XYZ holds ID5 fixed. Base reference1996=3975-1979 uses the verified offset change. Reference angles and other encoder zeros reuse the supported capture, not the invalidated earlier capture. Physical XYZ accuracy, camera registration and full collision geometry remain UNVERIFIED. The two XYZ direction trials and empty replay demonstrate command execution, not general autonomous picking or production safety.

2026-09-20: Manufacturer numeric speed3400 / acceleration150 profile enabled at user request. Physical response of the assembled arm at acceleration150 is UNVERIFIED until supervised staged trials. This is not a strength or production-safety validation.

2026-09-20 correction: all six physical factory acceleration-limit bytes at85 read50. Byte86=1 is a separate multiplier. The proposed 10-unit quantization explanation was falsified by150->50; speculative quantization code removed. Planner now reads and respects factory limits, without EEPROM/factory writes. Supervised sequence completed5.640s excluding return; fig remained outside ring.


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

### ArUco mobil entegrasyonu — 2026-09-27

Kullanıcı siyah dış kareyi 36 mm olarak doğruladı ve kodlamayı yetkilendirdi.
Android v0.22, ID 0 / DICT_4X4_50 kullanır. Kamera-robot ve etiket-model uç
dönüşümü 8 duruşla birlikte çözülür; 4 ayrı kontrol duruşu hesap dışında tutulur.
Bu model referanslı eşlemedir; gerçek kavrama merkezinin vendor tip ile örtüşmesi,
motor sıfırlarının doğruluğu, baskı toleransı, sabitleme rijitliği ve canlı kamera
hassasiyeti PHYSICAL VALIDATION REQUIRED. Kamera ARCore CPU iç parametreleri ile
kullanılır; ayrı distorsiyon katsayıları verilmez. Bu varsayım kontrol duruşlarındaki
hata ve gerçek fiziksel ölçüm ile doğrulanmalıdır. Kalibrasyon motor ofseti yazmaz.
Algılayıcı hatası >1.5 piksel, yakın maliyetli farklı PnP yönleri, yetersiz iki-eksen
dönüş çeşitliliği veya kontrol RMS >8 mm / maksimum >12 mm ise kalibrasyon reddedilir.
Otomatik tarama kayıtlı eklem zarfı ve modelde minimum Z=30 mm koşuluna bağlıdır;
gerçek çevre çarpışma kontrolü değildir. Tarama yalnız uygulamadaki açık kullanıcı
başlatmasıyla çalışır. Kodlama/test sırasında kol hareketi başlatılmadı.

Doğrulama: 125 JVM testi, Xiaomi üzerinde 4 native sayısal test ve 7 Python
yayın/etiket testi geçti; Android lint hata vermedi (96 uyarı). APK v22 telefona
yüklendi. Canlı ekranda ETİKET 0 / 34,9 cm / net gösterimi görüldü; bu sayı
bağımsız cetvel ölçümüyle doğrulanmadı. Fiziksel otomatik tarama çalıştırılmadı.
APK SHA256: F89B0035FA7C1A6DF4BF440F9DFF57E0AB2A4DDF8458BBD68BB6B9F1AC3A428C.

### ArUco kağıt etiketi — tasarım parametreleri

Kullanıcı normal yazıcı kullanabileceğini belirtti; 3D parça yerine A4 PDF
hazırlandı. DICT_4X4_50 / ID 0, siyah dış kare 36 mm, beyaz pay her yönde
6 mm, kesim 48 mm olarak tasarlandı; bunlar ölçülmüş mevcut donanım değerleri
değildir. PDF renderinde OpenCV ID 0 okuması ve dört yöndeki kaynak desen testleri
geçti. Gerçek baskı boyutu, kamerada görünürlük ve montaj uyumu PHYSICAL VALIDATION
REQUIRED. Etiket-kavrama merkezi dönüşümü TBD; mobil ArUco desteği bu teslimde
eklenmedi. Etiket hiçbir kalibrasyon kapısını otomatik olarak açmaz.

### 2026-09-27 — Codebase-memory bağlantısı

Codebase-memory-mcp 0.11.0 araç bağlantısı yanıt veriyor; `figbot` isimli yerel
indeks henüz oluşturulamadı. MCP ve bağımsız CLI üzerinden fast indeksleme
`persist_failed` döndürdü. Kontrol sırasında C: üzerinde yaklaşık 37 GB boştu;
hata mesajındaki disk alanı/izin önerisi kök neden olarak doğrulanmadı.
AGENTS.md içinde graph-first, kapsam kontrolü ve sınırlı kaynak okuma kuralları
eklendi. İndeks başarıyla kaydedilip sorgu/kapsam kontrolü geçene kadar kod
grafiği hazır veya token tasarrufu ölçülmüş sayılmayacaktır. Kök neden UNVERIFIED.

### 2026-09-23 — İlk ortam ölçümü çizimi

OLCUM_REHBERI.png yalnız ölçüm tarifidir; çizimdeki boyutlar örnektir ve ölçekli değildir.
Kullanıcı ölçüm referansı O, tabanın dik dönme ekseninin montaj yüzeyine izdüşümüdür.
Ön yönü incir toplama alanına doğru kullanıcı tanımlar. Bu referansın vendor URDF
base_link ile dönüşümü UNVERIFIED; doğrudan robot hedefi olarak kullanılmayacaktır.
Sepet merkezi, iç çapı, iç taban/üst kenar yüksekliği, incir yüzey farkı ve meyve
yüksekliği kullanıcıdan beklendiği için TBD. Sepetin yuvarlaklığı UNVERIFIED;
yuvarlak değilse şekli ile iç en/boy istenir. Kamera–kol eşlemesi ve fiziksel hedef
doğruluğu PHYSICAL VALIDATION REQUIRED. Bu rehber kalibrasyonun tamamlandığı anlamına gelmez.


### Android v23 — kalibrasyon engeli ve destekli bırakma (2026-09-27)

Kullanıcı kalibrasyonu başlatınca “Joint … exceeds profile envelope” gördüğünü
bildirdi; eklem numarası/ham değeri önceki arayüzde kesildiği için bilinmiyor.
Bu hata otomatik taramanın mevcut duruş kontrolünden gelebilir; mevcut kayıtlı
hareket zarfları fiziksel tüm eklem erişimi değildir. Zarflar genişletilmedi.
Artık hata eklem adı, okunan konum ve aralığı gösterir; Kalibre penceresi her
yöntemin ön koşullarını canlı listeler. Elle ölçüm aynı encoder dalındaki
ölçümleri hareket zarfı dışında da kabul eder; bu hareket izni vermez.

Kolu tut / Kolu bırak, altı motorun tork geri bildiriminden seçilir; hareket
sırasında devre dışıdır. Destekleme onayı ve motor iş parçacığında durumun
tekrar kontrolü gerekir. Mevcut releaseSupported kullanılır; otomatik tork
bırakma eklenmedi. Tutma etkinleşmesinde 0,8 sn doğrulama bitmeden kullanıcıya
desteği çek denmez. Son hata ekranda/prefs içinde saklanır ve ayrıntısı açılır.
Kol dururken tek kötü etiket karesi ölçümü iptal etmez; otomatik duruşta 15 sn
sınırı korunur. Hareket sırasında görüntü kaybında mevcut durdurma korunur.
Fiziksel otomatik tarama, destekli bırakma/tutma ve kalibrasyon doğruluğu bu
düzeltme sırasında henüz çalıştırılmadı: PHYSICAL VALIDATION REQUIRED.

V23 doğrulama: 133 JVM testi ve 4 yayın testi geçti. Android assemble/lint başarılı
(0 hata, 97 uyarı). publish_current --android-app ile yayımlandı; Xiaomi
2d9cc5ea üzerinde adb install Success ve versionCode=23 doğrulandı.
APK SHA256: 63F000D48078B609F09255CBFE39B808EFF5E1A4D9618EB389C24E5DE2B00524.
Kurulum sonrasında telefon Dozing/kilit ekranındaydı; yeni ekranın canlı
etkileşim kontrolü ve fiziksel kalibrasyon bu turda doğrulanmadı.
Codebase graph persist_failed; bu değişiklikte kaynaklar doğrudan okundu.

### v24 canlı teşhis — 2026-09-27

Kullanıcı uygulamayı kullanarak teşhis istedi, Xiaomi ADB dokunma iznini açtı.
Kalıcı hata ID4=2738, kayıtlı aralık1789–2732 idi. PC köprüsünden yalnız register
okumaları: pozisyon=[2022,767,3946,2738,1152,792], hepsi tork1/hız0;
ofset=[4080,2861,85,85,85,85], voltaj12.2–12.3V. Kanıt tmp/calibration_motor_diagnostic.json.
ID5=1152 okuması pasif olmasına rağmen eski referans dalı yüzünden engelleniyordu.
Yeni yalnız-pasif profilde tam modulo dönüş FK'da kabul edilir; ID5 komutu hâlâ
yasaktır. Etkin eksenlerin dal kontrolleri korunur.

Kalibrasyona özgü ingress toleransı8 encoder sayımı (~0.703 derece) bir yazılım
politikasıdır, ölçülmüş mekanik sınır değildir. Yalnız ilk mevcut duruşu kapsar,
hedefler asıl zarfta kalır ve normal profil kalibrasyon sonrası geri yüklenir.
Tarama merkezi içeri kaydırılır; dirsek merkezi en fazla200 sayım ek içeri kaydırma
denenir. Model başlangıç Z=22.39mm; yalnız yükselen ilk çıkışta10–30mm kabul edilir,
sonraki bütün hedef/rotalar en az30mm'dir. Gerçek engel kontrolü değildir.
Canlı uygulamada PC bağlantı ilk okuması da180ms zaman aşımında reddedildi;
sadece açılış kimlik okumasına1000ms süre eklendi; komutlar tekrar gönderilmez.
Fiziksel kalibrasyon doğruluğu ve çarpışmasızlık PHYSICAL VALIDATION REQUIRED.

V24 doğrulama: 134 JVM testi, telefonda 5 native matematik testi geçti. Native
testte yukarıdaki gerçek encoder duruşundan üretilen rota sentetik kamera/etiket
dönüşümüyle 8+4 fit/kontrol kapılarından geçti; gerçek kameranın kalibrasyon
başarısı değildir. assemble/lint başarılı. APK publish_current ile yayımlandı.
Canlı telefonda PC bağlantısı kuruldu; Kol bağlı ve tutuyor, Kolu bırak görüldü.
Kalibre penceresinde artık aralık hatası yok; etiket yönü belirsiz olduğu için
automatik başlangıç kapalı. Kullanıcıdan kameraya hafif yan açı vermesi istendi.

V24 APK SHA256: 41ACD583D7D606D172A1730800251630C46F4AD9315E971BB2389D930D5A94F1.
Kullanıcı kamera açısını değiştirdikten sonra canlı Kalibre penceresinde
OTOMATİK: Hazır görüldü (tmp/figbot_v24_now.xml). Motor hareketi bu noktaya
kadar başlatılmadı; ellerin çekildiği kullanıcı teyidi bekleniyor. Genel home
komutu hâlâ asıl hareket zarfını kullanır; 8 sayım ingress yalnız kalibrasyondadır.

### Android v25 — etiket/nesne kararlılığı (2026-09-27)

Canlı eski hata: bir duruşta15sn boyunca kararlı etiket ölçülemedi. Kaynakta
ArUco+YOLO tek işlem sırasındaydı; null veya belirsiz kare motorun kararlı
zamanını sıfırlıyordu. Yeni marker işçisi bağımsız90ms hedef aralığında çalışır.
Son1.5sn içinde en az5 bağımsız, ön kalite kontrolünü geçmiş kare, 3mm/3derece
konsensüsüyle değerlendirilir; motor duruşu değişirse pencere silinir. Son iyi
kare400ms sonra geçersizleşir; görüntü önbelleği bu motor kontrolünü yenilemez.

İncir işareti derinlik olmadığında da çizilir. Görsel süreklilik en fazla800ms;
yeni motor hedefi yalnız gerçek güncel detection+depth verisinden oluşur.
AR izleme kaybında oturum sayacı geçersizleşir; eski asenkron işler yayımlanmaz.
Bunlar politika eşikleridir, fiziksel ölçüm doğruluğu garantisi değildir.

Canlı Xiaomi testinde ilk192/192, ardından870/870 etiket karesi görüldü ve yönü
netti. İlk1sn sonrası kararlı konsensüs korundu. YOLO91–457ms, ArUco60–120ms
civarında ölçüldü; gözlenen durumda incir sayısı1. PC motor bağlantısı kuruldu,
Kol tutuyor ve Etiket31.7cm kararlı görüldü. Kamera mesafesi cetvelle doğrulanmadı.
Bu test motor hareketi veya 12 duruş kalibrasyonu değildir.
139 JVM testi, assemble ve lint geçti. Codebase index persist_failed olduğu
için ilgili kaynaklar doğrudan okundu.

V25 motor bağlı izlemde en az1437/1437 etiket karesi görüldü/yönü net bulundu;
kararlı konsensüs korundu, periyodik günlüklerde incir sayısı1. 10sn ekran
kaydı tmp/figbot_stability_v25.mp4 ve FigbotVision günlüğü aynı isimli.log;
440 video karesinde sabit ROI içindeki etiket/nesne renkli işaretleri bulundu.
Bu sınırlı sabit sahne testidir; hareketli sahne, fig derinliği ve tam kalibrasyon
başarısı iddiası değildir. 4 yayın testi de geçti.

### Android v26 — kamera referansı geçici kayıp (2026-09-28)

Canlı logda kalibrasyon 1/12 ardından tek karelik 3 mm / 0,5 derece referans
kontrolü "Kalibrasyonda telefon oynadı" hatası üretmişti. Ayrıca stale camera
motor fault gözlendi. Kullanıcı telefonun fiziksel olarak sabit olduğunu bildiriyor;
AR konum sıçraması olası neden, bağımsız ölçülmüş fiziksel hareket değildir.
Yeni geçit kısa kayıpta stop intent'i stale kontrolünden önce işler, ölçümleri
korur ve yeni ölçüm/hedefi engeller. Aynı orijinal kamera referansı + güncel
etiket 250 ms geri geldiğinde kesilen kalibrasyon bacağı yeniden planlanır.
Referans 1,5 sn doğrulanamazsa kalıcı invalid; yeni kalibrasyon gerekir.
AR tracking kaybında observation generation yine değişir, eski işler elenir;
kalibrasyon sonucu yalnız geçit READY ve güncel izleme ile kullanılabilir.
Uygulama oturum değişimi hâlâ sonucu siler. Eşikler politika; hareketli fiziksel
12 duruş kalibrasyonu PHYSICAL VALIDATION REQUIRED.

V26 doğrulama: 146 JVM testi (0 hata), assemble, lint (0 hata / 97 uyarı)
ve 4 yayın testi geçti. APK Xiaomi 2d9cc5ea üzerine -r ile yüklendi;
dumpsys versionCode 26 / 0.26.0-camera-recovery doğrulandı. GUNCEL APK ve
build SHA256 aynı: 4ef4518d01f6e92c94536635afad65dec13e69b86af788cceaee025eba03798a.
PC bağlantısında altı motor okundu fakat mevcut tutma devri ID1 is not stationary
nedeniyle reddedildi. Yeni hareket/tork açma yapılmadı. Canlı görüntüde etiket
sol kenara yakın, oldukça eğik; algılayıcı seen=0. Fotoğraflardaki önceki
22 cm/kararlı görünüm bu son canlı görüntüyle aynı duruş değildir.
Tam hareketli kalibrasyon ve kısa kayıptan fiziksel devam doğrulanmadı.

### Android v27 canlı kalibrasyon takibi (2026-09-28)

V26 kullanıcının sabit telefonunda ilk ölçümden sonra AR referansı kalıcı kayıp
nedeniyle başarısız oldu. V27 yalnız sabit ayaklık sözleşmesiyle cameraMarker
(OpenCV kamera eksenleri, mm) üzerinden hand-eye fit yapar. Fig world noktası
aynı frame kamera dönüşümüyle aynı kamera uzayına alınır. Game rotation vector
1 derece / doğrusal ivme 0,8 m/s² 200 ms hareket ihlalini kilitler; bunlar politika.
IMU salt yavaş ötelemeyi garanti edemez: ayaklık oynarsa yeniden kalibrasyon şart.
Kaynak: https://developers.google.com/ar/reference/java/com/google/ar/core/Pose
ve https://developer.android.com/develop/sensors-and-location/sensors/sensors_position

Canlı v27 taramalarında 5 ve 6 duruşa ulaşıldı, 12/12 henüz doğrulanmadı. ID4
34/62/34 °C, ID3 34/97/34 °C tutarsızlığı görüldü. Kullanıcı elle sıcak bulmadığını
bildirdi; gerçek bağımsız sıcaklık ölçümü yok. 55 sıçraması iki tek-register63
ve bir tam feedback okumasında 34,34,34 ile reddedildi (FigbotMotor günlüğü).
Aynı teyit 90/97 gibi büyük sıçramalara genişletildi; üç değer soğuk ve tutarlı
olmazsa eski sağlık kapısı korunur. Akım/voltaj/konum korumaları değişmedi.
Tek frenleme paketi yanlışlıkla HOLDING sayılıyordu; 100 ms kesintisiz settled
geri bildirim eklendi ve STOPPING testleri gerçek zaman adımlarına uyarlandı.
Geçici dosyalarda figbot_calib_v27*.log kısmi ham/matris kayıtları var. İlk5
duruş kısmi fit offset std yaklaşık 2,93/1,53/0,99 mm; bu tam kalibrasyon veya
bağımsız fiziksel uç doğruluğu kanıtı değildir. Kullanıcı daha geniş kadraj sağladı.

### Android v28/v29 — sabit masa, kayıt ve eşleme (2026-09-28)

Kullanıcı kol tabanının alt yüzeyi ile incirin bulunduğu masanın aynı seviyede
olduğunu doğruladı. Bu kurulumda masa Z=0 kabul edilir; dış ortam/eğimli zemin
bu varsayımla doğrulanmış değildir. Kullanıcı 27,4 cm kamera-etiket mesafesinin
metreyle uyuştuğunu bildirdi; tam 6D poz veya uç doğruluğunun ölçümü değildir.

Başarılı 12 duruş taramasının eski kaydı: öğrenme RMS2,97 / bağımsız kontrol
RMS3,43 / max4,38 mm. Yeni konumlarda v28 RMS11,23 ve9,87 mm ile reddedildi.
Tek kamera mesafesi bu eşleme farkından ayrıdır. Eski başarılı kayıt dosyadan
geri alındı fakat yeni sabit duruştaki taze etiket/encoder kontrolü17,1 mm /7,8deg
farkla reddetti; harekete zorlanmadı. Yeni başarılı kayıt atomik saklanır;
uygulama yeniden açıldığında yarım saniyelik taze durağan veriyle doğrulanır.

v29: Park başlangıcından sonra kamera/base ve marker/tool dönüşümleri sekiz
öğrenme pozu üzerinde birlikte SE(3) least squares ile iyileştirilir. Rotasyon
artık ilk pozdan tek başına alınmaz. Açısal artık ölçeği100 mm/rad algoritma
parametresidir, fiziksel boyut değildir. Dört bağımsız kontrol pozu optimizasyona
katılmaz. RMS/max ve8deg kabul kapıları korunur. İlk yeni canlı deneme öğrenme
4,1 / kontrol7,4 / kontrol max13,0 mm olduğundan yine reddedildi. Encoder sıfırları
ve nominal URDF geometrisi bu fit tarafından değiştirilmez, fiziksel model
hatası veya etiket eğriliği kesin kök neden olarak kanıtlanmış değildir.

YUV hazırlığı tek geçiş CHW dönüşümüyle sıcak çalışmada17–22 ms gözlendi
(eski178–431 ms). Kullanıcı sahneye beyaz kağıt ve beş incir koydu; beş algılama
aynı görüntüde görüldü ancak önceki sahneye göre doğruluk kıyası değildir.
Masa ışını hedefi ve varışta kapatma/50 mm kaldırma kodu eklendi. Otomatik kavrama,
masadan kaldırma ve sepet çevrimi henüz fiziksel olarak doğrulanmadı.

Sıcaklık doğrulama üç ayrı register63 okuması + yeni tam blok kullanır; üçü
<55 ve birbirine<=2deg ise son doğrudan sıcaklık ve yeni bloktaki diğer alanlar
kabul edilir. Eski örnek kullanımı yok; tutarlı yüksek sıcaklık hâlâ durdurur.
04:06 canlı log ID4 blok60/35, ayrı35/35/35; tarama12 duruşa tamamlandı. Bu
kayıt paket sıcaklık tutarsızlığı kanıtıdır; bağımsız termometre ölçümü yok.

V29 son canlı doğrulama: IPPE adaylarına solvePnPRefineLM eklendi; 12 duruş
04:11'de tamamlandı. Öğrenme RMS5,0 / kontrol RMS7,4 / max13,3 mm: max12mm
kapısı nedeniyle REDDEDİLDİ. Son durumda HOLDING, hedef hareketi başlamadı.
Kol modeli/etiket geometrisi farkının kök nedeni kesinleşmedi. Kullanıcıdan
siyah karenin iki kenarında36mm ve düz/rijit bağlanma kontrolü istendi.
Kontrol noktası çıkarılmadı, tolerans yükseltilmedi, yeni fit zorla etkinleştirilmedi.
182 JVM testi, telefonda5 native sayısal test,4 yayın testi geçti; lint0error98warning.
APK v29 yüklendi; yayımlanan iki APK ile build SHA256 eşit:
fad53769036b7c6e535fa2e7f17880b374ab465f05002a32dd69bcd5271cd530.
Kalibrasyonun yeni pozlarda başarısı, yeniden başlatıp başarılı kaydı fiziksel
olarak kullanma ve ilk otomatik incir kaldırma henüz doğrulanmadı.

## 2026-09-28 canlı kamera ve toplama denemesi güncellemesi
Önceki başarısız denemelerin ardından bilinen etiket bağlantısıyla kamera
kalibrasyonu 04:35'te kontrol RMS5,2/max7,6mm ile geçti; yeniden başlatıp güncel
encoder/etiket üzerinden 04:40:55'te kaydı kullanma doğrulandı. Kullanıcı bu
oturumda telefonu hareket ettirdiğini bildirdi; değişen kadraj kayıt reddini
tek başına yazılım hatası saymaya izin vermez.

05:02:42'de kadraj denetimli 12 duruş taraması fiziksel olarak tamamlandı:
kontrol RMS4,0/max7,0mm. Kanıt: tmp/calib_visibility_live.log ve
 tmp/scan_visibility_live.png. 05:09:35'te aynı kayıt taze ölçümlerle tekrar
kullanıldı. 05:03 hedef denemesinde kol incirlerin yanına kadar ilerledi;
incir kavranmadı. Hedef örtülünce başka incire geçme hatası gözlendi ve düzeltildi.
Bir ara görüntü/model farkı20mm kapısını aştı; aynı duruşta sonradan kayıt
kontrolü geçti. Bu farkın tüm çalışma alanındaki kök nedeni henüz kesinleşmedi.

İlk otomatik incir kaldırma ve sepet bırakma PHYSICAL VALIDATION REQUIRED.
Yeni PickupCycle tüm yolu önceden hesaplar; kullanıcı talebiyle hedef örtülse
ve kavrama başarısız olsa da kayıtlı bırakma konumuna gider. Konumun35mm çevresi
kalıcı deneme kaydıyla tekrar seçilmez;35mm fiziksel ölçü değil algoritmik eşleme
parametresidir. Mevcut sepet konumu/yolun boşluğu canlı deneme öncesi soruldu.
Motor sıcaklığının arada blok/tekli okumalarda sıçramasının kök nedeni çözülmedi;
soğuk üçlü doğrulama veya hata sonrası tutma sürer, sıcaklık sınırı artırılmadı.

Son yazılım doğrulaması:195 JVM testi ve4 yayın testi geçti; lint0error.
Yeni APK kuruldu, uygulama açıldı, PC köprüsü üzerinden HOLDING okundu.
Build ve iki GUNCEL APK SHA256:
5488cff5599e89014a509c1c8e98e0a3d28a18154c71b3d44abb91d379ee711b.
Yeni kilitli alma/sepet çevrimi fiziksel olarak henüz çalıştırılmadı;
sepet yerinin ve yolunun değişmediğine dair kullanıcı yanıtı bekleniyor.

05:32:28'de son APK kaydı yeniden taze etiket/encoder ile doğruladı;
05:32:54'e kadar585/585 etiket ölçümü görüldü. Bu, canlı algılamanın çalıştığını
gösterir; AR PAUSED durumundaki düzeltmenin bağımsız fiziksel testi değildir.
Başlangıçta analizde yaklaşık30sn boşluk gözlendi; kesin kök neden henüz
kanıtlanmadı. OnDraw hata ve CPU kare yaşı tanıları eklendi.
Son durum HOLDING, motorlar33–36°C, ilk kavrama yok. Kullanıcı05:13'te kontrolü
bıraktığını onayladı; yeni tam sepet çevrimi için bırakma yeri sorusu yanıtsız.
Son tanılı APK build/yayın SHA256:
75dde1426da7adbd601462dff7b682e4489faa4becac9b7d3aebb6a7813305f8.
195 JVM ve4 yayın testi geçti; aynı APK telefonda05:31:26'da güncellendi.

## 2026-09-28 — Evening grasp and landscape validation
The 12-pose live scan completed with held-out RMS3.8mm/max5.7mm.
The subsequent pickup reached approach and open-jaw seating but did not close:
measured FK tip was below8mm. Nominal pickup height is now25mm; that is a
provisional bench clearance, not measured fruit height. Current/stall contact
thresholds and6-count jaw preload are PHYSICAL VALIDATION REQUIRED. No actual
fig lift or basket release has been verified for this implementation.
CPU capture timing now tolerates bounded image/frame clock skew;2500/2500 live
marker detections were observed after this fix, not a guarantee for all poses.
The phone was subsequently physically moved; saved calibration must be freshly
validated for its new pose before motion.

Landscape viewport fix was installed on Xiaomi2d9cc5ea. Live screenshots
 tmp/ui_rotation_fixed_land.png and tmp/ui_rotation_fixed_port.png show full
camera surfaces and aligned tag outlines across forced display rotation.
Menu auto-hide, persistent DUR, back-to-close panel, enlarged font scrolling
were checked on the device. Temporary rotation/font/animation settings were
restored.204 JVM tests and Android lint passed. The UI rotation check did not
command robot motion; a hand was visible beside/supporting the arm.

## 2026-09-28 — Relative rig reference verification
New tests cover a common rigid world transform applied to camera and base,
small residuals with an isolated outlier, persistent relative displacement,
return to the stored mount without resetting/recalibrating, mixed uncertain
measurements, and IMU settling after motion or a sensor gap.211 JVM tests pass.
Joint camera/base movement and automatic recovery remain PHYSICAL VALIDATION
REQUIRED on hardware. No robot movement was commanded for this change.
The APK was installed and connected read-only to the existing holding motors.
Live21:36 marker/encoder reuse rejected the old fit with38.6mm/92.2deg residual;
the saved file was retained. A physical phone rotation/reposition occurred in
this session; the residual alone does not prove its exact cause. No successful
reuse or ground-target pickup is claimed for this changed camera pose.

## 2026-09-28 — Recovered camera fit and actual grasp evidence
Seven existing interrupted-scan samples, recovered from prior tool output with
rounded rotation entries, support a known unchanged marker-mount camera fit.
Only three train the fit; four held-out poses give RMS5.72/max8.02mm. The old
record is retained in tmp/calib_recover_record.txt. Fresh phone/encoder checks
accepted the recovered record at22:43 and again after APK reinstall at23:09,
without a new scan (tmp/seat_axis_ready.png). This establishes live reuse for
the current fixed setup, not independent absolute fingertip accuracy.

The22:44 approach stopped before closure because planned body settling offsets
violated the jaw-only grasp guard. Closing now holds the measured body pose.
At22:56 an explicit close-in-place and50mm commanded lift completed; jaw872,
currentRaw0, CLOSED_WITHOUT_CONTACT, and tmp/grasp_here_2.png show an EMPTY grasp.
The fig stayed on the table. No successful pickup or basket delivery is claimed.
The later forward-axis seating correction is installed but its pickup outcome
remains PHYSICAL VALIDATION REQUIRED. Grasp height25mm and model TCP-to-actual
grasp-centre agreement remain UNVERIFIED.219 JVM tests and lint pass.

Live vision also labels a rear yellow/black tool as a fig. Automatic selection
must not be represented as validated object recognition. Attempted locations
are retained across restart; no automatic retry/history reset was performed.

23:13 follow-up: after the user repositioned figs and answered ready, a supervised
new batch explicitly cleared history through the UI. Target202,-164mm was saved
as attempted; the arm began approach but stopped before closure. No automatic
retry followed. tmp/axis_pick_camera_stop.log records repeated fit restoration
and camera WAIT/READY transitions. Subsequent clock-order fixes pass221 JVM
tests plus lint; hardware validation is recorded separately below when available.

23:19–23:21 clock-fix live check (PID26649): the stored fit restored once after
connection. No WAIT/READY churn or repeated restoration appears in
tmp/clockfix_pick_result.log during the subsequent supervised approach, seating,
closure and lift. The second, previously unattempted target229,-60mm was selected
and retained in history. Closure at23:21:21 reports CLOSED_WITHOUT_CONTACT,
raw[2170,1695,3743,1901,1151,872], jawCurrent0. Screenshot
tmp/clockfix_pick_2.png shows EMPTY jaws and the fig still on the table, slightly
displaced. The finite grasp-only cycle completed without basket motion.

At the lifted holding pose the independent marker/model check then rejected a
persistent12.3mm/2.6deg residual. The phone was not intentionally moved during
this run; this residual does not identify camera displacement versus model,
marker pose or mechanical error. A repeated camera scan is not established as
the remedy. Physical grasp-centre geometry and motor-reference accuracy remain
the next unresolved measurements; do not widen validity thresholds to hide them.

## 2026-09-28 — Independent quantitative audit
Historical visually successful grip goal780/read787/current3 differs from current
goal870/read872/current0 with unchanged ID6 offset85.90counts=7.91degrees more
open; current aperture in millimetres remains unmeasured. This is not permission
to replay old poses or apply780 blindly. Current contact threshold cannot be a
universal object-present detector; the historical held-grasp current/gap falls
below its criteria. Empty current trials are evidenced by images, not current
alone. Old3128/new1151 wrist roll differ173.76degrees, affecting jaw orientation.

At the recent miss, independent ±20count per-axis acceptance can give21.33mm
model TCP error. This is a computed possible combination, not measured actual
worst-case tracking. For recent table target229,-60mm the stored geometry gives
15.59degree ray depression and3.36mm XY sensitivity per vertical CPU pixel;
±5pixels gives16.13/17.50mm. These are uncertainty sensitivities, not established
camera errors. No new frame/sign/unit transcription error was found in scope.

Offline execution of current Android planner and activity's subsequent-leg
speed cap gives2.948s jaw close and15.905s total FAST six-leg timing for the
documented example, excluding IO/settling. This is not hardware maximum or
measured harvest duration. Diagnostic sources and outputs are under
reports/diagnostics_20260928. Creator exact video metadata and own published
model/dataset configs were checked; the comparison LeRobot upstream SHA is
pinned but not known to be the creator's exact checkout. Creator policy accuracy
on our phone/figs and training/inference on RTX3050Ti4GB remain UNVERIFIED.

## 2026-09-29 — Grasp-control correction validation
251 JVM tests and Android lint pass. Regression coverage includes whole-path
jaw-only closure, fresh measured body hold, light-current unverified closure,
all six leg speeds, persistent endpoint identity/schema and bounded model-space
arrival compensation. These tests do not prove physical grasp success.

Offline actual planner with the same reference target/start and effective870
closure gives FAST5.417s versus prior15.905s. Jaw closure0.884s versus2.948s.
These sums exclude IO, settling, vision and optional single compensation; they
are not measured harvest duration or hardware maximum. Reproduction source
and output: reports/diagnostics_20260929/PickupTimingAudit.java and
pickup_timing.txt. Slow300 remains intentionally slow.

The live phone immediately before install still reports12.4mm/2.7deg saved
marker/model disagreement; screenshot tmp/fix_before.png. This does not prove
camera movement. Actual physical grasp centre, pixel/table contact and motor
zero registration remain PHYSICAL VALIDATION REQUIRED. No automatic threshold
increase is a substitute for those independent measurements.

Device delivery: APK30 installed with adb success and launched on2d9cc5ea.
Final source/delivery APK SHA256 A6E6C583BA4EF49C2D2BFE1EF141C286A08F83C86CC83548F99C6FBC2109A662.
PC bridge reconnect restored read-only HOLDING feedback; one-session bridge
needed restart after package replacement. No new movement/torque-enable command
was issued. Settings UI saved870/1153 then explicitly selected the historical
780/1153 preset under the user's existing grasp-development authorization;
this persisted as RECORDED_2026_09_20_RAW_PRESET, not an automatic migration.
After final install/relaunch the camera/model check still rejects13.3mm/2.9deg
disagreement. No successful new physical pickup claimed. App remains connected
and holding; automatic target following was not armed.

## 2026-09-29 — User-measured work surface and v31 live calibration evidence
User confirmed base-bottom-to-fruit-table vertical separation: 65 mm, with the
base above the table. The user subsequently clarified that this elevation was
newly added for field-like testing and was absent during earlier failed pickup
attempts. The previous same-level setup was therefore not a retrospectively
established plane error. Exact installation timing relative to logged attempts
is TBD. In the raised setup's unchanged robot frame, ground Z=-65 mm; provisional grasp clearance
25 mm yields target Z=-40 mm. Grasp clearance is still UNVERIFIED as an actual
fruit/physical-finger measurement. No URDF dimension or encoder zero was changed.

Version32 (0.32.0-work-surface) uses one persisted height for camera projection
and pickup/calibration floor checks. Preference work_surface.base_height_cm
defaults to 0 only for legacy compatibility. The UI accepts 6.5 or 6,5 cm;
6.5 was saved on the Xiaomi and verified in work_surface.xml after APK reinstall
and cold start. Saving sends no movement and preserves camera calibration and
attempted-target history.
Integrated software checks passed: 282 JVM tests and Android lint.

On v31, a live four-pose known-mount calibration completed at 02:52:46–02:52:54:
two poses fit the camera transform and two held-out poses yielded RMS7.2/max8.2mm.
Evidence: reports/diagnostics_20260929/calib31_live.log and tmp/calib31_run1.png.
The user started that scan between our tool calls; we observed completion,
not a tool-issued start. Old seven-pose fits remain readable; unknown mount
still needs twelve poses. These fit residuals are not absolute grasp accuracy.

The subsequent v31 approach, closure and lift did not establish successful fig
pickup and used ground Z=0. Whether elevation was already present for this exact
attempt is UNVERIFIED; do not attribute its failure to elevation without that
chronology. The v32 work-surface
correction was then used for a live calibration scan, which failed the held-out
check as detailed below. Successful grasp, real finger clearance, basket delivery
and autonomous harvest timing remain
PHYSICAL VALIDATION REQUIRED; software tests are not physical success evidence.

## 2026-09-29 — v32 live scan rejected; observation discrepancy unresolved
With the new phone view, automatic saved-fit reuse rejected44.8mm/12.6deg error.
We explicitly started the 03:10:24–03:10:32 four-pose scan. All four measurements
were collected, but held-out RMS11.3/max15.5mm failed validation. No successful
v32 calibration, physical pickup or basket delivery is claimed.

Offline analysis of poses3→4: identical model rotation; expected marker
translation23.094mm versus observed34.207mm. A constant tool-marker offset or
ground-height change cannot remove that discrepancy. Relative to the fit,
the last observation has +12.1mm optical-depth and +8.8mm camera-vertical residual.
Optical pose bias versus actual physical movement remains UNRESOLVED; neither
is established by this calculation. Evidence: reports/diagnostics_20260929/ground32_math_diagnosis.json
and reports/diagnostics_20260929/ground32_live.log.

The PC bridge timed out at03:13. hold_on_disconnect was verified; the subsequent
direct read-only COM5 check found stationary motors at33–37°C. The prior live
torque readings were1. This is an observed stationary state, not a new physical
safety certification. Developer-only marker_diagnostics (default off) now
supports a32-slot PNG/JSON ring at up to1Hz for raw corner/intrinsics diagnosis.
Its live diagnostic check is pending; motion policy and acceptance thresholds
were not changed for this instrumentation.

## 2026-09-29 — User confirms mechanical play above ID1
USER_CONFIRMED: table/base clamp is firm, but the rotating body above the bottom
ID1 servo has visible right-left play. Reviewed background remains stationary
and independent PnP agrees with the observed marker motion. Exact root component
(servo horn/body attachment versus internal gear backlash) is UNVERIFIED.

Diagnostic model TCP[201.769,-279.824,57.765]mm versus observed
[231.714,-263.060,60.134]mm differs34.3996mm. A6.03823deg unreported base yaw
reduces position residual to3.36578mm and orientation residual to1.28312deg.
The separate orientation diagnosis gives7.05964deg observed rotation against
0.08789deg model rotation, with axis/vertical dot0.994596. These are consistent
with base yaw freedom; they do not identify the faulty fastener or gear, or
establish a reusable -68.7017count encoder correction.

Evidence copied from tmp with SHA256 equality into
reports/diagnostics_20260929/scan33_base_yaw_explanation.json and
reports/diagnostics_20260929/scan33_axis_diagnosis.json. Motor movement tests are
paused pending physical play repair and fresh correspondence/grasp verification.
No repair, torque-release command, or successful new automatic fig pickup is
claimed. The v33 geometric target filter is still being implemented; build and
device verification must be recorded separately when actually completed.

## 2026-09-29 — Stationary-start distance report and correction scope
User reports the fig overlay can show about 2 m for an object about 30 cm away
on stationary startup; the figure refers to the fig, not the known-size marker.
Those distances are user-reported examples, not an independently measured test.
ARCore hit-test ranges were a separate fallback from the metric ground-plane
calculation. That fallback is removed from KolActivity's fig display and robot
feed. No direct scene depth measurement is substituted or invented.

The camera/ground transform and pixel contact still require physical validation.
The new read-only 36 mm marker range dialog can be compared with a ruler while
the camera stays fixed; it is not a fig-distance or grasp-success check.
Live comparison remains pending. Another active chat controls the same phone
and arm, so this chat must not independently replace/restart the app or run
instrumentation while that hardware session is in use.

## 2026-09-29 — Repair reported; post-repair correspondence remains unverified
USER_REPORTED_REPAIR: rotating coupling tightened, play gone,12V off; user then
confirmed12V reopened for supported hold. Exact repaired component and residual
play across poses remain UNVERIFIED. Earlier pause pending repair was followed
by this explicitly supported post-repair calibration check.

Version33 built with290 passing JVM tests and lint; installed version33 confirmed
on Xiaomi and published through the current-artifact script. Shared-camera-chat
FigTargetGeometry changes were included. APK/source-delivery SHA256:
DD16CA42BAFBCF29B9764CDEFF60FE2662456CBA125B86A65039906854CA2F5A.

Second short scan03:56:45–03:56:53 collected four poses and was followed by green
robot XYZ on screen. However, repair33_live.log at03:57:07.596 then records
13.5mm/6.0deg marker/model disagreement; this does not independently prove a
remaining mechanical fault or establish camera displacement. Successful physical
fig pickup and stable correspondence across working poses remain UNVERIFIED.

DUR around03:56:55, then explicit disconnect around03:57:30. Bridge confirmed
holding measured positions and exited; no8873 listener remains. Phone/arm control
was ceded to the other active camera chat, and this chat stopped all hardware/ADB
actions. Evidence: reports/diagnostics_20260929/repair33_live.log and
reports/diagnostics_20260929/repair33_stop.png. These documentation updates have
not triggered a second publication while the other device session is active.

Offline report repair33_after_tightening_analysis.json fits the camera from
only the second scan's first two samples and evaluates the remaining two:
fit RMS0.70754mm, held RMS5.18490/max6.37688mm, max angle0.31205deg, unchanged
acceptance limits passed. Last-pair unmodelled yaw0.29441deg is much smaller
than the earlier6.03823deg example, but arm configurations differ; no controlled
same-route repeatability or independent absolute grasp accuracy was measured.
The first post-repair scan begins with7.81442deg unmodelled rotation and fails
acceptance; the later13.5mm/6.0deg reuse rejection also remains evidence.
Local improvement is supported, complete mechanical/vision repair is not yet
established. Report: reports/diagnostics_20260929/repair33_after_tightening_analysis.json.

Camera correction delivery/check: combined v33 target-selection build retains
concurrent changes. 290 JVM tests, Android lint, APK/test-APK build and 4 Python
publication tests passed. The 30 cm synthetic marker native test ran on the
Xiaomi and passed (1 test); it is a numerical, not physical accuracy check.
Published through scripts.publish_current --android-app; build and both GUNCEL
APK files have SHA256 DD16CA42BAFBCF29B9764CDEFF60FE2662456CBA125B86A65039906854CA2F5A.

After user-authorized coordination, the other hardware chat stopped and
released the phone session. The camera-only app was reinstalled/restarted,
without connecting motors or issuing motion/torque commands. The live read-only
ID0 dialog shows camera-to-marker-centre23.4cm, optical-Z22.6cm. Screenshot:
reports/diagnostics_20260929/camera_distance_check.png. User ruler measurement
was requested and remains pending; these displayed values are not yet a
physically verified distance. Ground-projection / fig accuracy remains pending.

User comparison: user answered "evet 23" for the lens-to-ID0-centre ruler
measurement, versus live23.4cm. Treat as approximate centimetre-scale agreement,
not a certified4mm error bound. A single marker range does not establish full
camera pose, tabletop targets, or grasp accuracy.

A temporary read-only PC bridge (tmp/camera_readonly_bridge.py) rejects every
non-read ST3215 packet BEFORE serial transfer. No calibration/motion command
was issued. With fresh encoders, the saved camera calibration restored at
04:02:24.238 without a scan. App reported stored held-out RMS5.7mm; this is its
prior calibration residual, not a new absolute distance measurement. All live
motor rows observed HOLDING/stationary. The foreground lower-right fig has a
calibrated contact-range estimate38.8cm; physical ruler comparison was requested.
Evidence: camera_ground_check.png, camera_ground_uncovered.png,
camera_readonly_live.log in reports/diagnostics_20260929.


## 2026-09-29 — Cross-repository pickup integration scope
The user reports ID1 upper-body play repaired, arm/camera connected and workspace
clear. Independent post-repair accuracy across working poses remains UNVERIFIED.
Concurrent camera/hardware chats were contacted with explicit user authorization.
No motion was initiated by the upstream-review chat while another chat owned
the device. The camera chat's approximate23cm ruler versus23.4cm optical marker
range does not validate ground-contact coordinates or physical grasp centre.

New full-cycle candidate search passes293 JVM tests/lint and an offline112-target
comparison (107 to110 complete plans). Desktop planning57.8ms and2.86% reduction
in common-case nominal time are model/host measurements, not Android latency or
hardware harvest performance. Existing15/10mm seating,25mm grip clearance and
mesh clearance are PHYSICAL VALIDATION REQUIRED. No seven-repository training,
MoveIt runtime, ROS2 hardware adapter or Isaac policy deployment is claimed.

Final physical comparisons in this camera session: user confirmed approximate
23cm lens-to-marker range against23.4cm displayed, then answered "evet doru"
when asked to compare the38.8cm lens-to-foreground-fig ground-contact range.
This establishes USER_CONFIRMED_APPROXIMATE_RANGE at two distinct checks, not
millimetre-certified full XYZ accuracy, all-workspace validation or a pickup.
The session began with an app restart and did not require moving the camera;
saved calibration revalidated through fresh marker and encoder observations.

The diagnostic bridge ended after15307 read requests when a non-read packet
was attempted; that packet was rejected BEFORE serial transfer, so no motor
write was sent through this bridge. The app subsequently reported EOF/bridge
closed. Last available feedback at04:04:13.830 was HOLDING/stationary, motors
33–37C; this is last observed state, not continuous telemetry after disconnect.
Camera control is concluded and device ownership released by this chat; no
pick motion was requested. Keep the successful approximate range comparisons
separate from calibration/model residuals and from actual grasp validation.


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


## 2026-09-29 — Oblique-view investigation and v35 limits
User reports repeated calibration errors in a far-side arm pose and requests
angle-aware validation. The stationary captured view is~63.27deg from the
marker normal.32 frame replay: SUBPIX position std[0.028,0.014,0.096]mm and
rotation difference range0.269deg; this is repeatability, not absolute accuracy.
CONTOUR increases depth variability and APRILTAG costs~29ms desktop versus
SUBPIX~4.5ms; neither is adopted from this one-view comparison. Existing SUBPIX
is retained. No proof yet that view angle alone caused the previous15–21mm
held-out discrepancy, and no correction is fitted to erase that discrepancy.

New local sensitivity estimates exclude camera intrinsics/distortion error,
marker size/flatness error, flex, rolling shutter and encoder/model bias. The
0.35px noise floor and3mm/3deg gates are engineering assumptions, not physical
confidence intervals. Remaining planar ambiguity still gates independently.
The native raster test uses ideal pinhole synthetic images (focal900px); its
0.637mm maximum is not a real-camera or whole-workspace performance claim.
Fresh real v35 frame at63.24deg: width33.61px, local sensitivity1.84mm/0.69deg,
usable=true, stable. It does not validate camera-to-robot coordinates.
No motor movement, torque release, new calibration or pick was initiated.
Before installing v35, explicit disconnect confirmed measured-position hold;
bridge exited. App reopened camera-only with motor session disconnected.

Final v35 delivery: APK and both published copies SHA256
E59B5730AC8BFF0840922E3CDFCCBD1773CF45CA78F79DF09987DB07417D5206.
Four publication/locking tests passed. Read-only on-device dialog shows
29.6cm marker range,28.5cm optical Z,63deg view with usable status.
This is not a new ruler comparison. Evidence: v35_angle_dialog.png and
validation.json under reports/oblique_marker_review. Motor session remains
disconnected; no restart of the bridge or new movement was requested.


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


## 2026-09-29 — Begin passive visual demonstration teaching (v36)
User explicitly changed approach: fix phone next to arm, demonstrate picking
figs by hand, and learn image-to-joint behavior. User confirmed supported arm
and final camera placement. Official SO-ARM100/SO-101 repository and LeRobot
imitation-learning guide were re-read: demonstration recording precedes policy
training/evaluation. Their standard leader-arm action stream is not present
here; our hand-guided follower data contains measured joint trajectories only.

v36 adds explicitly enabled loopback-only TeachingCameraServer with raw RGB JPEG,
phone capture timestamp, generation and intrinsics; independent of tag detection.
Phone motor connect is blocked in this export mode. phone_teaching.py owns COM5,
records all six measured encoders plus time-associated images using SessionRecorder.
It does not issue goal/enable commands. Optional supported release only writes
verified torque-off; initial physical preflight found ALL motors ALREADY torque0,
so no release command was needed or issued by this recorder session.

303 JVM tests, lint and16 Python tests pass. Actual camera export returns640x480
color JPEG without overlays, including four figs after user camera repositioning.
Motor+camera read-only preflight passed. First dataset opened in
GUNCEL/YAZILIM/ST3215_TEST/ARM_CONTROL/TEACHING/DEMO_20260929T015858Z.
At71 frames:9.77Hz, largest loop gap0.140s, all six torque0. User instructed to
show nearest foreground fig first, pause after placing it, and report outcome.
Recording active at this entry; success labels, replay validation and learned
policy remain pending. No trained network or universal reachable-area model
is claimed. Camera/encoder timestamps and estimated transport uncertainty remain
available for resampling and rejecting bad intervals. 200ms alignment limit is
an initial slow-teaching acquisition gate, not precise action synchronization.
Sources: https://github.com/TheRobotStudio/SO-ARM100 and
https://huggingface.co/docs/lerobot/il_robots . No cloud upload.


First manual demonstration closed:82.453s,800 RGB frames and800 encoder/timing
rows; all800 video frames decode. All recorded torque states0; max camera/encoder
estimated separation130.2ms, max transport half-RTT31ms. User corrected the initial
FAILED response: fig was held in the gripper and transported to the drop location.
outcome.json preserves that correction and marks SUCCESSFUL_MANUAL_DEMONSTRATION.
Frames around40/44/48s show approach/closure/lift; no powered grasp or autonomous
replay was performed. Approximate initial target pixel226,360 was annotated from
initial.jpg, not a measured robotXYZ. First record remains local withSHA256.
Second separate record is being prepared for the middle fig; no trained policy yet.

2026-09-29 demonstration update: first and second episodes are user-confirmed
successful manual pickups. Second: 1007 decoded frames, 102.704s, all six torque
states 0, maximum estimated camera/encoder separation 140.7ms. The third setup
capture (DEMO_20260929T020913Z, 107 frames) aborted on camera timing and is not a
successful demonstration. Only two demonstrations are currently accepted.
No learned policy, powered grasp validation, new-position generalization or
autonomous replay is established. Recording sends no enable or position command.

2026-09-29 session closure supersedes the two-demo status above: four manual
demonstrations are now explicitly user-confirmed successful, totalling 3226
frames. The distant-target episode is user-reported UNREACHABLE_TARGET; this
is not a measured geometric reach envelope. Repositioned left/right episodes
were successful manually. All recordings are stopped. No learned policy or
autonomous pickup has been validated by these demonstrations.

2026-09-29 offline learning update: five successful user-confirmed episodes now
include a four-object sequence (1282frames); policy_trained is true but autonomous
validity remains false. One recording with four pickups is not four independent
scenes. Held-out fourth-pickup error69.245counts exceeded40.768counts hold baseline.
All-data fit is not independent validation. Excluded rapid-motion intervals are
quality flags, not proof of a specific mechanical drop. Phase boundaries are
approximate video/encoder annotations. Opening1559counts is a synthetic shared
target based on observed raw opening, not a verified physical jaw distance.
Candidate900 duration60.302s vs75s demonstrated task is a theoretical estimate;
900counts/s and1800counts/s2 are offline proposal parameters, not approved live
limits. Cartesian collision/floor clearance and bridges through excluded spans
require physical validation. Arm remained unpowered/read-only during recording;
no motor commands were sent by offline training or route generation.

2026-09-29 physical dry-run update supersedes the torque-off recording state:
user-authorized current hold and jaw opening followed by first empty approach
were executed. Approach passed encoder check(max3counts) and user reported no
table contact. Lift/basket test aborted on stationary23count ID2 residual against
the20count criterion. Load-dependent tracking, friction/deadband or mechanics
remain unseparated; no specific defective component is claimed. Waiting longer
was not justified by the observed stationary residual. All six joints now hold,
verified by three read-only checks. No grasp or basket arrival was verified.

2026-09-29 update: bounded goal correction was physically tested on ID2:23count
residual reduced to4counts after final measured hold. Remaining empty taught
basket route completed(max12count final error). This supersedes the earlier
incomplete-route status, but does not verify loaded grasp or basket containment.
Underlying static residual cause remains unknown. Factory PID/deadband/offset
settings were read but not changed. The new red object in final camera view is
unidentified; no claim that it is a detached robot part is made pending feedback.

2026-09-29 superseding feedback: user confirmed the red object is unrelated.
First live fig closure reached jaw947 and short lift encoder target completed;
visual occlusion prevents asserting physical grasp. Actual lifted fruit and
basket containment remain UNVERIFIED pending visible/user evidence. The new
raw-current rise stop is a conservative experiment gate, not a calibrated force
measurement or proof of contact. Preserve measured jaw while lifting/carrying;
open only after verified basket endpoint. No new dimensions assumed.

Subsequent user confirmed physical lift. Retention failed during carry: final
fresh camera shows fruit separately on table, jaw encoder stayed947 throughout.
Insufficient grasp depth, finger contact geometry, compliance and motion effects
are not separated. A tighter closure alone is NOT a proven remedy. Basket fruit
delivery failed despite the motor route completing. No release command issued.

Second attempt supersedes overall no-success status: user confirmed high-lift
retention and final fruit inside basket; turn camera visibly showed held fruit.
First failure remains in evidence. Successful jaw939, manually aligned fig and
slower turn120 were tested together; cause of success cannot be isolated. One
supervised fixed-position success does not establish autonomous localization,
repeatability, throughput or generalization. Camera does not see basket interior.

Faster four-fig trial: only first fruit visibly held through transfer; basket
containment not independently confirmed. Second fruit was pushed and stayed on
table. Third gripper endpoint visibly misses current object locations; no close
attempt. Fixed demonstration joint poses do not establish current pixel-to-robot
mapping. Hand displacement, setup differences and mechanical effects remain
unseparated; do not blame a specific component or infer contact geometry from
occluded single-camera views. Narrow opening1283 is demonstrated motor travel,
not a measured half-width in millimetres. Android camera-only processing recovery
passed80frames, but that does not validate grasp alignment or four-object success.

Follow-up feedback is uncertain: user did not see the second failed contact and
only suspects forward displacement. Do not mark this USER_CONFIRMED_PUSH or
choose a blind depth correction from it. Subsequent phone absence from ADB and
HTTP timeout prevent current visual validation; old images/hold records are not
current-state proof. Need reconnection plus current camera/base placement status.
