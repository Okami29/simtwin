# SimTwin

**A reproducible, open-source digital-twin simulator for networked FDM/FFF
additive-manufacturing fleets.**

SimTwin simulates a fleet of fused-filament printers, the network that connects
them, and the digital twins that observe them — and it makes the *gap* between
those three things measurable.

The core claim of a digital twin is that the twin tracks the asset. Most
"digital twin" simulators assume that gap away: telemetry appears in the twin the
instant it is generated, and a fault is a label attached to a row. SimTwin refuses
to do that. A twin is updated **only** by messages that survive an explicit
delivery pipeline, and faults are **mechanisms** that act on the plant, not on the
record. Twin staleness, synchronisation delay, resynchronisation counts and
fault-signature separability are therefore *outcomes* of the model, not inputs to
it.

MIT licensed · Python 3.11+ · NumPy-vectorised · 42 tests (5 against a live MQTT broker)

---

## What it models

**Device side (physics).** Three coupled first-order thermal nodes (nozzle, bed,
chamber) under PI control, an additive subsystem power model (heaters, motors,
electronics, fan), a road-geometry deposition model for material use, a
finite-state machine per device (`OFF → HEATING → PRINTING → DONE → IDLE`, plus
`FAIL → MAINTENANCE`), and wear that accumulates with use.

**Fault side (mechanisms).** Eleven faults in five families, each implemented as a
parameter perturbation on the plant — heater efficiency, thermal conductance,
parasitic heat load, PID gain, extrusion scale, motor/power scale, sensor bias and
noise, and terminal job interruption. A fault changes what the physics does; the
telemetry then reports what the physics did.

**Network side (delivery semantics).** Every message passes through an ordered
pipeline: device outage → replay queue → broker outage → Bernoulli loss → latency
(floor + jitter + lognormal tail) → QoS duplicates. Per-device and broker-wide
outage episodes are configurable.

**Twin side (state).** A registry of twins, each holding reported state, desired
state, configuration, connectivity, health and bookkeeping. The *only* write path
is `apply(message)`, invoked on delivery.

Two interchangeable transports implement the same interface:

* `InProcessTransport` — deterministic, dependency-free, bit-reproducible.
* `MqttTransport` — a real round trip through an MQTT broker (Mosquitto 2.1.2,
  `paho-mqtt` 2.1.0), with separate publisher and subscriber clients and a
  retained MQTT Last Will so the registry learns of ungraceful disconnects
  without polling.

Selected by one configuration flag (`mqtt.enabled`); the fleet engine never
branches on the transport type.

---

## Quick start

```bash
git clone https://github.com/Okami29/simtwin.git && cd simtwin
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt      # pinned to the study environment
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests -q            # 41 passed
```

Simulate a fleet:

```python
from simtwin.config import SimConfig
from simtwin.fleet.engine import FleetEngine

cfg = SimConfig.default()
cfg.fleet.size = 50
cfg.simulation.duration_s = 3600.0
cfg.faults.mode = "poisson"
cfg.faults.rate_per_hour = 5.0
cfg.network.loss_probability = 0.05
cfg.validate()

art = FleetEngine(cfg).run()
print(art.metrics["realtime_factor"])          # simulated seconds per wall second
print(art.metrics["twin_staleness_p95_s"])     # 95th-pct worst-twin staleness
```

Run the full experiment suite (~15 min, 1.8 GB of artifacts):

```bash
.venv/bin/python experiments/run_all.py         # E1-E7
.venv/bin/python experiments/make_figures.py    # figures + LaTeX/Markdown tables
```

Compile the manuscript:

```bash
tectonic paper/main.tex --outdir build/         # 28 pages
```

---

## Experiments

| ID | Question | Headline result |
|---|---|---|
| **E1** | How far does it scale on a laptop? | 1,000 printers at 88,643 device-steps/s, RTF 88.6, 3.3 GB peak RSS, 3.6 M messages at 99.97 % delivery |
| **E2** | What does telemetry frequency cost? | 686 → 70,363 msg/s over a 240-fold sampling sweep; RTF falls from 412 to 176 |
| **E3** | Do loss and outages affect twins the same way? | No. Loss cuts delivery to 70 % and lifts p95 staleness to 7.0 s; outages keep delivery at 99.3 % but lift p95 staleness to 179 s and resynchronisations to 324,942 |
| **E4** | Are injected faults separable from telemetry? | 10 of 11 faults reach Cohen's d >= 1.45 on at least one channel; bed-heater failure reaches 3.68 on power. Pooled mean AUC is 0.42-0.50, i.e. near chance |
| **E5** | How do fleets recover from outages? | 98.8 % delivery, but median twin staleness 234 s and 45,131 resynchronisations |
| **E6** | Is it reproducible? | Two runs at seed 2027 give byte-identical telemetry (SHA-256 match); seed 2028 differs |
| **E7** | Does the in-process transport correspond to a real broker? | Over Mosquitto, QoS 1 holds p95 staleness at 1.2 s; QoS 0 lets it grow 12.6-fold to 15.1 s |

