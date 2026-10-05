#!/usr/bin/env python3
"""Crossref verification of the SimTwin preprint bibliography.

Every reference cited in the manuscript is checked against the Crossref REST API
(https://api.crossref.org).  A reference is marked VERIFIED only when the DOI
resolves to a Crossref record AND the claimed title matches the record title
(normalised token overlap >= 0.8).  Non-DOI sources (standards, white papers,
the MQTT OASIS specifications) are verified by HTTP reachability of the
official publisher URL.

Outputs:
  results/bibliography_verification.json  - full machine-readable audit
  results/bibliography_verification.csv   - compact audit table

Run:  python experiments/verify_bibliography.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "SimTwinPreprint/1.0 (mailto:simtwin.research.contact@outlook.com)"}

# key -> (claimed title, claimed year, doi, url)
REFS: dict[str, tuple[str, int, str, str]] = {
    # --- digital twin foundations -----------------------------------------
    "grieves2014dt": ("Digital Twin Manufacturing Excellence through Virtual Factory Replication", 2014, "", "https://www.3ds.com/fileadmin/PRODUCTS-SERVICES/DELMIA/PDF/Whitepaper/DELMIA-APRISO-Digital-Twin-Whitepaper.pdf"),
    "grieves2017dt": ("Digital Twin Mitigating Unpredictable Undesirable Emergent Behavior in Complex Systems", 2017, "10.1007/978-3-319-38756-7_4", ""),
    "tao2019dtii": ("Digital Twin in Industry State of the Art", 2019, "10.1109/TII.2018.2873186", ""),
    "tao2019fivelayer": ("Digital twin-driven product design, manufacturing and service with big data", 2019, "10.1007/s00170-017-0582-1", ""),
    "fuller2020dt": ("Digital Twin Enabled Technologies, Challenges and Research Opportunities", 2020, "10.1080/00207543.2020.1751644", ""),
    "barricelli2019dt": ("A Systematic Literature Review on Digital Twin", 2019, "10.1016/j.rcim.2018.08.012", ""),
    "iso23247": ("Digital twin framework for manufacturing Part 1 Overview and general principles", 2021, "", "https://www.iso.org/standard/77319.html"),
    "iso30173": ("Information technology Digital twin representations of physical systems", 2023, "", "https://www.iso.org/standard/74846.html"),
    # --- manufacturing DT surveys / maturity ---------------------------------
    "liu2024dtms": ("Digital Twin-based manufacturing system a survey based on a novel reference model", 2024, "10.1007/s10845-023-02172-7", ""),
    "aznar2025dtm": ("Digital twin methodologies A systematic literature review on methodologies for developing digital twins in the manufacturing domain", 2025, "10.1016/j.jmsy.2025.100915", ""),
    "uhlenkamp2022maturity": ("Digital Twin Maturity Model A Conceptual Framework for Assessing Digital Twins in Factory Production", 2022, "10.1109/ACCESS.2022.3141379", ""),
    # --- digital twin synchronization ---------------------------------------
    # --- additive manufacturing digital twins --------------------------------
    "jyeniskhan2024amdt": ("Exploring the integration of digital twin and additive manufacturing technologies", 2024, "10.1016/j.ijlmm.2024.06.004", ""),
    "pantelidakis2022dt": ("A digital twin ecosystem for additive manufacturing using a real-time development platform", 2022, "10.1007/s00170-022-09164-6", ""),
    "henson2021dt": ("A digital twin strategy for major failure detection in fused deposition modeling processes", 2021, "10.1016/j.promfg.2021.06.039", ""),
    "fibremul2022": ("FIBR3DEmul an open-access simulation solution for 3D printing processes of FDM machines with 3 actuated axes", 2020, "10.1007/s00170-019-04713-y", ""),
    # --- IIoT / MQTT / OPC UA ------------------------------------------------
    "mqtt5oasis": ("MQTT Version 5.0 Specification for Line Structured Text", 2019, "", "https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html"),
    "mqtt311oasis": ("MQTT Version 3.1.1 Specification for Line Structured Text", 2014, "", "http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html"),
    "mtdn2025": ("MQTT Based Data Distribution Framework for Digital Twin Networks", 2025, "10.1145/3726122.3726269", ""),
    "kumar2024dtfactory": ("Design and Implementation of Digital Twin Factory Synchronized in Real-Time Using MQTT", 2024, "10.3390/machines12110759", ""),
    "park1998ncs": ("A Control Method in Networked Control Systems", 1998, "10.1109/TCST.1998.722195", ""),
    "zhang2001ncs": ("Stability of Networked Control Systems", 2001, "10.1109/9.905405", ""),
    "pustek2019ncs": ("Networked control systems A bibliometric analysis", 2019, "10.1016/j.arcontrol.2019.08.002", ""),
    # --- open-source DT / co-simulation frameworks ---------------------------
    "robles2023opentwins": ("OpenTwins An open-source framework for the development of next-gen compositional digital twins", 2023, "10.1016/j.compind.2023.104007", ""),
    "infante2025opentwins": ("Distributed digital twins on the open-source OpenTwins framework", 2025, "10.1016/j.aei.2024.102970", ""),
    "larsen2024recast": ("RECAST An Open-Source Digital Twin Framework for Industrial Production Environments", 2024, "10.1007/978-3-031-74482-2_19", ""),
    "schwede2024sbdm": ("Learning Simulation-Based Digital Twins for Discrete Material Flow Systems A Review", 2024, "10.1109/WSC63780.2024.10838729", ""),
    # --- synthetic data, fault injection, anomaly detection ------------------
    "makis2020ai4i": ("AI4I 2020 Predictive Maintenance Dataset", 2020, "10.1016/j.dib.2020.106498", ""),
    "synthpdm2026": ("Synthetic data for predictive maintenance a systematic literature review", 2026, "10.1007/s10845-026-02795-6", ""),
    "breunig2000lof": ("LOF Identifying Density-Based Local Outliers", 2000, "10.1145/342009.335388", ""),
    "liu2008iforest": ("Isolation Forest", 2008, "10.1109/ICDM.2008.17", ""),
    "scholkopf2001ocsvm": ("Estimating the Support of a High-Dimensional Distribution", 2001, "10.1162/089976601750264965", ""),
    "blazquez2021lof": ("A Review on Outlier Anomaly Detection in Time Series Data", 2021, "10.1145/3444690", ""),
    "darban2024deep": ("Deep Learning for Time Series Anomaly Detection A Survey", 2024, "10.1145/3691338", ""),
    "isermann2005fault": ("Model-based fault-detection and diagnosis Part I", 2005, "10.1016/j.conengprac.2004.04.001", ""),
    "szydlowski2021dataset": ("Dataset for Anomalies Detection in 3D Printing", 2021, "10.1038/s41597-021-00450-w", ""),
    "rahmandad2012repro": ("Reporting Guidelines for Simulation-Based Research", 2012, "10.1177/0049124110362615", ""),
    # --- FDM physics / energy ------------------------------------------------
    "kellens2017energy": ("Overview of energy productivity in 3D printing", 2017, "10.1016/j.rser.2016.08.023", ""),
    "malamed2015energy": ("A Simulative Study on Energy Consumption of the Fused Deposition Modeling FDM Process in Additive Manufacturing", 2015, "10.1016/j.procir.2015.07.042", ""),
    "valizadeh2021energy": ("Energy efficiency of material extrusion additive manufacturing", 2021, "10.1016/j.jclepro.2021.127411", ""),
    "kreiger2013energy": ("Environmental impacts of 3D printing at home", 2013, "10.1021/es305112n", ""),
    "tan2024sync": ("The digital twin synchronization problem Framework, formulations, and analysis", 2024, "10.1080/24725854.2023.2253869", ""),
    "alghamdi2023sync": ("A Framework for Digital Twin Synchronization A Path to Realizing the Full Potential of Digital Twins", 2023, "10.1016/j.jii.2023.100526", ""),
    "kaul2012aoi": ("Real-Time Status How Often Should One Update", 2012, "10.1109/INFCOM.2012.6195689", ""),
    "yates2021aoi": ("Age of Information An Introduction and Survey", 2021, "10.1109/JSAC.2021.3065072", ""),
    "zhang2001ncs": ("Stability of networked control systems", 2001, "10.1109/37.898794", ""),
    "walsh2002ncs": ("Stability analysis of networked control systems", 2002, "10.1109/87.998034", ""),
    "tonelli2020mqtt": ("The Use of MQTT in M2M and IoT Systems A Survey", 2020, "10.1109/ACCESS.2020.3035849", ""),
    "lei2024mqttsec": ("Securing the IoT Application Layer From an MQTT Protocol Perspective Challenges and Research Prospects", 2024, "10.1109/COMST.2024.3372630", ""),
    "martins2021mqttperf": ("A Performance Analysis of Internet of Things Networking Protocols Evaluating MQTT CoAP OPC UA", 2021, "10.3390/app11114879", ""),
    "florez2021coapmqtt": ("Performance evaluation of CoAP and MQTT with security support for IoT environments", 2021, "10.1016/j.comnet.2021.108338", ""),
    "tonelli2021brokers": ("Stress-Testing MQTT Brokers A Comparative Analysis of Performance Measurements", 2021, "10.3390/en14185817", ""),
    "slemda2021sladta": ("Digital Twin Data Pipeline Using MQTT in SLADTA", 2021, "10.1007/978-3-030-69373-2_7", ""),
    "kaltenerstaleh2020dtiot": ("Digital Twin and Internet of Things Current Standards Landscape", 2020, "10.3390/app10186519", ""),
    "cunha2023dosmqtt": ("DoS DDoS MQTT IoT A dataset for evaluating intrusions in IoT networks using the MQTT protocol", 2023, "10.1016/j.comnet.2023.109809", ""),
    "cho2010opcua": ("Performance evaluation of OPC UA", 2010, "10.1109/ETFA.2010.5641184", ""),
    "shafique2022pubsub": ("A Survey and Comparison of Publish Subscribe Protocols for the Industrial Internet of Things", 2022, "10.1145/3567445.3571107", ""),
}




def norm_title(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return " ".join(s.split())


def tokens(s: str) -> set[str]:
    stop = {"a", "an", "the", "of", "for", "and", "in", "on", "to", "with",
            "based", "toward", "towards", "is", "are", "its", "it", "from"}
    return {t for t in norm_title(s).split() if t not in stop}


def title_overlap(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def fetch(url: str, tries: int = 3):
    err = b"unreachable"
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read()
        except Exception as e:  # noqa: BLE001
            err = str(e).encode()
            time.sleep(1.5 * (i + 1))
    return 0, err


def main() -> int:
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    rows = []
    for key, (title, year, doi, url) in REFS.items():
        rec = {"key": key, "claimed_title": title, "claimed_year": year,
               "doi": doi or None, "url": url or None}
        if doi:
            status, body = fetch(f"https://api.crossref.org/works/{doi}")
            if status == 200:
                m = json.loads(body)["message"]
                ct = (m.get("title") or [""])[0]
                year_rec = None
                for fld in ("published-print", "published-online", "issued", "created"):
                    dp = (m.get(fld) or {}).get("date-parts")
                    if dp and dp[0] and dp[0][0]:
                        year_rec = dp[0][0]
                        break
                ev = m.get("event") or {}
                rec.update({
                    "crossref_title": ct,
                    "title_overlap": round(title_overlap(title, ct), 3),
                    "crossref_year": year_rec,
                    "container": (m.get("container-title") or [""])[0] or ev.get("name", "")
                                 or m.get("publisher", ""),
                    "volume": m.get("volume", ""),
                    "issue": m.get("issue", ""),
                    "page": m.get("page", ""),
                    "article_number": m.get("article-number", ""),
                    "publisher": m.get("publisher", ""),
                    "type": m.get("type", ""),
                    "issn": (m.get("ISSN") or [""])[0],
                    "authors": [f"{a.get('family', '')}, {a.get('given', '')}".strip(", ")
                                for a in m.get("author", [])],
                    "status": "crossref-ok",
                })
                rec["verified"] = rec["title_overlap"] >= 0.8
            else:
                rec["status"] = f"crossref HTTP {status}: {body[:150].decode('utf-8', 'ignore')}"
                rec["verified"] = False
        else:
            status, body = fetch(url) if url else (0, b"no url")
            rec["status"] = f"url HTTP {status}"
            rec["verified"] = status == 200
        rows.append(rec)
        flag = "OK  " if rec["verified"] else "FAIL"
        print(f"{flag} {key:24s} {rec.get('crossref_title', url or doi)[:64]}")

    (out_dir / "bibliography_verification.json").write_text(json.dumps(rows, indent=2))
    fields = ["key", "verified", "status", "doi", "crossref_title", "claimed_title",
              "title_overlap", "crossref_year", "claimed_year", "container", "volume",
              "issue", "page", "article_number", "publisher", "type", "issn", "authors", "url"]
    with open(out_dir / "bibliography_verification.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            r["authors"] = "; ".join(r.get("authors", []))
            w.writerow(r)

    n_ok = sum(1 for r in rows if r["verified"])
    print(f"\n{n_ok}/{len(rows)} verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
