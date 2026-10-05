# Cluster C — Industrial IoT, MQTT, OPC UA, and Networked Control Performance

Search/verification date: 2026-10-05.
Verification methods: Crossref REST API (`api.crossref.org/works/<doi>`), DOI resolution
(`doi.org`), OpenAlex Graph API, local SearXNG web search, and direct retrieval of primary
standards-body pages (docs.oasis-open.org, reference.opcfoundation.org, webstore.iec.ch).
IEEE Xplore and ACM DL block automated retrieval (HTTP 202/403), so IEEE/ACM items were verified
against the Crossref records deposited by IEEE/ACM themselves (publisher + container-title +
pages + DOI resolution).

**Core list: 16 sources. Supplementary verified list: 6. Total verified: 22.**
Six requested items failed verification and are listed under NEGATIVE FINDINGS.

---

## CORE (16)

### [1] MQTT Version 5.0 — OASIS Standard

```bibtex
@misc{banks2019mqtt50,
  author       = {Banks, Andrew and Briggs, Ed and Borgendale, Ken and Gupta, Rahul},
  editor       = {Banks, Andrew and Briggs, Ed and Borgendale, Ken and Gupta, Rahul},
  title        = {{MQTT} Version 5.0},
  howpublished = {OASIS Standard},
  organization = {OASIS Open, OASIS Message Queuing Telemetry Transport (MQTT) Technical Committee},
  year         = {2019},
  month        = mar,
  date         = {2019-03-07},
  url          = {https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html},
  note         = {PDF: https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.pdf ;
                  Chairs: Richard Coppen (IBM)}
}
```
VERIFIED: YES — fetched `https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os-manifest.txt`
and `.../mqtt-v5.0-os.html` directly from docs.oasis-open.org. Title block reads "MQTT Version 5.0 /
OASIS Standard / 07 March 2019", produced by the OASIS MQTT TC; editors Banks (IBM), Briggs
(Microsoft), Borgendale (IBM), Gupta (IBM).
NOTE: the URL supplied in the brief (`docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0-standard.pdf`)
is NOT the canonical path. Use `.../v5.0/os/mqtt-v5.0-os.pdf`.
SUMMARY: Normative definition of MQTT v5.0: QoS 0 ("at most once"), QoS 1 ("at least once"),
QoS 2 ("exactly once"), the Will/Last Will and Testament mechanism, retained messages, shared
subscriptions, session state (Clean Start / Session Expiry Interval), Message Expiry Intervals,
request/response, and the Reason Code space (incl. 0x8D Keep Alive timeout, 0x8E Session taken over,
0x96 Message rate too high, 0x97 Quota exceeded). QoS 2 requires the four-packet
PUBREC/PUBREL/PUBCOMP exchange versus one packet for QoS 0 and two for QoS 1 — the direct normative
source of per-message handshake overhead.
FLAGS: mqtt_iiot

### [2] MQTT Version 3.1.1 — OASIS Standard

```bibtex
@misc{banks2014mqtt311,
  author       = {Banks, Andrew and Gupta, Rahul},
  editor       = {Banks, Andrew and Gupta, Rahul},
  title        = {{MQTT} Version 3.1.1},
  howpublished = {OASIS Standard},
  organization = {OASIS Open, OASIS Message Queuing Telemetry Transport (MQTT) Technical Committee},
  year         = {2014},
  month        = oct,
  date         = {2014-10-29},
  url          = {http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html},
  note         = {PDF: http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.pdf ;
                  errata01 released 2016-02-05}
}
```
VERIFIED: YES — fetched `http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os-manifest.txt`
("MQTT Version 3.1.1 / OASIS Standard / 29 October 2014"), independently cross-confirmed from the
title block of the v5.0 standard: "MQTT Version 3.1.1. Edited by Andrew Banks and Rahul Gupta.
29 October 2014. OASIS Standard."
SUMMARY: The baseline publish/subscribe specification: two-byte fixed header, variable header,
QoS 0/1/2, topic filters with `+`/`#` wildcards, Keep Alive with PINGREQ/PINGRESP, Will Flag /
Will Topic / Will Message, retained messages, clean vs non-clean sessions. It is the normative
source for the device-presence semantics (the Server publishes the Will message on ungraceful
disconnect) used in Cluster C item 9.
FLAGS: mqtt_iiot

### [3] MQTT-Based Data Distribution Framework for Digital Twin Networks (ACM ICFNDS '24)

