# Python backend (Linode)

FastAPI service that performs the heavy lifting: SEC ingestion, market data, metrics, valuation, and LLM summarization.

## Running locally

```bash
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Tests

```bash
pytest
```

## Environment variables
- `SEC_USER_AGENT` — required by SEC EDGAR for rate-limit friendly calls.
- `MARKET_DATA_API_KEY` — API key for Yahoo/Finnhub/AlphaVantage (provider-specific).
- `LLM_ENDPOINT` — endpoint for summarization.
- `CACHE_TTL_SECONDS` — seconds to cache recent analysis responses (default `900`).

## API
- `POST /analyze` — body `{ "ticker": "AAPL", "force_refresh": false }`; returns analysis JSON described in `docs/architecture.md`.
- `GET /healthz` — liveness probe.

## Next steps
- Implement real EDGAR fetching/parsing (10-K/10-Q sections: MD&A, Risk Factors, Financial Statements).
- Replace placeholder DCF with full projection model and sensitivity table.
- Swap mock LLM with production provider and prompt templates.
