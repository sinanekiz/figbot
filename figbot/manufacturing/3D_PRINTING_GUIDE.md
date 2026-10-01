# 3D printing guide — V0

Status: `UNVERIFIED — PHYSICAL VALIDATION REQUIRED`

## Rev-G MG996R printable V1 first-print gate

Do not begin with the full structural set. Print the six STL files in
`cad/prototype_arm/printable_v1/fit_check_first` first. They check the nominal
MG996R and MG90S body openings, replaceable clamp bars, supplied horn and actual
20 mm tube. The CAD uses 0.8 mm total servo-body clearance and a 20.5 mm tube
socket; both values remain `UNVERIFIED` until the delivered parts are tried.

Use PETG, 0.20 mm layers, four walls and 35% infill only as an initial fit-coupon
recipe. Do not scale the STL in the slicer. A tight part must be measured and the
CAD parameter corrected; forcing or heating a servo into the coupon is not an
acceptable fit result. Full structural printing starts only after all six coupon
checks are recorded.

Applicable candidate parts (confirm against the released BOM/drawing):

| Part | Function | Initial process intent |
|---|---|---|
| ARM-002 | J1 housing | FFF prototype; mechanically loaded |
| ARM-004 | elbow housing | FFF prototype; mechanically loaded |
| ARM-006 | wrist housing | FFF prototype; mechanically loaded |
| GRP-001 | gripper body | FFF prototype |
| GRP-005/006/007 | silicone molds A/B/C | FFF mold tooling |
| FUN-001 | funnel shell | FFF prototype or fabricated sheet alternative |
| VIS-001 | camera pole/bracket features | print only non-structural bracket features |

## Initial slicer recipe

The following is an `ESTIMATE` for coupons and fit-check parts, not a released
structural recipe:

| Attribute | Housing/body start point | Mold-tool start point |
|---|---|---|
| Material | PETG from identified lot; dry per supplier | PETG or PLA if cure temperature permits |
| Nozzle | 0.4 or 0.6 mm | 0.4 mm |
| Layer height | 0.20 mm | 0.16–0.20 mm |
| Walls | 4–6 | 3–4 |
| Infill | 35–50%, local modifiers near fasteners | 20–35% |
| Top/bottom | at least 5 layers | at least 5 layers |
| Supports | only where unavoidable; never in bearing fits if avoidable | keep sealing/cavity face support-free |

Machine-specific temperature, speed and fan values must follow material supplier
limits and a validated printer profile; they are intentionally not invented here.

## Orientation and critical regions

- ARM-002/004/006 are EN AW-6082-T6 CNC parts in the controlled V0 baseline and
  shall not be substituted with printed load paths without a new structural review.
- Keep any printed prototype bearing proxies, shaft seats and datum faces away from support scars; they are fit-check tooling only.
- Use captured metal washers/inserts where the drawing calls for them; do not tap
  high-cycle load joints directly into weak layer orientation by default.
- Orient GRP-001 so finger-pivot and actuator attachment layers run continuously
  around the load path.
- Print GRP-005/006/007 with silicone cavity surfaces upward where possible. Seal
  porous mold surfaces using a silicone-compatible, reviewed release/seal system.
- FUN-001 must have a smooth product-contact path; remove stringing and sharp seams.

## Traveler and inspection

Record printer, nozzle, material/lot, drying, slicer/version, file hash, orientation,
settings, start/end time and anomalies. Inspect warpage, cracks, layer separation,
voids, fastener seats and mating dimensions from the drawing. Press-fit or bearing
dimensions are `TBD – MANUFACTURING REVIEW REQUIRED`; print calibration coupons
before any full housing.

Mechanically loaded printed parts are not accepted based on filament datasheet
strength. Test representative coupons and the complete assembly under controlled
loads; guard the test and record failure mode.
