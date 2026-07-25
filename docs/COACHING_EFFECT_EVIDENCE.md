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

## 5. Initial modeling policy

Coaching no longer has one silent neutral baseline. The model uses an explicit sensitivity grid for
an **individual score shift**, expressed in standard deviations of the relevant uncoached score
distribution:

- null: 0.00 SD;
- central proxy: 0.14 SD;
- strong: 0.30 SD.

The 0.14-SD value is borrowed from general Indian tutoring research and is not claimed as a NEET
estimate. The grid is converted into admission changes through the empirical score/rank and seat
allocation model. Program cohorts are then used for posterior predictive checks after accounting
for their strong selection mechanisms.

Intensive residential programs require a separate selection model. Fitting their observed 20–30%
MBBS rates by assigning all of the difference to coaching would be a serious error.

## 6. Evidence hierarchy

1. Randomized or quasi-experimental NEET intervention: none found yet.
2. NEET cohorts with denominators and a comparison group: not yet found.
3. NEET program cohorts with denominators but no controls: available.
4. NEET admitted-student composition: available.
5. General Indian tutoring causal/quasi-causal research: available as a proxy.
6. Foreign medical-admission-test coaching studies: available as an external bound.
7. Coaching-company claims: admissible only as low-trust audit inputs after denominator and outcome
   definitions are verified.
