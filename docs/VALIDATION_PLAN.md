# Calibration and validation plan

The project has enough unused aggregate statistics to avoid a model that merely reproduces its own
assumptions. Validation is organized by layer.

## 1. Data splitting principles

- Prefer **time holdouts**: calibrate on earlier years and validate on later years.
- Prefer **geographic holdouts**: fit national/state effects without one state, then predict it.
- Never use the same marginal both to create a coefficient and to advertise validation.
- Keep candidate qualification, seat offer, seat affordability, seat acceptance, course
  completion, and labor-market outcomes as separate targets.

## 2. Admission-model validation targets

### National and state score distribution

Use the 2024 anonymized centre-wise marks to fit/validate the score-distribution engine. Hold out
centres or complete states and compare:

- mean and variance;
- median and upper-tail quantiles;
- fractions above policy-relevant score thresholds;
- between-centre and between-state dispersion.

### NTA result marginals

Reserve selected published tables by year for validation:

- appeared and qualified by state;
- appeared and qualified by sex;
- appeared and qualified by reservation category;
- language and nationality marginals where available.

### Counselling and seat allocation

Use MCC/state allotment records to validate:

- total MBBS offers by college ownership;
- category and quota composition;
- closing ranks by round;
- vacancy and non-joining rates;
- government/private/deemed acceptance patterns.

### Tamil Nadu medium and repeater statistics

The model may use only part of the Tamil Nadu history for fitting. Hold out years to validate:

- Tamil- versus English-medium admission rates;
- government-school participation;
- first-attempt versus repeater composition;
- coached share among admitted students.

These are joint output constraints, not all causal coefficients.

## 3. Coaching-model validation

The coaching sensitivity grid is calibrated indirectly. For each observed program cohort:

1. Reconstruct its eligibility and selection rule as closely as possible.
2. Generate a matching synthetic candidate pool.
3. Apply the program's selection mechanism before coaching.
4. Apply the coaching score-shift distribution.
5. Compare predicted qualification and MBBS-admission counts with observed counts.

Cohorts are validation targets, not interchangeable estimates:

- SECL and APSWREIS validate selected, intensive programs;
- Sigaram validates a lower-resource, open-access community program;
- Tamil Nadu's coached share among admitted students validates coaching take-up and selection,
  although it lacks the applicant denominator.

The model fails validation if it can fit only the elite selected programs by predicting implausibly
large effects for ordinary coaching.

## 4. Household and education validation

Synthetic households must reproduce survey marginals not used during fitting:

- state × rural/urban consumption quantiles;
- household size and number of children;
- caste/social-group and religion distributions;
- parental education and occupation;
- school management, board, medium, and coaching participation;
- coaching expenditure as a share of household resources.

Where feasible, compare generated cross-tabs against HCES, NFHS, AIDIS, CMSE/NSS Education, and
IHDS tables.

## 5. Career-model validation

PLFS career trajectories should be tested against held-out years and cells:

- physician, engineer, lawyer, nurse, pharmacist, and general-graduate wage distributions;
- public/private and rural/urban physician gaps;
- labor-force participation and regular-salaried employment;
- age-earnings profiles;
- job-quality indicators where reproducible.

The model should report both weighted predictive errors and errors for socially important small
subgroups.

## 6. Metrics

- Binomial outcomes: calibration plots, standardized residuals, log score, and interval coverage.
- Continuous distributions: weighted quantile error, Wasserstein distance, and tail exceedance.
- Multicategory outcomes: log loss and category-specific calibration.
- Household synthesis: standardized absolute differences for held-out marginals and cross-tabs.
- Lifetime outcomes: posterior predictive intervals rather than validation against nonexistent
  linked life-course records.

## 7. Failure criteria

The product should be narrowed or stopped if:

- reasonable coaching priors cannot jointly reproduce open-access and selected-program cohorts;
- state results require implausibly large unexplained state multipliers;
- affordability predictions contradict observed joining/vacancy behavior;
- alternative-career mixtures cannot reproduce PLFS education/occupation marginals;
- uncertainty intervals are so wide that profile comparisons reverse under ordinary assumptions.
