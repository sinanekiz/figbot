# V0 RGB versus RGB-D camera decision

Status: `ARCHITECTURE RECOMMENDATION — UNVERIFIED — PHYSICAL VALIDATION REQUIRED`

| Criterion | Fixed RGB | RGB-D |
|---|---|---|
| V0 bench cost/availability | Usually lower; current PUR-005 is an RGB candidate | Usually higher; candidate not yet selected |
| XYZ method | Calibrated ray/table-plane intersection; assumes known planar height | SDK deprojection from pixel + depth, then calibrated rigid transform |
| Uneven ground/fruit height | Weak; height error becomes lateral/vertical target error | Better potential, but depth holes/noise on small, dark or reflective surfaces must be tested |
| Compute/integration | Simpler image pipeline | SDK, depth alignment and validity handling add complexity |
| Failure detection | Plane mismatch may look plausible unless separately checked | Invalid/low-confidence depth can be rejected, but valid-looking bias remains possible |
| V1 suitability | Limited where orchard ground is nonplanar | Preferred direction if physical trials show adequate small-object depth quality |

Recommendation: start V0 with the lowest-cost fixed RGB camera only for a rigid,
measured planar test surface and independently verify target XYZ. Keep the software
interface depth-aware so an RGB-D source can replace the plane estimator without
changing `camera_optical -> base_link` semantics. Before V1 or nonplanar T06 trials,
bench-test an RGB-D candidate and compare XYZ residual, missing-depth rate, latency,
field of view, dust/light sensitivity, host compatibility and total cost.

PUR-005 is a research candidate, not an approved purchase. No camera meets the
accuracy, lighting or environmental requirement until the calibration and physical
test protocols pass with preregistered limits.

