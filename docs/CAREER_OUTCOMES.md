# Career, unemployment, and earnings outcomes

A comparison based only on salaries among employed doctors, engineers, or lawyers is upward biased.
The simulator must include the probability that someone who begins a degree never completes it,
leaves the labor force, remains unemployed, takes a job unrelated to the degree, or obtains only
informal or unstable work.

## Required gates

For each path and demographic profile, estimate:

1. probability of completing the degree;
2. labor-force participation after completion;
3. employment conditional on labor-force participation;
4. occupation or field match conditional on employment;
5. formal/regular/public-sector status conditional on employment;
6. earnings conditional on each employed state.

Thus expected annual earnings are approximately:

\[
P(C)P(L\mid C)P(E\mid L,C)
\left[P(M\mid E)E(Y_M)+(1-P(M\mid E))E(Y_U)\right],
\]

where `C` is completion, `L` labor-force participation, `E` employment, `M` a field-matched job,
and `U` an unmatched job. Monte Carlo output should retain a point mass at zero for non-completion,
nonparticipation, and unemployment.

## Broad empirical anchors

The ILO/IHD India Employment Report 2024 estimates youth unemployment among graduates at 28.7% in
2022. State of Working India 2026 reports nearly 40% among graduates aged 15–25 and about 20% among
those aged 25–29 in 2023. These are broad age-specific graduate rates, not engineering-, law-, or
medicine-specific estimates.

The same ILO/IHD report states that youths with a technical degree had about 1.4 times the
probability of regular employment of youths without technical qualifications, and reports a 36.1%
formal-employment share for graduate-or-higher youths in 2022. The denominator of the latter measure
must be checked in the full report before using it as a conditional probability.

PLFS 2023–24 contains technical-education fields and labor outcomes. Its unweighted metadata show
6,067 engineering/technology degree records and 1,281 medicine degree records. This is enough for a
national hierarchical estimate, but medicine will need substantially more pooling at state and
social-group resolution. The microdata require a free portal login and must be analyzed using survey
weights.

## Underemployment

Official unemployment is not enough. The model should separately estimate:

- field mismatch;
- casual or informal employment;
- inadequate hours where measurable;
- earnings below a degree-specific adequacy threshold;
- repeated job search or exam preparation.

These states remain economically meaningful even when PLFS classifies the individual as employed.

## First implementation

Until PLFS microdata are acquired, use broad graduate unemployment rates as low-ESS parent priors.
Do not claim field-specific engineer or lawyer rates. Once PLFS is available, update medicine,
engineering, and other technical fields directly and define law through general education plus
occupation codes, because PLFS's technical-education field categories do not isolate law.
