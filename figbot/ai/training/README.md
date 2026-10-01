# Training scaffold

The entry point deliberately does not download weights or data. Create an isolated
ML environment, install a reviewed Ultralytics release, provide a local starting
checkpoint, then run:

```powershell
python -m ai.training.train --model path/to/local_checkpoint.pt --epochs 50 --imgsz 640
```

The command writes outputs under `ai/training/runs/`. Review the exact dependency
version and its license/security posture before use. Epoch count, image size,
augmentation and confidence thresholds are experiment parameters, not validated
design values. Export predictions from the frozen test split and evaluate them
with `ai.evaluation.evaluate`.

## Android bootstrap experiment

`prepare_public_fig_dataset.py` extracts the LVIS `fig_(fruit)` class, adds the
public Fruits-And-Vegetables hard-negative set, and makes object-centred crops for
the handheld-camera experiment. `train_mobile_fig_detector.py` fine-tunes YOLO11n
and exports a one-class ONNX model. Neither script turns public imagery into a
field-validated FIGBOT dataset; the generated model card retains that warning.

The current APK target is specifically **dry fig**, so
`prepare_public_dry_fig_dataset.py` is the active bootstrap builder. It samples the
CC BY 4.0 Dry Fruit Image Dataset (`10.17632/yfhgn8py5f.1`), creates approximate
boxes with GrabCut, and keeps fresh figs/other fruits as hard negatives. The boxes
are not human-reviewed and must be replaced by FIGBOT camera annotations.

`prepare_field_dry_fig_dataset.py` builds a reviewed YOLO set from a manifest of
phone screenshots, crops, boxes, explicit negative regions, and repeat counts.
The checked-in `ai/dataset/field_dry_fig_v1` manifest records the v0.3 adaptation
examples. All supplied scenes are used for adaptation, so its fit audit is not an
independent accuracy result.

`ai/dataset/field_dry_fig_v2` adds four reviewed outdoor soil/concrete scenes,
20 whole dried figs, multiple object-scale context crops, and explicit orchard
negative regions. It is the v0.4 adaptation input and likewise has no independent
validation split.

`ai/dataset/field_dry_fig_v3` adds six reviewed APK failure screenshots. It
targets dry figs crossed by grass and leaf-litter misses, while treating clean
leaf regions and fresh/dark/wet figs as negatives for the requested dry-only
class. Screenshot UI and output-overlay regions are excluded. It is the v0.5
adaptation input and has no independent validation split.

`ai/dataset/field_dry_fig_v4` records the later field-definition correction:
bruised, purple, dark, split, low-grade `hurda incir` on the ground are
collectable positives. It adds 11 new labelled figs, relabels three earlier dark
figs as positives, and adds clean leaf/glove/soil negatives. It is the v0.6
adaptation input and has no independent validation split.
