"""Passive, timestamped manual teaching. Never writes to a motor bus."""
import json
import time
import uuid
from pathlib import Path
from .protocol import BusError


class TeachingRecorder:
    def __init__(self, folder, clock=time.time):
        self.folder=Path(folder);self.clock=clock;self.active=False;self.summary=None

    def start(self, control, name='uzak_incir_yuksek_sepet'):
        if self.active:raise BusError('Elle öğretme kaydı zaten açık.')
        rows=control.read_all();control.validate_rows(rows)
        if any(r['torque']!=0 for r in rows.values()):
            raise BusError('Elle öğretme için altı motor da serbest olmalı.')
        self.folder.mkdir(parents=True,exist_ok=True)
        self.path=self.folder/('TEACH_'+time.strftime('%Y%m%dT%H%M%S',time.gmtime(self.clock()))+'_'+uuid.uuid4().hex[:6]+'.jsonl')
        self.file=self.path.open('x',encoding='utf-8',buffering=1)
        self.started=self.clock();self.count=0;self.marks=[];self.previous=None;self.max_gap=0.;self.flags=[]
        self.active=True
        self._write(dict(event='start',schema=1,name=name,time=self.started,
            offsets={str(i):v for i,v in control.offsets.items()},
            mode='PASSIVE_TORQUE_OFF',replay_validated=False))
        self.sample(rows,self.started)
        return str(self.path)

    def _write(self, row):
        self.file.write(json.dumps(row,ensure_ascii=False)+'\n');self.file.flush()

    def sample(self, rows, timestamp=None):
        if not self.active:return
        now=self.clock() if timestamp is None else timestamp
        if any(r['torque']!=0 for r in rows.values()):
            self.stop('ABORTED_TORQUE_CHANGED')
            raise BusError('Tork durumu değişti; elle öğretme kaydı kapatıldı.')
        positions={str(i):r['position'] for i,r in rows.items()}
        if self.previous:
            gap=now-self.previous['time'];self.max_gap=max(self.max_gap,gap)
            if gap>.5 and 'FEEDBACK_GAP' not in self.flags:self.flags.append('FEEDBACK_GAP')
            if any(abs(p-self.previous['positions'][i])>512 for i,p in positions.items()) and 'ENCODER_JUMP_REQUIRES_REVIEW' not in self.flags:
                self.flags.append('ENCODER_JUMP_REQUIRES_REVIEW')
        item=dict(event='sample',time=now,elapsed=now-self.started,positions=positions,
            speeds={str(i):r['speed'] for i,r in rows.items()},torque={str(i):r['torque'] for i,r in rows.items()})
        self._write(item);self.previous=item;self.count+=1

    def mark(self, label, control):
        if not self.active:raise BusError('Önce elle öğretme kaydını başlat.')
        if label not in ('baslangic','incire_ulastim','kavradim','sepete_ulastim','biraktim','sonraki_incire_cikis'):
            raise BusError('Öğretme işareti geçersiz.')
        rows=control.read_all();control.validate_rows(rows);self.sample(rows)
        mark=dict(event='mark',label=label,time=self.clock(),sample=self.count,
            positions={str(i):r['position'] for i,r in rows.items()})
        self._write(mark);self.marks.append(mark)

    def stop(self, reason='RECORDED_NOT_VALIDATED_FOR_REPLAY'):
        if not self.active:raise BusError('Açık elle öğretme kaydı yok.')
        self.summary=dict(event='stop',status=reason,time=self.clock(),samples=self.count,
            marks=self.marks,max_sample_gap=self.max_gap,flags=self.flags,
            replay_validated=False,path=str(self.path))
        self._write(self.summary);self.file.close();self.active=False
        self.path.with_suffix('.summary.json').write_text(json.dumps(self.summary,indent=2,ensure_ascii=False),encoding='utf-8')
        return self.summary

    def status(self):
        return dict(active=self.active,path=str(self.path) if hasattr(self,'path') else None,
            samples=getattr(self,'count',0),marks=[m['label'] for m in getattr(self,'marks',[])],
            flags=getattr(self,'flags',[]))
