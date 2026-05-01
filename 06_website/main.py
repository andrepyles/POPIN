"""
POPIN v4 — Web Application Backend
Uso: python -m uvicorn main:app --port 8000
     (rodar da pasta 06_website)
Acesse: http://localhost:8000
"""
import os
from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

HERE = Path(__file__).parent
load_dotenv(HERE.parent / ".env")
_db_env = os.getenv("DB_PATH", "")
# Slim web DB (preferred) — fall back to full DB for local dev
_slim = HERE / "popin_web.duckdb"
if _slim.exists() and not _db_env:
    DB_PATH = str(_slim)
elif _db_env:
    DB_PATH = str((HERE.parent / _db_env).resolve()) if not Path(_db_env).is_absolute() else _db_env
else:
    DB_PATH = str(HERE.parent / "popin.duckdb")

DIMENSIONS = ["people_centrism", "anti_elitism", "moral_dichotomy",
              "popular_sovereignty", "exclusionary_rhetoric", "crisis_rhetoric"]

COUNTRY_NAMES = {
    "ARG": "Argentina",   "BOL": "Bolivia",       "BRA": "Brazil",
    "CHL": "Chile",       "COL": "Colombia",      "CRI": "Costa Rica",
    "CUB": "Cuba",        "DOM": "Dom. Republic", "ECU": "Ecuador",
    "GTM": "Guatemala",   "HND": "Honduras",      "MEX": "Mexico",
    "NIC": "Nicaragua",   "PAN": "Panama",        "PER": "Peru",
    "PRY": "Paraguay",    "SLV": "El Salvador",   "URY": "Uruguay",
    "VEN": "Venezuela",
}

# ── Load all data at startup ───────────────────────────────────────────────────

def load_data():
    con = duckdb.connect(DB_PATH, read_only=True)
    # web_data = slim table (popin_web.duckdb); fallback to full join
    tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if "web_data" in tables:
        query = "SELECT * FROM web_data"
    else:
        query = """
            SELECT s.people_centrism, s.anti_elitism, s.moral_dichotomy,
                   s.popular_sovereignty, s.exclusionary_rhetoric,
                   s.crisis_rhetoric, s.final_score, s.n_chunks,
                   d.iso3, d.leader_name,
                   d.discourse_year AS year,
                   d.dtype, d.word_count
            FROM scores s
            JOIN discourses d ON d.id = s.discourse_id
            WHERE s.final_score IS NOT NULL AND d.dtype != 'INVALID'
        """
    df = con.execute(query).fetchdf()
    con.close()
    df["country"] = df["iso3"].map(COUNTRY_NAMES).fillna(df["iso3"])
    df["leader_short"] = df["leader_name"].apply(
        lambda n: " ".join(n.split()[:2]) if len(n.split()) > 3 else n)
    return df

df = load_data()

# ── Helper ─────────────────────────────────────────────────────────────────────

def _sub(dtype: str = "") -> pd.DataFrame:
    """Filter df by discourse type. Empty/ALL = no filter."""
    if dtype and dtype != "ALL":
        return df[df["dtype"] == dtype]
    return df

def _agg_countries(sub: pd.DataFrame):
    return (sub.groupby(["iso3", "country"])
               .agg(n=("final_score", "count"),
                    **{d: (d, "mean") for d in DIMENSIONS},
                    final_score=("final_score", "mean"))
               .reset_index().sort_values("final_score", ascending=False))

def _agg_leaders(sub: pd.DataFrame):
    return (sub.groupby(["leader_name", "leader_short", "iso3", "country"])
               .agg(n=("final_score", "count"),
                    **{d: (d, "mean") for d in DIMENSIONS},
                    final_score=("final_score", "mean"))
               .reset_index().sort_values("n", ascending=False))

# Pre-compute for ALL (fast path)
leaders_agg    = _agg_leaders(df)
countries_agg  = _agg_countries(df)
yearly_global  = (df.groupby("year")
                    .agg(n=("final_score","count"),
                         **{d:(d,"mean") for d in DIMENSIONS},
                         final_score=("final_score","mean"))
                    .reset_index().sort_values("year"))

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="POPIN v4")
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

@app.get("/")
def root():
    return FileResponse(HERE / "static" / "index.html")

@app.get("/api/dtypes")
def api_dtypes():
    counts = df.groupby("dtype")["final_score"].count().sort_values(ascending=False)
    return [{"dtype": k, "n": int(v)} for k, v in counts.items()]

