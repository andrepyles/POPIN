# GPT-5.6 Luna scoring job

`25_luna_all_noninvalid_openai_batch.py` is the batch driver for the manuscript's GPT-5.6 Luna full-text run. It reads the discourse text from `popin.duckdb`, uses the v4 system prompt defined in `04_score.py`, sends one request per non-`INVALID` document through the OpenAI Batch API, and imports completed scores into `scores` with run ID `luna__all_noninvalid__openai__v4`.

## Reproducing the published analysis

The released `popin.duckdb` already contains the manuscript scores and the underlying discourse texts. An evaluator can regenerate the exports and tables without making new model calls:

```bash
python 50_generate_final_tables.py
```

The raw batch output JSONL is not required for this step: the database preserves the selected scores, raw model responses, model/prompt identifiers, and run metadata.

## Re-running the model job

The driver is provided to document the scoring procedure and support a fresh run. It requires `duckdb`, a writable working copy of the database, and `OPENAI_API_KEY` set in the environment or a local `.env` file. Running it submits billable requests and writes scores into the database; it is not part of table regeneration. The historical batch state and transient API batch IDs are not included.

The scorer sends the complete available text for each document in one request; it does not chunk or truncate the text. API limits or failures are recorded by the job rather than silently shortening inputs. Because hosted models can change, a new run may not reproduce every historical score exactly; use the frozen database snapshot to reproduce the published tables.
