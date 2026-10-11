import pandas as pd

COLUMNS = {
    "season": "season",
    "round": "round",
    "raceName": "race_name",
    "date": "race_date",
    "Circuit.circuitId": "circuit_id",
    "Driver.driverId": "driver_id",
    "Constructor.constructorId": "constructor_id",
    "grid": "grid",
    "position": "position",
    "points": "points",
    "laps": "laps",
    "status": "status",
    "Time.millis": "race_time_ms",
}

def flatten_results(races: list[dict], record_path: str = "Results") -> pd.DataFrame:
    """Flatten nested race JSON into one row per driver per race."""
    return pd.json_normalize(
        races,
        record_path=record_path,
        meta=["season", "round", "raceName", "date", ["Circuit", "circuitId"]],
    )


def build_fact_results(races: list[dict], record_path: str = "Results") -> pd.DataFrame:
    """Flatten raw race JSON into one typed row per driver per race."""
    df = flatten_results(races, record_path)

    fact = df[list(COLUMNS)].rename(columns=COLUMNS)

    fact["season"] = fact["season"].astype(int)
    fact["round"] = fact["round"].astype(int)
    fact["race_date"] = pd.to_datetime(fact["race_date"])
    fact["points"] = fact["points"].astype(float)

    for col in ["grid", "position", "laps", "race_time_ms"]:
        fact[col] = pd.to_numeric(fact[col], errors="coerce").astype("Int64")

    # Classified = API gives a numeric position text (R, D, W otherwise)
    fact["is_classified"] = df["positionText"].str.isnumeric()

    return fact

def build_dim_driver(races: list[dict]) -> pd.DataFrame:
    """One row per driver."""
    df = flatten_results(races)
    cols = {
        "Driver.driverId": "driver_id",
        "Driver.code": "code",
        "Driver.givenName": "given_name",
        "Driver.familyName": "family_name",
        "Driver.dateOfBirth": "date_of_birth",
        "Driver.nationality": "nationality",
    }
    dim = df[list(cols)].rename(columns=cols)
    dim = dim.drop_duplicates(subset="driver_id").reset_index(drop=True)
    dim["date_of_birth"] = pd.to_datetime(dim["date_of_birth"])
    return dim


def build_dim_constructor(races: list[dict]) -> pd.DataFrame:
    """One row per constructor (team)."""
    df = flatten_results(races)
    cols = {
        "Constructor.constructorId": "constructor_id",
        "Constructor.name": "name",
        "Constructor.nationality": "nationality",
    }
    dim = df[list(cols)].rename(columns=cols)
    return dim.drop_duplicates(subset="constructor_id").reset_index(drop=True)

def build_dim_race(races: list[dict]) -> pd.DataFrame:
    """One row per race, with circuit details."""
    df = pd.json_normalize(races).drop(columns=["Results"])
    cols = {
        "season": "season",
        "round": "round",
        "raceName": "race_name",
        "date": "race_date",
        "Circuit.circuitId": "circuit_id",
        "Circuit.circuitName": "circuit_name",
        "Circuit.Location.locality": "locality",
        "Circuit.Location.country": "country",
        "Circuit.Location.lat": "lat",
        "Circuit.Location.long": "long",
    }
    dim = df[list(cols)].rename(columns=cols)
    dim["season"] = dim["season"].astype(int)
    dim["round"] = dim["round"].astype(int)
    dim["race_date"] = pd.to_datetime(dim["race_date"])
    dim["lat"] = dim["lat"].astype(float)
    dim["long"] = dim["long"].astype(float)
    return dim

