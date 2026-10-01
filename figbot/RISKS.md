# Risk Register

Scale: probability/impact = Low, Medium, High. No mitigation is considered verified until its listed verification succeeds.

| ID | Risk | Probability | Impact | Mitigation | Verification |
|---|---|---|---|---|---|
| R-001 | Gripper crushes/marks figs | High | High | three compliant variants, tunable stops/current limit | damage test; PHYSICAL VALIDATION REQUIRED |
| R-002 | AI labels green/soft fig as dry | Medium | High | critical-FP metric, confidence/reject policy, diverse data | held-out field dataset + physical trials |
| R-003 | Ground shadows degrade vision | High | Medium | varied-light dataset, shielded illumination evaluation | T05 lighting test |
| R-004 | Arm misses 3-5 s target | Medium | Medium | short links, nearby funnel, target prefetch, trajectory tuning | timed simulation then endurance test |
| R-005 | Motor torque is insufficient | Medium | High | calculate gravity/dynamic peaks and preserve margin | dyno/current/thermal test |
| R-006 | Printed joint fractures | Medium | High | metal load paths, print guidance, guard/exclusion zone | proof/load/fatigue test + human review |
| R-007 | Planetary gearbox backlash and compliance harm accuracy | Medium | Medium | closed-loop axes, calibration map, conservative approach motion | loaded bidirectional repeatability test |
| R-008 | Camera-base calibration drifts | Medium | High | rigid target, fiducial verification before run | calibration residual log |
| R-009 | Dust damages electronics | High | Medium | guarded enclosure and serviceable filters | ingress inspection/environment test |
| R-010 | Stone impact damages tool | Medium | Medium | classification reject, compliant fingers, current/impact stop | mixed-object test |
| R-011 | Funnel damages fruit | Medium | Medium | low release height, soft lining, short channel | drop/damage test |
| R-012 | Robot/test stand tips | Low | High | broad anchored V0 plate; V1 stability calculation | HUMAN ENGINEERING REVIEW + tilt/load test |
| R-013 | E-stop fails to remove hazardous drive energy | Low | Critical | dual-channel safety relay, redundant energy isolation, EDM and manual reset; final contactor/STO implementation remains blocked | qualified electrical review + fault test |
| R-014 | J2 exceeds continuous gearbox rating or drops under gravity | Medium | Critical | derated motion, mechanical counterbalance/brake review, guarded first motion | torque-speed/thermal test + controlled power-loss drop test |
| R-015 | Two arms enter the same swept volume or one arm reaches across the Y=0 ownership boundary | Medium | Critical | separate normal work regions, shared-volume mutex, conservative slow commissioning | dual-arm CAD sweep + interlock fault injection + guarded physical test |
| R-016 | Wider or filled basket moves the centre of gravity outside the stable envelope during braking/turning | Medium | High | keep battery/electronics low, limit fill height and speed until measured | mass-property review + tilt/brake test at defined fill levels |
| R-017 | Low basket-side opening jams, ejects or damages collected objects | Medium | Medium | 150 mm opening, soft liner, low release height, service access | representative-object feed/drop endurance test |
| R-018 | An irregular object stalls, bridges, accelerates excessively or is damaged on the sloped basket floor or rear pile | Medium | High | adjustable 5-12 degree floor, replaceable liner, soft rear stop, limit fill level until tested | representative-object feed-rate, jam, impact and damage test at several fill levels |
