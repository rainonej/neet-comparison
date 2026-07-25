from pathlib import Path

import pandas as pd


def test_neet_reconciliation_passes():
    path = Path("data/processed/neet_2024_nta_reconciliation.csv")
    assert path.exists()
    row = pd.read_csv(path).iloc[0]
    assert int(row["local_mark_rows"]) == int(row["official_appeared_excluding_ufm"]) == 2_333_162
    assert bool(row["centre_count_match_official"])
    assert "PASS" in str(row["verdict"])


def test_mcc_seat_matrix_has_totals():
    path = Path("data/processed/mcc_2024/mcc_2024_seat_matrix.csv")
    assert path.exists()
    df = pd.read_csv(path)
    assert len(df) >= 500
    assert {"institute", "program", "quota", "total_seats"}.issubset(df.columns)
    assert pd.to_numeric(df["total_seats"], errors="coerce").fillna(0).sum() > 10_000


def test_mcc_round1_allotment_schema():
    path = Path("data/processed/mcc_2024/mcc_2024_allotment_round_1.csv")
    assert path.exists()
    df = pd.read_csv(path)
    assert len(df) > 20_000
    assert {"rank", "allotted_quota", "allotted_institute", "course", "candidate_category"}.issubset(
        df.columns
    )


def test_mcc_round3_wide_and_allotment():
    allot = pd.read_csv("data/processed/mcc_2024/mcc_2024_allotment_round_3.csv")
    wide = pd.read_csv("data/processed/mcc_2024/mcc_2024_round3_status_wide.csv")
    assert len(allot) > 5_000
    assert len(wide) > 30_000
    assert set(allot["course"].dropna().unique()) <= {"MBBS", "BDS", "B.Sc. Nursing"}
    assert {"r1_institute", "r2_institute", "r3_institute", "rank"}.issubset(wide.columns)


def test_kerala_panels_deidentified():
    rank = pd.read_csv("data/processed/kerala/kerala_2025_medical_ranklist.csv")
    allot = pd.read_csv("data/processed/kerala/kerala_2025_mbbs_allotments.csv")
    last = pd.read_csv("data/processed/kerala/kerala_2025_mbbs_last_ranks.csv")
    assert len(rank) > 40_000
    assert len(allot) > 15_000
    assert len(last) > 1_000
    forbidden = {"appl_no", "applno", "application_number", "application_no", "name"}
    for df in (rank, allot, last):
        cols = {c.lower() for c in df.columns}
        assert not (cols & forbidden)
    assert set(allot["course"].dropna().unique()) <= {"MBBS", "BDS"}
