# Cluster B — AM Digital Twins, FDM/FFF Monitoring & Simulation, AM Fleet Simulation, FDM Energy & Deposition Models

Verification method: every entry below was resolved against the Crossref REST API
(`https://api.crossref.org/works/<DOI>`), and where available against the publisher landing page
(Springer Link, MDPI, IEEE, Elsevier/ScienceDirect metadata via Crossref `alternative-id`), the
Research Square preprint server, Europe PMC full-text XML, and the FIBR3DEmul GitHub README.
Abstracts were taken from Crossref, Semantic Scholar, Europe PMC, or the publisher page.
No citation, DOI, author list, journal, volume, page range, or number below is unverified.

## ⚠ Corrections to the supplied cluster brief

1. **"Exploring the integration of digital twin and additive manufacturing: state-of-the-art and future
   trends", *Journal of Manufacturing Systems*, 2024, PII S2588840424000556 — journal attribution is wrong.**
   PII `S2588840424000556` carries ISSN prefix **2588-8404 = International Journal of Lightweight Materials
   and Manufacture** (not JMS, ISSN 0278-6125). The record is: Jyeniskhan, Shomenov, Ali, Shehab,
   *"Exploring the integration of digital twin and additive manufacturing technologies"*, **Int. J. Lightweight
   Materials and Manufacture, vol. 7, no. 6, pp. 860–881, Nov 2024, DOI 10.1016/j.ijlmm.2024.06.004**
   (Crossref `alternative-id` = `S2588840424000556` — exact match to the PII supplied in the brief). Use this.
2. **"A digital twin ecosystem for additive manufacturing using a real-time development platform",
   *Journal of Intelligent Manufacturing*, 2022 — journal attribution is wrong.** DOI
   `10.1007/s00170-022-09164-6` resolves to **The International Journal of Advanced Manufacturing
   Technology, vol. 120, nos. 9–10, pp. 6547–6563, 2022** (Springer, ISSN 0268-3768/1433-3015). The DOI
   itself is correct; the journal name in the brief is not.
3. **"A digital twin strategy for major failure detection in fused deposition modeling processes" — DOI in the
   brief is wrong.** `10.1016/j.promfg.2021.06.052` does not resolve to this paper. The correct DOI is
   **10.1016/j.promfg.2021.06.039** (Procedia Manufacturing 53:359–367, 2021 — volume/pages as supplied).
4. **"FIBR3DEmul" is not in *Applied Sciences*.** The peer-reviewed venue is **The International Journal of
   Advanced Manufacturing Technology, vol. 106, nos. 7–8, pp. 3609–3623, 2020, DOI 10.1007/s00170-019-04713-y**
   (confirmed from the project README at `github.com/neuebot/FIBR3DEmul`, which links this Springer article).
5. **"Kellens et al., 'Energy productivity of additive manufacturing: From fundamental characteristics to
   environmental sustainability benchmarking', *Journal of Industrial Ecology* — DROPPED, not verifiable.**
   `10.1111/jie.12899` returns HTTP 404; `10.1111/jiec.12899` resolves to a *Journal of Industrial Ecology*
   "Issue Information, Cover, and Table of Contents" record, not to an article. A Crossref search restricted to
   ISSN 1088-1980 (JIE) with author=Kellens returns only the 2017 supplement papers. No such article was found
   at any DOI. Replaced by three verified Kellens/Gutowski energy sources ([14], [15], [16]).
6. **Kreiger & Pearce, *Energy Policy* 63:444–450 — DROPPED.** `10.1016/j.enpol.2013.08.077` resolves to a
   Jacobsson & Karltorp offshore-wind-policy article in *Energy Policy* 63:1182–1195. A Crossref search for
   Kreiger/Pearce energy consumption returns their *MRS Proceedings* and *ACS Sustainable Chemistry &
   Engineering* papers instead; the *Energy Policy* item could not be confirmed and is not cited.

---

## [1] AM digital twin review (the PII supplied in the brief)

```bibtex
@article{jyeniskhan2024exploring,
  author  = {Jyeniskhan, Nursultan and Shomenov, Kemel and Ali, Md Hazrat and Shehab, Essam},
  title   = {Exploring the integration of digital twin and additive manufacturing technologies},
  journal = {International Journal of Lightweight Materials and Manufacture},
  volume  = {7},
  number  = {6},
  pages   = {860--881},
  year    = {2024},
  month   = {11},
  issn    = {2588-8404},
  doi     = {10.1016/j.ijlmm.2024.06.004}
}
```
VERIFIED: YES — Crossref `/works/10.1016/j.ijlmm.2024.06.004`; `alternative-id = S2588840424000556` matches the PII in the brief exactly; ISSN 2588-8404 confirms the journal is IJLMM, not JMS.
SUMMARY: State-of-the-art review of DT–AM integration spanning design, simulation and production. It is the closest match to the title supplied in the brief and is the natural anchor citation for the "AM digital twin" framing in SimTwin's related work.
FLAGS: dt_model
NUMBERS: none extractable from Crossref metadata (paywalled; no abstract in Crossref).

