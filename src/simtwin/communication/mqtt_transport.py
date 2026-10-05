"""Real-broker MQTT transport (paho-mqtt).

This adapter replaces the in-process transport with a genuine publish/subscribe
round trip through an MQTT broker.  It exists for one reason: the paper's
network-impairment results are only credible if the delivery-semantics pipeline is
an abstraction over a *real* transport, not merely a simulation of one.

Design
------
* Two paho clients are used: a **publisher** (the device side) and a
  **subscriber** (the twin side).  Separating them means messages really do leave
  the process and come back, so broker queueing, QoS handshakes and retained
  Last-Will messages are exercised.
* The **Last Will and Testament** is registered on the publisher client before
  connection, on the ``lwt`` topic, retained.  This is the mechanism by which the
  twin registry learns a device became unreachable without polling.
* Delivery is **asynchronous**: paho's network thread appends to a thread-safe
  deque, and :meth:`step` drains that deque at the current simulated time.
  ``t_delivered`` is therefore the simulated time at which the twin *observed* the
  message, which is exactly the quantity the staleness metric needs.
* :class:`ConnectivityModel` still governs device-link and broker episodes, so the
  same impairment configuration drives both transports and results are comparable.
* Counters use the same names as :class:`InProcessTransport`, so every downstream
  metric and table works unchanged over either transport.

Latency measured over this transport is real broker latency observed on the
simulated clock, so it is not bit-reproducible the way the in-process transport is.
That is the point: E6 establishes reproducibility for the deterministic transport,
and this adapter establishes that the deterministic transport corresponds to a real
broker.
"""
from __future__ import annotations

import json
import threading
import time
from collections import deque

import numpy as np

from ..config import MqttConfig, NetworkConfig
from .message import LWT, TELEMETRY, Message, topic, topic_suffix
from .transport import ConnectivityModel, InProcessTransport, Transport

_MESSAGE_KINDS = (TELEMETRY, "state", "health", "alerts", "command",
                  "configuration", LWT)


