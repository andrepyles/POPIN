#!/usr/bin/env python3
"""Compara Luna full e Luna chunked na amostra comum de 1.000 discursos."""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import duckdb
import pandas as pd


ROOT = Path("/run/media/andre/5E12373112370E11/OneDrive/04 - Faculdade/02 - Mestrado/03 - Dissertação/02 - Código/popin")
DB = ROOT / "popin.duckdb"
OUT = ROOT / "data/gpd_v2_1_20251120/pilot_runs/glm_validation__sample_1000__v4"
MODELS = {
    "Qwen": "Qwen/Qwen3-30B-A3B-Instruct-2507",
    "DeepSeek": "deepseek/deepseek-v4-flash-0731",
    "Luna full": "gpt-5.6-luna",
    "Luna chunked": "gpt-5.6-luna__chunked_sample1000",
    "GLM": "z-ai/glm-4.7-flash",
}


def col(name: str) -> str:
    return name.replace("/", "_").replace("-", "_").replace(".", "_")


def corr(a: pd.Series, b: pd.Series) -> tuple[int, float | None, float | None]:
    x = pd.DataFrame({"a": a, "b": b}).dropna()
    if len(x) < 3 or x.a.nunique() < 2 or x.b.nunique() < 2:
        return len(x), None, None
    return len(x), round(float(x.a.corr(x.b)), 4), round(float(x.a.rank().corr(x.b.rank())), 4)


