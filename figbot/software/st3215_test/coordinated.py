"""Concurrent pose motion using Feetech SDK SyncWritePosEx register layout.

One broadcast starts every participating joint; the servo firmware performs
the acceleration ramps. Waypoints are dispatched by the existing serial worker,
without per-joint waits or a second COM owner. This is joint-space motion, not
Cartesian straight-line or collision planning.
"""
import math
from .protocol import BusError

# Manufacturer SyncWritePosEx example: speed3400, acceleration up to150.
# https://www.waveshare.com/wiki/ST3215_Servo
# Numeric maxima; zero/unlimited is deliberately not used for a loaded arm.
MAX_SPEED = 3400
MAX_ACCELERATION = 150
DEFAULT_SECONDS = .25


def profiles_for(start, target, requested_seconds, max_acceleration=MAX_ACCELERATION):
    if type(max_acceleration)!=int or not 1<=max_acceleration<=MAX_ACCELERATION:
        raise BusError('Motor ivme sınırı geçersiz.')
    if type(requested_seconds) not in (int, float) or not math.isfinite(requested_seconds) or not .25 <= requested_seconds <= 10:
        raise BusError('Hareket süresi 0.25–10 saniye olmalı.')
    distances = {i: abs(p-start[i]) for i, p in target.items() if p != start[i]}
    longest = max(distances.values(), default=0)
    # Minimum-time rest-to-rest triangle, or a trapezoid when speed saturates.
    # Time-scale the shared shape for slower requests and shorter joint travel.
    # STS acceleration unit = 100 counts/s². Never use zero (unlimited).
    acceleration = max_acceleration*100
    peak = min(MAX_SPEED, math.sqrt(longest*acceleration))
    fastest = longest/peak + peak/acceleration if peak else 0
    duration = max(requested_seconds, fastest)
    profiles = {}
    for i, d in distances.items():
        ratio=d/longest;scale=fastest/duration
        speed = max(1, min(MAX_SPEED, round(peak*ratio*scale)))
        acc = max(1, min(max_acceleration, round(max_acceleration*ratio*scale*scale)))
        profiles[i] = (target[i], speed, acc)
    return duration, profiles


def validate_waypoints(waypoints, initial, envelopes, max_acceleration=MAX_ACCELERATION, *, continuous=False):
    maximum=128 if continuous else 24
    if not isinstance(waypoints, list) or not 1 <= len(waypoints) <= maximum:
        raise BusError(f'1–{maximum} duruş gerekli.')
    previous = dict(initial); result = []; total = 0
    for item in waypoints:
        if not isinstance(item, dict) or not isinstance(item.get('positions'), dict) or not item['positions']:
            raise BusError('Her duruş motor konumlarını içermeli.')
        pose = dict(previous)
        for key, p in item['positions'].items():
            if str(key) not in ('1','2','3','4','5','6') or type(p) != int or not 0 <= p <= 4095:
                raise BusError('Motor ID/ham konum geçersiz.')
            i = int(key)
            if p != previous[i]:
                low, high = envelopes[i]
                if not low <= previous[i] <= high and abs(p-previous[i]) <= 20:
                    # A passive held joint may be outside its motion envelope.
                    # Retain it without transmitting any new target to that ID.
                    pose[i] = previous[i]
                    continue
                if not low <= previous[i] <= high or not low <= p <= high:
                    raise BusError(f'ID{i}: doğrulanmış oturum aralığı dışında hareket.')
                if abs(p-previous[i]) > 1024:
                    raise BusError('Bir duruş geçişi 90 dereceyi aşamaz.')
            pose[i] = p
        duration, _ = profiles_for(previous, pose, item.get('seconds', DEFAULT_SECONDS),max_acceleration)
        dwell = item.get('dwell', 0)
        if type(dwell) not in (int, float) or not math.isfinite(dwell) or not 0 <= dwell <= 2:
            raise BusError('Bekleme 0–2 saniye olmalı.')
        result.append({'positions': pose, 'seconds': duration, 'dwell': dwell})
        for flag in ('goal_midpoint','goal_stop'):
            if flag in item:
                if type(item[flag]) is not bool:raise BusError('Doğrudan hedef düğüm işareti geçersiz.')
                result[-1][flag]=item[flag]
        if item.get('goal_midpoint') and item.get('goal_stop'):
            raise BusError('Geçiş düğümü aynı zamanda duruş olamaz.')
        if 'release_gate' in item:
            if type(item['release_gate']) is not bool:
                raise BusError('Bırakma konumu doğrulama işareti geçersiz.')
            result[-1]['release_gate']=item['release_gate']
        if 'release_lead_seconds' in item:
            lead=item['release_lead_seconds']
            if not item.get('release_gate') or type(lead) not in (int,float) or not math.isfinite(lead) or not 0<lead<=.25:
                raise BusError('Yaklaşmada açılma payı 0–0.25 saniye ve bırakma işareti gerektirir.')
            result[-1]['release_lead_seconds']=lead
        if 'stream_seconds' in item:
            timing=item['stream_seconds']
            if type(timing) not in (int,float) or not math.isfinite(timing) or not (.02 if continuous else .25)<=timing<=10:
                raise BusError('Sürekli yol zamanlaması izin verilen aralıkta değil.')
            result[-1]['stream_seconds']=timing
        total += item.get('stream_seconds',duration)+dwell if continuous else duration+dwell+1.5
        previous = pose
    if total > 55:
        raise BusError('Çevrim zaman bütçesi 55 saniyeyi aşıyor.')
    return result


