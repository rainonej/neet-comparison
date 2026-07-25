"""Probe gated archives and record login/access status (does not store credentials).

MoSPI / DHS / OpenICPSR require interactive free accounts. This script checks
whether endpoints respond without auth and writes a status CSV for the tracker.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import requests

TARGETS = [
    {
        "dataset": "OpenICPSR_E112992",
        "url": "https://www.openicpsr.org/openicpsr/project/112992/version/V1/view",
        "download_hint": "https://www.openicpsr.org/openicpsr/project/112992/version/V1/download/data",
        "local_dir": "data/external/openicpsr/E112992/raw",
        "provider": "OpenICPSR",
    },
    {
        "dataset": "MoSPI_PLFS",
        "url": "https://microdata.gov.in/NADA/index.php/catalog/PLFS",
        "download_hint": "https://microdata.gov.in/NADA/index.php/catalog/213",
        "local_dir": "data/external/mospi/plfs",
        "provider": "MoSPI",
    },
    {
        "dataset": "MoSPI_HCES",
        "url": "https://microdata.gov.in/NADA/index.php/catalog/237",
        "download_hint": "https://microdata.gov.in/NADA/index.php/catalog/237/get-microdata",
        "local_dir": "data/external/mospi/hces",
        "provider": "MoSPI",
    },
    {
        "dataset": "MoSPI_CMSE",
        "url": "https://microdata.gov.in/NADA/index.php/catalog/255",
        "download_hint": "https://microdata.gov.in/NADA/index.php/catalog/255/get-microdata",
        "local_dir": "data/external/mospi/cmse",
        "provider": "MoSPI",
    },
    {
        "dataset": "MoSPI_AIDIS",
        "url": "https://microdata.gov.in/NADA/index.php/catalog/156",
        "download_hint": "https://microdata.gov.in/NADA/index.php/catalog/156/get-microdata",
        "local_dir": "data/external/mospi/aidis",
        "provider": "MoSPI",
    },
    {
        "dataset": "DHS_NFHS5",
        "url": "https://dhsprogram.com/data/dataset/India_Standard-DHS_2020.cfm",
        "download_hint": "https://dhsprogram.com/data/available-datasets.cfm",
        "local_dir": "data/external/dhs/nfhs5",
        "provider": "DHS",
    },
]


def probe(url: str) -> tuple[int | None, str, bool]:
    try:
        resp = requests.get(
            url,
            timeout=45,
            allow_redirects=True,
            headers={"User-Agent": "neet-comparison-research/0.1"},
        )
        text = (resp.text or "")[:2000].lower()
        loginish = any(
            token in text or token in resp.url.lower()
            for token in ("login", "sign in", "sign-in", "authenticate", "create account", "register")
        )
        return resp.status_code, resp.url, loginish
    except requests.RequestException as exc:
        return None, str(exc), True


def main() -> int:
    out = Path("data/processed/gated_download_status.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for target in TARGETS:
        local = Path(target["local_dir"])
        local.mkdir(parents=True, exist_ok=True)
        has_data = any(
            p.is_file() and p.suffix.lower() in {".zip", ".dta", ".sav", ".csv", ".dat", ".txt", ".rar"}
            and p.stat().st_size > 10_000
            for p in local.rglob("*")
        )
        status_code, final_url, loginish = probe(target["url"])
        dl_code, dl_url, dl_login = probe(target["download_hint"])
        if has_data:
            status = "downloaded_locally"
        elif loginish or dl_login or (dl_code in {401, 403}):
            status = "blocked_login_required"
        elif status_code and status_code >= 400:
            status = f"http_error_{status_code}"
        else:
            status = "catalog_reachable_download_not_automated"
        rows.append(
            {
                "date": date.today().isoformat(),
                "provider": target["provider"],
                "dataset": target["dataset"],
                "status": status,
                "catalog_http": status_code if status_code is not None else "",
                "catalog_final_url": final_url,
                "download_http": dl_code if dl_code is not None else "",
                "download_final_url": dl_url,
                "local_dir": target["local_dir"],
                "next_action": (
                    "register hashes via register_download.py"
                    if has_data
                    else "create free account and download archives per docs/GATED_NEXT.md"
                ),
            }
        )
        print(f"{target['dataset']}: {status}")

    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
