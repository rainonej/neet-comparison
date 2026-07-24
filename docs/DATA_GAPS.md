# Data gaps and workarounds

| Missing quantity | Why it matters | Why current sources fail | Best workaround | Uncertainty |
|---|---|---|---|---|
| Applicant household income/wealth | Maps burden and private-seat affordability | NTA does not publish it | Generate synthetic households from HCES/AIDIS/NFHS and calibrate participation using education surveys | High |
| Coaching denominator among all NEET candidates | Needed for coaching success rates | Studies often describe admitted students only | CMSE/NSS coaching prevalence + NEET-specific surveys + sensitivity analysis | Very high |
| Attempt number nationally | Repeaters change both odds and costs | NTA aggregate releases generally omit it | State admitted-student lists/reports, original surveys, targeted primary data | High |
| School board/type for candidates | Captures preparation inequality | Not in centre scores or MCC allotments | State studies; school catchment/centre ecology only as aggregate context, never individual inference | High |
| Domicile for 2024 centre scores | State quota is domicile-based | Test centre may differ from residence | Use state merit/allotment lists for state models; national centre data only for score ecology | High |
| Applicant-to-admission linkage | Converts score to actual seat outcome | Scores are anonymized; counselling uses ranks | Infer score-rank curve from NTA tables; use rank-based allotments; propagate mapping uncertainty | Medium-high |
| Full private/government tuition by college/quota/year | Determines affordability cliff | State-specific fragmented orders | Build state fee adapters and archive prospectuses/fee orders | Medium after collection |
| Longitudinal outcomes of applicants | Needed for causal life-course effects | No linked education-tax/labor dataset | PLFS conditional trajectories; label as projections, not effects | Very high |
| Mental-health causal effects | Needed for individual-risk claims | Small cross-sectional samples and aggregate death reports | Exposure index and qualitative narrative only | Prohibit individual probability |

## Primary-data option

A serious second phase could field a retrospective survey of NEET candidates sampled across score bands and states. Minimum variables:

- anonymized score/rank and year;
- attempt count;
- domicile, category, gender, school board/type/language;
- coaching mode, duration, fees, relocation, study hours;
- parental education/occupation, household income bands, assets and debt;
- offered seats, accepted seat, fees, alternate course;
- validated distress measures and support access;
- consent for follow-up.

This would still face recall and selection bias, but it would address the largest missing joint distribution.
