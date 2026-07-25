# Open data downloads (bootstrap + coaching-gap pass)

Last updated: 2026-07-25

This pass downloads **anonymous / no-login** sources only. Gated MoSPI/DHS/IHDS pulls are documented in [GATED_NEXT.md](GATED_NEXT.md). Coaching-effect microdata that requires outreach is listed in [COACHING_GAP_ASK_LIST.md](COACHING_GAP_ASK_LIST.md).

Register every successful file with `scripts/register_download.py`. Raw files stay under `data/external/` or `data/raw/` and are **not** committed.

## Status

| # | Source | Local path | Status |
|---|---|---|---|
| 1 | OSF `tnh4x` aspirant microdata | `data/external/osf/tnh4x/raw/` | Downloaded (CSV, methods, scales) |
| 2 | OpenICPSR E112992 | `data/external/openicpsr/E112992/raw/` | Still blocked: free ICPSR login (probe 2026-07-25) |
| 3 | NEET-2024 centre marks (reconstruction) | `data/external/neet-2024-center-marks.csv` | Downloaded; **reconciled** to NTA re-revised appeared 2,333,162 |
| 4 | NMC MBBS colleges | `data/raw/nmc_colleges.csv` (+ JSON) | Downloaded via NMC JSON API (823 rows) |
| 5 | MCC UG 2024 archive | `data/raw/mcc_2024/2024/` | Downloaded (37 PDFs + index) |
| 6 | Kerala CEE/KEAM public lists | `data/external/kerala_cee/raw/` + `data/processed/kerala/` | PDFs archived; **tidy panels** parsed (no appl. nos. in processed) |
| 7 | Official NTA centre PDFs | `data/raw/neet_2024/` | Best-effort only; not completed |
| 8 | **Dakshana annual reports + JDST 2024 notification** | `data/external/dakshana/raw/` | Downloaded (~520 MB; AR07–AR24 + JDST rules) |
| 9 | **CBSE dummy-school enforcement** | `data/external/cbse/raw/` + `data/processed/cbse_dummy_school_registry.csv` | Downloaded press PDFs + HTML lists; school registry built |
| 10 | **Tamil Nadu rank/allotment PDFs** | `data/external/tamil_nadu/counselling/raw/` | Downloaded (~60 PDFs from home + known 2023 lists) |
| 11 | Bihar Super 50 program docs | `data/external/bihar_super50/raw/` | Portal 404; news mirrors only |
| 12 | SATHEE / CSRL public pages | `data/external/sathee/raw/`, `data/external/csrl/raw/` | Landing pages only; no microdata |

## Coaching-gap public pass (2026-07-25)

```bash
python scripts/download_coaching_gap_public.py
# plus targeted curl for CBSE press PDFs and TN home PDF crawl

python scripts/build_cbse_dummy_school_registry.py
```

### What these public files can and cannot do

| Downloaded now | Can support | Cannot estimate |
|---|---|---|
| OSF Kota aspirants | Stress / parental-pressure module | Coaching fees, hours, NEET score, seat |
| Dakshana AR + JDST notice | Aggregate scholar success; selection design description | Rejected-applicant cutoff RDD |
| CBSE enforcement lists | School-level dummy-school exposure proxy | Which individual applicants used dummy schools |
| TN rank/allotment PDFs | Score/rank → allotment mechanism | Coaching dose, income, drop years (unless later linked) |
| Bihar / SATHEE / CSRL pages | Outreach targeting | Any applicant or usage microdata |

**Privacy:** Tamil Nadu public lists contain names, application numbers, and roll numbers. Keep them only under `data/external/` (gitignored). Strip identifiers before any `data/processed/` export. See [PRIVACY_AND_DATA_HANDLING.md](PRIVACY_AND_DATA_HANDLING.md).

## Commands used (earlier bootstrap)

```bash
# OSF (view-only token from catalog)
curl -L -o data/external/osf/tnh4x/raw/Data_for_analysis.csv \
  "https://osf.io/download/nz8fd/?view_only=871cca8775f8420e802e172b5534673e"

# NEET-2024 reconstruction
curl -L -o data/external/neet-2024-center-marks.csv \
  "https://github.com/hq969/neet-2024-center-marks/raw/refs/heads/main/csv/neet-2024-center-marks.csv"
python scripts/summarize_neet_2024_marks.py --retrieved-date 2026-07-25

# NMC + MCC
python scripts/scrape_nmc_colleges.py --out data/raw/nmc_colleges.csv
python scripts/scrape_mcc_archive.py --year 2024 --out data/raw/mcc_2024
```

## Provenance

Successful downloads are appended to `data/processed/download_manifest.csv` (SHA-256, bytes, URL, date, redistribution note). Coaching-gap crawl index: `data/processed/coaching_gap_public_manifest.csv`. Narrative outcomes: `reports/EXECUTION_NOTES.md`.

## Not in this pass

MoSPI PLFS/HCES/CMSE/NSS/AIDIS/TUS, DHS NFHS, ICPSR IHDS, PRICE ICE360, Young Lives, CMIE, EPWRF, Indiastat, author outreach emails, new RTIs. OpenICPSR E112992 waits on a free login during the gated batch.

Ask-for queue for Dakshana applicants, Super 50, SATHEE logs, CSRL, Careers360 raw survey, TN application fields, and commercial coaching histories: [COACHING_GAP_ASK_LIST.md](COACHING_GAP_ASK_LIST.md).
