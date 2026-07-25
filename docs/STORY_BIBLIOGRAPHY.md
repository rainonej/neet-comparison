# Story bibliography — claims behind the interactive

Citations for user-facing claims in `reports/interactive/the-accessible-seat.html`.
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
| +4 / −1 / 180 Q → max 720 | NTA NEET-UG scheme of examination | Used for “marks ÷ 4 ≈ questions” translation |

## Privilege-weighted odds

| Claim | Source | Caveat |
|---|---|---|
| TN English vs Tamil govt allotment gap | Justice A.K. Rajan Committee (2021) | State case; not national causal English effect |
| ~98.5% of admitted coached (TN) | Rajan Committee | Admitted denominator only |
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
