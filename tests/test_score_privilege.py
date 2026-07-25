"""Tests for score → rank → seat privilege model."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from neet_microsim.score_engine import (
    apply_score_shifts,
    arms_race_signatures,
    coaching_components_sd,
    coaching_shift_sd,
    load_score_config,
    load_score_distribution,
    population_mean_coaching_shift,
)
from neet_microsim.score_privilege import run_score_privilege_pipeline, simulate_score_stratum
from neet_microsim.seat_allocation import allocate_offers, capacity_from_config
from neet_microsim.privilege import PrivilegeStratum, build_career_paths_for_privilege

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config" / "score_privilege_scenarios.yaml"
PROCESSED = REPO / "data" / "processed"
QUANTILES = PROCESSED / "neet_2024_marks_quantiles.csv"


@pytest.mark.skipif(not CONFIG.exists() or not QUANTILES.exists(), reason="score config/data missing")
def test_arms_race_equal_coaching_preserves_relative_shift() -> None:
    config = load_score_config(CONFIG)
    dist = load_score_distribution(config=config, repo_root=REPO)
    rng = np.random.default_rng(0)
    baseline = dist.sample(5000, rng=rng)
    # Everyone intensive: relative coaching shift should be ~0 after subtracting pop mean
    # when force_population_prep matches individual prep.
    shifted, meta = apply_score_shifts(
        baseline,
        dist=dist,
        school_medium="english",
        metro_proximity="non_metro",
        prep_intensity="intensive",
        config=config,
        coaching_profile="conservative",
        subtract_population_mean=True,
        force_population_prep="intensive",
    )
    assert meta["relative_coaching_shift_sd"] == pytest.approx(0.0)
    # Medium/metro still apply
    assert meta["total_location_shift_sd"] == pytest.approx(
        meta["medium_shift_sd"] + meta["metro_shift_sd"]
    )
    assert shifted.mean() != pytest.approx(baseline.mean())


@pytest.mark.skipif(not CONFIG.exists(), reason="score config missing")
def test_capacity_cutoffs_are_seats_over_appeared() -> None:
    config = load_score_config(CONFIG)
    cap = capacity_from_config(config)
    assert 0 < cap.government_cutoff_percentile < cap.private_or_better_cutoff_percentile < 0.2
    rp = np.array([0.0, 0.01, 0.05, 0.5])
    offers = allocate_offers(rp, capacity=cap, can_afford_private=True)
    assert offers.accessible_seat[0]
    assert not offers.accessible_seat[-1]


@pytest.mark.skipif(
    not CONFIG.exists() or not (PROCESSED / "published_estimates.csv").exists(),
    reason="processed evidence missing",
)
def test_higher_privilege_stratum_gets_more_access_unilateral() -> None:
    config = load_score_config(CONFIG)
    careers = build_career_paths_for_privilege(processed=PROCESSED)
    arms = next(s for s in config["arms_race_scenarios"] if s["id"] == "unilateral")
    low = PrivilegeStratum(
        id="low",
        label="low",
        school_medium="tamil",
        can_afford_private=False,
        metro_proximity="non_metro",
        prep_intensity="none",
    )
    high = PrivilegeStratum(
        id="high",
        label="high",
        school_medium="english",
        can_afford_private=True,
        metro_proximity="metro",
        prep_intensity="intensive",
    )
    a = simulate_score_stratum(
        low, config, careers, arms_race=arms, draws=8000, seed=1, privilege_tier="low"
    )
    b = simulate_score_stratum(
        high, config, careers, arms_race=arms, draws=8000, seed=2, privilege_tier="high"
    )
    assert b["summary"].p_accessible_seat > a["summary"].p_accessible_seat
    assert b["summary"].mean_marks > a["summary"].mean_marks


@pytest.mark.skipif(
    not CONFIG.exists() or not (PROCESSED / "published_estimates.csv").exists(),
    reason="processed evidence missing",
)
def test_pipeline_writes_artifacts(tmp_path: Path) -> None:
    paths = run_score_privilege_pipeline(
        config_path=CONFIG,
        processed=PROCESSED,
        output_dir=tmp_path,
        draws=3000,
        arms_race_ids=["unilateral", "everyone_intensive"],
    )
    assert paths["score_inequality_story"].exists()
    assert paths["score_access_by_stratum"].exists()
    story = paths["score_inequality_story"].read_text(encoding="utf-8")
    assert "score_rank_seat" in story
    assert "unilateral" in story


def test_population_mean_coaching_shift_between_profiles() -> None:
    if not CONFIG.exists():
        pytest.skip("missing config")
    config = load_score_config(CONFIG)
    null = population_mean_coaching_shift(config, profile="null")
    cons = population_mean_coaching_shift(config, profile="conservative")
    assert null == pytest.approx(0.0)
    assert cons > 0.0


def test_two_part_coaching_diminishing_intensity() -> None:
    if not CONFIG.exists():
        pytest.skip("missing config")
    config = load_score_config(CONFIG)
    none = coaching_components_sd("none", config, profile="literature_central")
    modest = coaching_components_sd("modest", config, profile="literature_central")
    intensive = coaching_components_sd("intensive", config, profile="literature_central")
    assert none["coaching_shift_sd"] == pytest.approx(0.0)
    # At median spend, intensity term is zero: only θ.
    assert modest["intensity_shift_sd"] == pytest.approx(0.0)
    assert modest["coaching_shift_sd"] == pytest.approx(0.12)
    # 8× median => three doublings: θ + 3β = 0.12 + 0.15
    assert intensive["coaching_shift_sd"] == pytest.approx(0.12 + 3 * 0.05)
    assert coaching_shift_sd("intensive", config, profile="literature_central") > modest[
        "coaching_shift_sd"
    ]


def test_arms_race_signature_signs() -> None:
    if not CONFIG.exists():
        pytest.skip("missing config")
    config = load_score_config(CONFIG)
    sig = arms_race_signatures(config, profile="conservative")
    assert sig["beta1_private_return_sd"] > 0.0
    assert sig["beta2_positional_externality_sd"] < 0.0
