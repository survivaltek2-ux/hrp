from __future__ import annotations

import os
import datetime as dt
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth


def _get_first(d: Dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def _norm_race_id(race: Dict[str, Any]) -> str:
    meet = str(_get_first(race, ["meeting_id", "meetingId", "track_id", "trackId", "venue_id", "venueId"], "M"))
    num = str(_get_first(race, ["race_number", "raceNumber", "number", "raceNo"], "0"))
    date = str(_get_first(race, ["date", "race_date", "raceDate"], ""))
    return "-".join([p for p in [date, meet, num] if p])


def _kg_from_weight(val: Any, unit: str) -> Optional[float]:
    try:
        x = float(val)
    except Exception:
        return None
    if unit.lower() in {"kg", "kilogram", "kilograms"}:
        return x
    if unit.lower() in {"lb", "lbs", "pound", "pounds"}:
        return x * 0.45359237
    return x


def _meters_from_distance(val: Any, unit: str) -> Optional[float]:
    try:
        x = float(val)
    except Exception:
        return None
    u = unit.lower()
    if u in {"m", "meter", "meters"}:
        return x
    if u in {"f", "furlong", "furlongs"}:
        return x * 201.168
    if u in {"y", "yard", "yards"}:
        return x * 0.9144
    if u in {"km", "kilometer", "kilometers"}:
        return x * 1000.0
    return x


class TheRacingAPIClient:
    """Thin client for TheRacingAPI-like services.

    This is a template with flexible field extraction to accommodate variations
    in provider JSON. Set API base and key via args or env:

    - THERACINGAPI_BASE (default: https://api.theracingapi.com)
    - THERACINGAPI_KEY (required)
    - THERACINGAPI_KEY_HEADER (default: x-api-key)
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        # Basic auth
        username: Optional[str] = None,
        password: Optional[str] = None,
        # Legacy/API-key auth (fallback)
        api_key: Optional[str] = None,
        key_header: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.base_url = (base_url or os.getenv("THERACINGAPI_BASE") or "https://api.theracingapi.com").rstrip("/")

        # Prefer Basic Auth if provided
        self.username = username or os.getenv("THERACINGAPI_USERNAME")
        self.password = password or os.getenv("THERACINGAPI_PASSWORD")
        self.api_key = api_key or os.getenv("THERACINGAPI_KEY")
        self.key_header = key_header or os.getenv("THERACINGAPI_KEY_HEADER") or "x-api-key"
        self.timeout = timeout

        if self.username and self.password:
            self._auth_mode = "basic"
        elif self.api_key:
            self._auth_mode = "apikey"
        else:
            raise ValueError(
                "Missing credentials. Set THERACINGAPI_USERNAME and THERACINGAPI_PASSWORD for Basic Auth, "
                "or THERACINGAPI_KEY for API key auth."
            )

    def _request(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        kwargs: Dict[str, Any] = {"params": params or {}, "timeout": self.timeout}
        if self._auth_mode == "basic":
            kwargs["auth"] = HTTPBasicAuth(self.username, self.password)
        else:
            kwargs["headers"] = {self.key_header: self.api_key}
        resp = requests.get(url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    # --------------------------- Public fetchers --------------------------- #
    def fetch_results(
        self,
        *,
        start_date: str,
        end_date: Optional[str] = None,
        region: Optional[str] = None,
        distance_unit: str = "m",
        weight_unit: str = "kg",
    ) -> pd.DataFrame:
        """Fetch historical results into our training schema.

        Expected provider endpoints may vary; update the path/params to match.
        """
        end = end_date or start_date
        payload = self._request(
            "/v1/results",
            params={"start_date": start_date, "end_date": end, **({"region": region} if region else {})},
        )
        races: List[Dict[str, Any]] = payload.get("races") or payload.get("data") or []
        rows: List[Dict[str, Any]] = []
        for race in races:
            race_id = _norm_race_id(race)
            going = _get_first(race, ["going", "surfaceCondition", "trackCondition", "goingDesc"], None)
            rclass = _get_first(race, ["class", "grade", "raceClass"], None)
            distance_val = _get_first(race, ["distance_meters", "distance", "dist"], None)
            distance_m = _meters_from_distance(distance_val, distance_unit) if distance_val is not None else None

            runners = race.get("runners") or race.get("entries") or []
            field_size = len(runners)
            for r in runners:
                finish_pos = _get_first(r, ["finish_position", "position", "pos", "placing"], None)
                if finish_pos is None:
                    continue  # results must include a position to train
                horse_id = str(_get_first(r, ["horse_id", "horseId", "id"], _get_first(r, ["horse_name", "name"], "")))
                draw = _get_first(r, ["draw", "stall", "post"], None)
                weight = _kg_from_weight(_get_first(r, ["weight_carried", "weight", "carriedWeight"], None), weight_unit)
                age = _get_first(r, ["age"], None)
                rating = _get_first(r, ["official_rating", "rating", "OR"], None)
                jockey = _get_first(r, ["jockey", "jockey_name"], None)
                if isinstance(jockey, dict):
                    jockey = _get_first(jockey, ["name", "fullName"], None)
                trainer = _get_first(r, ["trainer", "trainer_name"], None)
                if isinstance(trainer, dict):
                    trainer = _get_first(trainer, ["name", "fullName"], None)
                dslr = _get_first(r, ["days_since_last_run", "daysSinceRun", "daysSinceLast"], None)

                rows.append(
                    {
                        "race_id": race_id,
                        "horse_id": horse_id,
                        "finish_position": int(finish_pos) if str(finish_pos).isdigit() else None,
                        "distance_meters": distance_m,
                        "draw": draw,
                        "weight_carried": weight,
                        "going": going,
                        "race_class": rclass,
                        "age": age,
                        "days_since_last_run": dslr,
                        "jockey": jockey,
                        "trainer": trainer,
                        "official_rating": rating,
                        "field_size": field_size,
                    }
                )

        df = pd.DataFrame(rows)
        # Enforce required columns, even if missing values
        required = [
            "race_id",
            "horse_id",
            "finish_position",
            "distance_meters",
            "draw",
            "weight_carried",
            "going",
            "race_class",
            "age",
            "days_since_last_run",
            "jockey",
            "trainer",
        ]
        for c in required:
            if c not in df.columns:
                df[c] = None
        return df

    def fetch_racecard(
        self,
        *,
        date: str,
        region: Optional[str] = None,
        distance_unit: str = "m",
        weight_unit: str = "kg",
    ) -> pd.DataFrame:
        """Fetch upcoming races (no finish positions)."""
        payload = self._request(
            "/v1/racecards",
            params={"date": date, **({"region": region} if region else {})},
        )
        races: List[Dict[str, Any]] = payload.get("races") or payload.get("data") or []
        rows: List[Dict[str, Any]] = []
        for race in races:
            race_id = _norm_race_id(race)
            going = _get_first(race, ["going", "surfaceCondition", "trackCondition", "goingDesc"], None)
            rclass = _get_first(race, ["class", "grade", "raceClass"], None)
            distance_val = _get_first(race, ["distance_meters", "distance", "dist"], None)
            distance_m = _meters_from_distance(distance_val, distance_unit) if distance_val is not None else None

            runners = race.get("runners") or race.get("entries") or []
            field_size = len(runners)
            for r in runners:
                horse_id = str(_get_first(r, ["horse_id", "horseId", "id"], _get_first(r, ["horse_name", "name"], "")))
                draw = _get_first(r, ["draw", "stall", "post"], None)
                weight = _kg_from_weight(_get_first(r, ["weight_carried", "weight", "carriedWeight"], None), weight_unit)
                age = _get_first(r, ["age"], None)
                rating = _get_first(r, ["official_rating", "rating", "OR"], None)
                jockey = _get_first(r, ["jockey", "jockey_name"], None)
                if isinstance(jockey, dict):
                    jockey = _get_first(jockey, ["name", "fullName"], None)
                trainer = _get_first(r, ["trainer", "trainer_name"], None)
                if isinstance(trainer, dict):
                    trainer = _get_first(trainer, ["name", "fullName"], None)
                dslr = _get_first(r, ["days_since_last_run", "daysSinceRun", "daysSinceLast"], None)

                rows.append(
                    {
                        "race_id": race_id,
                        "horse_id": horse_id,
                        "finish_position": None,  # card data has no result yet
                        "distance_meters": distance_m,
                        "draw": draw,
                        "weight_carried": weight,
                        "going": going,
                        "race_class": rclass,
                        "age": age,
                        "days_since_last_run": dslr,
                        "jockey": jockey,
                        "trainer": trainer,
                        "official_rating": rating,
                        "field_size": field_size,
                    }
                )

        df = pd.DataFrame(rows)
        required = [
            "race_id",
            "horse_id",
            "finish_position",
            "distance_meters",
            "draw",
            "weight_carried",
            "going",
            "race_class",
            "age",
            "days_since_last_run",
            "jockey",
            "trainer",
        ]
        for c in required:
            if c not in df.columns:
                df[c] = None
        return df
