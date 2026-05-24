"""
POPIN v4 — Dashboard interativo de visualização
Uso: python 05_dashboard.py
Acesse: http://localhost:8050
"""

import os
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, callback
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "./popin.duckdb")

# ── Paleta & constantes ───────────────────────────────────────────────────────

ACCENT   = "#C0392B"          # vermelho escuro
BG       = "#0F1117"          # fundo escuro
CARD_BG  = "#1A1D27"          # card
BORDER   = "#2A2D3E"
TEXT     = "#E8E8F0"
MUTED    = "#8B8FA8"
SUCCESS  = "#27AE60"
WARNING  = "#F39C12"

SEQ_SCALE  = [[0.0, "#1a4a6b"], [0.5, "#e8c547"], [1.0, "#C0392B"]]
COUNTRY_COLORS = px.colors.qualitative.Bold + px.colors.qualitative.Pastel

DIMENSIONS = ["people_centrism", "anti_elitism", "moral_dichotomy",
              "popular_sovereignty", "exclusionary_rhetoric", "crisis_rhetoric"]

DIM_LABELS = {
    "people_centrism":       "People Centrism",
    "anti_elitism":          "Anti-Elitism",
    "moral_dichotomy":       "Moral Dichotomy",
    "popular_sovereignty":   "Popular Sovereignty",
    "exclusionary_rhetoric": "Exclusionary Rhetoric",
    "crisis_rhetoric":       "Crisis Rhetoric",
    "final_score":           "Final Score (avg)",
}

COUNTRY_NAMES = {
    "ARG": "Argentina", "BOL": "Bolivia", "BRA": "Brazil",
    "CHL": "Chile",     "COL": "Colombia", "CRI": "Costa Rica",
    "DOM": "Dom. Republic", "ECU": "Ecuador", "GTM": "Guatemala",
    "HND": "Honduras",  "MEX": "Mexico",   "NIC": "Nicaragua",
    "PAN": "Panama",    "PER": "Peru",     "PRY": "Paraguay",
    "SLV": "El Salvador", "URY": "Uruguay", "VEN": "Venezuela",
}

LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=TEXT, size=12),
    margin=dict(l=0, r=0, t=36, b=0),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER),
    xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, tickfont=dict(color=MUTED)),
    yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, tickfont=dict(color=MUTED)),
)

# ── Carrega dados ─────────────────────────────────────────────────────────────

def load_data():
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("""
        SELECT s.discourse_id,
               s.people_centrism, s.anti_elitism, s.moral_dichotomy,
               s.popular_sovereignty, s.exclusionary_rhetoric,
               s.crisis_rhetoric, s.final_score, s.n_chunks,
               d.iso3, d.leader_name,
               d.discourse_year AS year,
               d.dtype, d.language, d.word_count
        FROM scores s
        JOIN discourses d ON d.id = s.discourse_id
        WHERE s.final_score IS NOT NULL AND d.dtype != 'INVALID'
    """).fetchdf()
    con.close()
    df["country"] = df["iso3"].map(COUNTRY_NAMES).fillna(df["iso3"])
    # shorten leader names
    df["leader_short"] = df["leader_name"].apply(
        lambda n: " ".join(n.split()[:2]) if len(n.split()) > 3 else n
    )
    return df

df = load_data()

# Aggregate tables
leaders_agg = (df.groupby(["leader_name","leader_short","iso3","country"])
                 .agg(n=("final_score","count"),
                      **{d: (d,"mean") for d in DIMENSIONS},
                      final_score=("final_score","mean"))
                 .reset_index().sort_values("n", ascending=False))

countries_agg = (df.groupby(["iso3","country"])
                   .agg(n=("final_score","count"),
                        **{d: (d,"mean") for d in DIMENSIONS},
                        final_score=("final_score","mean"))
                   .reset_index().sort_values("final_score", ascending=False))

yearly_agg = (df.groupby("year")
                .agg(n=("final_score","count"),
                     **{d: (d,"mean") for d in DIMENSIONS},
                     final_score=("final_score","mean"))
                .reset_index().sort_values("year"))

all_countries = sorted(df["iso3"].unique())
all_leaders   = sorted(df["leader_name"].unique())
all_dtypes    = sorted(df["dtype"].dropna().unique())
year_min, year_max = int(df["year"].min()), int(df["year"].max())

# ── Helpers ───────────────────────────────────────────────────────────────────

