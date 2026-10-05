"""Transport abstraction and the deterministic in-process transport.

The transport is where SimTwin's cyber-physical character lives: a device's twin is
updated *only* through messages that survive the delivery-semantics pipeline, so
network behaviour is a first-class object of the simulation rather than an
assumption in the analysis.

Delivery-semantics pipeline (applied per message, in this order)
----------------------------------------------------------------
1. **Device outage.**  If the device's link is down when the message is generated,
   the message is appended to the device's replay queue (bounded by
   ``replay_queue_limit``) and is *not* counted as generated-and-lost.  On
   reconnect the queue is replayed, oldest first, and messages older than
   ``max_message_age_s`` at delivery are dropped as ``stale``.
2. **Broker outage.**  If the broker is down at delivery time the message is
   dropped with reason ``broker_outage`` (QoS 0 semantics: no persistence).
3. **Loss.**  Bernoulli(``loss_probability``) independent thinning; reason ``loss``.
4. **Latency.**  ``L = base + |N(0, jitter_std)| * exp(sigma * N(0, 1))``, i.e. a
   deterministic floor, symmetric jitter, and a lognormal tail that reproduces the
   heavy right tail observed on real publish/subscribe infrastructure.
5. **Duplicates.**  With probability ``duplicate_probability`` a QoS >= 1 message is
   delivered a second time (at-least-once semantics).

All randomness is drawn from a seeded stream, so a run is fully reproducible.
"""
from __future__ import annotations

import heapq
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field

import numpy as np

from ..config import NetworkConfig
from .message import Message


class Transport(ABC):
    """Publish/subscribe transport interface."""

    @abstractmethod
    def publish(self, msg: Message) -> None: ...

    @abstractmethod
    def step(self, t_s: float) -> list[Message]:
        """Advance the transport to simulated time ``t_s``; return delivered messages."""

    def flush(self, t_s: float) -> list[Message]:
        """Deliver everything still in flight at the end of a run.

        The in-process transport releases everything it holds inside :meth:`step`,
        so the default is a no-op.  Asynchronous transports must block until their
        network thread has observed every published message, otherwise the tail of
        the run is silently attributed to loss.
        """
        return []

    @abstractmethod
    def is_online(self, printer_index: int, t_s: float) -> bool: ...

    def close(self) -> None:  # pragma: no cover - trivial default
        return None

    def counters(self) -> dict[str, float]:
        return dict(self._counters)

    _counters: dict[str, float] = {}


@dataclass
class ConnectivityModel:
    """Per-device disconnection episodes and broker-wide outage episodes.

    Episodes are generated lazily from a seeded stream: each device carries its own
    ``next_outage_at`` / ``offline_until`` scalars, which the engine advances in a
    vectorised step.  This keeps connectivity evaluation O(n) per timestep for the
    whole fleet and O(1) per message.
    """

    config: NetworkConfig
    n_devices: int
    next_outage_at: np.ndarray
    offline_until: np.ndarray
    #: Number of consecutive reconnect attempts that failed (for backoff reporting).
    reconnect_attempts: np.ndarray
    broker_next_outage_at: float = np.inf
    broker_offline_until: float = -np.inf
    #: Total scheduled device outage episodes (for metadata).
    scheduled_device_outages: int = 0
    scheduled_broker_outages: int = 0

    @classmethod
    def build(cls, cfg: NetworkConfig, n_devices: int, rng: np.random.Generator,
             duration_s: float) -> "ConnectivityModel":
        if cfg.mean_outage_interval_s > 0:
            first = rng.exponential(cfg.mean_outage_interval_s, size=n_devices)
            n_ep = int(np.ceil(duration_s / max(cfg.mean_outage_interval_s, 1e-9))) + 1
            scheduled = n_devices * n_ep
        else:
            first = np.full(n_devices, np.inf)
            scheduled = 0
        broker_first = (rng.exponential(cfg.mean_broker_outage_interval_s)
                        if cfg.mean_broker_outage_interval_s > 0 else np.inf)
        return cls(config=cfg, n_devices=n_devices, next_outage_at=first,
                   offline_until=np.full(n_devices, -np.inf),
                   reconnect_attempts=np.zeros(n_devices, dtype=np.int64),
                   broker_next_outage_at=float(broker_first),
                   scheduled_device_outages=scheduled,
                   scheduled_broker_outages=(
                       int(np.ceil(duration_s / max(cfg.mean_broker_outage_interval_s, 1e-9))) + 1
                       if cfg.mean_broker_outage_interval_s > 0 else 0))

    def step(self, t_s: float, rng: np.random.Generator) -> None:
        """Advance episode schedules to ``t_s`` (vectorised over devices)."""
        cfg = self.config
        if cfg.mean_outage_interval_s > 0:
            due = np.nonzero((t_s >= self.next_outage_at) & (t_s >= self.offline_until))[0]
            if due.size:
                k = int(due.size)
                dur = rng.uniform(cfg.outage_duration_min_s, cfg.outage_duration_max_s, size=k)
                backoff = rng.exponential(cfg.reconnect_backoff_base_s, size=k)
                self.offline_until[due] = t_s + dur + backoff
                self.next_outage_at[due] = self.offline_until[due] + rng.exponential(
                    cfg.mean_outage_interval_s, size=k)
                self.reconnect_attempts[due] += 1
        if cfg.mean_broker_outage_interval_s > 0 and t_s >= self.broker_next_outage_at \
                and t_s >= self.broker_offline_until:
            dur = rng.uniform(cfg.outage_duration_min_s, cfg.outage_duration_max_s)
            self.broker_offline_until = t_s + dur
            self.broker_next_outage_at = self.broker_offline_until + rng.exponential(
                cfg.mean_broker_outage_interval_s)

    def online_mask(self, t_s: float) -> np.ndarray:
        """Boolean link state of every device at ``t_s``."""
        return (t_s >= self.offline_until) & (t_s >= self.broker_offline_until)

    def broker_online(self, t_s: float) -> bool:
        return t_s >= self.broker_offline_until



