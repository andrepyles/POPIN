#!/usr/bin/env python3
"""Arquiva execuções históricas de scoring sem sobrescrever ``scores``.

O ``scores`` principal tem chave (discourse_id, model_id), portanto não pode
acomodar duas versões do prompt para o mesmo discurso. Esta camada preserva
cada arquivo/execução, inclusive respostas com erro, e cria visões para
navegação e auditoria.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "popin.duckdb"
DATA_ROOT = ROOT / "data/gpd_v2_1_20251120"
DIMS = (
    "people_centrism",
    "anti_elitism",
    "moral_dichotomy",
    "popular_sovereignty",
    "exclusionary_rhetoric",
    "crisis_rhetoric",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def as_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def as_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def discover_files() -> list[Path]:
    """Descobre agregados históricos e exclui requests/outputs intermediários."""
    candidates = sorted(DATA_ROOT.joinpath("sensitivity_runs").rglob("*.jsonl"))
    candidates += sorted(DATA_ROOT.joinpath("pilot_runs").rglob("*.jsonl"))
    result: list[Path] = []
    for path in candidates:
        rel = path.relative_to(DATA_ROOT).as_posix()
        name = path.name
        if name.endswith("_input.jsonl") or name.endswith(".output.jsonl"):
            continue
        if "/batches/" in f"/{rel}" or name.startswith("batch_"):
            continue
        result.append(path)
    return result


def read_rows(path: Path) -> tuple[list[dict[str, Any]], str | None]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    return [], f"linha {line_number} não é objeto JSON"
                rows.append(row)
    except Exception as exc:  # arquivo inválido fica no manifesto
        return [], f"{type(exc).__name__}: {exc}"
    return rows, None


def source_kind(rel: str) -> str:
    if rel.startswith("sensitivity_runs/"):
        return "prompt_sensitivity"
    if "stage2_10" in rel:
        return "stage2_pilot"
    return "model_pilot"


def execution_id(rel: str, file_hash: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(rel).stem)
    return f"history_{file_hash[:12]}_{stem}"


def classify_skip(rel: str, file_hash: str) -> str | None:
    # Estes agregados já estão no scores principal. O manifesto preserva a
    # origem/hash para não importar uma segunda cópia dos mesmos resultados.
    if rel in {
        "pilot_runs/glm_4.7_flash__sample_1000__v4.jsonl",
        "pilot_runs/luna_chunked_sample1000_results/luna_chunked_sample1000_v4.jsonl",
    }:
        return "already_in_scores_main"
    # A validação GLM foi copiada para uma pasta de validação, mas o conteúdo
    # é byte-a-byte duplicado do arquivo acima.
    if rel.startswith("pilot_runs/glm_validation__sample_1000__v4/"):
        return "duplicate_artifact_of_main_glm"
    return None


def infer_chunked(rows: list[dict[str, Any]], rel: str) -> bool:
    if "chunked" in rel.lower():
        return True
    for row in rows[:25]:
        if row.get("chunk_scores") is not None:
            return True
        n_chunks = as_int(row.get("n_chunks"))
        if n_chunks is not None and n_chunks > 1:
            return True
    return False


def infer_run_id(rows: list[dict[str, Any]], rel: str) -> str:
    values = {str(row["run_id"]) for row in rows if row.get("run_id")}
    if len(values) == 1:
        return next(iter(values))
    return Path(rel).stem


def model_label(model_id: str | None) -> str:
    labels = {
        "qwen/qwen3-30b-a3b-instruct-2507": "Qwen3 30B A3B Instruct 2507",
        "Qwen/Qwen3-30B-A3B-Instruct-2507": "Qwen3 30B A3B Instruct 2507",
        "deepseek/deepseek-v4-flash-0731": "DeepSeek V4 Flash 0731",
        "openai/gpt-5.6-luna": "GPT-5.6 Luna",
        "z-ai/glm-4.7-flash": "GLM 4.7 Flash",
    }
    return labels.get(model_id or "", model_id or "desconhecido")


def create_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS score_history (
            history_id VARCHAR PRIMARY KEY,
            execution_id VARCHAR NOT NULL,
            source_file VARCHAR NOT NULL,
            source_sha256 VARCHAR NOT NULL,
            source_row INTEGER NOT NULL,
            source_kind VARCHAR NOT NULL,
            discourse_id VARCHAR,
            iso3 VARCHAR,
            leader_name VARCHAR,
            discourse_date DATE,
            discourse_year INTEGER,
            model_id VARCHAR,
            model_label VARCHAR,
            prompt_id VARCHAR,
            provider VARCHAR,
            run_id VARCHAR,
            chunked BOOLEAN,
            n_chunks INTEGER,
            valid_chunks INTEGER,
            word_count INTEGER,
            people_centrism FLOAT,
            anti_elitism FLOAT,
            moral_dichotomy FLOAT,
            popular_sovereignty FLOAT,
            exclusionary_rhetoric FLOAT,
            crisis_rhetoric FLOAT,
            final_score FLOAT,
            cost_usd DOUBLE,
            has_error BOOLEAN,
            error_text VARCHAR,
            raw_json VARCHAR,
            imported_at TIMESTAMP DEFAULT now()
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS score_history_runs (
            execution_id VARCHAR PRIMARY KEY,
            source_file VARCHAR NOT NULL,
            source_sha256 VARCHAR NOT NULL,
            source_kind VARCHAR NOT NULL,
            model_id VARCHAR,
            model_label VARCHAR,
            prompt_id VARCHAR,
            provider VARCHAR,
            run_id VARCHAR,
            chunked BOOLEAN,
            source_rows INTEGER,
            imported_rows INTEGER,
            unique_discourses INTEGER,
            rows_with_scores INTEGER,
            rows_with_errors INTEGER,
            coverage VARCHAR,
            notes VARCHAR,
            imported_at TIMESTAMP DEFAULT now()
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS score_history_manifest (
            source_file VARCHAR PRIMARY KEY,
            source_sha256 VARCHAR NOT NULL,
            source_kind VARCHAR NOT NULL,
            status VARCHAR NOT NULL,
            reason VARCHAR,
            source_rows INTEGER,
            imported_rows INTEGER,
            unique_discourses INTEGER,
            source_bytes BIGINT,
            processed_at TIMESTAMP DEFAULT now()
        )
    """)