def card(children, style=None):
    s = {"background": CARD_BG, "border": f"1px solid {BORDER}",
         "borderRadius": "12px", "padding": "20px", "marginBottom": "16px"}
    if style:
        s.update(style)
    return html.Div(children, style=s)

def kpi(label, value, sub=None, color=TEXT):
    return html.Div([
        html.Div(value, style={"fontSize":"32px","fontWeight":"700","color":color,"lineHeight":"1"}),
        html.Div(label, style={"fontSize":"12px","color":MUTED,"marginTop":"4px","textTransform":"uppercase","letterSpacing":"0.08em"}),
        html.Div(sub, style={"fontSize":"11px","color":MUTED,"marginTop":"2px"}) if sub else None,
    ], style={"background":CARD_BG,"border":f"1px solid {BORDER}","borderRadius":"12px",
              "padding":"20px 24px","flex":"1","minWidth":"140px"})

def section_title(text):
    return html.H3(text, style={"color":TEXT,"fontWeight":"600","fontSize":"15px",
                                 "margin":"0 0 14px 0","letterSpacing":"0.02em"})

def fig_layout(fig, height=None, **kwargs):
    upd = dict(**LAYOUT_BASE)
    upd.update(kwargs)
    if height:
        upd["height"] = height
    # patch nested dicts
    if "xaxis" in kwargs:
        d = dict(LAYOUT_BASE["xaxis"]); d.update(kwargs["xaxis"]); upd["xaxis"] = d
    if "yaxis" in kwargs:
        d = dict(LAYOUT_BASE["yaxis"]); d.update(kwargs["yaxis"]); upd["yaxis"] = d
    fig.update_layout(**upd)
    return fig

def dropdown_style():
    return {
        "backgroundColor": CARD_BG, "border": f"1px solid {BORDER}",
        "borderRadius": "8px", "color": TEXT, "minWidth": "200px",
    }

def label(text):
    return html.Div(text, style={"color":MUTED,"fontSize":"12px","marginBottom":"4px",
                                  "textTransform":"uppercase","letterSpacing":"0.06em"})

# ── App layout ────────────────────────────────────────────────────────────────

app = dash.Dash(__name__, title="POPIN v4", suppress_callback_exceptions=True)

HEADER = html.Div([
    html.Div([
        html.Div([
            html.Span("POPIN", style={"color":ACCENT,"fontWeight":"800","fontSize":"22px"}),
            html.Span(" v4", style={"color":MUTED,"fontWeight":"300","fontSize":"16px"}),
        ]),
        html.Div("Populism Index for Latin America",
                 style={"color":MUTED,"fontSize":"13px","marginTop":"2px"}),
    ]),
    html.Div([
        html.Span(f"{len(df):,} discourses", style={"color":TEXT,"fontSize":"13px","marginRight":"24px"}),
        html.Span(f"{df['iso3'].nunique()} countries", style={"color":TEXT,"fontSize":"13px","marginRight":"24px"}),
        html.Span(f"{df['leader_name'].nunique()} leaders", style={"color":TEXT,"fontSize":"13px","marginRight":"24px"}),
        html.Span(f"{year_min}–{year_max}", style={"color":MUTED,"fontSize":"13px"}),
    ], style={"display":"flex","alignItems":"center"}),
], style={"background":CARD_BG,"borderBottom":f"1px solid {BORDER}",
          "padding":"16px 32px","display":"flex","alignItems":"center",
          "justifyContent":"space-between"})

NAV_ITEMS = [
    ("overview",     "Overview"),
    ("timeseries",   "Time Series"),
    ("leaders",      "Leaders"),
    ("countries",    "Countries"),
    ("distributions","Distributions"),
]

NAV = html.Div([
    html.Div([
        html.A(label, href="#", id=f"nav-{tab}",
               className="nav-link",
               **{"data-tab": tab},
               style={"color":TEXT if i==0 else MUTED,
                      "textDecoration":"none","fontSize":"13px","fontWeight":"600" if i==0 else "400",
                      "padding":"8px 16px","borderRadius":"6px",
                      "background": f"rgba(192,57,43,0.15)" if i==0 else "transparent",
                      "cursor":"pointer"})
        for i, (tab, label) in enumerate(NAV_ITEMS)
    ] + [
        dcc.Store(id="active-tab", data="overview"),
    ], style={"display":"flex","gap":"4px","padding":"12px 32px",
              "borderBottom":f"1px solid {BORDER}","background":BG}),
])

