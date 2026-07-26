# Story bibliography — claims behind the interactive

Citations for user-facing claims in `reports/interactive/the-accessible-seat.html` (visual essay) and `reports/interactive/sources-and-methods.html`.
Prefer administrative counts and nationally representative microdata over convenience surveys.
Full literature map: [RESEARCH_LITERATURE.md](RESEARCH_LITERATURE.md).
Pinned numeric rows: `data/processed/published_estimates.csv`.

## Prize (why medicine is worth chasing)

| Claim | Best support in-repo | Key | Grain / caveat |
|---|---|---|---|
| Higher physician earnings vs engineering / other paths | MoSPI PLFS 2025 wage anchors; World Bank health-labor PLFS means | `plfs_2025_physician_monthly_median`, `plfs_2025_engineer_monthly_median`; World Bank physician/engineer monthly wages | Employed earners; not causal return to NEET |
| Technical / professional credentials linked to more regular work | ILO/IHD *India Employment Report 2024* | Graduate youth unemployment 28.7%; technical degree ~1.4× regular-employment odds vs without | Broad graduate/youth, not medicine-only |
| Education as a mobility channel in India | Asher et al., AEJ Applied 2024 (intergenerational mobility); IHDS education-mobility studies | Listed in RESEARCH_LITERATURE | National mobility research — not NEET-specific |
| Medicine carries social prestige / family aspiration | Thomas (2010), *Medicine, merit, money and caste*; medical-education finance reviews | RESEARCH_LITERATURE § Medical education | Qualitative / ethical framing, not a prestige index |
| Job quality differs by health occupation & sector | World Bank (2025), *An Overview of the Indian Health Labor Markets* | Public vs private physician wage gap in published_estimates | Sector mix ≠ college ownership |

## Lottery / scarcity

| Claim | Source | Key |
|---|---|---|
| ~2.33M appeared, ~1.32M qualified (2024) | NTA re-revised press + centre-marks reconciliation | `neet_2024_*` rows |
| ~129,602 MBBS seats | NMC college page snapshot | `nmc_mbbs_seats_current_page` |
| Marks distribution / quantiles | Anonymized 2024 centre marks | `neet_2024_marks_*.csv` |
| +4 / −1 / 180 Q → max 720 | NTA NEET-UG scheme of examination | Used for “marks ÷ 4 ≈ questions” translation; wrong→correct is a 5-mark swing |

## Featured examination item

