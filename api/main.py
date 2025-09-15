from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


ARTIFACT_PATH = os.getenv("HRP_MODEL_PATH", str(Path(__file__).resolve().parents[1] / "artifacts" / "model.joblib"))


class Runner(BaseModel):
    race_id: str
    horse_id: str
    distance_meters: float | None = None
    draw: int | None = None
    weight_carried: float | None = None
    going: str | None = None
    race_class: str | int | None = None
    age: int | None = None
    days_since_last_run: int | None = None
    jockey: str | None = None
    trainer: str | None = None
    official_rating: float | None = None
    speed_figure: float | None = None
    field_size: int | None = None
    odds: float | None = None


class PredictRequest(BaseModel):
    runners: List[Runner]


app = FastAPI(title="HRP API", version="0.1.0")


def _load_bundle(path: str):
    if not Path(path).exists():
        raise FileNotFoundError(f"Model bundle not found at {path}")
    return joblib.load(path)


@app.on_event("startup")
def _startup() -> None:
    global BUNDLE, FB, MODEL
    BUNDLE = _load_bundle(ARTIFACT_PATH)
    FB = BUNDLE["feature_builder"]
    MODEL = BUNDLE["model"]


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
def predict(req: PredictRequest) -> Dict[str, Any]:
    if not req.runners:
        raise HTTPException(status_code=400, detail="No runners provided")

    df = pd.DataFrame([r.dict() for r in req.runners])
    # Ensure finish_position exists for transform; fill with 0
    if "finish_position" not in df.columns:
        df["finish_position"] = 0

    X, _y, groups = FB.transform(df)
    probs = MODEL.predict_proba(X.values, groups.values)

    out = []
    for row, p in zip(df.to_dict(orient="records"), probs):
        out.append({
            "race_id": row.get("race_id"),
            "horse_id": row.get("horse_id"),
            "win_probability": float(p),
        })
    return {"predictions": out}


# Dev entry: uvicorn api.main:app --reload
