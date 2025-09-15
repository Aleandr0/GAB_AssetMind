#!/usr/bin/env python3
"""
Utilità centralizzate per gestione date in GAB AssetMind
Consolida tutto il parsing, formatting e validazione delle date in un unico modulo
"""

import pandas as pd
import re
from datetime import datetime, date
from typing import Union, Optional, Any, List
from logging_config import get_logger

class DateParseError(Exception):
    """Eccezione per errori di parsing delle date"""
    pass

class CentralizedDateManager:
    """
    Manager centralizzato per tutte le operazioni sulle date

    Responsabilità:
    - Parsing unificato da diverse fonti (Excel, input utente, stringhe)
    - Formatting consistente per display e storage
    - Validazione date con range ragionevoli
    - Conversioni sicure tra formati
    - Logging dettagliato per debug
    """

    def __init__(self):
        self.logger = get_logger('DateManager')

        # Formati date supportati in ordine di priorità
        self.supported_formats = [
            '%Y-%m-%d',           # ISO format (preferito per storage)
            '%d/%m/%Y',           # European format (display)
            '%m/%d/%Y',           # US format
            '%Y/%m/%d',           # Alternative ISO
            '%d-%m-%Y',           # European with dashes
            '%m-%d-%Y',           # US with dashes
            '%d.%m.%Y',           # European with dots
            '%Y%m%d',             # Compact format
        ]

        # Range date ragionevoli per validazione
        self.min_year = 1980  # Esteso per includere date più vecchie
        self.max_year = 2050

        # Pattern regex per validazione rapida
        self.date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',           # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',           # DD/MM/YYYY or MM/DD/YYYY
            r'^\d{4}/\d{2}/\d{2}$',           # YYYY/MM/DD
            r'^\d{2}-\d{2}-\d{4}$',           # DD-MM-YYYY or MM-DD-YYYY
            r'^\d{2}\.\d{2}\.\d{4}$',         # DD.MM.YYYY
            r'^\d{8}$',                       # YYYYMMDD
        ]

    def parse_date(self, date_input: Any, strict: bool = False) -> Optional[datetime]:
        """
        Parsing universale di date da qualsiasi fonte

        Args:
            date_input: Input data (str, datetime, pandas.Timestamp, etc.)
            strict: Se True, solleva eccezione su errore instead di None

        Returns:
            datetime object o None se parsing fallisce

        Raises:
            DateParseError: Se strict=True e parsing fallisce
        """
        if date_input is None or pd.isna(date_input):
            return None

        try:
            # Caso 1: È già un datetime
            if isinstance(date_input, (datetime, date)):
                return self._validate_date_range(date_input)

            # Caso 2: È un pandas.Timestamp
            if isinstance(date_input, pd.Timestamp):
                return self._validate_date_range(date_input.to_pydatetime())

            # Caso 3: Conversione da stringa
            date_str = str(date_input).strip()

            # Controllo rapido per valori vuoti/nulli comuni
            if self._is_empty_date(date_str):
                return None

            # Pulizia stringa
            cleaned_date = self._clean_date_string(date_str)

            # Tentativo parsing con formati standard
            parsed_date = self._try_parse_formats(cleaned_date)

            if parsed_date:
                return self._validate_date_range(parsed_date)

            # Tentativo parsing con pandas (più flessibile ma lento)
            if not strict:
                try:
                    parsed_pandas = pd.to_datetime(cleaned_date, infer_datetime_format=True)
                    return self._validate_date_range(parsed_pandas.to_pydatetime())
                except:
                    pass

            # Se arriviamo qui, parsing fallito
            if strict:
                raise DateParseError(f"Impossibile parsare la data: {date_input}")

            self.logger.debug(f"Parsing fallito per data: {date_input}")
            return None

        except DateParseError:
            raise  # Re-raise se strict
        except Exception as e:
            self.logger.error(f"Errore inatteso parsing data {date_input}: {e}")
            if strict:
                raise DateParseError(f"Errore parsing data: {e}")
            return None

    def format_for_display(self, date_input: Any, format_type: str = 'european') -> str:
        """
        Formatta una data per visualizzazione nell'interfaccia

        Args:
            date_input: Input data
            format_type: 'european' (DD/MM/YYYY) o 'iso' (YYYY-MM-DD) o 'us' (MM/DD/YYYY)

        Returns:
            Stringa formattata o placeholder se parsing fallisce
        """
        try:
            parsed_date = self.parse_date(date_input)
            if not parsed_date:
                return "-"

            format_mapping = {
                'european': '%d/%m/%Y',
                'iso': '%Y-%m-%d',
                'us': '%m/%d/%Y',
                'compact': '%d%m%Y'
            }

            date_format = format_mapping.get(format_type, '%d/%m/%Y')
            return parsed_date.strftime(date_format)

        except Exception as e:
            self.logger.error(f"Errore formatting data per display: {e}")
            return str(date_input) if date_input else "-"

    def format_for_storage(self, date_input: Any) -> Optional[str]:
        """
        Formatta una data per storage nel database (formato ISO)

        Args:
            date_input: Input data

        Returns:
            Stringa ISO (YYYY-MM-DD) o None se parsing fallisce
        """
        try:
            parsed_date = self.parse_date(date_input)
            if not parsed_date:
                return None

            return parsed_date.strftime('%Y-%m-%d')

        except Exception as e:
            self.logger.error(f"Errore formatting data per storage: {e}")
            return None

    def format_for_excel(self, date_input: Any) -> Optional[str]:
        """
        Formatta una data per Excel (compatibilità)

        Args:
            date_input: Input data

        Returns:
            Stringa formato Excel o None se parsing fallisce
        """
        # Excel preferisce formato ISO per calcoli
        return self.format_for_storage(date_input)

    def validate_date_string(self, date_str: str) -> bool:
        """
        Validazione rapida di una stringa data senza parsing completo

        Args:
            date_str: Stringa da validare

        Returns:
            True se la stringa sembra una data valida
        """
        if not date_str or self._is_empty_date(date_str):
            return False

        # Controllo pattern regex
        for pattern in self.date_patterns:
            if re.match(pattern, date_str.strip()):
                return True

        return False

    def get_date_components(self, date_input: Any) -> Optional[dict]:
        """
        Estrae i componenti (anno, mese, giorno) da una data

        Args:
            date_input: Input data

        Returns:
            Dizionario con 'year', 'month', 'day' o None se parsing fallisce
        """
        try:
            parsed_date = self.parse_date(date_input)
            if not parsed_date:
                return None

            return {
                'year': parsed_date.year,
                'month': parsed_date.month,
                'day': parsed_date.day,
                'weekday': parsed_date.weekday(),  # 0=Monday
                'iso_week': parsed_date.isocalendar()[1]
            }

        except Exception as e:
            self.logger.error(f"Errore estrazione componenti data: {e}")
            return None

    def compare_dates(self, date1: Any, date2: Any) -> Optional[int]:
        """
        Confronta due date

        Args:
            date1, date2: Date da confrontare

        Returns:
            -1 se date1 < date2, 0 se uguali, 1 se date1 > date2, None se errore
        """
        try:
            parsed1 = self.parse_date(date1)
            parsed2 = self.parse_date(date2)

            if parsed1 is None or parsed2 is None:
                return None

            if parsed1 < parsed2:
                return -1
            elif parsed1 > parsed2:
                return 1
            else:
                return 0

        except Exception as e:
            self.logger.error(f"Errore confronto date: {e}")
            return None

    def get_today_formatted(self, format_type: str = 'storage') -> str:
        """
        Restituisce la data di oggi in formato specificato

        Args:
            format_type: 'storage', 'display', 'european', 'iso'

        Returns:
            Data di oggi formattata
        """
        today = datetime.now()

        if format_type == 'storage':
            return self.format_for_storage(today)
        else:
            return self.format_for_display(today, format_type)

    def parse_date_range(self, start_date: Any, end_date: Any) -> Optional[tuple]:
        """
        Parsing e validazione di un range di date

        Args:
            start_date, end_date: Date di inizio e fine

        Returns:
            Tupla (start_datetime, end_datetime) o None se errore
        """
        try:
            parsed_start = self.parse_date(start_date)
            parsed_end = self.parse_date(end_date)

            if parsed_start is None or parsed_end is None:
                return None

            if parsed_start > parsed_end:
                self.logger.warning(f"Range date invertito: {start_date} > {end_date}")
                # Swap automaticamente
                parsed_start, parsed_end = parsed_end, parsed_start

            return (parsed_start, parsed_end)

        except Exception as e:
            self.logger.error(f"Errore parsing range date: {e}")
            return None

    def batch_parse_dates(self, date_list: List[Any]) -> List[Optional[datetime]]:
        """
        Parsing batch di una lista di date (ottimizzato)

        Args:
            date_list: Lista di date da parsare

        Returns:
            Lista di datetime (None per parsing falliti)
        """
        results = []
        parse_stats = {'success': 0, 'failed': 0}

        for date_input in date_list:
            parsed = self.parse_date(date_input, strict=False)
            results.append(parsed)

            if parsed:
                parse_stats['success'] += 1
            else:
                parse_stats['failed'] += 1

        self.logger.info(f"Batch parsing completato: {parse_stats['success']} successi, {parse_stats['failed']} fallimenti")
        return results

    # Metodi privati helper

    def _is_empty_date(self, date_str: str) -> bool:
        """Controlla se la stringa rappresenta una data vuota"""
        empty_values = {'', 'na', 'n/a', 'null', 'none', 'nan', 'nat', '-'}
        return date_str.lower().strip() in empty_values

    def _clean_date_string(self, date_str: str) -> str:
        """Pulisce una stringa data da caratteri indesiderati"""
        # Rimuovi ora se presente (es: "2023-01-01 12:34:56" -> "2023-01-01")
        if ' ' in date_str:
            date_str = date_str.split()[0]

        # Rimuovi caratteri strani
        cleaned = re.sub(r'[^\d\-\/\.]', '', date_str)

        return cleaned.strip()

    def _try_parse_formats(self, date_str: str) -> Optional[datetime]:
        """Tenta parsing con formati standard"""
        for date_format in self.supported_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
        return None

    def _validate_date_range(self, date_obj: datetime) -> datetime:
        """Valida che la data sia in un range ragionevole"""
        if not (self.min_year <= date_obj.year <= self.max_year):
            raise DateParseError(f"Anno {date_obj.year} fuori dal range valido ({self.min_year}-{self.max_year})")

        return date_obj


