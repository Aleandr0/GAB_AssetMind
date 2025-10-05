from pathlib import Path

import pandas as pd
import pytest

from config import DatabaseConfig, get_application_directory
from models import PortfolioManager, MANUAL_UPDATE_NOTE, MANUAL_UPDATE_MESSAGE
from market_data import MarketDataError, MarketDataService
from date_utils import get_today_formatted


class FakeMarketProvider:
    """Provider di mercato fittizio per i test."""

    def __init__(self):
        self.calls = []

    def get_latest_price(self, ticker=None, isin=None, asset_name=None):
        self.calls.append({
            "ticker": ticker,
            "isin": isin,
            "asset_name": asset_name,
        })

        if ticker == "AAPL":
            return {"symbol": "AAPL", "price": 190.5, "currency": "USD"}

        if isin == "US5949181045":
            return {"symbol": "MSFT", "price": 330.0, "currency": "USD"}

        raise MarketDataError("Simbolo non supportato nel provider fittizio")


def _build_test_dataframe():
    """Costruisce un DataFrame coerente con lo schema del portfolio."""

    records = [
        {
            "id": 1,
            "category": "Azioni",
            "asset_name": "Apple Inc",
            "position": "Tech",
            "risk_level": 3,
            "ticker": "AAPL",
            "isin": "US0378331005",
            "created_at": "2023-01-01",
            "created_amount": 10,
            "created_unit_price": 120.0,
            "created_total_value": 1200.0,
            "updated_at": "2024-01-01",
            "updated_amount": 10,
            "updated_unit_price": 150.0,
            "updated_total_value": 1500.0,
            "accumulation_plan": "",
            "accumulation_amount": 0.0,
            "income_per_year": 0.0,
            "rental_income": 0.0,
            "note": "",
        },
        {
            "id": 2,
            "category": "Azioni",
            "asset_name": "Microsoft Corp",
            "position": "Tech",
            "risk_level": 2,
            "ticker": "",
            "isin": "US5949181045",
            "created_at": "2023-01-01",
            "created_amount": 5,
            "created_unit_price": 220.0,
            "created_total_value": 1100.0,
            "updated_at": "2024-01-01",
            "updated_amount": 0,
            "updated_unit_price": 0.0,
            "updated_total_value": 0.0,
            "accumulation_plan": "",
            "accumulation_amount": 0.0,
            "income_per_year": 0.0,
            "rental_income": 0.0,
            "note": "",
        },
        {
            "id": 3,
            "category": "Liquidità",
            "asset_name": "Conto corrente",
            "position": "Cash",
            "risk_level": 1,
            "ticker": "",
            "isin": "",
            "created_at": "2023-01-01",
            "created_amount": 1000.0,
            "created_unit_price": 1.0,
            "created_total_value": 1000.0,
            "updated_at": "2024-01-01",
            "updated_amount": 1000.0,
            "updated_unit_price": 1.0,
            "updated_total_value": 1000.0,
            "accumulation_plan": "",
            "accumulation_amount": 0.0,
            "income_per_year": 0.0,
            "rental_income": 0.0,
            "note": "",
        },
    ]

    return pd.DataFrame(records, columns=DatabaseConfig.DB_COLUMNS)


def test_update_market_prices_creates_historical_records():
    app_dir = Path(get_application_directory())
    test_dir = app_dir / "tests_tmp"
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "market_update.xlsx"

    if test_file.exists():
        test_file.unlink()

    try:
        manager = PortfolioManager(str(test_file))
        df = _build_test_dataframe()
        manager.save_data(df)

        provider = FakeMarketProvider()
        result = manager.update_market_prices(provider)

        # Verifica risultati riepilogo
        assert result["updated"] == 2
        assert not result["skipped"]
        alerts = result.get("alerts", [])
        assert len(alerts) == 2
        assert all(alert.get("change_pct") is not None for alert in alerts)

        reloaded = manager.load_data()
        today = get_today_formatted('storage')

        # Devono esserci due righe in più (storico duplicato)
        assert len(reloaded) == len(df) + 2

        new_ids = {detail["new_record_id"] for detail in result["details"]}
        assert len(new_ids) == 2

        for detail in result["details"]:
            row = reloaded[reloaded["id"] == detail["new_record_id"]].iloc[0]
            assert float(row["updated_unit_price"]) == detail["price"]
            assert row["updated_at"] == today
            assert round(float(row["updated_total_value"]), 2) == round(
                float(row["updated_amount"]) * detail["price"], 2
            )

        # Asset senza ticker deve ricevere il simbolo risolto
        msft_row = reloaded[reloaded["ticker"] == "MSFT"].iloc[-1]
        assert msft_row["updated_amount"] == 5

    finally:
        if test_file.exists():
            test_file.unlink()
        try:
            test_dir.rmdir()
        except OSError:
            # Directory non vuota (altri test), ignorare
            pass



