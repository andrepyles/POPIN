"""Carrega apenas fontes cruas do GPD e do LALLPI no DuckDB.

As colunas originais são mantidas como texto para evitar qualquer conversão
irreversível. As tabelas recebem somente três metadados de ingestão:
``_source_file``, ``_source_sha256`` e ``_row_number``.

Nenhum crosswalk, média, amostra, validação ou outra tabela derivada é criada.
"""

from __future__ import annotations

import csv
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(__import__("os").environ.get("DB_PATH", ROOT / "popin.duckdb"))


SOURCES = [
    (
        "raw_gpd_long",
        ROOT / "data/gpd_v2_1_20251120/GPD_v2.1_20251120.csv",
        "gpd_v2.1_20251120",
    ),
    (
        "raw_gpd_wide",
        ROOT / "data/gpd_v2_1_20251120/GPD_v2.1_20251120_Wide.csv",
        "gpd_v2.1_20251120",
    ),
    (
        "raw_lallpi_index",
        ROOT / "data/lallpi_2025/index_2025.csv",
        "lallpi_v2025.1",
    ),
]


def read_csv_preserving_values(path: Path) -> tuple[list[str], list[list[str]], str]:
    """Lê o CSV sem converter valores; tenta UTF-8 e depois Latin-1."""
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:  # pragma: no cover - Latin-1 sempre decodifica bytes válidos
        raise UnicodeDecodeError("unknown", raw, 0, len(raw), "encoding inválido")

    reader = csv.reader(text.splitlines())
    header = next(reader)
    rows = [row for row in reader]
    if any(len(row) != len(header) for row in rows):
        bad = next(i for i, row in enumerate(rows, start=2) if len(row) != len(header))
        raise ValueError(f"linha irregular em {path}: {bad}")
    return header, rows, hashlib.sha256(raw).hexdigest()


def safe_identifier(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_]", "_", value.strip())
    if not value or value[0].isdigit():
        value = "col_" + value
    return value.lower()


def unique_identifiers(header: list[str]) -> list[str]:
    result: list[str] = []
    seen: dict[str, int] = {}
    for original in header:
        base = safe_identifier(original)
        seen[base] = seen.get(base, 0) + 1
        result.append(base if seen[base] == 1 else f"{base}_{seen[base]}")
    return result


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def load_one(con: duckdb.DuckDBPyConnection, table: str, path: Path, source_version: str) -> dict:
    header, rows, source_sha256 = read_csv_preserving_values(path)
    columns = unique_identifiers(header)
    if len(set(columns)) != len(columns):
        raise ValueError(f"colunas duplicadas após normalização em {path}")

    # Somente os nomes são normalizados; os valores permanecem exatamente como
    # aparecem na fonte, inclusive vazios e zeros.
    all_columns = columns + ["_source_file", "_source_version", "_source_sha256", "_row_number"]
    ddl = ", ".join(f"{quote_identifier(column)} VARCHAR" for column in all_columns)
    con.execute(f"DROP TABLE IF EXISTS {quote_identifier(table)}")
    con.execute(f"CREATE TABLE {quote_identifier(table)} ({ddl})")

    placeholders = ", ".join("?" for _ in all_columns)
    insert_sql = (
        f"INSERT INTO {quote_identifier(table)} "
        f"({', '.join(quote_identifier(column) for column in all_columns)}) "
        f"VALUES ({placeholders})"
    )
    loaded_at = datetime.now(timezone.utc).isoformat()
    payload = [
        row + [str(path.relative_to(ROOT)), source_version, source_sha256, str(row_number)]
        for row_number, row in enumerate(rows, start=1)
    ]
    if payload:
        con.executemany(insert_sql, payload)

    return {
        "table": table,
        "source_file": str(path.relative_to(ROOT)),
        "source_version": source_version,
        "source_sha256": source_sha256,
        "columns": len(header),
        "rows": len(rows),
        "loaded_at_utc": loaded_at,
    }


def main() -> None:
    for _, path, _ in SOURCES:
        if not path.exists():
            raise FileNotFoundError(path)

    con = duckdb.connect(str(DB_PATH))
    try:
        con.execute("BEGIN TRANSACTION")
        results = [load_one(con, table, path, version) for table, path, version in SOURCES]
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    finally:
        con.close()

    print("Fontes cruas carregadas:")
    for result in results:
        print(
            f"- {result['table']}: {result['rows']} linhas, "
            f"{result['columns']} colunas, sha256={result['source_sha256']}"
        )
    print("Nenhuma tabela derivada foi criada.")


if __name__ == "__main__":
    main()
