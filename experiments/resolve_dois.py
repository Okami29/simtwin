#!/usr/bin/env python3
"""Resolve unverified bibliography keys against Crossref by title/author search.

Writes results/bibliography_search_candidates.json.  Used only to repair DOIs;
the authoritative audit remains experiments/verify_bibliography.py.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "SimTwinPreprint/1.0 (mailto:simtwin.research.contact@outlook.com)"}

QUERIES: dict[str, tuple[str, str]] = {
    # key: (bibliographic title query, author filter)
    "park1998ncs": ("A control method in networked control systems", "Park"),
    "pustek2019ncs": ("Bibliographical review on cyber attacks from a control oriented perspective", "Pustek"),
    "makis2020ai4i": ("AI4I 2020 Predictive Maintenance Dataset", "Makis"),
    "isermann2005fault": ("Model-based fault-detection and diagnosis Part I", "Isermann"),
    "szydlowski2021dataset": ("Dataset for anomalies detection in 3D printing", "Szydlowski"),
    "rahmandad2012repro": ("Reporting guidelines for simulation-based research", "Rahmandad"),
    "kellens2017energy": ("Overview of energy productivity in 3D printing", "Kellens"),
    "malamed2015energy": ("A simulative study on energy consumption of the fused deposition modeling process", "Malamed"),
    "valizadeh2021energy": ("Energy efficiency of material extrusion additive manufacturing", "Valizadeh"),
    "kreiger2013energy": ("Environmental impacts of 3D printing at home", "Kreiger"),
    "alghamdi2023sync": ("A framework for digital twin synchronization", "Alghamdi"),
    "grieves2017dt": ("Digital Twin Mitigating Unpredictable Undesirable Emergent Behavior in Complex Systems", "Grieves"),
    "tao2019dtii": ("Digital Twin in Industry State of the Art", "Tao"),
    "fuller2020dt": ("Digital twin enabled technologies challenges and research opportunities", "Fuller"),
    "barricelli2019dt": ("A systematic literature review on digital twin", "Barricelli"),
    "liu2024dtms": ("Digital Twin-based manufacturing system survey novel reference model", "Liu"),
    "aznar2025dtm": ("Digital twin methodologies systematic literature review manufacturing", "Aznar-Lapuente"),
    "uhlenkamp2022maturity": ("Digital Twin Maturity Model conceptual framework assessing digital twins factory production", "Uhlenkamp"),
    "iso23247": ("Digital twin framework for manufacturing overview and general principles", ""),
    "iso30173": ("Digital twin representations of physical systems", ""),
    "grieves2014dt": ("Digital Twin Manufacturing Excellence through Virtual Factory Replication", "Grieves"),
    "tao2019fivelayer": ("Digital twin-driven product design, manufacturing and service with big data", "Tao"),
}


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())


def main() -> int:
    out = {}
    for key, (title, author) in QUERIES.items():
        q = {"query.bibliographic": title, "rows": "5"}
        if author:
            q["query.author"] = author
        url = "https://api.crossref.org/works?" + urllib.parse.urlencode(q)
        try:
            msg = fetch(url)["message"]
            out[key] = [
                {
                    "doi": it.get("DOI"),
                    "title": (it.get("title") or [""])[0][:150],
                    "container": (it.get("container-title") or [""])[0][:90],
                    "year": ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0],
                    "volume": it.get("volume"),
                    "issue": it.get("issue"),
                    "page": it.get("page"),
                    "article": it.get("article-number"),
                    "type": it.get("type"),
                    "authors": "; ".join(
                        f"{a.get('family', '')} {a.get('given', '')}".strip()
                        for a in (it.get("author") or [])[:6]
                    ),
                }
                for it in msg.get("items", [])
            ]
            print(f"== {key}")
            for c in out[key]:
                print(f"   {c['year']} | {c['doi']} | {c['title'][:70]} | {c['container'][:45]}")
        except Exception as e:  # noqa: BLE001
            out[key] = {"error": str(e)}
            print(f"== {key}  ERROR {e}")
        time.sleep(0.4)
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "bibliography_search_candidates.json").write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
