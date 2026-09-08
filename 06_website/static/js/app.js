/* POPIN v4 — shared API keys, localized presentation, bounded asynchronous state. */
"use strict";

const I18N = {
  pt: {
    nav_overview:"Visão geral", nav_countries:"Países", nav_leaders:"Líderes", nav_about:"Sobre", about_sub:"Pesquisa, método e evidências para usar o POPIN.",
    nav_timeseries:"Série temporal", nav_dimensions:"Dimensões", brand_sub:"Índice de Populismo",
    github_repo:"Código no GitHub", dataset_label:"Instrumento",
    dataset_value:"GPT-5.6 Luna · texto integral · v4", loading:"Carregando dados…",
    ov_sub:"Média dos discursos analisados", ov_note:"O score varia de 0 a 100. Leia cada média junto do número de discursos e da faixa p25–p75, que reúne os 50% centrais dos casos.",
    ct_sub:"Compare médias e cobertura por país", ld_sub:"Selecione um líder para examinar seu perfil",
    ts_sub:"Evolução das médias anuais no período disponível", dm_sub:"Médias e dispersão das dimensões de populismo",
    kpi_discourses:"Discursos analisados", kpi_countries:"Países cobertos", kpi_leaders:"Líderes identificados", kpi_years:"Período",
    cc_speeches:"discursos", cc_title:"Score por país", badge_ranked:"Média decrescente", badge_final:"Score final", badge_radar:"Radar", badge_delta:"Primeiro / último ano",
    chart_map:"Mapa do populismo", chart_trend:"Média anual do corpus", chart_radar:"Perfil de populismo",
    chart_ranked:"Média e 50% centrais", chart_dim_bars:"Dimensões por país", chart_leaders:"Ranking de líderes",
    leader_badge:"Líderes", leader_coverage_note:"A cobertura mínima considera o número de discursos de cada líder no recorte selecionado.",
    chart_ts_line:"Comparação por país", chart_movers:"Primeiro e último ano disponível por país",
    chart_means:"Média e 50% centrais por grupo", chart_scatter2d:"Dispersão entre dimensões",
    f_countries:"Países", f_country:"País", f_all:"Todos os países", f_min_n:"Cobertura mínima",
    min_n_5:"≥5 discursos", min_n_1:"Todos os casos", f_dimension:"Dimensão", f_group_by:"Agrupar por",
    f_discourse:"Tipo de discurso", f_filter_by:"Tipo de discurso", drawer_dims:"Dimensões", drawer_trend:"Evolução histórica", drawer_radar:"Perfil radar",
    dim_people:"Povo-centrismo", dim_elite:"Anti-elitismo", dim_moral:"Dicotomia moral", dim_sovereignty:"Soberania popular", dim_excl:"Retórica excludente", dim_crisis:"Retórica de crise",
    lr_click_hint:"Ver perfil", hero_most:"Maior média no recorte", hero_least:"Menor média no recorte", legend_title:"Score de populismo · 0–100",
    dtype_all:"Todos os tipos", dtype_SPEECH:"Discurso", dtype_INTERVIEW:"Entrevista", dtype_DECREE:"Decreto", dtype_LETTER:"Carta", dtype_COMMUNIQUE:"Comunicado", dtype_PRESS_RELEASE:"Nota à imprensa",
    mean:"Média", central50:"p25–p75 · 50% centrais", empty:"Sem dados para este recorte. Ajuste os filtros.", error:"Não foi possível carregar estes dados.", retry:"Tentar novamente",
    search:"Buscar nos líderes carregados", scope:"Recorte ativo", ready:"Dados atualizados", partial:"Alguns dados não foram carregados", first:"Primeiro ano disponível", last:"Último ano disponível", change:"Variação", export_countries:"Exportar países (CSV)",
    distribution_note:"Grupos com pelo menos 5 discursos · 2000–2025.",
    corpus_mean:"Média do corpus", map_caption:"Média dos textos disponíveis em cada país.", country_caption:"Compare a média junto da cobertura.", export_csv:"Baixar CSV",
    quartile_note:"p25–p75: os 50% centrais dos discursos. Não é um intervalo de confiança.", score_scale:"Score de 0 a 100", trend_caption:"Médias anuais nos marcadores; curvas suavizadas apenas para leitura. A composição do corpus varia ao longo do tempo.",
    choose_countries:"Selecionar países", search_leader:"Buscar líder", methodology_title:"Sobre os dados e o índice",
    methodology_copy:"Os valores apresentados são médias dos textos disponíveis no corpus, conforme o filtro selecionado. A cobertura varia entre países, líderes e anos. O intervalo p25–p75 descreve a dispersão dos discursos; não mede a incerteza da média.",
  },
  en: {
    nav_overview:"Overview", nav_countries:"Countries", nav_leaders:"Leaders", nav_timeseries:"Time series", nav_dimensions:"Dimensions", brand_sub:"Populism Index", nav_about:"About", about_sub:"Research, method and evidence for using POPIN.",
    github_repo:"Code on GitHub", dataset_label:"Instrument", dataset_value:"GPT-5.6 Luna · full text · v4", loading:"Loading data…",
    ov_sub:"Mean score across analyzed discourses", ov_note:"Scores range from 0 to 100. Read each mean with its discourse count and p25–p75 interval, which contains the middle 50% of cases.",
    ct_sub:"Compare country means and coverage", ld_sub:"Select a leader to examine their profile", ts_sub:"Annual means over the available period", dm_sub:"Means and dispersion of populism dimensions",
    kpi_discourses:"Discourses analyzed", kpi_countries:"Countries covered", kpi_leaders:"Leaders identified", kpi_years:"Period",
    cc_speeches:"discourses", cc_title:"Score by country", badge_ranked:"Descending mean", badge_final:"Final score", badge_radar:"Radar", badge_delta:"First / last year",
    chart_map:"Populism map", chart_trend:"Annual corpus mean", chart_radar:"Populism profile", chart_ranked:"Mean and middle 50%", chart_dim_bars:"Dimensions by country", chart_leaders:"Leader ranking",
    leader_badge:"Leaders", leader_coverage_note:"Minimum coverage counts each leader’s discourses within the selected scope.",
    chart_ts_line:"Country comparison", chart_movers:"First and last available year by country", chart_means:"Mean and middle 50% by group", chart_scatter2d:"Dimension scatter",
    f_countries:"Countries", f_country:"Country", f_all:"All countries", f_min_n:"Minimum coverage", min_n_5:"≥5 discourses", min_n_1:"All cases", f_dimension:"Dimension", f_group_by:"Group by", f_discourse:"Discourse type", f_filter_by:"Discourse type",
    drawer_dims:"Dimensions", drawer_trend:"Historical evolution", drawer_radar:"Radar profile",
    dim_people:"People centrism", dim_elite:"Anti-elitism", dim_moral:"Moral dichotomy", dim_sovereignty:"Popular sovereignty", dim_excl:"Exclusionary rhetoric", dim_crisis:"Crisis rhetoric",
    lr_click_hint:"View profile", hero_most:"Highest mean in scope", hero_least:"Lowest mean in scope", legend_title:"Populism score · 0–100",
    dtype_all:"All types", dtype_SPEECH:"Speech", dtype_INTERVIEW:"Interview", dtype_DECREE:"Decree", dtype_LETTER:"Letter", dtype_COMMUNIQUE:"Communiqué", dtype_PRESS_RELEASE:"Press release",
    mean:"Mean", central50:"p25–p75 · middle 50%", empty:"No data for this scope. Adjust the filters.", error:"These data could not be loaded.", retry:"Try again",
    search:"Search loaded leaders", scope:"Active scope", ready:"Data updated", partial:"Some data could not be loaded", first:"First available year", last:"Last available year", change:"Change", export_countries:"Export countries (CSV)",
    distribution_note:"Groups with at least 5 discourses · 2000–2025.",
    corpus_mean:"Corpus mean", map_caption:"Mean of available texts in each country.", country_caption:"Compare each mean with its coverage.", export_csv:"Download CSV",
    quartile_note:"p25–p75: the middle 50% of discourses. This is not a confidence interval.", score_scale:"Score from 0 to 100", trend_caption:"Markers show annual means; curves are smoothed for display only. Corpus composition changes over time.",
    choose_countries:"Select countries", search_leader:"Search leaders", methodology_title:"About the data and index",
    methodology_copy:"Values are means of the texts available in the corpus, under the selected filter. Coverage varies across countries, leaders and years. The p25–p75 interval describes the dispersion of discourses; it does not measure uncertainty in the mean.",
  },
};
const DIMS = [
  {key:"final_score", pt:"Score final", en:"Final score"},
  {key:"people_centrism", pt:"Povo-centrismo", en:"People centrism"},
  {key:"anti_elitism", pt:"Anti-elitismo", en:"Anti-elitism"},
  {key:"moral_dichotomy", pt:"Dicotomia moral", en:"Moral dichotomy"},
  {key:"popular_sovereignty", pt:"Soberania popular", en:"Popular sovereignty"},
  {key:"exclusionary_rhetoric", pt:"Retórica excludente", en:"Exclusionary rhetoric"},
  {key:"crisis_rhetoric", pt:"Retórica de crise", en:"Crisis rhetoric"},
];
// country is the backend key. Neither translations nor sorting change selector values.
const COUNTRIES = {
  ARG:["Argentina","Argentina","Argentina"], BOL:["Bolivia","Bolívia","Bolivia"],
  BRA:["Brazil","Brasil","Brazil"], CHL:["Chile","Chile","Chile"], COL:["Colombia","Colômbia","Colombia"],
  CRI:["Costa Rica","Costa Rica","Costa Rica"], CUB:["Cuba","Cuba","Cuba"],
  DOM:["Dom. Republic","República Dominicana","Dominican Republic"], ECU:["Ecuador","Equador","Ecuador"],
  GTM:["Guatemala","Guatemala","Guatemala"], HND:["Honduras","Honduras","Honduras"],
  MEX:["Mexico","México","Mexico"], NIC:["Nicaragua","Nicarágua","Nicaragua"],
  PAN:["Panama","Panamá","Panama"], PER:["Peru","Peru","Peru"], PRY:["Paraguay","Paraguai","Paraguay"],
  SLV:["El Salvador","El Salvador","El Salvador"], URY:["Uruguay","Uruguai","Uruguay"], VEN:["Venezuela","Venezuela","Venezuela"],
};
const CATEGORY_COLORS = ["#185a82","#9b392e","#007f86","#70419b","#386d32","#a54d06","#a82e65","#465c94","#736008","#426864","#802e36","#396a9b","#80582b","#685380","#26704f","#8c4567","#4c5d25","#975139","#414a70"];
const NAVY = "#183b56", TEAL = "#007f86", INK = "#334155", GRID = "#e2e8f0";
const SANS = "IBM Plex Sans,system-ui,sans-serif", MONO = "IBM Plex Mono,monospace";
const SCORE_STOPS = [[0,[232,241,250]],[25,[181,209,232]],[50,[112,163,200]],[75,[58,112,153]],[100,[24,59,86]]];
const POP_SCALE = SCORE_STOPS.map(([v,c]) => [v/100,`rgb(${c.join(",")})`]);
const LEADER_LIMIT = 200; // main.py: n is Query(default=25), with no declared maximum.
const $ = id => document.getElementById(id);
const all = selector => Array.from(document.querySelectorAll(selector));
let LANG = "pt", GLOBAL_DTYPE = "ALL", _activeTrendDim = "final_score";
let _dimBarKey = "people_centrism", _scatterX = "people_centrism", _scatterY = "anti_elitism";
let _radarSelected = ["Venezuela","Brazil","Mexico","Argentina"];
const TS = {countries:["BRA","VEN","MEX","ARG","BOL","COL"], dim:"final_score"};
const DIST = {dim:"final_score", group:"country"};
const _cache = {}, countryCatalog = new Map();
let _allDtypes = [], scopeVersion = 0, lastRefresh = null;
const t = key => I18N[LANG][key] ?? I18N.pt[key] ?? key;
const locale = () => LANG === "pt" ? "pt-BR" : "en-US";
const valid = value => value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value));
const fmt = (value, digits=1) => valid(value) ? new Intl.NumberFormat(locale(), {minimumFractionDigits:digits,maximumFractionDigits:digits}).format(Number(value)) : "—";
const escapeHTML = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const text = (id,value) => { if ($(id)) $(id).textContent = value; };
const html = (id,value) => { if ($(id)) $(id).innerHTML = value; };
const dimLabel = key => DIMS.find(d => d.key === key)?.[LANG] ?? key;
const dtypeLabel = key => key === "ALL" ? t("dtype_all") : I18N[LANG][`dtype_${key}`] ?? key;
const countryName = value => {
  const row = typeof value === "object" && value ? COUNTRIES[value.iso3] : COUNTRIES[value];
  const key = typeof value === "object" && value ? value.country ?? value.iso3 : value;
  return (row ?? Object.values(COUNTRIES).find(c => c[0] === key))?.[LANG === "pt" ? 1 : 2] ?? key ?? "—";
};
const countryLabel = c => `${c.iso3} · ${countryName(c)}`;
const ctryColor = key => CATEGORY_COLORS[Math.max(0,Object.keys(COUNTRIES).findIndex(iso => iso === key || COUNTRIES[iso][0] === key)) % CATEGORY_COLORS.length];
const countryMarker = iso => `<span class="country-code">${escapeHTML(iso)}</span>`;
const coverageText = c => `n=${fmt(c.n,0)} · p25–p75 ${fmt(c.p25)}–${fmt(c.p75)}`;
const leaderMinN = () => $("leader-min-n-filter")?.value || "5";
const leaderCountry = () => $("leader-country-filter")?.value || "ALL";
const scoreWidth = value => valid(value) ? Math.min(100,Math.max(0,Number(value))) : 0;
function popColor(value) {
  const score = scoreWidth(value);
  const index = Math.min(3,Math.floor(score/25));
  const [start,lo] = SCORE_STOPS[index], [end,hi] = SCORE_STOPS[index+1];
  return `rgb(${lo.map((v,i) => Math.round(v+(hi[i]-v)*(score-start)/(end-start))).join(",")})`;
}
function storage(key,value) {
  try { return value === undefined ? localStorage.getItem(key) : localStorage.setItem(key,value); }
  catch { return null; } // Private browsing/storage policies must not prevent initialization.
}
function url(path,params={}) {
  const query = new URLSearchParams({...params, ...(GLOBAL_DTYPE === "ALL" ? {} : {dtype:GLOBAL_DTYPE})});
  return `/api/${path}?${query}`;
}

