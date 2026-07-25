"""Privilege-stratified access and annual earnings and access scenarios.

This module tells a descriptive inequality story under explicit assumptions:

1. Starting privilege (school medium, private-seat affordability, metro proximity, prep spend)
   changes the probability of an *accessible* MBBS seat.
2. Conditional on stratum, people who get a seat have much higher annual earnings (especially among the employed) than peers
   who miss and enter engineering / law / other-graduate paths.

Causal language is prohibited. Tamil Nadu medium rates are observed associations. The
affordability ~2x channel is a mechanical accounting identity when private offers match the
government rate and private seats are dropped for households that cannot pay.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from .attempt_inference import repeater_sensitivity_table
from .baseline import combine_independent_marginal_rates
from .bayes import beta_from_mean_ess
from .career import (
    CareerPathModel,
    LogNormalEarnings,
    earnings_quantiles,
    histogram_shares,
    kde_curve,
    simulate_one_year,
)
from .evidence import (
    PROCESSED,
    load_cmse_coaching_priors,
    load_plfs_extended_wage_anchors,
    load_wage_anchors,
)
from .model import fit_profile

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "config" / "privilege_scenarios.yaml"


@dataclass(frozen=True)
class PrivilegeStratum:
    id: str
    label: str
    school_medium: str
    can_afford_private: bool
    metro_proximity: str
    prep_intensity: str


@dataclass(frozen=True)
class AccessResult:
    stratum_id: str
    label: str
    p_government_offer: float
    p_private_offer: float
    p_accessible_seat: float
    p_accessible_if_could_afford: float
    affordability_access_ratio: float
    school_medium: str
    can_afford_private: bool
    metro_proximity: str
    prep_intensity: str
    observed_inputs: str
    sensitivity_inputs: str
    neutral_inputs: str
    assumptions: str


def load_privilege_config(path: Path | None = None) -> dict[str, Any]:
    config_path = DEFAULT_CONFIG if path is None else path
    with config_path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _clip_prob(value: float) -> float:
    return float(min(max(value, 1e-6), 1.0 - 1e-6))


def _apply_odds_multiplier(probability: float, multiplier: float) -> float:
    if multiplier <= 0:
        raise ValueError("multiplier must be positive")
    if abs(multiplier - 1.0) < 1e-12:
        return _clip_prob(probability)
    odds = probability / (1.0 - probability)
    return _clip_prob(odds * multiplier / (1.0 + odds * multiplier))


def stratum_from_ladder_row(row: dict[str, Any]) -> PrivilegeStratum:
    return PrivilegeStratum(
        id=str(row["id"]),
        label=str(row["label"]),
        school_medium=str(row["school_medium"]),
        can_afford_private=bool(row["can_afford_private"]),
        metro_proximity=str(row["metro_proximity"]),
        prep_intensity=str(row["prep_intensity"]),
    )


def government_offer_rate(stratum: PrivilegeStratum, config: dict[str, Any]) -> float:
    medium = config["tamil_nadu_medium"]
    if stratum.school_medium == "english":
        return float(medium["english_government_rate"])
    if stratum.school_medium == "tamil":
        return float(medium["tamil_government_rate"])
    raise ValueError(f"unknown school_medium {stratum.school_medium!r}")


def private_offer_rate(stratum: PrivilegeStratum, config: dict[str, Any]) -> float:
    mode = config["private_offer"]["mode"]
    gov = government_offer_rate(stratum, config)
    if mode == "match_government_rate":
        return gov
    raise ValueError(f"unsupported private_offer.mode {mode!r}")


def can_household_afford_private(stratum: PrivilegeStratum, config: dict[str, Any]) -> bool:
    fees = config["fees_inr_per_year"]
    tiers = config["household_resource_tiers_inr_per_year"]
    private_fee = float(fees["private_mbbs"])
    resources = (
        float(tiers["can_afford_private"])
        if stratum.can_afford_private
        else float(tiers["cannot_afford_private"])
    )
    return private_fee <= 0.5 * resources


def access_probabilities(
    stratum: PrivilegeStratum,
    config: dict[str, Any],
    *,
    admission_profile: str | None = None,
) -> AccessResult:
    """Compute offer and accessible-seat probabilities for one stratum."""

    profile_name = admission_profile or config["default_admission_profile"]
    profile = config["admission_profiles"][profile_name]
    apply_prep = bool(profile["apply_prep_admission_multipliers"])

    p_gov = government_offer_rate(stratum, config)
    p_priv = private_offer_rate(stratum, config)

    metro_cfg = config["metro_sensitivity"]
    metro_mult = float(
        metro_cfg["metro_offer_multiplier"]
        if stratum.metro_proximity == "metro"
        else metro_cfg["non_metro_offer_multiplier"]
    )
    prep_cfg = config["prep_intensity"][stratum.prep_intensity]
    prep_mult = float(prep_cfg["offer_odds_multiplier"]) if apply_prep else 1.0

    # Apply metro and (optional) prep as odds multipliers to both channels.
    combined_mult = metro_mult * prep_mult
    p_gov = _apply_odds_multiplier(p_gov, combined_mult)
    p_priv = _apply_odds_multiplier(p_priv, combined_mult)

    afford = can_household_afford_private(stratum, config)
    # Accessible = govt offer OR (private offer AND can afford). Approximate as
    # 1 - (1-p_gov)*(1-p_priv_effective) under conditional independence of channels.
    p_priv_effective = p_priv if afford else 0.0
    p_accessible = 1.0 - (1.0 - p_gov) * (1.0 - p_priv_effective)
    p_if_afford = 1.0 - (1.0 - p_gov) * (1.0 - p_priv)
    ratio = p_if_afford / p_gov if p_gov > 0 else float("inf")

    observed = (
        f"TN {stratum.school_medium}-medium govt rate from Rajan Table 7.18 post-NEET aggregate"
    )
    sensitivity = []
    if metro_mult != 1.0:
        sensitivity.append(f"metro_offer_multiplier={metro_mult}")
    if apply_prep and prep_mult != 1.0:
        sensitivity.append(f"prep_offer_odds_multiplier={prep_mult}")
    if not sensitivity:
        sensitivity.append("none_active_in_this_profile")
    neutral = []
    if not apply_prep:
        neutral.append("prep_admission_effect=1.0 (cost only)")
    if metro_mult == 1.0:
        neutral.append("metro multiplier inactive for non-metro")

    return AccessResult(
        stratum_id=stratum.id,
        label=stratum.label,
        p_government_offer=p_gov,
        p_private_offer=p_priv,
        p_accessible_seat=p_accessible,
        p_accessible_if_could_afford=p_if_afford,
        affordability_access_ratio=ratio,
        school_medium=stratum.school_medium,
        can_afford_private=afford,
        metro_proximity=stratum.metro_proximity,
        prep_intensity=stratum.prep_intensity,
        observed_inputs=observed,
        sensitivity_inputs="; ".join(sensitivity),
        neutral_inputs="; ".join(neutral) if neutral else "none",
        assumptions=(
            "private_offer mode=match_government_rate; "
            "accessible=1-(1-p_gov)*(1-p_priv*1{afford}); "
            "independent channels"
        ),
    )


def affordability_only_ratio(config: dict[str, Any]) -> float:
    """Mechanical can-afford / cannot-afford access ratio holding medium fixed.

    Uses English-medium government rate with metro/prep multipliers at 1.0.
    """

    medium = config["tamil_nadu_medium"]
    p_gov = float(medium["english_government_rate"])
    p_priv = p_gov  # match_government_rate
    p_cant = p_gov
    p_can = 1.0 - (1.0 - p_gov) * (1.0 - p_priv)
    return p_can / p_cant


def build_career_paths_for_privilege(
    *,
    processed: Path | None = None,
    bayes_profile: str = "conservative",
) -> dict[str, CareerPathModel]:
    """Career paths used by the privilege story.

    Important distinction:
    - ``government_mbbs`` / ``private_mbbs`` are *college seat types*. We do **not** have an
      identified causal earnings effect of private vs government medical college for the same
      student. Both use the same overall physician wage anchor. Fees differ; wages do not.
    - ``physician_public_sector`` / ``physician_private_sector`` are *post-graduation employment
      sector* anchors from World Bank (optional comparison), not college type.
    - Core medicine/engineering/nursing levels prefer MoSPI PLFS 2025 medians when
      ``data/processed/mospi/plfs_wage_anchors.csv`` exists.
    """

    processed_root = PROCESSED if processed is None else processed
    fit = fit_profile(bayes_profile, processed=processed_root)
    wages = load_wage_anchors(processed_root)
    extended = load_plfs_extended_wage_anchors(processed_root)
    nurse = wages["nursing"]
    employment = fit.career_medicine.employment_given_labor_force
    formal = fit.career_medicine.formal_job_given_employed

    def _path(
        name: str,
        *,
        completion: float,
        match: float,
        annual_matched: float,
        annual_unmatched: float,
        source: str,
        geometric_sd: float = 1.75,
        lfp: float = 0.85,
        employment_override=None,
    ) -> CareerPathModel:
        geom = geometric_sd if geometric_sd > 1.0 else 1.75
        return CareerPathModel(
            name=name,
            completion=beta_from_mean_ess(
                completion,
                8,
                label=f"{name}_completion",
                source="weak completion prior",
                evidence_class="prior",
            ),
            labor_force_participation=beta_from_mean_ess(
                lfp,
                8,
                label=f"{name}_lfp",
                source="weak LFP prior",
                evidence_class="prior",
            ),
            employment_given_labor_force=employment_override or employment,
            matched_job_given_employed=beta_from_mean_ess(
                match,
                6,
                label=f"{name}_match",
                source="weak field-match prior",
                evidence_class="prior",
            ),
            formal_job_given_employed=formal,
            matched_earnings=LogNormalEarnings.from_median_and_geometric_sd(
                median=annual_matched,
                geometric_sd=geom,
                label=f"{name}_matched_earnings",
                source=source,
            ),
            unmatched_earnings=LogNormalEarnings.from_median_and_geometric_sd(
                median=annual_unmatched,
                geometric_sd=geom,
                label=f"{name}_unmatched_earnings",
                source=source,
            ),
        )

    estimates = pd.read_csv(processed_root / "published_estimates.csv")
    by_id = estimates.set_index("estimate_id")["value"].astype(float)
    phys = wages["medicine"]
    eng = wages["engineering"]
    # Public/private *sector* physician wages remain World Bank means (not in PLFS extract yet).
    public_annual = float(by_id.get("world_bank_public_physician_monthly_wage", phys.monthly_inr)) * 12.0 / 1.15
    private_annual = (
        float(by_id.get("world_bank_private_physician_monthly_wage", phys.monthly_inr * 0.8)) * 12.0 / 1.15
    )
    law_annual = 0.5 * eng.annual_median_inr() + 0.5 * nurse.annual_median_inr()
    if "non_professional_graduate" in extended:
        nonprof = extended["non_professional_graduate"]
        nonprof_annual = nonprof.annual_median_inr()
        nonprof_source = nonprof.source
        nonprof_geom = nonprof.geometric_sd
    else:
        nonprof_annual = nurse.annual_median_inr() * 0.85
        nonprof_source = "stylized non-professional BA/BSc wage knob (PLFS extended anchors missing)"
        nonprof_geom = nurse.geometric_sd
    if "no_college" in extended:
        no_college = extended["no_college"]
        no_college_annual = no_college.annual_median_inr()
        no_college_source = no_college.source
        no_college_geom = no_college.geometric_sd
    else:
        no_college_annual = nurse.annual_median_inr() * 0.45
        no_college_source = "stylized secondary/no-college wage knob (PLFS extended anchors missing)"
        no_college_geom = nurse.geometric_sd
    weaker_employment = beta_from_mean_ess(
        max(employment.mean - 0.08, 0.45),
        employment.effective_sample_size,
        label="weaker_employment_given_lfp",
        source="stylized lower employment for non-college (knob)",
        evidence_class="labeled_sensitivity",
    )

    physician_source = (
        f"{phys.source}; SAME for govt/private college — "
        "no identified college-quality earnings effect"
    )
    return {
        "government_mbbs": _path(
            "government_mbbs",
            completion=0.92,
            match=0.72,
            annual_matched=phys.annual_median_inr(),
            annual_unmatched=nurse.annual_median_inr(),
            source=physician_source,
            geometric_sd=phys.geometric_sd,
        ),
        "private_mbbs": _path(
            "private_mbbs",
            completion=0.90,
            match=0.70,
            annual_matched=phys.annual_median_inr(),
            annual_unmatched=nurse.annual_median_inr(),
            source=physician_source,
            geometric_sd=phys.geometric_sd,
        ),
        "physician_public_sector": _path(
            "physician_public_sector",
            completion=0.92,
            match=0.75,
            annual_matched=public_annual,
            annual_unmatched=nurse.annual_median_inr(),
            source="World Bank public-sector physician wage (employment sector, not college)",
            geometric_sd=phys.geometric_sd,
        ),
        "physician_private_sector": _path(
            "physician_private_sector",
            completion=0.92,
            match=0.70,
            annual_matched=private_annual,
            annual_unmatched=nurse.annual_median_inr(),
            source="World Bank private-sector physician wage (employment sector, not college)",
            geometric_sd=phys.geometric_sd,
        ),
        "engineering": _path(
            "engineering",
            completion=0.82,
            match=0.55,
            annual_matched=eng.annual_median_inr(),
            annual_unmatched=nurse.annual_median_inr(),
            source=eng.source,
            geometric_sd=eng.geometric_sd,
        ),
        "law": _path(
            "law",
            completion=0.80,
            match=0.50,
            annual_matched=law_annual,
            annual_unmatched=nurse.annual_median_inr() * 0.9,
            source="weak law wage proxy (blend of PLFS eng/nurse; not law-identified)",
            geometric_sd=eng.geometric_sd,
        ),
        "other_graduate": _path(
            "other_graduate",
            completion=0.78,
            match=0.40,
            annual_matched=nurse.annual_median_inr(),
            annual_unmatched=nurse.annual_median_inr() * 0.85,
            source=f"{nurse.source} (other-graduate proxy)",
            geometric_sd=nurse.geometric_sd,
        ),
        "non_professional_graduate": _path(
            "non_professional_graduate",
            completion=0.75,
            match=0.35,
            annual_matched=nonprof_annual,
            annual_unmatched=nonprof_annual * 0.8,
            source=nonprof_source,
            geometric_sd=nonprof_geom,
        ),
        "no_college": _path(
            "no_college",
            completion=0.99,
            match=0.30,
            annual_matched=no_college_annual,
            annual_unmatched=no_college_annual * 0.75,
            source=no_college_source,
            geometric_sd=no_college_geom,
            lfp=0.80,
            employment_override=weaker_employment,
        ),
    }


def _mixture_weights(stratum: PrivilegeStratum, config: dict[str, Any]) -> dict[str, float]:
    weights_cfg = config["no_seat_mixture_weights"]
    if stratum.can_afford_private and stratum.school_medium == "english":
        key = "high_privilege"
    elif (not stratum.can_afford_private) and stratum.school_medium == "tamil":
        key = "low_privilege"
    else:
        key = "default"
    weights = {k: float(v) for k, v in weights_cfg[key].items()}
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


def _prep_cost_total(stratum: PrivilegeStratum, config: dict[str, Any]) -> float:
    prep = config["prep_intensity"][stratum.prep_intensity]
    years = float(config["prep_intensity"]["prep_years_before_degree"])
    return float(prep["annual_prep_cost_inr"]) * years

def simulate_stratum_outcomes(
    stratum: PrivilegeStratum,
    config: dict[str, Any],
    careers: dict[str, CareerPathModel],
    *,
    admission_profile: str | None = None,
    draws: int | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """Simulate access plus annual earnings distributions for one stratum.

    Primary metrics are annual earnings:
    - including zeros (employment filter / family-support state for young graduates);
    - conditional on employment (wage distribution among those with a job).

    Lifetime NPV with zeros locked for 35 years is intentionally not the primary story.
    """

    sim = config["simulation"]
    n = int(sim["draws"] if draws is None else draws)
    rng_seed = int(sim["seed"] if seed is None else seed)
    access = access_probabilities(stratum, config, admission_profile=admission_profile)
    hist_edges = [float(x) for x in sim["annual_histogram_edges_inr"]]

    path_annual: dict[str, np.ndarray] = {}
    path_employed: dict[str, np.ndarray] = {}
    quantile_rows: list[dict[str, Any]] = []
    hist_rows: list[dict[str, Any]] = []

    seed_offsets = {
        "government_mbbs": 1,
        "private_mbbs": 2,
        "physician_public_sector": 3,
        "physician_private_sector": 4,
        "engineering": 5,
        "law": 6,
        "other_graduate": 7,
        "non_professional_graduate": 8,
        "no_college": 9,
    }

    kde_rows: list[dict[str, Any]] = []
    # Shared KDE grid on positive earnings for overlay charts (rupees).
    kde_paths = [
        "government_mbbs",
        "private_mbbs",
        "engineering",
        "law",
        "other_graduate",
        "non_professional_graduate",
        "no_college",
        "physician_public_sector",
        "physician_private_sector",
    ]

    for path_name, model in careers.items():
        annual, summary, employed = simulate_one_year(
            model,
            draws=n,
            seed=rng_seed + seed_offsets[path_name],
        )
        path_annual[path_name] = annual
        path_employed[path_name] = employed
        for metric_name, arr in (
            ("annual", annual),
            ("annual_if_employed", annual[employed]),
        ):
            q = earnings_quantiles(arr)
            quantile_rows.append(
                {
                    "stratum_id": stratum.id,
                    "label": stratum.label,
                    "outcome": path_name,
                    "metric": metric_name,
                    "employment_rate": float(summary.probability_employed),
                    "zero_interpretation": (
                        "family_support_or_delayed_independence_not_street_poverty"
                        if metric_name == "annual"
                        else "wage_among_employed_only"
                    ),
                    **q,
                }
            )
        for row in histogram_shares(annual, edges=hist_edges):
            hist_rows.append(
                {
                    "stratum_id": stratum.id,
                    "label": stratum.label,
                    "outcome": path_name,
                    "metric": "annual",
                    **row,
                }
            )
        if employed.any():
            for row in histogram_shares(annual[employed], edges=hist_edges):
                hist_rows.append(
                    {
                        "stratum_id": stratum.id,
                        "label": stratum.label,
                        "outcome": path_name,
                        "metric": "annual_if_employed",
                        **row,
                    }
                )

    # Shared KDE grid across comparison paths (positive earnings among employed).
    positive_pool = np.concatenate(
        [
            path_annual[name][path_employed[name]]
            for name in kde_paths
            if name in path_annual and path_employed[name].any()
        ]
    )
    positive_pool = positive_pool[positive_pool > 0]
    kde_lo = float(np.quantile(positive_pool, 0.02))
    kde_hi = float(np.quantile(positive_pool, 0.98))
    shared_grid = np.linspace(kde_lo, kde_hi, 60)
    for path_name in kde_paths:
        if path_name not in path_annual:
            continue
        employed_earn = path_annual[path_name][path_employed[path_name]]
        if employed_earn.size < 5:
            continue
        xs, dens = kde_curve(employed_earn, grid=shared_grid)
        for x, d in zip(xs, dens, strict=True):
            kde_rows.append(
                {
                    "stratum_id": stratum.id,
                    "label": stratum.label,
                    "outcome": path_name,
                    "metric": "annual_if_employed_kde",
                    "x": float(x),
                    "density": float(d),
                    "note": "bins are display-only; KDE from continuous Monte Carlo draws",
                }
            )

    rng = np.random.default_rng(rng_seed + 99)
    gov_mass = access.p_government_offer
    priv_mass = access.p_private_offer if access.can_afford_private else 0.0
    seat_total = gov_mass + priv_mass
    if seat_total <= 0:
        raise ValueError("seat offer mass must be positive")
    p_gov_given_seat = gov_mass / seat_total

    seat_pick = rng.random(n) < p_gov_given_seat
    seat_annual = np.where(
        seat_pick, path_annual["government_mbbs"], path_annual["private_mbbs"]
    )
    seat_employed = np.where(
        seat_pick, path_employed["government_mbbs"], path_employed["private_mbbs"]
    )

    mix_w = _mixture_weights(stratum, config)
    mix_draw = rng.random(n)
    no_seat_annual = np.zeros(n)
    no_seat_employed = np.zeros(n, dtype=bool)
    cumulative = 0.0
    for path_name, weight in mix_w.items():
        low = cumulative
        cumulative += weight
        mask = (mix_draw >= low) & (mix_draw < cumulative)
        no_seat_annual[mask] = path_annual[path_name][mask]
        no_seat_employed[mask] = path_employed[path_name][mask]

    got_seat = rng.random(n) < access.p_accessible_seat
    unconditional_annual = np.where(got_seat, seat_annual, no_seat_annual)
    unconditional_employed = np.where(got_seat, seat_employed, no_seat_employed)

    composite = {
        "accessible_mbbs_seat": (seat_annual, seat_employed),
        "no_seat_mixture": (no_seat_annual, no_seat_employed),
        "unconditional_stratum": (unconditional_annual, unconditional_employed),
        "government_mbbs_only": (
            path_annual["government_mbbs"],
            path_employed["government_mbbs"],
        ),
    }
    for outcome_name, (annual_arr, employed_arr) in composite.items():
        for metric_name, arr in (
            ("annual", annual_arr),
            ("annual_if_employed", annual_arr[employed_arr]),
        ):
            q = earnings_quantiles(arr)
            quantile_rows.append(
                {
                    "stratum_id": stratum.id,
                    "label": stratum.label,
                    "outcome": outcome_name,
                    "metric": metric_name,
                    "employment_rate": float(employed_arr.mean()),
                    "zero_interpretation": (
                        "family_support_or_delayed_independence_not_street_poverty"
                        if metric_name == "annual"
                        else "wage_among_employed_only"
                    ),
                    **q,
                }
            )
        for row in histogram_shares(annual_arr, edges=hist_edges):
            hist_rows.append(
                {
                    "stratum_id": stratum.id,
                    "label": stratum.label,
                    "outcome": outcome_name,
                    "metric": "annual",
                    **row,
                }
            )

    grid = int(sim["cdf_grid_size"])
    gov_emp = path_annual["government_mbbs"][path_employed["government_mbbs"]]
    noseat_emp = no_seat_annual[no_seat_employed]
    if gov_emp.size == 0 or noseat_emp.size == 0:
        raise ValueError("need employed draws for CDF comparison")
    shared_lo = float(min(gov_emp.min(), noseat_emp.min()))
    shared_hi = float(max(gov_emp.max(), noseat_emp.max()))
    xs = np.linspace(shared_lo, shared_hi, grid)
    gov_sorted = np.sort(gov_emp)
    noseat_sorted = np.sort(noseat_emp)
    eng_emp = path_annual["engineering"][path_employed["engineering"]]
    eng_sorted = np.sort(eng_emp) if eng_emp.size else gov_sorted
    cdf_rows = []
    for x in xs:
        cdf_rows.append(
            {
                "stratum_id": stratum.id,
                "label": stratum.label,
                "metric": "annual_if_employed",
                "x": float(x),
                "cdf_government_mbbs": float(
                    np.searchsorted(gov_sorted, x, side="right") / gov_emp.size
                ),
                "cdf_no_seat_mixture": float(
                    np.searchsorted(noseat_sorted, x, side="right") / noseat_emp.size
                ),
                "cdf_engineering": float(
                    np.searchsorted(eng_sorted, x, side="right") / max(eng_emp.size, 1)
                ),
            }
        )

    def _cond_mean(annual: np.ndarray, employed: np.ndarray) -> float:
        return float(annual[employed].mean()) if employed.any() else float("nan")

    def _cond_median(annual: np.ndarray, employed: np.ndarray) -> float:
        return float(np.median(annual[employed])) if employed.any() else float("nan")

    return {
        "access": access,
        "quantile_rows": quantile_rows,
        "cdf_rows": cdf_rows,
        "histogram_rows": hist_rows,
        "p_accessible": access.p_accessible_seat,
        "p_government_offer": access.p_government_offer,
        "mixture_weights": mix_w,
        "government_employment_rate": float(path_employed["government_mbbs"].mean()),
        "no_seat_employment_rate": float(no_seat_employed.mean()),
        "government_annual_mean": float(path_annual["government_mbbs"].mean()),
        "no_seat_annual_mean": float(no_seat_annual.mean()),
        "government_annual_mean_if_employed": _cond_mean(
            path_annual["government_mbbs"], path_employed["government_mbbs"]
        ),
        "no_seat_annual_mean_if_employed": _cond_mean(no_seat_annual, no_seat_employed),
        "government_annual_median_if_employed": _cond_median(
            path_annual["government_mbbs"], path_employed["government_mbbs"]
        ),
        "no_seat_annual_median_if_employed": _cond_median(
            no_seat_annual, no_seat_employed
        ),
        "unconditional_annual_mean": float(unconditional_annual.mean()),
        "unconditional_employment_rate": float(unconditional_employed.mean()),
        "unconditional_annual_p90": float(np.quantile(unconditional_annual, 0.90)),
        "kde_rows": kde_rows,
        "govt_college_median_if_employed": _cond_median(
            path_annual["government_mbbs"], path_employed["government_mbbs"]
        ),
        "private_college_median_if_employed": _cond_median(
            path_annual["private_mbbs"], path_employed["private_mbbs"]
        ),
        "physician_public_sector_median_if_employed": _cond_median(
            path_annual["physician_public_sector"],
            path_employed["physician_public_sector"],
        ),
        "physician_private_sector_median_if_employed": _cond_median(
            path_annual["physician_private_sector"],
            path_employed["physician_private_sector"],
        ),
        "engineering_median_if_employed": _cond_median(
            path_annual["engineering"], path_employed["engineering"]
        ),
        "law_median_if_employed": _cond_median(path_annual["law"], path_employed["law"]),
        "non_professional_median_if_employed": _cond_median(
            path_annual["non_professional_graduate"],
            path_employed["non_professional_graduate"],
        ),
        "no_college_median_if_employed": _cond_median(
            path_annual["no_college"], path_employed["no_college"]
        ),
    }


def run_privilege_pipeline(
    *,
    config_path: Path | None = None,
    processed: Path | None = None,
    output_dir: Path | None = None,
    draws: int | None = None,
    admission_profile: str | None = None,
) -> dict[str, Path]:
    """Fit the privilege story and write machine-readable artifacts."""

    config = load_privilege_config(config_path)
    processed_root = PROCESSED if processed is None else processed
    out = (processed_root / "bayesian") if output_dir is None else output_dir
    out.mkdir(parents=True, exist_ok=True)

    careers = build_career_paths_for_privilege(processed=processed_root)
    profile = admission_profile or config["default_admission_profile"]

    access_rows: list[dict[str, Any]] = []
    quantile_rows: list[dict[str, Any]] = []
    cdf_rows: list[dict[str, Any]] = []
    hist_rows: list[dict[str, Any]] = []
    kde_rows: list[dict[str, Any]] = []
    ladder_summary: list[dict[str, Any]] = []

    for row in config["access_ladder"]:
        stratum = stratum_from_ladder_row(row)
        result = simulate_stratum_outcomes(
            stratum,
            config,
            careers,
            admission_profile=profile,
            draws=draws,
        )
        access_rows.append(asdict(result["access"]))
        quantile_rows.extend(result["quantile_rows"])
        cdf_rows.extend(result["cdf_rows"])
        hist_rows.extend(result["histogram_rows"])
        kde_rows.extend(result["kde_rows"])
        ladder_summary.append(
            {
                "stratum_id": stratum.id,
                "label": stratum.label,
                "p_accessible_seat": result["p_accessible"],
                "p_government_offer": result["p_government_offer"],
                "government_employment_rate": result["government_employment_rate"],
                "no_seat_employment_rate": result["no_seat_employment_rate"],
                "government_annual_mean": result["government_annual_mean"],
                "no_seat_annual_mean": result["no_seat_annual_mean"],
                "government_minus_noseat_annual_mean": (
                    result["government_annual_mean"] - result["no_seat_annual_mean"]
                ),
                "government_annual_mean_if_employed": result[
                    "government_annual_mean_if_employed"
                ],
                "no_seat_annual_mean_if_employed": result[
                    "no_seat_annual_mean_if_employed"
                ],
                "government_minus_noseat_annual_mean_if_employed": (
                    result["government_annual_mean_if_employed"]
                    - result["no_seat_annual_mean_if_employed"]
                ),
                "government_annual_median_if_employed": result[
                    "government_annual_median_if_employed"
                ],
                "no_seat_annual_median_if_employed": result[
                    "no_seat_annual_median_if_employed"
                ],
                "govt_college_median_if_employed": result[
                    "govt_college_median_if_employed"
                ],
                "private_college_median_if_employed": result[
                    "private_college_median_if_employed"
                ],
                "physician_public_sector_median_if_employed": result[
                    "physician_public_sector_median_if_employed"
                ],
                "physician_private_sector_median_if_employed": result[
                    "physician_private_sector_median_if_employed"
                ],
                "engineering_median_if_employed": result["engineering_median_if_employed"],
                "law_median_if_employed": result["law_median_if_employed"],
                "non_professional_median_if_employed": result[
                    "non_professional_median_if_employed"
                ],
                "no_college_median_if_employed": result["no_college_median_if_employed"],
                "unconditional_annual_mean": result["unconditional_annual_mean"],
                "unconditional_employment_rate": result["unconditional_employment_rate"],
                "unconditional_annual_p90": result["unconditional_annual_p90"],
                "mixture_weights": result["mixture_weights"],
            }
        )

    access_df = pd.DataFrame(access_rows)
    quant_df = pd.DataFrame(quantile_rows)
    cdf_df = pd.DataFrame(cdf_rows)
    hist_df = pd.DataFrame(hist_rows)

    tamil_base = next(
        s for s in ladder_summary if s["stratum_id"] == "tamil_cant_afford_nonmetro_none"
    )
    eng_cant = next(
        s for s in ladder_summary if s["stratum_id"] == "english_cant_afford_nonmetro_modest"
    )
    eng_can = next(
        s for s in ladder_summary if s["stratum_id"] == "english_can_afford_nonmetro_modest"
    )
    top = ladder_summary[-1]
    afford_ratio = affordability_only_ratio(config)
    cmse_priors = load_cmse_coaching_priors(processed_root)
    cmse_x_xii = (
        cmse_priors.query("sector_label == 'all' and enrolment_band == 'class_x_xii'")
        if not cmse_priors.empty
        else cmse_priors
    )

    story = {
        "model_version": config.get("model_version"),
        "admission_profile": profile,
        "primary_metric": config["simulation"].get("primary_metric", "annual_earnings"),
        "narrative": config.get("narrative", {}),
        "zero_earnings_note": (
            "Annual zeros are an employment/non-completion filter. For highly educated young "
            "adults they usually mean family support / delayed independence, not street poverty. "
            "Do not lock zeros into a 35-year lifetime NPV."
        ),
        "affordability_only_access_ratio": afford_ratio,
        "access_ladder": ladder_summary,
        "decomposition": {
            "p_accessible_low": tamil_base["p_accessible_seat"],
            "p_accessible_english_cant_afford": eng_cant["p_accessible_seat"],
            "p_accessible_english_can_afford": eng_can["p_accessible_seat"],
            "p_accessible_top": top["p_accessible_seat"],
            "p_government_low": tamil_base["p_government_offer"],
            "p_government_english": eng_can["p_government_offer"],
            "medium_access_ratio_english_cant_over_tamil_base": (
                eng_cant["p_accessible_seat"] / tamil_base["p_accessible_seat"]
            ),
            "affordability_step_ratio": eng_can["p_accessible_seat"]
            / eng_cant["p_accessible_seat"],
            "full_ladder_ratio_top_over_low": top["p_accessible_seat"]
            / tamil_base["p_accessible_seat"],
            "within_stratum_government_minus_noseat_annual_mean": eng_can[
                "government_minus_noseat_annual_mean"
            ],
            "within_stratum_government_minus_noseat_annual_mean_if_employed": eng_can[
                "government_minus_noseat_annual_mean_if_employed"
            ],
            "government_annual_median_if_employed_mid": eng_can[
                "government_annual_median_if_employed"
            ],
            "no_seat_annual_median_if_employed_mid": eng_can[
                "no_seat_annual_median_if_employed"
            ],
            "govt_vs_private_college_median_ratio_mid": (
                eng_can["govt_college_median_if_employed"]
                / eng_can["private_college_median_if_employed"]
            ),
            "public_vs_private_sector_physician_median_ratio_mid": (
                eng_can["physician_public_sector_median_if_employed"]
                / eng_can["physician_private_sector_median_if_employed"]
            ),
            "med_vs_engineering_median_ratio_mid": (
                eng_can["govt_college_median_if_employed"]
                / eng_can["engineering_median_if_employed"]
            ),
            "med_vs_nonprofessional_median_ratio_mid": (
                eng_can["govt_college_median_if_employed"]
                / eng_can["non_professional_median_if_employed"]
            ),
            "med_vs_nocollege_median_ratio_mid": (
                eng_can["govt_college_median_if_employed"]
                / eng_can["no_college_median_if_employed"]
            ),
            "cross_stratum_unconditional_annual_mean_ratio_top_over_low": (
                top["unconditional_annual_mean"] / tamil_base["unconditional_annual_mean"]
            ),
            "cross_stratum_unconditional_p90_ratio_top_over_low": (
                top["unconditional_annual_p90"] / tamil_base["unconditional_annual_p90"]
            ),
            "college_vs_sector_note": (
                "Govt vs private *college* seats share the same physician wage prior "
                "(ratio ~1). Public vs private *sector* physician wages differ (World Bank). "
                "Not a US-style private-college quality premium."
            ),
            "wage_source": careers["government_mbbs"].matched_earnings.source,
            "cmse_class_x_xii_coaching_rate": (
                float(cmse_x_xii["coaching_rate_weighted"].iloc[0])
                if not cmse_x_xii.empty
                else None
            ),
            "cmse_class_x_xii_coaching_exp_p50": (
                float(cmse_x_xii["coaching_exp_p50"].iloc[0])
                if not cmse_x_xii.empty and pd.notna(cmse_x_xii["coaching_exp_p50"].iloc[0])
                else None
            ),
        },
        "warnings": [
            "TN medium rates are observed associations among counselling applicants, not national causal English effects.",
            "Affordability ~2x is a mechanical accounting identity under match_government_rate private offers.",
            "Metro and prep admission multipliers are labeled sensitivity knobs unless prep_sensitivity profile is selected.",
            "Government vs private MBBS college wages are intentionally equal; do not read as college-quality effect.",
            "Medicine/engineering/nursing/non-professional/no-college wages prefer PLFS 2025 medians when mospi aggregates exist.",
            "CMSE coaching priors are school Class X–XII tutoring, not NEET-specific or dropper coaching.",
            "Histogram bins are display-only; KDE uses continuous Monte Carlo draws.",
            "Zeros mean employment filter / family support for young graduates, not lifetime destitution.",
            "Causal language for scenario contrasts is prohibited.",
        ],
    }

    access_path = out / "access_by_stratum.csv"
    quant_path = out / "earnings_quantiles_by_outcome.csv"
    cdf_path = out / "cdf_points.csv"
    hist_path = out / "earnings_histograms.csv"
    kde_path = out / "earnings_kde.csv"
    attempt_path = out / "attempt_repeater_sensitivity.csv"
    story_path = out / "inequality_story.json"
    access_df.to_csv(access_path, index=False)
    quant_df.to_csv(quant_path, index=False)
    cdf_df.to_csv(cdf_path, index=False)
    hist_df.to_csv(hist_path, index=False)
    pd.DataFrame(kde_rows).to_csv(kde_path, index=False)
    attempt_df = repeater_sensitivity_table()
    attempt_df.to_csv(attempt_path, index=False)
    import json

    story["attempt_inference"] = {
        "observed_p_repeater_among_admitted": float(
            attempt_df["p_repeater_among_admitted"].iloc[0]
        ),
        "source": str(attempt_df["source"].iloc[0]),
        "note": (
            "Backs out P(repeater|applicant) under labeled relative admission probabilities. "
            "Does not identify mean attempt count or the full 1,2,3,… distribution."
        ),
        "sensitivity": attempt_df[
            [
                "relative_admit_prob_repeater_over_first",
                "p_repeater_among_applicants",
                "p_first_attempt_among_applicants",
                "interpretation",
            ]
        ].to_dict(orient="records"),
    }
    story_path.write_text(json.dumps(story, indent=2), encoding="utf-8")
    return {
        "access_by_stratum": access_path,
        "earnings_quantiles_by_outcome": quant_path,
        "cdf_points": cdf_path,
        "earnings_histograms": hist_path,
        "earnings_kde": kde_path,
        "attempt_repeater_sensitivity": attempt_path,
        "inequality_story": story_path,
    }


__all__ = [
    "AccessResult",
    "PrivilegeStratum",
    "access_probabilities",
    "affordability_only_ratio",
    "build_career_paths_for_privilege",
    "combine_independent_marginal_rates",
    "load_privilege_config",
    "run_privilege_pipeline",
    "simulate_stratum_outcomes",
    "stratum_from_ladder_row",
]
