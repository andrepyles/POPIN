"""Probe curto para confirmar Luna via OpenRouter BYOK/OpenAI."""

from __future__ import annotations

import ast
import csv
import json
import os
import time
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "popin.duckdb"
SAMPLE_PATH = ROOT / "data/gpd_v2_1_20251120/sensitivity_test_sample.csv"
OUT_PATH = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna__8_byok_batch_probe__v4.jsonl"
META_PATH = OUT_PATH.with_suffix(".meta.json")
BATCH_URL = "https://openrouter.ai/api/beta/batches"
MODEL = "openai/gpt-5.6-luna"
N = 8
DIMENSIONS = [
    "people_centrism", "anti_elitism", "moral_dichotomy",
    "popular_sovereignty", "exclusionary_rhetoric", "crisis_rhetoric",
]


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


def request_json(url: str, key: str, method: str = "GET", payload: dict | None = None) -> dict:
    import urllib.request
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


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
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY não definido")
    docs = load_docs()
    prompt = load_prompt()
    payload = {
        "endpoint": "/v1/chat/completions",
        "model": MODEL,
        "requests": [{
            "custom_id": str(doc["discourse_id"]),
            "body": {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Score this political passage:\n\n{doc['text']}"},
                ],
                "temperature": 0,
                "max_tokens": 256,
                "reasoning": {"effort": "none"},
                "provider": {"allow_fallbacks": False, "only": ["openai"]},
            },
        } for doc in docs],
    }
    started = time.time()
    created = request_json(BATCH_URL, key, "POST", payload)
    batch_id = created.get("id")
    if not batch_id:
        raise SystemExit(json.dumps(created, ensure_ascii=False))
    print(json.dumps({"batch_id": batch_id, "status": created.get("status"), "requests": len(docs)}, ensure_ascii=False), flush=True)
    batch = created
    while batch.get("status") not in {"completed", "failed", "cancelled", "expired"}:
        time.sleep(10)
        batch = request_json(f"{BATCH_URL}/{batch_id}", key)
        print(json.dumps({"batch_id": batch_id, "status": batch.get("status")}, ensure_ascii=False), flush=True)

    by_id = {str(doc["discourse_id"]): doc for doc in docs}
    results = []
    for item in batch.get("results") or []:
        doc = by_id.get(str(item.get("custom_id")))
        if not doc:
            continue
        response = item.get("response") or {}
        body = response.get("body") or response
        content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content")
        try:
            scores, error = parse_scores(content), None
        except Exception as exc:
            scores, error = None, f"{type(exc).__name__}: {exc}"
        results.append({
            **{key: doc[key] for key in ("discourse_id", "iso3", "leader_name", "gpd_term_key", "gpd_totalaverage")},
            "model": MODEL,
            "batch_id": batch_id,
            "scores": scores,
            "raw_content": content,
            "usage": body.get("usage") or {},
            "error": item.get("error") or error,
            "http_status": response.get("status_code"),
        })
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in results), encoding="utf-8")
    meta = {
        "batch_id": batch_id,
        "status": batch.get("status"),
        "submitted": len(docs),
        "returned": len(batch.get("results") or []),
        "valid": sum(item["scores"] is not None for item in results),
        "usage": batch.get("usage"),
        "elapsed_s": round(time.time() - started, 3),
        "error": batch.get("error"),
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUT_PATH), "metadata": str(META_PATH), **meta}, ensure_ascii=False))


if __name__ == "__main__":
    main()
