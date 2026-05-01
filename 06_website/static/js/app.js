/* ═══════════════════════════════════════════════════════════════════
   POPIN v4 · App — populismo descomplicado
   Refs: CNN Election · Our World in Data · Grafana · The Pudding
═══════════════════════════════════════════════════════════════════ */

// ── i18n ──────────────────────────────────────────────────────────────
const I18N = {
  pt: {
    nav_overview:"Visão Geral", nav_countries:"Países", nav_leaders:"Líderes",
    nav_timeseries:"Série Temporal", nav_dimensions:"Dimensões",
    brand_sub:"Índice de Populismo · América Latina",
    loading:"Carregando dados…",
    ov_sub:"Populismo na América Latina · 2000–2025",
    ct_sub:"Análise comparativa de 19 países",
    ld_sub:"Clique em um líder para ver o perfil completo",
    ts_sub:"Evolução do populismo · 2000–2025",
    dm_sub:"Scores médios por dimensão de populismo",
    kpi_discourses:"Discursos analisados",
    kpi_countries:"Países cobertos",
    kpi_leaders:"Líderes identificados",
    kpi_years:"Anos de dados",
    cc_speeches:"discursos", cc_title:"Score por País", badge_ranked:"ordenado",
    badge_final:"Score Final", badge_radar:"Radar", badge_delta:"Δ Score",
    chart_map:"Mapa do Populismo",
    chart_trend:"Tendência Global do Populismo",
    chart_radar:"Perfil de Populismo", chart_ranked:"Ranking de Score",
    chart_dim_bars:"Dimensões por País",
    chart_leaders:"Ranking de Líderes",
    chart_ts_line:"Comparação por País",
    chart_movers:"Variação 2000–2025 por País",
    chart_means:"Score Médio por Grupo",
    chart_scatter2d:"Dispersão entre Dimensões",
    f_countries:"Países", f_country:"País", f_all:"Todos os Países",
    f_dimension:"Dimensão", f_group_by:"Agrupar por",
    f_discourse:"Tipo de Discurso", f_filter_by:"Tipo de discurso",
    drawer_dims:"Subdimensões", drawer_trend:"Evolução Histórica", drawer_radar:"Perfil Radar",
    dim_people:"Povo-Centrismo", dim_elite:"Anti-Elitismo", dim_moral:"Dicotomia Moral",
    dim_sovereignty:"Soberania Popular", dim_excl:"Retórica Excludente", dim_crisis:"Retórica de Crise",
    lr_click_hint:"ver perfil",
    hero_most:"Mais populista", hero_least:"Menos populista",
    legend_title:"Escala de Populismo",
    legend_low:"Baixo · 0–30", legend_med:"Moderado · 30–50",
    legend_high:"Alto · 50–65", legend_vhigh:"Muito Alto · 65+",
    dtype_all:"Todos",
    dtype_SPEECH:"Discurso", dtype_INTERVIEW:"Entrevista", dtype_DECREE:"Decreto",
    dtype_LETTER:"Carta", dtype_COMMUNIQUE:"Comunicado", dtype_PRESS_RELEASE:"Nota à Imprensa",
  },
  en: {
    nav_overview:"Overview", nav_countries:"Countries", nav_leaders:"Leaders",
    nav_timeseries:"Time Series", nav_dimensions:"Dimensions",
    brand_sub:"Populism Index · Latin America",
    loading:"Loading dataset…",
    ov_sub:"Populism across Latin America · 2000–2025",
    ct_sub:"Comparative analysis across 19 nations",
    ld_sub:"Click on a leader to see the full profile",
    ts_sub:"Populism evolution · 2000–2025",
    dm_sub:"Mean scores per populism dimension",
    kpi_discourses:"Discourses analyzed",
    kpi_countries:"Countries covered",
    kpi_leaders:"Leaders identified",
    kpi_years:"Years of data",
    cc_speeches:"speeches", cc_title:"Score by Country", badge_ranked:"ranked",
    badge_final:"Final Score", badge_radar:"Radar", badge_delta:"Δ Score",
    chart_map:"Populism Map",
    chart_trend:"Global Populism Trend",
    chart_radar:"Populism Profile", chart_ranked:"Score Ranking",
    chart_dim_bars:"Dimensions by Country",
    chart_leaders:"Leader Ranking",
    chart_ts_line:"Country Comparison",
    chart_movers:"Change 2000–2025 by Country",
    chart_means:"Mean Score by Group",
    chart_scatter2d:"Dimension Scatter",
    f_countries:"Countries", f_country:"Country", f_all:"All Countries",
    f_dimension:"Dimension", f_group_by:"Group by",
    f_discourse:"Discourse Type", f_filter_by:"Discourse type",
    drawer_dims:"Sub-dimensions", drawer_trend:"Historical Evolution", drawer_radar:"Radar Profile",
    dim_people:"People Centrism", dim_elite:"Anti-Elitism", dim_moral:"Moral Dichotomy",
    dim_sovereignty:"Popular Sovereignty", dim_excl:"Exclusionary Rhetoric", dim_crisis:"Crisis Rhetoric",
    lr_click_hint:"view profile",
    hero_most:"Most populist", hero_least:"Least populist",
    legend_title:"Populism Scale",
    legend_low:"Low · 0–30", legend_med:"Moderate · 30–50",
    legend_high:"High · 50–65", legend_vhigh:"Very High · 65+",
    dtype_all:"All",
    dtype_SPEECH:"Speech", dtype_INTERVIEW:"Interview", dtype_DECREE:"Decree",
    dtype_LETTER:"Letter", dtype_COMMUNIQUE:"Communiqué", dtype_PRESS_RELEASE:"Press Release",
  }
};

let LANG = "pt";
const t = k => I18N[LANG][k] ?? I18N.en[k] ?? k;

// ── Dimensions ────────────────────────────────────────────────────────
const DIMS = [
  { key:"final_score",           pt:"Score Final",          en:"Final Score"           },
  { key:"people_centrism",       pt:"Povo-Centrismo",       en:"People Centrism"       },
  { key:"anti_elitism",          pt:"Anti-Elitismo",        en:"Anti-Elitism"          },
  { key:"moral_dichotomy",       pt:"Dicotomia Moral",      en:"Moral Dichotomy"       },
  { key:"popular_sovereignty",   pt:"Soberania Popular",    en:"Popular Sovereignty"   },
  { key:"exclusionary_rhetoric", pt:"Retórica Excludente",  en:"Exclusionary Rhetoric" },
  { key:"crisis_rhetoric",       pt:"Retórica de Crise",    en:"Crisis Rhetoric"       },
];

