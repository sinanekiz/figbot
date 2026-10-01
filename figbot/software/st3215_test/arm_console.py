"""Local, supervised six-joint console. Starts disconnected and unarmed.

Agent commands use a session nonce, strictly increasing sequence, and a short
expiry. GUI and file commands share the same single serial worker and guards.
"""
import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import hashlib,json,queue,threading,time,uuid
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import serial
import cv2
from PIL import Image,ImageTk
from .camera import open_camera
from .protocol import Bus
from .arm_control import ArmControl,IDS,JOG_DELTA,JOG_SPEED
from .arm_commands import validate_command,CommandSlot
from .base_center import center_base,apply_reference
from .motion_library import MotionLibrary
from .coordinated import DEFAULT_SECONDS
from .teaching import TeachingRecorder


def poll_wait(last_poll, interval, now):
    return max(0.,min(.02,last_poll+interval-now))


class Console:
    def __init__(self,root,port='COM5',camera=2):
        self.root=root;self.port=port;self.camera=camera;self.jobs=CommandSlot()
        self.quit=threading.Event();self.lock=threading.Lock();self.frame=None;self.frame_at=0;self.frame_luminance=0.0
        self.pixel_change_at=0;self.frame_unix=0;self.camera_error='Kamera açılıyor';self.state={'state':'DISCONNECTED'}
        self.nonce=uuid.uuid4().hex;self.seq=0;self.last_command_at=time.perf_counter()
        self.folder=Path(__file__).parent/'ARM_CONTROL';self.folder.mkdir(exist_ok=True)
        self.library=MotionLibrary(self.folder/'motion_library.json')
        self.cartesian=None
        self.logdir=Path(__file__).parent/'KAYITLAR'/('SURUS_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
        self.logdir.mkdir(exist_ok=False)
        self.teaching=TeachingRecorder(self.folder/'TEACHING')
        root.title('FIGBOT · Kontrollü kol · Konum tutma');root.geometry('1160x910')
        bar=ttk.Frame(root,padding=12);bar.pack(fill='x')
        ttk.Label(bar,text='FIGBOT — EŞZAMANLI KOL KONTROLÜ',font=('Segoe UI',16,'bold')).pack(anchor='w')
        ttk.Label(bar,text='DUR konumu korumayı dener; durma doğrulanmazsa tork kesilir. SERBEST BIRAK ağırlığı taşımaz.').pack(anchor='w')
        buttons=ttk.Frame(bar);buttons.pack(fill='x',pady=8)
        for text,op in [('Bağlan (yalnız oku)','connect'),('Mevcut tutmayı devral','attach'),('Eksik tutmayı aç','recover'),('Konumu tutmayı aç','arm'),('DUR · Konumu koru','pause'),('Devam','resume'),('SERBEST BIRAK','release')]:
            ttk.Button(buttons,text=text,command=lambda x=op:self.jobs.put({'op':x,'source':'gui'})).pack(side='left',padx=4)
        self.status=ttk.Label(bar,text='Etkinleştirme için destekli kol ve boş çalışma alanı gerekir.',wraplength=1110);self.status.pack(anchor='w')
        poses=ttk.Frame(bar);poses.pack(fill='x',pady=4)
        ttk.Label(poses,text='Duruş adı:').pack(side='left')
        self.pose_name=tk.StringVar(value='kapali_baslangic')
        ttk.Entry(poses,textvariable=self.pose_name,width=20).pack(side='left')
        ttk.Button(poses,text='Bu duruşu kaydet',command=lambda:self.jobs.put({'op':'save_pose','name':self.pose_name.get()})).pack(side='left',padx=4)
        ttk.Button(poses,text='Duruşa birlikte git',command=lambda:self.jobs.put({'op':'move_saved_pose','name':self.pose_name.get(),'seconds':DEFAULT_SECONDS})).pack(side='left',padx=4)
        ttk.Button(poses,text='Başlangıç → Al/bırak → Başlangıç',command=lambda:self.jobs.put({'op':'play_saved_sequence','name':'al_birak'})).pack(side='left',padx=4)
        teachbar=ttk.Frame(bar);teachbar.pack(fill='x',pady=4)
        ttk.Button(teachbar,text='Elle öğret: Kaydı başlat',command=lambda:self.jobs.put({'op':'teach_start'})).pack(side='left')
        for caption,label in [('İncire ulaştım','incire_ulastim'),('Kavradım','kavradim'),('Sepete ulaştım','sepete_ulastim'),('Bıraktım','biraktim')]:
            ttk.Button(teachbar,text=caption,command=lambda n=label:self.jobs.put({'op':'teach_mark','label':n})).pack(side='left',padx=2)
        ttk.Button(teachbar,text='Kaydı bitir',command=lambda:self.jobs.put({'op':'teach_stop'})).pack(side='left',padx=4)
        xyzbar=ttk.Frame(bar);xyzbar.pack(fill='x',pady=4)
        ttk.Label(xyzbar,text='Kol tabanı XYZ (mm):').pack(side='left')
        self.xyz_values=[tk.StringVar(value=v) for v in ('260','-233','118')]
        for label,var in zip('XYZ',self.xyz_values):
            ttk.Label(xyzbar,text=label).pack(side='left');ttk.Entry(xyzbar,textvariable=var,width=7).pack(side='left')
        ttk.Button(xyzbar,text='Hesapla',command=lambda:self.xyz_job(False)).pack(side='left',padx=4)
        ttk.Button(xyzbar,text='XYZ konumuna git',command=lambda:self.xyz_job(True)).pack(side='left',padx=4)
        ttk.Label(xyzbar,text='Yerel geometrik tahmin; telefon koordinatı değildir.').pack(side='left')
        self.preview=ttk.Label(root);self.preview.pack()
        grid=ttk.Frame(root,padding=8);grid.pack(fill='x');self.labels={}
        names=['Taban','Omuz','Dirsek','Bilek bükme','Bilek dönüş','Kıskaç']
        for i,name in zip(IDS,names):
            row=ttk.Frame(grid);row.pack(fill='x')
            ttk.Label(row,text=f'{i} · {name}',width=18).pack(side='left')
            for sign in [-1,1]:
                ttk.Button(row,text=f'{sign*10:+}°',command=lambda i=i,s=sign:self.jobs.put({'op':'jog','joint':i,'delta':s*JOG_DELTA,'source':'gui'})).pack(side='left',padx=3)
            label=ttk.Label(row,text='—',width=95);label.pack(side='left',padx=8);self.labels[i]=label
        ttk.Label(root,text='Maksimum profil: hız3400 / ivme motorun kendi limitinden okunur. Duruş/çevrim birlikte sürülür. DUR çevrimi iptal eder.').pack(anchor='w',padx=16)
        root.protocol('WM_DELETE_WINDOW',self.close)
        threading.Thread(target=self.camera_loop,daemon=True).start()
        threading.Thread(target=self.worker,daemon=True).start();root.after(100,self.refresh)

    def camera_fresh(self):
        # A fixed camera looking at a stationary arm legitimately produces
        # near-identical frames. Pixel change therefore cannot distinguish a
        # frozen virtual webcam from a valid, quiet scene. The supervised jog
        # mode only needs an actively delivered frame; target-driven motion has
        # its own phone observation freshness and calibration gates.
        with self.lock:
            return (self.frame is not None and time.perf_counter()-self.frame_at<1.5
                    and self.frame_luminance>3.0)

    def xyz_job(self, move):
        try:
            xyz=[float(v.get()) for v in self.xyz_values]
            self.jobs.put({'op':'move_xyz' if move else 'plan_xyz','xyz_mm':xyz,'seconds':DEFAULT_SECONDS})
        except ValueError:self.status.configure(text='X,Y,Z sayısal milimetre değerleri olmalı.')

    def camera_loop(self):
        cap=None
        try:
            cap,frame,_=open_camera(self.camera,'DirectShow',cancelled=self.quit.is_set)
            old=None;last_image=0
            while not self.quit.is_set():
                now=time.perf_counter();digest=hashlib.blake2b(frame.tobytes(),digest_size=8).digest()
                with self.lock:
                    self.frame=frame;self.frame_at=now;self.frame_unix=time.time();self.frame_luminance=float(frame.mean())
                    if digest!=old:self.pixel_change_at=now
                    self.camera_error='';old=digest
                if now-last_image>.5:
                    last_image=now
                    ok,jpg=cv2.imencode('.jpg',frame)
                    if ok:
                        try:
                            tmp=self.folder/'camera.tmp';tmp.write_bytes(jpg.tobytes());tmp.replace(self.folder/'camera.jpg')
                        except OSError:pass
                ok,frame=cap.read()
                if not ok:raise RuntimeError('Kamera görüntüsü kesildi.')
        except Exception as e:self.camera_error=str(e)
        finally:
            if cap is not None:cap.release()

    def worker(self):
        control=None;connection=None;last_save=0;last_poll=0;interval=.08
        with (self.logdir/'telemetry.jsonl').open('a',encoding='utf-8',buffering=1) as log:
            while not self.quit.is_set():
                try:
                    incoming=self.folder/'command.json'
                    if incoming.exists():
                        try:
                            data=json.loads(incoming.read_text(encoding='utf-8'))
                            if data.get('session')==self.nonce and data.get('seq',0)>self.seq:
                                self.seq=validate_command(data,self.nonce,self.seq,time.time())
                                if not self.jobs.put(data):raise ValueError('Bekleyen komut var; yeni komut uygulanmadı.')
                        except (ValueError,OSError) as e:
                            self.state['command_error']=str(e)
                    job=self.jobs.take()
                    if job:
                        self.last_command_at=time.perf_counter();op=job['op']
                        if self.teaching.active and op not in ('teach_mark','teach_stop','pause','release','shutdown'):
                            raise ValueError('Elle öğretme açık; önce kaydı bitir. Motor hareketi engellendi.')
                        log.write(json.dumps({'event':'command','time':time.time(),'command':job})+'\n')
                        if op=='shutdown':
                            if self.teaching.active:self.teaching.stop('CLOSED_BY_USER')
                            if control and control.may_be_live:
                                control.pause('Pencere kapatma istendi; önce kol desteklenip serbest bırakılmalı.')
                            else:self.quit.set()
                        elif op=='connect':
                            if control:raise ValueError('Zaten bağlı.')
                            connection=serial.Serial(self.port,1000000,timeout=.015,write_timeout=.2)
                            control=ArmControl(Bus(connection));control.read_all()
                            reference=self.folder.parent/'base_reference.json'
                            if reference.exists():
                                apply_reference(control,json.loads(reference.read_text(encoding='utf-8')))
                        elif control is None:raise ValueError('Önce bağlan.')
                        elif op=='teach_start':
                            self.teaching.start(control)
                            control.message='ELLE ÖĞRETME KAYDI AÇIK · Motorlar serbest; kolu elle yönlendir.'
                        elif op=='teach_mark':self.teaching.mark(job.get('label'),control)
                        elif op=='teach_stop':
                            self.teaching.stop();control.message='Elle öğretme kaydı saklandı; henüz tekrar sürülmedi.'
                        elif op=='play_teaching':
                            from .taught_replay import play_replay
                            play_replay(self.folder/'TEACHING/replay_plan.json',control,self.camera_fresh())
                        elif op=='arm':control.arm(self.camera_fresh())
                        elif op=='attach':control.attach_existing_hold(self.camera_fresh())
                        elif op=='recover':control.recover_current_hold(self.camera_fresh())
                        elif op=='center_base':center_base(control,self.camera_fresh,self.folder.parent/'base_reference.json',self.logdir/'base_center_audit.json')
                        elif op=='jog':control.jog(job.get('joint'),job.get('delta'),self.camera_fresh())
                        elif op=='probe':control.probe(job.get('joint'),job.get('delta'),self.camera_fresh())
                        elif op=='retreat_probe':control.retreat_probe(job.get('joint'),job.get('delta'),self.camera_fresh())
                        elif op=='step':control.step(job.get('joint'),job.get('delta'),self.camera_fresh())
                        elif op=='move_pose':control.move_pose(job.get('positions'),job.get('seconds',DEFAULT_SECONDS),self.camera_fresh())
                        elif op=='play_sequence':control.play_sequence(job.get('waypoints'),self.camera_fresh())
                        elif op=='return_saved_home':self.library.return_home(job.get('name'),control,self.camera_fresh())
                        elif op=='save_pose':
                            self.library.save(job.get('name'),control)
                            control.message='Duruş kaydedildi: '+job['name']
                        elif op=='inspect_profiles':
                            self.state['profile_registers']={i:{'model_version_hex':control.bus.read(i,0,6).hex(),
                                                               'profile_hex':control.bus.read(i,41,7).hex(),
                                                               'register_85_hex':control.bus.read(i,85,2).hex()} for i in IDS}
                        elif op in ('plan_xyz','move_xyz'):
                            if self.cartesian is None:
                                from .cartesian import CartesianController
                                self.cartesian=CartesianController(self.folder.parent/'SO101_MODEL.urdf',self.folder.parent/'cartesian_reference.json')
                            if op=='move_xyz' and control.state=='PAUSED_HOLD':control.resume_existing_hold(self.camera_fresh())
                            plan=self.cartesian.plan(control,job.get('xyz_mm'))
                            self.state['xyz_plan']=plan
                            control.message='XYZ hesaplandı; model hatası %.2f mm. Fiziksel doğruluk henüz ölçülmedi.'%plan['model_error_mm']
                            if op=='move_xyz':control.move_pose(plan['positions'],job.get('seconds',DEFAULT_SECONDS),self.camera_fresh())
                        elif op in ('move_saved_pose','play_saved_sequence'):
                            if control.state=='PAUSED_HOLD':control.resume_existing_hold(self.camera_fresh())
                            if op=='move_saved_pose':control.move_pose(self.library.pose(job.get('name'),control),job.get('seconds',DEFAULT_SECONDS),self.camera_fresh())
                            else:self.library.play(job.get('name'),control,self.camera_fresh())
                        elif op=='pause':control.pause()
                        elif op=='release':control.release()
                        elif op=='resume':control.resume_existing_hold(self.camera_fresh())
                        self.state.pop('command_error',None)
                    now=time.perf_counter()
                    interval=.02 if control and isinstance(control.active,dict) and control.active.get('kind')=='smooth_path' else .08
                    if control and now-last_poll>=interval:
                        last_poll=now
                        if control.state in ('HOLDING','MOVING') and now-self.last_command_at>60:
                            control.pause('60 saniye yeni komut gelmedi.')
                        control.poll(self.camera_fresh())
                        if self.teaching.active and not control.feedback_error_count:self.teaching.sample(control.rows)
                    if control:self.state.update(state=control.state,message=control.message,rows=control.rows,targets=control.targets,active=control.active,ack_losses=control.ack_losses,last_sync_mismatch=getattr(control,'last_sync_mismatch',None),last_smooth_result=getattr(control,'last_smooth_result',None))
                except Exception as e:
                    self.state['command_error']=str(e)
                    if control:self.state.update(state=control.state,message=control.message,rows=control.rows,targets=control.targets)
                now=time.perf_counter()
                self.state['teaching']=self.teaching.status()
                self.state.update(session=self.nonce,seq=self.seq,updated_unix=time.time(),camera_frame_unix=self.frame_unix,camera_fresh=self.camera_fresh(),camera_error=self.camera_error,frame_luminance=self.frame_luminance,log_directory=str(self.logdir))
                if now-last_save>.2:
                    last_save=now;data=json.dumps(self.state,ensure_ascii=False)
                    try:
                        tmp=self.folder/'status.tmp';tmp.write_text(data,encoding='utf-8');tmp.replace(self.folder/'status.json')
                        log.write(data+'\n')
                    except OSError:pass
                # Python3.12 on this Windows host: Event.wait(3ms) measured
                # ~15.6ms, while sleep(3ms) uses a high-resolution wait (~3.4ms).
                # This sleep is capped at20ms; STOP is checked on every tick.
                time.sleep(.02 if control is None else poll_wait(last_poll,interval,time.perf_counter()))
        if connection:connection.close()

    def refresh(self):
        if self.quit.is_set():self.root.destroy();return
        self.status.configure(text=f"{self.state.get('state')} · {self.state.get('message','')} · {self.state.get('command_error','')} · {self.camera_error}")
        with self.lock:frame=self.frame
        if frame is not None:
            im=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));im.thumbnail((1080,470));self.photo=ImageTk.PhotoImage(im);self.preview.configure(image=self.photo)
        for i,label in self.labels.items():
            r=self.state.get('rows',{}).get(i)
            if r:label.configure(text=f"Konum {r['position']} · hedef {self.state.get('targets',{}).get(i,'—')} · {r['voltage']}V · {r['temperature']}°C · akım(ham) {r['current_raw']} · tork {r['torque']}")
        if not self.quit.is_set():self.root.after(120,self.refresh)

    def close(self):
        # Keep the worker alive: a published DISARMED state could be stale while
        # an arm command is in flight. Closing the UI must not abandon live torque.
        self.jobs.put({'op':'shutdown','source':'window_close'})
        self.state['command_error']='DUR istendi. Kol desteklenip tork kapatıldıktan sonra uygulama kapatılabilir.'


def main():
    p=argparse.ArgumentParser();p.add_argument('--port',default='COM5');p.add_argument('--camera',type=int,default=2);a=p.parse_args()
    root=tk.Tk();Console(root,a.port,a.camera);root.mainloop()

if __name__=='__main__':main()
