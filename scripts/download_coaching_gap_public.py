"""Download public artifacts that help close the coaching → score → seat gap.

Anonymous / no-login sources only. Does not request gated microdata.
Raw files stay under data/external/ (gitignored). Register key files after run.
"""

from __future__ import annotations

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

ROOT = Path(__file__).resolve().parents[1]


def log(msg: str) -> None:
    print(msg, flush=True)


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


def download(url: str, dest: Path, timeout: int = 60, attempts: int = 3) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        log(f"SKIP existing {dest} ({dest.stat().st_size} bytes)")
        return True
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            log(f"GET [{attempt + 1}/{attempts}] {url}")
            response = SESSION.get(url, timeout=timeout, allow_redirects=True)
            if response.status_code >= 400:
                error = RuntimeError(f"HTTP {response.status_code}")
                if attempt + 1 < attempts:
                    time.sleep(min(2**attempt, 8))
                continue
            # Reject tiny HTML error pages masquerading as PDFs
            content_type = response.headers.get("content-type", "").lower()
            if dest.suffix.lower() == ".pdf" and "html" in content_type and len(response.content) < 5000:
                error = RuntimeError(f"got HTML instead of PDF ({content_type})")
                break
            dest.write_bytes(response.content)
            log(f"OK {dest} ({dest.stat().st_size} bytes)")
            return True
        except Exception as exc:  # noqa: BLE001
            error = exc
            if attempt + 1 < attempts:
                time.sleep(min(2**attempt, 8))
    log(f"FAIL {url} -> {error}")
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
    return bool(re.search(r"\.(pdf|xlsx?|csv|zip|docx?|json)($|\?)", url, re.I))


def record(rows: list[dict], source: str, url: str, dest: Path, page: str = "", title: str = "") -> None:
    if not dest.exists() or dest.stat().st_size == 0:
        return
    rows.append(
        {
            "source": source,
            "page": page,
            "title": title or dest.name,
            "url": url,
            "local_file": dest.as_posix(),
            "bytes": str(dest.stat().st_size),
            "sha256": sha256(dest),
        }
    )


def download_osf(rows: list[dict]) -> None:
    """Known OSF view-only file GUIDs from prior catalog pass."""
    out = ROOT / "data/external/osf/tnh4x/raw"
    view = "871cca8775f8420e802e172b5534673e"
    # Fixed GUIDs already discovered in earlier bootstrap; avoid hanging on OSF SPA listing.
    files = [
        ("nz8fd", "Data_for_analysis.csv"),
    ]
    for existing in out.glob("*"):
        if existing.is_file() and existing.stat().st_size > 0:
            record(
                rows,
                "osf_tnh4x",
                f"https://osf.io/tnh4x/?view_only={view}",
                existing,
                title=existing.name,
            )
    for guid, filename in files:
        url = f"https://osf.io/download/{guid}/?view_only={view}"
        dest = out / filename
        if download(url, dest):
            record(rows, "osf_tnh4x", url, dest, title=filename)


def download_dakshana(rows: list[dict]) -> None:
    out = ROOT / "data/external/dakshana/raw"
    items = [
        ("https://www.dakshana.org/reports/", out / "_page_reports.html"),
        ("https://www.dakshana.org/wp-content/uploads/2025/09/AR24.pdf", out / "AR24.pdf"),
        ("https://dakshana.org/wp-content/uploads/2024/07/AR23_fast.pdf", out / "AR23_fast.pdf"),
        ("https://www.dakshana.org/wp-content/uploads/2023/08/AR22.pdf", out / "AR22.pdf"),
        ("https://www.dakshana.org/wp-content/uploads/2022/08/AR21.pdf", out / "AR21.pdf"),
        ("https://www.dakshana.org/wp-content/uploads/2021/08/AR20.pdf", out / "AR20.pdf"),
        ("https://www.dakshana.org/", out / "_page_home.html"),
    ]
    for url, dest in items:
        if download(url, dest):
            record(rows, "dakshana", url, dest)

    # Crawl reports page + home for JDST / selection PDFs
    for page_path in [out / "_page_reports.html", out / "_page_home.html"]:
        if not page_path.exists():
            continue
        html = page_path.read_text(encoding="utf-8", errors="ignore")
        base = "https://www.dakshana.org/"
        for text, href in extract_links(html, base):
            if not is_data_file(href):
                continue
            if not re.search(r"(AR\d|JDST|selection|scholar|neet|annual|report)", text + href, re.I):
                continue
            dest = out / safe_name(href)
            if download(href, dest):
                record(rows, "dakshana", href, dest, page=str(page_path), title=text)


def download_cbse_dummy_schools(rows: list[dict]) -> None:
    out = ROOT / "data/external/cbse/raw"
    pages = [
        "https://www.cbse.gov.in/cbsenew/press.html",
        "https://www.cbse.gov.in/cbsenew/cbse.html",
    ]
    for page in pages:
        html_path = out / f"_page_{safe_name(page, 'press')}.html"
        if not download(page, html_path):
            continue
        record(rows, "cbse_press", page, html_path, title="press_listing")
        html = html_path.read_text(encoding="utf-8", errors="ignore")
        for text, href in extract_links(html, page):
            blob = f"{text} {href}".lower()
            if not (
                ("disaffiliat" in blob or "dummy" in blob or "downgrad" in blob)
                and (is_data_file(href) or href.lower().endswith(".pdf"))
            ):
                # also grab any press PDF from March 2024 window if labeled
                if not (is_data_file(href) and ("2024" in blob or "dummy" in blob or "disaffiliat" in blob)):
                    continue
            dest = out / safe_name(href)
            if download(href, dest):
                record(rows, "cbse_dummy_schools", href, dest, page=page, title=text)

    # Known news mirrors listing school names (for registry construction if official PDF blocked)
    mirrors = [
        (
            "https://indianexpress.com/article/education/cbse-disaffiliates-20-schools-for-enrolling-dummy-students-9229056/",
            out / "mirror_indian_express_2024-03-22.html",
        ),
        (
            "https://www.thehindu.com/education/cbse-disaffiliates-20-schools-for-enrolling-dummy-students-5-of-them-in-delhi-3-in-up/article67980912.ece",
            out / "mirror_the_hindu_2024-03-22.html",
        ),
    ]
    for url, dest in mirrors:
        if download(url, dest):
            record(rows, "cbse_dummy_schools_mirror", url, dest)


