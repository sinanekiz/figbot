"""Actual L1.1 bearing section and nominal insert bores, separate from the arm BOM."""
import json
import zipfile
import trimesh
from cad.prototype_arm import build_linka_v1 as a
from cad.prototype_arm.export_forma_v6 import mesh,write_3mf
from cad.utils import export_shape
from scripts.package_linka_plates import OUT

def build():
    dest=OUT/'00_UYUM_DENEMESI';dest.mkdir(parents=True,exist_ok=True)
    # Cut an actual distal bearing seat; do not redraw an idealized substitute.
    seat=a.upper_side(1).intersect(a.h.box(36,16,36,(a.U,16,0)))
    cap=a.bearing_cap()
    block=a.h.box(52,16,8,(26,8,4))
    specs=[('M3_L5',8,4.2,5),('M3_L4',20,4.2,4.5),('M2_L4',32,2.9,4.4),('M2_L3',44,2.9,3.5)]
    for label,x,d,depth in specs:block=a.h.insert_hole(block,x,8,8,d,depth)
    shapes=[('A_UPPER_BEARING_SEAT',a.print_pose('UPPER',seat)),('B_BEARING_CAP',a.print_pose('BEARING-CAP',cap)),('C_INSERTS_LEFT_TO_RIGHT',block)]
    entries=[];x=8
    for name,s in shapes:
        assert len(s.val().Solids())==1 and s.val().isValid()
        export_shape(s,dest,name,['stl','step'])
        m=mesh(s);m.apply_translation([x-m.bounds[0,0],8-m.bounds[0,1],-m.bounds[0,2]])
        assert m.is_watertight and m.is_winding_consistent
        entries.append((name,name,m,[]));x=m.bounds[1,0]+8
    assert x<248
    write_3mf(entries,dest/'00_UYUM_DENEMESI.3mf')
    trimesh.util.concatenate([e[2] for e in entries]).export(dest/'00_UYUM_DENEMESI.stl')
    (dest/'OLCU_VE_KULLANIM.md').write_text('''# Küçük uyum denemesi — LINKA L1.1

Kol BOM'una eklenen yapısal parçalar değildir. Aynı filament, %100 ölçek ve aynı delik telafisiyle bas. Birleşik 3MF veya birleşik STL seç; ayrıca tekil STL'leri ekleme. Kuponu 100% dolgu ile dilimle; alttaki boşlukları/destek ihtiyacını önizlemede kontrol et. Parça A gerçek sağ üst kolun rulman ucundan kesilmiştir, B gerçek kapaktır.

- A: 625ZZ 5×16×5 mm rulman için Ø16,15 mm yuva. Rulman arkasında 2,5 mm basma desteği. Üç insert M2, dışØ3,2 × boy3 mm; M2×6 kapak vidaları. Kapağın üç ayağı plastiğe oturur; rulmana nominal0,2 mm eksenel boşluk kalır. Baskı toleransı denenmeden kuvvetle sıkma.
- B: A ile eşleşen Ø32 kapak. Standart L1-22 ile aynıdır; kupon için basılan temiz, uygun kapak sonradan kullanılabilir ancak üretim paketindeki iki kapağın yerine sayarken adet takibi yap.
- C: uzun şerit üzerindeki dört delik soldan sağa M3 boy5 / M3 boy4 / M2 boy4 / M2 boy3. Delikler sırasıyla Ø4,2×5 / Ø4,2×4,5 / Ø2,9×4,4 / Ø2,9×3,5 mm. Bu delikler gerçek nominal tasarım ölçüleridir; evrensel insert uyumu anlamına gelmez.

Pirinç inserti plastiği çatlatmadan, yüzeyle aynı hizaya yerleştir; soğuyunca uygun kısa vidayla dişin açık kaldığını kontrol et. Rulman ve kapaklı yuva testinde metal basma burcunun yalnız iç bileziğe bastığını doğrula. Delik dar çıkarsa tam boy parçayı zorlamak yerine ölçülen sapmayı kaydet; CAD veya dilimleyici telafisi birlikte değerlendirilecek.

Bu kupon motor yıldızı/kablosu, dayanım, tam kol hareketi ve meyve tutuşunu doğrulamaz. Bunlar gerçek parçalarla ayrıca kontrol edilir.
''',encoding='utf-8')
    (dest/'COUPON_DIMENSIONS.json').write_text(json.dumps(specs,indent=2),encoding='utf-8')
    with zipfile.ZipFile(OUT/'00_UYUM_DENEMESI.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(dest.iterdir()):z.write(p,p.name)
    print('Fit coupon valid/watertight; actual bearing section and cap exported')

if __name__=='__main__':build()
