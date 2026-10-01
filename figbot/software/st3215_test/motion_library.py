"""Measured joint poses tied to the actual servo encoder offsets."""
import json
import re
from pathlib import Path
from .protocol import BusError
from .coordinated import DEFAULT_SECONDS


class MotionLibrary:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():return {'schema':1,'poses':{},'sequences':{}}
        data=json.loads(self.path.read_text(encoding='utf-8'))
        if data.get('schema')!=1:raise BusError('Duruş dosyası sürümü geçersiz.')
        return data

    def save(self, name, control):
        if not isinstance(name,str) or not re.fullmatch(r'[\w -]{1,48}',name):
            raise BusError('Duruş adı 1–48 harf/rakam/boşluk olmalı.')
        if control.state not in ('HOLDING','PAUSED_HOLD','DISARMED'):
            raise BusError('Önce kolu sabit tut.')
        rows=control.read_all();control.validate_rows(rows)
        if any(abs(r['speed'])>10 or r['moving'] for r in rows.values()):
            raise BusError('Hareketli kol duruş olarak kaydedilemez.')
        data=self.load()
        data['poses'][name]={'positions':{str(i):r['position'] for i,r in rows.items()},
                             'offsets':{str(i):v for i,v in control.offsets.items()}}
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8');tmp.replace(self.path)
        return name

    def pose(self, name, control):
        item=self.load()['poses'].get(name)
        if not item:raise BusError('Kayıtlı duruş bulunamadı.')
        if item['offsets']!={str(i):v for i,v in control.offsets.items()}:
            raise BusError('Duruş farklı motor kalibrasyonuyla kaydedilmiş.')
        return item['positions']

    def sequence(self, name, control):
        data=self.load();items=data['sequences'].get(name)
        if not items:raise BusError('Kayıtlı çevrim bulunamadı.')
        home=data.get('home_cycles',{}).get(name)
        if home:
            if items[0]['pose']!=home or items[-1]['pose']!=home:
                raise BusError('Çevrim kayıtlı kapalı başlangıçta başlayıp bitmeli.')
            expected=self.pose(home,control)
            rows=control.read_all();control.validate_rows(rows)
            if any(abs(r['position']-expected[str(i)])>20 or abs(r['speed'])>50 for i,r in rows.items()):
                raise BusError('Çevrim için önce kayıtlı kapalı başlangıç duruşuna dön.')
        return [{'positions':self.pose(item['pose'],control),
                 'seconds':item.get('seconds',DEFAULT_SECONDS),'dwell':item.get('dwell',0),
                 **({'stream_seconds':item['stream_seconds']} if 'stream_seconds' in item else {})} for item in items]

    def play(self, name, control, camera_fresh):
        plan=self.sequence(name,control)
        data=self.load();home=data.get('home_cycles',{}).get(name)
        envelopes=dict(control.envelopes)
        if home:
            if len(plan)<3:raise BusError('Kapalı duruş için açılma ve dönüş yolu gerekli.')
            measured=self.pose(home,control)
            for i,(low,high) in envelopes.items():
                p=measured[str(i)]
                if low<=p<=high:continue
                # Unchanged passive wrist roll needs no range extension.
                if all(w['positions'][str(i)]==p for w in plan):continue
                # Only the observed shoulder/wrist-pitch extension is allowed,
                # within 256 counts of the old range. Interior waypoints must
                # already lie inside the original range. This is a supervised
                # taught route, not a collision-free workspace declaration.
                if i not in (2,4) or min(abs(p-low),abs(p-high))>256:
                    raise BusError('Kapalı duruş mevcut çalışma aralığından çok uzak.')
                if any(not low<=w['positions'][str(i)]<=high for w in plan[1:-1]):
                    raise BusError('Kapalı duruş uzantısı yalnız açılma/dönüşte kullanılabilir.')
                envelopes[i]=(min(low,p-20),max(high,p+20))
        # sequence() already verified the actual home pose. Do not command
        # that same pose again and wait before beginning the unfolding move.
        method=control.play_smooth if name in data.get('continuous_cycles',[]) else control.play_sequence
        method(plan[1:] if home else plan,camera_fresh,taught_envelopes=envelopes)

    def return_home(self, name, control, camera_fresh):
        """Explicit recovery from within the taught unfolding corridor only.

        Never called automatically after a fault. A remote or arbitrary arm
        pose is refused; it needs a separately checked return route.
        """
        data=self.load();transit=data.get('home_transits',{}).get(name)
        if not transit:raise BusError('Bu başlangıcın kayıtlı dönüş geçişi yok.')
        home=self.pose(name,control);entry=self.pose(transit,control)
        rows=control.read_all();control.validate_rows(rows)
        for i,r in rows.items():
            a,b=home[str(i)],entry[str(i)]
            if not min(a,b)-20<=r['position']<=max(a,b)+20:
                raise BusError('Kol kapalı başlangıcın dönüş koridorunda değil.')
        env=dict(control.envelopes)
        for i,(lo,hi) in env.items():
            p=home[str(i)]
            if not lo<=p<=hi and abs(rows[i]['position']-p)>20:
                if i not in (2,4) or min(abs(p-lo),abs(p-hi))>256:
                    raise BusError('Başlangıç dönüş aralığı geçersiz.')
                env[i]=(min(lo,p-20),max(hi,p+20))
        control.play_sequence([{'positions':home,'seconds':DEFAULT_SECONDS}],camera_fresh,taught_envelopes=env)
