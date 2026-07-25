# Story readiness — what we can show, at what grain

**Date:** 2026-07-25  
**Thesis we are trying to show:** Medicine’s rewards are real (mobility, respect, security, income). Because seats are scarce, prep is expensive, and private capacity is unequally affordable, NEET functions as a **heavily taxing lottery that privilege can bias** — then launders the outcome as merit. The emotional story is cruelty, not “school is useless.”

**Primary interactive product:** [reports/interactive/the-accessible-seat.html](interactive/the-accessible-seat.html)  
**Reproduce numbers:** `make bayes && make privilege && make score-privilege && make story`

---

## Readiness legend

| Tag | Meaning |
|---|---|
| **SHOW** | Defensible in a public narrative with labeled assumptions |
| **SHOW†** | Showable, but grain is state/proxy/prior — do not nationalize casually |
| **SENS** | Show only as interactive sensitivity / prior sweep |
| **BLOCK** | Not identifiable yet; omit or show as explicit gap |
| **LATER** | Feasible after more wiring, not blocking the core story |

---

## Checklist by narrative beat

### 1. National scarcity ecology

| Claim | Grain | Status | Evidence |
|---|---|---|---|
| ~2.33M appeared (NEET-UG 2024) | National, cohort year | **SHOW** | Reconciled NTA counts |
| ~130k NMC MBBS seats; ~18 appeared / seat | National capacity accounting | **SHOW** | NMC snapshot + appeared; seat CI intentionally wide |
| Qualify rate ≈ 56% | National | **SHOW** | Complete counts; *not* the privilege outcome |
| Qualify ≠ seat | Conceptual | **SHOW** | ~10 qualified per seat |
| Cutoff as seats/appeared percentile | National accounting | **SHOW†** | Not state/category counselling pools |

**Verdict:** Ready to lead the story. Grain = national exam ecology for 2024.

### 2. “Accessible seat” as the right outcome

| Claim | Grain | Status | Evidence |
|---|---|---|---|
| Private offer without affordability ≠ access | Model identity | **SHOW** | Affordability filter in privilege + score models |
| Govt vs private *college* is not the wage story | Profession priors | **SHOW** | Shared physician wage prior; private buys access |
| Soft qualify threshold distracts from scarcity | National | **SHOW** | Ecology + narrative docs |

**Verdict:** Ready. This is the conceptual hinge of the piece.

### 3. Privilege → access ladder

| Claim | Grain | Status | Evidence |
|---|---|---|---|
| English vs Tamil govt allotment gap | Tamil Nadu, post-NEET years | **SHOW†** | Rajan panel; Bayesian ratio ~2.3×; holdout year higher absolute rates |
| Affordability roughly doubles access when private is in play | Synthetic strata | **SENS** | Accounting knob (~1.9× in privilege model) |
| Metro / intensive prep raise access further | Synthetic strata | **SENS** | Labeled knobs + coaching prior |
| Full ladder ~5× (top/bottom accessible) | Synthetic national score model | **SHOW†** | Score→rank→seat unilateral decomp ~5.5× |
| National causal English / caste / income effects | National joints | **BLOCK** | No applicant-level SES×score×seat file |

**Verdict:** Ready as a *calibrated synthetic ladder*, with TN medium as the only strongly observed access association. Do not sell strata as India-wide causal effects.

### 4. Score → rank → seat (why marks matter)

| Claim | Grain | Status | Evidence |
|---|---|---|---|
| Empirical marks distribution | National centres, 2024 | **SHOW** | ~2.33M anonymized marks |
| Small location shifts move mass near cutoffs | Model | **SHOW** | Score-privilege Monte Carlo |
| Centre geography ≠ domicile / SES | Guardrail | **SHOW** | Explicit prohibition |
| State quota / category cutoffs | State adapters | **LATER** | Kerala/MCC extracts exist; not yet in story UI |

**Verdict:** Ready for national accounting cutoffs. State counselling grain is the next upgrade.

### 5. Coaching arms race

| Claim | Grain | Status | Evidence |
|---|---|---|---|
| Private return β₁ > 0 (own prep raises absolute score) | Skeptical prior | **SENS** | Two-part θ + β log₂ spend; not NEET LATE |
| Positional externality β₂ < 0 (relative ranks) | Model encoding | **SHOW** | Relative shift = δᵢ − δ̄; everyone_* scenarios |
| Strategic response (families buy more prep) | External literature | **SHOW†** | Documented elsewhere; not estimated from NEET microdata |
| 98–99% of *admitted* were coached (TN) | Admitted composition | **SHOW** | Wrong denominator for P(seat\|coach) |
| National coaching LATE | Applicant microdata | **BLOCK** | Held out as PPC only |

