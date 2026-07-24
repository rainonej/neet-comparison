# Proposed empirical model interfaces

## Household generator

Target output: joint synthetic distribution of state, rurality, consumption, assets, debt, caste/social group, religion, family size, parental education and occupation.

Use survey weights. Preserve dependence with either weighted hot-deck sampling or a fitted joint generative model. Do not independently sample marginals.

## Exam model

The empirical 2024 score distribution can be used directly. Conditioning that score on household and schooling variables is not identified. The initial model should therefore expose multiple scenarios:

- weak socioeconomic gradient;
- central calibrated gradient;
- strong gradient.

Coaching and repeat effects must similarly be sensitivity parameters until better data are acquired.

## Admission model

Admissions should be rank-driven. Construct:

- score-to-rank uncertainty;
- AIQ/deemed/central cutoff tables from MCC;
- state quota cutoffs from state authorities;
- category and domicile logic;
- family affordability filter after offer generation.

## Outcome model

Fit weighted hierarchical distributions to PLFS wage and job-quality outcomes. State, sector, sex, social group, urbanity, age and occupation can enter with partial pooling. Report observed support sizes.

## Narrative layer

The language model receives structured simulation summaries and provenance. It may explain but may not modify probabilities or create unsourced psychological outcomes.
