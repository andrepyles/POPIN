"""
POPIN v4 — Step 3: Classificação do tipo de discurso via LLM

Classifica cada discurso sem dtype definido em uma das categorias:
  SPEECH | COMMUNIQUE | INTERVIEW | PRESS_RELEASE | DECREE | LETTER | INVALID

O LLM recebe apenas os primeiros 500 caracteres do discurso.
Usa requisições concorrentes para saturar o vLLM e maximizar throughput.

Uso:
    python 03_classify.py
    python 03_classify.py --resume          # retoma job interrompido
    python 03_classify.py --limit 100       # teste com N discursos
    python 03_classify.py --concurrency 32  # ajusta paralelismo (padrão: 24)
"""

import argparse
import asyncio
import json
import os
import uuid

import duckdb
from dotenv import load_dotenv
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm

load_dotenv()
DB_PATH        = os.getenv("DB_PATH", "./popin.duckdb")
VLLM_BASE_URL  = os.getenv("VLLM_BASE_URL", "http://localhost:8080/v1")
VLLM_API_KEY   = os.getenv("VLLM_API_KEY", "vx")
VLLM_MODEL     = os.getenv("VLLM_MODEL", "Qwen/Qwen3-30B-A3B-Instruct-2507")

CHECKPOINT_EVERY = 200   # salva progresso a cada N discursos
PREVIEW_CHARS    = 500
VALID_TYPES      = {"SPEECH", "COMMUNIQUE", "INTERVIEW", "PRESS_RELEASE", "DECREE", "LETTER", "INVALID"}


# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a political science researcher classifying political texts.
Given the beginning of a political document, return ONLY a JSON object with:
  - "dtype": one of SPEECH, COMMUNIQUE, INTERVIEW, PRESS_RELEASE, DECREE, LETTER, INVALID
  - "reason": one short sentence explaining the classification (in English)

Definitions:
- SPEECH: oral address by a political leader to an audience
- COMMUNIQUE: official joint or governmental statement/declaration
- INTERVIEW: question-and-answer format with a journalist or host
- PRESS_RELEASE: brief official announcement for media
- DECREE: executive order or legal/administrative ruling
- LETTER: written correspondence addressed to a specific person or entity
- INVALID: too short, garbled, or impossible to classify

Respond ONLY with valid JSON, no extra text."""

def build_user_prompt(text: str) -> str:
    return f"Classify this political document:\n\n{text[:PREVIEW_CHARS].strip()}"


# ── LLM call (async) ──────────────────────────────────────────────────────────

async def classify_one(client: AsyncOpenAI, semaphore: asyncio.Semaphore,
                       doc_id: str, text: str, retries: int = 3) -> tuple[str, str, str]:
    """Retorna (doc_id, dtype, reason)."""
    async with semaphore:
        for attempt in range(retries):
            try:
                resp = await client.chat.completions.create(
                    model=VLLM_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": build_user_prompt(text)},
                    ],
                    temperature=0.0,
                    max_tokens=100,
                    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
                )
                raw = resp.choices[0].message.content.strip()

                # Remove blocos markdown se o modelo incluir ```json ... ```
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                    raw = raw.strip()

                data  = json.loads(raw)
                dtype = str(data.get("dtype", "")).upper().strip()
                reason = str(data.get("reason", "")).strip()

                if dtype not in VALID_TYPES:
                    dtype  = "INVALID"
                    reason = f"LLM returned unknown type: {dtype!r}"

                return doc_id, dtype, reason

            except Exception as exc:
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return doc_id, "INVALID", f"Error after {retries} attempts: {exc}"


# ── Jobs ──────────────────────────────────────────────────────────────────────

def get_or_create_job(con, total_rows: int, resume: bool) -> tuple[str, str | None]:
    """Retorna (job_id, last_id_processed).

    O resume é automático: basta rodar sem --resume que a query
    WHERE dtype IS NULL já devolve apenas o que falta processar.
    O job em aberto é retomado se existir, senão cria um novo.
    """
    if resume:
        row = con.execute("""
            SELECT job_id FROM jobs
            WHERE job_type = 'classify' AND status = 'running'
            ORDER BY started_at DESC LIMIT 1
        """).fetchone()
        if row:
            print(f"Retomando job {row[0]}")
            return row[0]
        print("Nenhum job interrompido encontrado. Iniciando novo.")

    job_id = str(uuid.uuid4())[:8]
    con.execute(
        "INSERT INTO jobs (job_id, job_type, total_rows, model_id) VALUES (?, 'classify', ?, ?)",
        [job_id, total_rows, VLLM_MODEL]
    )
    con.commit()
    return job_id

def checkpoint(con, job_id: str, processed: int):
    con.execute(
        "UPDATE jobs SET last_row = ?, updated_at = now() WHERE job_id = ?",
        [processed, job_id]
    )
    con.commit()

def finish_job(con, job_id: str):
    con.execute(
        "UPDATE jobs SET status = 'done', updated_at = now() WHERE job_id = ?",
        [job_id]
    )
    con.commit()


# ── Main ──────────────────────────────────────────────────────────────────────

async def classify(resume: bool, limit: int | None, concurrency: int):
    con = duckdb.connect(DB_PATH)

    query = "SELECT id, discourse FROM discourses WHERE dtype IS NULL ORDER BY id"
    if limit:
        query += f" LIMIT {limit}"

    rows = con.execute(query).fetchall()
    total = len(rows)
    print(f"Discursos a classificar: {total:,} | concorrência: {concurrency}\n")

    if total == 0:
        print("Nada a fazer.")
        con.close()
        return

    job_id = get_or_create_job(con, total, resume)

    client    = AsyncOpenAI(base_url=VLLM_BASE_URL, api_key=VLLM_API_KEY,
                           timeout=60.0)
    semaphore = asyncio.Semaphore(concurrency)
    stats     = {"ok": 0, "invalid": 0}
    processed = 0

    # Processa em lotes para poder fazer checkpoint periódico
    pbar = tqdm(total=total, desc="Classificando")

    for batch_start in range(0, len(rows), CHECKPOINT_EVERY):
        batch = rows[batch_start : batch_start + CHECKPOINT_EVERY]

        tasks   = [classify_one(client, semaphore, doc_id, discourse)
                   for doc_id, discourse in batch]
        results = await asyncio.gather(*tasks)

        # Grava resultados em lote
        for doc_id, dtype, _ in results:
            con.execute("UPDATE discourses SET dtype = ? WHERE id = ?", [dtype, doc_id])
            if dtype == "INVALID":
                stats["invalid"] += 1
            else:
                stats["ok"] += 1

        processed += len(batch)
        con.commit()
        checkpoint(con, job_id, processed)
        pbar.update(len(batch))

    pbar.close()
    finish_job(con, job_id)
    con.close()

    print(f"\nConcluído — job: {job_id}")
    print(f"  classificados:  {stats['ok']:,}")
    print(f"  INVALID:        {stats['invalid']:,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume",      action="store_true", help="Retoma job interrompido")
    parser.add_argument("--limit",       type=int, default=None, help="Classifica apenas N discursos")
    parser.add_argument("--concurrency", type=int, default=24,   help="Requisições simultâneas (padrão: 24)")
    args = parser.parse_args()
    asyncio.run(classify(resume=args.resume, limit=args.limit, concurrency=args.concurrency))
