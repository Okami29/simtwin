"""Regenerate paper/references.bib from Crossref-verified metadata.

Every entry is rebuilt from ``results/bibliography_verified.json``, which is
produced by ``experiments/dump_verified.py`` after resolving each DOI against the
Crossref REST API.  Entries that could not be resolved are dropped from the
bibliography rather than carried with unverified identifiers, and the drop list is
written to ``results/bibliography_dropped.json`` so the manuscript can state it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIED = ROOT / "results" / "bibliography_verified.json"
BIB = ROOT / "paper" / "references.bib"

# Keys that legitimately have no DOI: ISO/OASIS standards and the Grieves white paper.
NO_DOI_KEYS = {"grieves2014dt", "iso23247", "iso30173", "mqtt5oasis", "mqtt311oasis"}

# Keys dropped because no resolvable identifier could be found for the claimed work.
DROPPED_KEYS = {"park1998ncs", "pustek2019ncs", "makis2020ai4i", "malamed2015energy",
               "valizadeh2021energy"}

# Keys whose label encodes a year (or first author) the verified record contradicts.
RENAME = {
    "tao2019fivelayer": "tao2017fivelayer",
    "aznar2025dtm": "aznar2026dtm",
    "kellens2017energy": "baumers2017jiec",
    "alghamdi2023sync": "tan2023sync",
    "fibremul2022": "fibremul2020",
    "grieves2017dt": "grieves2016dt",
    "liu2024dtms": "liu2023dtms",
    "mtdn2025": "mtdn2024",
    "tan2024sync": "tan2023sync",
}


def _months(it: dict) -> str:
    return ""


def _entry_type(it: dict) -> str:
    t = it.get("type", "")
    if t in ("journal-article",):
        return "article"
    if t in ("proceedings-article", "conference"):
        return "inproceedings"
    if t == "book":
        return "book"
    if t in ("book-chapter", "book-section"):
        return "incollection"
    return "misc"


def _escape(s: str) -> str:
    return (s.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")
             .replace("#", r"\#").replace("$", r"\$"))


def _format(key: str, it: dict) -> str:
    etype = _entry_type(it)
    authors = it.get("authors") or []
    fam_given = []
    for family, given in authors:
        family = (family or "").strip()
        given = (given or "").strip()
        if family:
            fam_given.append(f"{family}, {given}" if given else family)
    fields: list[tuple[str, str]] = []
    if fam_given:
        fields.append(("author", " and ".join(fam_given)))
    fields.append(("title", "{" + _escape(it["title"]) + "}"))
    year = it.get("year")
    if year:
        fields.append(("year", str(year)))
    container = it.get("container") or ""
    if etype in ("article", "incollection") and container:
        fields.append(("journal" if etype == "article" else "booktitle", _escape(container)))
    elif container:
        fields.append(("booktitle" if etype == "inproceedings" else "journal",
                       _escape(container)))
    if it.get("volume"):
        fields.append(("volume", str(it["volume"])))
    if it.get("issue"):
        fields.append(("number", str(it["issue"])))
    if it.get("page"):
        fields.append(("pages", str(it["page"]).replace("-", "--")))
    if it.get("article") and not it.get("page"):
        fields.append(("articleno", str(it["article"])))
    if it.get("publisher") and etype in ("book", "incollection", "inproceedings", "misc"):
        fields.append(("publisher", _escape(it["publisher"])))
    fields.append(("doi", it["doi"]))
    body = ",\n".join(f"  {k:<10} = {{{v}}}" for k, v in fields if v)
    return f"@{etype}{{{key},\n{body}\n}}\n"


NO_DOI_ENTRIES = r"""
@misc{grieves2014dt,
  author       = {Grieves, Michael and Vickers, John},
  title        = {Digital Twin: Manufacturing Excellence through Virtual Factory Replication},
  year         = {2014},
  howpublished = {White paper, Florida Institute of Technology, Melbourne, FL, USA},
  url          = {https://www.sae.org/publications/technical-papers/content/2017-01-0392/},
  note         = {White paper; no DOI assigned}
}

@misc{iso23247,
  author       = {{International Organization for Standardization}},
  title        = {Automation Systems and Integration --- Digital Twin Framework for Manufacturing:
                 Part 1, Overview and General Principles},
  year         = {2021},
  howpublished = {ISO 23247-1:2021},
  publisher    = {International Organization for Standardization},
  address      = {Geneva, Switzerland},
  note         = {Standard; no DOI assigned}
}

@misc{iso30173,
  author       = {{International Organization for Standardization}},
  title        = {Information Technology --- Digital Twin Representations of Physical Systems},
  year         = {2023},
  howpublished = {ISO/IEC 30173:2023},
  publisher    = {International Organization for Standardization},
  address      = {Geneva, Switzerland},
  note         = {Standard; no DOI assigned}
}

@misc{mqtt5oasis,
  author       = {{OASIS Standard}},
  title        = {MQTT Version 5.0},
  year         = {2019},
  howpublished = {OASIS Standard, 3 December 2019},
  publisher    = {OASIS},
  url          = {https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html},
  note         = {Industry specification; no DOI assigned}
}

@misc{mqtt311oasis,
  author       = {{OASIS Standard}},
  title        = {MQTT Version 3.1.1},
  year         = {2014},
  howpublished = {OASIS Standard, 29 October 2014},
  publisher    = {OASIS},
  url          = {http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html},
  note         = {Industry specification; no DOI assigned}
}
"""


def main() -> int:
    data = json.loads(VERIFIED.read_text())
    entries, dropped = [], sorted(DROPPED_KEYS)
    for key, it in data.items():
        if "no_doi" in it:
            continue
        if "error" in it:
            dropped.append(key)
            continue
        entries.append(_format(RENAME.get(key, key), it))
    bib = "\n".join(entries) + "\n" + NO_DOI_ENTRIES.strip() + "\n"
    BIB.parent.mkdir(parents=True, exist_ok=True)
    BIB.write_text(bib)
    (ROOT / "results" / "bibliography_dropped.json").write_text(
        json.dumps({"dropped": dropped,
                    "no_doi_standards": sorted(NO_DOI_KEYS),
                    "total_verified": len(entries)}, indent=2))
    print(f"wrote {BIB}: {len(entries)} DOI-verified entries "
          f"+ {len(NO_DOI_KEYS)} standards/whitepaper entries")
    print(f"dropped (unverifiable): {dropped}")
    types: dict[str, int] = {}
    for m in re.finditer(r"@(\w+)\{", bib):
        types[m.group(1)] = types.get(m.group(1), 0) + 1
    print("entry types:", types)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