| Item | Official source | Answer / use | Caveat |
|---|---|---|---|
| NEET-UG 2020, English booklet E1, Q21: EcoRI palindromic recognition sequence | [Official NTA source page](https://neet.nta.nic.in/document/english-set-e1-neet-qp-2020/) and [English E1 PDF](https://cdnbbsr.s3waas.gov.in/s37bc1ec1d9c3426357e69acd5bf320061/uploads/2022/02/2022021555.pdf), page 4 | Option 1 / A: 5′–GAATTC–3′ / 3′–CTTAAG–5′. Used to demonstrate +4/−1/0 scoring, near-identical distractors, and a five-mark correct-vs-wrong gap. | Valid biotechnology recall under letter-sequence load; easy to misread. Does not by itself measure the full qualities of a future doctor. Limited excerpt for criticism and research; do not infer permission to republish full papers. |

Structured sample bank and provenance notes: [`docs/QUESTION_BANK.md`](QUESTION_BANK.md), `data/question_bank/neet_2020_e1_sample_questions.{json,csv}`.

## Privilege-weighted odds

| Claim | Source | Caveat |
|---|---|---|
| TN English vs Tamil govt allotment gap | Justice A.K. Rajan Committee (2021) | State case; not national causal English effect |
| ~98.5–99% of admitted coached (TN 2019–20) | Rajan Committee | Admitted denominator only; essay uses “about 99%” |
| Tamil-medium admits 14.88% → 1.99% (2016–17 → 2020–21) | Rajan Table 7.18 / project CSV | TN state case; composition, not national causal estimate |
| Rural govt-college admits ~61.5% avg pre-NEET → 49.91% (2020–21) | Rajan Committee / contemporary reportage | TN government-college window |
| Family income &lt; ₹2.5 lakh admits 47.42% → 41.05% (2016–17 → 2020–21) | Rajan Committee tabulations as reported | TN admitted composition |
| Private MBBS tuition ≈ ₹18.9–25 lakh/yr vs EWS ceiling ₹8 lakh | Rajasthan fee litigation (HC; SC declined interference, 2026) | State example, not national fee schedule |
| ~71.4% of admitted were repeaters (TN 2020–21) | Rajan Committee Table 7.38 | Not mean attempts among applicants |
| ~28.6% of admitted were current-year (TN 2020–21) | Rajan Committee Table 7.38 | Best in-repo age/attempt proxy; not national DOB |
| ₹10 lakh exclusive coaching for a repeater | Rajan Committee §5.4 | Narrative high, not national mean |
| ~₹95,033 average coaching cost (TN packages) | Rajan Committee §7.5.9.1 | Derived from fee bands |
| Coaching spend / participation | MoSPI CMSE 2025 unit aggregates | School tutoring frame; not NEET-dropper specific |
| Youth opportunity-cost wage proxy | PLFS 2025 no_college monthly median | Not NEET-linked |

## Arms race / coaching effects

| Claim | Source | Caveat |
|---|---|---|
| Skeptical prep → score priors | docs/COACHING_EFFECT_EVIDENCE.md | Not a NEET LATE |
| Strategic tutoring response | Cross-exam literature cited there | External; not estimated from NEET microdata |

## Attempts / retakes

| Claim | Source | Caveat |
|---|---|---|
| Sitting histograms (low/central/high/TN-cal) | `config/attempt_priors.yaml` | TN-calibrated under ρ; still not national |
| Ticket-cost trajectories | `ticket_cost_summary.json` | Scenario bands; accessible ≠ qualify |
| Resource runway formula | CMSE + HCES + AIDIS + PLFS (+ TUS) | Synthetic household; not NEET-linked |
| NTA prior appearances / Class XII year / DOB | Not public | RTI template 1b |

## Human accounts used in the visual essay

These accounts make the mechanisms concrete. They are reported examples, **not representative samples or causal estimates**. The essay links readers directly to the originating reports and does not reuse publication photography.

| Person / cohort | Reported facts used | Source | Editorial role / caveat |
|---|---|---|---|
| Kanakpriya and Virender Verma | Four years of preparation; 631/720; father reportedly committed roughly half his construction income to coaching EMIs for two years; family debt and sacrifice | ThePrint, Nootan Sharma, 5 July 2024: [NEET fiasco isn’t just about broken dreams](https://theprint.in/the-fineprint/neet-fiasco-isnt-just-about-broken-dreams-its-pushing-lakhs-of-families-into-poverty/2160783/) | Central family vignette showing the prize, coaching debt and strong-score uncertainty. One family, not prevalence evidence. |
| Jeevith Kumar | 548/600 in Class XII; NEET 193 without private tuition; 664 after outside help financed a one-year residential coaching program | NDTV, 19 October 2020: [Tamil Nadu shepherd’s son who cracked NEET needs help to study medicine](https://www.ndtv.com/india-news/neet-2020-tamil-nadu-shepherds-son-who-cracked-medical-entrance-exam-neet-needs-help-to-study-medicine-2312276) | Mechanism vignette for exam-specific preparation and affordability. Not an average coaching effect. |
| Seven Madurai government-school admits | All seven were repeat candidates who used private coaching; six had parents working as daily-wage earners; examples include ₹5.5 lakh and ₹1.5 lakh borrowing and cattle sold | Times of India, 1 August 2025: [7 from Madurai land MBBS seats under 7.5% quota](https://timesofindia.indiatimes.com/city/madurai/7-from-madurai-land-mbbs-seats-under-7-5-quota/articleshow/123029677.cms) | Human-scale corroboration of the repeater/coaching treadmill among a selected winning cohort. Not all TN candidates. |

## Citation keys used in the HTML

- `[PLFS25]` — MoSPI PLFS 2025 processed wage anchors  
- `[WB25]` — World Bank Indian health labor markets (PLFS-based)  
- `[IER24]` — ILO/IHD India Employment Report 2024  
- `[AEJ24]` — Asher et al. intergenerational mobility (AEJ Applied 2024)  
- `[Thomas10]` — Medicine, merit, money and caste (2010)  
- `[NTA24]` — NTA NEET-UG 2024 counts / scheme  
- `[NMC]` — NMC MBBS seat snapshot  
- `[Rajan21]` — Justice A.K. Rajan Committee (Tamil Nadu, 2021)  
- `[CMSE25]` — MoSPI CMSE 2025 coaching aggregates  
- `[hq969]` — Public NEET-2024 centre-marks reconstruction  
