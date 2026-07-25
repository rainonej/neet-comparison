# Gated and low-cost data acquisition checklist

Last audited: 2026-07-24

This document lists datasets that are relevant to the NEET life-course microsimulation but cannot simply be fetched anonymously. The order is intentional.

## Acquisition rules

For every source, preserve the **original archive exactly as downloaded**. Also download its questionnaire, schedule, codebook, sample-design document, multiplier/weight documentation, terms of use, and any readme. Do not extract and then discard the source ZIP.

Place originals under:

```text
data/external/<provider>/<dataset>/<wave>/raw/
```

Do not commit restricted or licensed microdata to a public repository. Register each file with `scripts/register_download.py`, which records its SHA-256 hash, size and provenance.

## Immediate public and author-request acquisitions

These now rank ahead of speculative government requests:

1. **OSF `tnh4x`:** ~~download~~ **done** (local CSV). Mental-health/demographics only; does not close coaching→seat.
2. **Coaching-gap public artifacts:** ~~download~~ **done** for Dakshana reports/JDST notice, CBSE dummy-school lists, TN rank/allotment PDFs. See `OPEN_DATA_DOWNLOADS.md`.
3. **Coaching-gap outreach (ask-for):** Dakshana JDST applicants, BSEB Super 50, SATHEE logs, CSRL, Careers360 raw survey — tracked in `COACHING_GAP_ASK_LIST.md` and `acquisition_tracker.csv` rows C1–C8.
4. **OpenICPSR E112992:** download the full Bagde–Epple–Taylor engineering-admissions replication package as an admissions/reservation analogue.
5. **Kerala CEE/KEAM:** archive medical rank, category, allotment, last-rank and vacancy records for 2019–2026.
6. **NIRF medical filings:** download institution submissions for every medical college, retaining aggregate economic/social challenge and outcome fields.
7. **Researcher requests:** contact the Alagappa University N=400 team, the Puducherry N=150 admitted-student team, the Guntur N=200 aspirant team, and the Kerala N=523 social-origin team. Use `RESEARCHER_OUTREACH_TEMPLATE.md`.
8. **Tamil Nadu committee trail:** request the deidentified analytical extract, codebook, tabulation workbook or scripts used by the A.K. Rajan Committee from DME/Selection Committee, School Education, M.G.R. Medical University and committee analysts. Public rank/allotment PDFs are already archived.
9. **Historical RTI replies:** recover the specific request IDs in `PUBLIC_RTI_ARCHIVE_LEADS.md`; these may contain old government tables without requiring a new politically sensitive request.

Do not download or retain named candidate records merely because they are publicly indexed. The project needs aggregate fields, not identities.

## Do these first: one free MoSPI account

A single free account at the MoSPI Microdata Portal unlocks most of the core Indian surveys. Download all files and documentation for:

1. **PLFS:** every annual wave from 2017-18 through 2023-24, calendar 2024, and calendar 2025. These are needed to pool rare occupations and estimate employment, unemployment, field mismatch, wage distributions and job formality for doctors, engineers, lawyers, nurses and other paths.
2. **HCES:** 2022-23 and 2023-24. These provide current household-consumption ranks and detailed affordability denominators.
3. **CMSE 2025:** the strongest current public source for private-coaching participation and expenditure.
4. **NSS Education 2017-18:** older, but unusually rich on school/course costs and expenditure on preparation for higher or additional studies.
5. **AIDIS 2019:** assets, debt, borrowing and wealth needed to decide whether a private seat is financially usable.
6. **Time Use 2019 and 2024:** study time, work, unpaid household labor and gendered opportunity costs.
7. **MIS 78th Round and CAMS 2022-23:** digital, transport, training and access conditions.
8. **ASUSE recent waves:** family-business and informal self-employment alternatives.
9. **NSS Health 2017-18:** lower priority, for family medical-shock burden and quality-of-life extensions.

The portal marks these studies as requiring login and offers free registration. The 2025 PLFS alone contains more than one million person records, while PLFS 2023-24 includes detailed occupation, education, activity, hours and wage variables. Keep the pre-2025 and revamped 2025 survey designs separate until harmonization is tested.

