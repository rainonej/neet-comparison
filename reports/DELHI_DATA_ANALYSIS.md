# NCT Delhi data analysis

**Date:** 2026-07-26  
**Branch:** `agent/add-delhi-data-audit`  
**Audit:** [docs/DELHI_DATA_AUDIT.md](../docs/DELHI_DATA_AUDIT.md)  
**Machine-readable summary:** `data/processed/delhi/delhi_stats_summary.json`

## Bottom line

Delhi is ready as a **third descriptive case** and as a **coaching–resources prior**, not as a replacement for the Tamil Nadu medium–score story. The CMSE extract reproduces the published Delhi coaching rate to three decimals, and joint household consumption × tutoring is observable. No public file links Delhi domicile, NEET score, school medium, and coaching for the same candidate.

## What was downloaded / registered

| Local archive | Role | Manifest |
|---|---|---|
| `data/external/mospi/cmse/2025/raw/Data in CSV.zip` | Person/household microdata (already held) | previously registered |
| `data/external/mospi/nss_education/2017-18/raw/Data_in_CSV.zip` | Historical medium × coaching (already held) | previously registered |
| `data/external/nta/raw/delhi/neet_2026_key_data_20260716.pdf` | 2025–2026 Delhi applicant-state totals | registered 2026-07-26 |
| `data/external/nta/raw/delhi/neet_2022_result_20220907.pdf` | 2022 Delhi applicant-state totals | registered 2026-07-26 |
| `data/external/mospi/cmse/2025/raw/cmse_2025_published_tables.pdf` | Published CMSE tables (NADA served PDF) | registered 2026-07-26 |
| Existing NEET-2024 centre marks + centre list | Delhi **exam-centre** score distribution | already local |

Restricted unit files remain gitignored. Only aggregates are committed under `data/processed/delhi/`.

## 1. Applicant-state NEET participation

| Year | Registered | Appeared | Qualified / appeared | UR/EWS cutoff |
|---:|---:|---:|---:|---:|
| 2021 | 34,520 | 31,202 | 75.5% | — |
| 2024 (peak) | 68,139 | 66,132 | 70.8% | 162 |
| 2025 | 63,046 | 61,199 | 65.9% | 144 |
| 2026 | 59,669 | 53,846 | 65.2% | 213 |

- Registrations nearly doubled from 2021 to 2024 (**1.97×**), then fell to 59,669 in 2026.
- 2026 appearance rate dropped to **90.2%** (vs ~97% in 2024–25).
- Qualification shares are **not** a score trend: the administrative cutoff moved from 162 → 144 → 213.

## 2. 2024 Delhi examination-centre scores

Filtered from the anonymized national release (`geography_type=exam_centre`):

| | Delhi centres | National |
|---|---:|---:|
| Candidates | 66,090 | 2,333,162 |
| Centres | 116 | 4,750 |
| Median marks | **213** | 163 |
| Share ≥600 | **5.0%** | 3.5% |

**Caveat:** a Delhi centre is not Delhi domicile. Use for exploratory geography / metro context only.

Artifact: `delhi_neet_2024_centre_score_summary.csv`.

## 3. CMSE 2025 coaching × resources (Delhi extract)

Weighted with `mult`; cells with &lt;30 unweighted observations suppressed.

| Enrolment band | n | Coaching rate | Median annual spend among coached |
|---|---:|---:|---:|
| All enrolled | 811 | **39.1%** | ₹8,900 |
| Class X–XII | 198 | **58.1%** | ₹24,000 |
| Class XII | 66 | **66.0%** | ₹25,100 |

Published validation: all-enrolled rate extract **0.3912** vs published **0.391** (abs error ≈ 0.0002).

### Resource gradient (Class X–XII, Delhi quintiles)

| Quintile | n | Coaching rate | Median spend \| coached | Burden p50 |
|---:|---:|---:|---:|---:|
| 1 (lowest) | 41 | 39.6% | ₹7,500 | 4.6% |
| 2 | 36 | 61.3% | ₹15,500 | 6.5% |
| 3 | — | suppressed | — | — |
| 4 | 34 | 56.2% | ₹24,000 | 7.9% |
| 5 (highest) | 58 | 69.4% | ₹31,000 | 7.1% |

- Q5 vs Q1 coaching-rate ratio ≈ **1.75×**
- Q5 vs Q1 median spend among coached ≈ **4.13×**
- Burden (annual coaching / 12× monthly household consumption) is similar across middle/upper quintiles (~6–8%), so poorer coached households face a comparable or only modestly lower share of resources despite much lower rupee spend.

School-type (Class X–XII): government and private-unaided coaching **rates** are similar (~56–58%), but private median spend is higher (₹28,500 vs ₹18,700).

## 4. Historical school medium × coaching (NSS 2017–18)

Delhi secondary / higher-secondary attenders:

| Medium | Student share | Coaching rate |
|---|---:|---:|
| Hindi | 43.6% | 36.9% |
| English | 56.4% | 56.8% |

English/Hindi coaching-rate ratio ≈ **1.54×**. This is school medium × school tutoring, **not** NEET paper language × score.

## 5. Fit for Bayesian model vs visual essay

| Use | Verdict | Why |
|---|---|---|
| Two-part Delhi coaching prior (P(coach), spend \| coach) by resources | **Yes — Bayesian** | Jointly observed in CMSE; better than attaching a national mean |
| Delhi participation / qualification descriptive series | **Yes — essay; weak Bayesian** | Good narrative; cutoff-dependent rates should not update ability |
| 2024 Delhi-centre score distribution | **Essay with caveat; optional metro prior** | Label as centre geography |
| Hindi/English school-medium margin | **Calibration margin only** | Unlinked to NEET candidates |
| Medium → NEET score effect | **No** | No Delhi joint |
| Coaching → NEET score causal | **No / sensitivity only** | Coaching not NEET-specific; no score link |
| Replace TN medium ladder in the essay | **No** | TN still has admitted-student medium × government-seat rates; Delhi does not |

### Recommended wiring

1. **Bayesian / privilege ladder:** add an optional Delhi coaching-access module using the two-part CMSE gradient; keep TN medium rates as the medium-channel evidence; do not invent a Delhi medium–score likelihood.
2. **Visual essay:** use Delhi for (a) participation boom/retreat, (b) tutoring rising with household resources, (c) qualified ≠ affordable seat under MCC/FMSC/GGSIPU. Keep the English/Tamil knife-edge story on Tamil Nadu evidence.

## Artifacts

```text
data/processed/delhi/
  delhi_neet_state_results_2021_2026.csv
  delhi_cmse_2025_published_benchmarks.csv
  delhi_school_medium_2019_20.csv
  delhi_cmse_coaching_by_band.csv
  delhi_cmse_coaching_by_consumption_quintile.csv
  delhi_cmse_coaching_by_school_type.csv
  delhi_nss75_medium_coaching.csv
  delhi_neet_2024_centre_score_summary.csv
  delhi_key_stats.csv
  delhi_stats_summary.json
```

Reproduce microdata aggregates:

```bash
python scripts/process_delhi_state.py
pytest -q tests/test_process_delhi_state.py
```
