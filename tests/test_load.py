import pandas as pd
import psycopg
import pytest

from etl.load import upsert


def constructors():
    return pd.DataFrame(
        {
            "constructor_id": ["red_bull", "ferrari"],
            "name": ["Red Bull", "Ferrari"],
            "nationality": ["Austrian", "Italian"],
        }
    )


def seed_dimensions(conn):
    upsert(conn, "dim_constructor", constructors(), ["constructor_id"])
    upsert(
        conn,
        "dim_driver",
        pd.DataFrame(
            {
                "driver_id": ["carlos"],
                "code": ["SAI"],
                "given_name": ["Carlos"],
                "family_name": ["Sainz"],
                "date_of_birth": pd.to_datetime(["1994-09-01"]),
                "nationality": ["Spanish"],
            }
        ),
        ["driver_id"],
    )
    upsert(
        conn,
        "dim_race",
        pd.DataFrame(
            {
                "season": [2024],
                "round": [1],
                "race_name": ["Test GP"],
                "race_date": pd.to_datetime(["2024-03-02"]),
                "circuit_id": ["test"],
                "circuit_name": ["Test Circuit"],
                "locality": ["Somewhere"],
                "country": ["Nowhere"],
                "lat": [10.5],
                "long": [20.5],
            }
        ),
        ["season", "round"],
    )


def fact_row():
    return pd.DataFrame(
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


def test_upsert_is_idempotent(conn):
    df = constructors()
    upsert(conn, "dim_constructor", df, ["constructor_id"])
    upsert(conn, "dim_constructor", df, ["constructor_id"])
    count = conn.execute("SELECT COUNT(*) FROM dim_constructor").fetchone()[0]
    assert count == 2


def test_upsert_updates_existing_row(conn):
    df = constructors()
    upsert(conn, "dim_constructor", df, ["constructor_id"])

    df.loc[0, "name"] = "Oracle Red Bull"
    upsert(conn, "dim_constructor", df, ["constructor_id"])

    name = conn.execute(
        "SELECT name FROM dim_constructor WHERE constructor_id = 'red_bull'"
    ).fetchone()[0]
    assert name == "Oracle Red Bull"


def test_missing_time_is_null_and_flag_is_boolean(conn):
    seed_dimensions(conn)
    upsert(conn, "fact_results", fact_row(), ["season", "round", "driver_id"])

    row = conn.execute("SELECT race_time_ms, is_classified FROM fact_results").fetchone()
    assert row == (None, False)


def test_foreign_keys_are_enforced(conn):
    upsert(conn, "dim_constructor", constructors(), ["constructor_id"])
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        upsert(conn, "fact_results", fact_row(), ["season", "round", "driver_id"])