@app.get("/api/stats")
def stats(dtype: str = Query(default="")):
    sub = _sub(dtype)
    ca  = _agg_countries(sub)
    la  = _agg_leaders(sub)
    top_c = ca.nlargest(1, "final_score").iloc[0]
    top_l = la.nlargest(1, "final_score").iloc[0]
    return {
        "n_discourses": int(len(sub)),
        "n_countries":  int(sub["iso3"].nunique()),
        "n_leaders":    int(sub["leader_name"].nunique()),
        "year_min":     int(sub["year"].min()),
        "year_max":     int(sub["year"].max()),
        "avg_score":    round(float(sub["final_score"].mean()), 2),
        "top_country":  {"name": top_c["country"], "score": round(float(top_c["final_score"]), 1)},
        "top_leader":   {"name": top_l["leader_short"], "score": round(float(top_l["final_score"]), 1)},
        "dim_avgs":     {d: round(float(sub[d].mean()), 2) for d in DIMENSIONS},
    }

@app.get("/api/countries")
def api_countries(dtype: str = Query(default="")):
    return _agg_countries(_sub(dtype)).round(2).to_dict("records")

@app.get("/api/yearly_global")
def api_yearly_global(dtype: str = Query(default="")):
    sub = _sub(dtype)
    yg = (sub.groupby("year")
             .agg(n=("final_score","count"),
                  **{d:(d,"mean") for d in DIMENSIONS},
                  final_score=("final_score","mean"))
             .reset_index().sort_values("year"))
    return yg.round(2).to_dict("records")

@app.get("/api/yearly")
def api_yearly(
    countries: str = Query(default=""),
    dim: str = Query(default="final_score"),
    dtype: str = Query(default=""),
):
    col = dim if dim in DIMENSIONS + ["final_score"] else "final_score"
    sub = _sub(dtype)
    if countries:
        sel = [c.strip() for c in countries.split(",") if c.strip()]
        if sel:
            sub = sub[sub["iso3"].isin(sel)]
    agg = (sub.groupby(["iso3", "country", "year"])[col]
              .mean().reset_index().rename(columns={col: "score"}))
    return agg.round(2).to_dict("records")

@app.get("/api/leaders")
def api_leaders(
    country: str = Query(default="ALL"),
    n: int = Query(default=25),
    dtype: str = Query(default=""),
):
    sub = _sub(dtype)
    la  = _agg_leaders(sub)
    if country != "ALL":
        la = la[la["iso3"] == country]
    return la.nlargest(n, "final_score").round(2).to_dict("records")

@app.get("/api/leader_trend")
def api_leader_trend(names: str = Query(default=""), dtype: str = Query(default="")):
    sel = [n.strip() for n in names.split("|") if n.strip()]
    if not sel:
        return []
    sub = _sub(dtype)
    sub = sub[sub["leader_name"].isin(sel)]
    agg = (sub.groupby(["leader_name", "leader_short", "year"])["final_score"]
              .mean().reset_index().round(2))
    return agg.to_dict("records")

@app.get("/api/distribution")
def api_distribution(
    dim: str = Query(default="final_score"),
    group: str = Query(default="country"),
    year_min: int = Query(default=2000),
    year_max: int = Query(default=2025),
    dtype: str = Query(default=""),
):
    col = dim if dim in DIMENSIONS + ["final_score"] else "final_score"
    sub = _sub(dtype)
    sub = sub[sub["year"].between(year_min, year_max)].copy()
    grp_col = "country" if group == "country" else "dtype"
    result = []
    for gv, g in sub.groupby(grp_col):
        s = g[col].dropna()
        if len(s) < 5:
            continue
        result.append({
            "group": gv, "min": round(float(s.min()), 2),
            "q1": round(float(s.quantile(.25)), 2),
            "median": round(float(s.median()), 2),
            "q3": round(float(s.quantile(.75)), 2),
            "max": round(float(s.max()), 2),
            "mean": round(float(s.mean()), 2),
            "n": int(len(s)),
        })
    result.sort(key=lambda x: x["mean"], reverse=True)
    return result

@app.get("/api/dim_country")
def api_dim_country(dtype: str = Query(default="")):
    """Returns per-country mean for all 6 dimensions + final_score."""
    return _agg_countries(_sub(dtype)).round(2).to_dict("records")
