"""Cost-band scaffolds and TN admitted-composition extracts.

IMPORTANT: Trajectories here are **not** joined attempt×spend×access simulations.
Single-application synthetic-stratum access rates must not be presented as cumulative
admission probabilities after multiple sittings. Public HTML should not render the
trajectory cards until those models are actually joined.

What is safe to show from this module:
- Rajan Table 7.38 current-year / repeater admitted shares (administrative proportions);
- labeled cost *bands* with cited anchors, without attaching mismatched access probs.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .attempt_inference import (
    RAJAN_REPEATER_SHARE_AMONG_ADMITTED,
    applicant_repeater_share,
)
from .attempt_priors import (
    calibrate_continuation_to_admitted_repeater_share,
    load_attempt_config,
    mean_sittings,
    sitting_distribution,
)
from .baseline import AttemptCost, repeat_year_cost
from .evidence import PROCESSED

REPO = Path(__file__).resolve().parents[2]

# NTA general category exam fee order-of-magnitude (INR); not the dominant cost.
NEET_EXAM_FEE_INR = 1_700.0

# Rajan Committee coaching anchors (INR).
RAJAN_REPEATER_COACHING_EXCLUSIVE_INR = 1_000_000.0  # "Rs.10 Lakhs exclusively for coaching"
RAJAN_AVG_COACHING_COST_INR = 95_033.0  # committee-derived average across packages
# Midpoint of reported long-term package band (~2.5–4.5L).
RAJAN_LONG_TERM_MID_INR = 350_000.0
RAJAN_LONG_TERM_HIGH_INR = 450_000.0
RAJAN_LONG_TERM_LOW_INR = 250_000.0
RAJAN_SHORT_TERM_MID_INR = 90_000.0  # mid short-term / one-year band

# Score-model spend multiples (config/score_privilege_scenarios.yaml) — for documentation only.
SCORE_MODEL_MEDIAN_POSITIVE_SPEND_INR = 9_900.0  # CMSE Class X–XII coached p50
SCORE_MODEL_MODEST_SPEND_INR = SCORE_MODEL_MEDIAN_POSITIVE_SPEND_INR  # 1× median
SCORE_MODEL_INTENSIVE_SPEND_INR = 8.0 * SCORE_MODEL_MEDIAN_POSITIVE_SPEND_INR  # ~₹79,200

# PLFS 2025 processed anchor: no_college monthly median (youth opp-cost proxy).
PLFS_NO_COLLEGE_MONTHLY_MEDIAN_INR = 12_000.0

# Public story must not attach these trajectories until attempt×spend×access are joined.
PUBLIC_STORY_TRAJECTORIES_ENABLED = False


@dataclass(frozen=True)
class CostBand:
    low: float
    mid: float
    high: float

    def as_dict(self) -> dict[str, float]:
        return {"low": self.low, "mid": self.mid, "high": self.high}


@dataclass(frozen=True)
class TicketTrajectory:
    id: str
    label: str
    years_out_of_school: int
    n_sittings_so_far: int
    stratum_id: str
    stratum_label: str
    p_accessible_seat: float
    p_accessible_is_single_application_stratum: bool
    arms_race_scenario: str
    cash_coaching_inr: CostBand
    cash_exam_travel_materials_inr: CostBand
    cash_lodging_relocation_inr: CostBand
    opportunity_cost_inr: CostBand
    total_family_economic_cost_inr: CostBand
    score_model_spend_anchor_inr: float | None
    psych_burden: str
    delayed_life_note: str
    punch_line: str
    sources: list[str]
    caveats: list[str]
    public_story_ok: bool

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["cash_coaching_inr"] = self.cash_coaching_inr.as_dict()
        d["cash_exam_travel_materials_inr"] = self.cash_exam_travel_materials_inr.as_dict()
        d["cash_lodging_relocation_inr"] = self.cash_lodging_relocation_inr.as_dict()
        d["opportunity_cost_inr"] = self.opportunity_cost_inr.as_dict()
        d["total_family_economic_cost_inr"] = self.total_family_economic_cost_inr.as_dict()
        return d


def _band_sum(*bands: CostBand) -> CostBand:
    return CostBand(
        low=sum(b.low for b in bands),
        mid=sum(b.mid for b in bands),
        high=sum(b.high for b in bands),
    )


def _load_cmse_class_xii(processed: Path | None = None) -> dict[str, float]:
    root = PROCESSED if processed is None else processed
    path = root / "mospi" / "cmse_coaching_priors.csv"
    df = pd.read_csv(path)
    row = df.loc[(df["sector_label"] == "all") & (df["enrolment_band"] == "class_xii")].iloc[0]
    return {
        "p50": float(row["coaching_exp_p50"]),
        "p90": float(row["coaching_exp_p90"]),
        "p25": float(row["coaching_exp_p25"]),
    }


def _load_accessible_rates(processed: Path | None = None) -> dict[str, float]:
    root = PROCESSED if processed is None else processed
    path = root / "bayesian" / "score_inequality_story.json"
    story = json.loads(path.read_text(encoding="utf-8"))
    rows = story.get("unilateral")
    if rows is None:
        rows = (story.get("access_ladder_by_scenario") or {}).get("unilateral", [])
    out: dict[str, float] = {}
    for row in rows:
        out[str(row["stratum_id"])] = float(row["p_accessible_seat"])
    if not out:
        raise KeyError(f"no unilateral accessible-seat rates in {path}")
    return out


def build_trajectories(processed: Path | None = None) -> list[TicketTrajectory]:
    """Research scaffolds only — not public-story quantitative trajectories.

    Access rates are single-application synthetic strata. Cost bands use separate
    Rajan / CMSE / PLFS anchors and are not the spend multiples used in the score model.
    """

    cmse = _load_cmse_class_xii(processed)
    access = _load_accessible_rates(processed)
    annual_opp = PLFS_NO_COLLEGE_MONTHLY_MEDIAN_INR * 12.0

    fresh_access = access["tamil_cant_afford_nonmetro_none"]
    modest_access = access["tamil_cant_afford_nonmetro_modest"]
    top_access = access["english_can_afford_metro_intensive"]

    # No-prep stratum: coaching cash must be zero (CMSE tutoring spend is for coached students).
    fresh_coaching = CostBand(low=0.0, mid=0.0, high=0.0)
    fresh_exam = CostBand(
        low=NEET_EXAM_FEE_INR,
        mid=NEET_EXAM_FEE_INR + 3_000.0,
        high=NEET_EXAM_FEE_INR + 8_000.0,
    )
    fresh_lodge = CostBand(low=0.0, mid=0.0, high=0.0)
    fresh_opp = CostBand(low=0.0, mid=0.0, high=0.0)
    fresh_total = _band_sum(fresh_coaching, fresh_exam, fresh_lodge, fresh_opp)

    # Two failed attempts + third sit: three exam fees in every band.
    drop_coaching = CostBand(
        low=2.0 * RAJAN_LONG_TERM_LOW_INR,
        mid=2.0 * RAJAN_LONG_TERM_MID_INR,
        high=RAJAN_REPEATER_COACHING_EXCLUSIVE_INR,
    )
    drop_exam = CostBand(
        low=3.0 * NEET_EXAM_FEE_INR,
        mid=3.0 * NEET_EXAM_FEE_INR + 15_000.0,
        high=3.0 * NEET_EXAM_FEE_INR + 40_000.0,
    )
    drop_lodge = CostBand(
        low=0.0,
        mid=2.0 * 80_000.0,
        high=2.0 * 180_000.0,
    )
    drop_opp = CostBand(
        low=1.0 * annual_opp,
        mid=2.0 * annual_opp,
        high=2.0 * annual_opp * 1.25,
    )
    drop_total = _band_sum(drop_coaching, drop_exam, drop_lodge, drop_opp)

    aff_coaching = CostBand(
        low=2.0 * RAJAN_SHORT_TERM_MID_INR,
        mid=2.0 * RAJAN_LONG_TERM_HIGH_INR,
        high=RAJAN_REPEATER_COACHING_EXCLUSIVE_INR * 1.2,
    )
    aff_total = _band_sum(aff_coaching, drop_exam, drop_lodge, drop_opp)

    inr_lakh = lambda x: f"₹{x / 1e5:.1f}L"  # noqa: E731
    shared_access_caveat = (
        "p_accessible_seat is a single-application synthetic-stratum rate — "
        "NOT cumulative admission after multiple sittings, NOT conditional on prior failures."
    )
    spend_mismatch_caveat = (
        f"Cost bands use Rajan/CMSE/PLFS anchors. Score-model modest/intensive spend plugs are "
        f"≈₹{SCORE_MODEL_MODEST_SPEND_INR:,.0f} / ₹{SCORE_MODEL_INTENSIVE_SPEND_INR:,.0f} "
        f"(CMSE median multiples) — not these Rajan package totals."
    )

    return [
        TicketTrajectory(
            id="fresh_xii_tamil_no_prep",
            label="First sit, right out of high school",
            years_out_of_school=0,
            n_sittings_so_far=1,
            stratum_id="tamil_cant_afford_nonmetro_none",
            stratum_label="Tamil · cannot afford private · non-metro · no paid prep",
            p_accessible_seat=fresh_access,
            p_accessible_is_single_application_stratum=True,
            arms_race_scenario="unilateral",
            cash_coaching_inr=fresh_coaching,
            cash_exam_travel_materials_inr=fresh_exam,
            cash_lodging_relocation_inr=fresh_lodge,
            opportunity_cost_inr=fresh_opp,
            total_family_economic_cost_inr=fresh_total,
            score_model_spend_anchor_inr=0.0,
            psych_burden=(
                "One high-stakes exam year while finishing Class XII — acute stress, "
                "but not yet multi-year identity foreclosure around the exam."
            ),
            delayed_life_note="Life start not yet delayed beyond a normal school-leaving year.",
            punch_line=(
                f"Research scaffold only: exam/materials mid ≈ {inr_lakh(fresh_total.mid)}; "
                f"single-application stratum access ≈ {100.0 * fresh_access:.1f}% "
                f"(not a multi-year trajectory probability)."
            ),
            sources=[
                "score_inequality_story.json unilateral tamil_cant_afford_nonmetro_none",
                "NTA exam fee order-of-magnitude",
            ],
            caveats=[
                shared_access_caveat,
                "No-prep coaching cash forced to ₹0 (do not attach CMSE coached-spend bands).",
                "Not for public HTML until attempt×spend×access are joined.",
            ],
            public_story_ok=False,
        ),
        TicketTrajectory(
            id="two_year_dropper_tamil_modest",
            label="Two drop years, still cannot afford private",
            years_out_of_school=2,
            n_sittings_so_far=3,
            stratum_id="tamil_cant_afford_nonmetro_modest",
            stratum_label="Tamil · cannot afford private · non-metro · modest prep",
            p_accessible_seat=modest_access,
            p_accessible_is_single_application_stratum=True,
            arms_race_scenario="unilateral",
            cash_coaching_inr=drop_coaching,
            cash_exam_travel_materials_inr=drop_exam,
            cash_lodging_relocation_inr=drop_lodge,
            opportunity_cost_inr=drop_opp,
            total_family_economic_cost_inr=drop_total,
            score_model_spend_anchor_inr=SCORE_MODEL_MODEST_SPEND_INR,
            psych_burden=(
                "Two years of full-time prep identity: higher distress among repeat aspirants "
                "is documented in convenience samples. Not an individual clinical risk score."
            ),
            delayed_life_note=(
                "Two years of delayed college/work entry; peers may already be earning or enrolled."
            ),
            punch_line=(
                f"Research scaffold only: multi-year cost mid ≈ {inr_lakh(drop_total.mid)}; "
                f"attached access {100.0 * modest_access:.1f}% is the modest-stratum "
                f"single-application rate — not P(seat | two failed attempts)."
            ),
            sources=[
                "score_inequality_story.json unilateral tamil_cant_afford_nonmetro_modest",
                "Rajan Committee coaching fee bands / ₹10L exclusive repeater coaching",
                "PLFS 2025 no_college monthly median opportunity-cost proxy",
            ],
            caveats=[
                shared_access_caveat,
                spend_mismatch_caveat,
                "Rajan ₹10L is a TN narrative high for exclusive coaching — not a national mean.",
                "Not for public HTML until attempt×spend×access are joined.",
            ],
            public_story_ok=False,
        ),
        TicketTrajectory(
            id="two_year_dropper_english_intensive_can_pay",
            label="Two drop years, English + intensive + can pay private",
            years_out_of_school=2,
            n_sittings_so_far=3,
            stratum_id="english_can_afford_metro_intensive",
            stratum_label="English · can afford private · metro · intensive prep",
            p_accessible_seat=top_access,
            p_accessible_is_single_application_stratum=True,
            arms_race_scenario="unilateral",
            cash_coaching_inr=aff_coaching,
            cash_exam_travel_materials_inr=drop_exam,
            cash_lodging_relocation_inr=drop_lodge,
            opportunity_cost_inr=drop_opp,
            total_family_economic_cost_inr=aff_total,
            score_model_spend_anchor_inr=SCORE_MODEL_INTENSIVE_SPEND_INR,
            psych_burden=(
                "Same calendar years and exam stress — with a family that can keep buying prep "
                "and cash a private offer if the rank allows."
            ),
            delayed_life_note="Same two-year delay; different ability to monetize a private allotment.",
            punch_line=(
                f"Research scaffold only: multi-year cost mid ≈ {inr_lakh(aff_total.mid)}; "
                f"attached access {100.0 * top_access:.1f}% is the top-stratum "
                f"single-application rate — not a cumulative repeater trajectory."
            ),
            sources=[
                "score_inequality_story.json unilateral english_can_afford_metro_intensive",
                "Rajan Committee coaching fee bands",
                "PLFS 2025 no_college monthly median opportunity-cost proxy",
            ],
            caveats=[
                shared_access_caveat,
                spend_mismatch_caveat,
                "Contrast is compositional / scenario, not a causal LATE of coaching.",
                "Not for public HTML until attempt×spend×access are joined.",
            ],
            public_story_ok=False,
        ),
    ]


def admitted_composition_story(processed: Path | None = None) -> dict[str, Any]:
    """TN current-year vs repeater shares — administrative proportions from Rajan."""

    root = PROCESSED if processed is None else processed
    candidates = [
        root / "bayesian" / "rajan_repeater_by_year.csv",
        root / "tamil_nadu" / "rajan_repeater_by_year.csv",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        raise FileNotFoundError(
            "rajan_repeater_by_year.csv missing; run make attempt-priors"
        )
    df = pd.read_csv(path)
    post = df.loc[df["neet_era"] == "post_neet"].copy()
    latest = df.loc[df["session"] == "2020-2021"].iloc[0]
    pre = df.loc[df["neet_era"] == "pre_neet"]
    rho = 1.75
    a = applicant_repeater_share(
        p_repeater_among_admitted=float(latest["repeater_share"]),
        relative_admit_prob=rho,
    )
    cont = calibrate_continuation_to_admitted_repeater_share(
        p_repeater_among_admitted=float(latest["repeater_share"]),
        relative_admit_prob=rho,
    )
    dist = sitting_distribution(cont)
    return {
        "grain": "admitted_tamil_nadu_mbbs",
        "proxy_for_birth_year": (
            "other_than_current_year_students ≈ not the Class XII cohort of that admission year; "
            "implies most winners were older than a typical first-sit school-leaver. "
            "National DOB / Class XII year tables are still missing (see RTI Template 1b)."
        ),
        "latest_session": str(latest["session"]),
        "p_first_among_admitted": float(latest["current_students_share"]),
        "p_repeater_among_admitted": float(latest["repeater_share"]),
        "pre_neet_mean_repeater_share": float(pre["repeater_share"].mean()),
        "post_neet_years": post.to_dict(orient="records"),
        "calibration_rho": rho,
        "implied_p_first_among_applicants": 1.0 - a,
        "implied_p_repeater_among_applicants": a,
        "anchored_continuation": cont,
        "scenario_mean_sittings_under_assumed_decay": mean_sittings(dist),
        "anchored_p_sit_1": float(dist["1"]),
        # Keep old key for artifact readers; value is scenario mean, not a calibrated fact.
        "calibrated_mean_sittings": mean_sittings(dist),
        "calibrated_continuation": cont,
        "calibrated_p_sit_1": float(dist["1"]),
        "calibration_note": (
            "Only P(K=1) is pinned via ρ to the admitted first/repeater split; "
            "later continuation rates use assumed decay_of_r1. Mean sittings is scenario-driven."
        ),
        "source": "Justice A.K. Rajan Committee Table 7.38",
        "rajan_repeater_share_constant": RAJAN_REPEATER_SHARE_AMONG_ADMITTED,
        "prefer_over_pooled_bayes": True,
    }


def attempt_cost_example_year() -> dict[str, float]:
    """One transparent AttemptCost + opportunity-cost year using baseline primitives."""

    mid = AttemptCost(
        exam_fee=NEET_EXAM_FEE_INR,
        travel=5_000.0,
        lodging=80_000.0,
        materials=10_000.0,
        coaching=RAJAN_LONG_TERM_MID_INR,
        relocation=20_000.0,
        extra_living=30_000.0,
    )
    return {
        "direct_total_inr": mid.total,
        "with_opp_cost_inr": repeat_year_cost(
            mid,
            delayed_earnings=PLFS_NO_COLLEGE_MONTHLY_MEDIAN_INR * 12.0,
        ),
        "burden_share_of_3lakh_hh": mid.burden_share(300_000.0),
    }


def write_ticket_cost_artifacts(
    out_dir: Path | None = None,
    processed: Path | None = None,
) -> dict[str, Path]:
    root = PROCESSED if processed is None else processed
    out = out_dir or (root / "bayesian")
    out.mkdir(parents=True, exist_ok=True)

    traj = build_trajectories(root)
    comp = admitted_composition_story(root)
    cfg = load_attempt_config()

    rows = []
    for t in traj:
        rows.append(
            {
                "trajectory_id": t.id,
                "label": t.label,
                "years_out_of_school": t.years_out_of_school,
                "n_sittings_so_far": t.n_sittings_so_far,
                "stratum_id": t.stratum_id,
                "p_accessible_seat": t.p_accessible_seat,
                "p_accessible_is_single_application_stratum": t.p_accessible_is_single_application_stratum,
                "public_story_ok": t.public_story_ok,
                "score_model_spend_anchor_inr": t.score_model_spend_anchor_inr,
                "cash_mid_inr": t.total_family_economic_cost_inr.mid
                - t.opportunity_cost_inr.mid,
                "opp_cost_mid_inr": t.opportunity_cost_inr.mid,
                "total_economic_mid_inr": t.total_family_economic_cost_inr.mid,
                "total_economic_high_inr": t.total_family_economic_cost_inr.high,
                "punch_line": t.punch_line,
            }
        )
    traj_csv = out / "ticket_cost_trajectories.csv"
    pd.DataFrame(rows).to_csv(traj_csv, index=False)

    summary = {
        "model_version": "0.3.0",
        "public_story_trajectories_enabled": PUBLIC_STORY_TRAJECTORIES_ENABLED,
        "admitted_composition": comp,
        "trajectories": [t.as_dict() for t in traj],
        "attempt_cost_year_example": attempt_cost_example_year(),
        "attempt_priors_model_version": cfg.get("model_version"),
        "score_model_spend_anchors_inr": {
            "modest": SCORE_MODEL_MODEST_SPEND_INR,
            "intensive": SCORE_MODEL_INTENSIVE_SPEND_INR,
            "note": "These are the plug-ins used in score→rank→seat, not Rajan package totals.",
        },
        "warnings": [
            "PUBLIC HTML: do not render trajectory cards — costs and access rates are not joined.",
            "p_accessible_seat values are single-application synthetic strata, not multi-sitting trajectories.",
            "Do not quote 0.01% unless a stratum model actually produces it.",
            "TN admitted current-year share (Rajan Table 7.38) is an administrative proportion — "
            "prefer it over pooled Beta posteriors that invent ESS and collapse years.",
            "Scenario mean sittings under assumed decay is not a calibrated attempt distribution.",
            "Costs are scenario bands with cited anchors, not causal treatment effects.",
        ],
    }
    json_path = out / "ticket_cost_summary.json"
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return {
        "ticket_cost_trajectories": traj_csv,
        "ticket_cost_summary": json_path,
    }