class InProcessTransport(Transport):
    """Deterministic, dependency-free transport implementing the full pipeline.

    Default transport for the experiments: no broker required, bit-reproducible from
    the seed, and the same interface as the real MQTT adapter, so an experiment can
    be re-run over a broker without touching model code.
    """

    def __init__(self, cfg: NetworkConfig, connectivity: ConnectivityModel,
                rng: np.random.Generator, qos: int = 0):
        self.cfg = cfg
        self.connectivity = connectivity
        self.rng = rng
        self.qos = qos
        self._heap: list[tuple[float, int, Message]] = []
        self._heap_seq = 0
        self._queues: dict[int, deque[Message]] = {}
        self._counters = {
            "generated": 0, "delivered": 0, "dropped_loss": 0, "dropped_stale": 0,
            "dropped_broker": 0, "duplicates": 0, "queued_for_replay": 0,
            "replayed": 0, "dropped_queue_overflow": 0,
            "latency_ms_sum": 0.0, "latency_ms_max": 0.0,
        }
        self._latencies: list[float] = []

    # -- publishing ----------------------------------------------------------
    def publish(self, msg: Message) -> None:
        """Apply step 1 of the pipeline (device-link outage -> replay queue)."""
        self._counters["generated"] += 1
        idx = int(msg.printer_id.rsplit("p", 1)[-1])
        if not self.is_online(idx, msg.t_generated):
            q = self._queues.setdefault(idx, deque())
            if len(q) >= self.cfg.replay_queue_limit:
                q.popleft()
                self._counters["dropped_queue_overflow"] += 1
            q.append(msg)
            self._counters["queued_for_replay"] += 1
            return
        self._release(msg, msg.t_generated, replayed=False)

    def _release(self, msg: Message, t_now: float, *, replayed: bool) -> None:
        """Apply loss, latency and duplication (pipeline steps 3-5)."""
        cfg = self.cfg
        if cfg.loss_probability > 0.0 and self.rng.random() < cfg.loss_probability:
            self._counters["dropped_loss"] += 1
            return
        latency = self._draw_latency_s()
        t_deliver = t_now + latency
        if t_deliver - msg.t_generated > cfg.max_message_age_s:
            self._counters["dropped_stale"] += 1
            return
        msg.t_delivered = t_deliver
        msg.replayed = replayed
        self._push(t_deliver, msg)
        if self.qos >= 1 and cfg.duplicate_probability > 0.0 \
                and self.rng.random() < cfg.duplicate_probability:
            self._push(t_deliver + latency, msg, duplicate=True)

    def _draw_latency_s(self) -> float:
        cfg = self.cfg
        jitter = abs(self.rng.normal(0.0, cfg.jitter_std_ms / 1000.0))
        if cfg.jitter_tail_sigma > 0.0:
            jitter *= float(np.exp(self.rng.normal(0.0, cfg.jitter_tail_sigma)))
        return cfg.base_latency_ms / 1000.0 + jitter

    def _push(self, t_deliver: float, msg: Message, *, duplicate: bool = False) -> None:
        self._heap_seq += 1
        heapq.heappush(self._heap, (t_deliver, self._heap_seq, msg))
        if duplicate:
            self._counters["duplicates"] += 1

    # -- consuming -----------------------------------------------------------
    def step(self, t_s: float) -> list[Message]:
        """Deliver everything due at ``t_s``, then replay reconnecting devices' queues."""
        self.connectivity.step(t_s, self.rng)
        out: list[Message] = []
        heap = self._heap
        while heap and heap[0][0] <= t_s:
            t_deliver, _, msg = heapq.heappop(heap)
            if not self.connectivity.broker_online(t_deliver):
                self._counters["dropped_broker"] += 1
                continue
            self._counters["delivered"] += 1
            lat = (t_deliver - msg.t_generated) * 1000.0
            self._counters["latency_ms_sum"] += lat
            if lat > self._counters["latency_ms_max"]:
                self._counters["latency_ms_max"] = lat
            self._latencies.append(lat)
            out.append(msg)
        mask = self.connectivity.online_mask(t_s)
        for idx, q in self._queues.items():
            if not q or not mask[idx]:
                continue
            while q:
                msg = q.popleft()
                if t_s - msg.t_generated > self.cfg.max_message_age_s:
                    self._counters["dropped_stale"] += 1
                    continue
                self._counters["replayed"] += 1
                self._release(msg, t_s, replayed=True)
        return out

    def is_online(self, printer_index: int, t_s: float) -> bool:
        return bool(self.connectivity.online_mask(t_s)[printer_index])

    def latency_array(self) -> np.ndarray:
        """All observed delivery latencies in ms (for percentile analysis)."""
        return np.asarray(self._latencies, dtype=np.float64)

    def close(self) -> None:
        return None
