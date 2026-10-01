"""Targeted software publication. Never rebuild or replace current prints."""
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from scripts.project_paths import ROOT, CURRENT, SOFTWARE, ARCHIVE


def publish(root=ROOT, current=CURRENT, software=SOFTWARE, archive=ARCHIVE, android_apk=False):
    source = root / 'software/st3215_test'
    target = software / 'ST3215_TEST'
    payloads = {target / p.name: p.read_bytes() for p in source.iterdir() if p.suffix in ('.py', '.md')}
    for name in ('handguided_data.py', 'handguided_routes.py', 'train_handguided_policy.py',
                 'requirements-handguided.txt'):
        tool = root / 'ai/training' / name
        if tool.exists():
            payloads[target / 'IMITATION_TOOLS' / name] = tool.read_bytes()
    for name in ('REFERANS_DURUS.png', 'REFERANS_DURUS.json', 'OLCUM_REHBERI.png'):
        if (source/name).exists(): payloads[target/name]=(source/name).read_bytes()
    model=root/'references/vendor/so101/Simulation/SO101/so101_new_calib.urdf'
    if model.exists(): payloads[target/'SO101_MODEL.urdf']=model.read_bytes()
    if android_apk:
        apk = root / 'software/android/figbot-scanner/app/build/outputs/apk/debug/app-debug.apk'
        payloads[software / 'FIGBOT_MOTOR_KONTROL.apk'] = apk.read_bytes()
        payloads[software / 'FIGBOT_INCIR_TARAYICI.apk'] = apk.read_bytes()
        payloads[software / 'ANDROID_OKU.md'] = (
            'FIGBOT 0.14.0-pc-bridge (versionCode 14)\n\n'
            'İki APK adı aynı birleşik uygulamayı içerir; birini kurmak yeterlidir.\n'
            'Telefon kamerası ve ARCore hedefleri ölçülmüş robot koordinatlarına çevirir.\n'
            'SO-101 için USB ST3215 protokolü, eşzamanlı hedef rotası, hız/izleme sınırları ve sabit kamera oturumu kapıları eklendi.\n'
            'Kavrama başarısı yalnız taşıma ve sepet içi yeni nesne görüntü kanıtıyla doğrulanır; kaybolan incir başarı sayılmaz.\n'
            '01: Telefon–OTG–motor kartı. 02: Eski Arduino/Bluetooth. 03: Telefon ve motor kartı ayrı USB kablolarıyla PC’ye bağlı.\n'
            '03 için önce PC_Uzerinden_Toplama.cmd dosyasını çalıştır, sonra telefonda PC üzerinden toplama ekranını aç > PC’ye bağlan.\n'
            'Kurulumun tamamı: ST3215_TEST/PC_ILE_TOPLAMA.md. Eski Telefon_Koordinat_Alici yalnız gözlem kaydı içindir; bu seçenek için açılmaz.\n'
            'İlk bağlantı yalnız okur. Hareket için fiziksel kol, kamera-zemin ve sepet ölçümleri uygulamada tamamlanmalıdır; değer uydurulmaz.\n'
            'Motor ekranı eski UNO/HC05 içindir; ayrıntılar: ST3215_TEST/TELEFON_KOORDINAT.md\n'
        ).encode('utf8')
        current_android_guide = root / 'software/android/figbot-scanner/ANDROID_OKU.md'
        if current_android_guide.exists():
            payloads[software / 'ANDROID_OKU.md'] = current_android_guide.read_bytes()
    # Both records are required together: the legacy display mapping and the
    # hand-supported SO-101 reference capture.  Publishing only one left the
    # current delivery unable to reproduce the calibration state.
    for calibration_name in ('so101_calibration.json', 'so101_reference_calibration.json', 'base_reference.json', 'cartesian_reference.json'):
        calibration = source / calibration_name
        if calibration.exists():
            payloads[target / calibration.name] = calibration.read_bytes()
    launcher = r'''@echo off
setlocal
cd /d "%~dp0..\.."
if not exist ".venv\Scripts\pythonw.exe" (
  echo Proje Python ortami bulunamadi. FIGBOT klasorunden calistirin.
  pause
  exit /b 1
)
set "PYTHONPATH=%CD%\GUNCEL\YAZILIM"
start "" ".venv\Scripts\pythonw.exe" -m ST3215_TEST.app
'''
    payloads[software / 'ST3215_Motor_Test.cmd'] = launcher.replace('\n', '\r\n').encode('ascii')
    payloads[software / 'Kol_Kamera_Konum.cmd'] = launcher.replace('-m ST3215_TEST.app','-m ST3215_TEST.observe').replace('.venv\\Scripts','.venv-camera\\Scripts').replace('\n','\r\n').encode('ascii')
    payloads[software / 'Kol_Kontrollu_Surus.cmd'] = launcher.replace('-m ST3215_TEST.app','-m ST3215_TEST.arm_console').replace('.venv\\Scripts','.venv-camera\\Scripts').replace('\n','\r\n').encode('ascii')
    receiver_launcher = '@echo off\ncd /d "%~dp0"\n"..\\..\\.venv-camera\\Scripts\\python.exe" -m ST3215_TEST.target_receiver\npause\n'
    payloads[software / 'Telefon_Koordinat_Alici.cmd'] = receiver_launcher.replace('\n','\r\n').encode('ascii')
    pc_launcher = '@echo off\nsetlocal\ncd /d "%~dp0"\n"..\\..\\.venv-camera\\Scripts\\python.exe" -m ST3215_TEST.pc_bridge %*\npause\n'
    payloads[software / 'PC_Uzerinden_Toplama.cmd'] = pc_launcher.replace('\n','\r\n').encode('ascii')
    payloads[target / 'SURUM.json'] = json.dumps({
        'revision': 'ST3215-TEST-3', 'date': '2026-09-19',
        'scope': 'single detached 12V ST3215 bench test',
        'adapter': 'Waveshare Bus Servo Adapter (A), identified by user description',
        'hardware_readback_validated': True, 'motion_hardware_validated': False, 'default_baud': 1000000,
        'travel_options_degrees': [60, 180, 270], 'default_travel_degrees': 270,
        'default_speed_profile': 'Maksimum',
        'maximum_profile_speed_register': 0, 'maximum_profile_acceleration_register': 0,
        'zero_semantics': 'maximum, not stop; position mode only',
        'numeric_speed_acceleration_register': 10,
        'source': 'software/st3215_test', 'launch': 'GUNCEL/YAZILIM/ST3215_Motor_Test.cmd'
        , 'arm_console': {
            'revision': 'SO101-SYNC-XYZ-20260920',
            'launch': 'GUNCEL/YAZILIM/Kol_Kontrollu_Surus.cmd',
            'guide': 'ST3215_TEST/AKICI_SURUS.md',
            'sync_backend': 'feetech-servo-sdk==1.0.0 GroupSyncWrite',
            'local_xyz_status': 'LOCAL_GEOMETRIC_ESTIMATE_SUPERVISED_VALIDATION',
            'camera_target_transform': 'UNVERIFIED',
            'empty_cycle_seconds_excluding_return': 10.47,
            'empty_cycle_seconds_including_return': 14.00,
            'physical_xyz_accuracy_verified': False
        }
    }, indent=2, ensure_ascii=False).encode('utf-8')
    changed = [p for p, data in payloads.items() if p.exists() and p.read_bytes() != data]
    if changed:
        archive.parent.mkdir(parents=True, exist_ok=True)
        prefix = 'YAZILIM_ONCEKI/' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '/'
        originals = {p: p.read_bytes() for p in changed}
        with zipfile.ZipFile(archive, 'a', zipfile.ZIP_DEFLATED) as z:
            for p, data in originals.items():
                z.writestr(prefix + p.relative_to(current).as_posix(), data)
        with zipfile.ZipFile(archive) as z:
            for p, data in originals.items():
                if hashlib.sha256(z.read(prefix + p.relative_to(current).as_posix())).digest() != hashlib.sha256(data).digest():
                    raise RuntimeError('Software archive verification failed: ' + str(p))
    for p, data in payloads.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        if p.read_bytes() != data:
            raise RuntimeError('Publication verification failed: ' + str(p))
    records = [{'path': p.relative_to(current).as_posix(), 'bytes': p.stat().st_size,
                'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
               for p in sorted(current.rglob('*')) if p.is_file() and p.name != 'DOSYA_LISTESI.json'
               and '__pycache__' not in p.parts]
    (current / 'DOSYA_LISTESI.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    print(json.dumps({'software': str(target), 'published_files': len(payloads)}, ensure_ascii=False))


if __name__ == '__main__':
    publish()
