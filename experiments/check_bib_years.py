"""Report bibliography keys whose label year disagrees with the verified record."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "results" / "bibliography_verified.json").read_text())
bib = (ROOT / "paper" / "references.bib").read_text()
years = dict(re.findall(r"@\w+\{([^,]+),.*?year\s*=\s*\{(\d{4})\}", bib, re.S))
bad = []
for key, year in years.items():
    m = re.search(r"(\d{4})", key)
    if m and m.group(1) != year:
        bad.append((key, m.group(1), year))
for key, key_year, bib_year in sorted(bad):
    print(f"{key:26s} key says {key_year}, record says {bib_year}")
print(f"\n{len(years)} entries checked, {len(bad)} key/year mismatches")
