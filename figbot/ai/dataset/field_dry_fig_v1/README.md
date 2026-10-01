# Phone field dry-fig dataset v1

This small reviewed set captures the failure modes reported during APK v0.2
testing: intact pear-shaped dried figs, multiple small figs on patterned carpet,
figs under a transparent bag, sofa texture as a hard negative, and stone/flower
distractors.

All five supplied screenshots are now used for field adaptation because the
initial held-out image showed that twelve field instances were insufficient for
useful generalisation. Consequently this set has no independent field-validation
split and no field accuracy claim may be derived from it. The source images are
cropped screenshots, not raw camera frames, and remain
`PHYSICAL VALIDATION REQUIRED`.

Build the YOLO-formatted field set with:

```powershell
python -m ai.training.prepare_field_dry_fig_dataset `
  --manifest ai/dataset/field_dry_fig_v1/manifest.json `
  --output path/to/field-dataset
```
