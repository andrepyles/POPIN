"""Importa os 900 scores Luna da amostra congelada no DuckDB."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "popin.duckdb"
JSONL_PATH = ROOT / (
    "data/gpd_v2_1_20251120/full_runs/"
    "luna__sample_900__openai__v4.jsonl"
)
MODEL_ID = "gpt-5.6-luna"


def main() -> None:
    rows = []
    seen = set()
    with JSONL_PATH.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            discourse_id = row["discourse_id"]
            if discourse_id in seen:
                raise ValueError(f"discurso duplicado no JSONL: {discourse_id}")
            seen.add(discourse_id)
            score = row.get("scores") or {}
            if not score:
                raise ValueError(f"linha {line_number} sem scores")
            rows.append((
                discourse_id,
                MODEL_ID,
                score.get("people_centrism"),
                score.get("anti_elitism"),
                score.get("moral_dichotomy"),
                score.get("popular_sovereignty"),
                score.get("exclusionary_rhetoric"),
                score.get("crisis_rhetoric"),
                score.get("final_score"),
                row.get("n_chunks", 1),
                json.dumps(row, ensure_ascii=False),
                row.get("prompt_id", "v4"),
                row.get("provider", "openai_direct_batch"),
                "luna__sample_900__openai__v4",
            ))

    if len(rows) != 900:
        raise ValueError(f"esperadas 900 linhas; encontradas {len(rows)}")

    con = duckdb.connect(str(DB_PATH))
    try:
        con.execute("BEGIN TRANSACTION")
        columns = {r[1] for r in con.execute("pragma table_info(scores)").fetchall()}
        for column in ("prompt_id", "provider", "run_id"):
            if column not in columns:
                con.execute(f"ALTER TABLE scores ADD COLUMN {column} VARCHAR")

        ids = [row[0] for row in rows]
        placeholders = ",".join("?" for _ in ids)
        found = con.execute(
            f"SELECT id FROM discourses WHERE id IN ({placeholders})", ids
        ).fetchall()
        missing = set(ids) - {r[0] for r in found}
        if missing:
            raise ValueError(f"discursos ausentes no DuckDB: {len(missing)}")

        con.executemany("""
            INSERT INTO scores (
                discourse_id, model_id, people_centrism, anti_elitism,
                moral_dichotomy, popular_sovereignty, exclusionary_rhetoric,
                crisis_rhetoric, final_score, n_chunks, raw_json,
                prompt_id, provider, run_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (discourse_id, model_id) DO UPDATE SET
                people_centrism = excluded.people_centrism,
                anti_elitism = excluded.anti_elitism,
                moral_dichotomy = excluded.moral_dichotomy,
                popular_sovereignty = excluded.popular_sovereignty,
                exclusionary_rhetoric = excluded.exclusionary_rhetoric,
                crisis_rhetoric = excluded.crisis_rhetoric,
                final_score = excluded.final_score,
                n_chunks = excluded.n_chunks,
                raw_json = excluded.raw_json,
                prompt_id = excluded.prompt_id,
                provider = excluded.provider,
                run_id = excluded.run_id,
                scored_at = now()
        """, rows)
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()

    print(f"Importados/atualizados: {len(rows)} scores")
    print(f"model_id: {MODEL_ID}; prompt_id: v4; provider: openai_direct_batch")


if __name__ == "__main__":
    main()
