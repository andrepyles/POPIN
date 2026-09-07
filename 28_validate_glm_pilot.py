#!/usr/bin/env python3
"""Importa o piloto GLM e produz a validação comparativa congelada em 1.000 discursos."""

from __future__ import annotations

import difflib
import json
import re
import unicodedata
from pathlib import Path

import duckdb
import pandas as pd


ROOT = Path("/root/popin-run")
DB = ROOT / "popin.duckdb"
RUN_DIR = ROOT / "data/gpd_v2_1_20251120/pilot_runs"
GLM_FILE = RUN_DIR / "glm_4.7_flash__sample_1000__v4.jsonl"
OUT_DIR = RUN_DIR / "glm_validation__sample_1000__v4"
MODEL_GLM = "z-ai/glm-4.7-flash"
MODEL_QWEN = "Qwen/Qwen3-30B-A3B-Instruct-2507"
MODEL_DEEPSEEK = "deepseek/deepseek-v4-flash-0731"
MODEL_LUNA = "gpt-5.6-luna"
MODELS = [MODEL_QWEN, MODEL_DEEPSEEK, MODEL_LUNA, MODEL_GLM]
DIMS = [
    "people_centrism",
    "anti_elitism",
    "moral_dichotomy",
    "popular_sovereignty",
    "exclusionary_rhetoric",
    "crisis_rhetoric",
    "final_score",
]
COUNTRY_NAMES = {
    "ARG": "Argentina", "BOL": "Bolivia", "BRA": "Brazil", "CHL": "Chile",
    "COL": "Colombia", "CRI": "Costa Rica", "CUB": "Cuba",
    "DOM": "Dominican Republic", "ECU": "Ecuador", "GTM": "Guatemala",
    "HND": "Honduras", "MEX": "Mexico", "NIC": "Nicaragua", "PAN": "Panama",
    "PER": "Peru", "PRY": "Paraguay", "SLV": "El Salvador", "URY": "Uruguay",
    "VEN": "Venezuela",
}


