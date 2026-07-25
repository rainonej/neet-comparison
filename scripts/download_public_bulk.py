"""Download remaining publicly reachable archives for the NEET comparison project.

Skips registration-gated MoSPI/DHS/IHDS microdata. Downloads:
- Kerala CEE PDFs linked from KEAM list pages (and recursive discovery)
- Public research/admin PDFs from the source catalog
- GitHub NEET reconstruction SQLite
- NIRF medical ranking page + linked PDFs/CSVs
- NTA public notices / information bulletin landing pages and linked PDFs
- MCC other years if present
- NMC stipend page JSON/HTML where available
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "neet-comparison-research/0.1 (+local archive; respectful crawl)"}
SESSION = requests.Session()
SESSION.headers.update(UA)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_name(url: str, fallback: str = "file") -> str:
    path = urlparse(url).path.rstrip("/")
    name = Path(path).name or fallback
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name[:180] or fallback


def download(url: str, dest: Path, timeout: int = 120, attempts: int = 4) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return True
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = SESSION.get(url, timeout=timeout, allow_redirects=True)
            if response.status_code >= 400:
                error = RuntimeError(f"HTTP {response.status_code}")
                if attempt + 1 < attempts:
                    time.sleep(min(2**attempt, 12))
                continue
            dest.write_bytes(response.content)
            print(f"OK {dest} ({dest.stat().st_size} bytes) <- {url}")
            return True
        except Exception as exc:  # noqa: BLE001
            error = exc
            if attempt + 1 < attempts:
                time.sleep(min(2**attempt, 12))
    print(f"FAIL {url} -> {error}")
    return False


def extract_links(html: str, base: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    out: list[tuple[str, str]] = []
    for tag in soup.find_all("a", href=True):
        href = urljoin(base, tag["href"])
        text = " ".join(tag.get_text(" ", strip=True).split())
        out.append((text, href))
    return out


def is_data_file(url: str) -> bool:
    return bool(re.search(r"\.(pdf|xlsx?|csv|zip|parquet|tsv|docx?|json)($|\?)", url, re.I))


def crawl_page_for_files(url: str, out_dir: Path, manifest_rows: list[dict], label: str) -> None:
    html_path = out_dir / f"_page_{safe_name(url, 'page')}.html"
    if not download(url, html_path):
        return
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    for text, href in extract_links(html, url):
        if not is_data_file(href):
            continue
        dest = out_dir / safe_name(href)
        ok = download(href, dest)
        if ok:
            manifest_rows.append(
                {
                    "source": label,
                    "page": url,
                    "title": text,
                    "url": href,
                    "local_file": str(dest).replace("\\", "/"),
                    "bytes": dest.stat().st_size,
                    "sha256": sha256(dest),
                }
            )


def download_kerala(manifest_rows: list[dict]) -> None:
    root = Path("data/external/kerala_cee/raw")
    pages = [
        "https://cee.kerala.gov.in/",
        "https://cee.kerala.gov.in/keam2025/",
        "https://cee.kerala.gov.in/keam2025/ranklist",
        "https://cee.kerala.gov.in/keam2025/allotlist",
        "https://cee.kerala.gov.in/keam2025/last_rank",
        "https://cee.kerala.gov.in/keam2025/catlist",
        "https://cee.kerala.gov.in/keam2024/",
        "https://cee.kerala.gov.in/keam2024/ranklist",
        "https://cee.kerala.gov.in/keam2024/allotlist",
        "https://cee.kerala.gov.in/keam2024/last_rank",
        "https://cee.kerala.gov.in/keam2024/catlist",
        "https://cee.kerala.gov.in/keam2023/",
        "https://cee.kerala.gov.in/keam2026/",
        "https://cee.kerala.gov.in/keam2026/notification",
    ]
    for page in pages:
        crawl_page_for_files(page, root / "files", manifest_rows, "kerala_cee")
        # Also follow non-file child pages that look like list directories (one hop).
        html_path = root / "files" / f"_page_{safe_name(page, 'page')}.html"
        if not html_path.exists():
            continue
        html = html_path.read_text(encoding="utf-8", errors="ignore")
        for text, href in extract_links(html, page):
            if is_data_file(href):
                continue
            if re.search(r"(rank|allot|last.?rank|catlist|vacanc|mbbs|medical|seat)", text + href, re.I):
                if href.rstrip("/").count("/") - page.rstrip("/").count("/") <= 2:
                    crawl_page_for_files(href, root / "files", manifest_rows, "kerala_cee")


def download_catalog_pdfs(manifest_rows: list[dict]) -> None:
    items = [
        (
            "world_bank_health_labor",
            "https://documents1.worldbank.org/curated/en/099093025154528532/pdf/P175882-fce3fc74-6041-43d5-b91f-7d94a3dc2bfa.pdf",
            Path("data/external/world_bank/raw/P175882_health_labor.pdf"),
        ),
        (
            "wid_india_2024",
            "https://wid.world/www-site/uploads/2024/03/WorldInequalityLab_WP2024_09_Income-and-Wealth-Inequality-in-India-1922-2023_Final.pdf",
            Path("data/external/wid/raw/WIL_WP2024_09_India.pdf"),
        ),
        (
            "rajan_committee_2021",
            "https://www.thehinducentre.com/resources/article36589938.ece/binary/N21092966.pdf",
            Path("data/external/tamil_nadu/raw/rajan_committee_neet_tn.pdf"),
        ),
        (
            "github_neet_sqlite",
            "https://github.com/hq969/neet-2024-center-marks/raw/refs/heads/main/db/neet-2024-center-marks.sqlite",
            Path("data/external/github_hq969/raw/neet-2024-center-marks.sqlite"),
        ),
        (
            "github_neet_centres_csv",
            "https://github.com/hq969/neet-2024-center-marks/raw/refs/heads/main/csv/neet-2024-centres.csv",
            Path("data/external/github_hq969/raw/neet-2024-centres.csv"),
        ),
        (
            "osf_view_only_page",
            "https://osf.io/tnh4x/overview?view_only=871cca8775f8420e802e172b5534673e",
            Path("data/external/osf/tnh4x/raw/project_overview.html"),
        ),
    ]
    for label, url, dest in items:
        if download(url, dest):
            manifest_rows.append(
                {
                    "source": label,
                    "page": "",
                    "title": dest.name,
                    "url": url,
                    "local_file": str(dest).replace("\\", "/"),
                    "bytes": dest.stat().st_size,
                    "sha256": sha256(dest),
                }
            )


def download_nirf(manifest_rows: list[dict]) -> None:
    out = Path("data/external/nirf/raw")
    pages = [
        "https://www.nirfindia.org/Rankings/2024/MedicalRanking.html",
        "https://www.nirfindia.org/Rankings/2025/MedicalRanking.html",
        "https://www.nirfindia.org/Rankings/2023/MedicalRanking.html",
        "https://www.nirfindia.org/",
    ]
    for page in pages:
        crawl_page_for_files(page, out, manifest_rows, "nirf")
        # also save ranking HTML for table extraction
        html_path = out / f"ranking_{safe_name(page)}.html"
        download(page, html_path)


def download_nta_public(manifest_rows: list[dict]) -> None:
    out = Path("data/external/nta/raw")
    pages = [
        "https://neet.nta.nic.in/",
        "https://neet.nta.nic.in/information-bulletin/",
        "https://neet.nta.nic.in/document-category/public-notices/",
        "https://exams.nta.ac.in/NEET/",
    ]
    for page in pages:
        crawl_page_for_files(page, out, manifest_rows, "nta_public")


def download_mcc_years(manifest_rows: list[dict], years: list[int]) -> None:
    # Use existing scraper for additional years.
    import subprocess
    import sys

    for year in years:
        subprocess.run(
            [sys.executable, "scripts/scrape_mcc_archive.py", "--year", str(year), "--out", "data/raw/mcc_ug"],
            check=False,
        )
        index = Path(f"data/raw/mcc_ug/{year}/archive_index.csv")
        if index.exists():
            manifest_rows.append(
                {
                    "source": f"mcc_ug_{year}",
                    "page": "https://mcc.nic.in/archive-ug/",
                    "title": "archive_index",
                    "url": "https://mcc.nic.in/archive-ug/",
                    "local_file": str(index).replace("\\", "/"),
                    "bytes": index.stat().st_size,
                    "sha256": sha256(index),
                }
            )


def download_ncrb_and_misc(manifest_rows: list[dict]) -> None:
    pages = [
        ("ncrb", "https://ncrb.gov.in/accidental-deaths-suicides-in-india-adsi.html", Path("data/external/ncrb/raw")),
        ("ilo", "https://www.ilo.org/publications/major-publications/india-employment-report-2024-youth-employment-education-and-skills", Path("data/external/ilo/raw")),
        ("aishe", "https://aishe.gov.in/", Path("data/external/aishe/raw")),
        ("udise", "https://udiseplus.gov.in/", Path("data/external/udise/raw")),
        (
            "nmc_stipend",
            "https://www.nmc.org.in/information-desk/for-students-to-study-in-india/details-of-stipend-paid-by-medical-colleges/",
            Path("data/external/nmc/raw"),
        ),
        (
            "cureus_neet_anxiety",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC10523350/",
            Path("data/external/literature/raw"),
        ),
    ]
    for label, url, out in pages:
        crawl_page_for_files(url, out, manifest_rows, label)


def write_manifest(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["source", "page", "title", "url", "local_file", "bytes", "sha256"]
    # de-dupe by local_file
    uniq: dict[str, dict] = {}
    for row in rows:
        uniq[row["local_file"]] = row
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(uniq.values())
    print(f"manifest rows={len(uniq)} -> {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-mcc-years", action="store_true")
    parser.add_argument("--mcc-years", default="2023,2025")
    args = parser.parse_args()

    rows: list[dict] = []
    download_catalog_pdfs(rows)
    download_kerala(rows)
    download_nirf(rows)
    download_nta_public(rows)
    download_ncrb_and_misc(rows)
    if not args.skip_mcc_years:
        years = [int(y.strip()) for y in args.mcc_years.split(",") if y.strip()]
        download_mcc_years(rows, years)

    write_manifest(rows, Path("data/processed/public_bulk_download_manifest.csv"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
