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
            "beat": "Privilege access ladder",
            "status": "SHOW†",
            "grain": "Synthetic strata + TN medium",
            "note": "~5× ladder; knobs labeled",
        },
        {
            "beat": "Coaching arms race",
            "status": "SENS",
            "grain": "Skeptical priors",
            "note": "β₁ / β₂ encoded; not NEET LATE",
        },
        {
            "beat": "Profession earnings",
            "status": "SHOW†",
            "grain": "PLFS-anchored Monte Carlo",
            "note": "Projection; zeros retained",
        },
        {
            "beat": "Attempt mean / histogram",
            "status": "BLOCK",
            "grain": "National",
            "note": "Only admitted repeater share + ρ sensitivity",
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
                "attempt_repeater_sensitivity.csv",
                "earnings_quantiles_by_outcome.csv",
                "cmse_coaching_priors.csv",
            ],
            "thesis": (
                "Medicine’s rewards are real. The rationing machine is cruel: "
                "a heavily taxing lottery that sells better odds to families who can afford the ticket, "
                "then launders the outcome as merit."
            ),
            "arms_race_blurb": (
                "Coaching is the entry fee of the lottery. Holding others fixed, prep can raise absolute scores. "
                "When the whole pool escalates, relative ranks barely move while money and years are still extracted."
            ),
            "warnings": score.get("warnings", []),
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
            "govt_cutoff_percentile": score["capacity"]["government_cutoff_percentile"],
            "any_cutoff_percentile": score["capacity"]["any_mbbs_cutoff_percentile"],
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
        "arms_race": {
            "signatures": score["arms_race_signatures"],
            "plug_in_deltas_sd": score["coaching_plug_in_deltas_sd"],
            "note": score.get("arms_race_note"),
        },
        "ladders": ladders,
        "marks_national": marks_hist,
        "marks_by_stratum": marks_by_stratum,
        "professions": professions,
        "attempts": attempts,
        "cmse_coaching": cmse,
        "privilege_affordability_ratio": privilege.get("affordability_only_access_ratio"),
        "readiness": readiness,
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