TABS = dcc.Tabs(
    id="tabs", value="overview",
    children=[dcc.Tab(label=lbl, value=tab) for tab, lbl in NAV_ITEMS],
    style={"background":BG,"borderBottom":f"1px solid {BORDER}","paddingLeft":"24px"},
    colors={"border":BORDER,"primary":ACCENT,"background":BG},
)

app.layout = html.Div([
    # Google Fonts
    html.Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"),
    HEADER,
    TABS,
    html.Div(id="tab-content", style={"padding":"24px 32px","maxWidth":"1400px","margin":"0 auto"}),
], style={"background":BG,"minHeight":"100vh","fontFamily":"Inter, sans-serif","color":TEXT})


# ── Tab router ────────────────────────────────────────────────────────────────

@callback(Output("tab-content","children"), Input("tabs","value"))
def render_tab(tab):
    if tab == "overview":      return render_overview()
    if tab == "timeseries":    return render_timeseries()
    if tab == "leaders":       return render_leaders()
    if tab == "countries":     return render_countries()
    if tab == "distributions": return render_distributions()


# ── Overview ──────────────────────────────────────────────────────────────────

def render_overview():
    avg_fs = df["final_score"].mean()
    top_country = countries_agg.iloc[0]
    top_leader  = leaders_agg.nlargest(1,"final_score").iloc[0]
    most_active = leaders_agg.nlargest(1,"n").iloc[0]

    kpis = html.Div([
        kpi("Total Discourses",  f"{len(df):,}", f"Scored by Qwen3-30B"),
        kpi("Countries",         str(df["iso3"].nunique()), "Latin America"),
        kpi("Leaders",           str(df["leader_name"].nunique()), f"{year_min}–{year_max}"),
        kpi("Avg Populism Score", f"{avg_fs:.1f}", "out of 100", color=ACCENT),
        kpi("Highest Country",   top_country["country"], f"Score: {top_country['final_score']:.1f}", color=WARNING),
        kpi("Most Populist Leader", top_leader["leader_short"], f"Score: {top_leader['final_score']:.1f}", color=ACCENT),
    ], style={"display":"flex","gap":"12px","flexWrap":"wrap","marginBottom":"20px"})

    # Bar chart — countries
    fig_bar = go.Figure()
    cdf = countries_agg.sort_values("final_score", ascending=True)
    fig_bar.add_trace(go.Bar(
        x=cdf["final_score"], y=cdf["country"],
        orientation="h",
        marker=dict(color=cdf["final_score"], colorscale=SEQ_SCALE,
                    cmin=0, cmax=70,
                    colorbar=dict(title="Score", tickfont=dict(color=MUTED), len=0.6)),
        text=cdf["final_score"].round(1),
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
        hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>",
    ))
    fig_bar = fig_layout(fig_bar, height=440, title="Average Populism Score by Country",
                         xaxis={"range":[0,80], "title":""},
                         yaxis={"title":""})

    # Scatter — people_centrism vs anti_elitism
    top30 = leaders_agg.head(30).copy()
    top30["country_label"] = top30["iso3"].map(COUNTRY_NAMES).fillna(top30["iso3"])
    iso3_list = sorted(top30["iso3"].unique())
    color_map = {iso3: COUNTRY_COLORS[i % len(COUNTRY_COLORS)] for i, iso3 in enumerate(iso3_list)}
    fig_sc = go.Figure()
    for iso3, grp in top30.groupby("iso3"):
        fig_sc.add_trace(go.Scatter(
            x=grp["people_centrism"], y=grp["anti_elitism"],
            mode="markers",
            marker=dict(size=grp["n"] / grp["n"].max() * 40 + 8,
                        color=color_map.get(iso3, "#888"),
                        line=dict(width=1, color=BG), opacity=0.85),
            name=COUNTRY_NAMES.get(iso3, iso3),
            text=grp["leader_short"],
            hovertemplate="<b>%{text}</b><br>People Centrism: %{x:.1f}<br>Anti-Elitism: %{y:.1f}<extra></extra>",
        ))
    fig_sc = fig_layout(fig_sc, height=440,
                        title="People Centrism vs Anti-Elitism (top 30 leaders by volume)",
                        xaxis={"title":"People Centrism","range":[0,100]},
                        yaxis={"title":"Anti-Elitism","range":[0,100]})
    fig_sc.add_shape(type="line", x0=0,y0=0,x1=100,y1=100,
                     line=dict(color=BORDER, width=1, dash="dot"))

    # Line — global trend
    fig_trend = go.Figure()
    for dim in DIMENSIONS:
        fig_trend.add_trace(go.Scatter(
            x=yearly_agg["year"], y=yearly_agg[dim].round(2),
            name=DIM_LABELS[dim], mode="lines",
            line=dict(width=2), opacity=0.8,
            hovertemplate=f"<b>{DIM_LABELS[dim]}</b><br>Year: %{{x}}<br>Score: %{{y:.1f}}<extra></extra>",
        ))
    fig_trend.add_trace(go.Scatter(
        x=yearly_agg["year"], y=yearly_agg["final_score"].round(2),
        name="Final Score", mode="lines+markers",
        line=dict(width=3, color=ACCENT),
        marker=dict(size=5),
        hovertemplate="<b>Final Score</b><br>Year: %{x}<br>Score: %{y:.1f}<extra></extra>",
    ))
    fig_trend = fig_layout(fig_trend, height=320,
                           title="Global Populism Trend 2000–2024",
                           xaxis={"title":""},
                           yaxis={"title":"Score","range":[0,80]})
    fig_trend.update_layout(hovermode="x unified")

    return html.Div([
        kpis,
        html.Div([
            card(dcc.Graph(figure=fig_bar,  config={"displayModeBar":False}), {"flex":"1"}),
            card(dcc.Graph(figure=fig_sc,   config={"displayModeBar":False}), {"flex":"1"}),
        ], style={"display":"flex","gap":"16px"}),
        card(dcc.Graph(figure=fig_trend, config={"displayModeBar":False})),
    ])