## [2] AM digital twin implementation review (MDPI, open access)

```bibtex
@article{benamor2024digitaltwin,
  author  = {Ben Amor, Sabrine and Elloumi, Nessrine and Eltaief, Ameni and Louhichi, Borhen and
             Alrasheedi, Nashmi H. and Seibi, Abdennour},
  title   = {Digital Twin Implementation in Additive Manufacturing: A Comprehensive Review},
  journal = {Processes},
  volume  = {12},
  number  = {6},
  pages   = {1062},
  year    = {2024},
  month   = {5},
  issn    = {2227-9717},
  doi     = {10.3390/pr12061062}
}
```
VERIFIED: YES — Crossref `/works/10.3390/pr12061062` (MDPI AG); abstract returned by Crossref.
SUMMARY: Reviews DTs across the whole AM chain (conception → manufacturing), covering applications, benefits, challenges and future directions, and stresses that DT development is iterative and needs cross-disciplinary collaboration. Useful for arguing that most published AM DTs are single-machine, bespoke, and require a physical asset.
FLAGS: dt_model | open_source
NUMBERS: none in abstract.



## [3] FDM/FFF digital twin requiring a physical printer (OctoPrint + external sensors)

```bibtex
@article{pantelidakis2022digitaltwin,
  author  = {Pantelidakis, Minas and Mykoniatis, Konstantinos and Liu, Jia and Harris, Gregory},
  title   = {A digital twin ecosystem for additive manufacturing using a real-time development platform},
  journal = {The International Journal of Advanced Manufacturing Technology},
  volume  = {120},
  number  = {9--10},
  pages   = {6547--6563},
  year    = {2022},
  month   = {6},
  issn    = {0268-3768},
  doi     = {10.1007/s00170-022-09164-6}
}
```
VERIFIED: YES — Crossref DOI lookup + Springer Link article page (vol. 120, pp. 6547–6563, published 13 Apr 2022) + full preprint text on Research Square (rs-1270408, CC BY 4.0), which supplied the hardware and validation numbers.
SUMMARY: Builds a "digital twin ecosystem" (DTE) for one FDM machine with two data paths: (a) the **OctoPrint** open-source web controller (treated as ground truth) and (b) **externally mounted sensors** for legacy machines. Data acquisition/processing/distribution runs on a **Raspberry Pi 3 (Raspberry Pi OS)** exposing a **Flask** REST sensor API; the virtual twin is rendered in **Unity 3D**. Validated on position, temperature and run duration; aimed at testing, process monitoring, remote management, historical data collection and analytics — a monitoring twin, not a physics twin, and it cannot be exercised without the physical printer attached.
FLAGS: hardware_required | dt_model | mqtt_iiot (IIoT-style HTTP/REST sensor API on a local network plus bidirectional OctoPrint↔Marlin link; **not** MQTT)
NUMBERS: printer = **Lulzbot Taz Workhorse** running **Marlin**; sensor node = Raspberry Pi 3; **Yocto-Thermocouple** USB sensor, response **< 30 ms**, range **−75 °C to 260 °C**, manufacturer error limit **± 2.2 °C**; **VL53L0X** ToF IR distance sensors, range **50–1200 mm**, **3–12 %** ranging accuracy; position test at physical (X, Y, Z) = (50, 53, 19) mm over 30 replications gave mean errors **2.69 mm (X), 0.06 mm (Y), 3.2 mm (Z)**; temperature validation at **180 °C** (mean 181.82 °C, SD 0.191) and **230 °C** (mean 230.89 °C, SD 0.092), 30 replications each; PLA operating window quoted as **180–230 °C**; kinematics test at acceleration **500 mm/s²**, feed rate 3000, average speeds **118.34 mm/s** over 100 mm moves and **171.23 mm/s** over 250 mm moves; print-duration validation mean **25.7133 s**, SD **0.157 s**.

## [4] FDM digital twin for major-failure detection (multi-view vision)

```bibtex
@article{henson2021digitaltwin,
  author  = {Henson, Christopher M. and Decker, Nathan I. and Huang, Qiang},
  title   = {A digital twin strategy for major failure detection in fused deposition modeling processes},
  journal = {Procedia Manufacturing},
  volume  = {53},
  pages   = {359--367},
  year    = {2021},
  issn    = {2351-9789},
  doi     = {10.1016/j.promfg.2021.06.039}
}
```
VERIFIED: YES — Crossref `/works/10.1016/j.promfg.2021.06.039` (Elsevier, `alternative-id = S2351978921000457`); abstract from Semantic Scholar. **The DOI in the brief (…06.052) is wrong.**
SUMMARY: Argues that detecting *end-effects* (part distortion) is more robust than detecting individual root causes such as melt-pool geometry or extruder clogging, because failures can have unknown sources. Builds a multi-view optical sensing system for a movable print bed and compares layer-by-layer image features against offline-generated digital twins of the actual prints, so detection latency is low enough to justify terminating a print.
FLAGS: hardware_required | dt_model | fault_injection | open_source (Procedia OA)
NUMBERS: **3 test prints**; failure rapidly detected in **2 of 3**, the third detected "after a short delay"; digital twins of prints generated **offline at specific layers** to reduce detection delay.

