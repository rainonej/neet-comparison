"""Load and materialize Bayesian prior profiles from config/bayesian_priors.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .bayes import TruncatedNormalEvidence, beta_from_mean_ess

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRIOR_PATH = REPO_ROOT / "config" / "bayesian_priors.yaml"

PROFILE_NAMES = ("neutral", "conservative", "reasonable")


@dataclass(frozen=True)
class PriorProfile:
    name: str
    binary_ess: float
    binary_mean_fallback: float
    log_odds_mean: float
    log_odds_sd: float
    coaching_shift: TruncatedNormalEvidence


def load_prior_config(path: Path | None = None) -> dict[str, Any]:
    config_path = DEFAULT_PRIOR_PATH if path is None else path
    with config_path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def materialize_profile(name: str, config: dict[str, Any] | None = None) -> PriorProfile:
    if name not in PROFILE_NAMES:
        raise ValueError(f"unknown prior profile {name!r}; expected one of {PROFILE_NAMES}")
    cfg = config if config is not None else load_prior_config()
    block = cfg["prior_profiles"][name]
    binary = block["binary_probability"]
    log_odds = block["log_odds_effect"]
    coaching = block["coaching_score_shift_sd"]
    mean = float(binary.get("mean", 0.50))
    return PriorProfile(
        name=name,
        binary_ess=float(binary["effective_sample_size"]),
        binary_mean_fallback=mean,
        log_odds_mean=float(log_odds["mean"]),
        log_odds_sd=float(log_odds["sd"]),
        coaching_shift=TruncatedNormalEvidence(
            mean=float(coaching["mean"]),
            sd=float(coaching["sd"]),
            lower=float(coaching["lower"]),
            upper=float(coaching["upper"]),
            label=f"{name}_coaching_score_shift_sd",
            source="config/bayesian_priors.yaml",
            evidence_class="prior",
        ),
    )


def binary_prior(
    profile: PriorProfile,
    *,
    center: float | None = None,
    label: str,
    source: str = "config/bayesian_priors.yaml",
):
    """Beta prior centered on a broad benchmark or the profile fallback."""

    mean = profile.binary_mean_fallback if center is None else center
    # Keep Beta support strictly inside (0, 1).
    mean = min(max(mean, 1e-4), 1.0 - 1e-4)
    return beta_from_mean_ess(
        mean,
        profile.binary_ess,
        label=label,
        source=source,
        evidence_class="prior",
    )
