"""FastAPI backend for ticker → analysis.

This is a skeleton showing how to glue together SEC ingestion, market data, metrics, valuation,
and LLM summarization. Heavy lifting (NLP, DCF) is simplified for the POC.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Ticker Analyzer", version="0.1")

# Configuration
SEC_USER_AGENT = os.environ.get("SEC_USER_AGENT", "ticker-analyzer/0.1 contact@example.com")
MARKET_DATA_API_KEY = os.environ.get("MARKET_DATA_API_KEY")
LLM_ENDPOINT = os.environ.get("LLM_ENDPOINT")
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "900"))


class AnalyzeRequest(BaseModel):
    ticker: str = Field(..., regex=r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")
    force_refresh: bool = False


class AnalysisResponse(BaseModel):
    ticker: str
    as_of: str
    summary: str
    financials: Dict[str, float]
    valuation: Dict[str, Any]
    risks: List[str]
    peer_comparison: Dict[str, Any]
    momentum: Dict[str, float]
    recommendation: str
    reasoning: str
    raw: Dict[str, Any]


@dataclass
class CacheEntry:
    expires_at: float
    payload: AnalysisResponse


@dataclass
class FilingSections:
    mda: str
    risk_factors: str
    financials: str


async def fetch_latest_filings(ticker: str) -> FilingSections:
    # Placeholder: call SEC EDGAR for 10-K and 10-Q. Respect rate limits and user agent.
    headers = {"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "gzip"}
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        # TODO: replace with real endpoints and parsing logic.
        await client.get("https://www.sec.gov")  # dummy call to illustrate pattern
    return FilingSections(mda="MD&A text", risk_factors="Risk factors text", financials="Financial statements text")


async def fetch_market_data(ticker: str) -> Dict[str, float]:
    # Placeholder: integrate Yahoo Finance / Finnhub / Alpha Vantage.
    return {
        "price": 181.3,
        "beta": 1.12,
        "rsi": 63.2,
        "sma_50": 175.1,
        "sma_200": 169.4,
    }


def compute_metrics(filings: FilingSections) -> Dict[str, float]:
    # Placeholder deterministic metrics; replace with parsed values.
    return {
        "revenue_growth": -2.1,
        "gross_margin": 44.1,
        "ebit_margin": 29.8,
        "free_cash_flow": 90.1,
        "net_debt_to_ebitda": 0.3,
        "roic": 21.4,
    }


def compute_recommendation(implied_overvaluation_pct: float) -> str:
    if implied_overvaluation_pct > 25:
        return "SELL"
    if implied_overvaluation_pct > 10:
        return "HOLD"
    return "BUY"


def dcf_valuation(metrics: Dict[str, float], market_data: Dict[str, float]) -> Dict[str, Any]:
    # Simplified DCF placeholder with sensitivity ranges.
    intrinsic_value = 155.2
    market_price = market_data["price"]
    implied_overvaluation = round((market_price - intrinsic_value) / intrinsic_value * 100, 1)
    return {
        "intrinsic_value": intrinsic_value,
        "market_price": market_price,
        "implied_overvaluation_pct": implied_overvaluation,
        "valuation_method": "DCF",
        "sensitivity": {"wacc": [8.0, 9.0, 10.0], "terminal_growth": [2.0, 2.5, 3.0]},
    }


async def summarize_with_llm(payload: Dict[str, Any]) -> str:
    # Placeholder LLM call; integrate OpenAI/Azure/etc via LLM_ENDPOINT.
    return (
        "Stable cash generation but trading above intrinsic value; hold rating until pricing aligns with fair value."
    )


def _get_cached(ticker: str) -> Optional[AnalysisResponse]:
    cache_entry = _CACHE.get(ticker)
    if not cache_entry:
        return None
    if cache_entry.expires_at < time.time():
        _CACHE.pop(ticker, None)
        return None
    return cache_entry.payload


def _set_cache(ticker: str, payload: AnalysisResponse) -> None:
    _CACHE[ticker] = CacheEntry(expires_at=time.time() + CACHE_TTL_SECONDS, payload=payload)


_CACHE: Dict[str, CacheEntry] = {}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(req: AnalyzeRequest) -> AnalysisResponse:
    started = time.time()

    cached = None if req.force_refresh else _get_cached(req.ticker)
    if cached:
        return cached

    filings = await fetch_latest_filings(req.ticker)
    market_data = await fetch_market_data(req.ticker)
    metrics = compute_metrics(filings)
    valuation = dcf_valuation(metrics, market_data)

    summary_text = await summarize_with_llm({
        "ticker": req.ticker,
        "metrics": metrics,
        "valuation": valuation,
        "market_data": market_data,
        "filings": {
            "mda": filings.mda,
            "risk_factors": filings.risk_factors,
            "financials": filings.financials,
        },
    })

    recommendation = compute_recommendation(valuation["implied_overvaluation_pct"])

    response = AnalysisResponse(
        ticker=req.ticker,
        as_of=time.strftime("%Y-%m-%d"),
        summary=summary_text,
        financials=metrics,
        valuation=valuation,
        risks=["Supply-chain uncertainty", "Regulatory pressure", "Services dependency growth"],
        peer_comparison={
            "peers": [
                {"ticker": "MSFT", "metric": "EV/EBITDA", "value": 22.5},
                {"ticker": "GOOGL", "metric": "EV/EBITDA", "value": 15.3},
            ]
        },
        momentum={
            "50d_sma": market_data["sma_50"],
            "200d_sma": market_data["sma_200"],
            "rsi": market_data["rsi"],
            "beta": market_data["beta"],
        },
        recommendation=recommendation,
        reasoning=summary_text,
        raw={
            "filing_insights": filings.mda[:200],
            "valuation_model": "deterministic dcf placeholder",
            "llm_prompt": "omitted",
            "latency_ms": round((time.time() - started) * 1000, 2),
        },
    )

    _set_cache(req.ticker, response)
    return response


@app.get("/healthz")
async def health() -> Dict[str, str]:
    return {"status": "ok"}
