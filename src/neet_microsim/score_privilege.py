"""Fixed-reference threshold privilege story (production pathway).

Synthetic strata receive latent NEET mark shifts (medium / metro / coaching), then are
evaluated against a **fixed** national marks CDF and capacity-equivalent threshold shares,
plus an affordability filter. This is not a joint applicant-pool ranking or a state
counselling allocator.

Arms-race scenarios subtract population-mean coaching shifts so equal escalation leaves
relative ranks unchanged. Shared baseline draws (common random numbers) keep
counterfactual comparisons CRN-stable.
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
    arms_race_signatures,
    coaching_components_sd,
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

# Ordered scenario pathway (not Shapley / Oaxaca / mediation). Increments depend on order.
ORDERED_PATHWAY_STEPS: list[dict[str, str]] = [
    {
        "stratum_id": "tamil_cant_afford_nonmetro_none",
        "step_id": "baseline",
        "channel": "baseline",
        "evidence_class": "scenario",
        "label": "Baseline · Tamil · cannot afford · non-metro · no prep",
    },
    {
        "stratum_id": "tamil_cant_afford_nonmetro_modest",
        "step_id": "modest_prep",
        "channel": "prep",
        "evidence_class": "transported_prior",
        "label": "+ Modest prep prior",
    },
    {
        "stratum_id": "english_cant_afford_nonmetro_modest",
        "step_id": "english_medium",
        "channel": "medium",
        "evidence_class": "transported_association",
        "label": "+ English-medium association (TN-calibrated)",
    },
    {
        "stratum_id": "english_can_afford_nonmetro_modest",
        "step_id": "afford_private",
        "channel": "affordability",
        "evidence_class": "scenario",
        "label": "+ Private-seat affordability",
    },
    {
        "stratum_id": "english_can_afford_metro_modest",
        "step_id": "metro",
        "channel": "metro",
        "evidence_class": "scenario",
        "label": "+ Metro sensitivity",
    },
    {
        "stratum_id": "english_can_afford_metro_intensive",
        "step_id": "intensive_prep",
        "channel": "prep",
        "evidence_class": "transported_prior",
        "label": "+ Intensive prep prior",
    },
]


@dataclass(frozen=True)
class ScoreStratumResult:
    stratum_id: str
    label: str
    arms_race_scenario: str
    coaching_profile: str
    labeled_prep_intensity: str
    effective_prep_intensity: str
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
    baseline_marks: np.ndarray | None = None,
) -> dict[str, Any]:
    """Simulate one synthetic stratum against the fixed national reference distribution.

    Pass ``baseline_marks`` (common random numbers) so counterfactual strata/scenarios
    that become mathematically identical after ``force_all_prep`` yield identical marks
    and access rates.
    """

    sim = config["simulation"]
    base_seed = int(sim["seed"] if seed is None else seed)
    dist = load_score_distribution(config=config, repo_root=REPO_ROOT)
    capacity = capacity_from_config(config)
    profile = coaching_profile or config["coaching"]["default_profile"]

    if baseline_marks is None:
        n = int(sim["draws"] if draws is None else draws)
        baseline = dist.sample(n, rng=np.random.default_rng(base_seed))
    else:
        baseline = np.asarray(baseline_marks, dtype=float)
        if baseline.ndim != 1:
            raise ValueError("baseline_marks must be a 1-d array")
        n = int(baseline.shape[0])
        if draws is not None and int(draws) != n:
            raise ValueError("draws does not match baseline_marks length")

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
        force_all_prep=arms_race.get("force_all_prep"),
    )
    rank_pct = marks_to_percentile_rank(shifted, dist)
    afford = can_afford_private_fee(stratum.can_afford_private, config)
    offers = allocate_offers(rank_pct, capacity=capacity, can_afford_private=afford)

    # Career draws use shared seeds (not stratum index) so they do not reintroduce
    # ladder-row Monte Carlo differences into access comparisons.
    path_annual: dict[str, np.ndarray] = {}
    path_employed: dict[str, np.ndarray] = {}
    for i, (path_name, model) in enumerate(careers.items(), start=1):
        annual, _summary, employed = simulate_one_year(
            model, draws=n, seed=int(sim["seed"]) + i
        )
        path_annual[path_name] = annual
        path_employed[path_name] = employed

    mix_w = _mixture_weights(stratum, config, privilege_tier=privilege_tier)
    mix_names = list(mix_w.keys())
    mix_probs = np.array([mix_w[k] for k in mix_names], dtype=float)
    # Deterministic mixture draws from stratum attributes only (not ladder row index).
    mix_seed = (
        int(sim["seed"])
        + 10_000 * (0 if stratum.school_medium == "tamil" else 1)
        + 1_000 * (0 if stratum.can_afford_private else 1)
        + 100 * (0 if stratum.metro_proximity == "non_metro" else 1)
        + 10 * {"none": 0, "modest": 1, "intensive": 2}.get(str(meta["effective_prep_intensity"]), 0)
    )
    mix_rng = np.random.default_rng(mix_seed)
    no_seat_choice = mix_rng.choice(mix_names, size=n, p=mix_probs)
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
        labeled_prep_intensity=stratum.prep_intensity,
        effective_prep_intensity=str(meta["effective_prep_intensity"]),
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

    # Common random numbers: one shared baseline marks vector for all strata/scenarios.
    sim = config["simulation"]
    n = int(sim["draws"] if draws is None else draws)
    shared_seed = int(sim["seed"])
    dist = load_score_distribution(config=config, repo_root=REPO_ROOT)
    shared_baseline = dist.sample(n, rng=np.random.default_rng(shared_seed))

    access_rows: list[dict[str, Any]] = []
    hist_rows: list[dict[str, Any]] = []
    score_hist_rows: list[dict[str, Any]] = []
    ladder_by_scenario: dict[str, list[dict[str, Any]]] = {}

    for arms in scenarios:
        ladder_by_scenario[arms["id"]] = []
        for row in config["access_ladder"]:
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
                baseline_marks=shared_baseline,
                seed=shared_seed,
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
    by_id = {s["stratum_id"]: s for s in unilateral}
    low = by_id.get("tamil_cant_afford_nonmetro_none")
    high = by_id.get("english_can_afford_metro_intensive") or (unilateral[-1] if unilateral else None)
    eng_cant = by_id.get("english_cant_afford_nonmetro_modest")
    eng_can = by_id.get("english_can_afford_nonmetro_modest")

    ordered_pathway = _build_ordered_pathway(by_id)

    coach_cfg = config["coaching"]
    plug_in_deltas = {
        intensity: coaching_components_sd(intensity, config, profile=profile)
        for intensity in coach_cfg["intensity_spend_multiples_of_median"]
    }
    signatures = arms_race_signatures(config, profile=profile)
    pop_mix = {str(k): float(v) for k, v in coach_cfg.get("population_mix_for_arms_race", {}).items()}

    gov_thr = capacity.government_capacity_threshold_percentile
    any_thr = capacity.any_mbbs_capacity_threshold_percentile
    story = {
        "model_version": config.get("model_version"),
        "model_family": config.get("model_family", "fixed_reference_threshold"),
        "model_description": (
            "Synthetic-stratum score shifts evaluated against a fixed national marks CDF "
            "and capacity-equivalent threshold shares. Not a joint applicant-pool ranking "
            "or state/category counselling allocator."
        ),
        "production_pathway": True,
        "common_random_numbers": True,
        "estimation": "plug_in_sensitivity",
        "coaching_profile": profile,
        "coaching_functional_form": coach_cfg.get("functional_form"),
        "coaching_plug_in_deltas_sd": plug_in_deltas,
        "population_coaching_mix_assumed": pop_mix,
        "population_coaching_mix_note": (
            "Assumed NEET-applicant prep mix for unilateral population-mean subtraction; "
            "not a measured applicant distribution."
        ),
        "arms_race_signatures": signatures,
        "narrative": config.get("narrative", {}),
        "capacity": {
            "government_like_seats": capacity.government_like_seats,
            "private_like_seats": capacity.private_like_seats,
            "n_appeared": capacity.n_appeared,
            "government_capacity_threshold_percentile": gov_thr,
            "any_mbbs_capacity_threshold_percentile": any_thr,
            # Backward-compatible aliases
            "government_cutoff_percentile": gov_thr,
            "any_mbbs_cutoff_percentile": any_thr,
        },
        "access_ladder_by_scenario": ladder_by_scenario,
        "ordered_scenario_pathway_unilateral": ordered_pathway,
        # Alias retained for older story builders
        "waterfall_unilateral": ordered_pathway,
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
            "full_ladder_note": (
                "Extreme all-channels-at-once scenario contrast, not a national inequality estimate, "
                "causal effect, or posterior result. Prefer ordered_scenario_pathway_unilateral."
            ),
            "mean_marks_low": None if low is None else low["mean_marks"],
            "mean_marks_top": None if high is None else high["mean_marks"],
        },
        "arms_race_note": (
            "Private return (β1>0): unilateral prep raises absolute scores. "
            "Positional externality (β2<0): relative coaching shifts subtract the population-mean "
            "coaching SD (from the assumed prep mix) so universal escalation (everyone_*) does not "
            "improve ranks while costs rise. rivals_escalate_* keeps the focal candidate's labeled "
            "prep while forcing rivals. Strategic response is documented externally, not estimated here."
        ),
        "warnings": [
            "Fixed-reference threshold model — not a joint ranked counselling simulation.",
            "National capacity-equivalent thresholds are accounting shares (seats/appeared), not state/category counselling cutoffs.",
            "Medium score shifts are calibrated toward TN associations; not national causal English effects.",
            "English-medium pathway step is partly circular with that TN calibration target.",
            "Coaching uses plug-in skeptical prior means (θ, β); access rates have no posterior intervals.",
            "Population coaching mix (arms race) is an assumed composition, not measured NEET applicants.",
            "Ordered scenario pathway increments depend on step order; not Shapley/Oaxaca/mediation.",
            "TN Rajan 99% coached admits / 71% repeaters are prevalence constraints, not score effects.",
            "Centre-marks file has no SES/coaching/domicile; privilege enters via synthetic shifts.",
            "Full ladder top/bottom ratio is an extreme scenario contrast.",
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


def _build_ordered_pathway(by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Ordered scenario pathway with evidence-class labels (order-dependent increments)."""

    rows: list[dict[str, Any]] = []
    baseline_p: float | None = None
    prev_p: float | None = None
    for step in ORDERED_PATHWAY_STEPS:
        stratum = by_id.get(step["stratum_id"])
        if stratum is None:
            continue
        p = float(stratum["p_accessible_seat"])
        if baseline_p is None:
            baseline_p = p
        delta = None if prev_p is None else p - prev_p
        ratio_vs_baseline = None if baseline_p is None or baseline_p <= 0 else p / baseline_p
        rows.append(
            {
                **step,
                "stratum_label": stratum["label"],
                "p_accessible_seat": p,
                "delta_p_accessible": delta,
                "ratio_vs_baseline": ratio_vs_baseline,
                "mean_marks": stratum["mean_marks"],
                "pathway_note": "Ordered scenario pathway; increments depend on step order.",
            }
        )
        prev_p = p
    return rows


# Backward-compatible alias
WATERFALL_STEPS = ORDERED_PATHWAY_STEPS


__all__ = [
    "ScoreStratumResult",
    "ORDERED_PATHWAY_STEPS",
    "WATERFALL_STEPS",
    "run_score_privilege_pipeline",
    "simulate_score_stratum",
]
