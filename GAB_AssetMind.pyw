#!/usr/bin/env python3
"""
GAB AssetMind - Portfolio Manager
File .pyw per avvio senza terminale su Windows
"""

if __name__ == "__main__":
    try:
        from main import GABAssetMind
        app = GABAssetMind()
        app.run()
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Errore GAB AssetMind", f"Errore critico: {e}")
        root.destroy()