class CoordinatedMotion:
    def move_pose(self, positions, seconds, camera_fresh):
        return self.play_sequence([{'positions': positions, 'seconds': seconds}], camera_fresh)

    def play_sequence(self, waypoints, camera_fresh, *, taught_envelopes=None):
        start,plan=self._prepare_plan(waypoints,camera_fresh,taught_envelopes)
        self._start_coordinated(plan, start, 1)

    def _prepare_plan(self, waypoints, camera_fresh, taught_envelopes=None, *, continuous=False):
        if self.state != 'HOLDING' or not camera_fresh:
            raise BusError('Hareket için sabit tutma ve güncel kamera gerekli.')
        try:
            rows = self.read_all(); self.validate_rows(rows)
            if any(r['torque'] != 1 or abs(r['speed']) > 50 or abs(r['position']-self.targets[i]) > 32 for i,r in rows.items()):
                raise BusError('Başlangıç konumu sabit değil.')
        except Exception as exc:
            self.pause(str(exc), fault=True)
            raise
        start = {i:r['position'] for i,r in rows.items()}
        # LeRobot STS control table: factory Maximum_Acceleration is ONE byte
        # at85; byte86 is a distinct multiplier. Read limits, never overwrite.
        limits={i:self.bus.read(i,85,1)[0] for i in start}
        if any(not 1<=a<=254 for a in limits.values()):
            raise BusError('Motor maksimum ivme kaydı doğrulanamadı.')
        self.motion_acceleration_limit=min(MAX_ACCELERATION,*limits.values())
        self.hardware_acceleration_limits=limits
        # Validate the ENTIRE program before the first hardware write.
        # A measured home route may have a local envelope; jog/XYZ limits stay
        # unchanged. Keep this snapshot with the running program only.
        self.motion_envelopes = dict(self.envelopes if taught_envelopes is None else taught_envelopes)
        plan = validate_waypoints(waypoints, start, self.motion_envelopes,self.motion_acceleration_limit,continuous=continuous)
        return start,plan

    def _start_coordinated(self, plan, start, index):
        item = plan[0]; target = item['positions']
        duration, profiles = profiles_for(start, target, item['seconds'],self.motion_acceleration_limit)
        self.active = dict(kind='sync_pose', start=start, target=target,
                           joints=list(profiles), deadline=self.clock()+duration+1.5,
                           seconds=duration, remaining=plan[1:], index=index, dwell=item['dwell'])
        self.targets = dict(target); self.state = 'MOVING'; self.settled_at = None
        self.passive_drift_count = {i:0 for i in start}
        try:
            if profiles:
                self.bus.sync_goal(profiles)
                # Broadcast has no ACK. Independently verify each register block.
                for i,(p,v,a) in profiles.items():
                    expected = bytes([a])+p.to_bytes(2,'little')+b'\0\0'+v.to_bytes(2,'little')
                    actual = self.bus.read(i,41,7)
                    if actual != expected:
                        self.last_sync_mismatch = {'joint':i,'expected':expected.hex(),'actual':actual.hex(),
                                                   'profiles':profiles,'time':self.clock()}
                        raise BusError(f'ID{i}: eşzamanlı hedef geri okuması uyuşmuyor; beklenen={expected.hex()}, okunan={actual.hex()}.')
            self.message = f'Eşzamanlı duruş {index}: {len(profiles)} motor birlikte hareket ediyor.'
        except Exception as exc:
            self.pause(str(exc), fault=True)
            raise

    def _poll_coordinated(self, rows):
        active = self.active
        if self.clock() > active['deadline'] + active['dwell']:
            raise BusError('Eşzamanlı hareket zamanında tamamlanmadı.')
        settled = True
        for i,r in rows.items():
            if r['torque'] != 1:
                raise BusError(f'ID{i}: konum tutma kayboldu.')
            start, target = active['start'][i], active['target'][i]
            if i in active['joints']:
                if not min(start,target)-32 <= r['position'] <= max(start,target)+32:
                    raise BusError(f'ID{i}: hareket aralığı dışına çıktı.')
            else:
                drift = abs(r['position']-target)>32 or abs(r['speed'])>100
                self.passive_drift_count[i] = self.passive_drift_count[i]+1 if drift else 0
                if self.passive_drift_count[i] >= 3:
                    raise BusError(f'ID{i}: sabit eklem sapması sürdü.')
            settled &= abs(r['position']-target)<=20 and abs(r['speed'])<=50 and not r['moving']
        if not settled:
            self.settled_at = None
            return
        if self.settled_at is None:
            self.settled_at = self.clock()
        if self.clock()-self.settled_at < active['dwell']:
            return
        if active['remaining']:
            start = {i:r['position'] for i,r in rows.items()}
            # Revalidate from actual feedback, including any tracking error.
            plan = validate_waypoints(active['remaining'], start, self.motion_envelopes,self.motion_acceleration_limit)
            self._start_coordinated(plan, start, active['index']+1)
        else:
            self.active = None; self.state = 'HOLDING'
            self.message = 'Eşzamanlı hareket tamamlandı; konum korunuyor.'
