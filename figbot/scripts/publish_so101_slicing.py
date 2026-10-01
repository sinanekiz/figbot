"""Publish verified slicer output without altering original CAD or dimensions."""
import hashlib,json,shutil,zipfile
from datetime import datetime,timezone
from pathlib import Path
from scripts.project_paths import ROOT,CURRENT,PRINTS,ARCHIVE
from scripts.prepare_so101_slicer import WORK,PLATES,settings,GENERAL,ARM,FILAMENT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
README='''# Centauri Carbon 2 — ayarları kayıtlı SO-101 baskıları

Yazıcı: ELEGOO Centauri Carbon 2 Combo, fiziksel 0,4 mm nozzle.
Malzeme: kullanıcının PLA+ makarası, etiketi 210–235 °C; kullanıcı 225 °C'de iyi sonuç aldığını bildirdi.
Tabla: Textured PEI / A yüzü, 60 °C. Bu ayarlar başka nozzle veya malzeme için değildir.

## Aç ve bas

01_TABAN_OMUZ, 02_KOL_BILEK, 03_KISKAC klasörlerinin her birindeki TABLA.3mf dosyasını ElegooSlicer'da **proje olarak** aç.
Yalnız geometri içe aktarma seçeneğini kullanma; aksi hâlde ayarlar taşınmaz.
Konumlar, yönler, %100 ölçek, destek, brim, PLA+ ve yazıcı ayarları kayıtlıdır.
Uygulama tekrar dilimlemek isterse Plakayı dilimle; sonra Ön İzleme/Yazdır.
CANVAS'ta PLA+ takılı gerçek makara yuvasını seçmek makara konumuna bağlıdır; dosya tek malzeme kullanır.
USB bellek alternatifi: aynı klasörde ECC2_PLA225.gcode hazırdır. Aynı parçalar için 3MF ve G-code iki ayrı baskı değildir.
00 motor mastarı isteğe bağlıdır; zorunlu kol parçası değildir.

## Kaydedilen profiller

- FIGBOT Genel Kalite 0.20 - CC2 0.4: 3 duvar, %20 gyroid, destek kapalı. Gelecek günlük işler için başlangıç profili; her farklı modelin desteği ayrı değerlendirilir.
- FIGBOT SO101 PLA+ 0.20 - CC2 0.4: 4 duvar, %25 gyroid, 5 alt/üst katman, 0,20 mm katman.
- FIGBOT PLA+ 225C - CC2: ilk ve diğer katmanlar 225 °C; 60 °C tabla; 10 mm³/sn hacimsel sınır.
- Kol destekleri: Normal/Otomatik + Snug, 45°, üst/alt Z boşluğu 0,20 mm, XY boşluğu 0,35 mm, 3 üst arayüz katmanı; 5 mm dış brim. Raft ve prime tower kapalı.
- Dış duvar 60, iç duvar 100, üst yüzey 50, ilk katman 30 mm/sn. İlk katman ivmesi 500, dış duvar 1500 mm/sn².

Normal destek bu parçalarda ağaç destekten daha az malzeme kullandı; ağaç desteğin tabandaki dal hatası nedeniyle normal destek seçildi.
Delik/yuva içindeki sökülebilir destek artıklarını montajdan önce temizle. Motoru veya vidayı zorlayarak sokma.

## Doğrulama sınırı ve kullanım

Gerçek ElegooSlicer 1.5.3.5 ile dört tabla dilimlendi; takım yolu sınırları, profil/nozzle/sıcaklıklar ve katman görselleri incelendi.
OEM CC2 başlangıç/bitiş G-code'u korundu. Bu hazırlık fiziksel baskı, tolerans ve mukavemet testinin yerine geçmez.
Filament markası bilinmiyor; akış oranı 1 başlangıç değeridir, basınç ilerletme kalibrasyonu uydurulmadı ve kapalıdır.
PLA+ için sıcak haznede çalışma uyarısına dikkat et: hazneyi ayrıca ısıtma; üretici PLA havalandırma talimatını uygula.
Temiz A yüzü kullan, ilk katmanı izle; baskı tamamen soğuyunca brim/destekleri ayır.
İlk baskıdan sonra ölçü/ilk katman/yüzey sonucuna göre akış ve PA kalibrasyonu yapılabilir.
Yazıcıya gönderim veya fiziksel baskı başlatılmadı. Slicer maliyet alanı gerçek makara alış fiyatı değildir.

CAD ölçüleri ve STL'ler değişmedi. Önceki dosyalar ARSIV/ESKI_SURUMLER.zip içinde SHA256 doğrulamasıyla saklanır.
'''

