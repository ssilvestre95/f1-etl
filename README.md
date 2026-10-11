# F1 ETL Pipeline

[Tests](https://github.com/ssilvestre95/f1-etl/actions/workflows/tests.yml/badge.svg)

A small ETL pipeline that extracts Formula 1 race and sprint results from the
[Jolpica F1 API](https://api.jolpi.ca/ergast/f1/), transforms them into a
dimensional model with `pandas`, and loads them into SQLite.

## Pipeline

````mermaid
flowchart LR
    API[Jolpica F1 API] -->|paginated requests,<br/>retries| E[extract.py]
    E -->|one JSON per race| R[(data/raw)]
    R --> T[transform.py]
    T -->|facts + dimensions| L[load.py]
    L -->|upsert| DB[(SQLite<br/>f1.db)]
````

## Features

- **Incremental loads:** only rounds missing from the database are requested.
- **Idempotent:** loads use upserts, so re-running never duplicates data.
- **Resilient extraction:** pagination, timeouts, and retries with backoff on
  temporary errors (`429`, `5xx`, network failures).
- **Raw layer:** each race is saved as JSON in `data/raw/` before transforming.
- **Tested:** `pytest` suite for the transform and load logic.

## Data model

| Table | Grain |
|---|---|
| `fact_results` | one row per driver per race |
| `fact_sprint_results` | one row per driver per sprint |
| `dim_driver` | one row per driver |
| `dim_constructor` | one row per team |
| `dim_race` | one row per race (`season`, `round`) |

`is_classified` is derived from the API's `positionText` (numeric means
classified; `R`, `D` and `W` mean retired, disqualified and withdrawn).

## Usage

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python main.py 2024          # one season
python main.py 2023 2024     # several seasons
python -m pytest -v          # run the tests
```

The database is created at `data/f1.db`.

## Project structure

```
etl/
├── extract.py    # API calls, pagination, retries, raw JSON
├── transform.py  # flatten, type, and model the data
└── load.py       # SQLite schema and upserts
tests/            # pytest suites
main.py           # orchestrates the pipeline
```

## Example query

```sql
SELECT d.given_name || ' ' || d.family_name AS driver, SUM(f.points) AS points
FROM fact_results f
JOIN dim_driver d ON d.driver_id = f.driver_id
WHERE f.season = 2024
GROUP BY f.driver_id
ORDER BY points DESC
LIMIT 5;
```

Sprint points live in `fact_sprint_results` and must be added to match the official championship totals.