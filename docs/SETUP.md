# Setup

## Requirements

- Python **3.11+**
- Network access for acquisition scripts
- Optional: free MoSPI / DHS / ICPSR accounts for gated surveys (see [GATED_NEXT.md](GATED_NEXT.md))

## Install

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

Useful checks:

```bash
make audit      # validate source_catalog.csv
make status     # rebuild reports/source_status.*
make test       # pytest
make summarize  # rebuild NEET-2024 mark summaries from local CSV
```

## Directory layout

```text
data/
  raw/                 # script downloads (NMC, MCC, NTA PDFs, …) — gitignored
  raw/restricted/      # account-gated survey dumps if not using external/ layout
  external/            # third-party archives and large reconstructions — gitignored
    <provider>/<dataset>/<wave>/raw/   # preferred layout for survey originals
  processed/           # small committed summaries, manifests, evidence tables

docs/                  # catalogs, checklists, model and privacy docs
scripts/               # downloaders, auditors, register_download
src/neet_microsim/     # baseline / Bayesian / career scaffolding
config/                # YAML assumptions and priors
reports/               # findings and execution notes
tests/
```

## What is committed vs local-only

**Committed:** catalogs, docs, scripts, small processed CSVs (allowlisted in `.gitignore`), download manifests with SHA-256 hashes.

**Local only (never push):**

- `data/raw/**` (except `.gitkeep`)
- `data/external/**` (except `.gitkeep`)
- `.venv/`, `.env`, credentials, cookies, RTI identity documents
- `_incoming/` staging copies of ChatGPT zip/bundle artifacts

After each download:

```bash
python scripts/register_download.py \
  --path data/external/.../file.zip \
  --url "https://..." \
  --notes "licence / limitation note"
```

## Privacy

Public counselling PDFs may contain names or roll numbers. Aggregate during ingestion and discard identifiers before anything lands under `data/processed/`. Run:

```bash
python scripts/check_processed_privacy.py
```
