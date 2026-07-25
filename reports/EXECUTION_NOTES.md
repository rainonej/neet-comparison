# Execution notes — 2026-07-25 (neet-comparison bootstrap)

## Repository seed

- Preserved the six-commit history from `neet-life-course-data-audit.bundle`.
- Overlayed the fuller `neet-life-course-data-audit(5).zip` snapshot (access kit, microsim scaffolding, coaching/TN evidence).
- Added setup docs (`SETUP.md`, `OPEN_DATA_DOWNLOADS.md`, `GATED_NEXT.md`) and `scripts/register_download.py`.

## Successfully acquired (local, gitignored)

| Source | Local path | Notes |
|---|---|---|
| OSF `tnh4x` | `data/external/osf/tnh4x/raw/` | CSV + methods DOCX + NSSI scales PDF |
| NEET-2024 centre marks reconstruction | `data/external/neet-2024-center-marks.csv` | 33,800,799 bytes; SHA-256 `35b67efe…114c`; 2,333,162 rows |
| NMC UG colleges | `data/raw/nmc_ug_colleges.json`, `data/raw/nmc_colleges.csv` | JSON API `getAllUgColleges`; 823 college rows |
| MCC UG 2024 archive | `data/raw/mcc_2024/2024/` | 37 indexed PDFs (seat matrices, allotments, vacancies, notices) |
| Kerala CEE / KEAM | `data/external/kerala_cee/raw/` | Home/notification HTML, 2025 rank/allot/last-rank/catlist landing pages, discovered link index |

Hashes and provenance are in `data/processed/download_manifest.csv`.

## Blocked or deferred

- **OpenICPSR E112992:** project page is public; download requires a free ICPSR login. Stub README left under `data/external/openicpsr/E112992/raw/`.
- **Official NTA centre PDFs:** `neetfs.ntaonline.in` root returns 404; `neet.nta.nic.in` responds; full centre-PDF crawl not completed in this pass. Reconstruction CSV remains the working score distribution.
- **Gated surveys (MoSPI / DHS / IHDS / PRICE / Young Lives):** intentionally deferred. Follow `docs/GATED_NEXT.md`.

## Validation

- Source catalog audit: 43 sources, 15 critical.
- Privacy header audit on `data/processed/` passed.
- Repository tests: `pytest` (see `pytest.ini`; `_incoming/` excluded).
