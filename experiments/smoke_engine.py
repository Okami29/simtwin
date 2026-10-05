"""Smoke test: build a fleet, run it, print the metrics it reports."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from simtwin.config import SimConfig
from simtwin.fleet.engine import FleetEngine

cfg = SimConfig.default()
print("n_steps", cfg.n_steps, "telemetry_period", cfg.telemetry_period_steps)
print("duration", cfg.simulation.duration_s, "dt", cfg.simulation.dt_s)
print("fleet", cfg.fleet.size, "fault rate/h", cfg.faults.rate_per_hour)

t0 = time.perf_counter()
eng = FleetEngine(cfg)
print("init %.3f s  n=%d" % (time.perf_counter() - t0, eng.n))

t0 = time.perf_counter()
art = eng.run()
print("run %.3f s" % (time.perf_counter() - t0))
for k, v in art.metrics.items():
    print("  %s: %s" % (k, v))
print("telemetry rows", len(art.telemetry), "events", len(art.events))
print("fault summary", art.fault_summary)
mid = art.telemetry[len(art.telemetry) // 2]
print("sample telemetry:", mid)
kinds: dict[str, int] = {}
for e in art.events:
    kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
print("event kinds:", kinds)
