"""Targeted Crossref title searches for bibliography keys still unresolved."""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "SimTwinPreprint/1.0 (mailto:simtwin.research.contact@outlook.com)"}

QUERIES: dict[str, str] = {
    "park1998ncs": "A control method in networked control systems",
    "pustek2019ncs": "Bibliographical review on cyber attacks from a control oriented perspective",
    "makis2020ai4i": "AI4I 2020 Predictive Maintenance Dataset",
    "isermann2005fault": "Model-based fault-detection and diagnosis - Part I",
    "szydlowski2021dataset": "Dataset for anomalies detection in 3D printing",
    "rahmandad2012repro": "Reporting Guidelines for Simulation-Based Research",
    "kellens2017energy": "Overview of energy productivity in 3D printing",
    "malamed2015energy": "A Simulative Study on Energy Consumption of the Fused Deposition Modeling FDM Process in Additive Manufacturing",
    "valizadeh2021energy": "Energy efficiency of material extrusion additive manufacturing",
    "kreiger2013energy": "Environmental impacts of new manufacturing technologies 3-D printing",
    "alghamdi2023sync": "A framework for digital twin synchronization path to realizing the full potential of digital twins",
    "henson2021dt": "digital twin strategy major failure detection fused deposition modeling",
    "synthpdm2026": "synthetic data generation predictive maintenance industrial",
}


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())


def main() -> int:
    out: dict[str, list] = {}
    for key, title in QUERIES.items():
        url = ("https://api.crossref.org/works?"
               + urllib.parse.urlencode({"query.title": title, "rows": "6"}))
        try:
            items = fetch(url)["message"].get("items", [])
            out[key] = [{"doi": it.get("DOI"),
                         "title": (it.get("title") or [""])[0][:160],
                         "container": (it.get("container-title") or [""])[0][:90],
                         "year": ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0],
                         "volume": it.get("volume"), "issue": it.get("issue"),
                         "page": it.get("page"), "article": it.get("article-number"),
                         "type": it.get("type"),
                         "authors": "; ".join(f"{a.get('family','')} {a.get('given','')}".strip()
                                              for a in (it.get("author") or [])[:6])}
                        for it in items]
            print(f"== {key}", flush=True)
            for c in out[key]:
                print(f"   {c['year']} | {c['doi']} | {c['title'][:76]}", flush=True)
        except Exception as exc:  # noqa: BLE001
            out[key] = [{"error": str(exc)}]
            print(f"== {key} ERROR {exc}", flush=True)
        time.sleep(0.5)
    (ROOT / "results" / "bibliography_title_candidates.json").write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
