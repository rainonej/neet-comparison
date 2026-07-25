"""Empirical NEET score distribution and coaching / privilege score shifts.

Scores are sampled from the processed national marks distribution, then shifted in
standard-deviation units. Arms-race comparisons subtract the population-mean shift so
that equal coaching leaves ranks unchanged while costs still rise.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "config" / "score_privilege_scenarios.yaml"


@dataclass(frozen=True)
class ScoreDistribution:
    """Piecewise-linear inverse CDF from empirical quantiles."""

    quantiles: np.ndarray
    marks: np.ndarray
    mean: float
    sd: float
    n_appeared: int
    source: str

    def sample(self, size: int, *, rng: np.random.Generator) -> np.ndarray:
        if size <= 0:
            raise ValueError("size must be positive")
        u = rng.random(size)
        return self.ppf(u)

    def ppf(self, u: np.ndarray) -> np.ndarray:
        u = np.clip(np.asarray(u, dtype=float), 0.0, 1.0)
        return np.interp(u, self.quantiles, self.marks)

    def cdf(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        return np.interp(x, self.marks, self.quantiles, left=0.0, right=1.0)


def load_score_config(path: Path | None = None) -> dict:
    cfg_path = DEFAULT_CONFIG if path is None else path
    with cfg_path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_score_distribution(
    *,
    config: dict | None = None,
    repo_root: Path | None = None,
) -> ScoreDistribution:
    root = REPO_ROOT if repo_root is None else repo_root
    cfg = config if config is not None else load_score_config()
    sc = cfg["score_distribution"]
    qpath = root / sc["quantiles_csv"]
    spath = root / sc["summary_csv"]
    qdf = pd.read_csv(qpath)
    quantiles = qdf["quantile"].to_numpy(dtype=float)
    marks = qdf["marks"].to_numpy(dtype=float)
    order = np.argsort(quantiles)
    quantiles, marks = quantiles[order], marks[order]

    mean = float(marks.mean())
    sd = float(marks.std())
    if spath.exists():
        summary = pd.read_csv(spath)
        by_metric = {
            str(m): v for m, v in zip(summary["metric"], summary["value"], strict=False)
        }
        if "mean_marks" in by_metric:
            try:
                mean = float(by_metric["mean_marks"])
            except (TypeError, ValueError):
                pass
        if "standard_deviation" in by_metric:
            try:
                sd = float(by_metric["standard_deviation"])
            except (TypeError, ValueError):
                pass

    return ScoreDistribution(
        quantiles=quantiles,
        marks=marks,
        mean=mean,
        sd=max(sd, 1e-6),
        n_appeared=int(sc["n_appeared"]),
        source=str(qpath.as_posix()),
    )


def _profile_params(config: dict, profile: str | None = None) -> dict:
    coach = config["coaching"]
    name = profile or coach["default_profile"]
    if name not in coach["profiles"]:
        raise ValueError(f"unknown coaching profile {name!r}")
    return coach["profiles"][name]


def coaching_components_sd(
    prep_intensity: str, config: dict, *, profile: str | None = None
) -> dict[str, float]:
    """Two-part coaching shift: any-prep jump θ + log2 intensity above median spend.

    δ = 1{S>0} * θ + 1{S>0} * β_doubling * log2(S / S_median)

    Intensity labels map to spend multiples of median (config). At the median,
    the intensity term is zero so modest prep = θ only.
    """

    coach = config["coaching"]
    params = _profile_params(config, profile)
    multiples = coach["intensity_spend_multiples_of_median"]
    if prep_intensity not in multiples:
        raise ValueError(f"unknown prep_intensity {prep_intensity!r}")

    # Backward compatibility: flat per-intensity tables (legacy configs).
    if "theta_any_prep_sd" not in params and prep_intensity in params:
        delta = float(params[prep_intensity])
        return {
            "theta_any_prep_sd": delta,
            "intensity_shift_sd": 0.0,
            "coaching_shift_sd": delta,
            "spend_multiple_of_median": float(multiples[prep_intensity]),
            "log2_spend_vs_median": 0.0,
        }

    theta = float(params["theta_any_prep_sd"])
    beta = float(params["beta_doubling_sd"])
    multiple = float(multiples[prep_intensity])
    if multiple <= 0.0:
        return {
            "theta_any_prep_sd": 0.0,
            "intensity_shift_sd": 0.0,
            "coaching_shift_sd": 0.0,
            "spend_multiple_of_median": 0.0,
            "log2_spend_vs_median": 0.0,
        }

    log2_ratio = float(np.log2(multiple))
    intensity = beta * log2_ratio
    return {
        "theta_any_prep_sd": theta,
        "intensity_shift_sd": intensity,
        "coaching_shift_sd": theta + intensity,
        "spend_multiple_of_median": multiple,
        "log2_spend_vs_median": log2_ratio,
    }


def coaching_shift_sd(prep_intensity: str, config: dict, *, profile: str | None = None) -> float:
    return float(coaching_components_sd(prep_intensity, config, profile=profile)["coaching_shift_sd"])


def population_mean_coaching_shift(config: dict, *, profile: str | None = None) -> float:
    mix = config["coaching"]["population_mix_for_arms_race"]
    return float(
        sum(float(w) * coaching_shift_sd(str(k), config, profile=profile) for k, w in mix.items())
    )


def arms_race_signatures(
    config: dict, *, profile: str | None = None
) -> dict[str, float]:
    """Private return vs positional externality under the relative-prep convention.

    β1_proxy: unilateral intensive vs none (absolute δ_intensive - δ_none).
    β2_proxy: -population mean δ (how much equal escalation cancels private gains).
    Arms-race signature: β1_proxy > 0 and β2_proxy < 0 under relative scoring.
    """

    delta_none = coaching_shift_sd("none", config, profile=profile)
    delta_intensive = coaching_shift_sd("intensive", config, profile=profile)
    delta_pop = population_mean_coaching_shift(config, profile=profile)
    return {
        "beta1_private_return_sd": delta_intensive - delta_none,
        "beta2_positional_externality_sd": -delta_pop,
        "population_mean_coaching_sd": delta_pop,
    }


def medium_shift_sd(school_medium: str, config: dict) -> float:
    table = config["medium_score_shift_sd"]
    if school_medium not in {"tamil", "english"}:
        raise ValueError(f"unknown school_medium {school_medium!r}")
    val = table[school_medium]
    return float(val)


def metro_shift_sd(metro_proximity: str, config: dict) -> float:
    table = config["metro_score_shift_sd"]
    if metro_proximity not in {"non_metro", "metro"}:
        raise ValueError(f"unknown metro_proximity {metro_proximity!r}")
    return float(table[metro_proximity])


def apply_score_shifts(
    baseline_marks: np.ndarray,
    *,
    dist: ScoreDistribution,
    school_medium: str,
    metro_proximity: str,
    prep_intensity: str,
    config: dict,
    coaching_profile: str | None = None,
    subtract_population_mean: bool = True,
    force_population_prep: str | None = None,
    force_all_prep: str | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Return shifted marks and the SD components used.

    ``force_all_prep``: both the focal candidate and the comparison population use that
    prep intensity (true universal-coaching world; relative coaching shift ≈ 0).

    ``force_population_prep`` alone: rivals escalate to that level while the focal
    candidate keeps ``prep_intensity`` (positional penalty / advantage).
    """

    if force_all_prep is not None and force_population_prep is not None:
        raise ValueError("set force_all_prep or force_population_prep, not both")

    effective_prep = force_all_prep if force_all_prep is not None else prep_intensity
    tau_m = medium_shift_sd(school_medium, config)
    tau_u = metro_shift_sd(metro_proximity, config)
    parts = coaching_components_sd(effective_prep, config, profile=coaching_profile)
    delta_i = float(parts["coaching_shift_sd"])
    if force_all_prep is not None:
        delta_pop = coaching_shift_sd(force_all_prep, config, profile=coaching_profile)
        delta_rel = delta_i - delta_pop
    elif force_population_prep is not None:
        delta_pop = coaching_shift_sd(force_population_prep, config, profile=coaching_profile)
        delta_rel = delta_i - delta_pop
    elif subtract_population_mean:
        delta_pop = population_mean_coaching_shift(config, profile=coaching_profile)
        delta_rel = delta_i - delta_pop
    else:
        delta_pop = 0.0
        delta_rel = delta_i

    total_sd = tau_m + tau_u + delta_rel
    shifted = baseline_marks + dist.sd * total_sd
    # NEET marks are bounded in practice.
    shifted = np.clip(shifted, float(dist.marks.min()), float(dist.marks.max()))
    signatures = arms_race_signatures(config, profile=coaching_profile)
    meta = {
        "medium_shift_sd": tau_m,
        "metro_shift_sd": tau_u,
        "theta_any_prep_sd": float(parts["theta_any_prep_sd"]),
        "intensity_shift_sd": float(parts["intensity_shift_sd"]),
        "coaching_shift_sd": delta_i,
        "population_coaching_shift_sd": delta_pop,
        "relative_coaching_shift_sd": delta_rel,
        "total_location_shift_sd": total_sd,
        "effective_prep_intensity": effective_prep,
        "force_all_prep": force_all_prep,
        "force_population_prep": force_population_prep,
        "beta1_private_return_sd": signatures["beta1_private_return_sd"],
        "beta2_positional_externality_sd": signatures["beta2_positional_externality_sd"],
    }
    return shifted, meta


def marks_to_percentile_rank(marks: np.ndarray, dist: ScoreDistribution) -> np.ndarray:
    """Higher marks => better (lower) rank percentile in [0, 1]."""

    # Empirical CDF of marks; top scorers have cdf near 1, rank percentile = 1 - cdf.
    cdf = dist.cdf(marks)
    return 1.0 - cdf


__all__ = [
    "ScoreDistribution",
    "apply_score_shifts",
    "coaching_shift_sd",
    "load_score_config",
    "load_score_distribution",
    "marks_to_percentile_rank",
    "medium_shift_sd",
    "metro_shift_sd",
    "population_mean_coaching_shift",
]
