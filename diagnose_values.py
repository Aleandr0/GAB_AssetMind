#!/usr/bin/env python3
"""
Script diagnostico per analizzare discrepanza valori portfolio
Esegui questo mentre l'app principale è chiusa
"""

import pandas as pd
import sys
from pathlib import Path

def analyze_portfolio(file_path='portfolio_data.xlsx'):
    """Analizza il file portfolio e trova discrepanze"""

    try:
        df = pd.read_excel(file_path, keep_default_na=False, na_values=[''])
    except PermissionError:
        print("ERRORE: Chiudi l'applicazione GAB AssetMind prima di eseguire questo script!")
        sys.exit(1)
    except FileNotFoundError:
        print(f"ERRORE: File {file_path} non trovato!")
        sys.exit(1)

    print(f"📊 ANALISI PORTFOLIO: {file_path}")
    print(f"=" * 80)
    print(f"Total records in Excel: {len(df)}")
    print()

    # Normalizza campi chiave
    def norm(s):
        if pd.isna(s) or s == '':
            return ''
        val = str(s).strip()
        if val.lower() in {'na','n/a','none','null','nan',''}:
            return ''
        return val

    for col in ['category','asset_name','position','isin']:
        if col in df.columns:
            df[col] = df[col].apply(norm)
        else:
            df[col] = ''

    # Crea asset_key
    df['asset_key'] = df['category'] + '|' + df['asset_name'] + '|' + df['position'] + '|' + df['isin']

    # Converti date
    df['effective_date'] = pd.to_datetime(
        df['updated_at'].replace(['', 'NA', 'N/A', 'na'], pd.NA).fillna(df['created_at']),
        format='%Y-%m-%d', errors='coerce'
    )

    # Deduplica
    df['original_index'] = df.index
    latest = df.sort_values(['effective_date', 'original_index'], ascending=[False, True]) \
               .groupby('asset_key').first().reset_index()

    print(f"Asset unici (dopo deduplica): {len(latest)}")
    print()

    # Calcola valori
    print("🔍 CALCOLO VALORI")
    print("-" * 80)

    # Somma tutti i record (SBAGLIATO)
    all_updated = df['updated_total_value'].fillna(0).sum()
    all_created = df['created_total_value'].fillna(0).sum()
    all_mixed = df['updated_total_value'].fillna(df['created_total_value']).sum()

    print(f"Somma TUTTI updated_total_value:        €{all_updated:>15,.2f}")
    print(f"Somma TUTTI created_total_value:        €{all_created:>15,.2f}")
    print(f"Somma TUTTI (updated or created):       €{all_mixed:>15,.2f}")
    print()

    # Somma deduplicata (CORRETTO)
    dedup_sum = latest['updated_total_value'].fillna(latest['created_total_value']).sum()
    print(f"Somma DEDUPLICATA (updated or created): €{dedup_sum:>15,.2f}  ✅ CORRETTO")
    print()

    # Confronto con valore atteso
    expected = 3071870.13
    diff = expected - dedup_sum

    print("📈 CONFRONTO CON VALORE ATTESO")
    print("-" * 80)
    print(f"Valore atteso (Valore Totale):          €{expected:>15,.2f}")
    print(f"Valore calcolato (deduplicato):         €{dedup_sum:>15,.2f}")
    print(f"Differenza:                             €{diff:>15,.2f}")

    if abs(diff) < 1:
        diff_pct = 0.0
    else:
        diff_pct = (diff / expected * 100) if expected > 0 else 0
    print(f"Differenza %:                           {diff_pct:>15,.4f}%")
    print()

    if abs(diff) > 1:
        print(f"⚠️  DISCREPANZA TROVATA: €{abs(diff):,.2f}")
        print()

        # Analisi dettagliata
        print("🔎 ANALISI DETTAGLIATA")
        print("-" * 80)

        # Record con valori anomali
        latest['total_val'] = latest['updated_total_value'].fillna(latest['created_total_value'])

        # Top 20 asset per valore
        print("\n📊 TOP 20 ASSET PER VALORE:")
        print()
        top20 = latest.nlargest(20, 'total_val')
        total_top20 = 0
        for i, (_, row) in enumerate(top20.iterrows(), 1):
            val = row['total_val']
            total_top20 += val
            print(f"{i:2d}. ID {int(row['id']):3d}: {row['category']:20s} "
                  f"{row['asset_name'][:35]:35s} → €{val:>12,.2f}")

        print()
        print(f"Somma top 20: €{total_top20:,.2f} ({total_top20/dedup_sum*100:.1f}% del totale)")
        print()

        # Cerca duplicati potenziali
        print("\n🔍 ASSET CON MULTIPLE VERSIONI:")
        print()
        duplicates = df.groupby('asset_key').size()
        multi_version = duplicates[duplicates > 1].sort_values(ascending=False)

        if len(multi_version) > 0:
            for asset_key, count in multi_version.head(10).items():
                records = df[df['asset_key'] == asset_key].sort_values('effective_date', ascending=False)
                print(f"\n  Asset: {asset_key[:60]}")
                print(f"  Versioni: {count}")
                for idx, (_, rec) in enumerate(records.iterrows()):
                    marker = "✅ CORRENTE" if idx == 0 else "🔵 STORICO"
                    val = rec['updated_total_value'] if pd.notna(rec['updated_total_value']) and rec['updated_total_value'] != 0 else rec['created_total_value']
                    print(f"    ID {int(rec['id']):3d} [{rec['effective_date'].strftime('%Y-%m-%d') if pd.notna(rec['effective_date']) else 'N/A':10s}] "
                          f"€{val:>12,.2f} {marker}")
        else:
            print("  Nessun duplicato trovato")

        print()

        # Cerca valori mancanti o zero
        print("\n⚠️  ASSET CON VALORI ZERO O MANCANTI:")
        print()
        zero_vals = latest[latest['total_val'] == 0]
        if len(zero_vals) > 0:
            for _, row in zero_vals.head(10).iterrows():
                print(f"  ID {int(row['id']):3d}: {row['category']:20s} {row['asset_name'][:40]:40s}")
        else:
            print("  Nessuno")
    else:
        print("✅ VALORI CORRETTI - Nessuna discrepanza significativa!")

    print()
    print("=" * 80)

if __name__ == '__main__':
    analyze_portfolio()
