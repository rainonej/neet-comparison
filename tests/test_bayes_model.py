"""Tests for Bayesian primitives and the end-to-end evidence model."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from neet_microsim.bayes import (
    BetaEvidence,
    DirichletEvidence,
    TruncatedNormalEvidence,
    beta_from_mean_ess,
    partial_pool_beta,
    shrinkage_weight,
)
from neet_microsim.model import (
    coaching_ppc_table,
    fit_all_profiles,
    fit_profile,
    posterior_summary_table,
    profile_comparison_table,
    run_bayesian_pipeline,
)
from neet_microsim.priors import PROFILE_NAMES, materialize_profile

REPO = Path(__file__).resolve().parents[1]
PROCESSED = REPO / "data" / "processed"


def test_beta_update_and_interval() -> None:
    prior = beta_from_mean_ess(0.5, 2, label="toy")
    posterior = prior.update_binomial(successes=3, trials=10)
    assert posterior.mean == pytest.approx(4 / 12)
    low, high = posterior.credible_interval()
    assert 0.0 < low < posterior.mean < high < 1.0


def test_partial_pool_shrinks_toward_parent() -> None:
    parent = beta_from_mean_ess(0.70, 20)
    child = partial_pool_beta(parent, child_successes=1, child_trials=2)
    assert parent.mean > child.mean > (1 / 2)
    assert shrinkage_weight(20, 2) == pytest.approx(20 / 22)


def test_dirichlet_and_truncated_normal_sample() -> None:
    rng = np.random.default_rng(0)
    mix = DirichletEvidence({"a": 2.0, "b": 2.0, "c": 2.0})
    draws = mix.sample(5000, rng=rng)
    assert set(draws) == {"a", "b", "c"}
    assert abs(float(draws["a"].mean()) - mix.mean["a"]) < 0.05
    shift = TruncatedNormalEvidence(mean=0.1, sd=0.05, lower=-0.05, upper=0.4)
    samples = shift.sample(3000, rng=rng)
    assert samples.min() >= -0.05
    assert samples.max() <= 0.4


def test_prior_profiles_load() -> None:
    for name in PROFILE_NAMES:
        profile = materialize_profile(name)
        assert profile.binary_ess > 0
        assert profile.coaching_shift.upper > profile.coaching_shift.lower


@pytest.mark.skipif(
    not (PROCESSED / "published_estimates.csv").exists(),
    reason="processed evidence not available",
)
def test_fit_profiles_and_pipeline(tmp_path: Path) -> None:
    fits = fit_all_profiles(processed=PROCESSED)
    assert [fit.profile for fit in fits] == list(PROFILE_NAMES)

    conservative = next(fit for fit in fits if fit.profile == "conservative")
    # Complete national qualify counts dominate any weak prior.
    assert conservative.qualify_rate.mean == pytest.approx(1315853 / 2333162, rel=1e-4)
    assert 0.04 < conservative.mbbs_capacity_rate.mean < 0.08
    assert conservative.tn_govt_english_post.mean > conservative.tn_govt_tamil_post.mean
    assert conservative.medium_rate_ratio_post > 1.5

    # Coaching cohorts must not update the coaching prior object identity/parameters.
    neutral = fit_profile("neutral", processed=PROCESSED)
    reasonable = fit_profile("reasonable", processed=PROCESSED)
    assert neutral.coaching_score_shift.mean == pytest.approx(0.0)
    assert reasonable.coaching_score_shift.mean > conservative.coaching_score_shift.mean

    summary = posterior_summary_table(fits)
    comparison = profile_comparison_table(fits, draws=2_000, seed=1)
    ppc = coaching_ppc_table(fits, processed=PROCESSED, draws=2_000)
    assert not summary.empty
    assert set(comparison["profile"]) == set(PROFILE_NAMES)
    assert ppc["used_to_update_coaching_effect"].eq(False).all()
    # Selected intensive programs should sit above national qualify rate.
    secl = ppc.loc[
        (ppc["evidence_id"] == "secl_sushrut_2023_24") & (ppc["outcome"] == "neet_qualified")
    ]
    assert (secl["observed_minus_predicted"] > 0.3).all()

    paths = run_bayesian_pipeline(
        processed=PROCESSED,
        output_dir=tmp_path / "bayesian",
        draws=1_500,
    )
    for path in paths.values():
        assert path.exists()
        assert path.stat().st_size > 0


def test_beta_evidence_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError):
        BetaEvidence(alpha=0.0, beta=1.0)
    prior = beta_from_mean_ess(0.4, 4)
    with pytest.raises(ValueError):
        prior.update_binomial(successes=5, trials=3)
