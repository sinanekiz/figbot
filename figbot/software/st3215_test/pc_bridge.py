"""Loopback-only ST3215 bridge for the Android PC mode. One client, one COM owner.

No hardware is opened on import or server startup. The Android controller owns
planning/verification; the bridge validates packets and never retries writes.
"""
import argparse
import socket
import subprocess
import time
from .protocol import Bus, packet, word


def validate(frame):
    if len(frame)<6 or frame[:2]!=b'\xff\xff' or len(frame)!=frame[3]+4 or sum(frame[2:])&255!=255:
        raise ValueError('Bozuk ST3215 paketi')
    motor,op=frame[2],frame[4]; data=frame[5:-1]
    if op==2 and 1<=motor<=6 and len(data)==2 and 1<=data[1]<=62 and data[0]+data[1]<=256:
        return motor,op,data,data[1]
    def writable(address,value):
        if address==40 and value in (b'\0',b'\1'):return True
        if address==42 and len(value)==2:return word(value)<=4095
        return (address==41 and len(value)==7 and 1<=value[0]<=150
                and word(value[1:3])<=4095 and value[3:5]==b'\0\0'
                and 1<=word(value[5:7])<=3400)
    if op==3 and 1<=motor<=6 and data and writable(data[0],data[1:]):return motor,op,data,0
    if op==0x83 and motor==254 and len(data)>=5:
        address,width=data[:2]; stride=width+1
        if (address,width) not in ((42,2),(41,7)) or (len(data)-2)%stride:raise ValueError('Geçersiz grup')
        rows=[data[i:i+stride] for i in range(2,len(data),stride)]
        ids=[row[0] for row in rows]
        if (1<=len(rows)<=6 and len(set(ids))==len(ids) and all(1<=i<=6 for i in ids)
                and all(writable(address,row[1:]) for row in rows)):return motor,op,data,0
    raise ValueError('Yalnız altı motorun okuma ve sınırlı RAM komutları kabul edilir; EEPROM kapalı.')


def receive_packet(client):
    # One absolute deadline also bounds slow partial packets.
    deadline=time.monotonic()+.5
    def exact(count):
        result=bytearray()
        while len(result)<count:
            left=deadline-time.monotonic()
            if left<=0:raise TimeoutError('Telefon bağlantısı zaman aşımı')
            client.settimeout(left)
            part=client.recv(count-len(result))
            if not part:raise EOFError('Telefon bağlantısı kapandı')
            result.extend(part)
        return bytes(result)
    head=exact(4)
    if head[:2]!=b'\xff\xff' or not 2<=head[3]<=64:raise ValueError('Paket başlığı geçersiz')
    return head+exact(head[3])


def hold_on_disconnect(bus):
    """Best-effort measured hold; never re-enable torque or auto-release gravity joints."""
    held={}
    try:
        for motor in range(1,7):
            feedback,torque=bus.feedback_state(motor)
            if torque==0:continue
            if torque!=1 or not 0<=feedback.position<=4095:raise ValueError('Geri bildirim geçersiz')
            acceleration=bus.read(motor,85,1)[0]
            if not 1<=acceleration<=150:raise ValueError('İvme sınırı geçersiz')
            held[motor]=feedback.position
            # Do not replay an old trajectory. Capture the position at each fresh read.
            bus.goal(motor,feedback.position,3400,acceleration)
            if bus.read(motor,42,2)!=feedback.position.to_bytes(2,'little'):raise ValueError('Tutma hedefi okunamadı')
        deadline=time.monotonic()+.9
        while held:
            settled=True
            for motor,position in held.items():
                feedback,torque=bus.feedback_state(motor)
                if torque!=1 or abs(feedback.position-position)>192:raise ValueError('Tutma aralığı aşıldı')
                settled &= abs(feedback.position-position)<=12 and abs(feedback.speed)<=50 and not feedback.moving
            if settled:break
            if time.monotonic()>=deadline:raise ValueError('Durma doğrulanamadı')
            time.sleep(.02)
        return 'Bağlantı kapandı; ölçülen konum tutması doğrulandı. Yeniden hareket başlatılmadı.'
    except Exception as error:
        return 'DURUM BELİRSİZ: '+str(error)+'. Kolun duruşunu kontrol et; otomatik tork kesilmedi.'


def serve_client(client,bus):
    changed=False
    try:
        client.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        while True:
            motor,op,data,size=validate(receive_packet(client))
            if op!=2:changed=True  # Includes ambiguous writes that fail before an ACK.
            result=bus.transact(motor,op,data,response_size=size)
            if motor!=254:client.sendall(packet(motor,0,result))
    finally:
        if changed:print(hold_on_disconnect(bus),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',help='Motor kartının COM portu; tek fiziksel USB seri kart varsa otomatik seçilir')
    args=parser.parse_args()
    import serial
    from serial.tools import list_ports
    candidates=[p for p in list_ports.comports() if p.vid is not None]
    port=args.port
    if not port:
        if len(candidates)!=1:
            print('Tek motor kartı seçilemedi. --port COMx ile başlat. Bulunan:',[(p.device,p.description) for p in candidates]);return 2
        port=candidates[0].device
    # Only an authorized Android device accepts adb reverse. A failure opens no serial port.
    subprocess.run(['adb','reverse','tcp:8873','tcp:8873'],check=True)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',8873));listener.listen(1)
        print(f'PC köprüsü hazır: {port}. Telefonda 03 > PC’ye bağlan. Diğer motor panellerini kapalı tut.',flush=True)
        client,_=listener.accept()
        with client:
            with serial.Serial(port,1000000,timeout=.015,write_timeout=.18) as connection:
                try:serve_client(client,Bus(connection))
                except Exception as error:print('Oturum bitti:',error,flush=True)
    print('Tek oturum sonlandı. Yeniden bağlantı için bu dosyayı tekrar aç.',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
