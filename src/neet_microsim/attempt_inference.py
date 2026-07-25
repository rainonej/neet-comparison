"""Infer applicant repeater share from admitted composition under labeled assumptions.

We observe P(repeater | admitted) from Tamil Nadu Rajan Committee figures. That does **not**
equal P(repeater | applicant) unless admission chances are independent of attempt history.

Let:
  r = P(repeater | admitted)          # observed among winners
  a = P(repeater | applicant)         # unknown
  ρ = P(admit | repeater) / P(admit | first-attempt)   # relative admission probability

Then:
  r = ρ a / (ρ a + (1 - a))
  a = r / (r + ρ (1 - r))

ρ = 1 recovers a = r (independence). ρ > 1 means repeaters are more likely to get seats, so the
applicant pool can have *fewer* repeaters than the admitted pool.

This does **not** identify the full distribution of attempt counts (1, 2, 3, …) without much
stronger structure. We only recover the first-attempt vs repeater (attempt ≥ 2) split under ρ.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# Observed among admitted (Tamil Nadu ordinary-quota reporting year).
RAJAN_REPEATER_SHARE_AMONG_ADMITTED = 0.7142
RAJAN_SOURCE = (
    "Justice A.K. Rajan Committee 2021: 71.42% of admitted students were repeaters (2020-21); "
    "admitted denominator only"
)


@dataclass(frozen=True)
class RepeaterInferenceRow:
    relative_admit_prob_repeater_over_first: float
    p_repeater_among_admitted: float
    p_repeater_among_applicants: float
    p_first_attempt_among_applicants: float
    interpretation: str


def applicant_repeater_share(
    *,
    p_repeater_among_admitted: float = RAJAN_REPEATER_SHARE_AMONG_ADMITTED,
    relative_admit_prob: float,
) -> float:
    """Back out P(repeater | applicant) given relative admission probability ρ."""

    if not 0.0 < p_repeater_among_admitted < 1.0:
        raise ValueError("p_repeater_among_admitted must lie in (0, 1)")
    if relative_admit_prob <= 0:
        raise ValueError("relative_admit_prob must be positive")
    r = p_repeater_among_admitted
    rho = relative_admit_prob
    return r / (r + rho * (1.0 - r))


def repeater_sensitivity_table(
    *,
    p_repeater_among_admitted: float = RAJAN_REPEATER_SHARE_AMONG_ADMITTED,
    relative_admit_probs: tuple[float, ...] = (0.5, 1.0, 1.5, 1.75, 2.0, 3.0, 4.0),
) -> pd.DataFrame:
    """Sensitivity of applicant repeater share to ρ = P(admit|rep) / P(admit|first).

    Includes 1.75 so the UI default can match the TN first/repeater-anchored scenario.
    """

    rows: list[dict[str, float | str]] = []
    for rho in relative_admit_probs:
        a = applicant_repeater_share(
            p_repeater_among_admitted=p_repeater_among_admitted,
            relative_admit_prob=rho,
        )
        if abs(rho - 1.0) < 1e-12:
            note = "independence: applicant repeater share equals admitted share"
        elif rho > 1:
            note = "repeaters more likely to get seats => fewer repeaters among applicants than among admitted"
        else:
            note = "first-timers more likely to get seats => more repeaters among applicants than among admitted"
        rows.append(
            {
                "p_repeater_among_admitted": p_repeater_among_admitted,
                "relative_admit_prob_repeater_over_first": rho,
                "p_repeater_among_applicants": a,
                "p_first_attempt_among_applicants": 1.0 - a,
                "source": RAJAN_SOURCE,
                "interpretation": note,
                "identifies_full_attempt_count_distribution": False,
            }
        )
    return pd.DataFrame(rows)
