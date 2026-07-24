# NEET life-course data audit

A reproducible source audit for a possible **NEET-UG life-course microsimulation**. The long-term idea is to simulate plausible household, schooling, exam, admission, cost, and career trajectories. This repository deliberately starts one step earlier: it asks what is actually measured, what can be linked, and what would have to be assumed.

## Current conclusion

A useful simulator is feasible, but not as a fully empirical causal model.

The public data are strongest for:

- candidate score distributions, especially the anonymized 2024 centre release;
- college and seat capacity;
- AIQ/deemed/central counselling allotments;
- household consumption, assets, education, coaching expenditure, employment, and wages in separate national surveys;
- state-level fee schedules and counselling outcomes, although these are highly fragmented.

The central missing link is a dataset containing **the same applicant's NEET score, admission outcome, coaching, household resources, school background, domicile, and later earnings**. No such national linked file has been identified.

Consequently, a future model must separate:

1. observed distributions;
2. estimated statistical relationships;
3. calibrated but unobserved links;
4. narrative-only context.

## Repository contents

- `docs/source_catalog.csv`: auditable source registry, variables, access, and limitations.
- `docs/state_counselling_portals.csv`: starting directory for state-level admissions, fee, and cutoff collection.
- `docs/source_manifest.yaml`: machine-readable acquisition manifest.
- `docs/FEASIBILITY.md`: what can be estimated and at what resolution.
- `docs/DATA_GAPS.md`: missing quantities and proposed workarounds.
- `docs/RESEARCH_LITERATURE.md`: papers and what each contributes.
- `data/processed/published_estimates.csv`: small set of explicitly sourced benchmark values.
- `data/processed/neet_2024_dataful_preview.csv`: ten-row preview transcribed from the public listing, not the full dataset.
- `data/processed/neet_2024_marks_*.csv`: reproducible summaries from an acquired full public reconstruction of the 2024 centre marks.
- `reports/INITIAL_FINDINGS.md`: concise audit conclusion and recommended empirical scope.
- `reports/EXECUTION_NOTES.md`: what was actually downloaded and validated in this run.
- `scripts/`: downloaders and parsers designed to preserve provenance.

Raw and external data are gitignored. The repository stores scripts, hashes, schemas, and source records rather than republishing files whose licenses or terms are unclear.

## Quick checks

```bash
make audit
make status
make test
```

## Immediate acquisition order

```bash
python scripts/audit_catalog.py
python scripts/fetch_neet_2024_centres.py --out data/raw/neet_2024
python scripts/scrape_nmc_colleges.py --out data/raw/nmc_colleges.csv
python scripts/scrape_mcc_archive.py --year 2024 --out data/raw/mcc_2024
```

The survey microdata require account-based downloads. Place them in `data/raw/restricted/` using the filenames documented in `docs/DATA_GAPS.md`; never commit them unless their license explicitly allows redistribution.

## Ethical and statistical guardrails

- Do not infer caste, income, coaching, or domicile from an examination centre.
- Do not interpret the fraction of admitted students who were coached as the probability of admission after coaching.
- Do not label model-generated trajectories as causal effects.
- Do not produce individual suicide-risk probabilities.
- Always expose assumptions and sensitivity ranges in user-facing outputs.
