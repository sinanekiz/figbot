# Laser-cut guide — V0 sheet parts

Status: `UNVERIFIED — MANUFACTURING REVIEW REQUIRED`

Candidate sheet parts are ARM-001 base plate, CHA-001 test-stand base, ELE-001
electronics tray and any drawing-released VIS-001 bracket plate. Confirm each against
the current BOM: a STEP model alone does not authorize laser cutting.

## Preflight

- Use only the released DXF revision; verify units and one known dimension before nesting.
- Confirm material/alloy, thickness, grain/protective-film requirements and quantity.
- Ensure closed profiles, no duplicate entities and no unsupported tiny features.
- Kerf compensation belongs to the manufacturer CAM setup and coupon result; do not
  scale or offset the engineering DXF silently.
- Hole size, edge distance and bend allowance are `TBD – MANUFACTURING REVIEW REQUIRED`.

## Process and inspection

Cut a first-article coupon or one part, inspect critical dimensions, then authorize
the batch. Mark part/revision away from functional surfaces. Remove dross and sharp
edges without changing datum geometry. Verify overall size, hole pattern, flatness,
slot/tab fit and surface condition against the drawing.

If ELE-001 is bent, use a revisioned bend drawing and record tool/radius/direction.
If CHA-001 or ARM-001 is welded, return to engineering for a post-weld datum and
distortion inspection plan. Laser-cut edges are not assumed suitable as precision
bearing or shaft fits.

