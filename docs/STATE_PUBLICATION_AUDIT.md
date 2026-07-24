# State admissions publication audit

The state-level problem is not a total absence of data. It is a **fragmentation and schema problem**. Most counselling authorities publish enough documents to reconstruct ranks, seat availability, and allotments, but each authority uses different identifiers, PDF layouts, quota labels, archival conventions, and fee orders.

The first-pass audit is in `state_publication_audit.csv`.

## Recommended adapter sequence

1. **MCC national adapter** — establishes common college/course/category vocabulary and covers AIQ, central, deemed, and related national pathways.
2. **Kerala** — best first state adapter because the public archive commonly includes rank lists, category lists, allotments, vacancies, and last-rank tables.
3. **Gujarat** — category-specific merit lists and seat matrices make it suitable for testing reservation and state-quota logic.
4. **Tamil Nadu** — especially valuable for coaching/repeater and government-school policy context, but institution and quota rules are more complex.
5. **Maharashtra** — important large-state stress test after the common schema is stable because information is spread across multiple portal sections.

## Common target schema

```text
admission_year
state
authority
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