// Per-resource generations cover filters within a scope; scopeVersion covers dtype changes.
// The generation check is still required when an abort arrives after a response was delivered.
const requests = new Map(), resourceStates = new Map(), viewStates = new Map();
function cancelRequest(key) {
  requests.get(key)?.controller.abort();
  requests.delete(key);
  resourceStates.delete(key);
}
async function request(key,path,onData,onStart,onError) {
  cancelRequest(key);
  const ticket = {controller:new AbortController(), scope:scopeVersion};
  requests.set(key,ticket);
  resourceStates.set(key,"loading");
  const current = () => requests.get(key) === ticket && ticket.scope === scopeVersion;
  onStart?.();
  updateRefreshStatus();
  const timeout = setTimeout(() => ticket.controller.abort(),30000);
  try {
    const response = await fetch(path,{signal:ticket.controller.signal});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!current()) return;
    onData(data);
    resourceStates.set(key,"ready");
  } catch (error) {
    if (!current()) return;
    resourceStates.set(key,"error");
    onError?.(error);
    console.warn(`POPIN ${key}:`,error.message);
  } finally {
    clearTimeout(timeout);
    if (current()) {
      requests.delete(key);
      if (![...resourceStates.values()].includes("loading")) lastRefresh = new Date();
      updateRefreshStatus();
    }
  }
}
function updateRefreshStatus() {
  const values = [...resourceStates.values()];
  const state = values.includes("loading") ? "loading" : values.includes("error") ? "error" : "ready";
  const el = $("refresh-status");
  if (el) {
    el.dataset.state = state;
    el.classList.toggle("is-error",state === "error");
    el.classList.toggle("is-loading",state === "loading");
    el.setAttribute("role","status");
    el.textContent = t(state === "error" ? "partial" : state === "loading" ? "loading" : "ready") +
      (state === "ready" && lastRefresh ? ` · ${new Intl.DateTimeFormat(locale(),{hour:"2-digit",minute:"2-digit"}).format(lastRefresh)}` : "");
  }
  updateScopeSummary();
}
function updateScopeSummary() {
  const country = leaderCountry();
  const suffix = $("section-leaders")?.classList.contains("active")
    ? ` · ${country === "ALL" ? t("f_all") : countryName(country)} · n≥${fmt(leaderMinN(),0)}` : "";
  text("scope-summary",`${t("scope")}: ${dtypeLabel(GLOBAL_DTYPE)}${suffix}`);
}
function stateMarkup(kind) {
  return `<div class="chart-empty ${kind === "error" ? "error-state is-error" : kind === "loading" ? "empty-state is-loading" : "empty-state"}" role="${kind === "error" ? "alert" : "status"}"><p>${t(kind === "loading" ? "loading" : kind === "error" ? "error" : "empty")}</p>${kind === "error" ? `<button type="button" class="retry-btn">${t("retry")}</button>` : ""}</div>`;
}
function setState(id,kind,retry) {
  const el = $(id);
  if (!el) return;
  viewStates.set(id,{kind,retry});
  el.setAttribute("aria-busy",String(kind === "loading"));
  if (id.startsWith("chart-")) schedulePlot(id,{state:kind,retry});
  else {
    el.innerHTML = stateMarkup(kind);
    el.querySelector(".retry-btn")?.addEventListener("click",retry);
  }
}
function clearState(id) {
  viewStates.delete(id);
  $(id)?.setAttribute("aria-busy","false");
}

