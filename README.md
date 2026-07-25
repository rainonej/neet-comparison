# neet-comparison

Source audit and reproducible data collection for a **NEET-UG life-course microsimulation** — comparing India’s medical-admissions bottleneck (one annual exam, extreme seat scarcity, coaching economy) against systems Americans already understand.

This repository starts one step before a full simulator: it asks what is measured, what can be linked, and what must be assumed.

## Current conclusion

A useful simulator is feasible as a **calibrated synthetic-population model**, not a fully empirical causal model.

Public data are strongest for score distributions, seat capacity, AIQ counselling allotments, and separate national surveys of household resources and coaching spend. The central missing link is a national file joining the **same applicant’s** NEET score, admission outcome, coaching intensity, household resources, school background, domicile, and later earnings.

## Quickstart

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -e ".[dev]"
make audit
make status
make test
make bayes
make privilege
make score-privilege
make story
```

Open the interactive story after `make story`:

`reports/interactive/the-accessible-seat.html`

See [docs/SETUP.md](docs/SETUP.md) for directory layout and gitignore rules.

## Acquisition: open now, gated next

**Already downloadable without login** (this bootstrap pass):

- OSF NEET/JEE aspirant microdata (`tnh4x`)
- OpenICPSR engineering-admissions replication (E112992)
- GitHub NEET-2024 centre-marks reconstruction
- NMC college/intake scrape, MCC UG archive, Kerala CEE public lists

Details and local paths: [docs/OPEN_DATA_DOWNLOADS.md](docs/OPEN_DATA_DOWNLOADS.md).

**Next (free accounts; do soon):** one MoSPI login for PLFS/HCES/CMSE/NSS/AIDIS/TUS, plus DHS NFHS and ICPSR IHDS. Runbook: [docs/GATED_NEXT.md](docs/GATED_NEXT.md). Full checklist: [docs/ACQUISITION_CHECKLIST.md](docs/ACQUISITION_CHECKLIST.md).

```bash
python scripts/audit_catalog.py
python scripts/scrape_nmc_colleges.py --out data/raw/nmc_colleges.csv
python scripts/scrape_mcc_archive.py --year 2024 --out data/raw/mcc_2024
python scripts/fetch_neet_2024_centres.py --out data/raw/neet_2024
```

Raw and external files are gitignored. Register every download with `scripts/register_download.py`. Never commit restricted microdata unless the licence explicitly allows redistribution.

## Key docs

| Doc | Purpose |
|---|---|
| [docs/FEASIBILITY.md](docs/FEASIBILITY.md) | What can be estimated and at what resolution |
| [docs/DATA_GAPS.md](docs/DATA_GAPS.md) | Missing joints and workarounds |
| [docs/DATA_HOLDER_AND_RESEARCHER_LEADS.md](docs/DATA_HOLDER_AND_RESEARCHER_LEADS.md) | Who likely already holds useful extracts |
| [docs/PRIVACY_AND_DATA_HANDLING.md](docs/PRIVACY_AND_DATA_HANDLING.md) | Lawful use; no retained identifiers |
| [docs/source_catalog.csv](docs/source_catalog.csv) | Auditable source registry |
| [reports/INITIAL_FINDINGS.md](reports/INITIAL_FINDINGS.md) | Audit bottom line |
| [docs/BAYESIAN_MODEL.md](docs/BAYESIAN_MODEL.md) | Bayesian evidence design |
| [reports/BAYESIAN_MODEL_REPORT.md](reports/BAYESIAN_MODEL_REPORT.md) | Fitted posteriors + profile sensitivity (current data freeze) |
| [reports/PRIVILEGE_INEQUALITY_STORY.md](reports/PRIVILEGE_INEQUALITY_STORY.md) | Privilege access ladder + seat vs no-seat lifetime earnings distributions |
| [reports/SCORE_PRIVILEGE_MODEL.md](reports/SCORE_PRIVILEGE_MODEL.md) | Score → rank → seat model with coaching arms-race scenarios |
| [reports/STORY_READINESS.md](reports/STORY_READINESS.md) | What we can show at what grain (SHOW / SENS / BLOCK) |
| [reports/interactive/the-accessible-seat.html](reports/interactive/the-accessible-seat.html) | Interactive India story (prize → lottery → razor margin → privilege tax) |
| [docs/STORY_BIBLIOGRAPHY.md](docs/STORY_BIBLIOGRAPHY.md) | Citations for prize / lottery / privilege claims in the story |

## Ethical and statistical guardrails

- Do not infer caste, income, coaching, or domicile from an examination centre.
- Do not interpret the fraction of admitted students who were coached as the probability of admission after coaching.
- Do not label model-generated trajectories as causal effects.
- Do not produce individual suicide-risk probabilities.
- Always expose assumptions and sensitivity ranges in user-facing outputs.
