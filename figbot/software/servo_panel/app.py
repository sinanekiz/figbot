"""Small native Windows panel. Opening/connecting never sends a motion command."""
import argparse
import math
import collections
import queue
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from serial.tools import list_ports

try:
    from .controller import ServoController
except ImportError:
    from controller import ServoController


class Worker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.tasks = collections.deque()
        self.lock = threading.Lock()
        self.updates = queue.Queue(maxsize=1)
        self.done = threading.Event()
        self.controller = ServoController(log_path=Path(__file__).resolve().parents[2] /
                                          ".codex_artifacts/arduino/panel-commands.log")

    def submit(self, action, value=None):
        with self.lock:
            if action in ("close", "disconnect") or value == "x":
                self.tasks.clear()
            elif action == "position" and self.tasks and self.tasks[-1][0] == "position":
                self.tasks[-1] = (action, value)
                return
            if not self.tasks:
                self.tasks.append((action, value))

    def publish(self, busy=False):
        state = self.controller.snapshot()
        state["busy"] = busy
        try:
            self.updates.get_nowait()
        except queue.Empty:
            pass
        self.updates.put_nowait(state)

    def run(self):
        try:
            while not self.done.is_set():
                with self.lock:
                    task = self.tasks.popleft() if self.tasks else None
                try:
                    if task:
                        action, value = task
                        if action == "close":
                            break
                        if action == "connect":
                            self.publish(busy=True)
                            self.controller.connect(value)
                        elif action == "disconnect":
                            self.controller.disconnect()
                            self.controller.log("Bağlantı kapatıldı.")
                        elif action == "command":
                            self.controller.send(value)
                        elif action == "position":
                            self.controller.set_position(*value)
                    self.controller.poll()
                except Exception as exc:
                    self.controller.log("Hata: " + str(exc))
                    self.controller.disconnect()
                self.publish()
                self.done.wait(0.04)
        finally:
            self.controller.disconnect()
            self.done.set()


def angle_from_point(x, y, cx, cy):
    return round(max(0, min(180, math.degrees(math.atan2(max(0, cy - y), x - cx)))))


