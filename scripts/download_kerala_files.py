"""Download every PDF/XLS/CSV linked from already-saved Kerala CEE HTML pages."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "neet-comparison-research/0.1"}
ROOT = Path("data/external/kerala_cee/raw")
OUT = ROOT / "files"
OUT.mkdir(parents=True, exist_ok=True)

BASES = {
    "keam2025_ranklist.html": "https://cee.kerala.gov.in/keam2025/ranklist",
    "keam2025_allotlist.html": "https://cee.kerala.gov.in/keam2025/allotlist",
    "keam2025_last_rank.html": "https://cee.kerala.gov.in/keam2025/last_rank",
    "keam2025_catlist.html": "https://cee.kerala.gov.in/keam2025/catlist",
    "keam2025_home.html": "https://cee.kerala.gov.in/keam2025/",
    "cee_home.html": "https://cee.kerala.gov.in/",
    "keam2026_notification.html": "https://cee.kerala.gov.in/keam2026/notification",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_name(url: str) -> str:
    name = Path(url.split("?")[0]).name
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:180]


def main() -> int:
    session = requests.Session()
    session.headers.update(UA)
    urls: dict[str, str] = {}

    for html_name, base in BASES.items():
        path = ROOT / html_name
        if not path.exists():
            continue
        soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "lxml")
        for a in soup.find_all("a", href=True):
            href = urljoin(base, a["href"])
            if re.search(r"\.(pdf|xlsx?|csv|zip)($|\?)", href, re.I):
                urls[href] = " ".join(a.get_text(" ", strip=True).split())

    # Also crawl 2024 pages fresh
    for page in [
        "https://cee.kerala.gov.in/keam2024/ranklist",
        "https://cee.kerala.gov.in/keam2024/allotlist",
        "https://cee.kerala.gov.in/keam2024/last_rank",
        "https://cee.kerala.gov.in/keam2024/catlist",
        "https://cee.kerala.gov.in/keam2023/ranklist",
        "https://cee.kerala.gov.in/keam2023/allotlist",
        "https://cee.kerala.gov.in/keam2023/last_rank",
        "https://cee.kerala.gov.in/keam2023/catlist",
    ]:
        try:
            resp = session.get(page, timeout=60)
            resp.raise_for_status()
            local = ROOT / f"_crawl_{safe_name(page)}.html"
            if not local.suffix:
                local = Path(str(local) + ".html")
            # keep readable names
            year = re.search(r"keam(20\d\d)", page)
            kind = page.rstrip("/").split("/")[-1]
            local = ROOT / f"keam{year.group(1)}_{kind}.html" if year else local
            local.write_bytes(resp.content)
            soup = BeautifulSoup(resp.text, "lxml")
            for a in soup.find_all("a", href=True):
                href = urljoin(page, a["href"])
                if re.search(r"\.(pdf|xlsx?|csv|zip)($|\?)", href, re.I):
                    urls[href] = " ".join(a.get_text(" ", strip=True).split())
            print(f"crawled {page}: status={resp.status_code}")
        except Exception as exc:  # noqa: BLE001
            print(f"crawl fail {page}: {exc}")

    print(f"unique file urls: {len(urls)}")
    ok = 0
    fail = 0
    for i, (url, title) in enumerate(sorted(urls.items()), start=1):
        dest = OUT / safe_name(url)
        if dest.exists() and dest.stat().st_size > 1000:
            ok += 1
            continue
        try:
            resp = session.get(url, timeout=120)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            print(f"[{i}/{len(urls)}] OK {dest.name} ({len(resp.content)} bytes) {title[:60]}")
            ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"[{i}/{len(urls)}] FAIL {url} {exc}")
            fail += 1

    print(f"done ok={ok} fail={fail} dir={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
