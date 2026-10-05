"""Configuration model for SimTwin.

Configuration is expressed as nested dataclasses, loadable from YAML/JSON dictionaries
and dumpable back to plain dictionaries (so every run can serialise the exact parameter
set that produced it, which is what makes the experiments reproducible).

Conventions
-----------
* Physical quantities carry a unit suffix (``_w`` watt, ``_c`` degree Celsius, ``_s``
  second, ``_g`` gram, ``_mm3`` cubic millimetre, ``_ms`` millisecond).
* Every stochastic parameter is paired with a named seed-derived stream; no stochastic
  parameter has a hidden random default.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ExperimentConfig:
    name: str = "adhoc"
    seed: int = 42
    output_dir: str = "results"
    description: str = ""


@dataclass
class FleetConfig:
    fleet_id: str = "fleet-01"
    size: int = 10
    printer_model: str = "desktop-fdm-std"
    material: str = "PLA"
    #: Mean idle time (s) between completing a job and starting the next.
    mean_idle_s: float = 300.0
    #: Fraction of printers that start with an in-progress job (0..1).
    initial_printing_fraction: float = 0.6


@dataclass
class SimulationConfig:
    duration_s: float = 3600.0
    dt_s: float = 1.0
    telemetry_interval_ms: float = 1000.0
    #: Seconds at the start of the run excluded from analysis windows.
    warmup_s: float = 60.0


@dataclass
class ThermalConfig:
    """Lumped-parameter thermal masses (one capacitance and one conductance each).

    ``capacitance_j_k`` is C [J/K]; ``conductance_w_k`` is G [W/K]; the open-loop time
    constant is tau = C/G [s]; the maximum steady-state rise over the sink at full
    heater power is P_max/G [K].
    """

    ambient_temp_c: float = 25.0
    #: Heater setpoints used when a device is preheating/printing.
    nozzle_target_c: float = 210.0
    bed_target_c: float = 60.0
    chamber_target_c: float = 45.0
    #: Open-frame desktop machines have no chamber heater; off by default.
    chamber_enabled: bool = False
    #: Setpoint deviation within which preheat is considered complete [K].
    preheat_tolerance_c: float = 3.0
    #: Minimum preheat time even if setpoints are reached earlier [s].
    preheat_min_s: float = 20.0
    #: Preheat is aborted as FAILED after this long [s].
    preheat_timeout_s: float = 900.0
    nozzle_capacitance_j_k: float = 16.0
    nozzle_conductance_w_k: float = 0.08
    nozzle_heater_power_w: float = 40.0
    bed_capacitance_j_k: float = 1200.0
    bed_conductance_w_k: float = 3.0
    bed_heater_power_w: float = 250.0
    chamber_capacitance_j_k: float = 2700.0
    chamber_conductance_w_k: float = 1.5
    chamber_heater_power_w: float = 150.0
    #: Fraction of nozzle/bed heater dissipation that warms the chamber.
    chamber_coupling: float = 0.35
    #: Proportional gain, in duty per unit normalised temperature error.
    pid_kp: float = 4.0
    #: Integral time constant [s]; Ki = Kp / pid_ti_s.
    pid_ti_s: float = 30.0
    #: Standard deviation of the additive process disturbance (thermal noise) [K].
    process_noise_std_c: float = 0.15
    #: Ornstein-Uhlenbeck correlation time of the process disturbance [s].
    process_noise_tau_s: float = 20.0
    #: Standard deviation of the temperature *measurement* noise [K].
    sensor_noise_std_c: float = 0.25


@dataclass
class PowerConfig:
    electronics_standby_w: float = 8.0
    hotend_fan_w: float = 3.0
    part_fan_w: float = 5.0
    motion_base_w: float = 12.0
    motion_speed_w: float = 40.0
    extruder_w: float = 8.0
    #: Standard deviation of the multiplicative power measurement noise.
    noise_std_frac: float = 0.02


@dataclass
class MaterialConfig:
    filament_diameter_mm: float = 1.75
    layer_height_mm: float = 0.2
    line_width_mm: float = 0.45
    density_g_cm3: float = 1.24
    #: Nominal travel speed [mm/s] used to normalise the motion-power term.
    nominal_speed_mm_s: float = 60.0


@dataclass
class JobConfig:
    duration_min_s: float = 1800.0
    duration_max_s: float = 21600.0
    layers_min: int = 60
    layers_max: int = 900
    volume_min_mm3: float = 5000.0
    volume_max_mm3: float = 220000.0
    speed_min_mm_s: float = 40.0
    speed_max_mm_s: float = 120.0
    #: Relative standard deviation of the realised job duration.
    duration_jitter_frac: float = 0.05


@dataclass
class HealthConfig:
    #: Nominal wear per operating second (health points/s).
    wear_rate_per_s: float = 1.0e-6
    #: Additional wear per operating second per unit fault severity.
    fault_wear_multiplier: float = 25.0
    #: Mean repair time [s] after a fault-triggered maintenance stop.
    mean_repair_s: float = 1800.0
    #: Health threshold below which preventive maintenance is scheduled.
    maintenance_threshold: float = 0.35
    #: Health to which a device is restored by preventive maintenance.
    #: Health to which a device is restored by preventive maintenance.
    maintenance_restore_health: float = 0.92


@dataclass
class NetworkConfig:
    """Delivery semantics of the simulated communication channel.

    All quantities are per-message and applied by the transport pipeline, not by
    the device model, so that physical-layer faults and network-layer faults
    stay separable in the analysis.
    """

    #: Fixed (base) one-way transport latency [ms].
    base_latency_ms: float = 12.0
    #: Standard deviation of the additive Gaussian latency jitter [ms].
    jitter_std_ms: float = 6.0
    #: Shape parameter of the lognormal tail component of the latency [ms].
    jitter_tail_sigma: float = 0.35
    #: Independent per-message loss probability (QoS 0 semantics).
    loss_probability: float = 0.0
    #: Probability that a QoS >= 1 message is delivered twice (at-least-once).
    duplicate_probability: float = 0.0
    #: Mean interval between per-device disconnection episodes [s] (0 disables).
    mean_outage_interval_s: float = 0.0
    #: Mean duration of a disconnection episode [s].
    mean_outage_duration_s: float = 0.0
    #: Minimum/maximum episode duration actually drawn.
    outage_duration_min_s: float = 10.0
    outage_duration_max_s: float = 120.0
    #: Base of the exponential reconnect backoff applied at each failed attempt [s].
    reconnect_backoff_base_s: float = 2.0
    #: Mean interval between broker-wide outages [s] (0 disables).
    mean_broker_outage_interval_s: float = 0.0
    #: Mean duration of a broker-wide outage [s].
    mean_broker_outage_duration_s: float = 0.0
    #: Maximum number of messages a disconnected device buffers for replay.
    replay_queue_limit: int = 10_000
    #: Telemetry messages older than this at delivery are dropped as stale [s].
    max_message_age_s: float = 300.0


@dataclass
class TwinConfig:
    """Digital-twin registry parameters."""

    #: Twin is declared stale when its last accepted update is older than this [s].
    staleness_threshold_s: float = 10.0
    #: Twin is declared OFFLINE when no update arrived for this long [s].
    offline_threshold_s: float = 60.0
    #: A device that reconnects sends a full state snapshot (retained message) first.
    snapshot_on_reconnect: bool = True


@dataclass
class FaultConfig:
    """Fault-injection schedule.

    ``mode``:
      * ``"none"``      - no faults (normal-operation control run).
      * ``"poisson"``   - onsets follow a Poisson process with rate
        ``rate_per_hour`` per printer; type drawn from ``weights``.
      * ``"scheduled"`` - faults placed explicitly through ``schedule``.
    """

    mode: str = "none"
    #: Poisson rate of fault onsets per printer per hour.
    rate_per_hour: float = 0.0
    #: Relative weights over fault type names (see simtwin.faults.FAULT_CATALOGUE).
    weights: dict[str, float] = field(default_factory=dict)
    #: Uniform range of fault severity (0..1).
    severity_min: float = 0.3
    severity_max: float = 1.0
    #: Uniform range of fault duration [s].
    duration_min_s: float = 300.0
    duration_max_s: float = 1800.0
    #: Seconds over which a fault ramps from zero to full severity.
    ramp_s: float = 60.0
    #: Explicit entries: dicts with printer_index, fault, onset_s, duration_s, severity.
    schedule: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MqttConfig:
    """Optional real-broker (MQTT) transport.

    When ``enabled`` is false the simulator uses the in-process transport, which
    implements the same delivery-semantics pipeline deterministically.
    """

    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 1883
    qos: int = 0
    keepalive_s: int = 60
    clean_session: bool = True
    topic_prefix: str = "simtwin"
    #: Seconds to wait for in-flight messages to drain at shutdown.
    drain_timeout_s: float = 10.0


@dataclass
class StorageConfig:
    output_dir: str = "results"
    formats: tuple[str, ...] = ("parquet",)
    write_telemetry: bool = True
    write_events: bool = True
    write_twins: bool = False
    compress: str = "zstd"



@dataclass
class SimConfig:
    """Root configuration object for one SimTwin run."""

    experiment: ExperimentConfig = field(default_factory=ExperimentConfig)
    fleet: FleetConfig = field(default_factory=FleetConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    thermal: ThermalConfig = field(default_factory=ThermalConfig)
    power: PowerConfig = field(default_factory=PowerConfig)
    material: MaterialConfig = field(default_factory=MaterialConfig)
    jobs: JobConfig = field(default_factory=JobConfig)
    health: HealthConfig = field(default_factory=HealthConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    twin: TwinConfig = field(default_factory=TwinConfig)
    faults: FaultConfig = field(default_factory=FaultConfig)
    mqtt: MqttConfig = field(default_factory=MqttConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)

    @classmethod
    def default(cls) -> "SimConfig":
        """The validated baseline configuration every experiment starts from."""
        cfg = cls()
        cfg.validate()
        return cfg

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SimConfig":
        """Build a config from a nested mapping, rejecting unknown keys."""
        cfg = cls()
        for section, value in (data or {}).items():
            if not hasattr(cfg, section):
                raise KeyError(f"unknown configuration section: {section!r}")
            sub = getattr(cfg, section)
            if not is_dataclass(sub):
                setattr(cfg, section, value)
                continue
            known = {f.name for f in fields(type(sub))}
            for key, val in (value or {}).items():
                if key not in known:
                    raise KeyError(f"unknown configuration key: {section}.{key}")
                if key == "formats" and isinstance(val, list):
                    val = tuple(val)
                setattr(sub, key, val)
        cfg.validate()
        return cfg

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SimConfig":
        with open(path) as fh:
            data = yaml.safe_load(fh) or {}
        return cls.from_dict(data)

    def validate(self) -> None:
        sim = self.simulation
        if self.fleet.size <= 0:
            raise ValueError("fleet.size must be positive")
        if sim.dt_s <= 0:
            raise ValueError("simulation.dt_s must be positive")
        if sim.duration_s <= 0:
            raise ValueError("simulation.duration_s must be positive")
        step_ms = sim.dt_s * 1000.0
        if sim.telemetry_interval_ms < step_ms:
            raise ValueError("simulation.telemetry_interval_ms must be >= dt_s * 1000")
        ratio = sim.telemetry_interval_ms / step_ms
        if abs(ratio - round(ratio)) > 1e-9:
            raise ValueError(
                "simulation.telemetry_interval_ms must be an integer multiple of dt_s * 1000"
            )
        net = self.network
        if not (0.0 <= net.loss_probability <= 1.0):
            raise ValueError("network.loss_probability must be in [0, 1]")
        if not (0.0 <= net.duplicate_probability <= 1.0):
            raise ValueError("network.duplicate_probability must be in [0, 1]")
        if self.faults.mode not in {"none", "poisson", "scheduled"}:
            raise ValueError(f"unknown faults.mode: {self.faults.mode!r}")
        # Imported lazily: the fault catalogue imports this module, so a
        # module-level import here would be circular.
        from .faults.catalogue import FAULT_CATALOGUE

        FAULT_NAMES = set(FAULT_CATALOGUE)
        if self.faults.mode == "poisson":
            unknown = set(self.faults.weights) - FAULT_NAMES
            if unknown:
                raise ValueError(f"faults.weights has unknown fault names: {sorted(unknown)}")
            if self.faults.weights and sum(self.faults.weights.values()) <= 0:
                raise ValueError("faults.weights must contain at least one positive weight")
        if self.faults.mode == "scheduled":
            for entry in self.faults.schedule:
                name = str(entry.get("fault", ""))
                if name not in FAULT_NAMES:
                    raise ValueError(f"faults.schedule entry has unknown fault: {name!r}")
                idx = int(entry.get("printer_index", -1))
                if not 0 <= idx < self.fleet.size:
                    raise ValueError(f"faults.schedule printer_index out of range: {idx}")

    @property
    def n_steps(self) -> int:
        return int(round(self.simulation.duration_s / self.simulation.dt_s))

    @property
    def telemetry_period_steps(self) -> int:
        return int(round(self.simulation.telemetry_interval_ms / (self.simulation.dt_s * 1000.0)))

    def to_dict(self) -> dict[str, Any]:
        def _clean(obj: Any) -> Any:
            if isinstance(obj, tuple):
                return [_clean(v) for v in obj]
            if isinstance(obj, dict):
                return {k: _clean(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_clean(v) for v in obj]
            return obj

        return _clean(asdict(self))