def download_tamil_nadu_archives(rows: list[dict]) -> None:
    """Archive TN Selection Committee home + Archives page and MBBS-related PDFs."""
    out = ROOT / "data/external/tamil_nadu/counselling/raw"
    pages = [
        "https://tnmedicalselection.net/",
        "https://tnmedicalselection.net/Archives.aspx",
    ]
    discovered: list[tuple[str, str, str]] = []
    for page in pages:
        html_path = out / f"_page_{safe_name(page, 'tn')}.html"
        if download(page, html_path):
            record(rows, "tamil_nadu_selection", page, html_path)
            html = html_path.read_text(encoding="utf-8", errors="ignore")
            for text, href in extract_links(html, page):
                blob = f"{text} {href}"
                if not is_data_file(href):
                    continue
                if re.search(
                    r"(mbbs|bds|rank|merit|allot|7\.5|government.?school|management|neet)",
                    blob,
                    re.I,
                ):
                    discovered.append((text, href, page))

    # Direct known public MBBS/BDS list PDFs (2023-24 examples + home news crawl)
    known = [
        "https://tnmedicalselection.net/news/15072023215007.pdf",  # MQ rank list
        "https://tnmedicalselection.net/news/27072023151144.pdf",  # 7.5% allotment
    ]
    for url in known:
        discovered.append((Path(urlparse(url).path).name, url, "known_url"))

    # Deduplicate and download
    seen: set[str] = set()
    for text, href, page in discovered:
        if href in seen:
            continue
        seen.add(href)
        dest = out / safe_name(href)
        if download(href, dest):
            record(rows, "tamil_nadu_selection", href, dest, page=page, title=text)
        time.sleep(0.4)


def download_bihar_super50(rows: list[dict]) -> None:
    out = ROOT / "data/external/bihar_super50/raw"
    pages = [
        "https://coaching.biharboardonline.com/",
        "https://coaching.biharboardonline.com/index",
        "https://www.biharboardonline.com/",
    ]
    for page in pages:
        html_path = out / f"_page_{safe_name(page, 'bseb')}.html"
        if not download(page, html_path):
            continue
        record(rows, "bihar_super50", page, html_path)
        html = html_path.read_text(encoding="utf-8", errors="ignore")
        for text, href in extract_links(html, page):
            blob = f"{text} {href}".lower()
            if not is_data_file(href):
                continue
            if re.search(r"(super.?50|neet|jee|coaching|prospectus|notification|brochure|admit)", blob):
                dest = out / safe_name(href)
                if download(href, dest):
                    record(rows, "bihar_super50", href, dest, page=page, title=text)


def download_csrl_and_sathee_public(rows: list[dict]) -> None:
    """Public program pages only — not applicant microdata."""
    items = [
        ("csrl", "https://www.csrl.in/", ROOT / "data/external/csrl/raw/_page_home.html"),
        ("csrl", "https://www.super30.org/", ROOT / "data/external/csrl/raw/_page_super30.html"),
        ("sathee", "https://sathee.iitk.ac.in/", ROOT / "data/external/sathee/raw/_page_home.html"),
        ("sathee", "https://sathee.online/", ROOT / "data/external/sathee/raw/_page_sathee_online.html"),
        (
            "careers360_survey_article",
            "https://medicine.careers360.com/articles/neet-preparation-survey",
            ROOT / "data/external/careers360/raw/_page_neet_preparation_survey.html",
        ),
    ]
    for source, url, dest in items:
        if download(url, dest):
            record(rows, source, url, dest)
            if dest.suffix == ".html":
                html = dest.read_text(encoding="utf-8", errors="ignore")
                for text, href in extract_links(html, url):
                    if is_data_file(href) and re.search(
                        r"(report|result|prospectus|brochure|notification|pdf)",
                        f"{text} {href}",
                        re.I,
                    ):
                        fdest = dest.parent / safe_name(href)
                        if download(href, fdest):
                            record(rows, source, href, fdest, page=url, title=text)


def write_manifest(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["source", "page", "title", "url", "local_file", "bytes", "sha256"]
    uniq: dict[str, dict] = {}
    for row in rows:
        uniq[row["local_file"]] = row
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(uniq.values())
    log(f"manifest rows={len(uniq)} -> {path}")


def main() -> int:
    rows: list[dict] = []
    log("=== OSF ===")
    download_osf(rows)
    log("=== Dakshana ===")
    download_dakshana(rows)
    log("=== CBSE dummy schools ===")
    download_cbse_dummy_schools(rows)
    log("=== Tamil Nadu counselling ===")
    download_tamil_nadu_archives(rows)
    log("=== Bihar Super 50 ===")
    download_bihar_super50(rows)
    log("=== CSRL / SATHEE / Careers360 public pages ===")
    download_csrl_and_sathee_public(rows)
    write_manifest(rows, ROOT / "data/processed/coaching_gap_public_manifest.csv")
    log("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