# Istanza globale per facilità d'uso
_date_manager = CentralizedDateManager()

# Funzioni di convenienza per accesso rapido
def parse_date(date_input: Any, strict: bool = False) -> Optional[datetime]:
    """Parsing rapido di una data"""
    return _date_manager.parse_date(date_input, strict)

def format_for_display(date_input: Any, format_type: str = 'european') -> str:
    """Formattazione rapida per display"""
    return _date_manager.format_for_display(date_input, format_type)

def format_for_storage(date_input: Any) -> Optional[str]:
    """Formattazione rapida per storage"""
    return _date_manager.format_for_storage(date_input)

def format_for_excel(date_input: Any) -> Optional[str]:
    """Formattazione rapida per Excel"""
    return _date_manager.format_for_excel(date_input)

def validate_date_string(date_str: str) -> bool:
    """Validazione rapida stringa data"""
    return _date_manager.validate_date_string(date_str)

def get_today_formatted(format_type: str = 'storage') -> str:
    """Data di oggi formattata"""
    return _date_manager.get_today_formatted(format_type)

def get_date_manager() -> CentralizedDateManager:
    """Accesso al manager centralizzato"""
    return _date_manager

# Backward compatibility con utils.py esistente
class DateFormatter:
    """Classe compatibilità per non rompere codice esistente"""

    @staticmethod
    def format_for_display(date_value: Any) -> str:
        return format_for_display(date_value, 'european')

    @staticmethod
    def format_for_form(date_value: Any) -> str:
        result = format_for_storage(date_value)
        return result if result else ""

    @staticmethod
    def format_for_excel(date_value: Any) -> Optional[str]:
        return format_for_excel(date_value)