def history_row(
    row: dict[str, Any],
    *,
    execution: str,
    source_file: str,
    file_hash: str,
    source_row: int,
    kind: str,
    is_chunked: bool,
) -> tuple[Any, ...]:
    score = row.get("scores") or {}
    errors = row.get("errors")
    if errors is None:
        errors = row.get("error")
    has_error = bool(errors) or score.get("final_score") is None
    discourse_date = row.get("discourse_date")
    if isinstance(discourse_date, str) and len(discourse_date) == 10:
        discourse_date = discourse_date
    raw = json.dumps(row, ensure_ascii=False, sort_keys=True)
    identity = f"{source_file}\n{file_hash}\n{source_row}\n{row.get('discourse_id')}"
    history_id = hashlib.sha256(identity.encode()).hexdigest()
    model_id = row.get("model")
    return (
        history_id,
        execution,
        source_file,
        file_hash,
        source_row,
        kind,
        row.get("discourse_id"),
        row.get("iso3"),
        row.get("leader_name"),
        discourse_date,
        as_int(row.get("discourse_year")),
        model_id,
        model_label(model_id),
        row.get("prompt_id"),
        row.get("provider"),
        row.get("run_id") or Path(source_file).stem,
        is_chunked,
        as_int(row.get("n_chunks")),
        as_int(row.get("valid_chunks") or row.get("n_valid_chunks")),
        as_int(row.get("word_count")),
        *[as_float(score.get(dim)) for dim in DIMS],
        as_float(score.get("final_score")),
        as_float(row.get("cost_usd")),
        has_error,
        json_text(errors),
        raw,
    )


