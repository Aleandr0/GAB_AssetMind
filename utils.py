#!/usr/bin/env python3
"""
Utilità e funzioni helper per GAB AssetMind
Contiene funzioni di supporto per validazione, formattazione e gestione errori
"""

import pandas as pd
import re
from datetime import datetime
from typing import Any, Optional, Union, List, Dict
from config import ValidationConfig, FieldMapping

class DataValidator:
    """Validatore per dati di input degli asset"""
    
    @staticmethod
    def is_empty(value: Any) -> bool:
        """Verifica se un valore è considerato vuoto"""
        if value is None or pd.isna(value):
            return True
        
        value_str = str(value).lower().strip()
        return value_str in ValidationConfig.EMPTY_VALUES or value_str == ''
    
    @staticmethod
    def clean_value(value: Any) -> str:
        """Pulisce un valore convertendolo in stringa utilizzabile"""
        if DataValidator.is_empty(value):
            return ""
        return str(value).strip()
    
    @staticmethod
    def validate_numeric(value: Any, field_name: str) -> float:
        """Valida e converte un valore numerico"""
        if DataValidator.is_empty(value):
            return 0.0
            
        try:
            # Rimuove formattazione valuta se presente
            if isinstance(value, str):
                cleaned = value.replace('€', '').replace(',', '').replace('.', '', -1)
                if '.' in cleaned:
                    cleaned = cleaned.replace('.', '', cleaned.count('.') - 1)
                numeric_value = float(cleaned)
            else:
                numeric_value = float(value)
            
            # Verifica range se definito
            if field_name in ValidationConfig.RANGES:
                min_val, max_val = ValidationConfig.RANGES[field_name]
                if not (min_val <= numeric_value <= max_val):
                    raise ValueError(f"{field_name} deve essere tra {min_val} e {max_val}")
            
            return numeric_value
            
        except (ValueError, TypeError) as e:
            raise ValueError(f"Valore non valido per {field_name}: {value}")
    
    @staticmethod
    def validate_date(date_value: Any) -> str:
        """Valida e formatta una data"""
        if DataValidator.is_empty(date_value):
            return ""
            
        date_str = str(date_value).strip()
        
        # Verifica formato YYYY-MM-DD
        if re.match(ValidationConfig.PATTERNS['date'], date_str):
            return date_str
            
        # Prova a parsare altri formati comuni
        try:
            if '/' in date_str and len(date_str) == 10:
                # Formato DD/MM/YYYY -> YYYY-MM-DD
                parsed = datetime.strptime(date_str, "%d/%m/%Y")
                return parsed.strftime("%Y-%m-%d")
            elif '-' in date_str:
                # Altri formati con trattini
                parsed = pd.to_datetime(date_str)
                return parsed.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass
            
        raise ValueError(f"Formato data non valido: {date_value}")
    
    @staticmethod
    def validate_isin(isin: str) -> str:
        """Valida un codice ISIN"""
        if DataValidator.is_empty(isin):
            return ""
            
        isin = isin.upper().strip()
        if not re.match(ValidationConfig.PATTERNS['isin'], isin):
            raise ValueError(f"Formato ISIN non valido: {isin}")
        
        return isin

class DateFormatter:
    """Utilità per formattazione date"""
    
    @staticmethod
    def format_for_display(date_value: Any) -> str:
        """Formatta una data per la visualizzazione (DD/MM/YYYY)"""
        if DataValidator.is_empty(date_value):
            return "-"
            
        try:
            date_str = str(date_value).strip()
            
            # Se è già in formato YYYY-MM-DD
            if re.match(r'^\d{4}-\d{2}-\d{2}', date_str):
                parsed = datetime.strptime(date_str[:10], "%Y-%m-%d")
                return parsed.strftime("%d/%m/%Y")
                
            # Se è un timestamp pandas
            if isinstance(date_value, pd.Timestamp):
                return date_value.strftime("%d/%m/%Y")
                
            # Altri formati
            parsed = pd.to_datetime(date_value)
            return parsed.strftime("%d/%m/%Y")
            
        except (ValueError, TypeError):
            # Se non riesce a parsare, rimuove eventuale ora
            if " " in str(date_value):
                return str(date_value).split()[0]
            return str(date_value)
    
    @staticmethod 
    def format_for_form(date_value: Any) -> str:
        """Formatta una data per l'inserimento nel form (YYYY-MM-DD)"""
        if DataValidator.is_empty(date_value):
            return ""
            
        try:
            date_str = str(date_value).strip()
            
            # Formato DD/MM/YYYY -> YYYY-MM-DD
            if "/" in date_str and len(date_str) == 10:
                parsed = datetime.strptime(date_str, "%d/%m/%Y")
                return parsed.strftime("%Y-%m-%d")
            # Formato YYYY-MM-DD (già corretto)
            elif "-" in date_str:
                return date_str[:10]  # Rimuove eventuale ora
            else:
                return date_str
                
        except ValueError:
            return str(date_value)
    
    @staticmethod
    def format_for_excel(date_value: Any) -> Optional[str]:
        """Formatta una data per Excel (YYYY-MM-DD)"""
        if DataValidator.is_empty(date_value):
            return None
            
        try:
            date_str = str(date_value)
            if "-" in date_str and len(date_str.split()[0]) == 10:
                return date_str.split()[0]  # Rimuove eventuale ora
            
            if isinstance(date_value, pd.Timestamp):
                return date_value.strftime("%Y-%m-%d")
            
            parsed = pd.to_datetime(date_value)
            return parsed.strftime("%Y-%m-%d")
            
        except (ValueError, TypeError):
            return str(date_value).split()[0] if " " in str(date_value) else str(date_value)

