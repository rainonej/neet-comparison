from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import requests

URL = "https://www.nmc.org.in/information-desk/for-students-to-study-in-india/list-of-college-teaching-mbbs/"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/raw/nmc_mbbs_colleges.csv"))
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    html = requests.get(URL, timeout=90).text
    tables = pd.read_html(html)
    candidates = [t for t in tables if {"State", "Annual Intake (Seats)"}.issubset(t.columns)]
    if not candidates:
        raise RuntimeError("NMC table not found; page structure may have changed")
    df = max(candidates, key=len)
    df.to_csv(args.out, index=False)
    print(f"Saved {len(df):,} college rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
