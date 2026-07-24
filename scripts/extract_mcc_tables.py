from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import pdfplumber


def normalize(line: str) -> str:
    return " ".join(line.split())


def main() -> int:
    parser = argparse.ArgumentParser(description="Conservative text-row extractor for MCC PDFs")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    with pdfplumber.open(args.pdf) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            for raw in text.splitlines():
                line = normalize(raw)
                # Keep lines containing a rank-like leading integer and meaningful text.
                match = re.match(r"^(\d{1,9})\s+(.{10,})$", line)
                if match:
                    rows.append((page_number, int(match.group(1)), match.group(2)))

    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["page", "leading_integer", "raw_row"])
        writer.writerows(rows)
    print(f"Extracted {len(rows):,} candidate rows; manual schema adapter still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
