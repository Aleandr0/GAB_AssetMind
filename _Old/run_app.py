#!/usr/bin/env python3
"""
GAB AssetMind - Portfolio Manager
Script di avvio semplice con controllo dipendenze

Per avviare l'applicazione:
python run_app.py
"""

import sys

try:
    # Importa e avvia l'app
    from main import GABAssetMind
    app = GABAssetMind()
    app.run()
except ImportError as e:
    print(f"Dipendenze mancanti: {e}")
    print("Esegui: pip install -r requirements.txt")
    input("Premi INVIO per chiudere...")
except Exception as e:
    print(f"Errore: {e}")
    input("Premi INVIO per chiudere...")
    sys.exit(1)