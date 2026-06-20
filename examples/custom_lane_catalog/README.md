# Custom Lane Catalog Example

Shows how to replace the default 5-lane catalog with a user-defined catalog
tailored to a specific project domain (here: an ETL pipeline).

## Usage

```bash
bash examples/custom_lane_catalog/run.sh
```

Or with the Python API:

```python
from journey_map.catalog_loader import load_catalog
from journey_map.position import position
from journey_map.selector import select_lane

catalog = load_catalog("examples/custom_lane_catalog/lanes.json")
pos = position("ingest csv data from a file source", catalog=catalog)
sel = select_lane(pos, catalog=catalog)
print(sel.primary_lane)  # "ingest"
```

## Catalog format

See `lanes.json` in this directory for the format. Required fields:
`lane_id`, `name`, `description`, `markers`. All other fields are optional.
