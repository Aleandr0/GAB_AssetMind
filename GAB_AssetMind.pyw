#!/usr/bin/env python3
"""
GAB AssetMind - Portfolio Manager (Refactored Version v2.0)
File .pyw per avvio senza terminale su Windows

Versione con architettura modulare e performance ottimizzate
Per tornare alla versione legacy: usa GAB_AssetMind_legacy.pyw
"""

if __name__ == "__main__":
    try:
        # Importa la versione refactored (ora rinominata main.py)
        from main import GABAssetMind
        
        print("GAB AssetMind v2.0 (Refactored) - Avvio in corso...")
        print("Architettura modulare caricata con successo")
        
        app = GABAssetMind()
        app.run()
        
    except ImportError as e:
        # Fallback alla versione legacy nella sottocartella _Legacy
        print(f"Errore import versione refactored: {e}")
        print("Tentativo fallback alla versione legacy...")
        try:
            from _Legacy.main import GABAssetMind
            print("Avviata versione legacy dalla cartella _Legacy")
            app = GABAssetMind()
            app.run()
        except Exception as fallback_error:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Errore GAB AssetMind", 
                               f"Errore critico in entrambe le versioni:\n\n"
                               f"Versione Refactored: {e}\n"
                               f"Versione Legacy: {fallback_error}\n\n"
                               f"Controlla che tutti i moduli siano presenti.")
            root.destroy()
            
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Errore GAB AssetMind", 
                           f"Errore nella versione refactored:\n{e}\n\n"
                           f"La versione legacy è disponibile in _Legacy/")
        root.destroy()