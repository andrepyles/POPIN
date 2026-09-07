"""Piloto Batch do Luna em lotes sequenciais de oito.

O primeiro lote de 64 foi aceito, mas a fila do provedor recusou o conjunto
inteiro por exceder 1M de tokens enfileirados. Este script preserva o mesmo
piloto e processa oito requisições por vez, aguardando cada lote terminar antes
de submeter o próximo.
"""

from __future__ import annotations

import importlib.util
import json
import os
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "14_luna_64_batch.py"
OUT_PATH = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna__64_batch_sharded8__v4.jsonl"
META_PATH = OUT_PATH.with_suffix(".meta.json")
BATCH_SIZE = 8


def load_module():
    spec = importlib.util.spec_from_file_location("luna_batch", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Não foi possível carregar {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def wait_batch(mod, key: str, docs: list[dict], prompt: str) -> tuple[dict, float]:
    requests = []
    for doc in docs:
        requests.append({
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
        })
    started = time.time()
    created = mod.post_json(mod.BATCH_URL, key, {
        "endpoint": "/v1/chat/completions",
        "model": mod.MODEL,
        "requests": requests,
    })
    batch_id = created.get("id")
    if not batch_id:
        raise RuntimeError(f"Resposta sem batch id: {created}")
    print(json.dumps({"batch_id": batch_id, "status": created.get("status"), "n": len(docs)}, ensure_ascii=False), flush=True)
    batch = created
    while batch.get("status") not in {"completed", "failed", "cancelled", "expired"}:
        time.sleep(10)
        batch = mod.get_json(f"{mod.BATCH_URL}/{batch_id}", key)
        print(json.dumps({
            "batch_id": batch_id,
            "status": batch.get("status"),
            "completed": batch.get("completed"),
            "failed": batch.get("failed"),
        }, ensure_ascii=False), flush=True)
    return batch, round(time.time() - started, 3)


def materialize(mod, batch: dict, docs: list[dict], batch_index: int) -> list[dict]:
    by_id = {str(doc["discourse_id"]): doc for doc in docs}
    output = []
    returned = {str(item.get("custom_id")) for item in batch.get("results") or []}
    for item in batch.get("results") or []:
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
            "batch_id": batch.get("id"),
            "batch_index": batch_index,
            "scores": scores,
            "raw_content": content,
            "usage": body.get("usage") or {},
            "error": error or parse_error,
            "http_status": http_status,
        })
    for doc in docs:
        if str(doc["discourse_id"]) not in returned:
            output.append({
                **{key: doc[key] for key in ("discourse_id", "iso3", "leader_name", "gpd_term_key", "gpd_totalaverage")},
                "model": mod.MODEL,
                "batch_id": batch.get("id"),
                "batch_index": batch_index,
                "scores": None,
                "raw_content": None,
                "usage": {},
                "error": f"Resultado ausente no Batch; status={batch.get('status')}; error={batch.get('error')}",
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
    all_results = []
    batch_meta = []
    started = time.time()
    for offset in range(0, len(docs), BATCH_SIZE):
        shard = docs[offset:offset + BATCH_SIZE]
        index = offset // BATCH_SIZE + 1
        try:
            batch, elapsed = wait_batch(mod, key, shard, prompt)
        except Exception as exc:
            raise SystemExit(f"Falha no lote {index}: {type(exc).__name__}: {exc}") from exc
        batch_meta.append({
            "batch_index": index,
            "batch_id": batch.get("id"),
            "status": batch.get("status"),
            "elapsed_s": elapsed,
            "request_counts": batch.get("request_counts"),
            "error": batch.get("error"),
        })
        all_results.extend(materialize(mod, batch, shard, index))
        if batch.get("status") != "completed":
            print(json.dumps({"stopped_after_batch": index, "status": batch.get("status")}, ensure_ascii=False), flush=True)
            break

    all_results.sort(key=lambda item: str(item["discourse_id"]))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as handle:
        for result in all_results:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
    valid = sum(item["scores"] is not None for item in all_results)
    cost = sum(float((item["usage"] or {}).get("cost") or 0) for item in all_results)
    meta = {
        "submitted_requests": len(docs),
        "written_results": len(all_results),
        "valid": valid,
        "batch_size": BATCH_SIZE,
        "batch_count": len(batch_meta),
        "elapsed_s": round(time.time() - started, 3),
        "cost_usd": round(cost, 6),
        "batches": batch_meta,
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(OUT_PATH),
        "metadata": str(META_PATH),
        **meta,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
