#!/usr/bin/env python3
"""
Modelli dati per GAB AssetMind
Gestisce la persistenza dei dati portfolio in formato Excel

Classi principali:
- Asset: Rappresenta un singolo asset del portfolio
- PortfolioManager: Gestisce il database Excel e le operazioni CRUD
"""

import pandas as pd
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from logging_config import get_logger
from security_validation import PathSecurityValidator, SecurityError
from date_utils import get_date_manager, format_for_storage, parse_date

class Asset:
    """
    Rappresenta un singolo asset del portfolio
    
    Supporta tutti i tipi di asset: ETF, Azioni, Fondi di investimento, Buoni del Tesoro,
    PAC, Criptovalute, Liquidità, Immobiliare, Oggetti
    
    Attributi:
        asset_id: ID univoco dell'asset
        category: Categoria (ETF, Azioni, etc.)
        asset_name: Nome dell'asset
        position: Posizione/descrizione (testo libero)
        risk_level: Livello di rischio 1-5
        ticker: Codice ticker di borsa
        isin: Codice ISIN
        created_at/updated_at: Date di creazione/aggiornamento
        created_amount/updated_amount: Quantità iniziale/attuale
        created_unit_price/updated_unit_price: Prezzo unitario iniziale/attuale
        created_total_value/updated_total_value: Valore totale iniziale/attuale
        accumulation_plan: Descrizione piano di accumulo
        accumulation_amount: Importo accumulo mensile
        income_per_year: Reddito annuale da investimento
        rental_income: Reddito annuale da affitto
        note: Note libere
    """
    
    def __init__(self, asset_id: int = None, category: str = "", asset_name: str = "", 
                 position: str = "", risk_level: int = 1, ticker: str = "", 
                 isin: str = "", created_at: str = "", created_amount: float = 0.0, 
                 created_unit_price: float = 0.0, created_total_value: float = 0.0,
                 updated_at: str = "", updated_amount: float = 0.0, 
                 updated_unit_price: float = 0.0, updated_total_value: float = 0.0,
                 accumulation_plan: str = "", accumulation_amount: float = 0.0,
                 income_per_year: float = 0.0, rental_income: float = 0.0, note: str = ""):
        self.id = asset_id
        self.category = category
        self.asset_name = asset_name
        self.position = position
        self.risk_level = risk_level
        self.ticker = ticker
        self.isin = isin
        self.created_at = created_at
        self.created_amount = created_amount
        self.created_unit_price = created_unit_price
        self.created_total_value = created_total_value
        self.updated_at = updated_at
        self.updated_amount = updated_amount
        self.updated_unit_price = updated_unit_price
        self.updated_total_value = updated_total_value
        self.accumulation_plan = accumulation_plan
        self.accumulation_amount = accumulation_amount
        self.income_per_year = income_per_year
        self.rental_income = rental_income
        self.note = note

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'category': self.category,
            'asset_name': self.asset_name,
            'position': self.position,
            'risk_level': self.risk_level,
            'ticker': self.ticker,
            'isin': self.isin,
            'created_at': self.created_at,
            'created_amount': self.created_amount,
            'created_unit_price': self.created_unit_price,
            'created_total_value': self.created_total_value,
            'updated_at': self.updated_at,
            'updated_amount': self.updated_amount,
            'updated_unit_price': self.updated_unit_price,
            'updated_total_value': self.updated_total_value,
            'accumulation_plan': self.accumulation_plan,
            'accumulation_amount': self.accumulation_amount,
            'income_per_year': self.income_per_year,
            'rental_income': self.rental_income,
            'note': self.note
        }

