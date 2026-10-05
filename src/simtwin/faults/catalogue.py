"""Fault catalogue: the physical/observational effect of every injectable fault.

Each fault is a *mechanism*, not a label: it declares which model parameters it
modifies and by how much at full severity.  The fault layer never writes to a
telemetry field directly; every fault signature is an emergent consequence of the
parameter change, which is what makes the generated time series interpretable.

Severity ``s`` ramps linearly from 0 to ``severity`` over ``ramp_s`` seconds after
onset, so a degradation fault develops gradually instead of stepping.

Fault mechanisms (effect at full severity, ``s = 1``)
----------------------------------------------------
``nozzle_heater_failure``   nozzle heater efficiency -> 0; nozzle temperature decays
                            toward ambient with ``tau_nozzle``; duty saturates at 1.
``bed_heater_failure``      bed heater efficiency -> 0; decay with ``tau_bed``.
``temperature_instability`` nozzle loop proportional gain x6 -> sustained limit cycle.
``nozzle_thermal_drift``    +8 W parasitic heat load on the nozzle node -> overshoot.
``abnormal_cooling``        nozzle conductance x4 (fan on the heat break) -> setpoint
                            unattainable, temperature sags, duty saturates.
``extrusion_blockage``      extrusion factor -> 0.4, extruder power x1.8: deposition
                            falls while motor demand rises (under-extrusion).
``motor_overheating``       motion power x2.5, wear accumulation x3.
``power_anomaly``           total demand x1.35 with no process change.
``sensor_drift_nozzle``     additive bias ramp (up to 15 K) on the nozzle
                            *measurement* only; the plant is untouched.
``sensor_noise``            nozzle/bed measurement noise x10; plant untouched.
``print_interruption``      terminal: the job aborts, device -> FAILED -> MAINTENANCE.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class FaultSpec:
    """Static description of one injectable fault mechanism."""

    name: str
    #: Human-readable mechanism, reused verbatim in the dataset schema documentation.
    description: str
    #: Subsystem class, used for the fault-family analysis in the manuscript.
    family: str
    #: True if the fault aborts the running job.
    terminal: bool = False
    #: True if the fault changes only what the twin *observes*, not the plant.
    observational: bool = False
    # -- effect coefficients at full severity ------------------------------
    nozzle_heater_efficiency: float = 1.0
    bed_heater_efficiency: float = 1.0
    nozzle_conductance_scale: float = 1.0
    nozzle_heat_load_w: float = 0.0
    nozzle_gain_scale: float = 1.0
    extrusion_scale: float = 1.0
    extruder_power_scale: float = 1.0
    motion_power_scale: float = 1.0
    total_power_scale: float = 1.0
    sensor_noise_scale: float = 1.0
    #: Additive sensor bias reached at full severity [K] (ramped over the duration).
    sensor_bias_k: float = 0.0
    #: Multiplier applied to the nominal wear rate while the fault is active.
    wear_multiplier: float = 1.0


def _catalogue() -> dict[str, FaultSpec]:
    specs = [
        FaultSpec("nozzle_heater_failure",
                  "Nozzle cartridge heater loses effectiveness; duty saturates while "
                  "nozzle temperature decays toward ambient with tau_nozzle.",
                  "thermal", nozzle_heater_efficiency=0.0, wear_multiplier=3.0),
        FaultSpec("bed_heater_failure",
                  "Heated-bed heater loses effectiveness; bed temperature decays with "
                  "tau_bed and chamber coupling weakens.",
                  "thermal", bed_heater_efficiency=0.0, wear_multiplier=2.0),
        FaultSpec("temperature_instability",
                  "Nozzle control-loop proportional gain multiplied by 6, producing a "
                  "sustained limit cycle around the setpoint.",
                  "thermal", nozzle_gain_scale=6.0, wear_multiplier=1.5),
        FaultSpec("nozzle_thermal_drift",
                  "Parasitic 8 W heat load applied to the nozzle node (thermistor "
                  "self-heating / heat creep); nozzle overshoots its setpoint.",
                  "thermal", nozzle_heat_load_w=8.0, wear_multiplier=2.0),
        FaultSpec("abnormal_cooling",
                  "Nozzle conductance to ambient multiplied by 4 (part fan aimed at the "
                  "heat break); setpoint unattainable, temperature sags, duty saturates.",
                  "thermal", nozzle_conductance_scale=4.0, wear_multiplier=1.5),
        FaultSpec("extrusion_blockage",
                  "Partial hotend blockage: deposited volume falls to 40 % of command "
                  "while extruder motor demand rises to 180 %.",
                  "extrusion", extrusion_scale=0.4, extruder_power_scale=1.8,
                  wear_multiplier=4.0),
        FaultSpec("motor_overheating",
                  "Axis motor friction/wear: motion power demand multiplied by 2.5 and "
                  "mechanical wear accumulation tripled.",
                  "mechanical", motion_power_scale=2.5, wear_multiplier=3.0),
        FaultSpec("power_anomaly",
                  "Unexplained 35 % increase in total electrical demand with no process "
                  "change (failing PSU / heater short to ground).",
                  "electrical", total_power_scale=1.35, wear_multiplier=2.0),
        FaultSpec("sensor_drift_nozzle",
                  "Additive bias ramp of up to 15 K on the nozzle thermistor "
                  "measurement; the physical plant is unchanged.",
                  "observational", sensor_bias_k=15.0, observational=True),
        FaultSpec("sensor_noise",
                  "Nozzle and bed measurement noise standard deviation multiplied by 10; "
                  "the physical plant is unchanged.",
                  "observational", sensor_noise_scale=10.0, observational=True),
        FaultSpec("print_interruption",
                  "Unrecoverable motion/controller fault: the active job aborts and the "
                  "device enters FAILED, then MAINTENANCE.",
                  "mechanical", terminal=True, wear_multiplier=5.0),
    ]
    return {s.name: s for s in specs}


FAULT_CATALOGUE: dict[str, FaultSpec] = _catalogue()

#: Fault families, for the aggregate analysis in the manuscript.
FAULT_FAMILIES: tuple[str, ...] = tuple(sorted({s.family for s in FAULT_CATALOGUE.values()}))

#: Default fault mix used by the Poisson fault-injection experiments.
DEFAULT_FAULT_WEIGHTS: dict[str, float] = {
    "nozzle_heater_failure": 1.0,
    "bed_heater_failure": 0.6,
    "temperature_instability": 1.0,
    "nozzle_thermal_drift": 1.0,
    "abnormal_cooling": 0.8,
    "extrusion_blockage": 1.2,
    "motor_overheating": 1.0,
    "power_anomaly": 0.8,
    "sensor_drift_nozzle": 1.0,
    "sensor_noise": 0.8,
    "print_interruption": 0.4,
}


def get_fault(name: str) -> FaultSpec:
    try:
        return FAULT_CATALOGUE[name]
    except KeyError as exc:  # pragma: no cover - configuration error path
        raise KeyError(f"unknown fault {name!r}; known: {sorted(FAULT_CATALOGUE)}") from exc

    def to_dict(self) -> dict:
        return asdict(self)
