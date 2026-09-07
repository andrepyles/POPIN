#!/usr/bin/env python3
"""Achata a estrutura do POPIN para uma tabela principal simples.

Depois da migração, ``scores`` passa a ser a fonte de consulta: uma linha por
discurso e execução, incluindo os testes históricos. ``runs`` guarda apenas o
catálogo curto das execuções. As tabelas ``raw_*`` continuam intactas.
"""

from pathlib import Path
import duckdb


ROOT = Path(__file__).resolve().parent
DB = ROOT / "popin.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB))
    try:
        con.execute("BEGIN TRANSACTION")

        for view in (
            "v_all_scores_navigable",
            "v_history_run_summary",
            "v_history_navigable",
            "v_scores_wide",
            "v_score_runs",
            "v_scores_navigable",
            "v_model_summary",
        ):
            con.execute(f"DROP VIEW IF EXISTS {view}")

        con.execute("DROP TABLE IF EXISTS scores_flat")
        con.execute("""
            CREATE TABLE scores_flat (
                score_id VARCHAR PRIMARY KEY,
                discourse_id VARCHAR NOT NULL,
                iso3 VARCHAR,
                leader_name VARCHAR,
                filename VARCHAR,
                discourse_date DATE,
                discourse_year INTEGER,
                dtype VARCHAR,
                model VARCHAR,
                model_id VARCHAR,
                execution_id VARCHAR NOT NULL,
                prompt_id VARCHAR,
                provider VARCHAR,
                run_id VARCHAR,
                scope VARCHAR,
                coverage VARCHAR,
                chunked BOOLEAN,
                chunk_words INTEGER,
                overlap_words INTEGER,
                n_chunks INTEGER,
                valid_chunks INTEGER,
                word_count INTEGER,
                people_centrism FLOAT,
                anti_elitism FLOAT,
                moral_dichotomy FLOAT,
                popular_sovereignty FLOAT,
                exclusionary_rhetoric FLOAT,
                crisis_rhetoric FLOAT,
                final_score FLOAT,
                status VARCHAR,
                error_text VARCHAR,
                source_kind VARCHAR,
                source_file VARCHAR,
                raw_json VARCHAR,
                scored_at TIMESTAMP
            )
        """)

        con.execute("""
            INSERT INTO scores_flat
            SELECT
                'main::' || coalesce(mc.execution_id, 'main_' || s.model_id) || '::' || s.discourse_id,
                s.discourse_id, d.iso3, d.leader_name, d.filename,
                d.discourse_date, d.discourse_year, d.dtype,
                coalesce(mc.model_label, s.model_id), s.model_id,
                coalesce(mc.execution_id, 'main_' || s.model_id),
                s.prompt_id, s.provider, s.run_id,
                coalesce(mc.run_scope, 'main'), mc.coverage,
                coalesce(mc.chunked, s.n_chunks > 1), mc.chunk_words,
                mc.overlap_words, s.n_chunks, NULL::INTEGER, d.word_count,
                s.people_centrism, s.anti_elitism, s.moral_dichotomy,
                s.popular_sovereignty, s.exclusionary_rhetoric,
                s.crisis_rhetoric, s.final_score,
                CASE WHEN s.final_score IS NULL THEN 'error' ELSE 'ok' END,
                NULL::VARCHAR, 'main', NULL::VARCHAR, s.raw_json, s.scored_at
            FROM scores s
            LEFT JOIN discourses d ON d.id = s.discourse_id
            LEFT JOIN model_catalog mc
              ON mc.model_id = s.model_id
             AND mc.prompt_id IS NOT DISTINCT FROM s.prompt_id
             AND mc.provider IS NOT DISTINCT FROM s.provider
             AND mc.run_id IS NOT DISTINCT FROM s.run_id
        """)

        con.execute("""
            INSERT INTO scores_flat
            SELECT
                'history::' || h.history_id,
                h.discourse_id, coalesce(d.iso3, h.iso3),
                coalesce(d.leader_name, h.leader_name), d.filename,
                coalesce(d.discourse_date, try_cast(h.discourse_date AS DATE)),
                coalesce(d.discourse_year, h.discourse_year), d.dtype,
                h.model_label, h.model_id, h.execution_id,
                h.prompt_id, h.provider, h.run_id,
                'historical', r.coverage, h.chunked,
                CASE WHEN h.chunked THEN 800 ELSE NULL END,
                0, h.n_chunks, h.valid_chunks,
                coalesce(h.word_count, d.word_count),
                h.people_centrism, h.anti_elitism, h.moral_dichotomy,
                h.popular_sovereignty, h.exclusionary_rhetoric,
                h.crisis_rhetoric, h.final_score,
                CASE WHEN h.has_error OR h.final_score IS NULL THEN 'error' ELSE 'ok' END,
                h.error_text, h.source_kind, h.source_file, h.raw_json,
                h.imported_at
            FROM score_history h
            LEFT JOIN score_history_runs r ON r.execution_id = h.execution_id
            LEFT JOIN discourses d ON d.id = h.discourse_id
        """)

        con.execute("DROP TABLE scores")
        con.execute("ALTER TABLE scores_flat RENAME TO scores")
        con.execute("CREATE INDEX scores_discourse_idx ON scores (discourse_id)")
        con.execute("CREATE INDEX scores_model_idx ON scores (model_id)")
        con.execute("CREATE INDEX scores_leader_idx ON scores (iso3, leader_name)")

        con.execute("DROP TABLE IF EXISTS runs")
        con.execute("""
            CREATE TABLE runs (
                run_id VARCHAR PRIMARY KEY,
                execution_id VARCHAR NOT NULL,
                model VARCHAR,
                model_id VARCHAR,
                prompt_id VARCHAR,
                provider VARCHAR,
                scope VARCHAR,
                coverage VARCHAR,
                chunked BOOLEAN,
                chunk_words INTEGER,
                n_rows INTEGER,
                n_scored INTEGER,
                source_kind VARCHAR,
                source_file VARCHAR,
                notes VARCHAR
            )
        """)
        con.execute("""
            INSERT INTO runs
            SELECT
                coalesce(mc.run_id, mc.execution_id), mc.execution_id,
                mc.model_label, mc.model_id, mc.prompt_id, mc.provider,
                mc.run_scope, mc.coverage, mc.chunked, mc.chunk_words,
                mc.source_n,
                (SELECT count(*) FROM scores s WHERE s.execution_id = mc.execution_id),
                'main', NULL, NULL
            FROM model_catalog mc
        """)
        con.execute("""
            INSERT INTO runs
            SELECT
                r.execution_id, r.execution_id, r.model_label, r.model_id,
                r.prompt_id, r.provider, r.source_kind, r.coverage, r.chunked,
                CASE WHEN r.chunked THEN 800 ELSE NULL END,
                r.source_rows, r.rows_with_scores, r.source_kind, r.source_file,
                r.notes
            FROM score_history_runs r
        """)

        con.execute("DROP TABLE model_catalog")
        con.execute("DROP TABLE score_history_manifest")
        con.execute("DROP TABLE score_history_runs")
        con.execute("DROP TABLE score_history")

        con.execute("COMMENT ON TABLE scores IS 'Fonte principal: uma linha por discurso e execucao; inclui scores principais e historicos.'")
        con.execute("COMMENT ON TABLE runs IS 'Catalogo simples das execucoes presentes em scores.'")
        con.execute("COMMENT ON COLUMN scores.final_score IS 'Score POPIN final, escala 0-100.'")
        con.execute("COMMENT ON COLUMN scores.scope IS 'full, pilot ou historical.'")
        con.execute("COMMENT ON COLUMN scores.chunked IS 'Se o texto foi avaliado em chunks.'")
        con.execute("COMMENT ON COLUMN scores.status IS 'ok ou error.'")

        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        print('tables:', con.sql("select table_name from information_schema.tables where table_schema='main' order by 1").fetchall())
        print('scores:', con.sql("select count(*), count(distinct discourse_id), count(distinct execution_id), sum(status='ok') from scores").fetchone())
        print('runs:', con.sql("select count(*) from runs").fetchone())
        print('by_model:', con.sql("select model, prompt_id, chunked, scope, count(*) from scores group by all order by 1,2,3,4").fetchall())
        con.close()


if __name__ == '__main__':
    main()