def test_update_market_prices_handles_nav_unavailable():
    """Gli asset NAV non disponibili devono richiedere intervento manuale duplicando il record."""

    app_dir = Path(get_application_directory())
    test_dir = app_dir / "tests_tmp"
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "nav_issue.xlsx"

    if test_file.exists():
        test_file.unlink()

    try:
        manager = PortfolioManager(str(test_file))

        base_record = {column: None for column in DatabaseConfig.DB_COLUMNS}
        base_record.update({
            "id": 10,
            "category": "Fondi di investimento",
            "asset_name": "BGF World Technology E2 EUR",
            "position": "Equity",
            "risk_level": 4,
            "ticker": "",
            "isin": "LU0171310955",
            "created_at": "2024-01-01",
            "created_amount": 100.0,
            "created_unit_price": 25.0,
            "created_total_value": 2500.0,
            "updated_at": "2024-08-01",
            "updated_amount": 100.0,
            "updated_unit_price": 30.0,
            "updated_total_value": 3000.0,
            "accumulation_plan": "",
            "accumulation_amount": 0.0,
            "income_per_year": 0.0,
            "rental_income": 0.0,
            "note": "",
        })
        df = pd.DataFrame([base_record], columns=DatabaseConfig.DB_COLUMNS)
        manager.save_data(df)

        class NavFailProvider:
            def get_latest_price(self, ticker=None, isin=None, asset_name=None):
                raise MarketDataError("NAV BlackRock HTTP 503")

        result = manager.update_market_prices(NavFailProvider())

        assert result["updated"] == 1
        assert not result["errors"]
        assert not result.get("skipped")

        manual_alerts = [alert for alert in result.get("alerts", []) if alert.get("type") == "manual_update_required"]
        assert len(manual_alerts) == 1
        manual_alert = manual_alerts[0]
        assert manual_alert["id"] == 10
        assert manual_alert.get("reason") == "issuer_nav_unavailable"

        manual_details = [detail for detail in result.get("details", []) if detail.get("id") == 10]
        assert manual_details and manual_details[0].get("manual") is True

        manual_updates = [entry for entry in result.get("manual_updates", []) if entry.get("id") == 10]
        assert manual_updates

        reloaded = manager.load_data()
        assert len(reloaded) == 2
        new_row = reloaded.iloc[-1]
        assert int(new_row["id"]) != 10
        assert float(new_row["updated_unit_price"]) == 30.0
        assert MANUAL_UPDATE_NOTE in str(new_row.get("note") or "")
        assert MANUAL_UPDATE_MESSAGE in str(new_row.get("note") or "")
        today = get_today_formatted('storage')
        assert new_row["updated_at"] == today
    finally:
        if test_file.exists():
            test_file.unlink()

def test_quote_from_issuer_nav_failure(monkeypatch):
    """Il resolver NAV deve propagare l'errore con provider indicato."""

    service = MarketDataService(api_key="dummy")
    symbol_info = {
        "symbol": "LU0171310955",
        "issuer_config": {"isin": "LU0171310955"},
    }

    def _fake_nav_fetch(isin, issuer_config):
        raise MarketDataError("NAV BlackRock HTTP 503")

    monkeypatch.setattr(service, "_fetch_blackrock_nav", _fake_nav_fetch)

    result = service._quote_from_issuer_nav(symbol_info)

    assert not result.success
    assert result.provider_used == "issuer_nav"
    assert result.error
    assert "NAV" in result.error


