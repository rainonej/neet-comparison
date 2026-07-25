# Coaching-gap datasets: ask-for list

Last updated: 2026-07-25

This is the outreach queue for datasets that would tighten the weakest empirical link:

**baseline ability/resources → preparation dose/type → NEET score/rank → government/private/no seat**

Public material already downloaded is summarized in [OPEN_DATA_DOWNLOADS.md](OPEN_DATA_DOWNLOADS.md). Use [RESEARCHER_OUTREACH_TEMPLATE.md](RESEARCHER_OUTREACH_TEMPLATE.md) for emails. Do not request names, phone numbers, addresses, DOBs, or exam roll numbers.

## Priority ask-for queue

| Priority | Holder | What to request | Why | Status |
|---|---|---|---|---|
| 1 | **Dakshana Foundation** | Deidentified **all-applicant** extract around JDST cutoffs: JDST scores, shortlist/interview/offer/acceptance, Class 10–12 marks, school type/board/state, income band, category, gender, prior NEET attempts, mock/attendance history, final NEET marks/percentile/AIR, counselling participation, government MBBS / private / BDS / veterinary / no-seat | Best existing scored-selection design for intensive residential coaching | `not_requested` — public aggregates + JDST rules already archived |
| 2 | **BSEB Super 50** | All applicants: entrance score/rank, centre/stream/cutoff, selection/waitlist/acceptance, residential flag, Class 10–12 results, attendance/internal tests, NEET registration/attempts/score/rank, counselling/admission | State admin pipeline with school baseline + entrance cutoff + multi-year coaching | `not_requested` — coaching portal currently 404; news mirrors archived only |
| 3 | **SATHEE / IIT Kanpur** (Prof. Amey Karkare / project team) | Event-log schema, school-rollout dates, deidentified usage/mock trajectories, feasibility of linking consenting users to NEET results | Best continuous preparation-dose source (hours, practice, mocks, timing) | `not_requested` — public platform page archived only |
| 4 | **CSRL Super 30** | Applicant written-test/interview scores, centre/sponsor, selection threshold, offer/acceptance, attendance, final score/rank/admission | Multi-centre scored-selection analogue to Dakshana | `not_requested` — public program page archived only |
| 5 | **Careers360** | Raw 2022 NEET preparation survey (N≈717), questionnaire, branching logic; any unsuccessful-candidate follow-ups; score/rank if available | Already collected fees/hours/mode/timing, but selection bias is severe | `not_requested` — article page archived only |
| 6 | **Tamil Nadu Selection Committee / DME** | Deidentified applicant→allotment spine beyond public PDFs: attempts, income/eligibility fields, school background, coaching flags if collected; plus A.K. Rajan Committee analytical extract | Best score→seat outcome spine; public rank/allotment PDFs already downloaded | public lists `downloaded`; richer fields `not_requested` |
| 7 | **CBSE** | Student-level attendance / dummy-enrolment records if any research extract exists; otherwise school affiliation codes for enforcement lists | Public school-level enforcement registry is already built; individual exposure still missing | school registry `downloaded`; microdata `not_requested` |
| 8 | **ALLEN / Aakash / Physics Wallah** | Anonymized preparation histories: fees, hours/mode, mock trajectories, dropper status, final NEET outcomes for research under NDA | Enormous dose datasets, commercially sensitive and strongly selected | `not_requested` |

## Also ask (login/account, not personal email)

These do **not** close the coaching→seat link alone, but fill household/coaching-spend priors. Tracked in [GATED_NEXT.md](GATED_NEXT.md) and `acquisition_tracker.csv` (A1–A15):

- MoSPI: PLFS, HCES, **CMSE 2025**, NSS Education, AIDIS, Time Use
- DHS: NFHS-4/5
- ICPSR: IHDS I/II; OpenICPSR E112992
- Young Lives India; PRICE ICE 360 (confirm terms)

## Exact variables to request (copy into outreach)

### Dakshana / Super 50 / CSRL (program-selection design)

For **every applicant**, not only scholars:

1. Application ID (arbitrary research ID; not phone/Aadhaar/roll)
2. Selection-test total and section scores
3. Applicable cutoff, shortlist status, interview score/recommendation
4. Offer, acceptance, centre, residential vs non-residential
5. Class 10–12 marks; school type, board, state/district
6. Income band, category, gender
7. Prior NEET attempts and scores (if known)
8. Attendance / mock-test history during coaching (if retained)
9. Final NEET marks, percentile, AIR, category rank
10. Counselling participation and seat outcome class: govt MBBS / private MBBS / BDS / veterinary / none

A narrow bandwidth around the cutoff is enough for a first design.

### SATHEE (dose-response design)

1. Registration date; declared exam; dropper flag
2. Baseline diagnostic / early mock score
3. Videos opened, minutes watched, question attempts/accuracy
4. Mock scores over time; live-class attendance; language
5. School or rollout cohort; inactivity spells
6. Linked NEET result **only with consent**
7. School-by-school rollout / capacity rules for quasi-experimental exposure

## Already obtained (do not re-request)

| Artifact | Local path (gitignored raw) | Use |
|---|---|---|
| OSF Kota aspirant microdata | `data/external/osf/tnh4x/raw/` | Psychosocial priors; not coaching→seat |
| Dakshana annual reports AR07–AR24 + JDST 2024 notification | `data/external/dakshana/raw/` | Aggregate scholar outcomes + selection rules |
| CBSE dummy/disaffiliation press + HTML lists | `data/external/cbse/raw/` | School-level dummy-school exposure proxy |
| CBSE school registry (derived) | `data/processed/cbse_dummy_school_registry.csv` | Join key for school-level analyses |
| TN Selection Committee MBBS/BDS rank & allotment PDFs | `data/external/tamil_nadu/counselling/raw/` | Score→seat mechanism (**strip identifiers before any processed export**) |
| SATHEE / CSRL / Bihar news mirrors | `data/external/sathee/`, `csrl/`, `bihar_super50/` | Outreach context only |

## Recommended send order

1. Dakshana (cutoff applicant extract)
2. BSEB Super 50 evaluation partnership (prospective if portal remains closed)
3. SATHEE/IIT Kanpur (schema + rollout feasibility)
4. CSRL
5. Careers360 raw survey
6. Tamil Nadu DME/Selection Committee (deidentified spine + Rajan extract)
7. Commercial coaching platforms last
