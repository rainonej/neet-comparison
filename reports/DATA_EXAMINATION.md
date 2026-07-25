# Data examination report

**Date:** 2026-07-25  
**Scope:** Local holdings under `data/` (raw, external, processed), their schemas, modelling utility, and preliminary statistics.  
**Repo state at analysis:** `main` @ clean working tree, synced with `origin/main`.

## Bottom line

We hold ~**1.07 GB across 721 inventoried files**, dominated by PDFs (MCC counselling, Kerala CEE, Tamil Nadu, Dakshana annual reports, NTA notices). The only large **candidate-level numeric** file is the NEET-2024 centre-marks reconstruction (**2,333,162** rows). Seat supply is snapshotable from NMC (**823** colleges, **129,602** UG seats). Together they imply roughly **18 mark-rows per NMC seat** — a scarcity ecology, not a causal admissions model.

Processed tables already turn the strongest public fragments into citation-ready inputs (score quantiles, Tamil Nadu medium rates, coaching-outcome Wilson intervals, employment benchmarks). **Gated national microdata** (HCES, CMSE, PLFS, NFHS, AIDIS) remain the largest acquisition gap for household and labor layers.

---

## 1. Inventory overview

| Location | Role | Approx. size / count |
|---|---|---|
| `data/external/neet-2024-center-marks.csv` + `github_hq969/` | Candidate marks + centre geography | ~74 MB CSV/SQLite |
| `data/raw/nmc_colleges.csv` | MBBS college/intake snapshot | 823 rows |
| `data/raw/mcc_2024/`, `mcc_ug/2023`, `mcc_ug/2025` | AIQ counselling PDFs + indexes | 37 + 62 + 4 indexed docs |
| `data/external/kerala_cee/` | State counselling/scholarship PDFs | 213 PDFs, ~184 MB |
| `data/external/tamil_nadu/` | State counselling mirrors / archives | ~62 MB |
| `data/external/dakshana/` | Free residential coaching annual reports | ~520 MB PDFs |
| `data/external/osf/tnh4x/` | Aspirant stress/NSSI microdata | n=151 CSV |
| `data/external/cbse/` | Dummy-school enforcement press PDFs | press + HTML |
| `data/external/ncrb/`, `nirf/`, `nta/`, `wid/`, `world_bank/` | Context PDFs/HTML | mixed |
| `data/processed/*.csv` | Small, commit-safe summaries | see §3 |

**By extension (local inventory):** 652 PDF, 52 HTML, 9 CSV, 6 JSON, 1 SQLite DB, 1 ZIP.

Raw/external bulk is gitignored; hashes and paths live in `data/processed/local_data_inventory.csv` and `download_manifest.csv`.

---

## 2. Schemas and modelling utility

### 2.1 NEET-2024 centre marks (critical)

**Source file:** `data/external/neet-2024-center-marks.csv`  
**Schema (headerless):**

| Column | Type | Meaning |
|---|---|---|
| `centre_id` | int | Test-centre code |
| `serial_number` | int | Anonymized within-centre sequence |
| `marks` | int | Raw NEET score (−180…720) |

**Centre geography:** `data/external/github_hq969/raw/neet-2024-centers.csv`  
Schema (headerless): `idx, state, city, center_name, centre_id` — **38** states/UTs (incl. Outside-India), **567** cities, **4,750** centres. Perfect join to marks (0 unmatched rows).

**Utility**
- National and centre/city/state-of-centre **score ecology**
- Rank/score curve calibration; scarcity narratives
- Centre-mean heterogeneity as *context*, never as individual SES

**Not usable for:** domicile, caste, income, coaching, attempt number, admission outcome, gender.

**Provenance caveat:** Third-party reconstruction of official NTA centre PDFs. Row count (~2.333M) should still be reconciled with official appeared/qualified releases before treating as canonical.

### 2.2 NMC college / seat supply (critical)

**File:** `data/raw/nmc_colleges.csv` (823 rows)

