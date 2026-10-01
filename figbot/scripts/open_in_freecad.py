"""Open the generated V0 STEP in FreeCAD when FreeCADCmd is available."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
step = root / "cad" / "assembly" / "FIGBOT_V0_ASSEMBLY.step"
local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
candidates = [
    shutil.which("FreeCAD"),
    shutil.which("FreeCAD.exe"),
    local_app_data / "Programs" / "FreeCAD 1.1" / "bin" / "freecad.exe",
]
command = next((str(path) for path in candidates if path and Path(path).is_file()), None)
if not command:
    raise SystemExit("FreeCAD not found. Follow SETUP_REQUIRED.md; the rest of the build remains usable.")
if not step.exists():
    raise SystemExit("Assembly STEP missing. Run scripts/build_all.py first.")
subprocess.run([command, str(step)], check=True)
