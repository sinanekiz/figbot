# FIGBOT P0 rover CAD

`build_p0_rover.py` produces the Rev-G controlled packaging assembly for the
flat-ground ground-collection prototype. Coordinates are +X forward, +Y left
and +Z up. Rev-G uses a 650 x 600 mm frame and 830 mm wheel-centre track. A
400 x 350 x 180 mm basket occupies the front-centre; two lightweight MG996R F/P test-arm
instances flank its side walls at X=120 mm, Y=+/-250 mm. Each side wall has a
150 mm front-side drop opening directly next to its arm. The basket floor is
8 degrees front-high/rear-low (`ESTIMATE`) and adjustable over a 5-12 degree
prototype range so objects can feed toward a soft rear stop. Feed reliability,
damage and the final replaceable liner material require physical validation.
The battery and programmable
electronics remain low; the camera boom reaches forward from a rear two-post
bridge.

The first arm-command lanes are X=420..600 mm and Y=180..320 mm left /
-320..-180 mm right. Wider camera detections require vehicle repositioning.
This is a layout rule, not a validated collision guarantee. Shared-volume
interlocking, full joint sweeps and physical timing remain required.

This geometry documents component placement and calculated gross clearances only. Wheel hubs,
steering knuckles, tie rods, motor shafts, chain sprockets, the linear actuator,
battery enclosure and servos use controlled envelopes. Hole patterns, horn stack,
fits and supplied brackets remain `TBD` until incoming parts are measured. The STEP file is
therefore **not a manufacturing release**.

Outputs:

- `cad/assembly/FIGBOT_P0_ROVER.step`
- `viewer/public/models/FIGBOT_P0_ROVER.glb`
- `renders/FIGBOT_P0_ROVER_*.png`
- `renders/FIGBOT_P0_BASKET_SLOPE_SECTION.png`
- `cad/rover/FIGBOT_P0_LAYOUT.json`
