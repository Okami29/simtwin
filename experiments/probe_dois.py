"""Direct DOI probes for the last outstanding bibliography keys."""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "SimTwinPreprint/1.0 (mailto:simtwin.research.contact@outlook.com)"}

DOIS = [
    "10.1016/j.dib.2020.104622",
    "10.3390/ma8125465",
    "10.1021/es305112n",
    "10.1109/87.754113",
    "10.1109/TCST.1998.722195",
    "10.1016/j.jclepro.2021.127411",
    "10.1016/j.rser.2017.02.038",
    "10.1109/9.722195",
    "10.1002/sdr.1481",
    "10.1080/24725854.2023.2253869",
    "10.1111/jiec.12668",
    "10.1016/j.arcontrol.2004.12.002",
    "10.1007/978-3-030-77970-2_50",
    "10.1007/s00170-017-0233-1",
    "10.1109/access.2020.2998358",
    "10.1109/access.2019.2953499",
    "10.1016/j.future.2025.107997",
    "10.1109/access.2022.3186353",
    "10.1109/jiot.2017.2685639",
    "10.1109/tii.2016.2541998",
    "10.1109/tii.2015.2416450",
    "10.1109/tcst.2012.2184820",
    "10.1109/tii.2019.2928584",
    "10.1109/access.2020.2998358",
    "10.1016/j.ijpe.2019.107544",
    "10.1016/j.rcim.2017.09.004",
    "10.1016/j.ijmachtools.2019.103479",
    "10.1016/j.jmatprotec.2018.05.031",
    "10.1016/j.procir.2017.03.035",
    "10.1016/j.promfg.2021.06.039",
    "10.1016/j.jmsy.2021.05.011",
    "10.1016/j.rcim.2020.102101",
    "10.1016/j.ijpe.2020.107845",
    "10.1016/j.ress.2019.107687",
    "10.1016/j.ijmachtools.2019.103479",
    "10.1016/j.ijmachtools.2019.103479",
]


def main() -> int:
    out = {}
    for doi in dict.fromkeys(DOIS):
        try:
            req = urllib.request.Request(f"https://api.crossref.org/works/{doi}", headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                it = json.loads(r.read())["message"]
            out[doi] = {"title": (it.get("title") or [""])[0][:170],
                        "container": (it.get("container-title") or [""])[0][:90],
                        "year": ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0],
                        "volume": it.get("volume"), "issue": it.get("issue"),
                        "page": it.get("page"), "article": it.get("article-number"),
                        "authors": "; ".join(f"{a.get('family','')} {a.get('given','')}".strip()
                                             for a in (it.get("author") or [])[:6])}
            print(f"{doi}\n   {out[doi]['year']} | {out[doi]['title'][:82]}\n"
                  f"   {out[doi]['container'][:70]} | v{out[doi]['volume']} "
                  f"n{out[doi]['issue']} p{out[doi]['page']} a{out[doi]['article']}", flush=True)
        except urllib.error.HTTPError as e:
            out[doi] = {"error": f"HTTP {e.code}"}
            print(f"{doi}  HTTP {e.code}", flush=True)
        except Exception as e:  # noqa: BLE001
            out[doi] = {"error": str(e)}
            print(f"{doi}  {e}", flush=True)
        time.sleep(0.4)
    (ROOT / "results" / "bibliography_doi_probe.json").write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
