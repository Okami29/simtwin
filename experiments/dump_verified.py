"""Dump verified bibliography rows with full Crossref metadata for .bib repair."""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "SimTwinPreprint/1.0 (mailto:simtwin.research.contact@outlook.com)"}

rows = json.load(open(ROOT / "results" / "bibliography_verification.json"))
keys = [r["key"] for r in rows if r["verified"]]
by_key = {r["key"]: r for r in rows}
extra = ["tao2019fivelayer", "fuller2020dt", "barricelli2019dt", "aznar2025dtm",
         "uhlenkamp2022maturity", "isermann2005fault", "szydlowski2021dataset",
         "rahmandad2012repro", "alghamdi2023sync", "kellens2017energy"]
replacements = {
    "tao2019fivelayer": "10.1007/s00170-017-0233-1",
    "fuller2020dt": "10.1109/access.2020.2998358",
    "barricelli2019dt": "10.1109/access.2019.2953499",
    "aznar2025dtm": "10.1016/j.future.2025.107997",
    "uhlenkamp2022maturity": "10.1109/access.2022.3186353",
    "isermann2005fault": "10.1016/j.arcontrol.2004.12.002",
    "szydlowski2021dataset": "10.1007/978-3-030-77970-2_50",
    "rahmandad2012repro": "10.1002/sdr.1481",
    "alghamdi2023sync": "10.1080/24725854.2023.2253869",
    "kellens2017energy": "10.1111/jiec.12668",
}

out = {}
for key in keys + extra:
    doi = replacements.get(key) or by_key[key].get("doi")
    if not doi:
        out[key] = {"no_doi": True, "claimed_title": by_key[key]["claimed_title"],
                    "claimed_year": by_key[key]["claimed_year"]}
        print(f"{key}\tNO-DOI\t{by_key[key]['claimed_title']} ({by_key[key]['claimed_year']})")
        continue
    try:
        req = urllib.request.Request(f"https://api.crossref.org/works/{doi}", headers=UA)
        with urllib.request.urlopen(req, timeout=40) as r:
            it = json.loads(r.read())["message"]
        out[key] = {"doi": doi, "title": (it.get("title") or [""])[0],
                    "container": (it.get("container-title") or [""])[0],
                    "year": ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0],
                    "volume": it.get("volume"), "issue": it.get("issue"),
                    "page": it.get("page"), "article": it.get("article-number"),
                    "publisher": it.get("publisher"), "type": it.get("type"),
                    "authors": [[a.get("family"), a.get("given")]
                                for a in (it.get("author") or [])]}
        print(f"{key}\t{doi}\t{out[key]['year']}\t{out[key]['title'][:70]}")
    except Exception as exc:  # noqa: BLE001
        out[key] = {"error": str(exc), "doi": doi}
        print(f"{key}\tERROR {exc}")
    time.sleep(0.35)

(ROOT / "results" / "bibliography_verified.json").write_text(json.dumps(out, indent=2))
print(f"\nwrote results/bibliography_verified.json ({len(out)} entries)")
