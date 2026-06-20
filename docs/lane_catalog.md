# Lane Catalog

## Default lanes

The built-in catalog contains five generic lanes:

| Lane ID | Name | Description |
|---|---|---|
| build | Build | Build a new artifact, project, feature, module, or service. |
| research | Research | Investigate, benchmark, evaluate, or compare an approach. |
| fix | Fix | Repair a defect, regression, failing test, or broken behavior. |
| blocked | Blocked | A blocker requires owner or external action before proceeding. |
| vision | Vision | A pure-vision ask that must be grounded into a concrete first slice. |

Routing priority (most specific first): `blocked, vision, research, fix, build`.

## Custom catalog format

A custom catalog is a JSON array (or YAML sequence) of lane objects.
Required fields per lane: `lane_id`, `name`, `description`, `markers`.

```json
[
  {
    "lane_id": "ingest",
    "name": "Data Ingestion",
    "description": "Build or fix data ingestion pipelines.",
    "markers": ["ingest", "ingestion", "csv pipeline"],
    "milestones": ["ingestion module"],
    "gates": ["end-to-end test passes"],
    "progress_artifacts": ["ingestion.py"],
    "provisional_level": "L2_ARTIFACT_PRODUCING",
    "component": "ingestion"
  }
]
```

Optional fields: `component`, `provisional_level`, `milestones`, `gates`,
`blockers`, `owner_dependent`, `next_unlocks`, `claim_boundary`,
`progress_artifacts`.

## Loading a custom catalog

Via CLI flag:

```bash
jm position --raw raw_goal.txt --catalog my_lanes.json --output pos.json
```

Via environment variable:

```bash
export JOURNEY_MAP_CATALOG=my_lanes.json
jm position --raw raw_goal.txt --output pos.json
```

Via Python API:

```python
from journey_map.catalog_loader import load_catalog
from journey_map.position import position

catalog = load_catalog("my_lanes.json")
pos = position("ingest csv data", catalog=catalog)
```

## YAML catalogs

YAML is supported with the optional extra:

```bash
pip install 'journey-map-thinking[yaml]'
```

Then use a `.yaml` or `.yml` file with the same structure.

## Validation

The loader validates all required fields and raises a `ValueError` with the
field name and lane entry if any are missing or malformed.