const COUNTRY_COLORS = {
  Venezuela:"#F87171", Nicaragua:"#FB923C", Bolivia:"#FBBF24", Ecuador:"#34D399",
  Mexico:"#2DD4BF", Argentina:"#38BDF8", Brazil:"#60A5FA", Peru:"#A78BFA",
  Colombia:"#F472B6", Paraguay:"#F43F5E", Guatemala:"#86EFAC", Honduras:"#67E8F9",
  Panama:"#FCD34D", Chile:"#818CF8", "El Salvador":"#E879F9", Uruguay:"#4ADE80",
  "Dom. Republic":"#FCA5A5", "Costa Rica":"#BEF264", Cuba:"#C084FC",
};

const FLAGS = {
  ARG:"🇦🇷", BOL:"🇧🇴", BRA:"🇧🇷", CHL:"🇨🇱", COL:"🇨🇴", CRI:"🇨🇷",
  CUB:"🇨🇺", DOM:"🇩🇴", ECU:"🇪🇨", GTM:"🇬🇹", HND:"🇭🇳", MEX:"🇲🇽",
  NIC:"🇳🇮", PAN:"🇵🇦", PER:"🇵🇪", PRY:"🇵🇾", SLV:"🇸🇻", URY:"🇺🇾",
  VEN:"🇻🇪",
};

// Approximate country centroids [lat, lon]
const CENTROIDS = {
  ARG:[-34,-64], BOL:[-17,-65], BRA:[-14,-51], CHL:[-35,-71],
  COL:[4,-72],   CRI:[10,-84],  CUB:[22,-79],  DOM:[19,-70],
  ECU:[-2,-78],  GTM:[15,-90],  HND:[15,-87],  MEX:[23,-102],
  NIC:[13,-85],  PAN:[9,-80],   PER:[-10,-76], PRY:[-23,-58],
  SLV:[14,-89],  URY:[-33,-56], VEN:[7,-66],
};

// ── Smooth populism color scale (dual-theme) ──────────────────────────
const _COLOR_STOPS_DARK = [
  [  0, [  9,  17,  30]],   // near-background — very low
  [ 25, [ 14, 165, 233]],   // #0EA5E9 sky blue
  [ 50, [234, 179,   8]],   // #EAB308 amber
  [ 72, [239,  68,  68]],   // #EF4444 red
  [100, [127,  29,  29]],   // #7F1D1D dark red
];
const _COLOR_STOPS_LIGHT = [
  [  0, [147, 197, 253]],   // #93C5FD light blue (visível sobre branco)
  [ 25, [ 14, 165, 233]],   // #0EA5E9 sky blue
  [ 50, [234, 179,   8]],   // #EAB308 amber
  [ 72, [239,  68,  68]],   // #EF4444 red
  [100, [127,  29,  29]],   // #7F1D1D dark red
];

let _COLOR_STOPS = _COLOR_STOPS_DARK;
let POP_SCALE = [
  [0.00, "#09111E"], [0.25, "#0EA5E9"],
  [0.50, "#EAB308"], [0.72, "#EF4444"], [1.00, "#7F1D1D"],
];

function popColor(score) {
  const s = Math.max(0, Math.min(100, score ?? 0));
  let lo = _COLOR_STOPS[0], hi = _COLOR_STOPS[_COLOR_STOPS.length - 1];
  for (let i = 0; i < _COLOR_STOPS.length - 1; i++) {
    if (s >= _COLOR_STOPS[i][0] && s <= _COLOR_STOPS[i+1][0]) {
      lo = _COLOR_STOPS[i]; hi = _COLOR_STOPS[i+1]; break;
    }
  }
  const t = lo[0] === hi[0] ? 0 : (s - lo[0]) / (hi[0] - lo[0]);
  const r = Math.round(lo[1][0] + t * (hi[1][0] - lo[1][0]));
  const g = Math.round(lo[1][1] + t * (hi[1][1] - lo[1][1]));
  const b = Math.round(lo[1][2] + t * (hi[1][2] - lo[1][2]));
  return `rgb(${r},${g},${b})`;
}

function updateColorStops() {
  if (THEME === "dark") {
    _COLOR_STOPS = _COLOR_STOPS_DARK;
    POP_SCALE = [[0.00,"#09111E"],[0.25,"#0EA5E9"],[0.50,"#EAB308"],[0.72,"#EF4444"],[1.00,"#7F1D1D"]];
  } else {
    _COLOR_STOPS = _COLOR_STOPS_LIGHT;
    POP_SCALE = [[0.00,"#93C5FD"],[0.25,"#0EA5E9"],[0.50,"#EAB308"],[0.72,"#EF4444"],[1.00,"#7F1D1D"]];
  }
}

// ── Tema ──────────────────────────────────────────────────────────────
let THEME = "dark";

const BG0 = "rgba(0,0,0,0)";
let GRID_C = "rgba(255,255,255,.04)";
let ZERO_C = "rgba(255,255,255,.08)";
let FONT_C = "#C4D4EE";

const BASE_LAY = {
  paper_bgcolor: BG0, plot_bgcolor: BG0,
  font:{ family:"Inter,system-ui,sans-serif", color: FONT_C, size:12 },
  margin:{ t:16, r:16, b:40, l:48 },
  colorway: Object.values(COUNTRY_COLORS),
  hoverlabel:{ bgcolor:"#0F1828", bordercolor:"rgba(255,255,255,.10)", font:{ family:"Inter,system-ui,sans-serif", color:"#E6EEFF", size:13 } },
};
const CFG = { displayModeBar:false, responsive:true };
const AX = (e={}) => ({ gridcolor:GRID_C, linecolor:GRID_C, zerolinecolor:ZERO_C, tickcolor:FONT_C, ...e });

function updateThemeVars() {
  if (THEME === "dark") {
    GRID_C = "rgba(255,255,255,.05)";
    ZERO_C = "rgba(255,255,255,.10)";
    FONT_C = "#C4D4EE";   // quase branco azulado — alto contraste no escuro
    BASE_LAY.font.color = FONT_C;
    BASE_LAY.hoverlabel.bgcolor = "#0F1828";
    BASE_LAY.hoverlabel.bordercolor = "rgba(255,255,255,.12)";
    BASE_LAY.hoverlabel.font.color = "#E6EEFF";
  } else {
    GRID_C = "rgba(0,0,0,.07)";
    ZERO_C = "rgba(0,0,0,.12)";
    FONT_C = "#1E2E42";   // quase preto azulado — alto contraste no claro
    BASE_LAY.font.color = FONT_C;
    BASE_LAY.hoverlabel.bgcolor = "#FFFFFF";
    BASE_LAY.hoverlabel.bordercolor = "rgba(0,0,0,.08)";
    BASE_LAY.hoverlabel.font.color = "#18243A";
  }
}