class App:
    def __init__(self, root, initial_port):
        self.root = root
        self.worker = Worker()
        self.worker.start()
        self.state = {"ready": False, "active": False, "busy": False}
        self.closed = self.dragging = False
        self.last_logs = None
        self.pending_position = None
        self.angle = 90
        root.title("FIGBOT · Motor kontrolü")
        root.geometry("740x900")
        root.minsize(720, 880)
        root.configure(bg="#f5f7fb")
        root.option_add("*Font", "{Segoe UI} 11")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", padding=5, font=("Segoe UI", 11))

        outer = tk.Frame(root, bg="#f5f7fb", padx=24, pady=16)
        outer.pack(fill="both", expand=True)
        self.label(outer, "Motor kontrolü", 24, "#172338", bold=True).pack(anchor="w")
        self.label(outer, "Kadranı sürükle, hedef konumu değiştir.", 11, "#637086").pack(anchor="w", pady=(3, 12))
        connection = tk.Frame(outer, bg="#f5f7fb")
        connection.pack(fill="x")
        self.port = tk.StringVar(value=initial_port)
        ports = [p.device for p in list_ports.comports() if p.vid is not None]
        self.selector = ttk.Combobox(connection, textvariable=self.port, values=ports, width=10, state="readonly")
        self.selector.pack(side="left", padx=(0, 10))
        self.connect_button = self.button(connection, "Bağlan", self.connect, "#e5eaf3", "#253750")
        self.connect_button.pack(side="left")
        self.status_label = self.label(connection, "Bağlı değil", 11, "#637086")
        self.status_label.pack(side="right")

        panel = tk.Frame(outer, bg="white", padx=16, pady=14, highlightthickness=1, highlightbackground="#e2e7ef")
        panel.pack(fill="x", pady=(14, 12))
        status_row = tk.Frame(panel, bg="white")
        status_row.pack(fill="x")
        self.signal = self.label(status_row, "Sinyal kapalı", 13, "#172338", bg="white", bold=True)
        self.signal.pack(side="left")
        self.ack_label = self.label(status_row, "Kart hedefi: —", 10, "#637086", bg="white")
        self.ack_label.pack(side="right")
        self.countdown = self.label(panel, "Başlamak için Arduino’ya bağlan.", 10, "#637086", bg="white")
        self.countdown.pack(anchor="w", pady=(4, 0))

        self.dial = tk.Canvas(panel, height=215, bg="white", highlightthickness=0, cursor="hand2", takefocus=True)
        self.dial.pack(fill="x")
        self.dial.bind("<Configure>", lambda _: self.draw_dial())
        self.dial.bind("<Button-1>", self.dial_press)
        self.dial.bind("<B1-Motion>", self.dial_move)
        self.dial.bind("<ButtonRelease-1>", self.dial_release)
        self.dial.bind("<Left>", lambda _: self.go(self.angle + 1))
        self.dial.bind("<Right>", lambda _: self.go(self.angle - 1))
        self.label(panel, "Hedef açı (komut) · 500–2500 µs · Fiziksel uçlar henüz doğrulanmadı.", 10, "#637086", bg="white").pack()

        presets = tk.Frame(panel, bg="white")
        presets.pack(fill="x", pady=(10, 12))
        for column in range(3):
            presets.columnconfigure(column, weight=1, uniform="preset")
        self.left = self.button(presets, "← Sol konum", lambda: self.go(99), "#edf2fa", "#21334d")
        self.left.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.centre = self.button(presets, "Merkez · 90°", lambda: self.go(90), "#215fe5", "white")
        self.centre.grid(row=0, column=1, sticky="ew", padx=5)
        self.right = self.button(presets, "Sağ konum →", lambda: self.go(81), "#edf2fa", "#21334d")
        self.right.grid(row=0, column=2, sticky="ew", padx=(5, 0))

        speed_row = tk.Frame(panel, bg="white")
        speed_row.pack(fill="x")
        self.speed_value = tk.IntVar(value=60)
        self.maximum = tk.BooleanVar(value=False)
        self.speed_label = self.label(speed_row, "Hız sınırı: 60°/sn (komut)", 12, "#253750", bg="white", bold=True)
        self.speed_label.pack(side="left")
        self.max_check = tk.Checkbutton(speed_row, text="En hızlı (rampa yok)", variable=self.maximum,
                                       command=self.speed_changed, bg="white", activebackground="white",
                                       fg="#253750", selectcolor="white", font=("Segoe UI", 10))
        self.max_check.pack(side="right")
        self.speed_slider = tk.Scale(panel, from_=30, to=360, orient="horizontal", resolution=10,
                                     variable=self.speed_value, showvalue=False, bg="white",
                                     troughcolor="#e5eaf3", highlightthickness=0, relief="flat",
                                     sliderrelief="flat", command=lambda _: self.speed_changed())
        self.speed_slider.pack(fill="x", pady=(2, 0))
        self.label(panel, "Düşük ayar hareketi yavaşlatır; en hızlı ayar motorun kendi hızını kullanır.",
                   10, "#637086", bg="white").pack(anchor="w", pady=(2, 12))

        actions = tk.Frame(panel, bg="white")
        actions.pack(fill="x")
        actions.columnconfigure((0, 1), weight=1, uniform="actions")
        self.fast = self.button(actions, "3 tur · dar aralık", lambda: self.command("t"), "#e7efff", "#214d99")
        self.fast.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.stop = self.button(actions, "Sinyali kapat", lambda: self.command("x"), "#fde9e8", "#ad302a")
        self.stop.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.label(panel, "Sinyali kapatmak motorun elektriğini kesmez.", 10, "#637086", bg="white").pack(pady=(7, 0))

        self.label(outer, "Kart yanıtları", 11, "#253750", bold=True).pack(anchor="w")
        self.logbox = tk.Text(outer, height=5, bg="white", fg="#36465d", relief="flat", padx=10, pady=8,
                             font=("Consolas", 10), wrap="word", state="disabled")
        self.logbox.pack(fill="both", expand=True, pady=(6, 8))
        self.label(outer, "Konum ve hız komutları gösterilir; motorun gerçek hareketi ölçülmez.", 10, "#637086").pack(anchor="w")
        self.apply_state(self.state)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(100, self.refresh)

    @staticmethod
    def label(parent, text, size, color, bg="#f5f7fb", bold=False):
        return tk.Label(parent, text=text, bg=bg, fg=color, anchor="w",
                        font=("Segoe UI", size, "bold" if bold else "normal"))

    @staticmethod
    def button(parent, text, command, background, foreground):
        return tk.Button(parent, text=text, command=command, bg=background, fg=foreground,
                         activebackground=background, activeforeground=foreground,
                         disabledforeground="#8c96a8", relief="flat", borderwidth=0,
                         cursor="hand2", padx=12, pady=8, font=("Segoe UI", 11, "bold"))

    def can_move(self):
        return self.state["ready"] and not self.state.get("busy") and not self.state.get("fast_running")

    def dial_geometry(self):
        return self.dial.winfo_width() / 2, 174, 132

    def draw_dial(self):
        self.dial.delete("all")
        cx, cy, radius = self.dial_geometry()
        color = "#215fe5" if self.can_move() else "#8c96a8"
        self.dial.create_arc(cx-radius, cy-radius, cx+radius, cy+radius,
                             start=0, extent=180, style="arc", outline="#e5eaf3", width=12)
        for angle in range(0, 181, 30):
            a = math.radians(angle)
            self.dial.create_line(cx+(radius-14)*math.cos(a), cy-(radius-14)*math.sin(a),
                                  cx+(radius-23)*math.cos(a), cy-(radius-23)*math.sin(a),
                                  fill="#a7b2c3", width=2)
            self.dial.create_text(cx+(radius+22)*math.cos(a), cy-(radius+22)*math.sin(a),
                                  text=f"{angle}°", fill="#637086", font=("Segoe UI", 10))
        a = math.radians(self.angle)
        x, y = cx+radius*math.cos(a), cy-radius*math.sin(a)
        self.dial.create_line(cx, cy, x, y, fill=color, width=4)
        self.dial.create_oval(cx-5, cy-5, cx+5, cy+5, fill=color, outline=color)
        self.dial.create_oval(x-10, y-10, x+10, y+10, fill=color, outline="white", width=3)
        self.dial.create_text(cx, cy+24, text=f"{self.angle}°", fill="#172338", font=("Segoe UI", 21, "bold"))

    def dial_press(self, event):
        if not self.can_move():
            return
        self.dial.focus_set()
        self.dragging = True
        self.dial_move(event)

    def dial_move(self, event):
        if not self.dragging or not self.can_move():
            return
        cx, cy, _ = self.dial_geometry()
        if (event.x-cx)**2 + (event.y-cy)**2 < 64:
            return
        self.angle = angle_from_point(event.x, event.y, cx, cy)
        self.draw_dial()
        self.queue_position()

    def dial_release(self, event):
        if not self.dragging:
            return
        self.dial_move(event)
        self.dragging = False
        self.cancel_pending()
        self.flush_position()

    def go(self, angle):
        if self.can_move():
            self.angle = max(0, min(180, int(angle)))
            self.draw_dial()
            self.queue_position()

    def queue_position(self):
        if self.can_move() and self.pending_position is None:
            self.pending_position = self.root.after(60, self.flush_position)

    def flush_position(self):
        self.pending_position = None
        if self.can_move():
            speed = 0 if self.maximum.get() else int(self.speed_value.get())
            self.worker.submit("position", (self.angle, speed))

    def cancel_pending(self):
        if self.pending_position is not None:
            self.root.after_cancel(self.pending_position)
            self.pending_position = None

    def speed_changed(self):
        maximum = self.maximum.get()
        self.speed_label.configure(text="Hız: en hızlı" if maximum else f"Hız sınırı: {self.speed_value.get()}°/sn (komut)")
        self.speed_slider.configure(state="normal" if self.can_move() and not maximum else "disabled")
        self.queue_position()

    def connect(self):
        if self.state.get("busy"):
            return
        if self.state["ready"]:
            self.cancel_pending()
            self.worker.submit("disconnect")
        elif self.port.get():
            self.state["busy"] = True
            self.apply_state(self.state)
            self.worker.submit("connect", self.port.get())

    def command(self, value):
        self.cancel_pending()
        self.dragging = False
        self.worker.submit("command", value)

    def apply_state(self, state):
        self.state = state
        ready, active, busy = state["ready"], state["active"], state.get("busy", False)
        self.connect_button.configure(text="Bağlantıyı kes" if ready else "Bağlan",
                                      state="disabled" if busy else "normal")
        self.selector.configure(state="disabled" if ready or busy else "readonly")
        self.status_label.configure(text="Bağlanıyor…" if busy else ("● Bağlı" if ready else "Bağlı değil"),
                                    fg="#15734e" if ready else "#637086")
        fast_running = state.get("fast_running", False)
        enabled = ready and not busy and not fast_running
        for button in (self.left, self.right, self.centre, self.fast, self.max_check):
            button.configure(state="normal" if enabled else "disabled")
        self.speed_slider.configure(state="normal" if enabled and not self.maximum.get() else "disabled")
        self.stop.configure(state="normal" if ready else "disabled")
        self.signal.configure(text="Hızlı test sürüyor" if fast_running else ("Sinyal etkin" if active else "Sinyal kapalı"))
        remaining = state.get("remaining")
        if fast_running:
            message = "3 tur sonunda merkezlenir; test hız ayarından bağımsızdır."
        elif active and remaining is not None:
            message = f"Son komuttan sonra otomatik kapanmaya yaklaşık {remaining:.0f} sn."
        elif ready:
            message = "Kadranı sürükleyerek hareketi başlatabilirsin."
        else:
            message = "Başlamak için Arduino’ya bağlan."
        self.countdown.configure(text=message)
        ack = state.get("target_angle")
        self.ack_label.configure(text="Kart hedefi: —" if ack is None else f"Kart hedefi: {ack}°")
        self.draw_dial()

    def refresh(self):
        if self.closed:
            return
        try:
            self.state = self.worker.updates.get_nowait()
            self.apply_state(self.state)
            logs = self.state["logs"]
            if logs != self.last_logs:
                self.logbox.configure(state="normal")
                self.logbox.delete("1.0", "end")
                self.logbox.insert("end", "\n".join(f"{stamp}  {line}" for stamp, line in logs))
                self.logbox.see("end")
                self.logbox.configure(state="disabled")
                self.last_logs = logs
        except queue.Empty:
            pass
        self.root.after(100, self.refresh)

    def close(self):
        self.closed = True
        self.cancel_pending()
        self.worker.submit("close")
        self.root.withdraw()
        self.wait_closed()

    def wait_closed(self):
        if self.worker.done.is_set():
            self.root.destroy()
        else:
            self.root.after(50, self.wait_closed)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM3")
    parser.add_argument("--connect", action="store_true")
    args = parser.parse_args()
    root = tk.Tk()
    app = App(root, args.port)
    if args.connect:
        root.after(250, app.connect)
    root.mainloop()
