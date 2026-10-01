# Machining and fabrication guide — V0

Status: `UNVERIFIED — MANUFACTURING REVIEW AND PHYSICAL VALIDATION REQUIRED`

Candidate parts: ARM-001/002/004/006 milled aluminium parts, ARM-003/005 link
tubes, ARM-007/008 joint shafts, CHA-001 stand base, VIS-001 mast/bracket and
ELE-001 electronics tray. The released BOM/drawing determines whether each is
saw-cut, drilled, turned, milled or sheet-cut.

## General controls

1. Verify part number, revision, units, quantity, material form and stock size.
2. Establish drawing datums before machining; do not dimension chained features from
   rough-cut edges unless the drawing explicitly permits it.
3. Machine bearing/shaft mating features in one setup where practical. The controlled
   baseline uses 6002-2RS with 32 H7/15 g6 interfaces and 608-2RS with 22 H7/8 g6
   interfaces; the drawing and `INTERFACE_CONTROL.csv` remain authoritative and
   shaft drawings require signoff before manufacture.
4. Deburr every edge; break only edges allowed by the drawing. Protect belt paths,
   cable routes and product-contact regions from burrs and swarf.
5. Clean parts before bearing installation and product-area assembly.

## Tubes ARM-003 and ARM-005

- Saw to released length using a stop; label immediately to prevent interchange.
- Support thin-wall tube during drilling/clamping to avoid ovalization.
- Drill paired pivot/attachment features from a controlled jig or one setup when the
  drawing requires coaxiality. Do not hand-match one assembly without recording it.
- Inspect length, hole position, hole diameter, squareness/parallelism and visible
  crushing. Numeric tolerances come only from released drawings.

## Plates and brackets

ARM-001 and CHA-001 establish assembly datums. Confirm flatness after cutting and
after any welding. If a weld is introduced, engineering must review distortion,
heat-affected properties, grounding and finish. ELE-001 edges require grommets or
edge protection wherever cables pass.

## Finish and disposition

Clear anodize is optional for exposed aluminium prototypes and black oxide is optional
for steel shafts; do not coat bearing fits, electrical bonding points or threaded
interfaces without masking instructions. Quarantine deviations,
record measured values and obtain engineering disposition before rework or use.
