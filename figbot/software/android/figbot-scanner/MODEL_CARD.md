# Collectable hurda-fig detector model card

Status: **PHONE FIELD TEST ONLY — NOT INDEPENDENTLY VALIDATED**

- Architecture/export: YOLO11n, one class (`dry_fig`), ONNX float32,
  fixed 640 x 640 input.
- Application confidence threshold: 0.35; NMS IoU threshold: 0.45.
- Starting point: APK v0.5 grass/leaf-adapted weights.
- Target definition correction: bruised, purple, dark, split, and low-grade
  ground figs described as `hurda incir` are collectable positives, not hard
  negatives.
- New adaptation: three reviewed 940 x 2048 APK screenshots containing 11 new
  collectable figs, plus three clean dark figs relabelled from an earlier scene.
  Clean whole-leaf, dry-leaf-cluster, glove, rock, and soil crops are negatives.
  Screenshot UI and detector overlays are excluded. This produced 320 repeated
  examples.
- Rehearsal: 500 sampled examples from the earlier mix, excluding the 40 copies
  that encoded dark/hurda figs as negatives.
- Internal validation: 150 synthetic examples. This is not an orchard test split.
- Frozen model SHA-256:
  `9FDA5D668FAF40EE5BF5659F94ACB721D4E0DB1CDB341B7AAC1B7845505BFFBD`.

## Supplied-scene fit audit

At threshold 0.35, the frozen ONNX model produced:

| Scene group | Labelled dry figs found | Extra boxes |
|---|---:|---:|
| New and corrected hurda-fig examples | 14 / 14 | 0 on six reviewed negative crops |
| New grass/leaf failure examples | 6 / 6 | 0 on reviewed negative crops |
| Four outdoor soil/concrete photos | 20 / 20 | 0 |
| Five earlier carpet/bag/sofa photos | 14 / 14 | 0 |
| **Total unique labelled collectable figs** | **54 / 54** | **0 on defined audit views** |

This is a training-scene fit check, not validation: all 18 phone scenes were
used during adaptation. It must not be presented as expected orchard accuracy.

## Known limits

- Unseen orchard lighting, motion blur, sun/shade transitions, partially buried
  figs, heavy occlusion, different cultivars, and the fixed FIGBOT camera remain
  unverified.
- Source photos are still images rather than raw ARCore camera frames.
- The new source files are screenshots. Only camera-area crops without UI or
  detector-overlay leakage were used for training and the fit audit.
- A green box remains a `dry_fig_candidate`. XYZ comes from ARCore depth/plane
  estimation and is not authorized for arm motion.
- Record the next unseen orchard batch before training on it. That pre-training
  result is the evidence needed to measure generalisation.
