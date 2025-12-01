# Zuplo Gateway configuration (sketch)

Configure Zuplo to expose the public API and forward requests to Fermyon Spin.

## Suggested route

- **Method**: `GET`
- **Path**: `/api/analyze/:ticker`
- **Backend**: Spin endpoint (e.g., `https://<spin-host>/analyze/:ticker`)

## Policies
- API key or JWT validation
- Rate limiting (e.g., 60 req/min per key)
- Response caching: respect `cache-control` headers from Spin
- Observability: log request ID, ticker, status, duration

## Example proxy handler (TypeScript snippet)
```ts
export default async function (req, ctx) {
  const ticker = req.params.ticker?.toUpperCase();
  if (!ticker) return ctx.throw(400, "Missing ticker");
  const url = `${ctx.env.SPIN_URL}/analyze/${ticker}`;
  return await ctx.fetch(url, { headers: { authorization: req.headers.get("authorization") || "" } });
}
```
