const RENDER_URL = "https://popin-4tvv.onrender.com";

export default {
  // Cron trigger — roda a cada 10 minutos
  async scheduled(event, env, ctx) {
    ctx.waitUntil(ping());
  },

  // HTTP trigger — permite testar manualmente acessando a URL do worker
  async fetch(request, env, ctx) {
    const result = await ping();
    return new Response(result, { headers: { "Content-Type": "text/plain" } });
  },
};

async function ping() {
  const start = Date.now();
  try {
    const res = await fetch(RENDER_URL, {
      method: "GET",
      headers: { "User-Agent": "POPIN-Keepalive/1.0" },
      signal: AbortSignal.timeout(15000),
    });
    const ms = Date.now() - start;
    const msg = `[OK] ${new Date().toISOString()} — status ${res.status} — ${ms}ms`;
    console.log(msg);
    return msg;
  } catch (err) {
    const msg = `[ERR] ${new Date().toISOString()} — ${err.message}`;
    console.error(msg);
    return msg;
  }
}
