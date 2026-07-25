"""Extract MCC 2024 seat-matrix and allotment PDFs into tidy CSVs."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import pdfplumber

SEAT_COLS = [
    "source_file",
    "matrix_title",
    "institute",
    "institute_code",
    "program",
    "quota",
    "open",
    "open_pwd",
    "general_ews",
    "general_ews_pwd",
    "obc",
    "obc_pwd",
    "sc",
    "sc_pwd",
    "st",
    "st_pwd",
    "total_seats",
]

ALLOT_COLS = [
    "source_file",
    "round",
    "sno",
    "rank",
    "allotted_quota",
    "allotted_institute",
    "course",
    "allotted_category",
    "candidate_category",
    "remarks",
]

INST_CODE_RE = re.compile(r"\((\d{5,7})\)\s*$")


def clean(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\n", " ").split())


def to_int(value: object) -> str:
    text = clean(value)
    if text in {"", "-", "—", "NA", "N/A"}:
        return ""
    try:
        return str(int(float(text)))
    except ValueError:
        return text


def parse_round(name: str) -> str:
    lower = name.lower()
    if "special_stray" in lower and "round_ii" in lower:
        return "special_stray_ii"
    if "special_stray" in lower and "round_iii" in lower:
        return "special_stray_iii"
    if "special_stray" in lower:
        return "special_stray"
    if "stray" in lower:
        return "stray"
    if "round_3" in lower or "round 3" in lower or "_r3_" in lower:
        return "3"
    if "round_2" in lower or "round 2" in lower:
        return "2"
    if "round_1" in lower or "round 1" in lower:
        return "1"
    return "unknown"


def _empty_seat_row(pdf_path: Path, title: str, inst: str, program: str, quota: str) -> dict[str, str]:
    code_match = INST_CODE_RE.search(inst)
    code = code_match.group(1) if code_match else ""
    inst_name = INST_CODE_RE.sub("", inst).strip(" ,")
    return {
        "source_file": pdf_path.name,
        "matrix_title": title or pdf_path.stem,
        "institute": inst_name,
        "institute_code": code,
        "program": program,
        "quota": quota,
        "open": "",
        "open_pwd": "",
        "general_ews": "",
        "general_ews_pwd": "",
        "obc": "",
        "obc_pwd": "",
        "sc": "",
        "sc_pwd": "",
        "st": "",
        "st_pwd": "",
        "total_seats": "",
    }


def extract_seat_matrix(pdf_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    title = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for table in tables:
                if not table:
                    continue
                header_idx = None
                header_kind = ""
                for i, raw in enumerate(table):
                    cells = [clean(c).lower() for c in raw]
                    joined = " ".join(cells)
                    compact = joined.replace(" ", "").replace("\n", "")
                    if "institute" in joined and "totalseats" in compact:
                        header_idx = i
                        # Full AIQ category matrix vs deemed Open/Total only.
                        header_kind = "full" if "obc" in compact or "general-ews" in compact else "simple"
                        break
                    if i == 0 and "final seat matrix" in joined:
                        title = clean(raw[0])
                if header_idx is None:
                    if table and clean(table[0][0]).lower().startswith("final seat matrix"):
                        title = clean(table[0][0])
                    continue
                for raw in table[header_idx + 1 :]:
                    cells = [clean(c) for c in raw]
                    if not cells or not cells[0] or cells[0].lower() == "institute":
                        continue
                    if header_kind == "simple" and len(cells) >= 5:
                        row = _empty_seat_row(pdf_path, title, cells[0], cells[1], cells[2])
                        row["open"] = to_int(cells[3])
                        row["total_seats"] = to_int(cells[4])
                        rows.append(row)
                        continue
                    if len(cells) < 14:
                        continue
                    numeric = cells[3:14]
                    if len(numeric) < 11:
                        continue
                    row = _empty_seat_row(pdf_path, title, cells[0], cells[1], cells[2])
                    row.update(
                        {
                            "open": to_int(numeric[0]),
                            "open_pwd": to_int(numeric[1]),
                            "general_ews": to_int(numeric[2]),
                            "general_ews_pwd": to_int(numeric[3]),
                            "obc": to_int(numeric[4]),
                            "obc_pwd": to_int(numeric[5]),
                            "sc": to_int(numeric[6]),
                            "sc_pwd": to_int(numeric[7]),
                            "st": to_int(numeric[8]),
                            "st_pwd": to_int(numeric[9]),
                            "total_seats": to_int(numeric[10]),
                        }
                    )
                    rows.append(row)
    return rows


def extract_allotment(
    pdf_path: Path,
    round_label: str | None = None,
    checkpoint: Path | None = None,
) -> list[dict[str, str]]:
    """Extract allotment tables page-by-page with optional CSV checkpoint/resume."""
    rows: list[dict[str, str]] = []
    round_name = round_label or parse_round(pdf_path.name)
    if checkpoint and checkpoint.exists() and checkpoint.stat().st_size > 0:
        with checkpoint.open(newline="", encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
        print(f"resuming {pdf_path.name} with {len(rows)} checkpoint rows")
    elif checkpoint:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        write_csv(checkpoint, ALLOT_COLS, [])

    seen_sno = {r["sno"] for r in rows}
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for page_number, page in enumerate(pdf.pages, start=1):
            page_new: list[dict[str, str]] = []
            for table in page.extract_tables() or []:
                for raw in table or []:
                    cells = [clean(c) for c in raw]
                    if len(cells) < 8 or not cells[0].isdigit():
                        continue
                    if not re.match(r"^\d+(\.\d+)?$", cells[1]):
                        continue
                    if cells[0] in seen_sno:
                        continue
                    course = cells[4]
                    quota = cells[2]
                    remarks = cells[7] if len(cells) > 7 else ""
                    # Drop misaligned/garbage rows common in large multi-round PDFs.
                    if course in {"", "-", "Course"}:
                        continue
                    if quota in {"", "-", "Allotted Quota", "AllottedQuota"}:
                        continue
                    if not re.search(r"MBBS|BDS|Nursing", course, re.I):
                        continue
                    row = {
                        "source_file": pdf_path.name,
                        "round": round_name,
                        "sno": cells[0],
                        "rank": cells[1],
                        "allotted_quota": quota,
                        "allotted_institute": cells[3],
                        "course": course,
                        "allotted_category": cells[5],
                        "candidate_category": cells[6],
                        "remarks": remarks,
                    }
                    page_new.append(row)
                    seen_sno.add(cells[0])
            if page_new:
                rows.extend(page_new)
                if checkpoint:
                    with checkpoint.open("a", newline="", encoding="utf-8") as handle:
                        writer = csv.DictWriter(handle, fieldnames=ALLOT_COLS)
                        writer.writerows(page_new)
            # Limit pdfplumber memory growth on multi-thousand-page PDFs.
            if hasattr(page, "flush_cache"):
                page.flush_cache()
            if page_number % 50 == 0 or page_number == total_pages:
                print(
                    f"  {pdf_path.name}: page {page_number}/{total_pages} rows={len(rows)}",
                    flush=True,
                )
    return rows


WIDE_R3_COLS = [
    "rank",
    "r1_quota",
    "r1_institute",
    "r1_course",
    "r1_remarks",
    "r2_quota",
    "r2_institute",
    "r2_course",
    "r2_remarks",
    "r3_quota",
    "r3_institute",
    "r3_course",
    "r3_allotted_category",
    "r3_candidate_category",
    "r3_option_no",
    "r3_remarks",
    "source_file",
]


def extract_round3_wide(pdf_path: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Parse Round-3 multi-round status PDF into wide + tidy Round-3 allotment rows."""
    wide_rows: list[dict[str, str]] = []
    allot_rows: list[dict[str, str]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables() or []:
                for raw in table or []:
                    cells = [clean(c) for c in raw]
                    if not cells or not re.match(r"^\d+(\.\d+)?$", cells[0]):
                        continue
                    if len(cells) >= 17 and cells[6] == "":
                        cells = cells[:6] + cells[7:]
                    if len(cells) < 16:
                        continue
                    rank = cells[0]
                    r1, r2, r3 = cells[1:5], cells[5:9], cells[9:16]
                    while len(r3) < 7:
                        r3.append("")
                    wide_rows.append(
                        {
                            "rank": rank,
                            "r1_quota": r1[0],
                            "r1_institute": r1[1],
                            "r1_course": r1[2],
                            "r1_remarks": r1[3],
                            "r2_quota": r2[0],
                            "r2_institute": r2[1],
                            "r2_course": r2[2],
                            "r2_remarks": r2[3],
                            "r3_quota": r3[0],
                            "r3_institute": r3[1],
                            "r3_course": r3[2],
                            "r3_allotted_category": r3[3],
                            "r3_candidate_category": r3[4],
                            "r3_option_no": r3[5],
                            "r3_remarks": r3[6],
                            "source_file": pdf_path.name,
                        }
                    )
                    if r3[1] not in {"", "-"} and re.search(r"MBBS|BDS|Nursing", r3[2] or "", re.I):
                        allot_rows.append(
                            {
                                "source_file": pdf_path.name,
                                "round": "3",
                                "sno": str(len(allot_rows) + 1),
                                "rank": rank,
                                "allotted_quota": r3[0],
                                "allotted_institute": r3[1],
                                "course": r3[2],
                                "allotted_category": r3[3],
                                "candidate_category": r3[4],
                                "remarks": r3[6],
                            }
                        )
            if hasattr(page, "flush_cache"):
                page.flush_cache()
            if page_number % 200 == 0 or page_number == len(pdf.pages):
                print(
                    f"  {pdf_path.name}: page {page_number}/{len(pdf.pages)} "
                    f"wide={len(wide_rows)} allot={len(allot_rows)}",
                    flush=True,
                )
    return wide_rows, allot_rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mcc-dir",
        type=Path,
        default=Path("data/raw/mcc_2024/2024"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/processed/mcc_2024"),
    )
    parser.add_argument(
        "--allotments",
        nargs="*",
        default=[
            "011_final_result_of_round_1_neet_ug_2024.pdf",
            "016_final_allotment_result_for_round_2_of_ug_counselling_2024.pdf",
            "019_final_result_round_3_ug_counselling_2024.pdf",
            "024_final_allotment_result_for_stray_vacancy_round_ug_counselling_2024.pdf",
            "029_final_allotment_result_for_ug_special_stray_vacancy_round_2024.pdf",
        ],
        help="Allotment PDF filenames relative to --mcc-dir",
    )
    parser.add_argument("--skip-allotments", action="store_true")
    parser.add_argument("--skip-matrices", action="store_true")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_matrices:
        matrix_rows: list[dict[str, str]] = []
        for pdf in sorted(args.mcc_dir.glob("*seat_matrix*.pdf")):
            extracted = extract_seat_matrix(pdf)
            print(f"matrix {pdf.name}: {len(extracted)} rows")
            matrix_rows.extend(extracted)
        out = args.out_dir / "mcc_2024_seat_matrix.csv"
        write_csv(out, SEAT_COLS, matrix_rows)
        print(f"wrote {out} ({len(matrix_rows)} rows)")

    if not args.skip_allotments:
        allot_rows: list[dict[str, str]] = []
        for name in args.allotments:
            pdf = args.mcc_dir / name
            if not pdf.exists():
                print(f"missing allotment pdf: {pdf}")
                continue
            round_name = parse_round(pdf.name)
            per = args.out_dir / f"mcc_2024_allotment_round_{round_name}.csv"
            if round_name == "3":
                wide_rows, extracted = extract_round3_wide(pdf)
                write_csv(args.out_dir / "mcc_2024_round3_status_wide.csv", WIDE_R3_COLS, wide_rows)
                print(f"round3 wide rows={len(wide_rows)}")
            else:
                extracted = extract_allotment(pdf, round_label=round_name, checkpoint=per)
            print(f"allotment {pdf.name}: {len(extracted)} rows")
            allot_rows.extend(extracted)
            write_csv(per, ALLOT_COLS, extracted)
            print(f"wrote {per}")
        # Merge with any previously extracted rounds already on disk.
        merged: list[dict[str, str]] = []
        for path in sorted(args.out_dir.glob("mcc_2024_allotment_round_*.csv")):
            with path.open(newline="", encoding="utf-8") as handle:
                merged.extend(csv.DictReader(handle))
        out = args.out_dir / "mcc_2024_allotments.csv"
        write_csv(out, ALLOT_COLS, merged)
        print(f"wrote {out} ({len(merged)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
