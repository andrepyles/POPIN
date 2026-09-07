"""POPIN v4 — Batch do Luna particionado por tokens e processado em ondas.

Cada batch recebe unidades até um teto estimado de tokens. As submissões são
feitas em paralelo, mas o total estimado de tokens em voo fica abaixo de um
orçamento conservador, evitando o limite de 1M observado na organização.
"""

from __future__ import annotations

import concurrent.futures
import importlib.util
import json
import os
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "14_luna_64_batch.py"
OUT_PATH = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna__64_batch_token_parallel__v4.jsonl"
META_PATH = OUT_PATH.with_suffix(".meta.json")

# Valores conservadores: a fila observada é de 1M de tokens.
TARGET_BATCH_TOKENS = 100_000
MAX_IN_FLIGHT_TOKENS = 800_000
MAX_WORKERS = 4
OUTPUT_RESERVE = 512


def load_module():
    spec = importlib.util.spec_from_file_location("luna_batch", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Não foi possível carregar {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def estimate_tokens(mod, prompt: str, doc: dict) -> int:
    """Estima tokens de entrada; usa tokenizer compatível quando disponível."""
    text = prompt + "\nScore this political passage:\n\n" + doc["text"]
    try:
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model("gpt-5")
        except Exception:
            encoding = tiktoken.get_encoding("o200k_base")
        prompt_tokens = len(encoding.encode(text))
    except Exception:
        # Fallback conservador para textos PT/EN quando tiktoken não estiver disponível.
        prompt_tokens = int(len(text) / 3.2)
    return prompt_tokens + OUTPUT_RESERVE


def make_batches(mod, docs: list[dict], prompt: str) -> list[dict]:
    weighted = [
        {"doc": doc, "estimated_tokens": estimate_tokens(mod, prompt, doc)}
        for doc in docs
    ]
    # First-fit decreasing: reduz o desperdício dos lotes quando há discursos
    # muito longos misturados com discursos curtos.
    weighted.sort(key=lambda item: item["estimated_tokens"], reverse=True)
    batches: list[dict] = []
    for item in weighted:
        if item["estimated_tokens"] > TARGET_BATCH_TOKENS:
            batches.append({"items": [item], "estimated_tokens": item["estimated_tokens"]})
            continue
        destination = None
        for batch in batches:
            if batch["estimated_tokens"] + item["estimated_tokens"] <= TARGET_BATCH_TOKENS:
                destination = batch
                break
        if destination is None:
            destination = {"items": [], "estimated_tokens": 0}
            batches.append(destination)
        destination["items"].append(item)
        destination["estimated_tokens"] += item["estimated_tokens"]
    for index, batch in enumerate(batches, start=1):
        batch["batch_index"] = index
        batch["docs"] = [item["doc"] for item in batch.pop("items")]
    return batches


def build_requests(mod, docs: list[dict], prompt: str) -> list[dict]:
    return [{
        "custom_id": str(doc["discourse_id"]),
        "body": {
            "model": mod.MODEL,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Score this political passage:\n\n{doc['text']}"},
            ],
            "temperature": 0,
            "max_tokens": 256,
            "reasoning": {"effort": "none"},
            "provider": {"allow_fallbacks": True},
        },
    } for doc in docs]


def run_batch(mod, key: str, batch: dict, prompt: str) -> dict:
    started = time.time()
    requests = build_requests(mod, batch["docs"], prompt)
    created = mod.post_json(mod.BATCH_URL, key, {
        "endpoint": "/v1/chat/completions",
        "model": mod.MODEL,
        "requests": requests,
    })
    batch_id = created.get("id")
    if not batch_id:
        raise RuntimeError(f"Batch {batch['batch_index']} sem id: {created}")
    print(json.dumps({
        "batch_index": batch["batch_index"],
        "batch_id": batch_id,
        "status": created.get("status"),
        "requests": len(requests),
        "estimated_tokens": batch["estimated_tokens"],
    }, ensure_ascii=False), flush=True)
    current = created
    while current.get("status") not in {"completed", "failed", "cancelled", "expired"}:
        time.sleep(10)
        current = mod.get_json(f"{mod.BATCH_URL}/{batch_id}", key)
        print(json.dumps({
            "batch_index": batch["batch_index"],
            "batch_id": batch_id,
            "status": current.get("status"),
            "request_counts": current.get("request_counts"),
        }, ensure_ascii=False), flush=True)
    return {
        "batch": batch,
        "response": current,
        "elapsed_s": round(time.time() - started, 3),
    }


def materialize(mod, run: dict) -> list[dict]:
    batch = run["batch"]
    response = run["response"]
    by_id = {str(doc["discourse_id"]): doc for doc in batch["docs"]}
    returned = {str(item.get("custom_id")) for item in response.get("results") or []}
    output = []
    for item in response.get("results") or []:
        custom_id = str(item.get("custom_id"))
        doc = by_id.get(custom_id)
        if not doc:
            continue
        http_status, body, error = mod.extract_response(item)
        content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content") if body else None
        try:
            scores = mod.parse_scores(content)
            scores["final_score"] = round(sum(scores.values()) / len(mod.DIMENSIONS), 2)
            parse_error = None
        except Exception as exc:
            scores = None
            parse_error = f"{type(exc).__name__}: {exc}"
        output.append({
            **{key: doc[key] for key in ("discourse_id", "iso3", "leader_name", "gpd_term_key", "gpd_totalaverage")},
            "model": mod.MODEL,
            "batch_id": response.get("id"),
            "batch_index": batch["batch_index"],
            "estimated_tokens": batch["estimated_tokens"],
            "scores": scores,
            "raw_content": content,
            "usage": body.get("usage") or {},
            "error": error or parse_error,
            "http_status": http_status,
        })
    for doc in batch["docs"]:
        if str(doc["discourse_id"]) not in returned:
            output.append({
                **{key: doc[key] for key in ("discourse_id", "iso3", "leader_name", "gpd_term_key", "gpd_totalaverage")},
                "model": mod.MODEL,
                "batch_id": response.get("id"),
                "batch_index": batch["batch_index"],
                "estimated_tokens": batch["estimated_tokens"],
                "scores": None,
                "raw_content": None,
                "usage": {},
                "error": f"Resultado ausente; status={response.get('status')}; error={response.get('error')}",
                "http_status": None,
            })
    return output


def main() -> None:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY não definido")
    mod = load_module()
    docs = mod.load_representative_docs()
    prompt = mod.load_v4_prompt()
    batches = make_batches(mod, docs, prompt)
    total_estimated = sum(batch["estimated_tokens"] for batch in batches)
    print(json.dumps({
        "requests": len(docs),
        "batches": len(batches),
        "target_batch_tokens": TARGET_BATCH_TOKENS,
        "max_in_flight_tokens": MAX_IN_FLIGHT_TOKENS,
        "total_estimated_tokens": total_estimated,
        "batch_sizes": [{"index": b["batch_index"], "requests": len(b["docs"]), "tokens": b["estimated_tokens"]} for b in batches],
    }, ensure_ascii=False), flush=True)

    all_results = []
    runs = []
    pending = list(batches)
    started = time.time()
    while pending:
        wave = []
        wave_tokens = 0
        while pending and len(wave) < MAX_WORKERS:
            candidate = pending[0]
            if wave and wave_tokens + candidate["estimated_tokens"] > MAX_IN_FLIGHT_TOKENS:
                break
            pending.pop(0)
            wave.append(candidate)
            wave_tokens += candidate["estimated_tokens"]
        print(json.dumps({"wave_batches": [b["batch_index"] for b in wave], "wave_estimated_tokens": wave_tokens}, ensure_ascii=False), flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(wave)) as pool:
            futures = [pool.submit(run_batch, mod, key, batch, prompt) for batch in wave]
            for future in futures:
                run = future.result()
                runs.append(run)
                all_results.extend(materialize(mod, run))

    all_results.sort(key=lambda item: str(item["discourse_id"]))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as handle:
        for result in all_results:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
    valid = sum(item["scores"] is not None for item in all_results)
    cost = sum(float((item["usage"] or {}).get("cost") or 0) for item in all_results)
    meta = {
        "requests": len(docs),
        "batches": len(batches),
        "written_results": len(all_results),
        "valid": valid,
        "target_batch_tokens": TARGET_BATCH_TOKENS,
        "max_in_flight_tokens": MAX_IN_FLIGHT_TOKENS,
        "max_workers": MAX_WORKERS,
        "total_estimated_tokens": total_estimated,
        "elapsed_s": round(time.time() - started, 3),
        "cost_usd": round(cost, 6),
        "batch_runs": [{
            "batch_index": run["batch"]["batch_index"],
            "batch_id": run["response"].get("id"),
            "status": run["response"].get("status"),
            "estimated_tokens": run["batch"]["estimated_tokens"],
            "requests": len(run["batch"]["docs"]),
            "elapsed_s": run["elapsed_s"],
            "request_counts": run["response"].get("request_counts"),
            "usage": run["response"].get("usage"),
            "error": run["response"].get("error"),
        } for run in runs],
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(OUT_PATH),
        "metadata": str(META_PATH),
        **meta,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
