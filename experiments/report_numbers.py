"""Print the exact numbers the manuscript quotes, straight from results/."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"


def show(name: str, cols: list[str], filt=None) -> None:
    import pandas as pd
    df = pd.read_csv(R / name / "summary.csv")
    if filt is not None:
        df = df[filt(df)]
    print(f"\n===== {name} =====")
    print(df[[c for c in cols if c in df.columns]].to_string(index=False))


show("E1_scalability", ["fleet_size", "wall_clock_s", "realtime_factor",
                        "device_steps_per_second", "peak_rss_mb", "messages_generated",
                        "message_delivery_ratio_pct"])
show("E2_telemetry_rate", ["telemetry_interval_ms", "messages_generated",
                           "telemetry_throughput_msg_s", "wall_clock_s", "peak_rss_mb"])
show("E3_network_impairment", ["scenario", "loss_probability", "mean_outage_interval_s",
                               "message_delivery_ratio_pct", "transport_latency_ms_mean",
                               "transport_latency_ms_max", "twin_staleness_p95_s",
                               "twin_offline_area_s", "resynchronisations"])
show("E5_outage_recovery", ["link_down_events", "link_up_events", "resynchronisations",
                            "twin_offline_area_s", "twin_staleness_p50_s",
                            "twin_staleness_max_s", "message_delivery_ratio_pct",
                            "sync_delay_ms_mean", "sync_delay_ms_max"])

print("\n===== E4 fault separability (max |d| per fault) =====")
import pandas as pd  # noqa: E402
df = pd.read_csv(R / "E4_fault_injection" / "separability.csv")
rows = []
for _, r in df.iterrows():
    det = json.loads(r["detail"])
    k, v = max(det.items(), key=lambda kv: abs(kv[1]))
    rows.append({"fault": r["fault"], "family": r["family"], "n": int(r["n_samples"]),
                 "peak_feature": k, "max_d": round(v, 2), "mean_auc": round(r["mean_auc"], 3)})
print(pd.DataFrame(rows).sort_values("max_d", key=lambda s: -s.abs()).to_string(index=False))

print("\n===== E4 run-level =====")
e4 = pd.read_csv(R / "E4_fault_injection" / "summary.csv")
print(e4.to_string(index=False))

print("\n===== E6 =====")
print(pd.read_csv(R / "E6_reproducibility" / "summary.csv").to_string(index=False))

meta = json.loads((R / "E1_scalability" / "n01000" / "metadata.json").read_text())
print("\n===== environment (E1 n=1000) =====")
env = meta.get("environment", {})
for k, v in env.items():
    print(f"  {k}: {v}")
print("  keys:", list(meta.keys()))