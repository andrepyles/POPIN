"""POPIN v4 — teste operacional do Luna com 64 chamadas em uma rodada.

Executa uma chamada por um discurso representativo de cada um dos 64
líderes–mandato do teste GPD bloqueado. Não há retries: o objetivo é observar
diretamente se a conta/provedor ainda devolve 429 sob paralelismo alto.
"""

from __future__ import annotations

import ast
import concurrent.futures
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
OUT_PATH = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna__64_parallel__v4.jsonl"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
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

    # Um discurso por líder–mandato: exatamente 64 unidades independentes.
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


def call_once(doc: dict, prompt: str, key: str) -> dict:
    started = time.perf_counter()
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Score this political passage:\n\n{doc['text']}"},
        ],
        "temperature": 0,
        "max_tokens": 256,
        "reasoning": {"effort": "none"},
        "provider": {"allow_fallbacks": True},
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://popin.local",
            "X-Title": "POPIN v4 Luna 64 parallel test",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.load(response)
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        message = ((payload.get("choices") or [{}])[0].get("message") or {})
        content = message.get("content")
        try:
            scores = parse_scores(content)
            final_score = round(sum(scores.values()) / len(DIMENSIONS), 2)
            scores["final_score"] = final_score
            parse_error = None
        except Exception as exc:
            scores = None
            parse_error = f"{type(exc).__name__}: {exc}"
        return {
            **{key: doc[key] for key in ("discourse_id", "iso3", "leader_name", "gpd_term_key", "gpd_totalaverage")},
            "model": MODEL,
            "scores": scores,
            "raw_content": content,
            "usage": payload.get("usage") or {},
            "error": parse_error,
            "http_status": 200,
            "latency_s": round(time.perf_counter() - started, 3),
        }
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        return {
            **{key: doc[key] for key in ("discourse_id", "iso3", "leader_name", "gpd_term_key", "gpd_totalaverage")},
            "model": MODEL,
            "scores": None,
            "raw_content": None,
            "usage": {},
            "error": f"HTTP {exc.code}: {detail}",
            "http_status": exc.code,
            "latency_s": round(time.perf_counter() - started, 3),
        }
    except Exception as exc:
        return {
            **{key: doc[key] for key in ("discourse_id", "iso3", "leader_name", "gpd_term_key", "gpd_totalaverage")},
            "model": MODEL,
            "scores": None,
            "raw_content": None,
            "usage": {},
            "error": f"{type(exc).__name__}: {exc}",
            "http_status": None,
            "latency_s": round(time.perf_counter() - started, 3),
        }


def main() -> None:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY não definido")
    docs = load_representative_docs()
    prompt = load_v4_prompt()
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as pool:
        futures = [pool.submit(call_once, doc, prompt, key) for doc in docs]
        results = [future.result() for future in futures]
    elapsed = round(time.perf_counter() - started, 3)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
    status = {}
    for result in results:
        code = str(result["http_status"] or "local_error")
        status[code] = status.get(code, 0) + 1
    valid = sum(result["scores"] is not None for result in results)
    cost = sum(float((result["usage"] or {}).get("cost") or 0) for result in results)
    print(json.dumps({
        "output": str(OUT_PATH),
        "requests": len(results),
        "valid": valid,
        "status": status,
        "cost_usd": round(cost, 6),
        "elapsed_s": elapsed,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