def zip_plate(root,plate):
    with zipfile.ZipFile(root/(plate+'.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for p in (root/plate).rglob('*'):
            if p.is_file():z.write(p,p.relative_to(root))

def manifest():
    write(CURRENT/'DOSYA_LISTESI.json',[dict(path=p.relative_to(CURRENT).as_posix(),bytes=p.stat().st_size,sha256=sha(p))
        for p in sorted(CURRENT.rglob('*')) if p.is_file() and p.name!='DOSYA_LISTESI.json'])

def archive(paths):
    old=[p for p in paths if p.exists()]
    prefix='SO101_DILIMLEME_ONCESI/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'/'
    with zipfile.ZipFile(ARCHIVE,'a',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for p in old:z.write(p,prefix+p.relative_to(CURRENT).as_posix())
    with zipfile.ZipFile(ARCHIVE) as z:
        for p in old:assert hashlib.sha256(z.read(prefix+p.relative_to(CURRENT).as_posix())).hexdigest()==sha(p)

def publish():
    destinations=[PRINTS/'ONCE_BUNU_OKU.md',PRINTS/'DILIMLEME_KONTROL.json',CURRENT/'SURUM.json']
    destinations.extend(p for p in (PRINTS/'PROFILLER').rglob('*') if p.is_file())
    mapping=[];results=[]
    for plate in PLATES:
        src=WORK/plate;dst=PRINTS/plate
        proof=json.loads((src/'KONTROL.json').read_text());results.append(proof)
        assert proof['plate']==plate and not (src/'cli.log').read_text().strip()
        for a,b in [('DILIMLENMIS.3mf','TABLA.3mf'),('plate_1.gcode','ECC2_PLA225.gcode'),
                    ('KONTROL.json','KONTROL.json'),('KATMAN_KONTROL.png','KATMAN_KONTROL.png')]:
            mapping.append((src/a,dst/b));destinations.append(dst/b)
        destinations.extend([dst/'OKU.md',PRINTS/(plate+'.zip')])
    archive(destinations)
    for src,dst in mapping:shutil.copy2(src,dst)
    shutil.copytree(WORK/'PROFILLER',PRINTS/'PROFILLER',dirs_exist_ok=True)
    # General blank project carries the everyday profile independently of the arm project.
    with zipfile.ZipFile(ROOT/'manufacturing/ecc2_slicer_template.3mf') as source:
        with zipfile.ZipFile(PRINTS/'PROFILLER/GENEL_BOS_PROJE.3mf','w',zipfile.ZIP_DEFLATED) as z:
            for n in source.namelist():
                z.writestr(n,json.dumps(settings(False)).encode() if n=='Metadata/project_settings.config' else source.read(n))
    for plate in PLATES:
        (PRINTS/plate/'OKU.md').write_text(f'# {plate}\n\nTABLA.3mf: ElegooSlicer projesi, bütün baskı ayarları içinde.\nECC2_PLA225.gcode: aynı tablanın doğrudan dosyası. İkisi alternatif, iki kez basma.\n\nCentauri Carbon 2 / 0,4 mm / PLA+ / 225 °C / Textured PEI A 60 °C.\nAyrıntılar ../ONCE_BUNU_OKU.md. STL yalnız geometri içindir; ayar taşımaz.\n',encoding='utf-8')
        zip_plate(PRINTS,plate)
    (PRINTS/'ONCE_BUNU_OKU.md').write_text(README,encoding='utf-8')
    report=dict(revision='DEC-089',slicer='ElegooSlicer 1.5.3.5',physical_approval=False,
        gui_preview_review=True,toolpath_bounds_verified=True,source_geometry_changed=False,
        material_brand='UNVERIFIED',user_nozzle_temperature=225,bed_surface='Textured PEI A',
        flow_and_PA_calibration='PHYSICAL VALIDATION REQUIRED',plates=results,
        stl_hashes={str(p.relative_to(PRINTS)):sha(p) for p in PRINTS.glob('*/TABLA.stl')})
    write(PRINTS/'DILIMLEME_KONTROL.json',report)
    status=json.loads((CURRENT/'SURUM.json').read_text(encoding='utf-8'))
    status.update(slicer_revision='DEC-089',slicer_profiles_embedded=True,printer_profile='CC2 0.4')
    write(CURRENT/'SURUM.json',status);manifest()
    print(json.dumps(report,ensure_ascii=False,indent=2))

def preserve_current(staged_prints):
    """A later CAD/package refresh must not silently remove verified machine settings."""
    path=PRINTS/'DILIMLEME_KONTROL.json'
    if not path.exists():return False
    report=json.loads(path.read_text(encoding='utf-8'))
    for rel,digest in report['stl_hashes'].items():
        if sha(staged_prints/rel)!=digest:
            raise RuntimeError('Geometry changed: re-slice and review before replacing current slicer projects')
    for plate in PLATES:
        for name in ['TABLA.3mf','ECC2_PLA225.gcode','KONTROL.json','KATMAN_KONTROL.png','OKU.md']:
            shutil.copy2(PRINTS/plate/name,staged_prints/plate/name)
        zip_plate(staged_prints,plate)
    for name in ['DILIMLEME_KONTROL.json','ONCE_BUNU_OKU.md']:shutil.copy2(PRINTS/name,staged_prints/name)
    shutil.copytree(PRINTS/'PROFILLER',staged_prints/'PROFILLER',dirs_exist_ok=True)
    return True

if __name__=='__main__':publish()
