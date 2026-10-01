# AI validation protocol

Status: `UNVERIFIED — PHYSICAL VALIDATION REQUIRED`

Report precision, recall and support for every class, the full confusion matrix,
and especially:

- green/soft fig predicted as `dry_fig_collect` / all green/soft figs;
- stone predicted as `dry_fig_collect` / all stones;
- dry-fig precision at the deployed confidence and overlap thresholds.

Metrics must be generated from a frozen, session-disjoint test manifest. Report
confidence intervals or raw numerators/denominators so a small test set is visible.
Also report latency distributions on the actual V0 compute target and camera stream.
For detection metrics, preregister one-to-one box matching and IoU rules; export
unmatched truth/predictions using the `__none__` convention documented under
`ai/evaluation/`. A classification-only confusion table must not be presented as a
complete detection result.

Evaluate separate slices for lighting, ground, occlusion, object size/image region,
camera height, staged/natural scenes and site/session. A threshold may be deployed
only after a recorded trade-off review; the sample value in `gate.py` is not an
accepted threshold. No metric authorizes motion without the downstream reach,
collision, calibration, interlock and operator-mode checks.

Failure review order is green/soft-to-dry, stone-to-dry, branch overlap, missed dry
figs, then nuisance leaf detections. Any dataset or threshold change creates a new
model version and requires the entire frozen evaluation to be rerun.
