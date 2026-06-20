# Security Policy

## Reporting a vulnerability

If you find a security issue, please open a GitHub issue with the label
"security" or contact the maintainers directly. Do not include sensitive
details in public issues.

## What this package does and does not do

- **Does:** read and write local JSON and text files under `~/.journey_map/`.
- **Does not:** make network calls, spawn subprocesses, access credentials,
  or read environment variables beyond `JOURNEY_MAP_ENABLED`,
  `JOURNEY_MAP_ROOT`, and `JOURNEY_MAP_CATALOG`.

## Sensitive data warning

Do not commit your `journey_history.jsonl` or other pipeline run files to a
public repository. These files may contain raw goal descriptions from your
private projects. The `.gitignore` in this repo excludes `*.jsonl` and
`pipeline_runs/` by default.

## No live credentials

This package does not use API keys, tokens, or credentials of any kind.
The `JOURNEY_MAP_ENABLED` environment variable is a boolean flag only.