# ── Time Series ───────────────────────────────────────────────────────────────

def render_timeseries():
    ctrl = card(html.Div([
        html.Div([
            label("Countries"),
            dcc.Dropdown(id="ts-countries",
                options=[{"label": COUNTRY_NAMES.get(c,c), "value": c} for c in all_countries],
                value=["BRA","VEN","ARG","MEX","COL"],
                multi=True, style=dropdown_style()),
        ], style={"flex":"2"}),
        html.Div([
            label("Dimension"),
            dcc.Dropdown(id="ts-dim",
                options=[{"label":v,"value":k} for k,v in DIM_LABELS.items()],
                value="final_score", clearable=False, style=dropdown_style()),
        ], style={"flex":"1"}),
        html.Div([
            label("Discourse Type"),
            dcc.Dropdown(id="ts-dtype",
                options=[{"label":"All","value":"ALL"}] +
                        [{"label":d,"value":d} for d in all_dtypes],
                value="ALL", clearable=False, style=dropdown_style()),
        ], style={"flex":"1"}),
        html.Div([
            label("Year Range"),
            dcc.RangeSlider(id="ts-years", min=year_min, max=year_max,
                value=[year_min, year_max],
                marks={y: str(y) for y in range(year_min, year_max+1, 4)},
                step=1, tooltip={"placement":"bottom"},
                className="range-slider"),
        ], style={"flex":"2"}),
    ], style={"display":"flex","gap":"20px","alignItems":"flex-end","flexWrap":"wrap"}))

    return html.Div([
        ctrl,
        card(dcc.Graph(id="ts-line",    config={"displayModeBar":False}, style={"height":"420px"})),
        html.Div([
            card(dcc.Graph(id="ts-heatmap", config={"displayModeBar":False}, style={"height":"340px"}), {"flex":"1"}),
            card(dcc.Graph(id="ts-area",    config={"displayModeBar":False}, style={"height":"340px"}), {"flex":"1"}),
        ], style={"display":"flex","gap":"16px"}),
    ])


