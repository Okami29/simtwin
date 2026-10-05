"""Run-artifact writers: telemetry, events, twin snapshots, metadata.

Every writer is deterministic and self-describing: the run metadata records the
full resolved configuration, the seed, the package versions, and the host, so a
result can be traced back to the exact inputs that produced it.

Supported formats: CSV, JSONL, and Parquet (via PyArrow, with zstd compression).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

__all__ = ["RunWriter", "collect_environment"]


def collect_environment() -> dict[str, Any]:
    """Python / platform / package versions for the run metadata.

    Delegates to :func:`simtwin.utilities.environment.detect_environment`, the
    single source of truth for environment provenance in the package.
    """
    from ..utilities.environment import detect_environment

    return detect_environment()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
        return None
    return value


class RunWriter:
    """Writes the artifacts of one simulation run into ``output_dir/run_id``."""

    def __init__(self, output_dir: str | Path, run_id: str,
                 formats: Iterable[str] = ("parquet",), compress: str = "zstd"):
        self.output_dir = Path(output_dir)
        self.run_id = run_id
        self.formats = tuple(f.lower() for f in formats)
        self.compress = compress
        self.run_dir = self.output_dir / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

    # -- helpers --------------------------------------------------------------
    def _write(self, name: str, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Write ``records`` in every configured format; return a file manifest."""
        info: dict[str, Any] = {"rows": len(records), "files": {}}
        if not records:
            return info
        df = pd.DataFrame([{k: _json_safe(v) for k, v in r.items()} for r in records])
        files: dict[str, str] = {}
        for fmt in self.formats:
            if fmt == "csv":
                path = self.run_dir / f"{name}.csv"
                df.to_csv(path, index=False)
            elif fmt in ("jsonl", "json"):
                path = self.run_dir / f"{name}.jsonl"
                with open(path, "w") as fh:
                    for rec in records:
                        fh.write(json.dumps(_json_safe(rec), separators=(",", ":")) + "\n")
            elif fmt == "parquet":
                path = self.run_dir / f"{name}.parquet"
                df.to_parquet(path, engine="pyarrow", compression=self.compress, index=False)
            else:
                raise ValueError(f"unsupported output format: {fmt!r}")
            files[fmt] = str(path.relative_to(self.output_dir))
        info["files"] = files
        info["columns"] = list(df.columns)
        return info

    # -- public API ------------------------------------------------------------
    def write_telemetry(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._write("telemetry", records)

    def write_events(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._write("events", records)

    def write_twins(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._write("twin_states", records)

    def write_metadata(self, *, config: dict[str, Any], seed: int, metrics: dict[str, Any],
                       fault_summary: dict[str, int], manifest: dict[str, Any],
                       experiment: str = "", extra: dict[str, Any] | None = None) -> Path:
        meta = {
            "run_id": self.run_id,
            "experiment": experiment,
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "seed": seed,
            "config": _json_safe(config),
            "metrics": _json_safe(metrics),
            "faults_injected": _json_safe(fault_summary),
            "artifacts": _json_safe(manifest),
            "environment": collect_environment(),
        }
        if extra:
            meta.update(_json_safe(extra))
        path = self.run_dir / "metadata.json"
        with open(path, "w") as fh:
            json.dump(meta, fh, indent=2, sort_keys=True)
        return path

    def write_summary_row(self, row: dict[str, Any],
                          filename: str = "summary.csv") -> Path:
        """Append one row to a per-experiment summary table (one file per experiment)."""
        path = self.output_dir / filename
        df = pd.DataFrame([{k: _json_safe(v) for k, v in row.items()}])
        header = not path.exists()
        df.to_csv(path, mode="a", header=header, index=False)
        return path

