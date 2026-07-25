"""Tests for ticket-cost scaffolds and TN sitting anchoring."""

from __future__ import annotations

import json

import pytest

from neet_microsim.attempt_inference import repeater_sensitivity_table
from neet_microsim.attempt_priors import (
    calibrate_continuation_to_admitted_repeater_share,
    inject_calibrated_scenarios,
    load_attempt_config,
    sitting_distribution,
    write_attempt_prior_artifacts,
)
from neet_microsim.ticket_cost import (
    PUBLIC_STORY_TRAJECTORIES_ENABLED,
    RAJAN_LONG_TERM_MID_INR,
    build_trajectories,
    write_ticket_cost_artifacts,
)


def test_tn_calibration_matches_implied_first_share() -> None:
    cont = calibrate_continuation_to_admitted_repeater_share(
        p_repeater_among_admitted=0.7142,
        relative_admit_prob=1.75,
    )
    dist = sitting_distribution(cont)
    # P(K=1) = 1 - r1 ≈ implied applicant first share under ρ
    assert float(dist["1"]) == pytest.approx(1.0 - cont["after_1"], abs=1e-6)
    assert 0.35 < float(dist["1"]) < 0.50


def test_calibrated_scenario_injected_and_honestly_labeled() -> None:
    cfg = inject_calibrated_scenarios(load_attempt_config())
    assert "tn_post_neet_calibrated" in cfg["scenarios"]
    sc = cfg["scenarios"]["tn_post_neet_calibrated"]
    assert sc["continuation"]["after_1"] > 0.5
    assert "assumed" in sc["label"].lower() or "decay" in sc["label"].lower()
    assert sc["calibration"]["identifies_full_attempt_count_distribution"] is False


def test_rho_sensitivity_includes_calibration_default() -> None:
    table = repeater_sensitivity_table()
    rhos = set(table["relative_admit_prob_repeater_over_first"].astype(float))
    assert 1.75 in rhos


def test_trajectories_are_scaffolds_not_public_story() -> None:
    assert PUBLIC_STORY_TRAJECTORIES_ENABLED is False
    traj = build_trajectories()
    by_id = {t.id: t for t in traj}
    fresh = by_id["fresh_xii_tamil_no_prep"]
    drop = by_id["two_year_dropper_tamil_modest"]
    aff = by_id["two_year_dropper_english_intensive_can_pay"]

    assert fresh.public_story_ok is False
    assert drop.public_story_ok is False
    assert aff.public_story_ok is False

    # No-prep must not attach paid coaching costs.
    assert fresh.cash_coaching_inr.mid == 0.0
    assert fresh.cash_coaching_inr.high == 0.0

    # Three sittings ⇒ three exam fees in every band.
    assert drop.cash_exam_travel_materials_inr.low == pytest.approx(3 * 1700.0)

    # Long-term package mid is midpoint of 2.5–4.5L.
    assert RAJAN_LONG_TERM_MID_INR == pytest.approx(350_000.0)

    assert fresh.p_accessible_is_single_application_stratum is True
    assert drop.p_accessible_seat > fresh.p_accessible_seat
    assert aff.p_accessible_seat > drop.p_accessible_seat
    assert drop.total_family_economic_cost_inr.mid > fresh.total_family_economic_cost_inr.mid


def test_write_artifacts_flag_public_off(tmp_path) -> None:
    paths = write_ticket_cost_artifacts(out_dir=tmp_path)
    summary = json.loads(paths["ticket_cost_summary"].read_text(encoding="utf-8"))
    assert summary["public_story_trajectories_enabled"] is False
    assert all(not t["public_story_ok"] for t in summary["trajectories"])
    assert "do not render trajectory cards" in " ".join(summary["warnings"]).lower()
    assert summary["admitted_composition"]["prefer_over_pooled_bayes"] is True
    bundled = write_attempt_prior_artifacts(out_dir=tmp_path / "bayes")
    text = bundled["attempt_continuation_scenarios"].read_text(encoding="utf-8")
    assert "tn_post_neet_calibrated" in text
