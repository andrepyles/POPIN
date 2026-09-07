"""Processa todos os textos não-INVALID com Luna via OpenAI Batch API.

O driver mantém no máximo três batches de aproximadamente 1,5 milhão de
tokens na fila (cerca de 4,5 milhões no total), abaixo do limite Tier 1 do
Luna. Resultados são gravados e importados no DuckDB a cada batch concluído,
permitindo retomada sem reenviar o que já terminou.
"""

from __future__ import annotations

import ast
import json
import os
import time
import uuid
from pathlib import Path
from urllib import error, request

import duckdb


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "popin.duckdb"
DATA_DIR = ROOT / "data/gpd_v2_1_20251120"
OUT_PATH = DATA_DIR / "full_runs/luna__all_noninvalid__openai__v4.jsonl"
STATE_PATH = DATA_DIR / "full_runs/luna__all_noninvalid__openai__v4.progress.json"
META_PATH = DATA_DIR / "full_runs/luna__all_noninvalid__openai__v4.meta.json"
API_BASE = "https://api.openai.com/v1"
MODEL = "gpt-5.6-luna"
PROMPT_ID = "v4"
PROVIDER = "openai_direct_batch"
RUN_ID = "luna__all_noninvalid__openai__v4"
# A organização devolveu token_limit_exceeded em 2.000.000 tokens enfileirados.
# Um batch de 1,2M deixa margem para cancelamentos ainda em propagação e para
# a reserva de saída contabilizada pela fila da API.
TARGET_BATCH_TOKENS = 1_200_000
MAX_IN_FLIGHT_TOKENS = 1_200_000
MAX_IN_FLIGHT_BATCHES = 1
POLL_SECONDS = 30
TERMINAL = {"completed", "failed", "cancelled", "expired"}
DIMENSIONS = [
    "people_centrism", "anti_elitism", "moral_dichotomy",
    "popular_sovereignty", "exclusionary_rhetoric", "crisis_rhetoric",
]


def load_local_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        value = value.strip().strip("'\"")
        if name.strip() and value:
            os.environ.setdefault(name.strip(), value)


