"""The vectorised fleet simulation engine.

One :class:`FleetEngine` owns ``n`` virtual printers as parallel NumPy state
arrays, a fault injector, a transport, and a twin registry.  :meth:`FleetEngine.run`
advances a discrete virtual clock in steps of ``dt_s``; per step it

1. activates fault onsets that have come due and builds the fault parameter field;
2. advances the job/state machine of every device (vectorised);
3. advances the thermal plant with the fault-modified parameters;
4. evaluates power and material integration from the same duties and speeds;
5. accumulates wear and applies health-driven maintenance transitions;
6. on telemetry ticks, builds one telemetry record per device and publishes it;
7. steps the transport, applies delivered messages to the twin registry, and
   samples twin staleness accounting.

Everything the engine writes to the outside world goes through the transport, so
the twin side of the system sees exactly what a real IIoT platform would see.

Design notes
------------
* State lives in a dict of NumPy arrays (``engine.state``), not in per-printer
  objects: a 10 000-printer fleet is ~2 MB of state and one timestep is a fixed
  number of vectorised operations, which is what makes the scalability results
  reported in the manuscript possible.
* The engine is a *virtual clock*: it advances simulated time, not wall-clock time.
  Real-time factor (simulated seconds per wall second) is reported as a metric.
* Determinism: all randomness flows from ``SeedPlan``-spawned streams, so the same
  config and seed produce identical telemetry.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..config import SimConfig
from ..printer.states import PrinterState, STATE_NAMES
from ..printer.thermal import ThermalPlant
from ..printer.process import JobGenerator, MaterialModel, PowerModel
from ..faults.injector import FaultInjector
from ..communication.message import (ALERTS, HEALTH, LWT, STATE, TELEMETRY, Message, topic)
from ..communication.transport import ConnectivityModel, InProcessTransport
from ..communication.mqtt_transport import build_transport
from ..twin.registry import TwinRegistry
from ..utilities.seeds import SeedPlan

OFF = int(PrinterState.OFFLINE)
IDLE = int(PrinterState.IDLE)
PRE = int(PrinterState.PREHEATING)
PRINT = int(PrinterState.PRINTING)
PAUSE = int(PrinterState.PAUSED)
DONE = int(PrinterState.COMPLETED)
FAIL = int(PrinterState.FAILED)
MAINT = int(PrinterState.MAINTENANCE)


@dataclass
class RunArtifacts:
    """Everything a run produced, in memory (the experiments consume this)."""

    config: dict[str, Any]
    seed: int
    telemetry: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    twin_snapshots: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    fault_summary: dict[str, int] = field(default_factory=dict)


class FleetEngine:
    """Vectorised multi-printer simulation engine."""

    def __init__(self, cfg: SimConfig, *, collect_telemetry: bool = True,
                 collect_events: bool = True, transport=None):
        self.cfg = cfg
        self.collect_telemetry = collect_telemetry
        self.collect_events = collect_events
        self.seed_plan = SeedPlan(seed=cfg.experiment.seed)
        self.rng_thermal = self.seed_plan.generator("thermal")
        self.rng_jobs = self.seed_plan.generator("jobs")
        self.rng_faults = self.seed_plan.generator("faults")
        self.rng_network = self.seed_plan.generator("network")
        self.rng_sensor = self.seed_plan.generator("sensor")
        self.rng_process = self.seed_plan.generator("process")

        n = cfg.fleet.size
        self.n = n
        self.dt = cfg.simulation.dt_s
        self.t = 0.0
        self.step_index = 0
        self.telemetry_period = cfg.telemetry_period_steps
        self.fleet_id = cfg.fleet.fleet_id
        self.prefix = cfg.mqtt.topic_prefix

        self.thermal = ThermalPlant.from_config(cfg.thermal)
        self.power_model = PowerModel.from_config(cfg.power, cfg.material)
        self.material = MaterialModel.from_config(cfg.material)
        self.jobs = JobGenerator.from_config(cfg.jobs)

        self.state: dict[str, Any] = {}
        self._init_state()

        self.injector = FaultInjector.build(n, cfg.faults, self.rng_faults,
                                           cfg.simulation.duration_s)
        self.connectivity = ConnectivityModel.build(cfg.network, n, self.rng_network,
                                                   cfg.simulation.duration_s)
        self.transport = transport or build_transport(
            cfg, self.connectivity, self.rng_network)
        self.printer_ids = [f"{self.fleet_id}-p{i:06d}" for i in range(n)]
        self.registry = TwinRegistry(self.fleet_id, self.printer_ids, cfg.twin)

        self._events: list[dict[str, Any]] = []
        self._telemetry: list[dict[str, Any]] = []
        self._twin_snapshots: list[dict[str, Any]] = []
        self._msg_seq = 0
        self._job_counter = n
        self._wall_publish_s = 0.0
        self._wall_transport_s = 0.0
        self._field: dict[str, np.ndarray] = {}

    # -- main loop ------------------------------------------------------------
    def _step(self) -> None:
        """Advance every subsystem by one physics/communication step."""
        self._step_state_machine()
        self._step_thermal()
        self._step_power_material()
        self._step_health()
        self._step_publish()
        self._step_transport()

    # -- initialisation -------------------------------------------------------
    def _init_state(self) -> None:
        cfg = self.cfg
        n = self.n
        rng = self.rng_process
        ambient = cfg.thermal.ambient_temp_c
        s: dict[str, Any] = {
            "state": np.zeros(n, dtype=np.int8),
            "nozzle_temp_c": np.full(n, ambient),
            "bed_temp_c": np.full(n, ambient),
            "chamber_temp_c": np.full(n, ambient),
            "nozzle_target_c": np.zeros(n),
            "bed_target_c": np.zeros(n),
            "chamber_target_c": np.full(n, ambient),
            "nozzle_duty": np.zeros(n),
            "bed_duty": np.zeros(n),
            "chamber_duty": np.zeros(n),
            "nozzle_integral": np.zeros(n),
            "bed_integral": np.zeros(n),
            "chamber_integral": np.zeros(n),
            "xi_nozzle": np.zeros(n),
            "xi_bed": np.zeros(n),
            "xi_chamber": np.zeros(n),
            "power_w": np.full(n, cfg.power.electronics_standby_w),
            "energy_j": np.zeros(n),
            "material_used_g": np.zeros(n),
            "health": np.ones(n),
            "jobs_completed": np.zeros(n, dtype=np.int64),
            "jobs_failed": np.zeros(n, dtype=np.int64),
            "idle_until": np.zeros(n),
            "maint_until": np.zeros(n),
            "preheat_started": np.zeros(n),
            "prev_connectivity": np.ones(n, dtype=np.int8),
        }
        s.update(self.jobs.sample(n, rng, first_job_index=0))
        # A fraction of the fleet starts mid-job so fleet-level utilisation is
        # meaningful from the first sample rather than synchronised.
        printing = rng.random(n) < cfg.fleet.initial_printing_fraction
        s["state"][printing] = PRE
        s["preheat_started"][printing] = -cfg.thermal.preheat_min_s
        s["nozzle_temp_c"][printing] = cfg.thermal.nozzle_target_c - 15.0
        s["bed_temp_c"][printing] = cfg.thermal.bed_target_c - 8.0
        s["state"][~printing] = IDLE
        s["idle_until"][~printing] = rng.uniform(0.0, cfg.fleet.mean_idle_s, size=n)[~printing]
        s["progress"][~printing] = 0.0
        self.state = s
        self._assign_targets()

    def _assign_targets(self) -> None:
        """Heater setpoints follow from the material preset and the state machine."""
        cfg = self.cfg
        s = self.state
        active = ((s["state"] == PRE) | (s["state"] == PRINT) | (s["state"] == PAUSE))
        s["nozzle_target_c"] = np.where(active, cfg.thermal.nozzle_target_c, 0.0)
        s["bed_target_c"] = np.where(active, cfg.thermal.bed_target_c, 0.0)
        s["chamber_target_c"] = np.where(active & cfg.thermal.chamber_enabled,
                                        cfg.thermal.chamber_target_c,
                                        cfg.thermal.ambient_temp_c)

    # -- main loop ------------------------------------------------------------
    def run(self, progress_every: int = 0) -> RunArtifacts:
        """Run the simulation to ``cfg.simulation.duration_s``."""
        n_steps = self.cfg.n_steps
        t0 = time.perf_counter()
        for k in range(n_steps):
            self.step_index = k
            self.t = (k + 1) * self.dt
            self._step()
            if progress_every and (k + 1) % progress_every == 0:
                print(f"  step {k + 1}/{n_steps} t={self.t:.0f}s", flush=True)
        self.step_index = n_steps
        wall = time.perf_counter() - t0
        return self._finalise(wall)
    # -- 1. faults + state machine --------------------------------------------
    def _step_state_machine(self) -> None:
        cfg = self.cfg
        s = self.state
        t = self.t
        self._field = self.injector.parameter_field(t)
        for f in self.injector.activate(t):
            self._emit_event("fault_onset", self.printer_ids[f.printer_index], t,
                             {"fault": f.fault, "severity": round(f.severity, 4),
                              "duration_s": f.duration_s})

        conn = self.connectivity.online_mask(t)
        prev = self.state["prev_connectivity"].astype(bool)
        for idx in np.nonzero(~conn & prev)[0]:
            self._emit_event("link_down", self.printer_ids[idx], t, {})
        for idx in np.nonzero(conn & ~prev)[0]:
            self._emit_event("link_up", self.printer_ids[idx], t, {})
        s["prev_connectivity"] = conn.astype(np.int8)

        st = s["state"]
        field_ = self._field

        # IDLE -> PREHEATING: a job is assigned from the fleet queue.
        start = (st == IDLE) & (t >= s["idle_until"])
        if start.any():
            st[start] = PRE
            s["preheat_started"][start] = t
            self._reset_job(start)

        # PREHEATING -> PRINTING once both setpoints are within tolerance.
        pre = st == PRE
        if pre.any():
            ok = (pre
                  & (s["nozzle_temp_c"] >= s["nozzle_target_c"] - cfg.thermal.preheat_tolerance_c)
                  & (s["bed_temp_c"] >= s["bed_target_c"] - cfg.thermal.preheat_tolerance_c)
                  & ((t - s["preheat_started"]) >= cfg.thermal.preheat_min_s))
            st[ok] = PRINT
            timeout = pre & ~ok & ((t - s["preheat_started"]) > cfg.thermal.preheat_timeout_s)
            st[timeout] = FAIL
            for idx in np.nonzero(ok)[0]:
                self._emit_event("print_start", self.printer_ids[idx], t,
                                 {"job_index": int(s["job_index"][idx])})
            for idx in np.nonzero(timeout)[0]:
                self._emit_event("preheat_timeout", self.printer_ids[idx], t, {})

        # PRINTING: progress, completion, terminal faults.
        printing = st == PRINT
        if printing.any():
            s["job_elapsed_s"] = np.where(printing, s["job_elapsed_s"] + self.dt,
                                          s["job_elapsed_s"])
            s["progress"] = np.where(printing,
                                     np.clip(s["job_elapsed_s"] / s["job_duration_s"], 0.0, 1.0),
                                     s["progress"])
            done = printing & (s["job_elapsed_s"] >= s["job_duration_s"])
            st[done] = DONE
            fatal = printing & field_["terminal_fault"]
            st[fatal] = FAIL
            for idx in np.nonzero(done)[0]:
                self._emit_event("print_complete", self.printer_ids[idx], t,
                                 {"job_index": int(s["job_index"][idx]),
                                  "material_used_g": round(float(s["material_used_g"][idx]), 3)})
            for idx in np.nonzero(fatal)[0]:
                self._emit_event("print_failed", self.printer_ids[idx], t,
                                 {"fault": str(field_["fault_code"][idx])})

        # COMPLETED -> IDLE with a queue delay before the next job.
        done = st == DONE
        if done.any():
            s["jobs_completed"][done] += 1
            st[done] = IDLE
            s["progress"][done] = 1.0
            s["idle_until"][done] = t + self.rng_process.exponential(cfg.fleet.mean_idle_s,
                                                                    size=int(done.sum()))

        # FAILED -> MAINTENANCE; MAINTENANCE -> IDLE after repair.
        failed = st == FAIL
        if failed.any():
            k = int(failed.sum())
            s["jobs_failed"][failed] += 1
            st[failed] = MAINT
            dur = self.rng_process.exponential(cfg.health.mean_repair_s, size=k)
            s["maint_until"][failed] = t + dur
            for idx in np.nonzero(failed)[0]:
                self._emit_event("maintenance_start", self.printer_ids[idx], t,
                                 {"repair_s": round(float(s["maint_until"][idx] - t), 1)})
        maint = st == MAINT
        if maint.any():
            healed = maint & (t >= s["maint_until"])
            st[healed] = IDLE
            s["health"][healed] = cfg.health.maintenance_restore_health
            s["idle_until"][healed] = t + self.rng_process.exponential(
                cfg.fleet.mean_idle_s, size=int(healed.sum()))
            for idx in np.nonzero(healed)[0]:
                self.injector.clear_terminal(int(idx))
                self._emit_event("maintenance_end", self.printer_ids[idx], t, {})

        # Preventive maintenance when wear drives health below the threshold.
        low = (st == PRINT) & (s["health"] < cfg.health.maintenance_threshold)
        if low.any():
            st[low] = MAINT
            s["maint_until"][low] = t + cfg.health.mean_repair_s
            s["idle_until"][low] = s["maint_until"][low]
        s["state"] = st
        self._assign_targets()

    # -- 2. thermal ------------------------------------------------------------
    def _step_thermal(self) -> None:
        s = self.state
        f = self._field
        self.thermal.step(
            state=s,
            targets={"nozzle_target_c": s["nozzle_target_c"],
                     "bed_target_c": s["bed_target_c"],
                     "chamber_target_c": s["chamber_target_c"]},
            dt_s=self.dt,
            rng=self.rng_thermal,
            nozzle_conductance_scale=f["nozzle_conductance_scale"],
            nozzle_heat_load_w=f["nozzle_heat_load_w"],
            nozzle_heater_efficiency=f["nozzle_heater_efficiency"],
            bed_heater_efficiency=f["bed_heater_efficiency"],
            nozzle_gain_scale=f["nozzle_gain_scale"],
        )

    # -- 3. power + material ----------------------------------------------------
    def _step_power_material(self) -> None:
        s = self.state
        f = self._field
        printing = (s["state"] == PRINT)
        heat_w = self.thermal.heat_load_w(s)
        speed = np.where(printing, s["job_speed_mm_s"], 0.0)
        dep_rate = self.material.deposition_rate_mm3_s(speed, f["extrusion_scale"])
        nom_rate = self.material.deposition_rate_mm3_s(s["job_speed_mm_s"])
        extrusion_ratio = np.where(nom_rate > 0, dep_rate / np.maximum(nom_rate, 1e-9), 0.0)
        p = self.power_model.power_w(
            heater_power_w=heat_w,
            printing=printing,
            nozzle_temp_c=s["nozzle_temp_c"],
            ambient_c=self.cfg.thermal.ambient_temp_c,
            speed_mm_s=speed,
            extrusion_ratio=extrusion_ratio,
            motion_scale=f["motion_power_scale"],
            extruder_scale=f["extruder_power_scale"],
            total_scale=f["total_power_scale"],
        )
        if self.power_model.noise_std_frac > 0:
            p = p * (1.0 + self.rng_process.normal(0.0, self.power_model.noise_std_frac,
                                                  size=self.n))
        s["power_w"] = np.maximum(p, 0.0)
        s["energy_j"] = s["energy_j"] + s["power_w"] * self.dt
        s["material_used_g"] = (s["material_used_g"]
                                + self.material.mass_rate_g_s(dep_rate) * self.dt)

    # -- 4. health --------------------------------------------------------------
    def _step_health(self) -> None:
        s = self.state
        f = self._field
        operating = (s["state"] == PRINT) | (s["state"] == PRE)
        wear = self.cfg.health.wear_rate_per_s * f["wear_multiplier"] * operating.astype(np.float64)
        s["health"] = np.clip(s["health"] - wear * self.dt, 0.0, 1.0)

    # -- 5. telemetry -----------------------------------------------------------
    def _step_publish(self) -> None:
        if self.step_index % self.telemetry_period != 0:
            return
        t0 = time.perf_counter()
        s = self.state
        f = self._field
        n = self.n
        nozzle_meas = self.thermal.sensor(s["nozzle_temp_c"], self.rng_sensor,
                                          f["sensor_noise_scale"], f["sensor_bias_k"])
        bed_meas = self.thermal.sensor(s["bed_temp_c"], self.rng_sensor,
                                       f["sensor_noise_scale"], 0.0)
        st = s["state"]
        printing = st == PRINT
        layers = s["job_layers"]
        collect = self.collect_telemetry
        records = self._telemetry
        for i in range(n):
            fault_code = str(f["fault_code"][i])
            payload = {
                "timestamp_s": self.t,
                "printer_id": self.printer_ids[i],
                "state": STATE_NAMES[int(st[i])],
                "progress": round(float(s["progress"][i]), 6),
                "current_layer": int(np.floor(s["progress"][i] * layers[i])),
                "layer_count": int(layers[i]),
                "nozzle_temperature_c": round(float(nozzle_meas[i]), 3),
                "nozzle_target_c": float(s["nozzle_target_c"][i]),
                "bed_temperature_c": round(float(bed_meas[i]), 3),
                "bed_target_c": float(s["bed_target_c"][i]),
                "chamber_temperature_c": round(float(s["chamber_temp_c"][i]), 3),
                "print_speed_mm_s": round(float(s["job_speed_mm_s"][i]), 3) if printing[i] else 0.0,
                "power_w": round(float(s["power_w"][i]), 3),
                "energy_wh": round(float(s["energy_j"][i]) / 3600.0, 6),
                "material_used_g": round(float(s["material_used_g"][i]), 4),
                "health_score": round(float(s["health"][i]), 6),
                "fault_code": fault_code if fault_code else None,
                "connectivity": "ONLINE" if self.transport.is_online(i, self.t) else "OFFLINE",
                "job_index": int(s["job_index"][i]),
            }
            self._msg_seq += 1
            self.transport.publish(Message(
                seq=self._msg_seq,
                topic=topic(self.prefix, self.fleet_id, self.printer_ids[i], TELEMETRY),
                kind=TELEMETRY, printer_id=self.printer_ids[i],
                payload=payload, t_generated=self.t, qos=self.cfg.mqtt.qos))
            if collect:
                payload["t_generated_s"] = self.t
                records.append(payload)
        self._wall_publish_s += time.perf_counter() - t0

    # -- 6. transport + twins ---------------------------------------------------
    def _step_transport(self) -> None:
        t0 = time.perf_counter()
        for msg in self.transport.step(self.t):
            self.registry.apply(msg)
        self.registry.sample(self.t, self.dt)
        self._wall_transport_s += time.perf_counter() - t0

    # -- helpers ----------------------------------------------------------------
    def _reset_job(self, mask: np.ndarray) -> None:
        """Assign a freshly drawn job to the selected devices."""
        s = self.state
        k = int(mask.sum())
        if k == 0:
            return
        job = self.jobs.sample(k, self.rng_jobs, first_job_index=self._job_counter,
                               aligned_start=True)
        self._job_counter += k
        for key in ("job_index", "job_duration_s", "job_elapsed_s", "job_layers",
                    "job_speed_mm_s", "job_volume_mm3", "progress"):
            s[key][mask] = job[key]
        s["material_used_g"][mask] = 0.0
        s["energy_j"][mask] = 0.0

    def _emit_event(self, kind: str, printer_id: str, t_s: float,
                    payload: dict[str, Any]) -> None:
        if not self.collect_events:
            return
        self._events.append({"kind": kind, "printer_id": printer_id,
                             "timestamp_s": round(t_s, 3), **payload})

    def _finalise(self, wall_s: float) -> RunArtifacts:
        for msg in self.transport.flush(self.t):
            self.registry.apply(msg)
        self.transport.close()
        return RunArtifacts(
            config=self.cfg.to_dict(),
            seed=self.cfg.experiment.seed,
            telemetry=self._telemetry,
            events=self._events,
            twin_snapshots=self._twin_snapshots,
            metrics=self._metrics(wall_s),
            fault_summary=self.injector.summary(),
        )

    def _metrics(self, wall_s: float) -> dict[str, Any]:
        tc = self.transport.counters()
        reg = self.registry.counters()
        n = self.n
        duration = self.cfg.simulation.duration_s
        generated = tc.get("generated", 0)
        delivered = tc.get("delivered", 0)
        dropped = (tc.get("dropped_loss", 0) + tc.get("dropped_stale", 0)
                   + tc.get("dropped_broker", 0) + tc.get("dropped_queue_overflow", 0))
        steps = max(self.step_index, 1)
        return {
            "fleet_size": n,
            "simulated_duration_s": duration,
            "wall_clock_s": wall_s,
            "realtime_factor": duration / wall_s if wall_s > 0 else float("nan"),
            "device_steps_per_second": (n * steps) / wall_s if wall_s > 0 else float("nan"),
            "n_steps": self.step_index,
            "messages_generated": generated,
            "messages_delivered": delivered,
            "messages_dropped": dropped,
            "message_delivery_ratio_pct": 100.0 * delivered / generated if generated else 100.0,
            "telemetry_throughput_msg_s": generated / wall_s if wall_s > 0 else float("nan"),
            "duplicates": tc.get("duplicates", 0),
            "queued_for_replay": tc.get("queued_for_replay", 0),
            "replayed": tc.get("replayed", 0),
            "dropped_loss": tc.get("dropped_loss", 0),
            "dropped_stale": tc.get("dropped_stale", 0),
            "dropped_broker": tc.get("dropped_broker", 0),
            "dropped_queue_overflow": tc.get("dropped_queue_overflow", 0),
            "transport_latency_ms_mean": (tc.get("latency_ms_sum", 0.0) / delivered
                                          if delivered else 0.0),
            "transport_latency_ms_max": tc.get("latency_ms_max", 0.0),
            "events_emitted": len(self._events),
            "time_in_publish_s": self._wall_publish_s,
            "time_in_transport_s": self._wall_transport_s,
            "time_in_physics_s": max(wall_s - self._wall_publish_s - self._wall_transport_s, 0.0),
            **reg,
        }

        f = self._field
        operating = (s["state"] == PRINT) | (s["state"] == PRE)
        wear = self.cfg.health.wear_rate_per_s * f["wear_multiplier"] * operating.astype(np.float64)
        s["health"] = np.clip(s["health"] - wear * self.dt, 0.0, 1.0)

        s["state"] = st
        self._assign_targets()

        self._job_counter = n
        self._wall_publish_s = 0.0
        self._wall_transport_s = 0.0
        self._field: dict[str, np.ndarray] = {}