## [5] FDM digital twin architecture for monitoring and optimisation

```bibtex
@article{mourtzis2021digitaltwin,
  author  = {Mourtzis, Dimitris and Togias, Thodoris and Angelopoulos, John and Stavropoulos, Panos},
  title   = {A Digital Twin architecture for monitoring and optimization of Fused Deposition Modeling processes},
  journal = {Procedia CIRP},
  volume  = {103},
  pages   = {97--102},
  year    = {2021},
  issn    = {2212-8271},
  doi     = {10.1016/j.procir.2021.10.015}
}
```
VERIFIED: YES — Crossref `/works/10.1016/j.procir.2021.10.015` (Elsevier, `alternative-id = S2212827121008568`).
SUMMARY: Proposes a layered DT architecture for FDM covering monitoring and process optimisation, in the CIRP line of work that treats the DT as a cyber-physical layer over a real machine. Cite it as evidence that published FDM DTs are machine-coupled and single-cell rather than fleet-level.
FLAGS: hardware_required | dt_model
NUMBERS: none extracted (paywalled; no abstract in Crossref).

## [6] Layer-wise in-situ monitoring (point-cloud fusion) for AM

```bibtex
@article{ye2021insitu,
  author  = {Ye, Zehao and Liu, Chenang and Tian, Wenmeng and Kan, Chen},
  title   = {In-situ point cloud fusion for layer-wise monitoring of additive manufacturing},
  journal = {Journal of Manufacturing Systems},
  volume  = {61},
  pages   = {210--222},
  year    = {2021},
  month   = {10},
  issn    = {0278-6125},
  doi     = {10.1016/j.jmsy.2021.09.002}
}
```
VERIFIED: YES — Crossref `/works/10.1016/j.jmsy.2021.09.002` (Elsevier, `alternative-id = S0278612521001886`).
SUMMARY: Representative of the layer-wise / camera-based monitoring line: fuses multi-view in-situ point clouds to reconstruct the deposited part layer by layer, providing the geometric feedback stream a closed-loop AM digital twin needs. Good citation for the physical sensing layer that SimTwin deliberately replaces with a simulator.
FLAGS: hardware_required | dt_model
NUMBERS: none extracted (paywalled).

## [7] AM production-paradigm simulation (factory level)

```bibtex
@inproceedings{avventuroso2017production,
  author    = {Avventuroso, G. and Foresti, R. and Silvestri, M. and Morosini Frazzon, E.},
  title     = {Production paradigms for additive manufacturing systems: A simulation-based analysis},
  booktitle = {2017 International Conference on Engineering, Technology and Innovation (ICE/ITMC)},
  pages     = {973--981},
  year      = {2017},
  month     = {6},
  publisher = {IEEE},
  doi       = {10.1109/ice.2017.8279987}
}
```
VERIFIED: YES — Crossref `/works/10.1109/ice.2017.8279987` (IEEE, proceedings-article, pp. 973–981, 2017-06).
SUMMARY: Simulation-based comparison of production paradigms for additive manufacturing systems at shop-floor level; one of the verified AM factory-scale simulation studies requested in the brief.
FLAGS: fleet_scale
NUMBERS: none extracted (IEEE full text not accessible from this environment).

## [8] AM capacity planning

```bibtex
@article{antomarchi2019capacity,
  author  = {Antomarchi, A. L. and Guillaume, R. and Durieux, S. and Thierry, C. and Duc, E.},
  title   = {Capacity planning in additive manufacturing},
  journal = {IFAC-PapersOnLine},
  volume  = {52},
  number  = {13},
  pages   = {2556--2561},
  year    = {2019},
  issn    = {2405-8963},
  doi     = {10.1016/j.ifacol.2019.11.591}
}
```
VERIFIED: YES — Crossref `/works/10.1016/j.ifacol.2019.11.591` (Elsevier, `alternative-id = S2405896319315782`).
SUMMARY: Capacity planning for additive manufacturing at the production-system level (IFAC world-congress line). Supports the claim that AM fleet/capacity questions have been studied with operations-research simulation, separately from the machine-level DT literature.
FLAGS: fleet_scale
NUMBERS: none extracted.


## [9] AM supply-chain / production-network configuration framework

```bibtex
@article{jimo2022additive,
  author  = {Jimo, Ajeseun and Braziotis, Christos and Rogers, Helen and Pawar, Kulwant},
  title   = {Additive manufacturing: A framework for supply chain configuration},
  journal = {International Journal of Production Economics},
  volume  = {253},
  pages   = {108592},
  year    = {2022},
  month   = {11},
  issn    = {0925-5273},
  doi     = {10.1016/j.ijpe.2022.108592}
}
```
VERIFIED: YES — Crossref `/works/10.1016/j.ijpe.2022.108592` (Elsevier, `alternative-id = S0925527322001773`).
SUMMARY: Network-configuration framework for additive manufacturing spanning multi-site / multi-machine deployment decisions. Cite as the network-level (fleet) end of the AM simulation literature, complementing the machine-level DT papers.
FLAGS: fleet_scale
NUMBERS: none extracted.