// Plotly renders are serialized per container. Hidden plots keep only their latest spec.
// ResizeObserver measures the container; navigation flushes and resizes newly visible plots.
const plots = new Map();
let resizeFrame = null;
const visible = el => !!el && el.getClientRects().length > 0 && !el.closest("[inert]");
function axis(overrides={}) {
  return {gridcolor:GRID,zerolinecolor:"#94a3b8",linecolor:GRID,automargin:true,
    tickfont:{family:MONO,color:INK,size:11},...overrides};
}
const scoreAxis = overrides => axis({range:[0,100],tickvals:[0,20,40,60,80,100],...overrides});
function layout(overrides={}) {
  return {paper_bgcolor:"rgba(0,0,0,0)",plot_bgcolor:"rgba(0,0,0,0)",autosize:true,
    font:{family:SANS,color:INK,size:12},separators:LANG === "pt" ? ",." : ".,",
    margin:{t:16,r:24,b:68,l:56},colorway:CATEGORY_COLORS,
    hoverlabel:{bgcolor:"#ffffff",bordercolor:"#cbd5e1",font:{family:SANS,color:INK,size:13}},
    showlegend:true,legend:{orientation:"h",x:0,y:-0.2,xanchor:"left",yanchor:"top",font:{family:SANS,size:11},bgcolor:"rgba(0,0,0,0)"},...overrides};
}
function plot(id,traces,overrides={}) {
  if (!traces.length) { setState(id,"empty"); return; }
  clearState(id);
  // ResizeObserver follows the container: keep explicit row-based chart heights
  // on that container too, so responsive resize does not restore the CSS default.
  if (overrides.height && $(id)) $(id).style.height = `${overrides.height}px`;
  schedulePlot(id,{traces,layout:layout(overrides)});
}
function schedulePlot(id,spec) {
  if (!$(id)) return;
  let slot = plots.get(id);
  if (!slot) { slot = {revision:0,rendered:0,running:false}; plots.set(id,slot); }
  slot.spec = spec;
  slot.revision++;
  flushPlot(id);
}
async function flushPlot(id) {
  const el = $(id), slot = plots.get(id);
  if (!slot || slot.running || slot.rendered === slot.revision || (!slot.spec.state && !visible(el))) return;
  slot.running = true;
  const revision = slot.revision, spec = slot.spec;
  try {
    if (spec.state) {
      if (el.data && typeof Plotly !== "undefined") Plotly.purge(el);
      el.innerHTML = stateMarkup(spec.state);
      el.querySelector(".retry-btn")?.addEventListener("click",spec.retry);
    } else {
      if (!el.data) el.replaceChildren();
      await Plotly.react(el,spec.traces,spec.layout,{displayModeBar:false,responsive:false});
    }
  } catch (error) {
    if (revision === slot.revision) {
      el.innerHTML = stateMarkup("error");
      el.querySelector(".retry-btn")?.addEventListener("click",() => schedulePlot(id,spec));
    }
    console.warn(`POPIN plot ${id}:`,error.message);
  } finally {
    slot.rendered = revision;
    slot.running = false;
    if (slot.rendered !== slot.revision) void flushPlot(id);
  }
}
function resizeVisiblePlots() {
  if (resizeFrame !== null) return;
  resizeFrame = requestAnimationFrame(() => {
    resizeFrame = null;
    for (const [id,slot] of plots) {
      const el = $(id);
      if (!visible(el)) continue;
      if (slot.rendered !== slot.revision) void flushPlot(id);
      else if (!slot.running && el.data && typeof Plotly !== "undefined") {
        Promise.resolve(Plotly.Plots.resize(el)).catch(() => {});
      }
    }
  });
}
function initPlotSizing() {
  if (typeof ResizeObserver !== "undefined") {
    const dimensions = new WeakMap();
    const observer = new ResizeObserver(entries => {
      let changed = false;
      for (const entry of entries) {
        const size = `${Math.round(entry.contentRect.width)}:${Math.round(entry.contentRect.height)}`;
        if (dimensions.get(entry.target) !== size) { dimensions.set(entry.target,size); changed = true; }
      }
      if (changed) resizeVisiblePlots();
    });
    all('[id^="chart-"]').forEach(el => observer.observe(el));
  }
  window.addEventListener("resize",resizeVisiblePlots);
  document.fonts?.ready.then(resizeVisiblePlots);
}
const barMargin = () => ({t:16,r:40,b:82,l:window.innerWidth <= 768 ? 100 : 170});
const polarLayout = () => ({margin:{t:30,r:70,b:100,l:70},polar:{bgcolor:"rgba(0,0,0,0)",
  radialaxis:scoreAxis({tickfont:{family:MONO,size:10,color:INK}}),angularaxis:{gridcolor:GRID,tickfont:{family:SANS,color:INK,size:11}}}});
