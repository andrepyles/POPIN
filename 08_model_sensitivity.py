"""POPIN v4 — comparação de modelos e sensibilidade ao prompt.

Executa a amostra congelada contra modelos compatíveis com a API OpenRouter,
mantendo a segmentação e o esquema de saída do v4. Cada configuração produz
um JSONL retomável com uma linha por discurso.

Exemplo:
    OPENROUTER_API_KEY=... python 08_model_sensitivity.py \
        --models deepseek/deepseek-v4-flash-0731 openai/gpt-5.6-luna \
        --prompts v4 neutral --concurrency 8
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
SAMPLE_PATH = ROOT / "data/gpd_v2_1_20251120/sensitivity_test_sample.csv"
OUT_DIR = ROOT / "data/gpd_v2_1_20251120/sensitivity_runs"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
CHUNK_WORDS = 800
DIMENSIONS = [
    "people_centrism", "anti_elitism", "moral_dichotomy",
    "popular_sovereignty", "exclusionary_rhetoric", "crisis_rhetoric",
]


def load_v4_system_prompt() -> str:
    """Lê o prompt v4 sem importar 04_score.py e suas dependências locais."""
    tree = ast.parse((ROOT / "04_score.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "SYSTEM_PROMPT"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("SYSTEM_PROMPT não encontrado em 04_score.py")


V4_PROMPT = load_v4_system_prompt()


def prompt_for(prompt_id: str) -> str:
    if prompt_id == "v4":
        return V4_PROMPT
    if prompt_id == "neutral":
        start = V4_PROMPT.index("REGIONAL SCOPE")
        end = V4_PROMPT.index("CHUNK SAFETY")
        return V4_PROMPT[:start] + V4_PROMPT[end:]
    raise ValueError(f"Prompt desconhecido: {prompt_id}")


def split_chunks(text: str, max_words: int = CHUNK_WORDS) -> list[str]:
    """Mesma segmentação contígua, sem overlap, usada pelo v4."""
    def words_to_chunks(words: list[str]) -> list[str]:
        return [" ".join(words[i:i + max_words])
                for i in range(0, len(words), max_words)]

    paragraphs = [p.strip() for p in re.split(r"\n{1,}", text) if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    for paragraph in paragraphs:
        words = paragraph.split()
        if len(words) > max_words:
            if current:
                chunks.append(" ".join(current))
                current, current_words = [], 0
            chunks.extend(words_to_chunks(words))
            continue
        if current_words + len(words) > max_words and current:
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
    scores = {}
    for dimension in DIMENSIONS:
        value = data.get(dimension)
        if value is None:
            scores[dimension] = 0.0
        else:
            scores[dimension] = round(max(0.0, min(100.0, float(value))), 2)
    return scores


def call_chunk(model: str, system_prompt: str, chunk: str, retries: int = 6) -> dict:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Score this political passage:\n\n{chunk}"},
        ],
        "temperature": 0,
        "max_tokens": 256,
        "reasoning": {"effort": "none"},
        "provider": {"allow_fallbacks": False},
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://popin.local",
            "X-Title": "POPIN v4 model sensitivity",
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
                "provider": payload.get("provider"),
                "finish_reason": choice.get("finish_reason"),
                "error": None,
            }
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError,
                json.JSONDecodeError, RuntimeError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if isinstance(exc, urllib.error.HTTPError):
                body = ""
                try:
                    body = exc.read().decode()
                    last_error = f"HTTP {exc.code}: {body[:500]}"
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
                time.sleep(2 ** attempt)
    return {"scores": None, "usage": {}, "provider": None,
            "finish_reason": None, "error": last_error}


def load_documents() -> list[dict]:
    with SAMPLE_PATH.open(encoding="utf-8-sig", newline="") as handle:
        sample = list(csv.DictReader(handle))
    if not sample:
        raise RuntimeError("amostra congelada vazia")
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        ids = [row["discourse_id"] for row in sample]
        placeholders = ",".join("?" for _ in ids)
        records = con.execute(
            f"SELECT id, discourse FROM discourses WHERE id IN ({placeholders})", ids
        ).fetchall()
    finally:
        con.close()
    text_by_id = {record[0]: record[1] for record in records}
    documents = []
    for row in sample:
        if row["discourse_id"] not in text_by_id:
            raise RuntimeError(f"discurso ausente no banco: {row['discourse_id']}")
        documents.append({**row, "text": text_by_id[row["discourse_id"]]})
    return documents


def aggregate(results: list[dict]) -> tuple[dict | None, int, float, list[str]]:
    valid = [result for result in results if result["scores"] is not None]
    errors = [result["error"] for result in results if result["error"]]
    if not valid:
        return None, 0, 0.0, errors
    weights = [result["word_count"] for result in valid]
    total_weight = sum(weights)
    scores = {
        dim: round(sum(result["scores"][dim] * result["word_count"]
                       for result in valid) / total_weight, 2)
        for dim in DIMENSIONS
    }
    scores["final_score"] = round(sum(scores[dim] for dim in DIMENSIONS) / 6, 2)
    return scores, len(valid), total_weight, errors


def run_configuration(model: str, prompt_id: str, documents: list[dict],
                      concurrency: int, budget_remaining: float) -> float:
    prompt = prompt_for(prompt_id)
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    model_slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", model)
    output_path = OUT_DIR / f"{model_slug}__{prompt_id}.jsonl"
    done = {}
    if output_path.exists():
        with output_path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    done[row["discourse_id"]] = row
    pending = [doc for doc in documents if doc["discourse_id"] not in done]
    run_id = f"{model_slug}__{prompt_id}__{uuid.uuid4().hex[:10]}"
    spent = sum((row.get("cost_usd") or 0.0) for row in done.values())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mode = "a" if output_path.exists() else "w"
    with output_path.open(mode, encoding="utf-8") as output:
        states = {}
        futures = {}
        for doc in pending:
            chunks = split_chunks(doc["text"])
            states[doc["discourse_id"]] = {
                "doc": doc, "chunks": chunks, "results": [None] * len(chunks)
            }
        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
            for discourse_id, state in states.items():
                for index, chunk in enumerate(state["chunks"]):
                    futures[pool.submit(call_chunk, model, prompt, chunk)] = (
                        discourse_id, index
                    )
            for future in concurrent.futures.as_completed(futures):
                discourse_id, index = futures[future]
                state = states[discourse_id]
                chunk_result = future.result()
                chunk_result["word_count"] = len(state["chunks"][index].split())
                state["results"][index] = chunk_result
                spent += float((chunk_result.get("usage") or {}).get("cost") or 0.0)
                if spent >= budget_remaining:
                    raise RuntimeError(
                        f"orçamento atingido durante {model}/{prompt_id}: ${spent:.4f}"
                    )
                if not all(result is not None for result in state["results"]):
                    continue
                doc = state["doc"]
                chunks = state["chunks"]
                chunk_results = state["results"]
                scores, valid_chunks, weighted_words, errors = aggregate(chunk_results)
                if errors:
                    raise RuntimeError(
                        f"falha ao pontuar {doc['discourse_id']} em {model}/{prompt_id}: {errors}"
                    )
                output_row = {
                    "run_id": run_id,
                    "model": model,
                    "prompt_id": prompt_id,
                    "prompt_sha256": prompt_hash,
                    "discourse_id": doc["discourse_id"],
                    "iso3": doc["iso3"],
                    "leader_name": doc["leader_name"],
                    "discourse_date": doc["discourse_date"],
                    "gpd_split": doc["gpd_split"],
                    "baseline_final_score": float(doc["baseline_final_score"]),
                    "n_chunks": len(chunks),
                    "valid_chunks": valid_chunks,
                    "weighted_words": weighted_words,
                    "scores": scores,
                    "errors": errors,
                    "cost_usd": round(sum(float((r.get("usage") or {}).get("cost") or 0.0)
                                          for r in chunk_results), 10),
                    "chunk_usage": [r.get("usage") or {} for r in chunk_results],
                }
                output.write(json.dumps(output_row, ensure_ascii=False) + "\n")
                output.flush()
                completed += 1
                if completed % 25 == 0 or completed == len(pending):
                    print(f"{model} / {prompt_id}: {completed}/{len(pending)}; custo acumulado ${spent:.4f}", flush=True)
    return spent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=[
        "deepseek/deepseek-v4-flash-0731"
    ])
    parser.add_argument("--prompts", nargs="+", default=["v4", "neutral"])
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--budget", type=float, default=8.0)
    args = parser.parse_args()
    if not os.getenv("OPENROUTER_API_KEY"):
        raise SystemExit("OPENROUTER_API_KEY não configurada")
    documents = load_documents()
    if args.limit:
        documents = documents[:args.limit]
    spent = 0.0
    for model in args.models:
        for prompt_id in args.prompts:
            remaining = args.budget - spent
            if remaining <= 0:
                raise SystemExit(f"orçamento esgotado: ${spent:.4f}")
            spent += run_configuration(model, prompt_id, documents, args.concurrency, remaining)
    print(f"Concluído. Custo aproximado registrado: ${spent:.4f}")


if __name__ == "__main__":
    main()