## [10] FDM G-code emulator (NOT a digital twin) — FIBR3DEmul

```bibtex
@article{faria2020fibr3demul,
  author  = {Faria, Carlos and Fonseca, Jaime and Bicho, Estela},
  title   = {FIBR3DEmul---an open-access simulation solution for 3D printing processes of FDM machines
            with 3+ actuated axes},
  journal = {The International Journal of Advanced Manufacturing Technology},
  volume  = {106},
  number  = {7--8},
  pages   = {3609--3623},
  year    = {2020},
  month   = {2},
  issn    = {0268-3768},
  doi     = {10.1007/s00170-019-04713-y}
}
```
VERIFIED: YES — Crossref DOI lookup + Springer Link article page + the project README at `github.com/neuebot/FIBR3DEmul` ("Custom 3 and 5 axis FDM process simulator. C++", which links this Springer article). **Not Applied Sciences.**
SUMMARY: A G-code (ISO/DIN 66025) parser plus a V-REP/CoppeliaSim plugin that emulates a custom 5-axis printer or a standard 3-axis Cartesian printer, generating tool trajectories, emulating extrusion, and performing motion execution and printer–printer / printer–workpiece collision detection. Validated by comparing virtual vs real printer position and velocity profiles. Source code is publicly available. This is the closest existing analogue to SimTwin's G-code-driven deposition core, and it is a *simulator*, not a synchronised twin.
FLAGS: open_source | dt_model (emulation only, no live twin) | hardware_required (only for the real-vs-virtual validation)
NUMBERS: G-code standard **ISO/DIN 66025**; simulator host **V-REP/CoppeliaSim ≥ 4.0.0**; parser in **C#**, plugin in **C++** with **Boost ≥ 1.6.4** and **Eigen ≥ 3**; plane selection G17/G18/G19 with joint C cyclic (no joint limits); funded by FIBR3D project POCI-01-0145-FEDER-016414.

## [11] FDM thermal simulation (NOT a digital twin)

```bibtex
@article{zhang2018lineartime,
  author  = {Zhang, Yaqi and Shapiro, Vadim},
  title   = {Linear-Time Thermal Simulation of As-Manufactured Fused Deposition Modeling Components},
  journal = {Journal of Manufacturing Science and Engineering},
  volume  = {140},
  number  = {7},
  pages   = {071002},
  year    = {2018},
  month   = {7},
  issn    = {1087-1357},
  doi     = {10.1115/1.4039556}
}
```
VERIFIED: YES — Crossref `/works/10.1115/1.4039556` (ASME, article number 071002, issued 2018-04-04).
SUMMARY: Physics-based thermal simulation of FDM parts with a linear-time formulation, i.e. it targets scalability of the thermal solve with part size. The natural citation for the argument that FEA-grade FDM thermal simulation is too expensive for fleet-scale, many-machine, near-real-time simulation — which is exactly what SimTwin trades away.
FLAGS: dt_model (physics model, not a twin)
NUMBERS: the linear-time scaling in the number of deposited beads is the headline result; no process temperatures extracted from the abstract.


## [12] FFF rate limits and high-throughput system design (process physics + deposition)

```bibtex
@article{go2017ratelimits,
  author  = {Go, Jamison and Schiffres, Scott N. and Stevens, Adam G. and Hart, A. John},
  title   = {Rate limits of additive manufacturing by fused filament fabrication and guidelines for
            high-throughput system design},
  journal = {Additive Manufacturing},
  volume  = {16},
  pages   = {1--11},
  year    = {2017},
  month   = {8},
  issn    = {2214-8604},
  doi     = {10.1016/j.addma.2017.03.007}
}
```
VERIFIED: YES — Crossref `/works/10.1016/j.addma.2017.03.007` (Elsevier, `alternative-id = S2214860416302834`); OpenAlex confirms the record (228 citations).
SUMMARY: The standard reference for material-extrusion rate limits: maximum sustainable volumetric throughput in FFF is governed by melting / heat-transfer capacity in the hot end and by viscous pressure drop, and the paper converts these into design guidelines for high-throughput multi-nozzle FFF systems. Use it to justify capping per-extruder volumetric flow in SimTwin's deposition model.
FLAGS: hardware_required
NUMBERS: no exact figures retrievable from Crossref / Semantic Scholar abstracts (full text paywalled); the companion source [13] tabulates measured maxima (13.0–87.5 mm³/s) and is the safer numeric citation.

## [13] Volumetric flow-rate limits, nozzle geometry, filament diameter (deposition model source)

