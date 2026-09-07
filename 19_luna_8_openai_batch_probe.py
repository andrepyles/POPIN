"""Piloto curto do Luna via Batch API oficial da OpenAI."""

from __future__ import annotations

import ast
import csv
import json
import os
import time
import uuid
from pathlib import Path
from urllib import error, request

import duckdb


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "popin.duckdb"
SAMPLE_PATH = ROOT / "data/gpd_v2_1_20251120/sensitivity_test_sample.csv"
OUT_PATH = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna__8_openai_batch_probe__v4.jsonl"
META_PATH = OUT_PATH.with_suffix(".meta.json")
API_BASE = "https://api.openai.com/v1"
MODEL = "gpt-5.6-luna"
N = 8
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
        name = name.strip()
        value = value.strip().strip("'\"")
        if name and value:
            os.environ.setdefault(name, value)


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
    rows = []
    with SAMPLE_PATH.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("gpd_split") == "test_locked":
                rows.append(row)
    selected = {}
    for row in sorted(rows, key=lambda item: (item["gpd_term_key"], item["discourse_id"])):
        selected.setdefault(row["gpd_term_key"], row)
    selected = list(selected.values())[:N]
    ids = [row["discourse_id"] for row in selected]
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        result = con.execute(
            f"SELECT id, discourse FROM discourses WHERE id IN ({','.join('?' for _ in ids)})", ids
        ).fetchall()
    finally:
        con.close()
    texts = dict(result)
    return [{**{key: row[key] for key in ("discourse_id", "iso3", "leader_name", "gpd_term_key", "gpd_totalaverage")}, "text": texts[row["discourse_id"]]} for row in selected]


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
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"luna_8_openai_probe.jsonl\"\r\nContent-Type: application/jsonl\r\n\r\n".encode(),
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


def main() -> None:
    load_local_env()
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY não definido; nenhum batch foi enviado")
    docs = load_docs()
    prompt = load_prompt()
    lines = []
    for doc in docs:
        lines.append(json.dumps({
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
        }, ensure_ascii=False))
    jsonl = ("\n".join(lines) + "\n").encode("utf-8")
    started = time.time()
    uploaded = upload_jsonl(jsonl, key)
    file_id = uploaded.get("id")
    if not file_id:
        raise RuntimeError(json.dumps(uploaded, ensure_ascii=False))
    batch = api_json(f"{API_BASE}/batches", key, "POST", {
        "input_file_id": file_id,
        "endpoint": "/v1/chat/completions",
        "completion_window": "24h",
        "metadata": {"project": "popin", "probe": "luna_8_openai_v4"},
    })
    batch_id = batch.get("id")
    if not batch_id:
        raise RuntimeError(json.dumps(batch, ensure_ascii=False))
    print(json.dumps({"batch_id": batch_id, "file_id": file_id, "status": batch.get("status"), "requests": len(docs)}, ensure_ascii=False), flush=True)
    while batch.get("status") not in TERMINAL:
        time.sleep(10)
        batch = api_json(f"{API_BASE}/batches/{batch_id}", key)
        print(json.dumps({"batch_id": batch_id, "status": batch.get("status"), "request_counts": batch.get("request_counts")}, ensure_ascii=False), flush=True)

    output_lines = b""
    if batch.get("output_file_id"):
        req = request.Request(
            f"{API_BASE}/files/{batch['output_file_id']}/content",
            headers={"Authorization": f"Bearer {key}"},
        )
        with request.urlopen(req, timeout=180) as response:
            output_lines = response.read()
    by_id = {str(doc["discourse_id"]): doc for doc in docs}
    results = []
    for line in output_lines.decode("utf-8").splitlines():
        item = json.loads(line)
        doc = by_id.get(str(item.get("custom_id")))
        if not doc:
            continue
        response = item.get("response") or {}
        body = response.get("body") or response
        content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content")
        try:
            scores, parse_error = parse_scores(content), None
        except Exception as exc:
            scores, parse_error = None, f"{type(exc).__name__}: {exc}"
        results.append({
            **{key: doc[key] for key in ("discourse_id", "iso3", "leader_name", "gpd_term_key", "gpd_totalaverage")},
            "model": MODEL,
            "batch_id": batch_id,
            "scores": scores,
            "raw_content": content,
            "usage": body.get("usage") or {},
            "error": item.get("error") or parse_error,
            "http_status": response.get("status_code"),
        })
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in results), encoding="utf-8")
    meta = {
        "batch_id": batch_id,
        "file_id": file_id,
        "output_file_id": batch.get("output_file_id"),
        "status": batch.get("status"),
        "submitted": len(docs),
        "returned": len(results),
        "valid": sum(item["scores"] is not None for item in results),
        "request_counts": batch.get("request_counts"),
        "usage": batch.get("usage"),
        "elapsed_s": round(time.time() - started, 3),
        "error": batch.get("errors"),
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUT_PATH), "metadata": str(META_PATH), **meta}, ensure_ascii=False))


if __name__ == "__main__":
    main()
