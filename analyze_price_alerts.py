"""
Script per analizzare gli asset con alert di variazione prezzo anomala
Mostra tutti i record storici per capire l'origine del problema
"""
import pandas as pd
from models import PortfolioManager

def analyze_asset(pm: PortfolioManager, asset_id: int):
    """Analizza tutti i record di un asset specifico"""
    df = pm.load_data()

    # Filtra tutti i record per questo asset ID
    asset_records = df[df['id'] == asset_id].copy()

    if asset_records.empty:
        print(f"❌ Nessun record trovato per ID {asset_id}")
        return

    # Ordina per data (created_at, poi updated_at)
    asset_records['sort_date'] = pd.to_datetime(
        asset_records['updated_at'].fillna(asset_records['created_at']),
        format='%Y-%m-%d', errors='coerce'
    )
    asset_records = asset_records.sort_values('sort_date')

    print(f"\n{'='*100}")
    print(f"ASSET ID {asset_id}")
    print(f"{'='*100}")

    # Info base
    first = asset_records.iloc[0]
    print(f"Nome: {first.get('asset_name', 'N/A')}")
    print(f"Ticker: {first.get('ticker', 'N/A')}")
    print(f"ISIN: {first.get('isin', 'N/A')}")
    print(f"Categoria: {first.get('category', 'N/A')}")
    print(f"\nTotale record storici: {len(asset_records)}")

    # Mostra tutti i record con prezzi
    print(f"\nSTORICO PREZZI:")
    print(f"{'-'*100}")
    print(f"{'Data':<12} {'Tipo':<8} {'Prezzo Unit.':<15} {'Quantità':<12} {'Valore Tot.':<15} {'Note':<30}")
    print(f"{'-'*100}")

    for idx, row in asset_records.iterrows():
        # Determina data e tipo
        updated_at = row.get('updated_at', '')
        created_at = row.get('created_at', '')

        if pd.notna(updated_at) and updated_at != '':
            date = updated_at
            rec_type = "UPDATE"
        else:
            date = created_at
            rec_type = "CREATE"

        # Determina prezzo e quantità
        if rec_type == "UPDATE":
            price = row.get('updated_unit_price', 0)
            amount = row.get('updated_amount', row.get('created_amount', 0))
            total = row.get('updated_total_value', 0)
        else:
            price = row.get('created_unit_price', 0)
            amount = row.get('created_amount', 0)
            total = row.get('created_total_value', 0)

        # Note (troncate)
        note = str(row.get('note', ''))[:30] if pd.notna(row.get('note')) else ''

        print(f"{date:<12} {rec_type:<8} {price:<15.6f} {amount:<12.2f} {total:<15.2f} {note:<30}")

    # Calcola variazioni
    print(f"\nANALISI VARIAZIONI:")
    if len(asset_records) >= 2:
        last = asset_records.iloc[-1]
        prev = asset_records.iloc[-2]

        last_price = last.get('updated_unit_price', last.get('created_unit_price', 0))
        prev_price = prev.get('updated_unit_price', prev.get('created_unit_price', 0))

        if prev_price > 0:
            variation = ((last_price - prev_price) / prev_price) * 100
            print(f"Prezzo precedente (penultimo record): €{prev_price:,.6f}")
            print(f"Prezzo ultimo record: €{last_price:,.6f}")
            print(f"Variazione: {variation:+.2f}%")

            if abs(variation) > 15:
                print(f"ALERT: Variazione anomala > 15%")
        else:
            print("Impossibile calcolare variazione (prezzo precedente = 0)")

if __name__ == "__main__":
    pm = PortfolioManager("portfolio_data.xlsx")

    # Asset con alert di variazione anomala
    problem_assets = [49, 50, 51, 58, 59, 62]

    print("ANALISI ASSET CON ALERT VARIAZIONE PREZZO")
    print("=" * 100)

    for asset_id in problem_assets:
        analyze_asset(pm, asset_id)

    print(f"\n{'='*100}")
    print("Analisi completata")
