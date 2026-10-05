"""Show Crossref search candidates for the bibliography keys that failed."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cands = json.load(open(ROOT / "results" / "bibliography_search_candidates.json"))
want = ["tao2019fivelayer", "fuller2020dt", "barricelli2019dt", "aznar2025dtm",
        "uhlenkamp2022maturity", "park1998ncs", "pustek2019ncs", "makis2020ai4i",
        "isermann2005fault", "szydlowski2021dataset", "rahmandad2012repro",
        "kellens2017energy", "malamed2015energy", "valizadeh2021energy",
        "kreiger2013energy", "alghamdi2023sync"]
for key in want:
    print(f"== {key}")
    val = cands.get(key)
    if isinstance(val, dict):
        print("   ERROR", val)
        continue
    for c in (val or [])[:4]:
        print(f"   {c['year']} | {c['doi']} | {c['title'][:78]}")
        print(f"        in {c['container'][:60]} | {c['authors'][:60]}")
