#!/usr/bin/env python3
"""
Test suite per validare calcoli valori portfolio
Verifica coerenza tra get_portfolio_summary() e get_visible_value()
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Aggiungi parent directory al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import PortfolioManager
from config import get_application_directory


class TestValueCalculation:
    """Test per validare calcoli valori portfolio"""

    @pytest.fixture
    def portfolio_manager(self, tmp_path):
        """Crea un PortfolioManager con dati di test"""
        # Crea file Excel temporaneo
        test_data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'category': ['ETF', 'ETF', 'ETF', 'ETF', 'ETF'],
            'asset_name': ['Asset A', 'Asset B', 'Asset A', 'Asset C', 'Asset C'],
            'position': ['Tech', 'Finance', 'Tech', 'Health', 'Health'],
            'isin': ['US001', 'US002', 'US001', 'US003', 'US003'],
            'ticker': ['AAPL', 'BAC', 'AAPL', 'JNJ', 'JNJ'],
            'risk_level': [3, 2, 3, 2, 2],
            'created_at': ['2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01'],
            'created_amount': [10, 20, 10, 15, 15],
            'created_unit_price': [100.0, 50.0, 100.0, 80.0, 80.0],
            'created_total_value': [1000.0, 1000.0, 1000.0, 1200.0, 1200.0],
            'updated_at': ['2024-06-01', '2024-06-01', '2024-12-01', '2024-06-01', '2024-12-01'],
            'updated_amount': [10, 20, 10, 15, 15],
            'updated_unit_price': [120.0, 55.0, 150.0, 90.0, 100.0],
            'updated_total_value': [1200.0, 1100.0, 1500.0, 1350.0, 1500.0],
            'accumulation_plan': ['', '', '', '', ''],
            'accumulation_amount': [0, 0, 0, 0, 0],
            'income_per_year': [0, 0, 0, 0, 0],
            'rental_income': [0, 0, 0, 0, 0],
            'note': ['', '', '', '', '']
        })

        test_file = tmp_path / "test_portfolio.xlsx"
        test_data.to_excel(test_file, index=False)

        return PortfolioManager(str(test_file))

    def test_normalization_consistency(self, portfolio_manager):
        """Test che normalizzazione campi sia consistente"""
        summary = portfolio_manager.get_portfolio_summary()
        current_assets = portfolio_manager.get_current_assets_only()

        # Verifica che il numero di asset correnti sia corretto
        # Asset A (ISIN US001): record 1 e 3, più recente è 3 (2024-12-01)
        # Asset B (ISIN US002): record 2
        # Asset C (ISIN US003): record 4 e 5, più recente è 5 (2024-12-01)
        assert len(current_assets) == 3, f"Expected 3 current assets, got {len(current_assets)}"

        # Verifica valore totale
        # Asset A: 1500, Asset B: 1100, Asset C: 1500
        expected_total = 1500 + 1100 + 1500
        assert summary['total_value'] == expected_total, \
            f"Expected {expected_total}, got {summary['total_value']}"

    def test_deduplication_logic(self, portfolio_manager):
        """Test che deduplica selezioni il record più recente"""
        current_assets = portfolio_manager.get_current_assets_only()

        # Trova Asset A (dovrebbe essere record 3, non 1)
        asset_a = current_assets[
            (current_assets['asset_name'] == 'Asset A') &
            (current_assets['isin'] == 'US001')
        ]

        assert len(asset_a) == 1, "Asset A should have exactly 1 current record"
        assert int(asset_a.iloc[0]['id']) == 3, \
            f"Asset A should use record 3 (most recent), got {asset_a.iloc[0]['id']}"
        assert float(asset_a.iloc[0]['updated_total_value']) == 1500.0

    def test_na_normalization(self):
        """Test che 'NA', 'N/A', 'null' siano normalizzati a stringa vuota"""
        test_data = pd.DataFrame({
            'id': [1, 2, 3],
            'category': ['ETF', 'ETF', 'ETF'],
            'asset_name': ['Asset X', 'Asset X', 'Asset X'],
            'position': ['NA', 'N/A', ''],  # Diversi formati NA
            'isin': ['US999', 'US999', 'US999'],
            'ticker': ['XXX', 'XXX', 'XXX'],
            'risk_level': [3, 3, 3],
            'created_at': ['2024-01-01', '2024-01-01', '2024-01-01'],
            'created_amount': [10, 10, 10],
            'created_unit_price': [100.0, 100.0, 100.0],
            'created_total_value': [1000.0, 1000.0, 1000.0],
            'updated_at': ['2024-06-01', '2024-07-01', '2024-08-01'],
            'updated_amount': [10, 10, 10],
            'updated_unit_price': [110.0, 120.0, 130.0],
            'updated_total_value': [1100.0, 1200.0, 1300.0],
            'accumulation_plan': ['', '', ''],
            'accumulation_amount': [0, 0, 0],
            'income_per_year': [0, 0, 0],
            'rental_income': [0, 0, 0],
            'note': ['', '', '']
        })

        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            test_data.to_excel(tmp.name, index=False)
            pm = PortfolioManager(tmp.name)

            # Tutti e tre i record dovrebbero essere considerati lo stesso asset
            current = pm.get_current_assets_only()
            assert len(current) == 1, \
                f"NA/N/A/'' should be normalized to same asset, got {len(current)} assets"

            # Dovrebbe usare il record più recente (id=3)
            assert int(current.iloc[0]['id']) == 3
            assert float(current.iloc[0]['updated_total_value']) == 1300.0


class TestPriceUpdateValidation:
    """Test per validazione aggiornamenti prezzi"""

    def test_anomalous_price_detection(self):
        """Test rilevamento variazioni prezzo anomale"""
        old_price = 100.0

        # Test variazioni normali
        assert abs((110.0 - old_price) / old_price * 100) < 20  # +10% OK
        assert abs((95.0 - old_price) / old_price * 100) < 20   # -5% OK

        # Test variazioni anomale
        anomalous_increase = 200.0  # +100%
        assert abs((anomalous_increase - old_price) / old_price * 100) > 20

        anomalous_decrease = 40.0  # -60%
        assert abs((anomalous_decrease - old_price) / old_price * 100) > 20

    def test_split_detection_pattern(self):
        """Test pattern detection per split azionari"""
        # Split 1:4 - prezzo diventa 1/4
        old_price = 400.0
        new_price = 100.0
        ratio = old_price / new_price

        # Ratios comuni: 2:1, 3:1, 4:1, 10:1
        common_splits = [2, 3, 4, 5, 10]
        is_likely_split = any(abs(ratio - split) < 0.1 for split in common_splits)

        assert is_likely_split, f"Ratio {ratio} suggests 4:1 split"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
