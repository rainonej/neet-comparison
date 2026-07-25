"""Tests for attempt continuation priors."""

from __future__ import annotations

import math

import pytest

from neet_microsim.attempt_priors import (
    load_attempt_config,
    mean_sittings,
    resource_runway,
    scenario_table,
    sitting_distribution,
    write_attempt_prior_artifacts,
)


def test_sitting_distribution_sums_to_one_and_central_mean() -> None:
    cfg = load_attempt_config()
    dist = sitting_distribution(cfg["scenarios"]["central"]["continuation"])
    assert sum(dist.values()) == pytest.approx(1.0)
    m = mean_sittings(dist)
    assert 1.6 < m < 1.85  # ~1.72 under central rates


def test_high_persistence_has_heavier_tail_than_low() -> None:
    cfg = load_attempt_config()
    low = sitting_distribution(cfg["scenarios"]["low_persistence"]["continuation"])
    high = sitting_distribution(cfg["scenarios"]["high_persistence"]["continuation"])
    assert mean_sittings(high) > mean_sittings(low)
    assert float(high["1"]) < float(low["1"])


def test_scenario_table_flags_not_national() -> None:
    table = scenario_table()
    assert set(table["scenario_id"]) >= {"low_persistence", "central", "high_persistence"}
    assert table["is_national_estimate"].eq(False).all()


def test_resource_runway_log_ratio() -> None:
    r = resource_runway(
        liquid=50_000,
        expected_disposable_1y=100_000,
        borrowing_capacity=50_000,
        repeat_year_burden=100_000,
        illiquid_wealth=1_000_000,
        illiquid_pledgeable_share=0.0,
    )
    assert r == pytest.approx(math.log(2.0))
    r_pledge = resource_runway(
        liquid=50_000,
        expected_disposable_1y=100_000,
        borrowing_capacity=50_000,
        repeat_year_burden=100_000,
        illiquid_wealth=1_000_000,
        illiquid_pledgeable_share=0.10,
    )
    assert r_pledge > r


def test_write_artifacts(tmp_path) -> None:
    paths = write_attempt_prior_artifacts(out_dir=tmp_path)
    assert paths["attempt_continuation_scenarios"].exists()
    assert paths["attempt_sitting_distributions"].exists()