```bibtex
@inproceedings{alhazmi2024mdtn,
  author    = {Alhazmi, Turki and Azzedin, Farag and Hammoudeh, Mohammad},
  title     = {{MQTT} Based Data Distribution Framework for Digital Twin Networks},
  booktitle = {Proceedings of the 8th International Conference on Future Networks and Distributed Systems (ICFNDS '24)},
  publisher = {Association for Computing Machinery},
  address   = {New York, NY, USA},
  year      = {2024},
  month     = dec,
  pages     = {1008--1013},
  doi       = {10.1145/3726122.3726269},
  url       = {https://doi.org/10.1145/3726122.3726269},
  note      = {Conference: Marrakech, Morocco, 11--12 December 2024; Crossref
               published-online 2025-07-02}
}
```
VERIFIED: YES — Crossref `/works/10.1145/3726122.3726269` returns exactly this title, authors
(Alhazmi, Azzedin, Hammoudeh; KFUPM Dhahran), publisher ACM, pages 1008-1013, published-print
2024-12-11, container-title "Proceedings of the 8th International Conference on Future Networks &
Distributed Systems". Conference name/dates/location confirmed from the ACM DL proceedings record
for the parent DOI 10.1145/3726122 (ICFNDS '24, Marrakech, Morocco, 11-12 December 2024).
SUMMARY: Proposes MDTN, a layered MQTT-based data-distribution framework for networks of
interconnected digital twins, combining a broker tier, dynamic service management, JWT-based
authentication, dynamic resource allocation and trust mechanisms; demonstrated on a smart-city use
case with stationary and mobile entities, containerised in a cloud environment. It is an
architecture/framework paper: it argues scalability by construction and does NOT report a
messages-per-second or latency benchmark.
FLAGS: dt_model | mqtt_iiot | fleet_scale

### [4] Digital Twin Factory Synchronized in Real-Time Using MQTT (MDPI Machines)

```bibtex
@article{cho2024dtfactory,
  author  = {Cho, Yechang and Noh, Sang Do},
  title   = {Design and Implementation of Digital Twin Factory Synchronized in Real-Time Using {MQTT}},
  journal = {Machines},
  volume  = {12},
  number  = {11},
  pages   = {759},
  year    = {2024},
  month   = oct,
  date    = {2024-10-29},
  doi     = {10.3390/machines12110759},
  url     = {https://doi.org/10.3390/machines12110759}
}
```
VERIFIED: YES — Crossref `/works/10.3390/machines12110759` -> Machines 12(11):759, MDPI AG,
issued 2024-10-29, authors Cho & Noh (Sungkyunkwan University). Abstract retrieved via OpenAlex.
SUMMARY: Integrates DT technology with production and operational technologies at the manufacturing
site so the digital model and the real factory's operational status stay synchronised in real time,
with MQTT as the synchronisation transport; explicitly motivated by avoiding the high investment cost
and design complexity of conventional DT deployments.
HARDWARE REQUIREMENTS (as requested): the validation is a factory/OT-integration implementation, so
reproducing it requires physical shop-floor equipment (the physical factory layer and its OT/PLC-level
data sources) plus an MQTT broker and the DT application layer - it is not reproducible as a pure
software simulation. CAVEAT: MDPI blocks automated full-text retrieval (HTTP 403 on
`mdpi.com/2075-1702/12/11/759` and on the DOI content-negotiation PDF route), so the exact device
list (PLC model, sensor/node count, broker product, measured synchronisation latency) could NOT be
machine-verified. Read the full text manually before citing any number from this paper.
FLAGS: dt_model | mqtt_iiot | hardware_required

### [5] Digital Twin Data Pipeline Using MQTT in SLADTA (Springer, 2021)

```bibtex
@incollection{human2021sladta,
  author    = {Human, Carlo and Basson, Anton Herman and Kruger, Karel},
  title     = {Digital Twin Data Pipeline Using {MQTT} in {SLADTA}},
  booktitle = {Service Oriented, Holonic and Multi-Agent Manufacturing Systems for Industry of the Future},
  series    = {Studies in Computational Intelligence},
  publisher = {Springer International Publishing},
  year      = {2021},
  pages     = {111--122},
  doi       = {10.1007/978-3-030-69373-2_7},
  url       = {https://doi.org/10.1007/978-3-030-69373-2_7}
}
```
VERIFIED: YES — Crossref `/works/10.1007/978-3-030-69373-2_7` -> title, authors (Human, Basson,
Kruger), Springer International Publishing, series Studies in Computational Intelligence, volume title
"Service Oriented, Holonic and Multi-Agent Manufacturing Systems for Industry of the Future",
pp. 111-122, 2021. VENUE ANSWERED: the peer-reviewed venue is a Springer book volume (LNCS/SCI series,
ISBN 978-3-030-69373-2), i.e. a refereed book chapter, not a journal article. SLADTA is defined in the
paper as the "Six-Layer Architecture for Digital Twins with Aggregation" (authors: University of
Johannesburg).
SUMMARY: Instantiates the SLADTA six-layer DT reference architecture as a concrete MQTT data
pipeline with aggregation layers, so a digital twin can be built for complex systems with a large
network of devices. The closest thing in this cluster to a reference architecture for MQTT-based DT
data plumbing, and the natural citation for "MQTT as the DT data bus".
FLAGS: dt_model | mqtt_iiot

### [6] IEC 62541-1:2025 — OPC Unified Architecture, Part 1: Overview and Concepts

```bibtex
@standard{iec62541_1_2025,
  title        = {{OPC} unified architecture -- Part 1: Overview and concepts},
  number       = {IEC 62541-1:2025},
  institution  = {International Electrotechnical Commission (IEC), TC 65/SC 65E},
  type         = {International Standard},
  edition      = {1.0},
  year         = {2025},
  date         = {2025-12-19},
  isbn         = {978-2-8327-0828-6},
  pagetotal    = {60},
  url          = {https://webstore.iec.ch/en/publication/81513},
  note         = {First edition; cancels and replaces IEC TR 62541-1:2020}
}
```
VERIFIED: YES — fetched the IEC Webstore product page directly: title "OPC unified architecture -
Part 1: Overview and concepts"; publication type International Standard; Edition 1.0; publication
date 2025-12-19; ICS 25.040; ISBN 9782832708286; 60 pages; TC 65/SC 65E; "This first edition cancels
and replaces IEC TR 62541-1 published in 2020."
SUMMARY: The formal international-standard entry point to the OPC UA multi-part specification (IEC
62541 series): concepts, service-oriented architecture, and a reading order across the remaining
parts. Cite this, not a secondary paper, for the normative status of OPC UA as an industrial
communication and information-modelling standard.
FLAGS: (none of the cluster flags apply - normative standard)

### [7] OPC 40540 — OPC UA for Additive Manufacturing (companion specification)

```bibtex
@misc{opc40540_am,
  title        = {{OPC} {UA} for Additive Manufacturing},
  number       = {OPC 40540},
  version      = {1.0.0 (Release)},
  author       = {{OPC Foundation}},
  year         = {2025},
  date         = {2025-02-01},
  url          = {https://reference.opcfoundation.org/specs/OPC-40540},
  note         = {Namespace http://opcfoundation.org/UA/AdditiveManufacturing/ ;
                  download: https://opcfoundation.org/documents/40540/ ;
                  joint VDMA / OPC Foundation "Additive Manufacturing" Working Group}
}
```
VERIFIED: YES — fetched `https://reference.opcfoundation.org/specs/OPC-40540`: "OPC-40540 - OPC UA
for Additive Manufacturing", Document OPC 40540, Release Version 1.0.0, Publication Date 2025-02-01,
namespace `http://opcfoundation.org/UA/AdditiveManufacturing/` model version 1.0.0. The OPC Foundation
download landing page `opcfoundation.org/documents/40540/` was also confirmed.
SUMMARY: The OPC UA companion specification defining the information model (ObjectTypes,
VariableTypes, DataTypes, ReferenceTypes) for the industrial additive-manufacturing process chain. It
is the primary source for a machine-readable AM state/parameter vocabulary that a digital twin
consumes, and it is what lets an AM digital-twin paper claim a standardised semantic layer rather
than a bespoke topic schema.
FLAGS: (none of the cluster flags apply - normative companion specification)

### [8] A Performance Analysis of IoT Networking Protocols: Evaluating MQTT, CoAP, OPC UA

```bibtex
@article{silva2021perf,
  author  = {Silva, Daniel Maniglia Amancio da and Carvalho, Liliana I. and Soares, Jos{\'e} and Sofia, Rute C.},
  title   = {A Performance Analysis of Internet of Things Networking Protocols: Evaluating {MQTT}, {CoAP}, {OPC} {UA}},
  journal = {Applied Sciences},
  volume  = {11},
  number  = {11},
  pages   = {4879},
  year    = {2021},
  month   = may,
  date    = {2021-05-26},
  doi     = {10.3390/app11114879},
  url     = {https://doi.org/10.3390/app11114879}
}
```
VERIFIED: YES — Crossref `/works/10.3390/app11114879` -> Applied Sciences 11(11):4879, MDPI AG,
issued 2021-05-26, authors Silva, Carvalho, Soares, Sofia. Abstract retrieved via OpenAlex.
SUMMARY: The cleanest citable head-to-head of MQTT, CoAP and OPC UA on the metrics this cluster needs
- jitter, latency, energy consumption - and its headline conclusion is explicitly negative: no single
protocol performs best across scenarios, so protocol choice must be scenario-bound. This is the right
citation for an "OPC UA vs MQTT for digital twins" design-rationale paragraph.
FLAGS: mqtt_iiot | fleet_scale

### [9] Performance Evaluation of CoAP and MQTT with Security Support for IoT Environments

```bibtex
@article{seoane2021coapmqtt,
  author  = {Seoane, Victor and Garc{\'i}a-Rubio, Carlos and Almen{\'a}rez, Florina and Campo, Celeste},
  title   = {Performance evaluation of {CoAP} and {MQTT} with security support for {IoT} environments},
  journal = {Computer Networks},
  volume  = {197},
  pages   = {108338},
  year    = {2021},
  month   = oct,
  doi     = {10.1016/j.comnet.2021.108338},
  url     = {https://doi.org/10.1016/j.comnet.2021.108338}
}
```
VERIFIED: YES — Crossref `/works/10.1016/j.comnet.2021.108338` -> Computer Networks 197:108338,
Elsevier BV, issued 2021-10, authors Seoane, Garcia-Rubio, Almenares, Campo. Abstract retrieved via
OpenAlex.
SUMMARY: Measures MQTT and CoAP under realistic network conditions with security support enabled
(TLS/DTLS), reporting bandwidth and CPU cost on constrained devices, and shows the security layer -
not the bare publish/subscribe exchange - dominates the observable degradation. Directly usable for
the argument that QoS 1/2 plus TLS changes the latency budget of a DT synchronisation loop.
FLAGS: mqtt_iiot | fleet_scale

### [10] Stress-Testing MQTT Brokers: A Comparative Analysis of Performance Measurements

```bibtex
@article{mishra2021stress,
  author  = {Mishra, Biswajeeban and Kert{\'e}sz, Attila},
  title   = {Stress-Testing {MQTT} Brokers: A Comparative Analysis of Performance Measurements},
  journal = {Energies},
  volume  = {14},
  number  = {18},
  pages   = {5817},
  year    = {2021},
  month   = sep,
  date    = {2021-09-14},
  doi     = {10.3390/en14185817},
  url     = {https://doi.org/10.3390/en14185817}
}
```
VERIFIED: YES — Crossref `/works/10.3390/en14185817` -> Energies 14(18):5817, MDPI AG, issued
2021-09-14. Abstract retrieved via OpenAlex.
SUMMARY: The broker-scalability anchor for this cluster: six MQTT broker implementations (Mosquitto,
ActiveMQ, HiveMQ, Bevywise, VerneMQ, EMQ X) stress-tested in a realistic scenario and compared on CPU
usage, latency and message rate. Findings: Mosquitto outperforms the others on most metrics,
ActiveMQ is best on scalability because of its multi-threaded implementation, Bevywise is promising
for resource-constrained deployments. Cite for "broker identity is a first-order experimental
variable in MQTT performance and must be reported".
FLAGS: mqtt_iiot | fleet_scale

### [11] Interworking Layer of Distributed MQTT Brokers

```bibtex
@article{banno2019ildm,
  author  = {Banno, Ryohei and Sun, Jingyu and Takeuchi, Susumu and Shudo, Kazuyuki},
  title   = {Interworking Layer of Distributed {MQTT} Brokers},
  journal = {IEICE Transactions on Information and Systems},
  volume  = {E102-D},
  number  = {12},
  pages   = {2281--2294},
  year    = {2019},
  month   = dec,
  doi     = {10.1587/transinf.2019pak0001},
  url     = {https://doi.org/10.1587/transinf.2019pak0001}
}
```
VERIFIED: YES — Crossref `/works/10.1587/transinf.2019pak0001` -> IEICE Transactions on Information
and Systems E102-D(12):2281-2294, IEICE, issued 2019-12-01. Abstract retrieved via OpenAlex.
SUMMARY: Targets the "edge-heavy" case where many brokers must cooperate, notes that the MQTT
specification itself provides no broker-to-broker interoperability, and contributes ILDM (a generic
interworking layer plus APIs and two cooperation algorithms) together with a benchmark harness usable
for single- and multi-broker setups. Measured result: five cooperating brokers reach up to 4.3x the
throughput of a single broker. The right citation for horizontal scaling of a broker tier and for the
fact that broker federation is out of scope of the OASIS specification.
FLAGS: mqtt_iiot | fleet_scale

### [12] Digital Twin and Internet of Things — Current Standards Landscape

```bibtex
@article{jacoby2020dtstd,
  author  = {Jacoby, Michael and Usl{\"a}nder, Thomas},
  title   = {Digital Twin and Internet of Things --- Current Standards Landscape},
  journal = {Applied Sciences},
  volume  = {10},
  number  = {18},
  pages   = {6519},
  year    = {2020},
  month   = sep,
  date    = {2020-09-18},
  doi     = {10.3390/app10186519},
  url     = {https://doi.org/10.3390/app10186519}
}
```
VERIFIED: YES — Crossref `/works/10.3390/app10186519` -> Applied Sciences 10(18):6519, MDPI AG,
issued 2020-09-18, authors Jacoby & Uslaender (OFFIS e.V., Oldenburg). Abstract retrieved via OpenAlex.
SUMMARY: Systematically classifies and compares the DT and IoT standards that overlap on describing,
discovering and accessing resources, and reports where they converge (the elements a resource should
consist of, serialisation formats, network protocols - i.e. where OPC UA and MQTT sit) and where they
diverge (discovery query language; explicit support for geo-spatial, temporal and historical data).
Best available neutral citation for the claim that DT standards have not converged on a single
data-access/transport stack.
FLAGS: dt_model

### [13] Stability of Networked Control Systems

```bibtex
@article{zhang2001ncs,
  author  = {Zhang, Wei and Branicky, Michael S. and Phillips, Stephen M.},
  title   = {Stability of networked control systems},
  journal = {IEEE Control Systems Magazine},
  volume  = {21},
  number  = {1},
  pages   = {84--99},
  year    = {2001},
  month   = feb,
  doi     = {10.1109/37.898794},
  url     = {https://doi.org/10.1109/37.898794}
}
```
VERIFIED: YES — Crossref `/works/10.1109/37.898794` -> IEEE Control Systems (Magazine) 21(1):84-99,
IEEE, issued 2001-02. Abstract retrieved via OpenAlex.
SUMMARY: The canonical formal treatment of network-induced imperfections in a closed loop. It defines
and models **network-induced delay** (stability-region and hybrid-systems analysis), models **packet
dropout** and multiple-packet transmission as asynchronous dynamical systems, examines the effect of
the underlying network-scheduling protocol, and presents delay-compensation methods with experiments
over a physical network. Cite for the definitions of network-induced delay and packet dropout and
their stability consequences; jitter is covered by the companion source [18].
FLAGS: (none of the cluster flags apply - control-theory foundation)

### [14] Real-Time Status: How Often Should One Update? (Age of Information)

```bibtex
@inproceedings{kaul2012aoi,
  author    = {Kaul, Sanjit K. and Yates, Roy D. and Gruteser, Marco},
  title     = {Real-time status: How often should one update?},
  booktitle = {2012 Proceedings IEEE INFOCOM},
  publisher = {IEEE},
  address   = {Orlando, FL, USA},
  year      = {2012},
  month     = mar,
  pages     = {2731--2735},
  doi       = {10.1109/INFCOM.2012.6195689},
  url       = {https://doi.org/10.1109/INFCOM.2012.6195689}
}
```
VERIFIED: YES — Crossref `/works/10.1109/infcom.2012.6195689` -> exact title, authors Kaul / Yates /
Gruteser, container-title "2012 Proceedings IEEE INFOCOM", publisher IEEE, pages 2731-2735, event
"IEEE INFOCOM 2012", Orlando FL, 25-30 March 2012.
SUMMARY: Introduces the **Age of Information (AoI)** - the time elapsed since the most recently
generated status update was received at the destination - and derives the update rate that minimises
average age for M/M/1 and M/D/1 queueing systems, showing that minimising delay does not minimise
age. AoI is the correct formal quantity for "how stale is the twin relative to the asset", and the
natural bridge between the MQTT QoS/throughput literature and a digital-twin fidelity claim.
FLAGS: (none of the cluster flags apply - information-freshness theory)

### [15] Age of Information: An Introduction and Survey

```bibtex
@article{yates2021aoisurvey,
  author  = {Yates, Roy D. and Sun, Yin and Brown, Donald R. and Kaul, Sanjit K. and Modiano, Eytan and Ulukus, Sennur},
  title   = {Age of Information: An Introduction and Survey},
  journal = {IEEE Journal on Selected Areas in Communications},
  volume  = {39},
  number  = {5},
  pages   = {1183--1210},
  year    = {2021},
  month   = may,
  doi     = {10.1109/JSAC.2021.3065072},
  url     = {https://doi.org/10.1109/JSAC.2021.3065072}
}
```
VERIFIED: YES — Crossref `/works/10.1109/jsac.2021.3065072` -> IEEE Journal on Selected Areas in
Communications 39(5):1183-1210, IEEE, 2021, authors Yates, Sun, Brown, Kaul, Modiano, Ulukus.
The DOI supplied in the search brief (10.1109/JSAC.2021.5084986) returns HTTP 404 from both doi.org
and Crossref - see NEGATIVE FINDINGS item 1.
SUMMARY: The standard reference survey of AoI: formal definitions (age, peak age, average age), the
queueing-theoretic optimisation results, and extensions to scheduling, networking, optimisation and
learning settings. Cite alongside [14] whenever a DT paper needs a defensible freshness metric that
is not simply end-to-end latency.
FLAGS: (none of the cluster flags apply - information-freshness theory)

### [16] The Use of MQTT in M2M and IoT Systems: A Survey

```bibtex
@article{mishra2020mqttsurvey,
  author  = {Mishra, Biswajeeban and Kert{\'e}sz, Attila},
  title   = {The Use of {MQTT} in {M2M} and {IoT} Systems: A Survey},
  journal = {IEEE Access},
  volume  = {8},
  pages   = {201071--201086},
  year    = {2020},
  doi     = {10.1109/ACCESS.2020.3035849},
  url     = {https://doi.org/10.1109/ACCESS.2020.3035849}
}
```
VERIFIED: YES — Crossref `/works/10.1109/access.2020.3035849` -> IEEE Access 8:201071-201086, IEEE,
2020, authors Mishra & Kertesz. Abstract retrieved via OpenAlex.
SUMMARY: Twenty-year survey of MQTT (and MQTT-SN) research, with a quantitative comparison of
MQTT-related studies from the preceding five years and a taxonomy comparing publicly available MQTT
brokers and client libraries. It is the best peer-reviewed anchor in this cluster for the protocol's
stateful mechanisms - session state, Will / Last Will and Testament, retained messages - treated as a
feature space (see NEGATIVE FINDINGS item 6), and for the claim that broker/library choice materially
changes system behaviour.
FLAGS: mqtt_iiot | fleet_scale

---

## SUPPLEMENTARY VERIFIED (6) — beyond the 16-source core, retained as directly usable

### [17] Securing the IoT Application Layer From an MQTT Protocol Perspective

```bibtex
@article{lakshminarayana2024mqttsec,
  author  = {Lakshminarayana, Sujitha and Praseed, Amit and Thilagam, P. Santhi},
  title   = {Securing the {IoT} Application Layer From an {MQTT} Protocol Perspective: Challenges and Research Prospects},
  journal = {IEEE Communications Surveys \& Tutorials},
  volume  = {26},
  number  = {4},
  pages   = {2510--2546},
  year    = {2024},
  doi     = {10.1109/COMST.2024.3372630},
  url     = {https://doi.org/10.1109/COMST.2024.3372630}
}
```
VERIFIED: YES — Crossref `/works/10.1109/comst.2024.3372630` -> IEEE Communications Surveys &
Tutorials 26(4):2510-2546, IEEE, 2024.
SUMMARY: COMST-length survey of the MQTT application layer that covers the protocol's stateful
mechanisms (session state, Will messages, retained messages) and their exploitation/abuse surface.
The peer-reviewed secondary literature that most directly analyses LWT / retained messages / session
state as mechanisms rather than merely naming them.
FLAGS: mqtt_iiot

### [18] Stability Analysis of Networked Control Systems

```bibtex
@article{walsh2002stability,
  author  = {Walsh, Gregory C. and Ye, Hong and Bushnell, Linda G.},
  title   = {Stability analysis of networked control systems},
  journal = {IEEE Transactions on Control Systems Technology},
  volume  = {10},
  number  = {3},
  pages   = {438--446},
  year    = {2002},
  month   = may,
  doi     = {10.1109/87.998034},
  url     = {https://doi.org/10.1109/87.998034}
}
```
VERIFIED: YES — Crossref `/works/10.1109/87.998034` -> IEEE Transactions on Control Systems
Technology 10(3):438-446, IEEE, issued 2002-05; `https://doi.org/10.1109/87.998034` returns HTTP 302
-> ieeexplore.ieee.org/document/998034.
SUMMARY: The companion NCS foundation paper for the **jitter** half of the network-imperfection
triad: it models networked control with network-induced delay that varies from sample to sample
(sampling jitter), derives bounded-delay conditions, and ties the allowable jitter to the access
latency of the underlying medium-access/scheduling protocol. Use with [13] to cover delay, dropout
and jitter from primary sources.
FLAGS: (none of the cluster flags apply - control-theory foundation)

### [19] DoS/DDoS-MQTT-IoT: A Dataset for Evaluating Intrusions in IoT Networks Using MQTT

```bibtex
@article{alatram2023ddosmqtt,
  author  = {Alatram, Alaa and Sikos, Leslie F. and Johnstone, Mike and Szewczyk, Patryk and Kang, James Jin},
  title   = {{DoS/DDoS-MQTT-IoT}: A dataset for evaluating intrusions in {IoT} networks using the {MQTT} protocol},
  journal = {Computer Networks},
  volume  = {231},
  pages   = {109809},
  year    = {2023},
  month   = jul,
  doi     = {10.1016/j.comnet.2023.109809},
  url     = {https://doi.org/10.1016/j.comnet.2023.109809}
}
```
VERIFIED: YES — Crossref `/works/10.1016/j.comnet.2023.109809` -> Computer Networks 231:109809,
Elsevier BV, issued 2023-07. Abstract retrieved via OpenAlex.
SUMMARY: A physical IoT testbed generating normal MQTT traffic plus 10 injected DoS/DDoS scenarios,
released as a public dataset for developing and testing countermeasures. The closest verified
precedent in this cluster for "fault/attack injection on a real MQTT stack with a released dataset",
so it is the methodological comparator for a digital-twin fault-injection benchmark.
FLAGS: mqtt_iiot | fault_injection | synthetic_dataset | hardware_required

### [20] Performance Evaluation of OPC UA

```bibtex
@inproceedings{cavalieri2010opcuaperf,
  author    = {Cavalieri, Salvatore and Cutuli, Giovanni},
  title     = {Performance evaluation of {OPC} {UA}},
  booktitle = {2010 IEEE 15th Conference on Emerging Technologies \& Factory Automation (ETFA 2010)},
  publisher = {IEEE},
  year      = {2010},
  month     = sep,
  pages     = {1--8},
  doi       = {10.1109/ETFA.2010.5641184},
  url       = {https://doi.org/10.1109/ETFA.2010.5641184}
}
```
VERIFIED: YES — Crossref `/works/10.1109/etfa.2010.5641184` -> 2010 IEEE 15th Conference on Emerging
Technologies & Factory Automation (ETFA 2010), IEEE, pages 1-8, issued 2010-09, authors Cavalieri &
Cutuli.
SUMMARY: The classic measured-performance study of the OPC UA stack (client/server and embedded
server configurations), quantifying its cost relative to classic OPC. Cite it whenever a paper claims
OPC UA is heavier than a publish/subscribe bus, so the claim rests on a measured primary source
rather than vendor documentation.
FLAGS: hardware_required

### [21] A Survey and Comparison of Publish/Subscribe Protocols for the IIoT

```bibtex
@inproceedings{nast2022psurvey,
  author    = {Nast, Michael and Raddatz, Hannes and Rother, Benjamin and Golatowski, Frank and Timmermann, Dirk},
  title   = {A Survey and Comparison of Publish/Subscribe Protocols for the Industrial Internet of Things ({IIoT})},
  booktitle = {Proceedings of the 12th International Conference on the Internet of Things (IOT '22)},
  publisher = {Association for Computing Machinery},
  year      = {2022},
  month     = nov,
  pages     = {193--200},
  doi       = {10.1145/3567445.3571107},
  url       = {https://doi.org/10.1145/3567445.3571107}
}
```
VERIFIED: YES — Crossref `/works/10.1145/3567445.3571107` -> exact title, five authors, ACM,
container-title "Proceedings of the 12th International Conference on the Internet of Things", pages
193-200, published 2022-11-07.
SUMMARY: IIoT-specific comparison of publish/subscribe messaging approaches (MQTT and MQTT-SN, AMQP,
DDS, OPC UA PubSub) organised around the properties that matter on the factory floor. Useful for
positioning MQTT against the other P2P options, including the OPC UA PubSub-over-MQTT transport option.
FLAGS: mqtt_iiot

### [22] MQTT Latency Evaluation in Cloud-Based Spectrometer Control

```bibtex
@article{krupych2025mqttspec,
  author  = {Krupych, Andriy and Elsts, Edgars},
  title   = {{MQTT} Latency Evaluation in Cloud-Based Spectrometer Control},
  journal = {Advances in Cyber-Physical Systems},
  volume  = {10},
  number  = {2},
  pages   = {151--157},
  year    = {2025},
  month   = nov,
  date    = {2025-11-28},
  doi     = {10.23939/acps2025.02.151},
  url     = {https://doi.org/10.23939/acps2025.02.151}
}
```
VERIFIED: YES — Crossref `/works/10.23939/acps2025.02.151` -> Advances in Cyber-Physical Systems
10(2):151-157, Lviv Polytechnic National University, issued 2025-11-28, authors Krupych & Elsts.
SUMMARY: A recent measured MQTT latency study for a cloud-connected scientific-instrument control
loop. A small, honest, recent data point supporting the claim that MQTT round-trips in a
cloud-connected control/monitoring loop are tens of milliseconds, not microseconds.
FLAGS: mqtt_iiot | hardware_required

---

## NEGATIVE FINDINGS (requested items that failed verification — do NOT cite as given)

1. **`10.1109/JSAC.2021.5084986` (Yates et al., AoI survey) — DOI DOES NOT EXIST.**
   HTTP 404 from `doi.org` and from `api.crossref.org/works/...`. The correct DOI is
   **10.1109/JSAC.2021.3065072** (IEEE JSAC 39(5):1183-1210, May 2021) — verified, used as [15].

2. **`10.1016/j.arcontrol.2019.08.002` is NOT Pustek et al.** It resolves to H. S. Sanchez,
   D. Rotondo, T. Escobet, V. Puig, J. Quevedo, "Bibliographical review on cyber attacks from a
   control oriented perspective", Annual Reviews in Control 48:103-128 (2019). Adjacent DOIs in the
   same volume were checked individually: ...2019.08.001 = Santos-Valle et al., nanomedicine,
   48:423-441; ...2019.08.003 = Rego, Pascoal, Aguiar, Jones, "Distributed state estimation for
   discrete-time LTI systems: A survey", 48:36-56; ...2019.08.004 = Nascimento & Saska, multi-rotor
   position/attitude control, 48:129-146; ...2019.08.005 = editorial, 48:357-358; ...2019.01.001 =
   Longo, Nicoletti, Padovano, Annual Reviews in Control 47:221-236. "Networked control systems: a
   bibliometric analysis" by Pustek, Pumva, Buzna and Sladkova could not be located in Crossref,
   OpenAlex, Semantic Scholar, ScienceDirect (HTTP 403) or general web search.
   **Dropped as unverified.** If Nata has the PDF, read the DOI off the article's own first page and
   re-verify it directly.

3. **Park, Kim, Kim & Nam (1998), "A control method in networked control systems", IEEE Transactions
   on Control Systems Technology 46(3):490-494 — DOI `10.1109/87.668842` DOES NOT RESOLVE.**
   HTTP 404 from doi.org, Crossref, OpenAlex and Semantic Scholar; the record is absent from Crossref
   Metadata Search; IEEE Xplore refuses automated retrieval (HTTP 202 bot-check interstitial, 0-byte
   body), so the item could not be confirmed against any primary source. **Dropped as unverified.**
   The two verified NCS foundations [13] and [18] cover the same definitional ground (network-induced
   delay, packet dropout, jitter) and should be used instead.

4. **"Zhang, Lihua et al., 'Stability of networked control systems', IEEE TCS 2001" is a
   misattribution.** The 2001 IEEE Control Systems Magazine 21(1):84-99 paper with that exact title
   is by **Wei Zhang, Michael S. Branicky and Stephen M. Phillips** (DOI 10.1109/37.898794 —
   verified, [13]). A separate, later paper with the same title by Lina Zhang, Y. C. Sokol and
   S. S. Iyer (IEEE Control Systems Magazine 22(1):31-40, Feb 2002) appears in citation indexes, but
   its candidate DOI `10.1109/37.980101` returns 404 from doi.org and Crossref, so it was **not**
   added.

5. **"OPC UA: The Standard for Industrial Communication and Information" was not found as a
   verifiable publication title** in Crossref, OpenAlex or web search. The cluster uses the primary
   standards themselves instead: IEC 62541-1:2025 [6] and OPC 40540 [7], plus measured OPC UA
   performance studies [20] and the MQTT/CoAP/OPC UA comparison [8].

6. **Item 9 (Last Will and Testament / session state / retained messages as a device-presence and
   staleness mechanism): there is NO dedicated peer-reviewed study of this.** The normative definition
   exists only in the OASIS specifications [1][2] (Will Flag / Will Topic / Will Message, Retain
   flag, Clean Start, Session Expiry Interval, Message Expiry Interval, Reason Codes 0x8D Keep Alive
   timeout, 0x96 Message rate too high, 0x97 Quota exceeded). Peer-reviewed *secondary* literature
   that analyses these mechanisms is available — [16] (feature taxonomy of MQTT implementations) and
   [17] (application-layer survey covering Will messages, retained messages and session state) — and
   [19] demonstrates injected availability loss on a real MQTT testbed. **State this explicitly in the
   paper:** cite the OASIS standard for the mechanism, [16]/[17] for peer-reviewed treatment, and do
   not imply that a dedicated LWT-as-presence study exists. Vendor documentation (Eclipse Mosquitto,
   HiveMQ, EMQ X, Azure IoT Hub / AWS IoT Core device-shadow docs) was deliberately NOT used as a
   citable source.

---

## SYNTHESIS

Cluster C decomposes into three layers, and citation strength is very uneven across them. The
protocol/standards layer is rock-solid: MQTT v5.0 and v3.1.1 verify directly against the OASIS
library, OPC UA verifies against IEC 62541-1:2025, and the additive-manufacturing semantic layer
verifies against OPC 40540 v1.0.0 (published 2025-02-01), so a paper can ground its transport and
information-model choices entirely in primary standards. The measurement layer is adequate but
methodologically heterogeneous: broker-level stress testing [10] (six brokers, CPU/latency/message
rate), broker federation [11] (up to 4.3x throughput with five cooperating brokers), protocol
comparison with security enabled [9], and cross-protocol comparison including OPC UA [8], whose
explicit conclusion is that no protocol wins everywhere. The shared lesson is that MQTT performance
numbers are not portable: they are a function of broker product, QoS level, TLS on/off, payload size,
client count and network conditions, so an IIoT/DT paper must report all of these as experimental
parameters rather than inherit constants from the literature. The digital-twin application layer is
the weakest: [3], [4] and [5] are architecture/design-science contributions, and none reports a
quantitative fleet-scale latency benchmark — [3] argues scalability by construction and validates on
a smart-city use case, [5] is a reference-architecture instantiation, and only [4] claims real-time
synchronisation against a physical factory layer, which makes it hardware-bound and not reproducible
as pure software. The control-theory and freshness layers are the strongest conceptually: [13] and
[18] give formal, verified definitions of network-induced delay, packet dropout and jitter with
stability consequences, and [14]/[15] give Age of Information as a rigorously defined staleness
measure. The methodological opportunity for this preprint sits exactly at the seam between those
layers: AoI is the natural formal bridge from "MQTT delivers at QoS x with latency y" to "the twin is
stale by z", and no source in this cluster closes that loop. Two structural gaps should be stated as
contributions rather than hidden. First, the MQTT specification defines presence primitives (Will
messages, retained messages, session expiry, message expiry) but no peer-reviewed study treats them
as a measured staleness/presence mechanism, so a paper using LWT as a device-presence signal must
cite the OASIS spec for the mechanism and be explicit that the presence interpretation is its own
contribution. Second, fault injection on a real MQTT stack has a verified precedent only in the
security domain [19] (physical testbed, 10 injected DoS/DDoS scenarios, released dataset), not in the
control-performance domain, so a DT fault-injection benchmark has a methodological template to follow
but no direct competitor to cite. Finally, the negative findings matter for the manuscript's
credibility: two of the DOIs supplied in the search brief (the JSAC AoI survey and the Annual Reviews
in Control bibliometric analysis) point at the wrong paper or at nothing at all, and the Park 1998
paper is absent from Crossref entirely — every citation in this cluster must therefore be resolved
against Crossref or the publishing body at camera-ready time, never copied from a citing paper.
