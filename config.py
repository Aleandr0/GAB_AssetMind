#!/usr/bin/env python3
"""
Configurazione centralizzata per GAB AssetMind
Contiene tutte le costanti, colori, dimensioni e mappature di campo
"""

import os
from typing import Dict, List, Tuple

class UIConfig:
    """Configurazione dell'interfaccia utente"""
    
    # Colori dell'interfaccia
    COLORS = {
        'primary': "#3b82f6",        # Blu principale
        'secondary': "#6b7280",      # Grigio secondario
        'success': "#16a34a",        # Verde successo
        'warning': "#f59e0b",        # Arancione avviso
        'danger': "#dc2626",         # Rosso errore
        'info': "#0891b2",           # Ciano informativo
        'purple': "#7c3aed",         # Viola per funzioni speciali
        
        # Hover colors
        'primary_hover': "#2563eb",
        'secondary_hover': "#4b5563",
        'success_hover': "#15803d",
        'warning_hover': "#d97706",
        'danger_hover': "#b91c1c",
        'info_hover': "#0e7490",
        'purple_hover': "#6d28d9"
    }
    
    # Dimensioni bottoni standardizzate
    BUTTON_SIZES = {
        'small': {'width': 100, 'height': 30},
        'medium': {'width': 95, 'height': 32},  # Ridotto da 120 a 95 per Portfolio
        'large': {'width': 140, 'height': 40},
        'compact': {'width': 110, 'height': 32}
    }
    
    # Font standardizzati
    FONTS = {
        'title': {'size': 20, 'weight': 'bold'},
        'header': {'size': 18, 'weight': 'bold'},
        'subheader': {'size': 14, 'weight': 'bold'},
        'button': {'size': 11, 'weight': 'bold'},
        'text': {'size': 12, 'weight': 'normal'},
        'small': {'size': 10, 'weight': 'normal'}
    }
    
    # Dimensioni finestre
    WINDOW_SIZES = {
        'main': "1200x800",
        'dialog': "400x300"
    }

class FieldMapping:
    """Mappatura centralizzata dei campi database <-> UI"""
    
    # Mappatura nomi colonne display -> database
    DISPLAY_TO_DB = {
        "ID": "id",
        "Position": "position",
        "Category": "category",
        "Investment Type": "type",
        "Tool": "tool",
        "Asset Name": "asset_name",
        "ISIN": "isin",
        "Ticker": "ticker",
        "Risk Level": "risk_level",
        "Created At": "created_at",
        "Created Amount": "created_amount",
        "Created Unit Price": "created_unit_price",
        "Created Total Value": "created_total_value",
        "Updated At": "updated_at",
        "Updated Amount": "updated_amount",
        "Updated Unit Price": "updated_unit_price",
        "Updated Total Value": "updated_total_value",
        "Accumulation Plan": "accumulation_plan",
        "Accumulation Amount": "accumulation_amount",
        "Income Per Year": "income_per_year",
        "Rental Income": "rental_income",
        "Note": "note",
        "Return %": "return_percentage"
    }
    
    # Mappatura inversa database -> display  
    DB_TO_DISPLAY = {v: k for k, v in DISPLAY_TO_DB.items()}
    
    # Campi monetari (per formattazione)
    MONETARY_FIELDS = {
        'created_unit_price', 'updated_unit_price', 
        'created_total_value', 'updated_total_value',
        'accumulation_amount', 'income_per_year', 'rental_income'
    }
    
    # Campi data
    DATE_FIELDS = {'created_at', 'updated_at'}
    
    # Campi numerici
    NUMERIC_FIELDS = {
        'id', 'risk_level', 'created_amount', 'updated_amount'
    }.union(MONETARY_FIELDS)

