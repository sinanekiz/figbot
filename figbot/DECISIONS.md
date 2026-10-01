## DEC-084 — Üç ince sert kepçe / ortak kremayer prototipi (2026-09-15)

CAD iteration record: use an open triangular perimeter of34mm circumradius, not a centre plate across the moving rods. Guide screws at localZ=-36/-30mm; guide split into two sideways removable halves with0.3mm nominal wing clearance. Through insert pilots allow the same finger to be used three times; install the120-degree finger's rod on the opposite tangential face to clear the pinion. Retain28-tooth gear:20-tooth trial interfered with the captured original star/rack interfaces and was rejected. Wrist-to-palm localX is52mm (first42mm study interfered with the existing wrist bracket); original W1 centre, spline/horn socket and arm spans remain unchanged. Final export/tests determine valid sample poses; no continuous collision certification. Recut original W1 horn/cover/screw access after adding frame webs.

Assembly review uses35-degree OPEN pose: servo enters axially before gears; rack enters sideways with guide halves removed; pinion/horn/closure unit approaches from negative localX with3mm axial offset, then seats axially. This is a sampled CAD sequence, not a physical assembly demonstration. Cable connector, tool access and real parts require trials.

Kullanıcı tasarıma başlanmasını, ince parmakları ve mümkünse ek satın alma olmamasını istedi. Aday başlangıç geometrisi: üç120 derece parmak,28mm pivot yarıçapı,12mm içeri krank,24mm rijit bağlantı,8mm sürgü bağlantı yarıçapı;0..35 derece açılma. Kepçe nominal1.2mm kabuk,5.5mm kök,50mm eksenel erişim; hareketli bağlantı plakası2.5mm, basılı mafsal burcuOD4/ID2.3/L3.1mm. Dişli modül1.25/28 diş/20 derece,4mm yüz, toplam aday0.30mm çevresel boşluk. Motor mevcutG1 ve özgün yıldızı; PLA kılavuzlar ve burçlar, ekstra motor/rulman/mil satın alınmaz. Tüm değerler tasarım adayıdır; fiziksel kuvvet, tolerans ve dayanım onayı değildir.

Hedef, mevcut listede kalan6 M2x8 ve6 M2L3 insertle altı bağlantı mafsalını kurmaktır; kılavuz kapakları M2x6/M2L4 kullanır. Listedeki satın alma adetleri gerçek envanter değildir. Parmak eskiyle aynı parça değildir; eski baskıya uyum iddia edilmez. Mekanizma inceleme çıktısı mevcut sabit CAD yolu altında tutulur, doğrulanmadan yeni baskı talimatı verilmez.

## DEC-083 — Ipsiz tutucu karşılaştırması; üç sert parmak yönü (2026-09-15)

Kullanıcı önce sadelik için iki kepçe çeneyi kabul etti. Bağımsız iki eş düz dişlili çalışma yalnız karşılaştırma CAD'idir: modül1.25,28 diş,20 derece basınç açısı,35mm merkez aralığı,4mm yüz,0.30mm nominal toplam çevresel boşluk ve0..24 derece çene hareketi. Bu değerler ölçülmüş veya fiziksel olarak doğrulanmış değildir. Montajlar, STEP/GLB, görseller ve inceleme URDF'si üretildi; baskı/BOM/firmware değiştirilmedi. İnceleme dosyaları GUNCEL/CAD/DISLI_TUTUCU_INCELEME altında baskı için kullanılmaz.

Kullanıcı daha sonra üç parmaklı ürün fotoğrafı gönderdi ve özellikle parmak esnekliği istemediğini, mevcut sert parmak biçiminin kullanılabileceğini açıkladı. Aktif tasarım yönü: mevcut G1 motoru, pinyon-kremayer ile ortak kılavuzlu sürgü, üç kısa rijit bağlantı kolu ve üç sert kepçe parmak. İp ve geri açma lastiği olmayacak; sürgü hem açmayı hem kapamayı sağlayacak. Bu bir mekanizma adayıdır, tamamlanmış CAD veya motor yeterliliği onayı değildir.120 derece yerleşim adaydır; yerden alma erişimi ve çarpışma değerlendirmesi belirleyecek. Sert parmakta isteğe bağlı yumuşak temas pedi esnek Fin Ray gövde gerektirmez.

Yeni uç için fiziksel incir boyutları, kuvvet-hareket ölçümü, motor erişimi, kılavuz sıkışması ve açık/kapalı tüm yol kontrol edilmeden baskı sürümü yayınlanmaz. Kullanıcının40–50g incir kütlesi korunur; bu bilgi çap veya sıkma kuvveti yerine geçmez. Önceki iki çene çalışmasının yaklaşık72.60g uç kütlesi, önceki71.61g tahmininden hafif değildir; hafiflik kazanımı iddia edilmez.

## DEC-082 — L1.5: 10 mm longer scoop fingers (2026-09-14)

User requests 10mm longer fingers with broad, thin distal scoops to reduce lateral fruit escape. Only L1-17 and L1-18 change relative to L1.4. Finger local tipZ -35→-45mm, head maximumZ4 retained (overall49mm); maximum transverse width49.19mm. Five ruled annular sections form each scoop, nominal radial wall1.6mm. Root width5.5mm, pivot bore5.1mm and both tendon bores/positions remain unchanged. No added hardware; L1-25 sleeves and all other23 printed types remain unchanged.

Candidate closed pose12deg retains minimum1.1447mm hard-finger clearance at the sampled poses -15,-10,0,6,12deg. This is not continuous swept collision certification or a promise of fruit retention. Fruit40–50g is user-provided; actual width/height remains UNKNOWN. The bottom and side seams intentionally remain open for clearance, drainage and movement. New1mm conformal TPU liners replace old flat4mm pads; compatible adhesive, food contact and actual friction/firmness TBD. No actuator limits or firmware are changed.

Print three replacement fingers in04A and three liners in05. Do not duplicate04/04A. Fingers print mouth up,4 walls/100% fill/5mm brim with external bed supports. Existing06 sleeves need not be reprinted. Export source, assemblies, closed-gripper scene, renders, URDF, print layouts, BOM and costs are rebuilt. CAD mass is a solid-volume estimate, not measured printed weight. PLA layer strength, supports removal, TPU fit, grasp reliability and creep require physical trials; manufacturing/load approval remains false.

# Design Decisions

## DEC-081 — Basılabilir plastik dirsek/parmak burçları, L1.4 (2026-09-14)

Kullanıcı burçları plastik olarak hazırlamamızı istedi. Mevcut baskıları mümkün olduğunca koru. L1-23 dirsek uzun burcu OD8/ID5,3/L28 bir adet; L1-24 aynı kesitte L4 iki adet, eski metal burç zarfında PLA deneme parçalarıdır. Eksen/rulman/vida/insert/pul/kol boyları değişmez. Plastik sıkma yükü altında sünme ve ezilme riski nedeniyle fiziksel yük onayı verilmez; ilk aşama yüksüz elle uyum kontrolüdür. Sıkma torku ve ömür TBD. Fiberli somunun varlığı plastiğin ön yük kaybını çözmez.

Eski parmak burcunun0,4mm et kalınlığı0,4mm nozzle için tek duvardı. L1-25 yeni PLA burç OD4,8/ID2,4/L6, et1,2mm; L1-17 pivot deliği3,2→5,1mm. Bu yeni çaplar tasarım adaylarıdır, kullanıcı ölçüsü değildir. Yeni burç eski parmağa sığmaz; üç yeni parmak04A ayrı tablaya konur. Parmağın5,5mm genişliği, iki tendon deliği, yumuşak ped, M2x14 vida ve kulaklar korunur. Yeni delik nominal2,45mm en dar yan ligamenti bırakır; sağlamlık hesabı/onayı sayılmaz. Burç-parmak çap payı0,3mm, M2-burç çap payı0,4mm, eksen boy payı0,5mm nominaldir. Bağlantı fiziksel olarak kontrol edilir; zorlayarak vida sokulmaz veya baskı delinmez.

06 ayrı tabla1 uzun+2 kısa+3 parmak burcu içerir; tüm burçların delik ekseni baskıZ yönünde,100% dolgu ve3 duvar metadata hedefi vardır. Dilimleyici ayar aktarımı ve gerçek kesintisiz duvarlar kontrol edilir. Eski geometri sadece L1-17 için değişir; diğer21 tip aynıdır. Metal burç kalemleri satın alınmayacak olarak değiştirilir, maliyet bilinmeyen filament ile güncellenir. Asıl625 rulmanlar ve24 çelik bilye korunur. Tüm güncel çıktı/zip dosyaları GUNCEL içinde; önceki dosyalar SHA256 doğrulamalı arşivde.

## DEC-079 — L1.2 continuous motor-foot floor and real buttresses (2026-09-14)

User points to unsupported motor-table feet in slicer. Section atZ75.9 confirms J3 outer foot has0mm² direct floor support; both J2A feet have22.283/140.566mm² (15.9%). A single connected CAD solid and collision pass did not test load-path adequacy. Earlier comment incorrectly called rectangular columns triangular gussets; correct it. Recommend stopping oldL1-06 print. No printer command is issued.

Change L1-06 base footprint from128×96 centred(-30,-9) to146×120 centred(-39,-6), stillZ75..80 with same4 screw axes. New boundsX[-112,34],Y[-66,54]. Add integral12mm-wide outward triangular buttresses fromZ79 to97, connecting each column to expanded floor. Reapply actual motor/flange voids and unchanged rear-crank sweep relief after union. Motor axes, apertures, crank65, fasteners and all other CAD parts unchanged. Preserve originalL1.1 ZIPs. L1.2 replacement-only deck must be separately named; do not silently overwrite downloaded files.

Check real root sections, assembly interference along sampled motion, exported solid validity and plate fit. No material strength, fatigue life, print support profile or physical load approval is inferred. User's no-machining preference remains unresolved for the two spacer families; this deck correction does not certify printed substitutes.

## DEC-078 — L1.1 assembly interfaces and complete hard-part screening (2026-09-14)

User is already printing plate01 at100% and has started plate02, and explicitly requests all corrections/checks. Keep the base, rotor, cage and two retainer halves unchanged; preserve the original issued ZIPs and identify replacement parts. Original L1 had real unscreened interference, including J3 horn cover/deck, crank/fixed retainer and fore-left/wrist bridge. Plate02 motor deck needs replacement; do not disguise this as a screw-only fix. No powered motion or printer operation is performed.

Raise J3 origin from(-65,-38,85) to(-65,-38,105)mm and change crank55 to65mm; keep upper150, fore120, coupler185, tail35 and shoulderZ110. These are deliberate design changes selected by closure/travel and solid-interference screening, not measured dimensions. J3 swept deck relief radius75 spansY[-37.8,-22.5]. Wrist bridge crossbar rises8mm, with continuous integral posts around unchanged factory-ear/pivot interfaces. Continuous crank angle representation is negative360..0 on the audited branch; never treat it as calibrated servo command range.

Both625 bearing outer supports now extend inward2mm (2.5mm backing wall); tip OD increases26 to32mm. Cap insert axes move from radius10 to12.5mm, increasing nominal ligament to the bearing pocket. Cap feet0.7mm seat on the plate; cap face19.2 gives0.2mm nominal axial end float rather than tightening an unsupported cap. M2x6 cap screws retain3.3mm nominal insert engagement. New upper plates and caps must be used together.

Replace the incomplete elbow shaft with a specified partial-thread ISO4762 M5x70 (nominal thread22, smooth48; incoming continuous smooth bearing land must reach47mm), two DIN125 M5 washers5.3x10x1 and one external M5 DIN985 locknut. Remove the asymmetric right-fore counterbore/boss; both fore outer faces are atY+/-27. Retain metal inner-ring compression sleeves OD8/ID5.3, lengths4/28/4mm, with square deburred ends; tolerance and bearing shield clearance require physical verification. No fully threaded M5 substitution at bearing journals.

Both rod ends use Elesa+Ganter ISO7379-4-M3-6 shoulder screws (shoulder4x6, threadM3x7, head7x3), two M4 DIN125 thrust washers4.3x9x0.8 per joint and a flush M3x4 heat insert at fixed seatY=-31. Rod thickness4 plus two0.8 washers leaves0.4mm nominal running clearance over the6mm shoulder. New crank/tail bosses include8mm-deep thread-tip clearance; the shoulder seats on the insert face, not on a free threaded spacer. Remove old rod sleeves and unspecified rear nut. Exact shoulder-screw designation matters; a regular M3x14 is not equivalent.

Motor ear hardware is M3x6 plus0.5mm washer (3.3mm nominal engagement with2.2mm ear) and M2x6 plus0.3mm washer (3.5mm engagement). Upper ties use M3x10+0.5 washer (4.5mm engagement), fore tie M3x8+0.5 (3.5mm), deck M3x10+0.5 (4.5mm), retainers M3x20+0.5 (4mm), wrist M2x8+0.3 (3.7mm). Correct screw head positions to outside the actual plate faces. Model the previously omitted retainer hardware and correct each8mm steel ball mass from0.332g to2.104g by geometry and7.85g/cm3; assigned masses still require weighing.

Sources: https://www.elesa.com/siteassets/PDF/PDF_EN/ISO%207379.pdf (manufacturer shoulder dimensions); https://eshop.wuerth.de/Hexagon-Socket-Head-Cap-Screw-ISO-4762-zinc-plated-109-steel-with-thick-layer-passivation-VZD-SCR-CYL-ISO4762-109-HS4-VZD-M5X70/415055%2070.sku/en/US/EUR/ (M5x70 partial thread22). Supplier stock is not certified. All exports, mass/cost candidates, URDF, views and affected tests must be regenerated. Physical insert/servo fit, printed strength/creep, tendon tuning and cable routing remain physical validation gates, not digital guarantees.

## DEC-077 — LINKA L1, new proximal-drive CAD (2026-09-13)

Final tool datum is wrist+(48,0,-45)mm, not the initial30mm study target. Forward palm offset clears the wrist stator during intermediate angles. Two L1-22 caps and inside shoulders axially retain the625 outer rings; metal compression sleeves4/28/4mm carry M5 axial clamp force through inner rings. These nominal sleeve/insert fits require physical trials. Tool mass target40g is not achieved; the design must not claim that it is.

Final L1 clearance iteration: wrist output axisY=-62mm relative to fore centre, reflected in IK/URDF; rear crank sweep relief and motor-deck bolts atX±28,Y±15. Printed guide eyes below the palm route separate closing tendons; three return bands have opposite opening moment. These replace intermediate44/50mm preview offsets that collided with the palm pillars and the inadequate early tendon lever. G1 captured-star rotating envelope is explicitly relieved; lateral torsion and soft-system parameters still require trials.

User explicitly rejects another unchanged R6 model and asks for a new lighter design using real working internet arms as references. New independently dimensioned source: `cad/prototype_arm/build_linka_v1.py`, viewer `linka-v1.html`. Mechanism references: MeArm official https://github.com/MeArm/MeArm and theGHIZmo EEZYbotARM Mk2 https://www.instructables.com/EEZYbotARM-Mk2-3D-Printed-Robot/. No reference STL or cutting file copied. References establish a buildable mechanism class, NOT performance validation of this adaptation.

Replace moving-arm geometry with two flat printable, windowed upper side plates and two separate fore plates. Axes150/120mm replace180/140 only in L1. Shoulder localZ110 (world176 on existing66mm mount), crank axis(-65,-38,85), crank55mm, coupler185mm, fore tail35mm; exact circle-intersection linkage solver. The55g J3 stator moves from distal upper arm to yaw deck. Keep4MG996R+2MG90S, paired shoulder, low wheel-front pickup/direct side basket, original factory-ear inserts, captured original stars and centre screws. Preserve known41.5x20.5mm J1 aperture and matched24x8mm/45mm-radius ball race; new removable deck bolts to new rotor bosses. Do not interchange R6 rotor and L1 deck.

Three short curved fingers use a compact open tripod palm, inward-facing compliant pads and individual elastic tendon links; actual fruit dimensions and elastic stiffness remain TBD. L1 introduces passive metal pivot sleeves and two625 bearings (5x16x5 nominal); these are design candidates, ownership/fit unverified. Fixed joints use inserts; rotating joints use sleeves so screw threads do not serve as bearing surfaces. Local100%/7-perimeter modifiers accompany structural part3MFs. This is inspectable CAD, not manufacturing approval. Old direct-elbow firmware is incompatible with the new linkage; no firmware, powered motion or purchasing is authorized by this CAD change. R6 full-arm release hold remains.

## DEC-076 — Evidence-based redesign; R6 printing recommendation on hold (2026-09-13)

User rejects R6 visual/function design and requests engineering justification. User confirms R6 NOT printed, actual figs40–50g; retain100g as separate upper requirement. Historical breakage must not be attributed to R6. R6 is reference-only, not a full-arm print recommendation. See reports/engineering_20260913/TASARIM_KARARI.md and scripts/arm_engineering_review.py for actual-CAD mass/COM, fruit-contact checks and uncertainty.

150/120mm links and tool(30,0,-45)mm are study candidates only;180/140CAD/firmware untouched. Target masses:65g upper print,70g elbow servo+upper hardware,45g fore print,23.4g wrist servo+fore hardware,40g complete tool; not achieved masses.25g extra allowance remains a scenario. Stall fractions are not continuous torque ratings. Retain original motor ears, keyed stars with external closures, centre screws and known mounting apertures. Future geometry must use continuous broad sections and short supported joint cheeks, compact three padded fingers and explicit compliant force distribution. Physical material/torque/grasp/gap/power and new3D clearance gates remain open. No manufacturing release, new CAD, purchase, firmware or movement in this review.

## DEC-075 — FORMA V6 R6 tapered transitions and captive star sockets (2026-09-13)

User requests correction of abrupt beam/seat/post transitions and shape-matched original servo-star sockets. User clarifies that external enclosure screws should retain the inserted star without additional fasteners through its tiny holes. Both source horns remain unmodified; original shaft centre screws remain required. All six outputs use a profile-keyed integral receiver plus one motor-facing printed closure, attached by two external M2x6 screws into M2 L4 inserts. No screws pass through peripheral horn holes. This supersedes R5 large-hole M2x5 fastening and micro OD8 washer retention. Large enclosure axes are X +/-19,Y0; micro +/-11.5,Y0. Pocket lateral clearance0.20mm, axial clearance0.15mm, closure2mm, blind pilot4.35mm deep plus entry clearance; candidate values require coupon validation. Closure part IDs F6-20 (4) / F6-21 (2). Do not substitute a printed spline.

Root webs taper from6x28mm sections into the unchanged hollow shell over X24..80 rather than ending abruptly near X52. Distal webs begin44mm before the shell end and taper from0.8x3mm embedded sections to6x16mm rounded sections through a smooth loft. Shoulder integral posts widen toward the rotor, with the existing servo openings and bearing clearance recut afterward. Preserve shaft axes, motor count,180/140mm spans, hollow midspan envelopes, wheel/basket positions, J1 aperture and all race/retainer running gaps. Added material and covers must be reflected in mass/moment screening; elbow moving mass target remains below150g. No rated strength or fit is inferred from CAD.

Rebuild assemblies, meshes, STEP, 3MF modifiers, renders, viewer models, URDF, BOM/cost and affected tests. Robotizmo M2 OD3.2 L4 / M3 OD4.5 L5 are sourced candidates, not measured fit; pilot calibration remains required. No purchase or device motion. Physical print orientation, insert pullout, cover retention, two-servo torque sharing and complete cable/tool access remain PHYSICAL VALIDATION REQUIRED.

