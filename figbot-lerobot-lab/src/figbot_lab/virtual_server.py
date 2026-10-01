"""Local-only virtual leader UI and guarded real-arm adapter."""
from __future__ import annotations
import argparse
import json
import mimetypes
import secrets
import threading
import time
import webbrowser
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen
from .common import ROOT, new_run, save_json, load_json, current_scene_task
from .virtual_motion import MotionBus, MotionController, MotorOverheat, load_profile, _EMERGENCY_TORQUE_OFF
from ._reference_protocol import MotorStatusError


class Application:
    def __init__(self):
        self.lock = threading.RLock()
        self.token = secrets.token_urlsafe(32)
        self.server_session = secrets.token_hex(8)
        self.state_revision = 0
        hardware_path = ROOT / 'configs/virtual_leader.hardware.json'
        self.hardware = load_json(hardware_path) if hardware_path.exists() else {}
        self.active_ids = tuple(self.hardware.get('active_motor_ids', range(1, 7)))
        self.motion = MotionController(on_event=self.event, active_ids=self.active_ids)
        self.profile_note = 'Fiziksel eklem eşlemesi gerekli.'
        self.recording = None
        self.last_recording = None
        self.record_file = None
        self.record_count = 0
        self.last_sim_sequence = -1
        self.recent_events = deque(maxlen=120)
        self.last_fault = None
        reference = ROOT / 'configs/virtual_leader.trial_reference.json'
        self.trial_reference = load_json(reference).get('angles') if reference.exists() else None
        closed_home = ROOT / 'configs/virtual_leader.closed_home.json'
        self.closed_home = load_json(closed_home) if closed_home.exists() else None

    def event(self, event):
        self.recent_events.append(event)
        if event.get('kind') in ('fault', 'thermal_cutoff', 'emergency_torque_off'):
            self.last_fault = dict(event)
            try:
                evidence = new_run('virtual_leader_fault')
                self.last_fault['evidence'] = str(evidence)
                save_json(evidence / 'fault.json', {'fault': self.last_fault, 'recent_events': list(self.recent_events)})
            except OSError as exc:
                self.last_fault['evidence_error'] = str(exc)
        if self.record_file:
            self.record_file.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + '\n')
            self.record_file.flush()
            self.record_count += 1

    def state(self):
        self.state_revision += 1
        return {**self.motion.snapshot(), 'application': 'figbot-virtual-leader', 'token': self.token,
                'server_session': self.server_session, 'state_revision': self.state_revision, 'profile_note': self.profile_note,
                'recording': str(self.recording) if self.recording else None,
                'last_recording': str(self.last_recording) if self.last_recording else None,
                'record_count': self.record_count, 'suggested_trial_angles': self.trial_reference,
                'closed_home_angles': self.closed_home.get('closed_angles') if self.closed_home else None,
                'physical_home_available': bool(self.closed_home and self.hardware.get('closed_home_valid', True)),
                'hardware_task': self.hardware.get('task', 'PICK_AND_PLACE'),
                'hardware_replacement': self.hardware.get('replacement'),
                'last_fault': self.last_fault}

    def action(self, route, value):
        if route == 'connect':
            if self.motion.bus:
                raise ValueError('Önce mevcut bağlantıyı kapatın.')
            import serial
            from serial.tools import list_ports
            port = value.get('port')
            if port not in {p.device for p in list_ports.comports()}:
                raise ValueError('Seçilen seri port bağlı değil.')
            profile, note = load_profile() if len(self.active_ids) == 6 else (None, 'Beş motor · Kıskaç yok · Göreli eşleme gerekli.')
            connection = serial.Serial(port, 1000000, timeout=.02, write_timeout=.2)
            motion = MotionController(MotionBus(connection), profile, on_event=self.event, active_ids=self.active_ids)
            motion.manual_temperature_monitor = True
            try:
                motion.connect_snapshot()  # READ packets only
            except MotorStatusError as exc:
                motion.fault(exc)  # a reported hardware protection fault requires torque release
            except BaseException:
                connection.close()
                raise
            self.motion, self.profile_note = motion, note
            try:
                motion.check_manual_temperature(motion.rows)
            except MotorOverheat as exc:
                motion.emergency_torque_off(str(exc), thermal=True)
        elif route == 'activate':
            if not self.motion.profile or not self.motion.profile.verified:
                raise ValueError('Doğrulanmış fiziksel eşleme gerekli; deneme kontrolünü kullanın.')
            self.stop_record()  # do not mix simulated and powered actions in one session
            self.motion.activate()
        elif route == 'activate_trial':
            from .relative_motion import RelativeController, RelativeMotionBus, validate_angles
            from .calibration import read_settings
            angles = value.get('angles')
            validate_angles(angles)
            replacement = self.hardware.get('replacement', {})
            if replacement.get('status') == 'PENDING_PHYSICAL_ID_VERIFICATION':
                raise ValueError('ID6 → ID4 değişimi henüz fiziksel olarak doğrulanmadı. Önce motor iletişimi kurulmalı.')
            if self.motion.bus is None or self.motion.state != 'CONNECTED' and not self.motion.emergency_latched:
                raise ValueError('Deneme için önce poz okumayı açın.')
            self.stop_record()
            try:
                rows = self.motion.read_all(checked=False)
                self.motion.require_manual_cooling(rows)
                settings = read_settings(self.motion.bus, motor_ids=self.motion.active_ids) if len(self.motion.active_ids) != 6 else read_settings(self.motion.bus)
            except MotorStatusError as exc:
                self.motion.fault(exc)
                raise
            rows = self.motion.read_all(checked=False)
            trial_bus = RelativeMotionBus(self.motion.bus.serial) if isinstance(self.motion.bus, MotionBus) else self.motion.bus
            motion = RelativeController(trial_bus, settings,
                {i: r['position'] for i, r in rows.items()}, angles, on_event=self.event,
                home_reference=self.closed_home if len(self.motion.active_ids) == 6 and self.hardware.get('closed_home_valid', True) else None)
            motion.epoch = self.motion.epoch + 1
            self.motion = motion
            self.profile_note = f'UNVERIFIED: relative control, provisional +1 directions; hardware register bounds, direct targets, speed{motion.speed} accel{motion.acceleration}.'
            motion.activate()
        elif route == 'target':
            self.motion.input(value.get('angles'), value.get('epoch'), value.get('sequence'), value.get('gesture'))
        elif route == 'home':
            from .relative_motion import RelativeController
            if not self.hardware.get('closed_home_valid', True):
                raise ValueError('Motor değişti; gerçek kol için yeni kapalı poz kaydı gerekli. Eski bilek hedefi kullanılmaz.')
            if self.motion.state == 'CONNECTED' and not isinstance(self.motion, RelativeController):
                self.action('activate_trial', {'angles': value.get('angles')})
            if not isinstance(self.motion, RelativeController):
                raise ValueError('Başlangıca dönüş için mevcut pozdan kontrolü açın.')
            if self.motion.snapshot().get('connection_recovering'):
                raise ValueError('Motor yanıtı bekleniyor; bağlantı gelince kapalı poza dönebilirsiniz.')
            try:
                self.motion.home()
            except ValueError:
                raise  # invalid saved reference must not cause a motor write
            except Exception as exc:
                self.motion.fault(exc)
                raise
        elif route == 'hold':
            try:
                self.motion.hold()
            except Exception as exc:
                self.motion.fault(exc)
                raise
        elif route == 'stop':
            if self.motion.may_be_live:
                if self.motion.recover_read_timeouts:
                    self.motion.emergency_torque_off('Durdur düğmesine basıldı; motor torku kapatıldı.')
                else:
                    self.motion.fault('Durdur düğmesine basıldı.')
        elif route == 'emergency':
            self.stop_record()
            if self.motion.bus is None:
                import serial
                from serial.tools import list_ports
                port = value.get('port')
                if port not in {p.device for p in list_ports.comports()}:
                    raise ValueError('USB motor kartı bağlı değil. Motor beslemesini kapatın.')
                connection = serial.Serial(port, 1000000, timeout=.02, write_timeout=.2)
                self.motion = MotionController(MotionBus(connection), on_event=self.event, active_ids=self.active_ids)
                self.motion.manual_temperature_monitor = True
            if self.hardware.get('replacement', {}).get('status') == 'PENDING_PHYSICAL_ID_VERIFICATION':
                # The replacement may still answer ID6 until its rename succeeds.
                # This is an explicit release only; no gripper goal or torque-on.
                try:
                    self.motion.bus.disable_torque(6, authority=_EMERGENCY_TORQUE_OFF)
                    source_off = self.motion.bus.read(6, 40, 1) == b'\0'
                    self.event({'kind': 'pending_replacement_torque_release', 'motor': 6,
                                'confirmed': source_off, 'monotonic': time.monotonic()})
                except Exception as exc:
                    self.event({'kind': 'pending_replacement_torque_release', 'motor': 6,
                                'confirmed': False, 'message': str(exc), 'monotonic': time.monotonic()})
            self.motion.emergency_torque_off('Motor torkunu kapatma istendi.')
        elif route == 'disconnect':
            self.stop_record()
            self.motion.disconnect()
        elif route == 'record/start':
            if self.recording:
                raise ValueError('Kayıt zaten açık.')
            self.recording = new_run('virtual_leader')
            self.record_count, self.last_sim_sequence = 0, -1
            source = 'COMMANDED_MOTOR_ACTIONS' if self.motion.state == 'ACTIVE' else 'SIMULATION_ONLY'
            if self.motion.state == 'ACTIVE' and self.motion.snapshot()['control_mode'] == 'RELATIVE_TRIAL':
                source = 'COMMANDED_MOTOR_ACTIONS_RELATIVE_TRIAL'
            save_json(self.recording / 'session.json', {'source': source, 'task': current_scene_task(),
                      'camera_included': False, 'training_ready': False,
                      'physical_success': 'UNVERIFIED', 'settings': self.motion.settings,
                      'control_mode': self.motion.snapshot()['control_mode'],
                      'active_motor_ids': list(self.motion.active_ids),
                      'gripper_available': 6 in self.motion.active_ids,
                      'task_mode': self.hardware.get('task', 'PICK_AND_PLACE'),
                      'profile_sha256_or_note': self.profile_note,
                      'note': 'Joint control log only. Camera synchronization and reviewed success labels required for visual training.'})
            self.record_file = (self.recording / 'events.jsonl').open('w', encoding='utf-8')
            self.event({'kind': 'recording_start', 'monotonic': time.monotonic(), 'source': source})
        elif route == 'record/stop':
            self.stop_record()
        elif route == 'record/simulation':
            angles = value.get('angles')
            import math
            if (not isinstance(angles, list) or len(angles) != 6 or
                    any(type(v) not in (float, int) or not math.isfinite(v) for v in angles)):
                raise ValueError('Geçersiz simülasyon açıları.')
            sequence = value.get('sequence')
            if type(sequence) is not int or sequence <= self.last_sim_sequence:
                raise ValueError('Geçersiz simülasyon kayıt sırası.')
            if self.motion.state == 'ACTIVE':
                raise ValueError('Gerçek sürüş simülasyon kaydı olarak işaretlenemez.')
            self.last_sim_sequence = sequence
            self.event({'kind': 'simulation_pose', 'monotonic': time.monotonic(), 'angles': angles})
        else:
            raise ValueError('Bilinmeyen işlem.')
        return self.state()

    def stop_record(self):
        if self.record_file:
            self.event({'kind': 'recording_stop', 'monotonic': time.monotonic()})
            self.record_file.close()
            save_json(self.recording / 'summary.json', {'events': self.record_count, 'training_ready': False})
            self.last_recording = self.recording
        self.record_file = self.recording = None

    def close(self):
        with self.lock:
            self.motion.disconnect()
            self.stop_record()


