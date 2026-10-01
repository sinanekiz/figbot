# FIGBOT AI workspace

This workspace supports the V0 five-class perception experiment:

- `dry_fig_collect`
- `green_fig_ignore`
- `stone_avoid`
- `leaf_ignore`
- `branch_avoid`

`training/` contains an optional Ultralytics training entry point, `inference/`
contains a conservative decision gate, and `evaluation/` computes repeatable
classification metrics from exported predictions. The first V0 experiment may
use detection; segmentation should be adopted only if overlap and grasp-point
errors justify its additional annotation and inference cost.

No model file or accuracy result is included. Every AI performance claim is
`UNVERIFIED — PHYSICAL VALIDATION REQUIRED` until the frozen test split contains
representative orchard images and the full camera/compute pipeline is tested.

Quick checks (from repository root):

```powershell
python -m unittest discover -s ai -p "test_*.py"
python -m ai.evaluation.evaluate --input ai/evaluation/example_predictions.csv
python -m ai.inference.gate --input ai/inference/example_detections.json
```

With the optional reviewed Ultralytics environment and a local checkpoint:

```powershell
python -m ai.inference.infer --model path/to/model.pt --source path/to/image.jpg --output detections.json
```

Training requires an optional ML environment; see `training/README.md`. Do not
mix evaluation images back into training after metrics have been reviewed.