@callback(
    Output("ts-line","figure"), Output("ts-heatmap","figure"), Output("ts-area","figure"),
    Input("ts-countries","value"), Input("ts-dim","value"),
    Input("ts-dtype","value"), Input("ts-years","value"),
)
def update_ts(sel_countries, dim, dtype, yr):
    sel_countries = sel_countries or all_countries[:5]
    y0, y1 = yr
    sub = df[(df["iso3"].isin(sel_countries)) & (df["year"].between(y0,y1))]
    if dtype != "ALL":
        sub = sub[sub["dtype"] == dtype]

    agg = (sub.groupby(["iso3","year"])[dim].mean().reset_index()
              .rename(columns={dim:"score"}))
    agg["country"] = agg["iso3"].map(COUNTRY_NAMES).fillna(agg["iso3"])

    iso3_list = sorted(agg["iso3"].unique())
    cmap = {iso3: COUNTRY_COLORS[i % len(COUNTRY_COLORS)] for i, iso3 in enumerate(iso3_list)}

    # Line
    fig_line = go.Figure()
    for iso3, grp in agg.groupby("iso3"):
        fig_line.add_trace(go.Scatter(
            x=grp["year"], y=grp["score"].round(2),
            name=COUNTRY_NAMES.get(iso3,iso3), mode="lines+markers",
            line=dict(width=2.5, color=cmap.get(iso3,"#888")),
            marker=dict(size=5),
            hovertemplate=f"<b>{COUNTRY_NAMES.get(iso3,iso3)}</b><br>%{{x}}: %{{y:.1f}}<extra></extra>",
        ))
    fig_line = fig_layout(fig_line, title=f"{DIM_LABELS.get(dim,dim)} over Time",
                          xaxis={"title":""},
                          yaxis={"title":"Score","range":[0,100]})
    fig_line.update_layout(hovermode="x unified")

    # Heatmap
    pivot = agg.pivot(index="country", columns="year", values="score").round(1)
    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=SEQ_SCALE, zmin=0, zmax=100,
        hoverongaps=False, text=pivot.values.round(1),
        texttemplate="%{text}",
        colorbar=dict(tickfont=dict(color=MUTED)),
        hovertemplate="<b>%{y}</b> · %{x}<br>Score: %{z:.1f}<extra></extra>",
    ))
    fig_heat = fig_layout(fig_heat, title="Heatmap: Score by Country & Year")
    fig_heat.update_layout(xaxis=dict(tickfont=dict(color=MUTED)),
                           yaxis=dict(tickfont=dict(color=MUTED)))

    # Area (stacked normalized)
    fig_area = go.Figure()
    for iso3, grp in agg.groupby("iso3"):
        fig_area.add_trace(go.Scatter(
            x=grp["year"], y=grp["score"].round(2),
            name=COUNTRY_NAMES.get(iso3,iso3),
            fill="tonexty", mode="lines",
            line=dict(width=0.5, color=cmap.get(iso3,"#888")),
            stackgroup="one",
            hovertemplate=f"<b>{COUNTRY_NAMES.get(iso3,iso3)}</b>: %{{y:.1f}}<extra></extra>",
        ))
    fig_area = fig_layout(fig_area, title="Stacked Area (relative contribution)",
                          xaxis={"title":""},
                          yaxis={"title":"Cumulative Score"})
    return fig_line, fig_heat, fig_area


# ── Leaders ───────────────────────────────────────────────────────────────────

def render_leaders():
    ctrl = card(html.Div([
        html.Div([
            label("Filter by Country"),
            dcc.Dropdown(id="ldr-country",
                options=[{"label":"All Countries","value":"ALL"}] +
                        [{"label":COUNTRY_NAMES.get(c,c),"value":c} for c in all_countries],
                value="ALL", clearable=False, style=dropdown_style()),
        ], style={"flex":"1"}),
        html.Div([
            label("Top N Leaders (ranking)"),
            dcc.Slider(id="ldr-topn", min=5, max=25, step=5, value=15,
                marks={n: str(n) for n in [5,10,15,20,25]}),
        ], style={"flex":"1"}),
        html.Div([
            label("Compare Leaders (radar & timeline)"),
            dcc.Dropdown(id="ldr-radar",
                options=[{"label":l,"value":l} for l in all_leaders],
                value=["Hugo Rafael Chávez Frías","Luiz Inácio Lula da Silva",
                       "Nayib Armando Bukele Ortez","Nicolás Maduro"],
                multi=True, style=dropdown_style()),
        ], style={"flex":"2"}),
    ], style={"display":"flex","gap":"20px","alignItems":"flex-end","flexWrap":"wrap"}))

    return html.Div([
        ctrl,
        html.Div([
            card(dcc.Graph(id="ldr-bar",   config={"displayModeBar":False}, style={"height":"460px"}), {"flex":"1"}),
            card(dcc.Graph(id="ldr-radar", config={"displayModeBar":False}, style={"height":"460px"}), {"flex":"1"}),
        ], style={"display":"flex","gap":"16px"}),
        card(dcc.Graph(id="ldr-timeline",  config={"displayModeBar":False}, style={"height":"380px"})),
        card(dcc.Graph(id="ldr-dims",      config={"displayModeBar":False}, style={"height":"380px"})),
    ])


