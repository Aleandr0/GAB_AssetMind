"""
Script per trovare i ticker corretti confrontando i prezzi attuali
con quelli inseriti manualmente il 2025-10-03

Strategia:
1. Per ogni asset problematico, prova tutti i ticker possibili
2. Confronta il prezzo ottenuto con quello manuale (±3% tolleranza)
3. Propone il ticker che matcha meglio
"""
import pandas as pd
from models import PortfolioManager
from market_data import MarketDataService

def find_correct_ticker_by_price():
    """Trova il ticker corretto basandosi sul confronto prezzi"""
    pm = PortfolioManager("portfolio_data.xlsx")
    market_provider = MarketDataService()

    # Asset problematici con i loro possibili ticker alternativi (da ricerca ISIN)
    assets_to_check = {
        49: {
            'name': 'Amundi MSCI Semiconductors',
            'isin': 'LU1900066033',
            'current_ticker': 'CHIP',
            'manual_price': 66.63,  # Prezzo inserito manualmente 2025-10-03
            'manual_date': '2025-10-03',
            'possible_tickers': ['LSMC', 'CHIP', 'CHIP.SW', 'CHIP.PA']  # Ticker da testare
        },
        50: {
            'name': 'Invesco EQQQ Nasdaq-100',
            'isin': 'IE00BFZXGZ54',
            'current_ticker': 'EQAC',
            'manual_price': 362.54,
            'manual_date': '2025-10-03',
            'possible_tickers': ['EQQB', 'EQAC', 'EQQQ', '3QQQ.DE']
        },
        51: {
            'name': 'Vanguard FTSE All-World High Div',
            'isin': 'IE00BK5BR626',
            'current_ticker': 'VGWE',
            'manual_price': 75.68,
            'manual_date': '2025-10-03',
            'possible_tickers': ['VGWE', 'VHYA', 'VHYD.L', 'VHYL']
        },
        58: {
            'name': 'iShares Core S&P 500',
            'isin': 'IE00B5BMR087',
            'current_ticker': 'SXR8',
            'manual_price': 613.70,
            'manual_date': '2025-10-03',
            'possible_tickers': ['SXR8', 'CSPX', 'CSPX.L', 'CSSPX', 'SXR8.DE']
        },
        59: {
            'name': 'iShares Core MSCI World',
            'isin': 'IE00B4L5Y983',
            'current_ticker': 'A0RPWH',
            'manual_price': 108.46,
            'manual_date': '2025-10-03',
            'possible_tickers': ['EUNL', 'IWDA', 'SWDA', 'IWDA.L', 'EUNL.DE', 'SWDA.SW']
        },
        62: {
            'name': 'Amundi Core MSCI World (o S&P 500 Info Tech)',
            'isin': 'IE000BI8OT95',
            'current_ticker': 'ETF146',
            'manual_price': 35.16,
            'manual_date': '2025-10-03',
            'possible_tickers': ['MWRE', 'ETF146', 'CW8', 'MWRD.PA']
        }
    }

    print("=" * 100)
    print("RICERCA TICKER CORRETTI TRAMITE CONFRONTO PREZZI")
    print("=" * 100)
    print("\nTolleranza: ±3% rispetto al prezzo manuale del 2025-10-03")

    results = {}

    for asset_id, info in assets_to_check.items():
        print(f"\n{'-' * 100}")
        print(f"ASSET ID {asset_id}: {info['name']}")
        print(f"{'-' * 100}")
        print(f"ISIN: {info['isin']}")
        print(f"Ticker attuale nel DB: {info['current_ticker']}")
        print(f"Prezzo manuale (2025-10-03): €{info['manual_price']:.2f}")
        print(f"\nTestando {len(info['possible_tickers'])} ticker possibili...")

        matches = []

        for ticker in info['possible_tickers']:
            print(f"\n  Testing ticker: {ticker}...", end=" ")
            try:
                # Prova a ottenere il prezzo
                quote_data = market_provider.get_latest_price(
                    ticker=ticker,
                    isin=None,  # Non usiamo ISIN per evitare override
                    asset_name=None
                )

                if quote_data and 'price' in quote_data:
                    price = float(quote_data['price'])
                    currency = quote_data.get('currency', 'N/A')
                    symbol = quote_data.get('symbol', ticker)

                    # Calcola differenza percentuale
                    diff_pct = abs((price - info['manual_price']) / info['manual_price'] * 100)

                    print(f"€{price:.2f} {currency} (Δ {diff_pct:.2f}%)", end="")

                    if diff_pct <= 3.0:
                        print(f" ✓ MATCH!")
                        matches.append({
                            'ticker': ticker,
                            'price': price,
                            'currency': currency,
                            'symbol': symbol,
                            'diff_pct': diff_pct
                        })
                    else:
                        print(f" ✗ Fuori tolleranza")
                else:
                    print("Nessun prezzo disponibile")

            except Exception as e:
                print(f"Errore: {str(e)[:50]}")

        # Riepilogo per questo asset
        print(f"\n{'=' * 100}")
        if matches:
            print(f"TROVATI {len(matches)} TICKER VALIDI:")
            # Ordina per differenza percentuale (migliore prima)
            matches.sort(key=lambda x: x['diff_pct'])

            for idx, match in enumerate(matches, 1):
                best_marker = " ← MIGLIORE" if idx == 1 else ""
                print(f"  {idx}. {match['ticker']}: €{match['price']:.2f} {match['currency']} "
                      f"(Δ {match['diff_pct']:.2f}%){best_marker}")

            results[asset_id] = {
                'best_ticker': matches[0]['ticker'],
                'current_ticker': info['current_ticker'],
                'manual_price': info['manual_price'],
                'market_price': matches[0]['price'],
                'diff_pct': matches[0]['diff_pct'],
                'all_matches': matches
            }
        else:
            print("NESSUN TICKER VALIDO TROVATO (tutti fuori tolleranza ±3%)")
            results[asset_id] = None

    # Riepilogo finale
    print(f"\n{'=' * 100}")
    print("RIEPILOGO CORREZIONI PROPOSTE")
    print(f"{'=' * 100}\n")

    corrections = []
    for asset_id, result in results.items():
        if result and result['best_ticker'] != result['current_ticker']:
            corrections.append({
                'id': asset_id,
                'old': result['current_ticker'],
                'new': result['best_ticker'],
                'confidence': f"{100 - result['diff_pct']:.1f}%"
            })
            print(f"ID {asset_id}: {result['current_ticker']} → {result['best_ticker']} "
                  f"(confidenza: {100 - result['diff_pct']:.1f}%)")

    if not corrections:
        print("Nessuna correzione necessaria")
        return

    print(f"\n{'=' * 100}")
    print(f"Vuoi applicare queste {len(corrections)} correzioni? (manualmente con lo script di correzione)")

if __name__ == "__main__":
    find_correct_ticker_by_price()