class CurrencyFormatter:
    """Utilità per formattazione valuta"""
    
    @staticmethod
    def format_for_display(value: Any) -> str:
        """Formatta un valore per la visualizzazione con €"""
        try:
            if DataValidator.is_empty(value):
                return "€0.00"
                
            numeric_value = float(str(value).replace('€', '').replace(',', ''))
            return f"€{numeric_value:,.2f}"
            
        except (ValueError, TypeError):
            return str(value) if value else "€0.00"
    
    @staticmethod
    def parse_from_display(value: str) -> float:
        """Converte un valore formattato in float"""
        if DataValidator.is_empty(value):
            return 0.0
            
        try:
            # Rimuove simboli di formattazione
            cleaned = str(value).replace('€', '').replace(',', '').strip()
            return float(cleaned) if cleaned else 0.0
        except (ValueError, TypeError):
            return 0.0

class ErrorHandler:
    """Gestione centralizzata degli errori"""
    
    @staticmethod
    def handle_file_error(error: Exception, file_path: str) -> str:
        """Gestisce errori di file"""
        if isinstance(error, FileNotFoundError):
            return f"File non trovato: {file_path}"
        elif isinstance(error, PermissionError):
            return f"Permessi insufficienti per accedere al file: {file_path}"
        elif isinstance(error, pd.errors.ExcelFileError):
            return f"File Excel corrotto o non valido: {file_path}"
        else:
            return f"Errore nell'accesso al file {file_path}: {error}"
    
    @staticmethod
    def handle_data_error(error: Exception, context: str = "") -> str:
        """Gestisce errori di dati"""
        if isinstance(error, ValueError):
            return f"Errore nei dati{' (' + context + ')' if context else ''}: {error}"
        elif isinstance(error, KeyError):
            return f"Campo mancante{' (' + context + ')' if context else ''}: {error}"
        elif isinstance(error, TypeError):
            return f"Tipo di dato non valido{' (' + context + ')' if context else ''}: {error}"
        else:
            return f"Errore nei dati{' (' + context + ')' if context else ''}: {error}"
    
    @staticmethod
    def handle_ui_error(error: Exception, component: str = "") -> str:
        """Gestisce errori dell'interfaccia utente"""
        component_text = f" nel componente {component}" if component else ""
        return f"Errore nell'interfaccia{component_text}: {error}"

class DataCache:
    """Cache semplice per ottimizzazione performance"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._ttl: int = 300  # 5 minuti di TTL
    
    def get(self, key: str) -> Optional[Any]:
        """Recupera un valore dalla cache"""
        if key not in self._cache:
            return None
            
        # Verifica TTL
        if key in self._timestamps:
            age = (datetime.now() - self._timestamps[key]).total_seconds()
            if age > self._ttl:
                self.invalidate(key)
                return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Imposta un valore nella cache"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
    
    def invalidate(self, key: str) -> None:
        """Invalida un elemento della cache"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Pulisce tutta la cache"""
        self._cache.clear()
        self._timestamps.clear()

class FieldUtils:
    """Utilità per gestione campi"""
    
    @staticmethod
    def get_display_name(db_field: str) -> str:
        """Converte un nome campo database in nome display"""
        return FieldMapping.DB_TO_DISPLAY.get(db_field, db_field)
    
    @staticmethod
    def get_db_name(display_field: str) -> str:
        """Converte un nome campo display in nome database"""
        return FieldMapping.DISPLAY_TO_DB.get(display_field, display_field)
    
    @staticmethod
    def is_monetary_field(field_name: str) -> bool:
        """Verifica se un campo è monetario"""
        return field_name in FieldMapping.MONETARY_FIELDS
    
    @staticmethod
    def is_date_field(field_name: str) -> bool:
        """Verifica se un campo è una data"""
        return field_name in FieldMapping.DATE_FIELDS
    
    @staticmethod
    def is_numeric_field(field_name: str) -> bool:
        """Verifica se un campo è numerico"""
        return field_name in FieldMapping.NUMERIC_FIELDS

def safe_execute(func, default_value=None, error_handler=None):
    """Esegue una funzione in modo sicuro gestendo le eccezioni"""
    try:
        return func()
    except Exception as e:
        if error_handler:
            error_handler(e)
        return default_value