@callback(
    Output("ldr-bar","figure"), Output("ldr-radar","figure"),
    Output("ldr-timeline","figure"), Output("ldr-dims","figure"),
    Input("ldr-country","value"), Input("ldr-topn","value"),
    Input("ldr-radar","value"),
)
def update_leaders(country, topn, radar_sel):
    sub = leaders_agg if country == "ALL" else leaders_agg[leaders_agg["iso3"] == country]
    top = sub.nlargest(topn, "final_score")

    # Horizontal bar
    fig_bar = go.Figure(go.Bar(
        x=top["final_score"].round(1), y=top["leader_short"],
        orientation="h",
        marker=dict(color=top["final_score"], colorscale=SEQ_SCALE, cmin=0, cmax=80,
                    colorbar=dict(tickfont=dict(color=MUTED), len=0.5)),
        text=top["final_score"].round(1), textposition="outside",
        textfont=dict(color=TEXT, size=11),
        customdata=top[["country","n"]],
        hovertemplate="<b>%{y}</b><br>%{customdata[0]}<br>Score: %{x:.1f}<br>Discourses: %{customdata[1]:,}<extra></extra>",
    ))
    fig_bar = fig_layout(fig_bar, title=f"Top {topn} Leaders — Final Score",
                         xaxis={"range":[0,85],"title":""},
                         yaxis={"categoryorder":"total ascending","title":""})

    # Radar
    radar_sel = radar_sel or []
    fig_radar = go.Figure()
    dim_names_r = [DIM_LABELS[d] for d in DIMENSIONS] + [DIM_LABELS[DIMENSIONS[0]]]
    for i, ldr in enumerate(radar_sel[:6]):
        row = leaders_agg[leaders_agg["leader_name"] == ldr]
        if row.empty: continue
        vals = [row[d].values[0] for d in DIMENSIONS] + [row[DIMENSIONS[0]].values[0]]
        fig_radar.add_trace(go.Scatterpolar(
            r=[round(v,1) for v in vals], theta=dim_names_r,
            name=row["leader_short"].values[0],
            fill="toself", opacity=0.55,
            line=dict(color=COUNTRY_COLORS[i % len(COUNTRY_COLORS)], width=2),
        ))
    fig_radar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT, size=11),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(range=[0,100], gridcolor=BORDER, tickfont=dict(color=MUTED, size=9)),
            angularaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT, size=11)),
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)),
        margin=dict(l=60, r=60, t=40, b=40),
        title=dict(text="Populism Dimensions Radar", font=dict(color=TEXT)),
    )

    # Timeline
    radar_sel2 = (radar_sel or [])[:5]
    sub2 = df[df["leader_name"].isin(radar_sel2)]
    agg2 = sub2.groupby(["leader_name","leader_short","year"])["final_score"].mean().reset_index()
    fig_time = go.Figure()
    for i, (ldr, grp) in enumerate(agg2.groupby("leader_name")):
        short = grp["leader_short"].iloc[0]
        fig_time.add_trace(go.Scatter(
            x=grp["year"], y=grp["final_score"].round(2),
            name=short, mode="lines+markers",
            line=dict(width=2.5, color=COUNTRY_COLORS[i % len(COUNTRY_COLORS)]),
            marker=dict(size=6),
            hovertemplate=f"<b>{short}</b><br>%{{x}}: %{{y:.1f}}<extra></extra>",
        ))
    fig_time = fig_layout(fig_time, title="Score Evolution over Time",
                          xaxis={"title":""},
                          yaxis={"title":"Final Score","range":[0,100]})
    fig_time.update_layout(hovermode="x unified")

    # Grouped bar: all dims per leader
    rows = []
    for ldr in radar_sel2:
        row = leaders_agg[leaders_agg["leader_name"]==ldr]
        if row.empty: continue
        for d in DIMENSIONS:
            rows.append({"leader": row["leader_short"].values[0],
                         "dim": DIM_LABELS[d], "score": round(row[d].values[0],1)})
    df_dims = pd.DataFrame(rows)
    fig_dims = go.Figure()
    if not df_dims.empty:
        for i, ldr in enumerate(df_dims["leader"].unique()):
            sub_d = df_dims[df_dims["leader"]==ldr]
            fig_dims.add_trace(go.Bar(
                x=sub_d["dim"], y=sub_d["score"],
                name=ldr,
                marker_color=COUNTRY_COLORS[i % len(COUNTRY_COLORS)],
                hovertemplate=f"<b>{ldr}</b><br>%{{x}}: %{{y:.1f}}<extra></extra>",
            ))
    fig_dims = fig_layout(fig_dims, title="Dimension Breakdown by Leader",
                          xaxis={"title":""},
                          yaxis={"title":"Score","range":[0,100]})
    fig_dims.update_layout(barmode="group")
    return fig_bar, fig_radar, fig_time, fig_dims


