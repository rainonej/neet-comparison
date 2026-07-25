"""Bayesian employment and earnings model for physician and alternative career paths."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .bayes import BetaEvidence


@dataclass(frozen=True)
class LogNormalEarnings:
    """Conditional annual earnings distribution in rupees.

    Parameters are on the natural-log scale and describe people who are employed in the indicated
    employment state.  Zero earnings from unemployment or labor-force exit are generated outside
    this distribution.
    """

    log_mean: float
    log_sd: float
    label: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        if self.log_sd <= 0:
            raise ValueError("log_sd must be positive")

    @classmethod
    def from_median_and_geometric_sd(
        cls,
        median: float,
        geometric_sd: float,
        *,
        label: str = "",
        source: str = "",
    ) -> "LogNormalEarnings":
        if median <= 0:
            raise ValueError("median must be positive")
        if geometric_sd <= 1:
            raise ValueError("geometric_sd must be greater than one")
        return cls(
            log_mean=float(np.log(median)),
            log_sd=float(np.log(geometric_sd)),
            label=label,
            source=source,
        )

    @property
    def mean(self) -> float:
        return float(np.exp(self.log_mean + 0.5 * self.log_sd**2))

    def sample(self, size: int, *, rng: np.random.Generator) -> np.ndarray:
        if size <= 0:
            raise ValueError("size must be positive")
        return rng.lognormal(self.log_mean, self.log_sd, size=size)


@dataclass(frozen=True)
class CareerPathModel:
    """Sequential probability model for a degree or occupational path.

    Separating these gates prevents a salary table among employed workers from being misread as the
    expected outcome for everyone who starts the degree.
    """

    name: str
    completion: BetaEvidence
    labor_force_participation: BetaEvidence
    employment_given_labor_force: BetaEvidence
    matched_job_given_employed: BetaEvidence
    formal_job_given_employed: BetaEvidence
    matched_earnings: LogNormalEarnings
    unmatched_earnings: LogNormalEarnings

    def plug_in_expected_annual_earnings(self) -> float:
        """Posterior-mean annual earnings including non-completion and non-employment."""

        mean_employed_wage = (
            self.matched_job_given_employed.mean * self.matched_earnings.mean
            + (1.0 - self.matched_job_given_employed.mean) * self.unmatched_earnings.mean
        )
        return (
            self.completion.mean
            * self.labor_force_participation.mean
            * self.employment_given_labor_force.mean
            * mean_employed_wage
        )


@dataclass(frozen=True)
class CareerSimulationSummary:
    path: str
    probability_degree_completed: float
    probability_in_labor_force: float
    probability_employed: float
    probability_field_matched: float
    probability_formal_employment: float
    mean_annual_earnings: float
    median_annual_earnings: float
    probability_zero_earnings: float
    p10_annual_earnings: float
    p90_annual_earnings: float


def simulate_one_year(
    model: CareerPathModel,
    *,
    draws: int = 100_000,
    seed: int = 0,
) -> tuple[np.ndarray, CareerSimulationSummary]:
    """Simulate one post-training year while propagating parameter uncertainty.

    Each draw samples population probabilities from their posterior and then samples an individual
    state.  The resulting earnings distribution therefore includes zeros for non-completion,
    labor-force exit, and unemployment.
    """

    if draws <= 0:
        raise ValueError("draws must be positive")
    rng = np.random.default_rng(seed)

    p_complete = model.completion.sample(draws, rng=rng)
    completed = rng.random(draws) < p_complete

    p_lfp = model.labor_force_participation.sample(draws, rng=rng)
    in_labor_force = completed & (rng.random(draws) < p_lfp)

    p_employed = model.employment_given_labor_force.sample(draws, rng=rng)
    employed = in_labor_force & (rng.random(draws) < p_employed)

    p_match = model.matched_job_given_employed.sample(draws, rng=rng)
    matched = employed & (rng.random(draws) < p_match)

    p_formal = model.formal_job_given_employed.sample(draws, rng=rng)
    formal = employed & (rng.random(draws) < p_formal)

    earnings = np.zeros(draws, dtype=float)
    matched_count = int(matched.sum())
    unmatched = employed & ~matched
    unmatched_count = int(unmatched.sum())
    if matched_count:
        earnings[matched] = model.matched_earnings.sample(matched_count, rng=rng)
    if unmatched_count:
        earnings[unmatched] = model.unmatched_earnings.sample(unmatched_count, rng=rng)

    summary = CareerSimulationSummary(
        path=model.name,
        probability_degree_completed=float(completed.mean()),
        probability_in_labor_force=float(in_labor_force.mean()),
        probability_employed=float(employed.mean()),
        probability_field_matched=float(matched.mean()),
        probability_formal_employment=float(formal.mean()),
        mean_annual_earnings=float(earnings.mean()),
        median_annual_earnings=float(np.median(earnings)),
        probability_zero_earnings=float((earnings == 0).mean()),
        p10_annual_earnings=float(np.quantile(earnings, 0.10)),
        p90_annual_earnings=float(np.quantile(earnings, 0.90)),
    )
    return earnings, summary
