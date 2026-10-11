# F1 ETL Pipeline

[Tests](https://github.com/ssilvestre95/f1-etl/actions/workflows/tests.yml/badge.svg)

A small ETL pipeline that extracts Formula 1 race and sprint results from the
[Jolpica F1 API](https://api.jolpi.ca/ergast/f1/), transforms them into a
dimensional model with `pandas`, and loads them into PostgreSQL.

## Pipeline

````mermaid
flowchart LR
    API[Jolpica F1 API] -->|paginated requests,<br/>retries| E[extract.py]
    E -->|one JSON per race| R[(data/raw)]
    R --> T[transform.py]
    T -->|facts + dimensions| L[load.py]
    L -->|upsert| DB[(PostgreSQL<br/>Neon)]
````

## Features

- **Incremental loads:** only rounds missing from the database are requested.
- **Idempotent:** loads use upserts, so re-running never duplicates data.
- **Resilient extraction:** pagination, timeouts, and retries with backoff on
  temporary errors (`429`, `5xx`, network failures).
- **Raw layer:** each race is saved as JSON in `data/raw/` before transforming.
- **Tested:** pytest suite for the transform and load logic, run in CI against a dedicated Postgres branch.
- **Scheduled:** a GitHub Actions workflow runs the pipeline every Monday and
  can also be triggered manually.
- **Atomic runs:** each run is a single transaction, so a failure never leaves
  a season half-loaded.

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

## Design decisions

- **Classification flag:** `is_classified` comes from the API's `positionText`,
  not from `status` or lap count. Retired drivers who complete 90% of the race
  are still classified, and one disqualified driver kept a numeric position.
- **Separate sprint fact table:** sprints are a different event with their own
  points, so they live in `fact_sprint_results`. The `results` endpoint alone
  understates championship totals.
- **Incremental by round:** the pipeline compares the season calendar with the
  rounds already loaded and only requests the missing ones.
- **Validate before load:** raw data is saved first, then checked (one winner,
  no duplicate drivers, plausible grid size). A failed check aborts the run
  before anything is written, and the workflow turns red.
- **Retry only transient errors:** `429`, `5xx` and network failures are
  retried with backoff; other `4xx` errors fail immediately.

## Usage

You need a PostgreSQL database (a free [Neon](https://neon.com) project works).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

echo "DATABASE_URL=postgresql://..." > .env   # your connection string

python main.py 2024          # one season
python main.py 2023 2024     # several seasons
```

### Tests

Tests need a separate database, so they never touch real data. Add a second
connection string to `.env` (for example, a Neon branch called `test`):

```bash
TEST_DATABASE_URL=postgresql://...
python -m pytest -v
```

### Scheduling

`.github/workflows/etl.yml` runs the pipeline every Monday. It expects a
`DATABASE_URL` repository secret.

## Project structure

```
etl/
├── extract.py    # API calls, pagination, retries, raw JSON
├── transform.py  # flatten, type, and model the data
└── load.py       # Postgres schema and upserts
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