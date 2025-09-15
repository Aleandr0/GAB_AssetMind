#!/usr/bin/env python3
"""
Sistema di logging configurabile per GAB AssetMind
Sostituisce i print di debug con logging professionale configurabile
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional
from config import get_application_directory

class AppLogger:
    """
    Sistema di logging centralizzato per GAB AssetMind

    Supporta diversi livelli di logging e output configurabili:
    - Console output con colori
    - File logging con rotazione automatica
    - Configurazione runtime del livello di debug
    """

    _instance: Optional['AppLogger'] = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.logger = logging.getLogger('GABAssetMind')
            self.logger.setLevel(logging.DEBUG)
            self._setup_handlers()
            AppLogger._initialized = True

    def _setup_handlers(self):
        """Configura i gestori di output per il logging"""

        # Rimuovi handler esistenti per evitare duplicati
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # 1. Console Handler con colori
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # Console mostra solo INFO e superiori

        # Formatter colorato per console
        console_formatter = ColoredFormatter(
            '%(asctime)s [%(levelname)s] %(name)s.%(module)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

        # 2. File Handler con rotazione
        try:
            log_dir = os.path.join(get_application_directory(), 'logs')
            os.makedirs(log_dir, exist_ok=True)

            log_file = os.path.join(log_dir, 'assetmind.log')

            # Rotazione automatica: max 5MB per file, mantieni 3 backup
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)  # File cattura tutto

            # Formatter dettagliato per file
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)-8s] %(name)s.%(module)s.%(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)

            self.logger.addHandler(file_handler)

        except Exception as e:
            # Fallback se non può creare file di log
            console_handler.setLevel(logging.DEBUG)
            print(f"Avviso: Impossibile creare log file: {e}")

        self.logger.addHandler(console_handler)

    def set_debug_mode(self, enabled: bool = True):
        """
        Abilita/disabilita modalità debug
        In debug mode, anche la console mostra messaggi DEBUG
        """
        console_level = logging.DEBUG if enabled else logging.INFO

        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not hasattr(handler, 'baseFilename'):
                handler.setLevel(console_level)

    def get_logger(self) -> logging.Logger:
        """Restituisce l'istanza logger configurata"""
        return self.logger


class ColoredFormatter(logging.Formatter):
    """Formatter che aggiunge colori ANSI ai messaggi di console"""

    # Codici colore ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Giallo
        'ERROR': '\033[31m',      # Rosso
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        # Applica colore al livello di log
        level_color = self.COLORS.get(record.levelname, '')
        reset_color = self.COLORS['RESET']

        # Colora solo il levelname
        colored_record = logging.makeLogRecord(record.__dict__)
        colored_record.levelname = f"{level_color}{record.levelname}{reset_color}"

        return super().format(colored_record)


# Factory functions per utilizzare il logger
def get_logger(name: str = '') -> logging.Logger:
    """
    Ottiene un logger configurato per GAB AssetMind

    Args:
        name: Nome specifico del modulo (opzionale)

    Returns:
        Logger configurato e pronto all'uso
    """
    app_logger = AppLogger()
    if name:
        return app_logger.get_logger().getChild(name)
    return app_logger.get_logger()


def set_debug_mode(enabled: bool = True):
    """
    Configura la modalità debug globalmente

    Args:
        enabled: True per abilitare debug sulla console
    """
    app_logger = AppLogger()
    app_logger.set_debug_mode(enabled)


# Funzioni di convenienza per logging rapido
def debug(msg, *args, **kwargs):
    """Log messaggio DEBUG"""
    get_logger().debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    """Log messaggio INFO"""
    get_logger().info(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    """Log messaggio WARNING"""
    get_logger().warning(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    """Log messaggio ERROR"""
    get_logger().error(msg, *args, **kwargs)

def critical(msg, *args, **kwargs):
    """Log messaggio CRITICAL"""
    get_logger().critical(msg, *args, **kwargs)


# Configurazione automatica all'import
if __name__ != '__main__':
    # Inizializza il sistema di logging quando il modulo viene importato
    app_logger = AppLogger()

    # Legge configurazione debug da variabile ambiente (opzionale)
    debug_enabled = os.getenv('GAB_DEBUG', 'false').lower() == 'true'
    if debug_enabled:
        set_debug_mode(True)