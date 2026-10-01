"""Run: python -m software.st3215_test.app [--demo]. No automatic connection."""
import argparse
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import serial
from serial.tools import list_ports
from .protocol import Bus, BusError, BusTimeout
from .controller import Controller


class Worker(threading.Thread):
    def __init__(self, demo=False):
        super().__init__(daemon=True)
        self.demo = demo
        self.jobs = queue.Queue()
        self.events = queue.Queue()
        self.release = threading.Event()
        self.shutdown = threading.Event()
        self.lock = threading.Lock()
        self.pending_move = None
        self.controller = None
        self.last_poll = 0

    def submit(self, name, *args):
        self.jobs.put((name, args))

    def move(self, position, speed):
        with self.lock:
            self.pending_move = (position, speed, time.monotonic())

    def request_stop(self):
        self.release.set()

    def clear_pending(self):
        with self.lock:
            self.pending_move = None
        while True:
            try:
                self.jobs.get_nowait()
            except queue.Empty:
                break

    def emit(self, kind, value):
        self.events.put((kind, value))

    def state(self):
        c = self.controller
        self.emit('state', {'connected': c is not None, 'armed': bool(c and c.armed),
                           'id': c.servo_id if c else None,
                           'limits': c.limits if c else (0, 4095),
                           'origin': c.origin if c else None})

    def disconnect(self):
        if self.controller:
            try:
                self.controller.stop()
            finally:
                self.controller.bus.close()
                self.controller = None

    def execute(self, name, args):
        if name == 'connect':
            if self.controller:
                raise BusError('Önce mevcut bağlantıyı kes.')
            port, baud = args
            if self.demo:
                from .demo import DemoBus
                bus = DemoBus()
            else:
                bus = Bus(serial.Serial(port, baudrate=baud, timeout=0.015, write_timeout=0.2))
            self.controller = Controller(bus, lambda: self.release.is_set() or self.shutdown.is_set())
            self.emit('status', 'USB açık. Motor ID seçip Oku düğmesine bas; henüz hareket komutu yok.')
        elif name == 'disconnect':
            self.disconnect()
            self.emit('status', 'Bağlantı kapalı. Tork kapatma gönderildi; güç kesme yerine geçmez.')
        elif name == 'inspect':
            model, mode, feedback = self.controller.inspect(*args)
            self.emit('feedback', feedback)
            self.emit('status', f'ID {args[0]} bulundu · Model kodu {model} · Mod {mode}. Henüz etkinleştirilmedi.')
        elif name == 'scan':
            if self.controller.armed:
                raise BusError('Arama öncesi torku kapat.')
            found = []
            for servo_id in range(1, 7):
                if self.release.is_set() or self.shutdown.is_set():
                    return
                try:
                    self.controller.bus.ping(servo_id)
                    found.append(servo_id)
                except BusTimeout:
                    pass
            self.emit('status', 'Bulunan ID: ' + (', '.join(map(str, found)) or 'yok. Güç, B jumperı ve COM portunu kontrol et.'))
        elif name == 'arm':
            feedback = self.controller.arm(*args)
            self.emit('feedback', feedback)
            self.emit('target', feedback.position)
            low, high = self.controller.limits
            self.emit('status', f'Test etkin · Aralık {(high-low)*360/4096:.0f}° ({low*360/4096:.1f}–{high*360/4096:.1f}°). Hız değişimi bir sonraki hareket komutunda uygulanır.')
        elif name == 'change_id':
            self.controller.change_id(*args)
            self.emit('status', f'Yeni ID {self.controller.servo_id} okundu, EEPROM kilidi doğrulandı. Motoru etiketle.')
        else:
            raise ValueError(name)

    def run(self):
        while not self.shutdown.is_set():
            name = None
            try:
                if self.release.is_set():
                    name = 'stop'
                    self.clear_pending()
                    self.release.clear()
                    if self.controller:
                        self.controller.stop()
                    self.emit('status', 'Tork kapatma tüm hatta gönderildi. Motor serbest kalır; mekanik fren değildir.')
                    self.emit('busy', False)
                    self.state()
                try:
                    name, args = self.jobs.get_nowait()
                except queue.Empty:
                    name = None
                if name:
                    self.execute(name, args)
                    self.state()
                    self.emit('busy', False)
                if self.release.is_set():
                    continue
                with self.lock:
                    movement, self.pending_move = self.pending_move, None
                if movement and self.controller and self.controller.armed:
                    position, speed, created = movement
                    if time.monotonic() - created < 0.5:
                        self.controller.move(position, speed)
                c = self.controller
                if c and c.servo_id and time.monotonic() - self.last_poll > 0.25:
                    feedback = c.bus.feedback(c.servo_id)
                    self.last_poll = time.monotonic()
                    if c.armed and (feedback.temperature >= 60 or not 9 <= feedback.voltage <= 12.6):
                        raise BusError('Gerilim/sıcaklık test sınırı dışında; test kesildi.')
                    self.emit('feedback', feedback)
            except Exception as exc:
                self.clear_pending()
                c = self.controller
                release_note = ''
                if name == 'stop':
                    release_note = ' Tork kapatma iletilemedi; motor gücünü kes.'
                if c and (c.armed or name == 'arm'):
                    try:
                        c.stop()
                        release_note = ' Tork kapatma gönderildi; yanıtla doğrulanmadı.'
                    except Exception:
                        release_note = ' Tork kapatma iletilemedi; motor gücünü kes.'
                if c:
                    c.servo_id = None
                self.emit('error', str(exc) + release_note)
                self.state()
                self.emit('busy', False)
            self.shutdown.wait(0.025)
        try:
            self.disconnect()
        except Exception:
            pass