def md(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "(sem observações)"
    frame = frame.copy()
    lines = ["| " + " | ".join(map(str, frame.columns)) + " |", "| " + " | ".join(["---"] * len(frame.columns)) + " |"]
    for row in frame.itertuples(index=False, name=None):
        vals = ["" if pd.isna(v) else str(v).replace("|", "\\|") for v in row]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main() -> None:
    con = duckdb.connect(str(DB), read_only=True)
    ids = con.execute("select distinct discourse_id from scores where model_id='z-ai/glm-4.7-flash'").df()
    con.execute("create or replace temp table pilot_ids as select * from ids")
    names = list(MODELS.values())
    long = con.execute("""
        select d.id as discourse_id,d.iso3,d.leader_name,d.dtype,d.word_count,s.model_id,s.final_score
        from discourses d join pilot_ids p on p.discourse_id=d.id join scores s on s.discourse_id=d.id
        where s.model_id in (?,?,?,?,?)
    """, names).df()
    piv = long.pivot_table(index=["discourse_id", "iso3", "leader_name", "dtype", "word_count"], columns="model_id", values="final_score", aggfunc="first").reset_index()
    rename = {value: key for key, value in MODELS.items()}
    piv = piv.rename(columns=rename)
    piv.to_csv(OUT / "scores_wide_with_luna_chunked.csv", index=False)

    pairs = []
    for i, (left, left_id) in enumerate(MODELS.items()):
        for right, right_id in list(MODELS.items())[i + 1:]:
            n, p, s = corr(piv[left], piv[right])
            pairs.append({"left": left, "right": right, "n": n, "pearson": p, "spearman": s, "mean_abs_delta": round(float((piv[left] - piv[right]).abs().mean()), 4)})
    corr_df = pd.DataFrame(pairs)
    corr_df.to_csv(OUT / "model_correlations_with_luna_chunked.csv", index=False)

    delta = piv["Luna chunked"] - piv["Luna full"]
    full_chunked = pd.DataFrame([{
        "n": len(piv),
        "pearson": corr(piv["Luna full"], piv["Luna chunked"])[1],
        "spearman": corr(piv["Luna full"], piv["Luna chunked"])[2],
        "mean_full": round(float(piv["Luna full"].mean()), 4),
        "mean_chunked": round(float(piv["Luna chunked"].mean()), 4),
        "mean_delta_chunked_minus_full": round(float(delta.mean()), 4),
        "mean_abs_delta": round(float(delta.abs().mean()), 4),
        "sd_delta": round(float(delta.std()), 4),
        "pct_chunked_lower": round(float((delta < 0).mean() * 100), 2),
        "pct_abs_delta_gt_20": round(float((delta.abs() > 20).mean() * 100), 2),
    }])
    full_chunked.to_csv(OUT / "luna_full_vs_chunked_summary.csv", index=False)

    piv["length_bucket"] = pd.cut(piv.word_count, bins=[0, 800, 1600, float("inf")], labels=["<=800", "801-1600", ">1600"])
    length = piv.groupby("length_bucket", observed=False).apply(lambda x: pd.Series({
        "n": len(x), "mean_full": x["Luna full"].mean(), "mean_chunked": x["Luna chunked"].mean(),
        "mean_delta": (x["Luna chunked"] - x["Luna full"]).mean(), "mean_abs_delta": (x["Luna chunked"] - x["Luna full"]).abs().mean(),
    }), include_groups=False).reset_index()
    for c in length.columns[1:]:
        length[c] = length[c].round(4)
    length.to_csv(OUT / "luna_full_vs_chunked_by_length.csv", index=False)

    leader = piv.groupby(["iso3", "leader_name"], as_index=False).agg(n_discourses=("discourse_id", "nunique"), **{f"{m}_mean": (m, "mean") for m in MODELS})
    for c in leader.columns[3:]:
        leader[c] = leader[c].round(2)
    leader = leader.sort_values("Qwen_mean", ascending=False)
    leader.to_csv(OUT / "leader_mean_comparison_with_luna_chunked.csv", index=False)

    # GPD: aproveita o matching de líderes já auditado na validação anterior.
    gpd_ref = pd.read_csv(OUT / "leader_gpd_validation.csv")
    gpd_ref = gpd_ref[gpd_ref.sample_scope == "SPEECH"][["iso3", "leader_name", "gpd_score100", "gpd_match_score", "gpd_n"]].drop_duplicates()
    speech = piv[piv.dtype.str.upper() == "SPEECH"].groupby(["iso3", "leader_name"], as_index=False).agg(**{f"{m}_mean": (m, "mean") for m in MODELS})
    gpd = speech.merge(gpd_ref, on=["iso3", "leader_name"], how="left")
    gpd.to_csv(OUT / "gpd_validation_with_luna_chunked.csv", index=False)
    gpd_rows = []
    for m in MODELS:
        x = gpd[[f"{m}_mean", "gpd_score100"]].dropna()
        n, p, s = corr(x[f"{m}_mean"], x.gpd_score100)
        gpd_rows.append({"model": m, "n": n, "pearson": p, "spearman": s, "mean_abs_delta": round(float((x[f"{m}_mean"] - x.gpd_score100).abs().mean()), 4), "mean_delta_model_minus_gpd": round(float((x[f"{m}_mean"] - x.gpd_score100).mean()), 4)})
    gpd_summary = pd.DataFrame(gpd_rows)
    gpd_summary.to_csv(OUT / "gpd_summary_with_luna_chunked.csv", index=False)

    # LALLPI: país-agregado na mesma amostra.
    lallpi = con.execute("""
        select iso3,avg(try_cast(pop as double)) lallpi_pop,avg(try_cast(pip as double)) lallpi_pip,avg(try_cast(ip as double)) lallpi_ip,
               avg(try_cast(pep as double)) lallpi_pep,avg(try_cast(ep as double)) lallpi_ep,avg(try_cast(pop_r as double)) lallpi_pop_r
        from raw_lallpi_index group by iso3
    """).df()
    country = piv.groupby("iso3", as_index=False).agg(**{f"{m}_mean": (m, "mean") for m in MODELS}).merge(lallpi, on="iso3", how="left")
    country.to_csv(OUT / "lallpi_validation_with_luna_chunked.csv", index=False)
    lallpi_rows = []
    for m in MODELS:
        for ind in ["lallpi_pop", "lallpi_pip", "lallpi_ip", "lallpi_pep", "lallpi_ep", "lallpi_pop_r"]:
            n, p, s = corr(country[f"{m}_mean"], country[ind])
            lallpi_rows.append({"model": m, "indicator": ind, "n": n, "pearson": p, "spearman": s})
    lallpi_summary = pd.DataFrame(lallpi_rows)
    lallpi_summary.to_csv(OUT / "lallpi_summary_with_luna_chunked.csv", index=False)

    report = [
        "# Luna full versus Luna chunked — piloto de 1.000 discursos",
        "",
        "O Luna chunked usa o mesmo prompt v4, chunks contíguos de 800 palavras, sem sobreposição e média ponderada por tamanho do chunk. A condição foi mantida separada do Luna full.",
        "",
        "## Luna full versus Luna chunked",
        "",
        md(full_chunked),
        "",
        "## Diferença por tamanho do discurso",
        "",
        md(length),
        "",
        "## Correlação entre modelos",
        "",
        md(corr_df),
        "",
        "## Validação GPD (somente SPEECH)",
        "",
        md(gpd_summary),
        "",
        "## Validação LALLPI (país-agregada)",
        "",
        md(lallpi_summary),
        "",
        "Arquivos principais: `scores_wide_with_luna_chunked.csv`, `luna_full_vs_chunked_summary.csv`, `luna_full_vs_chunked_by_length.csv`, `leader_mean_comparison_with_luna_chunked.csv`, `gpd_summary_with_luna_chunked.csv`, `lallpi_summary_with_luna_chunked.csv`.",
    ]
    (OUT / "luna_chunked_analysis.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"n_discourses": len(piv), "n_leaders": len(leader), "report": str(OUT / 'luna_chunked_analysis.md')}, ensure_ascii=False))


if __name__ == "__main__":
    main()
