"""Score → rank → seat privilege inequality story.

Replaces direct P(accessible seat) with latent NEET marks shifted by medium / metro /
coaching, national capacity cutoffs, and an affordability filter. Arms-race scenarios
subtract population-mean coaching shifts so equal escalation leaves ranks unchanged.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .career import CareerPathModel, earnings_quantiles, histogram_shares, simulate_one_year
from .evidence import PROCESSED
from .privilege import PrivilegeStratum, build_career_paths_for_privilege
from .score_engine import (
    apply_score_shifts,
    load_score_config,
    load_score_distribution,
    marks_to_percentile_rank,
)
from .seat_allocation import (
    allocate_offers,
    can_afford_private_fee,
    capacity_from_config,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "config" / "score_privilege_scenarios.yaml"


@dataclass(frozen=True)
class ScoreStratumResult:
    stratum_id: str
    label: str
    arms_race_scenario: str
    coaching_profile: str
    mean_marks: float
    median_marks: float
    p90_marks: float
    mean_rank_percentile: float
    p_government_offer: float
    p_private_offer: float
    p_any_mbbs_offer: float
    p_accessible_seat: float
    medium_shift_sd: float
    coaching_shift_sd: float
    relative_coaching_shift_sd: float
    total_location_shift_sd: float


def _mixture_weights(
    stratum: PrivilegeStratum,
    config: dict[str, Any],
    *,
    privilege_tier: str | None = None,
) -> dict[str, float]:
    weights_cfg = config["no_seat_mixture_weights"]
    tier = privilege_tier or "mid"
    if tier == "low":
        key = "low_privilege"
    elif tier == "high":
        key = "high_privilege"
    elif stratum.can_afford_private and stratum.school_medium == "english":
        key = "high_privilege"
    elif (not stratum.can_afford_private) and stratum.school_medium == "tamil":
        key = "low_privilege"
    else:
        key = "default"
    weights = {k: float(v) for k, v in weights_cfg[key].items()}
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


def simulate_score_stratum(
    stratum: PrivilegeStratum,
    config: dict[str, Any],
    careers: dict[str, CareerPathModel],
    *,
    arms_race: dict[str, Any],
    coaching_profile: str | None = None,
    privilege_tier: str | None = None,
    draws: int | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    sim = config["simulation"]
    n = int(sim["draws"] if draws is None else draws)
    rng = np.random.default_rng(int(sim["seed"] if seed is None else seed))
    dist = load_score_distribution(config=config, repo_root=REPO_ROOT)
    capacity = capacity_from_config(config)
    profile = coaching_profile or config["coaching"]["default_profile"]

    baseline = dist.sample(n, rng=rng)
    shifted, meta = apply_score_shifts(
        baseline,
        dist=dist,
        school_medium=stratum.school_medium,
        metro_proximity=stratum.metro_proximity,
        prep_intensity=stratum.prep_intensity,
        config=config,
        coaching_profile=profile,
        subtract_population_mean=bool(arms_race.get("subtract_population_mean_shift", True)),
        force_population_prep=arms_race.get("force_population_prep"),
    )
    rank_pct = marks_to_percentile_rank(shifted, dist)
    afford = can_afford_private_fee(stratum.can_afford_private, config)
    offers = allocate_offers(rank_pct, capacity=capacity, can_afford_private=afford)

    # Career draws
    path_annual: dict[str, np.ndarray] = {}
    path_employed: dict[str, np.ndarray] = {}
    for i, (path_name, model) in enumerate(careers.items(), start=1):
        annual, _summary, employed = simulate_one_year(model, draws=n, seed=int(sim["seed"]) + i)
        path_annual[path_name] = annual
        path_employed[path_name] = employed

    mix_w = _mixture_weights(stratum, config, privilege_tier=privilege_tier)
    mix_names = list(mix_w.keys())
    mix_probs = np.array([mix_w[k] for k in mix_names], dtype=float)
    no_seat_choice = rng.choice(mix_names, size=n, p=mix_probs)
    no_seat_annual = np.zeros(n, dtype=float)
    no_seat_employed = np.zeros(n, dtype=bool)
    for name in mix_names:
        m = no_seat_choice == name
        no_seat_annual[m] = path_annual[name][m]
        no_seat_employed[m] = path_employed[name][m]

    # Outcome path conditional on offer/access
    outcome = np.full(n, "no_seat", dtype=object)
    outcome[offers.government_offer] = "government_mbbs"
    outcome[offers.private_offer & offers.accessible_seat] = "private_mbbs"
    # private offer but unaffordable counts as no_seat for earnings path
    annual = no_seat_annual.copy()
    employed = no_seat_employed.copy()
    for path_name in ("government_mbbs", "private_mbbs"):
        m = outcome == path_name
        annual[m] = path_annual[path_name][m]
        employed[m] = path_employed[path_name][m]

    summary = ScoreStratumResult(
        stratum_id=stratum.id,
        label=stratum.label,
        arms_race_scenario=str(arms_race["id"]),
        coaching_profile=profile,
        mean_marks=float(np.mean(shifted)),
        median_marks=float(np.median(shifted)),
        p90_marks=float(np.quantile(shifted, 0.90)),
        mean_rank_percentile=float(np.mean(rank_pct)),
        p_government_offer=float(offers.government_offer.mean()),
        p_private_offer=float(offers.private_offer.mean()),
        p_any_mbbs_offer=float(offers.any_mbbs_offer.mean()),
        p_accessible_seat=float(offers.accessible_seat.mean()),
        medium_shift_sd=meta["medium_shift_sd"],
        coaching_shift_sd=meta["coaching_shift_sd"],
        relative_coaching_shift_sd=meta["relative_coaching_shift_sd"],
        total_location_shift_sd=meta["total_location_shift_sd"],
    )

    hist_edges = [float(x) for x in sim["annual_histogram_edges_inr"]]
    score_edges = [float(x) for x in sim["score_histogram_edges"]]
    hist_rows = []
    for row in histogram_shares(annual, edges=hist_edges):
        hist_rows.append(
            {
                "stratum_id": stratum.id,
                "label": stratum.label,
                "arms_race_scenario": arms_race["id"],
                "outcome": "realized",
                "metric": "annual",
                **row,
            }
        )
    score_hist = []
    for row in histogram_shares(shifted, edges=score_edges):
        score_hist.append(
            {
                "stratum_id": stratum.id,
                "label": stratum.label,
                "arms_race_scenario": arms_race["id"],
                **row,
            }
        )

    med_annual = path_annual["government_mbbs"]
    eng_annual = path_annual["engineering"]
    return {
        "summary": summary,
        "shifted_marks": shifted,
        "rank_percentile": rank_pct,
        "offers": offers,
        "realized_annual": annual,
        "realized_employed": employed,
        "histogram_rows": hist_rows,
        "score_histogram_rows": score_hist,
        "medicine_mean_if_employed": float(med_annual[path_employed["government_mbbs"]].mean())
        if path_employed["government_mbbs"].any()
        else float("nan"),
        "engineering_mean_if_employed": float(eng_annual[path_employed["engineering"]].mean())
        if path_employed["engineering"].any()
        else float("nan"),
        "medicine_median_if_employed": float(np.median(med_annual[path_employed["government_mbbs"]]))
        if path_employed["government_mbbs"].any()
        else float("nan"),
        "no_seat_median_if_employed": float(np.median(no_seat_annual[no_seat_employed]))
        if no_seat_employed.any()
        else float("nan"),
        "unconditional_annual_mean": float(annual.mean()),
        "unconditional_zero_share": float((annual <= 0).mean()),
        "mixture_weights": mix_w,
        "quantiles_realized": earnings_quantiles(annual),
        "quantiles_medicine": earnings_quantiles(med_annual),
    }


def run_score_privilege_pipeline(
    *,
    config_path: Path | None = None,
    processed: Path | None = None,
    output_dir: Path | None = None,
    draws: int | None = None,
    coaching_profile: str | None = None,
    arms_race_ids: list[str] | None = None,
) -> dict[str, Path]:
    config = load_score_config(config_path or DEFAULT_CONFIG)
    processed_root = PROCESSED if processed is None else processed
    out = (processed_root / "bayesian") if output_dir is None else output_dir
    out.mkdir(parents=True, exist_ok=True)

    careers = build_career_paths_for_privilege(processed=processed_root)
    profile = coaching_profile or config["coaching"]["default_profile"]
    scenarios = config["arms_race_scenarios"]
    if arms_race_ids is not None:
        scenarios = [s for s in scenarios if s["id"] in set(arms_race_ids)]

    access_rows: list[dict[str, Any]] = []
    hist_rows: list[dict[str, Any]] = []
    score_hist_rows: list[dict[str, Any]] = []
    ladder_by_scenario: dict[str, list[dict[str, Any]]] = {}

    for arms in scenarios:
        ladder_by_scenario[arms["id"]] = []
        for i, row in enumerate(config["access_ladder"]):
            stratum = PrivilegeStratum(
                id=str(row["id"]),
                label=str(row["label"]),
                school_medium=str(row["school_medium"]),
                can_afford_private=bool(row["can_afford_private"]),
                metro_proximity=str(row["metro_proximity"]),
                prep_intensity=str(row["prep_intensity"]),
            )
            result = simulate_score_stratum(
                stratum,
                config,
                careers,
                arms_race=arms,
                coaching_profile=profile,
                privilege_tier=str(row.get("privilege_tier", "mid")),
                draws=draws,
                seed=int(config["simulation"]["seed"]) + 1000 * i,
            )
            summary = result["summary"]
            access_rows.append(asdict(summary))
            hist_rows.extend(result["histogram_rows"])
            score_hist_rows.extend(result["score_histogram_rows"])
            ladder_by_scenario[arms["id"]].append(
                {
                    **asdict(summary),
                    "unconditional_annual_mean": result["unconditional_annual_mean"],
                    "unconditional_zero_share": result["unconditional_zero_share"],
                    "medicine_median_if_employed": result["medicine_median_if_employed"],
                    "no_seat_median_if_employed": result["no_seat_median_if_employed"],
                    "mixture_weights": result["mixture_weights"],
                }
            )

    capacity = capacity_from_config(config)
    unilateral = ladder_by_scenario.get("unilateral", [])
    low = next((s for s in unilateral if s["stratum_id"] == "tamil_cant_afford_nonmetro_none"), None)
    high = unilateral[-1] if unilateral else None
    eng_cant = next(
        (s for s in unilateral if s["stratum_id"] == "english_cant_afford_nonmetro_modest"),
        None,
    )
    eng_can = next(
        (s for s in unilateral if s["stratum_id"] == "english_can_afford_nonmetro_modest"),
        None,
    )

    story = {
        "model_version": config.get("model_version"),
        "model_family": "score_rank_seat",
        "coaching_profile": profile,
        "narrative": config.get("narrative", {}),
        "capacity": {
            "government_like_seats": capacity.government_like_seats,
            "private_like_seats": capacity.private_like_seats,
            "n_appeared": capacity.n_appeared,
            "government_cutoff_percentile": capacity.government_cutoff_percentile,
            "any_mbbs_cutoff_percentile": capacity.private_or_better_cutoff_percentile,
        },
        "access_ladder_by_scenario": ladder_by_scenario,
        "decomposition_unilateral": {
            "p_accessible_low": None if low is None else low["p_accessible_seat"],
            "p_accessible_english_cant_afford": None
            if eng_cant is None
            else eng_cant["p_accessible_seat"],
            "p_accessible_english_can_afford": None if eng_can is None else eng_can["p_accessible_seat"],
            "p_accessible_top": None if high is None else high["p_accessible_seat"],
            "full_ladder_ratio_top_over_low": (
                None
                if low is None or high is None or low["p_accessible_seat"] <= 0
                else high["p_accessible_seat"] / low["p_accessible_seat"]
            ),
            "mean_marks_low": None if low is None else low["mean_marks"],
            "mean_marks_top": None if high is None else high["mean_marks"],
        },
        "arms_race_note": (
            "Relative coaching shifts subtract the population-mean coaching SD so that "
            "universal escalation does not improve ranks — the arms-race property."
        ),
        "warnings": [
            "National capacity cutoffs are accounting shares (seats/appeared), not state/category counselling pools.",
            "Medium score shifts are calibrated toward TN associations; not national causal English effects.",
            "Coaching SD shifts are priors / proxies (Dongre-style), not NEET LATEs.",
            "Centre-marks file has no SES/coaching/domicile; privilege enters via synthetic shifts.",
            "Causal language for scenario contrasts is prohibited.",
        ],
    }

    access_path = out / "score_access_by_stratum.csv"
    hist_path = out / "score_earnings_histograms.csv"
    score_hist_path = out / "score_marks_histograms.csv"
    story_path = out / "score_inequality_story.json"
    pd.DataFrame(access_rows).to_csv(access_path, index=False)
    pd.DataFrame(hist_rows).to_csv(hist_path, index=False)
    pd.DataFrame(score_hist_rows).to_csv(score_hist_path, index=False)
    story_path.write_text(json.dumps(story, indent=2), encoding="utf-8")

    return {
        "score_access_by_stratum": access_path,
        "score_earnings_histograms": hist_path,
        "score_marks_histograms": score_hist_path,
        "score_inequality_story": story_path,
    }


__all__ = [
    "ScoreStratumResult",
    "run_score_privilege_pipeline",
    "simulate_score_stratum",
]
