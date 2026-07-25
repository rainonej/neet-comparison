# Small processed snapshots

Only tiny, citation-ready benchmarks and previews are stored here. Full external datasets are not committed unless redistribution is explicitly permitted.

- `published_estimates.csv` contains reported values with limitations in every row.
- `neet_2024_dataful_preview.csv` is a ten-row structural preview, not a substitute for downloading and verifying the official centre PDFs.
- `bayesian/` holds conjugate posterior summaries from `scripts/run_bayesian_model.py` (`posterior_summary.csv`, `profile_comparison.csv`, `ppc_coaching.csv`, `bayesian_results.json`). See `reports/BAYESIAN_MODEL_REPORT.md`.
- Privilege-story outputs in the same folder: `access_by_stratum.csv`, `earnings_quantiles_by_outcome.csv`, `earnings_histograms.csv` (display bins), `earnings_kde.csv` (smooth densities), `cdf_points.csv`, `inequality_story.json` from `make privilege`. Government vs private *college* seats share the same physician wage prior; public vs private *sector* physician wages are a separate comparison. See `reports/PRIVILEGE_INEQUALITY_STORY.md`.
- `mospi/` holds commit-safe weighted aggregates from local MoSPI unit files (`make mospi` / `scripts/process_mospi_priority.py`): PLFS wage anchors, CMSE coaching priors, HCES MPCE percentiles, AIDIS debt percentiles. Unit microdata stay under `data/external/mospi/` (gitignored).

The `neet_2024_marks_*` tables were generated from a 32.2 MB public third-party reconstruction of the official NTA centre PDFs. The raw reconstruction is retained locally under `data/external/`, hashed, and gitignored. Its 2,333,162 rows must still be reconciled against official candidate-count releases and alternative reconstructions before it is treated as canonical.
