"""Tests for MoSPI processed aggregates and wage/coaching loaders."""

from __future__ import annotations

from pathlib import Path

import pytest

from neet_microsim.evidence import (
    load_cmse_coaching_priors,
    load_plfs_extended_wage_anchors,
    load_wage_anchors,
)
from neet_microsim.privilege import build_career_paths_for_privilege

REPO = Path(__file__).resolve().parents[1]
PROCESSED = REPO / "data" / "processed"
MOSPI = PROCESSED / "mospi"


@pytest.mark.skipif(not (MOSPI / "plfs_wage_anchors.csv").exists(), reason="mospi aggregates missing")
def test_plfs_wage_anchors_preferred() -> None:
    wages = load_wage_anchors(PROCESSED)
    assert wages["medicine"].statistic == "median"
    assert wages["medicine"].monthly_inr == pytest.approx(53000.0)
    assert wages["medicine"].geometric_sd > 1.5
    assert wages["engineering"].monthly_inr == pytest.approx(40000.0)
    assert "PLFS" in wages["medicine"].source
    # Annual median is 12x monthly median (no /1.15 mean adjustment).
    assert wages["medicine"].annual_median_inr() == pytest.approx(53000.0 * 12.0)


@pytest.mark.skipif(not (MOSPI / "plfs_wage_anchors.csv").exists(), reason="mospi aggregates missing")
def test_extended_plfs_anchors_and_privilege_paths() -> None:
    ext = load_plfs_extended_wage_anchors(PROCESSED)
    assert "non_professional_graduate" in ext
    assert "no_college" in ext
    careers = build_career_paths_for_privilege(processed=PROCESSED)
    assert "PLFS" in careers["government_mbbs"].matched_earnings.source
    assert careers["no_college"].matched_earnings.log_mean < careers[
        "government_mbbs"
    ].matched_earnings.log_mean


@pytest.mark.skipif(not (MOSPI / "cmse_coaching_priors.csv").exists(), reason="mospi aggregates missing")
def test_cmse_coaching_priors_class_x_xii() -> None:
    priors = load_cmse_coaching_priors(PROCESSED)
    row = priors.query("sector_label == 'all' and enrolment_band == 'class_x_xii'").iloc[0]
    assert 0.3 < float(row["coaching_rate_weighted"]) < 0.5
    assert float(row["coaching_exp_p50"]) > 5000
