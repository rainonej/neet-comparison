# NCT Delhi data audit

This module asks what Delhi can add to the NEET life-course model beyond the Kerala and Tamil Nadu case studies. Delhi is unusually valuable because it has annual NTA applicant-state outcomes, anonymized 2024 scores at Delhi examination centres, recent household/student microdata that jointly observe coaching and household resources, a large Hindi/English school-language split, and public medical-admissions records spread across MCC, Delhi University, and GGSIPU.

It is **not** a single linked candidate file. Keep four different concepts separate:

1. Delhi as the applicant's reported state;
2. Delhi as the location of an examination centre;
3. school medium of instruction; and
4. NEET question-paper language.

None may be substituted for another without an explicit model assumption.

## What is committed

| File | What it contains |
|---|---|
| `data/processed/delhi/delhi_neet_state_results_2021_2026.csv` | Official annual Delhi registration, appearance, qualification and cutoff fields |
| `data/processed/delhi/delhi_cmse_2025_published_benchmarks.csv` | Published Delhi tutoring participation and expenditure benchmarks |
| `data/processed/delhi/delhi_school_medium_2019_20.csv` | Historical English/Hindi/Urdu school-enrolment margins |
| `data/processed/delhi/delhi_cmse_coaching_by_band.csv` | Weighted CMSE coaching rates and spend by enrolment band |
| `data/processed/delhi/delhi_cmse_coaching_by_consumption_quintile.csv` | Class X–XII coaching × Delhi consumption quintile (two-part margins) |
| `data/processed/delhi/delhi_cmse_coaching_by_school_type.csv` | Class X–XII coaching by school type |
| `data/processed/delhi/delhi_nss75_medium_coaching.csv` | Historical Hindi/English school medium × coaching |
| `data/processed/delhi/delhi_neet_2024_centre_score_summary.csv` | 2024 Delhi **exam-centre** score summaries |
| `data/processed/delhi/delhi_key_stats.csv` / `delhi_stats_summary.json` | Compact analysis outputs |
| `docs/delhi_source_catalog.csv` | Delhi-specific source and limitation registry |
| `scripts/process_delhi_state.py` | Reproducible local extraction of Delhi CMSE and NSS Education aggregates |
| `reports/DELHI_DATA_ANALYSIS.md` | Stats analysis and Bayesian / essay wiring recommendations |

Restricted unit microdata remain gitignored. Only weighted aggregate outputs should be committed after disclosure and sampling-error checks.

### Local extraction status (2026-07-26)

`python scripts/process_delhi_state.py` was run against the local CMSE 2025 and NSS Education 2017–18 archives. The all-enrolled coaching rate matched the published Delhi benchmark (0.391). Class X–XII quintile 3 was suppressed (&lt;30 unweighted). Source PDFs for the 2022 and 2026 NTA releases plus the CMSE published tables PDF were downloaded and hashed in `data/processed/download_manifest.csv`.

## 1. NEET outcomes

| Exam year | Registered | Appeared | Qualified | Appeared / registered | Qualified / appeared |
|---:|---:|---:|---:|---:|---:|
| 2021 | 34,520 | 31,202 | 23,554 | 90.4% | 75.5% |
| 2022 | 48,185 | 46,221 | 35,113 | 95.9% | 76.0% |
| 2023 | 55,890 | 54,701 | 39,764 | 97.9% | 72.7% |
| 2024 | 68,139 | 66,132 | 46,811 | 97.1% | 70.8% |
| 2025 | 63,046 | 61,199 | 40,331 | 97.1% | 65.9% |
| 2026 | 59,669 | 53,846 | 35,132 | 90.2% | 65.2% |

These are applicant-state aggregates, not centre-location counts. The 2024 row uses NTA's revised final July 26 result rather than the earlier provisional release.

### Do not interpret the qualification rate as a score trend

The qualifying threshold changes by year. For the UR/EWS category, the lower bound was 162 in 2024, 144 in 2025, and 213 in 2026. Therefore:

```text
qualified share != stable academic-performance measure
```

The annual table can support participation and administrative-outcome trends. Score-distribution comparisons require marks or percentile distributions and a common scale.

### 2024 centre-level scores

The court-ordered 2024 NTA release can be filtered to Delhi examination centres to estimate a Delhi-centre score distribution and within-city variation. This is useful for exploratory geography, but:

