# Annotation review

Annotation exports live in `ai/dataset/labels`; this directory stores annotation
instructions, reviewer notes and tool-specific configuration only.

- Fit boxes to visible object extent consistently.
- Label every instance of the five supported classes, including partially visible
  objects when class identity remains clear.
- Mark ambiguous fruit for review; never force it into `dry_fig_collect`.
- Record occlusion/truncation in reviewer notes when the selected tool supports it.
- Resolve class disagreement with an agronomy/product reviewer before the test
  manifest is frozen.
- Audit false `dry_fig_collect` labels first because they corrupt the critical
  green/soft-fig false-positive measurement.

Annotation quality is `UNVERIFIED — PHYSICAL VALIDATION REQUIRED`.

