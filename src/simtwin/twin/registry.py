"""Device-twin state model and twin registry.

Each simulated device has a twin holding the state aspects that the digital-twin
literature separates (Grieves; Tao et al.; ISO 23247):

``reported_state``
    What the twin believes the device is doing.  Written **only** by messages the
    transport delivered, never by the device model directly.
``desired_state``
    What the fleet controller wants the device to do (command side of the twin).
``configuration``
    Configuration the twin has last confirmed to the device.
``connectivity``
    Link state as observed by the registry (last delivery, last will).

Synchronisation quantities
--------------------------
``sync_delay_s``   ``t_delivered - t_generated`` for an accepted message.
``staleness_s(t)`` ``t - t_last_accepted``: age of information at the twin
                   (Kaul et al.; Yates et al.).
``status``         ``ONLINE`` below the staleness threshold, ``STALE`` up to the
                   offline threshold, ``OFFLINE`` beyond it or on a last will.
``resync_count``   full snapshot re-synchronisations, i.e. reconnect recoveries.

The registry adds fleet-level accounting: staleness area (time-integral of the
number of stale twins), synchronisation-delay percentiles, and resynchronisation
counts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..config import TwinConfig
from ..communication.message import (ALERTS, COMMAND, CONFIGURATION, HEALTH, LWT,
                                     STATE, TELEMETRY, Message)

STATUS_ONLINE = "ONLINE"
STATUS_STALE = "STALE"
STATUS_OFFLINE = "OFFLINE"


@dataclass
class DeviceTwin:
    """The digital twin of one device."""

    printer_id: str
    fleet_id: str
    firmware: str = "SimTwin-FW 1.0.0"
    desired_state: str = "IDLE"
    reported_state: str = "OFFLINE"
    configuration: dict[str, Any] = field(default_factory=dict)
    connectivity: str = STATUS_OFFLINE
    health_score: float = 1.0
    fault_code: str | None = None
    current_job: dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0
    nozzle_temp_c: float = 25.0
    bed_temp_c: float = 25.0
    chamber_temp_c: float = 25.0
    power_w: float = 0.0
    material_used_g: float = 0.0
    t_last_accepted: float = float("-inf")
    updates_accepted: int = 0
    updates_received_by_kind: dict[str, int] = field(default_factory=dict)
    resync_count: int = 0
    last_sync_delay_s: float = 0.0
    last_command_ack: dict[str, Any] = field(default_factory=dict)

    def staleness_s(self, t_s: float) -> float:
        """Age of the twin's information at simulated time ``t_s``."""
        if self.t_last_accepted == float("-inf"):
            return float("inf")
        return t_s - self.t_last_accepted

    def status(self, t_s: float, cfg: TwinConfig) -> str:
        st = self.staleness_s(t_s)
        if st == float("inf") or st > cfg.offline_threshold_s:
            return STATUS_OFFLINE
        if st > cfg.staleness_threshold_s:
            return STATUS_STALE
        return STATUS_ONLINE

    def apply(self, msg: Message, cfg: TwinConfig) -> None:
        """Apply one delivered message to the twin (the only write path)."""
        p = msg.payload
        kind = msg.kind
        self.updates_accepted += 1
        self.updates_received_by_kind[kind] = self.updates_received_by_kind.get(kind, 0) + 1
        self.t_last_accepted = msg.t_delivered if msg.t_delivered is not None else msg.t_generated
        self.last_sync_delay_s = self.t_last_accepted - msg.t_generated

        if kind == TELEMETRY:
            self.reported_state = p["state"]
            self.progress = p["progress"]
            self.nozzle_temp_c = p["nozzle_temperature_c"]
            self.bed_temp_c = p["bed_temperature_c"]
            self.chamber_temp_c = p["chamber_temperature_c"]
            self.power_w = p["power_w"]
            self.material_used_g = p["material_used_g"]
            self.health_score = p["health_score"]
            self.fault_code = p.get("fault_code")
            self.current_job = dict(p.get("job", {}))
        elif kind == STATE:
            self.reported_state = p["state"]
        elif kind == HEALTH:
            self.health_score = p["health_score"]
            self.fault_code = p.get("fault_code")
        elif kind == ALERTS:
            self.fault_code = p.get("fault_code")
        elif kind == LWT:
            self.connectivity = STATUS_OFFLINE
            self.reported_state = p.get("last_state", self.reported_state)
        elif kind == COMMAND:
            self.last_command_ack = dict(p)
        elif kind == CONFIGURATION:
            self.configuration.update(p)
        self.connectivity = self.status(self.t_last_accepted, cfg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "printer_id": self.printer_id,
            "fleet_id": self.fleet_id,
            "firmware": self.firmware,
            "desired_state": self.desired_state,
            "reported_state": self.reported_state,
            "connectivity": self.connectivity,
            "health_score": self.health_score,
            "fault_code": self.fault_code,
            "progress": self.progress,
            "nozzle_temperature_c": self.nozzle_temp_c,
            "bed_temperature_c": self.bed_temp_c,
            "chamber_temperature_c": self.chamber_temp_c,
            "power_w": self.power_w,
            "material_used_g": self.material_used_g,
            "t_last_accepted": self.t_last_accepted,
            "updates_accepted": self.updates_accepted,
            "resync_count": self.resync_count,
            "staleness_s": self.staleness_s,
            "current_job": dict(self.current_job),
            "configuration": dict(self.configuration),
            "last_command_ack": dict(self.last_command_ack),
        }


