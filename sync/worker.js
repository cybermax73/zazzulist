/**
 * ZazzuList — service de synchronisation (Cloudflare Worker + base D1, palier gratuit).
 *
 * Chaque utilisateur a un code secret (ZL-XXXX-XXXX) généré par la page ; ses données
 * (liste à voir, votes, vus, plateformes) sont stockées sous ce code. Pas de compte.
 *
 *   GET  /v1/sync/:code  -> { data, updated_at }   (404 si inconnu)
 *   PUT  /v1/sync/:code  <- JSON (<= 512 Ko)        (POST accepté aussi, pour sendBeacon)
 *   GET  /v1/health
 */

const ALLOWED_ORIGINS = ["https://cybermax73.github.io", "http://127.0.0.1:8080", "http://localhost:8080"];
const CODE_RE = /^ZL-[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}$/; // pas de 0/O/1/I pour éviter les confusions
const MAX_BYTES = 512 * 1024;

function cors(origin) {
  const ok = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": ok,
    "Access-Control-Allow-Methods": "GET, PUT, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  };
}

const json = (obj, status, headers) => new Response(JSON.stringify(obj), {
  status, headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...headers },
});

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const headers = cors(request.headers.get("Origin") || "");
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers });

    if (url.pathname === "/v1/health") return json({ ok: true }, 200, headers);

    const m = url.pathname.match(/^\/v1\/sync\/([^/]+)$/);
    if (!m) return json({ error: "not found" }, 404, headers);
    const code = decodeURIComponent(m[1]).toUpperCase();
    if (!CODE_RE.test(code)) return json({ error: "code invalide" }, 400, headers);

    if (request.method === "GET") {
      const row = await env.DB.prepare("SELECT data, updated_at FROM sync WHERE code = ?").bind(code).first();
      if (!row) return json({ error: "inconnu" }, 404, headers);
      return new Response(`{"data":${row.data},"updated_at":"${row.updated_at}"}`, {
        status: 200, headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...headers },
      });
    }

    if (request.method === "PUT" || request.method === "POST") {
      const body = await request.text();
      if (body.length > MAX_BYTES) return json({ error: "trop volumineux" }, 413, headers);
      let data;
      try { data = JSON.parse(body); } catch { return json({ error: "JSON invalide" }, 400, headers); }
      if (!data || typeof data !== "object" || Array.isArray(data)) return json({ error: "objet attendu" }, 400, headers);
      const now = new Date().toISOString();
      await env.DB.prepare(
        "INSERT INTO sync (code, data, updated_at, created_at) VALUES (?1, ?2, ?3, ?3) " +
        "ON CONFLICT(code) DO UPDATE SET data = ?2, updated_at = ?3"
      ).bind(code, JSON.stringify(data), now).run();
      return json({ ok: true, updated_at: now }, 200, headers);
    }

    return json({ error: "méthode non autorisée" }, 405, headers);
  },
};
