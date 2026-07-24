from __future__ import annotations

from pathlib import Path
import pandas as pd


def main() -> int:
    catalog = pd.read_csv("docs/source_catalog.csv", keep_default_na=False)
    order = ["critical", "high", "medium", "low"]
    catalog["priority"] = pd.Categorical(catalog["priority"], order, ordered=True)
    table = (
        catalog.sort_values(["priority", "domain", "id"])
        [["id", "domain", "publisher", "year", "geography", "status", "priority", "notes"]]
    )
    Path("reports").mkdir(exist_ok=True)
    table.to_csv("reports/source_status.csv", index=False)
    counts = catalog.groupby(["priority", "status"], observed=True).size().unstack(fill_value=0)
    Path("reports/source_status.md").write_text(
        "# Source status\n\n" + counts.to_markdown() + "\n",
        encoding="utf-8",
    )
    print(counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
