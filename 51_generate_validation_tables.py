"""Consolida as tabelas finais de validação do POPIN v4.1.0.

As fontes são os resultados congelados da auditoria de 06/09/2026. O script
não faz novas inferências nem recalibra scores: apenas preserva CSVs brutos
de diagnóstico e extrai o escopo SPEECH das tabelas que misturam escopos.

Uso:
    python 51_generate_validation_tables.py
    AUDIT_DIR=... VALIDATION_DIR=... python 51_generate_validation_tables.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AUDIT_DIR = Path(
    os.getenv(
        "AUDIT_DIR",
        ROOT / "data" / "release_v4" / "analysis" / "source_audit",
    )
)
VALIDATION_DIR = Path(
    os.getenv("VALIDATION_DIR", ROOT / "data" / "release_v4" / "analysis" / "validation")
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    """Return a portable repository path, or a basename for external overrides."""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def copy_csv(source_name: str, output_name: str) -> dict[str, object]:
    source = AUDIT_DIR / source_name
    target = VALIDATION_DIR / output_name
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copyfile(source, target)
    return {
        "path": display_path(target),
        "source": display_path(source),
        "rows": sum(1 for _ in source.open(encoding="utf-8")) - 1,
        "sha256": sha256(target),
    }


def filter_csv(source_name: str, output_name: str, field: str, value: str) -> dict[str, object]:
    source = AUDIT_DIR / source_name
    target = VALIDATION_DIR / output_name
    if not source.exists():
        raise FileNotFoundError(source)
    with source.open(newline="", encoding="utf-8") as source_handle:
        reader = csv.DictReader(source_handle)
        if reader.fieldnames is None or field not in reader.fieldnames:
            raise ValueError(f"Campo {field!r} ausente em {source}")
        with target.open("w", newline="", encoding="utf-8") as target_handle:
            writer = csv.DictWriter(target_handle, fieldnames=reader.fieldnames)
            writer.writeheader()
            rows = 0
            for row in reader:
                if row[field] == value:
                    writer.writerow(row)
                    rows += 1
    return {
        "path": display_path(target),
        "source": display_path(source),
        "filter": {field: value},
        "rows": rows,
        "sha256": sha256(target),
    }


def main() -> None:
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, dict[str, object]] = {}
    artifacts["model_gpd_speech"] = filter_csv(
        "gpd_term_metrics.csv",
        "model_gpd_speech.csv",
        "scope",
        "SPEECH",
    )
    artifacts["gpd_term_points_speech"] = filter_csv(
        "gpd_term_points.csv",
        "gpd_term_points_speech.csv",
        "scope",
        "SPEECH",
    )

    preserved = {
        "prompt_sensitivity": ("prompt_comparison.csv", "prompt_sensitivity.csv"),
        "lallpi_country_year": ("lallpi_country_year.csv", "lallpi_country_year.csv"),
        "coverage_all_models": ("coverage.csv", "coverage_all_models.csv"),
        "score_integrity_all_models": ("score_integrity.csv", "score_integrity_all_models.csv"),
        "prompt_inventory": ("prompt_inventory.csv", "prompt_inventory.csv"),
        "gpd_word_cutoffs_speech": ("word_cutoffs_gpd.csv", "gpd_word_cutoffs_speech.csv"),
        "model_pairs_full_corpus": ("paired_models.csv", "model_pairs_full_corpus.csv"),
        "gpd_text_match_diagnostics": (
            "gpd_text_candidate_metrics.csv",
            "gpd_text_match_diagnostics.csv",
        ),
        "luna_raw_integrity": ("luna_raw_integrity.csv", "luna_raw_integrity.csv"),
    }
    for key, (source_name, output_name) in preserved.items():
        artifacts[key] = copy_csv(source_name, output_name)

    metadata = {
        "release": "POPIN v4",
        "snapshot": "2026-09-06",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Final validation and robustness tables; no new model calls or post-hoc rescaling.",
        "primary_scope": "SPEECH",
        "gpd_unit": "leader-mandate",
        "gpd_scale_note": "GPD 0-2 was multiplied by 50 only for readable comparison; scales are not assumed equivalent.",
        "lallpi_unit": "country-year",
        "prompt_sensitivity_unit": "paired 900 discourse IDs",
        "artifacts": artifacts,
    }
    metadata_path = VALIDATION_DIR / "validation_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output_dir": str(VALIDATION_DIR),
        "artifacts": len(artifacts),
        "metadata": str(metadata_path),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
