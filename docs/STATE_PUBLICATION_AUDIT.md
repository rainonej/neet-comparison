# State admissions publication audit

The state-level problem is not a total absence of data. It is a **fragmentation and schema problem**. Most counselling authorities publish enough documents to reconstruct ranks, seat availability, and allotments, but each authority uses different identifiers, PDF layouts, quota labels, archival conventions, and fee orders.

The first-pass audit is in `state_publication_audit.csv`.

## Recommended adapter sequence

1. **MCC national adapter** — establishes common college/course/category vocabulary and covers AIQ, central, deemed, and related national pathways.
2. **Kerala** — best first state adapter because the public archive commonly includes rank lists, category lists, allotments, vacancies, and last-rank tables.
3. **Delhi NCT** — high-value urban comparison with public cutoffs and allotments, but it requires a multi-authority adapter across MCC, Delhi University/FMSC, and GGSIPU.
4. **Gujarat** — category-specific merit lists and seat matrices make it suitable for testing reservation and state-quota logic.
5. **Tamil Nadu** — especially valuable for coaching/repeater and government-school policy context, but institution and quota rules are more complex.
6. **Maharashtra** — important large-state stress test after the common schema is stable because information is spread across multiple portal sections.

Delhi should be implemented after the MCC vocabulary because the same Delhi institution can appear in national and local pathways. Preserve `authority`, `eligibility_basis`, and `quota` separately rather than forcing every record into a single "Delhi quota" bucket.

## Common target schema

```text
admission_year
state
authority
eligibility_basis
round
candidate_rank
state_rank
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

Names and personal identifiers should not be retained unless indispensable for deduplication and legally redistributable. Prefer stable hashes created locally, then discard source names from processed outputs.

## What state lists still do not solve

Even excellent state publication does not normally provide family income, assets, parental education, coaching expenditure, school quality, attempt count, or later employment. State admissions data therefore improve the **rank-to-seat mechanism**, not the socioeconomic-selection model.

For Delhi specifically, NTA applicant-state totals, Delhi-centre score files, CMSE household/student records, school-medium aggregates, and counselling records are separate datasets. They must not be silently joined as though they describe the same candidates.
