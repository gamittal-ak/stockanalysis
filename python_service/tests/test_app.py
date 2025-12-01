import pathlib
import sys

from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app as app_module  # noqa: E402


def test_recommendation_thresholds():
    assert app_module.compute_recommendation(5) == "BUY"
    assert app_module.compute_recommendation(15) == "HOLD"
    assert app_module.compute_recommendation(35) == "SELL"


def test_analyze_uses_cache(monkeypatch):
    app_module._CACHE.clear()

    calls = {"filings": 0}

    async def fake_fetch_filings(ticker: str):
        calls["filings"] += 1
        return app_module.FilingSections(
            mda="mda", risk_factors="risks", financials="financials"
        )

    async def fake_fetch_market_data(ticker: str):
        return {"price": 150.0, "beta": 1.0, "rsi": 50.0, "sma_50": 140.0, "sma_200": 130.0}

    async def fake_summarize(payload):
        return "summary"

    monkeypatch.setattr(app_module, "fetch_latest_filings", fake_fetch_filings)
    monkeypatch.setattr(app_module, "fetch_market_data", fake_fetch_market_data)
    monkeypatch.setattr(app_module, "summarize_with_llm", fake_summarize)

    client = TestClient(app_module.app)

    first = client.post("/analyze", json={"ticker": "AAPL"})
    assert first.status_code == 200
    second = client.post("/analyze", json={"ticker": "AAPL"})
    assert second.status_code == 200

    assert calls["filings"] == 1


def test_force_refresh_bypasses_cache(monkeypatch):
    app_module._CACHE.clear()

    calls = {"filings": 0}

    async def fake_fetch_filings(ticker: str):
        calls["filings"] += 1
        return app_module.FilingSections(
            mda="mda", risk_factors="risks", financials="financials"
        )

    async def fake_fetch_market_data(ticker: str):
        return {"price": 150.0, "beta": 1.0, "rsi": 50.0, "sma_50": 140.0, "sma_200": 130.0}

    async def fake_summarize(payload):
        return "summary"

    monkeypatch.setattr(app_module, "fetch_latest_filings", fake_fetch_filings)
    monkeypatch.setattr(app_module, "fetch_market_data", fake_fetch_market_data)
    monkeypatch.setattr(app_module, "summarize_with_llm", fake_summarize)

    client = TestClient(app_module.app)

    first = client.post("/analyze", json={"ticker": "MSFT", "force_refresh": True})
    assert first.status_code == 200
    second = client.post("/analyze", json={"ticker": "MSFT", "force_refresh": True})
    assert second.status_code == 200

    assert calls["filings"] == 2
