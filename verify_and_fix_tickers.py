"""
Script per verificare e correggere i ticker degli asset con problemi di matching
Confronta i ticker nel DB con quelli riportati negli alert
"""
import pandas as pd
from models import PortfolioManager

def verify_and_fix_tickers():
    """Verifica e corregge i ticker problematici"""
    pm = PortfolioManager("portfolio_data.xlsx")
    df = pm.load_data()

    # Mapping basato sugli alert ricevuti dal report
    # Format: asset_id -> (ticker_attuale_nel_db, ticker_corretto_da_alert, nome_asset)
    ticker_corrections = {
        49: {
            'current_ticker': 'CHIP',
            'correct_ticker': 'CHIP.SW',  # Dal report alert
            'name': 'Amundi MSCI Semiconductors UCITS ETF Acc',
            'isin': 'LU1900066033'
        },
        50: {
            'current_ticker': 'EQAC',
            'correct_ticker': 'VWCE.DE',  # Dal report alert
            'name': 'Invesco EQQQ Nasdaq-100 UCITS ETF Acc',
            'isin': 'IE00BFZXGZ54'
        },
        51: {
            'current_ticker': 'VGWE',
            'correct_ticker': 'VHYA.L',  # Dal report alert
            'name': 'Vanguard FTSE All-World High Div. Yield UCITS ETF Acc',
            'isin': 'IE00BK5BR626'
        },
        58: {
            'current_ticker': 'SXR8',
            'correct_ticker': 'CSPX.L',  # Dal report alert
            'name': 'IS CR 500 USD-AC EUR',
            'isin': 'IE00B5BMR087'
        },
        59: {
            'current_ticker': 'A0RPWH',
            'correct_ticker': 'IWDA.L',  # Dal report alert
            'name': 'Core MSCI World USD (Acc)',
            'isin': 'IE00B4L5Y983'
        },
        62: {
            'current_ticker': 'ETF146',
            'correct_ticker': 'MWRD.PA',  # Dal report alert
            'name': 'S&P 500 Information Tech USD (Acc)',
            'isin': 'IE000BI8OT95'
        }
    }

    print("=" * 100)
    print("VERIFICA E CORREZIONE TICKER")
    print("=" * 100)

    changes_made = []

    for asset_id, info in ticker_corrections.items():
        print(f"\n--- ASSET ID {asset_id} ---")
        print(f"Nome: {info['name']}")
        print(f"ISIN: {info['isin']}")
        print(f"Ticker ATTUALE nel DB: {info['current_ticker']}")
        print(f"Ticker CORRETTO da usare: {info['correct_ticker']}")

        # Trova tutti i record per questo asset
        mask = df['id'] == asset_id
        matching_records = df[mask]

        if matching_records.empty:
            print(f"ERRORE: Nessun record trovato per ID {asset_id}")
            continue

        current_ticker = matching_records.iloc[0].get('ticker', '')
        print(f"Ticker effettivo nel DB: {current_ticker}")

        if current_ticker != info['correct_ticker']:
            print(f"CORREZIONE NECESSARIA: {current_ticker} -> {info['correct_ticker']}")
            changes_made.append({
                'id': asset_id,
                'name': info['name'],
                'old': current_ticker,
                'new': info['correct_ticker']
            })
        else:
            print(f"OK: Ticker già corretto")

    if not changes_made:
        print("\n" + "=" * 100)
        print("Nessuna correzione necessaria - tutti i ticker sono corretti")
        return

    # Mostra riepilogo modifiche
    print("\n" + "=" * 100)
    print("RIEPILOGO MODIFICHE DA APPLICARE")
    print("=" * 100)
    for change in changes_made:
        print(f"ID {change['id']}: {change['old']} -> {change['new']} ({change['name'][:50]}...)")

    # Chiedi conferma
    print("\n" + "=" * 100)
    response = input(f"Vuoi applicare queste {len(changes_made)} correzioni? (si/no): ")
    if response.lower() != 'si':
        print("Operazione annullata")
        return

    # Applica le correzioni
    for change in changes_made:
        asset_id = change['id']
        new_ticker = change['new']

        # Aggiorna tutti i record dell'asset
        mask = df['id'] == asset_id
        df.loc[mask, 'ticker'] = new_ticker

    # Salva
    pm.save_data(df)
    print(f"\nFile salvato con {len(changes_made)} ticker corretti")
    print("\nIMPORTANTE:")
    print("1. Riapri l'applicazione per vedere le modifiche")
    print("2. Esegui 'python delete_records.py' per cancellare i record con prezzi errati")
    print("3. Rifai l'aggiornamento prezzi - dovrebbe funzionare correttamente ora")

if __name__ == "__main__":
    verify_and_fix_tickers()