class MqttTransport(Transport):
    """Publish/subscribe transport backed by a real MQTT broker.

    Parameters
    ----------
    cfg, connectivity:
        Same network configuration and episode model as the in-process transport.
    rng:
        Unused; present so the constructor signature matches the other transports.
    mqtt:
        Broker endpoint, QoS, topic prefix and shutdown drain budget.
    fleet_id:
        Fleet identifier used to build topic filters.
    """

    def __init__(self, cfg: NetworkConfig, connectivity: ConnectivityModel,
                 rng: np.random.Generator, mqtt: MqttConfig, fleet_id: str,
                 qos: int | None = None):
        import paho.mqtt.client as mqtt_lib  # local import: optional dependency

        self.cfg = cfg
        self.mqtt = mqtt
        self.connectivity = connectivity
        self.fleet_id = fleet_id
        self.prefix = mqtt.topic_prefix
        self.qos = mqtt.qos if qos is None else qos
        self._lib = mqtt_lib
        self._rng = np.random.default_rng(0)  # broker path is not seed-reproducible

        self._incoming: deque = deque()
        self._lock = threading.Lock()
        self._published = 0
        self._received = 0

        self._publisher = self._make_client(f"{fleet_id}-pub")
        self._publisher.will_set(
            topic(self.prefix, fleet_id, f"{fleet_id}-p000000", LWT),
            payload=json.dumps({"reason": "ungraceful_disconnect"}),
            qos=1, retain=True)
        self._subscriber = self._make_client(f"{fleet_id}-sub")
        self._subscriber.on_message = self._on_message

        self._publisher.connect(mqtt.host, mqtt.port, mqtt.keepalive_s)
        self._publisher.loop_start()
        self._subscriber.connect(mqtt.host, mqtt.port, mqtt.keepalive_s)
        for kind in _MESSAGE_KINDS:
            self._subscriber.subscribe(topic_suffix(self.prefix, fleet_id, kind),
                                       qos=self.qos)
        self._subscriber.loop_start()

        self._counters = {
            "generated": 0, "delivered": 0, "dropped_loss": 0, "dropped_stale": 0,
            "dropped_broker": 0, "duplicates": 0, "queued_for_replay": 0,
            "replayed": 0, "dropped_queue_overflow": 0,
            "latency_ms_sum": 0.0, "latency_ms_max": 0.0,
        }
        self._latencies: list[float] = []

    # -- clients ---------------------------------------------------------------
    def _make_client(self, client_id: str):
        lib = self._lib
        return lib.Client(lib.CallbackAPIVersion.VERSION2, client_id=client_id,
                          clean_session=self.mqtt.clean_session,
                          protocol=lib.MQTTv311)

    def _on_message(self, _client, _userdata, message) -> None:
        with self._lock:
            self._incoming.append(message)
            self._received += 1

    # -- publishing ------------------------------------------------------------
    def publish(self, msg: Message) -> None:
        """Publish one message to the broker; a down device link drops it first."""
        self._counters["generated"] += 1
        idx = int(msg.printer_id.rsplit("p", 1)[-1])
        if not self.is_online(idx, msg.t_generated):
            self._counters["dropped_loss"] += 1
            msg.dropped = True
            msg.drop_reason = "device_outage"
            return
        if msg.kind == LWT:
            return  # the will is registered on the client, never published directly
        info = self._publisher.publish(msg.topic, json.dumps(msg.to_envelope()),
                                       qos=msg.qos, retain=msg.retained)
        if msg.qos > 0:
            info.wait_for_publish(timeout=self.mqtt.drain_timeout_s)
        self._published += 1

    # -- consuming -------------------------------------------------------------
    def step(self, t_s: float) -> list[Message]:
        """Deliver every broker message observed by simulated time ``t_s``."""
        self.connectivity.step(t_s, self._rng)
        with self._lock:
            batch = list(self._incoming)
            self._incoming.clear()
        out: list[Message] = []
        for raw in batch:
            msg = _envelope_to_message(json.loads(raw.payload.decode("utf-8")))
            msg.t_delivered = t_s
            out.append(msg)
            self._counters["delivered"] += 1
            lat = (t_s - msg.t_generated) * 1000.0
            self._counters["latency_ms_sum"] += lat
            if lat > self._counters["latency_ms_max"]:
                self._counters["latency_ms_max"] = lat
            self._latencies.append(lat)
        return out

    def is_online(self, printer_index: int, t_s: float) -> bool:
        return bool(self.connectivity.online_mask(t_s)[printer_index])

    def latency_array(self) -> np.ndarray:
        return np.asarray(self._latencies, dtype=np.float64)

    def drain(self, timeout_s: float | None = None) -> int:
        """Block until every published message has been received.

        Returns the number still outstanding when the timeout expired.
        """
        deadline = time.monotonic() + (self.mqtt.drain_timeout_s
                                       if timeout_s is None else timeout_s)
        while time.monotonic() < deadline:
            with self._lock:
                outstanding = self._published - self._received
            if outstanding <= 0:
                return 0
            time.sleep(0.005)
        with self._lock:
            return max(self._published - self._received, 0)

    def flush(self, t_s: float) -> list[Message]:
        """Deliver every in-flight message at the final simulated time.

        The simulated clock runs far ahead of the wall clock (the fleet engine is
        thousands of times faster than real time), so a broker transport always has
        a backlog at the end of a run.  Draining it at ``t_s`` attributes those
        messages to *latency*, which is what a real subscriber would observe,
        instead of to loss, which it is not.
        """
        out: list[Message] = []
        self.drain()
        while True:
            batch = self.step(t_s)
            if not batch:
                return out
            out.extend(batch)

    def close(self) -> None:
        self.drain()
        for client in (self._publisher, self._subscriber):
            client.loop_stop()
            client.disconnect()


def _envelope_to_message(envelope: dict) -> Message:
    """Rebuild a :class:`Message` from a JSON envelope received off the wire."""
    return Message(seq=envelope["seq"], topic=envelope["topic"],
                   kind=envelope["kind"], printer_id=envelope["printer_id"],
                   payload=envelope["payload"], t_generated=envelope["t_generated"],
                   qos=envelope["qos"], retained=envelope["retained"])


def build_transport(cfg, connectivity: ConnectivityModel,
                    rng: np.random.Generator) -> Transport:
    """Return the transport selected by ``cfg.mqtt.enabled``.

    Keeping the choice in one place means the fleet engine never branches on the
    transport type, and an experiment can switch brokers with a config flag.
    """
    if cfg.mqtt.enabled:
        return MqttTransport(cfg.network, connectivity, rng, cfg.mqtt,
                             cfg.fleet.fleet_id, qos=cfg.mqtt.qos)
    return InProcessTransport(cfg.network, connectivity, rng, qos=cfg.mqtt.qos)
