"""Local camera/telemetry session recording. No serial access or motor writes."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2


def validate_observation(frame, frame_at, rows, rows_at, now):
    if frame is None or now-frame_at > 2:
        raise ValueError('Kamera görüntüsü gelmiyor; kayıt durduruldu.')
    if now-rows_at > 2 or sorted(r.get('id', 0) for r in rows) != list(range(1, 7)):
        raise ValueError('Altı motorun güncel konumu gerekli; kayıt durduruldu.')
    if any(not r.get('ok') or r.get('torque') != 0 for r in rows):
        raise ValueError('Motor yanıtı eksik veya tork açık; elle hareketi durdur.')


class SessionRecorder:
    def __init__(self, directory, frame, frame_at, rows, rows_at, now=None,
                 writer_factory=None, max_seconds=480):
        now = time.monotonic() if now is None else now
        validate_observation(frame, frame_at, rows, rows_at, now)
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.started = now
        self.max_seconds = max_seconds
        self.closed = False
        self.index = 0
        self.last_frame_at = None
        self.last_fingerprint = None
        self.unchanged_since = now
        self.shape = frame.shape
        self.writer = None
        self.log = None
        self.metadata = {
            'started_utc': datetime.now(timezone.utc).isoformat(),
            'status': 'RECORDING', 'motion_commands_sent': False,
            'calibration_complete': False, 'limits_applied': False,
            'video': 'camera.avi', 'nominal_video_fps': 10,
            'timing': 'Use samples.jsonl elapsed/frame_index; camera and telemetry are asynchronous.',
            'requested_manual_order': [1, 2, 3, 4, 5, 6],
        }
        try:
            h, w = frame.shape[:2]
            self.writer = (writer_factory or cv2.VideoWriter)(
                str(self.directory/'camera.avi'), cv2.VideoWriter_fourcc(*'MJPG'), 10, (w, h))
            if not self.writer.isOpened():
                raise RuntimeError('Video dosyası açılamadı; harekete başlama.')
            self.log = (self.directory/'samples.jsonl').open('w', encoding='utf-8')
            self._save_metadata()
        except Exception:
            if self.writer is not None:
                self.writer.release()
            if self.log is not None:
                self.log.close()
            raise

    def _save_metadata(self):
        (self.directory/'session.json').write_text(
            json.dumps(self.metadata, ensure_ascii=False, indent=2), encoding='utf-8')

    def add(self, frame, frame_at, rows, rows_at, now=None):
        if self.closed:
            raise RuntimeError('Kayıt zaten kapalı.')
        now = time.monotonic() if now is None else now
        try:
            validate_observation(frame, frame_at, rows, rows_at, now)
            if frame.shape != self.shape:
                raise ValueError('Kamera çözünürlüğü değişti; kayıt durduruldu.')
            if now-self.started >= self.max_seconds:
                self.close('Süre sınırına ulaşıldı')
                return 'Kayıt tamamlandı (8 dakika sınırı).'
            if frame_at == self.last_frame_at:
                return 'Yeni kamera karesi bekleniyor.'
            fingerprint = hashlib.blake2b(frame.tobytes(), digest_size=8).hexdigest()
            if fingerprint != self.last_fingerprint:
                self.unchanged_since = now
            unchanged = now-self.unchanged_since
            self.writer.write(frame)
            self.log.write(json.dumps({
                'frame_index': self.index, 'elapsed_seconds': now-self.started,
                'recorded_utc': datetime.now(timezone.utc).isoformat(),
                'camera_age_seconds': now-frame_at,
                'telemetry_age_seconds': now-rows_at,
                'image_unchanged_seconds': unchanged,
                'possible_frozen_image': unchanged > 5,
                'motor_readings': rows,
            }, ensure_ascii=False)+'\n')
            self.log.flush()
            self.index += 1
            self.last_frame_at = frame_at
            self.last_fingerprint = fingerprint
            if unchanged > 5:
                return 'Görüntü değişmiyor: sabit sahne veya donma olabilir; hareket sırasında kontrol et.'
            return f'KAYIT AÇIK · {now-self.started:.0f} sn · {self.index} kare'
        except Exception:
            self.close('Kamera/konum doğrulaması veya dosya yazımı başarısız')
            raise

    def close(self, reason='Kullanıcı kaydı bitirdi'):
        if self.closed:
            return
        self.closed = True
        try:
            if self.writer is not None:
                self.writer.release()
        finally:
            if self.log is not None:
                self.log.close()
            self.metadata.update(status='CLOSED', reason=reason, frames=self.index,
                                 ended_utc=datetime.now(timezone.utc).isoformat())
            self._save_metadata()
