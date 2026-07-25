"""Freeze model artifacts into the interactive story payload + HTML data block."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAYES = ROOT / "data" / "processed" / "bayesian"
MOSPI = ROOT / "data" / "processed" / "mospi"
OUT_DIR = ROOT / "reports" / "interactive"
OUT_JSON = OUT_DIR / "story-payload.json"
OUT_JS = OUT_DIR / "story-data.js"
HTML_PATH = OUT_DIR / "the-accessible-seat.html"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _f(x: str | float | int | None) -> float | None:
    if x is None or x == "":
        return None
    return float(x)


MARKS_PER_CORRECT = 4  # NTA NEET-UG: +4 correct, −1 wrong, 0 blank; 180 Q → max 720


def _quantile_table() -> list[tuple[float, float]]:
    rows = _read_csv(ROOT / "data" / "processed" / "neet_2024_marks_quantiles.csv")
    return sorted((float(r["quantile"]), float(r["marks"])) for r in rows)


def _marks_at_cdf(table: list[tuple[float, float]], p: float) -> float:
    if p <= table[0][0]:
        return table[0][1]
    if p >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        p0, m0 = table[i]
        p1, m1 = table[i + 1]
        if p0 <= p <= p1:
            t = (p - p0) / ((p1 - p0) or 1e-12)
            return m0 + t * (m1 - m0)
    return table[-1][1]


def _cdf_at_marks(table: list[tuple[float, float]], m: float) -> float:
    if m <= table[0][1]:
        return table[0][0]
    if m >= table[-1][1]:
        return table[-1][0]
    for i in range(len(table) - 1):
        p0, m0 = table[i]
        p1, m1 = table[i + 1]
        if m0 <= m <= m1:
            t = (m - m0) / ((m1 - m0) or 1e-12)
            return p0 + t * (p1 - p0)
    return 1.0


def build_razor_margin(n_appeared: int, govt_seats: int, private_seats: int) -> dict:
    """Translate capacity-equivalent rank thresholds into marks / question equivalents."""
    table = _quantile_table()
    total_seats = govt_seats + private_seats
    gov_cdf = 1.0 - govt_seats / n_appeared
    any_cdf = 1.0 - total_seats / n_appeared
    gov_marks = _marks_at_cdf(table, gov_cdf)
    any_marks = _marks_at_cdf(table, any_cdf)
    median_marks = _marks_at_cdf(table, 0.5)

    bands = []
    for k in (1, 2, 5, 10):
        dm = MARKS_PER_CORRECT * k
        lo, hi = any_marks - dm, any_marks + dm
        share = _cdf_at_marks(table, hi) - _cdf_at_marks(table, lo)
        bands.append(
            {
                "questions": k,
                "marks_window": MARKS_PER_CORRECT * k * 2,
                "marks_lo": round(lo, 1),
                "marks_hi": round(hi, 1),
                "share": share,
                "n_candidates": int(round(share * n_appeared)),
            }
        )

    gov_thr_marks = round(gov_marks, 1)
    any_thr_marks = round(any_marks, 1)
    return {
        "marks_per_correct": MARKS_PER_CORRECT,
        "n_questions": 180,
        "max_marks": 720,
        "scoring_note": (
            "NTA NEET-UG: 180 questions, +4 correct / -1 wrong / 0 blank. "
            "One extra correct answer (holding others fixed) is +4 marks."
        ),
        "threshold_note": (
            "Capacity-equivalent national rank thresholds (seats÷appeared mapped through "
            "national marks quantiles). Not state/category counselling cutoffs."
        ),
        "government_capacity_threshold_marks": gov_thr_marks,
        "any_mbbs_capacity_threshold_marks": any_thr_marks,
        # Backward-compatible aliases for older story JS
        "government_cutoff_marks": gov_thr_marks,
        "any_mbbs_cutoff_marks": any_thr_marks,
        "national_median_marks": round(median_marks, 1),
        "questions_median_below_any_threshold": round(
            (any_marks - median_marks) / MARKS_PER_CORRECT, 1
        ),
        "questions_median_below_govt_threshold": round(
            (gov_marks - median_marks) / MARKS_PER_CORRECT, 1
        ),
        "questions_median_below_any_cutoff": round(
            (any_marks - median_marks) / MARKS_PER_CORRECT, 1
        ),
        "questions_median_below_govt_cutoff": round(
            (gov_marks - median_marks) / MARKS_PER_CORRECT, 1
        ),
        "near_threshold_bands": bands,
        "near_cutoff_bands": bands,
        "interpolation": "Linear between published national marks quantiles",
    }


def build_bibliography() -> list[dict[str, str]]:
    return [
        {
            "key": "PLFS25",
            "text": "MoSPI Periodic Labour Force Survey unit files (processed 2025 wage anchors): physician vs engineering / other occupation medians.",
        },
        {
            "key": "WB25",
            "text": "World Bank (2025), An Overview of the Indian Health Labor Markets — PLFS-based physician/engineer wages and sector job-quality gaps.",
        },
        {
            "key": "IER24",
            "text": "ILO / Institute for Human Development, India Employment Report 2024 — graduate youth unemployment; technical degree and regular employment.",
        },
        {
            "key": "AEJ24",
            "text": "Asher, Novosad, et al. (AEJ Applied, 2024), Intergenerational Mobility in India — education as a mobility channel.",
        },
        {
            "key": "Thomas10",
            "text": "Thomas (2010), Medicine, merit, money and caste — prestige, private purchase, and contested merit in Indian medical education.",
        },
        {
            "key": "NTA24",
            "text": "NTA NEET-UG 2024 re-revised result press release + scheme of examination (+4/−1/180Q).",
        },
        {
            "key": "NMC",
            "text": "National Medical Commission MBBS college/seat list snapshot used for capacity accounting.",
        },
        {
            "key": "hq969",
            "text": "Public anonymized NEET-2024 centre-marks reconstruction (~2.33M rows), reconciled to NTA appeared counts.",
        },
        {
            "key": "Rajan21",
            "text": "Justice A.K. Rajan Committee report (Tamil Nadu, 2021) — medium, coaching, and repeater composition among admitted students.",
        },
        {
            "key": "CMSE25",
            "text": "MoSPI Comprehensive Modular Survey on Education 2025 — coaching participation and spend among enrolled students.",
        },
    ]


def build_payload() -> dict:
    score = json.loads((BAYES / "score_inequality_story.json").read_text(encoding="utf-8"))
    privilege = json.loads((BAYES / "inequality_story.json").read_text(encoding="utf-8"))
    bayes = json.loads((BAYES / "bayesian_results.json").read_text(encoding="utf-8"))

    marks_hist = [
        {
            "band": r["score_band"],
            "candidates": int(float(r["candidates"])),
            "share": float(r["share"]),
        }
        for r in _read_csv(ROOT / "data" / "processed" / "neet_2024_marks_histogram.csv")
    ]

    attempts = [
        {
            "rho": float(r["relative_admit_prob_repeater_over_first"]),
            "p_repeater_applicants": float(r["p_repeater_among_applicants"]),
            "p_first_applicants": float(r["p_first_attempt_among_applicants"]),
            "r_admitted": float(r["p_repeater_among_admitted"]),
        }
        for r in _read_csv(BAYES / "attempt_repeater_sensitivity.csv")
    ]

    # Ensure continuation prior + ticket-cost artifacts exist, then load
    from neet_microsim.attempt_priors import write_attempt_prior_artifacts

    write_attempt_prior_artifacts(out_dir=BAYES)
    attempt_scenarios = [
        {
            "id": r["scenario_id"],
            "label": r["label"],
            "r1": float(r["r_after_1"]),
            "r2": float(r["r_after_2"]),
            "r3": float(r["r_after_3"]),
            "r4p": float(r["r_after_4_plus"]),
            "mean_sittings": float(r["mean_sittings"]),
            "p1": float(r["p_sit_1"]),
            "p2": float(r["p_sit_2"]),
            "p3": float(r["p_sit_3"]),
            "p4": float(r["p_sit_4"]),
            "p5p": float(r["p_sit_5_plus"]),
            "calibrated": str(r.get("is_calibrated_to_admitted_composition", "")).lower()
            in {"true", "1"},
        }
        for r in _read_csv(BAYES / "attempt_continuation_scenarios.csv")
    ]

    ticket = json.loads((BAYES / "ticket_cost_summary.json").read_text(encoding="utf-8"))
    admitted_comp = ticket.get("admitted_composition", {})
    # Trajectory cards are research scaffolds only — never ship mismatched cost×access pairs.
    public_traj_ok = bool(ticket.get("public_story_trajectories_enabled", False))
    ticket_trajectories = ticket.get("trajectories", []) if public_traj_ok else []

    # Profession medians from privilege Monte Carlo (employed), first stratum as shared priors
    eq = _read_csv(BAYES / "earnings_quantiles_by_outcome.csv")
    profession_order = [
        ("government_mbbs", "Medicine"),
        ("engineering", "Engineering"),
        ("law", "Law (proxy)"),
        ("non_professional_graduate", "Non-professional grad"),
        ("no_college", "No college"),
    ]
    base = [r for r in eq if r["stratum_id"] == "tamil_cant_afford_nonmetro_none"]
    professions = []
    for outcome, label in profession_order:
        row = next(
            (
                r
                for r in base
                if r["outcome"] == outcome and r["metric"] == "annual_if_employed"
            ),
            None,
        )
        zrow = next(
            (r for r in base if r["outcome"] == outcome and r["metric"] == "annual"),
            None,
        )
        if not row:
            continue
        professions.append(
            {
                "id": outcome,
                "label": label,
                "median_lakh": round(float(row["p50"]) / 1e5, 2),
                "p25_lakh": round(float(row["p25"]) / 1e5, 2),
                "p75_lakh": round(float(row["p75"]) / 1e5, 2),
                "zero_share": _f(zrow["zero_share"]) if zrow else None,
                "employment_rate": _f(row["employment_rate"]),
            }
        )

    cmse = [
        {
            "sector": r["sector_label"],
            "band": r["enrolment_band"],
            "coaching_rate": float(r["coaching_rate_weighted"]),
            "spend_p50": float(r["coaching_exp_p50"]),
            "spend_p90": float(r["coaching_exp_p90"]),
        }
        for r in _read_csv(MOSPI / "cmse_coaching_priors.csv")
        if r["enrolment_band"] in {"class_x_xii", "class_xii"}
    ]

    # Compact ladder for all arms-race scenarios
    ladders = {}
    for scenario, rows in score["access_ladder_by_scenario"].items():
        ladders[scenario] = [
            {
                "id": r["stratum_id"],
                "label": r["label"],
                "p_accessible": r["p_accessible_seat"],
                "p_govt": r["p_government_offer"],
                "p_private": r["p_private_offer"],
                "mean_marks": r["mean_marks"],
                "median_marks": r["median_marks"],
                "labeled_prep_intensity": r.get("labeled_prep_intensity"),
                "effective_prep_intensity": r.get("effective_prep_intensity"),
                "coaching_shift_sd": r["coaching_shift_sd"],
                "relative_coaching_shift_sd": r["relative_coaching_shift_sd"],
                "total_location_shift_sd": r["total_location_shift_sd"],
                "unconditional_annual_mean": r["unconditional_annual_mean"],
                "medicine_median_if_employed": r["medicine_median_if_employed"],
                "no_seat_median_if_employed": r["no_seat_median_if_employed"],
            }
            for r in rows
        ]

    # Marks histograms for low vs top strata (unilateral)
    marks_by_stratum = {}
    for r in _read_csv(BAYES / "score_marks_histograms.csv"):
        if r["arms_race_scenario"] != "unilateral":
            continue
        sid = r["stratum_id"]
        marks_by_stratum.setdefault(sid, {"label": r["label"], "bins": []})
        marks_by_stratum[sid]["bins"].append(
            {
                "left": float(r["bin_left"]),
                "right": float(r["bin_right"]),
                "share": float(r["share"]),
            }
        )

    readiness = [
        {
            "beat": "National scarcity",
            "status": "SHOW",
            "grain": "NEET 2024 national",
            "note": "Appeared, seats, qualify rate pinned by counts",
        },
        {
            "beat": "Accessible seat framing",
            "status": "SHOW",
            "grain": "Model identity",
            "note": "Affordability filter; qualify ≠ seat",
        },
        {
            "beat": "Ordered scenario pathway",
            "status": "SENS",
            "grain": "Synthetic strata + TN medium",
            "note": "Order-dependent increments; not Shapley/Oaxaca; extreme top/bottom is not a national estimate",
        },
        {
            "beat": "Coaching arms race",
            "status": "SENS",
            "grain": "Skeptical plug-in priors + assumed 45/40/15 prep mix",
            "note": "everyone_* = universal prep; rivals_escalate_* = focal keeps label; not NEET LATE",
        },
        {
            "beat": "Profession earnings",
            "status": "SHOW†",
            "grain": "PLFS-anchored Monte Carlo",
            "note": "Projection; zeros retained",
        },
        {
            "beat": "National sitting histogram",
            "status": "BLOCK",
            "grain": "Need NTA tables",
            "note": "Show labeled low/central/high continuation scenarios instead",
        },
        {
            "beat": "TN admitted current-year / repeater composition",
            "status": "SHOW†",
            "grain": "Rajan Table 7.38 administrative proportions",
            "note": "Use year-specific shares (e.g. 28.6% in 2020–21); prefer over pooled Beta collapse",
        },
        {
            "beat": "Full attempt-count distribution",
            "status": "SENS",
            "grain": "TN first/repeater-anchored + assumed decay",
            "note": "Only P(K=1) pinned under ρ; later rates/mean sittings are assumption-driven",
        },
        {
            "beat": "Joined cost × multi-sitting access trajectories",
            "status": "BLOCK",
            "grain": "Need attempt×spend×access joint model",
            "note": "Cost bands and single-application stratum rates are not joined — cards withheld",
        },
        {
            "beat": "National admitted birth years",
            "status": "BLOCK",
            "grain": "Need NTA/NMC DOB or Class XII year",
            "note": "TN current-year admit share is the best age/attempt proxy in hand",
        },
        {
            "beat": "Wage gaps by identity",
            "status": "BLOCK",
            "grain": "Joint microdata",
            "note": "Privilege enters on access, not invented wage curves",
        },
    ]

    return {
        "meta": {
            "title": "The Accessible Seat",
            "subtitle": "Privilege, scarcity, and the coaching arms race in NEET-UG",
            "model_version_score": score.get("model_version"),
            "model_version_privilege": privilege.get("model_version"),
            "coaching_profile": score.get("coaching_profile"),
            "generated_from": [
                "score_inequality_story.json",
                "inequality_story.json",
                "bayesian_results.json",
                "neet_2024_marks_histogram.csv",
                "neet_2024_marks_quantiles.csv",
                "attempt_repeater_sensitivity.csv",
                "attempt_continuation_scenarios.csv",
                "ticket_cost_summary.json",
                "rajan_repeater_by_year.csv",
                "earnings_quantiles_by_outcome.csv",
                "cmse_coaching_priors.csv",
                "docs/STORY_BIBLIOGRAPHY.md",
            ],
            "thesis": (
                "Medicine’s rewards are real. Seats are scarce, preparation is costly, and private "
                "capacity is unequally affordable — so qualification is not access, and exam rank "
                "should not be read as a pure measure of individual merit."
            ),
            "arms_race_blurb": (
                "Coaching can be the entry fee of a rank tournament. Holding others fixed, prep can "
                "raise absolute scores. When the whole pool escalates equally, relative ranks barely "
                "move while money and years are still extracted."
            ),
            "warnings": score.get("warnings", []),
            "production_pathway": score.get("model_family", "fixed_reference_threshold"),
            "model_description": score.get("model_description"),
            "estimation": score.get("estimation", "plug_in_sensitivity"),
            "legacy_privilege_demo": privilege.get("status") == "legacy_accounting_demo",
        },
        "scarcity": {
            "n_appeared": score["capacity"]["n_appeared"],
            "govt_seats": score["capacity"]["government_like_seats"],
            "private_seats": score["capacity"]["private_like_seats"],
            "total_mbbs_seats": score["capacity"]["government_like_seats"]
            + score["capacity"]["private_like_seats"],
            "appeared_per_seat": round(
                score["capacity"]["n_appeared"]
                / (
                    score["capacity"]["government_like_seats"]
                    + score["capacity"]["private_like_seats"]
                ),
                1,
            ),
            "govt_capacity_threshold_percentile": score["capacity"].get(
                "government_capacity_threshold_percentile",
                score["capacity"].get("government_cutoff_percentile"),
            ),
            "any_capacity_threshold_percentile": score["capacity"].get(
                "any_mbbs_capacity_threshold_percentile",
                score["capacity"].get("any_mbbs_cutoff_percentile"),
            ),
            "govt_cutoff_percentile": score["capacity"].get(
                "government_capacity_threshold_percentile",
                score["capacity"].get("government_cutoff_percentile"),
            ),
            "any_cutoff_percentile": score["capacity"].get(
                "any_mbbs_capacity_threshold_percentile",
                score["capacity"].get("any_mbbs_cutoff_percentile"),
            ),
            "qualify_rate": next(
                (
                    row["qualify_rate_mean"]
                    for row in bayes.get("comparison", [])
                    if row.get("profile") == bayes.get("default_profile", "conservative")
                ),
                0.564,
            ),
            "tn_english_to_tamil_ratio": next(
                (
                    row["tn_english_to_tamil_rate_ratio"]
                    for row in bayes.get("comparison", [])
                    if row.get("profile") == bayes.get("default_profile", "conservative")
                ),
                None,
            ),
            "appeared_per_seat_bayes": bayes.get("scarcity", {})
            .get(bayes.get("default_profile", "conservative"), {})
            .get("appeared_per_mbbs_seat"),
            "qualified_per_seat": bayes.get("scarcity", {})
            .get(bayes.get("default_profile", "conservative"), {})
            .get("qualified_per_mbbs_seat"),
        },
        "decomposition": score["decomposition_unilateral"],
        "ordered_scenario_pathway": score.get(
            "ordered_scenario_pathway_unilateral",
            score.get("waterfall_unilateral", []),
        ),
        "waterfall": score.get(
            "ordered_scenario_pathway_unilateral",
            score.get("waterfall_unilateral", []),
        ),
        "arms_race": {
            "signatures": score["arms_race_signatures"],
            "plug_in_deltas_sd": score["coaching_plug_in_deltas_sd"],
            "population_coaching_mix_assumed": score.get("population_coaching_mix_assumed"),
            "population_coaching_mix_note": score.get("population_coaching_mix_note"),
            "note": score.get("arms_race_note"),
        },
        "ladders": ladders,
        "marks_national": marks_hist,
        "marks_by_stratum": marks_by_stratum,
        "razor": build_razor_margin(
            score["capacity"]["n_appeared"],
            score["capacity"]["government_like_seats"],
            score["capacity"]["private_like_seats"],
        ),
        "professions": professions,
        "attempts": attempts,
        "attempt_scenarios": attempt_scenarios,
        "attempt_note": (
            "National sitting histogram is unidentified. "
            "The TN first/repeater-anchored scenario pins only P(K=1) under labeled ρ=1.75; "
            "later continuation rates use assumed decay — mean sittings is scenario-driven, "
            "not a calibrated attempt distribution. "
            "Success exit = acceptable seat joined, not mere qualify. "
            "See docs/ATTEMPT_PRIORS.md."
        ),
        "attempt_default_rho": 1.75,
        "tn_repeater_time_series": [
            {
                "session": str(y.get("session")),
                "repeater_share": float(y["repeater_share"]),
                "current_students_share": float(y["current_students_share"]),
            }
            for y in (admitted_comp.get("post_neet_years") or [])
            if y.get("repeater_share") is not None
        ],
        "ticket_cost": {
            "public_story_trajectories_enabled": public_traj_ok,
            "trajectories": ticket_trajectories,
            "admitted_composition": admitted_comp,
            "warnings": ticket.get("warnings", []),
            "blocked_reason": (
                None
                if public_traj_ok
                else (
                    "Trajectory cards withheld: cost bands are not the score-model spend plugs, "
                    "and access rates are single-application synthetic strata — not multi-sitting outcomes."
                )
            ),
        },
        "cmse_coaching": cmse,
        "privilege_affordability_ratio": privilege.get("affordability_only_access_ratio"),
        "readiness": readiness,
        "bibliography": build_bibliography(),
        "zero_earnings_note": privilege.get("zero_earnings_note"),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT_JS.write_text(
        "window.STORY_DATA = "
        + json.dumps(payload, ensure_ascii=False)
        + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_JS}")
    if HTML_PATH.exists():
        print(f"Open {HTML_PATH}")


if __name__ == "__main__":
    main()
