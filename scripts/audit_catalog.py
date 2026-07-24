from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

REQUIRED = {
    "id", "domain", "title", "publisher", "year", "geography", "unit",
    "access", "format", "url", "variables", "linkage_keys", "candidate_level",
    "socioeconomic_variables", "status", "priority", "notes",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("docs/source_catalog.csv"))
    args = parser.parse_args()

    df = pd.read_csv(args.catalog, keep_default_na=False)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise SystemExit(f"Missing columns: {sorted(missing)}")
    if df["id"].duplicated().any():
        dupes = df.loc[df["id"].duplicated(keep=False), "id"].tolist()
        raise SystemExit(f"Duplicate source ids: {dupes}")

    summary = (
        df.groupby(["domain", "status"], dropna=False)
        .size()
        .rename("sources")
        .reset_index()
        .sort_values(["domain", "status"])
    )
    print(f"Sources: {len(df)}")
    print(f"Domains: {df['domain'].nunique()}")
    print(f"Critical sources: {(df['priority'] == 'critical').sum()}")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
