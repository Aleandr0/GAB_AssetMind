#!/usr/bin/env python3
"""
Validazione sicurezza per GAB AssetMind
Sistema di validazione path sicuri e prevenzione directory traversal
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Union, List, Optional
from logging_config import get_logger

class SecurityError(Exception):
    """Eccezione per violazioni di sicurezza"""
    pass

class PathSecurityValidator:
    """
    Validatore per path sicuri che previene directory traversal e altri attacchi

    Funzionalità:
    - Validazione path assoluti e relativi
    - Prevenzione directory traversal (../, ../../, etc.)
    - Whitelist di directory sicure
    - Blacklist di pattern pericolosi
    - Normalizzazione path cross-platform
    """

    def __init__(self, base_directory: str = None):
        """
        Args:
            base_directory: Directory base sicura (default: app directory)
        """
        self.logger = get_logger('PathSecurity')

        # Directory base sicura - dove l'app può operare
        if base_directory:
            self.base_directory = Path(base_directory).resolve()
        else:
            from config import get_application_directory
            self.base_directory = Path(get_application_directory()).resolve()

        # Directory sicure aggiuntive (relative alla base)
        self.safe_subdirectories = {
            'logs', 'backups', 'exports', 'temp', 'data', 'reports'
        }

        # Pattern pericolosi da bloccare
        self.dangerous_patterns = [
            r'\.\.[\\/]',           # Directory traversal
            r'[\\/]\.\.[\\/]',      # Directory traversal embedded
            r'^\.\.[\\/]',          # Directory traversal all'inizio
            r'[\\/]\.\.$',          # Directory traversal alla fine
            r'~[\\/]',              # Home directory reference
            r'\$[A-Z_]+',           # Environment variables
            r'%[A-Z_]+%',           # Windows environment variables
            r'[\x00-\x1f]',         # Caratteri controllo
            r'\.\.\\\\',            # Double backslash traversal
            r'\.\.//',              # Double slash traversal
        ]

        # Pattern per nomi file (più restrittivi)
        self.filename_dangerous_patterns = [
            r'[<>"|?*]',            # Caratteri illegali nei nomi file (escluso : per path)
        ]

        # Estensioni file sicure
        self.safe_extensions = {
            '.xlsx', '.xls', '.csv', '.txt', '.log', '.json',
            '.pdf', '.png', '.jpg', '.jpeg', '.bmp'
        }

        # Nomi file pericolosi
        self.dangerous_filenames = {
            'con', 'prn', 'aux', 'nul',  # Windows reserved
            'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
            'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
        }

    def validate_portfolio_path(self, file_path: Union[str, Path]) -> Path:
        """
        Valida un path portfolio e lo rende sicuro

        Args:
            file_path: Path da validare

        Returns:
            Path validato e sicuro

        Raises:
            SecurityError: Se il path non è sicuro
        """
        try:
            # Converte in Path e normalizza
            path_obj = Path(file_path)

            # Log della richiesta di validazione
            self.logger.debug(f"Validando path portfolio: {file_path}")

            # 1. Controllo pattern pericolosi
            self._check_dangerous_patterns(str(path_obj))

            # 2. Controllo nome file
            self._check_filename_safety(path_obj.name)

            # 3. Controllo estensione
            self._check_file_extension(path_obj.suffix)

            # 4. Risolvi path e controlla se è dentro area sicura
            safe_path = self._resolve_safe_path(path_obj)

            # 5. Controllo finale dei componenti
            self._check_path_components(safe_path)

            self.logger.info(f"Path portfolio validato con successo: {safe_path}")
            return safe_path

        except SecurityError:
            raise  # Re-raise security errors
        except Exception as e:
            self.logger.error(f"Errore durante validazione path {file_path}: {e}")
            raise SecurityError(f"Errore validazione path: {e}")

    def validate_export_path(self, file_path: Union[str, Path],
                           allow_user_directories: bool = True) -> Path:
        """
        Valida un path per export (più permissivo per salvare fuori dall'app)

        Args:
            file_path: Path da validare
            allow_user_directories: Consenti directory utente (Documents, Desktop, etc.)

        Returns:
            Path validato e sicuro

        Raises:
            SecurityError: Se il path non è sicuro
        """
        try:
            path_obj = Path(file_path)

            self.logger.debug(f"Validando path export: {file_path}")

            # 1. Controllo pattern pericolosi (più permissivo)
            self._check_dangerous_patterns(str(path_obj), strict=False)

            # 2. Controllo nome file
            self._check_filename_safety(path_obj.name)

            # 3. Controllo estensione (include formati export)
            export_extensions = self.safe_extensions.union({'.pdf', '.zip'})
            if path_obj.suffix.lower() not in export_extensions:
                raise SecurityError(f"Estensione file non sicura per export: {path_obj.suffix}")

            # 4. Risolvi path
            resolved_path = path_obj.resolve()

            # 5. Per export, controlla che non sia in directory di sistema critiche
            self._check_system_directories(resolved_path)

            # 6. Se consenti directory utente, verifica che sia ragionevole
            if allow_user_directories:
                self._check_user_directory_access(resolved_path)

            self.logger.info(f"Path export validato con successo: {resolved_path}")
            return resolved_path

        except SecurityError:
            raise
        except Exception as e:
            self.logger.error(f"Errore durante validazione export path {file_path}: {e}")
            raise SecurityError(f"Errore validazione export path: {e}")

    def _check_dangerous_patterns(self, path_str: str, strict: bool = True):
        """Controlla pattern pericolosi nel path"""
        normalized_path = path_str.replace('\\', '/')

        patterns_to_check = self.dangerous_patterns
        if not strict:
            # Per export, rimuovi alcuni controlli più rigidi
            patterns_to_check = [p for p in self.dangerous_patterns
                                if not any(x in p for x in ['~', '$', '%'])]

        for pattern in patterns_to_check:
            if re.search(pattern, normalized_path, re.IGNORECASE):
                raise SecurityError(f"Pattern pericoloso rilevato nel path: {pattern}")

    def _check_filename_safety(self, filename: str):
        """Controlla che il nome file sia sicuro"""
        if not filename or len(filename.strip()) == 0:
            raise SecurityError("Nome file vuoto")

        # Controllo lunghezza
        if len(filename) > 255:
            raise SecurityError("Nome file troppo lungo (max 255 caratteri)")

        # Controllo caratteri illegali nei nomi file
        for pattern in self.filename_dangerous_patterns:
            if re.search(pattern, filename):
                raise SecurityError("Nome file contiene caratteri illegali")

        # Controllo nomi riservati Windows
        base_name = filename.split('.')[0].lower()
        if base_name in self.dangerous_filenames:
            raise SecurityError(f"Nome file riservato dal sistema: {filename}")

        # Non deve iniziare o finire con spazi o punti
        if filename != filename.strip() or filename.endswith('.'):
            raise SecurityError("Nome file non può iniziare/finire con spazi o punti")

    def _check_file_extension(self, extension: str):
        """Controlla che l'estensione sia sicura"""
        if not extension:
            raise SecurityError("File senza estensione non permesso")

        if extension.lower() not in self.safe_extensions:
            raise SecurityError(f"Estensione file non sicura: {extension}")

    def _resolve_safe_path(self, path_obj: Path) -> Path:
        """Risolve il path e controlla che sia nell'area sicura"""
        try:
            # Se è relativo, lo rende relativo alla directory base
            if not path_obj.is_absolute():
                safe_path = (self.base_directory / path_obj).resolve()
            else:
                safe_path = path_obj.resolve()

            # Controlla che sia sotto la directory base
            if not self._is_path_under_base(safe_path):
                raise SecurityError(f"Path fuori dall'area sicura: {safe_path}")

            return safe_path

        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Errore risoluzione path: {e}")

    def _is_path_under_base(self, path: Path) -> bool:
        """Controlla che il path sia sotto la directory base sicura"""
        try:
            path.relative_to(self.base_directory)
            return True
        except ValueError:
            return False

    def _check_path_components(self, path: Path):
        """Controlla ogni componente del path"""
        for part in path.parts:
            if part in {'..', '.'}:
                raise SecurityError(f"Componente path non sicuro: {part}")

            # Controllo lunghezza componente
            if len(part) > 100:
                raise SecurityError(f"Componente path troppo lungo: {part}")

    def _check_system_directories(self, path: Path):
        """Controlla che non sia in directory di sistema critiche"""
        dangerous_roots = {
            'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)',
            '/bin', '/sbin', '/usr/bin', '/usr/sbin', '/etc', '/sys', '/proc'
        }

        path_str = str(path).replace('/', '\\') if os.name == 'nt' else str(path)

        for dangerous_root in dangerous_roots:
            try:
                if os.name == 'nt':
                    dangerous_root = dangerous_root.replace('/', '\\')

                if path_str.lower().startswith(dangerous_root.lower()):
                    raise SecurityError(f"Accesso negato a directory di sistema: {dangerous_root}")
            except Exception:
                continue

    def _check_user_directory_access(self, path: Path):
        """Controlla accesso ragionevole alle directory utente"""
        # Consenti comuni directory utente
        allowed_user_roots = ['Documents', 'Desktop', 'Downloads', 'Pictures']

        path_parts = path.parts
        if len(path_parts) > 2:  # Almeno C:\Users\username\...
            user_dir = path_parts[-2] if len(path_parts) > 2 else ''
            if user_dir in allowed_user_roots:
                return  # OK

        # Se non è in directory utente standard, deve essere relativo all'app
        if not self._is_path_under_base(path):
            # Consenti solo se è in una directory sicura comune
            common_safe_dirs = {'temp', 'export', 'backup'}
            if not any(safe_dir in str(path).lower() for safe_dir in common_safe_dirs):
                raise SecurityError(f"Path export non in area sicura: {path}")

    def create_safe_portfolio_path(self, filename: str) -> Path:
        """
        Crea un path sicuro per un nuovo portfolio nella directory base

        Args:
            filename: Nome del file portfolio

        Returns:
            Path sicuro per il portfolio
        """
        try:
            # Pulisci il nome file
            safe_filename = self._sanitize_filename(filename)

            # Assicurati che abbia estensione xlsx
            if not safe_filename.lower().endswith('.xlsx'):
                safe_filename += '.xlsx'

            # Crea path sicuro
            safe_path = self.base_directory / safe_filename

            # Valida il path risultante
            return self.validate_portfolio_path(safe_path)

        except Exception as e:
            self.logger.error(f"Errore creazione path sicuro per {filename}: {e}")
            raise SecurityError(f"Impossibile creare path sicuro: {e}")

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitizza un nome file rimuovendo caratteri pericolosi"""
        # Rimuovi estensione per processing
        name, ext = os.path.splitext(filename)

        # Rimuovi caratteri illegali
        safe_name = re.sub(r'[<>:"|?*\x00-\x1f\\\/]', '_', name)

        # Rimuovi spazi multipli
        safe_name = re.sub(r'\s+', ' ', safe_name).strip()

        # Limita lunghezza
        if len(safe_name) > 100:
            safe_name = safe_name[:100]

        # Rimuovi punti finali e spazi
        safe_name = safe_name.rstrip(' .')

        # Se vuoto, usa default
        if not safe_name:
            safe_name = 'portfolio'

        return safe_name + ext

    def get_safe_backup_path(self, original_path: Union[str, Path]) -> Path:
        """
        Genera un path sicuro per backup nella directory base

        Args:
            original_path: Path originale

        Returns:
            Path sicuro per backup
        """
        try:
            original_path_obj = Path(original_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            base_name = original_path_obj.stem
            extension = original_path_obj.suffix

            backup_filename = f"{base_name}_backup_{timestamp}{extension}"
            backup_path = self.base_directory / "backups" / backup_filename

            # Crea directory backup se non esistente
            backup_path.parent.mkdir(exist_ok=True)

            return backup_path

        except Exception as e:
            self.logger.error(f"Errore generazione path backup: {e}")
            raise SecurityError(f"Impossibile creare path backup sicuro: {e}")


# Factory function per facilità d'uso
def create_path_validator(base_directory: str = None) -> PathSecurityValidator:
    """
    Crea un validatore di path configurato

    Args:
        base_directory: Directory base (optional)

    Returns:
        Validatore configurato
    """
    return PathSecurityValidator(base_directory)


# Funzioni di convenienza per validazione rapida
def validate_portfolio_file(file_path: Union[str, Path]) -> Path:
    """Valida rapidamente un path portfolio"""
    validator = create_path_validator()
    return validator.validate_portfolio_path(file_path)

def validate_export_file(file_path: Union[str, Path]) -> Path:
    """Valida rapidamente un path export"""
    validator = create_path_validator()
    return validator.validate_export_path(file_path)

def create_safe_filename(filename: str) -> str:
    """Crea rapidamente un nome file sicuro"""
    validator = create_path_validator()
    return validator._sanitize_filename(filename)