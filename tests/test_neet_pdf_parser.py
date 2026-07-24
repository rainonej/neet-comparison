from pathlib import Path


def test_repo_has_source_catalog():
    assert Path("docs/source_catalog.csv").exists()


def test_repo_has_gap_document():
    assert "Applicant household income" in Path("docs/DATA_GAPS.md").read_text()
