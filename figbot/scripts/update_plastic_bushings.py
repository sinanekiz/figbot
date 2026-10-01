"""One-time source migration for DEC-081; no printer or motor operation."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def edit(rel,old,new):
    p=ROOT/rel;s=p.read_text(encoding='utf-8');assert old in s,(rel,old[:70]);p.write_text(s.replace(old,new),encoding='utf-8')

edit('scripts/package_linka_plates.py',"    ('05_YUMUSAK_PEDLER', 'TPU_OR_CUT_SILICONE', [(18,90,110),(18,110,110),(18,130,110)]),", "    ('05_YUMUSAK_PEDLER', 'TPU_OR_CUT_SILICONE', [(18,90,110),(18,110,110),(18,130,110)]),\n    ('06_PLASTIK_BURCLAR', 'PLA', [(23,20,20),(24,45,20),(24,70,20),(25,20,50),(25,45,50),(25,70,50)]),")
edit('scripts/package_linka_plates.py','LINKA L1.3 / DEC-080 deneme revizyonudur. L1.2\'ye göre yalnız L1-01 tabandaki kablo pencereleri değişti. Kablo çıkıntısı7×3,9×5,5mm olarak ölçüldü; gövdedeki konumu eşleşmeden yeni tabanı basma. L1.2\'nin diğer parçaları korunmuştur.', 'LINKA L1.4 / DEC-081 deneme revizyonudur. L1.3 sonrası yalnız üç L1-17 parmağın pivot deliği büyüdü; L1-23/24/25 plastik burçlar eklendi. Eski parmakla yeni burcu karıştırma. Diğer eski parçalar korunur. Burçlar için100% dolgu, en az3 duvar hedefi ve delik ekseni dik baskı; dilim önizlemesinde kesintisiz duvarlar kontrol edilir. Dar delikleri zorlayarak vida sokma. Plastik dirsek burçlarının ezilme/sünme davranışı ve sıkma ayarı doğrulanmadı; ilk kullanım yalnız uyum/yüksüz denemedir.')
edit('scripts/package_linka_plates.py','LINKA L1.3 — ayrı baskı tablaları','LINKA L1.4 — ayrı baskı tablaları')
edit('scripts/package_linka_plates.py','**4 PLA tablası + 1 isteğe bağlı yumuşak ped tablası**. Toplam29 PLA parça ve3 ped. DEC-080 tabandaki kablo pencerelerini ekler. L1.2\'ye göre YALNIZ L1-01 yenilenir; diğer parçaları yeniden basma.', '**5 PLA tablası + 1 isteğe bağlı yumuşak ped tablası**. Toplam35 PLA parça ve3 ped. DEC-081 üç parmağı yeniler ve6 plastik burç ekler. L1.3 basılıysa yalnız04A yeni parmaklar ve06 burçları bas; tam04 ile04A birlikte basılmaz.')
edit('scripts/package_linka_plates.py','| [05_YUMUSAK_PEDLER.zip](05_YUMUSAK_PEDLER.zip) | TPU pedler; silikon kullanılacaksa basma | 3 |', '| [05_YUMUSAK_PEDLER.zip](05_YUMUSAK_PEDLER.zip) | TPU pedler; silikon kullanılacaksa basma | 3 |\n| [06_PLASTIK_BURCLAR.zip](06_PLASTIK_BURCLAR.zip) | 1 uzun +2 kısa dirsek burcu,3 parmak burcu | 6 |')
edit('scripts/release_linka_cable_exit.py',"assert [r['part'] for r in rows if r['old_sha']!=r['new_sha']]==['L1-01-BASE']", "assert set(r['part'] for r in rows if r['old_sha']!=r['new_sha'])=={'L1-01-BASE','L1-17-FINGER'}")
edit('scripts/release_linka_cable_exit.py',"status.update(revision='LINKA L1.3 / DEC-080',", "status.update(revision='LINKA L1.4 / DEC-081',")
edit('scripts/release_linka_cable_exit.py',"printing_reuse='Only L1-01 changes from L1.2; do not reprint others; verify boot position before printing base'", "printing_reuse='From L1.3: replace three L1-17 fingers using04A and add06 plastic bushes; other21 old part types unchanged; prototype only'")
edit('scripts/release_linka_cable_exit.py',"print(json.dumps({'changed':['L1-01-BASE'],'other21_identical':True,'physical_cable_fit':'UNVERIFIED'}))", "print(json.dumps({'cable_window_unchanged_from_L13':True,'revision':'L1.4','physical_cable_fit':'UNVERIFIED'}))")
edit('scripts/publish_current.py',"    run('scripts.release_linka_cable_exit')", "    run('scripts.release_linka_cable_exit')\n    run('scripts.package_plastic_bushings')")
edit('scripts/publish_current.py','Bu düzenleme CAD geometrisini değiştirmedi.', 'L1.4 üç parmağın pivot deliğini değiştirir ve6 plastik burç ekler. Yalnız04A ve06 yeni baskı gerektirir; tam04 ile04A birlikte basılmaz. Plastik burçlar yüksüz uyum denemesidir, yüklü çalışma onayı değildir.')
edit('scripts/publish_current.py','Tam baskı için01,02,03,04 tablaları;05 yalnız yumuşak ped seçeneğidir.', 'Tam baskı için01,02,03,04,06 tablaları;05 yalnız yumuşak ped seçeneğidir. Eski L1.3 basılıysa yalnız04A üç yeni parmak ve06 altı burç basılır.')
edit('scripts/publish_current.py','Metal burç alternatifleri henüz çözümlenmedi.', 'L1.4 plastik burç alternatifi geometri olarak hazırdır; sıkma, sürtünme, aşınma ve sünme fiziksel olarak doğrulanmadı. Burçları100% dolgu, en az3 duvar hedefiyle delik ekseni dik bas; gerçek dilim önizlemesini kontrol et.')
edit('scripts/build_linka_shopping.py',"for row in ROWS:row['order_hold']=False", """for row in ROWS:row['order_hold']=False
for code,part,usage in [('ELBOW_SLEEVES','Baskı: PLA dirsek burçları','L1-23:1 adet28mm; L1-24:2 adet4mm; dış8/iç5,3'),('FINGER_TUBE','Baskı: PLA parmak burçları','L1-25:3 adet6mm; dış4,8/iç2,4; yalnız yeni L1-17 parmaklarla')]:
    index[code].update(part=part,usage=usage,buy_quantity=None,supplier='Mevcut filament',url=None,price_per_pack=None,order_hold=True,status='L1.4 BASILACAK; fiziksel doğrulama bekliyor',note='Metal burç alınmayacak, tornacı işi yok. GUNCEL/BASKI/06_PLASTIK_BURCLAR. Yalnız yüksüz uyum denemesi; PLA sünmesi ve sıkma ayarı doğrulanmadı.')
