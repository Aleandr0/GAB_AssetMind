#!/usr/bin/env python3
"""
Script di analisi approfondita del portfolio reale
Identifica potenziali problemi prima di eseguire test completi
"""

import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Aggiungi parent directory al path
sys.path.insert(0, str(Path(__file__).parent))

from config import DatabaseConfig


def analyze_portfolio(filepath='portfolio_data.xlsx'):
    """Analizza il portfolio reale e genera report dettagliato"""

    print("=" * 100)
    print("ANALISI PORTFOLIO REALE - GAB AssetMind")
    print("=" * 100)
    print(f"\nFile: {filepath}")
    print(f"Data analisi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Carica dati
        df = pd.read_excel(filepath)
        print(f"✅ File caricato con successo")
        print(f"   Righe totali: {len(df)}")
        print(f"   Colonne: {len(df.columns)}\n")

    except FileNotFoundError:
        print(f"❌ ERRORE: File {filepath} non trovato!")
        return
    except Exception as e:
        print(f"❌ ERRORE nel caricamento: {e}")
        return

    # ========================================================================
    # 1. STRUTTURA DATI
    # ========================================================================
    print("\n" + "=" * 100)
    print("1. ANALISI STRUTTURA DATI")
    print("=" * 100)

    # Verifica colonne
    expected_cols = DatabaseConfig.DB_COLUMNS
    missing_cols = set(expected_cols) - set(df.columns)
    extra_cols = set(df.columns) - set(expected_cols)

    if missing_cols:
        print(f"⚠️  COLONNE MANCANTI: {missing_cols}")
    else:
        print("✅ Tutte le colonne richieste sono presenti")

    if extra_cols:
        print(f"⚠️  COLONNE EXTRA (non previste): {extra_cols}")

    # Statistiche di base
    print(f"\n📊 Statistiche generali:")
    print(f"   - Record totali: {len(df)}")
    print(f"   - ID univoci: {df['id'].nunique()}")
    print(f"   - Asset univoci (name+ISIN): {df.groupby(['asset_name', 'isin']).ngroups}")

    # ========================================================================
    # 2. CATEGORIE ASSET
    # ========================================================================
    print("\n" + "=" * 100)
    print("2. DISTRIBUZIONE CATEGORIE")
    print("=" * 100)

    category_counts = df['category'].value_counts()
    print(f"\n{category_counts}\n")

    # Categorie non standard
    standard_categories = ['ETF', 'Azioni', 'Fondi di investimento', 'Buoni del Tesoro',
                          'PAC', 'Criptovalute', 'Liquidità', 'Immobiliare', 'Oggetti']
    non_standard = set(df['category'].dropna().unique()) - set(standard_categories)
    if non_standard:
        print(f"⚠️  CATEGORIE NON STANDARD: {non_standard}")

    # ========================================================================
    # 3. INTEGRITÀ DATI
    # ========================================================================
    print("\n" + "=" * 100)
    print("3. VERIFICA INTEGRITÀ DATI")
    print("=" * 100)

    # Campi critici con valori mancanti
    critical_fields = ['id', 'category', 'asset_name', 'created_at', 'created_total_value']
    for field in critical_fields:
        null_count = df[field].isna().sum()
        if null_count > 0:
            print(f"⚠️  Campo '{field}': {null_count} valori mancanti")

    # Valori numerici negativi (anomali)
    numeric_fields = ['created_amount', 'created_unit_price', 'created_total_value',
                     'updated_amount', 'updated_unit_price', 'updated_total_value']

    print(f"\n📈 Verifica valori numerici:")
    for field in numeric_fields:
        if field in df.columns:
            negative_count = (df[field] < 0).sum()
            if negative_count > 0:
                print(f"   ⚠️  '{field}': {negative_count} valori negativi (anomalo)")

            # Valori estremamente grandi (possibili errori)
            if df[field].max() > 1e6:
                print(f"   ⚠️  '{field}': valore max = {df[field].max():.2f} (verificare)")

    # ========================================================================
    # 4. TICKER E ISIN
    # ========================================================================
    print("\n" + "=" * 100)
    print("4. ANALISI TICKER/ISIN (Compatibilità API Market Data)")
    print("=" * 100)

    # Asset con ticker
    has_ticker = df[df['ticker'].notna() & (df['ticker'] != '') & (df['ticker'] != 'NA')]
    print(f"\n✅ Asset con ticker: {len(has_ticker)} / {len(df)}")

    # Asset con solo ISIN
    has_isin_only = df[
        (df['isin'].notna()) & (df['isin'] != '') & (df['isin'] != 'NA') &
        ((df['ticker'].isna()) | (df['ticker'] == '') | (df['ticker'] == 'NA'))
    ]
    print(f"⚠️  Asset con SOLO ISIN (no ticker): {len(has_isin_only)}")

    if len(has_isin_only) > 0:
        print(f"   Categorie interessate:")
        print(has_isin_only['category'].value_counts().to_string(header=False))

    # Asset senza ticker né ISIN
    no_identifier = df[
        ((df['ticker'].isna()) | (df['ticker'] == '') | (df['ticker'] == 'NA')) &
        ((df['isin'].isna()) | (df['isin'] == '') | (df['isin'] == 'NA'))
    ]
    print(f"\n❌ Asset SENZA ticker e SENZA ISIN: {len(no_identifier)}")

    if len(no_identifier) > 0:
        print(f"   Categorie (previsto per Liquidità, Immobiliare, Oggetti):")
        print(no_identifier['category'].value_counts().to_string(header=False))

    # ========================================================================
    # 5. RECORD STORICI E DEDUPLICAZIONE
    # ========================================================================
    print("\n" + "=" * 100)
    print("5. RECORD STORICI E LOGICA DEDUPLICAZIONE")
    print("=" * 100)

    # Normalizza position per deduplicazione (come fa l'app)
    df_normalized = df.copy()
    df_normalized['position'] = df_normalized['position'].replace(['NA', 'N/A', 'null'], '')

    # Raggruppa per asset_name + isin + position
    grouped = df_normalized.groupby(['asset_name', 'isin', 'position'])

    assets_with_history = []
    for (name, isin, pos), group in grouped:
        if len(group) > 1:
            assets_with_history.append({
                'asset_name': name,
                'isin': isin,
                'position': pos,
                'num_records': len(group),
                'ids': group['id'].tolist(),
                'dates': group['updated_at'].tolist()
            })

    print(f"\n📚 Asset con record storici: {len(assets_with_history)}")
    print(f"   (Asset con >1 record nella storia)")

    if assets_with_history:
        print(f"\n   Top 5 asset per numero di record:")
        sorted_assets = sorted(assets_with_history, key=lambda x: x['num_records'], reverse=True)[:5]
        for asset in sorted_assets:
            print(f"   - {asset['asset_name'][:40]:40} | Records: {asset['num_records']} | IDs: {asset['ids']}")

    # ========================================================================
    # 6. VALORI TOTALI E PERFORMANCE
    # ========================================================================
    print("\n" + "=" * 100)
    print("6. ANALISI VALORI E PERFORMANCE")
    print("=" * 100)

    # Calcola valore totale corrente (logica app)
    df['current_value'] = df['updated_total_value'].fillna(df['created_total_value'])
    total_portfolio_value = df['current_value'].sum()

    print(f"\n💰 Valore totale portfolio: €{total_portfolio_value:,.2f}")

    # Distribuzione per categoria
    print(f"\n📊 Distribuzione valore per categoria:")
    category_values = df.groupby('category')['current_value'].sum().sort_values(ascending=False)
    for cat, val in category_values.items():
        pct = (val / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        print(f"   {cat:25} | €{val:12,.2f} | {pct:5.1f}%")

    # Asset con variazioni significative
    df['performance_pct'] = (
        (df['updated_total_value'] - df['created_total_value']) / df['created_total_value'] * 100
    )

    high_performers = df[df['performance_pct'] > 20].sort_values('performance_pct', ascending=False)
    low_performers = df[df['performance_pct'] < -20].sort_values('performance_pct')

    if len(high_performers) > 0:
        print(f"\n📈 Asset con performance >+20%: {len(high_performers)}")
        print(high_performers[['asset_name', 'performance_pct']].head(3).to_string(index=False))

    if len(low_performers) > 0:
        print(f"\n📉 Asset con performance <-20%: {len(low_performers)}")
        print(low_performers[['asset_name', 'performance_pct']].head(3).to_string(index=False))

    # ========================================================================
    # 7. POTENZIALI PROBLEMI
    # ========================================================================
    print("\n" + "=" * 100)
    print("7. RIEPILOGO POTENZIALI PROBLEMI")
    print("=" * 100)

    issues = []

    if missing_cols:
        issues.append(f"❌ CRITICO: Colonne mancanti nel database: {missing_cols}")

    if len(has_isin_only) > 10:
        issues.append(f"⚠️  ATTENZIONE: {len(has_isin_only)} asset con solo ISIN (API potrebbero fallire)")

    if len(no_identifier) > 0:
        non_cash_no_id = no_identifier[~no_identifier['category'].isin(['Liquidità', 'Immobiliare', 'Oggetti'])]
        if len(non_cash_no_id) > 0:
            issues.append(f"⚠️  ATTENZIONE: {len(non_cash_no_id)} asset tradable senza ticker/ISIN")

    if len(df) > 100:
        issues.append(f"⚠️  PERFORMANCE: {len(df)} record potrebbero causare lentezza caricamento (>5s)")

    # Asset venduti ma ancora presenti
    sold_assets = df[(df['updated_amount'] == 0) & (df['updated_total_value'] == 0)]
    if len(sold_assets) > 10:
        issues.append(f"⚠️  PULIZIA: {len(sold_assets)} asset venduti ancora nel database")

    if issues:
        print("\n")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n   ✅ Nessun problema critico rilevato!")

    # ========================================================================
    # 8. RACCOMANDAZIONI
    # ========================================================================
    print("\n" + "=" * 100)
    print("8. RACCOMANDAZIONI")
    print("=" * 100)

    print("""
    ✅ PROSSIMI PASSI CONSIGLIATI:

    1. BACKUP PREVENTIVO:
       - Creare backup del file Excel attuale
       - Comando: cp portfolio_data.xlsx portfolio_data_backup_$(date +%Y%m%d).xlsx

    2. TEST AGGIORNAMENTO PREZZI:
       - Testare su 5-10 asset prima di aggiornare tutto
       - Verificare rate limiting API (8 req/min)
       - Controllare alert variazioni >20%

    3. MONITORAGGIO PERFORMANCE:
       - Misurare tempo caricamento portfolio
       - Verificare lag grafici matplotlib
       - Controllare uso memoria durante operazioni

    4. VALIDAZIONE DATI:
       - Verificare calcolo "Valore Totale" = "Valore selezionato" (senza filtri)
       - Testare filtri su categorie e verificare percentuali
       - Controllare coerenza grafici con tabella Portfolio

    5. EXPORT REPORT:
       - Generare PDF con dataset reale
       - Verificare formattazione con molte categorie
       - Testare Excel export con tutti i record
    """)

    print("=" * 100)
    print("FINE ANALISI")
    print("=" * 100)


if __name__ == "__main__":
    analyze_portfolio()
