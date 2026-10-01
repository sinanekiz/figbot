# Power architecture

## V0 bench prototype

`230 VAC facility power -> lockable disconnect -> branch protection -> certified enclosed 24 VDC supply -> K1/K2 actuator contactor path -> fused 24 V actuator branches`

The 24 V supply also feeds protected DC/DC converters for the 5 V AI computer and 5 V gripper rail. Logic power may remain on after an emergency stop only so that faults and logs can be retained; actuator energy must be removed. All exposed conductive chassis and power-supply protective-earth terminals must bond to PE.

The 451 W supply candidate is screened against the pessimistic 392.8 W connected-peak estimate. This is not enough evidence for final selection. Log DC-bus current during representative trajectories and review surge/overload behavior before approval. If measured peak, derating, or regeneration violates supply limits, increase capacity or add an appropriate braking/energy-absorption solution after engineering review.

## Voltage comparison

| Bus | Benefits | Drawbacks | V0 disposition |
|---|---|---|---|
| 12 V | Common accessories; lower touch voltage | Higher current and cable loss; incompatible with shortlisted 24–48 V stepper drivers | Reject for main motion bus |
| 24 V | Compatible with candidate drivers and industrial safety devices; moderate current | Requires conversion to 5 V; running torque still requires curve check | Preferred `ESTIMATE` baseline |
| 48 V | Better stepper high-speed torque and lower current | More stringent component selection; higher energy; not justified before speed tests | Alternative only after dynamometer data |

## V1 mobile prototype

Use a certified 24 V battery pack with an integral BMS and a correctly rated service disconnect only after pack voltage, chemistry, peak current, environmental sealing, charging, and enclosure requirements are reviewed. No battery model or runtime is selected here. The manual-push V1 does not include traction power.

## Grounding and segregation

- Protective earth and DC common are not interchangeable. Bond PE per the selected PSU manual and local electrical code.
- Route motor and mains wiring separately from encoder, camera, and logic wiring.
- Terminate cable shields according to the driver/encoder manual; do not invent a shield scheme before EMC review.
- Do not route emergency-stop channels through the application MCU.

> **HUMAN ENGINEERING REVIEW REQUIRED:** mains entry, PE bonding, overcurrent protection, conductor ampacity, contactor selection, emergency-stop performance level/category, and battery architecture.
