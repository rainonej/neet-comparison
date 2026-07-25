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


def coaching_shift_sd(prep_intensity: str, config: dict, *, profile: str | None = None) -> float:
    coach = config["coaching"]
    name = profile or coach["default_profile"]
    table = coach["profiles"][name]
    if prep_intensity not in table:
        raise ValueError(f"unknown prep_intensity {prep_intensity!r}")
    return float(table[prep_intensity])


def population_mean_coaching_shift(config: dict, *, profile: str | None = None) -> float:
    mix = config["coaching"]["population_mix_for_arms_race"]
    return float(
        sum(float(w) * coaching_shift_sd(str(k), config, profile=profile) for k, w in mix.items())
    )


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
) -> tuple[np.ndarray, dict[str, float]]:
    """Return shifted marks and the SD components used."""

    tau_m = medium_shift_sd(school_medium, config)
    tau_u = metro_shift_sd(metro_proximity, config)
    delta_i = coaching_shift_sd(prep_intensity, config, profile=coaching_profile)
    if force_population_prep is not None:
        # Individual still labeled by prep_intensity for cost accounting; relative shift uses forced pop.
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
    meta = {
        "medium_shift_sd": tau_m,
        "metro_shift_sd": tau_u,
        "coaching_shift_sd": delta_i,
        "population_coaching_shift_sd": delta_pop,
        "relative_coaching_shift_sd": delta_rel,
        "total_location_shift_sd": total_sd,
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
