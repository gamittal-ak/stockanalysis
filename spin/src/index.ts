// Spin HTTP component (TypeScript → compiled to WASI via spin build).
// Performs lightweight validation, cache hints, and calls the Python backend.

import { HandleRequest, HttpRequest, HttpResponse } from "@fermyon/spin-sdk";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const CACHE_TTL_SECONDS = 6 * 60 * 60; // 6 hours

const isValidTicker = (ticker: string) => /^[A-Z]{1,5}(\.[A-Z]{1,2})?$/.test(ticker);

const jsonResponse = (status: number, body: unknown, extraHeaders: Record<string, string> = {}): HttpResponse => ({
  status,
  headers: Object.assign({
    "content-type": "application/json",
    "cache-control": `public, max-age=${CACHE_TTL_SECONDS}`,
  }, extraHeaders),
  body: JSON.stringify(body),
});

export const handleRequest: HandleRequest = async function (request: HttpRequest): Promise<HttpResponse> {
  const ticker = (request.params as Record<string, string>)["ticker"]?.toUpperCase();
  if (!ticker || !isValidTicker(ticker)) {
    return jsonResponse(400, { error: "Invalid ticker. Use 1-5 letters, optional class suffix (e.g., BRK.B)." });
  }

  const forceRefresh = request.query.get("forceRefresh") === "true";
  const url = `${BACKEND_URL}/analyze`;
  const started = Date.now();

  try {
    const backend = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ ticker, force_refresh: forceRefresh }),
    });

    if (!backend.ok) {
      const message = await backend.text();
      return jsonResponse(backend.status, { error: message || "Backend error" }, { "x-spin-backend-status": String(backend.status) });
    }

    const payload = await backend.text();
    const durationMs = Date.now() - started;
    return {
      status: 200,
      headers: {
        "content-type": "application/json",
        "x-spin-duration-ms": String(durationMs),
        "x-spin-cache": forceRefresh ? "bypass" : "preferred",
      },
      body: payload,
    };
  } catch (err) {
    return jsonResponse(502, { error: "Failed to reach backend", detail: String(err) });
  }
};