## DEC-074 — FORMA V6 horn/load-path/retainer correction (2026-09-12)

User authorizes correction after browser review. Preserve DEC-073 J1 body aperture41.5x20.5 atX=-10.15, measured shaft axis, motor counts,180/140mm spans,24x8mm balls/R45 race,100mm shoulder height and existing running gaps. Recover original user-supplied horn references and model original centre screws and insert-mounted output screws. Exact current-specimen correspondence, spline/centre screw dimensions and fit remain UNVERIFIED pending comparison; never print a substitute spline. Review any provisional24/12mm hole pitches against those references.

Local structure candidates: preserve hollow midspans, deepen/widen integral non-J1 ear seats, widen root webs inward without encroaching horn plane, enlarge distal fork sections from4x12 to6x16mm; strengthen shoulder posts and connect them to rotor with integral lower gussets. Rotor central web increases2.5→4.5mm upward; outer retaining flange stays atZ60. Clip fixed retainer to existing rounded120x120 footprint (mount holes unchanged), roof top64→66.5mm while underside61.4mm stays fixed; enlarge rotor corner relief above the unchanged60.4mm ledge. New parts are a matched revision, not drop-in claims for older PB02 or R4 parts.

Rebuild all CAD, GLB/STEP/STL/3MF, views, URDF, cost/hardware reports and meaningful interface/collision/export tests. Re-check paths and moving mass; real strength, print properties, insert retention, complete cable/driver access and powered trials remain PHYSICAL VALIDATION REQUIRED. No firmware or physical-device operation in this CAD correction.

Final R5 details: recover the six-arm MG996R and asymmetric four-arm MG90 Arm03 user-reference contours, replacing the old24/12mm pitches. Large mounting axes are two recovered opposite source holes; smallhorn uses keyed0.20mm-clearance pocket and external M2x4/OD8xID2.2x0.5mm rimwashers atX±11.5. No smallfactoryhole drilling. Recut hornpilots after structural unions; cord holes start above the backingplate. Retainer reliefR60 became tangent to120mmoutline and failed watertightSTL; useR58 with2mmcardinalouterland. Widerpostlowerledge originally extendedR59.9 and failed+.9mmuplift check; trim only lowercornerledge outsideR57.6 overZ57.5..60.4. Functional rotorflangeR55 andledgetop60.4 unchanged. Preserve1.0/1.4mmroofgaps; matchedR5parts andphysicalrunningcheck required. M3x20retainer removesold2.5mmshim to retain4.5mmengagement. Reference-derived interfaces are not measuredphysicalfit. Two hornface coupons added.

## DEC-073 — Preserve J1 mounting clearance and audit assembly access (2026-09-12)

User reports the older aperture already fitted the motor but was tight with its cable; explicitly do not narrow it. Separate measured motor body dimensions from the mounting aperture. Keep J1 case39.9mm/offset-9.8mm/shaft5.7mm, but restore the full pre-DEC-072 opening:41.5x20.5mm centredX=-10.15mm (X=-30.9..10.6). This gives longitudinal case clearances1.15/0.45mm; it is not a new cable-fit measurement. Ear centres follow the measured case as in DEC-072, but physical ear dimensions remain unverified. Other servo mounts unchanged.

A separate rigid insertion-path audit found approximately6.37mm3 overlap at5mm lift even though the installed motor did not collide: the nominal factory ear clips the fixed bearing ring's inner edge. Cut a local rounded56.5x20.7mm entry envelope centredX=-9.8 overZ42..58. It is confined below radius40.8mm, preserves the ball groove, retainer, mounting seats and fasteners. Check the continuous union swept envelope of the nominal body/flange/shaft over60mm vertical travel, with upper assembly/balls/cage/ear bolts removed. This test excludes the real cable, connector and strain relief, so it is NOT a complete installation approval.

Do not assume a boot diameter, connector size or bend radius. Record those as TBD and request actual protrusion/width. Candidate assembly choice is cable-first entry into an accessible integral factory-ear seat; side-open routing or a structural service split must be selected after the boot envelope is known. A new separate rear clamp or arbitrary slot between insert bosses is not approved: it may obstruct service or weaken the bosses. No globally optimal claim; real wire motion, screwdriver access, insert retention, paired motor alignment, fatigue, strength and electrical sag remain open.

Rebuild V6 CAD/STEP/STL/3MF/URDF/renders/tests. Add a dedicated FORMA V6 browser view from current exported CAD, with whole arm, exposed fixed base, pickup/release context, motor visibility and transparent bodies. The service view removes the top assembly; it is not an installation animation. Preserve the prior R3 archive; new correction archive R4 is a dimensional prototype, not a final cable-complete print release.

