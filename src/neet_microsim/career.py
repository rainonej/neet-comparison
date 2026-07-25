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
    mean_annual_earnings_if_employed: float
    median_annual_earnings_if_employed: float
    p10_annual_earnings_if_employed: float
    p90_annual_earnings_if_employed: float


def simulate_one_year(
    model: CareerPathModel,
    *,
    draws: int = 100_000,
    seed: int = 0,
) -> tuple[np.ndarray, CareerSimulationSummary, np.ndarray]:
    """Simulate one post-training year while propagating parameter uncertainty.

    Returns ``(earnings, summary, employed_mask)``.

    Earnings include zeros for non-completion, labor-force exit, and unemployment. Those zeros
    are an *employment filter*, not a claim of lifetime destitution: for highly educated young
    adults they often mean delayed independence / family support, not street poverty.

    Conditional-on-employment quantiles are reported separately in the summary.
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

    if employed.any():
        employed_earnings = earnings[employed]
        mean_if_emp = float(employed_earnings.mean())
        median_if_emp = float(np.median(employed_earnings))
        p10_if_emp = float(np.quantile(employed_earnings, 0.10))
        p90_if_emp = float(np.quantile(employed_earnings, 0.90))
    else:
        mean_if_emp = median_if_emp = p10_if_emp = p90_if_emp = float("nan")

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
        mean_annual_earnings_if_employed=mean_if_emp,
        median_annual_earnings_if_employed=median_if_emp,
        p10_annual_earnings_if_employed=p10_if_emp,
        p90_annual_earnings_if_employed=p90_if_emp,
    )
    return earnings, summary, employed



def earnings_quantiles(earnings: np.ndarray) -> dict[str, float]:
    """Return distribution summaries including a zero-earnings share."""

    if earnings.size == 0:
        return {
            "mean": float("nan"),
            "zero_share": float("nan"),
            "p0": float("nan"),
            "p10": float("nan"),
            "p25": float("nan"),
            "p50": float("nan"),
            "p75": float("nan"),
            "p90": float("nan"),
            "p99": float("nan"),
            "n": 0.0,
        }
    return {
        "mean": float(earnings.mean()),
        "zero_share": float((earnings == 0).mean()),
        "p0": float(np.quantile(earnings, 0.0)),
        "p10": float(np.quantile(earnings, 0.10)),
        "p25": float(np.quantile(earnings, 0.25)),
        "p50": float(np.quantile(earnings, 0.50)),
        "p75": float(np.quantile(earnings, 0.75)),
        "p90": float(np.quantile(earnings, 0.90)),
        "p99": float(np.quantile(earnings, 0.99)),
        "n": float(earnings.size),
    }


def histogram_shares(
    values: np.ndarray,
    *,
    edges: list[float],
) -> list[dict[str, float]]:
    """Return share of mass in each half-open bin [edges[i], edges[i+1])."""

    if len(edges) < 2:
        raise ValueError("edges must contain at least two values")
    if values.size == 0:
        return []
    counts, _ = np.histogram(values, bins=np.asarray(edges, dtype=float))
    shares = counts / values.size
    rows = []
    for index, share in enumerate(shares):
        rows.append(
            {
                "bin_left": float(edges[index]),
                "bin_right": float(edges[index + 1]),
                "share": float(share),
                "count": float(counts[index]),
            }
        )
    return rows


def kde_curve(
    values: np.ndarray,
    *,
    grid: np.ndarray | None = None,
    points: int = 80,
    lower: float | None = None,
    upper: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Gaussian KDE on positive earnings (zeros excluded).

    Histograms use coarse bins for display only; underlying Monte Carlo draws are continuous.
    Density is estimated on log-earnings and transformed back to the rupee scale.
    """

    from scipy.stats import gaussian_kde

    positive = values[values > 0]
    if positive.size < 5:
        raise ValueError("need at least five positive values for KDE")
    lo = float(positive.min() if lower is None else lower)
    hi = float(np.quantile(positive, 0.995) if upper is None else upper)
    if hi <= lo:
        hi = lo * 1.1 + 1.0
    xs = np.linspace(lo, hi, points) if grid is None else np.asarray(grid, dtype=float)
    kde = gaussian_kde(np.log(np.clip(positive, 1e-6, None)))
    log_dens = kde(np.log(np.clip(xs, 1e-6, None)))
    dens = log_dens / np.clip(xs, 1e-6, None)
    return xs, dens.astype(float)


