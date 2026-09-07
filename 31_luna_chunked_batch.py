#!/usr/bin/env python3
"""Prepara e submete o Luna chunked v4 pela OpenAI Batch API."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import time
import urllib.request
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODEL = "gpt-5.6-luna"
CHUNK_WORDS = 800
DEFAULT_INPUT = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna_chunked_sample1000_input.jsonl"
DEFAULT_BATCH_DIR = ROOT / "data/gpd_v2_1_20251120/pilot_runs/luna_chunked_sample1000_batches"
MAX_EST_TOKENS = int(os.getenv("LUNA_BATCH_MAX_EST_TOKENS", "1500000"))


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
        return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

    paragraphs = [p.strip() for p in re.split(r"\n{1,}", text) if p.strip()]
    chunks, current, current_words = [], [], 0
    for para in paragraphs:
        words = para.split()
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


def prepare(input_path: Path, batch_dir: Path) -> None:
    if batch_dir.exists() and any(batch_dir.iterdir()):
        raise RuntimeError(f"Diretório já contém arquivos: {batch_dir}")
    batch_dir.mkdir(parents=True, exist_ok=True)
    prompt = load_prompt()
    docs = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    lines: list[str] = []
    metadata: list[dict] = []
    est_tokens = 0
    shard = 1
    total_chunks = 0

    def flush() -> None:
        nonlocal lines, metadata, est_tokens, shard
        if not lines:
            return
        path = batch_dir / f"batch_{shard:03d}.jsonl"
        path.write_text("".join(lines), encoding="utf-8")
        (batch_dir / f"batch_{shard:03d}.meta.json").write_text(
            json.dumps({"estimated_tokens": est_tokens, "requests": len(lines), "rows": metadata}, ensure_ascii=False),
            encoding="utf-8",
        )
        print(json.dumps({"file": str(path), "requests": len(lines), "estimated_tokens": est_tokens}, ensure_ascii=False), flush=True)
        lines, metadata, est_tokens = [], [], 0
        shard += 1

    for doc in docs:
        chunks = split_chunks(doc["text"])
        for idx, chunk in enumerate(chunks):
            custom_id = f"luna_s1000_{doc['discourse_id']}_c{idx:03d}"
            body = {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Score this political passage:\n\n{chunk}"},
                ],
                "temperature": 0,
                "max_completion_tokens": 80,
                "reasoning_effort": "none",
            }
            line_obj = {"custom_id": custom_id, "method": "POST", "url": "/v1/chat/completions", "body": body}
            # Estimativa conservadora: caracteres/4 + saída máxima.
            estimate = max(1, (len(prompt) + len(chunk)) // 4 + 80)
            if lines and est_tokens + estimate > MAX_EST_TOKENS:
                flush()
            lines.append(json.dumps(line_obj, ensure_ascii=False) + "\n")
            metadata.append({
                "custom_id": custom_id,
                "discourse_id": doc["discourse_id"],
                "chunk_idx": idx,
                "n_chunks": len(chunks),
                "chunk_words": len(chunk.split()),
                "filename": doc.get("filename"),
                "iso3": doc.get("iso3"),
                "leader_name": doc.get("leader_name"),
            })
            est_tokens += estimate
            total_chunks += 1
    flush()
    (batch_dir / "manifest.json").write_text(json.dumps({"model": MODEL, "prompt_id": "v4", "chunk_words": CHUNK_WORDS, "overlap": 0, "documents": len(docs), "chunks": total_chunks, "max_est_tokens": MAX_EST_TOKENS}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"documents": len(docs), "chunks": total_chunks, "shards": shard - 1, "dir": str(batch_dir)}, ensure_ascii=False))


def api_json(method: str, url: str, key: str, data: bytes | None = None, headers: dict | None = None) -> dict:
    req_headers = {"Authorization": f"Bearer {key}"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)


def upload(path: Path, key: str) -> str:
    boundary = uuid.uuid4().hex
    body = b"--" + boundary.encode() + b"\r\n"
    body += b'Content-Disposition: form-data; name="purpose"\r\n\r\n'
    body += b"batch\r\n--" + boundary.encode() + b"\r\n"
    body += f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'.encode()
    body += b"Content-Type: application/jsonl\r\n\r\n" + path.read_bytes()
    body += b"\r\n--" + boundary.encode() + b"--\r\n"
    result = api_json("POST", "https://api.openai.com/v1/files", key, body, {"Content-Type": f"multipart/form-data; boundary={boundary}"})
    return result["id"]


def submit(batch_dir: Path, shard: int, key: str) -> None:
    path = batch_dir / f"batch_{shard:03d}.jsonl"
    if not path.exists():
        raise FileNotFoundError(path)
    file_id = upload(path, key)
    payload = json.dumps({"input_file_id": file_id, "endpoint": "/v1/chat/completions", "completion_window": "24h", "metadata": {"run_id": "luna_chunked_sample1000_v4", "shard": f"{shard:03d}"}}).encode()
    batch = api_json("POST", "https://api.openai.com/v1/batches", key, payload, {"Content-Type": "application/json"})
    (batch_dir / f"batch_{shard:03d}.submitted.json").write_text(json.dumps({"input_file_id": file_id, "batch": batch}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"shard": shard, "file_id": file_id, "batch_id": batch.get("id"), "status": batch.get("status"), "request_counts": batch.get("request_counts")}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--outdir", type=Path, default=DEFAULT_BATCH_DIR)
    s = sub.add_parser("submit")
    s.add_argument("--outdir", type=Path, default=DEFAULT_BATCH_DIR)
    s.add_argument("--shard", type=int, required=True)
    args = parser.parse_args()
    if args.cmd == "prepare":
        prepare(args.input, args.outdir)
    else:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise SystemExit("OPENAI_API_KEY ausente")
        submit(args.outdir, args.shard, key)


if __name__ == "__main__":
    main()
