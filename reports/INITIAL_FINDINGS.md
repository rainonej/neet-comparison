# Initial data-audit findings

## Bottom line

A defensible first simulator is possible, provided it is described as a calibrated synthetic-population model rather than a causal prediction system. The project has enough public information to reconstruct the admissions tournament and to model family resources and career outcomes separately. It does not have a public national dataset that observes all of those stages for the same people.

## What is unusually strong

### 1. Exam-score ecology

The anonymized 2024 centre-wise release provides roughly 2.33 million candidate marks with test-centre geography. The official PDFs and centre index can be re-downloaded and hashed. This permits national, state-of-test-centre, city, and centre score distributions. Test-centre geography must not be interpreted as domicile or household background.

### 2. Seat supply and admissions

NMC records support college and authorized-intake tables. MCC archives contain seat matrices, final allotment results, admitted-candidate lists, vacancies, and round-specific material for national counselling. State authorities commonly publish parallel merit and allotment material for state quotas.

### 3. Household and education distributions

HCES, NFHS, AIDIS, IHDS, NSS Education, and CMSE jointly cover consumption, assets, debt, social group, religion, family structure, parental education, schooling, coaching participation, and education expenditure. These surveys can generate a plausible synthetic family population after registration and survey-weight processing.

### 4. Alternative careers and earnings

PLFS contains occupation, education, employment status, sector, wages, state, sex, urban/rural location, and social group. It can estimate conditional physician and alternative-career distributions, although detailed subgroup cells require hierarchical partial pooling.

## What is fundamentally missing

No identified national public file links, for the same applicant:

- household resources and parental background;
- school board/type/language and prior achievement;
- coaching mode, cost, and duration;
- attempt number;
- NEET score/rank;
- state domicile and counselling choices;
- seat offer and acceptance;
- medical-school completion;
- later wages, wealth, debt, or family transfers.

This means the model cannot directly estimate the causal effect of barely obtaining a seat, nor a fully conditioned admission probability such as `P(government MBBS | income, caste, sex, state, coaching, attempt)`. Those links must be estimated from narrower studies, calibrated, or exposed as sensitivity parameters.

## Highest-risk statistical mistakes

1. Treating the share of admitted students who received coaching as a coaching success rate.
2. Inferring caste, income, school type, or domicile from a test centre.
3. Treating authorized seats as completed degrees or practicing doctors.
4. Comparing a labor wage directly with household consumption or national-income percentiles without labeling the statistical mismatch.
5. Treating projected physician earnings as the causal return to NEET admission.
6. Producing individual suicide-risk probabilities from small cross-sectional studies.

## Best feasible first scope

- Cohort year: **2024**, because of the exceptional centre-score release.
- Geography: national score/capacity context plus MCC and three state adapters.
- Initial states: **Kerala, Gujarat, and Tamil Nadu**; add Maharashtra as the first harder portal.
- Household model: HCES + NFHS/AIDIS; use consumption and assets rather than pretending income alone is precisely measured.
- Coaching model: CMSE/NSS expenditure distribution plus NEET-specific observational studies; effect size remains a sensitivity parameter.
- Outcomes: PLFS conditional trajectories for physicians and alternatives, explicitly labeled projections.

## Next acquisition priorities

1. Run the NTA 2024 centre/PDF downloader and preserve hashes.
2. Snapshot NMC college/intake records and reconcile Institutes of National Importance.
3. Download all MCC 2024 UG seat, allotment, admitted-candidate, and vacancy files.
4. Build Kerala, Gujarat, and Tamil Nadu document indexes before writing custom parsers.
5. Register for HCES, CMSE, PLFS, NFHS, and AIDIS microdata and record exact file versions/licences.
6. Search for applicant-level surveys with coaching denominators, repeat attempts, ranks, and family background.
7. Decide whether a targeted original survey is necessary after the first calibrated model exposes uncertainty.
