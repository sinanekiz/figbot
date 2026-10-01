"""Supervised joint and coordinated-pose control; no collision safety claim.

All joints hold between jogs. Normal motion never writes EEPROM; the separately
invoked base_center maintenance operation records its coordinate change.
Hardware limits below are
session envelopes, deliberately narrower than the observed manual sweeps.
"""
import time
from dataclasses import asdict
from .protocol import BusError, BusTimeout, word
from .coordinated import CoordinatedMotion
from .smooth_path import SmoothMotion

IDS = tuple(range(1, 7))
# Base/roll do not cross encoder zero. ID2 uses the verified -813 offset.
ENVELOPES = {1:(2700,4090), 2:(850,3245), 3:(1810,4000),
             4:(773,2534), 5:(12,2050), 6:(780,2061)}
OFFSETS = {i:85 for i in IDS}
OFFSETS[2] = 2861
# The first hardware probes used a 5° / 5°s-like profile.  The arm now uses
# a deliberately bounded 10° increment with the documented 270°/s numeric
# profile; this remains below the firmware's unlimited (0, 0) profile.
JOG_DELTA = 114
JOG_SPEED = 3072
JOG_ACCELERATION = 10
MAX_TRANSIENT_FEEDBACK_ERRORS = 3
PASSIVE_POSITION_TOLERANCE = 32
PASSIVE_SPEED_TOLERANCE = 100


