# Open data downloads

Last updated: 2026-07-25

Local raw archives are gitignored under `data/external/` and `data/raw/`.  
Inventory: [`data/processed/local_data_inventory.csv`](../data/processed/local_data_inventory.csv) (~699 files, ~1.06 GB as of last build).

## Successfully downloaded

| Source | Local path | What we got |
|---|---|---|
| OSF `tnh4x` | `data/external/osf/tnh4x/raw/` | Survey CSV + methods + scales |
| NEET-2024 marks reconstruction | `data/external/neet-2024-center-marks.csv` + `github_hq969/raw/` | Full CSV (2.33M rows), centres CSV, longnames, SQLite/DB (~40MB) |
| NMC colleges | `data/raw/nmc_*.csv/json` | 823 UG colleges via JSON API |
| MCC UG archive | `data/raw/mcc_2024/`, `data/raw/mcc_ug/{2023,2025}/` | 2023 (~62 PDFs), 2024 (37), 2025 (4+) |
| Kerala CEE/KEAM | `data/external/kerala_cee/raw/files/` | **100+ PDFs**: medical rank lists, allotments, last ranks, category lists, BPL scholarship archives |
| NIRF Medical | `data/external/nirf/raw/` | Ranking HTML 2023–2025 + 150 institution report PDFs |
| NTA public notices / bulletins | `data/external/nta/raw/files/` | Information bulletins + public-notice PDFs from neet.nta.nic.in |
| Tamil Nadu | `data/external/tamil_nadu/` | Rajan Committee PDF + counselling archive PDFs |
| World Bank / WID | `data/external/world_bank/`, `wid/` | Health labor PDF; India inequality WP |
| NCRB ADSI | `data/external/ncrb/raw/` | Suicide/accident report PDFs linked from ADSI page |
| Dakshana / CBSE press | `data/external/dakshana/`, `cbse/` | Coaching-foundation annual reports; CBSE dummy-school inspection releases |
| Wayback NTA centre PDFs | `data/raw/neet_2024/pdfs_wayback/` | **14** archived centre PDFs only (live host is dead) |

## Not obtainable without login / host down

| Source | Status |
|---|---|
| OpenICPSR E112992 | Free ICPSR login required for download |
| Official live NTA centre PDFs (~4,750) | `neetfs.ntaonline.in` returns 404 / “not configured”; only 14 on Wayback |
| MoSPI / DHS / IHDS / PRICE / Young Lives | Account-gated — see [GATED_NEXT.md](GATED_NEXT.md) |

## Scripts

```bash
python scripts/download_kerala_files.py
python scripts/download_public_bulk.py --skip-mcc-years
python scripts/scrape_mcc_archive.py --year 2024 --out data/raw/mcc_2024
python scripts/scrape_nmc_colleges.py
python scripts/build_local_inventory.py
python scripts/register_download.py --path ... --url ...
```
