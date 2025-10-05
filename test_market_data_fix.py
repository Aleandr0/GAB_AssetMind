"""Test rapido per verificare che i mapping ticker corretti funzionino"""
import time
from market_data import MarketDataService

# Asset problematici con prezzi di riferimento (inseriti manualmente il 2025-10-03)
test_cases = [
    {
        'id': 49,
        'name': 'Amundi Semiconductors',
        'isin': 'LU1900066033',
        'ticker': 'CHIP',
        'expected_price': 66.63,
        'tolerance': 0.03  # 3%
    },
    {
        'id': 50,
        'name': 'Invesco EQQQ',
        'isin': 'IE00BFZXGZ54',
        'ticker': 'EQAC',
        'expected_price': 362.54,
        'tolerance': 0.03
    },
    {
        'id': 51,
        'name': 'Vanguard High Div',
        'isin': 'IE00BK5BR626',
        'ticker': 'VGWE',
        'expected_price': 75.68,
        'tolerance': 0.03
    },
    {
        'id': 58,
        'name': 'iShares S&P 500',
        'isin': 'IE00B5BMR087',
        'ticker': 'SXR8',
        'expected_price': 613.70,
        'tolerance': 0.03
    },
    {
        'id': 59,
        'name': 'iShares MSCI World',
        'isin': 'IE00B4L5Y983',
        'ticker': 'A0RPWH',
        'expected_price': 108.46,
        'tolerance': 0.03
    },
    {
        'id': 62,
        'name': 'Amundi Core World',
        'isin': 'IE000BI8OT95',
        'ticker': 'ETF146',
        'expected_price': 35.16,
        'tolerance': 0.03
    },
]

def test_market_data():
    print("=" * 100)
    print("TEST MARKET DATA CON MAPPING CORRETTI")
    print("=" * 100)
    print("\nAttenzione: Test con rate limiting per evitare ban API")
    print("Tolleranza: ±3% rispetto al prezzo di riferimento\n")

    provider = MarketDataService()
    results = []

    for idx, test in enumerate(test_cases, 1):
        print(f"\n[{idx}/{len(test_cases)}] Testing {test['name']} (ISIN: {test['isin']})")
        print(f"    Ticker DB: {test['ticker']}")
        print(f"    Prezzo riferimento: €{test['expected_price']:.2f}")

        try:
            # Usa ISIN per sfruttare il mapping corretto
            quote = provider.get_latest_price(
                ticker=test['ticker'],
                isin=test['isin'],
                asset_name=test['name']
            )

            if quote and 'price' in quote:
                price = float(quote['price'])
                currency = quote.get('currency', 'N/A')
                symbol = quote.get('symbol', 'N/A')
                provider_used = quote.get('provider', 'N/A')

                diff_pct = abs((price - test['expected_price']) / test['expected_price'])

                status = "✓ OK" if diff_pct <= test['tolerance'] else "✗ FUORI TOLLERANZA"
                print(f"    → Prezzo: €{price:.2f} {currency} | Symbol: {symbol} | Provider: {provider_used}")
                print(f"    → Variazione: {diff_pct*100:.2f}% | {status}")

                results.append({
                    'id': test['id'],
                    'name': test['name'],
                    'success': diff_pct <= test['tolerance'],
                    'price': price,
                    'diff_pct': diff_pct,
                    'provider': provider_used
                })
            else:
                print(f"    → ERRORE: Nessun prezzo disponibile")
                results.append({
                    'id': test['id'],
                    'name': test['name'],
                    'success': False,
                    'error': 'No price data'
                })

        except Exception as e:
            print(f"    → ERRORE: {str(e)[:80]}")
            results.append({
                'id': test['id'],
                'name': test['name'],
                'success': False,
                'error': str(e)[:80]
            })

        # Rate limiting: 8 req/min con TwelveData free
        if idx < len(test_cases):
            print(f"    Pausa 8 secondi (rate limiting)...")
            time.sleep(8)

    # Riepilogo
    print(f"\n{'=' * 100}")
    print("RIEPILOGO")
    print(f"{'=' * 100}\n")

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"Successi: {len(successful)}/{len(results)}")
    print(f"Falliti: {len(failed)}/{len(results)}\n")

    if successful:
        print("Asset con prezzo corretto:")
        for r in successful:
            print(f"  ✓ ID {r['id']}: {r['name']} | {r['price']:.2f} (Δ {r['diff_pct']*100:.2f}%) | {r.get('provider', 'N/A')}")

    if failed:
        print(f"\nAsset falliti:")
        for r in failed:
            error = r.get('error', 'Unknown')
            print(f"  ✗ ID {r['id']}: {r['name']} | {error}")

    return len(successful) == len(results)

if __name__ == "__main__":
    success = test_market_data()
    exit(0 if success else 1)
