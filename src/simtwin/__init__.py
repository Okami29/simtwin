"""SimTwin: an open-source digital twin simulator for networked FDM/FFF fleets.

SimTwin models fleets of network-connected fused-filament-fabrication printers as
virtual cyber-physical devices: each virtual printer carries an internal physical
state (thermal masses, motion, material, energy), emits structured telemetry over a
publish/subscribe transport, and is mirrored by a digital twin that applies realistic
message-delivery semantics (latency, jitter, loss, disconnection, reconnect,
queue-and-replay).

The package is deliberately *not* a high-fidelity physics simulator. It targets the
cyber-physical / IIoT layer: operational state, telemetry, twin synchronisation,
fault injection, communication failure, fleet behaviour, and reproducible labelled
dataset generation.

Modules
-------
config          Configuration dataclasses, YAML loading, validation.
printer         Thermal, power, material and process models; printer state machine.
faults          Fault catalogue and vectorised fault injection.
communication   In-process message bus, MQTT adapter, delivery-semantics pipeline.
twin            Digital twin registry and synchronisation logic.
fleet           The vectorised fleet simulation engine.
metrics         Metric accumulation (latency, throughput, delivery ratio, staleness).
storage         Dataset writers (CSV, JSONL, Parquet) and run metadata.
utilities       Seeding, environment detection, logging.
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