```text
Delhi examination centre != Delhi domicile
```

Candidates can sit outside their home state. Centre records must retain a field such as `geography_type=exam_centre`, never `domicile=Delhi`.

## 2. English, Hindi, and examination language

A historical UDISE+ 2019-20 transcription reports approximately:

| School medium | Enrolment | Share of the three reported media |
|---|---:|---:|
| English | 2,475,660 | 59.2% |
| Hindi | 1,677,233 | 40.1% |
| Urdu | 26,785 | 0.6% |

This table is useful as a population margin, not as a NEET result comparison. The committed source is a press transcription of UDISE+, so the archived primary table should be recovered before these counts are promoted to a model calibration target.

Three variables must remain distinct:

| Variable | Meaning | Public Delhi × score joint? |
|---|---|---|
| School medium | Language used by the school | No |
| NEET paper language | Language selected for the examination booklet | No |
| Coaching language | Language used by tutors/materials | No |

NTA publishes national language totals and state totals separately, but the standard result releases do not provide Delhi × paper language × score or qualification. National English/Hindi shares must not be applied to Delhi as though they were observed Delhi shares.

The NSS Education 2017-18 unit file does jointly observe school medium and private coaching. `scripts/process_delhi_state.py` produces historical Delhi Hindi/English medium × tutoring margins. Those estimates are still not NEET-specific and should be treated as a prior or contextual mechanism, not a direct test-score effect.

## 3. Tutoring and household resources

The 2025 Comprehensive Modular Survey on Education is the strongest Delhi source because student coaching and household consumption are observed in the same sampled households.

Published Delhi benchmarks include:

| Measure | Delhi estimate |
|---|---:|
| Enrolled students receiving private coaching, all levels | 39.1% |
| Higher-secondary students receiving private coaching | 59.2% |
| Mean annual private-coaching expenditure per enrolled student, all levels | ₹5,643 |
| Mean annual private-coaching expenditure per enrolled higher-secondary student | ₹12,891 |

The expenditure denominator is all enrolled students, not only students who received coaching. These averages therefore should not be compared directly to conditional spending among coached students.

### Reproducible microdata outputs

With the locally held CMSE and NSS Education archives, run:

```bash
python scripts/process_delhi_state.py
```

The script writes:

- `delhi_cmse_coaching_by_band.csv`;
- `delhi_cmse_coaching_by_consumption_quintile.csv`;
- `delhi_cmse_coaching_by_school_type.csv`; and
- `delhi_nss75_medium_coaching.csv`.

The consumption-quintile table estimates both the extensive and intensive margins:

1. probability of receiving any private coaching;
2. expenditure conditional on receiving coaching; and
3. coaching burden as annual coaching expenditure divided by annualized usual monthly household consumption.

Household consumption is a living-standard proxy, **not household income**. The preferred coaching model is a two-part or hurdle model:

\[
P(C_i > 0 \mid R_i, X_i)
\]

followed by

\[
\log C_i \mid C_i > 0 = \alpha + f(\log R_i) + \gamma X_i + \epsilon_i,
\]

where `R` is household resources and `X` includes school type, sex, social group, and other observed covariates. A spline or monotone function is preferable to assuming coaching expenditure rises linearly with resources.

### Sampling and disclosure cautions

Delhi is a small state/UT sample within national surveys. Before using generated cells:

- preserve survey weights;
- suppress cells with fewer than 30 unweighted observations;
- calculate replicate-weight or design-based standard errors when available;
- do not interpret a noisy quintile gradient as a precise causal elasticity;
- never commit household/person microdata; and
- label all CMSE tutoring as non-NEET-specific.

## 4. Medical-seat outcomes

Delhi admissions are not administered through one clean state portal. The reconstruction requires at least three adapters:

1. **MCC** for AIQ, central-university and related national pathways;
2. **Faculty of Medical Sciences, University of Delhi** for Delhi-quota eligibility and supporting materials; and
3. **GGSIPU** for MBBS Code 103 merit, allotment, cutoff, vacancy, fee and round records for affiliated institutions.

The target schema should preserve:

```text
admission_year
state_or_ut
authority
eligibility_basis
round
candidate_rank
neet_rank
candidate_category
quota
course
college_id
college_name
management_type
allotment_status
fee_category
source_document
source_page
```

This supports the distinction:

```text
qualified for NEET
    != received any medical seat
    != received an affordable government MBBS seat
```

