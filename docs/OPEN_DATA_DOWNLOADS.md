# Open data downloads (bootstrap pass)

Last updated: 2026-07-25

This pass downloads **anonymous / no-login** sources only. Gated MoSPI/DHS/IHDS pulls are documented in [GATED_NEXT.md](GATED_NEXT.md) and intentionally deferred.

Register every successful file with `scripts/register_download.py`. Raw files stay under `data/external/` or `data/raw/` and are **not** committed.

## Status

| # | Source | Local path | Status |
|---|---|---|---|
| 1 | OSF `tnh4x` aspirant microdata | `data/external/osf/tnh4x/raw/` | Downloaded (CSV, methods, scales) |
| 2 | OpenICPSR E112992 | `data/external/openicpsr/E112992/raw/` | Blocked: free ICPSR login required |
| 3 | NEET-2024 centre marks (reconstruction) | `data/external/neet-2024-center-marks.csv` | Downloaded; summaries refreshed |
| 4 | NMC MBBS colleges | `data/raw/nmc_colleges.csv` (+ JSON) | Downloaded via NMC JSON API (823 rows) |
| 5 | MCC UG 2024 archive | `data/raw/mcc_2024/2024/` | Downloaded (37 PDFs + index) |
| 6 | Kerala CEE/KEAM public lists | `data/external/kerala_cee/raw/` | Landing pages + link index archived |
| 7 | Official NTA centre PDFs | `data/raw/neet_2024/` | Best-effort only; not completed |

## Commands used

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

Successful downloads are appended to `data/processed/download_manifest.csv` (SHA-256, bytes, URL, date, redistribution note). Narrative outcomes: `reports/EXECUTION_NOTES.md`.

## Not in this pass

MoSPI PLFS/HCES/CMSE/NSS/AIDIS/TUS, DHS NFHS, ICPSR IHDS, PRICE ICE360, Young Lives, CMIE, EPWRF, Indiastat, author outreach emails, new RTIs. OpenICPSR E112992 waits on a free login during the gated batch.
