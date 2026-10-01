# Orchard phone dry-fig dataset v2

This reviewed adaptation set adds the first real outdoor soil and concrete
scenes supplied after APK v0.3 testing. It contains 20 labelled whole dried figs
across four 1152 x 2048 phone photos, plus explicit flower, stone, leaf, grass,
shoe, pipe, and empty-soil negative crops.

The four full scenes and their context crops are all used for adaptation. There
is no independent validation split, so any fit count on these photos is not a
field-accuracy claim. Keep future unseen orchard photos out of training until the
next frozen evaluation has been recorded.

Build with:

```powershell
python -m ai.training.prepare_field_dry_fig_dataset `
  --manifest ai/dataset/field_dry_fig_v2/manifest.json `
  --output path/to/orchard-field-dataset
```
