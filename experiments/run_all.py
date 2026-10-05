"""Experiment suite for the SimTwin study.

Six experiments, each writing a ``summary.csv`` under ``results/<name>/`` plus
full artifacts for representative runs:

E1 scalability      wall-clock cost, throughput and memory vs fleet size.
E2 telemetry_rate   message volume and twin freshness vs sampling period.
E3 network_impair   delivery, latency and twin synchronisation vs loss/outage.
E4 fault_injection  emergent telemetry signatures and fault separability.
E5 outage_recovery  twin staleness trajectory through a disconnection episode.
E6 reproducibility  bit-identical output for a fixed seed.

Usage
-----
    python experiments/run_all.py                # all experiments
    python experiments/run_all.py E1 E4          # a subset
    python experiments/run_all.py --quick        # reduced sizes (smoke run)
"""
from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from simtwin.config import SimConfig  # noqa: E402
from simtwin.fleet.engine import FleetEngine  # noqa: E402
from simtwin.metrics.quality import ResourceSampler, separability_score  # noqa: E402
from simtwin.storage.writers import RunWriter  # noqa: E402

RESULTS = ROOT / "results"

#: Telemetry features used for the fault-separability analysis.
SEPARABILITY_FEATURES: list[str] = [
    "nozzle_temperature_c",
    "bed_temperature_c",
    "chamber_temperature_c",
    "power_w",
    "print_speed_mm_s",
    "material_used_g",
    "health_score",
]


def _base(**overrides: Any) -> SimConfig:
    """Baseline configuration with section-path overrides, e.g. ``fleet__size=100``."""
    cfg = SimConfig.default()
    for key, value in overrides.items():
        section, field = key.split("__", 1)
        setattr(getattr(cfg, section), field, value)
    cfg.validate()
    return cfg


