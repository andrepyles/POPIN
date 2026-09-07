"""POPIN v4 — piloto estratificado de 1.000 discursos com GLM 4.7 Flash.

Mantém literalmente o prompt v4 e a segmentação do Qwen:
800 palavras, sem sobreposição e média ponderada pelo tamanho do chunk.
O resultado é separado e retomável; não altera a tabela scores.
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DB_PATH", ROOT / "popin.duckdb"))
OUT_DIR = ROOT / "data/gpd_v2_1_20251120/pilot_runs"
OUTPUT_PATH = OUT_DIR / "glm_4.7_flash__sample_1000__v4.jsonl"
MANIFEST_PATH = OUT_DIR / "glm_4.7_flash__sample_1000__v4.manifest.json"
MODEL = "z-ai/glm-4.7-flash"
PROMPT_ID = "v4"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
CHUNK_WORDS = 800
PENDING_LUNA_ID = "f4e8a8b087e1b114"  # HND_2017_19.txt
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


def split_chunks(text: str, max_words: int = CHUNK_WORDS) -> list[str]:
    def words_to_chunks(words: list[str]) -> list[str]:
        return [" ".join(words[i:i + max_words])
                for i in range(0, len(words), max_words)]

    paragraphs = [p.strip() for p in re.split(r"\n{1,}", text or "") if p.strip()]
    chunks, current, current_words = [], [], 0
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
        raise ValueError("resposta vazia")
    raw = content.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1].strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()
    data = json.loads(raw)
    return {
        dim: round(max(0.0, min(100.0, float(data[dim]))), 2)
        for dim in DIMENSIONS
    }


def json_schema() -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "popin_v4_scores",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {dim: {"type": "number"} for dim in DIMENSIONS},
                "required": DIMENSIONS,
                "additionalProperties": False,
            },
        },
    }


def call_chunk(chunk: str, key: str, provider: str | None, retries: int = 6) -> dict:
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": load_prompt()},
            {"role": "user", "content": f"Score this political passage:\n\n{chunk}"},
        ],
        "temperature": 0,
        "max_tokens": 128,
        "reasoning": {"effort": "none"},
        "response_format": json_schema(),
        "provider": {"allow_fallbacks": False},
    }
    if provider:
        body["provider"]["only"] = [provider]
    encoded = json.dumps(body).encode("utf-8")
    last_error = None
    for attempt in range(retries):
        req = urllib.request.Request(
            API_URL,
            data=encoded,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://popin.local",
                "X-Title": "POPIN v4 GLM pilot",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                payload = json.load(response)
            if payload.get("error"):
                raise RuntimeError(payload["error"])
            choice = (payload.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            return {
                "scores": parse_scores(message.get("content")),
                "usage": payload.get("usage") or {},
                "provider": payload.get("provider") or provider,
                "error": None,
            }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 402, 403):
                break
            if isinstance(exc, urllib.error.HTTPError) and exc.code == 429:
                retry_after = exc.headers.get("Retry-After")
                try:
                    delay = float(retry_after) if retry_after else min(60, 10 * (2 ** attempt))
                except (TypeError, ValueError):
                    delay = min(60, 10 * (2 ** attempt))
                time.sleep(delay)
                continue
            if attempt < retries - 1:
                time.sleep(min(30, 2 ** attempt))
    return {"scores": None, "usage": {}, "provider": provider, "error": last_error}


def size_bucket(word_count: int) -> str:
    if word_count <= 800:
        return "01_short"
    if word_count <= 2_000:
        return "02_medium"
    if word_count <= 5_000:
        return "03_long"
    return "04_xlong"


def stable_key(row: dict) -> str:
    return hashlib.sha256(row["id"].encode("utf-8")).hexdigest()


def select_documents(con: duckdb.DuckDBPyConnection, sample_size: int) -> list[dict]:
    columns = "id, iso3, leader_name, filename, discourse_date, discourse_year, word_count, dtype, discourse"
    raw = con.execute(
        f"SELECT {columns} FROM discourses WHERE coalesce(dtype, '') <> 'INVALID'"
    ).fetchall()
    names = ["id", "iso3", "leader_name", "filename", "discourse_date",
             "discourse_year", "word_count", "dtype", "text"]
    rows = [dict(zip(names, row)) for row in raw]
    forced = next((row for row in rows if row["id"] == PENDING_LUNA_ID), None)
    if forced is None:
        raise RuntimeError(f"discurso pendente do Luna ausente: {PENDING_LUNA_ID}")
    candidates = [row for row in rows if row["id"] != PENDING_LUNA_ID]
    # Reserve one deterministic observation per country before proportional
    # allocation, so small countries are not silently omitted.
    country_representatives = []
    reserved_ids = set()
    for iso3 in sorted({row["iso3"] for row in candidates}):
        representative = min(
            (row for row in candidates if row["iso3"] == iso3),
            key=stable_key,
        )
        country_representatives.append(representative)
        reserved_ids.add(representative["id"])
    candidates = [row for row in candidates if row["id"] not in reserved_ids]
    target = sample_size - 1 - len(country_representatives)
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in candidates:
        key = f"{row['iso3']}|{row['dtype']}|{size_bucket(int(row['word_count'] or 0))}"
        groups[key].append(row)
    total = len(candidates)
    quotas = {}
    remainders = []
    allocated = 0
    for key, group in groups.items():
        exact = target * len(group) / total
        quota = min(len(group), int(exact))
        quotas[key] = quota
        allocated += quota
        remainders.append((exact - quota, key))
    for _, key in sorted(remainders, reverse=True):
        if allocated >= target:
            break
        if quotas[key] < len(groups[key]):
            quotas[key] += 1
            allocated += 1
    selected = [forced, *country_representatives]
    for key, group in groups.items():
        selected.extend(sorted(group, key=stable_key)[:quotas[key]])
    if len(selected) != sample_size:
        raise RuntimeError(f"amostra produzida com tamanho inesperado: {len(selected)}")
    return selected


def aggregate(results: list[dict]) -> dict:
    valid = [r for r in results if r.get("scores") is not None]
    if not valid:
        return {"scores": None, "valid_chunks": 0, "errors": [r.get("error") for r in results]}
    weights = [r["word_count"] for r in valid]
    scores = {
        dim: round(sum(w * r["scores"][dim] for w, r in zip(weights, valid)) / sum(weights), 2)
        for dim in DIMENSIONS
    }
    scores["final_score"] = round(sum(scores[dim] for dim in DIMENSIONS) / 6, 2)
    return {
        "scores": scores,
        "valid_chunks": len(valid),
        "errors": [r.get("error") for r in results if r.get("error")],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=32)
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--provider", default=os.getenv("GLM_PROVIDER", "deepinfra"))
    args = parser.parse_args()
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY não configurada")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        documents = select_documents(con, args.sample_size)
    finally:
        con.close()
    manifest = {
        "model": MODEL,
        "prompt_id": PROMPT_ID,
        "chunk_words": CHUNK_WORDS,
        "sample_size": len(documents),
        "selection": "proportional stratified by iso3, dtype and length bucket; forced Luna-pending discourse",
        "forced_discourse_id": PENDING_LUNA_ID,
        "forced_filename": "HND_2017_19.txt",
        "provider": args.provider,
        "discourse_ids": [row["id"] for row in documents],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    done = {}
    if OUTPUT_PATH.exists():
        for line in OUTPUT_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if not row.get("errors"):
                    done[row["discourse_id"]] = row
    pending = [row for row in documents if row["id"] not in done]
    print(json.dumps({"sample": len(documents), "already_done": len(done), "pending": len(pending), "provider": args.provider}, ensure_ascii=False), flush=True)
    semaphore = concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency)
    futures = {}
    try:
        prompt = load_prompt()
        # A single prompt string is shared in the request body; loading it once
        # here also makes the run's prompt condition explicit.
        for doc in pending:
            chunks = split_chunks(doc["text"])
            for idx, chunk in enumerate(chunks):
                future = semaphore.submit(call_chunk, chunk, key, args.provider)
                futures[future] = (doc, chunks, idx)
        states = defaultdict(list)
        for future in concurrent.futures.as_completed(futures):
            doc, chunks, idx = futures[future]
            result = future.result()
            result["word_count"] = len(chunks[idx].split())
            states[doc["id"]].append((idx, result))
            if len(states[doc["id"]]) != len(chunks):
                continue
            ordered = [result for _, result in sorted(states[doc["id"]])]
            agg = aggregate(ordered)
            if agg["errors"]:
                print(json.dumps({
                    "retry_needed": doc["id"],
                    "filename": doc["filename"],
                    "errors": agg["errors"],
                }, ensure_ascii=False), flush=True)
                continue
            row = {
                "model": MODEL,
                "prompt_id": PROMPT_ID,
                "provider": args.provider,
                "discourse_id": doc["id"],
                "iso3": doc["iso3"],
                "leader_name": doc["leader_name"],
                "filename": doc["filename"],
                "discourse_date": str(doc["discourse_date"]),
                "discourse_year": doc["discourse_year"],
                "word_count": doc["word_count"],
                "n_chunks": len(chunks),
                "valid_chunks": agg["valid_chunks"],
                "scores": agg["scores"],
                "errors": agg["errors"],
                "chunk_usage": [r.get("usage") or {} for r in ordered],
            }
            with OUTPUT_PATH.open("a", encoding="utf-8") as output:
                output.write(json.dumps(row, ensure_ascii=False) + "\n")
            done[doc["id"]] = row
            if len(done) % 25 == 0 or len(done) == len(documents):
                cost = sum(float(u.get("cost") or 0.0) for u in row["chunk_usage"])
                print(json.dumps({"completed": len(done), "total": len(documents), "last": doc["filename"], "last_cost": round(cost, 6)}, ensure_ascii=False), flush=True)
    finally:
        semaphore.shutdown(wait=True)
    # Compacta a saída após uma retomada: remove linhas antigas que continham
    # 429 e mantém apenas uma linha válida por discurso.
    ordered_rows = [done[row["id"]] for row in documents if row["id"] in done]
    OUTPUT_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in ordered_rows),
        encoding="utf-8",
    )
    if len(done) != len(documents):
        print(f"incomplete rows={len(done)} pending={len(documents) - len(done)}", flush=True)
        return
    print(f"saved={OUTPUT_PATH} rows={len(done)}", flush=True)


if __name__ == "__main__":
    main()
