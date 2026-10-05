"""Message envelope and topic scheme.

Topic scheme
------------
All topics are rooted at a configurable prefix (default ``simtwin``)::

    {prefix}/{fleet_id}/{printer_id}/telemetry     device -> twin   periodic state
    {prefix}/{fleet_id}/{printer_id}/state         device -> twin   state-machine event
    {prefix}/{fleet_id}/{printer_id}/health        device -> twin   health/wear update
    {prefix}/{fleet_id}/{printer_id}/alerts        device -> twin   fault alert
    {prefix}/{fleet_id}/{printer_id}/command       twin   -> device desired-state command
    {prefix}/{fleet_id}/{printer_id}/configuration twin  -> device configuration push
    {prefix}/{fleet_id}/{printer_id}/lwt           broker  -> twin  MQTT Last Will

The ``lwt`` topic carries the MQTT Last Will and Testament: a retained message the
broker publishes on ungraceful disconnect, which is how the twin registry learns
that a device is unreachable without polling.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TELEMETRY = "telemetry"
STATE = "state"
HEALTH = "health"
ALERTS = "alerts"
COMMAND = "command"
CONFIGURATION = "configuration"
LWT = "lwt"

TOPIC_KINDS: tuple[str, ...] = (TELEMETRY, STATE, HEALTH, ALERTS, COMMAND, CONFIGURATION, LWT)


def topic(prefix: str, fleet_id: str, printer_id: str, kind: str) -> str:
    """Build a concrete topic string."""
    if kind not in TOPIC_KINDS:
        raise ValueError(f"unknown topic kind {kind!r}")
    return f"{prefix}/{fleet_id}/{printer_id}/{kind}"


def topic_suffix(prefix: str, fleet_id: str, kind: str) -> str:
    """Build a wildcard subscription filter for one topic kind across a fleet."""
    return f"{prefix}/{fleet_id}/+/{kind}"


@dataclass
class Message:
    """One published message with its delivery bookkeeping.

    ``t_generated`` and ``t_delivered`` are *simulated* timestamps in seconds from
    the start of the run.  The twin synchronisation delay is
    ``t_delivered - t_generated``, i.e. the transport delay the twin observes; the
    twin *staleness* at simulated time ``t`` is ``t - t_delivered``.
    """

    seq: int
    topic: str
    kind: str
    printer_id: str
    payload: dict[str, Any]
    t_generated: float
    qos: int = 0
    retained: bool = False
    #: Simulated time at which the transport released the message to subscribers.
    t_delivered: float | None = None
    #: True when the message was replayed from a device-side queue after a disconnect.
    replayed: bool = False
    #: True when this delivery is a duplicate of an earlier delivery (QoS >= 1).
    duplicate: bool = False
    #: True when the message was dropped (loss, stale, or broker outage).
    dropped: bool = False
    drop_reason: str = ""

    def latency_ms(self) -> float:
        if self.t_delivered is None:
            raise ValueError("message not delivered")
        return (self.t_delivered - self.t_generated) * 1000.0

    def to_envelope(self) -> dict[str, Any]:
        """JSON-ready envelope (the payload is nested, metadata stays in the topic)."""
        return {
            "seq": self.seq,
            "topic": self.topic,
            "kind": self.kind,
            "printer_id": self.printer_id,
            "t_generated": self.t_generated,
            "qos": self.qos,
            "retained": self.retained,
            "payload": self.payload,
        }