function scoreBarTrace(rows,key) {
  return {type:"bar",orientation:"h",name:dimLabel(key),x:rows.map(c => c[key]),y:rows.map(countryLabel),
    text:rows.map(c => fmt(c[key])),textposition:"outside",cliponaxis:false,textfont:{family:MONO,color:INK},
    marker:{color:rows.map(c => popColor(c[key]))},
    hovertext:rows.map(c => `${escapeHTML(countryLabel(c))}<br>${escapeHTML(dimLabel(key))}: ${fmt(c[key])}<br>n=${fmt(c.n,0)}`),hoverinfo:"text"};
}
function intervalTrace(rows,{horizontal=false,label=c => c.group,q1="q1",q3="q3"}={}) {
  const x = [], y = [], hovertext = [];
  for (const row of rows) {
    if (!valid(row[q1]) || !valid(row[q3])) continue;
    const group = label(row);
    x.push(...(horizontal ? [row[q1],row[q3],null] : [group,group,null]));
    y.push(...(horizontal ? [group,group,null] : [row[q1],row[q3],null]));
    const hint = `${escapeHTML(group)}<br>${t("central50")}: ${fmt(row[q1])}–${fmt(row[q3])}<br>n=${fmt(row.n,0)}`;
    hovertext.push(hint,hint,"");
  }
  return {type:"scatter",mode:"lines+markers",name:t("central50"),x,y,connectgaps:false,
    line:{color:INK,width:2,shape:"linear"},marker:{color:INK,size:7,symbol:horizontal ? "line-ns" : "line-ew"},hovertext,hoverinfo:"text"};
}