function mapGeoColors() {
  return THEME === "dark" ? {
    bgcolor:      "#1A2236",   // igual ao --card: sem "caixa" visível
    oceancolor:   "#0C1118",   // igual ao --bg: oceano bem escuro
    landcolor:    "#131B2A",   // igual ao --bg2: países fora do dataset
    countrycolor: "#2A3A58",   // borda sutil entre países
  } : {
    bgcolor:      "#FFFFFF",   // igual ao --card
    oceancolor:   "#EEF3FA",   // igual ao --bg: azul muito claro
    landcolor:    "#DCE8F5",   // países fora do dataset
    countrycolor: "#AABFD8",   // borda sutil
  };
}

async function setTheme(t) {
  THEME = t;
  document.documentElement.dataset.theme = t;
  updateThemeVars();
  updateColorStops();
  // Re-renderizar todos os gráficos ativos
  if (_cache.countries) {
    renderMap(_cache.countries);
    renderCountryCards(_cache.countries);
    renderHeroBanner(_cache.countries);
    renderCountryRanked(_cache.countries);
    renderDimBars(_cache.countries);
    if (_radarSelected.length) renderCountryRadar(_cache.countries, _radarSelected);
    renderMovers(_cache.countries);
    renderScatter2D(_cache.countries);
  }
  if (_cache.stats)        renderKPIs(_cache.stats);
  if (_cache.leaders)      renderLeaderRankList(_cache.leaders);
  if (_cache.yearlyGlobal) renderGlobalTrend(_cache.yearlyGlobal, _activeTrendDim);
  renderTSLine();
  renderHistogram();
}

// ── Helpers ───────────────────────────────────────────────────────────
const api = async p => { const r = await fetch(p); if(!r.ok) throw new Error(`API ${r.status}: ${p}`); return r.json(); };
// Responsive chart left margin (bar charts with country names)
const mL = () => window.innerWidth <= 480 ? 72 : window.innerWidth <= 768 ? 90 : 130;
// rgba: accepts both "#rrggbb" and "rgb(r,g,b)" strings
const rgba = (color, a) => {
  if (color.startsWith("rgb(")) {
    const [r,g,b] = color.slice(4,-1).split(",").map(Number);
    return `rgba(${r},${g},${b},${a})`;
  }
  const h = color.replace(/^#/,"");
  return `rgba(${parseInt(h.slice(0,2),16)},${parseInt(h.slice(2,4),16)},${parseInt(h.slice(4,6),16)},${a})`;
};
const ctryColor = n => COUNTRY_COLORS[n] ?? "#64748B";
const dimLabel  = k => DIMS.find(d=>d.key===k)?.[LANG] ?? k;
const dimLabels = () => DIMS.slice(1).map(d => d[LANG]);
const dtypeQ    = () => GLOBAL_DTYPE && GLOBAL_DTYPE !== "ALL" ? `&dtype=${GLOBAL_DTYPE}` : "";

function lay(ov={}) {
  const b = JSON.parse(JSON.stringify(BASE_LAY));
  for(const [k,v] of Object.entries(ov))
    b[k] = (v && typeof v==="object" && !Array.isArray(v) && b[k] && typeof b[k]==="object") ? {...b[k],...v} : v;
  return b;
}

// ── i18n DOM update ───────────────────────────────────────────────────
function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.dataset.i18n;
    const val = t(key);
    if(val) el.textContent = val;
  });
  document.documentElement.lang = LANG;
}

// ── Global discourse-type filter ──────────────────────────────────────
let GLOBAL_DTYPE = "ALL";
let _allDtypes   = [];

async function initDtypeFilter() {
  _allDtypes = await api("/api/dtypes");
  const container = document.getElementById("dtype-chips");

  const totalN = _allDtypes.reduce((s, d) => s + d.n, 0);
  const fmtN   = n => n >= 1000 ? (n / 1000).toFixed(1) + "k" : String(n);

  const makeChip = (label, value, n) => {
    const chip = document.createElement("div");
    chip.className = `chip ${value === GLOBAL_DTYPE ? "active" : ""}`;
    chip.dataset.dtype = value;
    if (n != null) {
      chip.innerHTML = `${label}<span class="chip-n">${fmtN(n)}</span>`;
    } else {
      chip.innerHTML = `${label}<span class="chip-n">${fmtN(totalN)}</span>`;
    }
    chip.addEventListener("click", () => {
      if (GLOBAL_DTYPE === value) return;
      GLOBAL_DTYPE = value;
      container.querySelectorAll(".chip").forEach(c => c.classList.toggle("active", c.dataset.dtype === value));
      refreshAll();
    });
    return chip;
  };

  container.appendChild(makeChip(t("dtype_all"), "ALL", null));
  _allDtypes.forEach(d => container.appendChild(makeChip(t(`dtype_${d.dtype}`) || d.dtype, d.dtype, d.n)));
}

// ── Navigation ────────────────────────────────────────────────────────
function navigateTo(sec) {
  document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
  const navItem = document.querySelector(`.nav-item[data-section="${sec}"]`);
  if (navItem) navItem.classList.add("active");
  document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
  const secEl = document.getElementById(`section-${sec}`);
  if (secEl) secEl.classList.add("active");
  localStorage.setItem("popin_section", sec);
  window.dispatchEvent(new Event("resize"));
}

