"""Native multi-channel bench UI. Startup, connection and arming cause no movement."""
import argparse
import collections
import json
import queue
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from serial.tools import list_ports

try:
    from .pca_controller import PCAController, JOINTS, SHOULDERS, channel_mask
except ImportError:
    from pca_controller import PCAController, JOINTS, SHOULDERS, channel_mask


class Worker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.controller = PCAController()
        self.lock = threading.Lock()
        self.tasks = collections.deque()
        self.updates = queue.Queue(maxsize=1)
        self.closed = threading.Event()
        self.block_motion = True
        self.last_status_write = 0

    def submit(self, action, value=None):
        with self.lock:
            if action in ('stop', 'disconnect', 'close', 'connect'):
                self.tasks.clear()
                self.block_motion = True
            elif action == 'arm':
                if any(t[0] in ('stop', 'disconnect', 'close') for t in self.tasks):
                    return
                if value[1]:
                    self.block_motion = False
                self.tasks = collections.deque(t for t in self.tasks
                                              if not (t[0] == 'position' and t[1][0] == value[0]))
            elif action == 'position':
                if self.block_motion:
                    return
                self.tasks = collections.deque(t for t in self.tasks
                                              if not (t[0] == action and t[1][0] == value[0]))
            self.tasks.append((action, value))

    def run(self):
        try:
            while not self.closed.is_set():
                with self.lock:
                    task = self.tasks.popleft() if self.tasks else None
                try:
                    if task:
                        action, value = task
                        if action == 'close':
                            break
                        if action == 'connect': self.controller.connect(value)
                        elif action == 'disconnect': self.controller.disconnect()
                        elif action == 'stop': self.controller.stop()
                        elif action == 'arm': self.controller.arm(*value)
                        elif action == 'position': self.controller.position(*value)
                    self.controller.poll()
                except Exception as exc:
                    with self.lock:
                        self.tasks.clear()
                        self.block_motion = True
                    try: self.controller.disconnect()
                    except Exception: pass
                    self.controller.message = 'Hata: ' + str(exc)
                try: self.updates.get_nowait()
                except queue.Empty: pass
                snapshot = self.controller.snapshot()
                self.updates.put_nowait(snapshot)
                if time.monotonic() - self.last_status_write > .5:
                    try:
                        path = Path(__file__).resolve().parents[2] / '.codex_artifacts/arduino/pca-panel-state.json'
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(json.dumps(dict(snapshot, timestamp=time.time()), ensure_ascii=False), encoding='utf-8')
                    except OSError:
                        pass
                    self.last_status_write = time.monotonic()
                self.closed.wait(.025)
        finally:
            try: self.controller.disconnect()
            finally: self.closed.set()


