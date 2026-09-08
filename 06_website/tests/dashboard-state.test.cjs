/* Focused state regressions; no server, browser, dependencies or production exports. */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../static/js/app.js'), 'utf8');

function harness() {
  const elements = new Map(), pending = [], chartCalls = [], frames = [];
  let document;
  class Element {
    constructor(id = '') {
      this.id = id; this.dataset = {}; this.attrs = {}; this.handlers = {};
      this.children = []; this.style = {}; this.value = ''; this.inert = false;
      this.isConnected = true; this.shown = true; this._html = ''; this.textContent = '';
      const classes = new Set();
      this.classList = {add: c => classes.add(c), remove: c => classes.delete(c), contains: c => classes.has(c),
        toggle: (c, active) => { active = active ?? !classes.has(c); active ? classes.add(c) : classes.delete(c); return active; }};
    }
    setAttribute(k, v) { this.attrs[k] = v; }
    removeAttribute(k) { delete this.attrs[k]; }
    addEventListener(k, f) { if (f) (this.handlers[k] ??= []).push(f); }
    click() { this.handlers.click?.forEach(f => f({target: this})); }
    focus() { document.activeElement = this; }
    contains(el) { return el === this || this.children.some(c => c.contains(el)); }
    closest() { return this.inert ? this : null; }
    getClientRects() { return this.shown ? [{}] : []; }
    appendChild(el) { this.children.push(el); return el; }
    insertAdjacentElement(_, el) { elements.set(el.id, el); }
    replaceChildren() { this.children = []; this._html = ''; }
    remove() { this.isConnected = false; }
    set innerHTML(value) {
      this._html = value; this.children = [];
      for (const match of value.matchAll(/<(button|option)\b([^>]*)>([\s\S]*?)<\/\1>/g)) {
        const el = new Element(); el.textContent = match[3];
        for (const attr of match[2].matchAll(/([\w-]+)="([^"]*)"/g)) {
          if (attr[1].startsWith('data-')) el.dataset[attr[1].slice(5)] = attr[2];
          if (attr[1] === 'class') attr[2].split(' ').forEach(c => el.classList.add(c));
          if (attr[1] === 'value') el.value = attr[2];
          el.attrs[attr[1]] = attr[2];
        }
        this.children.push(el);
      }
    }
    get innerHTML() { return this._html; }
    querySelectorAll(selector) {
      if (selector.includes('button:not(')) return this.children;
      const data = selector.match(/^\[data-([\w-]+)\]$/);
      if (data) return this.children.filter(el => Object.hasOwn(el.dataset, data[1]));
      if (selector.startsWith('.')) return this.children.filter(el => el.classList.contains(selector.slice(1)));
      return [];
    }
    querySelector(selector) { return this.querySelectorAll(selector)[0] ?? null; }
  }
  const get = id => { if (!elements.has(id)) elements.set(id, new Element(id)); return elements.get(id); };
  document = {
    readyState: 'loading', documentElement: {dataset: {}}, activeElement: null,
    body: new Element('body'), addEventListener() {},
    getElementById: id => elements.get(id) ?? null,
    createElement: () => new Element(),
    querySelector: selector => selector.includes('aria-current') ? get('nav-active') : null,
    querySelectorAll(selector) {
      if (selector.startsWith('body > main')) return [get('main'), get('site-sidebar'), get('sidebar-toggle')];
      if (selector === '[data-i18n]') return [...elements.values()].filter(el => el.dataset.i18n);
      return [];
    },
  };
  const context = vm.createContext({document, window: {innerWidth: 1200, addEventListener() {}},
    localStorage: {getItem() { return null; }, setItem() {}},
    console: {warn() {}, error() {}}, AbortController, URLSearchParams, Intl, Date, Blob, URL,
    setTimeout, clearTimeout, requestAnimationFrame: f => { frames.push(f); return frames.length; },
    fetch: (url, options) => new Promise(resolve => pending.push({url, options, resolve})),
    Plotly: {react: async (el, traces, layout) => { el.data = traces; chartCalls.push({id: el.id, traces, layout}); }, purge: el => { delete el.data; }, Plots: {resize() {}}},
  });
  vm.runInContext(source, context);
  return {run: code => vm.runInContext(code, context), context, get, elements, pending, chartCalls, document, frames};
}
const json = value => JSON.parse(JSON.stringify(value));
const response = (call, data) => call.resolve({ok: true, json: async () => data});
const settle = () => new Promise(resolve => setImmediate(resolve));

