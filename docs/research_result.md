# Research Result: Journey Map vs. Baseline Comparison

honest_scope: PROVISIONAL_RESEARCH_RESULT_NO_QUALITY_GUARANTEE
scope_walls_certified: false

---

## What was tested

A powered comparison of the journey-map pipeline against a plain-summary baseline
(referred to as the "compact" baseline in the study). The study evaluated whether
the structured journey-map output produced a measurably better "next action" for
an agent pipeline than the baseline.

## Study design

- 96 trials, split between the journey-map pipeline and the baseline.
- Primary metric: next-action quality (binary: correct / incorrect).
- Secondary metric: held-place avoidance (whether the pipeline prevented
  re-running the same action without new evidence).
- Verification method: two-clock software verification only. No blind human
  raters, no external audit, no independent lab.
- Powered at alpha=0.05 with sufficient n to detect a medium-sized effect.

## Results (honest null)

| Metric | Delta | p-value | Verdict |
|---|---|---|---|
| Next-action quality | 0.000 | 1.000 | NO MEASURABLE DIFFERENCE |
| Held-place avoidance | +0.042 | 0.819 | NOT SIGNIFICANT |

The study produced a null result. The journey-map pipeline did not produce
measurably better next-action quality than the baseline on this metric and this
verification method.

## What this means

The journey-map pipeline provides structured state persistence (position, lane,
gate, progress, update) that prevents re-derivation of context on each run.
This is framed as "structured state" not as "proven improvement." The null result
is an honest bound on what can be claimed.

No superiority claim is warranted by this evidence. The data do not support
claims of the pipeline being better than the baseline on this metric.

## Future work: M01 through M11

The milestones labeled M01-M11 in earlier internal design documents are future
work. They have not been completed, measured, or certified against external
benchmarks. They appear here only as a planning scaffold.

- M01: open-world benchmark harness (NOT_STARTED)
- M02: scored benchmark families with baselines (NOT_STARTED)
- M03: novelty detector layer (NOT_STARTED)
- M04: claim-boundary layer (NOT_STARTED)
- M05: claim-audit truth verification pass (NOT_STARTED)
- M06: semantic/LLM-gated claim-boundary layer scaffold (NOT_STARTED)
- M07: open-world measured capability gate (NOT_STARTED)
- M08: specialist model trained and compared (NOT_STARTED)
- M09: production activation with owner opt-in and rollback (NOT_STARTED)
- M10: reflection and durable memory from real execution (NOT_STARTED)
- M11: external benchmark comparison (NOT_STARTED)

## What cannot be reproduced from this repo

The raw trial records, human-annotation data, and internal benchmark inputs are
not included in this public repo. The study summary above is the complete
honest disclosure of what was measured and what was not.

See `examples/research_reproduction/` for a stub showing how to wire the
progress check to a real run if you wish to replicate the study design.

---

honest_scope: PROVISIONAL_RESEARCH_RESULT_NO_QUALITY_GUARANTEE
scope_walls_certified: false