def load_prompt() -> str:
    tree = ast.parse((ROOT / "04_score.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "SYSTEM_PROMPT"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("SYSTEM_PROMPT não encontrado")


def api_json(url: str, key: str, method: str = "GET", payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    req = request.Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with request.urlopen(req, timeout=180) as response:
            return json.load(response)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI HTTP {exc.code}: {detail[:1500]}") from exc


def upload_jsonl(lines: bytes, key: str, filename: str) -> dict:
    boundary = f"----codex-{uuid.uuid4().hex}"
    parts = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nbatch\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: application/jsonl\r\n\r\n".encode(),
        lines,
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    req = request.Request(
        f"{API_BASE}/files",
        data=b"".join(parts),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=300) as response:
            return json.load(response)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI upload HTTP {exc.code}: {detail[:1500]}") from exc


def download_file(file_id: str, key: str) -> bytes:
    req = request.Request(
        f"{API_BASE}/files/{file_id}/content",
        headers={"Authorization": f"Bearer {key}"},
    )
    with request.urlopen(req, timeout=300) as response:
        return response.read()


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
    scores["final_score"] = round(sum(scores.values()) / len(DIMENSIONS), 2)
    return scores


def seed_paths() -> list[Path]:
    return [
        DATA_DIR / "full_runs/luna__sample_900__openai__v4.jsonl",
        DATA_DIR / "full_runs/luna__evo_morales__openai__v4.jsonl",
        DATA_DIR / "pilot_runs/luna__parallel_probe_shard1__openai__v4.jsonl",
        DATA_DIR / "pilot_runs/luna__8_openai_batch_probe__v4.jsonl",
    ]


def load_seed_rows() -> dict[str, dict]:
    """Reaproveita apenas resultados Luna v4 já concluídos via OpenAI direta."""
    rows: dict[str, dict] = {}
    for path in seed_paths():
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("model") != MODEL or not row.get("scores"):
                continue
            discourse_id = str(row["discourse_id"])
            row["model"] = MODEL
            row["prompt_id"] = PROMPT_ID
            row["provider"] = PROVIDER
            rows.setdefault(discourse_id, row)
    return rows


def estimate_tokens(prompt: str, text: str) -> int:
    # Estimativa conservadora sem depender de tokenizer local; inclui reserva
    # de saída para que a fila da API não ultrapasse o teto operacional.
    return max(512, int((len(prompt) + len(text) + 64) / 4) + 512)


def doc_from_row(row: tuple) -> dict:
    keys = [
        "discourse_id", "iso3", "leader_name", "filename", "discourse_date",
        "discourse_year", "word_count", "dtype", "text",
    ]
    doc = dict(zip(keys, row))
    if doc["discourse_date"] is not None:
        doc["discourse_date"] = doc["discourse_date"].isoformat()
    return doc


def make_request(doc: dict, prompt: str) -> dict:
    return {
        "custom_id": str(doc["discourse_id"]),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Score this political passage:\n\n{doc['text']}"},
            ],
            "temperature": 0,
            "max_completion_tokens": 256,
            "reasoning_effort": "none",
        },
    }


def build_result(item: dict, doc: dict, batch_id: str) -> dict:
    response = item.get("response") or {}
    body = response.get("body") or response
    content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content")
    try:
        scores, parse_error = parse_scores(content), None
    except Exception as exc:
        scores, parse_error = None, f"{type(exc).__name__}: {exc}"
    return {
        **{key: doc[key] for key in ("discourse_id", "iso3", "leader_name", "filename", "discourse_date", "discourse_year", "word_count", "dtype")},
        "model": MODEL,
        "prompt_id": PROMPT_ID,
        "provider": PROVIDER,
        "run_id": RUN_ID,
        "batch_id": batch_id,
        "scores": scores,
        "raw_content": content,
        "usage": body.get("usage") or {},
        "error": item.get("error") or parse_error,
        "http_status": response.get("status_code"),
    }


def import_rows(rows: list[dict]) -> None:
    valid = [row for row in rows if row.get("scores")]
    if not valid:
        return
    con = duckdb.connect(str(DB_PATH))
    try:
        con.execute("BEGIN TRANSACTION")
        con.executemany(
            """
            INSERT INTO scores (
                discourse_id, model_id, people_centrism, anti_elitism,
                moral_dichotomy, popular_sovereignty, exclusionary_rhetoric,
                crisis_rhetoric, final_score, n_chunks, raw_json,
                prompt_id, provider, run_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (discourse_id, model_id) DO UPDATE SET
                people_centrism=excluded.people_centrism,
                anti_elitism=excluded.anti_elitism,
                moral_dichotomy=excluded.moral_dichotomy,
                popular_sovereignty=excluded.popular_sovereignty,
                exclusionary_rhetoric=excluded.exclusionary_rhetoric,
                crisis_rhetoric=excluded.crisis_rhetoric,
                final_score=excluded.final_score,
                n_chunks=excluded.n_chunks,
                raw_json=excluded.raw_json,
                prompt_id=excluded.prompt_id,
                provider=excluded.provider,
                run_id=excluded.run_id,
                scored_at=now()
            """,
            [
                (
                    row["discourse_id"], MODEL,
                    row["scores"].get("people_centrism"),
                    row["scores"].get("anti_elitism"),
                    row["scores"].get("moral_dichotomy"),
                    row["scores"].get("popular_sovereignty"),
                    row["scores"].get("exclusionary_rhetoric"),
                    row["scores"].get("crisis_rhetoric"),
                    row["scores"].get("final_score"), 1,
                    json.dumps(row, ensure_ascii=False),
                    PROMPT_ID, PROVIDER, RUN_ID,
                )
                for row in valid
            ],
        )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()


def write_rows(rows: dict[str, dict]) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as handle:
        for discourse_id in sorted(rows):
            handle.write(json.dumps(rows[discourse_id], ensure_ascii=False) + "\n")


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"completed_batches": [], "in_flight": [], "failed_ids": []}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def submit_batch(docs: list[dict], prompt: str, key: str, batch_index: int) -> dict:
    requests = [make_request(doc, prompt) for doc in docs]
    lines = ("\n".join(json.dumps(item, ensure_ascii=False) for item in requests) + "\n").encode("utf-8")
    estimated = sum(estimate_tokens(prompt, doc["text"]) for doc in docs)
    uploaded = upload_jsonl(lines, key, f"popin_luna_v4_{batch_index:04d}.jsonl")
    file_id = uploaded.get("id")
    if not file_id:
        raise RuntimeError(f"Upload sem file_id: {uploaded}")
    batch = api_json(
        f"{API_BASE}/batches", key, "POST",
        {
            "input_file_id": file_id,
            "endpoint": "/v1/chat/completions",
            "completion_window": "24h",
            "metadata": {
                "project": "popin", "run_id": RUN_ID,
                "batch_index": str(batch_index),
            },
        },
    )
    batch_id = batch.get("id")
    if not batch_id:
        raise RuntimeError(f"Batch sem id: {batch}")
    print(json.dumps({
        "event": "submitted", "batch_index": batch_index, "batch_id": batch_id,
        "file_id": file_id, "requests": len(docs),
        "estimated_tokens": estimated, "status": batch.get("status"),
    }, ensure_ascii=False), flush=True)
    return {
        "batch_index": batch_index, "batch_id": batch_id, "file_id": file_id,
        "doc_ids": [str(doc["discourse_id"]) for doc in docs],
        "estimated_tokens": estimated, "submitted_at": time.time(),
    }