def _run(cfg: SimConfig, *, sample_resources: bool = True) -> dict[str, Any]:
    """Run one simulation, sampling resources, and return metrics + artifacts."""
    sampler = ResourceSampler()
    engine = FleetEngine(cfg)
    peak_rss_start = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t0 = time.perf_counter()
    steps = cfg.n_steps
    for k in range(steps):
        engine.step_index = k
        engine.t = (k + 1) * engine.dt
        engine._step()
        if sample_resources and (k % 16 == 0):
            sampler.sample()
    wall = time.perf_counter() - t0
    engine.step_index = steps
    art = engine._finalise(wall)
    metrics = dict(art.metrics)
    metrics.update(sampler.summary())
    # ru_maxrss is bytes on Linux, kilobytes on macOS.
    scale = 1024.0 * 1024.0 if sys.platform == "linux" else 1024.0
    metrics["peak_rss_process_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / scale
    return {"metrics": metrics, "artifacts": art}


def _write(experiment: str, run_id: str, res: dict[str, Any], cfg: SimConfig,
          *, telemetry: bool = True, events: bool = True, twins: bool = False) -> dict[str, Any]:
    """Persist one run and return its summary row."""
    art = res["artifacts"]
    metrics = res["metrics"]
    writer = RunWriter(RESULTS / experiment, run_id, formats=("parquet", "csv"))
    manifest = {}
    if telemetry:
        manifest["telemetry"] = writer.write_telemetry(art.telemetry)
    if events:
        manifest["events"] = writer.write_events(art.events)
    if twins:
        manifest["twin_states"] = writer.write_twins(art.twin_snapshots)
    writer.write_metadata(config=cfg.to_dict(), seed=cfg.experiment.seed, metrics=metrics,
                          fault_summary=art.fault_summary, manifest=manifest,
                          experiment=experiment)
    return metrics



def _summary_row(experiment: str, metrics: dict[str, Any], **extra: Any) -> dict[str, Any]:
    """Build one summary row with a *fixed* column set.

    Every key is emitted even when the metric is absent, because summaries are
    appended row-by-row: a row that carries extra keys writes more fields than the
    header, and the resulting CSV is ragged and unparseable.  Metrics that a given
    run genuinely does not produce (e.g. twin-staleness percentiles in a run where
    no twin ever went stale) become empty cells, which pandas reads back as NaN.
    """
    keep = ("fleet_size", "simulated_duration_s", "wall_clock_s", "realtime_factor",
            "device_steps_per_second", "telemetry_throughput_msg_s", "peak_rss_mb",
            "mean_rss_mb", "peak_cpu_percent", "messages_generated", "messages_delivered",
            "message_delivery_ratio_pct", "transport_latency_ms_mean",
            "transport_latency_ms_max", "twin_staleness_area_s", "twin_offline_area_s",
            "twin_staleness_p50_s", "twin_staleness_p95_s", "twin_staleness_max_s",
            "mean_stale_twins", "mean_offline_twins", "resynchronisations",
            "sync_delay_ms_mean", "sync_delay_ms_p95", "sync_delay_ms_p99")
    row = {"experiment": experiment}
    row.update({k: metrics.get(k, "") for k in keep})
    row.update(extra)
    return row


def _append_summary(experiment: str, row: dict[str, Any]) -> None:
    """Append one row to ``results/<experiment>/summary.csv``.

    Rows written after the header are reindexed onto the header's columns, so a
    row carrying an unexpected key fails loudly here rather than silently
    producing a ragged file.
    """
    import pandas as pd

    path = RESULTS / experiment / "summary.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        cols = pd.read_csv(path, nrows=0).columns.tolist()
        missing = set(row) - set(cols)
        if missing:
            raise KeyError(
                f"{experiment}: summary row introduces columns absent from the "
                f"header of {path}: {sorted(missing)}. Delete the file and re-run.")
        row = {c: row.get(c, "") for c in cols}
    pd.DataFrame([row]).to_csv(path, mode="a", header=not path.exists(), index=False)


# -- E1: scalability -----------------------------------------------------------
def e1_scalability(quick: bool) -> None:
    sizes = [1, 10, 50, 100, 250, 500, 1000] if not quick else [1, 10, 100, 500]
    print(f"[E1] scalability: fleet sizes {sizes}")
    for n in sizes:
        cfg = _base(experiment__seed=101, fleet__size=n, simulation__duration_s=3600.0)
        res = _run(cfg)
        row = _summary_row("E1_scalability", res["metrics"], seed=cfg.experiment.seed)
        _write("E1_scalability", f"n{n:05d}", res, cfg, telemetry=(n <= 100), events=False)
        _append_summary("E1_scalability", row)
        print(f"  n={n:5d}  wall={row['wall_clock_s']:7.2f}s  "
              f"RTF={row['realtime_factor']:9.0f}x  "
              f"RSS={row['peak_rss_mb']:7.1f}MB  "
              f"thr={row['telemetry_throughput_msg_s']:9.0f} msg/s")


# -- E2: telemetry frequency ---------------------------------------------------
def e2_telemetry_rate(quick: bool) -> None:
    intervals_ms = [250.0, 500.0, 1000.0, 5000.0, 10000.0, 30000.0, 60000.0]
    if quick:
        intervals_ms = [500.0, 1000.0, 10000.0, 60000.0]
    # Sub-second telemetry needs a finer physics step than the 1 s baseline;
    # dt = 0.05 s makes every interval in the sweep an integer multiple of it.
    print(f"[E2] telemetry frequency: {intervals_ms} ms at n=100, dt=0.05 s, 30 min")
    for ms in intervals_ms:
        cfg = _base(experiment__seed=202, fleet__size=100, simulation__duration_s=1800.0,
                    simulation__dt_s=0.05, simulation__telemetry_interval_ms=ms)
        res = _run(cfg)
        row = _summary_row("E2_telemetry_rate", res["metrics"],
                           telemetry_interval_ms=ms, seed=cfg.experiment.seed)
        _write("E2_telemetry_rate", f"int{int(ms):06d}", res, cfg,
               telemetry=(ms >= 10000.0), events=False)
        _append_summary("E2_telemetry_rate", row)
        print(f"  {ms:8.0f} ms  gen={row['messages_generated']:9d}  "
              f"thr={row['telemetry_throughput_msg_s']:9.0f} msg/s  "
              f"wall={row['wall_clock_s']:6.2f}s")


# -- E3: network impairment ----------------------------------------------------
def e3_network_impairment(quick: bool) -> None:
    print("[E3] network impairment: loss sweep and outage sweep at n=200")
    for loss in ([0.0, 0.01, 0.05, 0.10, 0.20, 0.30] if not quick
                else [0.0, 0.05, 0.20]):
        cfg = _base(experiment__seed=303, fleet__size=200, simulation__duration_s=3600.0,
                    network__loss_probability=loss)
        res = _run(cfg)
        row = _summary_row("E3_network_impairment", res["metrics"],
                           scenario="loss", loss_probability=loss,
                           mean_outage_interval_s=0.0, seed=cfg.experiment.seed)
        _write("E3_network_impairment", f"loss{int(loss * 100):03d}", res, cfg, events=False)
        _append_summary("E3_network_impairment", row)
        print(f"  loss={loss:5.2f}  delivery={row['message_delivery_ratio_pct']:6.2f}%  "
              f"stale_area={row['twin_staleness_area_s']:9.1f}s  "
              f"resync={row['resynchronisations']:6d}")

    for interval in ([0.0, 1800.0, 900.0, 300.0, 120.0] if not quick else [0.0, 900.0, 300.0]):
        cfg = _base(experiment__seed=313, fleet__size=200, simulation__duration_s=3600.0,
                    network__mean_outage_interval_s=interval,
                    network__outage_duration_min_s=30.0,
                    network__outage_duration_max_s=180.0)
        res = _run(cfg)
        row = _summary_row("E3_network_impairment", res["metrics"],
                           scenario="outage", loss_probability=0.0,
                           mean_outage_interval_s=interval, seed=cfg.experiment.seed)
        _write("E3_network_impairment", f"out{int(interval):05d}", res, cfg, events=False)
        _append_summary("E3_network_impairment", row)
        print(f"  outage_every={interval:7.0f}s  "
              f"delivery={row['message_delivery_ratio_pct']:6.2f}%  "
              f"offline_area={row['twin_offline_area_s']:9.1f}s  "
              f"resync={row['resynchronisations']:6d}")



# -- E4: fault injection and separability --------------------------------------
def e4_fault_injection(quick: bool) -> None:
    import pandas as pd

    from simtwin.faults.catalogue import FAULT_CATALOGUE

    n = 60 if not quick else 30
    dur = 14400.0
    print(f"[E4] fault injection: n={n}, {dur / 3600:.0f} h, all catalogue faults")
    cfg = _base(experiment__seed=404, fleet__size=n, simulation__duration_s=dur,
                faults__mode="poisson", faults__rate_per_hour=6.0)
    res = _run(cfg)
    art = res["artifacts"]
    row = _summary_row("E4_fault_injection", res["metrics"], scenario="faulted",
                       seed=cfg.experiment.seed)
    _write("E4_fault_injection", "faulted", res, cfg)
    _append_summary("E4_fault_injection", row)
    print(f"  faults injected: {sum(art.fault_summary.values())} "
          f"across {len(art.fault_summary)} types")

    ctrl = _base(experiment__seed=405, fleet__size=n, simulation__duration_s=dur,
                 faults__mode="none")
    res_c = _run(ctrl)
    row_c = _summary_row("E4_fault_injection", res_c["metrics"], scenario="baseline",
                         seed=ctrl.experiment.seed)
    _write("E4_fault_injection", "baseline", res_c, ctrl, events=False)
    _append_summary("E4_fault_injection", row_c)

    # Separability: per fault type, faulted telemetry vs healthy printing telemetry.
    df = pd.DataFrame(art.telemetry)
    base = pd.DataFrame(res_c["artifacts"].telemetry)
    healthy = base[base["state"] == "PRINTING"]
    rows = []
    for fault in sorted(art.fault_summary):
        sub = df[(df["fault_code"] == fault) & (df["state"] == "PRINTING")]
        if len(sub) < 30:
            continue
        score = separability_score(
            healthy[SEPARABILITY_FEATURES].to_numpy(dtype=np.float64),
            sub[SEPARABILITY_FEATURES].to_numpy(dtype=np.float64))
        detail = {name: round(f["cohens_d"], 3)
                  for f, name in zip(score["per_feature"], SEPARABILITY_FEATURES)}
        rows.append({"fault": fault,
                     "family": FAULT_CATALOGUE[fault].family,
                     "n_samples": score["n_faulted"],
                     "mean_abs_cohens_d": round(score["mean_abs_cohens_d"], 4),
                     "mean_auc": round(score["mean_auc"], 4),
                     "min_auc": round(score["min_auc"], 4),
                     "detail": json.dumps(detail)})
        print(f"  {fault:24s} |d|={score['mean_abs_cohens_d']:6.2f}  "
              f"AUC={score['mean_auc']:5.3f}  n={score['n_faulted']}")
    out = RESULTS / "E4_fault_injection"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "separability.csv", index=False)


