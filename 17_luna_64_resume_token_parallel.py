"""Retoma o piloto do Luna sem repetir batches já concluídos.

Recupera os quatro batches do piloto fixo de oito requisições e processa apenas
as unidades restantes com o particionamento por tokens do script 16.
"""

from __future__ import annotations

import concurrent.futures
import importlib.util
import json
import os
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE14 = ROOT / "14_luna_64_batch.py"
SOURCE16 = ROOT / "16_luna_64_batch_token_parallel.py"
OUT_PATH = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna__64_batch_token_resume__v4.jsonl"
META_PATH = OUT_PATH.with_suffix(".meta.json")
MAX_IN_FLIGHT_TOKENS = 800_000
MAX_WORKERS = 4

OLD_BATCH_IDS = [
    "batch-1786907769-bxPEIkGNwv4VWXTWhQYZ",
    "batch-1786907905-TcJWDGtH1cyn5RoEXZsI",
    "batch-1786908031-AwWlWX952SGOhRRmVaGr",
    "batch-1786908321-H1kW1UymYyOtaCwKWmAg",
]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Não foi possível carregar {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def wait_existing(mod, key: str, batch_id: str) -> dict:
    current = mod.get_json(f"{mod.BATCH_URL}/{batch_id}", key)
    while current.get("status") not in {"completed", "failed", "cancelled", "expired"}:
        time.sleep(10)
        current = mod.get_json(f"{mod.BATCH_URL}/{batch_id}", key)
        print(json.dumps({"existing_batch": batch_id, "status": current.get("status")}, ensure_ascii=False), flush=True)
    return current


def main() -> None:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY não definido")
    mod14 = load(SOURCE14, "luna_batch_base")
    mod16 = load(SOURCE16, "luna_batch_token")
    docs = mod14.load_representative_docs()
    prompt = mod14.load_v4_prompt()
    recovered = []
    old_meta = []
    recovered_ids = set()

    for index, batch_id in enumerate(OLD_BATCH_IDS, start=1):
        batch = wait_existing(mod14, key, batch_id)
        shard = docs[(index - 1) * 8:index * 8]
        run = {"batch": {"batch_index": index, "estimated_tokens": 0, "docs": shard}, "response": batch, "elapsed_s": None}
        if batch.get("status") == "completed":
            recovered.extend(mod16.materialize(mod14, run))
            recovered_ids.update(str(doc["discourse_id"]) for doc in shard)
        old_meta.append({
            "batch_index": index,
            "batch_id": batch_id,
            "status": batch.get("status"),
            "request_counts": batch.get("request_counts"),
            "usage": batch.get("usage"),
            "error": batch.get("error"),
        })
        print(json.dumps({"recovered_batch": index, "status": batch.get("status"), "recovered_ids": len(recovered_ids)}, ensure_ascii=False), flush=True)

    remaining = [doc for doc in docs if str(doc["discourse_id"]) not in recovered_ids]
    new_batches = mod16.make_batches(mod16, remaining, prompt)
    total_estimated = sum(batch["estimated_tokens"] for batch in new_batches)
    print(json.dumps({
        "recovered": len(recovered),
        "remaining": len(remaining),
        "new_batches": len(new_batches),
        "new_estimated_tokens": total_estimated,
        "max_in_flight_tokens": MAX_IN_FLIGHT_TOKENS,
    }, ensure_ascii=False), flush=True)

    new_runs = []
    pending = list(new_batches)
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
        print(json.dumps({"new_wave": [b["batch_index"] for b in wave], "estimated_tokens": wave_tokens}, ensure_ascii=False), flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(wave)) as pool:
            futures = [pool.submit(mod16.run_batch, mod16, key, batch, prompt) for batch in wave]
            for future in futures:
                run = future.result()
                new_runs.append(run)
                recovered.extend(mod16.materialize(mod14, run))

    recovered.sort(key=lambda item: str(item["discourse_id"]))
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as handle:
        for result in recovered:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
    valid = sum(item["scores"] is not None for item in recovered)
    cost = sum(float((item["usage"] or {}).get("cost") or 0) for item in recovered)
    meta = {
        "requests": len(docs),
        "written_results": len(recovered),
        "valid": valid,
        "recovered_old_results": len(recovered_ids),
        "new_requests": len(remaining),
        "new_batches": len(new_batches),
        "max_in_flight_tokens": MAX_IN_FLIGHT_TOKENS,
        "max_workers": MAX_WORKERS,
        "new_estimated_tokens": total_estimated,
        "cost_usd": round(cost, 6),
        "old_batches": old_meta,
        "new_batches_detail": [{
            "batch_index": run["batch"]["batch_index"],
            "batch_id": run["response"].get("id"),
            "status": run["response"].get("status"),
            "estimated_tokens": run["batch"]["estimated_tokens"],
            "requests": len(run["batch"]["docs"]),
            "usage": run["response"].get("usage"),
            "error": run["response"].get("error"),
        } for run in new_runs],
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUT_PATH), "metadata": str(META_PATH), **meta}, ensure_ascii=False))


if __name__ == "__main__":
    main()
