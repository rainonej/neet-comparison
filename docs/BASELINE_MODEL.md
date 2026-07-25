# Baseline microsimulation model

This document records the deliberately simplified baseline requested for a usable first product.
It is not a causal model of NEET admission or physician earnings.

## 1. Independence rule

The public data often provide separate marginal facts but not their joint distribution. For
example, a state may publish applicant and admitted counts by category, while a survey provides
household-income distributions by state and social group, without identifying the same people.

The baseline adopts the following rule:

> When multiple measured attributes have separate admission rates but no joint table, treat their
> evidence as conditionally independent and combine it on the odds scale.

For base admission probability \(p_0\) and marginal probabilities \(p_j(x_j)\):

\[
\operatorname{odds}(p(x)) = \operatorname{odds}(p_0)
\prod_j \frac{\operatorname{odds}(p_j(x_j))}{\operatorname{odds}(p_0)}.
\]

The result is clipped to a valid probability. This is equivalent to an independent-evidence or
naive-Bayes-style baseline. It is preferable to multiplying probabilities directly, which rapidly
produces nonsensical values.

### Unmeasured is not the same as independent

If no outcome association is available for a variable, the baseline applies a neutral multiplier
of one. It does **not** invent a caste, income, gender, coaching, language, or location effect.
Sensitivity runs may add plausible effects later.

Every output must list:

- the attributes backed by an observed marginal;
- the attributes assigned a neutral effect;
- borrowed effects taken from another state or year;
- the independent-evidence assumption.

## 2. Household and applicant generation

Households should still be sampled jointly from household-survey microdata where possible.
Independence is a workaround for missing links between datasets, not a reason to destroy dependence
that is present inside HCES, NFHS, AIDIS, PLFS, or another source.

A synthetic record should contain at least:

- state and rural/urban or town class;
- household consumption and, where possible, income and wealth ranks;
- social category, religion, and household composition;
- parental education and occupation;
- student sex;
- school type, board, and medium of instruction;
- science-track eligibility;
- coaching choice and attempt number.

## 3. Admission probabilities

The simulator should estimate distinct outcomes rather than a generic pass probability:

1. government MBBS offer;
2. private or self-financing MBBS offer;
3. deemed-university MBBS offer;
4. BDS, AYUSH, or another health-course offer;
5. no acceptable offer.

An offered seat is then passed through a household affordability model. A private offer that a
family cannot finance is not counted as an accessible medical seat.

Where state/category applicant denominators and allotment numerators exist, use them directly.
Where only admitted composition exists, do not interpret it as an admission probability.

## 4. Coaching and repetition

The baseline does not yet claim an empirically measured coaching or repeat-attempt score effect.
Both default to a neutral probability multiplier and are exposed as sensitivity parameters.
Their costs, however, are modeled from observed or published expenditure distributions.

This creates an intentionally conservative baseline:

- coaching definitely costs money;
- repeating definitely consumes time and resources;
- any admission advantage is shown separately as an uncertain scenario.

## 5. Medium of instruction and school board

The model distinguishes:

- language in which NEET is taken;
- school medium of instruction;
- school board and syllabus;
- language of coaching materials;
- the predominantly English-language environment of MBBS education.

Tamil Nadu's A.K. Rajan Committee provides applicant and MBBS allotment counts by Tamil- and
English-medium schooling. Aggregating the ordinary pre-NEET years in Table 7.18 gives government
college allotment rates of approximately 8.25% for English-medium applicants and 6.90% for
Tamil-medium applicants. Aggregating the four listed post-NEET non-special-quota cohorts gives
approximately 9.50% and 4.34%, respectively.

The ratio of those observed rates changes from about 1.20 before NEET to about 2.19 after NEET.
This is a descriptive Tamil Nadu association, not a causal effect of English itself. Medium is
entangled with income, private schooling, CBSE exposure, urban location, and coaching. The model
may use it only as:

- a Tamil Nadu-specific observed marginal;
- a borrowed proxy elsewhere with a prominent warning;
- or a sensitivity range.

## 6. Outcome comparison

The first product will not require a regression-discontinuity comparison of candidates barely
above and below a cutoff. Instead it will compare projected conditional trajectories:

- physician employment and earnings;
- a weighted mixture of plausible alternative paths for a similar science-stream student;
- direct education and preparation costs;
- debt and delayed earnings;
- household transfers and net present value.

The alternative path is not simply "non-doctor." It should include observed probabilities for
engineering, nursing, pharmacy, BDS/AYUSH, general science, other college, work, repeated entrance
preparation, and nonparticipation where supported.

Because selection into medicine is substantial, the result must be called a **scenario contrast**
or **conditional projection**, never the causal effect of passing NEET.

## 7. Required outputs

Each simulated profile should report:

- government, private, and accessible-seat probabilities;
- which probabilities are observed, combined under independence, or assumed neutral;
- total family cash cost by attempt;
- cost as a share of annual household resources and liquid wealth;
- delayed-earnings cost under multiple alternative assumptions;
- probability distribution over alternative education/career paths;
- discounted physician and alternative lifetime earnings distributions;
- net financial return and downside risk;
- narrative context without individual mental-health prediction.
