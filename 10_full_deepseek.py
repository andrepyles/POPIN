"""Pontuação retomável da base completa com DeepSeek V4 Flash + prompt v4.

Usa a classificação ``dtype`` já congelada no DuckDB, exclui somente
``INVALID`` e grava um JSONL com uma linha por discurso concluído.
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import csv
import hashlib
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DB_PATH", ROOT / "popin.duckdb"))
OUT_DIR = ROOT / "data/gpd_v2_1_20251120/full_runs"
MODEL = "deepseek/deepseek-v4-flash-0731"
PROMPT_ID = "v4"
PROVIDER = "decart"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
CHUNK_WORDS = 800
DIMENSIONS = [
    "people_centrism", "anti_elitism", "moral_dichotomy",
    "popular_sovereignty", "exclusionary_rhetoric", "crisis_rhetoric",
]


def load_v4_system_prompt() -> str:
    tree = ast.parse((ROOT / "04_score.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "SYSTEM_PROMPT"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("SYSTEM_PROMPT não encontrado em 04_score.py")


SYSTEM_PROMPT = load_v4_system_prompt()
PROMPT_SHA256 = hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()


def split_chunks(text: str) -> list[str]:
    def words_to_chunks(words: list[str]) -> list[str]:
        return [" ".join(words[i:i + CHUNK_WORDS])
                for i in range(0, len(words), CHUNK_WORDS)]

    paragraphs = [p.strip() for p in re.split(r"\n{1,}", text) if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    for paragraph in paragraphs:
        words = paragraph.split()
        if len(words) > CHUNK_WORDS:
            if current:
                chunks.append(" ".join(current))
                current, current_words = [], 0
            chunks.extend(words_to_chunks(words))
            continue
        if current_words + len(words) > CHUNK_WORDS and current:
            chunks.append(" ".join(current))
            current, current_words = [], 0
        current.extend(words)
        current_words += len(words)
    if current:
        chunks.append(" ".join(current))
    return chunks or [text]


def parse_scores(content: str | None) -> dict[str, float]:
    if not content:
        raise ValueError("resposta sem conteúdo")
    raw = content.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1].strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()
    data = json.loads(raw)
    return {
        dim: round(max(0.0, min(100.0, float(data.get(dim) or 0.0))), 2)
        for dim in DIMENSIONS
    }


def call_chunk(chunk: str, retries: int = 6) -> dict:
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Score this political passage:\n\n{chunk}"},
        ],
        "temperature": 0,
        "max_tokens": 256,
        "reasoning": {"effort": "none"},
        "provider": {
            "only": [PROVIDER],
            "allow_fallbacks": False,
        },
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://popin.local",
            "X-Title": "POPIN v4 full corpus",
        },
        method="POST",
    )
    last_error = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                payload = json.load(response)
            if payload.get("error"):
                raise RuntimeError(payload["error"])
            choice = (payload.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            return {
                "scores": parse_scores(message.get("content")),
                "usage": payload.get("usage") or {},
                "provider": payload.get("provider") or PROVIDER,
                "error": None,
            }
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError,
                json.JSONDecodeError, RuntimeError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if isinstance(exc, urllib.error.HTTPError):
                response_body = ""
                try:
                    response_body = exc.read().decode()
                    last_error = f"HTTP {exc.code}: {response_body[:500]}"
                except Exception:
                    pass
                if exc.code in (401, 402, 403):
                    break
                if exc.code == 429 and attempt < retries - 1:
                    retry_after = exc.headers.get("Retry-After")
                    try:
                        delay = float(retry_after) if retry_after else 2 ** attempt
                    except ValueError:
                        delay = 2 ** attempt
                    time.sleep(min(60.0, max(2.0, delay)))
                    continue
            if attempt < retries - 1:
                time.sleep(min(60.0, 2 ** attempt))
    return {"scores": None, "usage": {}, "provider": PROVIDER, "error": last_error}


def load_documents() -> list[dict]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        rows = con.execute("""
            SELECT id, iso3, leader_name, discourse_date, discourse, word_count,
                   dtype
            FROM discourses
            WHERE dtype <> 'INVALID'
            ORDER BY id
        """).fetchall()
    finally:
        con.close()
    return [
        {
            "discourse_id": row[0], "iso3": row[1], "leader_name": row[2],
            "discourse_date": str(row[3]) if row[3] is not None else None,
            "text": row[4], "word_count": row[5] or 0, "dtype": row[6],
        }
        for row in rows
    ]


def aggregate(results: list[dict]) -> tuple[dict | None, int, int, list[str]]:
    valid = [r for r in results if r["scores"] is not None]
    errors = [r["error"] for r in results if r["error"]]
    if not valid:
        return None, 0, 0, errors
    total_weight = sum(r["word_count"] for r in valid)
    scores = {
        dim: round(sum(r["scores"][dim] * r["word_count"] for r in valid)
                   / total_weight, 2)
        for dim in DIMENSIONS
    }
    scores["final_score"] = round(sum(scores[dim] for dim in DIMENSIONS) / 6, 2)
    return scores, len(valid), total_weight, errors


def load_done(path: Path) -> dict[str, dict]:
    done: dict[str, dict] = {}
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    done[row["discourse_id"]] = row
    return done


def run(args: argparse.Namespace) -> None:
    documents = load_documents()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUT_DIR / "deepseek_deepseek-v4-flash-0731__v4__decart.jsonl"
    done = load_done(output_path)
    pending = [d for d in documents if d["discourse_id"] not in done]
    if args.limit:
        pending = pending[:args.limit]
    spent = sum(float(row.get("cost_usd") or 0.0) for row in done.values())
    run_id = f"deepseek_deepseek-v4-flash-0731__v4__decart__{uuid.uuid4().hex[:10]}"
    print(f"Base elegível: {len(documents)}; já concluídos: {len(done)}; pendentes: {len(pending)}")
    print(f"Provedor: {PROVIDER}; paralelismo: {args.concurrency}; teto local: ${args.budget:.4f}")

    with output_path.open("a", encoding="utf-8") as output:
        for batch_start in range(0, len(pending), args.batch_size):
            batch = pending[batch_start:batch_start + args.batch_size]
            states: dict[str, dict] = {}
            futures: dict[concurrent.futures.Future, tuple[str, int]] = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
                for doc in batch:
                    chunks = split_chunks(doc["text"])
                    states[doc["discourse_id"]] = {
                        "doc": doc, "chunks": chunks, "results": [None] * len(chunks)
                    }
                    for index, chunk in enumerate(chunks):
                        futures[pool.submit(call_chunk, chunk)] = (doc["discourse_id"], index)

                stop = False
                for future in concurrent.futures.as_completed(futures):
                    discourse_id, index = futures[future]
                    state = states[discourse_id]
                    result = future.result()
                    result["word_count"] = len(state["chunks"][index].split())
                    state["results"][index] = result
                    spent += float((result.get("usage") or {}).get("cost") or 0.0)
                    if spent >= args.budget:
                        stop = True
                    if not all(r is not None for r in state["results"]):
                        continue
                    scores, valid_chunks, weighted_words, errors = aggregate(state["results"])
                    if errors:
                        raise RuntimeError(
                            f"falha em {discourse_id}: {errors}"
                        )
                    doc = state["doc"]
                    row = {
                        "run_id": run_id, "model": MODEL, "prompt_id": PROMPT_ID,
                        "prompt_sha256": PROMPT_SHA256, "provider": PROVIDER,
                        "discourse_id": doc["discourse_id"], "iso3": doc["iso3"],
                        "leader_name": doc["leader_name"],
                        "discourse_date": doc["discourse_date"],
                        "dtype": doc["dtype"], "n_chunks": len(state["chunks"]),
                        "valid_chunks": valid_chunks, "weighted_words": weighted_words,
                        "scores": scores, "errors": errors,
                        "cost_usd": round(sum(float((r.get("usage") or {}).get("cost") or 0.0)
                                              for r in state["results"]), 10),
                        "chunk_usage": [r.get("usage") or {} for r in state["results"]],
                    }
                    output.write(json.dumps(row, ensure_ascii=False) + "\n")
                    output.flush()
                    done[doc["discourse_id"]] = row
                    if len(done) % 25 == 0:
                        print(f"concluídos: {len(done)}/{len(documents)}; custo acumulado: ${spent:.4f}", flush=True)
                    if stop:
                        break
                if stop:
                    for future in futures:
                        future.cancel()
                    print(f"Teto local atingido; custo acumulado: ${spent:.4f}")
                    return
            print(f"lote concluído: {batch_start + len(batch)}/{len(pending)} pendentes nesta execução; custo: ${spent:.4f}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--budget", type=float, default=8.60)
    args = parser.parse_args()
    if not os.getenv("OPENROUTER_API_KEY"):
        raise SystemExit("OPENROUTER_API_KEY não configurada")
    run(args)


if __name__ == "__main__":
    main()
