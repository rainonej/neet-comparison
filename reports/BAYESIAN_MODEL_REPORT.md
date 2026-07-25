# Bayesian evidence model — full report

**Date:** 2026-07-25  
**Model version:** 0.3.0 (`config/bayesian_priors.yaml`)  
**Default profile:** conservative  
**Assumption:** no additional gated microdata (PLFS / HCES / NFHS / AIDIS / OpenICPSR) for this pass.

## Bottom line

With only the public processed evidence already in-repo, a conjugate Bayesian layer is enough to pin down **national qualification and scarcity**, document a **large Tamil Nadu medium gap**, keep **coaching as a prior sensitivity (not a fitted treatment effect)**, and produce **career earnings ranges that include large zero-earnings mass**. Prior-profile choice barely moves quantities backed by complete counts; it mainly changes the coaching score-shift prior and the width of weakly identified employment posteriors.

Reproduce with:

```bash
make bayes
# or: python scripts/run_bayesian_model.py
```

Artifacts:

| File | Role |
|---|---|
| `data/processed/bayesian/posterior_summary.csv` | All posterior means / CIs / ESS by profile |
| `data/processed/bayesian/profile_comparison.csv` | Material conclusion table across profiles |
| `data/processed/bayesian/ppc_coaching.csv` | Coaching-cohort PPC residuals (no effect update) |
| `data/processed/bayesian/bayesian_results.json` | Compact machine-readable summary |

---

## 1. What was built

The project already had Bayesian *primitives* (`BetaEvidence`, `DirichletEvidence`, `TruncatedNormalEvidence`) and career-path Monte Carlo. This pass wired them into an end-to-end evidence update:

| Module | Purpose |
|---|---|
| `src/neet_microsim/priors.py` | Load neutral / conservative / reasonable profiles |
| `src/neet_microsim/evidence.py` | Read processed CSVs into typed evidence objects |
| `src/neet_microsim/model.py` | Fit posteriors, holdout check, PPC, profile comparison |
| `scripts/run_bayesian_model.py` | CLI entry point (`make bayes`) |

Design rules followed from `docs/BAYESIAN_MODEL.md`:

1. Complete same-population counts update at full weight.  
2. Proxies enter only through low effective sample size (ESS).  
3. Selected coaching cohorts are **posterior-predictive checks**, never treatment-effect updates.  
4. Absent field-specific employment evidence stays pooled to broad graduate rates (neutral on field).  
5. All three prior profiles remain runnable; the report shows how little vs how much they move.

---

## 2. Evidence used (and refused)

### Used

| Quantity | Source | Evidence class | Weight |
|---|---|---|---|
| NEET 2024 qualify rate | 1,315,853 / 2,333,162 | same-population complete counts | full |
| MBBS seats per appeared | 129,602 NMC seats / 2,333,162 appeared | capacity accounting | snapshot ESS ≈ 30 + prior ESS |
| TN govt allotment by medium | Rajan Table 7.18 post-NEET years except holdout | same-exam state complete counts | full on calibration years |
| MCC AIQ course mix | 57,873 tidy allotment rows | counselling complete counts | full |
| Graduate unemployment | ILO/IHD 28.7%; APU age bands ~40% / ~20% | India graduate proxy | suggested ESS 8–12 |
| Formal employment share | ILO/IHD 36.1% | weak prior center only | ESS 6 |
| Physician / engineer / nurse wages | World Bank PLFS-based monthly means | earnings anchors | median≈mean/1.15; geom. SD 1.75 |
| Coaching score shift | profile priors (0 / 0.08 / 0.14 SD) | prior | not updated by cohorts |

### Held out / validation only

- Tamil Nadu year **2020–2021** (last post-NEET year in the panel).  
- All coaching program cohorts in `coaching_outcome_rate_summary.csv`.

### Explicitly not used as causal updates

- Share coached among admitted TN students (composition, not effectiveness).  
- SECL / APSWREIS / Sigaram outcome rates as coaching LATEs.  
- Centre-of-exam geography as SES, caste, or domicile.  
- OSF Kota psychosocial sample for individual risk probabilities.

---

## 3. Posterior results (default: conservative)

### 3.1 National exam ecology

| Quantity | Posterior mean | 95% CI | ESS |
|---|---|---|---|
| NEET qualify rate | **0.5640** | 0.5633 – 0.5646 | ~2.33e6 |
| NMC MBBS seats / appeared | **0.0555** | 0.0064 – 0.1523 | 34 |
| Appeared per MBBS seat | **18.0** | — | derived |
| Qualified per MBBS seat | **10.2** | — | derived |

Qualification is essentially known once the reconciled NTA counts are accepted. Capacity is intentionally *not* given a 2.3-million-trial likelihood: the NMC page is a dynamic snapshot, so uncertainty remains wide even though the point rate is ~5.6%.

Interpretation: among people who appeared, roughly one MBBS seat exists for every 18 appeared candidates, and about 10 students qualify for each seat. This is scarcity accounting, not `P(offer | applicant, score, category, domicile)`.

### 3.2 Tamil Nadu medium (state case, not national)

Calibrated on post-NEET years except 2020–21; prior centers taken from pre-NEET rates.

| Quantity | Posterior mean | 95% CI |
|---|---|---|
| English-medium govt allotment rate | 0.0877 | 0.0859 – 0.0896 |
| Tamil-medium govt allotment rate | 0.0373 | 0.0322 – 0.0427 |
| English / Tamil rate ratio | **2.35** | — |

Holdout year 2020–21 observed rates were higher (English 0.123, Tamil 0.078). Absolute errors ≈ 0.036 and 0.041. The **direction and rough magnitude** of the English advantage are stable; the holdout year is more favorable overall than the earlier post-NEET average. Do not export this ratio as a national causal medium effect.

