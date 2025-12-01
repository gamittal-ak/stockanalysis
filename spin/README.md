# Fermyon Spin orchestrator

This component validates tickers, prefers cached responses, and forwards work to the Python backend.

## Development

1. Install Spin (`brew install fermyon/tap/spin` or see Fermyon docs).
2. Build the TypeScript component (requires the JS/Wasi template):
   ```bash
   spin build
   ```
3. Run locally with the backend running on port 8000:
   ```bash
   BACKEND_URL=http://localhost:8000 spin up --listen 0.0.0.0:3000
   ```
4. Call the endpoint:
   ```bash
   curl "http://localhost:3000/analyze/AAPL"
   ```

## Notes
- `BACKEND_URL` must point to the Python service.
- Basic ticker validation uses the regex `^[A-Z]{1,5}(\.[A-Z]{1,2})?$`.
- Cache hints use `cache-control` max-age of 6 hours; wire a real cache (Spin key-value or Redis) in production.
