# Next analytic steps — execution log

**Date:** 2026-07-25  
**Follows:** [DATA_EXAMINATION.md](DATA_EXAMINATION.md) §5–6

## Status board

| Step | Status | Artifact |
|---|---|---|
| Reconcile NEET rows/centres vs NTA 2024 press; hash PDFs | **Done — PASS** | `data/processed/neet_2024_nta_reconciliation.csv`; press PDFs under `data/external/nta/raw/press/`; 14 Wayback centre PDFs hashed |
| Extract MCC 2024 seat-matrix + allotments | **Done** | Seat matrix 674; allotments R1 26,109 / R2 23,817 / R3 6,582 (+ R3 wide status 36,761) / stray 1,058 / special-stray 307 |
| Parse Kerala rank/allotment/last-rank panels | **Done** | `data/processed/kerala/` (identifiers stripped) |
| Fix NMC consumers (`stateName` / `managementupdate`) | **Done** | `scripts/prelim_open_data_analysis.py` |
| Register/download HCES, CMSE, PLFS, NFHS, AIDIS | **Blocked — login** | `data/processed/gated_download_status.csv`; runbook unchanged in `docs/GATED_NEXT.md` |
| Complete OpenICPSR E112992 download | **Blocked — login** | Same status CSV; local README still documents wall |
| Machine-readable companion JSON | **Done** | `data/processed/prelim_analysis/data_examination_summary.json` (+ `summary.json`) |

## 1. NEET reconciliation

Official **re-revised** press (26 Jul 2024):

| Official | Value | Local reconstruction |
|---|---|---|
| Appeared (excl. UFM) | 2,333,162 | **2,333,162** (exact) |
| Appeared (incl. UFM) | 2,333,297 | −135 (UFM not in centre PDFs) |
| Qualified | 1,315,853 | n/a (marks file has no qualify flag) |
| Centres | 4,750 | **4,750** unique `centre_id` |
| Cities | 571 (press) | 567 distinct labels in centre CSV |

Press PDFs hashed and registered in `download_manifest.csv`. Live NTA centre PDF host remains down; **14** Wayback centre PDFs hashed in `neet_2024_wayback_centre_pdf_hashes.csv`.

## 2. MCC 2024 extracts

Scripts: `scripts/extract_mcc_2024.py`

| Output | Rows |
|---|---|
| `mcc_2024_seat_matrix.csv` | 674 (AIQ + deemed + AIIMS + JIPMER + ESIC + nursing + CU) |
| `mcc_2024_allotment_round_1.csv` | 26,109 |
| `mcc_2024_allotment_round_2.csv` | 23,817 (filtered valid course/quota rows) |
| `mcc_2024_allotment_round_3.csv` | 6,582 (Round-3 filled seats only) |
| `mcc_2024_round3_status_wide.csv` | 36,761 (R1/R2/R3 status per rank) |
| `mcc_2024_allotment_round_stray.csv` | 1,058 |
| `mcc_2024_allotment_round_special_stray.csv` | 307 |
| `mcc_2024_allotments.csv` | 57,873 merged tidy allotments |

Schema (allotments): `round, sno, rank, allotted_quota, allotted_institute, course, allotted_category, candidate_category, remarks`.

## 3. Kerala state adapter panels

Script: `scripts/parse_kerala_medical_panels.py`  
**No application numbers** written to `data/processed/` (privacy audit passes).

| Panel | Rows |
|---|---|
| Medical rank list 2025 | 46,367 (`state_rank`, `neet_score`, `neet_rank`) |
| MBBS/BDS allotments phases 1–4 | 19,290 |
| Last-rank long panel (college × category × phase) | 2,288 |

## 4. NMC consumer fix

`prelim_open_data_analysis.py` now groups on `stateName` / `managementupdate`. Regenerated summary shows Private 65,093 seats vs Govt. 63,859 (not a single `nan` bucket).

## 5–6. Gated downloads

Automated probe (`scripts/attempt_gated_downloads.py`) confirms **interactive free accounts** are still required for:

- MoSPI: PLFS, HCES, CMSE, AIDIS
- OpenICPSR E112992
- DHS NFHS catalog reachable but download not automatable without approved login

No credentials were available in this session. After you log in and download archives into the paths in `docs/GATED_NEXT.md`, run `register_download.py` and re-run the probe script.

## Commands to re-run

```bash
python scripts/reconcile_neet_2024.py
python scripts/extract_mcc_2024.py
python scripts/parse_kerala_medical_panels.py
python scripts/prelim_open_data_analysis.py
python scripts/attempt_gated_downloads.py
python scripts/check_processed_privacy.py
```