function initNav() {
  // Restaurar aba salva (ou "overview" como fallback)
  const saved = localStorage.getItem("popin_section") ?? "overview";
  navigateTo(saved);

  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", () => {
      navigateTo(item.dataset.section);
      if (window.innerWidth <= 768) closeMobileSidebar();
    });
  });

  document.getElementById("theme-toggle").addEventListener("click", () => {
    const next = THEME === "dark" ? "light" : "dark";
    localStorage.setItem("popin_theme", next);
    setTheme(next);
  });

  document.getElementById("lang-toggle").addEventListener("click", () => {
    LANG = LANG==="pt" ? "en" : "pt";
    localStorage.setItem("popin_lang", LANG);
    document.querySelectorAll(".lang-opt").forEach(el => {
      el.classList.toggle("active", el.dataset.lang===LANG);
    });
    applyI18n();
    refreshChartLabels();
    if(_cache.stats)     renderKPIs(_cache.stats);
    if(_cache.countries) { renderCountryCards(_cache.countries); renderHeroBanner(_cache.countries); }
    if(_cache.leaders)   renderLeaderRankList(_cache.leaders);
  });

  // ── Mobile sidebar toggle ─────────────────────────────────────────
  const sidebar    = document.querySelector(".sidebar");
  const overlay    = document.getElementById("sidebar-mob-overlay");
  const toggleBtn  = document.getElementById("sidebar-toggle");

  function openMobileSidebar() {
    sidebar.classList.add("open");
    overlay.classList.add("open");
    document.body.style.overflow = "hidden";
  }
  function closeMobileSidebar() {
    sidebar.classList.remove("open");
    overlay.classList.remove("open");
    document.body.style.overflow = "";
  }
  // expose to nav-item handler above
  window.closeMobileSidebar = closeMobileSidebar;

  toggleBtn.addEventListener("click", () => {
    sidebar.classList.contains("open") ? closeMobileSidebar() : openMobileSidebar();
  });
  overlay.addEventListener("click", closeMobileSidebar);
}

// ── Global cache ──────────────────────────────────────────────────────
const _cache = {};

function refreshChartLabels() {
  document.querySelectorAll("#trend-dim-toggle .toggle-btn").forEach(btn => {
    const dim = DIMS.find(d => d.key === btn.dataset.key);
    if (dim) btn.textContent = dim[LANG];
  });
  document.querySelectorAll("#ts-dim option, #dist-dim option, #dim-bar-select option, #scatter-x option, #scatter-y option").forEach(opt => {
    const dim = DIMS.find(d => d.key === opt.value);
    if (dim) opt.textContent = dim[LANG];
  });
  // Update dtype chip labels (preserve the .chip-n count span)
  document.querySelectorAll("#dtype-chips .chip").forEach(chip => {
    const dv   = chip.dataset.dtype;
    const span = chip.querySelector(".chip-n");
    const lbl  = dv === "ALL" ? t("dtype_all") : (t(`dtype_${dv}`) || dv);
    chip.innerHTML = `${lbl}${span ? span.outerHTML : ""}`;
  });
}

// ── Refresh everything after dtype change ─────────────────────────────
async function refreshAll() {
  const [stats, countries, leaders, yearlyGlobal] = await Promise.all([
    api(`/api/stats?${dtypeQ().slice(1)}`),
    api(`/api/countries?${dtypeQ().slice(1)}`),
    api(`/api/leaders?n=25${dtypeQ()}`),
    api(`/api/yearly_global?${dtypeQ().slice(1)}`),
  ]);
  _cache.stats=stats; _cache.countries=countries; _cache.leaders=leaders;

  renderKPIs(stats);
  renderHeroBanner(countries);
  renderCountryCards(countries);
  renderMap(countries);
  renderGlobalTrend(yearlyGlobal, _activeTrendDim);

  renderCountryRanked(countries);
  renderDimBars(countries);
  if(_radarSelected.length) renderCountryRadar(countries, _radarSelected);

  const lfilterSel = document.getElementById("leader-country-filter");
  if(lfilterSel) {
    document.getElementById("leader-count-badge").textContent = leaders.length;
    renderLeaderRankList(leaders);
  }

  renderTSLine();
  renderMovers(countries);
  renderHistogram();
  renderScatter2D(countries);
}

// ── KPIs ──────────────────────────────────────────────────────────────
function renderKPIs(stats) {
  document.getElementById("kpi-row").innerHTML = [
    { k:"kpi_discourses", v:stats.n_discourses.toLocaleString("pt-BR"), icon:"📄" },
    { k:"kpi_countries",  v:stats.n_countries,   icon:"🌎" },
    { k:"kpi_leaders",    v:stats.n_leaders,      icon:"🎙️" },
    { k:"kpi_years",      v:`${stats.year_min}–${stats.year_max}`, icon:"📅" },
  ].map(c=>`<div class="kpi-card">
    <div class="kpi-icon">${c.icon}</div>
    <div class="kpi-value">${c.v}</div>
    <div class="kpi-label">${t(c.k)}</div>
  </div>`).join("");
}

// ── Hero Banner (top/bottom country) ─────────────────────────────────
function renderHeroBanner(countries) {
  const sorted = [...countries].sort((a,b) => b.final_score - a.final_score);
  const top = sorted[0];
  const low = sorted[sorted.length - 1];
  const container = document.getElementById("hero-row");
  if(!container) return;

  const card = (c, tag) => {
    const col = popColor(c.final_score);
    const flag = FLAGS[c.iso3] ?? "";
    return `<div class="hero-card">
      <div class="hero-tag">${tag}</div>
      <div class="hero-country" style="color:${col}">${flag} ${c.country}</div>
      <div class="hero-score" style="color:${col}">Score: ${c.final_score.toFixed(1)} / 100</div>
      <div class="hero-bar-wrap"><div class="hero-bar-fill" style="width:${c.final_score}%;background:${col}"></div></div>
    </div>`;
  };
  container.innerHTML = card(top, t("hero_most")) + card(low, t("hero_least"));
}

// ── Country List (compact ranked rows) ───────────────────────────────
function renderCountryCards(countries) {
  const sorted = [...countries].sort((a,b) => b.final_score - a.final_score);
  document.getElementById("country-cards").innerHTML = sorted.map((c, i) => {
    const col = popColor(c.final_score);
    const pct = Math.min(c.final_score, 100);
    const flag = FLAGS[c.iso3] ?? "";
    return `<div class="cc-row">
      <span class="cc-rank">${i+1}</span>
      <span class="cc-flag-sm">${flag}</span>
      <span class="cc-label">${c.country}</span>
      <div class="cc-bar-inline">
        <div class="cc-bar-inline-fill" style="width:${pct}%;background:${col}"></div>
      </div>
      <span class="cc-score-sm" style="color:${col}">${c.final_score.toFixed(1)}</span>
    </div>`;
  }).join("");
}

