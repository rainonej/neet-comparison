"""Build a recursive inventory of local public data files (gitignored)."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOTS = [Path("data/external"), Path("data/raw")]
OUT = Path("data/processed/local_data_inventory.csv")
EXTS = {".pdf", ".csv", ".json", ".html", ".db", ".sqlite", ".xlsx", ".xls", ".zip", ".parquet", ".tsv"}


def sha256_quick(path: Path, limit: int = 1024 * 1024) -> str:
    """Hash first 1MB + size for large files; full hash under 8MB."""
    size = path.stat().st_size
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        if size <= 8 * 1024 * 1024:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
            return digest.hexdigest()
        digest.update(handle.read(limit))
        digest.update(str(size).encode())
        return "partial:" + digest.hexdigest()


def main() -> int:
    rows = []
    for root in ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.name in {".gitkeep", "README.md"}:
                continue
            if path.suffix.lower() not in EXTS:
                continue
            rel = path.as_posix()
            size = path.stat().st_size
            rows.append(
                {
                    "path": rel,
                    "bytes": size,
                    "ext": path.suffix.lower(),
                    "sha256_or_partial": sha256_quick(path),
                }
            )
    rows.sort(key=lambda r: r["path"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "ext", "sha256_or_partial"])
        writer.writeheader()
        writer.writerows(rows)
    total = sum(r["bytes"] for r in rows)
    print(f"wrote {OUT} rows={len(rows)} total_mb={total/1e6:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
