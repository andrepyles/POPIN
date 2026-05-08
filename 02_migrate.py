"""
POPIN v4 — Step 2: Migração do parquet histórico para DuckDB

Deduplicação em dois níveis (rejeita sem inserir):
  1. Exata:    SHA-256 do texto normalizado → id já existe no banco
  2. Filename: mesmo arquivo .txt já foi carregado anteriormente

Uso:
    python 02_migrate.py
    python 02_migrate.py --resume   # retoma carga interrompida
"""

import argparse
import hashlib
import os
import re
import unicodedata
import uuid

import duckdb
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
DB_PATH      = os.getenv("DB_PATH", "./popin.duckdb")
PARQUET_PATH = os.getenv("PARQUET_PATH", "../DiscourseDB/DiscourseDB_v1.0.parquet")
BATCH_SIZE   = 500


# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    return re.sub(r"\s+", " ", text).strip()

def make_id(text: str) -> str:
    return hashlib.sha256(normalize(text).encode()).hexdigest()[:16]

def parse_date(raw) -> str | None:
    if not raw or pd.isna(raw):
        return None
    try:
        return pd.to_datetime(str(raw).strip()).date().isoformat()
    except Exception:
        return None

def clean(val) -> str | None:
    """Converte NaN, 'nan', vazio e None para NULL."""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except Exception:
        pass
    s = str(val).strip()
    return None if s.lower() in ("nan", "none", "n/a", "") else s


# ── Jobs ──────────────────────────────────────────────────────────────────────

def get_or_create_job(con, total_rows: int, resume: bool) -> tuple[str, int]:
    if resume:
        row = con.execute("""
            SELECT job_id, last_row FROM jobs
            WHERE job_type = 'migrate' AND status = 'running'
            ORDER BY started_at DESC LIMIT 1
        """).fetchone()
        if row:
            print(f"Retomando job {row[0]} — linha {row[1]:,}")
            return row[0], row[1]
        print("Nenhum job interrompido encontrado. Iniciando novo.")

    job_id = str(uuid.uuid4())[:8]
    con.execute(
        "INSERT INTO jobs (job_id, job_type, total_rows) VALUES (?, 'migrate', ?)",
        [job_id, total_rows]
    )
    con.commit()
    return job_id, 0

def update_job(con, job_id: str, last_row: int):
    con.execute(
        "UPDATE jobs SET last_row = ?, updated_at = now() WHERE job_id = ?",
        [last_row, job_id]
    )
    con.commit()

def finish_job(con, job_id: str):
    con.execute(
        "UPDATE jobs SET status = 'done', updated_at = now() WHERE job_id = ?",
        [job_id]
    )
    con.commit()


# ── Migração ──────────────────────────────────────────────────────────────────

def migrate(resume: bool = False):
    print(f"Lendo: {PARQUET_PATH}")
    df = pd.read_parquet(PARQUET_PATH)
    total = len(df)
    print(f"  {total:,} registros\n")

    con = duckdb.connect(DB_PATH)
    job_id, start_row = get_or_create_job(con, total, resume)

    stats = {"inseridos": 0, "skip_hash": 0, "skip_filename": 0, "skip_curto": 0}

    for batch_start in tqdm(range(start_row, total, BATCH_SIZE), desc="Migrando"):
        batch = df.iloc[batch_start : batch_start + BATCH_SIZE]

        for _, row in batch.iterrows():
            text = str(row.get("DISCOURSE") or "").strip()

            # Descarta textos muito curtos (menos de 20 palavras)
            if len(text.split()) < 20:
                stats["skip_curto"] += 1
                continue

            filename = str(row.get("FILENAME") or "").strip() or None

            # Dedup por filename — mesmo arquivo já carregado
            if filename:
                exists = con.execute(
                    "SELECT 1 FROM discourses WHERE filename = ?", [filename]
                ).fetchone()
                if exists:
                    stats["skip_filename"] += 1
                    continue

            # Dedup por hash — texto idêntico com outro nome
            doc_id = make_id(text)
            exists = con.execute(
                "SELECT 1 FROM discourses WHERE id = ?", [doc_id]
            ).fetchone()
            if exists:
                stats["skip_hash"] += 1
                continue

            con.execute("""
                INSERT INTO discourses
                    (id, iso3, leader_name, filename, language,
                     discourse_place, discourse_date, discourse_year,
                     source, discourse, word_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                doc_id,
                clean(row.get("ISO3")),
                clean(row.get("LEADER_NAME")),
                filename,
                clean(row.get("LANGUAGE")),
                clean(row.get("DISCOURSE_PLACE")),
                parse_date(row.get("DISCOURSE_DATE")),
                int(row["DISCOURSE_YEAR"]),
                clean(row.get("SOURCE")),
                text,
                len(text.split()),
            ])
            stats["inseridos"] += 1

        con.commit()
        update_job(con, job_id, batch_start + len(batch))

    finish_job(con, job_id)
    con.close()

    print(f"\nConcluído — job: {job_id}")
    print(f"  inseridos:      {stats['inseridos']:,}")
    print(f"  skip (hash):    {stats['skip_hash']:,}")
    print(f"  skip (file):    {stats['skip_filename']:,}")
    print(f"  skip (curto):   {stats['skip_curto']:,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="Retoma carga interrompida")
    args = parser.parse_args()
    migrate(resume=args.resume)
