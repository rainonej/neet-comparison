# Score → rank → seat privilege model

**Date:** 2026-07-25  
**Model version:** 0.5.0 (`config/score_privilege_scenarios.yaml`)  
**Reproduce:** `make score-privilege`

## The story

1. **Privilege and coaching shift latent NEET marks** (medium, metro knob, coaching SD priors).
2. **Scarce seats are allocated by rank** using national capacity accounting (govt-like / private-like seats ÷ appeared).
3. **Affordability** turns a private offer into an accessible seat.
4. **A seat widens earnings** versus same-background peers on no-seat mixtures (PLFS wages + field employment gates).

Mobility is real. Meritocracy-as-access is not.

## Why scores instead of direct \(P(\text{seat})\)

We have ~2.33M anonymized centre-level marks (no SES/coaching/domicile). Modeling the marks distribution lets small coaching shifts matter near cutoffs and makes the arms race visible: if everyone coaches the same amount, **relative ranks do not move**.

## Arms race

Scenario `unilateral` subtracts the population-mean coaching shift.  
Scenarios `everyone_modest` / `everyone_intensive` force the whole population to the same prep intensity so relative coaching advantage collapses — the classic positional arms race.

## Data used

| Piece | Source |
|---|---|
| Marks distribution | `neet_2024_marks_quantiles.csv` |
| Capacity | NMC govt/private-like seat counts |
| Coaching SD priors | Dongre-style proxy grid in config |
| Medium shifts | Calibrated toward TN Rajan associations |
| Career returns | PLFS wage anchors + `plfs_field_employment.csv` |
| Coaching participation context | NSS Education / CMSE aggregates (priors docs) |

## Artifacts

Written under `data/processed/bayesian/`:

- `score_access_by_stratum.csv`
- `score_marks_histograms.csv`
- `score_earnings_histograms.csv`
- `score_inequality_story.json`

## Warnings

- National seats/appeared cutoffs ≠ state/category counselling pools.
- Medium shifts are not national causal English effects.
- Coaching SD shifts are not NEET LATEs.
- Causal language for scenario contrasts is prohibited.
