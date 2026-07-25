"""Append SHA-256 provenance for a downloaded file to download_manifest.csv."""

from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import date
from pathlib import Path

MANIFEST_COLUMNS = [
    "local_file",
    "source_url",
    "retrieved_date",
    "sha256",
    "bytes",
    "rows",
    "redistribution",
    "limitations",
]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in MANIFEST_COLUMNS})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True, help="Local file to register")
    parser.add_argument("--url", default="", help="Source URL or DOI")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/processed/download_manifest.csv"),
    )
    parser.add_argument("--retrieved-date", default=date.today().isoformat())
    parser.add_argument("--rows", default="", help="Optional row count if known")
    parser.add_argument(
        "--redistribution",
        default="not committed; local archive only",
    )
    parser.add_argument("--notes", default="", dest="limitations")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing manifest row with the same local_file path",
    )
    args = parser.parse_args()

    if not args.path.is_file():
        raise SystemExit(f"File not found: {args.path}")

    local = args.path.as_posix()
    entry = {
        "local_file": local,
        "source_url": args.url,
        "retrieved_date": args.retrieved_date,
        "sha256": file_sha256(args.path),
        "bytes": str(args.path.stat().st_size),
        "rows": args.rows,
        "redistribution": args.redistribution,
        "limitations": args.limitations,
    }

    rows = load_manifest(args.manifest)
    existing = [row for row in rows if row.get("local_file") == local]
    if existing and not args.replace:
        raise SystemExit(
            f"Manifest already has {local}. Pass --replace to overwrite that row."
        )
    rows = [row for row in rows if row.get("local_file") != local]
    rows.append(entry)
    write_manifest(args.manifest, rows)

    print(f"registered {local}")
    print(f"  sha256={entry['sha256']}")
    print(f"  bytes={entry['bytes']}")
    print(f"  manifest={args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
