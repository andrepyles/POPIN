# POPIN v4 — Populism Index · Latin America

**POPIN** (*Populism Index*) is a large-scale computational measurement of populist discourse by Latin American heads of government, covering 19 countries from 2000 to 2025.

The index scores each discourse across six analytical dimensions derived from the ideational approach to populism (Mudde & Kaltwasser, 2017; Hawkins et al., 2019), using a large language model as the measurement instrument. The v4.1.0 reproducibility package documents the GPT-5.6, prompt v4, full-text snapshot used by the current manuscript. The earlier v4.0 release remains available as a Qwen3 chunked scoring snapshot.

🌐 **Dashboard**: [popin-4tvv.onrender.com](https://popin-4tvv.onrender.com)
📦 **Current reproducibility package**: [Release v4.1.0](https://github.com/andrepyles/POPIN/releases/tag/v4.1.0)
📦 **Earlier Qwen snapshot**: [Release v4.0](https://github.com/andrepyles/POPIN/releases/tag/v4.0)

---

## Coverage

| | |
|---|---|
| **Countries** | 19 (Argentina, Bolivia, Brazil, Chile, Colombia, Costa Rica, Cuba, Dominican Republic, Ecuador, Guatemala, Honduras, Mexico, Nicaragua, Panama, Paraguay, Peru, El Salvador, Uruguay, Venezuela) |
| **Leaders** | 105 heads of government |
| **Period** | 2000–2025 |
| **Discourses** | 48,256 collected · 45,492 scored |
| **Manuscript snapshot** | GPT-5.6 Luna, prompt v4, full text, no chunking |
| **Earlier snapshot** | Qwen3-30B-A3B-Instruct (vLLM), 800-word chunks |

### Discourse types

| Type | N |
|------|---|
| Speech | 34,821 |
| Press Release | 6,675 |
| Interview | 2,653 |
| Communiqué | 859 |
| Decree | 322 |
| Letter | 162 |

---

## Dimensions

Each discourse is scored 0–100 on six dimensions, plus a final score. In the v4.1.0 manuscript snapshot each available full text is scored as one unit; the final discourse score is the arithmetic mean of the six dimensions. The earlier v4.0 snapshot aggregates 800-word chunks using their word counts.

| Dimension | Description |
|-----------|-------------|
| `people_centrism` | Appeals to "the people" as a homogeneous, virtuous group |
| `anti_elitism` | Condemnation of corrupt elites opposed to the people |
| `moral_dichotomy` | Manichean framing of society as morally divided |
| `popular_sovereignty` | Claim that power belongs exclusively to the people |
| `exclusionary_rhetoric` | Othering of groups portrayed as threats to the people |
| `crisis_rhetoric` | Framing of politics as an existential crisis requiring urgency |
| `final_score` | Arithmetic mean of the six dimension scores |

---

## Data

The manuscript snapshot and the earlier model snapshot are separate. Download the analytical database and score exports from [GitHub Release v4.1.0](https://github.com/andrepyles/POPIN/releases/tag/v4.1.0). Release v4.0 preserves the earlier Qwen3/chunked dataset.

| File | Size | Contents |
|------|------|----------|
| `popin.duckdb` | ~1.5 GB | Full analytical database — discourses, scores, source and run metadata |
| `popin_v4_scores.csv` | ~9.2 MB | Frozen GPT-5.6 v4 scores, with scoring cohort provenance |
| `popin_v4_scores.parquet` | ~1.0 MB | Same score table in Parquet format |

The 45,492-document score snapshot contains 44,592 records from the full run and 900 records from a separately identified pilot run. Both are exported with their `score_scope`, `score_coverage`, and `source_kind` fields. The pilot records are never presented as if they came from the full-run batch. See the release manifest and reproducibility guide for exact filters and hashes.

To regenerate the exports and analysis tables, install the pinned dependencies from [`requirements.txt`](requirements.txt) and follow [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md).

### Querying the database

```python
import duckdb

con = duckdb.connect("popin.duckdb", read_only=True)

# List tables
con.execute("SHOW TABLES").fetchdf()

# Manuscript snapshot: average final score by country
con.execute("""
    SELECT d.iso3, ROUND(AVG(s.final_score), 2) AS avg_score, COUNT(*) AS n
    FROM scores s
    JOIN discourses d ON d.id = s.discourse_id
    WHERE s.model_id = 'gpt-5.6-luna'
      AND s.prompt_id = 'v4'
      AND s.status = 'ok'
      AND s.chunked = FALSE
      AND s.scope IN ('full', 'pilot')
      AND d.dtype = 'SPEECH'
    GROUP BY d.iso3
    ORDER BY avg_score DESC
""").fetchdf()
```

### Portable score export columns

| Column | Type | Description |
|--------|------|-------------|
| `discourse_id` | string | SHA hash — unique discourse identifier |
| `iso3` | string | ISO 3166-1 alpha-3 country code |
| `leader_name` | string | Full name of the leader |
| `year` | integer | Year of the discourse |
| `dtype` | string | SPEECH / PRESS_RELEASE / INTERVIEW / COMMUNIQUE / DECREE / LETTER |
| `word_count` | integer | Discourse length in words |
| `n_chunks` | integer | Number of chunks processed by the model |
| `people_centrism` | float | Score 0–100 |
| `anti_elitism` | float | Score 0–100 |
| `moral_dichotomy` | float | Score 0–100 |
| `popular_sovereignty` | float | Score 0–100 |
| `exclusionary_rhetoric` | float | Score 0–100 |
| `crisis_rhetoric` | float | Score 0–100 |
| `final_score` | float | Arithmetic mean of six dimensions, 0–100 |
| `model_id` | string | Model used for scoring |
| `prompt_version` | string | POPIN prompt version |
| `provider` | string | Scoring provider/execution route |
| `score_scope` | string | `full` or `pilot` cohort |
| `score_coverage` | string | Coverage label from the scoring run |
| `source_kind` | string | Provenance class stored in DuckDB |
| `chunked` | boolean | Whether the discourse was scored by chunks |
| `scored_at` | timestamp | Scoring timestamp |

---

## Dashboard

The interactive dashboard is built with **FastAPI + DuckDB + Plotly.js** and deployed on [Render](https://render.com).

Features:
- Choropleth map of populism scores across Latin America
- Country and leader rankings
- Time series (2000–2025) with country comparison
- Dimensional radar profiles per country and leader
- Discourse type filter (speeches, interviews, press releases, etc.)
- Dark / light theme · PT / EN

To run locally:

```bash
cd 06_website
pip install -r requirements.txt
uvicorn main:app --port 8000
# open http://localhost:8000
```

---

## Methodology

### Populism operationalization

The index follows the ideational definition of populism, treating it as a thin-centered ideology that considers society divided into two homogeneous and antagonistic groups — "the pure people" versus "the corrupt elite" — and argues that politics should be an expression of the *volonté générale* of the people (Mudde, 2004).

The six dimensions are drawn from the Populist Rhetoric Coding Scheme (PRCS) and related frameworks used in comparative text analysis of political communication.

### Scoring pipeline

1. **Collection** — Presidential speeches, communiqués, interviews, decrees and letters collected from official government portals and archives
2. **Classification** — Discourse type assigned via LLM; invalid documents are excluded from scoring
3. **Scoring (v4.1.0 manuscript snapshot)** — GPT-5.6 Luna evaluates each full text with prompt v4 across six dimensions; the snapshot is not chunked. The full-run and pilot cohorts remain separately identified.
4. **Earlier scoring snapshot (v4.0)** — Qwen3-30B-A3B-Instruct evaluates contiguous chunks of up to 800 words; chunk scores are weighted by word count.
5. **Aggregation** — The final discourse score is the arithmetic mean of the six dimensions; country and leader scores are means over documents.

See [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md), [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md), and [`docs/RELEASE_MANIFEST_V4_20260908.json`](docs/RELEASE_MANIFEST_V4_20260908.json) for the exact workflow and data lineage.

---

## Citation

If you use POPIN data in academic work, please cite:

> Siqueira, André Pyles (2026). *Populismo em números: construção de um índice para mensurar a retórica populista na América Latina no século XXI*. Master's thesis, Universidade Presbiteriana Mackenzie. Data (POPIN v4) available at: https://github.com/andrepyles/POPIN

---

## References

- Mudde, C. (2004). The populist zeitgeist. *Government and Opposition*, 39(4), 541–563.
- Mudde, C., & Kaltwasser, C. R. (2017). *Populism: A very short introduction*. Oxford University Press.
- Hawkins, K. A., et al. (2019). *The ideational approach to populism*. Routledge.
