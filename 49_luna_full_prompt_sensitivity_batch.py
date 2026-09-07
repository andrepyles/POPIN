"""Luna full: teste pareado v4 versus v4 neutral nos 900 IDs congelados.

Este driver envia apenas a condição neutral. A condição v4 já está no banco
como piloto full de 900, e o resultado novo recebe model_id/run_id próprios
para nunca sobrescrever a execução principal.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import time
import uuid
from pathlib import Path
from urllib import error, request

import duckdb


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "popin.duckdb"
DATA_DIR = ROOT / "data/gpd_v2_1_20251120"
SAMPLE_PATH = DATA_DIR / "sensitivity_test_sample.csv"
OUT_PATH = DATA_DIR / "sensitivity_runs/openai_gpt-5.6-luna__neutral_full_900.jsonl"
META_PATH = OUT_PATH.with_suffix(".meta.json")
API_BASE = "https://api.openai.com/v1"
MODEL = "gpt-5.6-luna"
MODEL_ID = "gpt-5.6-luna__neutral_full_20260906"
PROMPT_ID = "v4 neutral"
RUN_ID = "luna__prompt_sensitivity_full__neutral__sample900__20260906"
PROVIDER = "openai_direct_batch"
TERMINAL = {"completed", "failed", "cancelled", "expired"}
DIMENSIONS = [
    "people_centrism", "anti_elitism", "moral_dichotomy",
    "popular_sovereignty", "exclusionary_rhetoric", "crisis_rhetoric",
]


def load_local_env() -> None:
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        value = value.strip().strip("'\"")
        if name.strip() and value:
            os.environ.setdefault(name.strip(), value)


def load_v4_prompt() -> str:
    tree = ast.parse((ROOT / "04_score.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "SYSTEM_PROMPT"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("SYSTEM_PROMPT não encontrado")


def neutral_prompt(v4: str) -> str:
    start = v4.index("REGIONAL SCOPE")
    end = v4.index("CHUNK SAFETY")
    return v4[:start] + v4[end:]


def load_docs() -> list[dict]:
    with SAMPLE_PATH.open(encoding="utf-8", newline="") as handle:
        sample = list(csv.DictReader(handle))
    if len(sample) != 900 or len({row["discourse_id"] for row in sample}) != 900:
        raise RuntimeError("A amostra congelada não tem exatamente 900 IDs únicos")
    ids = [row["discourse_id"] for row in sample]
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        placeholders = ",".join("?" for _ in ids)
        rows = con.execute(
            f"SELECT id, iso3, leader_name, filename, discourse_date, discourse_year, word_count, dtype, discourse FROM discourses WHERE id IN ({placeholders})",
            ids,
        ).fetchall()
    finally:
        con.close()
    by_id = {str(row[0]): row for row in rows}
    docs = []
    for item in sample:
        row = by_id.get(str(item["discourse_id"]))
        if row is None:
            raise RuntimeError(f"ID da amostra ausente no DuckDB: {item['discourse_id']}")
        doc = dict(zip(("discourse_id", "iso3", "leader_name", "filename", "discourse_date", "discourse_year", "word_count", "dtype", "text"), row))
        if doc["discourse_date"] is not None:
            doc["discourse_date"] = doc["discourse_date"].isoformat()
        docs.append(doc)
    return docs


def api_json(url: str, key: str, method: str = "GET", payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    for attempt in range(8):
        req = request.Request(url, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method=method)
        try:
            with request.urlopen(req, timeout=300) as response:
                return json.load(response)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code in {429, 500, 502, 503, 504} and attempt < 7:
                delay = min(60, 5 * (2 ** attempt))
                print(json.dumps({"event": "retry", "status": exc.code, "sleep_s": delay}, ensure_ascii=False), flush=True)
                time.sleep(delay)
                continue
            raise RuntimeError(f"OpenAI HTTP {exc.code}: {detail[:1500]}") from exc


def upload(lines: bytes, key: str) -> dict:
    boundary = f"----popin-{uuid.uuid4().hex}"
    body = b"".join([
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nbatch\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"popin_luna_neutral_full_900.jsonl\"\r\nContent-Type: application/jsonl\r\n\r\n".encode(),
        lines,
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    req = request.Request(f"{API_BASE}/files", data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
    try:
        with request.urlopen(req, timeout=300) as response:
            return json.load(response)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI upload HTTP {exc.code}: {detail[:1500]}") from exc


def parse_scores(content: str | None) -> dict[str, float]:
    if not content:
        raise ValueError("resposta vazia")
    raw = content.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1].strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()
    data = json.loads(raw)
    scores = {dim: round(max(0.0, min(100.0, float(data.get(dim, 0.0)))), 2) for dim in DIMENSIONS}
    scores["final_score"] = round(sum(scores.values()) / len(DIMENSIONS), 2)
    return scores


def main() -> None:
    load_local_env()
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY não definido; nenhum batch foi enviado")
    docs = load_docs()
    prompt = neutral_prompt(load_v4_prompt())
    requests = []
    estimated_tokens = 0
    for doc in docs:
        estimated_tokens += max(512, int((len(prompt) + len(doc["text"]) + 64) / 4) + 512)
        requests.append({
            "custom_id": str(doc["discourse_id"]),
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Score this political passage:\n\n{doc['text']}"},
                ],
                "temperature": 0,
                "max_completion_tokens": 256,
                "reasoning_effort": "none",
            },
        })
    lines = ("\n".join(json.dumps(item, ensure_ascii=False) for item in requests) + "\n").encode()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    uploaded = upload(lines, key)
    file_id = uploaded.get("id")
    if not file_id:
        raise RuntimeError(f"Upload sem file_id: {uploaded}")
    batch = api_json(f"{API_BASE}/batches", key, "POST", {
        "input_file_id": file_id,
        "endpoint": "/v1/chat/completions",
        "completion_window": "24h",
        "metadata": {"project": "popin", "run_id": RUN_ID, "prompt_id": PROMPT_ID, "scope": "prompt_sensitivity"},
    })
    batch_id = batch.get("id")
    if not batch_id:
        raise RuntimeError(f"Batch sem id: {batch}")
    print(json.dumps({"event": "submitted", "batch_id": batch_id, "file_id": file_id, "requests": len(docs), "estimated_tokens": estimated_tokens, "status": batch.get("status")}, ensure_ascii=False), flush=True)
    while batch.get("status") not in TERMINAL:
        time.sleep(15)
        batch = api_json(f"{API_BASE}/batches/{batch_id}", key)
        print(json.dumps({"event": "status", "batch_id": batch_id, "status": batch.get("status"), "request_counts": batch.get("request_counts")}, ensure_ascii=False), flush=True)
    output_bytes = b""
    if batch.get("output_file_id"):
        req = request.Request(f"{API_BASE}/files/{batch['output_file_id']}/content", headers={"Authorization": f"Bearer {key}"})
        with request.urlopen(req, timeout=300) as response:
            output_bytes = response.read()
    by_id = {str(doc["discourse_id"]): doc for doc in docs}
    results = {}
    for line in output_bytes.decode("utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        custom_id = str(item.get("custom_id"))
        doc = by_id.get(custom_id)
        if not doc:
            continue
        response = item.get("response") or {}
        body = response.get("body") or response
        content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content")
        try:
            scores, parse_error = parse_scores(content), None
        except Exception as exc:
            scores, parse_error = None, f"{type(exc).__name__}: {exc}"
        results[custom_id] = {**doc, "model": MODEL, "model_id": MODEL_ID, "prompt_id": PROMPT_ID, "provider": PROVIDER, "run_id": RUN_ID, "batch_id": batch_id, "scores": scores, "raw_content": content, "usage": body.get("usage") or {}, "error": item.get("error") or parse_error, "http_status": response.get("status_code")}
    for doc in docs:
        results.setdefault(str(doc["discourse_id"]), {**doc, "model": MODEL, "model_id": MODEL_ID, "prompt_id": PROMPT_ID, "provider": PROVIDER, "run_id": RUN_ID, "batch_id": batch_id, "scores": None, "raw_content": None, "usage": {}, "error": f"Resultado ausente; status={batch.get('status')}", "http_status": None})
    OUT_PATH.write_text("\n".join(json.dumps(results[key], ensure_ascii=False) for key in sorted(results)) + "\n", encoding="utf-8")
    valid = [row for row in results.values() if row.get("scores")]
    meta = {"batch_id": batch_id, "input_file_id": file_id, "output_file_id": batch.get("output_file_id"), "status": batch.get("status"), "submitted": len(docs), "returned": len(results), "valid": len(valid), "request_counts": batch.get("request_counts"), "usage": batch.get("usage"), "estimated_tokens": estimated_tokens, "elapsed_s": round(time.time() - started, 3), "output": str(OUT_PATH), "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()}
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"event": "materialized", **meta}, ensure_ascii=False), flush=True)
    con = duckdb.connect(str(DB_PATH))
    try:
        con.execute("BEGIN")
        for row in valid:
            s = row["scores"]
            con.execute("""INSERT INTO scores (score_id,discourse_id,iso3,leader_name,filename,discourse_date,discourse_year,dtype,model,model_id,execution_id,prompt_id,provider,run_id,scope,coverage,chunked,chunk_words,overlap_words,n_chunks,valid_chunks,word_count,people_centrism,anti_elitism,moral_dichotomy,popular_sovereignty,exclusionary_rhetoric,crisis_rhetoric,final_score,status,error_text,source_kind,source_file,raw_json,scored_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT DO NOTHING""", [hashlib.md5((row["discourse_id"]+"|"+MODEL_ID+"|"+RUN_ID).encode()).hexdigest(),row["discourse_id"],row["iso3"],row["leader_name"],row["filename"],row["discourse_date"],row["discourse_year"],row["dtype"],"GPT-5.6 Luna",MODEL_ID,RUN_ID,PROMPT_ID,PROVIDER,RUN_ID,"prompt_sensitivity","pilot",False,None,0,1,1,row["word_count"],s["people_centrism"],s["anti_elitism"],s["moral_dichotomy"],s["popular_sovereignty"],s["exclusionary_rhetoric"],s["crisis_rhetoric"],s["final_score"],"ok",None,"openai_batch","openai_gpt-5.6-luna__neutral_full_900.jsonl",json.dumps(row,ensure_ascii=False),None])
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()
    print(json.dumps({"event": "db_imported", "valid": len(valid), "run_id": RUN_ID}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
