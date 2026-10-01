"""One stable delivery directory for prints, CAD, purchasing and installed tools."""
import argparse,hashlib,json,shutil,subprocess,sys,zipfile
from datetime import datetime,timezone
from scripts.project_paths import ROOT,CURRENT,PRINTS,CAD,SOFTWARE,ARCHIVE
from scripts.publication_lock import publication_lock

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def snapshot_before_rebuild():
    files=sorted(p for p in CURRENT.rglob('*') if p.is_file())
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    prefix='GUNCEL_ONCEKI/'+stamp+'/'
    ARCHIVE.parent.mkdir(exist_ok=True)
    hashes={p.relative_to(CURRENT).as_posix():digest(p) for p in files}
    with zipfile.ZipFile(ARCHIVE,'a',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
        for p in files:z.write(p,prefix+p.relative_to(CURRENT).as_posix())
        z.writestr(prefix+'SNAPSHOT_SHA256.json',json.dumps(hashes,indent=2))
    with zipfile.ZipFile(ARCHIVE) as z:
        for rel,h in hashes.items():
            if hashlib.sha256(z.read(prefix+rel)).hexdigest()!=h:raise RuntimeError('Snapshot verification failed: '+rel)

def run(module,*args):subprocess.run([sys.executable,'-m',module,*args],cwd=ROOT,check=True)

def main():
    with publication_lock(ARCHIVE.with_suffix('.publication.lock')):
        _publish_locked()


def _publish_locked():
    parser=argparse.ArgumentParser();parser.add_argument('--rebuild-cad',action='store_true');parser.add_argument('--install-twin',action='store_true');parser.add_argument('--so101-shopping',action='store_true');parser.add_argument('--so101-print',action='store_true');parser.add_argument('--so101-slicer',action='store_true');parser.add_argument('--servo-test',action='store_true');parser.add_argument('--so101-assembly',action='store_true');parser.add_argument('--android-app',action='store_true');parser.add_argument('--aruco-label',action='store_true');args=parser.parse_args()
    if args.aruco_label:
        if any(value for key,value in vars(args).items() if key != 'aruco_label'):parser.error('--aruco-label must be used alone')
        from scripts.build_aruco_label import publish
        publish();return
    if args.android_app:
        if any(value for key,value in vars(args).items() if key != 'android_app'):parser.error('--android-app must be used alone')
        from scripts.publish_servo_test import publish
        publish(android_apk=True);return
    if args.so101_assembly:
        if any([args.rebuild_cad,args.install_twin,args.so101_shopping,args.so101_print,args.so101_slicer,args.servo_test]):parser.error('--so101-assembly must be used alone')
        from scripts.build_so101_assembly_guide import publish
        publish();return
    if args.servo_test:
        if any([args.rebuild_cad,args.install_twin,args.so101_shopping,args.so101_print,args.so101_slicer]):parser.error('--servo-test must be used alone')
        from scripts.publish_servo_test import publish
        publish();return
    if args.so101_slicer:
        if any([args.rebuild_cad,args.install_twin,args.so101_shopping,args.so101_print]):parser.error('--so101-slicer must be used alone')
        from scripts.publish_so101_slicing import publish
        publish();return
    if args.so101_shopping:
        if args.rebuild_cad or args.install_twin or args.so101_print:parser.error('--so101-shopping cannot be combined with CAD publication')
        from scripts.build_so101_shopping import publish
        publish();return
    status_path=CURRENT/'SURUM.json'
    so101_active=status_path.exists() and json.loads(status_path.read_text(encoding='utf-8')).get('model')=='SO-101 follower'
    if args.so101_print or so101_active:
        if args.install_twin:parser.error('SO-101 active; cannot publish obsolete LINKA twin delivery')
        from scripts.package_so101 import publish
        publish();return
    active=CAD/'TUTUCU/STATUS.json'
    twin=active.exists() and json.loads(active.read_text()).get('revision')=='DEC-086'
    if args.install_twin or twin:
        from scripts.publish_twin_scoop import install,refresh
        if args.rebuild_cad:
            run('scripts.audit_twin_scoop');run('scripts.export_twin_scoop')
        if args.install_twin or args.rebuild_cad:install()
        refresh();return
    if args.rebuild_cad:
        snapshot_before_rebuild()
        run('cad.prototype_arm.export_linka_v1','--render')
        run('scripts.validate_linka_v1')
    tripod_layout=(CAD/'TUTUCU/PRINT_LAYOUT.json').exists()
    if not tripod_layout:
        run('scripts.package_linka_plates')
        run('scripts.release_linka_cable_exit')
        run('scripts.package_plastic_bushings')
    else:
        run('scripts.package_tripod_plates')
        run('scripts.qa_tripod_plates')
    models=ROOT/'viewer/public/models/guncel';models.mkdir(parents=True,exist_ok=True)
    for p in CAD.glob('*.glb'):shutil.copy2(p,models/p.name)
    status=json.loads((CAD/'RELEASE_STATUS.json').read_text(encoding='utf-8'))
    status.update(current_directory='GUNCEL',print_directory='GUNCEL/BASKI',cad_directory='GUNCEL/CAD',viewer_url='http://127.0.0.1:5173/kol.html',archive='ARSIV/ESKI_SURUMLER.zip')
    review=CAD/'TUTUCU/STATUS.json'
    if review.exists():status['design_review']=json.loads(review.read_text(encoding='utf-8'))
    if tripod_layout:
        status.update(revision='DEC-085 / TABLA-02',print_layout_available=True,physical_approval=False)
        status['rod_joint']=json.loads((CAD/'CUBUK_MAFSALI/STATUS.json').read_text())
    (CURRENT/'SURUM.json').write_text(json.dumps(status,indent=2,ensure_ascii=False),encoding='utf-8')
    (CURRENT/'BASLA_BURADAN.md').write_text('''# FIGBOT — güncel dosyalar

Bu klasörün adı değişmez. Sürüm numarası SURUM.json içindedir.

- BASKI: numaralandırılmış tabla klasörleri; her klasörde3MF, alternatifSTL ve önizleme vardır.
- CAD: güncel STEP, STL, montaj, URDF ve teknik raporlar.
- ALISVERIS: hırdavatçıya verilecek A4PDF ve malzeme verisi.
- YAZILIM: son eldeki uygulama/firmware dosyaları. Mevcut LINKA mekanizmasına firmware uyumu onaylanmış değildir; klasördeki notu oku.

Önce basılmış parçaların tamamını tekrar basma. L1.1 sonrası motor tablası, L1.2 sonrası yalnız kablo açıklıklı alt taban değişti. Kablo7×3,9×5,5mm ölçüldü; gövde altından konumu henüz doğrulanmadı. L1.4 üç parmağın pivot deliğini değiştirdi ve6 plastik burç ekledi. L1.5 üç parmağı10mm uzatıp kepçe biçiminde genişletir;05 TPU astarlar da yenilenir. L1.4 sonrası yalnız04A ve05 yeni baskı gerektirir; tam04 ile04A birlikte basılmaz. Plastik burçlar yüksüz uyum denemesidir, yüklü çalışma onayı değildir.

Önceki sürümler ../ARSIV/ESKI_SURUMLER.zip içinde eski yollarıyla saklanır; baskıyı oradan başlatma. Kaynaklar proje içindeki cad, scripts, software, firmware vb. geliştirme klasörlerindedir.
''',encoding='utf-8')
    (PRINTS/'ONCE_BUNU_OKU.md').write_text('''# Güncel baskı klasörü — sabit yol

Tam baskı için01,02,03,04,06 tablaları;05 yalnız yumuşak ped seçeneğidir. L1.4 basılıysa yalnız04A kepçe parmakları ve05 kavisli TPU astarlar yenilenir;06 burçları tekrar basma. L1.3 basılıysa06 burçlar da gerekir.00 küçük uyum denemesidir.

01A yalnız kablo açıklıklı alt taban;02A yalnız destekli motor tablasıdır. Bunlar tam01/02 paketlerindeki aynı parçaların tek başına basılabilir kopyalarıdır: ikisini birlikte basma.

3MF veya alternatifSTL kullan; ikisini birlikte içe aktarma. Ölçek%100. Destek, brim ve modifier ayarlarını dilim önizlemesinde kontrol et. Yeni tabanın kablo konumu hâlâ fiziksel kontrol ister. L1.4 plastik burç alternatifi geometri olarak hazırdır; sıkma, sürtünme, aşınma ve sünme fiziksel olarak doğrulanmadı. Burçları100% dolgu, en az3 duvar hedefiyle delik ekseni dik bas; gerçek dilim önizlemesini kontrol et.

Sürüm değişse de bu klasör ve dosya adları korunur. Güncel sürüm ../SURUM.json içindedir.
''',encoding='utf-8')
    SOFTWARE.mkdir(exist_ok=True)
    (SOFTWARE/'OKU.md').write_text('''# Elde bulunan son yazılım dosyaları

Motor kontrolAPK: öncekiHC05 v0.11. TarayıcıAPK: v0.6. UNO dosyaları öncekiV5 kalibrasyon firmware'idir.

Bu dosyaların taşınması yeni LINKA mekanizmasıyla uyumlu oldukları anlamına gelmez. LINKA kapalı çevrim bağlantı geometrisi için eski firmware uyumlu kabul edilmemiştir; motorları çalıştırmak üzere otomatik yükleme yapılmadı. Motor_Kontrolu.cmd mevcut masaüstü panelini açar.
''',encoding='utf-8')
    if review.exists():
        notice='# Yeni üç kepçeli tutucu — CAD incelemesi\n\nYeni ipsiz tutucu CAD/TUTUCU içindedir ve webde gösterilir. BASKI klasöründeki önceki L1.5 parçalar bu yeni tutucu değildir. Yeni mekanizmanın fiziksel kavrama ve baskı onayı henüz yoktur. CAD/TUTUCU/OKU.md dosyasını oku.\n\n'
        for target in [CURRENT/'BASLA_BURADAN.md',PRINTS/'ONCE_BUNU_OKU.md']:
            target.write_text(notice+target.read_text(encoding='utf-8'),encoding='utf-8')
    if tripod_layout:
        from scripts.package_tripod_plates import delivery_notes
        delivery_notes()
    records=[{'path':p.relative_to(CURRENT).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(CURRENT.rglob('*')) if p.is_file() and p.name!='DOSYA_LISTESI.json']
    (CURRENT/'DOSYA_LISTESI.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print(json.dumps({'current':str(CURRENT),'files':len(records),'revision':status['revision']}))

if __name__=='__main__':main()