def server_for(app, port=8890, directory=None):
    directory = Path(directory or ROOT / 'virtual-leader/dist').resolve()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def respond(self, code, value, kind='application/json; charset=utf-8'):
            data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def valid_host(self):
            return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

        def do_GET(self):
            if not self.valid_host():
                self.respond(403, {'error': 'Yerel adres gerekli.'})
                return
            route = urlsplit(self.path).path
            if route == '/api/state':
                with app.lock:
                    self.respond(200, app.state())
                return
            if route == '/api/ports':
                from serial.tools import list_ports
                self.respond(200, {'ports': [{'device': p.device, 'description': p.description}
                                             for p in list_ports.comports()]})
                return
            filename = (directory / unquote(route).lstrip('/')).resolve()
            if not filename.is_relative_to(directory):
                self.respond(403, {'error': 'Geçersiz dosya yolu.'})
                return
            if route == '/':
                filename = directory / 'index.html'
            if not filename.is_file():
                self.respond(404, {'error': 'Dosya bulunamadı.'})
                return
            self.respond(200, filename.read_bytes(), mimetypes.guess_type(filename)[0] or 'application/octet-stream')

        def do_POST(self):
            origins = {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}
            if (not self.valid_host() or self.headers.get('Origin') not in origins or
                    not secrets.compare_digest(self.headers.get('X-Figbot-Token', ''), app.token)):
                self.respond(403, {'error': 'Yerel oturum doğrulanamadı.'})
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 8192:
                    raise ValueError('İstek boyutu geçersiz.')
                if not self.headers.get('Content-Type', '').startswith('application/json'):
                    raise ValueError('JSON gerekli.')
                value = json.loads(self.rfile.read(size))
                if not isinstance(value, dict):
                    raise ValueError('JSON nesnesi gerekli.')
                route = urlsplit(self.path).path
                if not route.startswith('/api/'):
                    raise ValueError('Bilinmeyen işlem.')
                with app.lock:
                    state = app.action(route[5:], value)
                self.respond(200, state)
            except (ValueError, KeyError, TypeError, OSError, RuntimeError) as exc:
                self.respond(400, {'error': str(exc)})
            except Exception as exc:
                self.respond(400, {'error': str(exc)})

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8890)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    url = f'http://127.0.0.1:{args.port}'
    try:
        with urlopen(url + '/api/state', timeout=.5) as response:
            existing = json.load(response)
        if existing.get('application') == 'figbot-virtual-leader':
            print('FIGBOT sanal sürücü zaten açık:', url, flush=True)
            if not args.no_browser:
                webbrowser.open(url)
            return
    except (OSError, ValueError):
        pass
    if not (ROOT / 'virtual-leader/dist/index.html').exists():
        raise SystemExit('Arayüzü önce derleyin: cd virtual-leader && npm run build')
    app = Application()
    server = server_for(app, args.port)
    stop = threading.Event()

    def worker():
        while not stop.wait(.05):
            with app.lock:
                app.motion.tick()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}'
    print('FIGBOT sanal sürücü:', url, flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=.1)
    finally:
        stop.set()
        thread.join(timeout=1)
        app.close()
        server.server_close()


if __name__ == '__main__':
    main()
