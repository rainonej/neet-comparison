# Baseline decisions after the first data audit

## Decisions adopted

1. **Missing cross-source dependence:** assume conditional independence and combine separate
   observed marginals on the odds scale.
2. **Completely unmeasured attributes:** use a neutral effect rather than fabricate a coefficient.
3. **Career return:** compare projected physician earnings and job quality with a background-
   relevant mixture of alternatives. Do not require a barely-admitted cutoff design for the MVP.
4. **Selection warning:** show raw, partially adjusted, and conservative earnings-gap scenarios
   because physician/non-physician differences are not purely caused by medical admission.
5. **Coaching and repeat attempts:** model observed cash and timing costs now. Keep probability
   effects neutral in the baseline and expose them as sensitivity parameters until denominators are
   acquired.
6. **English/regional medium and school board:** include state-specific observed marginals where
   applicant denominators exist. Use Tamil Nadu Table 7.18 as the first implemented case and do not
   generalize it as a causal national effect.
7. **Private affordability:** distinguish offered from accessible seats. An unaffordable private
   offer does not count as a usable medical-school outcome.

## Immediate implementation targets

- registration-gated household and labor microdata acquisition;
- state/category applicant and allotment denominators;
- college- and quota-specific fee histories;
- empirical alternative-path mixture after unsuccessful NEET attempts;
- age-earnings curves for physicians and alternative occupations;
- first end-to-end synthetic scenario with assumption provenance.
