# Attempt / retake priors

**Status:** National `P(sittings = 1,2,3,…)` is **not observed**.  
**Reproduce:** `make attempt-priors`  
**Config:** `config/attempt_priors.yaml`

## What we do know

| Fact | Grain | Use |
|---|---|---|
| TN admitted “other than current year” → 71.4% (2020–21) | Admitted, state | Composition anchor; wrong denominator for applicants |
| TN repeater share rose sharply post-NEET (12% → 71%) | Admitted, state/year | Hierarchical heterogeneity is real — no single national “~1/3 retake” |
| Selected AIIMS-Bhopal admission sample ~66% first-attempt (verify primary) | Admitted, elite | Lower-persistence bound among winners; not applicant pop |
| Stress higher among repeat aspirants (Alagappa / district surveys) | Convenience | Supports rising psych-exit hazard; not a stop probability |
| CMSE / HCES / AIDIS / PLFS / TUS | National surveys | Build **resource runway** synthetically; not linked to NEET IDs |

NTA public releases do **not** publish attempt counts or age. DOB almost certainly exists in applications (Aadhaar / Class X consistency rules). Class XII completion year would be more useful than age alone.

## Exit rule (do not get this wrong)

Stopping after “qualify” is wrong. Exit on success =

**accepted / joined an acceptable seat**

Someone who qualifies but gets no MBBS seat, only an unaffordable private seat, or a course they refuse may sit again.

## Model (not geometric)

After each sitting, competing risks:

- acceptable seat joined  
- repeat next year  
- alternative education  
- employment  
- resource-constrained exit  
- psychological / voluntary exit  

Continuation probability should **decay** with attempt number, age / years since Class XII, resource runway, and score-gap to target. A constant geometric `q` is a bad default.

### Resource runway

\[
R = \log\frac{\text{liquid} + \text{expected disposable over 1y} + \text{borrowing capacity}}{\text{repeat-year burden}}
\]

Burden ≈ coaching + materials + travel + hostel/relocation + incremental living + opportunity cost.  
Do **not** treat full home/land value as cash; sensitivity at 0% / 10% / 20% pledgeable illiquid wealth.

## Weak prior used in-repo

Priors are on **continuation rates** \(r_t = P(\text{sit again} \mid \text{reached sitting } t)\), then mapped to a sitting histogram.

| Scenario | \(r_1\) | \(r_2\) | \(r_3\) | \(r_{4+}\) | Mean sittings | Role |
|---|---|---|---|---|---|---|
| Low | 0.30 | 0.20 | 0.15 | 0.10 | ~1.37 | Unanchored sensitivity |
| Central | 0.50 | 0.33 | 0.25 | 0.17 | ~1.72 | Unanchored sensitivity |
| High | 0.70 | 0.50 | 0.35 | 0.25 | ~2.21 | Unanchored sensitivity |
| **TN post-NEET calibrated** | ≈0.59 | decays | … | … | ~1.9 | Default story: matches Rajan \(r=0.7142\) under ρ=1.75 |

**Calibration rule:** given admitted repeater share \(r\) and labeled ρ,

\[
a = \frac{r}{r + \rho(1-r)}, \quad r_1 = a,\quad P(K=1)=1-r_1
\]

Later \(r_t\) decay as fractions of \(r_1\). This pins the binary first vs ≥2 split to TN admitted composition; it does **not** identify national attempt counts.

Beta hyperparameters live in the YAML (means near the calibrated \(r_1\)). Report scenario sweeps, not a single “NEET mean attempts” number.

### Ticket cost (paired artifact)

`make attempt-priors` also writes `ticket_cost_summary.json`: first-sit vs two-drop-year trajectories with cash (CMSE / Rajan), opportunity cost (PLFS no-college), psych/life notes, and score-model `p_accessible_seat`. Honest low-privilege first-sit access is ~**1.4%**, not 0.01%.

Artifacts: `attempt_continuation_scenarios.csv`, `attempt_sitting_distributions.csv`, `rajan_repeater_by_year.csv`, `ticket_cost_*.csv/json`.

## How to get better data (priority order)

1. **NTA aggregate / RTI** — counts by prior appearances (0–4+), Class XII year, age band, score band, state, sex, category, qualify status. Ask whether a persistent candidate ID exists across years. Template: [RTI_REQUEST_TEMPLATES.md](RTI_REQUEST_TEMPLATES.md) § Template 1b.
2. **NMC admitted DOB** — age-at-admission among joiners only (selected).
3. **Age mixture fallback** — if NTA gives age but not attempts, mix current-XII age density shifted by years-since-XII (noisy).
4. **Original event-history survey** — must include stoppers, not only coaching centres / admits.
5. **External analogs** (CSAT older-candidate stock; MCAT multi-sit tail) — prior triangulation only.

## Relation to ρ-sensitivity

`attempt_inference.py` still backs out `P(repeater | applicant)` from Rajan’s admitted repeater share under labeled ρ. That is a **binary** first vs ≥2 split. Continuation scenarios supply the **full sitting histogram** under explicit decay assumptions. The TN-calibrated scenario is the hinge between those two. Neither identifies the national truth alone.

## Bayesian wiring

`model.py` updates `tn_first_among_admitted_mbbs` from Rajan Table 7.38 post-NEET year shares (small ESS). Posterior mean is the epistemic summary of **P(current-year | TN MBBS admit)** — a proxy that most winners are older than first-sit school-leavers, not national DOB microdata.
