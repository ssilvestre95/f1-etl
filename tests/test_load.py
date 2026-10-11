import sqlite3

import pandas as pd

from etl.load import create_schema, upsert


def make_conn():
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    return conn


def make_constructors():
    return pd.DataFrame(
        {
            "constructor_id": ["red_bull", "ferrari"],
            "name": ["Red Bull", "Ferrari"],
            "nationality": ["Austrian", "Italian"],
        }
    )


def test_upsert_is_idempotent():
    conn = make_conn()
    df = make_constructors()
    upsert(conn, "dim_constructor", df, ["constructor_id"])
    upsert(conn, "dim_constructor", df, ["constructor_id"])
    count = conn.execute("SELECT COUNT(*) FROM dim_constructor").fetchone()[0]
    assert count == 2


def test_upsert_updates_existing_row():
    conn = make_conn()
    df = make_constructors()
    upsert(conn, "dim_constructor", df, ["constructor_id"])

    df.loc[0, "name"] = "Oracle Red Bull"
    upsert(conn, "dim_constructor", df, ["constructor_id"])

    name = conn.execute(
        "SELECT name FROM dim_constructor WHERE constructor_id = 'red_bull'"
    ).fetchone()[0]
    assert name == "Oracle Red Bull"


def test_upsert_stores_missing_time_as_null():
    conn = make_conn()
    df = pd.DataFrame(
        {
            "season": [2024],
            "round": [1],
            "driver_id": ["carlos"],
            "constructor_id": ["ferrari"],
            "grid": pd.array([3], dtype="Int64"),
            "position": pd.array([20], dtype="Int64"),
            "points": [0.0],
            "laps": pd.array([10], dtype="Int64"),
            "status": ["Retired"],
            "race_time_ms": pd.array([None], dtype="Int64"),
            "is_classified": [False],
        }
    )
    upsert(conn, "fact_results", df, ["season", "round", "driver_id"])

    row = conn.execute("SELECT race_time_ms, is_classified FROM fact_results").fetchone()
    assert row == (None, 0)