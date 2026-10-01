# Dataset layout and collection contract

Expected layout:

```text
dataset/
  images/{train,val,test}/
  labels/{train,val,test}/
  manifests/{train.csv,val.csv,test.csv}
  raw/                 # immutable originals; excluded from model inputs
```

Empty folders are retained with `.gitkeep`. Image/label pairs use the same stem.
The recommended first annotation format is YOLO detection: one normalized
`class_id x_center y_center width height` row per object. Class IDs are fixed by
`training/dataset.yaml`; changing their order invalidates existing labels.

Each manifest should include:

`image_id,path,site,date_session,camera_id,lighting,ground_type,split,annotator,reviewer,notes`

## Collection rules

1. Capture dry, half-dry, green/soft figs, stones, leaves, branches, empty ground,
   shadows, partial occlusions and visually confusing negatives.
2. Record complete scenes, not only centered objects. Preserve the original image.
3. Use session-level splitting: all frames from one burst/location/day remain in
   one split. This prevents near-duplicate leakage.
4. Oversample safety-critical confusing scenes during collection, but report
   metrics both on a natural-distribution test set and a challenge set.
5. A second reviewer must inspect every `green_fig_ignore` and every object that
   touches a `dry_fig_collect` box before freezing the test set.
6. Do not label half-dry fruit as dry by convenience. Store it as review-required
   metadata until a product owner defines a new class and collection policy.
7. Avoid faces, vehicle plates and unrelated personal data; obtain site consent.

## Minimum metadata and QA

- Retain camera resolution, focus/exposure mode and approximate camera height.
- Record whether the sample is staged or naturally occurring.
- Reject corrupt files and flag blurred/overexposed images; do not silently delete
  difficult but valid scenes.
- Run duplicate checks before split assignment.
- Version the frozen manifest and annotation export together.

Dataset volume and class balance are deliberately `TBD`. They must be based on a
pilot error analysis, not an invented image count. Performance is `UNVERIFIED`.

