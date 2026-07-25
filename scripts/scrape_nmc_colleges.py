from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://www.nmc.org.in/MCIRest/open/getDataFromService?service=getAllUgColleges"
PAGE_URL = "https://www.nmc.org.in/information-desk/for-students-to-study-in-india/list-of-college-teaching-mbbs/"


def fetch_json(session: requests.Session) -> list[dict]:
    response = session.get(
        API_URL,
        headers={"Accept": "application/json", "User-Agent": "neet-comparison/0.1"},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    colleges = payload.get("ugCollege")
    if not isinstance(colleges, list) or not colleges:
        raise RuntimeError("NMC API returned no ugCollege rows")
    return colleges


def fetch_html_fallback(session: requests.Session) -> pd.DataFrame:
    html = session.get(PAGE_URL, timeout=90).text
    tables = pd.read_html(html)
    candidates = [t for t in tables if {"State", "Annual Intake (Seats)"}.issubset(t.columns)]
    if not candidates:
        raise RuntimeError("NMC HTML table not found; page structure may have changed")
    return max(candidates, key=len)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/raw/nmc_colleges.csv"))
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("data/raw/nmc_ug_colleges.json"),
        help="Also preserve the raw JSON API response",
    )
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.verify = True
    try:
        colleges = fetch_json(session)
        args.json_out.write_text(json.dumps({"ugCollege": colleges}, ensure_ascii=False), encoding="utf-8")
        frame = pd.DataFrame(colleges)
        if "collegeName" in frame.columns:
            frame = frame[frame["collegeName"].notna() & (frame["collegeName"].astype(str).str.len() > 0)]
    except Exception as api_error:
        print(f"NMC JSON API failed ({api_error}); trying HTML fallback")
        try:
            frame = fetch_html_fallback(session)
        except requests.exceptions.SSLError:
            # Some Windows Python installs lack the NMC intermediate cert chain.
            session.verify = False
            requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]
            frame = fetch_html_fallback(session)

    frame.to_csv(args.out, index=False)
    print(f"Saved {len(frame):,} college rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
