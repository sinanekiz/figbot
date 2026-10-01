"""Single unloaded-servo controller; all serial access belongs to one worker."""
import time
import re
from pathlib import Path

import serial


class ServoController:
    def __init__(self, factory=serial.Serial, clock=time.monotonic, sleep=time.sleep, log_path=None):
        self.factory, self.clock, self.sleep = factory, clock, sleep
        self.link = None
        self.ready = False
        self.active = False
        self.fast_running = False
        self.target_angle = None
        self.target_speed = None
        self.last_command_time = None
        self.buffer = ""
        self.logs = []
        self.log_path = Path(log_path) if log_path else None

    def log(self, text):
        self.logs.append((time.strftime("%H:%M:%S"), text))
        self.logs = self.logs[-100:]
        if self.log_path:
            try:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                with self.log_path.open("a", encoding="utf-8") as stream:
                    stream.write(time.strftime("%Y-%m-%d %H:%M:%S ") + text + "\n")
            except OSError:
                pass

    def connect(self, port):
        self.disconnect()
        self.buffer = ""
        try:
            self.link = self.factory(port=port, baudrate=115200, timeout=0, write_timeout=0.5)
            self.log(f"{port} açıldı; test yazılımının yanıtı bekleniyor.")
            deadline = self.clock() + 5
            while self.clock() < deadline and not self.ready:
                self.poll()
                self.sleep(0.03)
            if not self.ready:
                raise RuntimeError("Karttan beklenen test yazılımı yanıtı gelmedi.")
            self.log("Bağlantı hazır. Konum veya hızlı test düğmesine basabilirsin.")
        except Exception:
            self.disconnect()
            raise

    def poll(self):
        if not self.link:
            return
        waiting = self.link.in_waiting
        if waiting:
            self.buffer += self.link.read(min(waiting, 4096)).decode("utf-8", errors="replace")
            if len(self.buffer) > 8192:
                self.buffer = ""
                raise RuntimeError("Beklenmeyen uzun seri veri; bağlantı durduruldu.")
            while "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)
                self.handle_line(line.strip())

    def handle_line(self, line):
        if not line:
            return
        if line == "FIGBOT_SERVO_CHECK_V5 Pangle,speed c l r t x":
            self.ready, self.active = True, False
            self.fast_running = False
            self.last_command_time = None
            self.target_angle = self.target_speed = None
            self.log("Kart yanıt verdi; hareket sinyali kapalı.")
        elif self.ready and line.startswith("Centre: 1500us"):
            self.active = True
            self.fast_running = False
            self.last_command_time = self.clock()
            self.log("Kart onayı: merkez komutu (1500 µs).")
        elif self.ready and re.fullmatch(r"Position: \d+,\d+", line):
            angle, speed = map(int, line.removeprefix("Position: ").split(","))
            if not (0 <= angle <= 180 and (speed == 0 or 30 <= speed <= 360)):
                return
            self.active = True
            self.fast_running = False
            self.last_command_time = self.clock()
            self.target_angle, self.target_speed = angle, speed
            speed_text = "en hızlı" if speed == 0 else f"{speed}°/sn komut hızı"
            self.log(f"Kart onayı: hedef {angle}°, {speed_text}.")
        elif self.ready and line == "Small movement requested":
            self.active = True
            self.fast_running = False
            self.last_command_time = self.clock()
            self.log("Kart onayı: küçük hareket komutu.")
        elif self.ready and line.startswith("Fast test started:"):
            self.active = True
            self.fast_running = True
            self.last_command_time = self.clock()
            self.log("Hızlı test başladı: 3 tur, 1000–2000 µs. Gerçek açı ölçülmedi.")
        elif self.ready and line.startswith("Fast target:"):
            self.log("Kart hedefi: " + line.removeprefix("Fast target: "))
        elif line in ("Signal disabled", "Timeout: signal disabled", "Fast test finished: signal disabled"):
            self.active = False
            self.fast_running = False
            self.last_command_time = None
            messages = {"Signal disabled": "Kart onayı: sinyal kapalı.",
                        "Timeout: signal disabled": "10 saniye doldu; kart sinyali kapattı.",
                        "Fast test finished: signal disabled": "Hızlı komut dizisi bitti; sinyal kapalı."}
            self.log(messages[line])

    def send(self, command):
        if command not in ("c", "l", "r", "t", "x"):
            raise ValueError("İzin verilmeyen komut.")
        if not self.ready or not self.link:
            raise RuntimeError("Önce Arduino bağlantısını aç.")
        if self.fast_running and command != "x":
            self.log("Hızlı test sürüyor; bitmesini bekle veya Sinyali kapat düğmesine bas.")
            return
        self.link.write(command.encode("ascii"))
        names = {"c": "Merkezle", "l": "Sol (1600 µs)",
                 "r": "Sağ (1400 µs)", "t": "3 tur hızlı test", "x": "Sinyali kapat"}
        self.log("Gönderildi: " + names[command])

    def set_position(self, angle, speed):
        if type(angle) is not int or type(speed) is not int or not (0 <= angle <= 180) or not (speed == 0 or 30 <= speed <= 360):
            raise ValueError("Açı 0–180; hız 0 (en hızlı) veya 30–360 olmalı.")
        if not self.ready or not self.link:
            raise RuntimeError("Önce Arduino bağlantısını aç.")
        if self.fast_running:
            return
        self.link.write(f"P{angle},{speed}\n".encode("ascii"))

    def disconnect(self):
        if self.link:
            try:
                if self.ready:
                    self.link.write(b"x")
            except (OSError, serial.SerialException):
                pass
            finally:
                self.link.close()
                self.link = None
        self.ready, self.active = False, False
        self.fast_running = False
        self.last_command_time = None

    def snapshot(self):
        remaining = None
        if self.active and self.last_command_time is not None:
            remaining = max(0, 10 - (self.clock() - self.last_command_time))
        return {"ready": self.ready, "active": self.active, "remaining": remaining,
                "fast_running": self.fast_running,
                "target_angle": self.target_angle, "target_speed": self.target_speed,
                "logs": list(self.logs)}
