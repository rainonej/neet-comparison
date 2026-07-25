"""Reconcile local NEET-2024 marks against official NTA press figures.

Downloads/hashes NTA result press PDFs when missing, compares reconstruction
row counts and centre lists to official appeared/qualified totals, and writes
a tidy reconciliation CSV plus JSON under data/processed/.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

PRESS = {
    "neet_2024_rerevised_result_20240726.pdf": {
        "url": "https://nta.ac.in/Download/Notice/Notice_20240726213317.pdf",
        "label": "rerevised_2024-07-26",
        "registered": 2_406_079,
        "appeared_including_ufm": 2_333_297,
        "appeared_excluding_ufm": 2_333_162,
        "ufm_cases": 135,
        "qualified": 1_315_853,
        "centres": 4_750,
        "cities": 571,
    },
    "neet_2024_initial_result_20240604.pdf": {
        "url": "https://www.nta.ac.in/Download/Notice/Notice_20240604195244.pdf",
        "label": "initial_2024-06-04",
        "registered": 2_406_079,
        "appeared_including_ufm": 2_333_297,
        "appeared_excluding_ufm": 2_333_297,
        "ufm_cases": None,
        "qualified": 1_316_268,
        "centres": 4_750,
        "cities": 571,
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_press(out_dir: Path) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, meta in PRESS.items():
        path = out_dir / name
        if not path.exists() or path.stat().st_size < 10_000:
            resp = requests.get(meta["url"], timeout=120)
            resp.raise_for_status()
            path.write_bytes(resp.content)
        rows.append(
            {
                "file": str(path).replace("\\", "/"),
                "label": meta["label"],
                "url": meta["url"],
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "registered": meta["registered"],
                "appeared_including_ufm": meta["appeared_including_ufm"],
                "appeared_excluding_ufm": meta["appeared_excluding_ufm"],
                "ufm_cases": meta["ufm_cases"],
                "qualified": meta["qualified"],
                "official_centres": meta["centres"],
                "official_cities": meta["cities"],
            }
        )
    return rows


def hash_wayback_pdfs(pdf_dir: Path) -> list[dict]:
    rows = []
    if not pdf_dir.exists():
        return rows
    for path in sorted(pdf_dir.glob("*.pdf")):
        rows.append(
            {
                "file": str(path).replace("\\", "/"),
                "centre_id": path.stem,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--marks",
        type=Path,
        default=Path("data/external/neet-2024-center-marks.csv"),
    )
    parser.add_argument(
        "--centres",
        type=Path,
        default=Path("data/external/github_hq969/raw/neet-2024-centers.csv"),
    )
    parser.add_argument(
        "--press-dir",
        type=Path,
        default=Path("data/external/nta/raw/press"),
    )
    parser.add_argument(
        "--wayback-dir",
        type=Path,
        default=Path("data/raw/neet_2024/pdfs_wayback"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/processed"),
    )
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    press_rows = ensure_press(args.press_dir)
    wayback = hash_wayback_pdfs(args.wayback_dir)

    marks = pd.read_csv(
        args.marks,
        header=None,
        names=["centre_id", "serial_number", "marks"],
        dtype={"centre_id": "int32", "serial_number": "int32", "marks": "int16"},
    )
    centres = pd.read_csv(
        args.centres,
        header=None,
        names=["idx", "state", "city", "center_name", "centre_id"],
    )

    local_rows = int(len(marks))
    local_centres = int(marks["centre_id"].nunique())
    centre_list_n = int(len(centres))
    centre_list_unique = int(centres["centre_id"].nunique())
    cities = int(centres["city"].nunique())
    states = int(centres["state"].nunique())
    marks_centres = set(marks["centre_id"].astype(int))
    list_centres = set(centres["centre_id"].astype(int))
    missing_in_list = sorted(marks_centres - list_centres)
    missing_in_marks = sorted(list_centres - marks_centres)

    # Canonical official benchmark: re-revised press (26 Jul 2024)
    official = next(r for r in press_rows if r["label"] == "rerevised_2024-07-26")
    appeared_ex = int(official["appeared_excluding_ufm"])
    appeared_inc = int(official["appeared_including_ufm"])

    reconciliation = {
        "retrieved_date": date.today().isoformat(),
        "local_mark_rows": local_rows,
        "local_unique_centres_in_marks": local_centres,
        "centre_list_rows": centre_list_n,
        "centre_list_unique_ids": centre_list_unique,
        "centre_list_states": states,
        "centre_list_cities": cities,
        "official_appeared_excluding_ufm": appeared_ex,
        "official_appeared_including_ufm": appeared_inc,
        "official_qualified": int(official["qualified"]),
        "official_centres": int(official["official_centres"]),
        "official_cities": int(official["official_cities"]),
        "row_delta_vs_appeared_excluding_ufm": local_rows - appeared_ex,
        "row_delta_vs_appeared_including_ufm": local_rows - appeared_inc,
        "centre_count_match_official": local_centres == int(official["official_centres"]),
        "mark_rows_exact_match_appeared_excluding_ufm": local_rows == appeared_ex,
        "centres_in_marks_missing_from_list": missing_in_list,
        "centres_in_list_missing_from_marks": missing_in_marks,
        "wayback_official_pdfs_hashed": len(wayback),
        "press_pdfs": press_rows,
        "verdict": (
            "PASS: reconstruction row count equals NTA re-revised appeared "
            "excluding UFM (2,333,162); centre count equals 4,750."
            if local_rows == appeared_ex and local_centres == int(official["official_centres"])
            else "REVIEW: local reconstruction does not exactly match official totals."
        ),
    }

    summary_csv = args.out_dir / "neet_2024_nta_reconciliation.csv"
    flat = {
        k: v
        for k, v in reconciliation.items()
        if k not in {"press_pdfs", "centres_in_marks_missing_from_list", "centres_in_list_missing_from_marks"}
    }
    flat["centres_in_marks_missing_from_list_n"] = len(missing_in_list)
    flat["centres_in_list_missing_from_marks_n"] = len(missing_in_marks)
    flat["press_rerevised_sha256"] = official["sha256"]
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat.keys()))
        writer.writeheader()
        writer.writerow(flat)

    json_path = args.out_dir / "prelim_analysis" / "neet_2024_nta_reconciliation.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(reconciliation, indent=2), encoding="utf-8")

    wayback_csv = args.out_dir / "neet_2024_wayback_centre_pdf_hashes.csv"
    with wayback_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "centre_id", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(wayback)

    print(json.dumps({k: reconciliation[k] for k in [
        "local_mark_rows",
        "official_appeared_excluding_ufm",
        "official_qualified",
        "local_unique_centres_in_marks",
        "official_centres",
        "mark_rows_exact_match_appeared_excluding_ufm",
        "centre_count_match_official",
        "wayback_official_pdfs_hashed",
        "verdict",
    ]}, indent=2))
    print("wrote", summary_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
