# Evaluation input contract

`evaluate.py` consumes a CSV of matched truth/prediction pairs. Perform deterministic
one-to-one box matching with a preregistered IoU rule before export. Use `__none__` as
the truth for an unmatched prediction (false positive) and as the prediction for an
unmatched truth object (false negative). Never include `__none__,__none__` rows.

Example:

```csv
truth,prediction,confidence
dry_fig_collect,dry_fig_collect,0.91
green_fig_ignore,dry_fig_collect,0.84
dry_fig_collect,__none__,
__none__,stone_avoid,0.72
```

The tool reports class precision/recall including unmatched detections, the confusion
matrix including the `__none__` sentinel, and critical green/stone-to-dry rates. It
does not choose the IoU or confidence threshold and does not validate dataset quality.
Those settings, object-level matching code and the frozen manifest must be recorded
with results. Metrics remain `UNVERIFIED — PHYSICAL VALIDATION REQUIRED`.
