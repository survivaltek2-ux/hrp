from __future__ import annotations

import math
from typing import Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss


class SoftmaxRaceModel:
    """Train a per-horse classifier and convert to per-race probabilities.

    - Uses LogisticRegression by default for stability and interpretability.
    - During inference, converts per-horse probabilities to race-consistent
      probabilities using a softmax across log-odds within each race group.
    """

    def __init__(self, *, C: float = 1.0, max_iter: int = 1000, n_jobs: int = 1) -> None:
        self.clf = LogisticRegression(
            C=C,
            max_iter=max_iter,
            n_jobs=n_jobs,
            solver="lbfgs",
        )

    @staticmethod
    def _safe_logit(p: np.ndarray) -> np.ndarray:
        eps = 1e-9
        p = np.clip(p, eps, 1 - eps)
        return np.log(p / (1 - p))

    @staticmethod
    def _race_softmax(groups: np.ndarray, proba: np.ndarray) -> np.ndarray:
        """Convert independent probabilities to race-softmaxed probabilities.

        We treat the per-horse probability as if it came from a latent score
        (log-odds), then apply a softmax within each race group.
        """
        logits = SoftmaxRaceModel._safe_logit(proba)
        out = np.zeros_like(proba)
        unique_groups = np.unique(groups)
        for g in unique_groups:
            mask = groups == g
            z = logits[mask]
            # subtract max for stability
            z = z - z.max()
            ez = np.exp(z)
            out[mask] = ez / ez.sum()
        return out

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SoftmaxRaceModel":
        self.clf.fit(X, y)
        return self

    def predict_proba(self, X: np.ndarray, groups: np.ndarray) -> np.ndarray:
        p_ind = self.clf.predict_proba(X)[:, 1]
        return self._race_softmax(groups, p_ind)

    def evaluate_log_loss(self, X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> float:
        """Compute per-race softmaxed log loss against win labels.

        Note: In each race, only one runner has y=1; softmax ensures probabilities sum to 1.
        """
        p = self.predict_proba(X, groups)
        # log_loss expects 1D y and probs for class 1
        return float(log_loss(y, p, labels=[0, 1]))