test('late same-resource response cannot overwrite a newer response, even if transport ignores abort', async () => {
  const h = harness();
  h.run('globalThis.accepted = []');
  const old = h.run('request("leaders", "/old", data => accepted.push(data))');
  const latest = h.run('request("leaders", "/new", data => accepted.push(data))');
  assert.equal(h.pending[0].options.signal.aborted, true);
  response(h.pending[1], 'latest'); await latest;
  response(h.pending[0], 'obsolete'); await old;
  assert.deepEqual(json(h.run('accepted')), ['latest']);
});

test('rapid global scope refresh preserves country/minimum and rejects all old scope data', async () => {
  const h = harness();
  h.get('leader-country-filter').value = 'BRA';
  h.get('leader-min-n-filter').value = '1';
  h.run('_allDtypes = [{dtype:"SPEECH",n:10}]; renderCountries = () => {}; renderKPIs = () => {}; renderLeaderRankList = () => {}; renderGlobalTrend = () => {}; renderTSLine = () => {}; renderMovers = () => {}; renderHistogram = () => {}; buildCountryControls = () => {}');
  const first = h.run('refreshAll()');
  const second = h.run('GLOBAL_DTYPE = "SPEECH"; refreshAll()');
  assert.equal(h.pending.length, 14);
  const lead = h.pending[9];
  assert.match(lead.url, /country=BRA/); assert.match(lead.url, /min_n=1/); assert.match(lead.url, /n=200/); assert.match(lead.url, /dtype=SPEECH/);
  const payload = (call, tag) => call.url.includes('/stats?') ? {avg_score:tag} : call.url.includes('/countries?') ? [] : [{tag}];
  h.pending.slice(7).forEach(call => response(call, payload(call, 'new'))); await second;
  h.pending.slice(0, 7).forEach(call => response(call, payload(call, 'old'))); await first;
  assert.equal(h.run('_cache.stats.avg_score'), 'new');
  assert.equal(h.run('_cache.leaders[0].tag'), 'new');
  assert.equal(h.get('leader-country-filter').value, 'BRA');
});

test('trend and radar chip handlers render current cache after dtype changes', () => {
  const h = harness(); h.get('trend-dim-toggle'); h.get('country-radar-select');
  h.run('globalThis.rendered = []; renderGlobalTrend = data => rendered.push(data); renderCountryRadar = data => rendered.push(data); _cache.yearlyGlobal = "initial"; _cache.countries = "initial"; countryCatalog.set("BRA", {iso3:"BRA",country:"Brazil"}); buildDimensionControls(); buildCountryControls(); _cache.yearlyGlobal = "fresh trend"; _cache.countries = "fresh countries"');
  h.get('trend-dim-toggle').children[1].click();
  h.get('country-radar-select').children[0].click();
  assert.deepEqual(json(h.run('rendered')), ['fresh trend', 'fresh countries']);
});

test('IQR endpoints are independent of means outside quartiles; score axes stay fixed', () => {
  const h = harness();
  h.run('globalThis.specs = []; plot = (id,traces,layout) => specs.push({id,traces,layout}); _cache.distribution = [{group:"Brazil",mean:90,q1:10,q3:20,n:12}]; renderHistogram(); renderCountryRanked([{iso3:"BRA",country:"Brazil",final_score:2,p25:10,p75:20,n:12}])');
  const specs = json(h.run('specs'));
  assert.deepEqual(specs[0].traces[0].x, [10, 20, null]);
  assert.deepEqual(specs[0].traces[1].x, [90]);
  assert.deepEqual(specs[1].traces[0].x, [10, 20, null]);
  assert.deepEqual(specs[1].traces[1].x, [2]);
  assert.deepEqual(specs[0].layout.xaxis.range, [0, 100]);
  assert.equal(JSON.stringify(specs).includes('error_y'), false);
  assert.match(specs[0].traces[0].name, /50% centrais/);
});