### 3.3 MCC AIQ / deemed / central course mix

Among 2024 tidy allotment rows:

| Course family | Posterior share |
|---|---|
| MBBS | 0.848 |
| BDS | 0.130 |
| Nursing | 0.022 |
| Other | ≈ 0 |

This describes the MCC counselling stream only, not state-quota seats.

### 3.4 Career paths (broad graduate employment + wage anchors)

Employment given labor-force participation is pooled to graduate benchmarks (~0.71 mean, ESS 22–30). No field-specific NEET employment panel was available, so medicine and engineering share the same employment posterior and differ mainly through completion / match priors and wage anchors.

Monte Carlo one-year summaries (conservative, 40k draws; includes zeros):

| Path | Mean annual earnings (INR) | Zero-earnings share |
|---|---|---|
| Medicine | ~3.11e5 | ~0.45 |
| Engineering | ~2.15e5 | ~0.50 |
| Other graduate | ~1.07e5 | ~0.54 |

Medicine − engineering mean gap ≈ **₹96k / year** under these assumptions. That gap is **not** an identified causal return to NEET admission: it mixes World Bank occupation wages, weak completion/match priors, and graduate unemployment proxies. The important robust feature is the **large zero-earnings mass** once non-completion, non-participation, and unemployment are retained.

---

## 4. Prior-profile sensitivity

| Quantity | Neutral | Conservative | Reasonable | Moves? |
|---|---|---|---|---|
| Qualify rate | 0.5640 | 0.5640 | 0.5640 | No (counts dominate) |
| Seats / appeared | 0.0555 | 0.0555 | 0.0555 | Point rate fixed; CI width shrinks slightly with stronger prior ESS |
| TN eng/tam ratio | 2.35 | 2.35 | 2.35 | No material change |
| Coaching shift prior mean (SD) | 0.00 | 0.08 | 0.14 | Yes — by construction |
| Medicine mean earnings | 3.10e5 | 3.11e5 | 3.09e5 | Negligible vs model uncertainty |
| Medicine zero-earnings share | 0.45 | 0.45 | 0.45 | Stable |

**Conclusion:** for the quantities identified by administrative counts, the three profiles agree. Sensitivity work should focus on coaching score-shift scenarios and on household/labor microdata still blocked behind login—not on re-tuning the national qualify rate.

---

## 5. Coaching posterior-predictive checks

Coaching score-shift remains a truncated-normal **prior**. Cohorts were compared to national qualify / capacity posteriors without updating that prior.

| Cohort | Outcome | Observed | National reference | Observed − predicted | Selection |
|---|---|---|---|---|---|
| SECL 2023–24 | qualify | 0.975 | 0.564 | +0.41 | very strong |
| SECL 2023–24 | MBBS | 0.275 | 0.056 | +0.22 | very strong |
| APSWREIS 2024–25 | qualify | 0.794 | 0.564 | +0.23 | very strong |
| APSWREIS 2024–25 | MBBS | 0.072 | 0.056 | +0.017 | very strong |
| Sigaram 2018 | qualify | 0.167 | 0.564 | −0.40 | low |
| Sigaram 2019 | qualify | 0.163 | 0.564 | −0.40 | low |
| Sigaram 2020 | qualify | 0.474 | 0.564 | −0.09 | low |
| Sigaram 2020 | MBBS | 0.105 | 0.056 | +0.05 | low |

Reading:

- Intensive, entrance-selected residential programs sit far above national qualify rates. Treating that gap as a coaching treatment effect would be wrong.  
- Open-access Sigaram cohorts sit far *below* national qualify rates in 2018–19, then closer in 2020 with a small MBBS count.  
- No single coaching shift can jointly reproduce elite selected programs and open-access government-school cohorts. That is an intended validation failure mode from `docs/VALIDATION_PLAN.md`, and the PPC confirms it.

---

## 6. What the posterior does and does not answer

### Answers (under stated assumptions)

- Plausible national qualify rate and scarcity ratios for 2024.  
- Plausible TN ordinary-quota government allotment rates by school medium after NEET, with a holdout check.  
- How AIQ counselling seats split across MBBS / BDS / nursing.  
- How physician vs engineering vs other-graduate one-year earnings look once unemployment and non-completion zeros are kept.  
- How much conclusions move under neutral / conservative / reasonable priors.

### Does not answer

- Causal effect of coaching on NEET marks or seats.  
- Causal return to barely clearing a cutoff.  
- Joint `P(seat | score, income, caste, domicile, attempt, coaching)`.  
- Field-identified medicine/engineering unemployment from PLFS microdata (not yet in-repo).  
- Individual mental-health risk.

---

## 7. Implementation notes and tests

- Dependencies: `numpy`, `scipy` added to `pyproject.toml` (needed by `bayes.py`).  
- Tests: `tests/test_bayes_model.py` (6 cases) plus full suite **17 passed**.  
- Guardrail asserted in tests: `used_to_update_coaching_effect` is always false; SECL qualify residual remains > 0.3.

---

## 8. Recommended next modeling steps (when data resume)

1. Replace graduate employment proxies with weighted PLFS hierarchical field estimates.  
2. Build household generator from HCES/NFHS joints (stop using independence where joints exist).  
3. Convert coaching SD shifts into admission changes through the empirical score→rank→seat engine, then re-run cohort PPCs with explicit selection models.  
4. Add Kerala allotment panels as a second state adapter with category/quota structure.  
5. Partition more NTA/MCC marginals into calibration vs holdout per `docs/VALIDATION_PLAN.md`.

Until then, the conservative profile in `data/processed/bayesian/` is the default numerical backbone for scarcity, TN medium inequality, and non-causal career contrasts.