class PortfolioManager:
    """
    Gestisce il portfolio e la persistenza dei dati in Excel
    
    Fornisce operazioni CRUD (Create, Read, Update, Delete) per gli asset
    e calcoli di sommario per il portfolio.
    
    Attributes:
        excel_file: Nome del file Excel per la persistenza
        categories: Lista delle categorie di asset supportate
    """
    
    def __init__(self, excel_file: str = "portfolio_data.xlsx"):
        """
        Inizializza il gestore del portfolio con validazione sicurezza

        Args:
            excel_file: Nome del file Excel da usare (default: portfolio_data.xlsx)
        """
        self.path_validator = PathSecurityValidator()
        self.logger = get_logger('PortfolioManager')

        # Valida il path del file in modo sicuro
        try:
            self.excel_file = str(self.path_validator.validate_portfolio_path(excel_file))
            self.logger.info(f"Path portfolio validato: {self.excel_file}")
        except SecurityError as e:
            self.logger.error(f"Path portfolio non sicuro: {e}")
            # Fallback su path sicuro di default
            self.excel_file = str(self.path_validator.create_safe_portfolio_path("portfolio_data.xlsx"))
            self.logger.warning(f"Usando path sicuro di fallback: {self.excel_file}")
        except Exception as e:
            self.logger.error(f"Errore validazione path: {e}")
            self.excel_file = excel_file  # Fallback senza validazione

        self.categories = [
            "ETF", "Azioni", "Fondi di investimento", "Buoni del Tesoro",
            "PAC", "Criptovalute", "Liquidità", "Immobiliare", "Oggetti"
        ]
        self._initialize_excel()
    
    def _initialize_excel(self):
        if not os.path.exists(self.excel_file):
            # Usa schema centralizzato per evitare disallineamenti
            from config import DatabaseConfig
            columns = DatabaseConfig.DB_COLUMNS
            df = pd.DataFrame(columns=columns)
            df.to_excel(self.excel_file, index=False)
    
    def load_data(self) -> pd.DataFrame:
        """Loader semplice e collaudato: legge il foglio attivo/default,
        pulisce solo le date e calcola i totali mancanti, senza rinomine aggressive."""
        try:
            df = pd.read_excel(self.excel_file, keep_default_na=False, na_values=[''])
            self.logger.debug(f"load_data: columns={list(df.columns)} rows={len(df)}")

            # Pulisce le date (rimuove l'ora se presente)
            for col in ['created_at', 'updated_at']:
                if col in df.columns:
                    df[col] = df[col].apply(self._clean_date_from_excel)

            # Calcola i totali se mancanti
            if 'created_total_value' in df.columns:
                mask = pd.isna(df['created_total_value'])
                df.loc[mask, 'created_total_value'] = df.loc[mask, 'created_amount'].fillna(0) * df.loc[mask, 'created_unit_price'].fillna(0)

            if 'updated_total_value' in df.columns:
                mask = pd.isna(df['updated_total_value'])
                df.loc[mask, 'updated_total_value'] = df.loc[mask, 'updated_amount'].fillna(0) * df.loc[mask, 'updated_unit_price'].fillna(0)

            return df
        except Exception as e:
            self.logger.error(f"Errore nel caricamento dati: {e}")
            return pd.DataFrame()
    
    def _clean_date_from_excel(self, date_value):
        """Pulisce le date caricate da Excel usando il sistema centralizzato"""
        try:
            date_manager = get_date_manager()
            result = date_manager.format_for_storage(date_value)
            return result if result else ""
        except Exception as e:
            self.logger.error(f"Errore pulizia data da Excel: {e}")
            return ""
    
    def save_data(self, df: pd.DataFrame):
        try:
            # Salva usando openpyxl per supportare le formule Excel
            self.save_data_with_formulas(df)
            return True
        except Exception as e:
            self.logger.error(f"Errore nel salvataggio dati: {e}")
            return False
    
    def save_data_with_formulas(self, df: pd.DataFrame):
        """Salva i dati con formule Excel per i calcoli automatici"""
        from openpyxl import Workbook
        from openpyxl.utils.dataframe import dataframe_to_rows
        from datetime import datetime
        
        # Crea copia del DataFrame e formatta le date come solo giorno
        df_clean = df.copy()
        
        # Converte le colonne date per rimuovere l'ora
        date_columns = ['created_at', 'updated_at']
        for col in date_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].apply(self._format_date_for_excel)
        
        # Crea workbook
        wb = Workbook()
        ws = wb.active
        
        # Inserisce i dati dal DataFrame pulito
        for r in dataframe_to_rows(df_clean, index=False, header=True):
            ws.append(r)
        
        # Trova le colonne dei valori totali
        header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        header_list = list(header_row)
        
        try:
            created_amount_idx = header_list.index('created_amount')
            created_price_idx = header_list.index('created_unit_price')
            created_total_idx = header_list.index('created_total_value')
            
            updated_amount_idx = header_list.index('updated_amount')
            updated_price_idx = header_list.index('updated_unit_price')
            updated_total_idx = header_list.index('updated_total_value')
            
            # Converti gli indici in lettere di colonna
            from openpyxl.utils import get_column_letter
            
            created_amount_col = get_column_letter(created_amount_idx + 1)
            created_price_col = get_column_letter(created_price_idx + 1)
            created_total_col = get_column_letter(created_total_idx + 1)
            
            updated_amount_col = get_column_letter(updated_amount_idx + 1)
            updated_price_col = get_column_letter(updated_price_idx + 1)
            updated_total_col = get_column_letter(updated_total_idx + 1)
            
            # Applica le formule a tutte le righe (dalla riga 2 in poi)
            for row in range(2, ws.max_row + 1):
                # Formula per Valore Totale Iniziale = Quantità * Prezzo Unitario
                formula1 = f'={created_amount_col}{row}*{created_price_col}{row}'
                ws[f'{created_total_col}{row}'] = formula1
                
                # Formula per Valore Totale Attuale = Quantità * Prezzo Unitario
                formula2 = f'={updated_amount_col}{row}*{updated_price_col}{row}'
                ws[f'{updated_total_col}{row}'] = formula2
                
        except (ValueError, IndexError) as e:
            self.logger.error(f"Errore nell'applicazione delle formule: {e}")
        
        # Salva il file
        wb.save(self.excel_file)
    
    def _format_date_for_excel(self, date_value):
        """Formatta le date per Excel usando il sistema centralizzato"""
        try:
            date_manager = get_date_manager()
            return date_manager.format_for_excel(date_value)
        except Exception as e:
            self.logger.error(f"Errore formattazione data per Excel: {e}")
            # Fallback per compatibilità
            if pd.isna(date_value) or date_value == "" or date_value is None:
                return None
            date_str = str(date_value)
            return date_str.split()[0] if " " in date_str else date_str
    
    def add_asset(self, asset: Asset) -> bool:
        """
        Aggiunge un nuovo asset al portfolio
        
        Args:
            asset: Oggetto Asset da aggiungere
            
        Returns:
            True se il salvataggio è riuscito, False altrimenti
        """
        df = self.load_data()
        
        # Assegna ID automatico se non specificato
        if asset.id is None:
            asset.id = len(df) + 1 if not df.empty else 1
        
        # Assegna data corrente se non specificata usando sistema centralizzato
        if asset.created_at == "":
            from date_utils import get_today_formatted
            asset.created_at = get_today_formatted('storage')
        
        # Aggiunge l'asset al DataFrame
        new_row = pd.DataFrame([asset.to_dict()])
        df = pd.concat([df, new_row], ignore_index=True)
        
        return self.save_data(df)
    
    def update_asset(self, asset_id: int, updated_data: Dict[str, Any]) -> bool:
        df = self.load_data()
        
        if asset_id not in df['id'].values:
            return False
        
        # Non forzare la data di aggiornamento - viene gestita dal chiamante
        
        for key, value in updated_data.items():
            df.loc[df['id'] == asset_id, key] = value
        
        return self.save_data(df)
    
    def delete_asset(self, asset_id: int) -> bool:
        df = self.load_data()
        
        if asset_id not in df['id'].values:
            return False
        
        df = df[df['id'] != asset_id]
        return self.save_data(df)
    
    def get_asset(self, asset_id: int) -> Optional[Asset]:
        df = self.load_data()
        
        if asset_id not in df['id'].values:
            return None
        
        row = df[df['id'] == asset_id].iloc[0]
        return Asset(
            asset_id=row['id'],
            category=row['category'],
            asset_name=row['asset_name'],
            position=row['position'],
            risk_level=row['risk_level'],
            ticker=row['ticker'],
            isin=row['isin'],
            created_at=row['created_at'],
            created_amount=row['created_amount'],
            created_unit_price=row['created_unit_price'],
            created_total_value=row['created_total_value'],
            updated_at=row['updated_at'],
            updated_amount=row['updated_amount'],
            updated_unit_price=row['updated_unit_price'],
            updated_total_value=row['updated_total_value'],
            accumulation_plan=row['accumulation_plan'],
            accumulation_amount=row['accumulation_amount'],
            income_per_year=row['income_per_year'],
            rental_income=row['rental_income'],
            note=row['note']
        )
    
    def get_assets_by_category(self, category: str) -> List[Asset]:
        df = self.load_data()
        filtered_df = df[df['category'] == category]
        
        assets = []
        for _, row in filtered_df.iterrows():
            assets.append(Asset(
                asset_id=row['id'],
                category=row['category'],
                asset_name=row['asset_name'],
                position=row['position'],
                risk_level=row['risk_level'],
                ticker=row['ticker'],
                isin=row['isin'],
                created_at=row['created_at'],
                created_amount=row['created_amount'],
                created_unit_price=row['created_unit_price'],
                created_total_value=row['created_total_value'],
                updated_at=row['updated_at'],
                updated_amount=row['updated_amount'],
                updated_unit_price=row['updated_unit_price'],
                updated_total_value=row['updated_total_value'],
                accumulation_plan=row['accumulation_plan'],
                accumulation_amount=row['accumulation_amount'],
                income_per_year=row['income_per_year'],
                rental_income=row['rental_income'],
                note=row['note']
            ))
        
        return assets
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        df = self.load_data()
        
        if df.empty:
            return {
                'total_value': 0,
                'total_income': 0,
                'categories_count': {},
                'risk_distribution': {},
                'monthly_accumulation': 0
            }
        
        # NUOVA LOGICA: Considera solo record più recenti per ogni asset unico
        # Asset identificato da: category + asset_name + position + isin
        
        # Crea colonna per identificare univocamente ogni asset
        df['asset_key'] = (df['category'].fillna('') + '|' + 
                          df['asset_name'].fillna('') + '|' + 
                          df['position'].fillna('') + '|' + 
                          df['isin'].fillna(''))
        
        # Converte date per ordinamento (usa updated_at se disponibile, altrimenti created_at)
        df['effective_date'] = pd.to_datetime(df['updated_at'].fillna(df['created_at']), 
                                            format='%Y-%m-%d', errors='coerce')
        
        # Per ogni asset unico, prende solo il record con data più recente
        latest_records = df.sort_values('effective_date', ascending=False).groupby('asset_key').first().reset_index()
        
        # Calcola i totali sui record più recenti
        total_value = latest_records['updated_total_value'].fillna(latest_records['created_total_value']).sum()
        total_income = (latest_records['income_per_year'].fillna(0).sum() + 
                       latest_records['rental_income'].fillna(0).sum())
        categories_count = latest_records['category'].value_counts().to_dict()
        risk_distribution = latest_records['risk_level'].value_counts().to_dict()
        monthly_accumulation = latest_records['accumulation_amount'].fillna(0).sum()
        
        return {
            'total_value': total_value,
            'total_income': total_income,
            'categories_count': categories_count,
            'risk_distribution': risk_distribution,
            'monthly_accumulation': monthly_accumulation
        }
    
    def get_current_assets_only(self):
        """
        Ritorna solo gli asset più recenti (un record per asset unico)
        """
        df = self.load_data()
        if df.empty:
            return df

        # Normalizza campi chiave per deduplica
        def _norm(s):
            if pd.isna(s):
                return ''
            val = str(s).strip()
            if val.lower() in {'na','n/a','none','null','nan',''}:
                return ''
            return val
        for key_col in ['category','asset_name','position','isin']:
            if key_col in df.columns:
                df[key_col] = df[key_col].apply(_norm)
            else:
                df[key_col] = ''

        df['asset_key'] = (df['category'] + '|' + df['asset_name'] + '|' + df['position'] + '|' + df['isin'])

        # Ordina per data effettiva (updated_at preferito), poi prendi il primo per asset_key
        df['effective_date'] = pd.to_datetime(
            df['updated_at'].replace(['', 'NA', 'N/A', 'na'], pd.NA).fillna(df['created_at']),
            format='%Y-%m-%d', errors='coerce'
        )

        df['original_order'] = df.index
        latest_records = df.sort_values(['effective_date','original_order'], ascending=[False, True])\
                           .groupby('asset_key').first().reset_index()
        latest_records = latest_records.sort_values('original_order')
        latest_records = latest_records.drop(columns=[c for c in ['asset_key','effective_date','original_order'] if c in latest_records.columns])

        self.logger.debug(f"current_assets_only: input_rows={len(df)} output_rows={len(latest_records)}")
        return latest_records
    
    def get_filtered_assets(self, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Ritorna gli asset filtrati secondo i criteri specificati
        
        Args:
            filters: Dizionario con i filtri da applicare
                    {
                        'category': str | None,
                        'position': str | None, 
                        'risk_level': List[int] | None,
                        'value_range': (min, max) | None,
                        'name_search': str | None
                    }
        """
        df = self.get_current_assets_only()
        
        if df.empty or not filters:
            return df
        
        # Filtro per categoria
        if filters.get('category') and filters['category'] != 'All':
            df = df[df['category'] == filters['category']]
        
        # Filtro per posizione (contiene testo)
        if filters.get('position'):
            position_text = filters['position'].lower()
            df = df[df['position'].fillna('').str.lower().str.contains(position_text, na=False)]
        
        # Filtro per livello di rischio
        if filters.get('risk_level'):
            df = df[df['risk_level'].isin(filters['risk_level'])]
        
        # Filtro per range di valore
        if filters.get('value_range'):
            min_val, max_val = filters['value_range']
            # Usa updated_total_value se disponibile, altrimenti created_total_value
            df['current_value'] = df['updated_total_value'].fillna(df['created_total_value'])
            if min_val is not None:
                df = df[df['current_value'] >= min_val]
            if max_val is not None:
                df = df[df['current_value'] <= max_val]
            df = df.drop('current_value', axis=1)
        
        # Filtro per nome asset (contiene testo)
        if filters.get('name_search'):
            name_text = filters['name_search'].lower()
            df = df[df['asset_name'].fillna('').str.lower().str.contains(name_text, na=False)]
        
        return df
    
    def get_unique_positions(self) -> List[str]:
        """Ritorna tutte le posizioni uniche nel portfolio"""
        df = self.get_current_assets_only()
        positions = df['position'].fillna('').unique()
        return [pos for pos in positions if pos != '']
    
    def color_historical_records(self):
        """
        Colora i record storici di azzurro direttamente nel file Excel.
        I record storici sono quelli non più attuali per un dato asset.
        """
        try:
            from openpyxl import load_workbook
            from openpyxl.styles import Font
        except ImportError:
            self.logger.error("openpyxl non disponibile. Installa con: pip install openpyxl")
            return
        
        try:
            # Carica tutti i dati per identificare i record storici
            df = self.load_data()
            if df.empty:
                return
            
            # Identifica gli asset correnti
            current_df = self.get_current_assets_only()
            current_ids = set(current_df['id'].astype(int))
            
            # Record storici sono quelli non nell'insieme degli attuali
            historical_ids = set(df['id'].astype(int)) - current_ids
            
            self.logger.info(f"Record storici da colorare: {len(historical_ids)}")
            self.logger.info(f"Record attuali: {len(current_ids)}")
            
            # Apri il file Excel con openpyxl
            wb = load_workbook(self.excel_file)
            ws = wb.active
            
            # Definisci il colore azzurro per il testo
            blue_font = Font(color="0066CC")  # Azzurro
            
            # Itera sulle righe (skip header row 1)
            for row_idx in range(2, ws.max_row + 1):
                # La colonna A contiene l'ID (primo valore)
                id_cell = ws.cell(row=row_idx, column=1)
                
                try:
                    record_id = int(id_cell.value)
                    
                    # Se è un record storico, colora tutta la riga di azzurro
                    if record_id in historical_ids:
                        for col_idx in range(1, ws.max_column + 1):
                            cell = ws.cell(row=row_idx, column=col_idx)
                            cell.font = blue_font
                except (ValueError, TypeError):
                    # Se l'ID non è convertibile, skip
                    continue
            
            # Salva il file
            wb.save(self.excel_file)
            self.logger.info(f"File Excel aggiornato con {len(historical_ids)} record storici colorati di azzurro")
            
        except Exception as e:
            self.logger.error(f"Errore nella colorazione dei record storici: {e}")
            import traceback
            self.logger.debug(f"Stack trace: {traceback.format_exc()}")