# ── Countries ─────────────────────────────────────────────────────────────────

def render_countries():
    # Heatmap
    heat = countries_agg.set_index("country")[[*DIMENSIONS]].round(1)
    fig_heat = go.Figure(go.Heatmap(
        z=heat.values, x=[DIM_LABELS[d] for d in DIMENSIONS], y=heat.index.tolist(),
        colorscale=SEQ_SCALE, zmin=0, zmax=80,
        text=heat.values.round(1), texttemplate="%{text}",
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.1f}<extra></extra>",
        colorbar=dict(tickfont=dict(color=MUTED)),
    ))
    fig_heat = fig_layout(fig_heat, height=520,
                          title="Country × Dimension Heatmap")
    fig_heat.update_layout(
        xaxis=dict(tickfont=dict(color=TEXT, size=11)),
        yaxis=dict(tickfont=dict(color=TEXT, size=11)),
    )

    # Radar: countries
    fig_cr = go.Figure()
    dim_names_r = [DIM_LABELS[d] for d in DIMENSIONS] + [DIM_LABELS[DIMENSIONS[0]]]
    for i, row in countries_agg.iterrows():
        vals = [row[d] for d in DIMENSIONS] + [row[DIMENSIONS[0]]]
        fig_cr.add_trace(go.Scatterpolar(
            r=[round(v,1) for v in vals], theta=dim_names_r,
            name=row["country"], fill="toself", opacity=0.4,
            line=dict(width=1.5, color=COUNTRY_COLORS[i % len(COUNTRY_COLORS)]),
        ))
    fig_cr.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT, size=11),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(range=[0,100], gridcolor=BORDER, tickfont=dict(color=MUTED,size=9)),
            angularaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT,size=11)),
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT, size=10)),
        margin=dict(l=60,r=60,t=40,b=40),
        title=dict(text="Country Profiles (Radar)", font=dict(color=TEXT)),
        height=540,
    )

    # Grouped bar
    melt = countries_agg.melt(id_vars=["iso3","country"], value_vars=DIMENSIONS,
                               var_name="dim", value_name="score")
    melt["dim"] = melt["dim"].map(DIM_LABELS)
    fig_grp = px.bar(melt, x="country", y="score", color="dim", barmode="group",
                     color_discrete_sequence=COUNTRY_COLORS,
                     labels={"country":"","score":"Score","dim":"Dimension"},
                     title="All Dimensions by Country")
    fig_grp = fig_layout(fig_grp, height=400, xaxis={"title":""},
                         yaxis={"title":"Score","range":[0,90]})

    return html.Div([
        html.Div([
            card(dcc.Graph(figure=fig_heat, config={"displayModeBar":False}), {"flex":"1"}),
            card(dcc.Graph(figure=fig_cr,   config={"displayModeBar":False}), {"flex":"1"}),
        ], style={"display":"flex","gap":"16px"}),
        card(dcc.Graph(figure=fig_grp, config={"displayModeBar":False})),
    ])


# ── Distributions ─────────────────────────────────────────────────────────────

def render_distributions():
    ctrl = card(html.Div([
        html.Div([
            label("Dimension"),
            dcc.Dropdown(id="dist-dim",
                options=[{"label":v,"value":k} for k,v in DIM_LABELS.items()],
                value="final_score", clearable=False, style=dropdown_style()),
        ], style={"flex":"1"}),
        html.Div([
            label("Group by"),
            dcc.RadioItems(id="dist-group",
                options=[{"label":"Country","value":"country"},
                         {"label":"Leader (top 15)","value":"leader_short"},
                         {"label":"Discourse Type","value":"dtype"}],
                value="country", inline=True,
                style={"color":TEXT,"fontSize":"13px","marginTop":"6px"},
                inputStyle={"marginRight":"4px","marginLeft":"12px"}),
        ], style={"flex":"2"}),
        html.Div([
            label("Year Range"),
            dcc.RangeSlider(id="dist-years", min=year_min, max=year_max,
                value=[year_min, year_max],
                marks={y: str(y) for y in range(year_min, year_max+1, 4)},
                step=1, tooltip={"placement":"bottom"}),
        ], style={"flex":"2"}),
    ], style={"display":"flex","gap":"20px","alignItems":"flex-end","flexWrap":"wrap"}))

    return html.Div([
        ctrl,
        card(dcc.Graph(id="dist-box",  config={"displayModeBar":False}, style={"height":"480px"})),
        html.Div([
            card(dcc.Graph(id="dist-hist",   config={"displayModeBar":False}, style={"height":"340px"}), {"flex":"1"}),
            card(dcc.Graph(id="dist-violin", config={"displayModeBar":False}, style={"height":"340px"}), {"flex":"1"}),
        ], style={"display":"flex","gap":"16px"}),
    ])


