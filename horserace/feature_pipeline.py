from __future__ import annotations

import numpy as np
import pandas as pd
from typing import List, Optional, Tuple


REQUIRED_COLUMNS = [
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


class FeatureBuilder:
    """Feature engineering with frequency-capped one-hot for categoricals.

    - Numeric features are used as-is with clipping and optional normalization.
    - Categorical features use top-K most frequent categories; the rest collapse into an "__OTHER__" bucket.
    - Race-level normalization features (e.g., draw rank, weight vs field mean) are added.
    """

    def __init__(
        self,
        *,
        cat_top_k: int = 50,
        use_odds: bool = False,
        include_optional: bool = True,
    ) -> None:
        self.cat_top_k = cat_top_k
        self.use_odds = use_odds
        self.include_optional = include_optional

        self.categorical_cols_: List[str] = ["going", "race_class", "jockey", "trainer"]
        self.numeric_cols_: List[str] = [
            "distance_meters",
            "draw",
            "weight_carried",
            "age",
            "days_since_last_run",
        ]

        # Optional numeric columns if present
        self.optional_numeric_: List[str] = [
            "official_rating",
            "speed_figure",
            "field_size",
        ]

        if self.use_odds:
            self.optional_numeric_.append("odds")

        # Fitted artifacts
        self._cat_top_values: dict[str, List[str]] = {}
        self._num_means: dict[str, float] = {}
        self._num_stds: dict[str, float] = {}
        self.feature_columns_: List[str] = []

    def _validate_columns(self, df: pd.DataFrame) -> None:
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    @staticmethod
    def _add_derived(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Field size per race if not provided.
        if "field_size" not in df.columns:
            df["field_size"] = df.groupby("race_id")["horse_id"].transform("count")

        # Draw percentile within race (lower draw may be advantageous on some tracks).
        df["draw_rank"] = df.groupby("race_id")["draw"].rank(method="first")
        df["draw_pct"] = (df["draw_rank"] - 1) / (df["field_size"] - 1).replace(0, 1)

        # Weight deltas vs race mean.
        race_weight_mean = df.groupby("race_id")["weight_carried"].transform("mean")
        df["weight_vs_mean"] = df["weight_carried"] - race_weight_mean

        # Distance buckets for non-linear distance effects.
        bins = [0, 1200, 1600, 2000, 2400, 3600, np.inf]
        labels = ["sprint", "mile", "mid", "classic", "stayer", "ext"]
        df["distance_bucket"] = pd.cut(df["distance_meters"], bins=bins, labels=labels, include_lowest=True)

        return df

    def fit(self, df: pd.DataFrame) -> "FeatureBuilder":
        self._validate_columns(df)
        df = self._add_derived(df)

        # Determine available numeric columns
        num_cols = list(self.numeric_cols_)
        if self.include_optional:
            num_cols += [c for c in self.optional_numeric_ if c in df.columns]
        # Derived numeric
        num_cols += ["draw_pct", "weight_vs_mean"]

        # Derived categorical
        cat_cols = list(self.categorical_cols_) + ["distance_bucket"]

        # Fit numeric scalers (mean/std for standardization)
        for c in num_cols:
            s = df[c].astype(float).replace([np.inf, -np.inf], np.nan).fillna(0.0)
            self._num_means[c] = float(s.mean())
            self._num_stds[c] = float(max(s.std(ddof=0), 1e-6))

        # Fit categorical top-K values
        for c in cat_cols:
            top_vals = (
                df[c]
                .astype(str)
                .value_counts(dropna=False)
                .head(self.cat_top_k)
                .index.astype(str)
                .tolist()
            )
            self._cat_top_values[c] = top_vals

        # Materialize feature columns (order matters for inference)
        feature_columns: List[str] = []
        feature_columns += [f"num__{c}" for c in num_cols]
        for c in cat_cols:
            for v in self._cat_top_values[c]:
                feature_columns.append(f"cat__{c}__{v}")
            feature_columns.append(f"cat__{c}____OTHER__")

        self.feature_columns_ = feature_columns
        return self

    def transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """Transform raw df into feature matrix.

        Returns
        - X: pd.DataFrame of features with columns self.feature_columns_
        - y: pd.Series of win labels (1 if finish_position == 1 else 0)
        - groups: pd.Series of group ids (race_id) for per-race softmax later
        """
        self._validate_columns(df)
        df = self._add_derived(df)

        # Target and groups
        y = (df["finish_position"].astype(float) == 1).astype(int)
        groups = df["race_id"].astype(str)

        # Select numeric columns
        num_cols = [c.replace("num__", "") for c in self.feature_columns_ if c.startswith("num__")]

        # Build numeric matrix
        num_feats = {}
        for c in num_cols:
            col = df[c].astype(float).replace([np.inf, -np.inf], np.nan).fillna(self._num_means.get(c, 0.0))
            col = (col - self._num_means.get(c, 0.0)) / self._num_stds.get(c, 1.0)
            num_feats[f"num__{c}"] = col

        # Build categorical one-hot with top-K + OTHER
        cat_cols = sorted({c.split("__")[1] for c in self.feature_columns_ if c.startswith("cat__")})
        cat_feats = {}
        for c in cat_cols:
            vals = df[c].astype(str)
            top_vals = self._cat_top_values.get(c, [])
            for v in top_vals:
                cat_feats[f"cat__{c}__{v}"] = (vals == v).astype(int)
            cat_feats[f"cat__{c}____OTHER__"] = (~vals.isin(top_vals)).astype(int)

        X = pd.DataFrame({**num_feats, **cat_feats})
        # Ensure consistent column order and presence
        for col in self.feature_columns_:
            if col not in X:
                X[col] = 0
        X = X[self.feature_columns_]
        return X, y, groups

