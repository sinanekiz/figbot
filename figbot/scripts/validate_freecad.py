"""Import FIGBOT assembly STEP files in FreeCAD and save native FCStd copies.

Run with FreeCADCmd, not the system Python interpreter.
"""

from __future__ import annotations

import sys
from pathlib import Path

import FreeCAD as App
import Import


ROOT = Path(__file__).resolve().parents[1]
ASSEMBLY_DIR = ROOT / "cad" / "assembly"


def convert(name: str) -> tuple[int, int]:
    step_path = ASSEMBLY_DIR / f"{name}.step"
    fcstd_path = ASSEMBLY_DIR / f"{name}.FCStd"
    if not step_path.is_file():
        raise FileNotFoundError(step_path)

    document = App.newDocument(name)
    try:
        Import.insert(str(step_path), document.Name)
        document.recompute()
        shaped_objects = [obj for obj in document.Objects if hasattr(obj, "Shape")]
        solid_count = sum(len(obj.Shape.Solids) for obj in shaped_objects)
        if not shaped_objects or solid_count == 0:
            raise RuntimeError(f"{name}: imported STEP contains no solids")
        document.saveAs(str(fcstd_path))
        print(
            f"PASS {name}: objects={len(document.Objects)}, "
            f"solids={solid_count}, output={fcstd_path}"
        )
        return len(document.Objects), solid_count
    finally:
        App.closeDocument(document.Name)


def main() -> int:
    results = [
        convert("FIGBOT_V0_ASSEMBLY"),
        convert("FIGBOT_V1_ASSEMBLY"),
        convert("FIGBOT_CUSTOM_ARM_ASSEMBLY"),
        convert("FIGBOT_MG996R_TEST_ARM"),
        convert("FIGBOT_MG996R_PRINTABLE_V1"),
        convert("FIGBOT_MG996R_AERO_V2"),
        convert("FIGBOT_P0_ROVER"),
    ]
    print(f"PASS FreeCAD validation: assemblies={len(results)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
