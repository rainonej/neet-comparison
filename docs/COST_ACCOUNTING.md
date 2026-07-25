# Cost accounting for NEET attempts and medical education

The financial model separates cash paid, resources consumed, and delayed life-course timing.
Combining them into one unexplained number would overstate precision.

## Direct attempt costs

For attempt \(t\):

\[
C_{attempt,t} = C_{exam} + C_{travel} + C_{lodging} + C_{materials}
+ C_{coaching} + C_{relocation} + C_{extra\ living}.
\]

These components should be sampled from household- and location-relevant distributions when
possible. Coaching should distinguish online, local in-person, and residential programs.

## Repeat-year costs

A repeat year has at least three concepts of cost:

1. **Family cash outlay**: tutoring, fees, transport, materials, rent, and food beyond the normal
   household baseline.
2. **Resource burden**: cash outlay divided by annual household consumption/resources and by
   liquid assets.
3. **Timing cost**: later entry into the alternate degree, medical school, or labor market.

The repeat-year opportunity cost must depend on the counterfactual:

- If the student would otherwise start another degree, the main cost is delayed graduation and
  delayed post-degree earnings, not necessarily one full year of immediate salary.
- If the student would otherwise work, use an age-, state-, sex-, education-, and social-group-
  matched PLFS earnings distribution.
- If the student would otherwise remain out of work or education, monetary opportunity cost may
  be low even though the social and psychological cost is not.

The simulator should display these alternatives separately rather than choose one silently.

## Medical-school costs

For an accepted seat:

\[
C_{degree} = \sum_y (tuition_y + mandatory\ fees_y + housing_y + food_y + travel_y)
+ financing\ cost.
\]

Government, private/self-financing, deemed, NRI, and management quota costs must remain separate.
Affordability should be tested against:

- current annual household resources;
- liquid wealth;
- plausible borrowing constraints;
- scholarships or state support;
- catastrophic-burden thresholds shown as user-adjustable assumptions.

## Family-facing translations

Report at least:

- months or years of current household resources;
- percentage of annual household consumption;
- percentage of liquid assets;
- projected debt-service share;
- number of siblings whose modeled education budgets would be displaced, if household allocation
  is enabled.

These are translations of modeled costs, not moral judgments.

## Earnings and present value

Use age-specific occupation distributions where possible. For simulated path \(k\):

\[
NPV_k = -C_{education,k} + \sum_{a=a_0}^{A}
\frac{Earnings_{k,a} - debt\ service_{k,a}}{(1+r)^{a-a_0}}.
\]

Report undiscounted totals as well as several real discount rates. Never use one mean wage for an
entire career when an age-earnings profile can be estimated.