function renderKPIs(stats) {
  clearState("kpi-row");
  html("kpi-row",[
    ["kpi_discourses",fmt(stats.n_discourses,0)],["kpi_countries",fmt(stats.n_countries,0)],
    ["kpi_leaders",fmt(stats.n_leaders,0)],["kpi_years",`${stats.year_min ?? "—"}–${stats.year_max ?? "—"}`],
  ].map(([label,value]) => `<div class="kpi-card"><span class="kpi-label">${t(label)}</span><span class="kpi-value">${escapeHTML(value)}</span></div>`).join(""));
  text("corpus-average",fmt(stats.avg_score));
}
function renderHeroBanner(countries) {
  clearState("hero-row");
  const sorted = [...countries].filter(c => valid(c.final_score)).sort((a,b) => b.final_score-a.final_score);
  html("hero-row",sorted.length ? [[sorted[0],"hero_most"],[sorted.at(-1),"hero_least"]].map(([c,key]) =>
    `<div class="hero-card"><span class="hero-tag">${t(key)}</span><span class="hero-country">${countryMarker(c.iso3)} ${escapeHTML(countryName(c))}</span><span class="hero-score">${fmt(c.final_score)} / 100</span><span class="hero-coverage">${coverageText(c)}</span></div>`).join("") : "");
}
function renderCountryCards(countries) {
  if (!countries.length) { setState("country-cards","empty"); return; }
  clearState("country-cards");
  const sorted = [...countries].sort((a,b) => b.final_score-a.final_score);
  html("country-cards",`<table class="country-table"><caption>${t("cc_title")} · ${t("badge_ranked")}</caption><thead><tr><th scope="col">${t("f_country")}</th><th scope="col">${t("mean")}</th><th scope="col">${t("kpi_discourses")}</th><th scope="col">p25–p75</th></tr></thead><tbody>${sorted.map(c =>
    `<tr><th scope="row"><button type="button" class="country-link" data-country="${escapeHTML(c.iso3)}">${countryMarker(c.iso3)} <span>${escapeHTML(countryName(c))}</span></button></th><td class="country-mean"><span>${fmt(c.final_score)}</span><span class="score-microbar" aria-hidden="true"><span style="display:block;width:${scoreWidth(c.final_score)}%;background:${popColor(c.final_score)}"></span></span></td><td>${fmt(c.n,0)}</td><td>${fmt(c.p25)}–${fmt(c.p75)}</td></tr>`).join("")}</tbody></table>`);
  $("country-cards")?.querySelectorAll("[data-country]").forEach(button => button.addEventListener("click",() => {
    if ($("leader-country-filter")) $("leader-country-filter").value = button.dataset.country;
    navigateTo("leaders");
    void refreshLeaders();
  }));
}
function renderMap(countries) {
  plot("chart-map",countries.length ? [{type:"choropleth",locationmode:"ISO-3",locations:countries.map(c => c.iso3),z:countries.map(c => c.final_score),
    colorscale:POP_SCALE,zmin:0,zmax:100,showscale:false,
    marker:{line:{color:"#ffffff",width:0.8}},hovertext:countries.map(c => `${escapeHTML(countryLabel(c))}<br>${t("mean")}: ${fmt(c.final_score)}<br>${coverageText(c)}`),hoverinfo:"text"}] : [],
    {margin:{t:10,r:15,b:10,l:0},showlegend:false,geo:{bgcolor:"rgba(0,0,0,0)",showland:true,landcolor:"#e2e8f0",showocean:true,oceancolor:"#f8fafc",showcountries:true,countrycolor:"#cbd5e1",showframe:false,showcoastlines:false,projection:{type:"mercator"},lataxis:{range:[-58,35]},lonaxis:{range:[-118,-28]}}});
}
function renderGlobalTrend(rows,dim=_activeTrendDim) {
  const data = [...rows].sort((a,b) => a.year-b.year);
  plot("chart-trend",data.length ? [{type:"scatter",mode:"lines+markers",name:dimLabel(dim),x:data.map(r => r.year),y:data.map(r => r[dim]),
    connectgaps:false,line:{color:NAVY,width:2.5,shape:"spline",smoothing:0.5},marker:{size:5},hovertext:data.map(r => `${r.year} · ${dimLabel(dim)}: ${fmt(r[dim])}<br>n=${fmt(r.n,0)}`),hoverinfo:"text"}] : [],
    {xaxis:axis({tickformat:"d"}),yaxis:scoreAxis({title:{text:dimLabel(dim)}})});
}
function renderCountryRanked(countries) {
  const rows = [...countries].sort((a,b) => a.final_score-b.final_score);
  plot("chart-country-box",rows.length ? [intervalTrace(rows,{horizontal:true,label:countryLabel,q1:"p25",q3:"p75"}),
    {type:"scatter",mode:"markers",name:t("mean"),x:rows.map(c => c.final_score),y:rows.map(countryLabel),
      marker:{color:rows.map(c => popColor(c.final_score)),size:10,line:{color:NAVY,width:1}},
      hovertext:rows.map(c => `${escapeHTML(countryLabel(c))}<br>${t("mean")}: ${fmt(c.final_score)}<br>${coverageText(c)}`),hoverinfo:"text"}] : [],
    {margin:barMargin(),xaxis:scoreAxis(),yaxis:axis({categoryorder:"array",categoryarray:rows.map(countryLabel)}),height:Math.max(450,rows.length*27+120)});
}
function radarTrace(c,name,color) {
  const dimensions = [...DIMS.slice(1),DIMS[1]];
  return {type:"scatterpolar",mode:"lines+markers",name,r:dimensions.map(d => c[d.key] ?? null),theta:dimensions.map(d => d[LANG]),
    line:{color,width:2,shape:"linear"},marker:{size:4,color},connectgaps:false,
    hovertext:dimensions.map(d => `${escapeHTML(name)}<br>${d[LANG]}: ${fmt(c[d.key])}`),hoverinfo:"text"};
}
function renderCountryRadar(countries) {
  plot("chart-country-radar",countries.filter(c => _radarSelected.includes(c.country)).map(c => radarTrace(c,countryName(c),ctryColor(c.iso3))),polarLayout());
}
function renderDimBars(countries) {
  const rows = [...countries].sort((a,b) => a[_dimBarKey]-b[_dimBarKey]);
  plot("chart-dim-bars",rows.length ? [scoreBarTrace(rows,_dimBarKey)] : [],
    {margin:barMargin(),xaxis:scoreAxis({range:[0,105]}),yaxis:axis(),bargap:0.3,height:Math.max(450,rows.length*27+120)});
}
function renderTSLine() {
  const groups = new Map();
  (_cache.yearly ?? []).forEach(r => { if (!groups.has(r.iso3)) groups.set(r.iso3,[]); groups.get(r.iso3).push(r); });
  plot("chart-ts-line",[...groups.values()].map(rows => {
    rows.sort((a,b) => a.year-b.year);
    return {type:"scatter",mode:"lines+markers",name:countryName(rows[0]),x:rows.map(r => r.year),y:rows.map(r => r.score),connectgaps:false,
      line:{color:ctryColor(rows[0].iso3),width:2,shape:"spline",smoothing:0.5},marker:{size:4},
      hovertext:rows.map(r => `${escapeHTML(countryName(r))} · ${r.year}<br>${dimLabel(TS.dim)}: ${fmt(r.score)}`),hoverinfo:"text"};
  }),{xaxis:axis({tickformat:"d"}),yaxis:scoreAxis({title:{text:dimLabel(TS.dim)}}),margin:{t:16,r:24,b:125,l:60}});
}
function renderMovers() {
  const groups = new Map();
  (_cache.movers ?? []).forEach(r => { if (!groups.has(r.iso3)) groups.set(r.iso3,[]); groups.get(r.iso3).push(r); });
  const rows = [...groups.values()].filter(group => group.length >= 2).map(group => {
    group.sort((a,b) => a.year-b.year);
    return {...group[0],first:group[0],last:group.at(-1),delta:group.at(-1).score-group[0].score};
  }).sort((a,b) => a.delta-b.delta);
  const x = [],y = [];
  rows.forEach(r => { x.push(r.first.score,r.last.score,null); y.push(countryLabel(r),countryLabel(r),null); });
  const traces = [{type:"scatter",mode:"lines",x,y,connectgaps:false,line:{color:"#94a3b8",width:2,shape:"linear"},showlegend:false,hoverinfo:"skip"},
    ...["first","last"].map(key => ({type:"scatter",mode:"markers",name:t(key),x:rows.map(r => r[key].score),y:rows.map(countryLabel),
      marker:{color:key === "first" ? NAVY : TEAL,size:9,symbol:key === "first" ? "circle-open" : "diamond"},
      hovertext:rows.map(r => `${escapeHTML(countryLabel(r))}<br>${r.first.year}: ${fmt(r.first.score)} · ${r.last.year}: ${fmt(r.last.score)}<br>${t("change")}: ${fmt(r.delta)}`),hoverinfo:"text"}))];
  plot("chart-movers",rows.length ? traces : [],{margin:barMargin(),xaxis:scoreAxis({title:{text:t("badge_final")}}),yaxis:axis(),height:Math.max(400,rows.length*27+120)});
}
function renderHistogram() {
  const rows = _cache.distribution ?? [];
  const label = r => DIST.group === "country" ? countryName(r.group) : dtypeLabel(r.group);
  plot("chart-hist",rows.length ? [intervalTrace(rows,{label,horizontal:true}),{type:"scatter",mode:"markers",name:t("mean"),
    y:rows.map(label),x:rows.map(r => r.mean),marker:{size:9,color:rows.map(r => popColor(r.mean)),line:{color:NAVY,width:1}},
    hovertext:rows.map(r => `${escapeHTML(label(r))}<br>${t("mean")}: ${fmt(r.mean)}<br>${t("central50")}: ${fmt(r.q1)}–${fmt(r.q3)}<br>n=${fmt(r.n,0)}`),hoverinfo:"text"}] : [],
    {height:Math.max(420,rows.length*28+145),margin:{...barMargin(),b:115},yaxis:axis({autorange:"reversed",categoryorder:"array",categoryarray:rows.map(label)}),xaxis:scoreAxis({title:{text:dimLabel(DIST.dim)}}),legend:{orientation:"h",x:0,y:-0.18}});
  text("distribution-note",t("distribution_note"));
}
function renderScatter2D(countries) {
  plot("chart-scatter2d",countries.length ? [{type:"scatter",mode:"markers+text",name:t("f_countries"),
    x:countries.map(c => c[_scatterX]),y:countries.map(c => c[_scatterY]),text:countries.map(c => c.iso3),textposition:"top center",textfont:{family:SANS,color:INK,size:10},
    marker:{size:10,color:countries.map(c => c.final_score),colorscale:POP_SCALE,cmin:0,cmax:100,showscale:true,line:{color:NAVY,width:1},colorbar:{title:{text:t("badge_final")},thickness:10,tickvals:[0,20,40,60,80,100],outlinewidth:0}},
    hovertext:countries.map(c => `${escapeHTML(countryLabel(c))}<br>${dimLabel(_scatterX)}: ${fmt(c[_scatterX])}<br>${dimLabel(_scatterY)}: ${fmt(c[_scatterY])}<br>${t("badge_final")}: ${fmt(c.final_score)}<br>n=${fmt(c.n,0)}`),hoverinfo:"text"}] : [],
    {xaxis:scoreAxis({title:{text:dimLabel(_scatterX)}}),yaxis:scoreAxis({title:{text:dimLabel(_scatterY)}}),showlegend:false});
}