class App:
    def __init__(self, root, demo=False):
        self.root = root
        self.worker = Worker(demo)
        self.worker.start()
        self.connected = self.armed = self.busy = False
        self.selected = None
        self.feedback_time = 0
        self.syncing = False
        self.demo = demo
        root.title('FIGBOT · ST3215 Motor Testi · Hızlı profil' + (' — DEMO / MOTOR YOK' if demo else ''))
        root.geometry('1020x820')
        root.minsize(920, 760)
        root.configure(bg='#eef3f5')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 11))
        style.configure('TFrame', background='#eef3f5')
        style.configure('TLabel', background='#eef3f5', foreground='#183b48')
        style.configure('TLabelframe', background='#eef3f5')
        style.configure('TLabelframe.Label', background='#eef3f5', foreground='#183b48', font=('Segoe UI', 11, 'bold'))
        style.configure('TButton', padding=(12, 8))
        main = ttk.Frame(root, padding=22)
        main.pack(fill='both', expand=True)
        ttk.Label(main, text='FIGBOT  /  MOTOR TESTİ', font=('Segoe UI', 23, 'bold')).pack(anchor='w')
        ttk.Label(main, text='ST3215 · Bus Servo Adapter (A) · Tek motorla masa üzerinde test' + ('   [DEMO]' if demo else '')).pack(anchor='w', pady=(2, 12))
        wiring = 'PC ─ USB-C → Kart [B jumper] ─ 3 uçlu kablo → Tek ST3215\n12 V / 5 A adaptör → Kartın siyah DC girişi   |   UNO ve PCA9685 kullanılmaz.'
        ttk.Label(main, text=wiring, padding=12, background='#dcebe9').pack(fill='x', pady=(0, 12))
        connection = ttk.Frame(main)
        connection.pack(fill='x')
        self.port = tk.StringVar()
        self.port_box = ttk.Combobox(connection, textvariable=self.port, width=37, state='readonly')
        self.port_box.pack(side='left')
        self.refresh_button = ttk.Button(connection, text='Yenile', command=self.refresh)
        self.refresh_button.pack(side='left', padx=5)
        self.baud = tk.StringVar(value='1000000')
        self.baud_box = ttk.Combobox(connection, textvariable=self.baud, values=['1000000', '500000', '250000', '115200'], width=10, state='readonly')
        self.baud_box.pack(side='left', padx=5)
        self.connect_button = ttk.Button(connection, text='Bağlan', command=self.connect)
        self.connect_button.pack(side='left', padx=5)
        select = ttk.Frame(main)
        select.pack(fill='x', pady=10)
        ttk.Label(select, text='Motor ID').pack(side='left')
        self.id_var = tk.StringVar(value='1')
        self.id_box = ttk.Spinbox(select, from_=1, to=253, textvariable=self.id_var, width=5)
        self.id_box.pack(side='left', padx=8)
        self.inspect_button = ttk.Button(select, text='Oku', command=lambda: self.id_action('inspect'))
        self.inspect_button.pack(side='left')
        self.scan_button = ttk.Button(select, text='ID 1–6 ara', command=lambda: self.job('scan'))
        self.scan_button.pack(side='left', padx=8)
        self.readings = tk.StringVar(value='Konum: —    Gerilim: —    Sıcaklık: —')
        ttk.Label(main, textvariable=self.readings, font=('Segoe UI', 15, 'bold'), padding=12, background='white').pack(fill='x')
        self.detail = tk.StringVar(value='Canlı veri bekleniyor. Bağlanmak hareket başlatmaz.')
        ttk.Label(main, textvariable=self.detail).pack(anchor='w', pady=5)
        self.confirm = tk.BooleanVar(value=False)
        self.check = ttk.Checkbutton(main, text='Yalnız bir adet 12 V ST3215 bağlı; kola takılı değil, gövdesi sabit ve başlığı serbest.', variable=self.confirm, command=self.gates)
        self.check.pack(anchor='w', pady=9)
        motion = ttk.LabelFrame(main, text='Motor hareket testi', padding=12)
        motion.pack(fill='x')
        row = ttk.Frame(motion)
        row.pack(fill='x')
        self.arm_button = ttk.Button(row, text='Testi etkinleştir', command=lambda: self.job('arm', self.confirm.get(), int(self.travel.get())))
        self.arm_button.pack(side='left')
        ttk.Label(row, text='Hız (°/sn)').pack(side='left', padx=(18, 8))
        self.speed = tk.StringVar(value='Maksimum')
        self.speed_box = ttk.Combobox(row, values=['15', '30', '60', '120', '180', '270', 'Maksimum'], textvariable=self.speed, width=11, state='readonly')
        self.speed_box.pack(side='left')
        ttk.Label(row, text='Aralık (°)').pack(side='left', padx=(18, 8))
        self.travel = tk.StringVar(value='270')
        self.travel_box = ttk.Combobox(row, values=['60', '180', '270'], textvariable=self.travel, width=6, state='readonly')
        self.travel_box.pack(side='left')
        self.target = tk.DoubleVar(value=0)
        self.scale = ttk.Scale(motion, from_=0, to=4095, variable=self.target, command=self.slide)
        self.scale.pack(fill='x', pady=12)
        bottom = ttk.Frame(motion)
        bottom.pack(fill='x')
        self.minus = ttk.Button(bottom, text='−5°', command=lambda: self.nudge(-5))
        self.minus.pack(side='left')
        self.plus = ttk.Button(bottom, text='+5°', command=lambda: self.nudge(5))
        self.plus.pack(side='left', padx=8)
        self.target_text = tk.StringVar(value='Hedef, testi açarken motorun mevcut konumundan alınır.')
        ttk.Label(bottom, textvariable=self.target_text).pack(side='left', padx=8)
        self.stop_button = tk.Button(main, text='TORKU KAPAT · MOTOR SERBEST KALIR  [Esc]', command=self.stop,
                                     bg='#ac3439', fg='white', font=('Segoe UI', 12, 'bold'), relief='flat', pady=10)
        self.stop_button.pack(fill='x', pady=12)
        idrow = ttk.Frame(main)
        idrow.pack(fill='x')
        ttk.Label(idrow, text='Yeni ID (motorları tek tek numarala):').pack(side='left')
        self.new_id = tk.StringVar(value='2')
        self.new_id_box = ttk.Spinbox(idrow, from_=1, to=253, textvariable=self.new_id, width=5)
        self.new_id_box.pack(side='left', padx=8)
        self.change_button = ttk.Button(idrow, text='ID kaydet', command=self.change_id)
        self.change_button.pack(side='left')
        self.status = tk.StringVar(value='Maksimum hız + maksimum ivme seçili. Yalnız mekanizmadan ayrılmış motor testi. Bağlantıda otomatik hareket yok.')
        ttk.Label(main, textvariable=self.status, wraplength=940, padding=(0, 12), font=('Segoe UI', 11, 'bold')).pack(fill='x')
        root.bind('<Escape>', lambda _: self.stop())
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.refresh()
        self.gates()
        root.after(50, self.drain)

    def refresh(self):
        ports = list(list_ports.comports())
        self.port_map = {f'{p.device} · {p.description}': p.device for p in ports}
        if self.demo:
            self.port_map = {'DEMO — seri port kullanılmaz': 'DEMO'}
        values = list(self.port_map)
        self.port_box.configure(values=values)
        preferred = next((key for key in values if 'Bluetooth' not in key), '')
        self.port.set(preferred)

    def job(self, name, *args):
        if self.busy:
            return
        self.busy = True
        self.gates()
        self.worker.submit(name, *args)

    def connect(self):
        if self.connected:
            self.job('disconnect')
        elif self.port.get() in self.port_map:
            self.job('connect', self.port_map[self.port.get()], int(self.baud.get()))
        else:
            self.status.set('USB kartı görünmüyor. Veri kablosunu takıp Yenile düğmesine bas. Bluetooth COM portunu seçme.')

    def id_action(self, name):
        try:
            value = int(self.id_var.get())
            if not 1 <= value <= 253:
                raise ValueError()
            self.job(name, value)
        except ValueError:
            self.status.set('ID, 1–253 arasında tam sayı olmalı.')

    def change_id(self):
        try:
            value = int(self.new_id.get())
            if not 1 <= value <= 253:
                raise ValueError()
        except ValueError:
            self.status.set('Yeni ID, 1–253 arasında tam sayı olmalı.')
            return
        if messagebox.askokcancel('Kalıcı motor ID', f'Fiziksel olarak yalnız bir motor bağlı olmalı.\nID {self.selected} → {value} olarak kalıcı kaydedilsin mi?'):
            self.job('change_id', value, self.confirm.get())

    def gates(self):
        def enabled(widget, ok):
            widget.configure(state='normal' if ok else 'disabled')
        enabled(self.connect_button, not self.busy)
        self.connect_button.configure(text='Bağlantıyı kes' if self.connected else 'Bağlan')
        enabled(self.refresh_button, not self.connected and not self.busy)
        self.port_box.configure(state='disabled' if self.connected or self.busy else 'readonly')
        self.baud_box.configure(state='disabled' if self.connected or self.busy else 'readonly')
        idle = self.connected and not self.busy and not self.armed
        for widget in (self.inspect_button, self.scan_button, self.id_box):
            enabled(widget, idle)
        enabled(self.arm_button, idle and self.selected is not None and self.confirm.get())
        enabled(self.change_button, idle and self.selected is not None and self.confirm.get())
        for widget in (self.scale, self.minus, self.plus):
            enabled(widget, self.armed and not self.busy)
        # The bench declaration cannot be unchecked while motion is enabled.
        enabled(self.check, not self.armed and not self.busy)
        self.travel_box.configure(state='disabled' if self.armed or self.busy else 'readonly')

    def slide(self, _=None):
        if self.syncing or not self.armed or self.busy:
            return
        value = round(self.target.get())
        self.target_text.set(f'Hedef {value * 360 / 4096:.1f}° · {value} adım')
        speed = self.speed.get()
        self.worker.move(value, speed if speed == 'Maksimum' else int(speed))

    def nudge(self, degrees):
        value = min(float(self.scale['to']), max(float(self.scale['from']), self.target.get() + degrees * 4096 / 360))
        self.target.set(value)
        self.slide()

    def stop(self):
        self.armed = False
        self.gates()
        self.worker.request_stop()

    def drain(self):
        while True:
            try:
                kind, value = self.worker.events.get_nowait()
            except queue.Empty:
                break
            if kind == 'state':
                self.connected, self.armed, self.selected = value['connected'], value['armed'], value['id']
                if self.selected is not None:
                    self.id_var.set(str(self.selected))
                self.syncing = True
                self.scale.configure(from_=value['limits'][0], to=value['limits'][1])
                self.syncing = False
                if not self.connected:
                    self.feedback_time = 0
            elif kind == 'target':
                self.syncing = True
                self.target.set(value)
                self.syncing = False
                self.target_text.set(f'Başlangıç {value * 360 / 4096:.1f}° · Sürükle veya ±5° kullan')
            elif kind == 'feedback':
                self.feedback_time = time.monotonic()
                self.readings.set(f'Konum: {value.degrees:.1f}°    Gerilim: {value.voltage:.1f} V    Sıcaklık: {value.temperature} °C')
                self.detail.set(f'Konum {value.position}/4096 · Hız {value.speed * 360 / 4096:.1f} °/sn · Akım ham: {value.current_raw} · ' + ('Hareket ediyor' if value.moving else 'Hareket bayrağı kapalı'))
            elif kind == 'busy':
                self.busy = value
            elif kind in ('status', 'error'):
                self.status.set(value)
                if kind == 'error':
                    self.feedback_time = 0
        if not self.feedback_time or time.monotonic() - self.feedback_time > 1.5:
            self.readings.set('Konum: —    Gerilim: —    Sıcaklık: —')
            self.detail.set('Canlı veri yok / güncel değil. Son değerler geçerli ölçüm olarak gösterilmez.')
        self.gates()
        self.root.after(50, self.drain)

    def close(self):
        self.worker.request_stop()
        self.worker.shutdown.set()
        self.worker.join(timeout=1.5)
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true', help='No serial port, simulated single motor')
    args = parser.parse_args()
    root = tk.Tk()
    App(root, args.demo)
    root.mainloop()


if __name__ == '__main__':
    main()
