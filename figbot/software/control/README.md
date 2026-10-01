# Hardware control release candidate

`controller.py` controls the Pico 2 motion firmware over CRC-protected USB
serial. `gripper.py` configures the XL330 in current-based position mode.
`cli.py` is intentionally limited to restrained commissioning commands.

Examples on the Pi 5:

```bash
python -m software.control.cli --port /dev/ttyACM0 status
python -m software.control.cli --port /dev/ttyACM0 arm
python -m software.control.cli --port /dev/ttyACM0 home J1
python -m software.control.cli --port /dev/ttyACM0 move --j1 0 --j2 10 --j3 -20 --j4 -80
python -m software.control.cli --port /dev/ttyACM0 disarm
```

The controller reads present step counts before every move, clamps synchronized
rate/acceleration from each axis configuration, validates joint limits and waits
for explicit arming. Direction and zero offsets remain physical calibration
values. The gripper refuses to energize until current and open/closed positions
are numeric values produced by the damage/linkage tests.