const searchKey = value => String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLocaleLowerCase(locale());
function renderLeaderRankList(leaders) {
  const query = searchKey($("leader-search")?.value).trim();
  const sorted = [...leaders].sort((a,b) => b.final_score-a.final_score);
  const rows = sorted.map((leader,index) => ({leader,rank:index+1})).filter(({leader:l}) =>
    searchKey(`${l.leader_name} ${l.leader_short} ${countryName(l)} ${l.iso3}`).includes(query));
  const limit = leaders.length >= LEADER_LIMIT ? (LANG === "pt" ? " · limite de 200 atingido" : " · 200 limit reached") : "";
  text("leader-count-badge",`${fmt(rows.length,0)} / ${fmt(leaders.length,0)} ${LANG === "pt" ? "líderes carregados" : "loaded leaders"} · n≥${fmt(leaderMinN(),0)}${limit}`);
  if (!rows.length) { setState("leader-rank-list","empty"); return; }
  clearState("leader-rank-list");
  html("leader-rank-list",rows.map(({leader:l,rank},index) =>
    `<button class="lr-item" type="button" data-index="${index}" aria-haspopup="dialog" aria-controls="leader-drawer"><span class="lr-rank">${rank}</span><span class="lr-info"><span class="lr-name">${escapeHTML(l.leader_short || l.leader_name)}</span><span class="lr-sub">${escapeHTML(countryLabel(l))} · ${coverageText(l)}</span></span><span class="lr-right"><span class="lr-score">${fmt(l.final_score)}</span><span class="lr-bar-wrap" aria-hidden="true"><span class="lr-bar-fill" style="display:block;width:${scoreWidth(l.final_score)}%;background:${popColor(l.final_score)}"></span></span><span class="lr-click-hint">${t("lr_click_hint")}</span></span></button>`).join(""));
  $("leader-rank-list")?.querySelectorAll(".lr-item").forEach(button => button.addEventListener("click",() => openLeaderDrawer(rows[Number(button.dataset.index)].leader,button)));
}

let drawerLeader = null, drawerTrend = null, lastDrawerTrigger = null, backgroundInert = [], savedOverflow = "";
function renderDrawerProfile() {
  const leader = drawerLeader;
  if (!leader) return;
  text("drawer-name",leader.leader_short || leader.leader_name);
  text("drawer-meta",`${countryLabel(leader)} · ${coverageText(leader)}`);
  html("drawer-score-row",`<span class="drawer-score-big">${fmt(leader.final_score)}</span><span class="drawer-score-label">${t("badge_final")} · 0–100</span>`);
  html("drawer-dims",DIMS.slice(1).map(d => `<div class="dim-bar-row"><span class="dim-bar-label">${d[LANG]}</span><span class="dim-bar-track" aria-hidden="true"><span class="dim-bar-fill" style="display:block;width:${scoreWidth(leader[d.key])}%;background:${popColor(leader[d.key])}"></span></span><span class="dim-bar-val">${fmt(leader[d.key])}</span></div>`).join(""));
  plot("chart-drawer-radar",[radarTrace(leader,leader.leader_short || leader.leader_name,NAVY)],polarLayout());
}
function renderDrawerTrend() {
  if (!drawerLeader || drawerTrend === null) return;
  const rows = [...drawerTrend].sort((a,b) => a.year-b.year);
  plot("chart-drawer-trend",rows.length ? [{type:"scatter",mode:"lines+markers",name:t("mean"),x:rows.map(r => r.year),y:rows.map(r => r.final_score),
    line:{color:NAVY,width:2,shape:"spline",smoothing:0.5},marker:{size:5},connectgaps:false,
    hovertext:rows.map(r => `${r.year}: ${fmt(r.final_score)}`),hoverinfo:"text"}] : [],
    {xaxis:axis({tickformat:"d"}),yaxis:scoreAxis(),margin:{t:16,r:16,b:65,l:45}});
}
function fetchDrawerTrend() {
  const leader = drawerLeader;
  if (!leader) return Promise.resolve();
  return request("drawer",url("leader_trend",{names:leader.leader_name}),data => {
    if (drawerLeader !== leader) return;
    drawerTrend = data;
    renderDrawerTrend();
  },() => { drawerTrend = null; setState("chart-drawer-trend","loading"); },() => setState("chart-drawer-trend","error",fetchDrawerTrend));
}
function openLeaderDrawer(leader,trigger=document.activeElement) {
  const drawer = $("leader-drawer");
  if (!drawer) return;
  if (!drawerLeader) {
    lastDrawerTrigger = trigger;
    savedOverflow = document.body.style.overflow;
    // Keep existing inert states, including a closed mobile navigation menu.
    backgroundInert = all("body > main, #site-sidebar, #sidebar-toggle").filter(el => !el.contains(drawer)).map(el => [el,el.inert]);
    backgroundInert.forEach(([el]) => { el.inert = true; });
  }
  drawerLeader = leader;
  drawer.inert = false;
  drawer.classList.add("open");
  drawer.setAttribute("aria-hidden","false");
  drawer.setAttribute("tabindex","-1");
  $("drawer-overlay")?.classList.add("open");
  document.body.style.overflow = "hidden";
  renderDrawerProfile();
  ($("drawer-close") ?? drawer).focus();
  void fetchDrawerTrend();
  resizeVisiblePlots();
}
function closeLeaderDrawer() {
  if (!drawerLeader) return;
  cancelRequest("drawer");
  drawerLeader = null; drawerTrend = null;
  const drawer = $("leader-drawer");
  drawer?.classList.remove("open");
  drawer?.setAttribute("aria-hidden","true");
  if (drawer) drawer.inert = true;
  $("drawer-overlay")?.classList.remove("open");
  backgroundInert.forEach(([el,inert]) => { el.inert = inert; });
  backgroundInert = [];
  document.body.style.overflow = savedOverflow;
  if (lastDrawerTrigger?.isConnected) lastDrawerTrigger.focus();
  else document.querySelector('.nav-item[aria-current="page"]')?.focus();
  lastDrawerTrigger = null;
  updateRefreshStatus();
  resizeVisiblePlots();
}
function drawerKeydown(event) {
  if (!drawerLeader) return;
  if (event.key === "Escape") { event.preventDefault(); closeLeaderDrawer(); return; }
  if (event.key !== "Tab") return;
  const drawer = $("leader-drawer");
  const focusable = Array.from(drawer.querySelectorAll('button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')).filter(visible);
  const first = focusable[0] ?? drawer, last = focusable.at(-1) ?? drawer;
  if (event.shiftKey && (document.activeElement === first || !focusable.includes(document.activeElement))) {
    event.preventDefault(); last.focus();
  } else if (!event.shiftKey && (document.activeElement === last || !focusable.includes(document.activeElement))) {
    event.preventDefault(); first.focus();
  }
}

