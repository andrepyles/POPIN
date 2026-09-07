"""POPIN v4 — piloto de scoring, somente etapa 2.

Compara Qwen e DeepSeek com o prompt v4 atual e uma variante v4 com âncoras
textuais mínimas de escala, sem exemplos few-shot e sem alterar os seis eixos.
"""

from __future__ import annotations

import ast
import concurrent.futures
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "popin.duckdb"
SAMPLE_PATH = ROOT / "data/gpd_v2_1_20251120/sensitivity_test_sample.csv"
OUT_DIR = ROOT / "data/gpd_v2_1_20251120/pilot_runs"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
CHUNK_WORDS = 800
DIMENSIONS = [
    "people_centrism", "anti_elitism", "moral_dichotomy",
    "popular_sovereignty", "exclusionary_rhetoric", "crisis_rhetoric",
]


def load_v4_prompt() -> str:
    tree = ast.parse((ROOT / "04_score.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "SYSTEM_PROMPT" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("SYSTEM_PROMPT não encontrado")


V4_PROMPT = load_v4_prompt()


def anchored_prompt() -> str:
    start = V4_PROMPT.index("CONTINUOUS SCORING RULES:")
    end = V4_PROMPT.index("OUTPUT SCHEMA (strict minified JSON):")
    rules = """CONTINUOUS SCORING RULES:
- Range: [0.00, 100.00] with 0.01 resolution.
- 0.00 = no qualifying evidence for this dimension.
- 1.00–24.99 = weak or incidental evidence.
- 25.00–49.99 = clear but limited evidence.
- 50.00–74.99 = strong and recurrent evidence.
- 75.00–100.00 = dominant, systematic, and extreme evidence.
- The score represents evidentiary intensity for this dimension, not probability
  and not the share of words in the excerpt.
- Score each dimension independently. Do not lower one dimension because other
  dimensions are absent.
- Use 0.00 only when the qualifying evidence is absent from the excerpt.
- Weight explicit normative claims more than metaphors or implications.
- Do not inflate scores for text length, tone, or emotionality alone.

"""
    prompt = V4_PROMPT[:start] + rules + V4_PROMPT[end:]
    fewshot_start = prompt.index("FEW-SHOT EXAMPLE")
    output_start = prompt.index("Output ONLY the final JSON.", fewshot_start)
    return prompt[:fewshot_start] + prompt[output_start:]


def split_chunks(text: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n{1,}", text) if p.strip()]
    chunks, current, nwords = [], [], 0
    for paragraph in paragraphs:
        words = paragraph.split()
        if len(words) > CHUNK_WORDS:
            if current:
                chunks.append(" ".join(current))
                current, nwords = [], 0
            chunks.extend(" ".join(words[i:i + CHUNK_WORDS])
                          for i in range(0, len(words), CHUNK_WORDS))
        elif current and nwords + len(words) > CHUNK_WORDS:
            chunks.append(" ".join(current))
            current, nwords = words[:], len(words)
        else:
            current.extend(words)
            nwords += len(words)
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
        dim: round(max(0.0, min(100.0, float(data.get(dim, 0.0))),), 2)
        for dim in DIMENSIONS
    }


def call(model: str, prompt: str, chunk: str, key: str) -> dict:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Score this political passage:\n\n{chunk}"},
        ],
        "temperature": 0,
        "max_tokens": 256,
        "reasoning": {"effort": "none"},
        "provider": {"allow_fallbacks": False},
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://popin.local",
            "X-Title": "POPIN v4 stage 2 pilot",
        },
        method="POST",
    )
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                payload = json.load(response)
            if payload.get("error"):
                raise RuntimeError(payload["error"])
            choice = (payload.get("choices") or [{}])[0]
            return {
                "scores": parse_scores((choice.get("message") or {}).get("content")),
                "usage": payload.get("usage") or {},
                "error": None,
            }
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 402, 403):
                break
            time.sleep(min(30, 2 ** attempt))
    return {"scores": None, "usage": {}, "error": last}


def load_ten() -> list[dict]:
    import pandas as pd

    sample = pd.read_csv(SAMPLE_PATH)
    sample = sample[sample.discourse_id.isin(set(
        json.loads(line)["discourse_id"]
        for line in (ROOT / "data/gpd_v2_1_20251120/sensitivity_runs/deepseek_deepseek-v4-flash-0731__v4.jsonl").open()
        if line.strip()
    ))].copy()
    sample["bin"] = pd.cut(
        sample.baseline_final_score, [-.01, 20, 40, 60, 80, 100],
        labels=["0-20", "20-40", "40-60", "60-80", "80-100"],
    )
    selected = []
    for _, group in sample.groupby("bin", observed=True):
        group = group.sort_values(["baseline_final_score", "discourse_id"])
        selected.extend([group.iloc[int(.33 * (len(group) - 1))],
                         group.iloc[int(.66 * (len(group) - 1))]])
    ids = [str(row.discourse_id) for row in selected[:10]]
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        placeholders = ",".join("?" for _ in ids)
        rows = con.execute(
            f"SELECT id, discourse FROM discourses WHERE id IN ({placeholders})", ids
        ).fetchall()
    finally:
        con.close()
    texts = {row[0]: row[1] for row in rows}
    return [{"discourse_id": id_, "text": texts[id_]} for id_ in ids]


def run_config(model: str, prompt_id: str, prompt: str, docs: list[dict], key: str) -> None:
    slug = model.replace("/", "_")
    out = OUT_DIR / f"stage2_10__{slug}__{prompt_id}.jsonl"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for doc in docs:
            chunks = split_chunks(doc["text"])
            futures = [pool.submit(call, model, prompt, chunk, key) for chunk in chunks]
            results = [f.result() for f in futures]
            valid = [r for r in results if r["scores"] is not None]
            if valid:
                weights = [len(chunks[i].split()) for i, r in enumerate(results) if r["scores"] is not None]
                scores = {
                    dim: round(sum(w * r["scores"][dim] for w, r in zip(weights, valid)) / sum(weights), 2)
                    for dim in DIMENSIONS
                }
                scores["final_score"] = round(sum(scores.values()) / len(DIMENSIONS), 2)
            else:
                scores = None
            rows.append({
                "model": model, "prompt_id": prompt_id,
                "discourse_id": doc["discourse_id"], "scores": scores,
                "n_chunks": len(chunks), "errors": [r["error"] for r in results if r["error"]],
                "cost_usd": sum(float((r["usage"] or {}).get("cost") or 0) for r in results),
            })
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(out)


if __name__ == "__main__":
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY não definido")
    docs = load_ten()
    prompt_ids = [item.strip() for item in os.getenv("PILOT_PROMPTS", "v4,anchored").split(",") if item.strip()]
    for model in ["qwen/qwen3-30b-a3b-instruct-2507", "deepseek/deepseek-v4-flash-0731"]:
        for prompt_id in prompt_ids:
            prompt = V4_PROMPT if prompt_id == "v4" else anchored_prompt()
            run_config(model, prompt_id, prompt, docs, key)
