"""End-to-end Bayesian evidence update for the NEET life-course model.

This module fits conjugate posteriors under the three documented prior profiles using only
local processed evidence.  It does not claim causal identification of coaching or admission
effects.  Selected coaching cohorts are held out for posterior-predictive checks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import log
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .bayes import (
    BetaEvidence,
    DirichletEvidence,
    TruncatedNormalEvidence,
    beta_from_mean_ess,
    partial_pool_beta,
    shrinkage_weight,
)
from .career import CareerPathModel, LogNormalEarnings, simulate_one_year
from .evidence import (
    PROCESSED,
    load_aiq_course_counts,
    load_coaching_rate_summary,
    load_employment_benchmarks,
    load_medium_aggregate_rates,
    load_medium_year_rates,
    load_national_exam_counts,
    load_wage_anchors,
)
from .priors import PROFILE_NAMES, PriorProfile, binary_prior, load_prior_config, materialize_profile


@dataclass(frozen=True)
class PosteriorSummaryRow:
    profile: str
    quantity: str
    mean: float
    sd: float
    ci_low: float
    ci_high: float
    ess: float
    evidence_class: str
    source: str
    notes: str


@dataclass(frozen=True)
class ProfilePosteriors:
    profile: str
    qualify_rate: BetaEvidence
    mbbs_capacity_rate: BetaEvidence
    tn_govt_english_post: BetaEvidence
    tn_govt_tamil_post: BetaEvidence
    tn_first_among_admitted: BetaEvidence
    medium_rate_ratio_post: float
    coaching_score_shift: TruncatedNormalEvidence
    aiq_course_mix: DirichletEvidence
    career_medicine: CareerPathModel
    career_engineering: CareerPathModel
    career_other_graduate: CareerPathModel
    holdout_tn_year: str
    holdout_english_rate: float
    holdout_tamil_rate: float
    predicted_holdout_english: float
    predicted_holdout_tamil: float


def _beta_row(
    profile: str,
    quantity: str,
    posterior: BetaEvidence,
    *,
    notes: str = "",
) -> PosteriorSummaryRow:
    low, high = posterior.credible_interval(0.95)
    return PosteriorSummaryRow(
        profile=profile,
        quantity=quantity,
        mean=posterior.mean,
        sd=float(posterior.variance**0.5),
        ci_low=low,
        ci_high=high,
        ess=posterior.effective_sample_size,
        evidence_class=posterior.evidence_class,
        source=posterior.source,
        notes=notes,
    )


def _fit_qualify_and_capacity(profile: PriorProfile, processed: Path) -> tuple[BetaEvidence, BetaEvidence]:
    counts = load_national_exam_counts(processed)
    qualify_prior = binary_prior(
        profile,
        center=0.50,
        label="neet_qualify_rate",
        source="prior + NTA 2024 counts",
    )
    qualify = qualify_prior.update_binomial(
        successes=counts.qualified,
        trials=counts.appeared_excluding_ufm,
        evidence_weight=1.0,
        label="neet_qualify_rate",
        source=f"{counts.source_qualified}; denominator={counts.source_appeared}",
        evidence_class="same_population_complete_counts",
    )

    # Capacity is an accounting rate (seats / appeared), not P(offer | applicant).
    # The NMC page is a dynamic snapshot, so we do not treat seats as a 2.3M-trial binomial.
    capacity_center = min(
        max(counts.nmc_mbbs_seats / counts.appeared_excluding_ufm, 1e-4),
        1.0 - 1e-4,
    )
    snapshot_ess = 30.0
    capacity = beta_from_mean_ess(
        capacity_center,
        profile.binary_ess + snapshot_ess,
        label="nmc_mbbs_seats_per_appeared",
        source=f"{counts.source_seats}; {counts.source_appeared}",
        evidence_class="capacity_accounting",
    )
    return qualify, capacity


def _fit_tamil_nadu_medium(
    profile: PriorProfile,
    processed: Path,
) -> tuple[BetaEvidence, BetaEvidence, str, float, float, float, float]:
    """Update post-NEET government allotment rates; hold out the last year for validation."""

    years = load_medium_year_rates(processed)
    post = years.loc[years["neet_period"] == "post_neet"].copy()
    if post.empty:
        raise ValueError("no post-NEET Tamil Nadu medium rows available")
    holdout_year = str(post["year"].iloc[-1])
    calibrate = post.loc[post["year"] != holdout_year]
    holdout = post.loc[post["year"] == holdout_year].iloc[0]

    aggregates = {row.period: row for row in load_medium_aggregate_rates(processed)}
    post_agg = aggregates["post_neet"]

    # Use year-level sums excluding holdout for the count update; fall back to aggregate if needed.
    if calibrate.empty:
        eng_app = post_agg.english_applicants
        eng_allot = post_agg.english_government_allotments
        tam_app = post_agg.tamil_applicants
        tam_allot = post_agg.tamil_government_allotments
    else:
        eng_app = int(calibrate["applied_english_medium"].sum())
        eng_allot = int(calibrate["govt_allotted_english_medium"].sum())
        tam_app = int(calibrate["applied_tamil_medium"].sum())
        tam_allot = int(calibrate["govt_allotted_tamil_medium"].sum())

    # Broad center from pre-NEET English rate so the post-NEET Tamil shift is visible.
    pre = aggregates["pre_neet"]
    pre_english_rate = pre.english_government_allotments / pre.english_applicants
    prior_eng = binary_prior(
        profile,
        center=pre_english_rate,
        label="tn_govt_allotment_english_post_neet",
        source="Justice A.K. Rajan Committee Table 7.18",
    )
    prior_tam = binary_prior(
        profile,
        center=pre.tamil_government_allotments / pre.tamil_applicants,
        label="tn_govt_allotment_tamil_post_neet",
        source="Justice A.K. Rajan Committee Table 7.18",
    )
    # Same-state historical counts: full weight for calibration years.
    eng = prior_eng.update_binomial(
        successes=eng_allot,
        trials=eng_app,
        evidence_weight=1.0,
        evidence_class="same_exam_state_complete_counts",
    )
    tam = prior_tam.update_binomial(
        successes=tam_allot,
        trials=tam_app,
        evidence_weight=1.0,
        evidence_class="same_exam_state_complete_counts",
    )
    holdout_eng = float(holdout["govt_rate_english"])
    holdout_tam = float(holdout["govt_rate_tamil"])
    return eng, tam, holdout_year, holdout_eng, holdout_tam, eng.mean, tam.mean


def _fit_aiq_course_mix(profile: PriorProfile, processed: Path) -> DirichletEvidence:
    counts = load_aiq_course_counts(processed)
    # Weak symmetric prior scaled by profile ESS.
    prior_each = max(profile.binary_ess / 4.0, 0.5)
    prior = DirichletEvidence(
        {
            "mbbs": prior_each,
            "bds": prior_each,
            "nursing": prior_each,
            "other": prior_each,
        },
        label="mcc_2024_aiq_course_mix",
        source="MCC UG 2024 tidy allotments",
        evidence_class="prior",
    )
    if counts.total == 0:
        return prior
    updated = prior.update_counts(
        {
            "mbbs": counts.mbbs,
            "bds": counts.bds,
            "nursing": counts.nursing,
            "other": counts.other,
        },
        evidence_weight=1.0,
    )
    return DirichletEvidence(
        updated.alpha,
        label=updated.label,
        source=updated.source,
        evidence_class="same_population_complete_counts",
    )


def _employment_from_unemployment(
    unemployment: float,
    ess: float,
    *,
    label: str,
    source: str,
) -> BetaEvidence:
    employment = min(max(1.0 - unemployment, 1e-4), 1.0 - 1e-4)
    return beta_from_mean_ess(
        employment,
        ess,
        label=label,
        source=source,
        evidence_class="india_graduate_proxy",
    )


def _build_career_paths(profile: PriorProfile, processed: Path) -> tuple[CareerPathModel, ...]:
    benchmarks = {row.id: row for row in load_employment_benchmarks(processed)}
    youth = benchmarks["graduate_youth_unemployment_2022"]
    young = benchmarks["graduate_unemployment_15_25_2023"]
    older = benchmarks["graduate_unemployment_25_29_2023"]
    wages = load_wage_anchors(processed)

    parent_employment = _employment_from_unemployment(
        youth.estimate,
        youth.suggested_prior_ess + profile.binary_ess,
        label="graduate_employment_given_lfp_15_29",
        source=youth.source,
    )
    # Age bands as soft children of the youth parent.
    young_employment = partial_pool_beta(
        parent_employment,
        child_successes=(1.0 - young.estimate) * young.suggested_prior_ess,
        child_trials=young.suggested_prior_ess,
        child_evidence_weight=1.0,
        label="graduate_employment_given_lfp_15_25",
        source=young.source,
    )
    older_employment = partial_pool_beta(
        parent_employment,
        child_successes=(1.0 - older.estimate) * older.suggested_prior_ess,
        child_trials=older.suggested_prior_ess,
        child_evidence_weight=1.0,
        label="graduate_employment_given_lfp_25_29",
        source=older.source,
    )
    # Blend age bands for a mid-career-entry working assumption.
    blended_mean = 0.5 * young_employment.mean + 0.5 * older_employment.mean
    employment = beta_from_mean_ess(
        blended_mean,
        min(young_employment.effective_sample_size, older_employment.effective_sample_size),
        label="graduate_employment_blended_age",
        source="ILO/IHD 2024 + APU SOWI 2026 age bands",
        evidence_class="hierarchical",
    )

    formal_share = benchmarks.get("graduate_formal_employment_2022")
    if formal_share is None:
        formal = binary_prior(profile, center=0.36, label="formal_job_given_employed")
    else:
        # Keep as a weak prior center only; denominator not fully audited.
        formal = beta_from_mean_ess(
            formal_share.estimate,
            formal_share.suggested_prior_ess,
            label="formal_job_given_employed",
            source=formal_share.source,
            evidence_class="validation_pending_denominator_audit",
        )

    def _path(
        name: str,
        *,
        completion_mean: float,
        match_mean: float,
        wage_key: str,
        unmatched_annual: float,
        geometric_sd: float = 1.75,
    ) -> CareerPathModel:
        wage = wages[wage_key]
        # Field employment stays pooled to the graduate parent; no invented field premium.
        field_employment = partial_pool_beta(
            employment,
            label=f"{name}_employment_given_lfp",
            source=employment.source,
            evidence_class="hierarchical_no_field_counts",
        )
        return CareerPathModel(
            name=name,
            completion=binary_prior(
                profile,
                center=completion_mean,
                label=f"{name}_degree_completion",
                source="weak completion prior; no national NEET-path panel",
            ),
            labor_force_participation=binary_prior(
                profile,
                center=0.85,
                label=f"{name}_labor_force_participation",
                source="weak graduate LFP prior",
            ),
            employment_given_labor_force=field_employment,
            matched_job_given_employed=binary_prior(
                profile,
                center=match_mean,
                label=f"{name}_field_match_given_employed",
                source="weak field-match prior",
            ),
            formal_job_given_employed=formal,
            matched_earnings=LogNormalEarnings.from_median_and_geometric_sd(
                median=wage.annual_median_inr(),
                geometric_sd=wage.geometric_sd if wage.geometric_sd > 1.0 else geometric_sd,
                label=f"{name}_matched_annual_earnings",
                source=wage.source,
            ),
            unmatched_earnings=LogNormalEarnings.from_median_and_geometric_sd(
                median=unmatched_annual,
                geometric_sd=wage.geometric_sd if wage.geometric_sd > 1.0 else geometric_sd,
                label=f"{name}_unmatched_annual_earnings",
                source="PLFS/World Bank comparator wages / weak prior",
            ),
        )

    nurse_annual = wages["nursing"].annual_median_inr()
    medicine = _path(
        "medicine",
        completion_mean=0.92,
        match_mean=0.70,
        wage_key="medicine",
        unmatched_annual=nurse_annual,
    )
    engineering = _path(
        "engineering",
        completion_mean=0.82,
        match_mean=0.55,
        wage_key="engineering",
        unmatched_annual=nurse_annual,
    )
    other = _path(
        "other_graduate",
        completion_mean=0.78,
        match_mean=0.40,
        wage_key="nursing",
        unmatched_annual=nurse_annual * 0.85,
    )
    # Attach shrinkage note via unused computation for report diagnostics.
    _ = shrinkage_weight(parent_employment.effective_sample_size, young.suggested_prior_ess)
    return medicine, engineering, other


def _fit_tn_first_among_admitted(profile: PriorProfile, processed: Path) -> BetaEvidence:
    """Bayesian update for P(current-year / first-timer | TN MBBS admit).

    Uses Rajan Table 7.38 post-NEET year shares with deliberately small ESS
    (state admitted composition ≠ national applicant truth). Proxy for the
    claim that most winners are not first-sit school-leavers — not birth-year microdata.
    """

    candidates = [
        processed / "bayesian" / "rajan_repeater_by_year.csv",
        processed / "tamil_nadu" / "rajan_repeater_by_year.csv",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        # Fallback: single 2020-21 point from published prose.
        prior = binary_prior(
            profile,
            center=0.50,
            label="tn_first_among_admitted",
            source="prior + Rajan Table 7.38 fallback",
        )
        return prior.update_binomial(
            successes=0.2858 * 30.0,
            trials=30.0,
            evidence_weight=1.0,
            label="tn_first_among_admitted",
            source="Rajan 2020-21 current-students share 28.58% (ESS=30)",
            evidence_class="same_exam_other_state_or_year",
        )

    df = pd.read_csv(path)
    post = df.loc[df["neet_era"] == "post_neet"].copy()
    # Broad prior near pre-NEET high first-timer share so the post-NEET collapse is visible.
    prior = binary_prior(
        profile,
        center=0.90,
        label="tn_first_among_admitted",
        source="prior centered near pre-NEET TN first-timer admit share",
    )
    # Year ESS rises slightly for later years (clearer NEET equilibrium); still << nominal N.
    year_ess = {
        "2016-2017": 12.0,
        "2017-2018": 16.0,
        "2018-2019": 20.0,
        "2019-2020": 24.0,
        "2020-2021": 30.0,
    }
    post_ev = prior
    for _, row in post.iterrows():
        session = str(row["session"])
        ess = year_ess.get(session, 15.0)
        p = float(row["current_students_share"])
        post_ev = post_ev.update_binomial(
            successes=p * ess,
            trials=ess,
            evidence_weight=1.0,
            label="tn_first_among_admitted",
            source=f"Rajan Table 7.38 {session} current-students share (ESS={ess:g})",
            evidence_class="same_exam_other_state_or_year",
        )
    return post_ev


def fit_profile(profile_name: str, *, processed: Path | None = None) -> ProfilePosteriors:
    processed_root = PROCESSED if processed is None else processed
    config = load_prior_config()
    profile = materialize_profile(profile_name, config)
    qualify, capacity = _fit_qualify_and_capacity(profile, processed_root)
    eng, tam, holdout_year, hold_eng, hold_tam, pred_eng, pred_tam = _fit_tamil_nadu_medium(
        profile, processed_root
    )
    first_admit = _fit_tn_first_among_admitted(profile, processed_root)
    aiq = _fit_aiq_course_mix(profile, processed_root)
    medicine, engineering, other = _build_career_paths(profile, processed_root)
    return ProfilePosteriors(
        profile=profile_name,
        qualify_rate=qualify,
        mbbs_capacity_rate=capacity,
        tn_govt_english_post=eng,
        tn_govt_tamil_post=tam,
        tn_first_among_admitted=first_admit,
        medium_rate_ratio_post=eng.mean / tam.mean if tam.mean > 0 else float("inf"),
        coaching_score_shift=profile.coaching_shift,
        aiq_course_mix=aiq,
        career_medicine=medicine,
        career_engineering=engineering,
        career_other_graduate=other,
        holdout_tn_year=holdout_year,
        holdout_english_rate=hold_eng,
        holdout_tamil_rate=hold_tam,
        predicted_holdout_english=pred_eng,
        predicted_holdout_tamil=pred_tam,
    )


def posterior_summary_table(fits: list[ProfilePosteriors]) -> pd.DataFrame:
    rows: list[PosteriorSummaryRow] = []
    for fit in fits:
        rows.extend(
            [
                _beta_row(fit.profile, "neet_qualify_rate", fit.qualify_rate),
                _beta_row(
                    fit.profile,
                    "nmc_mbbs_seats_per_appeared",
                    fit.mbbs_capacity_rate,
                    notes="capacity accounting, not P(offer|applicant)",
                ),
                _beta_row(
                    fit.profile,
                    "tn_govt_allotment_english_post_neet",
                    fit.tn_govt_english_post,
                    notes="Tamil Nadu ordinary quota; not national",
                ),
                _beta_row(
                    fit.profile,
                    "tn_govt_allotment_tamil_post_neet",
                    fit.tn_govt_tamil_post,
                    notes="Tamil Nadu ordinary quota; not national",
                ),
                _beta_row(
                    fit.profile,
                    "tn_first_among_admitted_mbbs",
                    fit.tn_first_among_admitted,
                    notes=(
                        "P(current-year student | TN MBBS admit) from Rajan Table 7.38; "
                        "proxy that most winners are not first-sit school-leavers — "
                        "not national birth-year microdata"
                    ),
                ),
            ]
        )
        shift = fit.coaching_score_shift
        rows.append(
            PosteriorSummaryRow(
                profile=fit.profile,
                quantity="coaching_score_shift_sd",
                mean=shift.mean,
                sd=shift.sd,
                ci_low=shift.lower,
                ci_high=shift.upper,
                ess=float("nan"),
                evidence_class=shift.evidence_class,
                source=shift.source,
                notes="prior only; selected cohorts are PPC targets",
            )
        )
        for key, value in fit.aiq_course_mix.mean.items():
            rows.append(
                PosteriorSummaryRow(
                    profile=fit.profile,
                    quantity=f"aiq_course_share_{key}",
                    mean=value,
                    sd=float("nan"),
                    ci_low=float("nan"),
                    ci_high=float("nan"),
                    ess=fit.aiq_course_mix.effective_sample_size,
                    evidence_class=fit.aiq_course_mix.evidence_class,
                    source=fit.aiq_course_mix.source,
                    notes="MCC AIQ/deemed/central allotment mix",
                )
            )
        for path in (fit.career_medicine, fit.career_engineering, fit.career_other_graduate):
            rows.append(
                _beta_row(
                    fit.profile,
                    f"{path.name}_employment_given_lfp",
                    path.employment_given_labor_force,
                    notes="broad graduate proxy; not field-identified",
                )
            )
            rows.append(
                PosteriorSummaryRow(
                    profile=fit.profile,
                    quantity=f"{path.name}_plug_in_expected_annual_earnings_inr",
                    mean=path.plug_in_expected_annual_earnings(),
                    sd=float("nan"),
                    ci_low=float("nan"),
                    ci_high=float("nan"),
                    ess=float("nan"),
                    evidence_class="derived",
                    source="career gates × World Bank wage anchors",
                    notes="includes zeros for non-completion / non-employment via gate product",
                )
            )
    return pd.DataFrame([asdict(row) for row in rows])


def coaching_ppc_table(
    fits: list[ProfilePosteriors],
    *,
    processed: Path | None = None,
    draws: int = 20_000,
    seed: int = 7,
) -> pd.DataFrame:
    """Compare coaching-cohort outcome rates to national/posteriors without updating effects."""

    processed_root = PROCESSED if processed is None else processed
    cohorts = load_coaching_rate_summary(processed_root)
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for fit in fits:
        national = fit.qualify_rate.sample(draws, rng=rng)
        capacity = fit.mbbs_capacity_rate.sample(draws, rng=rng)
        shift = fit.coaching_score_shift.sample(draws, rng=rng)
        for cohort in cohorts:
            if cohort.outcome == "neet_qualified":
                reference = national
                reference_name = "posterior_national_qualify_rate"
            elif cohort.outcome in {"mbbs_admission", "government_mbbs_admission"}:
                reference = capacity
                reference_name = "posterior_national_mbbs_capacity_rate"
            else:
                continue
            # Under a neutral selection model the cohort mean would track the national rate.
            # Observed - predicted gaps diagnose selection, not a coaching LATE.
            predicted = float(reference.mean())
            residual = cohort.observed_rate - predicted
            rows.append(
                {
                    "profile": fit.profile,
                    "evidence_id": cohort.evidence_id,
                    "program": cohort.program,
                    "cohort_year": cohort.cohort_year,
                    "outcome": cohort.outcome,
                    "observed_rate": cohort.observed_rate,
                    "trials": cohort.trials,
                    "selection_into_program": cohort.selection_into_program,
                    "reference": reference_name,
                    "predicted_mean_under_national_rate": predicted,
                    "observed_minus_predicted": residual,
                    "coaching_prior_shift_mean_sd": float(shift.mean()),
                    "evidence_role": cohort.evidence_role,
                    "used_to_update_coaching_effect": False,
                }
            )
    return pd.DataFrame(rows)


def profile_comparison_table(
    fits: list[ProfilePosteriors],
    *,
    draws: int = 40_000,
    seed: int = 11,
) -> pd.DataFrame:
    """Summarize how material conclusions move across prior profiles."""

    rows: list[dict[str, Any]] = []
    for fit in fits:
        med_earn, med_summary, _ = simulate_one_year(
            fit.career_medicine, draws=draws, seed=seed
        )
        eng_earn, eng_summary, _ = simulate_one_year(
            fit.career_engineering, draws=draws, seed=seed + 1
        )
        other_earn, other_summary, _ = simulate_one_year(
            fit.career_other_graduate, draws=draws, seed=seed + 2
        )
        # Independent-odds combination is not needed here; report direct TN posteriors.
        rows.append(
            {
                "profile": fit.profile,
                "qualify_rate_mean": fit.qualify_rate.mean,
                "qualify_rate_ci_low": fit.qualify_rate.credible_interval()[0],
                "qualify_rate_ci_high": fit.qualify_rate.credible_interval()[1],
                "mbbs_capacity_rate_mean": fit.mbbs_capacity_rate.mean,
                "tn_english_govt_rate_mean": fit.tn_govt_english_post.mean,
                "tn_tamil_govt_rate_mean": fit.tn_govt_tamil_post.mean,
                "tn_first_among_admitted_mean": fit.tn_first_among_admitted.mean,
                "tn_first_among_admitted_ci_low": fit.tn_first_among_admitted.credible_interval()[0],
                "tn_first_among_admitted_ci_high": fit.tn_first_among_admitted.credible_interval()[1],
                "tn_english_to_tamil_rate_ratio": fit.medium_rate_ratio_post,
                "tn_holdout_year": fit.holdout_tn_year,
                "tn_holdout_english_observed": fit.holdout_english_rate,
                "tn_holdout_tamil_observed": fit.holdout_tamil_rate,
                "tn_holdout_english_abs_error": abs(
                    fit.predicted_holdout_english - fit.holdout_english_rate
                ),
                "tn_holdout_tamil_abs_error": abs(
                    fit.predicted_holdout_tamil - fit.holdout_tamil_rate
                ),
                "coaching_shift_prior_mean_sd": fit.coaching_score_shift.mean,
                "medicine_mean_annual_earnings": med_summary.mean_annual_earnings,
                "medicine_zero_earnings_share": med_summary.probability_zero_earnings,
                "engineering_mean_annual_earnings": eng_summary.mean_annual_earnings,
                "engineering_zero_earnings_share": eng_summary.probability_zero_earnings,
                "other_graduate_mean_annual_earnings": other_summary.mean_annual_earnings,
                "other_graduate_zero_earnings_share": other_summary.probability_zero_earnings,
                "medicine_minus_engineering_mean_earnings": float(
                    med_earn.mean() - eng_earn.mean()
                ),
                "medicine_minus_other_mean_earnings": float(
                    med_earn.mean() - other_earn.mean()
                ),
                "aiq_mbbs_share": fit.aiq_course_mix.mean["mbbs"],
            }
        )
    return pd.DataFrame(rows)


def scarcity_log_odds(fit: ProfilePosteriors) -> dict[str, float]:
    """Diagnostic transforms for report narrative."""

    q = fit.qualify_rate.mean
    c = fit.mbbs_capacity_rate.mean
    return {
        "log_odds_qualify": log(q / (1.0 - q)),
        "log_odds_capacity": log(c / (1.0 - c)),
        "appeared_per_mbbs_seat": 1.0 / c,
        "qualified_per_mbbs_seat": q / c,
    }


def fit_all_profiles(*, processed: Path | None = None) -> list[ProfilePosteriors]:
    return [fit_profile(name, processed=processed) for name in PROFILE_NAMES]


def run_bayesian_pipeline(
    *,
    processed: Path | None = None,
    output_dir: Path | None = None,
    draws: int = 40_000,
) -> dict[str, Path]:
    """Fit all profiles and write machine-readable artifacts."""

    processed_root = PROCESSED if processed is None else processed
    out = (processed_root / "bayesian") if output_dir is None else output_dir
    out.mkdir(parents=True, exist_ok=True)

    fits = fit_all_profiles(processed=processed_root)
    summary = posterior_summary_table(fits)
    comparison = profile_comparison_table(fits, draws=draws)
    ppc = coaching_ppc_table(fits, processed=processed_root)

    summary_path = out / "posterior_summary.csv"
    comparison_path = out / "profile_comparison.csv"
    ppc_path = out / "ppc_coaching.csv"
    summary.to_csv(summary_path, index=False)
    comparison.to_csv(comparison_path, index=False)
    ppc.to_csv(ppc_path, index=False)

    # Compact JSON for reports / canvases.
    import json

    payload = {
        "model_version": load_prior_config().get("model_version"),
        "profiles": PROFILE_NAMES,
        "default_profile": load_prior_config().get("default_profile"),
        "scarcity": {fit.profile: scarcity_log_odds(fit) for fit in fits},
        "comparison": comparison.to_dict(orient="records"),
        "assumptions": [
            "Missing cross-dataset joints use conditional independence only where explicitly combined.",
            "Absent effect evidence remains neutral.",
            "Selected coaching cohorts are PPC targets, not treatment-effect updates.",
            "Employment rates are broad graduate proxies, not field-identified NEET outcomes.",
            "NMC seats / appeared is capacity accounting, not an individual offer probability.",
            "No additional gated microdata were used.",
        ],
    }
    json_path = out / "bayesian_results.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {
        "posterior_summary": summary_path,
        "profile_comparison": comparison_path,
        "ppc_coaching": ppc_path,
        "bayesian_results": json_path,
    }
