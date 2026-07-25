# Score → rank → seat privilege model

**Date:** 2026-07-25  
**Model version:** 0.5.1 (`config/score_privilege_scenarios.yaml`)  
**Reproduce:** `make score-privilege`

## The story

1. **Privilege and coaching shift latent NEET marks** (medium, metro knob, two-part coaching priors).
2. **Scarce seats are allocated by rank** using national capacity accounting (govt-like / private-like seats ÷ appeared).
3. **Affordability** turns a private offer into an accessible seat.
4. **A seat widens earnings** versus same-background peers on no-seat mixtures (PLFS wages + field employment gates).

Mobility is real. Meritocracy-as-access is not.

## Why scores instead of direct \(P(\text{seat})\)

We have ~2.33M anonymized centre-level marks (no SES/coaching/domicile). Modeling the marks distribution lets small coaching shifts matter near cutoffs and makes the arms race visible: if everyone coaches the same amount, **relative ranks do not move**.

## Coaching channel (two-part prior)

Direct NEET coaching→marks LATEs are unidentified. The hole is narrower than “no evidence coaching helps”: we lack candidate-level quasi-experimental Indian data linking coaching type/duration/spend to mark changes conditional on baseline.

We therefore use a skeptical cross-exam prior:

\[
\delta = \mathbf{1}\{S>0\}\,\theta + \mathbf{1}\{S>0\}\,\beta_{\mathrm{doubling}}\,\log_2(S/\tilde{S})
\]

| Symbol | Meaning | Skeptical plug-in (`literature_central`) |
|---|---|---|
| \(\theta\) | Jump from no structured prep → some targeted prep | 0.12 SD |
| \(\beta_{\mathrm{doubling}}\) | Return to doubling positive spend | 0.05 SD |
| \(\tilde{S}\) | Median positive prep spend | CMSE Class X–XII coached p50 (~₹9,900) |

Intensity labels map to spend multiples of median: `none`=0, `modest`=1× (θ only), `intensive`=8× (θ + 3β).

Default profile remains `conservative` (θ=0.08, β=0.03). Sensitivity: `null` / `literature_central` / `reasonable`.

### Literature triangulation (not NEET LATEs)

| Source | Finding used as prior ingredient |
|---|---|
| Test-prep meta (exp/quasi-exp) | Targeted prep often ~0.1–0.3 SD; admission-test subgroup weaker |
| Colombia SaberEs DiD | ~0.07 SD; SES gap narrowed |
| Dongre–Tewary (India FE, elementary) | ~0.14 SD tutoring proxy |
| China Gaokao tutoring | Average effect can be ~0; heterogeneous |
| Korea tutoring expenditure IV | Modest returns to +spend |
| US mandatory college testing | +16% private tutoring (strategic response), stronger among affluent |
| TN Rajan Committee | 99% of admits coached (2019–20); repeaters →71% (2020–21) — **composition**, not LATE |

There is **no established logarithmic spending law**; log₂ is a convenient diminishing-returns parameterization, not an estimated production function.

## Arms race (three propositions)

| Claim | Model encoding |
|---|---|
| **Private return** \(\beta_1>0\) | Absolute δ rises with own prep (θ, β > 0 under non-null profiles) |
| **Strategic response** | Documented externally; not estimated from NEET microdata here |
| **Positional externality** \(\beta_2<0\) | Relative shift = δᵢ − δ̄_pop (or forced equal prep), so universal escalation cancels rank gains |

Scenario `unilateral` subtracts the population-mean coaching shift.  
Scenarios `everyone_modest` / `everyone_intensive` force the whole population to the same prep intensity so relative coaching advantage collapses.

Story JSON fields: `arms_race_signatures` (`beta1_private_return_sd`, `beta2_positional_externality_sd`) and `coaching_plug_in_deltas_sd`.

## Data used

| Piece | Source |
|---|---|
| Marks distribution | `neet_2024_marks_quantiles.csv` |
| Capacity | NMC govt/private-like seat counts |
| Coaching priors | Two-part grid in config + `bayesian_priors.yaml` |
| Medium shifts | Calibrated toward TN Rajan associations |
| Career returns | PLFS wage anchors + `plfs_field_employment.csv` |
| Coaching participation / spend context | NSS Education / CMSE aggregates |

## Artifacts

Written under `data/processed/bayesian/`:

- `score_access_by_stratum.csv`
- `score_marks_histograms.csv`
- `score_earnings_histograms.csv`
- `score_inequality_story.json`

## Warnings

- National seats/appeared cutoffs ≠ state/category counselling pools.
- Medium shifts are not national causal English effects.
- Coaching SD shifts are skeptical priors, not NEET LATEs.
- Causal language for scenario contrasts is prohibited.
