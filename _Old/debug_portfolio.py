#!/usr/bin/env python3
"""Debug script per verificare il caricamento portfolio"""

from models import PortfolioManager
import pandas as pd

print("=== Debug Portfolio Loading ===")

# Test 1: Carica dati raw
pm = PortfolioManager()
print(f"1. File Excel esiste: {pm.excel_file}")

# Test 2: Load raw data
df_raw = pm.load_data()
print(f"2. Raw data loaded: {len(df_raw)} records")
if not df_raw.empty:
    print(f"   Colonne: {list(df_raw.columns)}")
    print(f"   ID range: {df_raw['id'].min()} - {df_raw['id'].max()}")

# Test 3: Current assets only
df_current = pm.get_current_assets_only() 
print(f"3. Current assets: {len(df_current)} records")
if not df_current.empty:
    print(f"   ID range: {df_current['id'].min()} - {df_current['id'].max()}")
    print(f"   Prime 3 righe:")
    for _, row in df_current.head(3).iterrows():
        print(f"      ID {row['id']}: {row['category']} - {row['asset_name']}")

print("\n=== Test completato ===")