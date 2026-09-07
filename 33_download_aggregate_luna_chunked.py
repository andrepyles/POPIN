#!/usr/bin/env python3
"""Baixa outputs dos batches Luna, agrega chunks e importa no DuckDB remoto."""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

import duckdb


ROOT = Path("/root/popin-run")
DB = ROOT / "popin.duckdb"
BATCH_DIR = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna_chunked_sample1000_batches_1p5m"
INPUT = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna_chunked_sample1000_input.jsonl"
RESULT_DIR = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna_chunked_sample1000_results"
MODEL_ID = "gpt-5.6-luna__chunked_sample1000"
DIMS = ["people_centrism", "anti_elitism", "moral_dichotomy", "popular_sovereignty", "exclusionary_rhetoric", "crisis_rhetoric"]


def api_get(url: str) -> bytes:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY ausente")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=180) as response:
        return response.read()


def parse_json_content(content: str) -> dict:
    raw = (content or "").strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1].strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()
    data = json.loads(raw)
    return {dim: round(max(0.0, min(100.0, float(data.get(dim, 0.0)))), 2) for dim in DIMS}


def load_metadata() -> dict[str, dict]:
    out = {}
    for path in sorted(BATCH_DIR.glob("batch_*.meta.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload["rows"]:
            out[row["custom_id"]] = row
    return out


def download_outputs() -> list[dict]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    statuses = []
    for submitted in sorted(BATCH_DIR.glob("batch_*.submitted.json")):
        shard = submitted.name.split(".")[0]
        record = json.loads(submitted.read_text(encoding="utf-8"))
        batch = record.get("batch", {})
        batch_id = batch.get("id")
        if batch.get("status") != "completed" or not batch.get("output_file_id"):
            # Refresh status in case the local manifest predates completion.
            live = json.loads(api_get(f"https://api.openai.com/v1/batches/{batch_id}"))
            batch = live
        if batch.get("status") != "completed" or not batch.get("output_file_id"):
            raise RuntimeError(f"Batch incompleto: {batch_id} status={batch.get('status')}")
        target = RESULT_DIR / f"{shard}.output.jsonl"
        if not target.exists() or target.stat().st_size == 0:
            target.write_bytes(api_get(f"https://api.openai.com/v1/files/{batch['output_file_id']}/content"))
        statuses.append({"shard": shard, "batch_id": batch_id, "status": batch.get("status"), "request_counts": batch.get("request_counts"), "usage": batch.get("usage"), "output_file_id": batch.get("output_file_id")})
    (RESULT_DIR / "batch_status.json").write_text(json.dumps(statuses, ensure_ascii=False, indent=2), encoding="utf-8")
    return statuses


def aggregate() -> dict:
    metadata = load_metadata()
    docs = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    groups = {}
    output_lines = 0
    for path in sorted(RESULT_DIR.glob("batch_*.output.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            output_lines += 1
            item = json.loads(line)
            custom_id = item.get("custom_id")
            meta = metadata.get(custom_id)
            if not meta:
                raise RuntimeError(f"custom_id sem metadata: {custom_id}")
            did = meta["discourse_id"]
            group = groups.setdefault(did, {"meta": meta, "chunks": {}, "errors": []})
            response = item.get("response") or {}
            if item.get("error") or response.get("status_code") != 200:
                group["errors"].append({"custom_id": custom_id, "error": item.get("error") or response})
                continue
            body = (response.get("body") or {})
            choices = body.get("choices") or []
            content = ((choices[0].get("message") or {}).get("content") if choices else None)
            try:
                scores = parse_json_content(content)
                usage = body.get("usage") or {}
                group["chunks"][meta["chunk_idx"]] = {"scores": scores, "usage": usage, "chunk_words": meta["chunk_words"]}
            except Exception as exc:
                group["errors"].append({"custom_id": custom_id, "error": f"parse_error: {type(exc).__name__}: {exc}"})

    rows = []
    total_valid_chunks = 0
    total_errors = 0
    for doc in docs:
        did = doc["discourse_id"]
        group = groups.get(did)
        if not group:
            raise RuntimeError(f"Discurso sem output: {did}")
        chunks = group["chunks"]
        valid = [chunks[i] for i in sorted(chunks)]
        errors = group["errors"]
        total_valid_chunks += len(valid)
        total_errors += len(errors)
        if valid:
            weights = [x["chunk_words"] for x in valid]
            scores = {dim: round(sum(w * x["scores"][dim] for w, x in zip(weights, valid)) / sum(weights), 2) for dim in DIMS}
            scores["final_score"] = round(sum(scores.values()) / len(DIMS), 2)
        else:
            scores = None
        rows.append({
            "discourse_id": did,
            "iso3": doc.get("iso3"),
            "leader_name": doc.get("leader_name"),
            "filename": doc.get("filename"),
            "discourse_date": doc.get("discourse_date"),
            "discourse_year": doc.get("discourse_year"),
            "dtype": doc.get("dtype"),
            "word_count": doc.get("word_count"),
            "model": "gpt-5.6-luna",
            "prompt_id": "v4",
            "provider": "openai_batch_chunked",
            "run_id": "luna_chunked_sample1000_v4",
            "chunk_words": 800,
            "n_chunks": group["meta"]["n_chunks"],
            "n_valid_chunks": len(valid),
            "scores": scores,
            "chunk_scores": [chunks[i]["scores"] if i in chunks else None for i in range(group["meta"]["n_chunks"])],
            "chunk_usage": [chunks[i]["usage"] if i in chunks else None for i in range(group["meta"]["n_chunks"])],
            "errors": errors,
        })
    out = RESULT_DIR / "luna_chunked_sample1000_v4.jsonl"
    out.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    summary = {"documents": len(rows), "output_lines": output_lines, "chunks": sum(r["n_chunks"] for r in rows), "valid_chunks": total_valid_chunks, "errors": total_errors, "invalid_documents": sum(r["scores"] is None for r in rows), "output": str(out)}
    (RESULT_DIR / "aggregation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def import_db(rows_path: Path) -> None:
    con = duckdb.connect(str(DB))
    rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    values = []
    for row in rows:
        s = row["scores"]
        if not s:
            continue
        values.append((row["discourse_id"], MODEL_ID, *[s.get(dim) for dim in DIMS], s["final_score"], row["n_chunks"], json.dumps(row, ensure_ascii=False), "v4", "openai_batch_chunked", "luna_chunked_sample1000_v4"))
    con.executemany("""
        INSERT INTO scores (discourse_id,model_id,people_centrism,anti_elitism,moral_dichotomy,popular_sovereignty,exclusionary_rhetoric,crisis_rhetoric,final_score,n_chunks,raw_json,prompt_id,provider,run_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT (discourse_id,model_id) DO UPDATE SET
          people_centrism=excluded.people_centrism,anti_elitism=excluded.anti_elitism,moral_dichotomy=excluded.moral_dichotomy,
          popular_sovereignty=excluded.popular_sovereignty,exclusionary_rhetoric=excluded.exclusionary_rhetoric,crisis_rhetoric=excluded.crisis_rhetoric,
          final_score=excluded.final_score,n_chunks=excluded.n_chunks,raw_json=excluded.raw_json,prompt_id=excluded.prompt_id,provider=excluded.provider,run_id=excluded.run_id,scored_at=now()
    """, values)
    con.commit()
    print(json.dumps({"db_model": MODEL_ID, "rows": con.execute("select count(*) from scores where model_id=?", [MODEL_ID]).fetchone()[0]}, ensure_ascii=False))
    con.close()


def main() -> None:
    statuses = download_outputs()
    summary = aggregate()
    import_db(RESULT_DIR / "luna_chunked_sample1000_v4.jsonl")
    print(json.dumps({"batches": len(statuses), "summary": summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
