# Execution notes — 2026-07-25 (full public pull)

## Scale

After the expanded public crawl, local archives are about **1.06 GB / ~699 files** (see `data/processed/local_data_inventory.csv`).

## Major acquisitions

1. **Kerala CEE:** all linked medical/allied/engineering rank, allotment, last-rank, and category PDFs from KEAM 2025 pages, plus historical BPL scholarship notification PDFs.
2. **MCC:** UG archive PDFs for 2023, 2024, and available 2025 items.
3. **NIRF Medical:** ranking pages 2023–2025 and 150 institution report PDFs from `nirfpdfcdn`.
4. **NTA:** information bulletins and public-notice PDFs from `neet.nta.nic.in` (live centre-score PDF host is down).
5. **GitHub reconstruction:** centres CSV, longnames CSV, and `neet-2024-center-marks-data.db` in addition to the marks CSV.
6. **Background PDFs:** World Bank health labor, WID India inequality, Rajan Committee, NCRB ADSI-linked reports, Dakshana annual reports, CBSE dummy-school press releases, Tamil Nadu counselling archive PDFs.

## Official NTA centre PDFs

- Live URL pattern `https://neetfs.ntaonline.in/NEET_2024_Result/{id}.pdf` returns **404 / site not configured**.
- Wayback CDX finds only **14** archived centre PDFs; those are stored under `data/raw/neet_2024/pdfs_wayback/`.
- Working national score distribution remains the third-party reconstruction CSV/DB (hash-checked).

## Coaching-gap public download pass (same day)

Targeted pull for datasets that are available **without email**, plus an ask-for queue for the rest (`docs/COACHING_GAP_ASK_LIST.md`).

| Source | Result |
|---|---|
| OSF `tnh4x` | Confirmed local CSV (151 rows); Age/Gender/SES + stress scales only — **no** coaching fees/hours/NEET score/seat |
| Dakshana | AR07–AR24 + JDST 2024 notification (~520 MB under `data/external/dakshana/raw/`) |
| CBSE dummy schools | Mar 2024 + later inspection press PDFs; `disaffiliated.html` / `downgraded.html`; derived `data/processed/cbse_dummy_school_registry.csv` (25 school rows after cleanup) |
| Tamil Nadu counselling | ~61 MBBS/BDS-related PDFs from home crawl + known 2023 rank/allotment lists |
| Bihar Super 50 | `coaching.biharboardonline.com` **404**; Careers360 news mirror archived |
| SATHEE / CSRL | Landing pages only |

Scripts: `scripts/download_coaching_gap_public.py`, `scripts/build_cbse_dummy_school_registry.py`.

## Analytic next-steps pass (same day, later)

See [NEXT_STEPS_EXECUTION.md](NEXT_STEPS_EXECUTION.md).

- **NEET reconciliation:** reconstruction **2,333,162** rows = NTA re-revised appeared excl. UFM; centres **4,750**. Official press PDFs hashed.
- **MCC 2024:** seat-matrix CSV (674) + Round-1/stray allotment CSVs; Rounds 2–3 checkpointed.
- **Kerala:** de-identified rank (46,367), allotment (19,290), last-rank (2,288) panels under `data/processed/kerala/`.
- **NMC prelim script:** now uses `stateName` / `managementupdate`.

## Still blocked

- **OpenICPSR E112992** — login wall (reconfirmed by probe).
- **MoSPI / DHS / IHDS / PRICE / Young Lives** — free accounts still required (`docs/GATED_NEXT.md`; status in `data/processed/gated_download_status.csv`).
- **Dakshana / Super 50 / SATHEE / CSRL / Careers360 / commercial coaching microdata** — require outreach (`docs/COACHING_GAP_ASK_LIST.md`).

## Validation

- Privacy header audit on processed CSVs still required before committing new processed extracts from named allotment lists.
- Kerala/TN allotment PDFs may contain candidate identifiers; keep raw only under gitignored paths and aggregate before `data/processed/`.
