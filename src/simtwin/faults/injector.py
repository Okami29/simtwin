"""Fault scheduling and the translation of active faults into model parameters.

Two scheduling modes are supported.

``poisson``
    Fault onsets for each device follow a Poisson process of rate
    ``rate_per_hour``; type, severity and duration are drawn from the configured
    distributions from a dedicated random stream, so the schedule is fully
    determined by the seed.

``scheduled``
    The experiment script supplies explicit
    ``(printer_index, fault, onset_s, duration_s, severity)`` tuples.  This is the
    mode used by the controlled fault-detection experiment, where onset times must
    be identical across seeds.

At every timestep the injector emits a *parameter field*: one array per model
parameter giving the effect to apply to each device.  The engine passes those
arrays to the thermal, power and material models, which is the only channel
through which a fault can influence the simulation.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..config import FaultConfig
from .catalogue import FAULT_CATALOGUE, FaultSpec, get_fault

#: Multiplicative parameters (blended as 1 + s (c - 1)).
_MULTIPLICATIVE = (
    "nozzle_heater_efficiency", "bed_heater_efficiency", "nozzle_conductance_scale",
    "nozzle_gain_scale", "extrusion_scale", "extruder_power_scale",
    "motion_power_scale", "total_power_scale", "sensor_noise_scale", "wear_multiplier",
)
#: Additive parameters (blended as s * value).
_ADDITIVE = ("nozzle_heat_load_w", "sensor_bias_k")


@dataclass
class ActiveFault:
    """One injected fault instance."""

    printer_index: int
    fault: str
    onset_s: float
    duration_s: float
    severity: float
    #: Terminal faults persist until explicitly cleared (e.g. after repair).
    active: bool = True

    @property
    def end_s(self) -> float:
        """Expiry time; a non-positive duration means "until cleared" (terminal faults)."""
        return float("inf") if self.duration_s <= 0.0 else self.onset_s + self.duration_s

    def ramp(self, t_s: float, ramp_s: float) -> float:
        """Effective severity at ``t_s``: linear ramp-in, hard stop at ``end_s``."""
        if not self.active or t_s < self.onset_s or t_s >= self.end_s:
            return 0.0
        up = 1.0 if ramp_s <= 0 else min((t_s - self.onset_s) / ramp_s, 1.0)
        return self.severity * up


@dataclass
class FaultInjector:
    """Schedules faults and emits per-device parameter fields."""

    n_printers: int
    config: FaultConfig
    faults: list[ActiveFault] = field(default_factory=list)
    _cursor: int = 0

    @classmethod
    def build(cls, n_printers: int, cfg: FaultConfig, rng: np.random.Generator,
             duration_s: float) -> "FaultInjector":
        inj = cls(n_printers=n_printers, config=cfg)
        if cfg.mode == "none":
            return inj
        if cfg.mode == "scheduled":
            inj.faults = [
                ActiveFault(int(e["printer_index"]), str(e["fault"]), float(e["onset_s"]),
                            float(e["duration_s"]), float(e.get("severity", 1.0)))
                for e in cfg.schedule
            ]
            for f in inj.faults:
                get_fault(f.fault)  # validate names eagerly
        else:  # poisson
            inj.faults = cls._poisson_schedule(n_printers, cfg, rng, duration_s)
        inj.faults.sort(key=lambda f: (f.onset_s, f.printer_index))
        return inj

    @staticmethod
    def _poisson_schedule(n_printers: int, cfg: FaultConfig, rng: np.random.Generator,
                          duration_s: float) -> list[ActiveFault]:
        """Draw a Poisson fault schedule from the seeded stream."""
        names = list(cfg.weights) or sorted(FAULT_CATALOGUE)
        weights = np.array([cfg.weights.get(n, 1.0) for n in names], dtype=np.float64)
        total = weights.sum()
        if total <= 0.0:
            raise ValueError("faults.weights must contain at least one positive weight")
        weights /= total
        rate_per_s = cfg.rate_per_hour / 3600.0
        out: list[ActiveFault] = []
        if rate_per_s <= 0.0:
            return out
        for i in range(n_printers):
            t = rng.exponential(1.0 / rate_per_s)
            while t < duration_s:
                name = str(rng.choice(names, p=weights))
                spec = FAULT_CATALOGUE[name]
                # Terminal faults abort the job at onset, so they carry no duration.
                dur = 0.0 if spec.terminal else float(
                    rng.uniform(cfg.duration_min_s, cfg.duration_max_s))
                sev = float(rng.uniform(cfg.severity_min, cfg.severity_max))
                out.append(ActiveFault(i, name, t, dur, sev))
                t = t + rng.exponential(1.0 / rate_per_s)
        return out

    # -- per-step interface --------------------------------------------------
    def activate(self, t_s: float) -> list[ActiveFault]:
        """Advance the onset cursor to ``t_s``; return faults that started since last call."""
        started: list[ActiveFault] = []
        while self._cursor < len(self.faults) and self.faults[self._cursor].onset_s <= t_s:
            started.append(self.faults[self._cursor])
            self._cursor += 1
        return started

    def clear_terminal(self, printer_index: int) -> None:
        """Deactivate a device's terminal faults (called once repair is complete)."""
        for f in self.faults:
            if f.printer_index == printer_index and f.active and FAULT_CATALOGUE[f.fault].terminal:
                f.active = False

    def active_severities(self, t_s: float) -> dict[int, dict[str, float]]:
        """Return ``{printer_index: {fault_name: effective_severity}}`` at ``t_s``."""
        out: dict[int, dict[str, float]] = {}
        for f in self.faults:
            s = f.ramp(t_s, self.config.ramp_s)
            if s > 0.0:
                out.setdefault(f.printer_index, {})[f.fault] = s
        return out

    def parameter_field(self, t_s: float) -> dict[str, np.ndarray]:
        """Aggregate all active faults into per-device model-parameter fields.

        Multiplicative effects compose multiplicatively, additive effects
        additively.  Keys are consumed by :class:`simtwin.fleet.engine.FleetEngine`.
        """
        n = self.n_printers
        out: dict[str, np.ndarray] = {k: np.ones(n) for k in _MULTIPLICATIVE}
        for k in _ADDITIVE:
            out[k] = np.zeros(n)
        out["terminal_fault"] = np.zeros(n, dtype=bool)
        out["fault_code"] = np.full(n, "", dtype=object)
        out["fault_severity"] = np.zeros(n)

        for idx, faults in self.active_severities(t_s).items():
            dominant = max(faults.items(), key=lambda kv: kv[1])
            for name, sev in faults.items():
                spec: FaultSpec = get_fault(name)
                for key in _MULTIPLICATIVE:
                    coeff = getattr(spec, key)
                    out[key][idx] *= 1.0 + sev * (coeff - 1.0)
                for key in _ADDITIVE:
                    out[key][idx] += sev * getattr(spec, key)
                if spec.terminal:
                    out["terminal_fault"][idx] = True
            out["fault_code"][idx] = dominant[0]
            out["fault_severity"][idx] = dominant[1]
        return out

    def summary(self) -> dict[str, int]:
        """Counts of injected faults by type (recorded in run metadata)."""
        counts: dict[str, int] = {}
        for f in self.faults:
            counts[f.fault] = counts.get(f.fault, 0) + 1
        return counts
