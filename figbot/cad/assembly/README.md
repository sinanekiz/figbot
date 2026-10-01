# FIGBOT assemblies

`build_assemblies.py` builds the V0 bench assembly, a mechanical-only custom-arm subassembly and a V1 packaging concept from the same numbered CadQuery parts. V1 wheels, frame, and crate are deliberately simple purchased/proxy envelopes; they are not manufacturing definitions.

- `FIGBOT_V0_ASSEMBLY.step`: current digital bench prototype.
- `FIGBOT_CUSTOM_ARM_ASSEMBLY.step`: custom 605 mm arm and gripper with purchased motor/actuator envelopes, without the bench, funnel, camera or electronics.
- `FIGBOT_V1_ASSEMBLY.step`: manual-mobile packaging envelope, UNVERIFIED.
- `FIGBOT_V0_ASSEMBLY.FCStd`: FreeCAD-native V0 import, 60 solids at the latest validation.
- `FIGBOT_CUSTOM_ARM_ASSEMBLY.FCStd`: FreeCAD-native custom-arm import, 32 solids at the latest validation.
- `FIGBOT_V1_ASSEMBLY.FCStd`: FreeCAD-native V1 import, 72 solids at the latest validation.
- `viewer/public/models/*.glb`: lightweight named-node scenes.

Use `scripts/freecad_validate.ps1` to regenerate the FCStd files and verify that their STEP sources still contain solids. Use `scripts/open_in_freecad.py` for interactive V0 review.