Primary references checked: TowerPro MG996R product data (https://towerpro.com.tw/product/mg996R/) does not supply a verified wire-boot envelope for this specimen; Adafruit Mini Pan-Tilt assembly (https://learn.adafruit.com/mini-pan-tilt-kit-assembly/the-pan-base) demonstrates a split assembly approach, not a structurally equivalent fig arm; Prusa insert guidance (https://www.prusa3d.com/product/threaded-inserts/) supports heat-set fastening but does not certify these bosses. References inform method only; no reference geometry was treated as measured user hardware. No purchase or hardware motion.

## DEC-072 — Apply measured J1 body/shaft geometry to FORMA V6 (2026-09-12)

User asks whether the updated motor measurements are included; they were only recorded during DEC-071. Now apply the reported39.9mm main case length,7.3mm near-face-to-near-spline-edge gap and5.7mm spline outside diameter to the J1 yaw specimen only. Near case face to axis=10.15mm; case-centre-to-axis magnitude=9.80mm. Preserve source orientation: case centreX=-9.80, shaft/race axisXY=(0,0), motor topZ50. These must not be confused with the prior10.15mm body-centre offset.

F6-01 integrated motor cavity, ear seat/pillars and nominal ear insert centres follow YAW_MG; motor case envelope and shaft cylinder match measured dimensions. Retain0.8mm total body cavity allowance (0.4mm per side), width19.7/height42.9,49.5x10mm ear pitch and earZ=-12 as UNVERIFIED candidates. Symmetry of ears about the case and transverse shaft centring remain assumptions pending fit/measurement. This is not proof the finished motor mount is physically concentric. Original supplied horn remains an envelope and its spline is not newly manufactured. J2A/J2B/J3 and MG90S dimensions are not silently changed from one specimen's measurements.

Add F6-17-YAW-FIT as a separate small J1 ear/case coupon; retain F6-12 for unmeasured MG996R specimens. Rebuild assemblies, STEP/STL/3MF, renders, URDF, validation, mass/cost records and packages; verify axes from CAD surfaces and clearances/insert locations. Keep DEC-071 retainer relief. PB02 historical/current repair geometry is not re-centred by this decision. No live motor, firmware, printer or purchase operation.

## DEC-071 — Retainer inner-roof relief after reported rubbing (2026-09-12)

User reports the outer bearing frame rubs internally against the rotating plate's upper face and requests clearance. Increase nominal axial flange-to-retainer-roof clearance from0.4 to1.0mm for PB02. FORMA V6 investigation additionally found rotor pillar corner ledges atZ60.4 below theZ60.5 roof, giving only0.1mm clearance there (plain flange gap0.5mm). New V6 minimum roof clearance is1.0mm at those ledges and1.4mm at the plain flange. This is an explicit candidate print allowance, not a measured manufacturing tolerance or verified friction cure.

PB02: recess the inner roof from localZ15.4 to16.0 over R51.5..58.4, preserving outer wall/topZ18.4, radial capture overlap, bayonet locks, joining ears/pins, race contact and rotor/motor elevations. The relieved lip has2.4mm axial thickness. Export into new `release_02_clearance`; retain `release_01` as historical. Only the two revised side caps are intended as replacement candidates for the existing PB02 bench base; this does not approve reuse of the broken old arm.

FORMA V6: recess the retainer's inner underside (R53..60) fromZ60.5 to61.4, encompassing the radial sweep of the low pillar corners as well as the R55/Z60 rotor flange. Keep topZ64, outer fastener landR60..70, posts, screw lengths and all race/ball/shaft axes unchanged. Remaining local roof thickness2.6mm and radial flange capture overlap2.0mm are nominal CAD dimensions, not strength certification. Rotor geometry unchanged. Rebuild assemblies, exports, renders, URDF, collision/clearance checks and affected tests. Inspect free rotation,0.9mm hypothetical upward displacement without roof contact, and retained flange capture by1.6mm upward displacement; these are digital clearance checks, not allowed physical bearing travel. No motor motion, printer job, purchase, bearing-track modification or unmeasured servo-interface redesign.

The measured servo dimensions from ASM-20260912-BASE-MEASURED remain recorded but are not applied globally to the four motors during this narrowly scoped retainer revision: actual ear locating geometry and seating are still unverified. Axial clearance does not correct eccentric shaft alignment. Physical print warp, contact location, tilt, wear and capture under load remain PHYSICAL VALIDATION REQUIRED.


## DEC-070 — Reject V5 and start independent direct-ear FORMA V6 (2026-09-11)

User explicitly rejects V5 and requests a fresh arm inspired by https://www.youtube.com/watch?v=R7pfTQcmXE4, mounting motors by their factory ears with heat-set brass inserts, and restoring the ball-bearing base. V5 remains historical; do not recycle its clamp/capsule architecture or recommend its full-arm print. Browser inspection of the named FABRI Creator4.1 video confirms integrated rounded links and original horns; its kit uses different motor allocation, so no capacity or dimensions are copied.

Keep180/140mm link centres and4MG996R+2MG90S: yaw,paired shoulder,elbow,wrist,grip. Proposed V6 changes: base-to-shoulder100 instead of124mm; same66mm rover mounting plane ->166mm axis; compact tendon three-finger tool with(38,0,-66)mm nominal fruit offset instead of(34,0,-110). Restore PB02 race concept (45mm pitch radius,24x8mm balls) in a newly integrated screw-retained base; dimensions are not drop-in interchangeability with PB02. New fixed polymer joints use blind heat-set inserts. Original motor centre screw still screws into the motor's metal shaft; moving joints use smooth sleeves/bushings and insert-retained screws, never threads rubbing directly on plastic.

Nominal49.5x10 and28mm servo ear patterns, flange elevations, M2 horn pitches24/12mm and M3/M2 insert pockets4.2/2.9mm are candidate CAD parameters. Actual user hardware values remain UNVERIFIED; include first-fit coupons, explicit parameter map and hold full-arm printing until measured fit. Insert geometry must follow the purchased insert, not the Instagram4.1mm example. Three cords and compliant return/force limiting need physical routing and grasp tests. No firm grip/torque/strength claim. Rebuild CAD,meshes,renders,review URDF,mass/torque and geometric tests. No firmware, live motion, printing or purchasing.

Detailed V6 packaging and fit decisions: move ground pickup from Rev-I(700,415,20) to(740,415,20)mm to clear the compact wrist/servo envelopes; lift/clear/turn/release points remain as recorded in VALIDATION.json. Tool forward offset38mm is required by wrist/palm clearance. Base plate120x120x4; fixed retainer OD140; M4 mounting pattern100x100 replaces V5 100x86. Optional printed rover receiver132x142x10, topZ66, M4 pilot5.6x6. Rover truss is context, not released fabrication: high diagonal terminates inboard at(500,+/-330,47) then a low segment reaches(550,+/-415,47); its earlier direct diagonal collided with the new base and was removed. The plate-to-truss fastening remains TBD. Original PB02 parts other than qualified8mm balls are not claimed interchangeable.

Regional slicer reinforcement: ordinary prototype regions5 perimeters/30%; root, servo ear, bearing retainer support, palm pivot and M4 receiver regions7/100%; thin fingers and fit coupons5/100%. Regions cannot restore the section removed by a cavity, and density settings do not certify strength. Arm bodies are single continuous open oval beams with integrated supports, not split V5 shells. Passive joints use smooth metal sleeves retained by screws into inserts. Three-finger tendon routing shown schematically; return elastics and force control remain physical development items.

Final V6 local detail: finger-ear width16mm leaves1.6mm behind the4mm insert, with M2x14 pivot screw candidate. Gripper spool core diameter19mm encloses the horn insert bosses; three winding lanes separated by0.5mm flanges prevent those bosses intruding into the cord wrap. Cord lengths/forces remain uncalibrated.

## DEC-069 — Short bolted printable arm development (2026-09-11)

Mid-route wrist capsule clearance adds a local R28.5mm relief,3.6mm wide inY, centred at forearm(140,14.5,0)mm. This replaces a0.074mm3 nominal collision at the intermediate wrist angle; rerun exports and affected geometry/slice checks. It is a local clearance feature, not a widened permissible servo travel claim.

Detailed CAD corrections: fruit/tool offset is(34,0,-110)mm, required to clear wrist mounting/clamps. Shell joints use9 M3x40 bolts and9 aluminiumOD6/ID4/30mm compression sleeves, nominal6.25mm bores and flat washer lands. Scroll retainer holes atX+/-10mm clear the full finger travel; cam followerOD3/ID2.1 sleeves9.2mm with M2 fasteners keep the moving stack free. Guide/stem8.6/7.6mm, groove/follower3.8/3mm are prototype clearances. Finger requires removable slicer supports. The low vehicle plate expands to132x142x6mm to leave material around the100x86 M4 pattern. Candidate18mm carrier envelopes connect(300,280,90)→(550,280,51), (500,280,51)→(550,415,51), (310,285,90)→(500,280,140), (500,280,140)→(510,320,51), (510,320,51)→(550,415,51), mirrored inY. This routes support below the actual base/motor, replacing interfering Rev-I placeholder braces only in V5. Metal carrier fabrication/strength remains a separate physical design check. Full-horizontal torque screening exposes limited margin; folded transfer is the intended trial route. No assertion of lighter total mass or production strength.

User requests a printable, aesthetically coherent and structurally improved arm with existing motors. Develop AERO V5 separately from historical V4 and spatial Rev-I: 180/140 mm axis spans retained; replace separate weak root/beam ports with continuous flared, split shells and metal through-bolts. Nominal 30 mm high shell section with 2.4 mm skins and local bosses; compression sleeves at shell bolts; three identical radial fingers driven by one MG90S scroll cam, soft replaceable pads. Preserve four MG996R and two MG90S, original horns and original centre screws; use the updated user-supplied MG90 Arm03 contour as a fit candidate, not a confirmed fit. No printed load-bearing locking pins or servo spline.

Packaging correction from the spatial study: the prior complete servo/base interfaces require 124 mm base-to-shoulder height. On the 66 mm mounting surface this gives a 190 mm shoulder axis, not the provisional Rev-I 160 mm. The detailed three-finger mechanism uses a provisional 110 mm wrist-to-fruit offset, not the 60 mm visual placeholder. Recheck ground-to-basket reach and vehicle clearances with these dimensions. Cam OD76, guide OD88, radial law r=26-0.28*q mm over q=-25..25 degrees are trial geometry. All revised dimensions, prototype sleeve lengths and hardware interfaces remain subject to fit, grasp, thermal, fatigue and terrain validation. Retain no-conveyor/direct basket direction. No purchase or live movement authorized by CAD export.

## DEC-068 — Return to onboard basket, front low arms and existing servos (2026-09-11)

Additional provisional packaging dimensions: base plate centre Z63mm, upper face Z66mm; upper-arm closed oval section24x30mm with1.6mm wall, forearm section21x25mm with1.4mm wall. These are spatial study candidates requiring mounting, print-orientation and load validation, not released production dimensions.

User selects the prior integrated vehicle direction: existing servos, no conveyor, ground pickup ahead of the front tire and direct placement into an adjacent basket beginning above the tire. DEC-066 conveyors and DEC-067 specialized fleets are deferred alternatives. Retain two symmetric arm locations as in the previous integrated design, without claiming two physical motor sets are owned. Create Rev-I as a separate spatial/kinematic design study; preserve the existing Rev-H2/V4 files as historical hardware references.

Provisional Rev-I study dimensions: unchanged650x600 chassis,254mm wheels and830mm track; each shoulder at(550,+/-415,160)mm, shorter180/140mm joint spans and60mm wrist-to-fruit offset. The160mm shoulder axis replaces the earlier127mm conveyor study target only in this branch; it allows motor/support packaging and reduced extension on the higher basket route. Main basket rear/front X=-280/320, rear/front floor145/285mm; adjacent side entry extends toX510 with305mm floor and reaches over the front tire. These are documented design candidates, not measured manufactured dimensions or released STL interfaces. Preserve4MG996R+2MG90S per arm, yaw motion, supported roots and three-finger gripper intent. Verify target reach, sampled path/steering clearance and illustrative gravity loads before presenting results. Actual motor limits, continued-duty torque, strength, fruit size, transfer/slide behaviour, mounting/horn fit and fabrication details remain PHYSICAL VALIDATION REQUIRED. No BOM purchase, firmware or live motion changes.

## DEC-067 — Study separate mini pickers and shared transport (2026-09-11)

User proposes many single-arm mini vehicles collecting beneath trees into passive wheeled containers, with a separate vehicle exchanging/transporting them to the centre. Evaluate as an alternative architecture, not a production fleet commitment. Recommend short supported arms with nearby removable shallow trays, passive exchange carts serving active tree groups, empty-before-full exchange, and a transport route scheduled by capacity and fruit age. Start with one picker, then two pickers and one carrier; no claim that one carrier serves every future fleet size. Reuse 30-decare / estimated380-tree / estimated13,000-fruit / assumed40g / max100g baseline. The prior three integrated vehicles and paired conveyor concept remain reference alternatives; no CAD dimensions, BOM, firmware or purchases change. Fruit type, connected routes across three gardens, actual rates, cart/vehicle capacities, docking, quality and cost remain TBD. See reports/20260911_SPECIALIZED_FLEET_PLAN_TR.md and scenario JSON; arithmetic scenarios do not validate field throughput.

## DEC-066 — Low front arms feed paired incline conveyors (2026-09-11)

User proposes moving shoulders ahead of front wheels at wheel-radius height and depositing onto adjacent conveyors leading up to the basket. Adopt as the next architecture study: two low front arms, one narrow inboard conveyor per arm, one fixed work camera per side, first validate a single module with current camera. Nominal shoulder-axis target127mm follows current254mm wheels; NOT a frozen base elevation or revised CAD dimension. Existing high124mm shoulder pedestal cannot simply be stacked above that height. Two independent belt drives are candidates, not existing servo functions or purchases.100g payload/ground collection remain; arm-to-belt-to-basket is the proposed successor to direct basket placement, pending workspace, steering sweep, obstacle clearance, fruit handling, camera and power validation. No working-geometry/BOM replacement in this turn. See reports/20260911_LOW_ARMS_CONVEYORS_LAYOUT_TR.md.

## DEC-065 — Stage feasibility of the lightweight arm using existing servos (2026-09-11)

Baseline correction after user reminder: reuse recorded100g max object,40g mean and PLA0.4/0.2 print context rather than asking these as absent inputs. Ground pickup/basket placement is mandatory. Rev-H2 base280mm plus V4 shoulder124mm implies404mm shoulder height on that mount;30/36cm total-reach scenarios are not rover-ground solutions. Perform rover target-workspace and obstacle analysis BEFORE freezing a shorter arm. Lowering/relocating its mount is an alternative requiring a separate dimension/integration decision, not silently authorized geometry. No dimension changes here.

Create a feasibility plan, not CAD release: one bench arm first; retain four MG996R and two MG90S roles, explicit base yaw and independent joint bearings. Prefer supported direct yaw drive initially; the rendered pinion/ring is not selected and reduction trades servo angle for torque. Compare remote gripper against local motor by net mass and friction; preserve wrist function. Use closed hollow links, localized print modifiers and metal load-spreading joints. Require power isolation, measured mass/reach, root/horn coupons, gripper and dual-servo tests before a full build. Illustrative18/14cm and15/12cm link scenarios do not replace current300/220mm CAD. Static examples expose inadequate shoulder margin rather than certify feasibility; counterbalance or actuator change may remain necessary. Report reports/20260911_LIGHT_ARM_FEASIBILITY_PLAN_TR.md and scenario JSON are planning artifacts only; no firmware, BOM, CAD or purchases changed.

## DEC-064 — Diagnose power independently and re-size the failed arm (2026-09-11)

Adopt review direction after user reports power collapse, reach-dependent lifting failure and shoulder intermediate-connection fracture: isolate the battery/converter/cable/PCA path without servos; size moving mass and moment before selecting replacement motors; prioritize distal mass, reach reduction if feasible, broad supported root connection, compliant three-finger gripper and acceleration-limited control. Current closed hollow beams are not assumed solid. Oval/box and triangulated alternatives require section/load assessment; no automatic honeycomb strength claim. Exact redesigned span and dimensions TBD pending required reach, weights and fracture evidence. Keep current CAD dimensions/source unchanged and mark powered broken-arm use on hold. Report contains candidate architecture and diagnostic decision table, not a print release or certified strength analysis.

## DEC-063 — Send slider targets during user drag (2026-09-10)

Following user report of arm breakage during abrupt release-triggered motion, replace onStopTrackingTouch position submission with user-originated onProgressChanged submission. Preserve bounded/coalesced10Hz transmission, all-enabled preparation without positions, centre-first and stop behavior. No duplicate release send and no motion from programmatic setProgress. Guard UI move against disabled/rearming/disconnected state and uncentred non90 paired targets. Retain previous speed/range settings; actual acceleration and physical position are not measured. Continuous target updates do not prove that the broken assembly can move safely. Test rapid181-target input, latest-target sampling, separate-joint queueing and stop flushing. Only Android updated; installed UNO V5 unchanged.

## DEC-062 — Wide defaults and slider-only motion controls (2026-09-10)

Per explicit user instruction and reported successful500–2500us trial, Android v0.10 defaults all logical joints to that pulse range and360 command deg/s. Remove numeric entry/Go; settings becomes an accessible gear icon. Hide redundant centre controls except first activation/rearm of a shoulder pair. Preserve explicit centre-first, shared mirrored trajectory, manual disable and stop. Installed V5 accepts these commands, so no firmware rewrite needed. The additional request for wider pulse ranges/360-degree positional test is not implemented: actual motor variants/endstops are unverified, and manufacturer MG996R Robot specification is180-degree (https://towerpro.com.tw/product/mg995-robot-servo-180-rotation/). Arbitrarily relabelling the slider or expanding pulses would not establish physical360-degree travel. No CAD/BOM/purchase change.

## DEC-061 — Paired range calibration and simplified Android motion screen (2026-09-10)

User reports paired physical travel about 90 degrees across the 0..180 command scale with 360 speed selected, then requests all motors enabled with maximum default speed and settings hidden behind per-joint buttons. Provide Android v0.9/V5 and 360 default command deg/s. All logical joints arm once after validated fresh connection; arm alone sends no position/PWM holding target. Keep global stop, explicit pair first-centre, timeout/background stop and no automatic recovery after stop. Main controls preview slider target until release and provide numeric target + Go. Settings exposes disable/enable, speed, reverse and pulse range. Changing arm tabs only changes view; it does not stop the other arm.

Extend paired S and PAIR frames to five integers: leader, angle, speed, min, max. Permit min 500..1000 in steps of100, max=3000-min, default1000..2000. Source rejects active-range changes until a fresh enable resets the pair; UI re-arms after range change and requires centre again. Maintain a single shared complementary ramp and atomic adjacent-channel update. No automatic expansion to the widest range, voltage increase or physical endpoint assumption. Full command span at360 remains500ms at each range; actual motor angle/time/force must be measured. New clients reject V4 to avoid format mismatch. No CAD, BOM or purchase change.

## DEC-060 — 360 command deg/s, coordinated clients and firmware (2026-09-10)

At explicit user request raise the common P/S speed ceiling from 180 to 360 command deg/s. Add 240/300/360 selections in Android v0.8 and the desktop panel, retaining default 30. Version the controller handshake as V4/STATUS4 and reject V3 in updated clients; deploy client and controller together. Keep 0..180 command angles, paired shoulders at 1000..2000 us with complementary pulses summing 3000 us, centre-first activation, one I2C transaction for adjacent paired outputs, independent follower rejection, disabled startup, bounded serial parsing and existing stop/watchdog behavior. Do not widen paired pulse endpoints to address a reported roughly 90-degree physical sweep; servo pulse-to-angle calibration and mechanical limits remain unmeasured. Speed is an interpolation rate, not torque/power authority or guaranteed shaft speed. Test 360 boundaries and both paired trajectories for 500 ms full command-span timing with the fake clock. No CAD, BOM, wiring, physical motion or purchase change. Hardware reset/upload requires supported mechanism and disconnected motor supply; prepare and verify all artifacts first.


## DEC-050 — Full pin/socket AERO V4 bench arm reusing fitted couplers (2026-09-07)



- User reports good motor fit and requests the remaining printable arm with interlocking assembly, optional screws, and prototype operation without assembly screws. Implement a separate V4; preserve SNAP02/SNAP03 actual pocket/lid/tongue geometries and the original servo centre screws. Do not reinterpret the latest fit report as measured strength, endurance or complete-arm success.

- Preserve300/220mm joint spans,124mm shoulder height,4MG996R+2MG90S and beam offsets-18/+18mm. For this expressly printable bench variant replace V3 metal tubes by hollow printed20x20/16x16mm beams,204.6/128.6mm long, with local pin-bore bosses. New26mm-square sockets have20.5mm-square bores, end stops and two3.4mm pin bores per end. V3 metal cuts235/161mm are not interchangeable. No rover geometry or original purchase ledger changed.

- Large original tongue18x3mm slides into18.4x3.4mm void; micro12x2.4 into12.4x2.8mm void. Receivers start at localY23.5, stop atY52.3/44.3; cap geometries unchanged. Retaining bores match originalY34/44 and30/38; original3.3mm holes preserved, receivers3.4mm. Provide optional M3 nut/head access relief, rather than filling the sleeve cavities with structural webs.

- Printed pins:3.05mm nominal shanks,1.6mm heads, slotted tips0.8mm wide, radial barb increase0.325mm, tapered1.2mm noses. Grip lengths7.4/6.5/9.6/26.2/12.2mm for large coupler/micro coupler/motor clamp/beam/tower respectively. Passive axles use6mm shanks,6.65mm barbs,6.4mm bearing bores and14.6mm grip. All assembled stacks nominally0.2mm shorter than pin grip; elastic force/fatigue unknown. Optional M3 and M6 hardware is a design alternative, not purchased inventory.

- J1 nominal servo faceZ58, fitted coupler backplaneZ65; existing0.8mm thrust washer atZ73.7 and deck undersideZ74.5. Move ring supports to(±48,±45)mm with radial outriggers above the rotating sleeve/pin envelope. Preserve old base100x86 bolt pattern and add accessible x±50/y0 holes; bench restraint required. Actual servo/horn/thrust stack fit and shimming unverified; never use the centre screw to force the bearing stack.

- Shoulder servo nominal facesY±23, coupler backplanesY±16. Separate mirrored towers retain old motor clamp geometry; each has two8x6x9.8mm keys into8.4x6.4mm deck sockets, atX-38/+22,Y±39, with P6 pins atZ85.5. Foot seatZ90.5. Towers install vertically after fitting the motor and centre screw off the arm. MG90 faceY15.75/coupler backplaneY10. G1 moved to(30,0,-66)mm to clear the entire rotating capsule during finger opening; fixed fingertipZ-134. Palm supports routed outside the capsule sweep. Opposite journal supports and centre-screw driver passages explicitly retained.

- Rebuild all V4 part STEP/STL, full assembly STEP/GLB, review URDF and CAD renders. Pack75 new print instances (50 pins) on6 geometry-only plates, excluding18 already-fitted coupler pieces. Use local ECC2 installed profile256x256x256 and keep parts out of its246..256x0..20 exclusion. Small slots open upward in selected orientations to avoid trapped supports. No machine G-code/print command generated. Print profile/support behavior still requires slicer preview; initial trial uses conditional0.4mm/PLA settings, not universal machine instructions.

- Validate closed components, correct transform composition, matching quantities/pin stations, assembly insertion paths, all-pair overlap at default pose and sampled inter-frame motions including the complete G1 capsule. Record limitations of discrete checks, printed pin strength, servo pairing, power and external bench anchoring. Refresh a separate material/cost estimate using declared PLA density0.00124g/mm3, exact printed quantities, and null/TBD filament price; do not fabricate TL cost. Main-arm prototype assembly is now implemented; earlier full-clip NOT IMPLEMENTED notes are historical, not its current state.



## DEC-049 — MG90 native reference and SNAP-03 opposed-cover trial (2026-09-07)



- User supplies MG90servo_gear.SLDPRT and requests matching clip connections plus a full unattended arm print. Archive original unchanged. Local cadmpeg0.5.5, verified release ZIP SHA256 3a6d507944bbe5ce08f7aa6720ccdc953e265c19cb6d6630e242f03a88422ee8, decodes native DisplayLists; no source upload. STEP export gives invalid solid/negative volume and is REJECTED. Native mesh is one watertight component with consistent winding, 35x16.3x4.85mm, volume467.186mm3. Rotate only, no scaling. Source/license and physical horn identity remain unverified.

- New separate MG90-specific geometry; not a uniform scaled MG996R part. Canonical long arms along Y; body32x44mm, integral12mm-wide tongue endingY44mm, total32x66x5.5mm. Optional3.3mm holesY30/38 are not a finished AERO interface. FloorZ1.4, pocket topZ3.6, source plate2.1 thick; outward profile clearance0.20mm with last0.2mm entry relief0.40mm. Original lower central boss radius3.375 extends0.5 below plate; central access diameter7.4 clears it. Reference hub radius3.4 and height2.25 above plate.

- Two opposing same covers atZ3.7, thickness1.2, centre open aperture10mm, star axial play0.2mm. Rail underside45deg, top5.5; each lid tapered halfwidth12.6 at bottom to11.4 at top. Proposed latch deflection0.4mm, force/fatigue UNVERIFIED. Original horn and centre screw retained. No printed spline or tiny horn-hole screws.

- Motor non-shaft keepout beginsZ5.75 (reference hub end) as an explicit PHYSICAL VALIDATION REQUIRED assumption, yielding0.25 nominal print-to-plane gap. No real servo-case/spline clearance claim. Audit insertion, closure, torque stops and retention; rebuild local STL/STEP, assembly STEP/GLB, fixed URDF, render, print plate and ZIP; run SNAP02+03 regressions.

- Main arm dimensions, hardware, BOM, costs and motor firmware unchanged. Full clip-only integration is not implemented and not released: old round-hole adapters, motor clamps, M4 idlers and metal-profile joints still differ. Prepare a part-by-part integration list instead of packaging incompatible old parts as a completed arm. No unattended print, printer upload, automatic queue or motor command executed; the printer does not have confirmed automatic part removal.



## DEC-048 — Six-arm positive-key SNAP-02 connection (2026-09-07)



- User supplies `mg996_arm_4pad.step` and `MG996R_Standard_Servo_Horn_6_Arm.stl` and requests verification plus printable opposed-cover connection. Archive both unchanged with hashes. Four-arm STEP is a valid solid, 40x40x6.3mm; six-arm STL is one closed component, 31.28795x30.06656x5mm. They are not interchangeable. Only the six-arm contour is adopted for an isolated personal prototype, with CC BY-NC-SA attribution to InterSideraVersor / thing:4816510. Four-arm source/license unknown; no derived geometry from it.

- Replace the circular interface with the union of actual six-arm STL outer sections, simplified to0.003mm and offset0.20mm radially. Floor2mm, pocket2mm deep, final0.2mm mouth relief to0.40mm offset. Reference star flat thickness1.9mm, total5mm, hub OD envelope11.82mm. These source dimensions are not physical measurements of the user's horn. Retain original plastic horn and centre screw; no printed spline and no screws through the tiny star-arm holes.

- New body46x44mm with an integral18mm-wide short output tongue ending atY52mm; total46x74x6.8mm. Two optional future attachment holes diameter3.3mm atY34/44mm are not a finalized AERO joint interface. No new purchase or BOM entry. Centre tool access diameter8mm; the original centre screw bears on the original horn, not on the printed floor.

- Two identical opposite sliding lids: Z4.2mm, thickness1.4mm, open central aperture16mm; nominal star axial play0.3mm. Rail underside45deg, height6.8mm, normal clearance0.2mm in X at the matched slope. Latches require nominal0.5mm inward deflection; physical force/creep/fatigue unverified. Local3mm window bridges remain for slicer inspection. Prototype uses0.4mm nozzle/0.2mm layers; no generated machine G-code.

- Validate positive rotation stops in both directions, star axial capture, cover axial/pullout capture, open-body horn insertion and opposed cap insertion with the actual reference hub envelope. Rebuild STL/STEP, assembly STEP/GLB, fixed review URDF, rendered instructions and print plate/ZIP. Main arm/vehicle CAD and controller firmware unchanged; there is no motor command.

- Motor-case clearance check assumes non-shaft motor structure starts atZ7mm, at the reference horn's hub end. Print topZ6.8mm leaves0.2mm; this is explicitly a mounting constraint to check physically, not a confirmed servo dimension or spline fit. Release only the three-part unloaded bench print, not full-arm/loading/throwing approval. SNAP01 stays HOLD.



## DEC-046 - Continue with independent STAGE-02 bench and cable fixtures (2026-09-07)



- User asks to continue while the horn identity remains unanswered. Build only independent parts that do not adopt an unknown spline/star interface: a stationary MG996R bench stand preserving the AERO mount/clamp geometry, and a slip-on cable guide for nominal20mm square tube. Do not claim completion of the full clip-mounted arm.

- Stand proposed print envelope76x60x40.9mm; base5mm, nominal servo bottom clearance3mm, original clamp axes retained, two6x16mm side posts. Original M3 clamps/fasteners retained, rather than converting a load-bearing motor fixture to unvalidated clips. No hardware ownership assumed.

- Cable guide proposed internal square20.6mm, top throat19mm, walls1.8mm, axial width10mm, cable trough opening5.4mm. It is not a structural joint or proven strain relief. Insertion requires elastic deflection not verified by static mesh checks.

- Rebuild local part STL/STEP, reference assemblies STEP/GLB, fixed URDF, renders, print-only ZIP and tests. Main AERO CAD, BOM, purchased ledger and motor firmware unchanged. See cad/prototype_arm/stage02/ONCE_OKU.md and ASM-069. Existing missing horn identity and thickness still block the functional capsule integration.



## DEC-045 - SNAP-01 isolated retention coupon and reference correction (2026-09-07)



- User requests a printable first motor connection before extending the arm. Inspection of the actual EEZY gearservo mesh establishes its pocket is circular diameter20.8mm/depth2.5mm, not star-shaped; earlier visual interpretation confused facet lines with geometry. Do not infer positive torque transfer from reported fit.

- Build a separate two-part clip/retention coupon only: body40x38x9mm, floor2.4mm, source pocket2.5mm, lid34.2x34x1.8mm, lid lower faceZ5.15mm, front access diameter7mm and hub opening14mm. These are experimental proposed dimensions, not measured horn/servo specifications. Source-derived pocket retains CC BY-NC attribution; no commercial arm adoption.

- Two broad retention rails and latch windows constrain the sliding cover. Digital closed fit and rigid sliding path exclude overlap; insertion requires intentional latch flex, whose force/strain/fatigue are not validated. Explicitly no powered/loaded use: circular pocket has no positive torque key. Ask user which horn fits and for its image before the functional motor interface.

- Rebuilt local STL/STEP parts, assembly STEP/GLB, fixed inspection URDF, preview and tests. Main AERO V3, BOM and firmware unchanged. See cad/prototype_arm/snap01/ONCE_OKU.md and ASM-068. Do not advertise SNAP-01 as the finished requested motor connection.



## DEC-044 - SNAP-01 horn capsule concept (2026-09-07)



- User requests a two-piece snap enclosure around the supplied star horn and simpler screw-free assembly. Plan an isolated horn capsule with a shaped torque pocket, sliding retaining cover, broad retention rails and releasable latch detents. Retain the servo centre screw and current structural fasteners for the first prototype; latching a capsule does not retain the horn on the motor shaft.

- Scope is a documented concept, not implemented CAD or a print release. See docs/KLIPSLI_SERVO_BAGLANTI_PLANI.md and ASM-067. No critical dimensions, BOM, AERO exports or firmware changed. Geometry/clearances/material and measured retention loads must be established before adoption.



## DEC-043 - Six-motor CARD-02 illustrated cardboard experiment (2026-09-07)



- The user requests a detailed IKEA-style PDF with 2D cutting and 3D assembly instructions for all arm motors, superseding the limited CARD-01 teaching fixture for this experiment.

- Provide a separate short bench concept using four MG996R (yaw, two shoulder, elbow) and two MG90S (wrist, jaw). Proposed cardboard tube blanks are 70x110 and 50x110 mm, with four25mm faces and10mm closure tab. They are NOT joint-centre lengths; final L1/L2, fork spacing, support height, horn holes and fastener lengths must be measured on dry assembly.

- Use a180mm fixed base,140mm turning deck, passive sliding support ring, paired shoulder brackets and opposite pivots at elbow/wrist. Templates are proposed household blank cuts, not a fitted manufacturing design. Drawings illustrate assembly logic; no CAD collision/strength validation is claimed.

- Record unknowns in ASM-065. Include original horn attachment, paired-shoulder calibration, separate verified servo power, restrained unloaded-first tests and no100g/high-speed throwing approval. Firmware, AERO CAD, URDF, controlled dimensions and purchased BOM remain unchanged.

- Deliver `output/pdf/FIGBOT_KARTON_6_MOTOR_MONTAJ_KILAVUZU.pdf`. Validate page geometry, exact PDF cutting scale and content; render and visually inspect every page.



## DEC-001 - V0 before mobility



- Problem: Scope includes bench, manual-mobile, and autonomous versions.

- Options: build all in parallel; or validate manipulation first.

- Decision: Complete V0 digital and physical learning before detailed V1/V2 investment.

- Reason: lowest cost and fastest risk reduction.

- Impact: V1 model is packaging-only; V2 components are not selected.



## DEC-002 - Four-axis arm retained for V0



- Problem: Determine minimum useful joint count.

- Options: 3-axis position arm; 4-axis with tool pitch; higher DOF industrial layout.

- Decision: retain J1-J4 plus G1, with J4 mechanically simple and low mass.

- Reason: ground approach and funnel release benefit from tool pitch while extra roll is unnecessary.

- Impact: four coordinated axes; decision remains subject to V0 task testing.



## DEC-003 - 605 mm nominal tool-tip reach retained after comparison



- Problem: longer reach increases torque, inertia, and cycle time.

- Options: 520, 560, 605, and 650 mm nominal tool-tip reach candidates.

- Decision: retain 300 + 220 mm structural links plus an 85 mm tool offset (605 mm nominal) for V0.

- Reason: the deterministic 100-target study produced 90 complete cycles at 605 mm versus 80 at 520 mm and 88 at 560 mm; 650 mm gained only one additional target while increasing mass and J2 torque.

- Impact: `SIMULATED / UNVERIFIED`; camera acceptance region and physical bench layout must be measured before freezing stock lengths.



## DEC-004 - Hybrid aluminium/printed construction



- Problem: all-printed arm has uncertain stiffness and fatigue life.

- Options: all printed; machined metal; aluminium tubes with printed housings.

- Decision: aluminium rectangular tubes and metal shafts carry primary loads; printed parts package bearings, sensors, covers, and molds.

- Reason: accessible fabrication with lower moving mass and repair cost.

- Impact: printed structural joints remain `PHYSICAL VALIDATION REQUIRED`.



## DEC-005 - Passive compliance before closed-loop force control



- Problem: figs are damage-sensitive and force limits are unknown.

- Options: current-only control; load cell; passive spring/compliance plus current limit.

- Decision: use replaceable silicone fingers and spring compliance with conservative current limiting; keep a sensor mount for experiments.

- Reason: simpler V0 and safe experimental tunability.

- Impact: force setpoints are `UNVERIFIED`; physical damage testing is mandatory.



## DEC-006 - One robot-base coordinate source



- Problem: CAD packaging, kinematics, collision proxies, camera calibration, and Gazebo must reference the same frame.

- Options: independent visual offsets; or central base-frame coordinates.

- Decision: J1 is XY origin, ARM-001 top is Z=0; funnel volume center and camera optical-center targets come from `cad/config/parameters.py`.

- Reason: prevents visually plausible but analytically inconsistent assembly placement.

- Impact: V0/V1 STEP, GLB, reports, and calibration documents rebuild from the same parameters.



## DEC-007 - Hollow prototype joint housings



- Problem: initial solid ARM-004/ARM-006 CAD masses exceeded the aluminium link masses.

- Options: keep solid for stiffness; machine metal; add controlled cavities to printed prototypes.

- Decision: retain bearing rings/load paths and hollow low-stress volumes in the digital prototype.

- Reason: nominal density calculation reduced ARM-004/006 to approximately 0.215/0.233 kg and aligns with the low-inertia objective.

- Impact: printed stress, insert pull-out, fatigue, and proof-load tests are still `PHYSICAL VALIDATION REQUIRED`.



## DEC-008 - V0 axes use coaxial planetary geared closed-loop steppers



- Problem: the earlier 6:1/12:1/10:1 belt concept had no frozen pulley pitch, belt length, tensioner, or packaging and could not be manufactured from the shown CAD.

- Options: two-stage timing belts; strain-wave reducers; or purchased 10:1 planetary geared closed-loop steppers.

- Decision: use StepperOnline 23HS22-HG10-E1000 + CL57T-class driver for J2 and 17HS15-1684D-HG10-AR4 + CL42T-class driver for J1/J3/J4. The gearbox outputs drive separately supported joint shafts through clamping hubs.

- Reason: both motors have published dimensions and vendor STEP files; the 10:1 reducer removes large pulley stages and gives a common, serviceable axis architecture.

- Impact: J2 peak demand exceeds the gearbox continuous permissible torque but is below its published momentary torque. A counterbalance, reduced acceleration, torque-speed bench test, and proof-load test are mandatory before use. `PHYSICAL VALIDATION REQUIRED`.



## DEC-009 - Raspberry Pi 5 and Camera Module 3 Wide form the V0 compute/vision pair



- Problem: Camera Module 3 is CSI-2 and was inconsistent with the earlier reused x86-host baseline.

- Options: x86 plus USB camera; Raspberry Pi 5 plus CSI camera; or an RGB-D camera.

- Decision: freeze Raspberry Pi 5 (8 GB preferred, 4 GB minimum for bring-up) with Camera Module 3 Wide for the low-cost planar V0 bench. Pico 2 remains the deterministic motion controller.

- Reason: both boards have official mechanical drawings/STEP data and a supported camera stack. The table task can start with calibrated planar geometry.

- Impact: monocular RGB does not measure arbitrary depth. Target surface height must be controlled; RGB-D remains an upgrade after the V0 pick pipeline is measured.



## DEC-010 - PartGo RFQ formats and process split



- Problem: custom parts need uploadable manufacturing data rather than viewer-only meshes.

- Decision: CNC parts receive STEP/STP plus a controlled drawing, sheet parts also receive DXF, and printed parts receive STEP plus STL. The verified service is `partgo.co`; `partgo.com` is not the referenced Turkish manufacturing platform.

- Reason: these are the formats published by PartGo for CNC, sheet, and 3D-print quoting.

- Impact: automated online pricing is only a DFM/quote signal. Bearing fits, threads, GD&T, food contact, and safety-critical requirements still require drawing review and first-article inspection.



## DEC-011 - Separate vehicle, arm and brain products



- Problem: the first mobile BOM combined a high-clearance vehicle, robot arm, RTK, outdoor LiDAR, AI compute, industrial safety, tooling, spares and one-off engineering into one unit cost.

- Options: continue one full autonomous prototype; or validate independent low-cost modules.

- Decision: develop P0 flat-ground camera rover, P1 independent bench arm and P2 modular brain separately; integrate only after each module passes its acceptance tests.

- Reason: isolates technical risk, permits reuse of test equipment and prevents development/NRE from being reported as vehicle COGS.

- Impact: the earlier high-clearance Option 2 BOM remains a future reference, not the active purchase baseline.



## DEC-012 - P0 uses two-wheel differential drive



- Problem: four independent driven/suspended wheels dominate the first vehicle cost and are unnecessary for flat-ground camera/control validation.

- Options: four driven wheels; two driven wheels plus two casters; or purchased indoor robot base.

- Decision: use two independently driven 10-inch pneumatic wheels, two swivel casters, 24 V power, a dual brushed driver, Raspberry Pi 5 camera computer and ESP32 low-level controller.

- Reason: robot-vacuum-like kinematics are low-cost, observable and sufficient for manual camera driving, line/AprilTag following and obstacle-stop development.

- Impact: P0 is not an orchard terrain vehicle. Its estimated 20 kg payload, one-hour runtime and 0.5 m/s limit are physical test gates.



## DEC-013 - P0 traction baseline is 2 x 24 V 250 W



- Problem: the generic 200 rpm motor candidate has no published power, torque or current data and creates too much payload uncertainty.

- Options: keep the low-cost generic motors; use two 24 V 250 W geared brushed motors; or return to four-wheel outdoor traction.

- Decision: use two Pilmak-listed 24 V 250 W geared brushed motor candidates, a Cytron MDDS30 dual driver and a 24 V 18 Ah LiFePO4 candidate for the P0 costing baseline.

- Reason: each motor draws approximately 10.4 A at 250 W nominal electrical input, below the selected driver's published 30 A continuous-per-channel rating, while two motors preserve the low-cost differential layout.

- Impact: estimated P0 purchased-part cost becomes 71,435.37 TRY. Output rpm, continuous torque, stall current, shaft drawing and battery BMS current remain purchase gates; one motor is sampled before buying the pair or releasing sprockets.



## DEC-014 - Four equal wheels, rear drive and front Ackermann steering supersede DEC-012



- Problem: swivel casters do not match the intended vehicle appearance, forward steering behaviour or later transition from level ground to firm orchard lanes.

- Options: two driven wheels plus casters; skid steering with four wheels; four-wheel drive; or two rear driven wheels plus two front steered wheels.

- Decision: retain two 24 V 250 W rear traction motors but use four equal nominal 10-inch pneumatic wheels. The front pair steers through an Ackermann linkage; a 24 V linear actuator is the first low-cost steering candidate. `DEC-012` is superseded.

- Reason: all four contact patches can cross the same small surface discontinuities, steering does not scrub all tyres like skid steering, and only two traction motors are required.

- Impact: the vehicle can no longer pivot in place. Knuckle, hub, tie-rod, actuator stroke, steering sensor and mounting geometry are `TBD` until samples are measured. The P0 vehicle estimate rises above the former 80,000 TRY target.



## DEC-015 - Front-centre arm, basket behind, ground collection only (superseded by DEC-026)



- Problem: an arm at the rear needs excessive reach, while a side-mounted arm produces asymmetric mass and collision zones.

- Options: front arm/rear basket; rear arm/long reach; side-by-side arm and basket; or front-centre arm with the basket immediately behind it.

- Decision: put the removable arm base on the centreline slightly behind the front axle, the padded collection basket immediately behind the arm, the battery low between the rails, electronics low/side-serviceable, and the camera forward/down-looking. The task is fallen-fig collection from the ground, not picking from branches.

- Reason: the shortest useful arm can reach the ground in front of the bumper and rotate/drop rearward into the nearby basket while keeping lateral mass balanced.

- Impact: `FIGBOT_P0_ROVER.step` is an integration packaging study only. Per DEC-011, vehicle, arm and brain are still tested independently before the arm is physically fitted to the moving platform. Stability, camera occlusion, tip-over, gripper clearance and fruit-damage tests remain mandatory.



## DEC-016 - P0 Rev-B uses real purchased-arm geometry and readable mechanisms



- Problem: the first P0 packaging render used a twice-wide wheel extrusion, a disconnected camera proxy, solid block arm proxies and a full deck that hid the steering/drive architecture. It was not a credible physical representation.

- Decision: correct each tyre to its controlled 60 mm total width; model tyre/rim/hub separately; expose kingpins, tie rods, actuator body/rod, rear motor/gearbox and chain guards; use split 6 mm deck panels; place the battery on the deck below a raised slatted basket; connect the camera mast/brace/boom; and import Waveshare's official `RoArm-M3_STEP_260310.zip` geometry at the controlled arm base.

- Reason: purchased-part geometry and visible load paths provide a more honest interference and packaging review than decorative blocks.

- Impact: deck top becomes 111 mm, the basket bottom 232 mm and the camera centre `(270,-180,418)` mm. These packaging dimensions remain `PHYSICAL VALIDATION REQUIRED`; vendor STEP inclusion does not validate load, reach, repeatability or mounting-hole compatibility of the delivered revision.



## DEC-017 - P0 Rev-C widens wheel track and moves the camera to a structural bridge



- Problem: Rev-B retained a 400 mm wheel-centre track around a 450 mm frame. At steering angle the front tyre swept through the frame rail, while the single camera post occupied the same region as the right-front wheel. The raised basket and electronics also lacked explicit supports/trays.

- Options: shrink the frame; use smaller wheels; reduce steering angle; or keep the 600 x 450 mm frame and move the wheels/kingpins outward.

- Decision: keep the 600 x 450 mm bolt-together frame and 254 x 60 mm wheels, increase wheel-centre track to 670 mm, connect the front kingpins with a 580 mm axle beam, add rear stub axles/bearings, and retain a +/-30 degree steering limit. Move the camera to a two-post bridge at X=30, Y=+/-175 mm, Z=600 mm with a centre boom and camera at `(270,0,575)` mm. Add an explicit battery tray/straps, four basket posts and an open electronics tray containing Pi 5, ESP32, MDDS30, DC/DC and contactor envelopes.

- Reason: the conservative full-steer calculation gives at least 20 mm tyre-to-frame clearance, and the camera feet sit behind/inside the front wheel sweep rather than above a tyre.

- Impact: overall tyre-to-tyre width becomes approximately 730 mm although the structural frame remains 450 mm wide. Rev-E supersedes these vehicle dimensions through DEC-027; actual kingpin offset, tyre deformation and fastener heads still require measured-part collision checks.



## DEC-018 - Handheld Android scanning is an observation experiment, not a branch-picking release



- Problem: determine cheaply whether a tablet/phone can mark visible figs, estimate distance and express observations in the FIGBOT base frame while a person walks around a tree.

- Options: purchase depth hardware first; build an Android ARCore experiment; or infer monocular range from assumed fig size.

- Decision: build an ARCore V0 field scanner with optional Depth API, automatic offline dry-fig-candidate boxes, two-point `base_link` registration, JSON export and explicit HTTP observation transfer. Bundle a public dry-fig-data bootstrap detector for phone testing, explicitly train fresh/green figs as negatives, and keep FIGBOT-camera-trained detection as a validation gate.

- Reason: it allows recognition and coordinate feasibility to be tested without a hardware purchase, while explicitly separating a bootstrap demo model from the future FIGBOT field model.

- Impact: all phone-derived XYZ values are `UNVERIFIED — PHYSICAL VALIDATION REQUIRED`; the payload explicitly denies arm-motion authorization. The active mechanical baseline remains ground collection per DEC-015, and branch picking is not released by this experiment.



## DEC-019 - Field-adapt the phone detector at 640 pixels before hardware purchase



- Problem: the 320 x 320 public-image bootstrap missed most small dried figs at the planned approximately 600 mm camera height and produced large texture false positives.

- Decision: use a 640 x 640 offline YOLO11n detector adapted with the five reviewed phone screenshots, explicit stone/flower/sofa/bag negatives, and synthetic small-object compositions. Keep confidence at 0.35 and package the frozen ONNX model in APK v0.3.

- Reason: the supplied-scene fit audit found all 14 labelled dried figs with no extra boxes, whereas the bootstrap failed on the same small-object scenes.

- Impact: this is a field-adapted experiment, not an independent accuracy claim. New raw phone video and then the fixed FIGBOT camera view must be labelled and tested before coordinates can inform robot motion.



## DEC-020 - Add real orchard soil as a separate adaptation gate



- Problem: APK v0.3 recognized the supplied indoor scenes but struggled when the same dried figs were placed among gravel, dry leaves, flowers, concrete edges and perspective blur outdoors.

- Decision: retain the 640 x 640 model and 0.35 threshold, add four reviewed orchard phone photos with 20 whole-fig boxes, train full-frame and context-scale views together, and rehearse the earlier indoor and synthetic data.

- Reason: the frozen v0.4 ONNX fit audit detects all 20 orchard labels and all 14 earlier labels without extra boxes on those supplied scenes.

- Impact: the result shows adaptation to the reported failures, not orchard accuracy. The next unseen orchard photo/video batch must remain frozen until its pre-training results are recorded.



## DEC-021 - Treat grass occlusion and leaves as explicit detector failure classes



- Problem: APK v0.4 was reported as roughly 90% successful, but it missed pale dried figs crossed by grass and sometimes boxed whole leaves or leaf litter as dried figs.

- Decision: retain the 640 x 640 detector and 0.35 threshold; add six reviewed dry-fig boxes from the new failure screenshots at full-camera and context scales, and add clean leaf, leaf-litter, soil, grass, and fresh/dark/wet-fig crops as negatives. Exclude all screenshot UI and detector-overlay pixels from training crops.

- Reason: the frozen v0.5 ONNX fit audit finds the six unique new dry figs, the 20 earlier orchard figs, and the 14 indoor figs, while producing no boxes on the reviewed new negative crops.

- Impact: this is failure adaptation, not independent validation. The next unseen raw orchard sequence must be scored before any further training, and camera-derived targets remain unauthorized for arm motion.



## DEC-022 - Include bruised and purple scrap-grade figs in the collection class



- Problem: v0.5 treated some dark or wet-looking ground figs as negatives, but field practice classifies bruised, purple, dark, split, low-grade fruit as saleable `hurda incir` that must still be collected.

- Decision: keep a single collection class but redefine it to include normal dried figs and collectable hurda figs. Add 11 labelled figs from three new screenshots, relabel three clean earlier dark figs as positives, remove the 40 conflicting negative repetitions from rehearsal, and retain clean leaf, dry-leaf, glove, rock, and soil negatives.

- Reason: the frozen v0.6 ONNX fit audit detects all 14 new/corrected unique hurda examples and all 40 earlier labelled figs, with no boxes on the six new reviewed negative crops.

- Impact: the detector decides only `collectable_fig_candidate`; it does not grade quality or price. The 54/54 result is training-scene fit, not independent accuracy, and coordinates remain unauthorized for arm motion.



## DEC-023 - Stage the external mechanical RFQ before series release



- Problem: a supplier requested finalized design files, while the custom arm is an engineering candidate and the P0 rover still contains unmeasured purchased-part interfaces and a purchased-arm packaging reference.

- Options: label the current rover STEP production-ready; delay all supplier contact until physical parts are purchased; or issue a controlled staged RFQ for design freeze, first article and later series pricing.

- Decision: issue a mechanical-only staged RFQ. The separate 605 mm custom-arm assembly is the requested arm scope; the RoArm-M3 inside the P0 rover remains a space-claim reference. The supplier must close the interface register and manufacture one validated first article before any series release.

- Reason: suppliers can price engineering, prototype and future quantities now without misrepresenting packaging geometry or inventing unmeasured interfaces.

- Impact: the RFQ package is suitable for quotation and DFM only. Production approval remains blocked by incoming-component measurements, first-article inspection and physical validation.



## DEC-024 - Define the supplier package as a lightweight V1 collection demo



The 300/hour throughput proposal in this historical decision is superseded by DEC-025.



- Problem: suppliers need the product purpose, real arm load, throughput expectation and electronics ownership boundary before they can size and quote the mechanism.

- Decision: describe the current package as a preliminary V1 demonstration design. The camera localizes ground objects, the arm collects objects weighing no more than 0.10 kg and places them in the onboard basket. Use a stationary-demo acceptance target of at least 300 successful pick-and-place cycles per hour, while leaving mobile field throughput for physical validation. Favor a lightweight, quick and inexpensive arm rather than excess lifting capacity. All integrated control hardware must remain reprogrammable by the buyer through documented interfaces.

- Reason: a 0.10 kg handled object does not justify a heavy industrial arm, and a 12-second complete demo cycle is a clear, conservative supplier target relative to the existing simulated arm-only results.

- Impact: successful first-article validation may lead to hundreds of units, but this is a commercial possibility rather than a production commitment. Payload, cycle rate and field throughput remain physically unverified until timed tests pass.



## DEC-025 - Request supplier feasibility for 50-100 objects per minute



- Source: requester clarification on 2026-08-31.

- Decision: replace the proposed 300/hour stationary benchmark with the user-requested objective of 50-100 successfully collected objects per minute within a 5 m2 test area. Express 3000-6000/hour only as an arithmetic equivalent, not sustained hourly capacity.

- Boundary: this objective requires 0.6-1.2 s/object for sequential collection and is not demonstrated by the current 605 mm arm or prior simulations. Suppliers must assess feasibility, include perception, gripping, basket deposit, retries and base repositioning in system testing, and propose an achievable initial-demo rate or alternative architecture if required. Test duration, object layout and replenishment remain TBD.

- Impact: no CAD dimensions, actuators, operating limits or safety factors are changed to imply this performance. The 100 g limit is handled-object mass; gripper mass, arm mass and dynamic loads remain additional sizing inputs. Hardware must still be buyer-programmable, and production remains conditional on successful validation.



## DEC-026 - Rev-D uses two front arms and adjacent side basket inlets (superseded by DEC-027)



- Source: requester sketch and clarification on 2026-09-02 that the vehicle has two arms.

- Problem: Rev-C showed one centre arm carrying every object toward a narrow basket behind it. The long transfer and near-180-degree base reversal consume cycle time, and the model did not represent the intended two-arm architecture.

- Options: retain one centre arm; add a second arm but retain one remote drop point; place two arms at the rear; or place two front arms beside a widened centre basket with an inlet next to each arm.

- Decision: keep the 600 x 450 mm frame, 670 mm track and 430 mm wheelbase. Place two removable 125 mm arm adapters at `(105,+85,111)` and `(105,-85,111)` mm. Use a 280 x 500 x 160 mm main basket centred at `(-140,0)` mm with bottom Z=232 mm and mirrored tapered side inlets. Use nominal drop points `(65,+185,280)` and `(65,-185,280)` mm. Move the electronics and battery side-by-side below the raised basket and replace the two camera posts with one centre post between the arm plates.

- Reason: a deterministic 100-target plan-view comparison reduces mean pick-to-drop distance by 30.6% and mean yaw motion by 33.1%. Two independent work regions also permit parallel collection. The 500 mm basket overhangs the 450 mm frame by only 25 mm per side and retains 55 mm to the rear tyre inner faces; the tapered inlet retains 33.2 mm to the conservative front tyre sweep.

- Impact: DEC-015's single-arm placement is superseded. Rev-D remains a packaging concept. The 45 mm static gap between arm adapter plates does not prove dynamic arm clearance. Y=0 overlap targets require ownership logic and shared-volume interlocking. Full two-arm sweep, camera occlusion, inlet transfer, filled-basket stability, power capacity and physical cycle-time tests are mandatory. The 50-100 objects/minute objective remains unverified; ideal two-arm operation requires at most 2.4-1.2 seconds per arm cycle.



## DEC-027 - Rev-E moves the basket to the front and places both arms at its sides (superseded by DEC-028)



- Source: requester correction on 2026-09-02: the arms must stand at the sides of the basket, not behind/in front of it, and the basket must be the foremost body module.

- Problem: Rev-D still placed the basket behind the two arm bases and used projecting side chutes. That did not represent the intended architecture.

- Options: force the layout into the 600 x 450 mm Rev-D frame; use a narrow basket between close arm mounts; or widen the rover so a useful basket and two 125 mm arm adapters can share one longitudinal station.

- Decision: supersede Rev-D. Use a 650 x 600 mm frame, 830 mm wheel-centre track, 510 mm wheelbase with front/rear axles at X=290/-220 mm, and two arm bases at `(100,+260,111)` and `(100,-260,111)` mm. Put a 400 x 350 x 180 mm basket at the front-centre, centred at `(100,0)` mm, with its front face at X=300 mm and 150 mm low openings in both side walls next to the arms. Support the arm plates on a transverse 660 mm structural member. Move the camera bridge behind the basket and extend its boom forward.

- Reason: the arms now flank the basket at the same X station and release directly inward through the low side openings. The widened frame preserves calculated clearance instead of overlapping the arm adapters with the steered tyres. Rev-E retains 25.5 mm tyre-to-frame, 27.0 mm arm-adapter-to-front-wheel-sweep, 22.5 mm basket-side-to-adapter and 25.0 mm basket-front-to-frame clearances in the static plan calculation.

- Impact: the previous 600 x 450 mm frame, 670 mm track, rear basket and tapered side inlets are no longer the active integrated layout. Vehicle width becomes approximately 890 mm across tyres. Supplier pricing, steering linkage, frame material, mass properties and transport width must be refreshed. The official RoArm STEP remains only a packaging reference; the 605 mm custom-arm reach, dual-arm sweep, structural outrigger, front-loaded stability, camera view and physical cycle time require validation.



## DEC-028 - Rev-F uses a front-high, rear-low basket floor



- Source: requester clarification on 2026-09-02 that an object released at the front of the basket should move to the rear so filling starts at the rear.

- Problem: Rev-E has a flat floor and centred side openings. Objects can remain beside the release points, consume local capacity and obstruct the next deposit.

- Options: retain a flat basket and distribute with extra arm motion; add an active belt/auger; vibrate the basket; or use a passive adjustable slope with a replaceable liner.

- Decision: retain the Rev-E frame, wheel, arm and basket outer envelopes. Move each 150 mm side opening to X=220 mm and the nominal release point to `(250,+/-140)` mm. Raise the front end of the 400 mm basket floor by 56.2 mm using an 8 degree `ESTIMATE`; provide a 5-12 degree adjustable prototype range. Add a removable low-friction food-contact liner and a soft rear stop, with both materials `TBD`.

- Reason: gravity can move the object rearward after a short inward release without another arm sweep or powered conveyor. Adjustment lets the physical prototype find the lowest angle that feeds reliably without excessive impact speed.

- Impact: Rev-F supersedes the Rev-E flat basket. The front internal depth becomes approximately 123.8 mm before liner/clearance allowances. Irregular objects may slide, tumble, stop or bridge instead of rolling; feeding rate, damage, cleanliness, capacity, mass distribution and rear pile-up require physical validation. No throughput, food-contact or damage claim follows from the CAD geometry.



## DEC-029 - Use three 10-decare vehicle zones as the peak-day feasibility baseline



- Source: requester planning inputs on 2026-09-03.

- Problem: convert the user-estimated 13,000 figs/day across 30 decares into a fleet size, unloading schedule and battery requirement.

- Decision: use three identical vehicles, one nominal 10-decare zone per vehicle, for feasibility calculations. Use 0.04 kg/fig, a nominal 20 kg basket, the requester-specified 30 successful collections/minute/vehicle, six minutes per unloading event and a seven-hour work window as explicit editable assumptions.

- Arithmetic result: the fleet handles 520 kg/day. Each vehicle handles approximately 4,333 figs or 173.3 kg, requiring eight full 20 kg loads plus one approximately 13.3 kg final load, for nine unloading events. Collection plus assumed unloading takes approximately 3.31 hours/vehicle and leaves approximately 3.69 hours before the seven-hour boundary.

- Energy boundary: one 24 V 18 Ah pack does not cover the calculated job at 150–200 W average. With 80% usable energy and a 15% operational reserve, a 150 W measured average would require approximately 30.4 Ah nominal capacity or two 18 Ah pack equivalents; 200 W would require approximately 40.5 Ah or three pack equivalents.

- Impact: the three-vehicle plan remains conditional on a timed full-zone trial, measured unloading travel and logged 24 V bus energy. No battery, charger, BMS or fleet purchase is released by this decision. Local intermediate bins or replaceable baskets should be tested to avoid nine long returns per vehicle.



## DEC-030 - Size mobile energy from route distance and subsystem duty



- Source: requester clarification on 2026-09-03 that each vehicle covers one 10-decare garden and traction motors consume energy only while the vehicle moves.

- Decision: supersede use of whole-job average-power scenarios as the primary battery-sizing method. Calculate traction from route distance, speed and measured moving power; calculate arm energy only during collection; calculate compute, camera, control and standby energy over their actual powered durations.

- Current estimate: represent 10 decares as a 100 x 100 m equivalent square, use 8 m row spacing, 10% turn/avoidance distance and nine additional 100 m unloading returns. This produces 2.33 km and 1.62 motor-on hours at 0.4 m/s. Use 45 Wh/km traction, equivalent to 64.8 W while moving, plus 40 W dual arms, 12 W Pi/camera and 5 W control. The subtotal is 257 Wh and the 20% planning value is 309 Wh.

- Impact: the tree-row case remains slightly above the protected usable energy of one 18 Ah pack, so a single 24 V 30 Ah pack is the current practical candidate. Effective path spacing gives approximately 557 Wh at 2 m and 932 Wh at 1 m; these correspond to 24 V 40 Ah and 24 V 60 Ah candidate classes respectively. At 0.4 m/s, the 1 m full-area scan also requires at least 8.54 hours including unloading and therefore exceeds the seven-hour window. GPS route distance and logged 24 V Wh are required before battery selection; no purchase is authorized.



## DEC-031 - Rev-G uses a lightweight three-axis servo arm for the first collection proof



The RDS3235 actuator selection in this decision is superseded by DEC-033. The reach, passive wrist, side mounting and counterbalance architecture remain active.



- Source: requester instruction on 2026-09-03 to finalize the 3D arm before purchasing test hardware.

- Problem: the 605 mm NEMA/planetary custom arm is too heavy and expensive for the immediate performance proof, while MG996R-class servos at the shoulder leave insufficient torque and thermal margin for a 605 mm articulated arm.

- Decision: retain the 300 + 220 + 85 mm reach geometry but replace powered J4 with a passive parallelogram. Use one RDS3235 packaging candidate at J1, J2 and J3, an MG90S-class gripper actuator, 20 x 20 x 1.5 mm light-alloy tube candidates, supported joint carriers and an adjustable J2 counterbalance. Move the two 110 mm arm adapters to `(120,+250,111)` and `(120,-250,111)` mm. The sloped front basket envelope and side openings remain unchanged.

- Reason: the published RDS3235 envelope is 40.5 x 20 x 40 mm with 25T spline, approximately 60 g mass, up to 35 kg.cm stall torque and 0.11 s/60 degree no-load speed at the high-voltage condition. Removing the wrist motor and reducing link section lower distal mass; the counterbalance reduces continuous shoulder load. The narrower, slightly inward/forward mounts retain at least 20 mm calculated static packaging clearance and improve reach.

- Impact: the integrated rover uses the task-specific Rev-G arm instead of duplicated RoArm-M3 geometry. Published body/spline dimensions are controlled, but servo tabs, supplied brackets, horn stack-up, actual torque-speed curve, feedback accuracy, backlash, temperature and life remain `UNVERIFIED / PHYSICAL VALIDATION REQUIRED`. No purchase or production release follows from the CAD.



## DEC-032 - Use 30 successful collections/minute as the first two-arm vehicle proof target



- Source: requester planning instruction on 2026-09-03.

- Decision: the first mobile proof shall target 30 successful deposits/minute per vehicle. With two arms and ideal load sharing this is 15/minute/arm, or 4.0 seconds average for detection handoff, approach, grip, lift, adjacent-basket deposit and return. Keep 50-100/minute as a later stretch study rather than the first acceptance gate.

- Boundary: catalogue no-load servo speed does not establish a complete cycle. Measure full cycles with randomized ground locations, misses/retries and both arms active. A direct reach from the side base toward the vehicle centreline crosses the front basket footprint. Therefore arm commands are initially limited to X=420..600 mm and Y=180..320 mm left / -320..-180 mm right, Z=0..80 mm; the vehicle repositions wider camera detections into one of these lanes before a pick. The sampled lane is analytic-IK reachable, but full dynamic collision validation remains open.



## DEC-033 - Rev-G F/P prototype returns to MG996R with a dual-servo shoulder



- Source: requester correction on 2026-09-03 that the previously selected price/performance actuator was the lower-cost MG996R rather than RDS3235.

- Problem: one MG996R provides a published 11 kg.cm stall torque at 6 V, approximately 1.08 N.m. The current lightweight-arm mass estimate produces roughly 2 N.m static shoulder gravity torque in the horizontal pose before acceleration, friction and shock, so one unit at J2 is insufficient.

- Decision: supersede only the RDS3235 selection in DEC-031. Each arm uses one MG996R at J1, two mirrored and mechanically coupled MG996R units at J2, one MG996R at J3, one MG90S-class gripper servo, a passive wrist parallelogram and an adjustable shoulder counterbalance. The 300 + 220 + 85 mm reach, 20 x 20 x 1.5 mm lightweight links, arm base positions, basket and commanded side lanes remain unchanged.

- Reason: eight MG996R units for two arms have a current working retail subtotal of 2,026.24 TRY, substantially below the prior six-RDS3235 subtotal. The second J2 servo and counterbalance address the largest gravity load while the MG90S keeps distal mass low.

- Impact: dual hobby servos do not automatically share torque. Horn zero, linkage compliance, current balance and heating must be measured. Manufacturer no-load speed and stall torque do not establish the 4.0-second complete cycle or useful life. Final print holes wait for delivered-sample measurement; this remains a low-cost test architecture, not a production-strength release.



## DEC-034 - Release a coupon-gated printable V1 around nominal servo bodies



- Source: requester instruction on 2026-09-04 to accept standard motor dimensions, complete the 3D design and begin test printing without waiting for final sample metrology.

- Decision: use the TowerPro nominal MG996R body envelope `40.7 x 19.7 x 42.9 mm` and MG90S body envelope `22.8 x 12.2 x 28.5 mm`, with `0.8 mm` total body clearance and a `20.5 mm` socket for nominal 20 mm tube. Servo flanges are held by replaceable clamp bars; clone-specific tab holes are not required. Supplied horns attach through a radial-slot adapter whose fit remains unverified. Primary 300 mm and 220 mm moving links remain 20 x 20 x 1.5 mm light-alloy tube under REQ-MECH-003/004.

- Print gate: release six small fit coupons first for MG996R, MG90S, supplied horn and actual tube. Full brackets may be sliced only after those checks pass or the parametric clearances are corrected.

- Impact: printing can start immediately while avoiding a full-set reprint if delivered clone dimensions differ. The printed annular J1 slide, dual-servo J2 coupling, J3 printed bushing, horn attachment, gripper linkage, stiffness and fatigue remain `PHYSICAL VALIDATION REQUIRED`; this is not a production-strength or safety release.



## DEC-035 - Aero V2 keeps the metal load path and adds a legible curved gripper



- Source: requester design review on 2026-09-04 that Printable V1 appeared as unclear rectangular plates and did not visually read as a gripper.

- Decision: retain the controlled 300 + 220 + 85 mm reach, nominal servo openings, dual-MG996R shoulder and 20 x 20 x 1.5 mm light-alloy primary links. Replace the presentation and printable interface geometry with rounded bases, open mass-relieved carriers, curved mirrored scoop jaws and explicit horn/link motion references. Add optional modular hollow fairings with a nominal 0.8 mm wall around the aluminium tubes. Servo bodies, shafts, horns, tubes and soft pads in the colored STEP/GLB are reference geometry and are excluded from printable STL archives.

- Reason: keeping aluminium in the load path avoids making an unverified long printed shell structural. Short fairing modules fit a common printer bed and may be omitted for the lowest-moving-mass timing trial. The curved jaw silhouette and color-separated motors make the mechanism understandable before hardware arrives.

- Impact: the digital fairings add an estimated 78.5 g if all are installed. Required moving printed interfaces, including the MG90S retaining saddle, are estimated at 379.2 g before tubes, actuators and hardware. These estimates are CAD volume times 1.27 g/cm3 and exclude slicer variation and fasteners. Jaw closure, contact pressure, damage, food contact, print orientation, servo synchronization, stiffness, thermal behavior and cycle time remain `PHYSICAL VALIDATION REQUIRED`.

- Assembly correction: the initial Aero V2 presentation incorrectly left the MG90S axis vertical, displaced both jaw pivots by 3 mm and placed its horn away from the shaft. The corrected assembly places the MG90S axis parallel to the jaw pins, adds a two-screw printed retaining saddle, aligns jaw/palm pivots, places the horn on the shaft and generates both drive links from shared endpoint coordinates. The wrist-to-palm pivot pin is now explicit.

- Print-readiness audit: only FIT-001 through FIT-007 are released immediately. The audit corrected the printed gripper link to the assembly's 30.017 mm pin-centre distance and corrected the displayed M3/M4 pin diameters. The full structural set remains `NOT RELEASED` until delivered servo/horn/tube fit results, passive wrist-link anchors, counterbalance anchors and the fastener/spacer stack are resolved. The earlier all-STL filename was removed to prevent accidental full printing.



## DEC-036 - Release a fixed-wrist Aero V2 bench prototype on nominal clone dimensions



- Source: requester instruction on 2026-09-04 to accept clone motors as dimensionally standard and proceed to printing.

- Decision: accept the controlled nominal MG996R/MG90S envelopes for this prototype without incoming metrology. Replace the incomplete one-pin/passive-wrist presentation with a two-M4-pin fixed-angle wrist for the first constrained bench test. Add three pedestal counterbalance adjustment holes and a slide-on upper-tube anchor for an elastic cord or extension spring. Release the full STL set while retaining the seven fit coupons as recommended checks.

- Reason: a fixed wrist is lighter, simpler and immediately printable for a narrow planar pickup/release proof. It removes the unresolved parallelogram parts while still allowing the arm trajectory to keep the gripper usable by constraining forearm angle. The adjustable elastic anchor reduces static shoulder demand without requiring a finalized spring before printing.

- Impact: this release does not establish clone fit, unrestricted workspace, spring force, strength, safety, heating, life or four-second cycle performance. Field operation may require a self-leveling wrist after the bench proof. Exact fastener lengths and spacer stack remain assembly selections; physical validation is mandatory.





## DEC-037 - Rev-H above-wheel arm and rearward 30-degree basket placement study



- Source: requester 2026-09-05: reach forward over the wheel, collect and release/throw into the adjacent basket; camera on front lower raised region, battery and brain below basket.

- Decision: create a separate reviewed candidate, preserving the previously authorized Aero V2 printable parts and 300/220/85 mm controlled lengths. Frame 650 x 600 mm, track 830 mm and wheel diameter 254 mm are retained. Candidate arm base (380,415,280) mm is 26 mm above the nominal tire top. One arm is instantiated; opposite support only reserves future installation.

- Candidate basket floor is 600 x 660 mm in horizontal projection, X=-280..320 mm. Rear floor 140 mm, front floor 486.41 mm, 30 degrees front-high/rear-low. Front apron extends 95 mm with 18 mm rise. This avoids the first trial's unnecessarily high 628 mm entry. Width, lengths, support geometry and angle are provisional, NOT manufacturing dimensions.

- Low equipment envelopes: battery (90,110,166) mm, computer (-50,-100,146) mm, power (200,-100,138.5) mm; camera envelope (330,0,400) mm. Envelope dimensions are planning reservations and not new purchases or a BOM change.

- Existing fixed-wrist geometry is propagated rigidly during IK; it is not silently kept vertical as the forearm rotates. The first release branch collided with the basket. The retained branch gives clear checked poses and sampled obstacle checks, but requires a tilted ground approach and substantial shoulder movement. Throwing remains an experiment, not the validated transfer method.

- Scope: key-pose/18-sample obstacle review, exports and fixed inspection-only URDF. No continuous collision, joint-range mapping, self-collision, full steering, jaw-actuation, camera-FOV, loaded torque, durability or throwing guarantee. Rev-G is preserved separately. Bench print permission remains DEC-036; Rev-H vehicle support and basket geometry are not released for manufacture.





## DEC-038 - Two front-wheel arms, connected running gear, and 15-degree basket



- Source: requester 2026-09-05 asks to populate both front mounts, attach wheels/motors correctly, halve basket slope and bring the entry down near the arm origin.

- Supersedes DEC-037's single-arm instance and 30-degree candidate. Two identical (not chirality-mirrored printable) arms use yaw sign reversal at bases (380,+/-415,280) mm. Printed arm dimensions remain unchanged.

- Basket floor angle becomes 15 degrees, rear 145 mm, front 305.77 mm over 600 mm horizontal length. Rear increases 5 mm solely for reducer clearance, while front drops 180.64 mm. Example pad release is lowered from 610 to 440 mm. Camera moves to Z=240 mm. Trial food transport and early release are still unverified.

- Battery/computer envelopes shrink/reposition as listed in MASTER_SPEC to fit under the lowered floor. These are proposed space reservations, not measured purchased part dimensions or a BOM update.

- Running gear retains rear drive / front steering architecture. Two 50 mm gearbox and 50 mm diameter DC motor envelopes feed collinear couplings and 20 mm keyed shafts, each on two bearing housings. Front freely rotating hubs carry two bearings each on steering knuckles. Upper kingpin bridge, steering arms, tie rod, actuator, visible axle nuts/washers, wheel bolts, bearing brackets and support gussets complete the geometric load path. All component selections, fits, keys, fastener strengths, gear ratios, braking, actuator stroke and structural sizing remain UNVERIFIED.

- Replace tire-intersecting front uprights with supports at X=100,Y=+/-365 mm and upper cantilevers. Rear motor pockets are cut into the deck, shaped motor cradles sit against the side structure, and rim beads connect to tire seats. Nominal contact and zero-intersection tests are geometry checks only.

- Rebuild both-arm pose assemblies, GLB/STEP, renders, fixed inspection URDF and review archive. Preserve the separate Aero V2 bench print set; no vehicle manufacturing release or purchases are authorized by this change.





## DEC-039 - Correct full-arm print readiness after an internal assembly audit



- Source: requester 2026-09-05 final print check with supplied MG996R horn photos and a newly ordered ELEGOO Centauri Carbon 2 Combo.

- Keep user-authorized nominal clone body dimensions; no new measurement or permission gate. No critical dimensions or geometry changed in this audit.

- Correct the earlier full-set readiness assessment: HOLD full Aero V2 arm and gripper print because the J1 shaft-to-deck gap is 46.45 mm, jaws interfere with the palm, J2/J3 horn interfaces are incorrectly oriented/embedded, and hollow tube ends interfere with root hubs. These are CAD defects, not deferred physical validation.

- Retain FIT-001..007 for isolated dimensional trials. Preserve legacy full-set archive filenames for traceability but replace their readiness notices; previously downloaded copies are superseded. Historical release snapshots are not current print recommendations.

- Clarify 300/220 mm as joint spans; final metal saw-cut lengths require resolved socket insertion. No cost, purchased quantity or inventory changes.

- Record reproducible audit evidence and distinguish 19 passing legacy tests from assembly readiness. Rebuild current exports/renders/inspection URDF and refresh archives after metadata correction. Full linkage closure, hardware stacks, slicing and physical performance remain unresolved.



## DEC-040 - FreeCAD parameter bridge without changing the controlled baseline



- Source: requester accepts FreeCAD for dimension-editable CAD on 2026-09-05.

- Create separate arm and full Rev-H2 vehicle FCStd documents with a FeaturePython controller and individual Part::Feature solids. This is genuine generator-driven dimensional editing, not a reconstruction of independent Sketch/Pad/Pocket histories.

- Expose upper/forearm joint spans, basket slope/rear height and the two arm base coordinates. Defaults remain 300/220 mm, 15 degrees, 145 mm and (380,+/-415,280) mm. No controlled critical dimension or purchased BOM is changed.

- Variants remain in cad/freecad/variants, with rebuilt assemblies, STEP, GLB, STL, preview and fixed inspection URDF. Preserve the current viewer and controlled release outputs. User experimental dimensions do not revise MASTER_SPEC automatically.

- Retain the baseline pickup joint angles while editing arm dimensions. Adapt sleeve lengths/positions with link spans; do not claim updated grasp targets, support design, tube saw-cut lengths, collision clearance or strength. Modelling input bounds are not engineering-approved limits.

- Native regeneration requires the local CadQuery environment and project source, loaded by a narrowly scoped FreeCAD user module. A lone FCStd contains saved solids but not a portable standalone parametric implementation.

- Keep DEC-039 HOLD in all new documents and manifests. Test baseline geometry equivalence and real regeneration after native save/reopen.



## DEC-041 - AERO V3 printable bench redesign with active downward wrist



- Source: user requests correction of the arm for 3D printing, downward-facing ground gripper and a light wrist motor if needed (work spans 2026-09-05/06).

- Create separate AERO V3, retaining 300/220 mm joint spans and nominal MG996R/MG90S bodies. Shoulder axis changes from 146 to 124 mm above arm base. Vehicle bases remain (380,+/-415,280) mm; basket remains 15 degrees. Current vehicle mounting plates get the matching 100x86 mm hole pattern. V2 print releases remain held and are not relabelled as fixed.

- Use four MG996R (J1, dual J2, J3) and two existing MG90S (W1 wrist and G1 jaw) per arm. No purchase and no purchased ledger change. Separate V3 mechanical hardware/cost extract records unknown costs as TBD.

- Replace incorrect yaw mount/drive stack, perpendicular horn mistakes and tube ends. Offset upper/fore tubes -18/+18 mm from the common joint plane. Nominal tube cut lengths become 235 and 161 mm with through-bolt hole patterns in the V3 manual.

- Replace the former unclosed dual-link gripper with one fixed and one directly driven jaw. Add a removable wrist drive plate for assembly access and opposite idler support at wrist and elbow. Printed idler sleeve OD6/ID4.3/length6, bracket bore6.4, two 0.8 mm thrust washers leave 0.4 mm axial clearance. These are nominal FDM trial dimensions, not bearing-life specifications.

- Tool pitch is kept vertically down through W1 = -(shoulder + relative elbow), not passive gravity levelling. Display and review only; no physical motion or firmware command authorized by the CAD build. Servo zero/sense/range, paired-shoulder load sharing and cable routing require commissioning.

- Check all modeled solid pairs with no collision exclusions across 22 arm-path samples, 11 jaw angles and 3 dual-arm poses. Rebuild per-part STL/STEP, assembly STEP/GLB, renders, kinematic review URDF and FreeCAD variants. Finite sampling does not certify continuous clearance, real-world safety or manufacturing tolerances.

- Full CAD-volume gravity estimate gives roughly 13 kgf.cm shoulder demand with 100 g payload, before unmodelled fasteners/cables, friction and acceleration. Do not claim high-speed 100 g performance or adequate thermal duty. First physical trials unloaded, then 40 g; larger load/speed only after measured checks, with counterbalance or shoulder redesign if needed.

- Release scope: nominal digital bench trial files after successful audited geometry and mesh checks; first print fit coupons. No sliced machine G-code or production/strength approval. Supplied horn pitch, centre screws and final hardware fit remain physical checks.

# DEC-042 — Separate short cardboard bench experiment (2026-09-07)



The user requests household cardboard trials while waiting for the printer. Provide a reversible CARD-01 guide using one stationary MG996R and one MG90S gripper, approximately120mm maximum motor-axis-to-object lever. This is a separate experimental fixture; AERO V3 dimensions, print files, vehicle placement, purchased inventory and firmware remain unchanged. Use folded closed-section cardboard and reinforced supplied-horn attachment, not a full300/220mm cardboard arm or glued cardboard spline. Material strength and actual motion are unverified. The fixture can support module/state-sequence experiments; it cannot validate full-arm XYZ calibration, vertical-wrist control, load rating or throughput. See ASM-064 and `output/pdf/KARTON_KOL_KISA_DENEME.pdf`.



## DEC-047 — Reject unkeyed capsule as functional connection (2026-09-07)



User correctly identifies missing torque transfer. Suspend SNAP01 A/B/C print recommendations. B opens the lid hub path; C splits the lid into two opposite covers, but neither corrects the circular torque interface. Experimental C retains 40x38x9mm envelope, 1.8mm lids and 14mm central opening; these are proposed test dimensions, not measured hardware. B/C exports, renders and fixed review URDF remain isolated historical studies. The replacement must capture the original star/cross horn contour with load-bearing side walls, keep the shaft centre screw and allow opposed retaining covers clear of the hub. No full-arm or BOM change. 8BitRobots Wheel.stl is a verified cross-pocket mechanism example for FT90R only; do not copy its dimensions as MG996R dimensions.



## DEC-051 — MG90 SNAP03B asymmetric horn pocket fit trial (2026-09-08)



User reports one horn side does not fit. User Arm03 STL and MG90_Arm STEP show asymmetric long arms, +18.025/-15.675mm after X-60,-Z,Y canonical transform; old profile ±17.5mm. User follow-up explicitly requests shortening the excessive opposite side too: use ONLY new Arm03 exterior contour (not union with old), keep radial clearance0.20 and mouth0.40. Tip changes +0.525mm at long side and -1.825mm at short side relative to old17.5mm reaches; no arbitrary hole-pitch extension. Floor1.4, cover geometry and body/tongue/shaft centre unchanged. Preserve old SNAP03 and active V4 unchanged until physical fit. Rebuild isolated STEP/GLB assembly, fixed URDF, prints/render/audit/tests. Original horn thickness mismatch3.8vs4.85mm means actual axial retention is unverified. No BOM/purchase/printer action.



## DEC-052 — Integrated breakaway manufacturing scaffolds (2026-09-08)



User reports large prints failed and explicitly requests built-in removable supports, excluding successful direct motor couplers and pins/screws. Add separate manufacturing meshes in `aero_v4_supported`; do not alter functional AERO V4 CAD dimensions, SNAP02/03/03B, beam geometry or inventory. Ten complex parts on five replacement plates; a separate small support-removal coupon comes first. Manufacturing ribs: pitch2.4mm, wall0.8mm, contact neck0.42mm wide and0.6mm high,0.3mm lateral clearance,0mm deliberate vertical interface gap; shallow orthogonal0.6mm interface ribs support roof paths in either direction. Peelable strip segments at8.4mm pitch/8mm length. Contact seams are intentionally weak but actual breakaway force unknown. Small circular-hole crowns up to4.5mm in width and height remain geometric bridge exceptions, not guaranteed printable spans. No change to mating cavities; supports go into empty manufacturing space and are removed before assembly. STL/3MF keep each part and scaffolds in one object. Source mesh intersection audited; regenerate manufacturing assembly/render/fixed URDF and functional-reference exports. Offline PrusaSlicer2.8.1 QA is not the user's Elegoo machine profile and does not authorize printing QA G-code. Do not describe digital supports as physically validated or bulk-print-ready before coupon and actual sliced preview. Old unsupported complex print files should not be reused.



DEC052 implementation detail: final STL union is reopened and checked for manifold topology. Finite sacrificial ties with0.15mm added bounding thickness replace any edge-only scaffold contacts that would become non-manifold on STL welding; their volume/contact is reported separately. The shoulder-deck lower ledge gets one additional manufacturing rib row atY14mm in print coordinates, identified by the independent roof-layer audit. Neither operation removes functional material.



## DEC-053 — Solid unbarbed replacement pin trial (2026-09-09)



User reports thin slotted pins break; thick pins survive. Create isolated P1/P2/P3/P4/P6 solid substitutes,48 total, preserve grip lengths7.4/6.5/9.6/26.2/12.2mm, head diameter6.05mm/head height1.6mm, total length grip+2.8mm. Preserve requested3.05mm shank in full set; remove0.8mm split AND rigid3.7mm barb, use a monotonic1.2mm tapered lead-in (tip diameter2.55). Keeping rigid barb would prevent insertion. P5 6mm axle remains untouched/excluded. Nominal holes3.3/3.4mm imply clearance at3.05mm, so friction retention is not claimed. Add isolated P3-length diameter coupons3.05/3.15/3.25/3.35/3.45, unchanged heads, solely to select physical fit; no silent main-arm diameter change. Separate CAD/meshes/layouts/render/fixed URDF/estimate/tests; full assembly and legacy pin files remain historical unchanged pending fit. Original servo centre screws still required. No purchase or printer action.



## DEC-054 — Withdraw custom support designs at user request (2026-09-09)



User reports custom supports failed and explicitly requests original geometry. Withdraw DEC052 integrated support print recommendations and packages. Keep generated files only as historical failed trials; do not delete user artifacts. Original AERO V4 functional geometry and viewer were never modified by manufacturing supports and remain the selected part geometry. This is NOT permission to print complex overhangs without slicer-generated supports. Do not design further custom scaffolds unless requested again. DEC053 solid-pin work remains authorized and isolated.





## DEC-055 — Shared mirrored shoulder control (2026-09-09)


User confirms two opposing shoulder servos and requests one control. Firmware V2 reserves pairs1+2 and7+8, rejects independent P commands for either member, and uses a single logical trajectory with nominal complementary pulses summing3000us (A=theta/B=180-theta,1000..2000us). Both adjacent outputs are written in one I2C transaction with MODE2 OCH=0; no physical simultaneity/load-sharing claim. Arm/disarm/watchdog affect both. Paired speed10..60command degrees/s, first command after arming must be90degrees; first physical motion remains unknown. UI replaces two shoulder bars with one per arm, exposes common reversal, disables wide range, and requires user acknowledgement of detached horns or checked physical centre/direction. No individual offset/gain calibration is invented. User confirmed servo power disconnected before firmware update. CAD/BOM unchanged. See ASM-080.

## DEC-056 — All-printed captive bearing trial PB01 (2026-09-09)

User rejects ready bearing cost and explicitly requests printed plastic balls and races. Implement a separate HAND-OPERATED bearing trial before altering the assembled arm. Small coupon: ball pitch diameter40mm,6 balls, outside80.4mm, through-bore20mm. Large candidate: pitch90mm,24 balls,outside130.4mm,bore70mm. Both use full8mm spheres,4.2mm circular race radius,1.6mm separate ball cage,0.5mm nominal radial guide clearance,0.4mm rotor/retainer axial gap and three broad30-degree bayonet locks with three unsplit3mm anti-rotation pins. Ball-retaining cage outer rim is at least1.2mm. These are PROPOSED EXPERIMENTAL dimensions, not measured print tolerances or rated bearing specifications. Opposite axial load is caught by a plain retainer lip, not by a second ball row; tilted friction/creep remain unverified.

No printed spline replacement, integrated scaffold, bought hardware, firmware change, motor command or printer job. Keep current AERO base/deck/horns/kinematic dimensions and viewer unchanged. Large PB01 is NOT a drop-in retrofit: adapter, stanchion load path, servo axial clearance and arm integration remain TBD after the small bearing rolls successfully. Rebuild isolated bearing assemblies, STEP/STL/GLB, geometry-only print plates, CAD renders, fixed review URDF and experimental material estimate; validate geometry, cap insertion/locking path, captive uplift interference, free rotation and quantity/mesh consistency. CAD clearance does not establish acceptable friction, wear, retention or load capacity.

2026-09-09 user selection update: user explicitly skips the80.4mm small coupon and chooses the130.4mm large candidate for first printing. Supersedes the small-print prerequisite, not physical validation or the missing arm-adapter gate. Keep geometry/dimensions unchanged; check all three large print plates by offline slicing, publish a large-only pack and guide, and keep small files as optional history. First assembled use is still by hand without the arm/payload. Do not describe the standalone bearing as the finished original arm base.

## DEC-057 — PB02 integrated motor pedestal and keyed closed shoulder plate (2026-09-09)

User correctly identifies that PB01 lacks a motor interface. Withdraw PB01 as an arm-base print recommendation; retain history. PB02 release_01 replaces A4 base, shoulder deck, yaw washer and J1 standalone SNAP02 body/tongue pins only. Original physical MG996R star, two proven opposed SNAP02 caps, centre screw, motor clamps and shoulder towers remain. The exact central46x44mm SNAP02 pocket is rigidly integrated into the closed rotor; demonstration tongue removed. An8mm through-hole permits original screw access, not a new printed spline. Preserve motor origin58mm, horn transform65mm, deck top78.5mm, shoulder axis124mm and300/220mm links. Preserve four original shoulder sockets.

Bearing pitch90mm/24x8mm printed balls, lower race offset53.5mm. Local upper groove centre changes8.0 to7.6mm; sphere/cage centre changes8.0 to7.8mm for nominal simultaneous axial tangency, avoiding0.4mm unloaded descent toward motor case. Inner pilot shortened to beginlocalZ7.5 instead6.5 for opposed-cap insertion; radial guide engagement2.5mm. Actual axial load sharing with the servo remains UNVERIFIED. Lower race is removable: four14mm feet,8.4mm square sockets over8mm pedestal pegs, four6.2mm solid pins through6.3mm bores. Pedestal116x110x6mm with wider diagonal webs; motor-clamp tip relief4mm throughZ38.2.

One-piece upper retainer cannot pass over the closed deck. Split atX=+/-0.15mm into two radially installed halves; extend left lug tracks for interference-free radial entry. Joining ears atY+/-67mm use two additional6.2mm solid pins. Three existing3mm vertical retainer pins remain. All retention, creep and friction require physical trials. No custom support scaffolds, no powered/printer commands, no purchases. Five geometry-only3MF plates, exact39-piece experimental print inventory, STEP/STL/GLB, full-arm assembly and review URDF regenerated. Offline generic slicing is not an Elegoo G-code approval. First test without shoulder towers/payload; retain and use the original servo centre screw.


## DEC-058 — Shoulder command speed10–180deg/s; staged battery transition (2026-09-09)



User requests180deg/s shoulder adjustment on existing prototype while new base prints. Raise paired S command limit in UNO firmware and Python parser/controller/UI from60 to180; choices10,30,60,90,120,150,180; default30 unchanged. Both opposing motors still share one complementary1500us-centred trajectory and one I2C STOP update. Keep centre-first gate, narrow1000..2000us shoulder range, watchdog, stop/disarm, follower command rejection. V3/STATUS3 rejects old60-limited V2 to prevent silent UI/firmware mismatch. Native fake-clock tests check both pairs complete a full command span in1s at180 while preserving complementary pulses and rejecting181. UNO compiled; physical upload/connection deferred until current servo-power-off confirmation. No live motion command, CAD or BOM change.



Battery transition is preparation only: existing12V battery must feed a verified XL4016 buck output initially5.0V, never raw12V to servos/V+/VCC/UNO5V. Remove powerbank output before changing source. Shared PCA9685 V+ rail cannot accept two paralleled XL4016 outputs; independent servo supply branches need isolated positive wiring, common reference ground and current-rated protection. Exact module terminals/fusing/current capacity require visual confirmation before wiring instructions. Do not infer a2-motor-per-buck topology through a common board rail.


## DEC-059 — Android two-screen control and confirmed HC-05 (2026-09-09)

User requests phone camera/brain, Arduino actuation and two screens before battery power. User explicitly identifies HC-05. Implement native launcher, existing camera observation workflow with truthful calibration gate, and separate manual motor screen over paired-device RFCOMM SPP UUID00001101-0000-1000-8000-00805F9B34FB. Android12+ CONNECT runtime permission, no discovery or new location permission. ARCore optional for installation so motor tests do not require camera capability. Same applicationId, versionCode7. Preserve V3 pair/centre/watchdog controls; queue bounded/coalesced,10Hz maximum motion sends,300ms heartbeat,1.2s host stale limit. Leaving motor screen disconnects and stops; no background robot motion/autorearm.

HC-05 firmware selects SoftwareSerial D10RX/D11TX at proposed9600baud, generated exact shared V3 core. Dedicated USB and HC-05 sketches are alternative single-owner transports, not simultaneous control sources. Core-equivalence and fake-Wire tests preserve behavior. No automatic XYZ actuator commands: servo zero/sign/range and picking path remain unmeasured. Neither firmware nor APK installed on user hardware this turn; no live motion, wiring, battery or purchase action. HC-05 carrier power and RX divider must be verified physically; UNO battery supply deferred until communications test.
# DEC-080 — J1 kablo çıkışı, LINKA L1.3 (2026-09-14)

Kullanıcı alt tabanın motor çukurunda kablo çıkıntısına karşılık gelen duvarın kapalı olduğunu bildirdi. Eski motor maketi kablo/boot içermiyordu; gövde açıklığı bunun yerine geçmez. L1-01 için bağımsız LINKA base() tanımlandı, arşiv FORMA geometrisi değiştirilmedi.

Her iki kısa uç destek duvarının ortasında12mm genişlikte, Z4..28 arası yuvarlak tavanlı kablo penceresi açılır; alttaki4mm taban, üstteki insert taşıyan köprü, kulak delikleri ve rulman yolu korunur. İki uç açılması kablonun hangi kısa uçta olduğunun henüz doğrulanmamasındandır. Açıklık boyutları tasarım adayıdır, ölçülmüş kablo boyutu değildir. Kullanıcıdan en/yükseklik/çıkıntı ve uç konumu istendi. Ölçü gelene kadar PHYSICAL VALIDATION REQUIRED; yeni taban baskı onayı sayılmaz. Kablo pencereden geçirilerek montaj yapılır; üstten düz düşürme yolu açıldığı iddia edilmez.

L1.2 motor tablası ve diğer parçalar korunur. Donanım/BOM boyutları değişmez. L1-01 eski dosya ve baskıların otomatik uyumlu olduğu söylenmez; arşivler korunur.
# DEC-080 ölçü eki — 2026-09-14

Kullanıcı kablo çıkıntısını en7mm × yükseklik3,9mm × gövdeden uzama5,5mm olarak bildirdi. Mevcut12mm kablo penceresi daraltılmaz; yalnız ölçü kaydı, koşullu açıklık testi ve paket notları güncellenir. CAD katıları ve bağlantı ölçüleri değişmez.7mm çıkıntı ortalandığında nominal yan pay2,5mm/yan olur. Alt kenarın yerleşikZ4,5..17,6 aralığında olması koşuluyla0,5mm çevresel/tip paylı ölçü zarfı her iki kısa uçta kontrol edilir. Gerçek çıkıntı konumu/fiş/bükülme yolu henüz ölçülmüş değildir; tüm montaj doğrulanmış sayılmaz.


## DEC-084 print-layout addendum / TABLA-01

User requested bed-sized files to print the current new arm. No critical CAD dimensions changed. Use recorded256x256mm bed and0.4mm nozzle; preserve source STL volumes and scale100%.07 has8 mechanism pieces;08 has3 scoops and6 linkage bushes. Keep old L1-25 bushes and two micro horn covers.04 excludes obsolete L1-16/17/19;05/04A archived with SHA256 verification. Full set01/02/03/04/06/07/08 has47 PLA instances. New parts have>=12mm bounding-box separation for5mm brims, minimum8mm bed edge reserve. Fingers rotate+90deg about localY (concave side up); links/rack+90X; guide+90Y; pinion/bush Z axis upright. Frame original local pose needs generated supports. Generic offline PrusaSlicer slicing is geometry evidence, not the actual printer profile or physical strength approval. Assemblies/renders/URDF retained byte-identically because CAD geometry is unchanged. No BOM procurement or motor command change.

## DEC-085 — Standart metal vida ve basılı çubuk burcu (2026-09-16)

Kullanıcı ISO7379-4-M3-6 bulamadı ve alternatifin hazırlanmasını istedi. Plastik vida kullanılmaz. Mevcut L1-14 krank ve L1-10 önkol yuvaları korunur. Yalnız L1-15 uzun çubuk ve yeni iki L1-26 burç basılır. Çubuk eksen aralığı185mm korunur; uç dış çap14, uç kalınlık5,6, pivot deliği6,3mm. Burç OD6/ID3,3/L6mm. Standart M3x10 metal vida ve iç3,2/dış7/kalınlık0,5mm M3 pul; mevcut M3x4 insert. Nominal3,5mm diş tutuşu,0,4mm toplam eksen ve0,3mm çap boşluğu. İki ISO7379 ve dört M4 pul listeden çıkar; iki M3x10 ve iki M3 pul eklenir. Yeni çubuk03'ten09'a taşınır; tam set49 baskı parçasıdır. Tutucu geometrisi korunur; bildirilen kırılganlığı bu karar çözmez. Baskı ve gerçek sıkma/sünme PHYSICAL VALIDATION REQUIRED.

## DEC-086 — İki kepçeli tutucu, 2026-09-16
Kullanıcı kırılgan üç parmaklı tutucunun iki kepçeye dönmesini istedi. Yeni TS tasarımı DEC-083 dişli geometrisini kaynak bağımlılığı olarak kullanır; eski çıktı tekrar yayımlanmaz. Tek mevcut MG90S, iki modül1,25/28 diş ve zıt24derece açılma adayı. Kepçe cidarı2,6mm, kökü10x6mm ve yerel kaburgalar; dört izole ince dikme yerine6mm kalın pencere boşluklu yan duvarlar. Mevcut bilek yıldızı datumunda montaj. Pasif eksen için eldeki M2x14 metal vida, OD6/ID2,4/L8 baskı burcu ve M2L4 insert. Başlangıç CAD boyutları fiziksel ölçü/kuvvet onayı değildir. Taban bağlantısı için kullanıcıdan sorunun oturma mı hizalama mı olduğu bekleniyor; ölçülmemiş yıldız yüksekliği değiştirilmez.

## DEC-086 ölçü ve yayın eki — 2026-09-17

TS-FRAME bilek yıldız datumunu korur; geniş tutucu şasisi32mm öne taşınır, motorun karşı yanında12mm kalın bir perdeyle bağlanır. İlk çift perde W1 servo gövdesine girdiği için kaldırıldı; G1 motor açıklığı yeniden kesildi. Bu yer değişimi uç momentini artırır. Nominal tool kütlesi önce72,33g, sonra100,18g; yerelX yatayken öz ağırlık bilek momenti0,0251→0,0524Nm. Bunlar CAD/atanmış parça kütleleri, tartım/kapasite onayı değildir. 50g meyve merkezi yaklaşık99mm'de0,0486Nm ilave eder; ivme/sürtünme/kablo dahil değil.

J1-CAPTURE-CUP: dış50, merkez12,6, taban4, çevre2mm (toplam6). Mevcut45,6mm yuva çevresine23,1mm iç yarıçapla0,3mm/yan boşluk. Yıldız merkezi ve rotor değişmez. J1'in iki kapak vidasıM2x6 yerineM2x8; mevcutM2L4 insert. Diğer üç büyük yıldız kapağı korunur. Yeni tam baskı34 örnek; 07 üç,08 iki,10 bir parça. Eski üç parmak ve üçL1-25 kaldırılır. M2L4 toplam23, M2L3 toplam6, M2x6 toplam24, M2x8 toplam4, M2x14 toplam1. Plastik burç TS-BUSH6/2,4/8. Kaynaklarda eski CAD modülleri yalnız bağımlılık olarak kalır; çıktılar SHA256 doğrulanarak arşivlenir.

## DEC-087 — SO-101 için mevcut alım uzlaştırması (2026-09-17)

Kullanıcının hazır kol tercihine göre yeni alım planı tek SO-101 follower içindir. 12 V C047 / 1:345 motorlar seçildi; 6 motor ve 1 Waveshare Bus Servo Adapter (A) gerekir. Leader, kamera ve yeni bilgisayar başlangıç alımına eklenmez. Bu tercih videodaki bütün otonomi/öğretme davranışının yalnız follower ile hazır olduğu anlamına gelmez. Resmî SO-101 geometrisi bu çalışmada değiştirilmez, önceki LINKA çıktıları yeni model gibi yayımlanmaz.

Arşiv V6 satın alma Excel'inin 66 satırı okunur; 8.774,90 TL tarihsel kayıt toplamı yeni bütçeden ayrılır. 7 MG996R, 2 MG90S, 2 PCA9685 kaydı korunur, yeni bus motorlarının yerine sayılmaz. Alet, güç kablosu ve sarflar yeniden kullanım adayıdır. Akü sağlığı ve besleme arızası kesinleşmediğinden yeni akü zorunlu alıma eklenmez. 5 A adaptör kartı sınırı ve 6 motorun akım toplamı nedeniyle eşzamanlı yüksek yük işletmesi onaylanmaz.

Plan ve maliyet kaynakları purchasing/so101_*.json; oluşturucu scripts/build_so101_shopping.py. Yalnız alışveriş yayını `python -m scripts.publish_current --so101-shopping` ile yapılır. Bilinmeyen fiyatlar null/TBD, ürün ara toplamı 148,93 USD, teslim toplamı bilinmiyor. Mevcut motor paketleri ve hırdavat miktarı doğrulanmadan ikinci kez vida/başlık/kablo alımı önerilmez. Satın alma yapılmadı; CAD/URDF/firmware değişmedi.


## DEC-088 — Official SO-101 follower print delivery and confirmed orders (2026-09-18)
User ordered six motors and purchased one 12 V 5 A desktop PSU for TRY 321.25. Motor SKU, supplier and paid total remain TBD; do not substitute quote prices. Paid/ordered quantities are removed from repeat-purchase quantities. Preserve the original 66 Excel records; additions remain separately sourced user records. Known spend TRY 9696.15 excludes unknown motor and existing cable cost.

Use unchanged upstream SO-ARM100 commit eecbe3e0a9ebb23e25ad7b2759b03884c6660903 official SO101 follower geometry. Eleven main parts plus two official gauges. No changes to critical dimensions, holes or servo mounts. Only rigid transforms; print rotations registered to official Prusa follower mesh, except board plate printed on its broad flat original bottom face. Preserve the moving-jaw internal negative-volume cavity. Standard original M2x6/M3x6 attachment to motor cases and horns; do not add heat inserts to holes that were not designed for them. Existing DIN912 M3 head clearance remains a physical check; retain the motor-supplied centre screws.

256 mm bed split into 00 gauges and three numbered main plates. Deliver generic 3MF/STL, individual reprint STLs, previews, original STEP assembly, original URDF and source SHA256 manifest through publish_current. No G-code or proven strength claim. Archive prior CAD/prints and obsolete LINKA shopping lists with SHA256 verification before removal. Historical source modules remain developer dependencies. Do not publish old LINKA by the default current-refresh command after migration.


## DEC-088 SAMM confirmation — 2026-09-18
User confirmed SAMM as motor supplier. Conversation catalog match: Waveshare 22414 / MP03422 ST3215 12 V 30 kg.cm; catalog dimensions 45.22 x 35 x 24.72 mm. Official Waveshare SO-ARM101 assembly lists six ST3215 for follower. Nominal original 01-03 print geometry therefore retained, printing before arrival is reasonable; 00 physical gauge is optional, not a blocker. No hole or critical dimension changed. Physical tolerances, received SKU/package contents, paid total and screw head clearance remain UNVERIFIED. SAMM lists one horn while manufacturer assembly uses front/rear horns; verify the 11 required horns without automatically ordering more. Use the motor-pack pointed case screws rather than assuming existing M2 machine screws are equivalent. See manufacturing/so101_samm_check.md.


## DEC-089 — Native CC2 slicing profiles (2026-09-18)
Retain all DEC-088 SO101 CAD/STL geometry and official print rotations. Replace generic delivery TABLA.3mf with native ElegooSlicer projects at the same stable paths; add G-code for CC2 Combo / physical 0.4 mm nozzle / Textured PEI A only. User filament PLA+, label 210–235 C, successful temperature 225 C. Use 225/60 C, 0.20 mm layers, 4 walls, 25% gyroid, 5 top/bottom layers, moderate speeds and 10 mm3/s volumetric cap. Separate everyday preset: 3 walls, 20% gyroid, supports off. Brand, flow and pressure advance are not calibrated.
Actual ElegooSlicer 1.5.3.5 CLI slices and native GUI previews reviewed. Normal automatic Snug support selected over tree: tree reported critical lost branches on base; normal slices without CLI errors, reduces total main-plate material by about 27 g and time by 3 h 24 min. 45-degree threshold, 0.20 mm Z / 0.35 mm XY gaps, 3 top interface layers, 5 mm outside brim. Removable supports inside some openings require cleaning.
OEM CC2 machine macros retained. Publish via scripts.publish_current --so101-slicer after SHA256 archive. A future package refresh preserves slicing artifacts only if plate STL hashes match; changed geometry requires re-slicing. No physical print started and no strength/fit guarantee implied.

## Android kamera-kol eşleme iyileştirmesi — 2026-09-28
V29 mesafe göstergesini eşleme hatasından açıkça ayırır. Park başlangıcından
kamera/base ve marker/tool pozları yalnız8 öğrenme pozu üzerinde birlikte
least squares ile iyileştirilir;4 bağımsız kontrol pozu tutulur. 100mm/rad
rotasyon artık ölçeği algoritmik koşullandırmadır; URDF/motor sıfırı değiştirilmez.
Etiket IPPE başlangıç çözümleri OpenCV solvePnPRefineLM ile köşe reprojeksiyon
hatasını azaltacak biçimde iyileştirilir. Kalite ve fiziksel kabul kapıları korunur.
Kaynak: https://docs.opencv.org/4.12.0/d5/d1f/calib3d_solvePnP.html
Başarılı kalibrasyon atomik dosyada tutulur; yeniden açılışta taze etiket ve
encoder kontrolü olmadan hareket yetkisi sağlamaz. CAD/BOM/ölçü değişikliği yok.
Son fiziksel deneme max13,3mm nedeniyle başarısız; ilk otomatik kaldırma yok.

## 2026-09-28 kilitli hedef çevrimi ve kadraj sınırı
Kullanıcı, seçilmiş hedef görünmese de alma-sepet hareketinin tamamlanmasını ve
başarısız konumların tekrar denenmemesini istedi. PickupCycle yaklaşma/kapatma/
kaldırma/taşıma/açmayı hareket öncesi doğrular. Başlatılacak hedef atomik dosyada
saklanır;35mm XY eşleme çevresi yalnız açık yeni-tur sıfırlamasıyla temizlenir.
Çevrim boyunca yeni algılama başka hedefe yönlendiremez; sonlu yol encoder ile
izlenir. Fig/etiket örtülmesi yeni koordinat üretmez; kamera/IMU referans kaybı,
motor hatası ve DUR hâlâ durdurur. Kavrama başarısı hareket bitişinden çıkarılmaz.

Yaklaşmada yatay IK yetmezse aşağı eğimli açılar mevcut eklem ve masa sınırları
ile denenir. IK ve kalibrasyon rota araması motor worker dışında çalışır;
sonuç geldiğinde duruş/kamera/kalibrasyon/iptal kimliği yeniden doğrulanır.
PC köprüsü watchdog süresi gevşetilmedi. Bilinen etiket bağlantısında tarama
köşeleri ve yol CPU kamera kadrajında öngörülür; bu örtülme/çarpışma garantisi değil.
05:02 canlı kalibrasyon RMS4,0/max7,0mm ile geçti; ilk otomatik kavrama henüz yok.
CAD, ölçüler, motor sıfırları ve eklem sınırları değiştirilmedi.

ARCore dünya takibi PAUSED olduğunda eski onDrawFrame erken dönüşü canlı
CPU görüntüsü üzerindeki etiket/incir analizini de kesiyordu. Kamera görüntüsü
ve taze kare/IMU kontrolü bağımsız tutuldu; yalnız AR dünya derinliği/hitTest
TRACKING gerektirir. STOPPED ve eski kareler hareket yetkisi sağlamaz.
Kaynak: https://developers.google.com/ar/reference/java/com/google/ar/core/Frame
(acquireCameraImage ile acquireDepthImage16Bits farklı koşullara sahiptir).

## 2026-09-28 — Measured jaw contact and CPU camera timing

Pickup now plans a horizontal 10–15 mm open-jaw seating leg at unchanged model
height before closing. Jaw closing runs at 180 counts/s; the fallback endpoint
is 24 counts below the previous closed setting, inside the unchanged envelope.
A raw-current rise plus stalled position (>=12 counts behind command, speed<=5,
current>=max(8, idle+6), stable within 3 counts for >=180 ms with <=100ms gaps)
indicates possible contact, not identified fruit or calibrated force. Stop at
that measured position with one 6-count preload, retained during lift/carry.
Motor temperature/current/voltage and tracking fault limits remain active.
Explicit DUR acknowledgement can recover only a healthy stationary FAULT_HOLD,
without writes; the first fault reason is retained in motor_errors.log.

Live Xiaomi logs showed valid CPU images consistently leading AR frame time by
34–36ms; the old negative-delay check discarded both marker and fig inference.
Permit source-clock skew of either sign within 100 ms, conservatively subtract its
absolute magnitude from host receipt time; repeated/nonmonotonic images and
larger skews still reject. ARCore frame timestamp time base is unspecified:
https://developers.google.com/ar/reference/java/com/google/ar/core/Frame
After this change 2500/2500 marker frames were detected, with 3 figs reported.

Calibration search includes shifted shoulder centers without changing joint
limits, pose diversity or clearance checks. The predictive minimum tag edge may
use 80% of an already fresh unambiguous observed edge, clamped28..32 CPU pixels (matching the detector minimum);
actual detector quality and calibration residual gates remain unchanged.
This avoids rejecting all possible paths solely because a reliably observed
foreshortened tag has a side smaller than the previous fixed 32-pixel heuristic.

Fallback calibration planning now selects 12 distinct poses from bounded joint
offsets when no complete fixed pattern remains visible. Every connecting leg
still checks the same table clearance, passive roll, envelope and tag visibility.
Yaw changes are interleaved with pitch changes; acceptance still requires held-out
residuals and existing pose diversity checks. Live 20:47 camera parameters and
saved mount reproduced the fixed-pattern failure offline; the subset generated
12 valid candidate poses. Candidate generation is not a physical fit result.

During a bounded automatic calibration leg, temporary tag ambiguity no longer
stops midway. Fresh CPU camera frames, fixed-phone IMU and all motor guards are
still required. Calibration samples still require stationary encoders plus a
fresh unambiguous stable tag; the15-second sample timeout remains. Live20:52
run stopped before its first destination due to short marker ambiguity, then
could not recover a clear stationary measurement. No pickup claim from this run.

## 2026-09-28 — Grasp clearance and camera controls

Live pickup reached the open-jaw seating endpoint, then refused closing because
measured FK tip height fell below8mm despite a nominal10mm target. The error was
SEATING→CLOSING, not loss of fruit detection. Nominal bench grasp Z is now25mm
(provisional control clearance, not a measured fig dimension). An already low
measured pose may only leave upward; paths below the table or ending below8mm
still reject. The target location stays recorded as attempted after failure.

Camera controls moved into a right-hand scroll panel shared by portrait and
landscape. Menu or camera tap toggles it;6 seconds inactivity hides it. DUR stays
visible and touch-sized. Rotation keeps the Activity/serial session; layout
resizes to insets. TalkBack touch exploration disables the inactivity timeout.
No camera tap starts a robot movement. Actual phone movement still requires the
existing camera-reference checks; rotating the display is not permission to
reuse a displaced calibration.

## 2026-09-28 — Rotation viewport correction
KolActivity now updates the OpenGL viewport on every surface size change and
invalidates the camera UV transform. Old tag/fruit overlay coordinates are
cleared until the next frame. Previously the preserved EGL context retained
the portrait viewport after landscape rotation, squeezing the camera into only
part of the screen while overlays used the new dimensions. No motor command
or calibration tolerance changed in this correction.

## 2026-09-28 — Rigid camera/base assembly and calibration reuse
Camera-to-base calibration remains relative to the arm, not the AR world.
IMU disturbance or a prolonged camera gap cancels motion but preserves the saved
transform. After the rig settles, fresh stationary marker + encoder evidence
may reactivate the existing transform without a 12-pose scan. A rejected match
is retried read-only; restoring the prior mount can recover without relaunch.
Idle stationary checks also catch relative shifts with little IMU acceleration.
No in-flight transform adaptation or automatic motion restart was added.

Reuse now requires at least7 distinct fresh frames spanning600ms. All but at
most1 of the latest9 must agree for a match or mismatch; mixed evidence waits.
The existing12mm/8deg gates are unchanged. IMU revalidation requires600ms of
quiet rotation/acceleration; these timing values are policy, not sensor accuracy.
GroundProjection continues to resolve table contact from camera intrinsics and
the calibrated base-camera transform without AR depth. This only applies to the
user-confirmed plane at base Z=0; a vehicle on uneven ground needs ground geometry
updates independently of the camera-to-arm calibration.

## 2026-09-28 — Recover known mount without repeating an interrupted full scan
Live22:28 stopped at sample7 after a91°C block reading and independent
34,34,38,34,34°C readings. Three subsequent consistent cold readings were required,
but the two-extra-read cap could never supply them after a third-slot outlier.
Cap is now3 extra reads; any hot direct reading still rejects, disagreement stays
bounded,55°C threshold and250ms motor-loop bound remain unchanged. This corrects
confirmation logic; it does not establish the hardware cause of the spikes.

A previously validated unchanged tool-marker mount makes camera relocation a
6-parameter fit. New known-mount path uses3 training +4 independent held-out poses;
first setup still uses8+4 for both transforms. Pose diversity, disjoint held-out
poses and6/10mm training,8/12mm validation,8deg rotation limits are unchanged.
The seven22:27:53–22:28:10 samples were recovered from tool output (rounded to
9 decimal rotation entries because the Android log ring expired) and tested in
KnownMountRecoveryTest. Java and independent SciPy results agree: trainingRMS2.17,
heldRMS5.72,max8.02mm. No held-out samples were fitted or removed.
Candidate calibration will still require fresh stationary phone marker/encoder
reuse validation before it can authorize any movement. Previous record is backed
up in tmp/calib_recover_record.txt; the recovery candidate is tmp/recovered_camera.record.

22:43 live recovery succeeded: the app accepted the recovered camera transform
against fresh stationary marker/encoder observations without moving for calibration.
Screenshot tmp/recovery_live.png shows table-derived fruit XYZ with a stationary
camera.22:44 approach and seating reached the foreground fig; closure was rejected
by startGrasp because the activity replanned toward the old body pose instead of
holding measured settling offsets. Closing now uses PickupPlan.close(measured).
An explicit long-press Hedefe Git > Burada kavra test closes in place, raises50mm,
and holds. It does not clear attempted-target history, approach again, or visit
the basket; normal automatic cycles still use the six-stage route.

The horizontal 10–15 mm seating direction now follows the projected tool forward
axis, independently of the preceding/folded starting pose. The former start-to-
target vector could point backward relative to the fingers. Z stays constant;
near-vertical ambiguous projection is rejected and existing path checks remain.
This is a model-direction correction, not independent measurement of the physical
finger grasp centre. Regression covers independence from two starting poses.

## 2026-09-28 — Live sensor/frame clock ordering
23:13 supervised new-layout approach stopped before grasp; the saved relative
fit repeatedly restored even while the setup appeared stationary. Both mount
readiness and camera-frame gating compared newer asynchronous callbacks with
the old motor-tick-start timestamp, incorrectly classifying fresh samples as
future readings. Production mount checks now read the clock while holding the
sensor state lock; camera guard samples evaluation time after frame arguments
are captured. No age, acceleration, angle, or calibration thresholds changed.
Regression tests reproduce both stale-clock failures and retain genuine stale
sensor/frame rejection. Physical stop attribution requires the new live run;
the old logs did not contain the specific mount invalidation reason.

## 2026-09-28 — Independent feasibility and reference-video audit
User requested physics/mathematics/vision/code synthesis and comparison with
Nikodem Bartnik's exact video59JTCvpG_Ec before further trial-and-error driving.
Read-only independent kinematics, vision and upstream-source audits were combined.
Same-hardware Sept20 supervised fig-lift evidence supports continued bench
development; arbitrary-ground perfection or sub3s autonomous picking is not
established. Current Java/Python/pinned-URDF math is mutually consistent, while
physical grasp centre, hand-aligned zeros, jaw aperture and plane registration
remain independently unverified. Repeated moving-marker fits cannot identify
an arbitrary physical TCP offset absorbed by the fitted marker mount.

Retain existing hardware and fixed calibration records. Prioritize independent
grasp/aperture and plane measurements, pose-dependent endpoint accuracy, then
timing optimization. A bounded taught planar map is an alternative prototype
path; creator ACT/SmolVLA checkpoints are not drop-in fig-picking programs.
No automatic production switch to learning, no new dependency install, and no
hardware/EEPROM/control-code changes were made by this audit. Detailed current
report is published as ST3215_TEST/TEKNIK_TESHIS_VE_YOL.md.

## 2026-09-29 — Explicit grasp settings, endpoint verification and cycle speed
Implement the known audit defects before claiming physical accuracy. Every
committed pickup leg now uses the frozen selected speed; seating/closing/release
have an explicit600counts/s cap. Existing shoulder/elbow1000 and overall1200
limits stay in force. Grasp closing freezes freshly measured body positions;
more than3counts of body drift before command rejects before writes. Empty
closure reports CLOSED_UNVERIFIED; contact current remains a candidate, not
object-present or force proof. Existing current/temperature/stop limits remain.

The original seated model pose must be within4mm/2deg before closing. Only one
4–8mm bounded compensation is permitted, preserving measured jaw/passive roll,
checking the original pose after settling and retaining travel/table checks.
This is model arrival policy, not an independently measured physical TCP.

Raw gripper endpoints persist atomically with encoder-profile identity. Legacy
894-minus24 behavior migrates explicitly to870; hidden arithmetic is removed.
The780/1153 Sept20 preset is an explicit setting, not an automatic migration.
Capturing current aperture refreshes and validates idle feedback first. Settings
changes send no movement; corrupt/incompatible records block automatic pickup.
No EEPROM reference, physical dimension, camera tolerance or learned policy
was substituted. Version30 is0.30.0-grasp-control.

## 2026-09-29 — Measured table plane and four-pose known-mount renewal
The user explicitly confirmed the arm base bottom is 65 mm ABOVE the fruit's
table. Subsequent user clarification: this elevation was newly added for
field-like testing and was absent during earlier failed attempts. It changes
the current setup; it does not invalidate the earlier same-level setup or
explain its failures. The exact transition relative to logged attempts is TBD.
Version32 (0.32.0-work-surface) stores base height in centimetres under
work_surface.base_height_cm. Missing records retain the legacy 0 default;
the current setup must explicitly save 6.5 via long-press Hedefe Git >
Taban yüksekliği (cm). Saving does not move motors, invalidate the camera
calibration, or clear attempted targets.

Keep the existing robot coordinate origin, URDF and encoder references.
Ground is Z=-65 mm and the provisional 25 mm grasp clearance gives Z=-40 mm.
Camera ray/plane projection and pickup/calibration path floors all reference
the same selected work plane. This is measured setup geometry, not a change
to critical arm dimensions or proof of physical fingertip accuracy.

With an unchanged known tool-marker mount, renewal uses two fitting poses
and two separate held-out poses; prior seven-pose records remain accepted.
Unknown marker mount still requires the full twelve-pose procedure. The
four-pose path was observed succeeding on v31; v32 physical pickup remains
unverified. Integrated validation: 282 JVM tests and Android lint passed.

## 2026-09-29 — Preserve failed v32 calibration evidence; inspect raw observations
Version32 was installed and the 6.5 cm setting was saved through the phone UI.
Persistence was verified in work_surface.xml after APK reinstall and cold start.
The new phone view rejected the old fit (44.8mm/12.6deg); the explicitly started
03:10:24–03:10:32 four-pose scan collected all poses but failed held-out validation
(RMS11.3/max15.5mm). Do not accept that fit or report successful pickup.

Model rotation is identical for poses3→4, yet expected marker translation is
23.094mm and observed translation34.207mm. A fixed marker offset or table-plane
change cannot reconcile this pair. Last-pose optical-depth/vertical residuals
are +12.1/+8.8mm; optical bias versus physical movement remains unresolved.
Keep thresholds and motion policy unchanged. Add only an opt-in developer
marker_diagnostics capture: at most one PNG/JSON pair per second, 32-slot ring,
default off, to inspect raw corners and camera intrinsics before further claims.
Evidence: reports/diagnostics_20260929/ground32_math_diagnosis.json and
reports/diagnostics_20260929/ground32_live.log.

## 2026-09-29 — Confirmed base-body play; require physical repair before motion
The user confirmed visible right-left play in the rotating body above the
bottom ID1 servo while the table clamp remains firm. Stationary background
and independent raw-corner PnP checks support the observed marker rotation.
In the diagnosed sample, an unreported6.038deg base yaw reduces34.400mm model
position mismatch to3.366mm and orientation mismatch to1.283deg. The equivalent
ID1-count delta (-68.702) is a diagnostic calculation, NOT a new encoder offset.

Do not fit away this variable mechanical freedom with a software offset, wider
calibration thresholds, or repeated motor trials. Pause motor movement tests
until play is physically repaired and marker/model correspondence is reverified.
Exact loose horn/body attachment versus internal gearbox source is UNVERIFIED;
no physical repair, torque release or successful new pickup is claimed.
The separately developed v33 geometric target filter is not recorded as built
or physically validated yet. Retain the user-confirmed65mm setup height without
retroactively blaming prior same-level attempts on that later elevation.

Permanent evidence (copied with SHA256 verification):
reports/diagnostics_20260929/scan33_base_yaw_explanation.json and
reports/diagnostics_20260929/scan33_axis_diagnosis.json.

## 2026-09-29 — Stationary-start fig range must not fall back to AR hits
User reports a roughly 30 cm scene displayed as roughly 2 m in the FIG box,
not the ID0 marker readout, when starting with a stationary camera. Exact
numeric reproduction on this device is pending; no screenshot of that original
reading was captured. KolActivity previously displayed AR depth/plane/feature
ranges when measured-plane projection was unavailable, and could transform a
depth/plane fallback into robot targets when the marker reference was valid.

Remove both fig-range and robot-target fallback paths. FigTargetGeometry uses
only a validated camera/ground-plane reference, and keeps camera-to-contact
range distinct from the provisional raised grasp point. Invalid reference or
projection gives no target. AR world tracking and initial camera movement are
not inputs to this metric projection. Legacy tap calibration and the separate
historical MainActivity scanner are outside this change.

Add a read-only live ID0 distance dialog (Hedefe Git long press > Kamera
mesafesini kontrol et). It uses the measured 36 mm black square and camera
intrinsics, with fresh unambiguous stable observations, without robot FK or AR
depth. This permits a ruler check; it does not certify fig coordinates. A
separate ground-tag measurement workflow was proposed but not implemented or
physically set up. Do not infer that hiding invalid AR numbers fixes physical
camera accuracy. No motor movement, calibration-threshold or encoder change
is part of this correction.

## 2026-09-29 — User-reported repair, v33 delivery and exclusive device handoff
User reported the rotating coupling play fixed with12V off, then confirmed12V
on for supported hold. Treat this as reported repair, not independent proof of
the exact loose component or repeatability across working poses.

Build33 includes the shared FigTargetGeometry changes;290 JVM tests and lint
passed, device version33 was confirmed, and publish_current delivered the APK.
After the second short scan03:56:45–53, green robot XYZ appeared, but the later
03:57:07 log rejected13.5mm/6.0deg marker/model disagreement. Do not equate that
intermediate green overlay with durable calibration or successful physical pickup.

Root issued DUR around03:56:55 and explicit disconnect around03:57:30. The bridge
confirmed measured hold and exited; no8873 listener remains. Cede exclusive
phone/arm control to the other active camera chat; no further device commands
or republishing by this chat while that session operates. Evidence:
reports/diagnostics_20260929/repair33_live.log and repair33_stop.png.

Offline post-tightening analysis confirms local improvement in the second scan:
fit RMS0.708mm, held RMS5.185/max6.377mm, max orientation0.312deg, last-pair
unmodelled yaw0.294deg. The earlier~6deg example uses a different configuration;
do not present this as controlled same-path repeatability. First-scan initial
unmodelled rotation7.814deg still rejects, as does the later13.5mm/6.0deg check.
Keep full-workspace accuracy and pickup unverified. Durable numerical report:
reports/diagnostics_20260929/repair33_after_tightening_analysis.json.


## 2026-09-29 — Upstream pickup review and bounded full-cycle selection
Seven user-requested repositories were inspected at pinned commits (22 selected
files); provenance and hashes are in reports/upstream_pickup_review. No foreign
arm driver, calibration constant, model weights or RL policy was installed.
PickupCycle now evaluates the existing seven pitches as complete six-leg plans,
keeps 15mm seating preferred and 10mm fallback, and chooses the shortest nominal
complete trajectory. Remove the unnecessary pre-seating lift requirement only
from full-cycle selection; validate the actual post-seating lift and every leg.
Current C2 timing, joint/temperature/tracking limits, passive roll, ground plane,
gripper settings and fresh execution guards remain in force. No CAD change.
293 JVM tests and lint passed. Offline112 targets:107 to110 feasible, no lost
solutions; common-case nominal time668.133 to649.053s. This is not physical speed
or grasp evidence. Full mesh collision/Cartesian path/RL remain unimplemented.
User confirmed mechanical play repaired and authorized coordination with the two
other active FIGBOT chats. Device actions wait for exclusive handoff; latest
13.5mm/6deg rejection must not be bypassed. See published source guide
software/st3215_test/KAYNAK_REPOLAR_VE_TOPLAMA.md.

## 2026-09-29 — Serialize current publication after concurrent archive writes
Concurrent publish_current invocations collided while appending to the shared
ESKI_SURUMLER.zip. One invocation failed its header/SHA check while the other
was still writing. After the last writer completed, all6003 indexed local
headers matched the central directory. The three latest entries passed CRC
readback; both archived APKs hash to DD16CA42BAFBCF29B9764CDEFF60FE2662456CBA125B86A65039906854CA2F5A,
preserving the previous camera-check build. No ZIP rewrite or deletion needed.
Source and current ANDROID_OKU.md match, including both user range confirmations.

scripts.publish_current now takes a cross-process nonblocking publication lock
before dispatch to any publisher. A second CLI publication fails before writes;
OS releases the lock on exit. Direct lower-level publisher calls are not covered
and remain unsupported for concurrent use. Two lock regressions and four existing
publication tests pass. Audit records: archive_header_audit.json and
archive_latest_verified.json under reports/diagnostics_20260929.


## 2026-09-29 — Angle-aware marker precision and rotation consensus (v35)
Keep IPPE_SQUARE + LM perspective pose estimation, without empirical angle offsets,
FK-based pose substitution, calibration threshold widening, or forced recentering.
MarkerViewQuality evaluates the normal-to-viewing-ray incidence (not optical-axis
angle), minimum projected polygon width, and local 6-DOF pinhole sensitivity.
J contains camera-frame translation and rotation-about-marker-centre derivatives;
local covariance is sigma^2 inverse(J^T J), sigma=max(0.35 px,reprojection RMS).
Usable gates: incidence<80deg, width>=20px, translation RSS<=3mm, rotation
RSS<=3deg. Existing detector edge28px/reprojection1.5px/planar-ambiguity gates
remain. These engineering limits and noise floor are UNVERIFIED for absolute
physical error; they do not detect systematic lens/print/flex/model errors.
Prediction applies the same precision gate for known-mount scan paths. Unknown
mount scans still rely on live observations; no new unverified mount is invented.
StablePoseWindow retains its 3mm/3deg inlier and freshness gates, but averages
admitted orientations on SO(3) about the medoid instead of using one raw frame.
All KolActivity marker-dependent execution, calibration/reuse, range and target
gates now require usable(), while raw detection/ambiguity stays diagnostic data.
301 JVM tests, Android lint, 8 device-native tests pass; native raster grid has
12 tilt/roll cases, max0.636812mm/0.179125deg. No motion or pickup validation.
Sources: OpenCV PnP documentation https://docs.opencv.org/4.x/d5/d1f/calib3d_solvePnP.html.
Evidence: reports/oblique_marker_review (32 pre-change raw frames, corner
refinement comparison, native_angle_test.log, v35_live.log and screenshot).


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

2026-09-29 passive recorder hardening: default and check-only modes use
ReadOnlyTeachingBus, rejecting every non-READ instruction and invalid/broadcast
servo address before serial I/O. The explicitly selected supported-release mode
retains its separate torque-off path. No supported-release flag was used during
the recorded demonstrations. Recorder, teaching and recording tests: 13 passed.

## 2026-09-29 — Corrected imitation targets and separate route candidates
User clarified that hand-guided success does not make every movement desirable:
open the gripper before approach, keep opening consistent, remove accidental
drops/deviations and improve fig/basket routes. Preserve raw observations; store
synthetic corrected targets separately with source hashes and phase annotations.
Do not infer an intended Cartesian path where geometry is unknown. Exclude
suspect training intervals; route bridges across them remain review candidates.
No new physical dimension or jaw opening in mm is asserted.

Train an explicit small CPU visual/joint baseline locally, withholding the fourth
pickup without overlapping sample histories. Old episodes with possible late
opening are excluded. The first policy failed the held-out baseline comparison;
retain weights/evidence but mark deployment REJECTED_HELD_OUT_CYCLE. No cloud
upload or learned-policy-to-motor connection. Route generation is a separate
deterministic process, not a claimed capability of this rejected network.

## 2026-09-29 — Bounded measured-position shoulder correction
Following explicit user request, compensate the reproduced stationary shoulder
residual through bounded SRAM goal adjustments. Preserve physical endpoint
tolerance and factory settings. Enable only for verified stationary ID2 residuals
near a reviewed target; never for a moving joint, camera loss or arbitrary fault.
Use no more than3x12count trims, verify other held joints, then establish measured
hold and recheck original arrival tolerance. This is an opt-in supervised helper,
not a blanket bypass of motion faults. Real test reduced final residual23->4
counts and allowed remaining empty taught basket route to complete.

## 2026-09-29 — Supervised grasp verification
Use bounded incremental jaw closure with fresh image/readback and independent
short-lift verification. Preserve measured closing position through taught lift
and carry; no automatic reopening inherited from the empty-route harness.
Release requires the recorded basket encoder endpoint. Raw-current and position
residuals only indicate possible contact; neither proves grasp. Keep learned
neural policy disconnected because its held-out evaluation failed.

## 2026-09-29 — Faster supervised four-fig trial and narrower opening
User explicitly requested collecting all four faster, then reducing unnecessary
jaw travel. Use observed opening1283 instead of1559; the44% reduction refers to
encoder travel from935, not a claim about millimetres of physical opening.
Requested empty approach240 and loaded transfer180 (previous successful120)
remain bounded by250 profile cap. Keep near-object motion90 and incremental
closure60, existing feedback/arrival/camera limits. Retain separate visual
checkpoints; no autonomous policy deployment or high-speed900 candidate.
New targets use demonstrated approach corridors, reversed for loaded returns
to avoid suspect hand-guided carry discontinuities. These reverse corridors
require staged physical review; numerical preflight is not collision proof.

## 2026-09-29 — Isolate teaching camera from inference workload
Observed camera freshness interruptions during supervised motion, then503 with
105ms CPU-image skew rejection. In teaching-camera mode run only the raw export
task; keep ArUco/YOLO on the normal operation path. Preserve all timing limits
and camera/motor interlocks. Install only while robot holds stationary, then
verify actual distinct fresh frames before a separately reviewed motion resume.
This improves camera transport; it does not establish object localization.
