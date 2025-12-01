# Ticker → Full Automated Analysis (POC)

This document captures the end-to-end blueprint for the proof of concept described in the prompt. The goal is to accept a ticker symbol and return a structured analysis that includes SEC filing insights, fundamental metrics, valuation, and a recommendation.

## High-level flow

1. **Zuplo API** receives `GET /api/analyze/{ticker}` requests, validates the token, rate limits, and forwards the ticker to Fermyon Spin.
2. **Fermyon Spin** performs quick validation and cache lookup, then calls the Python backend over HTTP/JSON. It returns the assembled JSON payload to Zuplo.
3. **Python backend (Linode)** fetches and parses SEC filings, collects market data, builds financial metrics, runs valuation models, summarizes insights with an LLM, and responds with a final recommendation plus raw analysis artifacts.

## Data contracts

### Public API response (via Zuplo / Spin)
```json
{
  "ticker": "AAPL",
  "as_of": "2024-12-31",
  "summary": "Apple’s revenue declined 2% YoY due to hardware softness; services remained resilient.",
  "financials": {
    "revenue_growth": -2.1,
    "gross_margin": 44.1,
    "ebit_margin": 29.8,
    "free_cash_flow": 90.1,
    "net_debt_to_ebitda": 0.3,
    "roic": 21.4
  },
  "valuation": {
    "intrinsic_value": 155.2,
    "market_price": 181.3,
    "implied_overvaluation_pct": 17.0,
    "valuation_method": "DCF",
    "sensitivity": {
      "wacc": [8.0, 9.0, 10.0],
      "terminal_growth": [2.0, 2.5, 3.0]
    }
  },
  "risks": ["Supply-chain uncertainty", "Regulatory pressure", "Services dependency growth"],
  "peer_comparison": {
    "peers": [
      {"ticker": "MSFT", "metric": "EV/EBITDA", "value": 22.5},
      {"ticker": "GOOGL", "metric": "EV/EBITDA", "value": 15.3}
    ]
  },
  "momentum": {
    "50d_sma": 175.1,
    "200d_sma": 169.4,
    "rsi": 63.2,
    "beta": 1.12
  },
  "recommendation": "HOLD",
  "reasoning": "Stable cash generation but trading above intrinsic value; wait for a pullback.",
  "raw": {
    "filing_insights": "...",
    "valuation_model": "...",
    "llm_prompt": "..."
  }
}
```

### Internal Python service request
```json
{
  "ticker": "AAPL",
  "force_refresh": false
}
```

### Internal Python service response
Matches the public API response; Spin simply forwards it.

## Component responsibilities

### Zuplo
- Handles API keys and rate limiting.
- Transforms error codes to client-friendly messages.
- Adds request logging/metrics.
- Forwards to Spin endpoint `/analyze/{ticker}`.

### Fermyon Spin orchestrator
- Validates ticker pattern (1–5 uppercase letters, optional dot suffix for classes).
- Checks a lightweight cache (e.g., Spin key-value or Redis on Linode) with TTL ~6–12 hours.
- Calls Python backend (`POST /analyze`) when cache miss or `force_refresh=true`.
- Normalizes backend errors into HTTP responses.
- Adds response headers for cache status and processing duration.

### Python backend
- **Data ingestion**
  - SEC EDGAR: latest 10-K and 10-Q; parse MD&A, Risk Factors, and Financial Statements sections.
  - Market data: price, volume, beta, peer multiples (Yahoo Finance, Finnhub, or Alpha Vantage).
- **Parsing & metrics**
  - NLP extraction for repeated risk themes (frequency, recency weighting).
  - Financial metrics: growth rates, margins, ROIC, leverage, FCF, liquidity ratios.
- **Valuation**
  - Deterministic DCF with scenario/sensitivity tables (vary WACC, terminal growth, margin drift).
  - Optional comparables sanity check (EV/EBITDA, P/E vs peers).
- **Summarization**
  - LLM to produce: filing summary, financial health, risks, valuation takeaway, and Buy/Hold/Sell.
- **Observability**
  - Structured logs, trace IDs passed from Spin, Prometheus metrics (latency, cache hit rate, model timing).

## Deployment notes
- **Zuplo**: configure `GET /api/analyze/{ticker}` to proxy to Spin URL; enforce auth and rate limits.
- **Spin**: build as `spin up` for local dev; deploy to Fermyon Cloud with env vars for backend URL and cache config.
- **Python backend**: deploy to Linode (VM or Kubernetes). Provide env vars for EDGAR rate limit throttle, market data API keys, and LLM provider.

## Security & compliance
- Respect SEC EDGAR rate limits (User-Agent with contact email, 10 requests/sec overall cap).
- Input validation for tickers and optional `force_refresh`.
- Strip PII from logs; avoid storing raw filings beyond processing cache unless required.

## Extension ideas
- Earnings call transcript ingestion, Monte Carlo valuation, portfolio-level alerts, and webhook notifications when intrinsic value crosses market price.