def cdf_points(values: np.ndarray, *, grid_size: int = 41) -> tuple[np.ndarray, np.ndarray]:
    """Empirical CDF on a linear grid from min to max (or a zero-aware span)."""

    if grid_size < 2:
        raise ValueError("grid_size must be at least 2")
    if values.size == 0:
        raise ValueError("values must be non-empty")
    lo = float(np.min(values))
    hi = float(np.max(values))
    if hi <= lo:
        xs = np.array([lo, hi if hi > lo else lo + 1.0])
        ys = np.array([0.0, 1.0])
        return xs, ys
    xs = np.linspace(lo, hi, grid_size)
    sorted_vals = np.sort(values)
    ys = np.searchsorted(sorted_vals, xs, side="right") / values.size
    return xs, ys.astype(float)


def simulate_lifetime_npv(
    model: CareerPathModel,
    *,
    annual_education_cost: float,
    degree_years: float,
    working_years: int = 35,
    real_discount_rate: float = 0.03,
    age_earnings_growth_real: float = 0.015,
    prep_cost_total: float = 0.0,
    draws: int = 40_000,
    seed: int = 0,
) -> tuple[np.ndarray, dict[str, float]]:
    """Simulate lifetime NPV: upfront prep + training costs, then earnings path.

    Training years contribute negative cash flows (fees). After training, each draw samples one
    annual earnings level from ``simulate_one_year`` logic (parameter uncertainty + individual
    state) and grows it at a constant real rate. Zeros from non-completion / non-employment are
    retained for the whole career in that draw.
    """

    if annual_education_cost < 0 or prep_cost_total < 0:
        raise ValueError("costs cannot be negative")
    if degree_years < 0 or working_years <= 0:
        raise ValueError("degree_years must be non-negative and working_years positive")
    if draws <= 0:
        raise ValueError("draws must be positive")
    if real_discount_rate <= -1.0:
        raise ValueError("real_discount_rate must be greater than -1")

    base_earnings, _, _ = simulate_one_year(model, draws=draws, seed=seed)
    train_years = int(np.ceil(degree_years))
    n_flows = 1 + train_years + working_years
    years = np.arange(n_flows, dtype=float)
    discount = (1.0 + real_discount_rate) ** years

    # Flow template shared across draws except the earnings block.
    flow_template = np.zeros(n_flows, dtype=float)
    flow_template[0] = -prep_cost_total
    for year in range(train_years):
        if year + 1 > degree_years:
            fraction = degree_years - year
            flow_template[1 + year] = -annual_education_cost * fraction
        else:
            flow_template[1 + year] = -annual_education_cost

    growth = (1.0 + age_earnings_growth_real) ** np.arange(working_years, dtype=float)
    # earnings[d, t] = base[d] * growth[t]
    earnings_block = base_earnings[:, None] * growth[None, :]
    flows = np.broadcast_to(flow_template, (draws, n_flows)).copy()
    flows[:, 1 + train_years :] = earnings_block
    npvs = (flows / discount[None, :]).sum(axis=1)

    summary = earnings_quantiles(npvs)
    summary["path"] = model.name
    summary["real_discount_rate"] = real_discount_rate
    summary["working_years"] = float(working_years)
    summary["degree_years"] = float(degree_years)
    summary["annual_education_cost"] = float(annual_education_cost)
    summary["prep_cost_total"] = float(prep_cost_total)
    return npvs, summary