```bibtex
@article{wust2026highthroughput,
  author  = {W{\"u}st, Philipp and Kattinger, Julian and Dahmen, Frederik and Spiehl, Dieter and
            Bonten, Christian and Blaeser, Andreas},
  title   = {High-Throughput Fused Filament Fabrication of PLA: Effects of Melting Zone Length and
            Filament Diameter on Extrusion Force and Volumetric Flow Rate},
  journal = {Journal of Manufacturing and Materials Processing},
  volume  = {10},
  number  = {7},
  pages   = {233},
  year    = {2026},
  month   = {7},
  issn    = {2504-4494},
  doi     = {10.3390/jmmp10070233}
}
```
VERIFIED: YES — Crossref `/works/10.3390/jmmp10070233` (MDPI), abstract from Crossref; full text retrieved as the publisher PDF (`res.mdpi.com/d_attachment/jmmp/jmmp-10-00233/article_deploy/jmmp-10-00233.pdf`) and Table 1 read directly.
SUMMARY: Combines a load-cell test rig with non-isothermal numerical simulation to show that throughput is limited by the competition between heat-transfer-controlled melting and viscous pressure losses; longer melting zones raise attainable flow monotonically for 2.85 mm filament, while 1.75 mm filament shows an optimum melting-zone length beyond which added flow resistance dominates. Best single source for concrete volumetric-flow-rate ceilings in SimTwin's deposition / energy model.
FLAGS: hardware_required | open_source
NUMBERS: max volumetric flow **Q_max** (Table 1, E3D nozzles, PLA at 220 °C unless noted): **13.0 mm³/s** (v6, D = 0.40 mm, L = 12.5 mm); **16.0 mm³/s** (Revo, 0.40 mm, 19.6 mm); **24.0 mm³/s** (Revo HF, 0.40 mm, 19.6 mm, Voron Clockwork 2); **37.0 mm³/s** (Revo HF, 1.20 mm); **38.5 mm³/s** (Volcano, 1.20 mm, 21.0 mm); **76.5 mm³/s** (Supervolcano, 1.20 mm, 51.5 mm, E3D Titan Aero); **87.5 mm³/s** (Supervolcano, 1.20 mm, Hemera XS, 220 °C). Nozzle internal geometry: cone angle α = **60°**, D_Noz = **1.2 mm**, L_III = **2.4 mm**, D_I = **2.0 mm** (1.75 mm filament) or **3.2 mm** (2.85 mm filament); filament diameters **1.75 mm** and **2.85 mm**.

## [14] FDM/SLS/SLM/EBM/SL energy and resource inventory (concrete FDM power + SEC)

```bibtex
@article{kellens2017environmental,
  author  = {Kellens, Karel and Mertens, Raya and Paraskevas, Dimos and Dewulf, Wim and Duflou, Joost R.},
  title   = {Environmental Impact of Additive Manufacturing Processes: Does AM Contribute to a More
            Sustainable Way of Part Manufacturing?},
  journal = {Procedia CIRP},
  volume  = {61},
  pages   = {582--587},
  year    = {2017},
  issn    = {2212-8271},
  doi     = {10.1016/j.procir.2016.11.153}
}
```
VERIFIED: YES — Crossref `/works/10.1016/j.procir.2016.11.153` (Procedia CIRP 61:582–587, 2017); numbers read from the open-access CC BY-NC-ND PDF (24th CIRP Conference on Life Cycle Engineering).
SUMMARY: Comparative LCI overview of SLM, SLS, EBM, FDM and SL, including machine-level operational/standby power and specific energy consumption (SEC) tables. Its FDM table is the most directly usable published inventory for setting SimTwin's per-machine power defaults and for showing the enormous spread between machines.
FLAGS: open_source
NUMBERS (FDM, Table 6 — average power in kW operational / standby; SEC in MJ/kg): Stratasys FDM 1650 (ABS) **1.320 kW**, SEC **1247.0**; FDM 2000 (ABS) **2.200 kW**, SEC **414.7**; FDM 8000 (ABS) **2.200 kW**, SEC **83.1**; FDM Quantum (ABS) **11.000 kW**, SEC **589.3**; FDM 3000 **0.570 kW** operational / **0.530 kW** standby; FDM 400 mc (PC) **2.450 kW**, SEC **519.0–536.0**; Dimension SST **1.100 kW** / **0.400 kW** standby; Dimension 768 STT **1.100 kW** / **0.250 kW** standby, SEC **688.7**. Contrast: SLS polymer machines **1.30–16.8 kW** operational (standby **0.34–3.52 kW**), SEC **107.0–145.1 MJ/kg**; SLM **0.79–3.35 kW** (standby **0.43–0.70 kW**), SEC **83.0–588.0 MJ/kg**; EBM **2.13–2.22 kW**, SEC **60.0–375.0 MJ/kg**; SL **1.2–3.0 kW**, SEC **49.9–149.0 MJ/kg**.


## [15] Rate and energy-efficiency limits across AM processes

