"""Unit tests for SimTwin.

Run with ``pytest`` from the repository root.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from simtwin.config import SimConfig  # noqa: E402
from simtwin.communication.message import (TELEMETRY, Message, topic)  # noqa: E402
from simtwin.communication.transport import ConnectivityModel, InProcessTransport  # noqa: E402
from simtwin.faults.catalogue import FAULT_CATALOGUE  # noqa: E402
from simtwin.faults.injector import FaultInjector  # noqa: E402
from simtwin.fleet.engine import FleetEngine  # noqa: E402
from simtwin.printer.thermal import ThermalPlant  # noqa: E402
from simtwin.storage.writers import RunWriter  # noqa: E402
from simtwin.twin.registry import (STATUS_OFFLINE, STATUS_ONLINE, STATUS_STALE,  # noqa: E402
                                   TwinRegistry)
from simtwin.utilities.seeds import SeedPlan  # noqa: E402


# -- configuration -------------------------------------------------------------
def test_default_config_validates():
    cfg = SimConfig.default()
    assert cfg.fleet.size > 0
    assert cfg.n_steps > 0
    assert cfg.telemetry_period_steps >= 1


def test_config_rejects_unknown_section():
    with pytest.raises(KeyError):
        SimConfig.from_dict({"nonsense": {"a": 1}})


def test_config_rejects_unknown_key():
    with pytest.raises(KeyError):
        SimConfig.from_dict({"thermal": {"not_a_field": 1}})


def test_config_rejects_bad_telemetry_alignment():
    cfg = SimConfig.default()
    cfg.simulation.dt_s = 0.7
    cfg.simulation.telemetry_interval_ms = 1000.0
    with pytest.raises(ValueError):
        cfg.validate()


def test_config_yaml_round_trip(tmp_path):
    cfg = SimConfig.default()
    path = tmp_path / "cfg.yaml"
    path.write_text(__import__("yaml").safe_dump(cfg.to_dict()))
    other = SimConfig.from_yaml(path)
    assert other.to_dict() == cfg.to_dict()


def test_config_rejects_unknown_fault_name():
    cfg = SimConfig.default()
    cfg.faults.mode = "poisson"
    cfg.faults.rate_per_hour = 1.0
    cfg.faults.weights = {"not_a_real_fault": 1.0}
    with pytest.raises(ValueError):
        cfg.validate()


# -- seeding -------------------------------------------------------------------
def test_seed_plan_streams_are_independent():
    plan = SeedPlan(seed=42)
    a = plan.generator("thermal").random(8)
    b = plan.generator("network").random(8)
    assert not np.array_equal(a, b)


def test_seed_plan_is_reproducible():
    a = SeedPlan(seed=7).generator("faults").random(64)
    b = SeedPlan(seed=7).generator("faults").random(64)
    assert np.array_equal(a, b)


# -- thermal -------------------------------------------------------------------
def test_thermal_heat_up_reaches_setpoint():
    cfg = SimConfig.default()
    plant = ThermalPlant.from_config(cfg.thermal)
    n = 4
    state = {
        "nozzle_temp_c": np.full(n, cfg.thermal.ambient_temp_c),
        "bed_temp_c": np.full(n, cfg.thermal.ambient_temp_c),
        "chamber_temp_c": np.full(n, cfg.thermal.ambient_temp_c),
        "nozzle_integral": np.zeros(n), "bed_integral": np.zeros(n),
        "chamber_integral": np.zeros(n),
        "xi_nozzle": np.zeros(n), "xi_bed": np.zeros(n), "xi_chamber": np.zeros(n),
    }
    targets = {"nozzle_target_c": np.full(n, 210.0), "bed_target_c": np.full(n, 60.0),
               "chamber_target_c": np.full(n, cfg.thermal.ambient_temp_c)}
    rng = np.random.default_rng(0)
    for _ in range(600):
        plant.step(state=state, targets=targets, dt_s=1.0, rng=rng)
    assert state["nozzle_temp_c"].min() > 200.0
    assert state["bed_temp_c"].min() > 55.0
    assert state["nozzle_temp_c"].max() < 230.0  # no runaway


def test_thermal_cool_down_toward_ambient():
    cfg = SimConfig.default()
    plant = ThermalPlant.from_config(cfg.thermal)
    state = {
        "nozzle_temp_c": np.array([210.0]), "bed_temp_c": np.array([60.0]),
        "chamber_temp_c": np.array([40.0]),
        "nozzle_integral": np.zeros(1), "bed_integral": np.zeros(1),
        "chamber_integral": np.zeros(1),
        "xi_nozzle": np.zeros(1), "xi_bed": np.zeros(1), "xi_chamber": np.zeros(1),
    }
    targets = {"nozzle_target_c": np.zeros(1), "bed_target_c": np.zeros(1),
               "chamber_target_c": np.full(1, cfg.thermal.ambient_temp_c)}
    rng = np.random.default_rng(1)
    for _ in range(3000):
        plant.step(state=state, targets=targets, dt_s=1.0, rng=rng)
    assert state["nozzle_temp_c"][0] < cfg.thermal.ambient_temp_c + 2.0


def test_heater_failure_makes_temperature_sag():
    """The fault mechanism, not a scripted label, drives the observable signature."""
    cfg = SimConfig.default()
    plant = ThermalPlant.from_config(cfg.thermal)
    state = {"nozzle_temp_c": np.array([210.0]), "bed_temp_c": np.array([60.0]),
             "chamber_temp_c": np.array([40.0]),
             "nozzle_integral": np.zeros(1), "bed_integral": np.zeros(1),
             "chamber_integral": np.zeros(1),
             "xi_nozzle": np.zeros(1), "xi_bed": np.zeros(1), "xi_chamber": np.zeros(1)}
    targets = {"nozzle_target_c": np.full(1, 210.0), "bed_target_c": np.full(1, 60.0),
               "chamber_target_c": np.full(1, 40.0)}
    rng = np.random.default_rng(2)
    for _ in range(60):
        plant.step(state=state, targets=targets, dt_s=1.0, rng=rng,
                   nozzle_heater_efficiency=0.0)
    assert state["nozzle_temp_c"][0] < 205.0
    assert state["nozzle_duty"][0] == pytest.approx(1.0)  # controller saturates


# -- fault injection -----------------------------------------------------------
def test_fault_catalogue_is_consistent():
    families = {s.family for s in FAULT_CATALOGUE.values()}
    for name, spec in FAULT_CATALOGUE.items():
        assert spec.name == name
        assert spec.family in families
    assert {s.name for s in FAULT_CATALOGUE.values() if s.terminal}


def test_fault_injector_poisson_respects_schedule_bounds():
    cfg = SimConfig.default()
    cfg.faults.mode = "poisson"
    cfg.faults.rate_per_hour = 50.0
    rng = np.random.default_rng(3)
    inj = FaultInjector.build(20, cfg.faults, rng, 3600.0)
    assert inj.faults
    for f in inj.faults:
        assert 0 <= f.printer_index < 20
        assert 0.0 <= f.onset_s < 3600.0
        assert f.fault in FAULT_CATALOGUE


def test_fault_severity_ramps():
    cfg = SimConfig.default()
    cfg.faults.mode = "scheduled"
    cfg.faults.schedule = [{"printer_index": 0, "fault": "nozzle_heater_failure",
                            "onset_s": 100.0, "duration_s": 1000.0, "severity": 1.0}]
    inj = FaultInjector.build(2, cfg.faults, np.random.default_rng(0), 2000.0)
    assert inj.parameter_field(50.0)["nozzle_heater_efficiency"][0] == pytest.approx(1.0)
    mid = inj.parameter_field(100.0 + cfg.faults.ramp_s / 2)["nozzle_heater_efficiency"][0]
    assert 0.0 < mid < 1.0
    end = inj.parameter_field(1000.0)["nozzle_heater_efficiency"][0]
    assert end == pytest.approx(0.0)


def test_terminal_fault_flagged():
    cfg = SimConfig.default()
    cfg.faults.mode = "scheduled"
    cfg.faults.schedule = [{"printer_index": 1, "fault": "print_interruption",
                            "onset_s": 10.0, "duration_s": 0.0, "severity": 1.0}]
    inj = FaultInjector.build(3, cfg.faults, np.random.default_rng(0), 100.0)
    assert bool(inj.parameter_field(20.0)["terminal_fault"][1])
    assert not bool(inj.parameter_field(20.0)["terminal_fault"][0])


# -- transport -----------------------------------------------------------------
def _tele(idx: int, t: float, seq: int) -> Message:
    """A telemetry message with the full payload the twin write path expects."""
    return Message(seq=seq, topic="t", kind=TELEMETRY, printer_id=f"f-p{idx:06d}",
                   payload={"state": "PRINTING", "progress": 0.5,
                            "nozzle_temperature_c": 210.0, "bed_temperature_c": 60.0,
                            "chamber_temperature_c": 35.0, "power_w": 120.0,
                            "material_used_g": 10.0, "health_score": 0.99,
                            "fault_code": None, "job": {}},
                   t_generated=t)


def _transport(loss=0.0, dup=0.0, base_ms=10.0, outage_every=0.0, n=5, dur=1000.0,
              seed=11, queue=10000, max_age=600.0):
    cfg = SimConfig.default()
    cfg.network.loss_probability = loss
    cfg.network.duplicate_probability = dup
    cfg.network.base_latency_ms = base_ms
    cfg.network.jitter_std_ms = 1.0
    cfg.network.jitter_tail_sigma = 0.0
    cfg.network.mean_outage_interval_s = outage_every
    cfg.network.outage_duration_min_s = 50.0
    cfg.network.outage_duration_max_s = 50.0
    cfg.network.replay_queue_limit = queue
    cfg.network.max_message_age_s = max_age
    rng = np.random.default_rng(seed)
    conn = ConnectivityModel.build(cfg.network, n, rng, dur)
    return InProcessTransport(cfg.network, conn, rng, qos=1)


def test_transport_delivers_all_healthy_messages():
    tr = _transport()
    for k in range(1, 101):
        tr.publish(_tele(0, float(k), k))
        tr.step(float(k))
    tr.step(1000.0)  # drain the in-flight tail
    c = tr.counters()
    assert c["generated"] == 100
    assert c["delivered"] == 100
    assert c["dropped_loss"] == 0


def test_transport_applies_loss_rate():
    tr = _transport(loss=0.25)
    for k in range(1, 4001):
        tr.publish(_tele(k % 5, float(k), k))
        tr.step(float(k))
    c = tr.counters()
    ratio = c["dropped_loss"] / c["generated"]
    assert 0.20 < ratio < 0.30  # 4000 draws, binomial concentration


def test_transport_latency_is_bounded_and_positive():
    tr = _transport(base_ms=10.0)
    for k in range(1, 501):
        tr.publish(_tele(0, float(k), k))
        tr.step(float(k))
    tr.step(1000.0)  # drain
    lat = tr.latency_array()
    assert lat.size == 500
    assert lat.min() >= 10.0
    assert lat.max() < 10.0 + 8.0  # jitter std 1 ms, no lognormal tail


def test_transport_outage_queues_and_replays():
    tr = _transport(outage_every=100.0, n=1, dur=1000.0, queue=10000)
    delivered = 0
    for k in range(1, 1001):
        tr.publish(_tele(0, float(k), k))
        delivered += len(tr.step(float(k)))
    c = tr.counters()
    assert c["queued_for_replay"] > 0
    assert c["replayed"] > 0
    assert c["delivered"] == delivered


def test_transport_queue_overflow_is_counted():
    tr = _transport(outage_every=1.0, n=1, dur=1000.0, queue=5, max_age=1e9)
    for k in range(1, 501):
        tr.publish(_tele(0, float(k), k))
        tr.step(float(k))
    assert tr.counters()["dropped_queue_overflow"] > 0


def test_transport_stale_messages_are_dropped():
    tr = _transport(outage_every=1.0, n=1, dur=1000.0, queue=10000, max_age=10.0)
    for k in range(1, 501):
        tr.publish(_tele(0, float(k), k))
        tr.step(float(k))
    assert tr.counters()["dropped_stale"] > 0


def test_transport_produces_duplicates_at_configured_rate():
    tr = _transport(dup=0.2)
    for k in range(1, 2001):
        tr.publish(_tele(0, float(k), k))
        tr.step(float(k))
    c = tr.counters()
    assert 0.15 < c["duplicates"] / c["generated"] < 0.25


def test_topic_format():
    assert topic("simtwin", "fleet-01", "fleet-01-p000007", TELEMETRY) == \
        "simtwin/fleet-01/fleet-01-p000007/telemetry"


# -- twin registry -------------------------------------------------------------
def _registry(n=3, stale=5.0, offline=30.0):
    cfg = SimConfig.default()
    cfg.twin.staleness_threshold_s = stale
    cfg.twin.offline_threshold_s = offline
    ids = [f"f-p{i:06d}" for i in range(n)]
    return TwinRegistry("f", ids, cfg.twin), cfg.twin


def test_twin_starts_offline_and_becomes_online():
    reg, _ = _registry()
    assert reg.status_counts(0.0)[STATUS_OFFLINE] == 3
    msg = _tele(0, 1.0, 1)
    msg.t_delivered = 1.01
    reg.apply(msg)
    assert reg.status_counts(1.01)[STATUS_ONLINE] == 1


def test_twin_goes_stale_then_offline():
    reg, twin_cfg = _registry(stale=5.0, offline=30.0)
    msg = _tele(0, 1.0, 1)
    msg.t_delivered = 1.0
    reg.apply(msg)
    twin = reg.twins["f-p000000"]
    assert twin.status(10.0, twin_cfg) == STATUS_STALE
    assert twin.status(100.0, twin_cfg) == STATUS_OFFLINE
    # Staleness is measured against the last accepted update.
    assert twin.staleness_s(100.0) == pytest.approx(99.0)


def test_twin_resynchronisation_counted_on_replay():
    reg, _ = _registry()
    msg = _tele(0, 1.0, 1)
    msg.t_delivered = 60.0
    msg.replayed = True
    reg.apply(msg)
    assert reg.counters()["resynchronisations"] == 1
    assert reg.twins["f-p000000"].resync_count == 1


def test_twin_staleness_area_accumulates():
    reg, _ = _registry(n=1, stale=5.0, offline=30.0)
    msg = _tele(0, 1.0, 1)


# -- engine --------------------------------------------------------------------
def _engine_cfg(n=12, dur=1800.0, seed=5, faults=0.0, loss=0.0):
    cfg = SimConfig.default()
    cfg.experiment.seed = seed
    cfg.fleet.size = n
    cfg.simulation.duration_s = dur
    cfg.faults.mode = "poisson" if faults else "none"
    cfg.faults.rate_per_hour = faults
    cfg.network.loss_probability = loss
    cfg.validate()
    return cfg


def test_engine_is_deterministic():
    a = FleetEngine(_engine_cfg()).run()
    b = FleetEngine(_engine_cfg()).run()
    assert a.telemetry == b.telemetry
    assert a.events == b.events


def test_engine_seed_changes_output():
    a = FleetEngine(_engine_cfg(seed=1)).run()
    b = FleetEngine(_engine_cfg(seed=2)).run()
    assert a.telemetry != b.telemetry


def test_engine_telemetry_schema():
    art = FleetEngine(_engine_cfg()).run()
    required = {"timestamp_s", "printer_id", "state", "progress", "nozzle_temperature_c",
                "bed_temperature_c", "power_w", "material_used_g", "health_score",
                "fault_code", "connectivity"}
    assert art.telemetry
    assert required <= set(art.telemetry[0])


def test_engine_printers_reach_printing_and_complete_jobs():
    art = FleetEngine(_engine_cfg(n=8, dur=7200.0)).run()
    assert "PRINTING" in {t["state"] for t in art.telemetry}
    kinds = {e["kind"] for e in art.events}
    assert "print_start" in kinds
    assert "print_complete" in kinds


def test_engine_printing_nozzle_tracks_setpoint():
    art = FleetEngine(_engine_cfg(n=8, dur=7200.0)).run()
    temps = np.array([t["nozzle_temperature_c"] for t in art.telemetry
                      if t["state"] == "PRINTING"])
    assert temps.mean() == pytest.approx(210.0, abs=4.0)


def test_engine_heater_fault_depresses_temperature():
    cfg = _engine_cfg(n=30, dur=7200.0, faults=20.0)
    cfg.faults.weights = {"nozzle_heater_failure": 1.0}
    art = FleetEngine(cfg).run()
    hot = np.array([t["nozzle_temperature_c"] for t in art.telemetry
                    if t["fault_code"] == "nozzle_heater_failure"
                    and t["state"] == "PRINTING"])
    base = np.array([t["nozzle_temperature_c"] for t in art.telemetry
                     if t["fault_code"] is None and t["state"] == "PRINTING"])
    assert hot.size > 100
    assert hot.mean() < base.mean() - 10.0


def test_engine_terminal_fault_fails_the_job():
    cfg = _engine_cfg(n=10, dur=7200.0, faults=120.0)
    cfg.faults.weights = {"print_interruption": 1.0}
    cfg.fleet.initial_printing_fraction = 1.0
    art = FleetEngine(cfg).run()
    assert art.fault_summary.get("print_interruption", 0) > 0
    assert any(e["kind"] == "print_failed" for e in art.events)
    assert any(e["kind"] == "maintenance_start" for e in art.events)


def test_engine_loss_reduces_delivery():
    clean = FleetEngine(_engine_cfg(n=20, dur=3600.0)).run()
    lossy = FleetEngine(_engine_cfg(n=20, dur=3600.0, loss=0.3)).run()
    assert lossy.metrics["dropped_loss"] > 0
    assert (lossy.metrics["message_delivery_ratio_pct"]
            < clean.metrics["message_delivery_ratio_pct"])


def test_engine_reports_realtime_factor():
    art = FleetEngine(_engine_cfg(n=50, dur=3600.0)).run()
    assert art.metrics["realtime_factor"] > 100.0


# -- storage -------------------------------------------------------------------
def test_storage_round_trip_parquet_and_csv(tmp_path):
    import pandas as pd

    art = FleetEngine(_engine_cfg(n=4, dur=300.0)).run()
    w = RunWriter(tmp_path, "unit_run", formats=("parquet", "csv", "jsonl"))
    man = {"telemetry": w.write_telemetry(art.telemetry),
           "events": w.write_events(art.events)}
    w.write_metadata(config=art.config, seed=art.seed, metrics=art.metrics,
                     fault_summary=art.fault_summary, manifest=man, experiment="unit")
    df = pd.read_parquet(tmp_path / "unit_run" / "telemetry.parquet")
    assert len(df) == len(art.telemetry)
    assert df["nozzle_temperature_c"].notna().all()
    assert len(pd.read_csv(tmp_path / "unit_run" / "telemetry.csv")) == len(df)
    assert (tmp_path / "unit_run" / "metadata.json").exists()


# -- MQTT broker transport -----------------------------------------------------
# These tests require a broker on 127.0.0.1:1883 (e.g. `mosquitto -p 1883`).
# They are skipped automatically when no broker is listening, so the suite stays
# runnable on a machine without Mosquitto installed.
import socket as _socket


def _broker_available(host="127.0.0.1", port=1883) -> bool:
    try:
        with _socket.create_connection((host, port), 0.5):
            return True
    except OSError:
        return False


requires_broker = pytest.mark.skipif(
    not _broker_available(), reason="no MQTT broker on 127.0.0.1:1883")


def _mqtt_cfg(n=4, dur=60.0, seed=11, qos=1, loss=0.0):
    cfg = SimConfig.default()
    cfg.experiment.seed = seed
    cfg.fleet.size = n
    cfg.simulation.duration_s = dur
    cfg.simulation.dt_s = 0.05
    cfg.network.loss_probability = loss
    cfg.network.base_latency_ms = 0.0
    cfg.network.jitter_std_ms = 0.0
    cfg.network.jitter_tail_sigma = 0.0
    cfg.mqtt.enabled = True
    cfg.mqtt.qos = qos
    cfg.mqtt.drain_timeout_s = 5.0
    cfg.validate()
    return cfg


@requires_broker
def test_mqtt_transport_delivers_through_real_broker():
    from simtwin.communication.mqtt_transport import MqttTransport

    cfg = _mqtt_cfg(n=4, dur=60.0, qos=1)
    art = FleetEngine(cfg).run()
    tc = art.metrics
    assert tc["messages_generated"] > 0
    # QoS 1 over loopback to a local broker must deliver essentially everything.
    assert tc["message_delivery_ratio_pct"] > 99.0
    assert art.metrics["twin_staleness_p95_s"] < 2.0


@requires_broker
def test_mqtt_transport_matches_in_process_message_count():
    """The broker path generates the same telemetry volume as the in-process path."""
    cfg_broker = _mqtt_cfg(n=4, dur=60.0, qos=1)
    cfg_local = _mqtt_cfg(n=4, dur=60.0, qos=1)
    cfg_local.mqtt.enabled = False
    a = FleetEngine(cfg_broker).run()
    b = FleetEngine(cfg_local).run()
    assert len(a.telemetry) == len(b.telemetry)
    assert a.metrics["messages_generated"] == b.metrics["messages_generated"]


@requires_broker
def test_mqtt_transport_qos0_is_lossless_over_tcp():
    """A broker over TCP does not drop messages, at either QoS level.

    The configured ``loss_probability`` is an impairment the *in-process* model
    applies; it is not a property of the broker. Asserting the broker path is
    lossless pins that distinction down, so nobody reads the in-process loss
    numbers as broker measurements.
    """
    for qos in (0, 1):
        art = FleetEngine(_mqtt_cfg(n=4, dur=60.0, qos=qos, loss=0.5)).run()
        m = art.metrics
        assert m["messages_delivered"] == m["messages_generated"], (qos, m)
        assert m["message_delivery_ratio_pct"] == 100.0


@requires_broker
def test_mqtt_transport_qos0_adds_no_backpressure_vs_qos1():
    """QoS 1 blocks on PUBACK; QoS 0 does not, so its queue grows unbounded.

    This is the mechanism E7 reports: with no handshake to throttle on, a producer
    running far faster than real time fills the client outbox, and the twin
    observes a delivery latency (hence a staleness) orders of magnitude larger than
    under QoS 1.
    """
    q0 = FleetEngine(_mqtt_cfg(n=4, dur=60.0, qos=0)).run().metrics
    q1 = FleetEngine(_mqtt_cfg(n=4, dur=60.0, qos=1)).run().metrics
    assert q0["transport_latency_ms_mean"] > 10.0 * max(
        q1["transport_latency_ms_mean"], 1.0)
    assert q0["twin_staleness_p95_s"] > 5.0 * q1["twin_staleness_p95_s"]


@requires_broker
def test_mqtt_transport_counters_use_shared_names():
    """The broker transport reports the counter names every metric depends on."""
    from simtwin.communication.mqtt_transport import MqttTransport
    from simtwin.communication.transport import InProcessTransport

    cfg = _mqtt_cfg(n=2, dur=10.0, qos=1)
    conn = ConnectivityModel.build(cfg.network, 2, np.random.default_rng(0),
                                   cfg.simulation.duration_s)
    broker = MqttTransport(cfg.network, conn, np.random.default_rng(0), cfg.mqtt,
                           cfg.fleet.fleet_id, qos=1)
    local = InProcessTransport(cfg.network, conn, np.random.default_rng(0), qos=1)
    assert set(broker.counters()) == set(local.counters())
    broker.close()
