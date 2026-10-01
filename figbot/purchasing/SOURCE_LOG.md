# Source log

All sources were checked on **2026-08-20**. URLs are also embedded in `PURCHASE_CANDIDATES.csv`.

| Item | Source type | What was verified | Caveat |
|---|---|---|---|
| StepperOnline 1-CL57TE-S20 | Manufacturer store | Kit contents, 2.0 N·m holding torque, 1000 PPR encoder, 24–50 VDC driver, price | Running torque must come from the downloadable torque curve |
| StepperOnline 1-CL42T-P05-V41 | Manufacturer regional store | Kit contents, 0.48 N·m holding torque, encoder, 24–48 VDC driver, price | Price/stock region may differ for Türkiye |
| ROBOTIS XL330-M288-T | Manufacturer store and e-manual | Price, mass, voltage, torque/current data, current-based control | Stall torque is not a continuous rating |
| Raspberry Pi 5 and Camera Module 3 | Manufacturer product brief/store | Board input, official list price, camera resolution/FOV | Application inference performance is unverified |
| NVIDIA Jetson Orin Nano Super | Manufacturer marketplace | Current marketplace price and compute/power headline specs | Official price pages conflict; re-check before budgeting |
| Luxonis OAK-D Lite | Manufacturer store/docs | Depth range, sensor and power specs | Current price was not reliably exposed; quote required |
| RealSense D405 | Manufacturer comparison page | Current list price and close-range positioning | Accuracy on the FIGBOT scene must be tested |
| MEAN WELL LRS-450-24 / LRS-350-24 | Authorized distributor linked to manufacturer datasheets | Output power/current, efficiency, prices | Mains installation, surge, regeneration, and derating require review |
| Omron A22E-M-02 and G9SE-201 | Authorized distributor plus manufacturer family documentation | Contact arrangement, ratings, price, safety-relay outputs | Components alone do not create a validated safety function |
# 2026-08-20 — P0 Rev-B vendor geometry

- Waveshare RoArm-M3 wiki: https://www.waveshare.com/wiki/RoArm-M3
- Official STEP archive: https://files.waveshare.com/wiki/RoArm-M3/RoArm-M3_STEP_260310.zip
- Official 2D archive: https://files.waveshare.com/wiki/RoArm-M3/RoArm-M3_2Dsize.zip
- Use: exact vendor CAD envelope in `FIGBOT_P0_ROVER`; not a validation of the delivered revision.