// ── Choropleth Map + ISO labels ───────────────────────────────────────
function renderMap(countries) {
  const withC = countries.filter(c => CENTROIDS[c.iso3]);

  // Choropleth: filled country shapes
  const choropleth = {
    type: "choropleth",
    locationmode: "ISO-3",
    locations: countries.map(c => c.iso3),
    z: countries.map(c => c.final_score),
    text: countries.map(c =>
      `<b>${FLAGS[c.iso3]??""} ${c.country}</b><br>Score: <b>${c.final_score.toFixed(1)}</b><br>${c.n.toLocaleString()} ${t("cc_speeches")}`
    ),
    hoverinfo: "text",
    colorscale: POP_SCALE,
    zmin: 0, zmax: 80,
    showscale: true,
    colorbar: {
      thickness: 10, len: 0.72, x: 1.01, outlinewidth: 0,
      tickcolor: FONT_C, tickfont: {color: FONT_C, size: 10},
      title: {text: "", font: {size: 10}},
    },
    marker: { line: { color: THEME === "dark" ? "#030812" : "#A8C4DC", width: 0.7 } },
  };

  // ISO labels on top via scattergeo
  const labels = {
    type: "scattergeo",
    lat: withC.map(c => CENTROIDS[c.iso3][0]),
    lon: withC.map(c => CENTROIDS[c.iso3][1]),
    text: withC.map(c => c.iso3),
    mode: "text",
    textfont: { color: THEME === "dark" ? "rgba(255,255,255,0.75)" : "rgba(20,36,60,0.6)", size: 8, family:"Inter,system-ui,sans-serif" },
    hoverinfo: "none",
    showlegend: false,
  };

  const geo = mapGeoColors();
  const layout = {
    paper_bgcolor: BG0,
    margin: { t:0, r:10, b:0, l:0 },
    geo: {
      bgcolor: geo.bgcolor,
      showland: true,  landcolor: geo.landcolor,
      showocean: true, oceancolor: geo.oceancolor,
      showcountries: true, countrycolor: geo.countrycolor,
      showframe: false, showcoastlines: false,
      countrywidth: 0.5,
      projection: { type:"mercator" },
      lataxis: { range:[-58, 35] },
      lonaxis: { range:[-118, -28] },
      showlakes: false,
    },
    hoverlabel: BASE_LAY.hoverlabel,
    showlegend: false,
  };

  Plotly.newPlot("chart-map", [choropleth, labels], layout, CFG);
}

// ── Global Trend ──────────────────────────────────────────────────────
let _activeTrendDim = "final_score";

