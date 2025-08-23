#!/usr/bin/env python3
"""
Test specifico per il salvataggio asset
"""

from models import Asset, PortfolioManager
import pandas as pd

print("=== TEST SALVATAGGIO ASSET ===")

# Test 1: Verifica file Excel esistente
print("1. Controllo file Excel...")
try:
    df = pd.read_excel('portfolio_data.xlsx')
    print(f"OK - File Excel caricato: {len(df)} righe, {len(df.columns)} colonne")
    print(f"Colonne: {list(df.columns)}")
except Exception as e:
    print(f"ERRORE - Errore caricamento Excel: {e}")

# Test 2: Crea PortfolioManager
print("\n2. Test PortfolioManager...")
try:
    pm = PortfolioManager()
    print("OK - PortfolioManager creato")
except Exception as e:
    print(f"ERRORE - Errore PortfolioManager: {e}")

# Test 3: Crea asset di test
print("\n3. Creazione asset di test...")
try:
    test_asset = Asset(
        category="ETF",
        assetName="Asset Test",
        position="Test Position",
        riskLevel=3,
        ticker="TEST",
        createdAmount=100.0,
        createdUnitPrice=25.50,
        note="Test note"
    )
    print("OK - Asset di test creato")
    print(f"Asset data: {test_asset.to_dict()}")
except Exception as e:
    print(f"ERRORE - Errore creazione asset: {e}")

# Test 4: Salva asset
print("\n4. Test salvataggio...")
try:
    result = pm.add_asset(test_asset)
    print(f"Risultato salvataggio: {result}")
except Exception as e:
    print(f"ERRORE - Errore salvataggio: {e}")

# Test 5: Verifica salvataggio
print("\n5. Verifica salvataggio...")
try:
    df_after = pd.read_excel('portfolio_data.xlsx')
    print(f"Righe dopo salvataggio: {len(df_after)}")
    if len(df_after) > 0:
        print("OK - Salvataggio funziona!")
        print("Ultima riga:")
        print(df_after.tail(1))
    else:
        print("ERRORE - Nessuna riga salvata!")
except Exception as e:
    print(f"ERRORE - Errore verifica: {e}")

print("\n=== FINE TEST ===")
input("Premi INVIO per chiudere...")