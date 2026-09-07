"""POPIN v4 — piloto do Batch API do Luna com as mesmas 64 unidades do teste paralelo.

O teste envia uma única submissão assíncrona ao Batch API da OpenRouter. Ele não
faz 64 chamadas HTTP concorrentes; a OpenRouter processa e devolve os resultados
posteriormente. O prompt, o recorte e os parâmetros seguem o teste anterior.
"""

from __future__ import annotations

import ast
import csv
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "popin.duckdb"
SAMPLE_PATH = ROOT / "data/gpd_v2_1_20251120/sensitivity_test_sample.csv"
OUT_PATH = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna__64_batch__v4.jsonl"
META_PATH = OUT_PATH.with_suffix(".meta.json")
BATCH_URL = "https://openrouter.ai/api/beta/batches"
MODEL = "openai/gpt-5.6-luna"
DIMENSIONS = [
    "people_centrism", "anti_elitism", "moral_dichotomy",
    "popular_sovereignty", "exclusionary_rhetoric", "crisis_rhetoric",
]


def load_v4_prompt() -> str:
    tree = ast.parse((ROOT / "04_score.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "SYSTEM_PROMPT"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("SYSTEM_PROMPT não encontrado")


def load_representative_docs() -> list[dict]:
    rows = []
    with SAMPLE_PATH.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("gpd_split") == "test_locked":
                rows.append(row)

    selected = {}
    for row in sorted(rows, key=lambda item: (item["gpd_term_key"], item["discourse_id"])):
        selected.setdefault(row["gpd_term_key"], row)
    selected = list(selected.values())
    if len(selected) != 64:
        raise RuntimeError(f"Esperados 64 líder–mandato; encontrados {len(selected)}")

    ids = [row["discourse_id"] for row in selected]
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        placeholders = ",".join("?" for _ in ids)
        result = con.execute(
            f"SELECT id, discourse FROM discourses WHERE id IN ({placeholders})", ids
        ).fetchall()
    finally:
        con.close()
    texts = {row[0]: row[1] for row in result}
    missing = [item for item in ids if item not in texts]
    if missing:
        raise RuntimeError(f"Discursos ausentes no DuckDB: {missing[:5]}")
    return [
        {
            "discourse_id": row["discourse_id"],
            "iso3": row["iso3"],
            "leader_name": row["leader_name"],
            "gpd_term_key": row["gpd_term_key"],
            "gpd_totalaverage": row["gpd_totalaverage"],
            "text": texts[row["discourse_id"]],
        }
        for row in selected
    ]


def parse_scores(content: str | None) -> dict[str, float]:
    if not content:
        raise ValueError("resposta vazia")
    raw = content.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1].strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()
    data = json.loads(raw)
    return {
        dim: round(max(0.0, min(100.0, float(data.get(dim, 0.0)))), 2)
        for dim in DIMENSIONS
    }


def post_json(url: str, key: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://popin.local",
            "X-Title": "POPIN v4 Luna 64 batch pilot",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def get_json(url: str, key: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def extract_response(item: dict) -> tuple[int | None, dict, str | None]:
    response = item.get("response") or {}
    if isinstance(response, dict) and "body" in response:
        status = response.get("status_code")
        body = response.get("body") or {}
    else:
        status = response.get("status_code") if isinstance(response, dict) else None
        body = response if isinstance(response, dict) else {}
    error = item.get("error")
    if body.get("error") and not error:
        error = body["error"]
    return status, body, json.dumps(error, ensure_ascii=False) if error else None


def main() -> None:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY não definido")

    docs = load_representative_docs()
    prompt = load_v4_prompt()
    requests = []
    for doc in docs:
        requests.append({
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
                "provider": {"allow_fallbacks": True},
            },
        })

    submitted_at = time.time()
    try:
        created = post_json(BATCH_URL, key, {
            "endpoint": "/v1/chat/completions",
            "model": MODEL,
            "requests": requests,
        })
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise SystemExit(f"Batch submission HTTP {exc.code}: {detail}") from exc

    batch_id = created.get("id")
    if not batch_id:
        raise SystemExit(f"Resposta sem batch id: {json.dumps(created, ensure_ascii=False)[:2000]}")

    print(json.dumps({"batch_id": batch_id, "status": created.get("status"), "requests": len(requests)}, ensure_ascii=False), flush=True)
    status_url = f"{BATCH_URL}/{batch_id}"
    batch = created
    while batch.get("status") not in {"completed", "failed", "cancelled", "expired"}:
        time.sleep(10)
        batch = get_json(status_url, key)
        print(json.dumps({
            "batch_id": batch_id,
            "status": batch.get("status"),
            "completed": batch.get("completed"),
            "failed": batch.get("failed"),
        }, ensure_ascii=False), flush=True)

    by_id = {str(doc["discourse_id"]): doc for doc in docs}
    results = []
    for item in batch.get("results") or []:
        custom_id = str(item.get("custom_id"))
        doc = by_id.get(custom_id)
        if not doc:
            continue
        http_status, body, error = extract_response(item)
        content = None
        if body:
            content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content")
        try:
            scores = parse_scores(content)
            scores["final_score"] = round(sum(scores.values()) / len(DIMENSIONS), 2)
            parse_error = None
        except Exception as exc:
            scores = None
            parse_error = f"{type(exc).__name__}: {exc}"
        results.append({
            **{key: doc[key] for key in ("discourse_id", "iso3", "leader_name", "gpd_term_key", "gpd_totalaverage")},
            "model": MODEL,
            "batch_id": batch_id,
            "scores": scores,
            "raw_content": content,
            "usage": body.get("usage") or {},
            "error": error or parse_error,
            "http_status": http_status,
        })

    seen = {str(item.get("custom_id")) for item in batch.get("results") or []}
    for doc in docs:
        if str(doc["discourse_id"]) not in seen:
            results.append({
                **{key: doc[key] for key in ("discourse_id", "iso3", "leader_name", "gpd_term_key", "gpd_totalaverage")},
                "model": MODEL,
                "batch_id": batch_id,
                "scores": None,
                "raw_content": None,
                "usage": {},
                "error": f"Resultado ausente no Batch; status={batch.get('status')}",
                "http_status": None,
            })

    results.sort(key=lambda item: str(item["discourse_id"]))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")

    elapsed = round(time.time() - submitted_at, 3)
    valid = sum(item["scores"] is not None for item in results)
    cost = sum(float((item["usage"] or {}).get("cost") or 0) for item in results)
    meta = {
        "batch_id": batch_id,
        "status": batch.get("status"),
        "submitted_requests": len(requests),
        "returned_results": len(batch.get("results") or []),
        "written_results": len(results),
        "valid": valid,
        "elapsed_s": elapsed,
        "cost_usd": round(cost, 6),
        "batch_response": batch,
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(OUT_PATH),
        "metadata": str(META_PATH),
        "batch_id": batch_id,
        "status": batch.get("status"),
        "submitted_requests": len(requests),
        "returned_results": len(batch.get("results") or []),
        "valid": valid,
        "cost_usd": round(cost, 6),
        "elapsed_s": elapsed,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
