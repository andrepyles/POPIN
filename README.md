# POPIN v4

## Populism Index for Latin America

POPIN is a reproducible framework for measuring populist discourse in presidential communication across Latin America. Version 4 covers 19 countries and presidential documents collected between 2000 and 2025.

The project operationalizes the ideational approach to populism as a text-based measurement instrument. It is designed to make the corpus, scoring rule, uncertainty checks, and model provenance explicit.

- Dashboard: [popin-4tvv.onrender.com](https://popin-4tvv.onrender.com)
- Repository: [github.com/andrepyles/POPIN](https://github.com/andrepyles/POPIN)
- Release: [POPIN v4.1.0](https://github.com/andrepyles/POPIN/releases/tag/v4.1.0)

## Release scope

| Item | Coverage |
|---|---:|
| Countries | 19 |
| Period | 2000–2025 |
| Documents collected | 48,256 |
| Documents eligible for scoring | 45,492 |
| Primary discourse types | speeches, press releases, interviews, communiqués, decrees, letters |

The repository contains the analysis code and a compact database snapshot used by the web dashboard. The complete analytical DuckDB database and raw text corpus are intentionally kept outside Git because of their size and are handled as data-release artifacts.

## Construct and dimensions

Each eligible document receives a score from 0 to 100 on six theoretically distinct dimensions:

| Field | Meaning |
|---|---|
| `people_centrism` | representation of the people as a unified and virtuous collective |
| `anti_elitism` | criticism of elites as opposed to the people |
| `moral_dichotomy` | moral division between the people and their opponents |
| `popular_sovereignty` | claim that political authority belongs to the people |
| `exclusionary_rhetoric` | exclusion or othering of groups portrayed as threats |
| `crisis_rhetoric` | presentation of politics as an urgent or existential crisis |

`final_score` is the arithmetic mean of the six dimensions. The dimensions remain separately available because they represent different theoretical mechanisms, even when empirical correlations between them are high.

## Version 4 scoring rule

1. Documents classified as `INVALID` are excluded.
2. Text is divided into contiguous chunks of at most 800 words, without overlap.
3. The scoring prompt requests one structured numeric score for each dimension.
4. Chunk scores are aggregated using chunk word counts.
5. The document score is the mean of the six aggregated dimensions.
6. Every score records the model, prompt version, chunking information, and timestamp.

The code is model-agnostic. This is deliberate: model comparisons and sensitivity analyses must use the same discourse IDs and be identified by metadata rather than silently replacing one model with another. The dashboard snapshot currently opens with the full-text GPT-5.6 Luna view; comparative outputs belong in the analytical data package.

## Repository layout

```text
01_setup_db.py          Create the core DuckDB schema
02_migrate.py           Import and normalize the discourse corpus
03_classify.py          Classify document type and validity
04_score.py             Score documents with the v4 rule
05_dashboard.py         Generate the analytical dashboard
06_robustness_checks.py Run robustness diagnostics
07_pca_analysis.py      Inspect dimensional structure
06_website/              FastAPI dashboard and web-data snapshot
```

The exploratory model and prompt experiments are preserved in the repository history, but are not part of the release `main` surface. This keeps the public entry point focused on the reproducible pipeline.

## Reproduce the pipeline

Create a virtual environment, install the project dependencies used by the scripts, and configure credentials locally. Never commit `.env` or API keys.

```bash
python -m venv .venv
source .venv/bin/activate
pip install duckdb pandas numpy scikit-learn requests tqdm
cp .env.example .env
```

Set the input paths and provider credentials in the local environment, then run:

```bash
python 01_setup_db.py
python 02_migrate.py --resume
python 03_classify.py --resume --concurrency 24
python 04_score.py --concurrency 16
python 06_robustness_checks.py
python 07_pca_analysis.py
```

For the web dashboard:

```bash
cd 06_website
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000).

## Data model

The core database uses `discourses` as the document table and `scores` as the model-output table. The score table is keyed by discourse and run metadata, allowing multiple models, prompts, and chunking strategies to coexist without overwriting one another.

At minimum, analyses should report:

- the discourse universe and exclusion rule;
- the model and prompt version;
- whether scoring was full-text or chunked;
- the aggregation unit and minimum number of documents;
- uncertainty measures such as standard errors or confidence intervals.

## Citation

Please cite the working paper and the release when using POPIN. The citation record will be updated with the SSRN and journal references when available.

> Siqueira, André Pyles. *Populismo em números: construção de um índice para mensurar a retórica populista na América Latina no século XXI*. Master's thesis, Universidade Presbiteriana Mackenzie. POPIN v4.1.0.

## References

- Hawkins, K. A., Carlin, R. E., Littvay, L., & Rovira Kaltwasser, C. (2019). *The Ideational Approach to Populism*. Routledge.
- Mudde, C. (2004). The populist zeitgeist. *Government and Opposition*, 39(4), 541–563.
- Mudde, C., & Rovira Kaltwasser, C. (2017). *Populism: A Very Short Introduction*. Oxford University Press.
