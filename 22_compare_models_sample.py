"""Compara Qwen, DeepSeek e Luna na amostra congelada de 900 discursos."""

from __future__ import annotations

import math
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "popin.duckdb"
SAMPLE_PATH = ROOT / "data/gpd_v2_1_20251120/sensitivity_test_sample.csv"
OUT_PATH = ROOT / "data/gpd_v2_1_20251120/full_runs/MODEL_COMPARISON_LUNA_900.md"
MODELS = {
    "Qwen": "Qwen/Qwen3-30B-A3B-Instruct-2507",
    "DeepSeek": "deepseek/deepseek-v4-flash-0731",
    "Luna": "gpt-5.6-luna",
}


def corr(x: pd.Series, y: pd.Series, rank: bool = False) -> float:
    a = pd.to_numeric(x, errors="coerce").to_numpy(float)
    b = pd.to_numeric(y, errors="coerce").to_numpy(float)
    ok = np.isfinite(a) & np.isfinite(b)
    if rank:
        a, b = pd.Series(a[ok]).rank(method="average").to_numpy(), pd.Series(b[ok]).rank(method="average").to_numpy()
    else:
        a, b = a[ok], b[ok]
    return float(np.corrcoef(a, b)[0, 1]) if len(a) > 1 else float("nan")


def metrics(x: pd.Series, y: pd.Series) -> dict[str, float]:
    a = pd.to_numeric(x, errors="coerce").to_numpy(float)
    b = pd.to_numeric(y, errors="coerce").to_numpy(float)
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    e = a - b
    return {
        "n": int(len(a)), "pearson": corr(pd.Series(a), pd.Series(b)),
        "spearman": corr(pd.Series(a), pd.Series(b), rank=True),
        "mae": float(np.mean(np.abs(e))), "rmse": float(np.sqrt(np.mean(e ** 2))),
        "bias": float(np.mean(e)),
    }


def fmt(v: float, digits: int = 2) -> str:
    if pd.isna(v):
        return "—"
    return f"{v:.{digits}f}".replace(".", ",")


def table(df: pd.DataFrame, float_cols: list[str] | None = None) -> str:
    out = df.copy()
    for col in float_cols or []:
        if col in out:
            out[col] = out[col].map(fmt)
    headers = [str(c) for c in out.columns]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in out.itertuples(index=False, name=None):
        lines.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |")
    return "\n".join(lines)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    sample = pd.read_csv(SAMPLE_PATH)
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        ids = sample["discourse_id"].tolist()
        ph = ",".join("?" for _ in ids)
        scores = con.execute(
            f"""SELECT discourse_id, model_id, final_score
                FROM scores WHERE discourse_id IN ({ph})""", ids
        ).fetchdf()
        lallpi = con.execute(
            "SELECT iso3, year, pop, pop_r FROM raw_lallpi_index"
        ).fetchdf()
    finally:
        con.close()
    scores["model"] = scores["model_id"].map({v: k for k, v in MODELS.items()})
    scores = scores.dropna(subset=["model"])
    wide = sample.copy()
    for model in MODELS:
        model_scores = scores.loc[scores["model"].eq(model), ["discourse_id", "final_score"]]
        wide = wide.merge(model_scores.rename(columns={"final_score": model}), on="discourse_id", how="left", validate="one_to_one")
    wide["year"] = wide["discourse_year"].astype(str)
    lallpi["year"] = lallpi["year"].astype(str)
    for col in ["pop", "pop_r"]:
        lallpi[col] = pd.to_numeric(lallpi[col], errors="coerce")
    return wide, lallpi


