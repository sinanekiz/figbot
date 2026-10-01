"""Camera + read-only telemetry preparation. No goal, torque or EEPROM writes."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
import tkinter as tk
from tkinter import ttk

import cv2
from PIL import Image, ImageTk
import serial
from serial.tools import list_ports
from .protocol import Bus
from .camera import open_camera
from .recording import SessionRecorder


class ReadOnlyBus(Bus):
    def transact(self, servo_id, instruction, data=b'', response_size=None):
        if instruction not in (1, 2) or not 1 <= servo_id <= 253:
            raise ValueError('Bu ekranda yalnız bireysel PING/READ komutları kullanılabilir.')
        return super().transact(servo_id, instruction, data, response_size)


def read_sample(bus, ids):
    results=[]
    for servo_id in ids:
        row={'id':servo_id,'captured_utc':datetime.now(timezone.utc).isoformat()}
        try:
            f=bus.feedback(servo_id)
            row.update(asdict(f), degrees=f.degrees, torque=bus.read(servo_id,40,1)[0],ok=True)
        except Exception as exc:
            row.update(ok=False,error=str(exc))
        results.append(row)
    return results


class Observer:
    def __init__(self, root):
        self.root=root;self.lock=threading.Lock();self.stop=threading.Event()
        self.frame=None;self.frame_at=0;self.rows=[];self.rows_at=0
        self.motor_thread=None;self.camera_thread=None
        self.motor_stop=threading.Event();self.camera_stop=threading.Event()
        self.motor_note='USB bağlantısı kapalı.';self.camera_note='Kamera kapalı.'
        self.recorder=None;self.record_note=''
        root.title('FIGBOT · Kamera ve Konum Okuma · HAREKET YOK');root.geometry('1120x810')
        top=ttk.Frame(root,padding=14);top.pack(fill='x')
        ttk.Label(top,text='KALİBRASYON HAZIRLIĞI — YALNIZ GÖRÜNTÜ VE OKUMA',font=('Segoe UI',15,'bold')).pack(anchor='w')
        ttk.Label(top,text='Hareket, tork açma/kapatma veya ID değiştirme komutu göndermez. Kapatmak motoru durdurmaz.').pack(anchor='w')
        controls=ttk.Frame(top);controls.pack(fill='x',pady=8)
        ports=list(list_ports.comports());default=next((p.device for p in ports if p.vid==0x1a86),'')
        self.port=tk.StringVar(value=default)
        ttk.Label(controls,text='USB:').pack(side='left')
        ttk.Combobox(controls,textvariable=self.port,values=[p.device for p in ports],width=10).pack(side='left',padx=5)
        self.single=tk.BooleanVar(value=False)
        ttk.Checkbutton(top,text='Sürücüye elektriksel olarak yalnız TEK motor bağlı; zincir ayrıldı.',variable=self.single).pack(anchor='w')
        self.unique=tk.BooleanVar(value=False)
        ttk.Checkbutton(top,text='VEYA: Altı motorun farklı ID 1–6 olduğunu tek tek doğruladım.',variable=self.unique).pack(anchor='w')
        ttk.Button(controls,text='Konum okumayı başlat',command=self.start_motor).pack(side='left',padx=5)
        ttk.Button(controls,text='USB okumayı kapat',command=self.motor_stop.set).pack(side='left')
        self.id=tk.IntVar(value=1)
        ttk.Label(controls,text='Tek motor ID:').pack(side='left',padx=(12,4))
        ttk.Spinbox(controls,from_=1,to=253,textvariable=self.id,width=5).pack(side='left')
        cam=ttk.Frame(top);cam.pack(fill='x',pady=8)
        self.camera_index=tk.IntVar(value=0)
        ttk.Label(cam,text='Kamera numarası:').pack(side='left')
        ttk.Spinbox(cam,from_=0,to=9,textvariable=self.camera_index,width=4).pack(side='left',padx=4)
        self.camera_mode=tk.StringVar(value='Otomatik')
        ttk.Combobox(cam,textvariable=self.camera_mode,values=['Otomatik','Windows / MSMF','DirectShow'],state='readonly',width=17).pack(side='left',padx=4)
        ttk.Button(cam,text='Kamerayı aç',command=self.start_camera).pack(side='left',padx=4)
        ttk.Button(cam,text='Kamerayı kapat',command=self.close_camera).pack(side='left')
        ttk.Button(cam,text='Görüntü + konum kaydet',command=self.snapshot).pack(side='left',padx=12)
        ttk.Label(top,text='Kayıtlar yerel bilgisayarda kalır. Kamera ve konumlar ayrı zaman damgalıdır; eşzamanlı ölçüm değildir.').pack(anchor='w')
        rec=ttk.Frame(top);rec.pack(fill='x',pady=4)
        ttk.Button(rec,text='Elle kalibrasyon kaydını başlat',command=self.start_recording).pack(side='left')
        ttk.Button(rec,text='Kaydı bitir',command=self.stop_recording).pack(side='left',padx=6)
        ttk.Label(rec,text='Sıra: 1 taban → 2 omuz → 3 dirsek → 4 bilek → 5 dönüş → 6 kıskaç').pack(side='left')
        self.status=ttk.Label(top,text='Hazır. Önce kamera açılabilir.',wraplength=1050);self.status.pack(anchor='w',pady=6)
        self.preview=ttk.Label(root,text='Kamerayı kola ve çalışma zeminine yönelt. Kamera açma düğmesine bas.');self.preview.pack(fill='both',expand=True)
        self.table=ttk.Treeview(root,columns=('id','position','degrees','voltage','temperature','torque','state'),show='headings',height=6)
        for col,title in zip(self.table['columns'],['ID','Enkoder','Motor açısı °','Gerilim V','Sıcaklık °C','Tork kaydı','Durum']):
            self.table.heading(col,text=title);self.table.column(col,width=115 if col!='state' else 280)
        self.table.pack(fill='x',padx=14,pady=10)
        self.save_note='';self.display_rows_at=0
        root.protocol('WM_DELETE_WINDOW',self.close);root.after(100,self.refresh)

    def start_motor(self):
        if self.motor_thread and self.motor_thread.is_alive():return
        if not(self.single.get() or self.unique.get()):
            self.save_note='Önce tek motor bağlantısını veya farklı ID’leri doğrula. Aynı ID’deki motorlar ayırt edilemez.';return
        try:
            ids=list(range(1,7)) if self.unique.get() else [int(self.id.get())]
            if not all(1<=i<=253 for i in ids):raise ValueError()
        except Exception:
            self.save_note='Geçerli motor ID: 1–253.';return
        port=self.port.get();self.motor_stop.clear();self.save_note=''
        def worker():
            try:
                with serial.Serial(port,1000000,timeout=.015,write_timeout=.2) as connection:
                    bus=ReadOnlyBus(connection)
                    self.motor_note='Yalnız konum okunuyor; motor ID’si fiziksel eklem kimliğini tek başına doğrulamaz.'
                    while not self.stop.is_set() and not self.motor_stop.is_set():
                        rows=read_sample(bus,ids)
                        with self.lock:self.rows=rows;self.rows_at=time.monotonic()
                        self.motor_stop.wait(.35)
                self.motor_note='USB okumaları kapatıldı; tork durumu değiştirilmedi.'
            except Exception as exc:self.motor_note='USB açılamadı / okuma kesildi: '+str(exc)
        self.motor_thread=threading.Thread(target=worker,daemon=True);self.motor_thread.start()

    def start_camera(self):
        if self.camera_thread and self.camera_thread.is_alive():return
        try:index=int(self.camera_index.get());assert 0<=index<=9
        except Exception:self.save_note='Kamera numarası 0–9 olmalı.';return
        self.camera_stop.clear();self.camera_note='Kamera açılıyor…'
        mode=self.camera_mode.get()
        def worker():
            capture=None
            try:
                capture,frame,backend=open_camera(index,mode,
                    cancelled=lambda:self.stop.is_set() or self.camera_stop.is_set(),
                    report=lambda note:setattr(self,'camera_note',note))
                with self.lock:self.frame=frame;self.frame_at=time.monotonic()
                self.camera_note=f'Kamera {index} açık ({backend}).'
                while not self.stop.is_set() and not self.camera_stop.is_set():
                    ok,frame=capture.read()
                    if not ok:raise RuntimeError('Kameradan görüntü alınamadı.')
                    with self.lock:self.frame=frame;self.frame_at=time.monotonic()
                    self.camera_stop.wait(.04)
            except Exception as exc:self.camera_note=str(exc)
            finally:
                if capture is not None:capture.release()
                with self.lock:self.frame=None;self.frame_at=0
        self.camera_thread=threading.Thread(target=worker,daemon=True);self.camera_thread.start()

    def close_camera(self):
        self.camera_stop.set();self.camera_note='Kamera kapatılıyor.'

    def start_recording(self):
        if self.recorder is not None and not self.recorder.closed:return
        with self.lock:frame=self.frame;frame_at=self.frame_at;rows=list(self.rows);rows_at=self.rows_at
        target=Path(__file__).resolve().parent/'KAYITLAR'/('ELLE_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        try:
            self.recorder=SessionRecorder(target,frame,frame_at,rows,rows_at)
            self.record_note='KAYIT AÇIK — yalnız elle hareket, motorlar serbest.'
        except Exception as exc:self.record_note=str(exc)

    def stop_recording(self):
        if self.recorder is not None:
            self.recorder.close()
            self.record_note='Kayıt tamamlandı: '+str(self.recorder.directory)

    def snapshot(self):
        with self.lock:
            frame=None if self.frame is None else self.frame.copy();frame_at=self.frame_at
            rows=list(self.rows);rows_at=self.rows_at
        now=time.monotonic()
        if frame is None or now-frame_at>2:
            self.save_note='Kayıt için güncel kamera görüntüsü gerekiyor.';return
        target=Path(__file__).resolve().parent/'KAYITLAR';target.mkdir(exist_ok=True)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        picture=target/(stamp+'.jpg')
        if not cv2.imwrite(str(picture),frame):self.save_note='Görüntü dosyası yazılamadı.';return
        data={'recorded_utc':datetime.now(timezone.utc).isoformat(),'image':picture.name,
              'camera_age_seconds':now-frame_at,'telemetry_age_seconds':now-rows_at if rows_at else None,
              'telemetry_stale':not rows_at or now-rows_at>2,'motor_readings':rows,
              'calibration_complete':False,'motion_commands_sent':False}
        (target/(stamp+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        self.save_note='Kaydedildi: '+str(picture)

    def refresh(self):
        with self.lock:frame=self.frame;frame_at=self.frame_at;rows=list(self.rows);rows_at=self.rows_at
        now=time.monotonic()
        if self.recorder is not None and not self.recorder.closed:
            try:self.record_note=self.recorder.add(frame,frame_at,rows,rows_at,now)
            except Exception as exc:self.record_note='KAYIT DURDU: '+str(exc)
        if frame is not None and now-frame_at<2:
            im=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));im.thumbnail((1050,365))
            self.photo=ImageTk.PhotoImage(im);self.preview.configure(image=self.photo,text='')
        else:self.preview.configure(image='',text='Kamera kapalı veya görüntü güncel değil.')
        if rows_at!=self.display_rows_at or (rows_at and now-rows_at>2):
            self.table.delete(*self.table.get_children());self.display_rows_at=rows_at
            for r in rows:
                if r['ok']:
                    state='ESKİ OKUMA' if now-rows_at>2 else 'Okundu; eklem eşlemesi doğrulanmadı'
                    values=(r['id'],r['position'],f"{r['degrees']:.2f}",r['voltage'],r['temperature'],r['torque'],state)
                else:values=(r['id'],'—','—','—','—','—',r['error'])
                self.table.insert('','end',values=values)
        self.status.configure(text=self.record_note+' '+self.camera_note+' '+self.motor_note+' '+self.save_note)
        if not self.stop.is_set():self.root.after(100,self.refresh)

    def close(self):
        self.stop_recording()
        self.stop.set();self.camera_stop.set();self.motor_stop.set();self.root.destroy()


def main():
    parser=argparse.ArgumentParser(description='Read-only camera and six-servo observation')
    parser.add_argument('--camera-index',type=int,choices=range(10),default=0)
    parser.add_argument('--camera-mode',choices=['Otomatik','Windows / MSMF','DirectShow'],default='Otomatik')
    parser.add_argument('--port')
    parser.add_argument('--read-verified-chain',action='store_true',help='Only after each physical motor ID1-6 has been verified')
    parser.add_argument('--open-camera',action='store_true')
    args=parser.parse_args()
    root=tk.Tk();app=Observer(root)
    app.camera_index.set(args.camera_index);app.camera_mode.set(args.camera_mode)
    if args.port:app.port.set(args.port)
    if args.read_verified_chain:
        app.unique.set(True);root.after(200,app.start_motor)
    if args.open_camera:root.after(400,app.start_camera)
    root.mainloop()

if __name__=='__main__':main()
