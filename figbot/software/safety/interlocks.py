"""Fail-deenergized supervisory logic; never substitutes for hardwired E-stop."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class State(Enum):
    DISARMED = auto()
    ARMED = auto()
    FAULT_LATCHED = auto()
    ESTOP_LATCHED = auto()


@dataclass(frozen=True)
class Inputs:
    estop_channels_ok: bool = False
    communications_fresh: bool = False
    joint_limits_ok: bool = False
    drive_feedback_ok: bool = False

    @property
    def healthy(self) -> bool:
        return all((
            self.estop_channels_ok,
            self.communications_fresh,
            self.joint_limits_ok,
            self.drive_feedback_ok,
        ))


class Supervisor:
    def __init__(self) -> None:
        self.state = State.DISARMED

    @property
    def motion_enable_request(self) -> bool:
        """A request only; physical drive enable must fail safe independently."""
        return self.state is State.ARMED

    def update(self, inputs: Inputs) -> State:
        if not inputs.estop_channels_ok:
            self.state = State.ESTOP_LATCHED
        elif self.state is State.ARMED and not inputs.healthy:
            self.state = State.FAULT_LATCHED
        return self.state

    def arm(self, inputs: Inputs) -> bool:
        if self.state is State.DISARMED and inputs.healthy:
            self.state = State.ARMED
            return True
        return False

    def disarm(self) -> None:
        if self.state is State.ARMED:
            self.state = State.DISARMED

    def manual_reset(self, inputs: Inputs) -> bool:
        """Reset latch only; a separate arm action is still required."""
        if self.state in (State.ESTOP_LATCHED, State.FAULT_LATCHED) and inputs.healthy:
            self.state = State.DISARMED
            return True
        return False

