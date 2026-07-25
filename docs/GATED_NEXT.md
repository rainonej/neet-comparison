# Gated surveys — do this next

Short runbook for the free-account downloads deferred from the open bootstrap pass. Full detail remains in [ACQUISITION_CHECKLIST.md](ACQUISITION_CHECKLIST.md), [DATA_REQUEST_TEXT.md](DATA_REQUEST_TEXT.md), and [gated_data_acquisition.csv](gated_data_acquisition.csv).

## Rules (non-negotiable)

1. Preserve the **original archive** exactly as downloaded; also keep questionnaire, codebook, sample design, weights, and terms.
2. Store under:

   ```text
   data/external/<provider>/<dataset>/<wave>/raw/
   ```

   Optionally mirror a working copy under `data/raw/restricted/` if an extraction script expects it.
3. **Never commit** restricted microdata to this public repo.
4. Register each file:

   ```bash
   python scripts/register_download.py \
     --path data/external/mospi/plfs/2023-24/raw/archive.zip \
     --url "https://..." \
     --notes "MoSPI licence; local only; no redistribution"
   ```

## One MoSPI account (do first)

Register once at the MoSPI microdata portal, then download **archives + documentation** for:

| Dataset | Waves / notes |
|---|---|
| PLFS | Annual 2017–18 through 2023–24; calendar 2024 and 2025. Keep pre-2025 and revamped 2025 designs separate. |
| HCES | 2022–23 and 2023–24 |
| CMSE | 2025 (private coaching / tuition expenditure) |
| NSS Education | 2017–18 |
| AIDIS | 2019 |
| Time Use | 2019 and 2024 |
| MIS 78th / CAMS | 2022–23 |
| ASUSE | recent waves |
| NSS Health | 2017–18 and **2025** (A14 / A14b) |

### Local status (2026-07-25)

Downloaded via official `mospi-unitdata` API (CSV + docs; not committed): **PLFS** 2023–24 + calendar 2025, **HCES** 2022–23 + 2023–24, **CMSE** 2025, **NSS Education** 2017–18, **AIDIS** 2019. Further waves (extra PLFS, TUS, MIS, CAMS, ASUSE, Health) are in `python scripts/download_mospi_unitdata.py --model-batch`. Tracker: `docs/acquisition_tracker.csv` / `docs/gated_data_acquisition.csv`.

### If the NADA pages hang (common)

`get-microdata` HTML often never finishes. There is **no public mirror** of recent PLFS/HCES/CMSE unit files (World Bank/IPUMS only have older NSS employment rounds). Use MoSPI’s official API client instead:

1. When https://microdata.gov.in loads at all, open **Profile → Generate API Key**.
2. Put the key in gitignored `.env` as `MOSPI_API_KEY=...` (do not paste it into chat).
3. Run:

   ```bash
   pip install mospi-unitdata
   python scripts/download_mospi_unitdata.py --search "PLFS"
   python scripts/download_mospi_unitdata.py --priority
   ```

Docs: https://www.mospi.gov.in/unitdata-python-library and https://github.com/nso-india/mospi-unitdata

If `microdata.gov.in` itself connection-refuses, the API is down too — wait/retry later; do not use unofficial redistributed copies.

## Then other free archives

| Archive | What to request | Paste text |
|---|---|---|
| OpenICPSR E112992 | Bagde–Epple–Taylor engineering admissions replication zip | free ICPSR account (download gated even though project page is public) |
| DHS Program | NFHS-4 and NFHS-5 household, member, women, men; GPS separately | [DATA_REQUEST_TEXT.md](DATA_REQUEST_TEXT.md) |
| ICPSR | IHDS-I **22626**, IHDS-II **36151** (all related files) | free account |
| PRICE ICE 360 | 2014, 2016, 2021, 2023 — confirm terms before paying | [DATA_REQUEST_TEXT.md](DATA_REQUEST_TEXT.md) |
| Young Lives India | child, household, school, community, constructed longitudinal | free registration |

## Still not “download and forget”

- **RTI** templates: [RTI_REQUEST_TEMPLATES.md](RTI_REQUEST_TEMPLATES.md) — central portal is **Indian citizens only**; use a collaborator.
- **Researcher outreach**: [RESEARCHER_OUTREACH_TEMPLATE.md](RESEARCHER_OUTREACH_TEMPLATE.md) + [DATA_HOLDER_AND_RESEARCHER_LEADS.md](DATA_HOLDER_AND_RESEARCHER_LEADS.md).
- **Paid later**: EPWRF (narrow), Indiastat (only after exact table list), CMIE quote first.

## When you finish a gated batch

1. Register hashes with `register_download.py`.
2. Append a short section to `reports/EXECUTION_NOTES.md`.
3. Tick rows in `docs/acquisition_tracker.csv` / `docs/gated_data_acquisition.csv`.
4. Do **not** `git add` anything under `data/external/` or `data/raw/` except allowlisted processed summaries.
