import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from scripts.publish_servo_test import publish
from scripts import publish_current


class SoftwarePublishTests(unittest.TestCase):
    def test_android_dispatch_and_archive(self):
        with patch('sys.argv', ['publish_current', '--android-app']), patch('scripts.publish_servo_test.publish') as action:
            publish_current.main()
            action.assert_called_once_with(android_apk=True)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); current=root/'GUNCEL'; software=current/'YAZILIM'; archive=root/'ARSIV/ESKI_SURUMLER.zip'
            (root/'software/st3215_test').mkdir(parents=True)
            apk=root/'software/android/figbot-scanner/app/build/outputs/apk/debug/app-debug.apk'
            apk.parent.mkdir(parents=True); apk.write_bytes(b'new apk')
            software.mkdir(parents=True)
            (software/'FIGBOT_MOTOR_KONTROL.apk').write_bytes(b'old apk')
            with contextlib.redirect_stdout(io.StringIO()):
                publish(root,current,software,archive,android_apk=True)
            with zipfile.ZipFile(archive) as z:
                name=next(n for n in z.namelist() if n.endswith('FIGBOT_MOTOR_KONTROL.apk'))
                self.assertEqual(z.read(name), b'old apk')
            self.assertEqual((software/'FIGBOT_INCIR_TARAYICI.apk').read_bytes(), b'new apk')
            self.assertIn('0.14.0-pc-bridge',(software/'ANDROID_OKU.md').read_text(encoding='utf8'))
            self.assertIn('ST3215_TEST.pc_bridge',(software/'PC_Uzerinden_Toplama.cmd').read_text())
            guide=root/'software/android/figbot-scanner/ANDROID_OKU.md'
            guide.write_text('FIGBOT 0.22.0-aruco-calib',encoding='utf8')
            with contextlib.redirect_stdout(io.StringIO()):
                publish(root,current,software,archive,android_apk=True)
            self.assertEqual((software/'ANDROID_OKU.md').read_bytes(),guide.read_bytes())

    def test_software_only_archive_and_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'software/st3215_test'
            source.mkdir(parents=True)
            (source / 'app.py').write_text('print(1)')
            (source / 'OKU.md').write_text('guide')
            training=root/'ai/training'
            training.mkdir(parents=True)
            (training/'handguided_routes.py').write_text('# offline route generation')
            (source / 'so101_reference_calibration.json').write_text('{"status":"captured"}')
            (source / 'base_reference.json').write_text('{"status":"VERIFIED","new_offset":4080}')
            (source / 'cartesian_reference.json').write_text('{"status":"LOCAL_GEOMETRIC_ESTIMATE_SUPERVISED_VALIDATION"}')
            current = root / 'GUNCEL'
            software = current / 'YAZILIM'
            prints = current / 'BASKI'
            prints.mkdir(parents=True)
            (prints / 'TABLA.3mf').write_bytes(b'preserve current print')
            archive = root / 'ARSIV/ESKI_SURUMLER.zip'
            with contextlib.redirect_stdout(io.StringIO()):
                publish(root, current, software, archive)
            self.assertEqual((prints / 'TABLA.3mf').read_bytes(), b'preserve current print')
            self.assertEqual((software/'ST3215_TEST/IMITATION_TOOLS/handguided_routes.py').read_text(),
                             '# offline route generation')
            old = (software / 'ST3215_TEST/app.py').read_bytes()
            (source / 'app.py').write_text('print(2)')
            with contextlib.redirect_stdout(io.StringIO()):
                publish(root, current, software, archive)
            with zipfile.ZipFile(archive) as z:
                archived = [name for name in z.namelist() if name.endswith('/app.py')]
                self.assertEqual(len(archived), 1)
                self.assertEqual(z.read(archived[0]), old)
            records = json.loads((current / 'DOSYA_LISTESI.json').read_text())
            self.assertIn('BASKI/TABLA.3mf', [r['path'] for r in records])
            launcher = (software / 'ST3215_Motor_Test.cmd').read_text()
            self.assertIn('-m ST3215_TEST.app', launcher)
            self.assertIn('cd /d "%~dp0..\\.."', launcher)
            camera_launcher=(software/'Kol_Kamera_Konum.cmd').read_text()
            self.assertIn('.venv-camera\\Scripts\\pythonw.exe',camera_launcher)
            self.assertIn('-m ST3215_TEST.observe',camera_launcher)
            arm_launcher=(software/'Kol_Kontrollu_Surus.cmd').read_text()
            self.assertIn('-m ST3215_TEST.arm_console',arm_launcher)
            self.assertIn('.venv-camera\\Scripts\\pythonw.exe',arm_launcher)
            receiver_launcher=(software/'Telefon_Koordinat_Alici.cmd').read_text()
            self.assertIn('-m ST3215_TEST.target_receiver',receiver_launcher)
            self.assertTrue((software/'ST3215_TEST/so101_reference_calibration.json').exists())
            self.assertEqual(json.loads((software/'ST3215_TEST/base_reference.json').read_text())['new_offset'],4080)
            self.assertEqual(json.loads((software/'ST3215_TEST/cartesian_reference.json').read_text())['status'],'LOCAL_GEOMETRIC_ESTIMATE_SUPERVISED_VALIDATION')

    def test_cli_dispatches_only_software(self):
        with patch('sys.argv', ['publish_current', '--servo-test']), patch('scripts.publish_servo_test.publish') as action:
            publish_current.main()
            action.assert_called_once_with()

    def test_cli_rejects_mixed_publication(self):
        with patch('sys.argv', ['publish_current', '--servo-test', '--so101-slicer']), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                publish_current.main()
            self.assertEqual(error.exception.code, 2)
