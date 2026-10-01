"""Reproducible FIGBOT build entry point."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cad.assembly.build_assemblies import build_assemblies
from cad.build import PARTS, build_all_parts, build_part
from cad.rover.build_p0_rover import build_p0_rover
from cad.prototype_arm.build_servo_arm import build_servo_arm
from cad.prototype_arm.build_printable_v1 import build as build_printable_v1
from cad.prototype_arm.build_aero_v2 import build as build_aero_v2
from scripts.generate_manual_pdf import build_manual
from scripts.build_rev_g_arm_cost import build as build_rev_g_arm_cost


def copy_release() -> Path:
    release = ROOT / "releases" / "V0-PROTOTYPE"
    release.mkdir(parents=True, exist_ok=True)
    for name in (
        "README.md", "MASTER_SPEC.md", "PLAN.md", "STATUS.md", "DECISIONS.md",
        "ASSUMPTIONS.md", "RISKS.md", "OPEN_QUESTIONS.md", "SETUP_REQUIRED.md",
    ):
        shutil.copy2(ROOT / name, release / name)
    for source, target in (
        (ROOT / "cad" / "assembly" / "FIGBOT_V0_ASSEMBLY.step", release / "FIGBOT_V0_ASSEMBLY.step"),
        (ROOT / "bom", release / "bom"), (ROOT / "electrical", release / "electrical"),
        (ROOT / "manufacturing", release / "manufacturing"), (ROOT / "assembly", release / "assembly"),
        (ROOT / "software", release / "software"), (ROOT / "simulation", release / "simulation"),
        (ROOT / "reports", release / "reports"), (ROOT / "cad", release / "cad_source_and_outputs"),
        (ROOT / "firmware" / "pico2_motion", release / "firmware" / "pico2_motion_source"),
    ):
        if not source.exists():
            continue
        if source.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(
                source, target, dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "build-*"),
            )
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    uf2 = ROOT / "firmware" / "pico2_motion" / "build-pico2-sdk230" / "figbot_pico2_motion.uf2"
    if uf2.is_file():
        firmware_release = release / "firmware"
        firmware_release.mkdir(parents=True, exist_ok=True)
        shutil.copy2(uf2, firmware_release / uf2.name)
    (release / "RELEASE_STATUS.md").write_text(
        "# PROTOTYPE - NOT YET PRODUCTION VALIDATED\n\n"
        "Digital V0 package. Physical safety, strength, food contact, AI performance, cycle time, tolerances, and manufacturing readiness are not validated. See OPEN_QUESTIONS.md and reports/DESIGN_REVIEW_V0.md.\n",
        encoding="utf-8",
    )
    return release


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", choices=sorted(PARTS))
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    if args.part:
        build_part(args.part)
        print(f"Built {args.part}")
        return 0
    build_all_parts()
    build_assemblies()
    build_servo_arm()
    build_printable_v1()
    build_aero_v2()
    build_p0_rover()
    build_rev_g_arm_cost()
    build_manual()
    simulation_runner = ROOT / "simulation" / "run_pick_simulation.py"
    if simulation_runner.exists():
        subprocess.run([sys.executable, "-m", "simulation.run_pick_simulation"], cwd=ROOT, check=True)
    dual_arm_evaluator = ROOT / "simulation" / "evaluate_dual_arm_layout.py"
    if dual_arm_evaluator.exists():
        subprocess.run([sys.executable, "-m", "simulation.evaluate_dual_arm_layout"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "simulation.evaluate_rev_g_arm"], cwd=ROOT, check=True)
    if not args.skip_tests:
        subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, check=True)
    copy_release()
    print("FIGBOT build complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
