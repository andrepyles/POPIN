# POPIN v4.1.0 — code map

The index and six measurement dimensions remain POPIN v4. Release v4.1.0 packages the GPT-5.6 Luna, prompt v4, full-text snapshot described in the current manuscript. Release v4.0 is an earlier Qwen3 chunked scoring snapshot; do not treat the two model outputs as one analytical run.

## Reproducing the frozen tables

| Step | File | Function |
|---|---|---|
| 1 | `popin.duckdb` (release asset) | Full corpus, score runs, source tables and execution metadata |
| 2 | `50_generate_final_tables.py` | Selects GPT-5.6 v4 full-text scores, exports CSV/Parquet and descriptive SPEECH tables |
| 3 | `tools/reproduce_validation_audit.py` | Recomputes GPD, LALLPI, model-comparison, prompt-sensitivity and integrity outputs from DuckDB and packaged audit inputs |
| 4 | `51_generate_validation_tables.py` | Consolidates the reproducible validation outputs for publication |
| 5 | `25_luna_all_noninvalid_openai_batch.py` | Driver used for the GPT-5.6 Luna full-text v4 scoring run |
| 6 | `04_score.py` | Contains the original POPIN v4 measurement prompt and the legacy Qwen/vLLM chunked scorer |

Run the export generator from the repository root after downloading the release database to `popin.duckdb`:

```bash
python 50_generate_final_tables.py
python tools/reproduce_validation_audit.py
python 51_generate_validation_tables.py
```

By default, outputs are written to `data/release_v4/`. Set `DB_PATH` to use a database in another location and `OUT_DIR` to change the output directory.

The manuscript's score snapshot is already in `popin.duckdb`; rerunning the Luna batch is not needed to regenerate manuscript tables. The batch driver is included to document the original scoring procedure. Running it submits model requests and requires an OpenAI API key; see `docs/LUNA_BATCH_JOB.md` before running it.

## Execution and import history

- `01_setup_db.py` through `03_classify.py`: database setup, corpus migration and document classification.
- `04_score.py`: original v4 Qwen/vLLM scorer, 800-word chunks and word-weighted aggregation.
- `10_full_deepseek.py` and `11_import_deepseek_scores.py`: DeepSeek comparison runs.
- `25_luna_all_noninvalid_openai_batch.py`: GPT-5.6 Luna full-text run driver.
- `31_luna_chunked_batch.py` through `35_analyze_luna_chunked.py`: Luna chunked robustness run.
- `36_import_score_history.py` through `40_filter_small_runs.py`: score-history import and database normalization.
- `49_luna_full_prompt_sensitivity_batch.py`: prompt sensitivity sample.

Execution JSONL files, pilots and model comparisons are supporting evidence. Keep their `model_id`, prompt, chunking, scope and run identifiers when using them; they do not replace the frozen selection.

The minimal audit inputs are stored under `data/release_v4/analysis/source_inputs/`; large exploratory runs and temporary processing files are not part of the public package.

## Website snapshot

`06_website/popin_web.duckdb` is a compact dashboard database. It does not contain the full source texts and is not sufficient to reproduce the corpus analyses. Use the root `popin.duckdb` release asset for the research database. The dashboard can be run independently from `06_website/`.

For data fields see `docs/DATA_DICTIONARY.md`; for exact filters and hashes see `docs/REPRODUCIBILITY.md` and `docs/RELEASE_MANIFEST_V4_20260908.json`.
