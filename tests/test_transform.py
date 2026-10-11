import pandas as pd

from etl.transform import build_dim_driver, build_fact_results


def make_result(driver, team, position, position_text, status, points, millis=None):
    result = {
        "position": position,
        "positionText": position_text,
        "points": points,
        "grid": "1",
        "laps": "50",
        "status": status,
        "Driver": {
            "driverId": driver,
            "code": driver[:3].upper(),
            "givenName": driver.title(),
            "familyName": "Test",
            "dateOfBirth": "1990-01-01",
            "nationality": "Dutch",
        },
        "Constructor": {
            "constructorId": team,
            "name": team.title(),
            "nationality": "Austrian",
        },
    }
    if millis is not None:
        result["Time"] = {"millis": millis}
    return result


def make_race(round_number, results):
    return {
        "season": "2024",
        "round": str(round_number),
        "raceName": f"Test GP {round_number}",
        "date": f"2024-03-0{round_number}",
        "Circuit": {"circuitId": "test_circuit"},
        "Results": results,
    }


RACES = [
    make_race(1, [
        make_result("max", "red_bull", "1", "1", "Finished", "25", "5000000"),
        make_result("lando", "mclaren", "2", "2", "Lapped", "18", "5010000"),
        make_result("carlos", "ferrari", "3", "R", "Retired", "0"),
    ]),
    make_race(2, [
        make_result("max", "red_bull", "1", "1", "Finished", "25", "4900000"),
    ]),
]


def test_fact_has_one_row_per_driver_per_race():
    fact = build_fact_results(RACES)
    assert len(fact) == 4


def test_fact_types():
    fact = build_fact_results(RACES)
    assert fact["points"].dtype == "float64"
    assert str(fact["position"].dtype) == "Int64"
    assert pd.api.types.is_datetime64_any_dtype(fact["race_date"])


def test_is_classified_follows_position_text():
    fact = build_fact_results(RACES)
    retired = fact[fact["driver_id"] == "carlos"].iloc[0]
    assert not retired["is_classified"]
    assert pd.isna(retired["race_time_ms"])
    assert fact[fact["driver_id"] == "max"]["is_classified"].all()


def test_dim_driver_has_unique_drivers():
    dim = build_dim_driver(RACES)
    assert len(dim) == 3
    assert dim["driver_id"].is_unique