## Next: free applications at other archives

### DHS Program: NFHS-4 and NFHS-5

Request all India file families that are relevant to household construction:

- household recode;
- household-member recode;
- women and men files;
- GPS cluster files, under the separate GPS approval;
- questionnaires, recode manuals and geographic documentation.

Use the project description in `DATA_REQUEST_TEXT.md`. NFHS contributes assets, wealth rank, social group/caste, religion, education, family composition and district/cluster context.

### ICPSR: IHDS-I and IHDS-II

Download ICPSR studies **22626** and **36151**, including household, individual, eligible-women, birth-history, medical-facility, school, community and panel-linking files. Registration is free. These older surveys remain unusually valuable because they jointly observe household income, caste, schooling, fees, tutoring, siblings, occupations and wages.

### PRICE ICE 360

Create a PRICE account and request microdata for all four listed waves: **2014, 2016, 2021 and 2023**. The 2023 wave reports 40,000 households and covers measured household income, consumption, assets, debt, savings, education spending and labor participation. The site does not publicly state whether access is free, approved case-by-case or priced, so obtain the terms and quote before committing money.

### Young Lives India

Register with the host archive and download every public child, household, school, community and constructed longitudinal file for India. It is not nationally representative, but it is one of the best sources for aspirations, cognitive scores, household poverty, caste, parental investment and later transitions.

## Highest-value inexpensive requests: RTI

The 2026 NEET application replica shows that NTA directly collects fields including **mode of preparation, annual family-income band, both parents' occupation and qualification, place of residence, category, gender, question-paper medium, school type/board/state/district, and previous NEET appearance**. That means the joint information we thought did not exist may exist inside NTA's operational database.

Use the templates in `RTI_REQUEST_TEMPLATES.md` for:

1. NTA application/result schema and anonymized socioeconomic-score records or existing cross-tabulations;
2. MCC electronic allotment and actual-joining records;
3. NMC historical college capacity, ownership, fee, completion and attrition records;
4. separate state RTIs, beginning with Kerala, Gujarat, Tamil Nadu and Maharashtra.

The central RTI portal is restricted to Indian citizens. It also explicitly excludes state-government authorities. NTA states that its central RTI fee is ₹10; state procedures and fees vary.

## Low-cost paid sources

### EPWRF India Time Series — buy narrowly

Use pay-per-use only after the free microdata have been analyzed. Current charges are ₹20 per selected column for up to 200 lines and ₹10 for each additional 200 lines. Useful modules include state domestic product, price indices, consumption expenditure, employment, educational statistics, health statistics and tax-return statistics. Do not buy a broad annual module before identifying exact missing series.

### Indiastat Districts — wait until the table list is fixed

The official 15-day plan permits ten tables across 640 districts for ₹5,664 including GST in India, or $283 under its foreign price schedule. The 30-day plan permits 30 tables for ₹8,142 or $354. This is useful only for district series that remain unavailable from official sources.

### CMIE Consumer Pyramids — request a quote, do not buy yet

CPHS is potentially extremely valuable because it repeatedly observes household income, employment and highly detailed expenses, including education and private tuition. Current pricing is not public. Check institutional/library access and request an academic quote and variable dictionaries before spending personal money.

### AAMC custom report — U.S. comparison

Submit an aggregate request crossing family-income quintile, parental education, race/ethnicity, MCAT/GPA bands and applicant/matriculant status. AAMC says custom reports may carry a fee, which will be disclosed before acceptance.

## What to upload back

For each acquired source, upload the untouched source archive plus documentation. A good batch is:

```text
provider_dataset_wave_raw.zip
provider_dataset_wave_docs.zip
license_or_terms.pdf
```

Do not send passwords, account cookies, API keys, identity documents or RTI portal credentials. For restricted datasets, confirm that sharing the files with a collaborator is permitted; otherwise run the repository's future local extraction script and share only approved derived aggregates.

## Full machine-readable inventory

See `docs/gated_data_acquisition.csv` for every source, exact action, cost, variables, use and limitation.
