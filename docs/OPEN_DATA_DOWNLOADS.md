# Open data downloads (bootstrap pass)

Last updated: 2026-07-25

This pass downloads **anonymous / no-login** sources only. Gated MoSPI/DHS/IHDS pulls are documented in [GATED_NEXT.md](GATED_NEXT.md) and intentionally deferred.

Register every successful file with `scripts/register_download.py`. Raw files stay under `data/external/` or `data/raw/` and are **not** committed.

## Targets

| # | Source | Local path (after download) | Command / URL |
|---|---|---|---|
| 1 | OSF `tnh4x` aspirant microdata | `data/external/osf/tnh4x/raw/` | OSF project download (view-only link in catalog) |
| 2 | OpenICPSR E112992 | `data/external/openicpsr/E112992/raw/` | https://doi.org/10.3886/E112992V1 |
| 3 | NEET-2024 centre marks (reconstruction) | `data/external/neet-2024-center-marks.csv` | GitHub raw CSV from `hq969/neet-2024-center-marks` |
| 4 | NMC MBBS colleges | `data/raw/nmc_colleges.csv` | `python scripts/scrape_nmc_colleges.py --out data/raw/nmc_colleges.csv` |
| 5 | MCC UG 2024 archive | `data/raw/mcc_2024/` | `python scripts/scrape_mcc_archive.py --year 2024 --out data/raw/mcc_2024` |
| 6 | Kerala CEE/KEAM public lists | `data/external/kerala_cee/raw/` | Public rank / allotment / last-rank pages from cee.kerala.gov.in |
| 7 | Official NTA centre PDFs | `data/raw/neet_2024/` | `python scripts/fetch_neet_2024_centres.py --out data/raw/neet_2024` (best-effort) |

## After NEET-2024 CSV

```bash
python scripts/summarize_neet_2024_marks.py --retrieved-date 2026-07-25
```

Committed outputs: `data/processed/neet_2024_marks_*.csv` and an updated `download_manifest.csv` row.

## Provenance

Successful downloads are appended to `data/processed/download_manifest.csv` (SHA-256, bytes, URL, date, redistribution note). Narrative outcomes for this machine live in `reports/EXECUTION_NOTES.md`.

## Not in this pass

MoSPI PLFS/HCES/CMSE/NSS/AIDIS/TUS, DHS NFHS, ICPSR IHDS, PRICE ICE360, Young Lives, CMIE, EPWRF, Indiastat, author outreach emails, new RTIs.
