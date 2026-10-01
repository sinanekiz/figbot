"""Replay explicitly selected samples from a verified passive teaching file.

Ranges are local to this measured route, not global robot travel limits.
No automatic motor enabling, encoder wrapping, or geometric zero changes.
"""
import hashlib
import json
from pathlib import Path
from .protocol import BusError


def prepare_replay(plan_path, control):
    path=Path(plan_path);plan=json.loads(path.read_text(encoding='utf-8'))
    filename=plan['recording']
    if Path(filename).name!=filename or '/' in filename or '\\' in filename:
        raise BusError('Öğretme kaydı aynı klasörde olmalı.')
    raw=(path.parent/filename).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=plan['recording_sha256']:
        raise BusError('Öğretme kaydının özeti değişti.')
    records=[json.loads(line) for line in raw.decode('utf-8').splitlines()]
    header=records[0];end=records[-1]
    if header.get('event')!='start' or end.get('event')!='stop' or end.get('status')!='RECORDED_NOT_VALIDATED_FOR_REPLAY' or end.get('flags'):
        raise BusError('Öğretme kaydı tamamlanmamış veya inceleme bayrağı var.')
    summary=json.loads((path.parent/filename).with_suffix('.summary.json').read_text(encoding='utf-8'))
    if summary['status']!='RECORDED_NOT_VALIDATED_FOR_REPLAY':
        raise BusError('Öğretme kaydı kullanıcı tarafından geçersiz işaretlenmiş.')
    if header['offsets']!={str(i):v for i,v in control.offsets.items()}:
        raise BusError('Öğretme kaydı farklı kalibrasyon kullanıyor.')
    samples=[r for r in records if r.get('event')=='sample']
    if any(set(r['positions'])!={str(i) for i in range(1,7)} or any(t!=0 for t in r['torque'].values()) for r in samples):
        raise BusError('Öğretme kaydı altı serbest motoru içermeli.')
    def sample(index):
        if type(index)!=int or not 0<=index<len(samples):raise BusError('Öğretme örnek numarası geçersiz.')
        return samples[index]['positions']
    first=sample(plan['start_sample']);rows=control.read_all();control.validate_rows(rows)
    recovery=plan.get('recovery_start')
    if recovery is not None:
        if set(recovery)!={str(i) for i in range(1,7)} or any(type(v)!=int or not 0<=v<=4095 for v in recovery.values()):
            raise BusError('Dönüş başlangıcı geçersiz.')
        first=recovery
    if any(abs(r['position']-first[str(i)])>20 or abs(r['speed'])>50 for i,r in rows.items()):
        raise BusError('Kol kayıtlı tekrar başlangıcında değil.')
    if max(r['positions']['5'] for r in samples)-min(r['positions']['5'] for r in samples)>12:
        raise BusError('Bilek dönüşü bu kayıtta sabit değil; ayrı yol incelemesi gerekli.')
    envelopes={i:(max(0,min(r['positions'][str(i)] for r in samples)-20),
                  min(4095,max(r['positions'][str(i)] for r in samples)+20)) for i in range(1,7)}
    if plan.get('route_mode')=='direct_goals':
        if recovery is not None:raise BusError('Doğrudan hedef programı kapalı başlangıç gerektirir.')
        from .goal_route import build_goal_route
        spec=plan['goal_route']
        pose=lambda n:{int(i):v for i,v in sample(n).items()}
        waypoints,_=build_goal_route({i:r['position'] for i,r in rows.items()},pose(plan['start_sample']),
            pose(spec['pickup_sample']),pose(spec['basket_sample']),cycles=spec.get('cycles',2),
            speed_limit=spec.get('speed_limit',1200),acceleration=spec.get('acceleration',50),
            clearance_counts=spec.get('clearance_counts',64),release_lead=spec.get('release_lead',.18),
            opening_seconds=spec.get('opening_seconds',.56),
            home_joint_speed_limit=spec.get('home_joint_speed_limit',1000))
        return waypoints,envelopes
    if plan.get('route_mode') not in (None,'taught'):raise BusError('Bilinmeyen hedef planlayıcı.')
    waypoints=[]
    for item in plan['waypoints']:
        pose=dict(sample(item['sample']));pose['5']=rows[5]['position']
        if 'blend_toward_sample' in item:
            # Round only clearance poses toward the next demonstrated pose.
            # Pickup, release, wrist roll and jaw calibration stay untouched.
            target=sample(item['blend_toward_sample']);limit=item.get('blend_max_counts',32)
            if type(limit)!=int or not 1<=limit<=64:raise BusError('Geçiş yuvarlama payı 1–64 sayım olmalı.')
            if item.get('release_gate'):raise BusError('Bırakma duruşu yuvarlanamaz.')
            for key in ('1','2','3','4'):
                delta=round((target[key]-pose[key])*.25)
                pose[key]+=max(-limit,min(limit,delta))
        if 'gripper_sample' in item:
            # The same demonstrated open/closed jaw positions can overlap arm
            # travel on the return route; no invented jaw calibration values.
            pose['6']=sample(item['gripper_sample'])['6']
        waypoint=dict(positions=pose,seconds=.25,stream_seconds=item['stream_seconds'])
        if 'release_gate' in item:waypoint['release_gate']=item['release_gate']
        if 'release_lead_seconds' in item:waypoint['release_lead_seconds']=item['release_lead_seconds']
        waypoints.append(waypoint)
    if recovery is not None:
        # An explicitly requested recovery may join a nearby recorded sample;
        # it cannot jump to a distant part of the recording or enable motors.
        if any(rows[i]['torque']!=1 or not envelopes[i][0]<=first[str(i)]<=envelopes[i][1] or
               abs(waypoints[0]['positions'][str(i)]-first[str(i)])>192 for i in range(1,7)):
            raise BusError('Dönüş için yakın kayıtlı geçiş ve doğrulanmış tutma gerekli.')
    return waypoints,envelopes


def play_replay(plan_path,control,camera_fresh):
    waypoints,envelopes=prepare_replay(plan_path,control)
    kind=json.loads(Path(plan_path).read_text(encoding='utf-8')).get('curve_kind','pchip')
    control.play_smooth(waypoints,camera_fresh,taught_envelopes=envelopes,curve_kind=kind)
