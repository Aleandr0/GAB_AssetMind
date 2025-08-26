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
            'riskLevel': self.risk_level,
            'ticker': self.ticker,
            'isin': self.isin,
            'createdAt': self.created_at,
            'createdAmount': self.created_amount,
            'created_unit_price': self.created_unit_price,
            'created_total_value': self.created_total_value,
            'updatedAt': self.updated_at,
            'updatedAmount': self.updated_amount,
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
        Inizializza il gestore del portfolio
        
        Args:
            excel_file: Nome del file Excel da usare (default: portfolio_data.xlsx)
        """
        self.excel_file = excel_file
        self.categories = [
            "ETF", "Azioni", "Fondi di investimento", "Buoni del Tesoro", 
            "PAC", "Criptovalute", "Liquidità", "Immobiliare", "Oggetti"
        ]
        self._initialize_excel()
    
    def _initialize_excel(self):
        if not os.path.exists(self.excel_file):
            columns = [
                'id', 'category', 'asset_name', 'position', 'risk_level', 'ticker', 'isin',
                'createdAt', 'createdAmount', 'createdUnitPrice', 'createdTotalValue',
                'updatedAt', 'updatedAmount', 'updatedUnitPrice', 'updatedTotalValue',
                'accumulation_plan', 'accumulation_amount', 'income_per_year', 'rental_income', 'note'
            ]
            df = pd.DataFrame(columns=columns)
            df.to_excel(self.excel_file, index=False)
    
    def load_data(self) -> pd.DataFrame:
        try:
            df = pd.read_excel(self.excel_file)
            
            # Formatta le date per rimuovere l'ora durante il caricamento
            date_columns = ['created_at', 'updated_at']
            for col in date_columns:
                if col in df.columns:
                    df[col] = df[col].apply(self._clean_date_from_excel)
            
            return df
        except Exception as e:
            print(f"Errore nel caricamento dati: {e}")
            return pd.DataFrame()
    
    def _clean_date_from_excel(self, date_value):
        """Pulisce le date caricate da Excel rimuovendo l'ora"""
        if pd.isna(date_value) or date_value == "":
            return date_value
            
        try:
            # Se è un Timestamp pandas, convertilo solo alla data
            if isinstance(date_value, pd.Timestamp):
                return date_value.strftime("%Y-%m-%d")
            
            # Se è già una stringa, rimuovi eventuale ora
            date_str = str(date_value)
            if " " in date_str:
                return date_str.split()[0]
            
            return date_str
            
        except (ValueError, TypeError):
            return date_value
    
    def save_data(self, df: pd.DataFrame):
        try:
            # Salva usando openpyxl per supportare le formule Excel
            self.save_data_with_formulas(df)
            return True
        except Exception as e:
            print(f"Errore nel salvataggio dati: {e}")
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
            print(f"Errore nell'applicazione delle formule: {e}")
        
        # Salva il file
        wb.save(self.excel_file)
    
    def _format_date_for_excel(self, date_value):
        """Formatta le date per Excel (solo giorno, no ora)"""
        if pd.isna(date_value) or date_value == "" or date_value is None:
            return None
            
        try:
            from datetime import datetime
            
            # Se è già una stringa in formato YYYY-MM-DD, mantienila
            date_str = str(date_value)
            if "-" in date_str and len(date_str.split()[0]) == 10:
                return date_str.split()[0]  # Rimuove eventuale ora
            
            # Se è un timestamp pandas, convertilo
            if isinstance(date_value, pd.Timestamp):
                return date_value.strftime("%Y-%m-%d")
            
            # Prova parsing generale
            parsed_date = pd.to_datetime(date_value)
            return parsed_date.strftime("%Y-%m-%d")
            
        except (ValueError, TypeError):
            return str(date_value).split()[0] if " " in str(date_value) else str(date_value)
    
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
        
        # Assegna data corrente se non specificata
        if asset.created_at == "":
            asset.created_at = datetime.now().strftime("%Y-%m-%d")
        
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
        
        # Converte date per ordinamento (usa updatedAt se disponibile, altrimenti createdAt)
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
        Ritorna solo gli asset più recenti (un record per ogni asset unico)
        Utile per verificare la logica di deduplica
        """
        df = self.load_data()
        
        if df.empty:
            return df
        
        # Crea chiave univoca per ogni asset
        df['asset_key'] = (df['category'].fillna('') + '|' + 
                          df['asset_name'].fillna('') + '|' + 
                          df['position'].fillna('') + '|' + 
                          df['isin'].fillna(''))
        
        # Converte date per ordinamento
        df['effective_date'] = pd.to_datetime(df['updated_at'].fillna(df['created_at']), 
                                            format='%Y-%m-%d', errors='coerce')
        
        # Prende solo il record più recente per ogni asset
        latest_records = df.sort_values('effective_date', ascending=False).groupby('asset_key').first().reset_index()
        
        # Rimuove le colonne helper
        latest_records = latest_records.drop(['asset_key', 'effective_date'], axis=1)
        
        # Ordina per ID per mantenere l'ordine di inserimento
        latest_records = latest_records.sort_values('id').reset_index(drop=True)
        
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