E3 and E7 are worth reading together: **delivery ratio and twin freshness are
measurably different quantities.** A channel can look healthy on delivery and be
unusable on freshness. Reporting only delivery ratio — which most fleet telemetry
work does — hides the failure that matters to a twin.

The E4 result has a second half that matters just as much: per-channel effect
sizes are large and mechanistically coherent, while the *pooled* classifier sits at
chance. Aggregating across channels destroys the signal, so report per-channel
effect sizes.

E7 skips itself (writing a summary row that says so) unless a broker is listening:

```bash
mosquitto -p 1883 &
.venv/bin/python experiments/run_all.py E7
```

---

## Determinism

Runs are a pure function of (configuration, seed). Randomness comes from
independent named NumPy streams spawned from a single `SeedPlan`, so adding a
consumer of randomness in one subsystem cannot shift the stream in another — the
failure mode that makes "reproducible" seeded simulations quietly non-reproducible.

E6 verifies this at the artifact level, not the summary-statistic level: two runs
at the same seed produce telemetry with identical SHA-256 digests.

The single exception is the MQTT broker transport, where latency is wall-clock.
E7 reports distributions, not digests.

---

## Layout

```
src/simtwin/
  config.py                        configuration + cross-field validation
  printer/thermal.py               coupled thermal nodes + PI control
  printer/process.py               power, deposition, job generation
  printer/states.py                device finite-state machine
  faults/catalogue.py              11 faults, 5 families, mechanism parameters
  faults/injector.py               scheduling + parameter-field construction
  communication/message.py         envelope + topic scheme (incl. LWT)
  communication/transport.py       delivery-semantics pipeline, in-process transport
  communication/mqtt_transport.py  real-broker adapter + build_transport factory
  twin/registry.py                 twin state, written only on delivery
  fleet/engine.py                  vectorised fleet loop
  storage/writers.py               CSV / JSONL / Parquet + metadata.json
  metrics/quality.py               staleness, offline area, separability
  utilities/seeds.py               SeedPlan: independent named streams
  utilities/environment.py         detected hardware/software record
experiments/run_all.py             E1-E7
experiments/make_figures.py        figures + booktabs tables
experiments/verify_bibliography.py Crossref resolution of every citation
paper/main.tex                     manuscript (elsarticle)
datasets/simtwin-v0.1/             versioned dataset + SHA-256 manifest
```

## Dataset

`datasets/simtwin-v0.1/` (52.6 MB, 15 files) carries the per-experiment summary
tables, the E4 baseline/faulted telemetry pair (864,000 rows x 20 columns), the
separability table, the E4 event log and the bibliography audit — each with a
SHA-256 digest in `manifest.json`. See `datasets/simtwin-v0.1/DATASET.md`.

Everything is synthetic. Nothing was collected from a physical machine.

## Bibliography

Every cited entry in the manuscript was resolved against the Crossref REST API by
DOI and its title compared with the returned record: **44 of 49 verified this way**.
The remaining five are standards and an industry whitepaper with no DOI assigned
(ISO 23247-1, ISO/IEC 30173, MQTT 3.1.1, MQTT 5.0, and the Grieves–Vickers digital
twin whitepaper); those were verified against their publisher's canonical page.
**All 49 cited entries are verified.** Five entries that could not be resolved at
all were **dropped** rather than cited; the reasons are recorded in
`results/bibliography_dropped.json`. Per-entry records — query, resolved title and
year, DOI status, verification method — are published in
`results/bibliography_verification.json` and as CSV, and shipped with the dataset.

The canonical repository is <https://github.com/Okami29/simtwin>; the versioned
dataset archive is `dist/simtwin-v0.1.tar.gz` and is also mirrored in
`datasets/simtwin-v0.1/`.

## Testing

```bash
.venv/bin/python -m pytest tests -q          # 42 passed
.venv/bin/python -m pytest tests -q -k mqtt  # 5 broker tests (needs mosquitto)
```

The four MQTT tests skip themselves when no broker is listening, so the suite
stays runnable on a machine without Mosquitto.

## Licence

MIT — see `LICENSE`.
