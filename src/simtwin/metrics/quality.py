"""Resource sampling and derived quality metrics.

``ResourceSampler`` measures the simulator's own CPU and resident memory while a
run is in progress, so the scalability study reports measured cost rather than
operation counts.  ``separability_score`` quantifies how well a fault's telemetry
signature separates from normal operation — the property that makes a synthetic
dataset useful for fault-detection research.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

try:  # pragma: no cover - psutil is a hard dependency of the experiments
    import psutil

    _HAVE_PSUTIL = True
except Exception:  # pragma: no cover
    _HAVE_PSUTIL = False


@dataclass
class ResourceSampler:
    """Samples RSS and CPU time of the simulator process at a fixed wall interval."""

    interval_s: float = 0.05
    rss_mb_samples: list[float] = field(default_factory=list)
    cpu_percent_samples: list[float] = field(default_factory=list)
    _proc: Any = None
    _last_sample: float = 0.0

    def __post_init__(self) -> None:
        self._proc = psutil.Process(os.getpid()) if _HAVE_PSUTIL else None
        if self._proc is not None:
            self._proc.cpu_percent(None)  # prime the counter
        self._last_sample = time.perf_counter()

    def sample(self, force: bool = False) -> None:
        """Record a sample if ``interval_s`` of wall time has elapsed."""
        if self._proc is None:
            return
        now = time.perf_counter()
        if not force and now - self._last_sample < self.interval_s:
            return
        self._last_sample = now
        self.rss_mb_samples.append(self._proc.memory_info().rss / (1024.0 * 1024.0))
        self.cpu_percent_samples.append(self._proc.cpu_percent(None))

    def summary(self) -> dict[str, float]:
        """Peak/mean RSS and CPU over the sampling window."""
        if self._proc is None or not self.rss_mb_samples:
            return {"peak_rss_mb": float("nan"), "mean_rss_mb": float("nan"),
                    "mean_cpu_percent": float("nan"), "peak_cpu_percent": float("nan"),
                    "psutil_available": float(_HAVE_PSUTIL)}
        rss = np.asarray(self.rss_mb_samples)
        cpu = np.asarray(self.cpu_percent_samples)
        return {
            "peak_rss_mb": float(rss.max()),
            "mean_rss_mb": float(rss.mean()),
            "peak_cpu_percent": float(cpu.max()),
            "mean_cpu_percent": float(cpu.mean()),
            "psutil_available": float(_HAVE_PSUTIL),
        }


def separability_score(normal: np.ndarray, faulted: np.ndarray) -> dict[str, float]:
    """Separability of two 1-D samples by feature, using Cohen's *d* and AUC.

    ``normal`` and ``faulted`` are ``(n_samples, n_features)`` arrays.  Returns the
    mean |d| and mean one-vs-one AUC across features, plus per-feature detail.
    AUC is computed in closed form from the rank statistic (Mann-Whitney U), which
    needs no scikit-learn import at run time.
    """
    normal = np.atleast_2d(np.asarray(normal, dtype=np.float64))
    faulted = np.atleast_2d(np.asarray(faulted, dtype=np.float64))
    if normal.shape[1] != faulted.shape[1]:
        raise ValueError("feature counts differ")
    per_feature: list[dict[str, float]] = []
    for j in range(normal.shape[1]):
        a, b = normal[:, j], faulted[:, j]
        pooled = np.sqrt(0.5 * (a.var(ddof=1) + b.var(ddof=1))) if a.size > 1 and b.size > 1 else 0.0
        d = float((b.mean() - a.mean()) / pooled) if pooled > 0 else float("nan")
        per_feature.append({"feature_index": j, "cohens_d": d, "auc": _auc(a, b)})
    ds = np.array([p["cohens_d"] for p in per_feature], dtype=np.float64)
    aucs = np.array([p["auc"] for p in per_feature], dtype=np.float64)
    return {
        "mean_abs_cohens_d": float(np.nanmean(np.abs(ds))),
        "min_abs_cohens_d": float(np.nanmin(np.abs(ds))) if ds.size else float("nan"),
        "mean_auc": float(np.nanmean(aucs)),
        "min_auc": float(np.nanmin(aucs)) if aucs.size else float("nan"),
        "n_normal": int(normal.shape[0]),
        "n_faulted": int(faulted.shape[0]),
        "per_feature": per_feature,
    }


def _auc(a: np.ndarray, b: np.ndarray) -> float:
    """Mann-Whitney AUC that a value drawn from ``b`` exceeds one from ``a``."""
    if a.size == 0 or b.size == 0:
        return float("nan")
    allv = np.concatenate([a, b])
    order = np.argsort(allv, kind="mergesort")
    ranks = np.empty(allv.size, dtype=np.float64)
    ranks[order] = np.arange(1, allv.size + 1, dtype=np.float64)
    # Average ranks of ties so the statistic is exact for discretised signals.
    values, inverse, counts = np.unique(allv, return_inverse=True, return_counts=True)
    sums = np.zeros(values.size, dtype=np.float64)
    np.add.at(sums, inverse, ranks)
    ranks = (sums / counts)[inverse]
    r_b = ranks[a.size:].sum()
    u = r_b - b.size * (b.size + 1) / 2.0
    return float(u / (a.size * b.size))
