#!/usr/bin/env python3
"""Importa o piloto GLM já concluído no DuckDB local do POPIN."""

import json
from pathlib import Path

import duckdb


ROOT = Path("/run/media/andre/5E12373112370E11/OneDrive/04 - Faculdade/02 - Mestrado/03 - Dissertação/02 - Código/popin")
DB = ROOT / "popin.duckdb"
JSONL = ROOT / "data/gpd_v2_1_20251120/pilot_runs/glm_4.7_flash__sample_1000__v4.jsonl"
MODEL = "z-ai/glm-4.7-flash"
RUN_ID = "glm_4.7_flash__sample_1000__v4"
DIMS = ["people_centrism", "anti_elitism", "moral_dichotomy", "popular_sovereignty", "exclusionary_rhetoric", "crisis_rhetoric"]


def main() -> None:
    rows = []
    with JSONL.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("errors") or row.get("scores", {}).get("final_score") is None:
                continue
            rows.append(row)
    assert len(rows) == 1000
    assert len({r["discourse_id"] for r in rows}) == 1000

    con = duckdb.connect(str(DB))
    sql = """
        INSERT INTO scores (
            discourse_id, model_id, people_centrism, anti_elitism, moral_dichotomy,
            popular_sovereignty, exclusionary_rhetoric, crisis_rhetoric, final_score,
            n_chunks, raw_json, prompt_id, provider, run_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (discourse_id, model_id) DO UPDATE SET
            people_centrism=excluded.people_centrism,
            anti_elitism=excluded.anti_elitism,
            moral_dichotomy=excluded.moral_dichotomy,
            popular_sovereignty=excluded.popular_sovereignty,
            exclusionary_rhetoric=excluded.exclusionary_rhetoric,
            crisis_rhetoric=excluded.crisis_rhetoric,
            final_score=excluded.final_score,
            n_chunks=excluded.n_chunks,
            raw_json=excluded.raw_json,
            prompt_id=excluded.prompt_id,
            provider=excluded.provider,
            run_id=excluded.run_id,
            scored_at=now()
    """
    values = []
    for row in rows:
        scores = row["scores"]
        values.append((
            row["discourse_id"], MODEL,
            *[scores.get(dim) for dim in DIMS], scores["final_score"],
            row.get("n_chunks"), json.dumps(row, ensure_ascii=False),
            "v4", row.get("provider", "deepinfra"), RUN_ID,
        ))
    con.executemany(sql, values)
    con.commit()
    print(con.execute("select model_id,count(*) from scores where model_id=? group by 1", [MODEL]).fetchall())
    print(con.execute("select count(*) from scores where model_id in (?, ?, ?, ?)", [
        "Qwen/Qwen3-30B-A3B-Instruct-2507", "deepseek/deepseek-v4-flash-0731", "gpt-5.6-luna", MODEL
    ]).fetchone())
    con.close()


if __name__ == "__main__":
    main()
