# Public data mirrors and provenance audit

This audit distinguishes lawful public records and research deposits from unverifiable or privacy-invasive copies.

## Tier 1 — primary or openly deposited data

| Source | Contents | Use | Status |
|---|---|---|---|
| NTA 2024 centre-wise score release | anonymized marks by centre serial number | empirical score distribution and geographic validation | official PDFs were public; preserve checksums and extraction code |
| OSF project `tnh4x` | anonymized NEET/JEE aspirant survey, codebook, methods | mental-health and parental-pressure model | openly described by the authors; download manually if automated access fails |
| Kerala CEE/KEAM | rank, category, allotment, last-rank and vacancy publications | Kerala admissions adapter | public official records |
| MCC archive | national-quota seat matrices and allotments | AIQ/deemed/central admissions | public official records |
| NMC college/course search | college ownership, intake and recognition | supply model | public official records |
| NIRF submissions | institution-level student composition and outcomes | socioeconomic and outcome validation | public institution filings |
| OpenICPSR replication packages | Indian engineering admissions and affirmative-action research data/code | methodological analogue | public research deposits |

## Tier 2 — reproducible third-party reconstructions

The `hq969/neet-2024-center-marks` repository documents how official NTA centre PDFs were downloaded and converted into CSV/SQLite records. Treat it as a reconstruction, validate counts and hashes, and retain the official source URLs in provenance metadata.

Commercial or community databases such as RankerCentral, NeetLogiq, and college-predictor repositories may save substantial extraction work. Before use, require:

- source PDF identifiers;
- extraction date and year coverage;
- field definitions;
- duplicate and correction rules;
- license for research reuse;
- evidence that personal identifiers have been removed.

## Tier 3 — discovery-only sources

Forums, Reddit, Telegram references, coaching advertisements, and student discussion boards may reveal filenames, broken government links, coaching cohorts, or names of report authors. They are not evidence for probabilities unless traced to a primary record or a documented sample.

## Rejected or quarantined sources

- synthetic “realistic” admissions datasets;
- files offered through credential sharing or bypassed access controls;
- identifiable candidate spreadsheets without clear public authority and research purpose;
- datasets with no provenance or definitions;
- screenshots of tables when the underlying official record is available.

## Privacy rule for public candidate records

Some public admission lists contain personal information. Public visibility does not make identifiers analytically necessary. Extraction must:

1. read the record in a temporary workspace;
2. retain only permitted fields such as year, state, college, course, quota, category, gender, rank band, and outcome;
3. remove names, dates of birth, phone numbers, addresses, application numbers, roll numbers, and exact identifiers;
4. aggregate small cells before distribution;
5. delete the identifiable intermediate file when legally and technically appropriate.

The repository must never publish a re-identification key or join a named candidate across datasets.