def recover_or_wait(active: dict, docs_by_id: dict[str, dict], rows: dict[str, dict], state: dict, key: str) -> bool:
    batch_id = active["batch_id"]
    batch = api_json(f"{API_BASE}/batches/{batch_id}", key)
    print(json.dumps({
        "event": "status", "batch_index": active["batch_index"],
        "batch_id": batch_id, "status": batch.get("status"),
        "request_counts": batch.get("request_counts"),
    }, ensure_ascii=False), flush=True)
    if batch.get("status") not in TERMINAL:
        return False

    new_rows: list[dict] = []
    if batch.get("output_file_id"):
        for line in download_file(batch["output_file_id"], key).decode("utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            custom_id = str(item.get("custom_id"))
            doc = docs_by_id.get(custom_id)
            if doc:
                new_rows.append(build_result(item, doc, batch_id))
    returned = {str(row["discourse_id"]) for row in new_rows}
    failed_ids = [doc_id for doc_id in active["doc_ids"] if doc_id not in returned or not next((r.get("scores") for r in new_rows if str(r["discourse_id"]) == doc_id), None)]
    for row in new_rows:
        if row.get("scores"):
            rows[str(row["discourse_id"])] = row
    import_rows(new_rows)
    state["completed_batches"].append({
        "batch_index": active["batch_index"], "batch_id": batch_id,
        "status": batch.get("status"), "requests": len(active["doc_ids"]),
        "returned": len(new_rows), "valid": len([r for r in new_rows if r.get("scores")]),
        "failed_ids": failed_ids, "request_counts": batch.get("request_counts"),
        "usage": batch.get("usage"),
        "elapsed_s": round(time.time() - active["submitted_at"], 3),
    })
    state["in_flight"] = [item for item in state["in_flight"] if item["batch_id"] != batch_id]
    state["failed_ids"] = sorted(set(state.get("failed_ids", [])) | set(failed_ids))
    save_state(state)
    write_rows(rows)
    print(json.dumps({
        "event": "materialized", "batch_index": active["batch_index"],
        "batch_id": batch_id, "status": batch.get("status"),
        "returned": len(new_rows), "valid": len([r for r in new_rows if r.get("scores")]),
        "failed": len(failed_ids), "total_saved": len(rows),
    }, ensure_ascii=False), flush=True)
    return True


def main() -> None:
    load_local_env()
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY não definido; nenhum batch foi enviado")
    prompt = load_prompt()
    state = load_state()
    rows = load_seed_rows()
    if OUT_PATH.exists():
        for line in OUT_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if row.get("scores"):
                    rows[str(row["discourse_id"])] = row
    write_rows(rows)
    print(json.dumps({
        "event": "start", "model": MODEL, "prompt_id": PROMPT_ID,
        "scope": "dtype <> INVALID", "seeded_valid": len(rows),
        "target_batch_tokens": TARGET_BATCH_TOKENS,
        "max_in_flight_tokens": MAX_IN_FLIGHT_TOKENS,
        "max_in_flight_batches": MAX_IN_FLIGHT_BATCHES,
    }, ensure_ascii=False), flush=True)

    # O mesmo processo importa resultados durante a leitura; manter a
    # conexão em modo read-write evita conflito de configuração do DuckDB.
    con = duckdb.connect(str(DB_PATH))
    cursor = con.execute(
        """
        SELECT id, iso3, leader_name, filename, discourse_date,
               discourse_year, word_count, dtype, discourse
        FROM discourses
        WHERE dtype <> 'INVALID'
        ORDER BY id
        """
    )
    docs_by_id: dict[str, dict] = {}
    active = list(state.get("in_flight", []))
    # Batches cancelados antes da validação podem permanecer em
    # ``cancelling`` por vários minutos, embora já não tenham requisições
    # enfileiradas. Eles não têm resultado a recuperar e não devem bloquear a
    # retomada do restante da fila.
    still_cancelling = []
    kept_active = []
    for item in active:
        batch = api_json(f"{API_BASE}/batches/{item['batch_id']}", key)
        counts = batch.get("request_counts") or {}
        if (
            batch.get("status") == "cancelling"
            and counts.get("total", 0) == 0
            and counts.get("completed", 0) == 0
        ):
            still_cancelling.append(item["batch_id"])
        else:
            kept_active.append(item)
    if still_cancelling:
        print(json.dumps({"event": "skip_cancel_pending", "batch_ids": still_cancelling}, ensure_ascii=False), flush=True)
        state["in_flight"] = kept_active
        save_state(state)
    active = kept_active
    for item in active:
        for doc_id in item["doc_ids"]:
            docs_by_id.setdefault(doc_id, {"discourse_id": doc_id})

    # Reconstrói os documentos dos batches em voo antes de continuar a fila.
    if active:
        pending_rows = []
        while len(pending_rows) < 1000:
            chunk = cursor.fetchmany(1000)
            if not chunk:
                break
            pending_rows.extend(chunk)
            for raw in chunk:
                doc = doc_from_row(raw)
                docs_by_id[str(doc["discourse_id"])] = doc
        # Se necessário, completa a leitura apenas para recuperar IDs raros.
        if any(docs_by_id.get(doc_id, {}).get("text") is None for item in active for doc_id in item["doc_ids"]):
            for raw in cursor.fetchall():
                doc = doc_from_row(raw)
                docs_by_id[str(doc["discourse_id"])] = doc
    for item in list(active):
        while not recover_or_wait(item, docs_by_id, rows, state, key):
            time.sleep(POLL_SECONDS)
        active = [other for other in active if other["batch_id"] != item["batch_id"]]

    # Retoma o cursor do início: os batches em voo são excepcionais e a
    # seleção por completed_ids torna a passagem barata e idempotente.
    con.close()
    con = duckdb.connect(str(DB_PATH))
    cursor = con.execute(
        """
        SELECT id, iso3, leader_name, filename, discourse_date,
               discourse_year, word_count, dtype, discourse
        FROM discourses
        WHERE dtype <> 'INVALID'
        ORDER BY id
        """
    )
    next_index = 1 + max([int(x.get("batch_index", 0)) for x in state.get("completed_batches", [])] + [0])
    current: list[dict] = []
    current_tokens = 0

    def wait_for_one() -> None:
        nonlocal active
        while active:
            changed = False
            for item in list(active):
                if recover_or_wait(item, docs_by_id, rows, state, key):
                    active.remove(item)
                    changed = True
                    break
            if changed:
                return
            time.sleep(POLL_SECONDS)

    def release_current() -> None:
        nonlocal current, current_tokens, next_index, active
        if not current:
            return
        while len(active) >= MAX_IN_FLIGHT_BATCHES:
            wait_for_one()
        for doc in current:
            docs_by_id[str(doc["discourse_id"])] = doc
        item = submit_batch(current, prompt, key, next_index)
        active.append(item)
        state["in_flight"] = active
        save_state(state)
        next_index += 1
        current = []
        current_tokens = 0

    for raw in cursor.fetchall():
        doc = doc_from_row(raw)
        doc_id = str(doc["discourse_id"])
        if doc_id in rows:
            continue
        docs_by_id[doc_id] = doc
        estimate = estimate_tokens(prompt, doc["text"])
        if current and current_tokens + estimate > TARGET_BATCH_TOKENS:
            release_current()
        current.append(doc)
        current_tokens += estimate
    release_current()
    while active:
        wait_for_one()
    con.close()

    total_docs = 0
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        total_docs = con.execute("SELECT count(*) FROM discourses WHERE dtype <> 'INVALID'").fetchone()[0]
        db_count = con.execute("SELECT count(*) FROM scores WHERE model_id = ? AND prompt_id = ?", [MODEL, PROMPT_ID]).fetchone()[0]
    finally:
        con.close()
    meta = {
        "model": MODEL, "prompt_id": PROMPT_ID, "provider": PROVIDER,
        "scope": "dtype <> INVALID", "total_noninvalid": total_docs,
        "saved_valid_jsonl": len(rows), "db_scores": db_count,
        "completed_batches": len(state.get("completed_batches", [])),
        "failed_ids": len(state.get("failed_ids", [])),
        "target_batch_tokens": TARGET_BATCH_TOKENS,
        "max_in_flight_tokens": MAX_IN_FLIGHT_TOKENS,
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"event": "finished", **meta}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
