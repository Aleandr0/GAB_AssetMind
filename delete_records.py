"""
Script helper per cancellare record specifici dal portfolio Excel
Utile per test e rollback di aggiornamenti prezzi errati
"""
import pandas as pd
from models import PortfolioManager
from pathlib import Path

def delete_records_by_ids(excel_file: str, record_ids: list[int]):
    """
    Cancella record specifici dal file Excel basandosi sui loro ID interni

    Args:
        excel_file: Path del file Excel
        record_ids: Lista di ID dei record da cancellare
    """
    pm = PortfolioManager(excel_file)

    # Carica tutti i dati
    df = pm.load_data()

    if df.empty:
        print("❌ Nessun dato nel portfolio")
        return

    print(f"\n📊 Record totali PRIMA della cancellazione: {len(df)}")
    print(f"🎯 Record da cancellare: {record_ids}")

    # Mostra i record che verranno cancellati
    records_to_delete = df[df['id'].isin(record_ids)]
    if records_to_delete.empty:
        print("⚠️  Nessun record trovato con questi ID")
        return

    print(f"\n🗑️  Record che verranno cancellati ({len(records_to_delete)}):")
    for _, row in records_to_delete.iterrows():
        asset_name = row.get('asset_name', 'N/A')
        updated_at = row.get('updated_at', 'N/A')
        price = row.get('updated_unit_price', row.get('created_unit_price', 'N/A'))
        print(f"  - ID {row['id']}: {asset_name} | Data: {updated_at} | Prezzo: {price}")

    # Chiedi conferma
    response = input(f"\n⚠️  Confermi la cancellazione di {len(records_to_delete)} record? (si/no): ")
    if response.lower() != 'si':
        print("❌ Operazione annullata")
        return

    # Cancella i record
    df_cleaned = df[~df['id'].isin(record_ids)]

    print(f"\n📊 Record totali DOPO la cancellazione: {len(df_cleaned)}")
    print(f"✅ Cancellati: {len(df) - len(df_cleaned)} record")

    # Salva
    pm.save_data(df_cleaned)
    print(f"\n✅ File salvato: {excel_file}")
    print("\n💡 Suggerimento: Riapri l'applicazione per vedere le modifiche")

if __name__ == "__main__":
    # IDs dei record creati nell'ultimo aggiornamento prezzi (dal report)
    # Record IDs: 69-89 (21 record totali)
    record_ids_to_delete = list(range(69, 90))  # 69, 70, 71, ..., 89

    excel_file = "portfolio_data.xlsx"

    print("=" * 70)
    print("🗑️  UTILITY DI CANCELLAZIONE RECORD")
    print("=" * 70)

    delete_records_by_ids(excel_file, record_ids_to_delete)
