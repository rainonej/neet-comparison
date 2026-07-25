"""Small, auditable primitives for the baseline model.

These functions implement accounting and the explicitly requested independence workaround.
They do not contain fitted NEET admission coefficients.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import prod
from typing import Iterable, Mapping


def _validate_probability(value: float, *, name: str) -> None:
    if not 0.0 < value < 1.0:
        raise ValueError(f"{name} must lie strictly between 0 and 1; received {value!r}")


def _odds(probability: float) -> float:
    return probability / (1.0 - probability)


def _probability(odds: float) -> float:
    return odds / (1.0 + odds)


def combine_independent_marginal_rates(
    base_rate: float,
    marginal_rates: Mapping[str, float],
) -> float:
    """Combine separate outcome marginals under conditional independence.

    Each marginal contributes its odds ratio relative to the same base rate. An empty mapping
    returns the base rate. This is a transparent naive-Bayes-style approximation and must not be
    presented as an empirically observed joint probability.
    """

    _validate_probability(base_rate, name="base_rate")
    if not marginal_rates:
        return base_rate
    for name, rate in marginal_rates.items():
        _validate_probability(rate, name=f"marginal_rates[{name!r}]")

    base_odds = _odds(base_rate)
    evidence_ratios = [_odds(rate) / base_odds for rate in marginal_rates.values()]
    combined_odds = base_odds * prod(evidence_ratios)
    return _probability(combined_odds)


@dataclass(frozen=True)
class AttemptCost:
    """Direct incremental family cost for one examination attempt."""

    exam_fee: float = 0.0
    travel: float = 0.0
    lodging: float = 0.0
    materials: float = 0.0
    coaching: float = 0.0
    relocation: float = 0.0
    extra_living: float = 0.0

    @property
    def total(self) -> float:
        values = (
            self.exam_fee,
            self.travel,
            self.lodging,
            self.materials,
            self.coaching,
            self.relocation,
            self.extra_living,
        )
        if any(value < 0 for value in values):
            raise ValueError("Cost components cannot be negative")
        return sum(values)

    def burden_share(self, annual_household_resources: float) -> float:
        if annual_household_resources <= 0:
            raise ValueError("annual_household_resources must be positive")
        return self.total / annual_household_resources


def repeat_year_cost(
    attempt: AttemptCost,
    *,
    delayed_earnings: float = 0.0,
    foregone_education_subsidy: float = 0.0,
) -> float:
    """Return a scenario-specific repeat-year cost.

    ``delayed_earnings`` should reflect the chosen counterfactual. It may be zero when the student
    would otherwise have remained out of work. The function does not assume one year of salary.
    """

    if delayed_earnings < 0 or foregone_education_subsidy < 0:
        raise ValueError("Opportunity-cost components cannot be negative")
    return attempt.total + delayed_earnings + foregone_education_subsidy


def discounted_cash_flow(
    annual_flows: Iterable[float],
    *,
    real_discount_rate: float,
) -> float:
    """Calculate net present value for annual cash flows beginning at year zero."""

    if real_discount_rate <= -1.0:
        raise ValueError("real_discount_rate must be greater than -1")
    return sum(
        flow / ((1.0 + real_discount_rate) ** year)
        for year, flow in enumerate(annual_flows)
    )
