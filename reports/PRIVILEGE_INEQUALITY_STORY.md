# Privilege-compounding inequality story

**Date:** 2026-07-25  
**Model version:** 0.4.0 (`config/privilege_scenarios.yaml`)  
**Primary outcome:** **P(accessible / affordable MBBS seat)** + **annual earnings by profession**  
**Reproduce:** `make privilege`

## The story

1. **Access bias:** privilege (school medium, private-seat affordability, and labeled metro/prep knobs) raises the chance of an *accessible* MBBS seat.
2. **Return gap:** once on a path, wages are modeled **by profession**, not by college ownership. Medicine pays more than engineering / law / non-professional graduate / no-college paths among the employed.

**NEET “qualify rate” is not the outcome that matters here.** Qualifying is a soft threshold relative to seat scarcity. What matters for families is whether the student gets a seat they can actually take.

Mobility is real. Meritocracy-as-description-of-access is not.

---

## Earnings: by profession — not by caste / gender / parents’ income (yet)

If government and private *college* share the same physician wage prior, then the wage chart should be **profession curves**, not “govt college vs private college.” That is what we show.

| Path | Median ₹L if employed | vs medicine |
|---|---|---|
| Medicine (govt or private college) | ~4.5–4.8 | 1.0× |
| Engineering | ~3.3 | med **~1.4×** |
| Law (proxy knob) | ~2.6 | — |
| Non-professional graduate (knob) | ~1.6 | med **~3×** |
| No college (knob) | ~0.8 | med **~6×** |

**Demographics (caste, gender, race, parents’ education/income, city) are not plotted as earnings curves.** That would require joint wage microdata (PLFS / HCES / similar) that this repo does not have unlocked. Privilege enters the model on the **access** side (who gets a seat), not as invented wage gaps by identity.

Private seats mainly buy **access** + high fees. World Bank public vs private *sector* physician wages (~₹6.2L vs ₹3.9L) are a separate employment-sector comparison, not college ownership.

Zeros (~44–52% on graduate paths) = employment / family-support filter for young adults, not street poverty.

---

## 1. Access — affordable seats only (percent)

| Stratum | P(govt offer) | P(accessible seat) |
|---|---|---|
| Tamil · cannot afford private | **4.3%** | **4.3%** |
| English · cannot afford private | **9.5%** | **9.5%** |
| English · can afford private | **9.5%** | **18.1%** |
| English · can afford · metro (knob) | **11.6%** | **21.9%** |

- Full ladder **~5.0×** (accessible top / bottom)
- Affordability-only channel (**accounting knob**) **~1.91×**
- TN English/Tamil association **~2.19×** (observed; not a national causal English effect)

Private offers that fail the affordability filter do **not** count.

---

## 2. Attempts — what one number plus a prior can (and cannot) do

**Observed:** 71.4% of *admitted* TN students were repeaters (Rajan 2020–21). That is **P(repeater | admitted)**, not **P(repeater | applicant)** and not mean attempts.

Let \(r\) = admitted repeater share, \(\rho\) = \(P(\text{admit}|\text{repeater}) / P(\text{admit}|\text{first})\). Then:

\[
a = P(\text{repeater}|\text{applicant}) = \frac{r}{r + \rho(1-r)}
\]

| ρ (repeater admit odds / first-timer) | P(repeater \| applicants) | P(first attempt \| applicants) |
|---|---|---|
| 0.5 | **83%** | 17% |
| 1.0 (independence) | **71%** | 29% |
| 1.5 | **62%** | 38% |
| 2.0 | **56%** | 44% |
| 3.0 | **45%** | 55% |
| 4.0 | **38%** | 62% |

Annual appeared counts and a prior help only **inside** this structure: they constrain how large \(\rho\) or \(a\) can be if you also know seat totals and steady-state flows. They do **not** identify the full attempt-count distribution (1, 2, 3, …) or mean attempts without much stronger assumptions (e.g. geometric attempts + constant admit odds by attempt number).

Artifact: `data/processed/bayesian/attempt_repeater_sensitivity.csv`

### Related composition fact (still wrong denominator for causal claims)

| Fact | Value | Limitation |
|---|---|---|
| Share of *admitted* who had coaching (2019–20) | **~98.5%** | Winning pool only — not P(seat \| coaching) |

Prep spend / years-off distributions are **not invented** here (CMSE snippets and config prep-cost lines are knobs or wrong populations).

---

## 3. Binning vs KDE

Monte Carlo earnings are continuous. Coarse bins are display-only. Smooth densities: `earnings_kde.csv`.

---

## Evidence vs knobs

| Item | Kind |
|---|---|
| Profession wage curves | Anchored priors (medicine / engineering); some paths still knobs |
| Accessible-seat rates from TN medium + affordability | Medium = observed association; affordability = knob identity |
| Rajan repeater share → applicant share under ρ | Real \(r\); labeled sensitivity on \(\rho\) |
| Earnings by caste / gender / parents’ income / city | **Blocked** until joint wage microdata |
| Mean attempts / full attempt histogram | **Not identified** from \(r\) alone |
| Qualify rate | Ecology elsewhere; **not** the privilege-story outcome |

Artifacts: `access_by_stratum.csv`, `earnings_quantiles_by_outcome.csv`, `earnings_histograms.csv`, `earnings_kde.csv`, `attempt_repeater_sensitivity.csv`, `inequality_story.json`
