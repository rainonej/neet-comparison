"""Continuation-rate priors for NEET sittings (sensitivity, not national estimates).

Maps labeled r_t = P(sit again | reached sitting t) into a distribution over
total sittings. See docs/ATTEMPT_PRIORS.md and config/attempt_priors.yaml.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO / "config" / "attempt_priors.yaml"


def load_attempt_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or DEFAULT_CONFIG
    with cfg_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def sitting_distribution(
    continuation: dict[str, float],
    *,
    max_sit: int = 8,
) -> dict[str, float]:
    """P(total sittings = k) from continuation rates after each sitting.

    continuation keys: after_1, after_2, after_3, after_4_plus
    """

    def r(t: int) -> float:
        if t <= 1:
            return float(continuation["after_1"])
        if t == 2:
            return float(continuation["after_2"])
        if t == 3:
            return float(continuation["after_3"])
        return float(continuation["after_4_plus"])

    for t in range(1, 5):
        q = r(t)
        if not 0.0 <= q <= 1.0:
            raise ValueError(f"continuation rate out of [0,1]: sitting {t} -> {q}")

    # Survival to sitting k: product of continuations after 1..k-1
    probs: dict[int, float] = {}
    survive = 1.0  # probability of reaching sitting 1
    for k in range(1, max_sit + 1):
        if k < max_sit:
            stop = 1.0 - r(k)
            probs[k] = survive * stop
            survive *= r(k)
        else:
            probs[k] = survive  # absorb remaining mass at max_sit

    total = sum(probs.values())
    if total <= 0:
        raise ValueError("degenerate sitting distribution")
    return {str(k): probs[k] / total for k in range(1, max_sit + 1)}


def mean_sittings(dist: dict[str, float]) -> float:
    return sum(int(k) * p for k, p in dist.items())


def scenario_table(cfg: dict[str, Any] | None = None) -> pd.DataFrame:
    cfg = cfg or load_attempt_config()
    rows = []
    for sid, sc in cfg["scenarios"].items():
        dist = sitting_distribution(sc["continuation"])
        row: dict[str, Any] = {
            "scenario_id": sid,
            "label": sc["label"],
            "r_after_1": sc["continuation"]["after_1"],
            "r_after_2": sc["continuation"]["after_2"],
            "r_after_3": sc["continuation"]["after_3"],
            "r_after_4_plus": sc["continuation"]["after_4_plus"],
            "mean_sittings": mean_sittings(dist),
            "p_sit_1": dist["1"],
            "p_sit_2": dist["2"],
            "p_sit_3": dist["3"],
            "p_sit_4": dist["4"],
            "p_sit_5_plus": sum(dist[str(k)] for k in range(5, 9)),
            "is_national_estimate": False,
            "success_exit": cfg.get("success_exit"),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def sitting_distribution_long(cfg: dict[str, Any] | None = None) -> pd.DataFrame:
    cfg = cfg or load_attempt_config()
    rows = []
    for sid, sc in cfg["scenarios"].items():
        dist = sitting_distribution(sc["continuation"])
        for k, p in dist.items():
            rows.append(
                {
                    "scenario_id": sid,
                    "label": sc["label"],
                    "total_sittings": int(k),
                    "probability": p,
                    "is_national_estimate": False,
                }
            )
    return pd.DataFrame(rows)


def resource_runway(
    *,
    liquid: float,
    expected_disposable_1y: float,
    borrowing_capacity: float,
    repeat_year_burden: float,
    illiquid_wealth: float = 0.0,
    illiquid_pledgeable_share: float = 0.0,
) -> float:
    """log((liquid + disposable + borrow + pledgeable illiquid) / burden)."""

    if repeat_year_burden <= 0:
        raise ValueError("repeat_year_burden must be positive")
    if not 0.0 <= illiquid_pledgeable_share <= 1.0:
        raise ValueError("illiquid_pledgeable_share must lie in [0, 1]")
    resources = (
        liquid
        + expected_disposable_1y
        + borrowing_capacity
        + illiquid_wealth * illiquid_pledgeable_share
    )
    if resources <= 0:
        return float("-inf")
    return math.log(resources / repeat_year_burden)


def beta_prior_means(cfg: dict[str, Any] | None = None) -> dict[str, float]:
    cfg = cfg or load_attempt_config()
    out = {}
    for key, ab in cfg["beta_priors"].items():
        a, b = float(ab["alpha"]), float(ab["beta"])
        out[key] = a / (a + b)
    return out


def write_attempt_prior_artifacts(
    out_dir: Path | None = None,
    cfg_path: Path | None = None,
) -> dict[str, Path]:
    cfg = load_attempt_config(cfg_path)
    out = out_dir or (REPO / "data" / "processed" / "bayesian")
    out.mkdir(parents=True, exist_ok=True)

    scenarios = scenario_table(cfg)
    long = sitting_distribution_long(cfg)
    scen_path = out / "attempt_continuation_scenarios.csv"
    dist_path = out / "attempt_sitting_distributions.csv"
    scenarios.to_csv(scen_path, index=False)
    long.to_csv(dist_path, index=False)

    summary = {
        "model_version": cfg.get("model_version"),
        "success_exit": cfg.get("success_exit"),
        "beta_prior_means": beta_prior_means(cfg),
        "scenarios": scenarios.to_dict(orient="records"),
        "warnings": cfg.get("warnings", []),
        "note": (
            "Labeled continuation sensitivity for simulation. "
            "Not a measured national NEET attempt distribution."
        ),
    }
    json_path = out / "attempt_priors_summary.json"
    import json

    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return {
        "attempt_continuation_scenarios": scen_path,
        "attempt_sitting_distributions": dist_path,
        "attempt_priors_summary": json_path,
    }
