"""Passive phone RGB + encoder demonstrations. Never sends position/enable commands.

Only --supported-release may disable torque after explicit user support. All
subsequent motor operations are reads. Stop leaves torque off; no auto-hold.
Phone export is opt-in localhost:8874 via adb forward, never a LAN service.
"""
import argparse
import json
import math
import time
import urllib.request
from pathlib import Path

from .arm_control import ArmControl
from .protocol import Bus, BusError
from .recording import SessionRecorder


class ReadOnlyTeachingBus(Bus):
    """Protocol-level guarantee: passive capture can transmit only servo READs."""
    def transact(self,servo_id,instruction,data=b'',response_size=None):
        if instruction!=2 or servo_id not in range(1,7):
            raise BusError('Passive demonstration bus rejects every non-read packet')
        return super().transact(servo_id,instruction,data,response_size)


def camera_sample(url, opener=urllib.request.urlopen, clock=time.monotonic):
    began=clock()
    with opener(url,timeout=1) as response:
        data=response.read(2_000_001);headers=response.headers
    ended=clock();age=int(headers['X-Age-Ns'])/1e9
    captured=int(headers['X-Capture-Ns']);generation=int(headers['X-Generation'])
    if len(data)>2_000_000 or not data.startswith(b'\xff\xd8') or not data.endswith(b'\xff\xd9'):
        raise ValueError('Invalid camera JPEG')
    if not math.isfinite(age) or age<0 or age>.3 or ended-began>.25:
        raise ValueError('Camera timing stale; do not begin demonstration')
    timing=dict(phone_capture_ns=captured,phone_generation=generation,
                request_start_monotonic=began,request_end_monotonic=ended,
                phone_frame_age_seconds=age,transport_uncertainty_seconds=(ended-began)/2,
                estimated_capture_monotonic=(began+ended)/2-age,
                intrinsics=[float(v) for v in headers['X-Intrinsics'].split(',')])
    return data,timing


def require_passive(rows):
    if set(rows)!=set(range(1,7)) or any(r['torque']!=0 for r in rows.values()):
        raise BusError('Six torque-off motor readings required; record stopped')
    ArmControl.validate_rows(rows)


def write_status(folder,**values):
    temporary=folder/'status.tmp'
    temporary.write_text(json.dumps(values,ensure_ascii=False,indent=2),encoding='utf-8')
    temporary.replace(folder/'status.json')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',default='COM5')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--camera',default='http://127.0.0.1:8874/frame')
    parser.add_argument('--supported-release',action='store_true')
    parser.add_argument('--check-only',action='store_true')
    parser.add_argument('--target',default='USER_DEMONSTRATION; target association pending')
    parser.add_argument('--seconds',type=int,default=480)
    args=parser.parse_args()
    import cv2
    import numpy as np
    import serial
    if args.output.exists():raise ValueError('New unique output directory required')
    args.output.mkdir(parents=True)
    recorder=None;stream=None;released=False;frames=0;last_capture=None;generation=None;last_time=None
    reason='STOPPED';observations=[]
    try:
        # Verify independent fresh images before any hardware write.
        for _ in range(5):
            data,timing=camera_sample(args.camera)
            if observations and timing['phone_capture_ns']<=observations[-1]:
                time.sleep(.12);continue
            observations.append(timing['phone_capture_ns']);time.sleep(.12)
        if len(observations)<3:raise ValueError('No fresh camera sequence; torque unchanged')
        with serial.Serial(args.port,1_000_000,timeout=.015,write_timeout=.18) as connection:
            bus_type=Bus if args.supported_release and not args.check_only else ReadOnlyTeachingBus
            control=ArmControl(bus_type(connection));rows=control.read_all();control.validate_rows(rows)
            if args.check_only:
                write_status(args.output,state='PREFLIGHT_OK',camera_frames=len(observations),rows=rows,motor_writes=False)
                return
            if args.supported_release:
                if any(r['moving'] or abs(r['speed'])>5 for r in rows.values()):
                    raise BusError('Arm must be stationary before supported release')
                if not control.release():raise BusError(control.message)
                released=True
            rows=control.read_all();require_passive(rows)
            started=time.monotonic();max_gap=0
            while time.monotonic()-started<args.seconds and not (args.output/'STOP').exists():
                loop=time.monotonic()
                rows_began=time.monotonic();rows=control.read_all();rows_ended=time.monotonic();require_passive(rows)
                if rows_ended-rows_began>.25:raise BusError('Encoder read span too large')
                data,timing=camera_sample(args.camera)
                if generation is not None and timing['phone_generation']!=generation:
                    raise ValueError('Camera session changed; start a new demonstration')
                generation=timing['phone_generation']
                if last_capture is not None and timing['phone_capture_ns']<=last_capture:
                    if time.monotonic()-last_time>.5:raise ValueError('Camera frames stopped advancing')
                    time.sleep(.01);continue
                now=time.monotonic();frame_at=timing['estimated_capture_monotonic']
                rows_at=(rows_began+rows_ended)/2
                if abs(frame_at-rows_at)>.2:raise ValueError('Camera/encoder alignment exceeds 200ms')
                frame=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
                motor_rows=[dict(id=i,ok=True,**row) for i,row in rows.items()]
                if recorder is None:
                    recorder=SessionRecorder(args.output/'episode',frame,frame_at,motor_rows,rows_at,now,max_seconds=args.seconds)
                    recorder.metadata.update(task='Pick figs by hand and place in container',target=args.target,
                        mode='PASSIVE_HAND_GUIDED',action_source='MEASURED_JOINT_TRAJECTORY; no leader actions',
                        camera_mount='USER_FIXED_NEXT_TO_ARM',camera_to_robot_calibration_required=False,
                        policy_trained=False,autonomous_replay_allowed=False,
                        joint_units='raw encoder counts; do not normalize using assumed offsets')
                    recorder._save_metadata()
                    (args.output/'initial.jpg').write_bytes(data)
                    stream=(args.output/'timing.jsonl').open('x',encoding='utf-8',buffering=1)
                recorder.add(frame,frame_at,motor_rows,rows_at,now)
                if last_time is not None:max_gap=max(max_gap,now-last_time)
                timing.update(frame_index=frames,encoder_read_start=rows_began,encoder_read_end=rows_ended,
                              camera_encoder_delta_seconds=frame_at-rows_at)
                stream.write(json.dumps(timing)+'\n');frames+=1;last_capture=timing['phone_capture_ns'];last_time=now
                (args.output/'latest.jpg').write_bytes(data)
                write_status(args.output,state='RECORDING',frames=frames,elapsed=now-started,max_gap=max_gap,
                             measured_hz=frames/(now-started) if now>started else 0,rows=rows,
                             torque_released=released,position_commands_sent=False)
                time.sleep(max(0,.1-(time.monotonic()-loop)))
    except Exception as error:
        reason='ABORTED: '+str(error)
        raise
    finally:
        if stream:stream.close()
        if recorder:recorder.close(reason)
        if not args.check_only:
            write_status(args.output,state=reason,frames=frames,torque_released=released,
                         position_commands_sent=False,automatic_reenable=False)


if __name__=='__main__':main()
