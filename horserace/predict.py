from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Predict win probabilities for a race card")
    ap.add_argument("--model", required=True, help="Path to trained model.joblib")
    ap.add_argument("--card_csv", required=True, help="CSV with upcoming races (same schema, finish_position optional)")
    ap.add_argument("--out_csv", required=True, help="Where to write predictions CSV")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    bundle = joblib.load(args.model)
    fb = bundle["feature_builder"]
    model = bundle["model"]

    df = pd.read_csv(args.card_csv)

    # Allow missing finish_position in card; fill dummy
    if "finish_position" not in df.columns:
        df = df.copy()
        df["finish_position"] = 0

    X, _y, groups = fb.transform(df)
    probs = model.predict_proba(X.values, groups.values)

    out_df = df[["race_id", "horse_id"]].copy()
    out_df["win_probability"] = probs

    # Sort within race by probability desc for readability
    out_df = (
        out_df
        .sort_values(["race_id", "win_probability"], ascending=[True, False])
        .reset_index(drop=True)
    )

    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args.out_csv, index=False)
    print(f"Wrote predictions to {args.out_csv}")


if __name__ == "__main__":
    main()

