import logging
import sqlite3
import sys
from datetime import date

from etl.extract import extract_rounds, fetch_schedule, save_raw
from etl.load import DB_PATH, create_schema, loaded_rounds, upsert
from etl.transform import (
    build_dim_constructor,
    build_dim_driver,
    build_dim_race,
    build_fact_results,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("f1_etl")

DIM_COLUMNS_IN_FACT = ["race_name", "race_date", "circuit_id"]
FACT_KEYS = ["season", "round", "driver_id"]


def run(season: int) -> None:
    log.info("Starting ETL for season %s", season)

    with sqlite3.connect(DB_PATH) as conn:
        create_schema(conn)

        # Decide what is missing
        schedule = fetch_schedule(season)
        past = {r["round"] for r in schedule if r["date"] <= date.today()}
        missing = sorted(past - loaded_rounds(conn, season))
        if not missing:
            log.info("Season %s is up to date", season)
            return
        log.info("Missing rounds: %s", missing)

        # Extract
        races = extract_rounds(season, missing, "results")
        sprints = extract_rounds(season, missing, "sprint")
        save_raw(races, season, "results")
        save_raw(sprints, season, "sprint")
        if not races:
            log.warning("No results published yet for rounds %s", missing)
            return
        log.info("Extracted %s races and %s sprints", len(races), len(sprints))

        # Transform + Load
        upsert(conn, "dim_driver", build_dim_driver(races), ["driver_id"])
        upsert(conn, "dim_constructor", build_dim_constructor(races), ["constructor_id"])
        upsert(conn, "dim_race", build_dim_race(races), ["season", "round"])

        fact = build_fact_results(races).drop(columns=DIM_COLUMNS_IN_FACT)
        upsert(conn, "fact_results", fact, FACT_KEYS)
        log.info("Loaded %s result rows", len(fact))

        if sprints:
            fact_sprint = build_fact_results(sprints, "SprintResults").drop(
                columns=DIM_COLUMNS_IN_FACT
            )
            upsert(conn, "fact_sprint_results", fact_sprint, FACT_KEYS)
            log.info("Loaded %s sprint rows", len(fact_sprint))

    log.info("Finished ETL for season %s", season)


if __name__ == "__main__":
    seasons = [int(s) for s in sys.argv[1:]] or [2024]
    for season in seasons:
        run(season)