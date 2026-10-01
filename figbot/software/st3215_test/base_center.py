"""Explicit, stationary base-only coordinate recentering (not joint homing).

Feetech SMS_STS::CalibrationOfs writes 128 to torque register40. The vendor
documents this as making the present position2048. Never command4095->0.
"""
import json
import time
from .protocol import BusError, BusTimeout, word, signed_magnitude


def save_record(path, data):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    tmp.replace(path)


def apply_reference(control, data):
    if data.get('status')!='VERIFIED' or data.get('servo_id')!=1:
        raise BusError('Taban merkez kaydı doğrulanmamış.')
    old=data['old_position'];new=data['new_position']
    shift=(85-signed_magnitude(data['new_offset'],11)+2048)%4096-2048
    bounds=[2700+shift,5256+shift]
    if (not 3900<=old<=4095 or abs(new-2048)>8 or
            data['envelope']!=bounds or not 0<=bounds[0]<bounds[1]<=4095):
        raise BusError('Taban koordinat dönüşümü geçersiz.')
    if abs(((old+shift-new+2048)%4096)-2048)>8:
        raise BusError('Taban ofset dönüşümü uyuşmuyor.')
    if word(control.bus.read(1,31,2))!=data['new_offset']:
        raise BusError('Taban kayıtlı ofseti donanımla uyuşmuyor.')
    control.offsets[1]=data['new_offset']
    control.envelopes[1]=tuple(bounds)
    control.base_reference=data


def center_base(control, camera_check, reference_path, audit_path, sleep=time.sleep):
    if control.state!='HOLDING' or not camera_check() or control.base_reference:
        raise BusError('Taban merkezleme için ilk kalibrasyon ve sabit canlı tutma gerekir.')
    bus=control.bus
    before=control.read_all();control.validate_rows(before)
    if not 3900<=before[1]['position']<=4095:
        raise BusError('Bu işlem yalnız doğrulanmış üst taban dalında kullanılabilir.')
    for i,r in before.items():
        if (r['torque']!=1 or r['speed']!=0 or r['moving'] or
                abs(word(bus.read(i,42,2))-r['position'])>20):
            raise BusError('Merkezleme öncesi sabit tutma doğrulanamadı.')
    if (word(bus.read(1,31,2))!=85 or bus.read(1,33,1)!=b'\0' or
            word(bus.read(1,3,2))!=777):
        raise BusError('Taban model/mod/eski ofset uyuşmuyor.')
    record={'status':'PREPARED','servo_id':1,'old_offset':85,
            'old_position':before[1]['position'],'before':before,'time_unix':time.time()}
    save_record(audit_path,record)  # Durable record before the first hardware write.
    try:
        if not control.disable_verified(1):raise BusError('Taban torku kapatılamadı.')
        sleep(.1)
        r=bus.feedback(1)
        if abs(r.position-before[1]['position'])>8 or r.speed or r.moving or not camera_check():
            raise BusError('Serbest taban merkezleme öncesinde oynadı.')
        record['status']='CALIBRATION_SENT';save_record(audit_path,record)
        try:bus.write(1,40,b'\x80')
        except BusTimeout:pass  # No retry of a potentially applied calibration.
        sleep(.1)
        # Keep this vertical base axis off until the NEW coordinates are verified.
        if not control.disable_verified(1):raise BusError('Merkezleme sonrası taban torku doğrulanamadı.')
        r=bus.feedback(1);offset=word(bus.read(1,31,2))
        if abs(r.position-2048)>8 or r.speed or r.moving:
            raise BusError('Yeni orta konum2048 doğrulanamadı.')
        shift=(85-signed_magnitude(offset,11)+2048)%4096-2048
        record.update(status='VERIFIED',new_position=r.position,new_offset=offset,
                      envelope=[2700+shift,5256+shift])
        apply_reference(control,record)
        for i in range(2,7):
            other=bus.feedback(i)
            if (abs(other.position-before[i]['position'])>12 or other.speed or other.moving
                    or bus.read(i,40,1)!=b'\1'):
                raise BusError('Diğer eklemin tutması değişti.')
        if not camera_check():raise BusError('Merkezleme sırasında kamera kesildi.')
        control.targets[1]=r.position
        control.goal_verified(1,r.position,speed=57,acceleration=1)
        if bus.read(1,40,1)!=b'\1':bus.write(1,40,b'\1')
        for _ in range(10):
            sleep(.08)
            fresh=control.read_all();control.validate_rows(fresh)
            if not camera_check():raise BusError('Tutma doğrulamasında kamera kesildi.')
            if any(v['torque']!=1 or abs(v['position']-control.targets[i])>12 or
                   abs(v['speed'])>50 for i,v in fresh.items()):
                raise BusError('Merkezleme sonrası aynı fiziksel duruş korunamadı.')
        record['after']=fresh
        save_record(reference_path,record);save_record(audit_path,record)
        control.state='HOLDING';control.active=None
        control.message='Taban aynı duruşta2048 merkezlendi; fiziksel aralık yeni sayaca taşındı.'
        return record
    except Exception as e:
        control.fail_stop([1],'Taban merkezleme durduruldu: '+str(e))
        record.update(status='FAILED',error=str(e))
        try:save_record(audit_path,record)
        except OSError:pass  # A disk failure must never prevent the hardware stop.
        raise
