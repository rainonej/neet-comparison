"""Parse Kerala KEAM medical rank / allotment / last-rank PDFs into tidy panels.

Privacy: application numbers are never written to data/processed/. Raw PDFs remain
under gitignored data/external/.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import pdfplumber

RANK_COLS = [
    "year",
    "list_name",
    "serial_no",
    "neet_score",
    "neet_rank",
    "state_rank",
    "source_file",
]

ALLOT_COLS = [
    "year",
    "phase",
    "serial_no",
    "state_rank",
    "candidate_category",
    "allotted_category",
    "college_code",
    "college_name",
    "course",
    "seat_type",
    "option_no",
    "source_file",
]

LASTRANK_COLS = [
    "year",
    "phase",
    "course",
    "college_code",
    "college_name",
    "college_type",
    "category",
    "last_rank",
    "other_categories_raw",
    "source_file",
]

CAT_COLS = ["SM", "EZ", "MU", "LA", "DV", "VK", "BH", "BX", "KN", "KU", "SC", "ST", "EW"]


def clean(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\n", " ").split())


def parse_int(value: object) -> str:
    text = clean(value).rstrip(".")
    if text in {"", "-", "—"}:
        return ""
    try:
        return str(int(float(text)))
    except ValueError:
        return ""


def extract_rank_list(pdf_path: Path, year: str = "2025") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for table in tables:
                if not table:
                    continue
                for raw in table:
                    cells = [clean(c) for c in raw]
                    if len(cells) < 5:
                        continue
                    if not re.match(r"^\d+\.?$", cells[0]):
                        continue
                    # single-column block
                    if len(cells) >= 5 and parse_int(cells[2]) and parse_int(cells[3]):
                        rows.append(
                            {
                                "year": year,
                                "list_name": "kerala_state_medical_rank",
                                "serial_no": parse_int(cells[0]),
                                "neet_score": parse_int(cells[2]),
                                "neet_rank": parse_int(cells[3]),
                                "state_rank": parse_int(cells[4]),
                                "source_file": pdf_path.name,
                            }
                        )
                    # dual column pages sometimes return only left or both via text
            # fallback: regex on text for dual-column layout completeness
            text = page.extract_text() or ""
            for match in re.finditer(
                r"(\d+)\.\s+(\d{6,8})\s+(\d{1,3})\s+(\d{1,7})\s+(\d{1,7})",
                text,
            ):
                serial, _appl, score, neet_rank, state_rank = match.groups()
                rows.append(
                    {
                        "year": year,
                        "list_name": "kerala_state_medical_rank",
                        "serial_no": serial,
                        "neet_score": score,
                        "neet_rank": neet_rank,
                        "state_rank": state_rank,
                        "source_file": pdf_path.name,
                    }
                )
    # de-dupe by state_rank (prefer first)
    dedup: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row["state_rank"] or row["serial_no"]
        if key and key not in dedup:
            dedup[key] = row
    return [dedup[k] for k in sorted(dedup, key=lambda x: int(x))]


def _split_college(college: str) -> tuple[str, str]:
    if "-" in college:
        code, name = college.split("-", 1)
        return code.strip(), name.strip()
    return "", college


def extract_allotment(pdf_path: Path, phase: str, year: str = "2025") -> list[dict[str, str]]:
    """Parse phase allotment tables.

    Phase 1 layout:
      SlNo ApplNo Rank CandidateCategory College Course SeatType OptionNo
    Phase 2+ layout:
      SlNo ApplNo Rank College Course CandidateCategory AllottedCategory OptionNo
    """
    rows: list[dict[str, str]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for table in tables:
                if not table:
                    continue
                for raw in table:
                    cells = [clean(c) for c in raw]
                    if len(cells) < 8:
                        continue
                    if not cells[0].isdigit() or not cells[1].isdigit():
                        continue
                    # Detect layout: college names are long / contain '-' / 'Medical'
                    third = cells[3]
                    phase1_like = len(third) <= 4 and "medical" not in third.lower() and "-" not in third
                    if phase1_like:
                        code, name = _split_college(cells[4])
                        rows.append(
                            {
                                "year": year,
                                "phase": phase,
                                "serial_no": cells[0],
                                "state_rank": parse_int(cells[2]),
                                "candidate_category": third,
                                "allotted_category": "",
                                "college_code": code,
                                "college_name": name,
                                "course": cells[5],
                                "seat_type": cells[6],
                                "option_no": parse_int(cells[7]),
                                "source_file": pdf_path.name,
                            }
                        )
                    else:
                        code, name = _split_college(third)
                        rows.append(
                            {
                                "year": year,
                                "phase": phase,
                                "serial_no": cells[0],
                                "state_rank": parse_int(cells[2]),
                                "candidate_category": cells[5],
                                "allotted_category": cells[6],
                                "college_code": code,
                                "college_name": name,
                                "course": cells[4],
                                "seat_type": cells[6],
                                "option_no": parse_int(cells[7]),
                                "source_file": pdf_path.name,
                            }
                        )
    return rows


def extract_last_rank(pdf_path: Path, phase: str, year: str = "2025") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    course = "MBBS"
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if re.search(r"\bBDS\b", text) and not re.search(r"\bMBBS\b", text.split("\n")[0:5].__repr__()):
                # keep default unless page clearly BDS-only header
                pass
            tables = page.extract_tables() or []
            for table in tables:
                if not table:
                    continue
                header_idx = None
                for i, raw in enumerate(table):
                    cells = [clean(c) for c in raw]
                    joined = " ".join(cells)
                    if "Name of College" in joined and "SM" in joined:
                        header_idx = i
                        break
                    if len(cells) == 1 and cells[0] in {"MBBS", "BDS"}:
                        course = cells[0]
                if header_idx is None:
                    continue
                for raw in table[header_idx + 1 :]:
                    cells = [clean(c) for c in raw]
                    if len(cells) < 15:
                        continue
                    # formats vary: [code, name, type, SM...EW, other] or [name...,]
                    if cells[2] in {"G", "S", "N"} and len(cells[0]) <= 5:
                        code, name, ctype = cells[0], cells[1], cells[2]
                        cats = cells[3:16]
                        other = cells[16] if len(cells) > 16 else ""
                    else:
                        continue
                    for cat, val in zip(CAT_COLS, cats, strict=False):
                        rows.append(
                            {
                                "year": year,
                                "phase": phase,
                                "course": course,
                                "college_code": code,
                                "college_name": name,
                                "college_type": ctype,
                                "category": cat,
                                "last_rank": parse_int(val),
                                "other_categories_raw": other if cat == "SM" else "",
                                "source_file": pdf_path.name,
                            }
                        )
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/external/kerala_cee/raw/files"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/processed/kerala"),
    )
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rank_pdf = args.raw_dir / "mbbsranklist.pdf"
    if rank_pdf.exists():
        ranks = extract_rank_list(rank_pdf)
        write_csv(args.out_dir / "kerala_2025_medical_ranklist.csv", RANK_COLS, ranks)
        print(f"ranklist rows={len(ranks)}")
    else:
        print("missing", rank_pdf)

    allot_map = {
        "1": "mbbs_p1_final.pdf",
        "2": "mbbs_p2_final.pdf",
        "3": "mbbs_p3_final.pdf",
        "4": "mbbs_p4_final.pdf",
    }
    allot_rows: list[dict[str, str]] = []
    for phase, name in allot_map.items():
        pdf = args.raw_dir / name
        if not pdf.exists():
            print("missing", pdf)
            continue
        extracted = extract_allotment(pdf, phase=phase)
        print(f"allotment phase {phase}: {len(extracted)}")
        allot_rows.extend(extracted)
        write_csv(
            args.out_dir / f"kerala_2025_mbbs_allotment_phase_{phase}.csv",
            ALLOT_COLS,
            extracted,
        )
    write_csv(args.out_dir / "kerala_2025_mbbs_allotments.csv", ALLOT_COLS, allot_rows)
    print(f"allotments total={len(allot_rows)}")

    lastrank_map = {
        "1": "mbbs_lrank_final.pdf",
        "2": "mbbs_lrank_p2_final.pdf",
        "3": "mbbs_lrank_p3_final2.pdf",
    }
    last_rows: list[dict[str, str]] = []
    for phase, name in lastrank_map.items():
        pdf = args.raw_dir / name
        if not pdf.exists():
            print("missing", pdf)
            continue
        extracted = extract_last_rank(pdf, phase=phase)
        print(f"last_rank phase {phase}: {len(extracted)}")
        last_rows.extend(extracted)
        write_csv(
            args.out_dir / f"kerala_2025_mbbs_last_rank_phase_{phase}.csv",
            LASTRANK_COLS,
            extracted,
        )
    write_csv(args.out_dir / "kerala_2025_mbbs_last_ranks.csv", LASTRANK_COLS, last_rows)
    print(f"last_ranks total={len(last_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
