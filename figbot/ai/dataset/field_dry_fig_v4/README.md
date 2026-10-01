# Scrap-grade (hurda) dry-fig failure dataset v4

This reviewed adaptation set records the user's field-definition correction:
bruised, purple, dark, split, or low-grade ground figs described as **hurda
incir** are still collectable and belong to the detector's positive class.

The set contains 11 unique collectable figs in the three newly supplied APK
screenshots and relabels three clean, non-overlayed dark figs from an earlier
screenshot that v0.5 had incorrectly treated as negatives. It also adds clean
green-leaf, dry-leaf-cluster, glove, rock, and soil negative crops. Screenshot
UI, text, and green detector-overlay regions are excluded from training crops.

All examples are adaptation/training material. There is no independent
validation split, so fit on these screenshots is not a field-accuracy claim.

Build with:

```powershell
python -m ai.training.prepare_field_dry_fig_dataset `
  --manifest ai/dataset/field_dry_fig_v4/manifest.json `
  --output path/to/hurda-field-dataset
```