test('dimension mean tooltips do not present final-score quartiles as dimension dispersion', () => {
  const h = harness();
  const trace = json(h.run('scoreBarTrace([{iso3:"BRA",country:"Brazil",people_centrism:42,p25:3,p75:9,n:12}], "people_centrism")'));
  assert.match(trace.hovertext[0], /42,0/);
  assert.match(trace.hovertext[0], /n=12/);
  assert.doesNotMatch(trace.hovertext[0], /p25|p75|3,0–9,0/);
});

test('drawer discards closed/previous leader responses and restores focus and inert state', async () => {
  const h = harness();
  ['leader-drawer', 'drawer-close', 'drawer-overlay', 'drawer-name', 'drawer-meta', 'drawer-score-row', 'drawer-dims', 'chart-drawer-trend', 'chart-drawer-radar'].forEach(h.get);
  const trigger = h.get('leader-trigger');
  h.document.activeElement = trigger;
  h.get('leader-drawer').children = [h.get('drawer-close')];
  h.run('globalThis.specs = []; plot = (id,traces) => specs.push({id,traces}); openLeaderDrawer({leader_name:"Old",leader_short:"Old",iso3:"BRA",country:"Brazil",final_score:20,n:9})');
  assert.equal(h.get('leader-drawer').inert, false);
  assert.equal(h.get('main').inert, true);
  let prevented = false;
  h.context.tabEvent = {key: 'Tab', preventDefault() { prevented = true; }};
  h.run('drawerKeydown(tabEvent)');
  assert.equal(prevented, true);
  h.run('closeLeaderDrawer()');
  assert.equal(h.get('leader-drawer').inert, true);
  assert.equal(h.get('main').inert, false);
  assert.equal(h.document.activeElement, trigger);
  h.run('openLeaderDrawer({leader_name:"New",leader_short:"New",iso3:"BRA",country:"Brazil",final_score:50,n:10})');
  response(h.pending[1], [{year:2020, final_score:50}]); await settle();
  response(h.pending[0], [{year:2000, final_score:20}]); await settle();
  const trends = json(h.run('specs.filter(s => s.id === "chart-drawer-trend")'));
  assert.equal(trends.length, 1); assert.deepEqual(trends[0].traces[0].y, [50]);
  h.run('drawerKeydown({key:"Escape",preventDefault(){}})');
  assert.equal(h.get('leader-drawer').inert, true);
});

test('hidden chart defers rendering and flushes only the newest spec on visibility', async () => {
  const h = harness(), chart = h.get('chart-test'); chart.shown = false;
  h.run('plot("chart-test", [{y:[1]}]); plot("chart-test", [{y:[2]}])');
  assert.equal(h.chartCalls.length, 0);
  chart.shown = true;
  await h.run('flushPlot("chart-test")');
  assert.equal(h.chartCalls.length, 1); assert.deepEqual(json(h.chartCalls[0].traces[0].y), [2]);
});

test('mobile closing affects nav only and desktop reopening restores nav access', () => {
  const h = harness(), sidebar = h.get('site-sidebar'), nav = h.get('nav');
  nav.classList.add('nav'); sidebar.children.push(nav);
  h.run('window.innerWidth = 768; setMobileMenu(false)');
  assert.equal(nav.inert, true); assert.equal(sidebar.inert, false); assert.equal(sidebar.attrs['aria-hidden'], undefined);
  h.run('setMobileMenu(true)'); assert.equal(nav.inert, false);
  h.run('window.innerWidth = 1024; setMobileMenu(false)'); assert.equal(nav.inert, false);
});

test('explicit row-based plot height survives container-driven resizing', () => {
  const h = harness(); const chart = h.get('chart-test'); chart.shown = false;
  h.run('plot("chart-test", [{y:[1]}], {height:677})');
  assert.equal(chart.style.height, '677px');
});