```bibtex
@article{gutowski2017rate,
  author  = {Gutowski, Timothy and Jiang, Sheng and Cooper, Daniel and Corman, Gero and Hausmann, Michael and
            Manson, Jan-Anders and Schudeleit, Timo and Wegener, Konrad and Sabelle, Matias and
            Ramos-Grez, Jorge and Sekulic, Dusan P.},
  title   = {Note on the Rate and Energy Efficiency Limits for Additive Manufacturing},
  journal = {Journal of Industrial Ecology},
  volume  = {21},
  number  = {S1},
  year    = {2017},
  month   = {10},
  issn    = {1088-1980},
  doi     = {10.1111/jiec.12664}
}
```
VERIFIED: YES — Crossref `/works/10.1111/jiec.12664` (JIE 21(S1), 2017-10-09); abstract returned by Crossref.
SUMMARY: Reviews process rates and energy intensities across AM with simple heat-transfer models that explain observed improvements and identify rate limits. Documents roughly one order of magnitude improvement in laser-metal raw build rate over a decade and **more than two orders of magnitude** for polymer extrusion, plus an "efficiency plateau" in laser-metal technologies (faster rates require more power with no gain in energy or rate efficiency). The right citation for the physical ceiling on extrusion throughput that any FDM simulator must respect.
FLAGS: dt_model (analytic heat-transfer model)
NUMBERS: laser-metal build-rate improvement ≈ **1 order of magnitude** over the decade; polymer (filament and pellet) extrusion **> 2 orders of magnitude**; qualitative efficiency-plateau finding.

## [16] Measured power/energy of desktop FFF and vat-polymerisation printers

```bibtex
@article{hopkins2021energy,
  author  = {Hopkins, Nicholas and Jiang, Liben and Brooks, Hadley},
  title   = {Energy consumption of common desktop additive manufacturing technologies},
  journal = {Cleaner Engineering and Technology},
  volume  = {2},
  pages   = {100068},
  year    = {2021},
  month   = {6},
  issn    = {2666-7908},
  doi     = {10.1016/j.clet.2021.100068}
}
```
VERIFIED: YES — Crossref `/works/10.1016/j.clet.2021.100068` (Elsevier, `alternative-id = S2666790821000288`); abstract from Semantic Scholar; OpenAlex confirms the record is open access.
SUMMARY: 1 Hz power measurements across a range of low-cost desktop FFF and vat-polymerisation printers, reporting volumetric specific energy use and fitting semi-empirical equations that predict energy use from simple print metrics. The single most directly usable source for SimTwin's default per-print energy model on hobby-class FDM hardware.
FLAGS: hardware_required | open_source | synthetic_dataset (the fitted predictive equations are directly reusable as simulator defaults)
NUMBERS: **volumetric specific energy use 24.8–85.7 kJ/cm³ for FFF** and **10.8–21.5 kJ/cm³ for vat polymerisation**; power sampled at **1 Hz**. Converted for PLA at ρ = 1.24 g/cm³ the FFF band is ≈ **5.6–19.2 kWh/kg** of deposited material — *our unit conversion, not the authors' figure*.

## [17] Process parameters vs specific energy consumption in FDM

```bibtex
@article{lunetto2020correlation,
  author  = {Lunetto, Vincenzo and Priarone, Paolo C. and Galati, Manuela and Minetola, Paolo},
  title   = {On the correlation between process parameters and specific energy consumption in fused
            deposition modelling},
  journal = {Journal of Manufacturing Processes},
  volume  = {56},
  pages   = {1039--1049},
  year    = {2020},
  month   = {8},
  issn    = {1526-6125},
  doi     = {10.1016/j.jmapro.2020.06.002}
}
```
VERIFIED: YES — Crossref `/works/10.1016/j.jmapro.2020.06.002` (Elsevier, `alternative-id = S1526612520303753`); abstract from Semantic Scholar.
SUMMARY: Experimental FDM study (ABS and PC-ABS) showing that the specific-energy-consumption framework used for conventional unit processes transfers to FDM, and that raising the **average deposition rate** along the deposition path is an effective route to lower specific printing energy. Provides the functional form (SEC as a function of layer thickness and infill strategy) that SimTwin's energy model needs.
FLAGS: hardware_required
NUMBERS: materials **ABS** and **PC-ABS**; analysed variables = **layer thickness** and **infill strategy**; responses = process time and energy consumption at the FDM unit-process level; empirical predictive models of energy efficiency vs process variables are proposed (numeric coefficients are in the paywalled full text and are not reproduced here).


## [18] FDM process parameters → energy consumption (PLA, Taguchi L27)

