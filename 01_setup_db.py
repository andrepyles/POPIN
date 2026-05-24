"""
POPIN v4 — Step 1: Setup do banco DuckDB

Uso:
    python 01_setup_db.py
"""

import os
import duckdb
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "./popin.duckdb")


def setup(db_path: str) -> None:
    con = duckdb.connect(db_path)

    # ── Discursos ─────────────────────────────────────────────────────────────
    # 'id' = SHA-256 do texto normalizado (16 chars).
    # Duplicatas exatas e near-duplicatas são rejeitadas na ingestão — não chegam aqui.
    # dtype: SPEECH | COMMUNIQUE | INTERVIEW | PRESS_RELEASE | DECREE | LETTER | INVALID
    con.execute("""
        CREATE TABLE IF NOT EXISTS discourses (
            id              VARCHAR PRIMARY KEY,
            iso3            VARCHAR NOT NULL,
            leader_name     VARCHAR,
            filename        VARCHAR UNIQUE,
            language        VARCHAR,
            discourse_place VARCHAR,
            discourse_date  DATE,
            discourse_year  INTEGER,
            source          VARCHAR,
            discourse       VARCHAR NOT NULL,
            word_count      INTEGER,
            dtype           VARCHAR,
            ingested_at     TIMESTAMP DEFAULT now()
        )
    """)

    # ── Scores POPIN ──────────────────────────────────────────────────────────
    # Um registro por (discurso × modelo). Permite comparar versões de modelo.
    # Eixos (Mudde 2004; Moffitt 2016; Pappas 2019):
    #   1. people_centrism       — o povo como ator moral central
    #   2. anti_elitism          — crítica moralizada às elites
    #   3. moral_dichotomy       — divisão maniqueia povo/elite
    #   4. popular_sovereignty   — vontade popular como legitimidade suprema
    #   5. exclusionary_rhetoric — exclusão de grupos do "povo verdadeiro"
    #   6. crisis_rhetoric       — invocação performativa de crise/ameaça existencial
    #   final_score              — média simples dos 6 eixos
    con.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            discourse_id            VARCHAR REFERENCES discourses(id),
            model_id                VARCHAR NOT NULL,
            people_centrism         FLOAT,
            anti_elitism            FLOAT,
            moral_dichotomy         FLOAT,
            popular_sovereignty     FLOAT,
            exclusionary_rhetoric   FLOAT,
            crisis_rhetoric         FLOAT,
            final_score             FLOAT,
            n_chunks                INTEGER,
            raw_json                VARCHAR,
            scored_at               TIMESTAMP DEFAULT now(),
            PRIMARY KEY (discourse_id, model_id)
        )
    """)

    # ── Jobs ──────────────────────────────────────────────────────────────────
    # Checkpoint para retomar cargas longas interrompidas (ex: vast.ai cai).
    con.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id      VARCHAR PRIMARY KEY,
            job_type    VARCHAR NOT NULL,
            status      VARCHAR DEFAULT 'running',
            last_row    INTEGER DEFAULT 0,
            total_rows  INTEGER,
            model_id    VARCHAR,
            started_at  TIMESTAMP DEFAULT now(),
            updated_at  TIMESTAMP DEFAULT now()
        )
    """)

    con.commit()
    con.close()


if __name__ == "__main__":
    # Apaga banco existente para começar limpo (remova essa linha em produção)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    setup(DB_PATH)

    con = duckdb.connect(DB_PATH)
    tables = con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    con.close()

    print(f"Banco criado: {DB_PATH}")
    for (t,) in tables:
        print(f"  - {t}")
