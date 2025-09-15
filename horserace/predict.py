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
    ap.add_argument("--out_json", help="Optional: also write predictions JSON here")
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

    out_dir = Path(args.out_csv).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args.out_csv, index=False)
    print(f"Wrote predictions to {args.out_csv}")

    if args.out_json:
        try:
            # Emit an array of objects for easy frontend consumption
            records = out_df.to_dict(orient="records")
            out_json_path = Path(args.out_json)
            out_json_path.parent.mkdir(parents=True, exist_ok=True)
            import json

            with open(out_json_path, "w", encoding="utf-8") as f:
                json.dump(records, f)
            print(f"Wrote predictions JSON to {out_json_path}")
        except Exception as e:
            print(f"Warning: failed to write JSON output: {e}")


if __name__ == "__main__":
    main()
