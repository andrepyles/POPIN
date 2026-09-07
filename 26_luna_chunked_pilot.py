"""Piloto Luna v4 com a mesma lógica de chunking do Qwen original.

Usa o prompt v4 de 04_score.py, chunks contíguos de 800 palavras sem
sobreposição, uma chamada por chunk e média ponderada pelo tamanho do chunk.
O resultado é salvo em JSONL separado e não altera a tabela scores.
"""

from __future__ import annotations

import ast
import asyncio
import json
import os
import re
import time
from urllib import error, request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INPUT_PATH = ROOT / os.getenv(
    "LUNA_CHUNKED_INPUT",
    "data/gpd_v2_1_20251120/pilot_runs/luna_chunked_pilot10_input.jsonl",
)
OUTPUT_PATH = ROOT / os.getenv(
    "LUNA_CHUNKED_OUTPUT",
    "data/gpd_v2_1_20251120/pilot_runs/luna_chunked_pilot10_v4.jsonl",
)
MODEL = "gpt-5.6-luna"
CHUNK_WORDS = 800
CONCURRENCY = 16
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
    """Cópia da função split_chunks do 04_score.py."""
    def words_to_chunks(word_list: list[str]) -> list[str]:
        return [
            " ".join(word_list[i:i + max_words])
            for i in range(0, len(word_list), max_words)
        ]

    paragraphs = [p.strip() for p in re.split(r"\n{1,}", text) if p.strip()]
    chunks, current, current_words = [], [], 0
    for para in paragraphs:
        para_words = para.split()
        if len(para_words) > max_words:
            if current:
                chunks.append(" ".join(current))
                current, current_words = [], 0
            chunks.extend(words_to_chunks(para_words))
            continue
        if current_words + len(para_words) > max_words and current:
            chunks.append(" ".join(current))
            current, current_words = [], 0
        current.extend(para_words)
        current_words += len(para_words)
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
    scores = {
        dim: round(max(0.0, min(100.0, float(data.get(dim, 0.0)))), 2)
        for dim in DIMENSIONS
    }
    return scores


def call_chunk(prompt: str, chunk: str, key: str) -> dict:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Score this political passage:\n\n{chunk}"},
        ],
        "temperature": 0,
        "max_completion_tokens": 80,
        "reasoning_effort": "none",
    }
    body = json.dumps(payload).encode("utf-8")
    last_error = None
    for attempt in range(5):
        req = request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=180) as response:
                payload = json.load(response)
            choice = (payload.get("choices") or [{}])[0]
            content = (choice.get("message") or {}).get("content")
            return {
                "scores": parse_scores(content),
                "usage": payload.get("usage") or {},
                "error": None,
            }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if isinstance(exc, error.HTTPError) and exc.code in (401, 403):
                break
            if attempt < 4:
                time.sleep(min(30, 2 ** attempt))
    return {"scores": None, "usage": {}, "error": last_error}


async def score_chunk(semaphore: asyncio.Semaphore, prompt: str,
                      chunk: str, key: str) -> dict:
    async with semaphore:
        return await asyncio.to_thread(call_chunk, prompt, chunk, key)


async def process_doc(semaphore: asyncio.Semaphore, prompt: str,
                      doc: dict, key: str) -> dict:
    chunks = split_chunks(doc["text"])
    results = await asyncio.gather(*[
        score_chunk(semaphore, prompt, chunk, key) for chunk in chunks
    ])
    valid = [r for r in results if r["scores"] is not None]
    if not valid:
        scores = None
    else:
        weights = [len(chunks[i].split()) for i, r in enumerate(results)
                   if r["scores"] is not None]
        scores = {
            dim: round(sum(w * r["scores"][dim] for w, r in zip(weights, valid)) / sum(weights), 2)
            for dim in DIMENSIONS
        }
        scores["final_score"] = round(sum(scores[dim] for dim in DIMENSIONS) / len(DIMENSIONS), 2)
    usage = [r["usage"] for r in results if r["usage"]]
    return {
        "discourse_id": doc["discourse_id"],
        "iso3": doc.get("iso3"),
        "leader_name": doc.get("leader_name"),
        "filename": doc.get("filename"),
        "discourse_year": doc.get("discourse_year"),
        "word_count": doc.get("word_count"),
        "model": MODEL,
        "prompt_id": "v4",
        "provider": "openai_direct_chunked_pilot",
        "chunk_words": CHUNK_WORDS,
        "n_chunks": len(chunks),
        "n_valid_chunks": len(valid),
        "scores": scores,
        "chunk_scores": [r["scores"] for r in results],
        "usage": usage,
        "errors": [r["error"] for r in results if r["error"]],
    }


async def main() -> None:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY não definido")
    docs = [json.loads(line) for line in INPUT_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    prompt = load_prompt()
    semaphore = asyncio.Semaphore(CONCURRENCY)
    rows = []
    for doc in docs:
        row = await process_doc(semaphore, prompt, doc, key)
        rows.append(row)
        print(json.dumps({
            "discourse_id": row["discourse_id"],
            "leader_name": row["leader_name"],
            "n_chunks": row["n_chunks"],
            "final_score": (row["scores"] or {}).get("final_score"),
            "errors": len(row["errors"]),
        }, ensure_ascii=False), flush=True)
    OUTPUT_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(f"saved={OUTPUT_PATH} rows={len(rows)}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
