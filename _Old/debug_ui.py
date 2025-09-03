#!/usr/bin/env python3
"""Debug UI per verificare errori interfaccia"""

import sys
import traceback
from main import GABAssetMind

try:
    print("Avvio app...")
    app = GABAssetMind()
    
    print("Caricamento dati portfolio...")
    app.load_portfolio_data()
    
    print("Controllo numero items in TreeView...")
    items = app.portfolio_tree.get_children()
    print(f"Items nella tabella: {len(items)}")
    
    if len(items) == 0:
        print("ERRORE: Nessun item nella tabella!")
        print("Tentativo caricamento manuale...")
        
        df = app.portfolio_manager.get_current_assets_only()
        print(f"DataFrame ha {len(df)} record")
        
        if not df.empty:
            print("Chiamata update_portfolio_table...")
            app.update_portfolio_table(df)
            
            items = app.portfolio_tree.get_children()
            print(f"Dopo update: {len(items)} items")
    
    print("Avvio interfaccia...")
    app.root.mainloop()
    
except Exception as e:
    print(f"ERRORE: {e}")
    traceback.print_exc()