Cross-authority college identifiers and quota labels need harmonization before Delhi can be compared with Kerala or Tamil Nadu.

## 5. What is and is not jointly observed

| Relationship | Directly observed? | Best source |
|---|---|---|
| Delhi applicant state × registered/appeared/qualified | Yes, aggregate | NTA annual results |
| Delhi exam centre × candidate score | Yes, anonymized for 2024 | NTA centre release |
| Coaching × household consumption | Yes, sampled households | CMSE 2025 |
| School medium × coaching | Yes, historical sampled students | NSS Education 2017-18 |
| School medium population margin | Yes, aggregate/historical | UDISE+ |
| Rank × college × quota × round | Yes, fragmented | MCC/FMSC/GGSIPU |
| Delhi domicile × score × school medium | No | Data request needed |
| Score × household resources × coaching spend | No | Candidate survey or administrative linkage needed |
| NEET paper language × Delhi score distribution | No | NTA custom tabulation/RTI needed |
| Attempt count × score × household resources | No | NTA/custom survey needed |

No public file found here contains:

```text
NEET score
+ Delhi domicile
+ paper language
+ school medium
+ household resources
+ coaching intensity
+ attempt count
+ final seat outcome
```

Synthetic joins must be labeled as model-generated and accompanied by sensitivity analysis over unknown correlations.

## 6. Recommended NTA data request

Request an anonymized Delhi applicant-state table at the finest safe grain:

- examination year;
- score band or anonymized score;
- percentile and All India Rank band;
- question-paper language;
- category and sex;
- first-time/repeater status or attempt number, if collected;
- Class XII board and school-state fields, if collected;
- appeared/absent and qualification status; and
- counselling data-sharing destination.

The minimum useful release is Delhi × paper language × score band × category. A state-by-language count without scores would answer composition but not the language-performance question.

## 7. Modeling status

| Component | Status | Use |
|---|---|---|
| Annual Delhi participation and qualification | SHOW | Descriptive applicant-state trend with cutoff warning |
| 2024 Delhi-centre score distribution | SHOW with caveat | Centre-location distribution only (median 213 vs national 163) |
| CMSE coaching/resource gradients | SHOW | Delhi tutoring-access prior; Q5/Q1 rate ≈1.75×, spend ≈4.1× |
| English/Hindi school-medium margin | SENS until primary table recovered | Synthetic-population calibration |
| NSS medium × coaching joint | SENS / mechanism prior | Historical; not NEET language or score |
| Medium effect on NEET score | BLOCK | No Delhi-linked score evidence |
| Coaching causal effect on score | SENS | Must borrow external evidence/prior |
| Delhi rank-to-seat pathway | BUILD | Public records exist but require multi-authority adapter |

**Bayesian model:** use Delhi for the two-part coaching × resources prior; do not replace Tamil Nadu medium–seat likelihoods.  
**Visual essay:** use for participation boom/retreat, tutoring–resource arms race, and qualified ≠ affordable seat; keep the English/Tamil knife-edge on TN evidence. Details in [reports/DELHI_DATA_ANALYSIS.md](../reports/DELHI_DATA_ANALYSIS.md).

## Sources

- NTA NEET public notices: <https://neet.nta.nic.in/document-category/public-notices/>
- NTA revised NEET-UG 2024 result: <https://www.nta.ac.in/Download/Notice/Notice_20240726213317.pdf>
- NTA NEET-UG 2026 key data, including 2025 comparison: <https://cdnbbsr.s3waas.gov.in/s37bc1ec1d9c3426357e69acd5bf320061/uploads/2026/07/202607161539405935.pdf>
- CMSE 2025 catalog and data dictionary: <https://microdata.gov.in/NADA/index.php/catalog/255>
- NSS Education 2017-18 catalog: <https://microdata.gov.in/NADA/index.php/catalog/151>
- UDISE+ portal: <https://udiseplus.gov.in/>
- Historical Delhi school-medium transcription: <https://indianexpress.com/article/cities/delhi/more-girls-than-boys-in-hindi-and-urdu-medium-schools-in-delhi-7387859/>
- MCC UG archive: <https://mcc.nic.in/archive-ug/>
- Faculty of Medical Sciences, University of Delhi: <https://fmsc.du.ac.in/index.htm>
- GGSIPU admissions archive: <https://ipu.ac.in/admission2025main.php>
