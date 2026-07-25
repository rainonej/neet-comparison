"""Download MoSPI unit-level archives via the official API (resilient).

- Reads MOSPI_API_KEY from .env
- Disables SSL verify for microdata.gov.in (broken chain)
- Streams files (official client buffers whole body and hangs on large zips)
- Skips files already present locally
- Prefer CSV + documentation; skip JSON/SAS/SPSS/Stata when CSV exists

Usage:
  python scripts/download_mospi_unitdata.py --search "PLFS"
  python scripts/download_mospi_unitdata.py --resume-remaining
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
_orig_request = requests.sessions.Session.request


def _insecure_mospi_request(self, method, url, **kwargs):  # type: ignore[no-untyped-def]
    if isinstance(url, str) and "microdata.gov.in" in url:
        kwargs.setdefault("verify", False)
    return _orig_request(self, method, url, **kwargs)


requests.sessions.Session.request = _insecure_mospi_request  # type: ignore[method-assign]

from MospiUnitdata import list_datasets, list_files  # noqa: E402
from MospiUnitdata.MospiUnitdata import BASE_URL, _request_with_retry  # noqa: E402

# Force line-buffered logs so monitors see progress
try:
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
except Exception:
    pass

SKIP_IF_CSV_EXISTS = (".json.zip", "_json.zip", ".sas.zip", "_sas.zip", ".spss.zip", "_spss.zip", ".stata.zip", "_stata.zip")

REMAINING = [
    ("DDI-IND-MOSPI-NSS-HCES23-24", "data/external/mospi/hces/2023-24/raw"),
    ("DDI-IND-MOSPI-NSS-CMSE80-2025", "data/external/mospi/cmse/2025/raw"),
    (
        "DDI-IND-MOSPI-NSSO-77Rnd-Sch18.2-January2019-December2019",
        "data/external/mospi/aidis/2019/raw",
    ),
]


def load_dotenv() -> None:
    env = Path(".env")
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def api_key(cli: str | None) -> str:
    load_dotenv()
    key = (cli or os.environ.get("MOSPI_API_KEY", "")).strip()
    if not key:
        raise SystemExit("Missing MOSPI_API_KEY in .env")
    return key


def has_csv(folder: Path) -> bool:
    return any(
        p.is_file() and p.stat().st_size > 10_000 and "csv" in p.name.lower()
        for p in folder.glob("*")
    )


def should_skip_name(name: str, folder: Path) -> bool:
    low = name.lower().replace(" ", "")
    if has_csv(folder) and any(tok in low for tok in ("json", "sas", "spss", "stata")):
        # keep non-data docs that happen to mention those words out of this filter
        if low.endswith(".zip") or "data" in low:
            return True
    return False


def stream_download(url: str, headers: dict[str, str], dest: Path, timeout: int = 600) -> bool:
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with requests.get(
            url,
            headers=headers,
            stream=True,
            timeout=timeout,
            verify=False,
        ) as resp:
            if resp.status_code >= 400:
                print(f"  HTTP {resp.status_code} for {dest.name}", flush=True)
                return False
            total = int(resp.headers.get("content-length") or 0)
            written = 0
            last_report = time.time()
            with tmp.open("wb") as handle:
                for chunk in resp.iter_content(chunk_size=1024 * 256):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    written += len(chunk)
                    now = time.time()
                    if now - last_report >= 5:
                        if total:
                            pct = 100.0 * written / total
                            print(
                                f"  … {dest.name}: {written/1e6:.1f}/{total/1e6:.1f} MB ({pct:.0f}%)",
                                flush=True,
                            )
                        else:
                            print(f"  … {dest.name}: {written/1e6:.1f} MB", flush=True)
                        last_report = now
        if written < 100:
            print(f"  tiny/empty response for {dest.name} ({written} bytes)", flush=True)
            tmp.unlink(missing_ok=True)
            return False
        tmp.replace(dest)
        print(f"  OK {dest.name} ({written/1e6:.1f} MB)", flush=True)
        return True
    except requests.RequestException as exc:
        print(f"  FAIL {dest.name}: {exc}", flush=True)
        tmp.unlink(missing_ok=True)
        return False


def download_smart(key: str, idno: str, dest: str) -> bool:
    folder = Path(dest)
    folder.mkdir(parents=True, exist_ok=True)
    print(f"\n=== {idno} -> {folder}", flush=True)
    files = list_files(idno, key)
    if not files:
        print("  no files / API failed", flush=True)
        return False

    headers = {"X-API-KEY": key}
    ok_any = False
    for info in files:
        name = info["name"]
        target = folder / name
        if target.exists() and target.stat().st_size > 1000:
            print(f"  skip existing {name} ({target.stat().st_size/1e6:.1f} MB)", flush=True)
            ok_any = True
            continue
        if should_skip_name(name, folder):
            print(f"  skip alt format {name} (CSV already present)", flush=True)
            continue
        url = f"{BASE_URL}/fileslist/download/{idno}/{info['base64']}"
        print(f"  get {name}", flush=True)
        if stream_download(url, headers, target):
            ok_any = True
    return ok_any


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--search", default=None)
    parser.add_argument("--list-files", metavar="IDNO")
    parser.add_argument("--download", nargs=2, metavar=("IDNO", "DEST"))
    parser.add_argument(
        "--resume-remaining",
        action="store_true",
        help="HCES (fill missing) + CMSE + AIDIS with skip/CSV prefer",
    )
    args = parser.parse_args()
    key = api_key(args.api_key)

    if args.search:
        rows = list_datasets(key, query=args.search) or []
        if not rows:
            print("No results / API unreachable", file=sys.stderr)
            return 1
        for row in rows:
            print(f"{row.get('idno')}\t{row.get('title')}", flush=True)
        return 0

    if args.list_files:
        files = list_files(args.list_files, key) or []
        for f in files:
            print(f.get("name"), f.get("size"), flush=True)
        return 0 if files else 1

    if args.download:
        return 0 if download_smart(key, args.download[0], args.download[1]) else 1

    if args.resume_remaining:
        failures = []
        for idno, dest in REMAINING:
            if not download_smart(key, idno, dest):
                failures.append(idno)
        if failures:
            print("failures:", "; ".join(failures), file=sys.stderr, flush=True)
            return 1
        print("\nDone remaining batch.", flush=True)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