Useful fields: `collegeName`, `stateName`, `managementupdate`, `ugApproved`, `universityName`, `yearOfInc`, `collegeId`, contact/address columns. Several numeric ID columns (`state`, `management`) are null/unusable in this scrape; use `stateName` and `managementupdate`.

**Utility:** National MBBS capacity baseline; government vs private seat split; state capacity adapters. Reconcile with MCC AIIMS/JIPMER/ESIC matrices (INIs may be incomplete on the NMC page).

### 2.3 MCC UG counselling archives (critical for AIQ)

Indexes: `data/raw/mcc_2024/2024/archive_index.csv` (37), `mcc_ug/2023` (62), `mcc_ug/2025` (4 partial).  
Schema: `title, url, local_file`. Bodies are PDFs (seat matrices, round results, vacancies, admitted lists).

**Utility:** Reconstruct AIQ / deemed / AIIMS / JIPMER allotment flows by round. Still need table extraction before microsim use. Does **not** cover most state-quota seats.

### 2.4 Tamil Nadu medium × admission (high — state case)

Processed from Justice A.K. Rajan Committee Table 7.18:

| File | Schema highlights |
|---|---|
| `tamil_nadu_medium_admissions_2010_2021.csv` | year, neet_period, quota_group, applied/allotted by English/Tamil medium |
| `tamil_nadu_medium_admission_rates.csv` | + `govt_rate_*`, `rate_ratio_english_to_tamil` |
| `tamil_nadu_medium_aggregate_rates.csv` | pre_neet vs post_neet aggregates |

**Utility:** Strong before/after-NEET illustration of medium-language inequality among **applicants who reached counselling**. Not a national causal effect; admitted/applicant denominators are TN-ordinary-quota specific.

### 2.5 Coaching outcome evidence (high for calibration bounds)

| File | Role |
|---|---|
| `coaching_outcome_evidence.csv` | Program-level counts + selection notes |
| `coaching_outcome_rate_summary.csv` | Observed rates + Wilson 95% CIs |

Programs: SECL Ke Sushrut, Dr. B.R. Ambedkar IIT-NEET centres, Sigaram Free NEET Coaching.  
**Every row marks `causal_effect_usable = no`** — selection into free/intensive programs is extreme. Use only as **upper-bound / sensitivity** calibrators, never as P(admit | coaching).

Supporting corpus: Dakshana annual reports (~520 MB), Bihar Super-50 / CSRL / SATHEE page mirrors — narrative and occasional counts, not tidy outcome panels.

### 2.6 OSF aspirant microdata `tnh4x` (medium — mental health priors)

**File:** `data/external/osf/tnh4x/raw/Data_for_analysis.csv` (n=151)  
**Schema:** `Age`, `Gender` (0/1), `SES (5=highest…1=Lowest)`, item batteries + totals `ESS`, `PPE`, `GMS`, `DSHI`.

**Utility:** Kota-hostel convenience sample for stress / parental-expectation / NSSI **priors and narrative**. No NEET score, seat, or coaching-cost fields in the CSV. Do not produce individual suicide probabilities.

### 2.7 CBSE dummy-school registry (medium — school-pipeline risk)

**File:** `cbse_dummy_school_registry.csv` (25 schools)  
Schema: `school_name, location_raw, enforcement_outcome, allegation_type, source_wave, source_file`.

**Utility:** Qualitative/enforcement signal that “dummy affiliation” exists as a preparation pathway; too small for rates.

### 2.8 Employment / distribution benchmarks (medium — outcome layer stubs)

- `employment_benchmarks.csv` — graduate unemployment priors (ILO/IHD, Azim Premji, etc.)
- `published_estimates.csv` — 18 citation-ready scalars (candidates, seats, World Bank physician wages, WID shares, Rajan coaching shares, CMSE coaching-spend metadata)
- World Bank / WID PDFs under `data/external/` for source text

**Utility:** Validation targets and prior centres until PLFS microdata are registered and processed.

### 2.9 State portal crawls (medium — parsers not yet done)

