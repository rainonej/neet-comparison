from pathlib import Path

import pandas as pd


def test_source_ids_are_unique_and_catalog_is_substantial():
    catalog = pd.read_csv("docs/source_catalog.csv")
    assert len(catalog) >= 30
    assert catalog["id"].is_unique
    assert {"exam_scores", "admissions", "household_resources", "labor_outcomes"}.issubset(
        set(catalog["domain"])
    )


def test_neet_histogram_matches_summary():
    histogram = pd.read_csv("data/processed/neet_2024_marks_histogram.csv")
    summary = pd.read_csv("data/processed/neet_2024_marks_summary.csv")
    rows = int(summary.loc[summary["metric"] == "rows", "value"].iloc[0])
    assert int(histogram["candidates"].sum()) == rows
    assert abs(histogram["share"].sum() - 1) < 1e-9


def test_raw_external_marks_are_manifested_but_not_required():
    # The 32 MB third-party reconstruction is intentionally excluded from the
    # distributable repository. Its provenance and checksum must remain.
    assert not Path("data/external/neet-2024-center-marks.csv").exists()
    manifest = pd.read_csv("data/processed/download_manifest.csv")
    row = manifest.loc[manifest["local_file"] == "data/external/neet-2024-center-marks.csv"]
    assert len(row) == 1
    assert int(row.iloc[0]["rows"]) > 2_000_000
    assert "data/external/**/*" in Path(".gitignore").read_text()
