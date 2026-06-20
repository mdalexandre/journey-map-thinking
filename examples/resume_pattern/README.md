# Resume Pattern Example

The resume pattern lets you pick up a pipeline run from a saved position JSON
rather than re-running `jm position` from scratch.

## What this is

Structured state persistence: instead of re-deriving where the task is on the
journey map each run, you save `journey_position.json` and resume from
`jm select-lane` directly.

## What this is NOT

The resume pattern is NOT a proven improvement over re-running the full pipeline.
The 96-trial comparison between structured state and the baseline produced
delta = 0.000, p = 1.000 on the next-action metric. See `docs/research_result.md`
for the full honest null result.

The value of the resume pattern is that it prevents re-derivation of context
when the position is already known, not that it improves outcomes.

## Usage

```bash
python examples/resume_pattern/run.py
```
