#!/usr/bin/env python3
"""Limpa pilotos minúsculos e padroniza as condições de prompt no DuckDB."""

from pathlib import Path
import duckdb


ROOT = Path(__file__).resolve().parent
DB = ROOT / "popin.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB))
    try:
        con.execute("BEGIN TRANSACTION")

        small_runs = [r[0] for r in con.execute("""
            SELECT execution_id
            FROM scores
            GROUP BY execution_id
            HAVING count(*) <= 10
        """).fetchall()]

        if small_runs:
            con.execute(
                "DELETE FROM scores WHERE execution_id IN (SELECT * FROM UNNEST(?))",
                [small_runs],
            )
            con.execute(
                "DELETE FROM runs WHERE execution_id IN (SELECT * FROM UNNEST(?))",
                [small_runs],
            )

        con.execute("""
            UPDATE scores
            SET prompt_id = CASE
                WHEN prompt_id = 'neutral' THEN 'v4 neutral'
                WHEN prompt_id = 'anchored' THEN 'v4 anchored'
                WHEN prompt_id IS NULL THEN 'v4'
                ELSE prompt_id
            END
        """)
        con.execute("""
            UPDATE runs
            SET prompt_id = CASE
                WHEN prompt_id = 'neutral' THEN 'v4 neutral'
                WHEN prompt_id = 'anchored' THEN 'v4 anchored'
                WHEN prompt_id IS NULL THEN 'v4'
                ELSE prompt_id
            END
        """)
        con.execute("""
            UPDATE scores AS s
            SET scope = r.scope
            FROM runs AS r
            WHERE s.execution_id = r.execution_id
              AND r.scope IS NOT NULL
        """)

        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        print('removed_small_runs:', len(small_runs))
        print('scores:', con.sql('select count(*), count(distinct execution_id) from scores').fetchone())
        print('prompts:')
        for row in con.sql("select model, prompt_id, scope, count(*) from scores group by all order by 1,2,3").fetchall():
            print(row)
        con.close()


if __name__ == '__main__':
    main()