def norm(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def name_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ta, tb = set(a.split()), set(b.split())
    token = 2 * len(ta & tb) / (len(ta) + len(tb)) if ta and tb else 0.0
    sequence = difflib.SequenceMatcher(None, a, b).ratio()
    return max(token, sequence)


def corr_rows(frame: pd.DataFrame, left: str, right: str) -> dict:
    sub = frame[[left, right]].dropna()
    if len(sub) < 3 or sub[left].nunique() < 2 or sub[right].nunique() < 2:
        return {"n": int(len(sub)), "pearson": None, "spearman": None}
    return {
        "n": int(len(sub)),
        "pearson": round(float(sub[left].corr(sub[right], method="pearson")), 4),
        # Evita depender de scipy no ambiente da VPS.
        "spearman": round(float(sub[left].rank(method="average").corr(sub[right].rank(method="average"), method="pearson")), 4),
    }


def md_table(frame: pd.DataFrame) -> str:
    """Tabela Markdown sem exigir o pacote opcional tabulate."""
    if frame.empty:
        return "(sem observações)"
    cols = [str(c) for c in frame.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in frame.itertuples(index=False, name=None):
        vals = ["" if pd.isna(v) else str(v).replace("|", "\\|") for v in row]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def import_glm(con: duckdb.DuckDBPyConnection, rows: list[dict]) -> None:
    sql = """
        INSERT INTO scores (
            discourse_id, model_id, people_centrism, anti_elitism, moral_dichotomy,
            popular_sovereignty, exclusionary_rhetoric, crisis_rhetoric, final_score,
            n_chunks, raw_json, prompt_id, provider, run_id
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
    """
    values = []
    for row in rows:
        s = row["scores"]
        values.append((
            row["discourse_id"], MODEL_GLM,
            *[s.get(dim) for dim in DIMS[:-1]], s.get("final_score"),
            row.get("n_chunks"), json.dumps(row, ensure_ascii=False),
            "v4", row.get("provider", "deepinfra"),
            "glm_4.7_flash__sample_1000__v4",
        ))
    con.executemany(sql, values)


def make_gpd_match(model_frame: pd.DataFrame, gpd: pd.DataFrame) -> pd.DataFrame:
    gpd = gpd.copy()
    gpd["country_norm"] = gpd["country"].map(norm)
    gpd["leader_norm"] = gpd["leader"].map(norm)
    # A escala observada no GPD v2.1 é 0-2; convertemos apenas a unidade para
    # 0-100, mantendo a mesma ordenação e sem estimar uma calibração.
    gpd["gpd_score100"] = gpd["gpd_score"] * 50.0
    gpd = gpd.dropna(subset=["gpd_score"])
    # O GPD possui uma linha por termo/observação; a média representa a referência
    # do líder no conjunto disponível, sem calibrar os scores dos modelos.
    gpd_agg = (
        gpd.groupby(["country_norm", "leader_norm", "country", "leader"], as_index=False)
        .agg(gpd_score100=("gpd_score100", "mean"), gpd_n=("gpd_score100", "size"))
    )
    leaders = model_frame[["iso3", "leader_name"]].drop_duplicates().copy()
    leaders["country"] = leaders["iso3"].map(COUNTRY_NAMES)
    leaders["country_norm"] = leaders["country"].map(norm)
    leaders["leader_norm"] = leaders["leader_name"].map(norm)
    out = []
    for row in leaders.itertuples(index=False):
        candidates = gpd_agg[gpd_agg["country_norm"] == row.country_norm]
        best = None
        for cand in candidates.itertuples(index=False):
            score = name_similarity(row.leader_norm, cand.leader_norm)
            if best is None or score > best[0]:
                best = (score, cand)
        if best is None:
            out.append({**row._asdict(), "gpd_leader": None, "gpd_match_score": None, "gpd_score100": None, "gpd_n": None})
        else:
            sim, cand = best
            accepted = sim >= 0.72
            out.append({
                **row._asdict(), "gpd_leader": cand.leader if accepted else None,
                "gpd_match_score": round(sim, 4),
                "gpd_score100": float(cand.gpd_score100) if accepted else None,
                "gpd_n": int(cand.gpd_n) if accepted else None,
            })
    return pd.DataFrame(out)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    with GLM_FILE.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("errors"):
                continue
            if row.get("scores", {}).get("final_score") is None:
                continue
            rows.append(row)
    if len(rows) != 1000 or len({r["discourse_id"] for r in rows}) != 1000:
        raise RuntimeError(f"Piloto inválido: rows={len(rows)} unique={len(set(r['discourse_id'] for r in rows))}")

    con = duckdb.connect(str(DB))
    import_glm(con, rows)
    con.commit()
    ids = [r["discourse_id"] for r in rows]
    con.execute("CREATE OR REPLACE TEMP TABLE pilot_ids(id VARCHAR)")
    con.executemany("INSERT INTO pilot_ids VALUES (?)", [(x,) for x in ids])

    model_frame = con.execute(
        """
        SELECT d.id AS discourse_id, d.iso3, d.leader_name, d.dtype, d.word_count,
               s.model_id, s.final_score
        FROM discourses d JOIN scores s ON s.discourse_id=d.id
        JOIN pilot_ids p ON p.id=d.id
        WHERE s.model_id IN (?, ?, ?, ?)
        """, MODELS
    ).df()
    model_frame.to_csv(OUT_DIR / "scores_long.csv", index=False)
    wide = (
        model_frame.pivot_table(index=["discourse_id", "iso3", "leader_name", "dtype", "word_count"],
                                columns="model_id", values="final_score", aggfunc="first")
        .reset_index()
    )
    wide.columns = [str(c).replace("/", "_").replace("-", "_").replace(".", "_") for c in wide.columns]
    wide.to_csv(OUT_DIR / "scores_wide.csv", index=False)

    # Correlation/reproducibility between models, at the discourse level.
    model_cols = {m: m.replace("/", "_").replace("-", "_").replace(".", "_") for m in MODELS}
    corr = []
    for i, left in enumerate(MODELS):
        for right in MODELS[i + 1:]:
            a, b = model_cols[left], model_cols[right]
            vals = wide[[a, b]].rename(columns={a: "left", b: "right"})
            result = corr_rows(vals, "left", "right")
            corr.append({"left": left, "right": right, **result, "mean_abs_delta": round(float((vals["left"] - vals["right"]).abs().mean()), 4)})
    corr_df = pd.DataFrame(corr)
    corr_df.to_csv(OUT_DIR / "model_correlations.csv", index=False)

    # Leader-level model means, plus GPD matching. GPD validation is also emitted for SPEECH only.
    gpd = con.execute("SELECT country, leader, try_cast(totalaverage AS DOUBLE) AS gpd_score FROM raw_gpd_wide").df()
    leader_model = (
        model_frame.groupby(["iso3", "leader_name", "model_id"], as_index=False)
        .agg(n_discourses=("discourse_id", "nunique"), mean_score=("final_score", "mean"), sd_score=("final_score", "std"))
    )
    leader_wide = leader_model.pivot_table(index=["iso3", "leader_name"], columns="model_id", values="mean_score").reset_index()
    leader_wide.columns = [str(c).replace("/", "_").replace("-", "_").replace(".", "_") for c in leader_wide.columns]
    leader_wide.to_csv(OUT_DIR / "leader_means.csv", index=False)

    validation_rows = []
    for dtype_label, frame in [("ALL", model_frame), ("SPEECH", model_frame[model_frame["dtype"].str.upper() == "SPEECH"])]:
        agg = frame.groupby(["iso3", "leader_name", "model_id"], as_index=False).agg(mean_score=("final_score", "mean"), n_discourses=("discourse_id", "nunique"))
        agg_wide = agg.pivot_table(index=["iso3", "leader_name"], columns="model_id", values="mean_score").reset_index()
        agg_wide.columns = [str(c).replace("/", "_").replace("-", "_").replace(".", "_") for c in agg_wide.columns]
        match = make_gpd_match(agg_wide, gpd)
        for model in MODELS:
            col = model_cols[model]
            if col not in agg_wide.columns:
                continue
            sub = match[["iso3", "leader_name", "gpd_leader", "gpd_match_score", "gpd_score100", "gpd_n"]].copy()
            sub["model_score"] = agg_wide[col].values
            sub["model_id"] = model
            sub["sample_scope"] = dtype_label
            sub["delta_vs_gpd"] = sub["model_score"] - sub["gpd_score100"]
            validation_rows.append(sub)
    leader_validation = pd.concat(validation_rows, ignore_index=True)
    leader_validation.to_csv(OUT_DIR / "leader_gpd_validation.csv", index=False)

    gpd_summary = []
    for (scope, model), sub in leader_validation.groupby(["sample_scope", "model_id"]):
        sub = sub.dropna(subset=["gpd_score100", "model_score"])
        result = corr_rows(sub.rename(columns={"model_score": "model", "gpd_score100": "gpd"}), "model", "gpd")
        gpd_summary.append({"sample_scope": scope, "model_id": model, **result,
                            "mean_abs_delta": round(float(sub["delta_vs_gpd"].abs().mean()), 4) if len(sub) else None,
                            "mean_delta_model_minus_gpd": round(float(sub["delta_vs_gpd"].mean()), 4) if len(sub) else None,
                            "matched_leaders": int(len(sub))})
    gpd_summary_df = pd.DataFrame(gpd_summary)
    gpd_summary_df.to_csv(OUT_DIR / "gpd_validation_summary.csv", index=False)
    leader_validation.sort_values("delta_vs_gpd", key=lambda s: s.abs(), ascending=False).head(30).to_csv(OUT_DIR / "top_gpd_discrepancies.csv", index=False)

    # LALLPI é um indicador país-ano; aqui usamos a média país na janela disponível.
    lallpi = con.execute("""
        SELECT iso3,
               avg(try_cast(pop AS DOUBLE)) AS lallpi_pop,
               avg(try_cast(pip AS DOUBLE)) AS lallpi_pip,
               avg(try_cast(ip AS DOUBLE)) AS lallpi_ip,
               avg(try_cast(pep AS DOUBLE)) AS lallpi_pep,
               avg(try_cast(ep AS DOUBLE)) AS lallpi_ep,
               avg(try_cast(pop_r AS DOUBLE)) AS lallpi_pop_r
        FROM raw_lallpi_index GROUP BY iso3
    """).df()
    country_model = model_frame.groupby(["iso3", "model_id"], as_index=False).agg(mean_score=("final_score", "mean"), n_discourses=("discourse_id", "nunique"))
    country_wide = country_model.pivot_table(index="iso3", columns="model_id", values="mean_score").reset_index()
    country_wide.columns = [str(c).replace("/", "_").replace("-", "_").replace(".", "_") for c in country_wide.columns]
    country_validation = country_wide.merge(lallpi, on="iso3", how="left")
    country_validation.to_csv(OUT_DIR / "country_lallpi_validation.csv", index=False)
    lallpi_summary = []
    for model in MODELS:
        col = model_cols[model]
        for indicator in ["lallpi_pop", "lallpi_pip", "lallpi_ip", "lallpi_pep", "lallpi_ep", "lallpi_pop_r"]:
            if col not in country_validation.columns:
                continue
            result = corr_rows(country_validation.rename(columns={col: "model", indicator: "indicator"}), "model", "indicator")
            lallpi_summary.append({"model_id": model, "indicator": indicator, **result})
    pd.DataFrame(lallpi_summary).to_csv(OUT_DIR / "lallpi_validation_summary.csv", index=False)

    counts = model_frame.groupby("model_id").size().to_dict()
    speech_n = int(model_frame.loc[model_frame["model_id"] == MODEL_GLM, "dtype"].str.upper().eq("SPEECH").sum())
    report = [
        "# Validação do piloto GLM 4.7 Flash — amostra comum de 1.000 discursos",
        "",
        "Escopo: scores v4, chunking de 800 palavras sem sobreposição. O GLM foi importado como condição separada (`z-ai/glm-4.7-flash`, provider `deepinfra`). GPD e LALLPI são referências externas de validação, não padrões-ouro perfeitos.",
        "",
        f"- Discursos GLM válidos: {len(rows):,}; discursos SPEECH: {speech_n:,}.",
        f"- Cobertura por modelo no painel comum: {counts}.",
        "- GPD: validação líder-agregada; a tabela SPEECH deve ser a referência principal para comparação com a codificação de discursos.",
        "- LALLPI: validação país-agregada, média dos anos disponíveis.",
        "",
        "## Correlação entre modelos",
        "",
        md_table(corr_df),
        "",
        "## Correlação com GPD",
        "",
        md_table(gpd_summary_df),
        "",
        "## Correlação com LALLPI",
        "",
        md_table(pd.DataFrame(lallpi_summary)),
        "",
        "Arquivos: `scores_long.csv`, `scores_wide.csv`, `model_correlations.csv`, `leader_gpd_validation.csv`, `gpd_validation_summary.csv`, `top_gpd_discrepancies.csv`, `country_lallpi_validation.csv`, `lallpi_validation_summary.csv`.",
    ]
    (OUT_DIR / "validation_report.md").write_text("\n".join(report), encoding="utf-8")
    con.close()
    print(json.dumps({
        "glm_rows": len(rows),
        "glm_model_rows_in_db": int(duckdb.connect(str(DB), read_only=True).execute("select count(*) from scores where model_id=?", [MODEL_GLM]).fetchone()[0]),
        "output_dir": str(OUT_DIR),
        "report": str(OUT_DIR / "validation_report.md"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
