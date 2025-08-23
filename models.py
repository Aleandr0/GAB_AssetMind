import pandas as pd
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

class Asset:
    def __init__(self, asset_id: int = None, category: str = "", asset_name: str = "", 
                 position: float = 0.0, risk_level: int = 1, ticker: str = "", 
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
            'Id': self.id,
            'category': self.category,
            'assetName': self.asset_name,
            'position': self.position,
            'riskLevel': self.risk_level,
            'ticker': self.ticker,
            'isin': self.isin,
            'createdAt': self.created_at,
            'createdAmount': self.created_amount,
            'createdUnitPrice': self.created_unit_price,
            'createdTotalValue': self.created_total_value,
            'updatedAt': self.updated_at,
            'updatedAmount': self.updated_amount,
            'updatedUnitPrice': self.updated_unit_price,
            'updatedTotalValue': self.updated_total_value,
            'accumulationPlan': self.accumulation_plan,
            'accumulationAmount': self.accumulation_amount,
            'incomePerYear': self.income_per_year,
            'rentalIncome': self.rental_income,
            'note': self.note
        }

class PortfolioManager:
    def __init__(self, excel_file: str = "portfolio_data.xlsx"):
        self.excel_file = excel_file
        self.categories = [
            "ETF", "Azioni", "Obbligazioni", "Buoni del Tesoro", 
            "PAC", "Criptovalute", "Liquidità", "Immobiliare", "Oggetti"
        ]
        self._initialize_excel()
    
    def _initialize_excel(self):
        if not os.path.exists(self.excel_file):
            columns = [
                'Id', 'category', 'assetName', 'position', 'riskLevel', 'ticker', 'isin',
                'createdAt', 'createdAmount', 'createdUnitPrice', 'createdTotalValue',
                'updatedAt', 'updatedAmount', 'updatedUnitPrice', 'updatedTotalValue',
                'accumulationPlan', 'accumulationAmount', 'incomePerYear', 'rentalIncome', 'note'
            ]
            df = pd.DataFrame(columns=columns)
            df.to_excel(self.excel_file, index=False)
    
    def load_data(self) -> pd.DataFrame:
        try:
            return pd.read_excel(self.excel_file)
        except Exception as e:
            print(f"Errore nel caricamento dati: {e}")
            return pd.DataFrame()
    
    def save_data(self, df: pd.DataFrame):
        try:
            df.to_excel(self.excel_file, index=False)
            return True
        except Exception as e:
            print(f"Errore nel salvataggio dati: {e}")
            return False
    
    def add_asset(self, asset: Asset) -> bool:
        print(f"DEBUG models.py: add_asset chiamato con asset: {asset.asset_name}")
        df = self.load_data()
        print(f"DEBUG models.py: df caricato, righe: {len(df)}")
        
        if asset.id is None:
            asset.id = len(df) + 1 if not df.empty else 1
            print(f"DEBUG models.py: nuovo ID assegnato: {asset.id}")
        
        if asset.created_at == "":
            asset.created_at = datetime.now().strftime("%Y-%m-%d")
            print(f"DEBUG models.py: data creazione: {asset.created_at}")
        
        new_row = pd.DataFrame([asset.to_dict()])
        print(f"DEBUG models.py: nuova riga creata: {new_row}")
        df = pd.concat([df, new_row], ignore_index=True)
        print(f"DEBUG models.py: df dopo concat, righe: {len(df)}")
        
        result = self.save_data(df)
        print(f"DEBUG models.py: salvataggio risultato: {result}")
        return result
    
    def update_asset(self, asset_id: int, updated_data: Dict[str, Any]) -> bool:
        df = self.load_data()
        
        if asset_id not in df['Id'].values:
            return False
        
        updated_data['updatedAt'] = datetime.now().strftime("%Y-%m-%d")
        
        for key, value in updated_data.items():
            df.loc[df['Id'] == asset_id, key] = value
        
        return self.save_data(df)
    
    def delete_asset(self, asset_id: int) -> bool:
        df = self.load_data()
        
        if asset_id not in df['Id'].values:
            return False
        
        df = df[df['Id'] != asset_id]
        return self.save_data(df)
    
    def get_asset(self, asset_id: int) -> Optional[Asset]:
        df = self.load_data()
        
        if asset_id not in df['Id'].values:
            return None
        
        row = df[df['Id'] == asset_id].iloc[0]
        return Asset(
            asset_id=row['Id'],
            category=row['category'],
            asset_name=row['assetName'],
            position=row['position'],
            risk_level=row['riskLevel'],
            ticker=row['ticker'],
            isin=row['isin'],
            created_at=row['createdAt'],
            created_amount=row['createdAmount'],
            created_unit_price=row['createdUnitPrice'],
            created_total_value=row['createdTotalValue'],
            updated_at=row['updatedAt'],
            updated_amount=row['updatedAmount'],
            updated_unit_price=row['updatedUnitPrice'],
            updated_total_value=row['updatedTotalValue'],
            accumulation_plan=row['accumulationPlan'],
            accumulation_amount=row['accumulationAmount'],
            income_per_year=row['incomePerYear'],
            rental_income=row['rentalIncome'],
            note=row['note']
        )
    
    def get_assets_by_category(self, category: str) -> List[Asset]:
        df = self.load_data()
        filtered_df = df[df['category'] == category]
        
        assets = []
        for _, row in filtered_df.iterrows():
            assets.append(Asset(
                asset_id=row['Id'],
                category=row['category'],
                asset_name=row['assetName'],
                position=row['position'],
                risk_level=row['riskLevel'],
                ticker=row['ticker'],
                isin=row['isin'],
                created_at=row['createdAt'],
                created_amount=row['createdAmount'],
                created_unit_price=row['createdUnitPrice'],
                created_total_value=row['createdTotalValue'],
                updated_at=row['updatedAt'],
                updated_amount=row['updatedAmount'],
                updated_unit_price=row['updatedUnitPrice'],
                updated_total_value=row['updatedTotalValue'],
                accumulation_plan=row['accumulationPlan'],
                accumulation_amount=row['accumulationAmount'],
                income_per_year=row['incomePerYear'],
                rental_income=row['rentalIncome'],
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
        
        total_value = df['updatedTotalValue'].fillna(df['createdTotalValue']).sum()
        total_income = df['incomePerYear'].fillna(0).sum() + df['rentalIncome'].fillna(0).sum()
        categories_count = df['category'].value_counts().to_dict()
        risk_distribution = df['riskLevel'].value_counts().to_dict()
        monthly_accumulation = df['accumulationAmount'].fillna(0).sum()
        
        return {
            'total_value': total_value,
            'total_income': total_income,
            'categories_count': categories_count,
            'risk_distribution': risk_distribution,
            'monthly_accumulation': monthly_accumulation
        }