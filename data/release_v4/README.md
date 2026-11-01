# POPIN v4.1.0 — score exports and analysis tables

This folder contains compact exports for the manuscript snapshot, derived from the full `popin.duckdb` analytical database distributed as a v4.1.0 GitHub release asset.

## Files

- `popin_v4_scores.csv` — one GPT-5.6 Luna score per non-invalid document.
- `popin_v4_scores.parquet` — same rows and columns in Parquet format.
- `analysis/` — descriptive summaries for the main `SPEECH` population and frozen validation outputs.
- `analysis/source_inputs/` — the small versioned crosswalks and sensitivity output files required to reproduce validation analyses.

The frozen 45,492-document export contains 44,592 records with `score_scope=full` and 900 distinct records with `score_scope=pilot`. Both use prompt v4 and one unchunked full-text unit per document. The export retains `score_scope`, `score_coverage`, `source_kind`, `provider`, `prompt_version`, and `chunked`; keep those fields when filtering or reporting results.

The manuscript's primary substantive analysis filters `dtype = 'SPEECH'` (34,821 documents). See `docs/DATA_DICTIONARY.md`, `docs/REPRODUCIBILITY.md`, and `docs/RELEASE_MANIFEST_V4_20260908.json` for the schema, exact filters, hashes, and steps to rebuild the files.

To regenerate the score export and descriptive tables, download the release's `popin.duckdb` to the repository root and run:

```bash
python 50_generate_final_tables.py
python tools/reproduce_validation_audit.py
python 51_generate_validation_tables.py
```

The dashboard database under `06_website/` is a compact web snapshot and is not the source of record for the research corpus or these exports.
