"""DEC-081 replacement fingers only; current stable paths and explicit prototype status."""
import json,zipfile
import numpy as np
import trimesh
from scripts.package_linka_plates import SOURCE,OUT,combine_3mf,preview

NOTE='''# Kepçe parmaklar ve plastik burçlar — L1.5 / DEC-082

Yalnız yüksüz uyum ve elle hareket denemesi. Yüklü kullanım/ömür/sünme doğrulanmadı.

- 06: L1-23 uzun dirsek burcu1 adet (dış8/iç5,3/boy28mm); L1-24 kısa burç2 adet (dış8/iç5,3/boy4mm); L1-25 parmak burcu3 adet (dış4,8/iç2,4/boy6mm).
- 04A: pivot deliği5,1mm olan yeni L1-17 parmak3 adet. Eski3,2mm delikli parmakla yeni burç uymaz. Eski parçayı matkapla büyütme talimatı değildir; yenisini bas.
- L1.5: L1-17 parmak10mm daha uzun, kepçe biçiminde genişledi. L1-18 temas yüzeyi1mm TPU astar olarak yenilendi;05 yeniden basılır. Burç,vida,insert ve pivot/iki ip deliği korunur. L1.4 basılıysa yalnız04A ve05 yenilenir;06 burçları tekrar basma.
- Tam04 yeni parmakları içerir; 04A ile birlikte basma. L1.4 sonrası diğer23 parça türü değişmedi. Vida, insert, pul ve rulman ölçüleri değişmedi. Çelik bilye ve625 rulmanlar plastik burçla ikame edilmez.
- Kepçe parmak baskısı: ağız yukarı,0,4mm nozzle,4 duvar,%100 dolgu,5mm brim; yalnız tabladan dış destek (snug/sıkı). TPU astar1mm,3 duvar,%100 dolgu,5mm brim ve tabladan dış destek.04A,04 ve05 için PrusaSlicer2.8.1 ile0,16mm katmanda çevrimdışı takım yolu üretildi; bu gerçek yazıcı/TPU profili veya destek sökümü onayı değildir. Organik destek kullanılırsa komşu nesneye taşabilir; yeniden dilim kontrolü gerekir.
- PLA, mevcut0,4mm nozzle için: burçlarda100% dolgu ve en az3 duvar hedefi, delik ekseni dik. Parmak burcu nominal1,2mm, dirsek1,35mm etlidir. Gerçek çizgi genişliğine göre kesintisiz dolu halkayı önizlemede kontrol et. Üst/alt yüzey düzgün olmalı. Küçük taban alanı nedeniyle5mm dış brim kullan; metadata aktarılmadıysa elle ekle. Brim kalıntısı yatak yüzünde kalmamalı. G-code/makine profili değildir.
- Önce bir parmak burcunu ve yeni parmağı eşleştir: burç parmak içinde elle dönebilmeli, M2 vida deliğe zorlamadan geçmeli. Delik dar/oval veya duvar eksikse montajı zorlamadan baskı ayarını düzelt.
- Parmak dizilimi: sabit kulak / yeni parmak içindeki6mm burç / karşı sabit kulak. M2x14 vida içinden geçer.5,5mm parmak için nominal0,5mm eksen payı vardır; düğüm ve gerçek baskı payı ayrıca kontrol edilir.
- Dirsek milindeki4/28/4mm uzunluklar eski konumlarda korunur; burçlar yalnız iç bileziklere dayanır. Fiberli somunu plastiği ezerek sıkma. Güvenli sıkma torku TBD; sayısal tork önerilmiyor. Baskı sıkıldığında boşluk değişiyor, burç kısalıyor veya dirsek sıkışıyorsa motorla çalıştırma. Vida gevşek bırakılarak sorun gizlenmez.
- Metal burç siparişi/tornacı işi yok. Baskı malzemesi maliyeti, gerçek sürtünme ve kullanım ömrü henüz ölçülmedi.
'''

def main():
    name='04A_YALNIZ_YENI_PARMAKLAR';dest=OUT/name;dest.mkdir(exist_ok=True)
    pid='L1-17-FINGER';entries=[]
    for i,x in enumerate([20,100,180],1):
        m=trimesh.load_mesh(SOURCE/'PRINT_STL'/f'{pid}.stl')
        shift=(np.array([x,20,0])-m.bounds[0]).tolist();m.apply_translation(shift)
        entries.append(dict(id=pid,copy=i,name=f'{pid}__{i}',translation=shift,mesh=m))
    trimesh.util.concatenate([e['mesh'] for e in entries]).export(dest/f'{name}.stl')
    combine_3mf(entries,dest/f'{name}.3mf','PLA');preview(dest/f'{name}.png',name,'PLA',entries)
    (dest/'BASLAMADAN_ONCE.md').write_text(NOTE,encoding='utf-8')
    with zipfile.ZipFile(OUT/f'{name}.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in dest.iterdir():z.write(p,p.name)
    name='06_PLASTIK_BURCLAR';dest=OUT/name
    (dest/'BASLAMADAN_ONCE.md').write_text(NOTE,encoding='utf-8')
    with zipfile.ZipFile(OUT/f'{name}.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in dest.iterdir():z.write(p,p.name)
    (SOURCE/'PLASTIK_BURC_MONTAJI.md').write_text(NOTE,encoding='utf-8')
    guide=SOURCE/'ASSEMBLY_NOTES_TR.md';old=guide.read_text(encoding='utf-8')
    if not old.startswith('# L1.5 / DEC-082'):
        guide.write_text('# L1.5 / DEC-082 — kepçe parmaklar\n\n04A üç uzun kepçe parmak,05 üç1mm kavisli TPU iç astardır. Parmakların pivot ve iki ip deliği aynı konumdadır; L1-25 plastik burç ve M2x14 vida korunur. Astarlar iç bükey yüzeye eşleşir; destek kalıntısı temizlenir. Uygun yapıştırıcı/sabitleme ve meyve temas deneyi TBD; sert PLA ile yumuşak astar ikame edilmez.12deg yalnız CAD kapalı görünümüdür, servo komutu değildir. Yan ve dipte hareket boşlukları vardır; meyve kaçırmama fiziksel olarak doğrulanmadı. L1.4 basılıysa yalnız04A ve05 yenilenir;06 burçları tekrar basma.\n\n'+old,encoding='utf-8')
    p=SOURCE/'RELEASE_STATUS.json';s=json.loads(p.read_text(encoding='utf-8'))
    s.update(revision='LINKA L1.5 / DEC-082',status='SCOOP AND PRINTED BUSH PROTOTYPE; PHYSICAL VALIDATION REQUIRED', scoop_closed_angle_deg=12, scoop_min_sampled_clearance_mm=1.1447,physical_approval=False,plastic_bushes='L1-23/24/25; three new L1-17 fingers required',load_validation='UNVERIFIED; polymer clamp creep and wear not measured')
    p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
