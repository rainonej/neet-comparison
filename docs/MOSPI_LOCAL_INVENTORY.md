# MoSPI local inventory (unit files)

Downloaded 2026-07-25 via the official `mospi-unitdata` API. **Unit microdata stay local / gitignored**; only hashes and aggregates are committed. Paths are under `data/external/mospi/`.

| ID | Dataset / wave | Local unit archive | Model use (blurb) |
|---|---|---|---|
| A1 | PLFS calendar 2025 | `plfs/2025/raw/Data_in_CSV.zip` | Current labour-market outcomes under the revamped 2025 design; keep separate from pre-2025 waves. |
| A1 | PLFS Jul 2023–Jun 2024 | `plfs/2023-24/raw/CSV_data_PLFS_2023_2024.zip` | Primary wage/employment anchors for physicians and alternate careers. |
| A1 | PLFS Jul 2022–Jun 2023 | `plfs/2022-23/raw/Data_in_CSV.zip` | Pool rare occupations; validate year-to-year stability. |
| A1 | PLFS Jul 2021–Jun 2022 | `plfs/2021-22/raw/PLFS_Data_2021-22_CSV.zip` | Extra ESS for doctor/engineer/lawyer cells. |
| A1 | PLFS Jul 2020–Jun 2021 | `plfs/2020-21/raw/CSV_Unit_level_data_PLFS_July2020_June2021.zip` | Pandemic-year labour outcomes; use carefully for validation. |
| A1 | PLFS Jul 2019–Jun 2020 | `plfs/2019-20/raw/CSV_PLFS_19_20.zip` | Pre-pandemic labour baseline for pooling. |
| A1 | PLFS calendar 2023 | `plfs/2023-calendar/raw/CSV_PLFS_Calendar_Year_2023.zip` | Calendar-year design check vs July–June annual. |
| A1 | PLFS calendar 2022 | `plfs/2022-calendar/raw/PLFS_Data_2022-22_CSV.zip` | Calendar-year design check vs July–June annual. |
| A2 | HCES 2023–24 | `hces/2023-24/raw/HCES_Data_2023-24_Csv.zip` | Household resource / MPCE percentiles for affordability and relative rank. |
| A2 | HCES 2022–23 | `hces/2022-23/raw/CSV_data_HH_Cons_exp_22_23.zip` | Robustness wave for consumption ranks and coaching burden. |
| A3 | CMSE 2025 | `cmse/2025/raw/Data in CSV.zip` | Current private-coaching participation and expenditure priors. |
| A4 | NSS Education 2017–18 | `nss_education/2017-18/raw/Data_in_CSV.zip` | Historical tutoring/prep costs and education-access structure. |
| A5 | AIDIS 2019 | `aidis/2019/raw/CSV_DI_77.zip` | Assets/debt financing capacity for private seats and catastrophic costs. |
| A10 | TUS 2024 | `tus/2024/raw/TUS2024.zip` | Study time and unpaid-work opportunity cost (unit zip, not CSV-named). |
| A10 | TUS 2019 | `tus/2019/raw/Unit level data of TUS 2019.zip` | Earlier time-use wave for gendered time-budget priors. |
| A11 | MIS 78th 2020–21 | `mis/2020-21/raw/CSV_MIS_78.zip` | Digital/transport/migration/access context for opportunity constraints. |
| A12 | CAMS 2022–23 | `cams/2022-23/raw/CSV_CAMS_79.zip` | Education/health/digital modules validating household access conditions. |
| A13 | ASUSE 2023–24 | `asuse/2023-24/raw/ASUSE_DATA_2023_24_CSV.zip` | Informal/family-business alternative career paths. |
| A13 | ASUSE 2022–23 | `asuse/2022-23/raw/ASUSE_Data_2022_23_CSV.zip` | Second ASUSE wave for informal-enterprise alternatives. |
| A14 | NSS Health 2017–18 | `nss_health/2017-18/raw/CSV_HSCH_75.zip` | Family medical-shock / insurance burden for QoL extensions. |
| A14b | NSS Health 2025 | `nss_health/2025/raw/CSV_data_household_social_consumption_heaith_Jan_Dec25.zip` | Recent health-spending priors; check overlap with 75th Round before pooling. |

## Processed aggregates already derived

See `data/processed/mospi/` (PLFS wage anchors, CMSE coaching priors, HCES MPCE percentiles, AIDIS debt percentiles). These are the commit-safe model inputs.

## Provenance

SHA-256 hashes for the unit archives above are recorded in `data/processed/download_manifest.csv` via `scripts/register_download.py`.
