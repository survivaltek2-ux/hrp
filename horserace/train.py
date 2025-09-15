from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .feature_pipeline import FeatureBuilder
from .model import SoftmaxRaceModel


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Train horse race win model")
    ap.add_argument("--train_csv", required=True, help="Path to training CSV")
    ap.add_argument("--out_model", required=True, help="Output path for model.joblib")
    ap.add_argument("--use_odds", action="store_true", help="Include odds as a feature if present")
    ap.add_argument("--test_size", type=float, default=0.15, help="Validation split fraction")
    ap.add_argument("--random_state", type=int, default=42)
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.train_csv)

    fb = FeatureBuilder(use_odds=args.use_odds)
    fb.fit(df)
    X, y, groups = fb.transform(df)

    # Group-aware split: split by unique race_id so no leakage across races.
    rng = np.random.default_rng(args.random_state)
    unique_groups = np.array(sorted(groups.unique()))
    n_groups = len(unique_groups)
    if n_groups >= 2:
        n_val_groups = max(1, int(round(args.test_size * n_groups)))
        n_val_groups = min(n_groups - 1, n_val_groups)  # keep at least 1 train group
        val_groups = set(rng.choice(unique_groups, size=n_val_groups, replace=False))
        val_mask = groups.isin(val_groups)
    else:
        # Fallback to row-level split when only one group exists
        n = len(X)
        n_val = max(1, int(round(args.test_size * n)))
        idx = np.arange(n)
        rng.shuffle(idx)
        val_idx = set(idx[:n_val].tolist())
        val_mask = groups.index.to_series().map(lambda i: i in val_idx)

    X_train, X_val = X[~val_mask], X[val_mask]
    y_train, y_val = y[~val_mask], y[val_mask]
    g_train, g_val = groups[~val_mask], groups[val_mask]

    model = SoftmaxRaceModel()
    model.fit(X_train.values, y_train.values)

    val_loss = model.evaluate_log_loss(X_val.values, y_val.values, g_val.values)
    print(f"Validation softmax log-loss: {val_loss:.5f}")

    out = {
        "feature_builder": fb,
        "model": model,
        "feature_columns": fb.feature_columns_,
    }
    Path(args.out_model).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(out, args.out_model)
    print(f"Saved model to {args.out_model}")


if __name__ == "__main__":
    main()