index['FINGER_SCREW']['usage']='Üç parmak; M2x14 vida yeni plastik burcun içinden geçer'
index['FINGER_SCREW']['note']='L1.4 yeni L1-17 parmak ve L1-25 burçla; pul eklenmez. Sıkınca parmak serbest dönmeli; gerçek insert tutuşu kontrol edilmeli.'""")
edit('scripts/build_linka_shopping.py',"revision='LINKA L1.1 / DEC-078'", "revision='LINKA L1.4 / DEC-081'")
edit('scripts/build_linka_shopping.py',"md='# LINKA L1.1 — bir kol için montaj alışveriş listesi", "md='# LINKA L1.4 — bir kol için montaj alışveriş listesi")
edit('scripts/build_linka_shopping.py','14 Eylül 2026 / DEC-078. **Eski L1 listesinin yerine geçer.**','14 Eylül 2026 / DEC-081. **Metal dirsek/parmak burçları satın alınmaz; plastik deneme parçaları basılır.** Vida, pul, insert ve rulmanlar L1.1 ölçülerini korur.')
edit('scripts/build_linka_shopping.py',"else 'ölçü/kesim'", "else ('BASILACAK' if r['code'] in {'ELBOW_SLEEVES','FINGER_TUBE'} else 'bekle')")
edit('scripts/build_hardware_counter_list.py','Dirsek ara burçları:</b> metal işleme siparişi verilmeyecek.<br/>Hazır parça / 3D baskı alternatifi henüz doğrulanmadı.', 'Dirsek ara burçları:</b> L1-23/24 plastik deneme baskısı.<br/>06 tablasında. Metal burç alınmayacak.')
edit('scripts/build_hardware_counter_list.py','Parmak ara burçları:</b> boru alıp kestirme / deldirme yok.<br/>3D baskı alternatifi henüz doğrulanmadı.', 'Parmak ara burçları:</b> L1-25 plastik deneme baskısı.<br/>Yeni L1-17 parmakla; metal boru alınmayacak.')
edit('scripts/build_hardware_counter_list.py','bekleyen burç çözümü olmadan tam montaj listesi değildir.', 'plastik burçlar için yüklü kullanım onayı verilmemiştir.')
edit('scripts/build_hardware_counter_list.py','LINKA L1.1','LINKA L1.4')
edit('viewer/kol.html','LINKA L1.3','LINKA L1.4')
edit('viewer/kol.html','DEC–080','DEC–081')

if __name__=='__main__':print('DEC-081 source migration applied')