# -- E5: outage and recovery ---------------------------------------------------
def e5_outage_recovery(quick: bool) -> None:
    print("[E5] outage and recovery: sustained disconnection episodes")
    cfg = _base(experiment__seed=505, fleet__size=50, simulation__duration_s=3600.0,
                network__mean_outage_interval_s=600.0,
                network__outage_duration_min_s=120.0,
                network__outage_duration_max_s=300.0,
                twin__staleness_threshold_s=5.0, twin__offline_threshold_s=30.0)
    res = _run(cfg)
    art = res["artifacts"]
    row = _summary_row("E5_outage_recovery", res["metrics"], seed=cfg.experiment.seed)
    _write("E5_outage_recovery", "episode", res, cfg)
    _append_summary("E5_outage_recovery", row)
    print(f"  link_down={sum(1 for e in art.events if e['kind'] == 'link_down')}  "
          f"link_up={sum(1 for e in art.events if e['kind'] == 'link_up')}  "
          f"resync={row['resynchronisations']}  "
          f"offline_area={row['twin_offline_area_s']:.0f}s")


# -- E6: reproducibility -------------------------------------------------------
def e6_reproducibility(quick: bool) -> None:
    print("[E6] reproducibility: identical seeds vs independent seeds")
    import hashlib

    import pandas as pd

    def digest(seed: int) -> str:
        cfg = _base(experiment__seed=seed, fleet__size=40, simulation__duration_s=3600.0,
                    faults__mode="poisson", faults__rate_per_hour=5.0,
                    network__loss_probability=0.05,
                    network__mean_outage_interval_s=900.0)
        art = FleetEngine(cfg).run().telemetry
        blob = json.dumps(art, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(blob).hexdigest()

    a1, a2 = digest(2027), digest(2027)
    b1 = digest(2028)
    rows = [{"trial": "seed=2027 run1", "sha256": a1},
            {"trial": "seed=2027 run2", "sha256": a2},
            {"trial": "seed=2028 run1", "sha256": b1},
            {"trial": "same_seed_identical", "sha256": str(a1 == a2)},
            {"trial": "different_seed_differs", "sha256": str(a1 != b1)}]
    out = RESULTS / "E6_reproducibility"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "summary.csv", index=False)
    print(f"  same seed identical: {a1 == a2}")
    print(f"  different seed differs: {a1 != b1}")
