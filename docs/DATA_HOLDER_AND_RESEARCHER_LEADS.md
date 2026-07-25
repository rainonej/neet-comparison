# Data holders and researcher leads

This document records people and institutions that have either published a reusable dataset, analyzed unusually granular NEET-related records, or are plausible holders of non-public extracts. It is an outreach map, not a claim that every listed researcher can legally redistribute their raw data.

## Highest-priority leads

### 1. Susmita Biswas and Sucharita Maji — open aspirant microdata

Their 2026 study of NEET and JEE aspirants in residential hostels in Kota reports an anonymized dataset, codebook, methods, and measures in a public OSF project. The published sample contains 151 usable respondents (152 recruited) and measures perceived parental expectations, academic stress, mattering, non-suicidal self-injury, and demographics.

- Institution: Humanities and Social Sciences, IIT (ISM) Dhanbad
- Public project: `https://osf.io/tnh4x/overview?view_only=871cca8775f8420e802e172b5534673e`
- Corresponding author: Susmita Biswas, `23dr0189@iitism.ac.in`
- Immediate action: download the dataset and codebook; verify whether exam type distinguishes NEET from JEE and whether coaching duration, repeat status, gender, age, home state, or family background are present.

This is the strongest newly identified dataset because it is openly described as anonymized and accompanied by documentation.

### 2. Tamil Nadu A.K. Rajan Committee data chain — the best administrative insider route

The committee's report did not arise solely from public tables. It states that records were supplied by the Directorate of Medical Education and Selection Committee, School Education Department, Tamil Nadu Dr M.G.R. Medical University, and government coaching centres. Court reproductions of the report describe a detailed file for 2,583 government- and aided-school students who cleared NEET, including school type, social background, medium, gender, score ranges, and coaching information. Exact parental income was not available for that cohort.

Likely holders or former holders:

- Directorate of Medical Education, Tamil Nadu
- Selection Committee / Additional Directorate of Medical Education
- Tamil Nadu School Education Department
- Tamil Nadu Dr M.G.R. Medical University
- state government NEET coaching programme administrators
- committee members and analysts, including Justice A.K. Rajan, Dr G.R. Ravindranath, Prof L. Jawahar Nesan, and relevant department secretaries and medical-education officials serving on the committee

Immediate request should be narrow: ask for a deidentified analytical extract, codebook, tabulation workbook, or scripts used to produce the report—not the identifiable admissions file.

### 3. M. Sundarapandiyan and G. Kalaiyarasan — 400 NEET-oriented students

A 2026 CC BY study surveyed 400 Grade 11–12 students attending NEET-oriented streams or coaching centres in one urban South Indian district. It measured coaching intensity, repeat attempts, academic stress, exam anxiety, depressive symptoms, parental pressure, conflict, emotional support, and home environment.

- Institution: Department of Education, Alagappa University, Karaikudi, Tamil Nadu
- Study: *Psychosocial Consequences of NEET Preparation: Examining Stress, Anxiety, and Home Environment among Higher Secondary Students*
- DOI: `10.22159/ijoe.2026v14i2.58546`
- Immediate request: anonymized respondent data, questionnaire/codebook, district identity at the coarsest shareable level, NEET/JEE distinction if relevant, and exact definitions for coaching intensity and repeat attempts.

### 4. Rajalakshmi Mahendran, Shivayogappa S. Teli, and Sunil S. Shivekar — admitted-student academic records

Their retrospective study used records for 150 students admitted to MBBS in 2017–18 and linked NEET score, Class 12 performance, school board, demographics, and first-year MBBS outcomes.

- Institution: Sri Manakula Vinayagar Medical College and Hospital, Puducherry
- Immediate request: deidentified analytic file and variable definitions, especially school board/medium, category, gender, NEET marks, and first-year outcomes.
- Value: validates how much precise NEET-score variation predicts medical-school performance among admitted students.

### 5. Keerthana Vuppuluri and collaborators — 200 NEET aspirants

A 2023 study surveyed 200 students preparing for NEET-UG 2020 at a private junior college using the Westside Test Anxiety Scale and a demographic pro forma.

- Institution: Katuri Medical College and Hospital, Guntur, Andhra Pradesh
- Corresponding author listed in the paper: `vuppulurikeerthana@gmail.com`
- American-linked collaborator: Vijaya Krishna Prasad Vudathaneni has been affiliated with Albert Einstein College of Medicine, New York.
- Immediate request: deidentified survey data, demographic pro forma, coaching and preparation variables, and permission to use aggregates for model validation.

### 6. Sreekala Edannur and C. Rasak — Kerala social-origin dataset

Their study collected data from 523 SC, ST, and OBC students in Kerala enrolled in medical, engineering, paramedical, arts, and science programmes. Variables concern social origin, family social capital, networks, institution type, and programme selection.

- Affiliation at publication: Pondicherry University / Mahe Centre
- Study: *The Role of Social Origin and Social Capital in Accessing Higher Education by Backward Class Students of India*
- Immediate request: anonymized data and questionnaire, or at minimum cross-tabs separating medicine from engineering/paramedical/arts and science by caste, parental education, occupation, income/wealth proxies, school type, and institution ownership.
- Limitation: collected before the mature NEET regime, so it is a structural-access dataset rather than a direct NEET dataset.

