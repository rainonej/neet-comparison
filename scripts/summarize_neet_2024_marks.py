from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/external/neet-2024-center-marks.csv"),
    )
    parser.add_argument("--out", type=Path, default=Path("data/processed"))
    parser.add_argument("--retrieved-date", default="2026-07-24")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(
        args.input,
        header=None,
        names=["centre_id", "serial_number", "marks"],
        dtype={"centre_id": "int32", "serial_number": "int32", "marks": "int16"},
    )

    quantiles = [0, 0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 0.999, 1]
    frame["marks"].quantile(quantiles).rename_axis("quantile").reset_index(
        name="marks"
    ).to_csv(args.out / "neet_2024_marks_quantiles.csv", index=False)

    distribution = (
        frame["marks"].value_counts().sort_index().rename_axis("marks").reset_index(name="candidates")
    )
    distribution["share"] = distribution["candidates"] / len(frame)
    distribution["cumulative_share"] = distribution["share"].cumsum()
    distribution.to_csv(args.out / "neet_2024_marks_distribution.csv", index=False)

    bins = [-180, 0, 100, 200, 300, 400, 500, 600, 650, 700, 721]
    labels = ["<0", "0–99", "100–199", "200–299", "300–399", "400–499", "500–599", "600–649", "650–699", "700–720"]
    score_bands = pd.cut(frame["marks"], bins=bins, labels=labels, right=False, include_lowest=True)
    histogram = score_bands.value_counts(sort=False).rename_axis("score_band").reset_index(name="candidates")
    histogram["share"] = histogram["candidates"] / len(frame)
    histogram.to_csv(args.out / "neet_2024_marks_histogram.csv", index=False)

    summary = pd.DataFrame(
        [
            ["source_file", args.input.name, ""],
            ["sha256", file_sha256(args.input), ""],
            ["rows", len(frame), "candidate-mark rows"],
            ["unique_centres", frame["centre_id"].nunique(), "test-centre IDs"],
            ["minimum_marks", int(frame["marks"].min()), "marks"],
            ["maximum_marks", int(frame["marks"].max()), "marks"],
            ["mean_marks", float(frame["marks"].mean()), "marks"],
            ["standard_deviation", float(frame["marks"].std()), "marks"],
            ["median_marks", float(frame["marks"].median()), "marks"],
            ["negative_score_rows", int((frame["marks"] < 0).sum()), "candidate-mark rows"],
            ["score_720_rows", int((frame["marks"] == 720).sum()), "candidate-mark rows"],
        ],
        columns=["metric", "value", "unit"],
    )
    summary.to_csv(args.out / "neet_2024_marks_summary.csv", index=False)

    pd.DataFrame(
        [
            {
                "local_file": str(args.input),
                "source_url": "https://github.com/hq969/neet-2024-center-marks/raw/refs/heads/main/csv/neet-2024-center-marks.csv",
                "retrieved_date": args.retrieved_date,
                "sha256": file_sha256(args.input),
                "bytes": args.input.stat().st_size,
                "rows": len(frame),
                "redistribution": "not committed; third-party reconstruction of official NTA PDFs",
                "limitations": "No identity, domicile, category, gender, income, coaching, or admission outcome. Reconcile row count with official candidate totals.",
            }
        ]
    ).to_csv(args.out / "download_manifest.csv", index=False)

    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
