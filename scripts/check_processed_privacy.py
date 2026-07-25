#!/usr/bin/env python3
"""Fail when processed tabular files expose common direct-identifier columns."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

FORBIDDEN = {
    "name", "student_name", "candidate_name", "father_name", "mother_name",
    "date_of_birth", "dob", "phone", "mobile", "email", "address",
    "roll_number", "roll_no", "application_number", "application_no",
    "aadhaar", "passport_number",
}


def normalized(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def audit(root: Path) -> list[str]:
    failures: list[str] = []
    for path in sorted(root.rglob("*.csv")):
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            try:
                header = next(reader)
            except StopIteration:
                continue
        bad = sorted({normalized(col) for col in header} & FORBIDDEN)
        if bad:
            failures.append(f"{path}: forbidden identifier columns {bad}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    failures = audit(args.root)
    if failures:
        print("\n".join(failures))
        return 1
    print(f"Privacy header audit passed for {args.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
