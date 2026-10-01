"""Read the existing FIGBOT phone camera over a temporary USB ADB forward."""
from __future__ import annotations

import math
import subprocess
import time
import urllib.request

from .common import new_run, save_json


def adb(*arguments):
    result = subprocess.run(["adb", *arguments], capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise ValueError(f"ADB failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def phone_frame(url, opener=urllib.request.urlopen, clock=time.monotonic):
    import cv2
    import numpy as np
    began = clock()
    with opener(url, timeout=1) as response:
        data = response.read(2_000_001)
        headers = response.headers
    ended = clock()
    try:
        age = int(headers['X-Age-Ns']) / 1e9
        captured = int(headers['X-Capture-Ns'])
        generation = int(headers['X-Generation'])
        intrinsics = [float(v) for v in headers['X-Intrinsics'].split(',')]
        width, height = int(headers['X-Width']), int(headers['X-Height'])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('Invalid phone camera metadata') from exc
    if len(data) > 2_000_000 or not data.startswith(b'\xff\xd8') or not data.endswith(b'\xff\xd9'):
        raise ValueError('Phone returned invalid JPEG')
    roundtrip = ended - began
    if not math.isfinite(age) or not 0 <= roundtrip <= .25 or not 0 <= age <= .3 or age + roundtrip > .3:
        raise ValueError('Phone camera frame or USB transport is stale')
    if (captured <= 0 or generation < 0 or width <= 0 or height <= 0
            or len(intrinsics) != 4 or not all(map(math.isfinite, intrinsics))
            or intrinsics[0] <= 0 or intrinsics[1] <= 0):
        raise ValueError('Invalid phone camera metadata')
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None or image.shape[:2] != (height, width):
        raise ValueError('Decoded camera dimensions disagree with metadata')
    return data, image, {'capture_ns': captured, 'generation': generation, 'age_s': age,
                         'usb_roundtrip_s': roundtrip, 'pc_age_upper_s': age + roundtrip,
                         'intrinsics': intrinsics, 'pc_read_monotonic': ended,
                         'pc_capture_interval': [began - age, ended - age]}


def capture_phone(serial=None, seconds=5, on_frame=None):
    if not 0 < seconds <= 120:
        raise ValueError('Capture duration must be within (0,120] seconds')
    devices = [line.split()[0] for line in adb('devices').splitlines()[1:]
               if len(line.split()) >= 2 and line.split()[1] == 'device']
    if serial is None:
        if len(devices) != 1:
            raise ValueError('Connect one unlocked phone with USB debugging allowed, or use --serial')
        serial = devices[0]
    if serial not in devices:
        raise ValueError('Selected phone is disconnected or USB debugging is not authorized')
    # teaching_camera explicitly disables the installed app's motor connection UI.
    adb('-s', serial, 'shell', 'am', 'start', '-n', 'com.figbot.scanner/.KolActivity',
        '--ez', 'teaching_camera', 'true')
    port = adb('-s', serial, 'forward', 'tcp:0', 'tcp:8874')
    if not port.isdigit():
        raise ValueError('ADB did not return a temporary local port')
    frames, last_capture, generation = [], None, None
    run = None
    succeeded = False
    try:
        run = new_run('phone_camera')
        url = f'http://127.0.0.1:{port}/frame'
        deadline = time.monotonic() + 12
        last_error = None
        while time.monotonic() < deadline:
            try:
                _, _, initial_meta = phone_frame(url)
                break
            except (OSError, ValueError, KeyError) as error:
                last_error = str(error)
                time.sleep(.2)
        else:
            raise ValueError(f'Phone camera not ready. Keep the app visible and allow camera access. {last_error}')
        # Observer failures must propagate; do not retry or hide motor faults.
        if on_frame is not None:
            on_frame(initial_meta)
        generation = initial_meta['generation']
        last_capture = initial_meta['capture_ns']
        began = time.monotonic()
        while time.monotonic() - began < seconds:
            data, image, meta = phone_frame(url)
            if generation is not None and meta['generation'] != generation:
                raise ValueError('Phone camera session changed during capture')
            generation = meta['generation']
            if last_capture is not None and meta['capture_ns'] < last_capture:
                raise ValueError('Phone camera clock moved backwards')
            if on_frame is not None:
                on_frame(meta)
            if meta['capture_ns'] != last_capture:
                (run / f'frame_{len(frames):04d}.jpg').write_bytes(data)
                (run / 'latest.jpg').write_bytes(data)
                frames.append(meta)
                last_capture = meta['capture_ns']
            time.sleep(.08)
        if len(frames) < 3:
            raise ValueError('At least three distinct fresh phone images required')
        save_json(run / 'capture.json', {'source': 'FIGBOT_V37_USB_RAW_CAMERA', 'serial': serial,
                  'frames': len(frames), 'timing': frames, 'width': image.shape[1], 'height': image.shape[0],
                  'has_robot_state': False, 'motor_commands_sent': False})
        succeeded = True
        return run
    except BaseException as error:
        if run is not None:
            save_json(run / 'capture.json', {'status': 'FAILED', 'error': str(error),
                      'frames': len(frames), 'timing': frames, 'motor_commands_sent': False})
        raise
    finally:
        try:
            adb('-s', serial, 'forward', '--remove', f'tcp:{port}')
        except Exception as cleanup_error:
            if run is not None:
                save_json(run / 'cleanup_error.json', {'error': str(cleanup_error)})
            if succeeded:
                raise ValueError(f'Could not remove ADB camera forward tcp:{port}; evidence: {run}') from cleanup_error
