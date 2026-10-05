"""Print the bibliography audit rows that failed verification."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = json.load(open(ROOT / "results" / "bibliography_verification.json"))
print("=== DOI resolved but claimed title did not match (repair the title) ===")
for x in rows:
    if x["status"] == "crossref-ok" and not x["verified"]:
        print(f"{x['key']}")
        print(f"  claimed : {x['claimed_title']} ({x['claimed_year']})")
        print(f"  actual  : {x.get('crossref_title')} ({x.get('crossref_year')})"
              f" overlap={x.get('title_overlap')}")
        print(f"  doi     : {x['doi']}")
        print(f"  authors : {x.get('authors')}")
        print(f"  in      : {x.get('container')}")
print()
print("=== DOI did not resolve (repair or drop the DOI) ===")
for x in rows:
    if x["status"].startswith("crossref HTTP"):
        print(f"{x['key']}: {x['doi']} :: {x['claimed_title']} ({x['claimed_year']})")
