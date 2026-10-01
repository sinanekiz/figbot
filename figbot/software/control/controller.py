"""Pi-side motion client with strict limits and explicit arming."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Mapping

from .protocol import Frame, ProtocolError, decode_frame, encode_frame


CONFIG_PATH = Path(__file__).with_name("hardware_config.json")


class MotionClient:
    def __init__(self, port: str, config_path: Path = CONFIG_PATH) -> None:
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError("Install pyserial before connecting hardware") from exc
        self.config = json.loads(config_path.read_text(encoding="utf-8"))
        self.serial = serial.Serial(port, self.config["serial"]["baud"], timeout=0.5)
        self.sequence = 0

    def _exchange(self, kind: str, *fields: object) -> Frame:
        self.sequence += 1
        self.serial.write(encode_frame(Frame(kind, self.sequence, tuple(map(str, fields)))))
        reply = decode_frame(self.serial.readline())
        if reply.seq != self.sequence:
            raise ProtocolError(f"sequence mismatch: {reply.seq} != {self.sequence}")
        if reply.kind == "ERR":
            raise RuntimeError(",".join(reply.fields))
        return reply

    def status(self) -> Frame:
        return self._exchange("STATUS")

    def heartbeat(self) -> Frame:
        return self._exchange("HEARTBEAT")

    def arm(self) -> Frame:
        return self._exchange("ARM")

    def disarm(self) -> Frame:
        return self._exchange("DISARM")

    def home(self, axis: str) -> Frame:
        index = {"J1": 0, "J2": 1, "J3": 2, "J4": 3}.get(axis.upper())
        if index is None:
            raise ValueError(f"unknown axis: {axis}")
        return self._exchange("HOME", index)

    def move_degrees(self, joints: Mapping[str, float], step_rate_hz: int = 8000, acceleration_steps_s2: int = 12000) -> Frame:
        axes = self.config["axes"]
        target_steps: list[int] = []
        steps_per_degree_by_axis: list[float] = []
        for name in ("J1", "J2", "J3", "J4"):
            value = float(joints[name])
            axis = axes[name]
            if not axis["min_deg"] <= value <= axis["max_deg"]:
                raise ValueError(f"{name}={value} outside [{axis['min_deg']}, {axis['max_deg']}]")
            steps_per_degree = axis["motor_steps_per_rev"] * axis["microsteps"] * axis["gear_ratio"] / 360.0
            steps_per_degree_by_axis.append(steps_per_degree)
            target_steps.append(round((value + axis["zero_offset_deg"]) * steps_per_degree * axis["direction"]))
        if not 100 <= step_rate_hz <= 20000:
            raise ValueError("step_rate_hz must be 100..20000")
        if not 1000 <= acceleration_steps_s2 <= 200000:
            raise ValueError("acceleration_steps_s2 must be 1000..200000")
        status = self.status()
        if len(status.fields) != 5 or status.fields[0] != "ARMED_IDLE":
            raise RuntimeError(f"move requires ARMED_IDLE; received {status.fields}")
        current_steps = [int(value) for value in status.fields[1:]]
        deltas = [abs(goal - current) for goal, current in zip(target_steps, current_steps)]
        dominant = max(deltas, default=0)
        if dominant:
            for index, (name, delta) in enumerate(zip(("J1", "J2", "J3", "J4"), deltas)):
                if not delta:
                    continue
                axis = axes[name]
                scale = dominant / delta
                allowed_rate = axis["max_deg_s"] * steps_per_degree_by_axis[index] * scale
                allowed_accel = axis["max_deg_s2"] * steps_per_degree_by_axis[index] * scale
                step_rate_hz = min(step_rate_hz, int(allowed_rate))
                acceleration_steps_s2 = min(acceleration_steps_s2, int(allowed_accel))
        return self._exchange("MOVE", *target_steps, step_rate_hz, acceleration_steps_s2)

    def wait_until_idle(self, timeout_s: float = 30.0) -> Frame:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            reply = self.status()
            if reply.fields and reply.fields[0] == "ARMED_IDLE":
                return reply
            self.heartbeat()
            time.sleep(self.config["serial"]["heartbeat_ms"] / 1000)
        self.disarm()
        raise TimeoutError("motion timeout; disarm requested")

    def close(self) -> None:
        self.serial.close()