- **Kerala CEE:** category/rank/allotment/last-rank pages + large BPL-scholarship PDF corpus
- **Tamil Nadu counselling:** HTML/PDF archive mirrors
- Mostly **document holdings**, not extracted tables

### 2.10 Weak / incomplete local holdings

| Holding | Status | Note |
|---|---|---|
| OpenICPSR E112992 | page + README only | Login/download not completed |
| NCRB ADSI | landing HTML + unrelated PDFs mixed in crawl | Need targeted ADSI yearbooks |
| NIRF medical rankings | HTML snapshots | College quality context only |
| Gated MoSPI/DHS microdata | absent | See `docs/GATED_NEXT.md` |

---

## 3. Preliminary statistics

### 3.1 NEET-2024 score ecology

| Statistic | Value |
|---|---|
| Rows | 2,333,162 |
| Centres | 4,750 |
| Mean / SD | 217.2 / 166.2 |
| Median | 163 |
| P10 / P25 / P75 / P90 / P95 / P99 | 50 / 87 / 313 / 484 / 570 / 657 |
| Skewness | +0.98 (right-skewed) |
| Scores &lt; 0 | 9,477 (0.41%) |
| Exact 720 | 61 |
| ≥600 / ≥650 | 81,550 (3.5%) / 30,204 (1.3%) |

**Histogram shares (approx.):** 0–99 ≈ 29%, 100–199 ≈ 28%, 200–299 ≈ 15%, 300–399 ≈ 10%, 400–499 ≈ 7%, 500–599 ≈ 6%, 600+ ≈ 3.5%.

**Centre heterogeneity:** mean-of-centre-means 212; SD of centre means ≈ 52; IQR of centre means ≈ 67. Only **one** centre with n≥100 has mean ≥400. Median centre size ≈ 467 candidates.

**State-of-centre means (selected):** highest — Chandigarh UT (~305), Rajasthan (~280), Haryana (~261); lowest — several Northeast UTs/states (~150–180) and Madhya Pradesh (~174). **Interpretation rule:** centre state ≠ candidate domicile; treat as exam geography only.

### 3.2 Seat scarcity (NMC snapshot × marks)

| Quantity | Value |
|---|---|
| NMC UG seats (sum `ugApproved`) | 129,602 |
| Colleges | 823 |
| Mean / median intake | 157 / 150 (max 250) |
| Government-like seats | 63,859 (49.3%) across 456 colleges |
| Private-like seats | 65,743 (50.7%) across 367 colleges |
| Mark-rows per NMC seat | **≈ 18.0** |
| NMC seats ÷ candidates ≥650 | ≈ 4.3 |

**Top seat states:** Karnataka (14,094), UP (13,425), Tamil Nadu (13,050), Maharashtra (12,824), Telangana (9,540).

These ratios bound the tournament; they are not admission probabilities (many seats are state-quota, category-reserved, or privately priced).

### 3.3 Tamil Nadu medium × government allotment

Aggregated ordinary-quota rates (Rajan Table 7.18):

| Period | English govt rate | Tamil govt rate | English∶Tamil rate ratio |
|---|---|---|---|
| Pre-NEET | 8.25% | 6.90% | **1.20** |
| Post-NEET | 9.50% | 4.34% | **2.19** |

Post-NEET years show persistently higher English∶Tamil ratios (peak **5.15** in 2017–18). Tamil applicant volume also collapses post-NEET (42,897 → 5,919 in the aggregated windows) — composition change and selection, not a clean ATE.

### 3.4 Coaching program outcome rates (selected, non-causal)

| Program / cohort | Outcome | Rate (Wilson 95% CI) |
|---|---|---|
| SECL Sushrut 2023–24 | NEET qualified | 97.5% (87–100%) |
| SECL Sushrut 2023–24 | MBBS admission | 27.5% (16–43%) |
| SECL Sushrut 2024–25 | NEET qualified | 77.5% (62–88%) |
| Ambedkar IIT-NEET centres 2024–25 | NEET qualified | 79.4% (73–85%) |
| Ambedkar IIT-NEET centres 2024–25 | MBBS admission | 7.2% (4–12%) |
| Sigaram Free 2018–19 | NEET qualified | ~16–17% |
| Sigaram Free 2020 | MBBS admission | 10.5% (3–31%), n=19 |

