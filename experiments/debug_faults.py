"""Debug: faults + network impairments + determinism."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from simtwin.config import SimConfig
from simtwin.fleet.engine import FleetEngine


def run(seed=7, faults=True, network=True, n=40, dur=7200.0):
    cfg = SimConfig.default()
    cfg.experiment.seed = seed
    cfg.fleet.size = n
    cfg.simulation.duration_s = dur
    if faults:
        cfg.faults.mode = "poisson"
        cfg.faults.rate_per_hour = 4.0
    if network:
        cfg.network.loss_probability = 0.02
        cfg.network.duplicate_probability = 0.01
        cfg.network.mean_outage_interval_s = 900.0
        cfg.network.outage_duration_min_s = 20.0
        cfg.network.outage_duration_max_s = 120.0
        cfg.network.mean_broker_outage_interval_s = 3600.0
    cfg.validate()
    return FleetEngine(cfg).run()


a = run()
print("=== faults + network, n=40, 2 h ===")
for k in ("messages_generated", "messages_delivered", "messages_dropped",
         "message_delivery_ratio_pct", "duplicates", "queued_for_replay", "replayed",
         "dropped_loss", "dropped_stale", "dropped_broker", "dropped_queue_overflow",
         "transport_latency_ms_mean", "transport_latency_ms_max", "resynchronisations",
         "twin_staleness_area_s", "twin_offline_area_s", "max_concurrently_stale_twins",
         "mean_stale_twins", "sync_delay_ms_p99", "realtime_factor"):
    print("  %s: %s" % (k, a.metrics[k]))
print("  fault_summary:", a.fault_summary)
kinds: dict[str, int] = {}
for e in a.events:
    kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
print("  event kinds:", kinds)

b = run()
same = (a.telemetry == b.telemetry and a.events == b.events
        and a.metrics["messages_delivered"] == b.metrics["messages_delivered"])
print("=== determinism (same seed):", same)

c = run(seed=8)
print("=== determinism (different seed):", a.telemetry != c.telemetry)

d = run(faults=False, network=False)
print("=== baseline (no faults/network) delivery:",
      d.metrics["message_delivery_ratio_pct"], "faults:", d.fault_summary)

# Fault effect sanity: a heater-degradation fault must depress nozzle temperature.
e = run(faults=True, n=40, dur=7200.0)
hot = [t for t in e.telemetry if t["fault_code"] == "nozzle_heater_failure"
       and t["state"] == "PRINTING"]
base = [t for t in e.telemetry if t["fault_code"] is None and t["state"] == "PRINTING"]
if hot:
    mh = sum(t["nozzle_temperature_c"] for t in hot) / len(hot)
    mb = sum(t["nozzle_temperature_c"] for t in base) / len(base)
    ph = sum(t["power_w"] for t in hot) / len(hot)
    pb = sum(t["power_w"] for t in base) / len(base)
    print("=== heater_degradation: mean nozzle %.2f C vs baseline %.2f C" % (mh, mb))
    print("    mean power %.1f W vs baseline %.1f W  (n=%d faulted samples)" % (ph, pb, len(hot)))
else:
    print("=== no heater_degradation samples")
