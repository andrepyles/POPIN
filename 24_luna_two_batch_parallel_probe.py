"""Teste de dois batches Luna simultâneos abaixo do limite de fila."""

from __future__ import annotations

import csv
import importlib.util
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "20_luna_evo_all_openai_batch.py"
SAMPLE = ROOT / "data/gpd_v2_1_20251120/sensitivity_test_sample.csv"
OUT_DIR = ROOT / "data/gpd_v2_1_20251120/pilot_runs"
TARGET_EST_TOKENS = 650_000


def load_module():
    spec = importlib.util.spec_from_file_location("luna_batch", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.load_local_env()
    return module


def load_docs(module):
    sample_ids = {
        row["discourse_id"]
        for row in csv.DictReader(SAMPLE.open(encoding="utf-8-sig", newline=""))
    }
    con = duckdb.connect(str(module.DB_PATH), read_only=True)
    try:
        rows = con.execute(
            """
            SELECT id, iso3, leader_name, filename, discourse_date,
                   discourse_year, word_count, dtype, discourse
            FROM discourses
            WHERE dtype = 'SPEECH' AND id NOT IN (SELECT * FROM UNNEST(?))
            ORDER BY id
            LIMIT 2000
            """,
            [list(sample_ids)],
        ).fetchall()
    finally:
        con.close()
    keys = [
        "discourse_id", "iso3", "leader_name", "filename", "discourse_date",
        "discourse_year", "word_count", "dtype", "text",
    ]
    docs = []
    for row in rows:
        doc = dict(zip(keys, row))
        if doc["discourse_date"] is not None:
            doc["discourse_date"] = doc["discourse_date"].isoformat()
        docs.append(doc)
    return docs


def make_shards(module, docs):
    prompt = module.load_prompt()
    shards = [[], []]
    estimates = [0, 0]
    for doc in docs:
        line = json.dumps(module.make_request(doc, prompt), ensure_ascii=False)
        estimate = max(1, len(line) // 4)
        target = 0 if estimates[0] <= estimates[1] else 1
        if estimates[target] + estimate > TARGET_EST_TOKENS:
            other = 1 - target
            if estimates[other] + estimate <= TARGET_EST_TOKENS:
                target = other
            else:
                if all(estimates[i] >= TARGET_EST_TOKENS for i in (0, 1)):
                    break
        shards[target].append((doc, line, estimate))
        estimates[target] += estimate
        if all(estimates[i] >= TARGET_EST_TOKENS for i in (0, 1)):
            break
    return shards, estimates


def submit(module, shard, index, key):
    lines = ("\n".join(item[1] for item in shard) + "\n").encode("utf-8")
    uploaded = module.upload_jsonl(lines, key)
    file_id = uploaded["id"]
    batch = module.api_json(
        f"{module.API_BASE}/batches", key, "POST", {
            "input_file_id": file_id,
            "endpoint": "/v1/chat/completions",
            "completion_window": "24h",
            "metadata": {
                "project": "popin", "probe": "two_parallel_batches_v4",
                "shard": str(index), "requests": str(len(shard)),
            },
        }
    )
    return {"index": index, "file_id": file_id, "batch": batch, "requests": len(shard), "estimated_tokens": sum(x[2] for x in shard)}


def main():
    module = load_module()
    key = module.os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY não definido")
    docs = load_docs(module)
    shards, estimates = make_shards(module, docs)
    if any(not shard for shard in shards):
        raise RuntimeError(f"não foi possível construir dois shards: {estimates}")
    print(json.dumps({"docs": sum(len(s) for s in shards), "requests": [len(s) for s in shards], "estimated_tokens": estimates}, ensure_ascii=False), flush=True)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit, module, shard, i + 1, key) for i, shard in enumerate(shards)]
        submitted = [future.result() for future in futures]
    for item in submitted:
        batch = item["batch"]
        print(json.dumps({"event": "submitted", "shard": item["index"], "batch_id": batch.get("id"), "status": batch.get("status"), "requests": item["requests"], "estimated_tokens": item["estimated_tokens"]}, ensure_ascii=False), flush=True)

    statuses = {item["index"]: item for item in submitted}
    while any(item["batch"].get("status") not in module.TERMINAL for item in statuses.values()):
        time.sleep(10)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {
                pool.submit(module.api_json, f"{module.API_BASE}/batches/{item['batch']['id']}", key): index
                for index, item in statuses.items()
                if item["batch"].get("status") not in module.TERMINAL
            }
            for future, index in [(future, futures[future]) for future in futures]:
                statuses[index]["batch"] = future.result()
        for index, item in statuses.items():
            batch = item["batch"]
            print(json.dumps({"event": "status", "shard": index, "batch_id": batch.get("id"), "status": batch.get("status"), "request_counts": batch.get("request_counts")}, ensure_ascii=False), flush=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    docs_by_id = {str(doc["discourse_id"]): doc for shard in shards for doc, _, _ in shard}
    for index, item in statuses.items():
        batch = item["batch"]
        result = {"shard": index, "batch_id": batch.get("id"), "status": batch.get("status"), "request_counts": batch.get("request_counts"), "usage": batch.get("usage"), "errors": batch.get("errors")}
        if batch.get("status") == "completed" and batch.get("output_file_id"):
            req = module.request.Request(f"{module.API_BASE}/files/{batch['output_file_id']}/content", headers={"Authorization": f"Bearer {key}"})
            with module.request.urlopen(req, timeout=180) as response:
                parsed = module.parse_output(response.read(), docs_by_id, batch["id"])
            path = OUT_DIR / f"luna__parallel_probe_shard{index}__openai__v4.jsonl"
            path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in parsed.values()), encoding="utf-8")
            result["output"] = str(path)
            result["returned"] = len(parsed)
        (OUT_DIR / f"luna__parallel_probe_shard{index}__openai__v4.meta.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"event": "saved", **result}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
