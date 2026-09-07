"""Tabela por líder da amostra de 900, com deltas dos modelos contra o GPD."""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "popin.duckdb"
SAMPLE_PATH = ROOT / "data/gpd_v2_1_20251120/sensitivity_test_sample.csv"
OUT_MD = ROOT / "data/gpd_v2_1_20251120/full_runs/LEADER_GPD_DELTA_LUNA_SAMPLE_900.md"
OUT_CSV = OUT_MD.with_suffix(".csv")
MODELS = {
    "Qwen": "Qwen/Qwen3-30B-A3B-Instruct-2507",
    "DeepSeek": "deepseek/deepseek-v4-flash-0731",
    "Luna": "gpt-5.6-luna",
}


def f(value: object) -> str:
    if pd.isna(value):
        return "—"
    return f"{float(value):.2f}".replace(".", ",")


def markdown(df: pd.DataFrame) -> str:
    headers = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in df.itertuples(index=False, name=None):
        lines.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |")
    return "\n".join(lines)


def main() -> None:
    sample = pd.read_csv(SAMPLE_PATH)
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        ids = sample["discourse_id"].tolist()
        placeholders = ",".join("?" for _ in ids)
        scores = con.execute(
            f"SELECT discourse_id, model_id, final_score FROM scores WHERE discourse_id IN ({placeholders})",
            ids,
        ).fetchdf()
        lallpi = con.execute("SELECT iso3, year, pop_r FROM raw_lallpi_index").fetchdf()
    finally:
        con.close()

    scores["model"] = scores["model_id"].map({v: k for k, v in MODELS.items()})
    wide = sample.copy()
    for model in MODELS:
        current = scores.loc[scores["model"].eq(model), ["discourse_id", "final_score"]]
        wide = wide.merge(
            current.rename(columns={"final_score": model}),
            on="discourse_id", how="left", validate="one_to_one"
        )

    rows = []
    for (leader, iso3), group in wide.groupby(["leader_name", "iso3"], dropna=False):
        row = {"Líder": leader, "País": iso3, "N discursos": len(group)}
        for model in MODELS:
            row[model] = group[model].mean()
            row[f"SE {model}"] = group[model].std(ddof=1) / np.sqrt(len(group))

        gpd = group[group["gpd_split"].eq("test_locked")].groupby("gpd_term_key")["gpd_totalaverage"].first()
        row["GPD"] = gpd.mean() * 50 if len(gpd) else np.nan
        row["Termos GPD"] = len(gpd) if len(gpd) else np.nan
        for model in MODELS:
            row[f"Delta {model} − GPD"] = row[model] - row["GPD"] if pd.notna(row["GPD"]) else np.nan

        years = group[["iso3", "discourse_year"]].drop_duplicates().copy()
        years["year"] = years["discourse_year"].astype(str)
        lp = lallpi.copy()
        lp["year"] = lp["year"].astype(str)
        lp["pop_r"] = pd.to_numeric(lp["pop_r"], errors="coerce")
        match = years.merge(lp, on=["iso3", "year"])["pop_r"].dropna()
        row["LALLPI POP_R"] = match.mean() * 100 if len(match) else np.nan
        row["Anos LALLPI"] = len(match) if len(match) else np.nan
        rows.append(row)

    result = pd.DataFrame(rows).sort_values(["GPD", "Luna"], ascending=[False, False], na_position="last")
    result.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    display = result.copy()
    for col in display.columns:
        if col not in ["Líder", "País", "N discursos", "Termos GPD", "Anos LALLPI"]:
            display[col] = display[col].map(f)
    display["N discursos"] = display["N discursos"].astype(int)
    for col in ["Termos GPD", "Anos LALLPI"]:
        display[col] = display[col].map(lambda x: "—" if pd.isna(x) else str(int(x)))

    text = [
        "# Comparação por líder — amostra POPIN de 900 discursos",
        "",
        "Todos os 900 discursos são `dtype = SPEECH`. A tabela contém todos os líderes presentes na amostra.",
        "`Delta modelo − GPD` é o score médio do modelo menos o GPD reescalado para 0–100.",
        "O GPD usado é exclusivamente o subconjunto `test_locked`; ausência de GPD não significa score zero.",
        "LALLPI POP_R é contextual, agregado por país–ano, e não é usado no cálculo dos deltas.",
        "",
        markdown(display),
        "",
    ]
    OUT_MD.write_text("\n".join(text), encoding="utf-8")
    print(f"Líderes: {len(result)}")
    print(f"GPD disponível: {int(result['GPD'].notna().sum())}")
    print(f"Markdown: {OUT_MD}")
    print(f"CSV: {OUT_CSV}")
    print("\nTOP 15 POR GPD")
    print(markdown(display.head(15)))


if __name__ == "__main__":
    main()
