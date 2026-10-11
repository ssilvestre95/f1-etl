import json
from pathlib import Path
import requests
import time
from datetime import date
import logging

log = logging.getLogger("f1_etl.extract")

BASE_URL = "https://api.jolpi.ca/ergast/f1"
RAW_DIR = Path("data/raw")
PAGE_SIZE = 100
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

def fetch_page(url: str, offset: int, retries: int = 3) -> dict:
    """Fetch one page, retrying with a growing delay on failure."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(
                url, params={"limit": PAGE_SIZE, "offset": offset}, timeout=30
            )
            response.raise_for_status()
            return response.json()["MRData"]
        except requests.RequestException as e:
            status = e.response.status_code if e.response is not None else None
            retryable = status is None or status in RETRYABLE_STATUS
            log.warning("Attempt %s/%s failed (offset=%s): %s", attempt, retries, offset, e)
            if not retryable or attempt == retries:
                raise
            time.sleep(2 * attempt)


def extract_season(season: int, endpoint: str = "results") -> Path:
    """Download all rows of a season endpoint (results or sprint) and save the raw JSON."""
    results_key = "SprintResults" if endpoint == "sprint" else "Results"
    url = f"{BASE_URL}/{season}/{endpoint}.json"
    offset = 0
    races_by_round = {}

    while True:
        data = fetch_page(url, offset)
        total = int(data["total"])

        for race in data["RaceTable"]["Races"]:
            round_number = race["round"]
            if round_number in races_by_round:
                races_by_round[round_number][results_key].extend(race[results_key])
            else:
                races_by_round[round_number] = race

        offset += PAGE_SIZE
        if offset >= total:
            break

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"{endpoint}_{season}.json"
    out_path.write_text(json.dumps(list(races_by_round.values()), indent=2))
    log.info("Saved %s races to %s", len(races_by_round), out_path)
    return out_path


def fetch_schedule(season: int) -> list[dict]:
    """Return the season calendar as a list of {round, date} dicts."""
    data = fetch_page(f"{BASE_URL}/{season}.json", 0)
    return [
        {"round": int(r["round"]), "date": date.fromisoformat(r["date"])}
        for r in data["RaceTable"]["Races"]
    ]


def extract_rounds(season: int, rounds: list[int], endpoint: str = "results") -> list[dict]:
    """Fetch only the given rounds of a season, one request per round."""
    races = []
    for round_number in rounds:
        url = f"{BASE_URL}/{season}/{round_number}/{endpoint}.json"
        data = fetch_page(url, 0)
        races.extend(data["RaceTable"]["Races"])
        time.sleep(0.5)  # be nice to the rate limit
    return races


def save_raw(races: list[dict], season: int, endpoint: str) -> None:
    """Save each race as its own raw JSON file."""
    out_dir = RAW_DIR / str(season)
    out_dir.mkdir(parents=True, exist_ok=True)
    for race in races:
        path = out_dir / f"{endpoint}_{race['round']}.json"
        path.write_text(json.dumps(race, indent=2))