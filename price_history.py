#!/usr/bin/env python3
"""
Sistema di tracking storico prezzi per analisi trend e performance
Estrae dati storici da Excel e genera metriche performance
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from logging_config import get_logger


@dataclass
class PricePoint:
    """Punto prezzo storico"""
    date: datetime
    price: float
    amount: float
    total_value: float


@dataclass
class PerformanceMetrics:
    """Metriche performance asset"""
    current_value: float
    initial_value: float
    absolute_return: float
    percentage_return: float
    annualized_return: Optional[float]
    volatility: Optional[float]
    max_drawdown: Optional[float]
    best_day_return: Optional[float]
    worst_day_return: Optional[float]
    total_days: int
    price_history: List[PricePoint]


class PriceHistoryTracker:
    """
    Tracker storico prezzi con calcolo metriche performance

    Features:
    - Estrazione storico da Excel
    - Calcolo rendimenti assoluti e percentuali
    - Volatilità e drawdown
    - Annualized return
    - Grafici trend (data export per matplotlib)
    """

    def __init__(self, portfolio_manager):
        """
        Args:
            portfolio_manager: Istanza PortfolioManager
        """
        self.portfolio_manager = portfolio_manager
        self.logger = get_logger(self.__class__.__name__)

    def get_asset_history(
        self,
        asset_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[PricePoint]:
        """
        Recupera storico prezzi per un asset

        Args:
            asset_id: ID asset
            start_date: Data inizio (opzionale)
            end_date: Data fine (opzionale, default oggi)

        Returns:
            Lista PricePoint ordinati per data
        """
        try:
            df = self.portfolio_manager.load_data()

            # Filtra per asset_id
            asset_records = df[df['id'] == asset_id].copy()

            if asset_records.empty:
                self.logger.warning(f"Nessun record trovato per asset ID {asset_id}")
                return []

            history = []

            for _, row in asset_records.iterrows():
                # Prendi data più recente tra updated_at e created_at
                date_str = row.get('updated_at') or row.get('created_at')
                if not date_str or pd.isna(date_str):
                    continue

                try:
                    date = pd.to_datetime(date_str)
                except:
                    continue

                # Filtra per date range
                if start_date and date < start_date:
                    continue
                if end_date and date > end_date:
                    continue

                # Estrai prezzo e amount
                price = row.get('updated_unit_price', 0) or row.get('created_unit_price', 0)
                amount = row.get('updated_amount', 0) or row.get('created_amount', 0)
                total_value = row.get('updated_total_value', 0) or row.get('created_total_value', 0)

                if price and not pd.isna(price):
                    history.append(PricePoint(
                        date=date,
                        price=float(price),
                        amount=float(amount) if amount else 0,
                        total_value=float(total_value) if total_value else float(price) * float(amount or 0)
                    ))

            # Ordina per data
            history.sort(key=lambda p: p.date)

            return history

        except Exception as exc:
            self.logger.error(f"Errore recupero storico asset {asset_id}: {exc}")
            return []

    def calculate_performance(
        self,
        asset_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[PerformanceMetrics]:
        """
        Calcola metriche performance per un asset

        Args:
            asset_id: ID asset
            start_date: Data inizio analisi
            end_date: Data fine analisi

        Returns:
            PerformanceMetrics o None se dati insufficienti
        """
        history = self.get_asset_history(asset_id, start_date, end_date)

        if len(history) < 2:
            self.logger.warning(f"Dati insufficienti per calcolare performance asset {asset_id}")
            return None

        # Valori iniziale e finale
        initial_value = history[0].total_value
        current_value = history[-1].total_value

        # Rendimento assoluto e percentuale
        absolute_return = current_value - initial_value
        percentage_return = (absolute_return / initial_value * 100) if initial_value > 0 else 0

        # Calcola annualized return
        first_date = history[0].date
        last_date = history[-1].date
        total_days = (last_date - first_date).days

        annualized_return = None
        if total_days > 0 and initial_value > 0:
            years = total_days / 365.25
            annualized_return = (pow(current_value / initial_value, 1/years) - 1) * 100

        # Calcola volatilità (standard deviation dei rendimenti giornalieri)
        volatility = None
        if len(history) >= 3:
            daily_returns = []
            for i in range(1, len(history)):
                prev_price = history[i-1].price
                curr_price = history[i].price
                if prev_price > 0:
                    daily_return = (curr_price - prev_price) / prev_price
                    daily_returns.append(daily_return)

            if daily_returns:
                volatility = np.std(daily_returns) * np.sqrt(252) * 100  # Annualized volatility

        # Calcola max drawdown
        max_drawdown = None
        if len(history) >= 2:
            peak = history[0].total_value
            max_dd = 0

            for point in history:
                if point.total_value > peak:
                    peak = point.total_value
                drawdown = (point.total_value - peak) / peak
                if drawdown < max_dd:
                    max_dd = drawdown

            max_drawdown = max_dd * 100  # Percentuale

        # Best/worst day
        best_day = None
        worst_day = None
        if len(history) >= 2:
            day_returns = []
            for i in range(1, len(history)):
                prev = history[i-1].total_value
                curr = history[i].total_value
                if prev > 0:
                    day_return = (curr - prev) / prev * 100
                    day_returns.append(day_return)

            if day_returns:
                best_day = max(day_returns)
                worst_day = min(day_returns)

        return PerformanceMetrics(
            current_value=current_value,
            initial_value=initial_value,
            absolute_return=absolute_return,
            percentage_return=percentage_return,
            annualized_return=annualized_return,
            volatility=volatility,
            max_drawdown=max_drawdown,
            best_day_return=best_day,
            worst_day_return=worst_day,
            total_days=total_days,
            price_history=history
        )

    def get_portfolio_performance(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[int, PerformanceMetrics]:
        """
        Calcola performance per tutti gli asset correnti del portfolio

        Returns:
            Dict {asset_id: PerformanceMetrics}
        """
        try:
            current_assets = self.portfolio_manager.get_current_assets_only()

            results = {}
            for _, asset in current_assets.iterrows():
                asset_id = int(asset['id'])
                metrics = self.calculate_performance(asset_id, start_date, end_date)
                if metrics:
                    results[asset_id] = metrics

            return results

        except Exception as exc:
            self.logger.error(f"Errore calcolo performance portfolio: {exc}")
            return {}

    def export_to_csv(
        self,
        asset_id: int,
        output_file: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        """
        Esporta storico prezzi in CSV per analisi esterna

        Args:
            asset_id: ID asset
            output_file: Path file CSV output
            start_date: Data inizio (opzionale)
            end_date: Data fine (opzionale)
        """
        history = self.get_asset_history(asset_id, start_date, end_date)

        if not history:
            self.logger.warning(f"Nessun dato da esportare per asset {asset_id}")
            return

        # Converti in DataFrame
        df = pd.DataFrame([
            {
                'date': point.date.strftime('%Y-%m-%d'),
                'price': point.price,
                'amount': point.amount,
                'total_value': point.total_value
            }
            for point in history
        ])

        df.to_csv(output_file, index=False)
        self.logger.info(f"Storico asset {asset_id} esportato in {output_file}")

    def generate_performance_report(
        self,
        asset_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Genera report testuale performance

        Returns:
            Report formattato
        """
        metrics = self.calculate_performance(asset_id, start_date, end_date)

        if not metrics:
            return f"Dati insufficienti per asset ID {asset_id}"

        lines = ["=" * 80]
        lines.append(f"📈 PERFORMANCE REPORT - Asset ID {asset_id}")
        lines.append("=" * 80)

        # Valori base
        lines.append(f"\n💰 VALORI")
        lines.append(f"  Valore iniziale:     €{metrics.initial_value:>15,.2f}")
        lines.append(f"  Valore corrente:     €{metrics.current_value:>15,.2f}")
        lines.append(f"  Rendimento assoluto: €{metrics.absolute_return:>15,.2f}")

        # Rendimenti
        lines.append(f"\n📊 RENDIMENTI")
        lines.append(f"  Rendimento totale:   {metrics.percentage_return:>15.2f}%")
        if metrics.annualized_return is not None:
            lines.append(f"  Rendimento annuo:    {metrics.annualized_return:>15.2f}%")

        # Rischio
        if metrics.volatility is not None or metrics.max_drawdown is not None:
            lines.append(f"\n⚠️  RISCHIO")
            if metrics.volatility is not None:
                lines.append(f"  Volatilità (ann.):   {metrics.volatility:>15.2f}%")
            if metrics.max_drawdown is not None:
                lines.append(f"  Max drawdown:        {metrics.max_drawdown:>15.2f}%")

        # Best/Worst
        if metrics.best_day_return is not None:
            lines.append(f"\n📈 ESTREMI")
            lines.append(f"  Miglior giorno:      {metrics.best_day_return:>15.2f}%")
            lines.append(f"  Peggior giorno:      {metrics.worst_day_return:>15.2f}%")

        # Info temporale
        lines.append(f"\n📅 PERIODO")
        lines.append(f"  Giorni analizzati:   {metrics.total_days:>15d}")
        lines.append(f"  Punti dati:          {len(metrics.price_history):>15d}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)


# Esempio utilizzo
if __name__ == '__main__':
    from models import PortfolioManager

    # Esempio con dati reali (richiede file Excel)
    try:
        pm = PortfolioManager("portfolio_data.xlsx")
        tracker = PriceHistoryTracker(pm)

        # Performance singolo asset
        asset_id = 1
        report = tracker.generate_performance_report(asset_id)
        print(report)

        # Performance portfolio completo
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE PORTFOLIO COMPLETO")
        print("=" * 80)

        portfolio_perf = tracker.get_portfolio_performance()
        for aid, metrics in portfolio_perf.items():
            print(f"\nAsset {aid}: {metrics.percentage_return:+.2f}% "
                  f"(€{metrics.absolute_return:,.2f})")

    except FileNotFoundError:
        print("File portfolio_data.xlsx non trovato. Esempio con dati mock.")