## Public replication packages useful as methodological analogues

### Bagde, Epple, and Taylor

OpenICPSR hosts a public replication package for an Indian engineering-admissions study covering caste, gender, college quality, attendance, and academic success across more than 200 colleges. It is not medical admissions, but it provides a ready-made template for reservation cutoffs, marginal admissions, and outcomes.

- Project: `https://doi.org/10.3886/E112992V1`
- Use: validate admissions mechanisms, reservation logic, and Bayesian prior scales for differences in access and college quality.

### Surana and Rai

OpenICPSR also hosts code for a study of affirmative action and educational attainment among disadvantaged religious minorities in Andhra Pradesh.

- Project: `https://doi.org/10.3886/E230422V2`
- Use: methods and code patterns for subgroup exposure and educational-attainment outcomes.

## Public administrative sources that can substitute for private data

### Kerala CEE

The KEAM medical portal publishes rank lists, category lists, allotment lists, last ranks, MBBS vacancies, medical-allied outcomes, and notifications. These records can reconstruct the Kerala admission mechanism and validate simulated allotments, but they do not include family income, parental education, or coaching.

### NMC admitted-student uploads

NMC requires colleges to submit final admitted-student records. Publicly indexed files sometimes contain quota, category, gender, college, course, exam identifiers, names, dates of birth, or roll numbers. Only aggregate, deidentified extraction is permitted in this project. Identifiers must be discarded immediately and never linked to other sources.

### NIRF medical-college filings

NIRF institution submissions contain aggregate student counts by gender, in-state/out-of-state origin, economically backward status, socially challenged status, tuition reimbursement, graduation outcomes, placements, and sometimes median salaries. A national medical-college panel could validate socioeconomic composition and outcomes without individual records.

### Ministry of Education RTI archive

The public archive indexes historical NEET requests concerning candidate score bands, category lists, family financial status, government coaching expenditure, private coaching-centre counts, and state seat inventories. Reply attachments are inconsistently indexed. The request IDs should be used to ask the ministry or original applicants for archived replies.

## Commercial and community-built admissions databases

- RankerCentral claims a cleaned database of more than one million allotments across states, derived from government PDFs. Request an export, data dictionary, years, and license rather than scraping an interactive product blindly.
- NeetLogiq publishes MCC/KEA/INI-CET admissions information and may have normalized historical records.
- Public college-predictor repositories can reveal parsing code and cleaned cutoff tables. Every record must be traced to an official PDF before use.
- Synthetic Kaggle “college admission” datasets must not be mistaken for observed NEET data.

## Coaching-gap program holders (added 2026-07-25)

These are now the highest-value requests for the preparation → score → seat link. Full variable lists and send order: [COACHING_GAP_ASK_LIST.md](COACHING_GAP_ASK_LIST.md).

### Dakshana Foundation — scored JDST selection

Public annual reports and the JDST 2024 notification are already archived under `data/external/dakshana/raw/`. What is still missing is the **all-applicant** file (selected and rejected) with JDST scores, cutoffs, and final NEET/seat outcomes for a fuzzy cutoff design.

- Site: `https://www.dakshana.org/`
- Contact route: `scholarship@dakshana.org` / institutional research channel
- Request: deidentified applicants near JDST cutoffs, not scholar success stories

### BSEB Super 50

Free residential/non-residential JEE–NEET coaching with an entrance test. The coaching portal returned **404** on 2026-07-25; news mirrors are archived under `data/external/bihar_super50/raw/`. Prefer a university evaluation partnership before the next cohort finishes NEET.

### SATHEE (IIT Kanpur)

Public platform pages archived; student-level usage logs are not public. Best continuous dose-response target (watch time, practice, mocks, school rollouts). Contact the SATHEE project team / Prof. Amey Karkare.

### CSRL Super 30

Public program pages only. Request applicant test/interview scores, centre thresholds, and outcomes across centres.

### Careers360 2022 preparation survey

Published charts exist; raw N≈717 file and branching logic still need a vendor request. Severe selection: many non-admits skipped preparation questions.

## Outreach order

1. OSF project — **done** (downloaded; mental-health fields only).
2. **Dakshana JDST applicant extract** (coaching-gap #1).
3. **BSEB Super 50** partnership / extract.
4. **SATHEE** schema + rollout feasibility.
5. CSRL; Careers360 raw survey.
6. Contact the four direct study teams (Alagappa, Puducherry, Guntur, Kerala social-origin) with concrete, minimal data requests.
7. Contact Tamil Nadu committee members and administrative data holders for the analytical extract or tabulation workbook used in the report; public rank/allotment PDFs already archived.
8. Build Kerala CEE, NMC aggregate, and NIRF panels from public records.
9. Contact commercial coaching platforms and database builders last.
10. Use forums only to locate documents, original RTI applicants, or researchers—not as statistical evidence.

## What not to request

Do not request or accept names, phone numbers, exact dates of birth, addresses, roll numbers, application numbers, or other identifiers. The useful unit is an anonymized candidate or an aggregate cell. A dataset being downloadable somewhere does not establish that it may lawfully or ethically be redistributed.
