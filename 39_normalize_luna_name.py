#!/usr/bin/env python3
"""Padroniza o nome legível do GPT-5.6 Luna no DuckDB."""

from pathlib import Path
import duckdb


DB = Path(__file__).resolve().parent / "popin.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB))
    try:
        con.execute("BEGIN TRANSACTION")
        con.execute("""
            UPDATE scores
            SET model = 'GPT-5.6 Luna'
            WHERE lower(model) = 'gpt-5.6-luna'
        """)
        con.execute("""
            UPDATE runs
            SET model = 'GPT-5.6 Luna'
            WHERE lower(model) = 'gpt-5.6-luna'
        """)
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        print(con.sql("""
            SELECT model, model_id, count(*) AS n
            FROM scores
            WHERE lower(model) LIKE '%luna%'
            GROUP BY ALL
            ORDER BY model, model_id
        """).fetchall())
        con.close()


if __name__ == '__main__':
    main()