class AssetConfig:
    """Configurazione per gestione asset"""

    # Categorie supportate (nuova struttura gerarchica)
    CATEGORIES = [
        "Azionari (Equity)",
        "Obbligazionari (Fixed Income)",
        "Materie Prime (Commodities)",
        "Immobiliari (Real Estate)",
        "Strumenti Alternativi (Alternatives)",
        "Liquidità e Strumenti Monetari"
    ]
    
    # Livelli di rischio
    RISK_LEVELS = ["1", "2", "3", "4", "5"]

    # Frequenze PAC (Piano di Accumulo)
    PAC_FREQUENCIES = [
        "Settimanale",
        "Quindicinale",
        "Mensile",
        "Trimestrale",
        "Semestrale",
        "Annuale",
        "Unico",
        "Sospeso"
    ]

    # Mapping gerarchico: Categoria → Tipi di Investimento
    INVESTMENT_TYPES_BY_CATEGORY = {
        "Azionari (Equity)": [
            "Azionariato Globale",
            "Azionariato Americano",
            "Azionariato Europeo",
            "Azionariato Paesi Sviluppati",
            "Azionariato Paesi Emergenti",
            "Azioni Small Cap Paesi Sviluppati",
            "Azioni Value / Growth",
            "Azioni ESG / Sostenibili"
        ],
        "Obbligazionari (Fixed Income)": [
            "Obbligazioni Governative Europee",
            "Obbligazioni Governative Globali",
            "Obbligazioni Governative a Medio Termine",
            "Obbligazioni Governative a Lungo Termine",
            "Obbligazioni Corporate Investment Grade",
            "Obbligazioni High Yield",
            "Obbligazioni Green Bond"
        ],
        "Materie Prime (Commodities)": [
            "Oro",
            "Argento",
            "Petrolio",
            "Gas Naturale",
            "Metalli Industriali",
            "Materie Prime Agricole"
        ],
        "Immobiliari (Real Estate)": [
            "REIT Globali",
            "Fondi Immobiliari",
            "Immobiliare Diretto",
            "Crowdfunding Immobiliare",
            "Immobiliare Logistico",
            "Immobiliare Residenziale"
        ],
        "Strumenti Alternativi (Alternatives)": [
            "Private Equity",
            "Private Debt",
            "Hedge Funds",
            "Infrastrutture",
            "Criptovalute",
            "ETF Alternativi"
        ],
        "Liquidità e Strumenti Monetari": [
            "Conto Corrente",
            "Conto Deposito",
            "Fondo Monetario",
            "Pronti Contro Termine",
            "Buoni del Tesoro",
            "ETF Monetari"
        ]
    }

    # Mapping gerarchico: Tipo di Investimento → Strumenti
    TOOLS_BY_INVESTMENT_TYPE = {
        # Azionari
        "Azionariato Globale": ["ETF UCITS", "Fondo Azionario", "Azione Diretta", "Certificato d'investimento", "ETN/ETP su equity", "Derivati su indici o azioni"],
        "Azionariato Americano": ["ETF UCITS", "Fondo Azionario", "Azione Diretta", "Certificato d'investimento", "ETN/ETP su equity", "Derivati su indici o azioni"],
        "Azionariato Europeo": ["ETF UCITS", "Fondo Azionario", "Azione Diretta", "Certificato d'investimento", "ETN/ETP su equity", "Derivati su indici o azioni"],
        "Azionariato Paesi Sviluppati": ["ETF UCITS", "Fondo Azionario", "Azione Diretta", "Certificato d'investimento", "ETN/ETP su equity", "Derivati su indici o azioni"],
        "Azionariato Paesi Emergenti": ["ETF UCITS", "Fondo Azionario", "Azione Diretta", "Certificato d'investimento", "ETN/ETP su equity", "Derivati su indici o azioni"],
        "Azioni Small Cap Paesi Sviluppati": ["ETF UCITS", "Fondo Azionario", "Azione Diretta", "Certificato d'investimento", "ETN/ETP su equity", "Derivati su indici o azioni"],
        "Azioni Value / Growth": ["ETF UCITS", "Fondo Azionario", "Azione Diretta", "Certificato d'investimento", "ETN/ETP su equity", "Derivati su indici o azioni"],
        "Azioni ESG / Sostenibili": ["ETF UCITS", "Fondo Azionario", "Azione Diretta", "Certificato d'investimento", "ETN/ETP su equity", "Derivati su indici o azioni"],

        # Obbligazionari
        "Obbligazioni Governative Europee": ["ETF Obbligazionario", "Fondo Obbligazionario", "Obbligazione Diretta", "Certificato a reddito", "ETN/ETP su bond", "Derivati su tassi o credito"],
        "Obbligazioni Governative Globali": ["ETF Obbligazionario", "Fondo Obbligazionario", "Obbligazione Diretta", "Certificato a reddito", "ETN/ETP su bond", "Derivati su tassi o credito"],
        "Obbligazioni Governative a Medio Termine": ["ETF Obbligazionario", "Fondo Obbligazionario", "Obbligazione Diretta", "Certificato a reddito", "ETN/ETP su bond", "Derivati su tassi o credito"],
        "Obbligazioni Governative a Lungo Termine": ["ETF Obbligazionario", "Fondo Obbligazionario", "Obbligazione Diretta", "Certificato a reddito", "ETN/ETP su bond", "Derivati su tassi o credito"],
        "Obbligazioni Corporate Investment Grade": ["ETF Obbligazionario", "Fondo Obbligazionario", "Obbligazione Diretta", "Certificato a reddito", "ETN/ETP su bond", "Derivati su tassi o credito"],
        "Obbligazioni High Yield": ["ETF Obbligazionario", "Fondo Obbligazionario", "Obbligazione Diretta", "Certificato a reddito", "ETN/ETP su bond", "Derivati su tassi o credito"],
        "Obbligazioni Green Bond": ["ETF Obbligazionario", "Fondo Obbligazionario", "Obbligazione Diretta", "Certificato a reddito", "ETN/ETP su bond", "Derivati su tassi o credito"],

        # Materie Prime
        "Oro": ["ETC su commodity", "ETF commodity", "Futures su commodity", "Opzioni su commodity", "Certificati su commodity", "Azioni di produttori"],
        "Argento": ["ETC su commodity", "ETF commodity", "Futures su commodity", "Opzioni su commodity", "Certificati su commodity", "Azioni di produttori"],
        "Petrolio": ["ETC su commodity", "ETF commodity", "Futures su commodity", "Opzioni su commodity", "Certificati su commodity", "Azioni di produttori"],
        "Gas Naturale": ["ETC su commodity", "ETF commodity", "Futures su commodity", "Opzioni su commodity", "Certificati su commodity", "Azioni di produttori"],
        "Metalli Industriali": ["ETC su commodity", "ETF commodity", "Futures su commodity", "Opzioni su commodity", "Certificati su commodity", "Azioni di produttori"],
        "Materie Prime Agricole": ["ETC su commodity", "ETF commodity", "Futures su commodity", "Opzioni su commodity", "Certificati su commodity", "Azioni di produttori"],

        # Immobiliari
        "REIT Globali": ["REIT (azione quotata)", "ETF Immobiliare", "Fondo Immobiliare", "Immobiliare Diretto", "Crowdfunding Immobiliare", "Certificato Immobiliare"],
        "Fondi Immobiliari": ["REIT (azione quotata)", "ETF Immobiliare", "Fondo Immobiliare", "Immobiliare Diretto", "Crowdfunding Immobiliare", "Certificato Immobiliare"],
        "Immobiliare Diretto": ["REIT (azione quotata)", "ETF Immobiliare", "Fondo Immobiliare", "Immobiliare Diretto", "Crowdfunding Immobiliare", "Certificato Immobiliare"],
        "Crowdfunding Immobiliare": ["REIT (azione quotata)", "ETF Immobiliare", "Fondo Immobiliare", "Immobiliare Diretto", "Crowdfunding Immobiliare", "Certificato Immobiliare"],
        "Immobiliare Logistico": ["REIT (azione quotata)", "ETF Immobiliare", "Fondo Immobiliare", "Immobiliare Diretto", "Crowdfunding Immobiliare", "Certificato Immobiliare"],
        "Immobiliare Residenziale": ["REIT (azione quotata)", "ETF Immobiliare", "Fondo Immobiliare", "Immobiliare Diretto", "Crowdfunding Immobiliare", "Certificato Immobiliare"],

        # Strumenti Alternativi
        "Private Equity": ["Fondo Private Equity/VC", "Fondo Private Debt", "Hedge Fund", "Fondo Infrastrutture", "Criptovalute Dirette", "ETN/ETF su cripto"],
        "Private Debt": ["Fondo Private Equity/VC", "Fondo Private Debt", "Hedge Fund", "Fondo Infrastrutture", "Criptovalute Dirette", "ETN/ETF su cripto"],
        "Hedge Funds": ["Fondo Private Equity/VC", "Fondo Private Debt", "Hedge Fund", "Fondo Infrastrutture", "Criptovalute Dirette", "ETN/ETF su cripto"],
        "Infrastrutture": ["Fondo Private Equity/VC", "Fondo Private Debt", "Hedge Fund", "Fondo Infrastrutture", "Criptovalute Dirette", "ETN/ETF su cripto"],
        "Criptovalute": ["Fondo Private Equity/VC", "Fondo Private Debt", "Hedge Fund", "Fondo Infrastrutture", "Criptovalute Dirette", "ETN/ETF su cripto"],
        "ETF Alternativi": ["Fondo Private Equity/VC", "Fondo Private Debt", "Hedge Fund", "Fondo Infrastrutture", "Criptovalute Dirette", "ETN/ETF su cripto"],

        # Liquidità
        "Conto Corrente": ["Conto Corrente", "Conto Deposito", "Fondo Monetario UCITS", "Pronti Contro Termine", "Buoni del Tesoro a breve", "ETF Monetario"],
        "Conto Deposito": ["Conto Corrente", "Conto Deposito", "Fondo Monetario UCITS", "Pronti Contro Termine", "Buoni del Tesoro a breve", "ETF Monetario"],
        "Fondo Monetario": ["Conto Corrente", "Conto Deposito", "Fondo Monetario UCITS", "Pronti Contro Termine", "Buoni del Tesoro a breve", "ETF Monetario"],
        "Pronti Contro Termine": ["Conto Corrente", "Conto Deposito", "Fondo Monetario UCITS", "Pronti Contro Termine", "Buoni del Tesoro a breve", "ETF Monetario"],
        "Buoni del Tesoro": ["Conto Corrente", "Conto Deposito", "Fondo Monetario UCITS", "Pronti Contro Termine", "Buoni del Tesoro a breve", "ETF Monetario"],
        "ETF Monetari": ["Conto Corrente", "Conto Deposito", "Fondo Monetario UCITS", "Pronti Contro Termine", "Buoni del Tesoro a breve", "ETF Monetario"]
    }

    # Categorie che richiedono identificativi completi per i dati di mercato
    MARKET_IDENTIFIER_CATEGORIES = {
        "ETF", "Azioni", "Fondi di investimento", "PAC", "Criptovalute"
    }

    # Mappatura campi rilevanti per categoria
    CATEGORY_FIELD_MAPPING = {
        "ETF": ["ticker", "isin", "income_per_year"],
        "Azioni": ["ticker", "isin", "income_per_year"], 
        "Fondi di investimento": ["ticker", "isin", "income_per_year"],
        "Buoni del Tesoro": ["isin", "income_per_year"],
        "PAC": ["ticker", "isin", "accumulation_plan", "accumulation_amount", "income_per_year"],
        "Criptovalute": ["ticker"],
        "Liquidità": ["income_per_year"],
        "Immobiliare": ["rental_income"],
        "Oggetti": []
    }
    
    # Campi sempre attivi (per tutte le categorie)
    ALWAYS_ACTIVE_FIELDS = [
        "category", "type", "tool", "asset_name", "position", "risk_level",
        "created_at", "created_amount", "created_unit_price", "created_total_value",
        "updated_at", "updated_amount", "updated_unit_price", "updated_total_value",
        "note"
    ]
    
    # Campi numerici (riceveranno "0" quando non applicabili)
    NUMERIC_DEFAULT_FIELDS = {
        "income_per_year", "rental_income", "accumulation_amount"
    }

