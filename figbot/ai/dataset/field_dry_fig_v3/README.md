# Phone failure-example dataset v3

This reviewed adaptation set targets the two failure modes reported after the
otherwise successful outdoor APK test: dry figs partly crossed by grass were
missed, while large fig-like leaves were occasionally detected as dry figs.

It contains six labelled dry figs across three phone screenshots. It also adds
explicit leaf, leaf-litter, soil, grass, and fresh/dark/wet-fig negative crops.
Fresh or wet-looking figs remain negative because the requested target class is
**dry fig only**. Screenshot UI and green detector-overlay regions are excluded
from training crops wherever they could leak the application's output into the
model.

All examples are adaptation/training material. There is no independent
validation split, so fit on these screenshots is not a field-accuracy claim.

Build with:

```powershell
python -m ai.training.prepare_field_dry_fig_dataset `
  --manifest ai/dataset/field_dry_fig_v3/manifest.json `
  --output path/to/field-failure-dataset
```
