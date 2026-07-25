# Evidence on coaching effects

The earlier baseline treated coaching's admission effect as unidentified and therefore neutral.
That was too coarse. The evidence does not identify one national causal coefficient, but it does
contain several useful layers.

## 1. Direct NEET program cohorts

`data/processed/coaching_outcome_evidence.csv` records programs with actual cohort denominators.
The most informative examples currently found are:

- **SECL Ke Sushrut, 2023–24:** 39 of 40 coached students qualified and 11 obtained MBBS seats.
  Students were economically disadvantaged but selected through a competitive NEET-pattern test,
  and then received intensive residential support.
- **APSWREIS specialised centres, 2024–25:** 143 of 180 NEET trainees qualified and 13 obtained
  MBBS seats. These were SC/ST residential-school students, with the strongest students selected
  for specialised coaching.
- **Sigaram community cohorts:** open-access government-school coaching produced qualification
  rates of 9/54 in 2018, 17/104 in 2019, and 9/19 in 2020; the reported MBBS counts were 0, 0,
  and 2 respectively.

These cohorts establish that outcomes vary enormously with baseline selection, coaching intensity,
school environment, geography, and year. They cannot by themselves answer what would have happened
to the same students without coaching.

## 2. Admitted-student composition

The Tamil Nadu A.K. Rajan Committee reported that almost all admitted students in one cohort had
received coaching. This is a powerful **prevalence constraint**, but not an effectiveness estimate:
the total numbers of coached and uncoached applicants are missing.

## 3. General tutoring research

India-specific education research is relevant as a weak prior:

- Dongre and Tewary use within-household fixed effects in rural elementary-school data and report a
  positive standardized-score effect around 0.14 standard deviations.
- Kumar and Roy Chowdhury find tutoring positively associated with learning outcomes and report
  substantial economic and time burdens: roughly 40–50% of household educational expenditure and
  around 20% of per-capita annual consumption expenditure in the populations they study.
- National participation research shows tutoring is more common among urban, privately schooled,
  and economically advantaged students, and expenditure demand is relatively inelastic.

The exam, age, curriculum, and tutoring intensity differ from NEET preparation. These findings must
not be relabeled as a NEET causal effect.

## 4. External medical-admission-test research

Studies of Australia's UMAT generally find small, section-specific, or statistically insignificant
commercial-coaching effects after adjustment. This supplies a defensible lower-bound scenario, but
UMAT is more aptitude-oriented than NEET's school-curriculum examination.

## 5. Cross-exam experimental / quasi-experimental priors

NEET-specific causal score effects remain unidentified. International and Indian tutoring
evidence still supports a **skeptical prior** that targeted preparation usually moves scores a
little, with diminishing and heterogeneous returns to spend:

| Source | Approximate result | Role for NEET |
|---|---|---|
| Large-scale test-prep meta (exp/quasi-exp, ~2025) | Overall ~0.26 SD; commercial ~0.31; admission-test subgroup ~0.14 (inconclusive) | Upper band for targeted prep; do not paste 0.26 into NEET |
| Colombia SaberEs DiD | ~0.07 SD / +2.2 percentile ranks | Credible small positive |
| Dongre–Tewary (India HH FE, elementary) | ~0.14 SD | India tutoring proxy (weak ESS) |
| China Gaokao private tutoring | Average ~0; positive for some subgroups | Heterogeneity / quality matter |
| Korea tutoring expenditure IV | +10% spend → at most ~0.8–1.3% subject-score gains | Modest intensity returns |
| US mandatory college-entrance testing | +16% private tutoring prevalence (esp. affluent areas) | Strategic response / arms-race behavior |

**Spending shape:** there is no established universal \(\log\) law. Returns look closer to a jump from
none → some targeted prep, then diminishing / noisy gains. Money is a noisy intensity proxy
(selection, scholarships, branding, lodging).

**Recommended skeptical priors** (modeling, not published LATEs):

- \(\theta\) (any meaningful prep vs none) \(\sim N(0.12, 0.10^2)\)
- \(\beta_{\mathrm{doubling}}\) (doubling positive spend) \(\sim N(0.05, 0.08^2)\)

Implemented in `config/score_privilege_scenarios.yaml` as the two-part form
\(\delta = 1\{S>0\}\theta + 1\{S>0\}\beta\log_2(S/\tilde{S})\) with profiles
`null` / `conservative` / `literature_central` / `reasonable`.

## 6. Arms race is not “coaching teaches more”

An educational arms race needs three claims:

1. **Private return:** holding others fixed, more prep raises score/rank/admission odds.
2. **Strategic response:** when the exam matters more (or rivals prep more), families buy more prep.
3. **Positional externality:** when rivals prep more, own admission odds fall at fixed own prep.

Fixed seats make the social return smaller than the private return: if everyone coaches equally,
scores may rise while relative admission probabilities largely return to baseline and costs rise.
TN Rajan composition (near-universal coaching among admits; rising repeater share) is strong
**institutional** evidence of escalation, not a score LATE.

## 7. Modeling policy in this repo

The score → rank → seat model (`make score-privilege`) uses the two-part prior above, converts
shifts through the empirical marks distribution and capacity cutoffs, and encodes the positional
externality by subtracting population-mean coaching shifts (or forcing equal prep). Program
cohorts remain for posterior predictive checks after selection adjustment — not for identifying θ.

Intensive residential programs require a separate selection model. Fitting their observed 20–30%
MBBS rates by assigning all of the difference to coaching would be a serious error.

## 8. Evidence hierarchy

1. Randomized or quasi-experimental NEET intervention: none found yet.
2. NEET cohorts with denominators and a comparison group: not yet found.
3. NEET program cohorts with denominators but no controls: available.
4. NEET admitted-student composition: available (TN Rajan).
5. Cross-exam experimental / quasi-experimental test-prep effects: available as skeptical priors.
6. General Indian tutoring causal/quasi-causal research: available as a weak proxy.
7. Foreign medical-admission-test coaching studies: available as an external bound.
8. Coaching-company claims: admissible only as low-trust audit inputs after denominator and outcome
   definitions are verified.

**Priority data gap:** longitudinal or quasi-experimental Indian candidate data linking coaching
type, duration, hours, and expenditure to changes in NEET marks/rank conditional on baseline.
