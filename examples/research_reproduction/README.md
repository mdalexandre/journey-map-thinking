# Research Reproduction

This directory provides a stub for reproducing the study design described in
`docs/research_result.md`.

## What CAN be reproduced

The study design: run the 5-stage journey-map pipeline on a set of goals, record
whether `jm progress` exits 0 (progress) or 1 (no-progress), compare with a
baseline that skips the pipeline.

See `harness_stub.py` for a minimal wiring example.

## What CANNOT be reproduced from this repo

- The raw trial inputs and labels used in the original 96-trial comparison.
- The human annotation data (none was collected; this was two-clock software
  verification only).
- The internal benchmark families A-F referenced in the forward journey design.

## Honest summary

The 96-trial comparison produced delta = 0.000, p = 1.000 on the next-action
metric. The study found no measurable difference between the pipeline output and
the baseline. This null result is documented in `docs/research_result.md` with
no superiority claim.
