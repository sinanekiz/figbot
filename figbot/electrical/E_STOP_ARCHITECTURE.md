# Emergency-stop architecture

> # HUMAN ENGINEERING REVIEW REQUIRED
>
> This is a safety concept, not a validated safety function. A qualified machinery-safety and electrical engineer must determine required risk reduction, stop category, performance level/category, standards applicability, contactor architecture, braking/gravity behavior, reset logic, and validation tests before anyone enters the robot workspace.

## Proposed V0 concept

1. A red mushroom, yellow-background, latching emergency-stop device provides two mechanically linked, direct-opening normally closed channels.
2. Both channels enter a 24 V safety relay. The MCU may monitor an auxiliary status contact but is not in the safety path.
3. Safety outputs drive redundant force-guided contactors K1 and K2, or another validated final switching arrangement, that remove 24 V actuator power from every motor driver and gripper actuator.
4. The AI computer and safety-status logic may remain energized for logging. They cannot re-enable motion.
5. A separate manual reset outside the reachable hazard zone is required after the E-stop is released. Reset must not initiate motion.
6. Contactor feedback/EDM must detect welded or failed final switching elements before reset.
7. A separate guarded enable/start action is required to energize motion after reset.

## Important unresolved hazard

Removing electrical power may allow the shoulder to fall under gravity. The safe response could require a counterbalance, spring, normally engaged brake, controlled stop followed by power isolation, or physical restraint. The correct solution depends on the risk assessment and measured mechanics; none is validated here. Do not assume power removal alone makes the arm safe.

## Candidate components are not an approved safety chain

The Omron A22E-M-02 (dual NC) and G9SE-201 safety relay are traceable research candidates. Their combination with contactors, wiring, reset circuit, diagnostic coverage, and stopping behavior must be engineered and validated as a complete safety function. A single ordinary relay is not an acceptable substitute.

## Required validation record

- Applicable standards and risk assessment identified by a qualified reviewer.
- Required PL/SIL/category and stop category documented.
- Dual-channel open/short/cross-fault tests.
- Each contactor welded-contact simulation and EDM test.
- Loss of 24 V, loss of logic, MCU crash, driver fault, encoder fault, and cable-break tests.
- Measured stop time and stopping distance at worst speed/load.
- Shoulder/gravity-drop test with controlled exclusion zone.
- Reset/restart interlock test; no automatic restart after power restoration.
- Signed schematic, component ratings, conductor sizes, fuse coordination, and validation report.