function renderTrendToggle(yearlyGlobal) {
  _cache.yearlyGlobal = yearlyGlobal;   // cache para re-render no setTheme
  const container = document.getElementById("trend-dim-toggle");
  container.innerHTML = "";
  DIMS.forEach(d => {
    const btn = document.createElement("div");
    btn.className = `toggle-btn ${d.key===_activeTrendDim?"active":""}`;
    btn.textContent = d[LANG];
    btn.dataset.key = d.key;
    btn.addEventListener("click", () => {
      _activeTrendDim = d.key;
      container.querySelectorAll(".toggle-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      renderGlobalTrend(yearlyGlobal, _activeTrendDim);
    });
    container.appendChild(btn);
  });
  renderGlobalTrend(yearlyGlobal, _activeTrendDim);
}

function renderGlobalTrend(data, dim) {
  Plotly.newPlot("chart-trend", [{
    type:"scatter", mode:"lines+markers",
    x:data.map(d=>d.year), y:data.map(d=>d[dim]),
    line:{ color:"#4F8EF7", width:2.5, shape:"spline" },
    marker:{ size:5, color:"#4F8EF7" },
    fill:"tozeroy", fillcolor:rgba("#4F8EF7",.07),
    hovertemplate:"%{x}: <b>%{y:.1f}</b><extra></extra>",
  }], lay({
    margin:{t:10,r:16,b:38,l:48},
    xaxis:AX({dtick:2}),
    yaxis:AX({range:[0,80]}),
  }), CFG);
}

// ── Countries Section ─────────────────────────────────────────────────
function renderCountryRanked(countries) {
  const sorted = [...countries].sort((a,b)=>a.final_score-b.final_score);
  Plotly.newPlot("chart-country-box",[{
    type:"bar", orientation:"h",
    x:sorted.map(c=>c.final_score), y:sorted.map(c=>`${FLAGS[c.iso3]??""} ${c.country}`),
    text:sorted.map(c=>c.final_score.toFixed(1)),
    textposition:"outside", cliponaxis:false,
    textfont:{color:FONT_C,size:12,family:"Inter,system-ui,sans-serif"},
    marker:{color:sorted.map(c=>popColor(c.final_score)), opacity:0.88},
    hovertemplate:"<b>%{y}</b><br>Score: <b>%{x:.1f}</b><extra></extra>",
  }], lay({
    margin:{t:10,r:55,b:36,l:mL()},
    xaxis:AX({range:[0,95]}),
    yaxis:AX(),
    bargap:0.28, showlegend:false,
  }), CFG);
}

let _radarSelected = ["Venezuela","Brazil","Mexico","Argentina"];

function initCountryRadarSelect(countries) {
  const container = document.getElementById("country-radar-select");
  const names = countries.map(c=>c.country).sort();
  names.forEach(name => {
    const chip = document.createElement("div");
    chip.className = `chip ${_radarSelected.includes(name)?"active":""}`;
    chip.textContent = name;
    chip.addEventListener("click",()=>{
      if(_radarSelected.includes(name)){
        if(_radarSelected.length<=1)return;
        _radarSelected=_radarSelected.filter(n=>n!==name);
        chip.classList.remove("active");
      } else {
        if(_radarSelected.length>=7)return;
        _radarSelected.push(name);
        chip.classList.add("active");
      }
      renderCountryRadar(countries,_radarSelected);
    });
    container.appendChild(chip);
  });
  renderCountryRadar(countries,_radarSelected);
}

function renderCountryRadar(countries, selected) {
  const dimKeys = DIMS.slice(1).map(d=>d.key);
  const labels  = [...dimLabels(), dimLabel(DIMS[1].key)];
  const traces  = selected.map(name => {
    const c   = countries.find(x=>x.country===name); if(!c) return null;
    const col = ctryColor(name);
    return { type:"scatterpolar", mode:"lines+markers", name,
      r:[...dimKeys.map(k=>c[k]),c[dimKeys[0]]], theta:labels,
      fill:"toself", fillcolor:rgba(col,.08),
      line:{color:col,width:2}, marker:{size:4,color:col},
      hovertemplate:"<b>%{theta}</b>: %{r:.1f}<extra></extra>",
    };
  }).filter(Boolean);
  Plotly.newPlot("chart-country-radar", traces, lay({
    margin:{t:20,r:30,b:20,l:30},
    polar:{ bgcolor:BG0,
      radialaxis:{range:[0,80],tickfont:{size:9},gridcolor:GRID_C,linecolor:GRID_C},
      angularaxis:{gridcolor:GRID_C,tickfont:{size:10}},
    },
    legend:{font:{size:10},bgcolor:BG0},
  }), CFG);
}

// ── Dimension Bars per Country (replaces heatmap) ─────────────────────
let _dimBarKey = "people_centrism";

function initDimBarSelect() {
  const sel = document.getElementById("dim-bar-select");
  DIMS.slice(1).forEach(d => {
    const o = document.createElement("option");
    o.value = d.key; o.textContent = d[LANG];
    sel.appendChild(o);
  });
  sel.addEventListener("change", () => {
    _dimBarKey = sel.value;
    if(_cache.countries) renderDimBars(_cache.countries);
  });
}

function renderDimBars(countries) {
  const sorted = [...countries].sort((a,b) => a[_dimBarKey] - b[_dimBarKey]);
  Plotly.newPlot("chart-dim-bars",[{
    type:"bar", orientation:"h",
    x: sorted.map(c => c[_dimBarKey]),
    y: sorted.map(c => `${FLAGS[c.iso3]??""} ${c.country}`),
    text: sorted.map(c => (c[_dimBarKey]||0).toFixed(1)),
    textposition:"outside", cliponaxis:false,
    textfont:{color:FONT_C,size:12},
    marker:{color: sorted.map(c => popColor(c[_dimBarKey]||0)), opacity:0.88},
    hovertemplate:"<b>%{y}</b><br>Score: <b>%{x:.1f}</b><extra></extra>",
  }], lay({
    margin:{t:10,r:55,b:36,l:mL()},
    xaxis:AX({range:[0,95]}),
    yaxis:AX(),
    bargap:0.28, showlegend:false,
  }), CFG);
}

// ── Leader Rank List ──────────────────────────────────────────────────
function renderLeaderRankList(leaders) {
  const sorted = [...leaders].sort((a,b)=>b.final_score-a.final_score);
  document.getElementById("leader-rank-list").innerHTML = sorted.map((l,i)=>{
    const col = popColor(l.final_score);
    const pct = Math.min(l.final_score,100);
    const rankCls = i===0?"gold":i===1?"silver":i===2?"bronze":"";
    const leaderJson = JSON.stringify({
      name:l.leader_name, short:l.leader_short, country:l.country, iso3:l.iso3,
      score:l.final_score, n:l.n,
      people_centrism:l.people_centrism, anti_elitism:l.anti_elitism,
      moral_dichotomy:l.moral_dichotomy, popular_sovereignty:l.popular_sovereignty,
      exclusionary_rhetoric:l.exclusionary_rhetoric, crisis_rhetoric:l.crisis_rhetoric
    }).replace(/"/g,"&quot;");
    const flag = FLAGS[l.iso3] ?? "";
    return `<div class="lr-item" data-leader="${leaderJson}">
      <div class="lr-rank ${rankCls}">${i===0?"🥇":i===1?"🥈":i===2?"🥉":"#"+(i+1)}</div>
      <div class="lr-info">
        <div class="lr-name">${l.leader_short}</div>
        <div class="lr-sub">${flag} ${l.country} · ${(l.n||0).toLocaleString("pt-BR")} ${t("cc_speeches")}</div>
        <div class="lr-click-hint">${t("lr_click_hint")}</div>
      </div>
      <div class="lr-right">
        <div class="lr-score" style="color:${col}">${l.final_score.toFixed(1)}</div>
        <div class="lr-bar-wrap">
          <div class="lr-bar-fill" style="width:${pct}%;background:${col}"></div>
          <div class="lr-bar-mid"></div>
        </div>
        <div class="lr-click-hint">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
          ${t("lr_click_hint")}
        </div>
      </div>
    </div>`;
  }).join("");
  document.querySelectorAll(".lr-item").forEach(el => {
    el.addEventListener("click", () => openLeaderDrawer(JSON.parse(el.dataset.leader)));
  });
}

// ── Leader Drawer ─────────────────────────────────────────────────────
async function openLeaderDrawer(leader) {
  const overlay = document.getElementById("drawer-overlay");
  const drawer  = document.getElementById("leader-drawer");

  document.getElementById("drawer-name").textContent = leader.short;
  document.getElementById("drawer-meta").textContent =
    `${FLAGS[leader.iso3]??""} ${leader.country} (${leader.iso3}) · ${(leader.n||0).toLocaleString("pt-BR")} ${t("cc_speeches")}`;

  const col = popColor(leader.score);
  document.getElementById("drawer-score-row").innerHTML = `
    <div class="drawer-score-big" style="color:${col}">${leader.score.toFixed(1)}</div>
    <div class="drawer-score-label">${t("badge_final")}<br><span style="color:var(--text3);font-size:11px">0–100</span></div>`;

  const dimKeys = DIMS.slice(1);
  document.getElementById("drawer-dims").innerHTML = dimKeys.map(d => {
    const val = leader[d.key] ?? 0;
    const c   = popColor(val);
    const pct = Math.min(val,100);
    return `<div class="dim-bar-row">
      <div class="dim-bar-label">${d[LANG]}</div>
      <div class="dim-bar-track"><div class="dim-bar-fill" style="width:${pct}%;background:${c}"></div></div>
      <div class="dim-bar-val" style="color:${c}">${val.toFixed(1)}</div>
    </div>`;
  }).join("");

  overlay.classList.add("open");
  drawer.classList.add("open");

  try {
    const trend = await api(`/api/leader_trend?names=${encodeURIComponent(leader.name)}${dtypeQ()}`);
    if(trend.length) {
      trend.sort((a,b)=>a.year-b.year);
      Plotly.newPlot("chart-drawer-trend",[{
        type:"scatter", mode:"lines+markers",
        x:trend.map(r=>r.year), y:trend.map(r=>r.final_score),
        line:{color:col,width:2.5,shape:"spline"},
        marker:{size:5,color:col},
        fill:"tozeroy", fillcolor:rgba(col,.08),
        hovertemplate:"%{x}: <b>%{y:.1f}</b><extra></extra>",
      }], lay({
        margin:{t:10,r:10,b:36,l:44},
        xaxis:AX({dtick:2}),
        yaxis:AX({range:[0,80]}),
      }), CFG);
    }
  } catch(e) { console.warn("Trend error:", e); }

  const dimKeys2 = DIMS.slice(1).map(d=>d.key);
  const labels   = [...dimLabels(), dimLabel(DIMS[1].key)];
  const vals     = [...dimKeys2.map(k=>leader[k]??0), leader[dimKeys2[0]]??0];
  Plotly.newPlot("chart-drawer-radar",[{
    type:"scatterpolar", mode:"lines+markers", name:leader.short,
    r:vals, theta:labels,
    fill:"toself", fillcolor:rgba(col,.10),
    line:{color:col,width:2.5}, marker:{size:5,color:col},
    hovertemplate:"<b>%{theta}</b>: %{r:.1f}<extra></extra>",
  }], lay({
    margin:{t:16,r:16,b:16,l:16},
    polar:{ bgcolor:BG0,
      radialaxis:{range:[0,80],tickfont:{size:8},gridcolor:GRID_C,linecolor:GRID_C},
      angularaxis:{gridcolor:GRID_C,tickfont:{size:10}},
    },
    showlegend:false,
  }), CFG);
}

function closeLeaderDrawer() {
  document.getElementById("drawer-overlay").classList.remove("open");
  document.getElementById("leader-drawer").classList.remove("open");
}

// ── Time Series ───────────────────────────────────────────────────────
const TS = { countries:[], dim:"final_score" };

async function renderTSLine() {
  if(!TS.countries.length) return;
  const data = await api(`/api/yearly?countries=${TS.countries.join(",")}` +
    `&dim=${TS.dim}${dtypeQ()}`);
  const byC  = {};
  data.forEach(d => (byC[d.iso3]=byC[d.iso3]||[]).push(d));
  const traces = Object.entries(byC).map(([,rows])=>{
    rows.sort((a,b)=>a.year-b.year);
    return { type:"scatter", mode:"lines+markers", name:rows[0].country,
      x:rows.map(r=>r.year), y:rows.map(r=>r.score),
      line:{color:ctryColor(rows[0].country),width:2.5,shape:"spline"},
      marker:{size:5}, hovertemplate:"%{x}: <b>%{y:.1f}</b><extra></extra>",
    };
  });
  Plotly.newPlot("chart-ts-line", traces, lay({
    margin:{t:10,r:16,b:44,l:52},
    xaxis:AX({dtick:2}),
    yaxis:AX({range:[0,80],title:{text:dimLabel(TS.dim),font:{size:11}}}),
    legend:{font:{size:10},bgcolor:BG0},
  }), CFG);
}

// ── Top Movers (replaces heatmap) ─────────────────────────────────────
async function renderMovers(countries) {
  const data = await api(`/api/yearly?countries=${countries.map(c=>c.iso3).join(",")}` +
    `&dim=final_score${dtypeQ()}`);
  const byC = {};
  data.forEach(d => (byC[d.country]=byC[d.country]||[]).push(d));

  const deltas = Object.entries(byC).map(([name, rows]) => {
    rows.sort((a,b)=>a.year-b.year);
    const first = rows[0]?.score ?? 0;
    const last  = rows[rows.length-1]?.score ?? 0;
    return { country: name, iso3: rows[0]?.iso3, delta: +(last-first).toFixed(2) };
  }).sort((a,b)=>a.delta-b.delta);

  const colors = deltas.map(d => d.delta >= 0 ? "#F87171" : "#4ADE80");

  Plotly.newPlot("chart-movers",[{
    type:"bar", orientation:"h",
    x: deltas.map(d=>d.delta),
    y: deltas.map(d=>`${FLAGS[d.iso3]??""} ${d.country}`),
    text: deltas.map(d=>(d.delta>=0?"+":"")+d.delta.toFixed(1)),
    textposition:"outside", cliponaxis:false,
    textfont:{color:FONT_C,size:12},
    marker:{color:colors, opacity:0.85},
    hovertemplate:"<b>%{y}</b><br>Variação: <b>%{x:+.1f}</b><extra></extra>",
  }], lay({
    margin:{t:10,r:55,b:36,l:mL()},
    xaxis:AX({title:{text:"Δ Score",font:{size:11}}}),
    yaxis:AX(),
    bargap:0.3, showlegend:false,
  }), CFG);
}

function initTSCountryChips(countries) {
  const container = document.getElementById("ts-country-chips");
  const defaults  = ["BRA","VEN","MEX","ARG","BOL","COL"];
  TS.countries    = defaults.slice();
  countries.forEach(c => {
    const chip = document.createElement("div");
    chip.className = `chip ${defaults.includes(c.iso3)?"active":""}`;
    chip.textContent = `${FLAGS[c.iso3]??""} ${c.country}`;
    chip.addEventListener("click",()=>{
      if(TS.countries.includes(c.iso3)){
        if(TS.countries.length<=1)return;
        TS.countries=TS.countries.filter(x=>x!==c.iso3); chip.classList.remove("active");
      } else { TS.countries.push(c.iso3); chip.classList.add("active"); }
      renderTSLine();
    });
    container.appendChild(chip);
  });
}

function initTSFilters() {
  const sel = document.getElementById("ts-dim");
  DIMS.forEach(d=>{ const o=document.createElement("option"); o.value=d.key; o.textContent=d[LANG]; sel.appendChild(o); });
  sel.addEventListener("change",()=>{ TS.dim=sel.value; renderTSLine(); });
}

// ── Dimensions ────────────────────────────────────────────────────────
const DIST = { dim:"final_score", group:"country" };

async function renderHistogram() {
  const data   = await api(`/api/distribution?dim=${DIST.dim}&group=${DIST.group}${dtypeQ()}`);
  const colors = Object.values(COUNTRY_COLORS);
  const traces = data.slice(0,25).map((d,i)=>({
    type:"bar", name:d.group,
    x:[d.group], y:[d.mean],
    text:[d.mean.toFixed(1)], textposition:"outside", cliponaxis:false,
    textfont:{color:FONT_C,size:12},
    error_y:{type:"data",array:[(d.q3-d.q1)/2],visible:true,color:GRID_C,thickness:1.5,width:4},
    marker:{color:DIST.group==="country"?popColor(d.mean):colors[i%colors.length],opacity:0.88},
    hovertemplate:`<b>${d.group}</b><br>Média: ${d.mean.toFixed(1)}<br>IQR: ${d.q1.toFixed(1)}–${d.q3.toFixed(1)}<br>n=${d.n}<extra></extra>`,
  }));
  Plotly.newPlot("chart-hist", traces, lay({
    margin:{t:10,r:16,b:90,l:52},
    xaxis:AX({tickangle:-40,tickfont:{size:10}}),
    yaxis:AX({range:[0,105]}),
    showlegend:false, bargap:0.3,
  }), CFG);
}

// ── 2D Scatter (replaces correlation heatmap) ─────────────────────────
let _scatterX = "people_centrism", _scatterY = "anti_elitism";

function initScatterSelects() {
  ["scatter-x","scatter-y"].forEach((id, idx) => {
    const sel = document.getElementById(id);
    DIMS.slice(1).forEach(d => {
      const o = document.createElement("option");
      o.value = d.key; o.textContent = d[LANG];
      sel.appendChild(o);
    });
    sel.value = idx===0 ? _scatterX : _scatterY;
    sel.addEventListener("change", () => {
      _scatterX = document.getElementById("scatter-x").value;
      _scatterY = document.getElementById("scatter-y").value;
      if(_cache.countries) renderScatter2D(_cache.countries);
    });
  });
}

function renderScatter2D(countries) {
  // Sort to find outliers (top+bottom 4) that will get labels
  const sortedByX = [...countries].sort((a,b) => b[_scatterX] - a[_scatterX]);
  const outlierSet = new Set([
    ...sortedByX.slice(0,3).map(c=>c.iso3),
    ...sortedByX.slice(-2).map(c=>c.iso3),
    ...[...countries].sort((a,b)=>b[_scatterY]-a[_scatterY]).slice(0,2).map(c=>c.iso3),
  ]);

  const main = {
    type:"scatter", mode:"markers",
    x: countries.map(c=>c[_scatterX]),
    y: countries.map(c=>c[_scatterY]),
    customdata: countries.map(c=>[c.country, c.final_score, c.iso3]),
    marker:{
      size: countries.map(c => 9 + c.final_score * 0.12),
      color: countries.map(c=>c.final_score),
      colorscale: POP_SCALE,
      cmin:0, cmax:80, showscale:false,
      line:{color: THEME === "dark" ? "rgba(255,255,255,.15)" : "rgba(0,0,0,.12)", width:1},
      opacity:0.9,
    },
    hovertemplate:"<b>%{customdata[0]}</b><br>%{xaxis.title.text}: <b>%{x:.1f}</b><br>%{yaxis.title.text}: <b>%{y:.1f}</b><br>Score final: <b>%{customdata[1]:.1f}</b><extra></extra>",
  };

  // Outlier labels only
  const labeled = countries.filter(c => outlierSet.has(c.iso3));
  const labelTrace = {
    type:"scatter", mode:"text",
    x: labeled.map(c=>c[_scatterX]),
    y: labeled.map(c=>c[_scatterY]),
    text: labeled.map(c=>`${FLAGS[c.iso3]??""} ${c.iso3}`),
    textposition:"top center",
    textfont:{size:9, color:FONT_C},
    hoverinfo:"none",
    showlegend:false,
  };

  Plotly.newPlot("chart-scatter2d", [main, labelTrace], lay({
    margin:{t:10,r:20,b:50,l:60},
    xaxis:AX({title:{text:dimLabel(_scatterX),font:{size:11}},range:[0,100]}),
    yaxis:AX({title:{text:dimLabel(_scatterY),font:{size:11}},range:[0,100]}),
    showlegend:false,
  }), CFG);
}

function initDistFilters() {
  const dimSel=document.getElementById("dist-dim");
  DIMS.forEach(d=>{ const o=document.createElement("option"); o.value=d.key; o.textContent=d[LANG]; dimSel.appendChild(o); });
  const groupSel=document.getElementById("dist-group");
  const refresh=()=>{ DIST.dim=dimSel.value; DIST.group=groupSel.value; renderHistogram(); };
  dimSel.addEventListener("change",refresh);
  groupSel.addEventListener("change",refresh);
}

// ── Leader filter ─────────────────────────────────────────────────────
async function initLeaderFilter(countries) {
  const sel = document.getElementById("leader-country-filter");
  countries.forEach(c=>{ const o=document.createElement("option"); o.value=c.iso3; o.textContent=`${FLAGS[c.iso3]??""} ${c.country}`; sel.appendChild(o); });
  sel.addEventListener("change",async()=>{
    const leaders = await api(`/api/leaders?country=${sel.value}&n=25${dtypeQ()}`);
    _cache.leaders = leaders;
    document.getElementById("leader-count-badge").textContent = leaders.length;
    renderLeaderRankList(leaders);
  });
}

// ── Bootstrap ─────────────────────────────────────────────────────────
async function main() {
  // Restaurar preferências salvas
  const savedTheme = localStorage.getItem("popin_theme");
  if (savedTheme && savedTheme !== THEME) {
    THEME = savedTheme;
    document.documentElement.dataset.theme = savedTheme;
  }
  const savedLang = localStorage.getItem("popin_lang");
  if (savedLang) {
    LANG = savedLang;
    document.querySelectorAll(".lang-opt").forEach(el => {
      el.classList.toggle("active", el.dataset.lang === LANG);
    });
  }

  updateThemeVars();
  updateColorStops();
  applyI18n();
  initNav();
  initDistFilters();
  initTSFilters();
  initDimBarSelect();
  initScatterSelects();

  document.getElementById("drawer-close").addEventListener("click", closeLeaderDrawer);
  document.getElementById("drawer-overlay").addEventListener("click", closeLeaderDrawer);

  // Init dtype filter first
  await initDtypeFilter();

  const [stats, countries, leaders, yearlyGlobal] = await Promise.all([
    api("/api/stats"), api("/api/countries"),
    api("/api/leaders?n=25"), api("/api/yearly_global"),
  ]);
  _cache.stats=stats; _cache.countries=countries; _cache.leaders=leaders;

  document.getElementById("loader").classList.add("hidden");

  // Overview
  renderKPIs(stats);
  renderHeroBanner(countries);
  renderCountryCards(countries);
  renderMap(countries);
  renderTrendToggle(yearlyGlobal);

  // Countries
  initCountryRadarSelect(countries);
  renderCountryRanked(countries);
  renderDimBars(countries);

  // Leaders
  await initLeaderFilter(countries);
  document.getElementById("leader-count-badge").textContent = leaders.length;
  renderLeaderRankList(leaders);

  // Time Series
  initTSCountryChips(countries);
  renderTSLine();
  renderMovers(countries);

  // Dimensions
  renderHistogram();
  renderScatter2D(countries);
}

main().catch(err => {
  console.error(err);
  document.getElementById("loader").innerHTML = `
    <div class="loader-inner">
      <p style="color:#F87171;font-weight:600">Erro ao carregar dados.</p>
      <p style="font-size:11px;margin-top:4px;opacity:.6">O servidor está rodando em :8000?</p>
      <p style="font-size:11px;margin-top:2px;opacity:.4">${err.message}</p>
    </div>`;
});
