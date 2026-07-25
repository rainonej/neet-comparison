"""Parse CBSE disaffiliated/downgraded HTML lists into a school-level registry CSV."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/external/cbse/raw"
OUT = ROOT / "data/processed/cbse_dummy_school_registry.csv"


def parse_list(path: Path, outcome: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "lxml")
    rows: list[dict[str, str]] = []
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = [" ".join(td.get_text(" ", strip=True).split()) for td in tr.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            if cells[0].lower().replace(".", "").replace(" ", "") in {
                "sno",
                "slno",
                "sno",
                "sno",
                "#",
            } or "school" in cells[0].lower() and "name" in cells[0].lower():
                # header-ish
                if not re.match(r"^\d+$", cells[0]):
                    continue
            if re.match(r"^\d+$", cells[0]) and len(cells) > 1:
                school = cells[1]
                rest = cells[2:]
            else:
                school = cells[0]
                rest = cells[1:]
            if len(school) < 4:
                continue
            rows.append(
                {
                    "school_name": school,
                    "location_raw": " | ".join(rest),
                    "enforcement_outcome": outcome,
                    "allegation_type": (
                        "dummy_students_ineligible_or_records"
                        if outcome == "disaffiliated"
                        else "affiliation_downgrade"
                    ),
                    "source_wave": "cbse_press_html_list",
                    "source_file": path.as_posix(),
                }
            )
    if rows:
        return rows

    # fallback: text lines that look like school names
    skip_prefixes = (
        "list of",
        "disaffiliated school",
        "downgraded school",
        "central board",
        "click here",
        "home",
        "press",
    )
    for line in soup.get_text("\n", strip=True).splitlines():
        line = " ".join(line.split())
        low = line.lower()
        if any(low.startswith(p) for p in skip_prefixes):
            continue
        if len(line) > 15 and re.search(r"(school|vidyalaya|academy|convent)", line, re.I):
            # Prefer lines that include a place/pin fragment
            rows.append(
                {
                    "school_name": line[:200],
                    "location_raw": "",
                    "enforcement_outcome": outcome,
                    "allegation_type": (
                        "dummy_students_ineligible_or_records"
                        if outcome == "disaffiliated"
                        else "affiliation_downgrade"
                    ),
                    "source_wave": "cbse_press_html_textline",
                    "source_file": path.as_posix(),
                }
            )
    return rows


def main() -> int:
    rows = parse_list(RAW / "disaffiliated.html", "disaffiliated")
    rows += parse_list(RAW / "downgraded.html", "downgraded")
    uniq: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        uniq[(row["school_name"].lower(), row["enforcement_outcome"])] = row

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "school_name",
        "location_raw",
        "enforcement_outcome",
        "allegation_type",
        "source_wave",
        "source_file",
    ]
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(uniq.values())
    print(f"wrote {len(uniq)} rows -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