def main() -> None:
    files = discover_files()
    con = duckdb.connect(str(DB_PATH))
    try:
        create_schema(con)
        con.execute("BEGIN TRANSACTION")
        insert_history = """
            INSERT INTO score_history (
                history_id, execution_id, source_file, source_sha256, source_row,
                source_kind, discourse_id, iso3, leader_name, discourse_date,
                discourse_year, model_id, model_label, prompt_id, provider,
                run_id, chunked, n_chunks, valid_chunks, word_count,
                people_centrism, anti_elitism, moral_dichotomy,
                popular_sovereignty, exclusionary_rhetoric, crisis_rhetoric,
                final_score, cost_usd, has_error, error_text, raw_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT (history_id) DO NOTHING
        """
        insert_run = """
            INSERT INTO score_history_runs (
                execution_id, source_file, source_sha256, source_kind, model_id,
                model_label, prompt_id, provider, run_id, chunked, source_rows,
                imported_rows, unique_discourses, rows_with_scores,
                rows_with_errors, coverage, notes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT (execution_id) DO UPDATE SET
                source_file=excluded.source_file, source_sha256=excluded.source_sha256,
                source_rows=excluded.source_rows, imported_rows=excluded.imported_rows,
                unique_discourses=excluded.unique_discourses,
                rows_with_scores=excluded.rows_with_scores,
                rows_with_errors=excluded.rows_with_errors,
                notes=excluded.notes, imported_at=now()
        """
        insert_manifest = """
            INSERT INTO score_history_manifest (
                source_file, source_sha256, source_kind, status, reason,
                source_rows, imported_rows, unique_discourses, source_bytes
            ) VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT (source_file) DO UPDATE SET
                source_sha256=excluded.source_sha256, status=excluded.status,
                reason=excluded.reason, source_rows=excluded.source_rows,
                imported_rows=excluded.imported_rows,
                unique_discourses=excluded.unique_discourses,
                source_bytes=excluded.source_bytes, processed_at=now()
        """
        imported_files = 0
        imported_rows = 0
        manifest_rows = []
        for path in files:
            rel = path.relative_to(DATA_ROOT).as_posix()
            file_hash = sha256_file(path)
            rows, read_error = read_rows(path)
            kind = source_kind(rel)
            unique_ids = {row.get("discourse_id") for row in rows}
            unique_ids.discard(None)
            skip = classify_skip(rel, file_hash)
            if read_error:
                status, reason = "rejected_invalid_json", read_error
            elif len(unique_ids) != len(rows):
                status = "rejected_duplicate_discourse_ids"
                reason = f"{len(rows) - len(unique_ids)} linhas duplicadas por discourse_id"
            elif skip:
                status, reason = "already_represented", skip
            else:
                status, reason = "imported", None
                exec_id = execution_id(rel, file_hash)
                chunked = infer_chunked(rows, rel)
                run_id = infer_run_id(rows, rel)
                values = [history_row(
                    row, execution=exec_id, source_file=rel, file_hash=file_hash,
                    source_row=index, kind=kind, is_chunked=chunked,
                ) for index, row in enumerate(rows, start=1)]
                con.executemany(insert_history, values)
                first = rows[0] if rows else {}
                model_id = first.get("model")
                prompt_ids = {str(row.get("prompt_id")) for row in rows if row.get("prompt_id")}
                providers = {str(row.get("provider")) for row in rows if row.get("provider")}
                scores_n = sum(1 for row in rows if (row.get("scores") or {}).get("final_score") is not None)
                errors_n = sum(1 for row in rows if row.get("errors") or row.get("error") or not row.get("scores"))
                coverage = "sample_1000" if len(rows) == 1000 else ("sample_900" if len(rows) == 900 else "pilot")
                notes = "; ".join([
                    f"prompt_ids={','.join(sorted(prompt_ids)) or 'missing'}",
                    f"providers={','.join(sorted(providers)) or 'missing'}",
                ])
                con.execute(insert_run, [
                    exec_id, rel, file_hash, kind, model_id, model_label(model_id),
                    next(iter(prompt_ids), None), next(iter(providers), None), run_id,
                    chunked, len(rows), len(values), len(unique_ids), scores_n,
                    errors_n, coverage, notes,
                ])
                imported_files += 1
                imported_rows += len(values)
            manifest_rows.append((
                rel, file_hash, kind, status, reason, len(rows),
                len(rows) if status == "imported" else 0, len(unique_ids), path.stat().st_size,
            ))
        con.executemany(insert_manifest, manifest_rows)

        con.execute("""
            CREATE OR REPLACE VIEW v_history_navigable AS
            SELECT
                h.history_id, h.execution_id, h.source_file, h.source_kind,
                h.discourse_id, d.iso3, d.leader_name, d.filename,
                d.discourse_date, d.discourse_year, d.dtype,
                h.model_id, h.model_label, h.prompt_id, h.provider, h.run_id,
                h.chunked, h.n_chunks, h.valid_chunks, h.word_count,
                h.people_centrism, h.anti_elitism, h.moral_dichotomy,
                h.popular_sovereignty, h.exclusionary_rhetoric,
                h.crisis_rhetoric, h.final_score, h.cost_usd, h.has_error,
                h.error_text, h.imported_at
            FROM score_history h
            LEFT JOIN discourses d ON d.id = h.discourse_id
        """)
        con.execute("""
            CREATE OR REPLACE VIEW v_history_run_summary AS
            SELECT
                r.execution_id, r.source_file, r.source_kind, r.model_id,
                r.model_label, r.prompt_id, r.provider, r.run_id, r.chunked,
                r.source_rows, r.imported_rows, r.unique_discourses,
                r.rows_with_scores, r.rows_with_errors, r.coverage,
                avg(h.final_score) AS mean_score,
                stddev_samp(h.final_score) AS sd_score
            FROM score_history_runs r
            LEFT JOIN score_history h USING (execution_id)
            GROUP BY ALL
        """)
        con.execute("""
            CREATE OR REPLACE VIEW v_all_scores_navigable AS
            SELECT
                'main' AS source_layer, discourse_id, iso3, leader_name, filename,
                discourse_date, discourse_year, dtype, execution_id, model_label,
                model_family, model_version, run_scope, coverage, chunked,
                chunk_words, overlap_words, prompt_id, provider, run_id, n_chunks,
                people_centrism, anti_elitism, moral_dichotomy,
                popular_sovereignty, exclusionary_rhetoric, crisis_rhetoric,
                final_score, scored_at, NULL::VARCHAR AS source_file,
                NULL::VARCHAR AS source_kind, NULL::BOOLEAN AS has_error
            FROM v_scores_navigable
            UNION ALL
            SELECT
                'history' AS source_layer, discourse_id, iso3, leader_name, filename,
                discourse_date, discourse_year, dtype, execution_id, model_label,
                NULL::VARCHAR AS model_family, NULL::VARCHAR AS model_version,
                'historical' AS run_scope, NULL::VARCHAR AS coverage, chunked,
                NULL::INTEGER AS chunk_words, NULL::INTEGER AS overlap_words,
                prompt_id, provider, run_id, n_chunks, people_centrism,
                anti_elitism, moral_dichotomy, popular_sovereignty,
                exclusionary_rhetoric, crisis_rhetoric, final_score,
                imported_at AS scored_at, source_file, source_kind, has_error
            FROM v_history_navigable
        """)
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        print(con.execute("SELECT status, count(*) FROM score_history_manifest GROUP BY 1 ORDER BY 1").fetchall())
        print(con.execute("SELECT count(*), count(DISTINCT discourse_id), count(DISTINCT execution_id) FROM score_history").fetchone())
        print(con.execute("SELECT model_label, prompt_id, chunked, count(*) FROM score_history GROUP BY ALL ORDER BY 1,2,3").fetchall())
        con.close()
    print(f"Arquivos importados: {imported_files}; linhas históricas: {imported_rows}")


if __name__ == "__main__":
    main()
