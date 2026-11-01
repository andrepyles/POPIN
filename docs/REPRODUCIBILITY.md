# POPIN v4.1.0 — reproduction guide

This guide identifies the frozen data snapshot used by the manuscript and the files needed to regenerate the published tables. The POPIN measurement instrument is version 4; `v4.1.0` is the reproducibility package revision.

## Frozen specification

- Model: `gpt-5.6-luna` (GPT-5.6 Luna).
- Prompt: `v4`, with definitions for all six POPIN dimensions.
- Input: the available full text, one document per score, not chunked.
- Final score: unweighted arithmetic mean of `people_centrism`, `anti_elitism`, `moral_dichotomy`, `popular_sovereignty`, `exclusionary_rhetoric`, and `crisis_rhetoric`.
- Article population: `dtype = 'SPEECH'`.
- Frozen dataset: 45,492 non-invalid documents, 19 countries, 105 leaders, 2000–2025; 34,821 are speeches.
- Score provenance: 44,592 rows have `scope='full'`; 900 distinct documents have `scope='pilot'`. Both cohorts use prompt v4 and the unchunked GPT-5.6 scorer. Exports retain their provenance; do not report the full-run count as 45,492.
- No post-hoc GPD rescaling is applied.
- The earlier public v4.0 snapshot used Qwen3-30B-A3B-Instruct and 800-word chunks. It is a separate model/scoring release.

## Download and integrity

Download `popin.duckdb`, `popin_v4_scores.csv`, and `popin_v4_scores.parquet` from the [GitHub release v4.1.0](https://github.com/andrepyles/POPIN/releases/tag/v4.1.0). Compare each file's SHA-256 to `docs/RELEASE_MANIFEST_V4_20260908.json` and the release notes before analysis.

Keep the database read-only. It is the full research database; `06_website/popin_web.duckdb` is a 5.6 MB dashboard snapshot and is not a replacement for it.

## Rebuild score exports and descriptive tables

Environment: Python 3, `duckdb`, `pandas`, and `numpy`; pinned versions are in `requirements-reproducibility.txt`. DuckDB writes the Parquet export directly; `pyarrow` is not required.

Install the pinned analysis dependencies with:

```bash
python -m pip install -r requirements-reproducibility.txt
```

Place `popin.duckdb` in the repository root or set `DB_PATH`, then run:

```bash
python 50_generate_final_tables.py
```

The script reads `discourses` and `scores` in read-only mode. It selects model `gpt-5.6-luna`, prompt `v4`, `status='ok'`, `chunked=false`, scopes `full` and `pilot`, and excludes `INVALID`. It checks for duplicate IDs, missing scores, and the frozen row/cohort counts before writing.

Outputs under `data/release_v4/`:

- `popin_v4_scores.csv` and `popin_v4_scores.parquet`: one selected score per document with full/pilot cohort provenance.
- `analysis/country_speech.csv`, `leader_speech.csv`, `year_speech.csv`, and `dimension_speech.csv`: descriptive summaries of the 34,821 `SPEECH` records.
- `analysis/analysis_metadata.json`: filters, population and cohort counts.

Regenerate the audit outputs and consolidated validation tables with:

```bash
python tools/reproduce_validation_audit.py
python 51_generate_validation_tables.py
```

The audit script uses the release database plus the versioned crosswalk and sensitivity inputs under `data/release_v4/analysis/source_inputs/`; it does not require a local backup database or private file paths. Validation inputs, filters, counts and hashes are recorded in `data/release_v4/analysis/validation/validation_metadata.json` and its README. GPD and LALLPI citations/versions are documented in the source-input README and root manifests.

## Minimal query

```python
import duckdb

con = duckdb.connect("popin.duckdb", read_only=True)
result = con.sql("""
    SELECT d.iso3, AVG(s.final_score) AS mean_score, COUNT(*) AS n
    FROM scores s
    JOIN discourses d ON d.id = s.discourse_id
    WHERE s.model_id = 'gpt-5.6-luna'
      AND s.prompt_id = 'v4'
      AND s.status = 'ok'
      AND s.chunked = FALSE
      AND s.scope IN ('full', 'pilot')
      AND d.dtype = 'SPEECH'
    GROUP BY d.iso3
    ORDER BY mean_score DESC
""").fetchdf()
print(result)
con.close()
```

## Interpretation and source terms

Report `n`, the aggregation unit, the model/prompt, and the scoring cohort. Country and leader estimates weight each speech equally; the descriptive standard error in the tables is the document-level sample standard deviation divided by the square root of `n`, and does not model within-leader or within-country dependence. The corpus preserves source attribution and is distributed under the same corpus coverage used by the earlier public v4.0 database; source-specific terms still apply. See the source manifests before redistributing text separately from this research release.
