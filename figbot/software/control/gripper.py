"""ROBOTIS XL330 current-limited gripper interface."""

from __future__ import annotations

import json
from pathlib import Path

from .controller import CONFIG_PATH


class GripperClient:
    ADDR_OPERATING_MODE = 11
    ADDR_CURRENT_LIMIT = 38
    ADDR_TORQUE_ENABLE = 64
    ADDR_GOAL_CURRENT = 102
    ADDR_PROFILE_ACCELERATION = 108
    ADDR_PROFILE_VELOCITY = 112
    ADDR_GOAL_POSITION = 116
    ADDR_PRESENT_CURRENT = 126
    ADDR_PRESENT_POSITION = 132
    CURRENT_BASED_POSITION_MODE = 5

    def __init__(self, port: str, config_path: Path = CONFIG_PATH) -> None:
        try:
            from dynamixel_sdk import PacketHandler, PortHandler
        except ImportError as exc:
            raise RuntimeError("Install dynamixel-sdk before connecting XL330") from exc
        self.config = json.loads(config_path.read_text(encoding="utf-8"))["gripper"]
        self.port = PortHandler(port)
        self.packet = PacketHandler(float(self.config["protocol"]))
        if not self.port.openPort() or not self.port.setBaudRate(int(self.config["baud"])):
            raise RuntimeError(f"cannot open/configure DYNAMIXEL port {port}")
        self.id = int(self.config["id"])

    def _check(self, result: int, error: int, operation: str) -> None:
        if result != 0 or error != 0:
            raise RuntimeError(f"{operation} failed: comm={result}; device={error}")

    def _write1(self, address: int, value: int, operation: str) -> None:
        result, error = self.packet.write1ByteTxRx(self.port, self.id, address, value)
        self._check(result, error, operation)

    def _write2(self, address: int, value: int, operation: str) -> None:
        result, error = self.packet.write2ByteTxRx(self.port, self.id, address, value)
        self._check(result, error, operation)

    def _write4(self, address: int, value: int, operation: str) -> None:
        result, error = self.packet.write4ByteTxRx(self.port, self.id, address, value)
        self._check(result, error, operation)

    def configure(self) -> None:
        limit = self.config["current_limit_ma"]
        if not isinstance(limit, int):
            raise RuntimeError("gripper current_limit_ma must be set from the physical damage test")
        self._write1(self.ADDR_TORQUE_ENABLE, 0, "torque off")
        self._write1(self.ADDR_OPERATING_MODE, self.CURRENT_BASED_POSITION_MODE, "operating mode")
        self._write2(self.ADDR_CURRENT_LIMIT, limit, "current limit")
        self._write4(self.ADDR_PROFILE_ACCELERATION, int(self.config["profile_acceleration"]), "profile acceleration")
        self._write4(self.ADDR_PROFILE_VELOCITY, int(self.config["profile_velocity"]), "profile velocity")
        self._write1(self.ADDR_TORQUE_ENABLE, 1, "torque on")

    def move(self, position_ticks: int, current_limit_ma: int | None = None) -> None:
        current = current_limit_ma if current_limit_ma is not None else self.config["current_limit_ma"]
        if not isinstance(current, int):
            raise RuntimeError("gripper current limit is not physically calibrated")
        self._write2(self.ADDR_GOAL_CURRENT, current, "goal current")
        self._write4(self.ADDR_GOAL_POSITION, int(position_ticks), "goal position")

    def open(self) -> None:
        position = self.config["open_position_ticks"]
        if not isinstance(position, int):
            raise RuntimeError("open_position_ticks is not physically calibrated")
        self.move(position)

    def close_soft(self) -> None:
        position = self.config["closed_position_ticks"]
        if not isinstance(position, int):
            raise RuntimeError("closed_position_ticks is not physically calibrated")
        self.move(position)

    def disable(self) -> None:
        self._write1(self.ADDR_TORQUE_ENABLE, 0, "torque off")

    def close(self) -> None:
        try:
            self.disable()
        finally:
            self.port.closePort()