class DatabaseConfig:
    """Configurazione database e file"""
    
    # Nome file di default
    DEFAULT_PORTFOLIO_FILE = "portfolio_data.xlsx"
    
    # Colonne database (ordine aggiornato con type e tool)
    DB_COLUMNS = [
        'id', 'position', 'category', 'type', 'tool', 'asset_name', 'isin', 'ticker', 'risk_level',
        'created_at', 'created_amount', 'created_unit_price', 'created_total_value',
        'updated_at', 'updated_amount', 'updated_unit_price', 'updated_total_value',
        'accumulation_plan', 'accumulation_amount', 'income_per_year', 'rental_income', 'note',
        'return_percentage'
    ]

class ValidationConfig:
    """Configurazione per validazione dati"""
    
    # Valori considerati vuoti/nulli
    EMPTY_VALUES = {'', 'nan', 'none', 'null', 'n/a', 'na'}
    
    # Range valori accettabili
    RANGES = {
        'risk_level': (1, 5),
        'created_amount': (0, float('inf')),
        'updated_amount': (0, float('inf')),
        'created_unit_price': (0, float('inf')),
        'updated_unit_price': (0, float('inf'))
    }
    
    # Pattern regex per validazione
    PATTERNS = {
        'isin': r'^[A-Z]{2}[A-Z0-9]{10}$',
        'date': r'^\d{4}-\d{2}-\d{2}$'
    }