def distribution(wide: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model in MODELS:
        s = wide[model].astype(float)
        rows.append({
            "Modelo": model, "N": int(s.notna().sum()), "Média": s.mean(),
            "DP": s.std(), "Mediana": s.median(), "Mínimo": s.min(),
            "Máximo": s.max(), "% >= 50": (s.ge(50).mean() * 100),
            "% = 0": (s.eq(0).mean() * 100),
        })
    return pd.DataFrame(rows)


def pairwise(wide: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for left, right in [("Qwen", "DeepSeek"), ("Qwen", "Luna"), ("DeepSeek", "Luna")]:
        m = metrics(wide[left], wide[right])
        rows.append({"Comparação": f"{left} − {right}", **m})
    return pd.DataFrame(rows)


def gpd_validation(wide: pd.DataFrame, min_n: int = 1) -> pd.DataFrame:
    d = wide[wide["gpd_split"].eq("test_locked")].copy()
    counts = d.groupby("gpd_term_key").size()
    keep = counts[counts >= min_n].index
    d = d[d["gpd_term_key"].isin(keep)]
    rows = []
    for model in MODELS:
        agg = d.groupby("gpd_term_key").agg(
            reference=("gpd_totalaverage", "first"), score=(model, "mean"), n=("discourse_id", "size")
        ).reset_index()
        m = metrics(agg["score"], agg["reference"] * 50)
        rows.append({"Modelo": model, "N termos": len(agg), **m})
    return pd.DataFrame(rows)


def lallpi_validation(wide: pd.DataFrame, lallpi: pd.DataFrame, indicator: str, min_n: int = 1) -> pd.DataFrame:
    d = wide.groupby(["iso3", "year"]).agg(
        Qwen=("Qwen", "mean"), DeepSeek=("DeepSeek", "mean"), Luna=("Luna", "mean"),
        n=("discourse_id", "size")
    ).reset_index()
    d = d[d["n"] >= min_n].merge(lallpi[["iso3", "year", indicator]], on=["iso3", "year"])
    d["reference"] = d[indicator] * 100 if indicator == "pop_r" else d[indicator]
    rows = []
    for model in MODELS:
        m = metrics(d[model], d["reference"])
        rows.append({"Modelo": model, "N país-ano": len(d), **m})
    return pd.DataFrame(rows)


def leader_table(wide: pd.DataFrame, model: str, n_min: int = 10) -> pd.DataFrame:
    d = wide.groupby(["leader_name", "iso3"]).agg(
        N=("discourse_id", "size"), Média=(model, "mean"), DP=(model, "std")
    ).reset_index()
    d = d[d["N"] >= n_min].copy()
    d["SE"] = d["DP"] / np.sqrt(d["N"])
    return d.sort_values(["Média", "N"], ascending=[False, False]).head(10)


def leader_comparison(wide: pd.DataFrame, n_min: int = 10) -> pd.DataFrame:
    rows = []
    for (leader, iso3), group in wide.groupby(["leader_name", "iso3"]):
        if len(group) < n_min:
            continue
        row = {"Líder": leader, "País": iso3, "N": len(group)}
        for model in MODELS:
            row[model] = group[model].mean()
            row[f"SE {model}"] = group[model].std(ddof=1) / math.sqrt(len(group))
        gpd = group[group["gpd_split"].eq("test_locked")].groupby("gpd_term_key")["gpd_totalaverage"].first()
        row["GPD"] = gpd.mean() * 50 if len(gpd) else np.nan
        row["N GPD"] = len(gpd)
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["Luna", "N"], ascending=[False, False])


def main() -> None:
    wide, lallpi = load_data()
    lines = [
        "# POPIN v4 — comparação Qwen, DeepSeek e Luna na amostra de 900",
        "",
        "Execução: scores v4 no mesmo conjunto congelado de 900 discursos; Luna foi executado diretamente na OpenAI Batch API.",
        "As métricas de associação usam correlação de Pearson e Spearman; `bias` é POPIN menos a referência.",
        "",
        "## 1. Distribuição dos scores",
        "",
        table(distribution(wide), ["Média", "DP", "Mediana", "Mínimo", "Máximo", "% >= 50", "% = 0"]),
        "",
        "## 2. Concordância entre modelos",
        "",
        table(pairwise(wide), ["pearson", "spearman", "mae", "rmse", "bias"]),
        "",
        "## 3. Validação convergente com GPD",
        "",
        "O GPD é agregado por líder–mandato no teste bloqueado. O `totalaverage` original (0–2) é reescalado para 0–100.",
        "",
        "### Todos os termos do teste bloqueado",
        "",
        table(gpd_validation(wide), ["pearson", "spearman", "mae", "rmse", "bias"]),
        "",
        "### Termos com pelo menos 5 discursos na amostra",
        "",
        table(gpd_validation(wide, 5), ["pearson", "spearman", "mae", "rmse", "bias"]),
        "",
        "## 4. Validação externa com LALLPI — país–ano",
        "",
        "`POP_R` é o indicador principal e foi multiplicado por 100; `POP` é reportado como teste secundário na escala original do arquivo.",
        "",
        "### POP_R — todas as células disponíveis",
        "",
        table(lallpi_validation(wide, lallpi, "pop_r"), ["pearson", "spearman", "mae", "rmse", "bias"]),
        "",
        "### POP_R — células com pelo menos 5 discursos",
        "",
        table(lallpi_validation(wide, lallpi, "pop_r", 5), ["pearson", "spearman", "mae", "rmse", "bias"]),
        "",
        "### POP — todas as células disponíveis",
        "",
        table(lallpi_validation(wide, lallpi, "pop"), ["pearson", "spearman", "mae", "rmse", "bias"]),
        "",
        "### POP — células com pelo menos 5 discursos",
        "",
        table(lallpi_validation(wide, lallpi, "pop", 5), ["pearson", "spearman", "mae", "rmse", "bias"]),
        "",
        "## 5. Top 10 líderes — mínimo de 10 discursos",
        "",
    ]
    for model in MODELS:
        lines += [f"### {model}", "", table(leader_table(wide, model), ["Média", "DP", "SE"]), ""]
    lines += [
        "## 6. Comparação conjunta por líder",
        "",
        "Líderes com pelo menos 10 discursos. O GPD aparece somente quando há termo no teste bloqueado; `SE` é o erro-padrão da média dos discursos.",
        "",
        table(leader_comparison(wide), ["Qwen", "SE Qwen", "DeepSeek", "SE DeepSeek", "Luna", "SE Luna", "GPD"]),
        "",
    ]
    lines += [
        "## 7. Leitura correta",
        "",
        "- Luna deve ser comparado com os demais principalmente por ordenação, correlação e validade convergente; os níveis absolutos não são intercambiáveis.",
        "- GPD é a validação mais próxima do construto, pois opera no nível líder–mandato e deriva de codificação humana.",
        "- LALLPI é validação externa contextual no nível país–ano, não codificação discurso a discurso.",
        "- O erro-padrão dos rankings por líder mede a incerteza da média amostral e não a incerteza total do modelo.",
    ]
    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT_PATH)
    print("\nDISTRIBUIÇÃO")
    print(table(distribution(wide), ["Média", "DP", "Mediana", "Mínimo", "Máximo", "% >= 50", "% = 0"]))
    print("\nMODELOS")
    print(table(pairwise(wide), ["pearson", "spearman", "mae", "rmse", "bias"]))
    print("\nGPD")
    print(table(gpd_validation(wide), ["pearson", "spearman", "mae", "rmse", "bias"]))
    print("\nLALLPI POP_R")
    print(table(lallpi_validation(wide, lallpi, "pop_r"), ["pearson", "spearman", "mae", "rmse", "bias"]))
    print("\nLÍDERES — TOP 15 POR LUNA")
    print(table(leader_comparison(wide).head(15), ["Qwen", "SE Qwen", "DeepSeek", "SE DeepSeek", "Luna", "SE Luna", "GPD"]))


if __name__ == "__main__":
    main()
