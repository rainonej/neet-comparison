from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

ARCHIVE_URL = "https://mcc.nic.in/archive-ug/"
DEFAULT_PATTERN = r"(allotment|admitted|seat matrix|vacancy|result)"


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=10))
def fetch(url: str) -> requests.Response:
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    return response


def safe_name(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:140]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--pattern", default=DEFAULT_PATTERN)
    parser.add_argument("--out", type=Path, default=Path("data/raw/mcc_ug"))
    parser.add_argument("--index-only", action="store_true")
    args = parser.parse_args()

    target = args.out / str(args.year)
    target.mkdir(parents=True, exist_ok=True)
    response = fetch(ARCHIVE_URL)
    soup = BeautifulSoup(response.text, "lxml")
    pattern = re.compile(args.pattern, re.I)

    records = []
    for link in soup.find_all("a", href=True):
        title = " ".join(link.get_text(" ", strip=True).split())
        href = urljoin(ARCHIVE_URL, link["href"])
        context = " ".join(link.parent.get_text(" ", strip=True).split()) if link.parent else title
        if str(args.year) not in context and str(args.year) not in href:
            continue
        if not pattern.search(title + " " + context):
            continue
        if not ("pdf" in href.lower() or "download" in title.lower() or "view" in title.lower()):
            continue
        records.append((title or context, href))

    # Deduplicate while retaining order.
    unique = []
    seen = set()
    for record in records:
        if record[1] not in seen:
            seen.add(record[1]); unique.append(record)

    with (target / "archive_index.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f); writer.writerow(["title", "url", "local_file"])
        for i, (title, url) in enumerate(unique, start=1):
            name = f"{i:03d}_{safe_name(title)}.pdf"
            writer.writerow([title, url, name])
            if not args.index_only:
                out = target / name
                if not out.exists():
                    data = fetch(url).content
                    out.write_bytes(data)
                    print(f"Downloaded {title} -> {out}")
    print(f"Indexed {len(unique)} matching archive items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
