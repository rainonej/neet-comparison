# Execution notes — 2026-07-24

## Successfully acquired and processed

A complete public third-party reconstruction of the anonymized NEET-UG 2024 centre-wise marks was downloaded from `hq969/neet-2024-center-marks`.

- Raw size: 33,800,799 bytes
- SHA-256: `35b67efe2fed174b49ff023e807b4f51cdb8f3c3a0396739b01f88cfb6bb114c`
- Parsed rows: 2,333,162
- Unique centre IDs: 4,750
- Score range: -180 to 720
- Median: 163
- 90th percentile: 484
- 99th percentile: 657

The raw file is preserved locally under `data/external/` but is not tracked or packaged because the reconstruction repository does not expose an explicit redistribution licence. Reproducible summaries and a download manifest are tracked.

## Direct official acquisition

The official NTA index and PDF endpoints were identified and implemented in `scripts/fetch_neet_2024_centres.py`. DNS access to the NTA host was unavailable from the execution container during the audit, so the official downloader could not be live-validated here. The independent reconstruction documents the same endpoints and extraction process. A future run should download the official PDFs, retain hashes, compare row counts, and treat discrepancies as data-quality findings rather than silently choosing one reconstruction.

## Registration-gated files

HCES, CMSE, PLFS, NFHS, AIDIS, and related microdata were not redistributed. Their catalogs, required variables, and intended joins are recorded. A human account/licence acceptance step is required before placing the files under `data/raw/restricted/`.

## Validation

- Source catalog audit passed.
- Five repository tests passed.
- Processed score-band counts sum exactly to the acquired raw row count.
