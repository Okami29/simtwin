"""Final targeted Crossref resolution for the last outstanding bibliography keys."""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "SimTwinPreprint/1.0 (mailto:simtwin.research.contact@outlook.com)"}

QUERIES: dict[str, tuple[str, str]] = {
    "ncs_survey": ("Networked control systems A survey", "Pustek"),
    "pdm_dataset": ("predictive maintenance dataset machine data", "Makis"),
    "fdm_energy": ("energy consumption fused deposition modeling machine", "Gutowski"),
    "mex_energy": ("energy consumption material extrusion additive manufacturing process parameters", "Geem"),
    "pdmsurvey": ("predictive maintenance survey machine learning industry", "Anawar"),
    "syncprob": ("digital twin synchronization problem", "Barricelli"),
}


def main() -> int:
    out: dict[str, list] = {}
    for key, (title, author) in QUERIES.items():
        url = ("https://api.crossref.org/works?"
               + urllib.parse.urlencode({"query.bibliographic": title,
                                          "query.author": author, "rows": "6"}))
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                items = json.loads(r.read())["message"].get("items", [])
            out[key] = [{"doi": it.get("DOI"),
                         "title": (it.get("title") or [""])[0][:160],
                         "container": (it.get("container-title") or [""])[0][:90],
                         "year": ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0],
                         "volume": it.get("volume"), "issue": it.get("issue"),
                         "page": it.get("page"), "article": it.get("article-number"),
                         "authors": "; ".join(f"{a.get('family','')} {a.get('given','')}".strip()
                                              for a in (it.get("author") or [])[:6])}
                        for it in items]
            print(f"== {key}", flush=True)
            for c in out[key]:
                print(f"   {c['year']} | {c['doi']} | {c['title'][:74]} | {c['container'][:34]}",
                      flush=True)
        except Exception as exc:  # noqa: BLE001
            out[key] = [{"error": str(exc)}]
            print(f"== {key} ERROR {exc}", flush=True)
        time.sleep(0.5)
    (ROOT / "results" / "bibliography_final_candidates.json").write_text(
        json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