class TwinRegistry:
    """Fleet-level collection of twins plus synchronisation accounting."""

    def __init__(self, fleet_id: str, printer_ids: list[str], cfg: TwinConfig,
                 firmwares: list[str] | None = None):
        self.cfg = cfg
        self.fleet_id = fleet_id
        self.printer_ids = printer_ids
        firmwares = firmwares or ["SimTwin-FW 1.0.0"] * len(printer_ids)
        self.twins: dict[str, DeviceTwin] = {
            pid: DeviceTwin(printer_id=pid, fleet_id=fleet_id, firmware=fw)
            for pid, fw in zip(printer_ids, firmwares)
        }
        self._n = len(printer_ids)
        self._stale_area_s = 0.0
        self._offline_area_s = 0.0
        self._sampled_s = 0.0
        self._peak_stale = 0
        self._sync_delays: list[float] = []
        self._staleness_samples: list[float] = []
        self._resyncs = 0

    # -- write path ----------------------------------------------------------
    def apply(self, msg: Message) -> None:
        twin = self.twins.get(msg.printer_id)
        if twin is None:  # pragma: no cover - defensive
            return
        if msg.kind == TELEMETRY and msg.replayed:
            twin.resync_count += 1
            self._resyncs += 1
        twin.apply(msg, self.cfg)
        if msg.t_delivered is not None:
            self._sync_delays.append((msg.t_delivered - msg.t_generated) * 1000.0)

    def set_desired_state(self, printer_id: str, state: str) -> None:
        twin = self.twins.get(printer_id)
        if twin is not None:
            twin.desired_state = state

    # -- periodic accounting --------------------------------------------------
    def sample(self, t_s: float, dt_s: float) -> dict[str, int]:
        """Update staleness-area accounting; call once per simulated timestep."""
        stale = offline = 0
        peak = 0.0
        for twin in self.twins.values():
            st = twin.staleness_s(t_s)
            if st == float("inf"):
                offline += 1
            else:
                peak = max(peak, st)
                if st > self.cfg.offline_threshold_s:
                    offline += 1
                elif st > self.cfg.staleness_threshold_s:
                    stale += 1
        self._stale_area_s += stale * dt_s
        self._offline_area_s += offline * dt_s
        self._sampled_s += dt_s
        self._peak_stale = max(self._peak_stale, stale + offline)
        self._staleness_samples.append(peak)
        return {"stale_twins": stale, "offline_twins": offline}

    # -- read path -----------------------------------------------------------
    def staleness_array(self, t_s: float) -> np.ndarray:
        """Staleness of every twin at ``t_s`` (never-seen twins reported as 0)."""
        out = np.empty(self._n)
        for i, pid in enumerate(self.printer_ids):
            st = self.twins[pid].staleness_s(t_s)
            out[i] = 0.0 if st == float("inf") else st
        return out

    def status_counts(self, t_s: float) -> dict[str, int]:
        counts = {STATUS_ONLINE: 0, STATUS_STALE: 0, STATUS_OFFLINE: 0}
        for twin in self.twins.values():
            counts[twin.status(t_s, self.cfg)] += 1
        return counts

    def counters(self) -> dict[str, float]:
        delays = np.asarray(self._sync_delays, dtype=np.float64)
        stales = np.asarray(self._staleness_samples, dtype=np.float64)
        return {
            "twins": self._n,
            "updates_accepted": int(sum(t.updates_accepted for t in self.twins.values())),
            "resynchronisations": self._resyncs,
            "twin_staleness_area_s": self._stale_area_s,
            "twin_offline_area_s": self._offline_area_s,
            "max_concurrently_stale_twins": self._peak_stale,
            # Time-average number of twins in each synchronisation state.
            "mean_stale_twins": self._stale_area_s / max(self._sampled_s, 1e-9),
            "mean_offline_twins": self._offline_area_s / max(self._sampled_s, 1e-9),
            # Worst-twin staleness across the run: the age-of-information signal
            # that the binary stale/offline counters above threshold on.
            "twin_staleness_p50_s": float(np.percentile(stales, 50)) if stales.size else 0.0,
            "twin_staleness_p95_s": float(np.percentile(stales, 95)) if stales.size else 0.0,
            "twin_staleness_max_s": float(stales.max()) if stales.size else 0.0,
            "sync_delay_ms_mean": float(delays.mean()) if delays.size else 0.0,
            "sync_delay_ms_p95": float(np.percentile(delays, 95)) if delays.size else 0.0,
            "sync_delay_ms_p99": float(np.percentile(delays, 99)) if delays.size else 0.0,
            "sync_delay_ms_max": float(delays.max()) if delays.size else 0.0,
        }

    def snapshot(self, t_s: float) -> list[dict[str, Any]]:
        """Full twin-state snapshot (used by the twin-state dataset)."""
        out = []
        for pid in self.printer_ids:
            twin = self.twins[pid]
            d = twin.to_dict()
            st = twin.staleness_s(t_s)
            d["staleness_s"] = float("nan") if st == float("inf") else st
            d["status"] = twin.status(t_s, self.cfg)
            out.append(d)
        return out