**Verdict:** Ready as an *arms-race explainer* with prior toggles. Not ready as a causal coaching ROI calculator.

### 6. Attempts / years of trying

| Claim | Grain | Status | Evidence |
|---|---|---|---|
| 71% of *admitted* were repeaters (TN 2020–21) | Admitted | **SHOW** | Rajan |
| Applicant repeater share under ρ sensitivity | Algebraic | **SENS** | `attempt_repeater_sensitivity.csv` |
| Continuation-rate sitting histograms (low/central/high/TN-cal) | Labeled prior | **SENS** | `config/attempt_priors.yaml` · TN-cal pins P(K=1) to Rajan under ρ=1.75 |
| Ticket-cost trajectories (cash + opp cost + psych) | Scenario bands | **SHOW†** | `ticket_cost_summary.json` — honest ~1.4% first-sit access, not 0.01% |
| Bayes P(current-year \| TN admit) | Admitted TN | **SHOW†** | `tn_first_among_admitted_mbbs` from Rajan Table 7.38 |
| National admitted birth years / Class XII year | National | **BLOCK** | RTI Template 1b; TN current-year share is best proxy |
| Mean attempts / full histogram as national fact | National | **BLOCK** | Need NTA prior-appearances × Class XII year tables |
| Resource runway in microsim loop | Synthetic household | **LATER** | Formula + ticket bands exist; not full agent loop |

**Verdict:** Ready to teach the denominator trap, show **TN-calibrated** persistence, and price the ticket. Not ready to quote national mean attempts or birth-year histograms.

### 7. Earnings / life after the seat

| Claim | Grain | Status | Evidence |
|---|---|---|---|
| Medicine median ≫ engineering / law / no-college among employed | Profession priors + PLFS anchors | **SHOW†** | Monte Carlo; not causal return to NEET |
| Large zero-earnings mass (~45–55%) | Young-adult filter | **SHOW** | Family support / delayed independence — not street poverty |
| Wage gaps by caste / gender / parents’ income | Joint PLFS×admission | **BLOCK** | Privilege on access side only (for now) |
| Lifetime 35-year NPV with locked zeros | Projection choice | **BLOCK** | Explicitly discouraged |
**Verdict:** Ready for profession curves + zero-mass honesty. Not ready for demographic wage charts or causal “return to a seat.”

### 8. Full life-course microsimulation

| Claim | Grain | Status | Evidence |
|---|---|---|---|
| Synthetic population with linked stages | National | **LATER** | Scaffolding + MoSPI priors exist; joints still assumed |
| Causal RD of barely getting a seat | Local | **BLOCK** | No linked score–outcome panel |

**Verdict:** Not required to tell the access story. Do not wait for it.

---

## Overall distance to “showable”

| Layer | Distance | Notes |
|---|---|---|
| Exam scarcity + qualify≠seat | **0 — ship** | Strongest public facts |
| Accessible-seat framing | **0 — ship** | Conceptual + model filter |
| Privilege ladder (synthetic + TN medium) | **~1 — ship with footnotes** | Story-ready; label knobs |
| Coaching arms race | **~1 — ship as sensitivity** | Priors, not LATEs |
| Profession earnings + zeros | **~1 — ship with footnotes** | Projection, not causal |
| Attempts algebra | **~1 — ship as teaching tool** | Not mean attempts |
| State counselling realism | **~2 — partial data** | Kerala/MCC in repo, not in UI |
| Demographic wage inequality | **~4 — blocked** | Need joints |
| Causal coaching / seat returns | **~5 — blocked** | Need applicant panels / quasi-experiments |

**Bottom line:** We can already show the *core India narrative* at **national ecology + calibrated synthetic privilege strata + skeptical coaching priors + profession wage projections**. We cannot yet show **causal**, **demographic-wage**, or **full state-counselling** versions of the same story.

---

## Gaps filled in this pass

1. This readiness matrix (granularity + SHOW/SENS/BLOCK).
2. `scripts/build_interactive_story.py` — freezes story payload from model artifacts.
3. `reports/interactive/the-accessible-seat.html` — scrolly interactive telling the shippable India story.

## Gaps still open (do not fake)

- National P(seat | income, caste, gender, board, coaching, attempt).
- NEET coaching LATE.
- Mean attempt count.
- Earnings by identity groups for NEET pathways.
- State-by-state fee cliffs and category cutoffs in the interactive.