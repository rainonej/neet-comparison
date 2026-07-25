"""Small Bayesian evidence primitives for the NEET microsimulation.

The project has many partial aggregate statistics and very few linked individual records.  This
module therefore favors transparent conjugate models that can be inspected, updated, and stress-
tested without requiring a large probabilistic-programming runtime.

These distributions are epistemic: they represent uncertainty about population probabilities and
mixture weights.  They are not individual psychological or clinical risk predictions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
from scipy.stats import beta as beta_dist
from scipy.stats import truncnorm


def _validate_probability(value: float, *, name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must lie in [0, 1]; received {value!r}")


@dataclass(frozen=True)
class BetaEvidence:
    """Beta distribution for a binary probability with provenance.

    ``effective_sample_size`` is ``alpha + beta``.  For a literal binomial sample it can be the
    prior pseudo-count plus the observed denominator.  For a borrowed proxy or published marginal,
    it should be deliberately much smaller than the source's nominal sample size.
    """

    alpha: float
    beta: float
    label: str = ""
    source: str = ""
    evidence_class: str = "unspecified"

    def __post_init__(self) -> None:
        if self.alpha <= 0 or self.beta <= 0:
            raise ValueError("alpha and beta must be positive")

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def effective_sample_size(self) -> float:
        return self.alpha + self.beta

    @property
    def variance(self) -> float:
        total = self.alpha + self.beta
        return (self.alpha * self.beta) / (total * total * (total + 1.0))

    def credible_interval(self, mass: float = 0.95) -> tuple[float, float]:
        if not 0.0 < mass < 1.0:
            raise ValueError("mass must lie strictly between zero and one")
        tail = (1.0 - mass) / 2.0
        return (
            float(beta_dist.ppf(tail, self.alpha, self.beta)),
            float(beta_dist.ppf(1.0 - tail, self.alpha, self.beta)),
        )

    def update_binomial(
        self,
        *,
        successes: float,
        trials: float,
        evidence_weight: float = 1.0,
        label: str | None = None,
        source: str | None = None,
        evidence_class: str | None = None,
    ) -> "BetaEvidence":
        """Update with integer or fractional binomial evidence.

        ``evidence_weight`` permits survey-effective sample sizes or explicit down-weighting of a
        non-comparable proxy.  It must never be chosen solely to make the desired answer appear.
        """

        if trials < 0 or successes < 0 or successes > trials:
            raise ValueError("successes must lie between zero and trials")
        if evidence_weight < 0:
            raise ValueError("evidence_weight cannot be negative")
        failures = trials - successes
        return BetaEvidence(
            alpha=self.alpha + evidence_weight * successes,
            beta=self.beta + evidence_weight * failures,
            label=self.label if label is None else label,
            source=self.source if source is None else source,
            evidence_class=self.evidence_class if evidence_class is None else evidence_class,
        )

    def sample(self, size: int, *, rng: np.random.Generator) -> np.ndarray:
        if size <= 0:
            raise ValueError("size must be positive")
        return rng.beta(self.alpha, self.beta, size=size)


def beta_from_mean_ess(
    mean: float,
    effective_sample_size: float,
    *,
    label: str = "",
    source: str = "",
    evidence_class: str = "prior",
) -> BetaEvidence:
    """Construct a Beta distribution from a mean and effective sample size."""

    if not 0.0 < mean < 1.0:
        raise ValueError("mean must lie strictly between zero and one")
    if effective_sample_size <= 0:
        raise ValueError("effective_sample_size must be positive")
    return BetaEvidence(
        alpha=mean * effective_sample_size,
        beta=(1.0 - mean) * effective_sample_size,
        label=label,
        source=source,
        evidence_class=evidence_class,
    )


def partial_pool_beta(
    parent: BetaEvidence,
    *,
    child_successes: float = 0.0,
    child_trials: float = 0.0,
    child_evidence_weight: float = 1.0,
    label: str = "",
    source: str = "",
    evidence_class: str = "hierarchical",
) -> BetaEvidence:
    """Shrink a child cell toward a parent Beta using a conjugate update.

    With no child evidence this returns a copy of the parent (re-labeled). Observed support and
    parent ESS jointly determine the degree of shrinkage.
    """

    if child_trials < 0 or child_successes < 0 or child_successes > child_trials:
        raise ValueError("child_successes must lie between zero and child_trials")
    if child_evidence_weight < 0:
        raise ValueError("child_evidence_weight cannot be negative")
    if child_trials == 0:
        return BetaEvidence(
            alpha=parent.alpha,
            beta=parent.beta,
            label=label or parent.label,
            source=source or parent.source,
            evidence_class=evidence_class,
        )
    return parent.update_binomial(
        successes=child_successes,
        trials=child_trials,
        evidence_weight=child_evidence_weight,
        label=label or parent.label,
        source=source or parent.source,
        evidence_class=evidence_class,
    )


def shrinkage_weight(parent_ess: float, child_ess: float) -> float:
    """Fraction of posterior mean attributable to the parent, in [0, 1]."""

    if parent_ess < 0 or child_ess < 0:
        raise ValueError("ESS values cannot be negative")
    total = parent_ess + child_ess
    if total == 0:
        raise ValueError("at least one ESS must be positive")
    return parent_ess / total


@dataclass(frozen=True)
class DirichletEvidence:
    """Dirichlet distribution for alternative-path or employment-state mixtures."""

    alpha: Mapping[str, float]
    label: str = ""
    source: str = ""
    evidence_class: str = "unspecified"

    def __post_init__(self) -> None:
        if not self.alpha:
            raise ValueError("alpha must contain at least one category")
        if any(value <= 0 for value in self.alpha.values()):
            raise ValueError("all Dirichlet concentration parameters must be positive")

    @property
    def effective_sample_size(self) -> float:
        return float(sum(self.alpha.values()))

    @property
    def mean(self) -> dict[str, float]:
        total = self.effective_sample_size
        return {key: value / total for key, value in self.alpha.items()}

    def update_counts(
        self,
        counts: Mapping[str, float],
        *,
        evidence_weight: float = 1.0,
    ) -> "DirichletEvidence":
        if evidence_weight < 0:
            raise ValueError("evidence_weight cannot be negative")
        unknown = set(counts) - set(self.alpha)
        if unknown:
            raise ValueError(f"unknown categories: {sorted(unknown)}")
        if any(value < 0 for value in counts.values()):
            raise ValueError("counts cannot be negative")
        updated = {
            key: value + evidence_weight * counts.get(key, 0.0)
            for key, value in self.alpha.items()
        }
        return DirichletEvidence(
            updated,
            label=self.label,
            source=self.source,
            evidence_class=self.evidence_class,
        )

    def sample(self, size: int, *, rng: np.random.Generator) -> dict[str, np.ndarray]:
        if size <= 0:
            raise ValueError("size must be positive")
        keys = list(self.alpha)
        matrix = rng.dirichlet([self.alpha[key] for key in keys], size=size)
        return {key: matrix[:, index] for index, key in enumerate(keys)}


@dataclass(frozen=True)
class TruncatedNormalEvidence:
    """A bounded Normal prior, useful for score shifts and log-odds effects."""

    mean: float
    sd: float
    lower: float
    upper: float
    label: str = ""
    source: str = ""
    evidence_class: str = "prior"

    def __post_init__(self) -> None:
        if self.sd <= 0:
            raise ValueError("sd must be positive")
        if self.lower >= self.upper:
            raise ValueError("lower must be less than upper")

    def sample(self, size: int, *, rng: np.random.Generator) -> np.ndarray:
        if size <= 0:
            raise ValueError("size must be positive")
        a = (self.lower - self.mean) / self.sd
        b = (self.upper - self.mean) / self.sd
        return truncnorm.rvs(
            a,
            b,
            loc=self.mean,
            scale=self.sd,
            size=size,
            random_state=rng,
        )
