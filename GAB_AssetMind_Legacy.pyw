#!/usr/bin/env python3
"""
GAB AssetMind - Portfolio Manager (Legacy Version)
File .pyw per avvio senza terminale su Windows

Versione legacy mantenuta per compatibilità
Versione principale: GAB_AssetMind.pyw (Refactored v2.0)
"""

if __name__ == "__main__":
    try:
        # Importa la versione legacy dalla sottocartella _Legacy
        from _Legacy.main import GABAssetMind
        
        print("GAB AssetMind v1.0 (Legacy) - Avvio in corso...")
        print("Versione legacy caricata dalla cartella _Legacy")
        
        app = GABAssetMind()
        app.run()
        
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Errore GAB AssetMind Legacy", 
                           f"Errore nella versione legacy:\n{e}\n\n"
                           f"Usa GAB_AssetMind.pyw per la versione refactored")
        root.destroy()