function navigateTo(section) {
  if (!$("section-"+section)) section = "overview";
  all(".nav-item[data-section]").forEach(el => {
    const active = el.dataset.section === section;
    el.classList.toggle("active",active);
    if (active) el.setAttribute("aria-current","page"); else el.removeAttribute("aria-current");
  });
  all(".section").forEach(el => { const active = el.id === "section-"+section; el.classList.toggle("active",active); el.hidden = !active; });
  storage("popin_section",section);
  if ($("global-filter-bar")) $("global-filter-bar").hidden = section === "about";
  updateScopeSummary();
  resizeVisiblePlots();
}
function setMobileMenu(open) {
  const sidebar = $("site-sidebar"), nav = sidebar?.querySelector(".nav");
  open = !!open && window.innerWidth <= 768;
  sidebar?.classList.toggle("open",open);
  $("sidebar-mob-overlay")?.classList.toggle("open",open);
  $("sidebar-toggle")?.setAttribute("aria-expanded",String(open));
  // The sidebar is now a topbar: never hide the brand/language controls with aria-hidden.
  sidebar?.removeAttribute("aria-hidden");
  if (nav) {
    nav.inert = window.innerWidth <= 768 && !open;
    nav.setAttribute("aria-hidden",String(nav.inert));
  }
}
function initNav() {
  navigateTo(storage("popin_section") || "overview");
  all(".nav-item[data-section]").forEach(el => el.addEventListener("click",() => {
    navigateTo(el.dataset.section); setMobileMenu(false);
    if (window.innerWidth <= 768) $("sidebar-toggle")?.focus();
  }));
  $("lang-toggle")?.addEventListener("click",() => setLanguage(LANG === "pt" ? "en" : "pt"));
  $("sidebar-toggle")?.addEventListener("click",() => setMobileMenu(!$("site-sidebar")?.classList.contains("open")));
  $("sidebar-mob-overlay")?.addEventListener("click",() => setMobileMenu(false));
  window.addEventListener("resize",() => setMobileMenu($("site-sidebar")?.classList.contains("open")));
  setMobileMenu(false);
  document.addEventListener("keydown",event => {
    if (drawerLeader) { drawerKeydown(event); return; }
    if (event.key === "Escape" && $("site-sidebar")?.classList.contains("open")) {
      setMobileMenu(false); $("sidebar-toggle")?.focus();
    }
  });
}
function applyI18n() {
  all("[data-about-lang]").forEach(el => { el.hidden = el.dataset.aboutLang !== LANG; });
  all("[data-i18n]").forEach(el => {
    const value = I18N[LANG][el.dataset.i18n];
    if (value !== undefined) el.textContent = value; // Preserve new parent-authored copy without a known key.
  });
  document.documentElement.lang = LANG === "pt" ? "pt-BR" : "en";
  all(".lang-opt").forEach(el => el.classList.toggle("active",el.dataset.lang === LANG));
  const labels = {"leader-search":t("search"),"leader-country-filter":t("f_country"),"leader-min-n-filter":t("f_min_n"),"ts-dim":t("f_dimension"),"dist-dim":t("f_dimension"),"dist-group":t("f_group_by"),"dim-bar-select":t("f_dimension"),"scatter-x":`${t("f_dimension")} X`,"scatter-y":`${t("f_dimension")} Y`,"drawer-close":LANG === "pt" ? "Fechar perfil" : "Close profile","sidebar-toggle":LANG === "pt" ? "Menu de navegação" : "Navigation menu","lang-toggle":LANG === "pt" ? "Switch to English" : "Mudar para português"};
  for (const [id,label] of Object.entries(labels)) $(id)?.setAttribute("aria-label",label);
  if ($("leader-search")) $("leader-search").placeholder = t("search");
  text("export-countries",t("export_csv"));
  text("distribution-note",t("distribution_note"));
}
function setLanguage(language) {
  LANG = language === "en" ? "en" : "pt";
  storage("popin_lang",LANG);
  applyI18n();
  buildDtypeChips(); buildCountryControls(); buildDimensionControls();
  if (_cache.stats) renderKPIs(_cache.stats);
  if (_cache.countries) renderCountries(_cache.countries);
  if (_cache.leaders) renderLeaderRankList(_cache.leaders);
  if (_cache.yearlyGlobal) renderGlobalTrend(_cache.yearlyGlobal);
  if (_cache.yearly) renderTSLine();
  if (_cache.movers) renderMovers();
  if (_cache.distribution) renderHistogram();
  renderDrawerProfile(); renderDrawerTrend();
  for (const [id,state] of [...viewStates]) setState(id,state.kind,state.retry);
  updateRefreshStatus(); resizeVisiblePlots();
}
function buildDtypeChips() {
  const el = $("dtype-chips");
  if (!el || !_allDtypes.length) return;
  clearState("dtype-chips");
  const rows = [{dtype:"ALL",n:_allDtypes.reduce((sum,d) => sum+Number(d.n),0)},..._allDtypes];
  el.innerHTML = rows.map(d => `<button type="button" class="chip${d.dtype === GLOBAL_DTYPE ? " active" : ""}" data-dtype="${escapeHTML(d.dtype)}" aria-pressed="${d.dtype === GLOBAL_DTYPE}">${escapeHTML(dtypeLabel(d.dtype))}<span class="chip-n">${fmt(d.n,0)}</span></button>`).join("");
  el.querySelectorAll("[data-dtype]").forEach(button => button.addEventListener("click",() => {
    if (GLOBAL_DTYPE === button.dataset.dtype) return;
    GLOBAL_DTYPE = button.dataset.dtype;
    el.querySelectorAll("[data-dtype]").forEach(chip => { const active = chip.dataset.dtype === GLOBAL_DTYPE; chip.classList.toggle("active",active); chip.setAttribute("aria-pressed",String(active)); });
    void refreshAll();
  }));
}
function buildCountryControls() {
  const rows = [...countryCatalog.values()].sort((a,b) => countryName(a).localeCompare(countryName(b),locale()));
  const select = $("leader-country-filter"), selected = leaderCountry();
  if (select) {
    select.innerHTML = `<option value="ALL">${t("f_all")}</option>` + rows.map(c => `<option value="${escapeHTML(c.iso3)}">${escapeHTML(countryLabel(c))}</option>`).join("");
    if (selected !== "ALL" && !rows.some(c => c.iso3 === selected)) {
      const option = document.createElement("option"); option.value = selected; option.textContent = countryName(selected); select.appendChild(option);
    }
    select.value = selected;
  }
  for (const [id,radar] of [["country-radar-select",true],["ts-country-chips",false]]) {
    const el = $(id);
    if (!el) continue;
    el.innerHTML = rows.map(c => {
      const active = radar ? _radarSelected.includes(c.country) : TS.countries.includes(c.iso3);
      return `<button type="button" class="chip${active ? " active" : ""}" data-country="${escapeHTML(c.iso3)}" aria-pressed="${active}">${escapeHTML(countryName(c))}</button>`;
    }).join("");
    el.querySelectorAll("[data-country]").forEach(button => button.addEventListener("click",() => {
      const c = countryCatalog.get(button.dataset.country);
      const key = radar ? c.country : c.iso3, chosen = radar ? _radarSelected : TS.countries;
      const next = chosen.includes(key) ? chosen.filter(v => v !== key) : [...chosen,key];
      if (radar) _radarSelected = next; else TS.countries = next;
      const active = next.includes(key); button.classList.toggle("active",active); button.setAttribute("aria-pressed",String(active));
      if (radar && _cache.countries) renderCountryRadar(_cache.countries);
      else if (!radar) void refreshYearly();
    }));
  }
}
function buildDimensionControls() {
  for (const [id,value,dimensions] of [["dim-bar-select",_dimBarKey,DIMS.slice(1)],["ts-dim",TS.dim,DIMS],["dist-dim",DIST.dim,DIMS],["scatter-x",_scatterX,DIMS.slice(1)],["scatter-y",_scatterY,DIMS.slice(1)]]) {
    if (!$(id)) continue;
    html(id,dimensions.map(d => `<option value="${d.key}">${d[LANG]}</option>`).join(""));
    $(id).value = value;
  }
  html("trend-dim-toggle",DIMS.map(d => `<button type="button" class="toggle-btn${d.key === _activeTrendDim ? " active" : ""}" data-key="${d.key}" aria-pressed="${d.key === _activeTrendDim}">${d[LANG]}</button>`).join(""));
  $("trend-dim-toggle")?.querySelectorAll("[data-key]").forEach(button => button.addEventListener("click",() => {
    _activeTrendDim = button.dataset.key;
    $("trend-dim-toggle").querySelectorAll("[data-key]").forEach(el => { const active = el.dataset.key === _activeTrendDim; el.classList.toggle("active",active); el.setAttribute("aria-pressed",String(active)); });
    if (_cache.yearlyGlobal) renderGlobalTrend(_cache.yearlyGlobal); // Never capture an old dtype response.
  }));
}

