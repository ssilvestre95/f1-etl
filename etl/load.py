import os

import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()

SCHEMA = """
CREATE TABLE IF NOT EXISTS dim_driver (
    driver_id      TEXT PRIMARY KEY,
    code           TEXT,
    given_name     TEXT,
    family_name    TEXT,
    date_of_birth  DATE,
    nationality    TEXT
);

CREATE TABLE IF NOT EXISTS dim_constructor (
    constructor_id TEXT PRIMARY KEY,
    name           TEXT,
    nationality    TEXT
);

CREATE TABLE IF NOT EXISTS dim_race (
    season         INTEGER,
    round          INTEGER,
    race_name      TEXT,
    race_date      DATE,
    circuit_id     TEXT,
    circuit_name   TEXT,
    locality       TEXT,
    country        TEXT,
    lat            DOUBLE PRECISION,
    long           DOUBLE PRECISION,
    PRIMARY KEY (season, round)
);

CREATE TABLE IF NOT EXISTS fact_results (
    season         INTEGER,
    round          INTEGER,
    driver_id      TEXT REFERENCES dim_driver (driver_id),
    constructor_id TEXT REFERENCES dim_constructor (constructor_id),
    grid           INTEGER,
    position       INTEGER,
    points         DOUBLE PRECISION,
    laps           INTEGER,
    status         TEXT,
    race_time_ms   BIGINT,
    is_classified  BOOLEAN,
    PRIMARY KEY (season, round, driver_id),
    FOREIGN KEY (season, round) REFERENCES dim_race (season, round)
);

CREATE TABLE IF NOT EXISTS fact_sprint_results (
    season         INTEGER,
    round          INTEGER,
    driver_id      TEXT REFERENCES dim_driver (driver_id),
    constructor_id TEXT REFERENCES dim_constructor (constructor_id),
    grid           INTEGER,
    position       INTEGER,
    points         DOUBLE PRECISION,
    laps           INTEGER,
    status         TEXT,
    race_time_ms   BIGINT,
    is_classified  BOOLEAN,
    PRIMARY KEY (season, round, driver_id),
    FOREIGN KEY (season, round) REFERENCES dim_race (season, round)
);
"""


def get_connection() -> psycopg.Connection:
    """Open a connection using DATABASE_URL (use it with a `with` block)."""
    return psycopg.connect(os.environ["DATABASE_URL"])


def create_schema(conn: psycopg.Connection) -> None:
    """Create all tables if they do not exist yet."""
    conn.execute(SCHEMA)


def upsert(conn: psycopg.Connection, table: str, df: pd.DataFrame, keys: list[str]) -> None:
    """Insert rows; on primary key conflict, update the other columns."""
    df = df.copy()
    for col in df.select_dtypes(include="datetime").columns:
        df[col] = df[col].dt.date

    rows = df.astype(object).where(df.notna(), None).values.tolist()

    cols = list(df.columns)
    placeholders = ", ".join(["%s"] * len(cols))
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c not in keys)
    sql = (
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT ({', '.join(keys)}) DO UPDATE SET {updates}"
    )
    with conn.cursor() as cur:
        cur.executemany(sql, rows)


def loaded_rounds(conn: psycopg.Connection, season: int) -> set[int]:
    """Rounds of a season already present in fact_results."""
    rows = conn.execute(
        "SELECT DISTINCT round FROM fact_results WHERE season = %s", (season,)
    ).fetchall()
    return {r[0] for r in rows}