def e7_broker_fidelity(quick: bool) -> None:
    """E7: does the deterministic transport correspond to a real broker?

    The in-process transport is an *impairment model*; E7 checks that the same
    message objects, topics and QoS semantics behave coherently when they really
    traverse an MQTT broker.  Skipped (with a summary row saying so) when no broker
    is listening, so the suite stays runnable on a machine without Mosquitto.
    """
    import socket

    import pandas as pd

    host, port = "127.0.0.1", 1883
    try:
        with socket.create_connection((host, port), 0.5):
            pass
    except OSError:
        out = RESULTS / "E7_broker_fidelity"
        out.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([{"trial": "skipped",
                       "detail": f"no MQTT broker on {host}:{port}"}]).to_csv(
            out / "summary.csv", index=False)
        print("[E7] skipped: no MQTT broker on 127.0.0.1:1883")
        return

    print("[E7] broker fidelity: in-process transport vs Mosquitto round trip")
    n = 20 if not quick else 8
    dur = 120.0
    rows: list[dict[str, Any]] = []
    for enabled, label in ((True, "broker"), (False, "in-process")):
        for qos in (0, 1):
            for loss in (0.0, 0.3):
                cfg = _base(experiment__seed=4242, fleet__size=n,
                            simulation__duration_s=dur, simulation__dt_s=0.05,
                            network__loss_probability=loss,
                            network__base_latency_ms=0.0,
                            network__jitter_std_ms=0.0,
                            network__jitter_tail_sigma=0.0,
                            mqtt__enabled=enabled, mqtt__qos=qos,
                            mqtt__drain_timeout_s=20.0)
                res = _run(cfg, sample_resources=False)
                m = res["metrics"]
                rows.append({
                    "transport": label, "qos": qos, "configured_loss": loss,
                    "generated": m["messages_generated"],
                    "delivered": m["messages_delivered"],
                    "delivery_pct": round(m["message_delivery_ratio_pct"], 2),
                    "latency_ms_mean": round(m["transport_latency_ms_mean"], 1),
                    "latency_ms_max": round(m["transport_latency_ms_max"], 1),
                    "staleness_p95_s": round(m["twin_staleness_p95_s"], 3),
                    "staleness_max_s": round(m["twin_staleness_max_s"], 3),
                    "realtime_factor": round(m["realtime_factor"], 1),
                })
                print(f"  {label:11s} qos{qos} loss={loss:<4}  "
                      f"delivery={rows[-1]['delivery_pct']:6.2f}%  "
                      f"lat_mean={rows[-1]['latency_ms_mean']:9.1f}ms  "
                      f"stale_p95={rows[-1]['staleness_p95_s']:7.3f}s")
    out = RESULTS / "E7_broker_fidelity"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "summary.csv", index=False)
    print(f"  wrote {out / 'summary.csv'}")