class ArmControl(CoordinatedMotion, SmoothMotion):
    def __init__(self, bus, clock=time.perf_counter):
        self.bus=bus; self.clock=clock; self.state='DISARMED'
        self.targets={}; self.rows={}; self.active=None; self.message='Motorlar etkin değil.'
        self.may_be_live=False; self.settled_at=None; self.ack_losses=0
        self.envelopes=dict(ENVELOPES)
        self.offsets=dict(OFFSETS);self.base_reference=None
        self.stop_check_at=None; self.start_check_at=None
        self.feedback_error_count=0
        self.passive_drift_count={i:0 for i in IDS}
        self.recovery_ids=()

    def disable_verified(self,i):
        for _ in range(3):
            try:self.bus.write(i,40,b'\0')
            except Exception:pass
            try:
                if self.bus.read(i,40,1)==b'\0':return True
            except Exception:pass
        return False

    def fail_stop(self,ids,reason):
        failed=[i for i in ids if not self.disable_verified(i)]
        self.active=None;self.stop_check_at=None
        self.state='FAULT_UNCONFIRMED' if failed else 'FAULT_STOPPED'
        self.message=reason+f' Torku kapatılan eklemler: {list(ids)}; doğrulanamayan: {failed}. Diğer eklemler tutabilir.'

    def goal_verified(self,i,p,speed=JOG_SPEED,acceleration=JOG_ACCELERATION):
        try:self.bus.goal(i,p,speed,acceleration)
        except BusTimeout:
            # No blind retry: a missing ACK may still mean the write applied.
            self.ack_losses+=1
            if self.ack_losses>2:raise BusError('Tekrarlanan yazma yanıt kaybı; bağlantı araştırılmalı.')
        expected=(bytes([acceleration])+p.to_bytes(2,'little')+b'\0\0'
                  +speed.to_bytes(2,'little'))
        if self.bus.read(i,41,7)!=expected:raise BusError(f'ID{i}: hedef/hız/ivme geri okuması uyuşmuyor.')

    def read_all(self):
        rows={}
        for i in IDS:
            if hasattr(self.bus,'feedback_state'):
                feedback,torque=self.bus.feedback_state(i)
                rows[i]=asdict(feedback);rows[i]['torque']=torque
            else:
                rows[i]=asdict(self.bus.feedback(i))
                rows[i]['torque']=self.bus.read(i,40,1)[0]
        self.rows=rows
        return rows

    @staticmethod
    def validate_rows(rows):
        for i,r in rows.items():
            if not 0<=r['position']<=4095 or not 10<=r['voltage']<=12.6 or r['temperature']>=55:
                raise BusError(f"ID{i}: geri bildirim geçersiz "
                               f"(konum={r['position']}, gerilim={r['voltage']}V, sıcaklık={r['temperature']}°C).")
            if abs(r['current_raw'])>150:
                raise BusError(f'ID{i}: deney akım eşiği aşıldı (ham değer; amper değildir).')

    def attach_existing_hold(self,camera_fresh):
        """Adopt an already torque-enabled, stationary servo chain without a write.

        This is used after the console process restarts.  It never changes a
        goal or torque state; it only accepts a stable existing hardware hold.
        """
        if self.state!='DISARMED' or not camera_fresh:
            raise BusError('Mevcut tutmayı devralmak için bağlı, güncel kamera gerekir.')
        rows=self.read_all(); self.validate_rows(rows)
        for i,r in rows.items():
            if word(self.bus.read(i,31,2))!=self.offsets[i]:
                raise BusError(f'ID{i}: kayıtlı ofset donanımla uyuşmuyor.')
            if r['torque']!=1 or abs(r['speed'])>50:
                raise BusError(f'ID{i}: mevcut tutma sabit değil.')
            goal=word(self.bus.read(i,42,2))
            if abs(goal-r['position'])>20:
                raise BusError(f'ID{i}: donanım hedefi mevcut konumdan uzak.')
        self.targets={i:r['position'] for i,r in rows.items()}
        self.may_be_live=True; self.state='HOLDING'; self.active=None
        self.feedback_error_count=0
        self.message='Mevcut motor konum tutması yazma yapmadan devralındı.'

    def resume_existing_hold(self,camera_fresh):
        """Clear a pause/fault latch only after a clean stationary readback."""
        if self.state not in ('PAUSED_HOLD','FAULT_HOLD') or not camera_fresh:
            raise BusError('Devam için korunmuş, güncel kamera görülmelidir.')
        rows=self.read_all(); self.validate_rows(rows)
        for i,r in rows.items():
            if r['torque']!=1 or abs(r['speed'])>50 or abs(r['position']-self.targets[i])>20:
                raise BusError(f'ID{i}: tutma devam için doğrulanamadı.')
        self.active=None; self.stop_check_at=None; self.feedback_error_count=0
        self.passive_drift_count={i:0 for i in IDS}
        self.state='HOLDING'; self.message='Geçerli geri bildirimle aynı konumdan devam ediliyor.'

    def recover_current_hold(self,camera_fresh):
        """Hold disabled joints in place while preserving verified existing holds.

        Reconnecting does not imply that hardware torque is off. Validate the
        complete chain before any write; never replay an old disabled-joint goal.
        On activation failure disable only joints this operation tried to enable.
        """
        if self.state!='DISARMED' or not camera_fresh:
            raise BusError('Mevcut duruşu tutmak için bağlı, güncel kamera gerekir.')
        rows=self.read_all();self.validate_rows(rows)
        disabled=[]
        for i,r in rows.items():
            if r['torque'] not in (0,1) or r['speed']!=0 or r['moving']:
                raise BusError(f'ID{i}: başlangıç duruşu sabit değil.')
            if self.bus.read(i,33,1)!=b'\0' or word(self.bus.read(i,3,2))!=777:
                raise BusError(f'ID{i}: model/mod uyuşmuyor.')
            if word(self.bus.read(i,31,2))!=self.offsets[i]:
                raise BusError(f'ID{i}: kalibrasyon ofseti değişmiş.')
            if r['torque']:
                if abs(word(self.bus.read(i,42,2))-r['position'])>20:
                    raise BusError(f'ID{i}: mevcut donanım hedefi konumdan uzak.')
            else:disabled.append(i)
        # Recheck after register inspection, before the first activation.
        fresh=self.read_all();self.validate_rows(fresh)
        if any(abs(fresh[i]['position']-r['position'])>8 or
               fresh[i]['speed']!=0 or fresh[i]['moving'] or
               fresh[i]['torque']!=r['torque'] for i,r in rows.items()):
            raise BusError('Tutmayı devralmadan önce kol durumu değişti.')
        self.targets={i:r['position'] for i,r in fresh.items()}
        if not self.base_reference:
            self.envelopes[1]=(0,1160) if fresh[1]['position']<=1160 else ENVELOPES[1]
        self.may_be_live=True;attempted=[]
        try:
            for i in disabled:
                if abs(self.bus.feedback(i).position-self.targets[i])>8:
                    raise BusError('Etkinleştirme öncesi serbest eklem oynadı.')
                attempted.append(i)  # A goal write itself may enable torque.
                self.goal_verified(i,self.targets[i],speed=57,acceleration=1)
                if self.bus.read(i,40,1)!=b'\1':
                    try:self.bus.write(i,40,b'\1')
                    except BusTimeout:pass
                if self.bus.read(i,40,1)!=b'\1':
                    raise BusError(f'ID{i}: tork açma doğrulanamadı.')
        except Exception:
            failed=[i for i in attempted if not self.disable_verified(i)]
            self.state='FAULT_UNCONFIRMED' if failed else 'FAULT_STOPPED'
            self.message=f'Tutma tamamlanamadı; mevcut tutan motorlar korundu. Doğrulanamayan: {failed}.'
            raise
        self.active=None;self.feedback_error_count=0;self.recovery_ids=tuple(disabled)
        self.passive_drift_count={i:0 for i in IDS}
        self.state='STARTING';self.start_check_at=self.clock()+.8
        self.message='Mevcut duruşta eksik tutma açıldı; hareketsizlik doğrulanıyor.'

    def arm(self, camera_fresh):
        if self.state!='DISARMED': raise BusError('Önce serbest bırak; otomatik yeniden etkinleştirme yok.')
        if not camera_fresh: raise BusError('Güncel kamera gerekli.')
        rows=self.read_all(); self.validate_rows(rows)
        # Manual base sweep crossed zero. Work only in the current raw branch;
        # never assume that firmware takes the short route across 4095/0.
        if not self.base_reference:
            self.envelopes[1]=(0,1160) if rows[1]['position']<=1160 else ENVELOPES[1]
        for i,r in rows.items():
            if r['torque']!=0 or r['speed']!=0: raise BusError('Başlangıçta bütün motorlar serbest ve sabit olmalı.')
            if self.bus.read(i,33,1)!=b'\0' or word(self.bus.read(i,3,2))!=777:
                raise BusError(f'ID{i}: model/mod uyuşmuyor.')
            if word(self.bus.read(i,31,2))!=self.offsets[i]: raise BusError(f'ID{i}: kalibrasyon ofseti değişmiş.')
            # Holding a manually placed, stationary pose writes back precisely
            # that measured pose.  It is not evidence that the pose is a
            # validated travel range, so jog() still enforces ENVELOPES.
        self.targets={i:r['position'] for i,r in rows.items()}
        # From the FIRST goal write onward, an ambiguous write may have applied.
        self.may_be_live=True
        try:
            for i in IDS:
                if abs(self.bus.feedback(i).position-self.targets[i])>8: raise BusError('Etkinleştirme öncesi kol oynadı.')
                # Observed firmware can enable torque on a goal write, so this
                # is already an activation, not a guaranteed passive preload.
                self.goal_verified(i,self.targets[i])
                if self.bus.read(i,40,1)!=b'\1':
                    try:self.bus.write(i,40,b'\1')
                    except BusTimeout:pass  # Independent read below is required.
                if self.bus.read(i,40,1)!=b'\1': raise BusError('Tork açma doğrulanamadı.')
            self.state='STARTING';self.start_check_at=self.clock()+.8
            self.message='Etkinleştirme sonrası gerçek hareketsizlik doğrulanıyor.'
        except Exception:
            self.release()
            raise

    def probe(self,joint,delta,camera_fresh):
        """Supervised calibration probe: at most 2 degrees, slow numeric profile."""
        if type(delta)!=int or not 1<=abs(delta)<=23:
            raise BusError('Yön denemesi en çok23 sayım olabilir.')
        return self.jog(joint,delta,camera_fresh,slow=True)

    def retreat_probe(self,joint,delta,camera_fresh):
        """Supervised return toward the recorded interval, never away or across zero."""
        if type(delta)!=int or not 1<=abs(delta)<=23:
            raise BusError('Aralığa dönüş denemesi en çok23 sayım olabilir.')
        return self.jog(joint,delta,camera_fresh,slow=True,retreat=True)

    def step(self,joint,delta,camera_fresh):
        if type(delta)!=int or not 1<=abs(delta)<=57:
            raise BusError('Yavaş adım en çok57 sayım olabilir.')
        return self.jog(joint,delta,camera_fresh,slow=True)

    def jog(self, joint, delta, camera_fresh,slow=False,retreat=False):
        if self.state!='HOLDING': raise BusError('Yeni adım için kol sabit tutma durumunda olmalı.')
        if not camera_fresh: raise BusError('Güncel kamera gerekli.')
        if type(joint)!=int or joint not in IDS or type(delta)!=int or not 1<=abs(delta)<=JOG_DELTA:
            raise BusError('Tek komut en fazla yaklaşık10 derece olabilir.')
        try:
            rows=self.read_all(); self.validate_rows(rows)
            if any(r['torque']!=1 or abs(r['position']-self.targets[i])>32 for i,r in rows.items()):
                raise BusError('Kol mevcut hedefini tutmuyor.')
        except Exception as e:
            self.pause(str(e),fault=True)
            raise
        target=rows[joint]['position']+delta
        start=rows[joint]['position']
        low,high=self.envelopes[joint]
        returning=(slow and retreat and abs(delta)<=23 and 0<=target<=4095 and
                   ((start>high and high<=target<start) or
                    (start<low and start<target<=low)))
        if not low<=target<=high and not returning:
            raise BusError('Deney aralığı/enkoder sıfırı geçilemez.')
        self.active=(joint,start,target,self.clock()+abs(delta)/JOG_DELTA+3)
        self.targets[joint]=target; self.state='MOVING'; self.settled_at=None
        try:
            self.goal_verified(joint,target,speed=57 if slow else JOG_SPEED,
                               acceleration=1 if slow else JOG_ACCELERATION)
        except Exception as e:
            self.pause(str(e),fault=True)
            raise

    def poll(self,camera_fresh=True):
        try:
            try:
                rows=self.read_all(); self.validate_rows(rows)
                self.feedback_error_count=0
            except Exception as feedback_error:
                self.feedback_error_count+=1
                if self.state=='STARTING' and self.recovery_ids:
                    raise feedback_error
                if (self.state in ('STARTING','HOLDING','MOVING','PAUSED_HOLD') and
                        self.feedback_error_count<MAX_TRANSIENT_FEEDBACK_ERRORS):
                    self.message=(f'Geçici geri bildirim sapması '
                                  f'({self.feedback_error_count}/{MAX_TRANSIENT_FEEDBACK_ERRORS}); konum korunuyor.')
                    return self.rows
                raise feedback_error
            if self.stop_check_at is not None:
                escaped=[i for i,r in rows.items() if r['torque'] and
                         abs(r['position']-self.targets[i])>192]
                if escaped:
                    self.fail_stop(escaped,'Durma sırasında sınırlı hareket aralığı aşıldı.')
                    return rows
                if self.clock()>=self.stop_check_at:
                    bad=[i for i,r in rows.items() if r['torque'] and
                         (abs(r['position']-self.targets[i])>12 or abs(r['speed'])>50)]
                    self.stop_check_at=None
                    if bad:self.fail_stop(bad,'Konumda durma gerçekleşmedi.');return rows
            if self.state not in ('STARTING','HOLDING','MOVING'): return rows
            if not camera_fresh: raise BusError('Kamera kesildi veya görüntü donmuş olabilir.')
            if self.state=='STARTING' and self.recovery_ids:
                if any(rows[i]['torque']!=1 or abs(rows[i]['position']-self.targets[i])>12
                       or abs(rows[i]['speed'])>50 for i in self.recovery_ids):
                    raise BusError('Yeni etkinleştirilen eklem mevcut konumda durmadı.')
            if isinstance(self.active,dict) and self.active.get('kind')=='sync_pose':
                self._poll_coordinated(rows)
                return rows
            if isinstance(self.active,dict) and self.active.get('kind')=='smooth_path':
                self._poll_smooth(rows)
                return rows
            for i,r in rows.items():
                if r['torque']!=1: raise BusError(f'ID{i}: konum tutma kayboldu.')
                if self.active and i==self.active[0]:
                    _,start,target,deadline=self.active
                    if not min(start,target)-16<=r['position']<=max(start,target)+16:
                        raise BusError('Hareket beklenen küçük pencerenin dışına çıktı.')
                    if self.clock()>deadline: raise BusError('Hareket süre sınırında tamamlanmadı.')
                    if abs(r['position']-target)<=20 and abs(r['speed'])<=50:
                        if self.settled_at is None:self.settled_at=self.clock()
                        if self.clock()-self.settled_at>=.3:
                            self.active=None;self.state='HOLDING';self.message='Adım tamamlandı; konum korunuyor.'
                    else:self.settled_at=None
                else:
                    drifting=(abs(r['position']-self.targets[i])>PASSIVE_POSITION_TOLERANCE or
                              abs(r['speed'])>PASSIVE_SPEED_TOLERANCE)
                    self.passive_drift_count[i]=self.passive_drift_count[i]+1 if drifting else 0
                    if self.passive_drift_count[i]>=MAX_TRANSIENT_FEEDBACK_ERRORS:
                        raise BusError(f'ID{i}: sabit eklem sapması üç okumada sürdü.')
                    if drifting:
                        self.message=(f'ID{i}: geçici sabit-eklem sapması '
                                      f'({self.passive_drift_count[i]}/{MAX_TRANSIENT_FEEDBACK_ERRORS}); konum korunuyor.')
            if self.state=='STARTING' and self.clock()>=self.start_check_at:
                self.recovery_ids=()
                self.state='HOLDING';self.message='Altı eklemin konum tuttuğu ölçülerek doğrulandı.'
            return rows
        except Exception as e:
            if self.state=='STARTING' and self.recovery_ids:
                self.fail_stop(self.recovery_ids,'Etkinleştirme durduruldu: '+str(e))
                self.recovery_ids=()
            elif self.stop_check_at is not None and self.clock()>=self.stop_check_at:
                self.fail_stop(IDS,'Durma geri bildirimi doğrulanamadı: '+str(e))
            elif self.may_be_live and self.state in ('STARTING','HOLDING','MOVING','PAUSED_HOLD'):
                self.pause(str(e),fault=True)
            raise

    def pause(self,reason='Kullanıcı durdurdu.',fault=False):
        """Freeze at freshly measured positions; never continue an old trajectory.

        If any fresh read/hold write cannot be verified, latch an explicit unknown
        state. Do not automatically drop a gravity-loaded arm by releasing it.
        """
        if self.state.startswith('FAULT') and not fault:
            return False  # A STOP must not clear a latched fault.
        self.active=None; self.state='FAULT_HOLD' if fault else 'PAUSED_HOLD'
        problems=[];settling_allowance=.35
        if self.may_be_live:
            for i in IDS:
                try:
                    if self.bus.read(i,40,1)!=b'\1':raise BusError('Tork kapalı; DUR tekrar etkinleştirmedi.')
                    feedback=self.bus.feedback(i);p=feedback.position
                    if not 0<=p<=4095: raise BusError('Geçersiz konum')
                    # Do not downgrade a running trajectory's verified braking
                    # acceleration to the older jog profile (10). On this arm
                    # the freshly read factory cap is 50. Never write EEPROM.
                    acceleration=getattr(self,'motion_acceleration_limit',JOG_ACCELERATION)
                    self.goal_verified(i,p,acceleration=acceleration)
                    if word(self.bus.read(i,42,2))!=p or self.bus.read(i,40,1)!=b'\1':
                        raise BusError('Tutma doğrulanamadı')
                    self.targets[i]=p
                    if abs(feedback.speed)>50:
                        # The unchanged captured target can require braking,
                        # overshoot and return. This finite diagnostic allowance
                        # includes nominal return time plus latency/settling;
                        # register acceleration is NOT guaranteed loaded braking.
                        # Keep the target, 192-count excursion guard and final
                        # 12-count / 50-count/s check; never resume the old path.
                        settling_allowance=max(settling_allowance,min(.9,
                            .30+(1+2**.5)*abs(feedback.speed)/(acceleration*100)))
                except Exception as e: problems.append(f'ID{i}: {e}')
        else:
            self.state='DISARMED'; self.message=reason+' Motorlar etkin değil.'
            return True
        if self.may_be_live:self.stop_check_at=self.clock()+settling_allowance
        if problems:
            # Unknown hold is not a stopped robot. Cut torque to any joint whose
            # stop could not be confirmed rather than letting its old goal run.
            self.fail_stop(IDS,reason+' Tutma yazımı doğrulanamadı: '+'; '.join(problems))
            return False
        self.message=reason+(' | '+ '; '.join(problems) if problems else ' Konum tutma hedefleri doğrulandı.')
        return not problems

    def release(self):
        """Always try/read every ID, even if a torque-enable ACK was lost."""
        self.active=None;self.stop_check_at=None; failed=[]
        for i in IDS:
            if not self.disable_verified(i):failed.append(i)
        self.may_be_live=bool(failed)
        self.state='FAULT_UNCONFIRMED' if failed else 'DISARMED'
        self.message=f'Tork kapatma doğrulanamadı: {failed}' if failed else 'Altı motorun torku0 doğrulandı; kol serbest.'
        return not failed
