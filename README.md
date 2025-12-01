# Stock Analysis POC

This repository contains a proof-of-concept for a "ticker → automated analysis" pipeline that stitches together Zuplo (API edge), Fermyon Spin (orchestration), and a Python backend on Linode (heavy compute + LLM summarization).

## Components

- **docs/architecture.md** — End-to-end blueprint, API contracts, responsibilities, and deployment notes.
- **spin/** — Fermyon Spin orchestrator configuration and TypeScript handler to validate tickers, route to the backend, and surface cache/latency headers.
- **python_service/** — FastAPI skeleton that fetches SEC filings, computes metrics, runs a placeholder DCF, and generates a Buy/Hold/Sell recommendation.

## Quickstart (local backend)

1. Install Python dependencies:
   ```bash
   cd python_service
   pip install -r requirements.txt
   ```
2. Run the FastAPI service:
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```
3. Spin handler expects `BACKEND_URL` (defaults to http://localhost:8000) and exposes `/analyze/{ticker}`.

## Expected response shape
See `docs/architecture.md` for the canonical JSON response and field meanings.

## Deployment hints
- Deploy Spin to Fermyon Cloud with `BACKEND_URL` pointing to the Linode backend.
- Configure Zuplo to expose `GET /api/analyze/{ticker}` and forward to the Spin endpoint, adding auth/rate limits.
- Use environment variables for SEC User-Agent, market data API keys, and LLM endpoint in production.
