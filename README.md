# POPIN v4 — Populism Index · Latin America

**POPIN** (*Populism Index*) is a large-scale computational measurement of populist discourse by Latin American heads of government, covering 19 countries from 2000 to 2025.

The index scores each discourse across six analytical dimensions derived from the ideational approach to populism (Mudde & Kaltwasser, 2017; Hawkins et al., 2019), using a large language model (Qwen3-30B) as the classification engine.

🌐 **Dashboard**: [popin-4tvv.onrender.com](https://popin-4tvv.onrender.com)   
📦 **Data release**: [Releases → v4.0](https://github.com/andrepyles/POPIN/releases/tag/v4.0)

---

## Coverage

| | |
|---|---|
| **Countries** | 19 (Argentina, Bolivia, Brazil, Chile, Colombia, Costa Rica, Cuba, Dominican Republic, Ecuador, Guatemala, Honduras, Mexico, Nicaragua, Panama, Paraguay, Peru, El Salvador, Uruguay, Venezuela) |
| **Leaders** | 105 heads of government |
| **Period** | 2000–2025 |
| **Discourses** | 48,256 collected · 45,492 scored |
| **Model** | Qwen3-30B-A3B-Instruct (vLLM) |

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

Each discourse is scored 0–100 on six dimensions, plus a weighted final score:

| Dimension | Description |
|-----------|-------------|
| `people_centrism` | Appeals to "the people" as a homogeneous, virtuous group |
| `anti_elitism` | Condemnation of corrupt elites opposed to the people |
| `moral_dichotomy` | Manichean framing of society as morally divided |
| `popular_sovereignty` | Claim that power belongs exclusively to the people |
| `exclusionary_rhetoric` | Othering of groups portrayed as threats to the people |
| `crisis_rhetoric` | Framing of politics as an existential crisis requiring urgency |
| `final_score` | Weighted mean of all six dimensions |

---

## Repository structure

```
POPIN/
├── 06_website/
│   ├── main.py               # FastAPI backend
│   ├── popin_web.duckdb      # Slim DB for the dashboard (no discourse text)
│   ├── render.yaml           # Render deployment config
│   ├── requirements.txt
│   └── static/
│       ├── index.html
│       ├── css/style.css
│       ├── js/app.js
└── README.md
```

---

## Data

The full dataset is distributed as a [GitHub Release](https://github.com/andrepyles/POPIN/releases/tag/v4.0):

| File | Size | Contents |
|------|------|----------|
| `popin.duckdb` | 1.3 GB | Complete database — discourses, scores, metadata |
| `popin_scores.xlsx` | 4.9 MB | Per-discourse scores, no text — ready for pivot tables |

### Querying the database

```python
import duckdb

con = duckdb.connect("popin.duckdb", read_only=True)

# List tables
con.execute("SHOW TABLES").fetchdf()

# Average final score by country
con.execute("""
    SELECT d.iso3, ROUND(AVG(s.final_score), 2) AS avg_score, COUNT(*) AS n
    FROM scores s
    JOIN discourses d ON d.id = s.discourse_id
    WHERE s.final_score IS NOT NULL
    GROUP BY d.iso3
    ORDER BY avg_score DESC
""").fetchdf()
```

### Excel file columns

| Column | Type | Description |
|--------|------|-------------|
| `discourse_id` | string | SHA hash — unique discourse identifier |
| `iso3` | string | ISO 3166-1 alpha-3 country code |
| `country` | string | Country name |
| `leader_name` | string | Full name of the leader |
| `year` | integer | Year of the discourse |
| `discourse_type` | string | SPEECH / PRESS_RELEASE / INTERVIEW / COMMUNIQUE / DECREE / LETTER |
| `word_count` | integer | Discourse length in words |
| `n_chunks` | integer | Number of chunks processed by the model |
| `people_centrism` | float | Score 0–100 |
| `anti_elitism` | float | Score 0–100 |
| `moral_dichotomy` | float | Score 0–100 |
| `popular_sovereignty` | float | Score 0–100 |
| `exclusionary_rhetoric` | float | Score 0–100 |
| `crisis_rhetoric` | float | Score 0–100 |
| `final_score` | float | Weighted mean 0–100 |
| `model_id` | string | Model used for scoring |
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
2. **Classification** — Discourse type assigned via LLM (Qwen3-30B)
3. **Scoring** — Each discourse chunked and scored on 6 dimensions (0–100) using structured LLM output
4. **Aggregation** — Country and leader scores computed as means over all scored discourses

---

## Citation

If you use POPIN data in academic work, please cite:

> Siqueira, André Pyles (2026). *POPIN v4: A Computational Populism Index for Latin America, 2000–2025*. Master's thesis, [Institution]. Data available at: https://github.com/andrepyles/POPIN

---

## References

- Mudde, C. (2004). The populist zeitgeist. *Government and Opposition*, 39(4), 541–563.
- Mudde, C., & Kaltwasser, C. R. (2017). *Populism: A very short introduction*. Oxford University Press.
- Hawkins, K. A., et al. (2019). *The ideational approach to populism*. Routledge.