```bibtex
@article{enemuoh2021effect,
  author  = {Enemuoh, Emmanuel U. and Duginski, Stefan and Feyen, Connor and Menta, Venkata G.},
  title   = {Effect of Process Parameters on Energy Consumption, Physical, and Mechanical Properties of
            Fused Deposition Modeling},
  journal = {Polymers},
  volume  = {13},
  number  = {15},
  pages   = {2406},
  year    = {2021},
  month   = {7},
  issn    = {2073-4360},
  doi     = {10.3390/polym13152406}
}
```
VERIFIED: YES — Crossref `/works/10.3390/polym13152406` (MDPI), abstract from Crossref; full text read from Europe PMC **PMC8347717** (setup and ANOVA tables read directly).
SUMMARY: Taguchi L27 + ANOVA study of five FDM parameters on energy consumption, production time, part weight, dimensional accuracy, hardness and tensile strength for PLA on an Ultimaker machine, with energy metered at the wall. Establishes the ranking of parameter effects on energy, which is the sensitivity structure a simulator's energy sub-model should reproduce.
FLAGS: hardware_required | open_source
NUMBERS: machine **Ultimaker S5** (Ultimaker S3 for some sample builds), heated bed held at **60 °C**, raster orientation **45°**, slicer **Ultimaker Cura**, energy metered with an in-line energy meter; layer resolution range **20–300 µm**; factor levels: layer thickness **0.1 / 0.2 / 0.3 mm**, infill density **20–100 %**, infill pattern (triangle / grid / gyroid / cubic), print speed **40 / 60 / 80 mm/s**, shell thickness **0.4 / 0.6 / 1.2 mm** (0.8 mm nominal; nozzle diameter **0.4 mm**). ANOVA F-values for energy consumption: layer thickness **F = 704.57 (p = 0.000)**, print speed **F = 204.75 (p = 0.000)**, infill density **F = 81.50 (p = 0.000)**, infill pattern **F = 9.12 (p = 0.002)**, shell thickness **F = 3.18 (p = 0.069, n.s.)**. Effect ranking on energy: **layer thickness (Δ = 0.1811 dB) > print speed (Δ = 0.0939 dB) > infill density > infill pattern > shell thickness**. Energy-minimising setting = layer thickness **0.3 mm**, infill density **20 %**, **triangle** infill, print speed **80 mm/s**, shell thickness **0.4 mm**. Context figure quoted from US EIA: US manufacturing accessories consume ≈ **1.35 × 10¹⁹ J/yr**, ≈ **521 MT CO₂-eq**.

## [19] FFF power-demand characterisation + discrete-event simulation of a virtual AM plant

```bibtex
@article{kim2022characterization,
  author  = {Kim, Kyudong and Noh, Heena and Park, Kijung and Jeon, Hyun Woo and Lim, Sunghoon},
  title   = {Characterization of power demand and energy consumption for fused filament fabrication using
            CFR-PEEK},
  journal = {Rapid Prototyping Journal},
  volume  = {28},
  number  = {7},
  pages   = {1394--1406},
  year    = {2022},
  month   = {7},
  issn    = {1355-2546},
  doi     = {10.1108/RPJ-07-2021-0188}
}
```
VERIFIED: YES — Crossref `/works/10.1108/RPJ-07-2021-0188` (Emerald); structured abstract returned by Crossref.
SUMMARY: Full-factorial DoE over layer thickness and printing speed for CFR-PEEK FFF, regressing **average power demand** and **total energy consumption** on material addition rate (MAR); the regression models are then embedded in a **discrete-event simulation of a virtual AM plant** with multiple FFF machines and part designs, comparing higher-MAR-first-out, FIFO and lower-MAR-first-out dispatch rules. The strongest single bridge in Cluster B between machine-level energy models and fleet-level AM simulation, and the closest published template for SimTwin's energy-plus-fleet design.
FLAGS: hardware_required | fleet_scale | dt_model
NUMBERS: factors = **layer thickness** and **printing speed** (full factorial); responses = average power demand and total energy consumption modelled as functions of **material addition rate (MAR)**; AM plant = **discrete-event simulation of multiple FFF machines** producing aircraft parts, evaluated on order lead time, production volume, power demand and energy consumption; headline finding: the decrease in energy consumption **dominates** the increase in power demand as MAR rises, and **higher-MAR-first-out** is the best dispatch strategy.

## [20] Measured filament densities (PLA / ABS / PETG / HIPS / PVB)

```bibtex
@article{hofmann2026xray,
  author  = {Hofmann, Thomas and Buschmann, Martin and Homolka, Peter},
  title   = {X-Ray Attenuation Properties of Additive Manufacturing and 3D Printing Materials for Mimicking
            Tissues in Radiographic Phantoms Measured by CT from 70 to 140 kV: 2025 Update},
  journal = {Biomimetics},
  volume  = {11},
  number  = {3},
  pages   = {202},
  year    = {2026},
  month   = {3},
  issn    = {2313-7673},
  doi     = {10.3390/biomimetics11030202}
}
```
VERIFIED: YES — Crossref `/works/10.3390/biomimetics11030202` (MDPI), abstract from Crossref; density table read from Europe PMC full text **PMC13023429** (Table 3).
SUMMARY: Measures 22 thermoplastic filaments and 27 photopolymer resins, reporting both measured printed-part density and manufacturer nominal filament density with ±0.01 g/cm³ uncertainty. Cleanest peer-reviewed source for the filament densities a deposition/mass model needs, and it also documents the systematic porosity gap between printed part and nominal filament density.
FLAGS: open_source
NUMBERS (nominal filament density g/cm³, measured printed density range in brackets): **PLA 1.22–1.27** (typ. **1.24**; measured 1.21–1.27); **ABS 1.04–1.10** (typ. **1.04**; measured 1.02–1.11); **PETG/PCTG 1.23–1.28** (typ. **1.27**; measured 1.22–1.30); **HIPS 1.05** (measured 0.99–1.03); **PVB 1.08** (measured 1.10). Printed density falls below nominal by **Δρ ≈ 0.02–0.06 g/cm³** (HIPS worst), i.e. ≈ **2–6 % porosity** — relevant to mass and energy-per-gram bookkeeping. Measurement uncertainty **± 0.01 g/cm³**.


