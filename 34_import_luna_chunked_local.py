#!/usr/bin/env python3
"""Importa o resultado agregado do Luna chunked no DuckDB local."""

import json
from pathlib import Path

import duckdb


ROOT = Path("/run/media/andre/5E12373112370E11/OneDrive/04 - Faculdade/02 - Mestrado/03 - Dissertação/02 - Código/popin")
DB = ROOT / "popin.duckdb"
INPUT = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna_chunked_sample1000_results/luna_chunked_sample1000_v4.jsonl"
MODEL = "gpt-5.6-luna__chunked_sample1000"
DIMS = ["people_centrism", "anti_elitism", "moral_dichotomy", "popular_sovereignty", "exclusionary_rhetoric", "crisis_rhetoric"]


def main() -> None:
    rows = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1000
    assert all(row.get("scores") for row in rows)
    con = duckdb.connect(str(DB))
    values = []
    for row in rows:
        scores = row["scores"]
        values.append((row["discourse_id"], MODEL, *[scores[dim] for dim in DIMS], scores["final_score"], row["n_chunks"], json.dumps(row, ensure_ascii=False), "v4", "openai_batch_chunked", "luna_chunked_sample1000_v4"))
    con.executemany("""
        INSERT INTO scores (discourse_id,model_id,people_centrism,anti_elitism,moral_dichotomy,popular_sovereignty,exclusionary_rhetoric,crisis_rhetoric,final_score,n_chunks,raw_json,prompt_id,provider,run_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT (discourse_id,model_id) DO UPDATE SET
          people_centrism=excluded.people_centrism,anti_elitism=excluded.anti_elitism,moral_dichotomy=excluded.moral_dichotomy,
          popular_sovereignty=excluded.popular_sovereignty,exclusionary_rhetoric=excluded.exclusionary_rhetoric,crisis_rhetoric=excluded.crisis_rhetoric,
          final_score=excluded.final_score,n_chunks=excluded.n_chunks,raw_json=excluded.raw_json,prompt_id=excluded.prompt_id,provider=excluded.provider,run_id=excluded.run_id,scored_at=now()
    """, values)
    con.commit()
    print(con.execute("select model_id,count(*) from scores where model_id=? group by 1", [MODEL]).fetchall())
    con.close()


if __name__ == "__main__":
    main()