class Messages:
    """Messaggi standardizzati per l'interfaccia"""
    
    SUCCESS = {
        'asset_saved': "Asset salvato con successo",
        'asset_deleted': "Asset eliminato con successo", 
        'asset_copied': "Asset copiato! Modifica i dati e clicca 'Salva Asset'",
        'portfolio_switched': "Portfolio cambiato con successo",
        'backup_created': "Backup creato con successo"
    }
    
    WARNINGS = {
        'no_asset_selected': "Nessun asset selezionato",
        'no_data_available': "Nessun dato disponibile",
        'confirm_delete': "Sei sicuro di voler eliminare questo asset?"
    }
    
    ERRORS = {
        'save_failed': "Impossibile salvare l'asset",
        'load_failed': "Errore nel caricamento dati",
        'invalid_data': "Dati non validi",
        'file_not_found': "File non trovato",
        'permission_denied': "Permessi insufficienti"
    }

# Funzioni di utilità per la configurazione
def get_application_directory() -> str:
    """Restituisce la directory dove cercare/salvare i file dell'app.

    - In eseguibile PyInstaller: usa la cartella dell'eseguibile (dist/), NON la
      cartella temporanea di estrazione (`_MEIPASS`) che è di sola lettura.
    - In esecuzione da sorgente: usa la cartella del file corrente.
    """
    import sys
    # Eseguibile "frozen" (PyInstaller): punta alla cartella dell'eseguibile
    if getattr(sys, 'frozen', False) and hasattr(sys, 'executable'):
        return os.path.dirname(sys.executable)
    # Esecuzione normale: cartella del modulo
    return os.path.dirname(os.path.abspath(__file__))

def get_theme_colors(dark_mode: bool = False) -> Dict[str, str]:
    """Restituisce i colori del tema in base alla modalità"""
    if dark_mode:
        # Colori tema scuro (future implementation)
        return UIConfig.COLORS
    else:
        return UIConfig.COLORS
