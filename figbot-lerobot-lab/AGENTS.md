# FIGBOT LeRobot lab

- This is a separate experiment requested by the user. The sibling `figbot/` project is read-only.
- Keep all generated files, weights, caches, data and environments inside this lab.
- Preserve source provenance with SHA256 and pin Hub revisions in `assets.lock.json`.
- Do not substitute raw encoder counts for a pretrained policy's calibrated state.
- Never infer mechanical limits from observed demonstration minima/maxima.
- Predictions are written to files. Calibration has a READ-only motor interface; its packet guard must reject every non-READ instruction, including torque and EEPROM writes.
- Keep reference smoke tests, transfer diagnostics, held-out evaluations and physical success distinct.
- Never upload recordings or launch paid compute without explicit user instruction.
- Run tests for changed modules. Test camera code with synthetic capture until the user connects a camera.
- Unknown calibration and hardware assumptions belong in `ASSUMPTIONS.md`.
