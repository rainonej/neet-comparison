"""Tests for LEGACY independent-offers privilege accounting demo.

Production pathway tests live in test_score_privilege.py.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from neet_microsim.attempt_inference import applicant_repeater_share, repeater_sensitivity_table
from neet_microsim.privilege import (
    PrivilegeStratum,
    access_probabilities,
    affordability_only_ratio,
    build_career_paths_for_privilege,
    load_privilege_config,
    run_privilege_pipeline,
    simulate_stratum_outcomes,
)

REPO = Path(__file__).resolve().parents[1]
PROCESSED = REPO / "data" / "processed"
CONFIG = REPO / "config" / "privilege_scenarios.yaml"


def test_repeater_inference_independence_and_selection() -> None:
    r = 0.7142
    assert applicant_repeater_share(
        p_repeater_among_admitted=r, relative_admit_prob=1.0
    ) == pytest.approx(r)
    # If repeaters are twice as likely to be admitted, applicant repeater share falls.
    a2 = applicant_repeater_share(p_repeater_among_admitted=r, relative_admit_prob=2.0)
    assert a2 < r
    assert a2 == pytest.approx(r / (r + 2.0 * (1.0 - r)))
    table = repeater_sensitivity_table()
    assert "p_repeater_among_applicants" in table.columns
    assert table["identifies_full_attempt_count_distribution"].eq(False).all()


@pytest.mark.skipif(not CONFIG.exists(), reason="privilege config missing")
def test_affordability_only_ratio_near_two() -> None:
    config = load_privilege_config(CONFIG)
    ratio = affordability_only_ratio(config)
    assert 1.7 < ratio < 2.1


@pytest.mark.skipif(not CONFIG.exists(), reason="privilege config missing")
def test_baseline_prep_does_not_change_access() -> None:
    config = load_privilege_config(CONFIG)
    modest = PrivilegeStratum(
        id="t",
        label="t",
        school_medium="english",
        can_afford_private=True,
        metro_proximity="non_metro",
        prep_intensity="modest",
    )
    intensive = PrivilegeStratum(
        id="t2",
        label="t2",
        school_medium="english",
        can_afford_private=True,
        metro_proximity="non_metro",
        prep_intensity="intensive",
    )
    a = access_probabilities(modest, config, admission_profile="baseline_neutral_prep")
    b = access_probabilities(intensive, config, admission_profile="baseline_neutral_prep")
    assert a.p_accessible_seat == pytest.approx(b.p_accessible_seat)
    c = access_probabilities(intensive, config, admission_profile="prep_sensitivity")
    assert c.p_accessible_seat > a.p_accessible_seat


@pytest.mark.skipif(
    not (PROCESSED / "published_estimates.csv").exists(),
    reason="processed evidence missing",
)
def test_within_stratum_government_earns_more_if_employed() -> None:
    config = load_privilege_config(CONFIG)
    careers = build_career_paths_for_privilege(processed=PROCESSED)
    stratum = PrivilegeStratum(
        id="english_can_afford_nonmetro_modest",
        label="mid",
        school_medium="english",
        can_afford_private=True,
        metro_proximity="non_metro",
        prep_intensity="modest",
    )
    result = simulate_stratum_outcomes(stratum, config, careers, draws=3_000, seed=1)
    assert result["government_annual_mean_if_employed"] > result["no_seat_annual_mean_if_employed"]
    assert result["government_annual_median_if_employed"] > result["no_seat_annual_median_if_employed"]
    assert result["p_accessible"] > result["access"].p_government_offer
    metrics = {row["metric"] for row in result["quantile_rows"]}
    assert "annual" in metrics
    assert "annual_if_employed" in metrics
    assert "npv" not in metrics


@pytest.mark.skipif(
    not (PROCESSED / "published_estimates.csv").exists(),
    reason="processed evidence missing",
)
def test_pipeline_writes_artifacts(tmp_path: Path) -> None:
    paths = run_privilege_pipeline(
        config_path=CONFIG,
        processed=PROCESSED,
        output_dir=tmp_path / "bayesian",
        draws=1_500,
    )
    for path in paths.values():
        assert path.exists()
        assert path.stat().st_size > 0
    import json

    story = json.loads(paths["inequality_story"].read_text(encoding="utf-8"))
    assert story["primary_metric"] == "annual_earnings"
    assert story["production_pathway"] is False
    assert story["status"] == "legacy_accounting_demo"
    assert story["superseded_by"] == "fixed_reference_threshold"
    assert story["affordability_only_access_ratio"] > 1.7
    assert story["decomposition"]["full_ladder_ratio_top_over_low"] > 3.0
    assert "earnings_histograms" in paths
    assert "earnings_kde" in paths
    assert "attempt_repeater_sensitivity" in paths
    assert "attempt_inference" in story
    # College types should not invent a large wage gap.
    assert 0.85 < story["decomposition"]["govt_vs_private_college_median_ratio_mid"] < 1.15
    assert story["decomposition"]["med_vs_nocollege_median_ratio_mid"] > 1.5
    assert any("LEGACY" in w for w in story["warnings"])


def test_govt_and_private_college_share_wage_prior() -> None:
    careers = build_career_paths_for_privilege(processed=PROCESSED)
    gov = careers["government_mbbs"].matched_earnings.mean
    priv = careers["private_mbbs"].matched_earnings.mean
    assert gov == pytest.approx(priv, rel=0.02)
    pub = careers["physician_public_sector"].matched_earnings.mean
    prv = careers["physician_private_sector"].matched_earnings.mean
    assert pub > prv
