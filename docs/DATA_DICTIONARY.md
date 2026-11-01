# POPIN v4.1.0 — data dictionary

## Analytical database

Download `popin.duckdb` from the [v4.1.0 GitHub release](https://github.com/andrepyles/POPIN/releases/tag/v4.1.0). The root database is the complete research database and contains discourse texts, score histories, source tables and run metadata. `06_website/popin_web.duckdb` is a small dashboard snapshot and is not the analytical source of record.

The frozen manuscript snapshot has 45,492 non-invalid documents (34,821 `SPEECH`), across 19 countries, 105 leaders and 2000–2025. It uses GPT-5.6 Luna, prompt `v4`, the available full text without chunking, and six equally weighted dimensions. The score selection has two separately recorded cohorts: 44,592 rows with `scope='full'` and 900 rows with `scope='pilot'`. These are distinct document IDs. The export retains the cohort fields.

## Tables

### `discourses`

One row per source document. The `discourse` field contains the text present in the published corpus snapshot.

| Field | Type | Definition |
|---|---|---|
| `id` | VARCHAR | Stable discourse identifier; joins to `scores.discourse_id` |
| `iso3` | VARCHAR | ISO 3166-1 alpha-3 country code |
| `leader_name` | VARCHAR | Standardized leader name |
| `filename` | VARCHAR | Source document filename |
| `language` | VARCHAR | Language metadata when available |
| `discourse_place` | VARCHAR | Place metadata when available |
| `discourse_date` | DATE | Document date when available |
| `discourse_year` | INTEGER | Year used for aggregation |
| `source` | VARCHAR | Source URL or archive attribution |
| `discourse` | VARCHAR | Full text available in the corpus |
| `word_count` | INTEGER | Word count recorded at ingestion |
| `dtype` | VARCHAR | Type: `SPEECH`, `PRESS_RELEASE`, `INTERVIEW`, `COMMUNIQUE`, `DECREE`, `LETTER`, or `INVALID` |
| `ingested_at` | TIMESTAMP | Ingestion timestamp |

### `scores`

Scoring results and provenance. Multiple models, prompts and runs can have rows for the same discourse; select a specific version/run before analysis.

| Field | Type | Definition |
|---|---|---|
| `discourse_id` | VARCHAR | Joins to `discourses.id` |
| `model_id` | VARCHAR | Stable model identifier |
| `people_centrism` | FLOAT | People-centrism score, 0–100 |
| `anti_elitism` | FLOAT | Anti-elitism score, 0–100 |
| `moral_dichotomy` | FLOAT | Moral dichotomy score, 0–100 |
| `popular_sovereignty` | FLOAT | Popular sovereignty score, 0–100 |
| `exclusionary_rhetoric` | FLOAT | Exclusionary rhetoric score, 0–100 |
| `crisis_rhetoric` | FLOAT | Crisis rhetoric score, 0–100 |
| `final_score` | FLOAT | Arithmetic mean of the six dimensions, 0–100 |
| `n_chunks` | INTEGER | Number of evaluated units; one for the full-text snapshot |
| `raw_json` | VARCHAR | Stored model response when available |
| `scored_at` | TIMESTAMP | Score timestamp |
| `prompt_id` | VARCHAR | Prompt version/identifier |
| `provider` | VARCHAR | Provider or execution route |
| `run_id` | VARCHAR | Run identifier |
| `score_id` | VARCHAR | Score row identifier |
| `iso3`, `leader_name`, `filename`, `discourse_date`, `discourse_year`, `dtype` | varies | Denormalized discourse metadata |
| `model` | VARCHAR | Model label used by older runs |
| `execution_id` | VARCHAR | Execution/batch identifier |
| `scope` | VARCHAR | Scope such as `full`, `pilot`, or sensitivity sample |
| `coverage` | VARCHAR | Declared coverage for the run |
| `chunked` | BOOLEAN | Whether text was scored in chunks |
| `chunk_words`, `overlap_words`, `valid_chunks` | INTEGER | Chunking metadata, where applicable |
| `word_count` | INTEGER | Input word count recorded for the run |
| `status` | VARCHAR | Run status (the v4.1.0 export uses `ok`) |
| `error_text` | VARCHAR | Error detail where present |
| `source_kind`, `source_file` | VARCHAR | Provenance for imported or active database rows |

### Other tables

The database also retains `raw_gpd_long`, `raw_gpd_wide`, `raw_lallpi_index`, `jobs`, and `v_all_scores_navigable` for validation, execution history and navigation. Consult `SHOW TABLES` and `DESCRIBE <table>` for the exact delivered schema.

## Frozen export fields

The release assets `popin_v4_scores.csv` and `popin_v4_scores.parquet` (also generated under `data/release_v4/` when running `50_generate_final_tables.py`) contain one selected score per non-invalid document. Besides the document metadata and six scores, they include `prompt_version`, `provider`, `score_scope`, `score_coverage`, `source_kind`, `chunked`, and `scored_at` so that the full and pilot cohorts remain identifiable.

## Interpretation

- Scores are points on a 0–100 measurement scale, not percentages of citizens or probabilities.
- The manuscript's primary substantive population is `dtype = 'SPEECH'`.
- Country, leader and year means weight each discourse equally.
- P25–P75 describes the central 50%; it is not a confidence interval.
- Report the model, prompt, cohort, text coverage, aggregation unit and sample size.
- Do not apply post-hoc GPD rescaling to the frozen scores.
- Source texts retain their original provenance and source terms; see the repository's source manifests and release notes.
