from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
from pathlib import Path

import pdfplumber
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

CENTRE_INDEX_URL = (
    "https://neet.ntaonline.in/frontend/web/common-scorecard/"
    "getdataresult?draw=1&start=0&length=4750"
)
PDF_URL = "https://neetfs.ntaonline.in/NEET_2024_Result/{centre_id}.pdf"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=15))
def download(url: str, path: Path, timeout: int = 90) -> None:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    path.write_bytes(response.content)


def parse_pdf(path: Path, centre_id: int) -> list[tuple[int, int, int]]:
    """Parse (centre_id, serial_number, marks) from an NTA centre PDF.

    The PDFs contain a repeated 'Srlno. Marks' header and can wrap across pages.
    We extract integers from text lines and then consume them in serial/marks pairs.
    """
    rows: list[tuple[int, int, int]] = []
    active = False
    pending: list[int] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for raw in text.splitlines():
                line = raw.strip()
                if "Srlno." in line and "Marks" in line:
                    active = True
                    continue
                if line.startswith("Centre:"):
                    active = False
                    pending.clear()
                    continue
                if not active:
                    continue
                values = [int(x) for x in re.findall(r"-?\d+", line)]
                pending.extend(values)
                while len(pending) >= 2:
                    serial, marks = pending[:2]
                    del pending[:2]
                    if serial > 0 and -180 <= marks <= 720:
                        rows.append((centre_id, serial, marks))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/raw/neet_2024"))
    parser.add_argument("--limit-centres", type=int)
    parser.add_argument("--skip-pdfs", action="store_true")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    index_path = args.out / "centre_index.json"
    if not index_path.exists():
        download(CENTRE_INDEX_URL, index_path)
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    centres = payload["data"]
    if args.limit_centres:
        centres = centres[: args.limit_centres]

    with (args.out / "centres.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["serial", "state", "city", "centre_name", "centre_id"])
        for item in centres:
            writer.writerow([
                item.get("SrNo"), item.get("CENT_STATE"), item.get("CENT_CITY"),
                item.get("CENT_NAME"), item.get("CENTNO"),
            ])

    if args.skip_pdfs:
        return 0

    pdf_dir = args.out / "pdfs"
    pdf_dir.mkdir(exist_ok=True)
    marks_path = args.out / "marks.csv"
    hashes_path = args.out / "sha256.csv"
    with marks_path.open("w", newline="", encoding="utf-8") as marks_file, hashes_path.open(
        "w", newline="", encoding="utf-8"
    ) as hash_file:
        marks_writer = csv.writer(marks_file)
        marks_writer.writerow(["centre_id", "serial_number", "marks"])
        hash_writer = csv.writer(hash_file)
        hash_writer.writerow(["centre_id", "filename", "sha256", "parsed_rows"])

        for position, item in enumerate(centres, start=1):
            centre_id = int(item["CENTNO"])
            pdf_path = pdf_dir / f"{centre_id}.pdf"
            if not pdf_path.exists():
                download(PDF_URL.format(centre_id=centre_id), pdf_path)
                time.sleep(0.1)
            rows = parse_pdf(pdf_path, centre_id)
            marks_writer.writerows(rows)
            hash_writer.writerow([centre_id, pdf_path.name, sha256(pdf_path), len(rows)])
            print(f"[{position}/{len(centres)}] {centre_id}: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