EXPERIMENTS: dict[str, Callable[[bool], None]] = {
    "E1": e1_scalability,
    "E2": e2_telemetry_rate,
    "E3": e3_network_impairment,
    "E4": e4_fault_injection,
    "E5": e5_outage_recovery,
    "E6": e6_reproducibility,
    "E7": e7_broker_fidelity,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SimTwin experiment suite")
    parser.add_argument("experiments", nargs="*", default=[],
                        help=f"subset of {', '.join(EXPERIMENTS)} (default: all)")
    parser.add_argument("--quick", action="store_true", help="reduced sizes for a smoke run")
    args = parser.parse_args(argv)
    chosen = [k.upper() for k in args.experiments] or list(EXPERIMENTS)
    t0 = time.perf_counter()
    failures: list[str] = []
    for key in chosen:
        if key not in EXPERIMENTS:
            parser.error(f"unknown experiment {key!r}; choose from {', '.join(EXPERIMENTS)}")
        try:
            EXPERIMENTS[key](args.quick)
        except Exception as exc:  # noqa: BLE001 - keep the suite running
            failures.append(key)
            print(f"[{key}] FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
    print(f"[done] {len(chosen) - len(failures)}/{len(chosen)} experiment(s) in "
          f"{time.perf_counter() - t0:.1f}s -> {RESULTS}"
          + (f"  (failed: {', '.join(failures)})" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())