test('time series use gentle curves without altering observations or quartile lines', () => {
  const h = harness();
  h.run(`globalThis.specs=[]; plot=(id,traces)=>specs.push({id,traces});
    renderGlobalTrend([{year:2020,final_score:10,n:5},{year:2021,final_score:20,n:5}]);
    _cache.yearly=[{iso3:'BRA',country:'Brazil',year:2020,score:10},{iso3:'BRA',country:'Brazil',year:2021,score:20}]; renderTSLine();
    drawerLeader={leader_name:'Example'}; drawerTrend=[{year:2020,final_score:10},{year:2021,final_score:20}]; renderDrawerTrend();`);
  for (const spec of json(h.run('specs'))) {
    assert.equal(spec.traces[0].line.shape,'spline',spec.id);
    assert.ok(spec.traces[0].line.smoothing <= 0.6);
    assert.deepEqual(spec.traces[0].y,[10,20]);
    assert.equal(spec.traces[0].connectgaps,false);
  }
  assert.equal(h.run('intervalTrace([{group:"test",q1:1,q3:2,n:5}]).line.shape'),'linear');
});

test('About is a menu destination and hides only irrelevant data filters', () => {
  const h = harness(); h.get('section-about'); h.get('section-overview'); h.get('global-filter-bar');
  h.run('navigateTo("about")'); assert.equal(h.get('global-filter-bar').hidden,true);
  h.run('navigateTo("overview")'); assert.equal(h.get('global-filter-bar').hidden,false);
  const html=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
  assert.match(html,/data-section="about"/);
  assert.match(html,/id="section-about"/);
  assert.doesNotMatch(html,/<footer[^>]*>[\s\S]*?<details/);
});

test('country labels, missing numbers and CSV retain identity without unsafe interpolation', () => {
  const h = harness();
  assert.equal(h.run('countryName({iso3:"BRA",country:"Brazil"})'), 'Brasil');
  assert.equal(h.run('countryName("Dom. Republic")'), 'República Dominicana');
  assert.equal(h.run('fmt(1234.5)'), '1.234,5');
  assert.equal(h.run('fmt(null)'), '—');
  assert.equal(h.run('escapeHTML("<img src=x>")'), '&lt;img src=x&gt;');
  const csv = h.run('countriesCSV([{iso3:"BRA",country:"Brazil",n:12,final_score:45.5,p25:20,p75:60}])');
  assert.match(csv, /"BRA","Brazil","Brasil","ALL","12","45.5"/);
  h.run('LANG = "en"'); assert.equal(h.run('countryName("Dom. Republic")'), 'Dominican Republic');
});

test('locale change redraws every loaded chart and preserves unknown parent translation keys', () => {
  const h = harness(), unknown = h.get('new-parent-copy');
  unknown.dataset.i18n = 'not_registered'; unknown.textContent = 'Parent text';
  h.run(`globalThis.redrawn = []; buildCountryControls = () => {}; buildDimensionControls = () => {}; buildDtypeChips = () => {};
    renderKPIs = () => {}; renderLeaderRankList = () => {};
    for (const name of ['renderCountries','renderGlobalTrend','renderTSLine','renderMovers','renderHistogram','renderDrawerProfile','renderDrawerTrend']) globalThis[name] = () => redrawn.push(name);
    Object.assign(_cache,{countries:[],yearlyGlobal:[],yearly:[],movers:[],distribution:[]}); setLanguage('en')`);
  assert.deepEqual(json(h.run('redrawn')), ['renderCountries','renderGlobalTrend','renderTSLine','renderMovers','renderHistogram','renderDrawerProfile','renderDrawerTrend']);
  assert.equal(unknown.textContent, 'Parent text');
  const html = fs.readFileSync(path.join(__dirname, '../static/index.html'), 'utf8');
  for (const [,key] of html.matchAll(/data-i18n="([^"]+)"/g)) {
    assert.equal(h.run(`typeof I18N.en[${JSON.stringify(key)}]`), 'string', `missing EN: ${key}`);
  }
});

test('HTTP failure exposes retry state and a successful retry clears it', async () => {
  const h = harness(); h.get('leader-rank-list'); h.get('refresh-status');
  const first = h.run('refreshLeaders()');
  h.pending[0].resolve({ok: false, status:503}); await first;
  assert.match(h.get('leader-rank-list').innerHTML, /retry-btn/);
  assert.equal(h.get('refresh-status').classList.contains('is-error'), true);
  const retry = h.run('refreshLeaders()'); response(h.pending[1], []); await retry;
  assert.equal(h.get('refresh-status').classList.contains('is-error'), false);
  assert.match(h.get('leader-rank-list').innerHTML, /Sem dados/);
});
