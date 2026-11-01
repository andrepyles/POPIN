"""Generate the frozen POPIN v4.1.0 analysis exports from the full DuckDB.

The article snapshot contains 45,492 non-invalid documents. The score rows
come from two separately recorded GPT-5.6 v4 full-text cohorts: the 44,592-row
full run and a 900-row pilot run. Their provenance is retained in every export.

Usage:
    python 50_generate_final_tables.py
    DB_PATH=/path/to/popin.duckdb OUT_DIR=/path/to/output python 50_generate_final_tables.py
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DB_PATH", ROOT / "popin.duckdb"))
OUT_DIR = Path(os.getenv("OUT_DIR", ROOT / "data" / "release_v4"))

DIMENSIONS = [
    "people_centrism",
    "anti_elitism",
    "moral_dichotomy",
    "popular_sovereignty",
    "exclusionary_rhetoric",
    "crisis_rhetoric",
]

COUNTRY_NAMES = {
    "ARG": "Argentina", "BOL": "Bolívia", "BRA": "Brasil",
    "CHL": "Chile", "COL": "Colômbia", "CRI": "Costa Rica",
    "CUB": "Cuba", "DOM": "República Dominicana", "ECU": "Equador",
    "GTM": "Guatemala", "HND": "Honduras", "MEX": "México",
    "NIC": "Nicarágua", "PAN": "Panamá", "PER": "Peru",
    "PRY": "Paraguai", "SLV": "El Salvador", "URY": "Uruguai",
    "VEN": "Venezuela",
}


def load_frozen_scores(db_path: Path) -> pd.DataFrame:
    """Load one canonical v4 full-text score per eligible discourse."""
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = con.execute(
            """
            SELECT
                d.id AS discourse_id,
                d.iso3,
                d.leader_name,
                d.discourse_year AS year,
                d.dtype,
                d.word_count,
                s.n_chunks,
                s.people_centrism,
                s.anti_elitism,
                s.moral_dichotomy,
                s.popular_sovereignty,
                s.exclusionary_rhetoric,
                s.crisis_rhetoric,
                s.final_score,
                s.model_id,
                s.prompt_id AS prompt_version,
                s.provider,
                s.scope AS score_scope,
                s.coverage AS score_coverage,
                s.source_kind,
                s.chunked,
                s.scored_at
            FROM scores s
            JOIN discourses d ON d.id = s.discourse_id
            WHERE s.model_id = 'gpt-5.6-luna'
              AND s.prompt_id = 'v4'
              AND s.status = 'ok'
              AND s.chunked = FALSE
              AND s.scope IN ('full', 'pilot')
              AND d.dtype <> 'INVALID'
            ORDER BY d.id
            """
        ).fetchdf()
    finally:
        con.close()

    if rows.empty:
        raise RuntimeError(f"No frozen POPIN v4 scores found in {db_path}")
    if rows["discourse_id"].duplicated().any():
        duplicates = int(rows["discourse_id"].duplicated(keep=False).sum())
        raise RuntimeError(f"Selected score query returned {duplicates} duplicate rows")
    if rows[DIMENSIONS + ["final_score"]].isna().any().any():
        raise RuntimeError("The selected score snapshot contains null score values")

    expected = {
        "documents": 45_492,
        "speeches": 34_821,
        "countries": 19,
        "leaders": 105,
        "full_run": 44_592,
        "pilot": 900,
    }
    observed = {
        "documents": int(len(rows)),
        "speeches": int((rows["dtype"] == "SPEECH").sum()),
        "countries": int(rows["iso3"].nunique()),
        "leaders": int(rows["leader_name"].nunique()),
        "full_run": int((rows["score_scope"] == "full").sum()),
        "pilot": int((rows["score_scope"] == "pilot").sum()),
    }
    if observed != expected:
        raise RuntimeError(f"Snapshot counts differ: expected={expected}, observed={observed}")
    if not rows["score_scope"].isin(["full", "pilot"]).all():
        raise RuntimeError("Unexpected score cohort in frozen snapshot")
    return rows


def summary(rows: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    records: list[dict] = []
    for values, group in rows.groupby(keys, dropna=False, sort=True):
        if not isinstance(values, tuple):
            values = (values,)
        record = dict(zip(keys, values))
        scores = group["final_score"].astype(float)
        record.update({
            "n": int(scores.count()),
            "mean_score": scores.mean(),
            "median_score": scores.median(),
            "sd_score": scores.std(ddof=1),
            "se_document": scores.std(ddof=1) / np.sqrt(scores.count()),
            "p25_score": scores.quantile(0.25),
            "p75_score": scores.quantile(0.75),
            "min_score": scores.min(),
            "max_score": scores.max(),
            "mean_word_count": group["word_count"].mean(),
        })
        records.append(record)
    return pd.DataFrame.from_records(records)


def dimension_summary(rows: pd.DataFrame) -> pd.DataFrame:
    records: list[dict] = []
    for dimension in DIMENSIONS:
        scores = rows[dimension].astype(float)
        records.append({
            "dimension": dimension,
            "n": int(scores.count()),
            "mean_score": scores.mean(),
            "median_score": scores.median(),
            "sd_score": scores.std(ddof=1),
            "se_document": scores.std(ddof=1) / np.sqrt(scores.count()),
            "p25_score": scores.quantile(0.25),
            "p75_score": scores.quantile(0.75),
            "min_score": scores.min(),
            "max_score": scores.max(),
        })
    return pd.DataFrame.from_records(records)


def main() -> None:
    rows = load_frozen_scores(DB_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = OUT_DIR / "popin_v4_scores.csv"
    parquet_path = OUT_DIR / "popin_v4_scores.parquet"
    rows.to_csv(csv_path, index=False, encoding="utf-8")
    duckdb.from_df(rows).write_parquet(str(parquet_path), compression="zstd")

    speech_rows = rows.loc[rows["dtype"] == "SPEECH"].copy()
    speech_rows["country"] = speech_rows["iso3"].map(COUNTRY_NAMES).fillna(speech_rows["iso3"])
    tables = {
        "country_speech.csv": summary(speech_rows, ["iso3", "country"]),
        "leader_speech.csv": summary(speech_rows, ["iso3", "country", "leader_name"]),
        "year_speech.csv": summary(speech_rows, ["year"]),
        "dimension_speech.csv": dimension_summary(speech_rows),
    }
    analysis_dir = OUT_DIR / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    for filename, table in tables.items():
        table.to_csv(analysis_dir / filename, index=False, encoding="utf-8")

    cohort_counts = rows.groupby(["score_scope", "score_coverage"], dropna=False).size()
    metadata = {
        "release": "POPIN v4",
        "package_revision": "4.1.0",
        "snapshot": "2026-09-06",
        # Store only the portable asset name; never publish a machine-local path.
        "source_database": DB_PATH.name,
        "source_tables": ["discourses", "scores"],
        "score_filter": {
            "model_id": "gpt-5.6-luna",
            "prompt_id": "v4",
            "status": "ok",
            "chunked": False,
            "scope": ["full", "pilot"],
            "discourse_type_excluded": "INVALID",
        },
        "observations": int(len(rows)),
        "speech_observations": int(len(speech_rows)),
        "countries": int(rows["iso3"].nunique()),
        "leaders": int(rows["leader_name"].nunique()),
        "year_min": int(rows["year"].min()),
        "year_max": int(rows["year"].max()),
        "cohorts": [
            {
                "scope": str(scope),
                "coverage": str(coverage),
                "documents": int(count),
            }
            for (scope, coverage), count in cohort_counts.items()
        ],
        "dimensions": DIMENSIONS,
        "score": "arithmetic_mean_of_six_dimensions",
        "posthoc_gpd_rescaling": False,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (analysis_dir / "analysis_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "database": str(DB_PATH),
        "output_dir": str(OUT_DIR),
        "documents": len(rows),
        "speeches": len(speech_rows),
        "cohorts": metadata["cohorts"],
        "exports": [str(csv_path), str(parquet_path)],
        "analysis_tables": sorted(tables),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