const COUNTRY_VIEWS = ["hero-row","country-cards","chart-map","chart-country-box","chart-country-radar","chart-dim-bars","chart-scatter2d"];
function renderCountries(countries) {
  renderHeroBanner(countries); renderCountryCards(countries); renderMap(countries);
  renderCountryRanked(countries); renderCountryRadar(countries); renderDimBars(countries); renderScatter2D(countries);
}
function refreshCountries() {
  return request("countries",url("countries"),data => {
    _cache.countries = data;
    data.forEach(c => countryCatalog.set(c.iso3,c));
    buildCountryControls(); renderCountries(data);
    if ($("export-countries")) $("export-countries").disabled = !data.length;
  },() => {
    delete _cache.countries;
    COUNTRY_VIEWS.forEach(id => setState(id,"loading"));
    if ($("export-countries")) $("export-countries").disabled = true;
  },() => COUNTRY_VIEWS.forEach(id => setState(id,"error",refreshCountries)));
}
function refreshStats() {
  return request("stats",url("stats"),data => { _cache.stats = data; renderKPIs(data); },
    () => { delete _cache.stats; text("corpus-average","—"); setState("kpi-row","loading"); },
    () => setState("kpi-row","error",refreshStats));
}
function refreshLeaders() {
  closeLeaderDrawer(); updateScopeSummary();
  return request("leaders",url("leaders",{country:leaderCountry(),n:LEADER_LIMIT,min_n:leaderMinN()}),data => {
    _cache.leaders = data; renderLeaderRankList(data);
  },() => { delete _cache.leaders; text("leader-count-badge","—"); setState("leader-rank-list","loading"); },
    () => setState("leader-rank-list","error",refreshLeaders));
}
function refreshGlobalTrend() {
  return request("globalTrend",url("yearly_global"),data => { _cache.yearlyGlobal = data; renderGlobalTrend(data); },
    () => { delete _cache.yearlyGlobal; setState("chart-trend","loading"); },() => setState("chart-trend","error",refreshGlobalTrend));
}
function refreshYearly() {
  if (!TS.countries.length) {
    cancelRequest("yearly"); _cache.yearly = []; renderTSLine(); updateRefreshStatus(); return Promise.resolve();
  }
  return request("yearly",url("yearly",{countries:TS.countries.join(","),dim:TS.dim}),data => { _cache.yearly = data; renderTSLine(); },
    () => { delete _cache.yearly; setState("chart-ts-line","loading"); },() => setState("chart-ts-line","error",refreshYearly));
}
function refreshMovers() {
  return request("movers",url("yearly",{dim:"final_score"}),data => { _cache.movers = data; renderMovers(); },
    () => { delete _cache.movers; setState("chart-movers","loading"); },() => setState("chart-movers","error",refreshMovers));
}
function refreshDistribution() {
  return request("distribution",url("distribution",{dim:DIST.dim,group:DIST.group,year_min:2000,year_max:2025}),data => { _cache.distribution = data; renderHistogram(); },
    () => { delete _cache.distribution; setState("chart-hist","loading"); },() => setState("chart-hist","error",refreshDistribution));
}
function refreshDtypes() {
  return request("dtypes","/api/dtypes",data => { _allDtypes = data; buildDtypeChips(); },
    () => setState("dtype-chips","loading"),() => setState("dtype-chips","error",refreshDtypes));
}
async function refreshAll() {
  scopeVersion++;
  closeLeaderDrawer();
  for (const key of [...requests.keys()]) cancelRequest(key);
  resourceStates.clear();
  updateScopeSummary();
  await Promise.allSettled([refreshStats(),refreshCountries(),refreshLeaders(),refreshGlobalTrend(),refreshYearly(),refreshMovers(),refreshDistribution(),
    ...(!_allDtypes.length ? [refreshDtypes()] : [])]);
}
function countriesCSV(countries) {
  // Machine-readable decimal points; labels and metadata preserve API identity and scope.
  const cell = value => `"${String(value ?? "").replace(/^[=+@\-\t\r]/,"'$&").replace(/"/g,'""')}"`;
  const fields = ["iso3","country","country_display","dtype","n","final_score","p25","p75",...DIMS.slice(1).map(d => d.key)];
  return "\uFEFF"+[fields,...countries.map(c => fields.map(key => key === "country_display" ? countryName(c) : key === "dtype" ? GLOBAL_DTYPE : c[key]))].map(row => row.map(cell).join(",")).join("\r\n");
}
function exportCountries() {
  if (!_cache.countries?.length) return;
  const objectURL = URL.createObjectURL(new Blob([countriesCSV(_cache.countries)],{type:"text/csv;charset=utf-8"}));
  const link = document.createElement("a");
  link.href = objectURL; link.download = `popin-countries-${GLOBAL_DTYPE.replace(/[^a-z0-9_-]/gi,"_")}.csv`;
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(objectURL),1000);
}
function bindControls() {
  $("leader-country-filter")?.addEventListener("change",refreshLeaders);
  $("leader-min-n-filter")?.addEventListener("change",refreshLeaders);
  $("leader-search")?.addEventListener("input",() => { if (_cache.leaders) renderLeaderRankList(_cache.leaders); });
  $("dim-bar-select")?.addEventListener("change",event => { _dimBarKey = event.target.value; if (_cache.countries) renderDimBars(_cache.countries); });
  $("ts-dim")?.addEventListener("change",event => { TS.dim = event.target.value; void refreshYearly(); });
  for (const id of ["dist-dim","dist-group"]) $(id)?.addEventListener("change",() => {
    DIST.dim = $("dist-dim")?.value ?? DIST.dim; DIST.group = $("dist-group")?.value ?? DIST.group; void refreshDistribution();
  });
  for (const id of ["scatter-x","scatter-y"]) $(id)?.addEventListener("change",() => {
    _scatterX = $("scatter-x")?.value ?? _scatterX; _scatterY = $("scatter-y")?.value ?? _scatterY;
    if (_cache.countries) renderScatter2D(_cache.countries);
  });
  $("drawer-close")?.addEventListener("click",closeLeaderDrawer);
  $("drawer-overlay")?.addEventListener("click",closeLeaderDrawer);
  $("export-countries")?.addEventListener("click",exportCountries);
}
async function main() {
  LANG = storage("popin_lang") === "en" ? "en" : "pt";
  document.documentElement.dataset.theme = "light";
  if ($("leader-drawer")) { $("leader-drawer").inert = true; $("leader-drawer").setAttribute("aria-hidden","true"); }
  // Keep availability stable through empty dtype responses, without making up measurements.
  Object.entries(COUNTRIES).forEach(([iso3,row]) => countryCatalog.set(iso3,{iso3,country:row[0]}));
  if ($("chart-hist") && !$("distribution-note")) {
    const note = document.createElement("p"); note.id = "distribution-note"; note.className = "section-note";
    $("chart-hist").insertAdjacentElement("afterend",note);
  }
  applyI18n(); buildDimensionControls(); buildCountryControls(); bindControls(); initNav(); initPlotSizing();
  // Loading is local to each region; navigation and independent resources remain usable.
  $("loader")?.classList.add("hidden");
  if ($("loader")) $("loader").hidden = true;
  await refreshAll();
}
if (typeof document !== "undefined") {
  const start = () => main().catch(error => {
    console.error("POPIN initialization:",error);
    setState("kpi-row","error",() => window.location.reload());
  });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded",start,{once:true});
  else void start();
}
