#!/usr/bin/env python3
"""
GAB AssetMind - Portfolio Manager (Refactored Version v2.0)
File .pyw per avvio senza terminale su Windows

Versione con architettura modulare e performance ottimizzate
Per tornare alla versione legacy: usa GAB_AssetMind_legacy.pyw
"""

if __name__ == "__main__":
    try:
        # Importa la versione refactorizzata con architettura modulare
        from main_refactored import GABAssetMind
        
        print("GAB AssetMind v2.0 (Refactored) - Avvio in corso...")
        print("Architettura modulare caricata con successo")
        
        app = GABAssetMind()
        app.run()
        
    except ImportError as e:
        # Fallback automatico alla versione legacy se refactored non disponibile
        print(f"Fallback alla versione legacy: {e}")
        try:
            from main import GABAssetMind
            print("Avviata versione legacy")
            app = GABAssetMind()
            app.run()
        except Exception as fallback_error:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Errore GAB AssetMind", 
                               f"Errore critico (anche nel fallback legacy):\n{fallback_error}")
            root.destroy()
            
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Errore GAB AssetMind", 
                           f"Errore nella versione refactorizzata:\n{e}\n\n"
                           f"Prova ad usare GAB_AssetMind_legacy.pyw per la versione precedente")
        root.destroy()