"""Lumped-capacitance thermal model of a desktop FDM print head, bed and chamber.

Model
-----
Each thermal node is a single capacitance ``C`` [J/K] linked to the ambient by a
single conductance ``G`` [W/K] and driven by a heater of rated power ``P`` [W]
with duty cycle ``u`` in [0, 1]:

    C dT/dt = u P - G (T - T_amb) + q_fault + xi(t)                            (1)

``xi(t)`` is an Ornstein-Uhlenbeck (OU) disturbance with correlation time
``tau_noise`` and stationary standard deviation ``process_noise_std_c``:

    xi_{k+1} = rho xi_k + sigma N(0,1),  rho = exp(-dt/tau_noise),
    sigma = process_noise_std_c sqrt(1 - rho^2)                                (2)

Heaters are driven by a duty-saturated PI controller on the *normalised* error
``e = (T_set - T)/(T_set - T_amb)``:

    u = clip(Kp e + (Kp/Ti) integral(e dt), 0, 1)                              (3)

Normalising the error makes one gain set behave consistently across the nozzle
(25 -> 210 K rise), the bed (25 -> 60 K rise) and a heated chamber, matching the
PWM-duty semantics of a Marlin-style controller.

The open-loop step response of (1) at full duty is
``T(t) = T_amb + (P/G)(1 - exp(-t G/C))``: a first-order lag with time constant
``tau = C/G`` and maximum rise ``P/G``.  The defaults give ``tau_nozzle = 200 s``
(25 -> 200 degC in ~86 s) and ``tau_bed = 400 s`` (25 -> 60 degC in ~217 s), the
order of magnitude reported for desktop hotends and heated beds.

The chamber is a passive node warmed by coupling from the bed and hotend:

    C_c dT_c/dt = u_c P_c + k G_b (T_b - T_c) + k G_n (T_n - T_c)
                  - G_c (T_c - T_amb) + xi_c(t)                                 (4)

All functions operate on NumPy arrays so one call advances the thermal state of a
whole fleet; scalar callers may pass floats.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..config import ThermalConfig


@dataclass
class ThermalNodeParams:
    """Parameters of one first-order thermal node."""

    capacitance_j_k: float
    conductance_w_k: float
    heater_power_w: float
    chamber_coupling: float = 0.0

    @property
    def tau_s(self) -> float:
        """Open-loop thermal time constant ``C/G`` [s]."""
        return self.capacitance_j_k / self.conductance_w_k

    @property
    def max_rise_k(self) -> float:
        """Steady-state rise over ambient at full heater duty [K]."""
        return self.heater_power_w / self.conductance_w_k

    @property
    def holding_duty(self) -> float:
        """Duty needed to hold one kelvin of rise (``G/P``) [1/K]."""
        return self.conductance_w_k / self.heater_power_w


@dataclass
class ThermalPlant:
    """Three coupled first-order nodes (nozzle, bed, chamber) with PI heaters."""

    nozzle: ThermalNodeParams
    bed: ThermalNodeParams
    chamber: ThermalNodeParams
    ambient_c: float
    pid_kp: float
    pid_ti_s: float
    process_noise_std_c: float
    process_noise_tau_s: float
    sensor_noise_std_c: float

    @classmethod
    def from_config(cls, cfg: ThermalConfig) -> "ThermalPlant":
        k = cfg.chamber_coupling
        return cls(
            nozzle=ThermalNodeParams(cfg.nozzle_capacitance_j_k, cfg.nozzle_conductance_w_k,
                                     cfg.nozzle_heater_power_w, k),
            bed=ThermalNodeParams(cfg.bed_capacitance_j_k, cfg.bed_conductance_w_k,
                                  cfg.bed_heater_power_w, k),
            chamber=ThermalNodeParams(cfg.chamber_capacitance_j_k, cfg.chamber_conductance_w_k,
                                      cfg.chamber_heater_power_w, 0.0),
            ambient_c=cfg.ambient_temp_c,
            pid_kp=cfg.pid_kp,
            pid_ti_s=cfg.pid_ti_s,
            process_noise_std_c=cfg.process_noise_std_c,
            process_noise_tau_s=cfg.process_noise_tau_s,
            sensor_noise_std_c=cfg.sensor_noise_std_c,
        )

    def duty(self, temp_c, target_c, integ, dt_s, gain_scale=1.0):
        """Duty-saturated PI controller (3) with conditional anti-windup."""
        denom = np.maximum(target_c - self.ambient_c, 1e-6)
        err = (target_c - temp_c) / denom
        integ = integ + err * dt_s
        u = np.clip(self.pid_kp * gain_scale * err + (self.pid_kp / self.pid_ti_s) * integ, 0.0, 1.0)
        # Conditional integration: undo the integration when saturated and the
        # error still pushes further into saturation (nozzle cold-start, bed off).
        integ = np.where((u >= 1.0) & (err > 0.0), integ - err * dt_s, integ)
        integ = np.where((u <= 0.0) & (err < 0.0), integ - err * dt_s, integ)
        return u, integ

    def ou_step(self, xi, dt_s: float, rng: np.random.Generator) -> np.ndarray:
        """Exact OU update (2) for correlation time ``process_noise_tau_s``."""
        if self.process_noise_std_c <= 0.0:
            return xi
        rho = np.exp(-dt_s / self.process_noise_tau_s)
        sigma = self.process_noise_std_c * np.sqrt(max(1.0 - rho * rho, 0.0))
        return rho * xi + sigma * rng.normal(0.0, 1.0, size=np.shape(xi))

    def sensor(self, temp_c, rng: np.random.Generator, noise_scale=1.0, bias_c=0.0) -> np.ndarray:
        """Noisy temperature *measurement* (sensor model, distinct from plant state)."""
        out = temp_c + bias_c
        if self.sensor_noise_std_c > 0.0:
            out = out + rng.normal(0.0, 1.0, size=np.shape(temp_c)) * self.sensor_noise_std_c * noise_scale
        return out

    def step(
        self,
        *,
        state: dict[str, np.ndarray],
        targets: dict[str, np.ndarray],
        dt_s: float,
        rng: np.random.Generator,
        nozzle_conductance_scale=1.0,
        nozzle_heat_load_w=0.0,
        bed_conductance_scale=1.0,
        chamber_conductance_scale=1.0,
        nozzle_heater_efficiency=1.0,
        bed_heater_efficiency=1.0,
        nozzle_gain_scale=1.0,
    ) -> dict[str, np.ndarray]:
        """Advance the three thermal nodes by one timestep (1), (2), (4).

        Fault effects enter only through the explicit scale/load arguments, so the
        fault layer never mutates temperatures directly and every fault's physical
        mechanism stays auditable in one place.
        """
        duty_n, integ_n = self.duty(state["nozzle_temp_c"], targets["nozzle_target_c"],
                                    state["nozzle_integral"], dt_s, nozzle_gain_scale)
        duty_b, integ_b = self.duty(state["bed_temp_c"], targets["bed_target_c"],
                                    state["bed_integral"], dt_s)
        duty_c, integ_c = self.duty(state["chamber_temp_c"], targets["chamber_target_c"],
                                    state["chamber_integral"], dt_s)

        g_n = self.nozzle.conductance_w_k * nozzle_conductance_scale
        g_b = self.bed.conductance_w_k * bed_conductance_scale
        g_c = self.chamber.conductance_w_k * chamber_conductance_scale
        k = self.nozzle.chamber_coupling

        dtn = (duty_n * self.nozzle.heater_power_w * nozzle_heater_efficiency
               - g_n * (state["nozzle_temp_c"] - self.ambient_c) + nozzle_heat_load_w
               + state["xi_nozzle"])
        dtb = (duty_b * self.bed.heater_power_w * bed_heater_efficiency
               - g_b * (state["bed_temp_c"] - self.ambient_c) + state["xi_bed"])
        dtc = (duty_c * self.chamber.heater_power_w
               + k * g_b * (state["bed_temp_c"] - state["chamber_temp_c"])
               + k * g_n * (state["nozzle_temp_c"] - state["chamber_temp_c"])
               - g_c * (state["chamber_temp_c"] - self.ambient_c)
               + state["xi_chamber"])

        state["nozzle_temp_c"] = state["nozzle_temp_c"] + dt_s * dtn / self.nozzle.capacitance_j_k
        state["bed_temp_c"] = state["bed_temp_c"] + dt_s * dtb / self.bed.capacitance_j_k
        state["chamber_temp_c"] = state["chamber_temp_c"] + dt_s * dtc / self.chamber.capacitance_j_k

        state["nozzle_duty"] = duty_n
        state["bed_duty"] = duty_b
        state["chamber_duty"] = duty_c
        state["nozzle_integral"] = integ_n
        state["bed_integral"] = integ_b
        state["chamber_integral"] = integ_c
        state["xi_nozzle"] = self.ou_step(state["xi_nozzle"], dt_s, rng)
        state["xi_bed"] = self.ou_step(state["xi_bed"], dt_s, rng)
        state["xi_chamber"] = self.ou_step(state["xi_chamber"], dt_s, rng)
        return state

    def heat_load_w(self, state: dict[str, np.ndarray]) -> np.ndarray:
        """Instantaneous heater power [W] delivered by the three heaters."""
        return (state["nozzle_duty"] * self.nozzle.heater_power_w
                + state["bed_duty"] * self.bed.heater_power_w
                + state["chamber_duty"] * self.chamber.heater_power_w)
