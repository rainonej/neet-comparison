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

## Still blocked

- **OpenICPSR E112992** — login wall.
- **MoSPI / DHS / IHDS / PRICE / Young Lives** — deferred to gated pass (`docs/GATED_NEXT.md`).

## Validation

- Privacy header audit on processed CSVs still required before committing new processed extracts from named allotment lists.
- Kerala/TN allotment PDFs may contain candidate identifiers; keep raw only under gitignored paths and aggregate before `data/processed/`.
