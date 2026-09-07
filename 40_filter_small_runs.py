#!/usr/bin/env python3
"""Remove execuções com menos de 900 linhas e normaliza chunk_words."""

from pathlib import Path
import duckdb


DB = Path(__file__).resolve().parent / "popin.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB))
    try:
        con.execute("BEGIN TRANSACTION")
        small_runs = [r[0] for r in con.execute("""
            SELECT execution_id
            FROM scores
            GROUP BY execution_id
            HAVING count(*) < 900
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
            SET chunk_words = CASE WHEN chunked THEN 800 ELSE 0 END
        """)
        con.execute("""
            UPDATE runs
            SET chunk_words = CASE WHEN chunked THEN 800 ELSE 0 END
        """)
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        print('removed_runs:', small_runs)
        print('scores:', con.sql("select count(*), count(distinct execution_id), count(*) filter (where chunk_words is null) from scores").fetchone())
        print('runs:')
        for row in con.sql("""
            SELECT model, prompt_id, chunked, chunk_words, scope, count(*) AS n
            FROM scores
            GROUP BY ALL
            ORDER BY model, prompt_id, scope
        """).fetchall():
            print(row)
        con.close()


if __name__ == '__main__':
    main()
