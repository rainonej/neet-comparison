# Bayesian evidence model

The project contains complete administrative counts, survey estimates, selected coaching cohorts,
state-specific associations, and weak external proxies. A Bayesian model is appropriate because it
can preserve uncertainty and update a common set of quantities without pretending that all evidence
has equal relevance.

## 1. Default stance

The default profile is **conservative**:

- effects are centered close to zero unless direct evidence says otherwise;
- broad national rates may center a field-specific prior but receive a low effective sample size;
- selected coaching cohorts are posterior-predictive checks, not treatment-effect updates;
- missing cross-dataset dependence uses the documented conditional-independence approximation;
- entirely absent effect evidence remains neutral rather than being filled with an invented penalty.

Two additional profiles must always be runnable:

- **neutral**: broad, weak priors, including a zero-centered coaching shift;
- **reasonable**: places somewhat more weight on the best available Indian proxy evidence.

The final interface should display how materially conclusions change under all three profiles.

## 2. Evidence weighting

A source's nominal sample size is not automatically its Bayesian weight. A very large study of a
different population may be less relevant than a small complete administrative table for the exact
state and year.

Suggested hierarchy:

1. Exact applicant/allotment counts for the same exam, state, quota, and year: full count update.
2. Design-based survey estimate for the same target: update using survey effective sample size.
3. Same exam but different state or year: partial weight.
4. General Indian tutoring or graduate-employment evidence: weak prior center.
5. International or non-comparable examination evidence: sensitivity only.
6. Competitively selected coaching programs: validation after explicitly simulating selection.

Every posterior object carries a label, source, and evidence class.

## 3. Probability families

Use Beta-Binomial models for:

- science-stream continuation;
- taking NEET;
- degree completion;
- labor-force participation;
- employment conditional on participation;
- field-matched employment;
- formal or regular salaried employment;
- seat acceptance conditional on offer and affordability.

Use Dirichlet-Multinomial models for:

- government/private/deemed/BDS/AYUSH/no-seat outcomes;
- alternative education choices;
- employment-state or career-path mixtures.

Use bounded Normal distributions for uncertain score shifts and log-odds effects. Use hierarchical
lognormal models for positive earnings conditional on employment state.

## 4. Hierarchy and partial pooling

Employment and admission rates will become unstable when divided by state, sex, social group,
urbanity, age, and field. The model should pool them hierarchically:

```text
India graduate employment
  -> age × sex × urbanity graduate employment
      -> field (medicine, engineering, law, ...)
          -> state × field
              -> finer social group when sample support permits
```

Small cells shrink toward the appropriate parent rather than producing zero or one probabilities.
Posterior output must include observed support and the degree of shrinkage.

## 5. Calibration versus validation

Do not spend every aggregate statistic fitting the model. Candidate score quantiles, state/gender/
category marginals, allotment counts, coaching cohorts, graduate unemployment by age, and formal
employment by education should be partitioned into calibration and held-out posterior-predictive
checks.

A model fails validation when it reproduces its fitted national mean but cannot reproduce important
held-out tails, state totals, age gradients, or zero-earnings shares.

## 6. Interpretation

The posterior answers questions such as:

> Under this evidence and these assumptions, what range of government-seat, employment, and
> lifetime-earnings outcomes is plausible for synthetic people with this profile?

It does not answer:

> What is the identified causal effect of NEET admission or coaching for this individual?