Spread across programs is enormous and tracks **selection intensity**, not a stable coaching treatment effect.

### 3.5 OSF Kota aspirant sample (n=151)

| Measure | Result |
|---|---|
| Age | mean 18.5 (SD 2.0), range 13–28 |
| Gender coding | 118 vs 33 (coded 0/1; confirm codebook before sex-labelled outputs) |
| SES | skewed toward lower/middle (40 / 31 / 45 / 22 / 13 for levels 1–5) |
| ESS / PPE / GMS / DSHI means | 48.4 / 29.8 / 11.9 / 1.62 |
| Any DSHI &gt; 0 | **45.7%** of sample |
| Notable correlations | ESS–PPE r≈0.44; ESS–DSHI r≈0.34; SES–DSHI r≈−0.12 |

Small, selected, cross-sectional — prior fodder only.

### 3.6 Other processed snapshots

- **Published estimates:** 18 rows covering candidates, centres, NMC seats, World Bank physician/engineer/nurse wages, WID top-1% shares, Rajan coaching/repeater shares among admitted TN students, CMSE coaching-spend metadata (unweighted subset).
- **Employment benchmarks:** graduate youth unemployment ~28.7% (15–29, ILO/IHD 2024) and ~40% (15–25, APU SOWI 2026 approx.) as prior centres.
- **CBSE dummy schools:** 25 enforcement-linked names (disaffiliation / show-cause style outcomes).

---

## 4. What the data can and cannot support

### Feasible now (with clear labels)

1. **Score ecology module** — national/centre/city distributions, scarcity vs NMC seats, sensitivity of “competitive band” cutoffs.
2. **Capacity module** — college × state × ownership seats; AIQ PDF extraction pipeline next.
3. **State inequality case study** — TN medium rates pre/post NEET as a documented structural break.
4. **Coaching sensitivity bounds** — wide priors from selected free/residential programs + CMSE spend metadata once microdata arrive.
5. **Outcome stubs** — published wage/unemployment benchmarks until PLFS is in-repo.

### Not supported by current local files

- Joint applicant-level `P(seat | score, coaching, income, caste, domicile, attempt)`
- Causal return to coaching or to barely clearing a cutoff
- National mental-health prevalence or individual risk scores
- Full state-quota admission reconstruction (Kerala/TN PDFs not yet parsed)
- Household consumption/wealth microsimulation (gated surveys not downloaded)

---

## 5. Recommended next analytic steps

1. **Reconcile** NEET row counts and centre lists against official NTA 2024 appeared/qualified figures; hash official PDFs where re-downloadable.
2. **Extract MCC 2024** seat-matrix and final-allotment tables into tidy CSVs (rank, category, institute, round).
3. **Parse Kerala** rank/allotment/last-rank pages into structured panels for the first state adapter.
4. **Fix NMC scrape consumers** to use `stateName` / `managementupdate` (older prelim script grouped null `state`/`management`).
5. **Register and download** HCES, CMSE, PLFS, NFHS, AIDIS per `docs/GATED_NEXT.md`.
6. **Complete OpenICPSR E112992** download after login (engineering-admissions replication as structural analogue).

---

## 6. Machine-readable companion

Regenerated summary JSON:

`data/processed/prelim_analysis/data_examination_summary.json`

Related existing artifacts: `neet_2024_marks_*.csv`, `published_estimates.csv`, `reports/INITIAL_FINDINGS.md`.

---

## Guardrails (unchanged)

- Do not infer caste, income, coaching, or domicile from test centre.
- Do not treat share-coached-among-admitted as coaching success probability.
- Do not label synthetic trajectories as causal effects.
- Do not emit individual suicide-risk probabilities from the OSF or NCRB materials.
