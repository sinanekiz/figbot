"""Expiring local commands and bounded, stop-priority mailbox (no hardware)."""
import math
import threading
import time


def validate_command(data,nonce,last,now):
    if data.get('session')!=nonce or type(data.get('seq'))!=int or data['seq']<=last:
        raise ValueError('Oturum veya komut sırası geçersiz.')
    stamp=data.get('created_unix')
    if type(stamp) not in (float,int) or not math.isfinite(stamp) or not 0<=now-stamp<=3:
        raise ValueError('Komut süresi geçti.')
    if data.get('op') not in ('connect','attach','recover','arm','jog','probe','retreat_probe','step','pause','release','resume','center_base','move_pose','play_sequence','save_pose','move_saved_pose','play_saved_sequence','return_saved_home','plan_xyz','move_xyz','inspect_profiles','teach_start','teach_mark','teach_stop','play_teaching'):
        raise ValueError('Bilinmeyen işlem.')
    return data['seq']


class CommandSlot:
    """No movement backlog. STOP/release discard pending movement commands."""
    def __init__(self,clock=time.time):
        self.lock=threading.Lock();self.pending=None;self.clock=clock

    def put(self,job):
        job=dict(job);job.setdefault('created_unix',self.clock())
        with self.lock:
            if self.pending and self.pending['op'] in ('pause','release','shutdown'):
                return False
            if self.pending and job['op'] not in ('pause','release','shutdown'):
                return False
            self.pending=job
            return True

    def take(self):
        with self.lock:
            job=self.pending;self.pending=None
        if job and not 0<=self.clock()-job['created_unix']<=3:
            raise ValueError('Kuyruktaki komutun süresi geçti; uygulanmadı.')
        return job

    def clear(self):
        with self.lock:self.pending=None