---

## SYNTHESIS

Cluster B splits into three literatures that rarely cite each other, and the seam between them is SimTwin's opening. The AM digital-twin reviews [1, 2] and the FDM DT implementations [3, 4, 5, 6] are all machine-coupled: Pantelidakis et al. [3] needs a Lulzbot Taz Workhorse, a Raspberry Pi 3, a Yocto-Thermocouple (−75 to 260 °C, < 30 ms, ± 2.2 °C) and VL53L0X ToF sensors (50–1200 mm, 3–12 % accuracy) before the twin means anything, and its own validation shows the sensor-driven twin is 2.69 mm off in X and 3.2 mm off in Z — adequate for state mirroring, useless for geometry-level fault physics. Henson et al. [4] is the closest published analogue to SimTwin's fault-detection story and is explicit that twins of real prints are generated **offline at specific layers** precisely because online fidelity is unaffordable; it detected failure in 2 of 3 test prints. The factory-level AM simulation work [7, 8, 9] and Kim et al.'s discrete-event AM plant [19] sit at the opposite extreme: queueing, capacity, dispatch and supply-chain configuration with no machine physics at all. Nothing in the verified set gives a fleet of FDM machines with G-code-level deposition physics, a machine-level energy model, and injectable faults in one open-source package. On the simulator side, FIBR3DEmul [10] is the nearest existing open-source G-code emulator (ISO/DIN 66025 parsing, 3-axis and 5-axis kinematics, extrusion emulation, collision detection, C++/C# + CoppeliaSim, public source), but it is a one-machine emulator with no twin semantics, no energy model, no fault injection and no fleet abstraction. The deposition-physics literature supplies hard ceilings for that core: Go et al. [12] establish that throughput is bounded by melting capacity versus viscous pressure drop, and Wüst et al. [13] tabulate measured maxima from **13.0 mm³/s** (0.40 mm E3D v6, PLA at 220 °C) to **76.5–87.5 mm³/s** (1.20 mm Supervolcano), with 1.75 mm filament showing an optimum melting-zone length while 2.85 mm filament improves monotonically. Energy defaults should be anchored on measurements rather than nameplate ratings: Hopkins et al. [16] measured **24.8–85.7 kJ/cm³** volumetric specific energy for desktop FFF at 1 Hz, Kellens et al. [14] inventory industrial FDM at **0.57–11.0 kW** operational and **0.25–0.53 kW** standby with SEC spanning **83.1–1247 MJ/kg**, and Gutowski et al. [15] supply the heat-transfer reasoning for why polymer extrusion improved by more than two orders of magnitude in build rate. The parameter sensitivities are consistent across sources and should shape SimTwin's energy sub-model: Enemuoh et al. [18] rank layer thickness (F = 704.57) above print speed (F = 204.75) above infill density (F = 81.50) for energy on an Ultimaker S5 at a 60 °C bed, and Lunetto et al. [17] show that raising average deposition rate lowers specific printing energy — energy is closer to a function of deposition path and throughput than of nozzle temperature alone. For mass bookkeeping, Hofmann et al. [20] give peer-reviewed nominal filament densities (PLA 1.24, ABS 1.04, PETG 1.27 g/cm³) plus a systematic 2–6 % printed-part porosity gap that a naive density-times-volume mass model will silently ignore. Two structural gaps follow directly: no verified AM DT paper in this cluster reports MQTT/Sparkplug-style telemetry — [3] uses an HTTP/REST Flask API plus OctoPrint, so SimTwin's MQTT/IIoT interface is a genuine differentiator here rather than a reimplementation — and no verified source couples fleet-scale dispatch with machine-level deposition-and-energy physics, which is precisely the coupling SimTwin claims. Write-up caveats: the brief's journal attributions for the "JMS 2024" review and the "JIM 2022" digital-twin ecosystem paper are both wrong (corrections 1–2), the Procedia Manufacturing DOI in the brief is wrong (correction 3), FIBR3DEmul is IJAMT not Applied Sciences (correction 4), and the Kellens "Energy productivity" JIE paper and the Kreiger & Pearce *Energy Policy* paper could not be verified at any DOI and must not be cited (corrections 5–6).