@callback(
    Output("dist-box","figure"), Output("dist-hist","figure"), Output("dist-violin","figure"),
    Input("dist-dim","value"), Input("dist-group","value"), Input("dist-years","value"),
)
def update_dist(dim, group, yr):
    y0, y1 = yr
    sub = df[df["year"].between(y0,y1)].copy()
    if group == "leader_short":
        top15 = sub["leader_name"].value_counts().head(15).index
        sub = sub[sub["leader_name"].isin(top15)]
    order_vals = (sub.groupby(group)[dim].median()
                     .sort_values(ascending=False).index.tolist())

    # Box
    fig_box = go.Figure()
    for i, grp_val in enumerate(order_vals):
        s = sub[sub[group]==grp_val][dim]
        fig_box.add_trace(go.Box(
            y=s, name=str(grp_val),
            marker_color=COUNTRY_COLORS[i % len(COUNTRY_COLORS)],
            line_color=COUNTRY_COLORS[i % len(COUNTRY_COLORS)],
            fillcolor=f"rgba({int(COUNTRY_COLORS[i%len(COUNTRY_COLORS)][1:3],16)},"
                      f"{int(COUNTRY_COLORS[i%len(COUNTRY_COLORS)][3:5],16)},"
                      f"{int(COUNTRY_COLORS[i%len(COUNTRY_COLORS)][5:7],16)},0.3)",
            boxpoints=False, showlegend=False,
            hovertemplate=f"<b>{grp_val}</b><br>Median: %{{median:.1f}}<br>IQR: [%{{q1:.1f}}, %{{q3:.1f}}]<extra></extra>",
        ))
    fig_box = fig_layout(fig_box, title=f"Distribution of {DIM_LABELS.get(dim,dim)} by {group}",
                         xaxis={"title":""},
                         yaxis={"title":"Score","range":[0,105]})

    # Histogram
    fig_hist = go.Figure(go.Histogram(
        x=sub[dim], nbinsx=50,
        marker=dict(color=ACCENT, opacity=0.8, line=dict(color=BG, width=0.5)),
        hovertemplate="Score: %{x:.1f}<br>Count: %{y}<extra></extra>",
    ))
    fig_hist = fig_layout(fig_hist, title=f"Overall Distribution — {DIM_LABELS.get(dim,dim)}",
                          xaxis={"title":"Score"},
                          yaxis={"title":"Count"})
    fig_hist.add_vline(x=sub[dim].mean(), line_dash="dash", line_color=WARNING,
                       annotation_text=f"Mean: {sub[dim].mean():.1f}",
                       annotation_font_color=WARNING)

    # Violin
    fig_viol = go.Figure()
    for i, grp_val in enumerate(order_vals[:10]):
        s = sub[sub[group]==grp_val][dim]
        fig_viol.add_trace(go.Violin(
            y=s, name=str(grp_val),
            fillcolor=f"rgba({int(COUNTRY_COLORS[i%len(COUNTRY_COLORS)][1:3],16)},"
                      f"{int(COUNTRY_COLORS[i%len(COUNTRY_COLORS)][3:5],16)},"
                      f"{int(COUNTRY_COLORS[i%len(COUNTRY_COLORS)][5:7],16)},0.4)",
            line_color=COUNTRY_COLORS[i % len(COUNTRY_COLORS)],
            box_visible=True, meanline_visible=True, showlegend=False,
            hovertemplate=f"<b>{grp_val}</b><br>Score: %{{y:.1f}}<extra></extra>",
        ))
    fig_viol = fig_layout(fig_viol, title=f"Violin — {DIM_LABELS.get(dim,dim)}",
                          xaxis={"title":""},
                          yaxis={"title":"Score","range":[0,105]})

    return fig_box, fig_hist, fig_viol


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  POPIN v4 Dashboard")
    print("  Acesse: http://localhost:8050\n")
    app.run(debug=False, port=8050)
