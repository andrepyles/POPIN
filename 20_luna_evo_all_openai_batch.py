"""Pontua todos os textos não-INVALID de Evo Morales via Batch API da OpenAI."""

from __future__ import annotations

import ast
import argparse
import json
import os
import time
import uuid
from pathlib import Path
from urllib import error, request

import duckdb


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "popin.duckdb"
SEED_PATH = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna__8_openai_batch_probe__v4.jsonl"
OUT_PATH = ROOT / "data/gpd_v2_1_20251120/full_runs/luna__evo_morales__openai__v4.jsonl"
META_PATH = OUT_PATH.with_suffix(".meta.json")
API_BASE = "https://api.openai.com/v1"
MODEL = "gpt-5.6-luna"
DIMENSIONS = [
    "people_centrism", "anti_elitism", "moral_dichotomy",
    "popular_sovereignty", "exclusionary_rhetoric", "crisis_rhetoric",
]
TERMINAL = {"completed", "failed", "cancelled", "expired"}


def load_local_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        value = value.strip().strip("'\"")
        if name.strip() and value:
            os.environ.setdefault(name.strip(), value)


def load_prompt() -> str:
    tree = ast.parse((ROOT / "04_score.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "SYSTEM_PROMPT"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("SYSTEM_PROMPT não encontrado")


def load_docs() -> list[dict]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        rows = con.execute(
            """
            SELECT id, iso3, leader_name, filename, discourse_date,
                   discourse_year, word_count, dtype, discourse
            FROM discourses
            WHERE lower(leader_name) LIKE '%evo morales%'
              AND dtype <> 'INVALID'
            ORDER BY discourse_date, id
            """
        ).fetchall()
    finally:
        con.close()
    keys = [
        "discourse_id", "iso3", "leader_name", "filename", "discourse_date",
        "discourse_year", "word_count", "dtype", "text",
    ]
    docs = []
    for row in rows:
        doc = dict(zip(keys, row))
        if doc["discourse_date"] is not None:
            doc["discourse_date"] = doc["discourse_date"].isoformat()
        docs.append(doc)
    return docs


def load_seed() -> dict[str, dict]:
    if not SEED_PATH.exists():
        return {}
    result = {}
    for line in SEED_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("scores"):
            result[str(row["discourse_id"])] = row
    return result


def api_json(url: str, key: str, method: str = "GET", payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    req = request.Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with request.urlopen(req, timeout=180) as response:
            return json.load(response)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI HTTP {exc.code}: {detail[:1000]}") from exc


def upload_jsonl(lines: bytes, key: str) -> dict:
    boundary = f"----codex-{uuid.uuid4().hex}"
    parts = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nbatch\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"luna_evo_morales_v4.jsonl\"\r\nContent-Type: application/jsonl\r\n\r\n".encode(),
        lines,
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    req = request.Request(
        f"{API_BASE}/files",
        data=b"".join(parts),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=180) as response:
            return json.load(response)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI upload HTTP {exc.code}: {detail[:1000]}") from exc


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


def make_request(doc: dict, prompt: str) -> dict:
    return {
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
    }


def parse_output(output_bytes: bytes, docs_by_id: dict[str, dict], batch_id: str) -> dict[str, dict]:
    result = {}
    for line in output_bytes.decode("utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        custom_id = str(item.get("custom_id"))
        doc = docs_by_id.get(custom_id)
        if not doc:
            continue
        response = item.get("response") or {}
        body = response.get("body") or response
        content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content")
        try:
            scores, parse_error = parse_scores(content), None
        except Exception as exc:
            scores, parse_error = None, f"{type(exc).__name__}: {exc}"
        result[custom_id] = {
            **{key: doc[key] for key in ("discourse_id", "iso3", "leader_name", "filename", "discourse_date", "discourse_year", "word_count", "dtype")},
            "model": MODEL,
            "prompt_id": "v4",
            "provider": "openai_direct_batch",
            "batch_id": batch_id,
            "scores": scores,
            "raw_content": content,
            "usage": body.get("usage") or {},
            "error": item.get("error") or parse_error,
            "http_status": response.get("status_code"),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recover-batch", help="recupera um batch já concluído sem reenviar requisições")
    args = parser.parse_args()
    load_local_env()
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY não definido; nenhum batch foi enviado")
    docs = load_docs()
    docs_by_id = {str(doc["discourse_id"]): doc for doc in docs}
    seed = {}
    for seed_id, row in load_seed().items():
        if seed_id not in docs_by_id:
            continue
        doc = docs_by_id[seed_id]
        for field in ("iso3", "leader_name", "filename", "discourse_date", "discourse_year", "word_count", "dtype"):
            row.setdefault(field, doc[field])
        row.setdefault("prompt_id", "v4")
        row.setdefault("provider", "openai_direct_batch")
        seed[seed_id] = row
    pending = [doc for doc in docs if str(doc["discourse_id"]) not in seed]

    if args.recover_batch:
        batch_id = args.recover_batch
        batch = api_json(f"{API_BASE}/batches/{batch_id}", key)
        if batch.get("status") not in TERMINAL:
            raise RuntimeError(f"Batch ainda não está terminal: {batch.get('status')}")
        new_rows = {}
        if batch.get("output_file_id"):
            req = request.Request(
                f"{API_BASE}/files/{batch['output_file_id']}/content",
                headers={"Authorization": f"Bearer {key}"},
            )
            with request.urlopen(req, timeout=180) as response:
                new_rows = parse_output(response.read(), docs_by_id, batch_id)
        combined = {**seed, **new_rows}
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text("".join(json.dumps(combined[str(doc["discourse_id"])], ensure_ascii=False) + "\n" for doc in docs if str(doc["discourse_id"]) in combined), encoding="utf-8")
        meta = {
            "batch_id": batch_id,
            "input_file_id": batch.get("input_file_id"),
            "output_file_id": batch.get("output_file_id"),
            "status": batch.get("status"),
            "total_docs": len(docs),
            "seeded": len(seed),
            "submitted": (batch.get("request_counts") or {}).get("total"),
            "returned_new": len(new_rows),
            "combined_written": len(combined),
            "valid_combined": sum(row.get("scores") is not None for row in combined.values()),
            "request_counts": batch.get("request_counts"),
            "usage": batch.get("usage"),
            "error": batch.get("errors"),
        }
        META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"output": str(OUT_PATH), "metadata": str(META_PATH), **meta}, ensure_ascii=False))
        return

    prompt = load_prompt()
    lines = [json.dumps(make_request(doc, prompt), ensure_ascii=False) for doc in pending]
    jsonl = ("\n".join(lines) + "\n").encode("utf-8") if lines else b""
    print(json.dumps({
        "total_docs": len(docs), "seeded": len(seed), "pending": len(pending),
        "word_count": sum(int(doc["word_count"] or 0) for doc in docs),
        "estimated_input_tokens_chars_div_4": round(len(jsonl) / 4),
    }, ensure_ascii=False), flush=True)
    if not pending:
        combined = seed
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text("".join(json.dumps(combined[str(doc["discourse_id"])], ensure_ascii=False) + "\n" for doc in docs), encoding="utf-8")
        print(json.dumps({"status": "already_complete", "output": str(OUT_PATH)}, ensure_ascii=False))
        return

    started = time.time()
    uploaded = upload_jsonl(jsonl, key)
    file_id = uploaded.get("id")
    if not file_id:
        raise RuntimeError(json.dumps(uploaded, ensure_ascii=False))
    batch = api_json(f"{API_BASE}/batches", key, "POST", {
        "input_file_id": file_id,
        "endpoint": "/v1/chat/completions",
        "completion_window": "24h",
        "metadata": {"project": "popin", "probe": "evo_morales_all_v4"},
    })
    batch_id = batch.get("id")
    if not batch_id:
        raise RuntimeError(json.dumps(batch, ensure_ascii=False))
    print(json.dumps({"batch_id": batch_id, "file_id": file_id, "status": batch.get("status"), "requests": len(pending)}, ensure_ascii=False), flush=True)
    while batch.get("status") not in TERMINAL:
        time.sleep(10)
        batch = api_json(f"{API_BASE}/batches/{batch_id}", key)
        print(json.dumps({"batch_id": batch_id, "status": batch.get("status"), "request_counts": batch.get("request_counts")}, ensure_ascii=False), flush=True)

    new_rows = {}
    if batch.get("output_file_id"):
        req = request.Request(
            f"{API_BASE}/files/{batch['output_file_id']}/content",
            headers={"Authorization": f"Bearer {key}"},
        )
        with request.urlopen(req, timeout=180) as response:
            new_rows = parse_output(response.read(), docs_by_id, batch_id)
    combined = {**seed, **new_rows}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("".join(json.dumps(combined[str(doc["discourse_id"])], ensure_ascii=False) + "\n" for doc in docs if str(doc["discourse_id"]) in combined), encoding="utf-8")
    meta = {
        "batch_id": batch_id,
        "file_id": file_id,
        "output_file_id": batch.get("output_file_id"),
        "status": batch.get("status"),
        "total_docs": len(docs),
        "seeded": len(seed),
        "submitted": len(pending),
        "returned_new": len(new_rows),
        "combined_written": len(combined),
        "valid_combined": sum(row.get("scores") is not None for row in combined.values()),
        "request_counts": batch.get("request_counts"),
        "usage": batch.get("usage"),
        "elapsed_s": round(time.time() - started, 3),
        "error": batch.get("errors"),
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUT_PATH), "metadata": str(META_PATH), **meta}, ensure_ascii=False))


if __name__ == "__main__":
    main()
