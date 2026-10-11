import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/f1.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS dim_driver (
    driver_id      TEXT PRIMARY KEY,
    code           TEXT,
    given_name     TEXT,
    family_name    TEXT,
    date_of_birth  TEXT,
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
    race_date      TEXT,
    circuit_id     TEXT,
    circuit_name   TEXT,
    locality       TEXT,
    country        TEXT,
    lat            REAL,
    long           REAL,
    PRIMARY KEY (season, round)
);

CREATE TABLE IF NOT EXISTS fact_results (
    season         INTEGER,
    round          INTEGER,
    driver_id      TEXT,
    constructor_id TEXT,
    grid           INTEGER,
    position       INTEGER,
    points         REAL,
    laps           INTEGER,
    status         TEXT,
    race_time_ms   INTEGER,
    is_classified  INTEGER,
    PRIMARY KEY (season, round, driver_id),
    FOREIGN KEY (season, round) REFERENCES dim_race (season, round),
    FOREIGN KEY (driver_id) REFERENCES dim_driver (driver_id),
    FOREIGN KEY (constructor_id) REFERENCES dim_constructor (constructor_id)
);
CREATE TABLE IF NOT EXISTS fact_sprint_results (
    season         INTEGER,
    round          INTEGER,
    driver_id      TEXT,
    constructor_id TEXT,
    grid           INTEGER,
    position       INTEGER,
    points         REAL,
    laps           INTEGER,
    status         TEXT,
    race_time_ms   INTEGER,
    is_classified  INTEGER,
    PRIMARY KEY (season, round, driver_id),
    FOREIGN KEY (season, round) REFERENCES dim_race (season, round),
    FOREIGN KEY (driver_id) REFERENCES dim_driver (driver_id),
    FOREIGN KEY (constructor_id) REFERENCES dim_constructor (constructor_id)
);
"""


def create_schema(conn: sqlite3.Connection) -> None:
    """Create all tables if they do not exist yet."""
    conn.executescript(SCHEMA)
    conn.commit()

def upsert(conn: sqlite3.Connection, table: str, df: pd.DataFrame, keys: list[str]) -> None:
    """Insert rows; on primary key conflict, update the other columns."""
    df = df.copy()
    for col in df.select_dtypes(include="datetime").columns:
        df[col] = df[col].dt.strftime("%Y-%m-%d")

    rows = df.astype(object).where(df.notna(), None).values.tolist()

    cols = list(df.columns)
    placeholders = ", ".join("?" * len(cols))
    updates = ", ".join(f"{c} = excluded.{c}" for c in cols if c not in keys)
    sql = (
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT ({', '.join(keys)}) DO UPDATE SET {updates}"
    )
    conn.executemany(sql, rows)
    conn.commit()

def loaded_rounds(conn: sqlite3.Connection, season: int) -> set[int]:
    """Rounds of a season already present in fact_results."""
    rows = conn.execute(
        "SELECT DISTINCT round FROM fact_results WHERE season = ?", (season,)
    ).fetchall()
    return {r[0] for r in rows}