class App:
    def __init__(self, root, initial_port='COM3', connect=False):
        self.root = root
        self.worker = Worker()
        self.worker.start()
        self.state = dict(ready=False, enabled=0, active=0, connected=False)
        self.closed = False
        self.test_jobs = []
        self.rows = {}
        self.pending_arms = {}
        root.title('FIGBOT · Arduino / PCA9685 · Kol kontrolü')
        root.geometry('1080x820')
        root.minsize(1000, 820)
        root.configure(bg='#f3f6fb')
        root.option_add('*Font', '{Segoe UI} 10')
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TNotebook.Tab', padding=(18, 8))
        main = tk.Frame(root, bg='#f3f6fb', padx=22, pady=16)
        main.pack(fill='both', expand=True)
        tk.Label(main, text='Kol kontrolü', font=('Segoe UI', 23, 'bold'), bg='#f3f6fb', fg='#18324a').pack(anchor='w')
        tk.Label(main, text='PCA9685 · Her eklem için tek bar · Karşılıklı omuz motorları birlikte, ters yönlü.',
                 bg='#f3f6fb', fg='#52687b').pack(anchor='w', pady=(2, 10))
        bar = tk.Frame(main, bg='#f3f6fb'); bar.pack(fill='x')
        self.port = tk.StringVar(value=initial_port)
        self.ports = ttk.Combobox(bar, textvariable=self.port, width=10, state='readonly')
        self.ports.pack(side='left')
        ttk.Button(bar, text='Portları yenile', command=self.refresh_ports).pack(side='left', padx=5)
        self.connect_button = ttk.Button(bar, text='Bağlan', command=self.connect)
        self.connect_button.pack(side='left')
        self.stop_button = tk.Button(bar, text='TÜM PWM SİNYALLERİNİ KAPAT', bg='#b83434', fg='white',
                                    command=self.stop, relief='flat', padx=14, pady=7)
        self.stop_button.pack(side='right')
        self.message = tk.StringVar(value='Bağlı değil · Başlangıçta tüm kanallar kapalı.')
        tk.Label(main, textvariable=self.message, bg='#f3f6fb', fg='#255b6c', anchor='w', wraplength=1000).pack(fill='x', pady=10)
        self.notebook = ttk.Notebook(main)
        for arm in range(2):
            page = tk.Frame(self.notebook, bg='white', padx=12, pady=6)
            self.notebook.add(page, text=f'Kol {arm + 1} · kanallar {arm * 6}–{arm * 6 + 5}')
            for joint, name in enumerate(JOINTS):
                if joint == 2: continue
                if joint == 1: name = f'Omuz · CH {arm * 6 + 1:02d} + {arm * 6 + 2:02d}'
                self.make_row(page, arm * 6 + joint, name, '2 × MG996R' if joint == 1 else 'MG996R' if joint < 4 else 'MG90S')
        bottom = tk.Frame(main, bg='#f3f6fb'); bottom.pack(side='bottom', fill='x', pady=(5, 0))
        self.test_button = ttk.Button(bottom, text='Kanal 0 küçük test: 90 → 95 → 85 → 90°', command=self.test)
        self.test_button.pack(side='left')
        tk.Label(main, bg='#fff0d8', fg='#744910', anchor='w', justify='left', padx=10, pady=8,
                 text='0–180° barlar komut açısıdır; gerçek hareket aralığı ölçülmedi. Başlangıç: 1000–2000 µs.\n'
                      '“Geniş” seçeneği: 500–2500 µs; yalnızca uçları kontrol edilmiş, mekanizmadan ayrılmış motorda kullan.\n'
                      'İlk hareket mevcut konum bilinmediği için hızlı olabilir. PWM kapanınca kol düşebilir: kolu destekle.\n'
                      'Omuz: tek bar → A=θ, B=180−θ. Önce başlıklar bağlantıdan ayrıkken 90° merkezle; sonra küçük hareketle yönü doğrula.\n'
                      'Nominal eşleme yük paylaşımını garanti etmez. Zorlama / vızıltı varsa gücü kes; merkez ayarı gerekir.').pack(side='bottom', fill='x', pady=(8, 0))
        self.notebook.pack(fill='both', expand=True)
        self.refresh_ports()
        self.apply_state(self.state)
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(80, self.poll)
        if connect: root.after(150, self.connect)

    def refresh_ports(self):
        self.ports['values'] = [p.device for p in list_ports.comports()]

    def make_row(self, page, channel, name, model):
        frame = tk.Frame(page, bg='white', pady=4)
        frame.pack(fill='x')
        arm = tk.BooleanVar(value=False)
        angle = tk.IntVar(value=90)
        speed = tk.IntVar(value=30)
        wide = tk.BooleanVar(value=False)
        reverse = tk.BooleanVar(value=False)
        top = tk.Frame(frame, bg='white'); top.pack(fill='x')
        check = tk.Checkbutton(top, text=f'CH {channel:02d}  {name}', variable=arm, bg='white',
                               font=('Segoe UI', 11, 'bold'), command=lambda c=channel: self.arm(c))
        check.pack(side='left')
        tk.Label(top, text=model, bg='white', fg='#7a8792').pack(side='left', padx=8)
        tk.Label(top, textvariable=angle, bg='white', fg='#215fe5', width=3).pack(side='left')
        tk.Label(top, text='° hedef', bg='white', fg='#215fe5').pack(side='left')
        ack = tk.StringVar(value='Sinyal kapalı')
        tk.Label(top, textvariable=ack, bg='white', fg='#52687b').pack(side='right')
        controls = tk.Frame(frame, bg='white'); controls.pack(fill='x')
        tk.Label(controls, text='0°', bg='white').pack(side='left')
        slider = tk.Scale(controls, from_=0, to=180, orient='horizontal', variable=angle,
                          resolution=1, tickinterval=0, showvalue=False, width=12, sliderlength=18,
                          bg='white', highlightthickness=0,
                          command=lambda value, c=channel: self.move(c))
        slider.pack(side='left', fill='x', expand=True)
        tk.Label(controls, text='180°', bg='white').pack(side='left')
        centre = ttk.Button(controls, text='90°', width=5, command=lambda c=channel: self.centre(c))
        centre.pack(side='left', padx=8)
        tk.Label(controls, text='Hız °/sn', bg='white').pack(side='left')
        speeds = ttk.Combobox(controls, textvariable=speed, values=(10, 30, 60, 90, 120, 150, 180, 240, 300, 360), width=4, state='readonly')
        speeds.pack(side='left', padx=6)
        rev = tk.Checkbutton(controls, text='Ters', variable=reverse, bg='white')
        rev.pack(side='left')
        expansion = tk.Checkbutton(controls, text='Geniş', variable=wide, bg='white')
        expansion.pack(side='left')
        fit = tk.BooleanVar(value=False)
        fit_check = None
        if channel in SHOULDERS:
            expansion.configure(state='disabled')
            fit_check = tk.Checkbutton(frame, text='Başlıklar mekanizmadan ayrık veya merkez/yön uyumu fiziksel olarak kontrol edildi',
                                       variable=fit, bg='white', fg='#744910', command=lambda: self.apply_state(self.state))
            fit_check.pack(anchor='w')
        self.rows[channel] = dict(arm=arm, angle=angle, speed=speed, wide=wide, reverse=reverse,
                                 check=check, slider=slider, centre=centre, ack=ack, fit=fit, fit_check=fit_check, speed_choices=speeds)

    def connect(self):
        self.cancel_test()
        self.pending_arms.clear()
        if self.state.get('connected'):
            self.worker.submit('disconnect')
        else:
            self.worker.submit('connect', self.port.get())

    def arm(self, channel):
        self.cancel_test()
        value = self.rows[channel]['arm'].get()
        if channel in SHOULDERS and value and not self.rows[channel]['fit'].get():
            self.rows[channel]['arm'].set(False)
            return
        self.pending_arms[channel] = value
        self.worker.submit('arm', (channel, value))

    def move(self, channel):
        mask = channel_mask(channel)
        if not self.state.get('ready') or self.state.get('enabled', 0) & mask != mask:
            return
        row = self.rows[channel]
        value = row['angle'].get()
        if row['reverse'].get(): value = 180 - value
        if channel in SHOULDERS and self.state.get('active', 0) & mask != mask and value != 90:
            return
        self.worker.submit('position', (channel, value, row['speed'].get(), row['wide'].get()))

    def centre(self, channel):
        self.rows[channel]['angle'].set(90)
        self.move(channel)

    def cancel_test(self):
        for job in self.test_jobs:
            self.root.after_cancel(job)
        self.test_jobs.clear()

    def test(self):
        if not self.state.get('ready') or self.state.get('enabled') != 1:
            return
        self.cancel_test()
        def set_angle(value):
            self.rows[0]['angle'].set(value)
            self.move(0)
        set_angle(90)
        for delay, value in ((1200, 95), (2400, 85), (3600, 90)):
            self.test_jobs.append(self.root.after(delay, lambda v=value: set_angle(v)))
        self.test_jobs.append(self.root.after(5000, self.stop))

    def stop(self):
        self.cancel_test()
        self.pending_arms.clear()
        self.state['enabled'] = 0
        self.worker.submit('stop')
        self.apply_state(self.state)

    def apply_state(self, state):
        self.state = state
        ready = state.get('ready', False)
        self.message.set(state.get('message', 'Bağlı değil'))
        self.connect_button.configure(text='Bağlantıyı kapat' if state.get('connected') else 'Bağlan')
        if not ready:
            self.cancel_test()
            self.pending_arms.clear()
        for channel, row in self.rows.items():
            mask = channel_mask(channel)
            enabled = state.get('enabled', 0) & mask == mask
            paired = channel in SHOULDERS
            running = state.get('active', 0) & mask == mask
            if channel in self.pending_arms and self.pending_arms[channel] == enabled:
                del self.pending_arms[channel]
            if channel not in self.pending_arms: row['arm'].set(enabled)
            row['check'].configure(state='normal' if ready and (not paired or row['fit'].get()) else 'disabled')
            row['centre'].configure(state='normal' if ready and enabled else 'disabled')
            row['slider'].configure(state='normal' if ready and enabled and (not paired or running) else 'disabled')
            if paired:
                row['fit_check'].configure(state='disabled' if enabled else 'normal')
            ack = state.get('acks', {}).get(channel)
            text = f'Kart hedefi: {ack[0]}° · {ack[2]}–{ack[3]} µs' if ack and enabled else 'Etkin · hareket bekliyor' if enabled else 'Sinyal kapalı'
            if paired:
                text = f'Kart hedefi: A {ack[0]}° / B {180-ack[0]}°' if ack and running else 'Önce 90° merkez düğmesine bas' if enabled else 'İki motorun sinyali kapalı'
            row['ack'].set(text)
        self.test_button.configure(state='normal' if ready and state.get('enabled') == 1 else 'disabled')

    def poll(self):
        if self.closed: return
        try: self.apply_state(self.worker.updates.get_nowait())
        except queue.Empty: pass
        self.root.after(80, self.poll)

    def close(self):
        self.closed = True
        self.cancel_test()
        self.worker.submit('close')
        self.worker.join(timeout=1)
        self.root.destroy()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default='COM3')
    parser.add_argument('--connect', action='store_true')
    args = parser.parse_args()
    root = tk.Tk()
    App(root, args.port, args.connect)
    root.mainloop()
