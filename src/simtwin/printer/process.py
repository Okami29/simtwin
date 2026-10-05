"""Power, material-deposition and print-job models.

Power model
-----------
Instantaneous electrical demand is the sum of the energised subsystems:

    P(t) = P_elec
         + u_n P_n + u_b P_b + u_c P_c                      (heaters: duty x rated)
         + P_fan_hotend [T_n > T_amb + 20]
         + P_fan_part    [printing]
         + (P_mot_base + P_mot_v * v / v_nom) [printing]    (motion)
         + P_extruder * Q / Q_nom                           (extrusion)        (5)

Heater terms use the *duty* produced by the thermal controller, so heating energy
is not an independent assumption: it follows from the same first-order plant that
produces the temperature trajectory.  Energy is integrated by rectangular
quadrature, ``E_{k+1} = E_k + P_k dt``.

The defaults are chosen so that the implied volumetric specific energy consumption
``SEC = E / V_dep`` of a bed-heated PLA print lands inside the 24.8-85.7 kJ/cm^3
band measured for FFF by Hopkins et al. (2021); the experiment suite reports the
value actually obtained rather than asserting it.

Material model
--------------
Deposited road volume rate is the slicer identity

    Q_dep = w_line * h_layer * v_print * s_extrusion         [mm^3/s]          (6)

with ``s_extrusion`` a multiplicative extrusion factor (1.0 nominal; < 1 models
under-extrusion).  Deposited mass follows from the melt density rho:

    dm/dt = Q_dep * rho / 1000                              [g/s]             (7)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..config import JobConfig, MaterialConfig, PowerConfig


@dataclass
class PowerModel:
    """Additive subsystem power model (5)."""

    electronics_standby_w: float
    hotend_fan_w: float
    part_fan_w: float
    motion_base_w: float
    motion_speed_w: float
    extruder_w: float
    nominal_speed_mm_s: float
    noise_std_frac: float

    @classmethod
    def from_config(cls, cfg: PowerConfig, material: MaterialConfig) -> "PowerModel":
        return cls(
            electronics_standby_w=cfg.electronics_standby_w,
            hotend_fan_w=cfg.hotend_fan_w,
            part_fan_w=cfg.part_fan_w,
            motion_base_w=cfg.motion_base_w,
            motion_speed_w=cfg.motion_speed_w,
            extruder_w=cfg.extruder_w,
            nominal_speed_mm_s=material.nominal_speed_mm_s,
            noise_std_frac=cfg.noise_std_frac,
        )

    def power_w(
        self,
        *,
        heater_power_w: np.ndarray,
        printing: np.ndarray,
        nozzle_temp_c: np.ndarray,
        ambient_c: float,
        speed_mm_s: np.ndarray,
        extrusion_ratio: np.ndarray,
        motion_scale=1.0,
        extruder_scale=1.0,
        total_scale=1.0,
    ) -> np.ndarray:
        """Instantaneous demand [W] (5)."""
        printing = printing.astype(np.float64)
        hotend_fan = ((nozzle_temp_c - ambient_c) > 20.0).astype(np.float64) * self.hotend_fan_w
        v_norm = np.clip(speed_mm_s / self.nominal_speed_mm_s, 0.0, 4.0)
        motion = printing * (self.motion_base_w + self.motion_speed_w * v_norm) * motion_scale
        extruder = printing * self.extruder_w * np.clip(extrusion_ratio, 0.0, 4.0) * extruder_scale
        part_fan = printing * self.part_fan_w
        return ((self.electronics_standby_w + heater_power_w + hotend_fan + motion + extruder
                 + part_fan) * total_scale)


@dataclass
class MaterialModel:
    """Road-geometry deposition model (6), (7)."""

    line_width_mm: float
    layer_height_mm: float
    density_g_cm3: float
    filament_diameter_mm: float

    @classmethod
    def from_config(cls, cfg: MaterialConfig) -> "MaterialModel":
        return cls(cfg.line_width_mm, cfg.layer_height_mm, cfg.density_g_cm3,
                   cfg.filament_diameter_mm)

    def deposition_rate_mm3_s(self, speed_mm_s: np.ndarray, extrusion_scale=1.0) -> np.ndarray:
        """Deposited road volume rate (6) [mm^3/s]."""
        return self.line_width_mm * self.layer_height_mm * speed_mm_s * extrusion_scale

    def mass_rate_g_s(self, deposition_rate_mm3_s: np.ndarray) -> np.ndarray:
        """Deposited mass rate (7) [g/s]."""
        return deposition_rate_mm3_s * self.density_g_cm3 / 1000.0

    def filament_length_rate_mm_s(self, deposition_rate_mm3_s: np.ndarray) -> np.ndarray:
        """Feedstock advance rate [mm/s] implied by conservation of mass."""
        area = np.pi * (self.filament_diameter_mm / 2.0) ** 2
        return deposition_rate_mm3_s / area

@dataclass
class JobGenerator:
    """Stochastic print-job generator (durations, layers, speeds, part volumes)."""

    duration_min_s: float
    duration_max_s: float
    layers_min: int
    layers_max: int
    volume_min_mm3: float
    volume_max_mm3: float
    speed_min_mm_s: float
    speed_max_mm_s: float
    duration_jitter_frac: float

    @classmethod
    def from_config(cls, cfg: JobConfig) -> "JobGenerator":
        return cls(cfg.duration_min_s, cfg.duration_max_s, cfg.layers_min, cfg.layers_max,
                   cfg.volume_min_mm3, cfg.volume_max_mm3, cfg.speed_min_mm_s,
                   cfg.speed_max_mm_s, cfg.duration_jitter_frac)

    def sample(self, n: int, rng: np.random.Generator,
               first_job_index: int = 0, aligned_start: bool = False) -> dict[str, np.ndarray]:
        """Draw ``n`` job descriptors.

        With ``aligned_start`` the elapsed time is 0 for every job (a cold fleet that
        starts together); otherwise elapsed is uniform over the realised duration so a
        fleet launched at t = 0 is in a mixed phase of life, which is what makes
        fleet-level utilisation statistics meaningful.
        """
        duration = rng.uniform(self.duration_min_s, self.duration_max_s, size=n)
        realised = np.maximum(duration * (1.0 + rng.normal(0.0, self.duration_jitter_frac, size=n)), 60.0)
        layers = rng.integers(self.layers_min, self.layers_max + 1, size=n).astype(np.float64)
        speed = rng.uniform(self.speed_min_mm_s, self.speed_max_mm_s, size=n)
        volume = rng.uniform(self.volume_min_mm3, self.volume_max_mm3, size=n)
        elapsed = np.zeros(n) if aligned_start else rng.uniform(0.0, realised, size=n)
        return {
            "job_index": first_job_index + np.arange(n, dtype=np.int64),
            "job_duration_s": realised,
            "job_elapsed_s": elapsed,
            "job_layers": layers,
            "job_speed_mm_s": speed,
            "job_volume_mm3": volume,
            "progress": np.clip(elapsed / realised, 0.0, 1.0),
        }
