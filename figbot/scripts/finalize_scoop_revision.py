"""Apply DEC-082 documentation changes; geometry is defined in build_linka_v1."""
from pathlib import Path

def edit(path,old,new):
    p=Path(path);s=p.read_text(encoding='utf-8');assert old in s,(path,old);p.write_text(s.replace(old,new),encoding='utf-8')

edit('scripts/package_plastic_bushings.py','# Plastik burçlar — L1.4 / DEC-081','# Kepçe parmaklar ve plastik burçlar — L1.5 / DEC-082')
edit('scripts/package_plastic_bushings.py',"status='PRINTED BUSH PROTOTYPE; UNLOADED FIT ONLY'","status='SCOOP AND PRINTED BUSH PROTOTYPE; PHYSICAL VALIDATION REQUIRED', scoop_closed_angle_deg=12, scoop_min_sampled_clearance_mm=1.1447")
edit('scripts/publish_current.py','Yalnız04A ve06 yeni baskı gerektirir','L1.4 sonrası yalnız04A ve05 yeni baskı gerektirir')
edit('scripts/package_linka_plates.py','L1.3 basılıysa yalnız04A yeni parmaklar ve06 burçları bas','L1.4 basılıysa04A kepçe parmaklar ve05 TPU astarlar yenilenir. L1.3 basılıysa ayrıca06 burçları bas')
edit('scripts/release_linka_cable_exit.py',"'revision':'L1.4'","'revision':'L1.5'")
edit('scripts/release_linka_cable_exit.py','From L1.3: replace three L1-17 fingers using04A and add06 plastic bushes; other21 old part types unchanged; prototype only','From L1.4: replace L1-17 fingers using04A and L1-18 TPU liners using05; other23 types unchanged. From L1.3 also add06 plastic bushes; prototype only')
edit('scripts/build_linka_shopping.py',"\ndef build():","\nindex['PADS'].update(part='Baskı: 1mm kavisli TPU iç astar',usage='L1-18; üç yeni kepçe parmağın iç yüzeyi',supplier='Mevcut TPU filament',url=None,buy_quantity=None,price_per_pack=None,order_hold=True,status='L1.5 BASILACAK; fiziksel doğrulama bekliyor',note='05 tablasında üç adet. Eski4mm düz silikon ped kullanılmaz. TPU sertliği, destek sökümü, uygun yapıştırıcı/sabitleme ve meyvede iz bırakma testi TBD; gerçek maliyet ve gıda teması UNVERIFIED.')\n\ndef build():")
for p in ['scripts/build_linka_shopping.py','scripts/build_hardware_counter_list.py']:
    edit(p,'LINKA L1.4','LINKA L1.5')
edit('scripts/build_linka_shopping.py','/ DEC-081','/ DEC-082')
edit('scripts/build_hardware_counter_list.py','F. Hobi / silikon','F. Hobi / yumuşak temas')
edit('scripts/build_hardware_counter_list.py',"'<b>4 kalınlıkta yumuşak silikon levha</b>; 3 ped, yaklaşık<br/>4 × 10 × 13. Küçük artık parça yeterli. <b>TPU ped varsa alma.</b>',need='3 ped',buy='artık'","'<b>1 mm kavisli TPU iç astar:</b> 05 tablasında 3D baskı.<br/>Üç kepçe parmak için. <b>Eski düz silikon levhayı alma.</b>',need='3 astar',buy='BASKI'")

decision='''## DEC-082 — L1.5: 10 mm longer scoop fingers (2026-09-14)

User requests 10mm longer fingers with broad, thin distal scoops to reduce lateral fruit escape. Only L1-17 and L1-18 change relative to L1.4. Finger local tipZ -35→-45mm, head maximumZ4 retained (overall49mm); maximum transverse width49.19mm. Five ruled annular sections form each scoop, nominal radial wall1.6mm. Root width5.5mm, pivot bore5.1mm and both tendon bores/positions remain unchanged. No added hardware; L1-25 sleeves and all other23 printed types remain unchanged.

Candidate closed pose12deg retains minimum1.1447mm hard-finger clearance at the sampled poses -15,-10,0,6,12deg. This is not continuous swept collision certification or a promise of fruit retention. Fruit40–50g is user-provided; actual width/height remains UNKNOWN. The bottom and side seams intentionally remain open for clearance, drainage and movement. New1mm conformal TPU liners replace old flat4mm pads; compatible adhesive, food contact and actual friction/firmness TBD. No actuator limits or firmware are changed.

Print three replacement fingers in04A and three liners in05. Do not duplicate04/04A. Fingers print mouth up,4 walls/100% fill/5mm brim with external bed supports. Existing06 sleeves need not be reprinted. Export source, assemblies, closed-gripper scene, renders, URDF, print layouts, BOM and costs are rebuilt. CAD mass is a solid-volume estimate, not measured printed weight. PLA layer strength, supports removal, TPU fit, grasp reliability and creep require physical trials; manufacturing/load approval remains false.

'''
p=Path('DECISIONS.md');p.write_text(decision+p.read_text(encoding='utf-8'),encoding='utf-8')
p=Path('MASTER_SPEC.md');p.write_text('# Active revision — LINKA L1.5 / DEC-082\n\nOnly L1-17 fingers and L1-18 liners change from L1.4: tip extends10mm, broad49.19mm scoop, nominal1.6mm radial wall, new1mm TPU inner liner. Root/bores/fasteners/bushes unchanged. Reprint04A and05 only if L1.4 already printed. Candidate closure12deg; sampled minimum finger gap1.1447mm. Physical grasp, fruit fit, strength and liner attachment UNVERIFIED. Earlier current-revision statements below are historical. See DEC-082.\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
p=Path('ASSUMPTIONS.md');p.write_text('# L1.5 scoop assumptions — DEC-082\n\nFruit width/height, TPU hardness/density/food contact, liner adhesive and safe grip force are UNKNOWN. 40–50g fruit does not establish its diameter. 1.6mm radial scoop wall and1mm TPU liner are prototype design choices; minimum normal loft wall may differ from radial section thickness. At12deg CAD closure sampled finger gap is1.1447mm, not zero; no promise of no dropped fruit. Finger/liner support removal and loaded PLA creep/strength PHYSICAL VALIDATION REQUIRED. No hardware or firmware increase is authorized by this CAD revision.\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
