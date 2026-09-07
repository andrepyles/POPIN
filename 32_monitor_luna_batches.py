#!/usr/bin/env python3
"""Libera sequencialmente os shards Luna chunked sem ultrapassar a fila."""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BATCH_DIR = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna_chunked_sample1000_batches_1p5m"
TOTAL_SHARDS = 9
POLL_SECONDS = 60
ACTIVE = {"validating", "in_progress", "finalizing", "cancelling"}


def status(batch_id: str) -> dict:
    req = urllib.request.Request(
        f"https://api.openai.com/v1/batches/{batch_id}",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def submitted(shard: int) -> dict | None:
    path = BATCH_DIR / f"batch_{shard:03d}.submitted.json"
    if not path.exists():
        return None
    record = json.loads(path.read_text(encoding="utf-8"))
    # O script de submissão preserva o retorno completo em {input_file_id,batch}.
    record["batch_id"] = record.get("batch_id") or record.get("batch", {}).get("id")
    return record


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY ausente")
    while True:
        active = []
        completed = []
        for shard in range(1, TOTAL_SHARDS + 1):
            record = submitted(shard)
            if not record:
                continue
            batch = status(record["batch_id"])
            current = batch.get("status")
            if current in ACTIVE:
                active.append((shard, current, batch.get("request_counts")))
            elif current == "completed":
                completed.append(shard)
            elif current in {"failed", "expired", "cancelled"}:
                print(json.dumps({"event": "stopped", "shard": shard, "status": current, "errors": batch.get("errors")}, ensure_ascii=False), flush=True)
                return

        if active:
            print(json.dumps({"event": "waiting", "active": active, "completed": completed}, ensure_ascii=False), flush=True)
            time.sleep(POLL_SECONDS)
            continue

        next_shard = next((s for s in range(1, TOTAL_SHARDS + 1) if not submitted(s)), None)
        if next_shard is None:
            print(json.dumps({"event": "finished", "shards": TOTAL_SHARDS}, ensure_ascii=False), flush=True)
            return

        print(json.dumps({"event": "submitting", "shard": next_shard}, ensure_ascii=False), flush=True)
        subprocess.run([
            "python3", str(ROOT / "31_luna_chunked_batch.py"), "submit",
            "--outdir", str(BATCH_DIR), "--shard", str(next_shard),
        ], check=True)
        time.sleep(5)


if __name__ == "__main__":
    main()
