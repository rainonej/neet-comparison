"""Tests for ticket-cost trajectories and TN sitting calibration."""

from __future__ import annotations

import pytest

from neet_microsim.attempt_priors import (
    calibrate_continuation_to_admitted_repeater_share,
    inject_calibrated_scenarios,
    load_attempt_config,
    sitting_distribution,
    write_attempt_prior_artifacts,
)
from neet_microsim.ticket_cost import build_trajectories, write_ticket_cost_artifacts


def test_tn_calibration_matches_implied_first_share() -> None:
    cont = calibrate_continuation_to_admitted_repeater_share(
        p_repeater_among_admitted=0.7142,
        relative_admit_prob=1.75,
    )
    dist = sitting_distribution(cont)
    # P(K=1) = 1 - r1 ≈ implied applicant first share under ρ
    assert float(dist["1"]) == pytest.approx(1.0 - cont["after_1"], abs=1e-6)
    assert 0.35 < float(dist["1"]) < 0.50


def test_calibrated_scenario_injected() -> None:
    cfg = inject_calibrated_scenarios(load_attempt_config())
    assert "tn_post_neet_calibrated" in cfg["scenarios"]
    assert cfg["scenarios"]["tn_post_neet_calibrated"]["continuation"]["after_1"] > 0.5


def test_trajectories_honest_access_rates() -> None:
    traj = build_trajectories()
    by_id = {t.id: t for t in traj}
    fresh = by_id["fresh_xii_tamil_no_prep"]
    drop = by_id["two_year_dropper_tamil_modest"]
    aff = by_id["two_year_dropper_english_intensive_can_pay"]
    # Do not invent absurd 0.01% rates
    assert fresh.p_accessible_seat > 0.005
    assert fresh.p_accessible_seat < 0.03
    assert drop.p_accessible_seat > fresh.p_accessible_seat
    assert aff.p_accessible_seat > drop.p_accessible_seat
    assert drop.total_family_economic_cost_inr.mid > fresh.total_family_economic_cost_inr.mid
    assert drop.opportunity_cost_inr.mid > 0


def test_write_artifacts(tmp_path) -> None:
    paths = write_ticket_cost_artifacts(out_dir=tmp_path)
    assert paths["ticket_cost_summary"].exists()
    assert paths["ticket_cost_trajectories"].exists()
    bundled = write_attempt_prior_artifacts(out_dir=tmp_path / "bayes")
    assert "tn_post_neet_calibrated" in bundled["attempt_continuation_scenarios"].read_text(
        encoding="utf-8"
    )
