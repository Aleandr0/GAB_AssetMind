#!/usr/bin/env python3
"""
GAB AssetMind - Portfolio Management Application (Refactored Version)
Applicazione per la gestione professionale di portafogli diversificati con interfaccia moderna

Architettura modulare con separazione delle responsabilità:
- UI Components: Componenti interfaccia separati e riutilizzabili  
- Configuration: Configurazione centralizzata per colori, dimensioni, mappature
- Utils: Utilità per validazione, formattazione, gestione errori
- Models: Logica di business e persistenza dati

Autore: GAB AssetMind Team
Versione: 2.0 (Refactored)
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import sys
import os
import glob
from typing import Optional, Dict, Any
import pandas as pd

# Import dei moduli refactored
from config import UIConfig, DatabaseConfig, Messages, get_application_directory
from utils import ErrorHandler, DataCache, safe_execute
from models import PortfolioManager
from ui_components import NavigationBar, PortfolioTable
from asset_form import AssetForm
from charts_ui import ChartsUI
from export_ui import ExportUI

# Configurazione tema dell'applicazione
ctk.set_appearance_mode("light")  # Modalità chiara
ctk.set_default_color_theme("blue")  # Tema blu

class GABAssetMind:
    """
    Applicazione principale per la gestione portfolio (Versione Refactored)
    
    Architettura modulare con componenti specializzati:
    - NavigationBar: Barra navigazione e controlli globali
    - PortfolioTable: Tabella portfolio con filtri avanzati  
    - AssetForm: Form gestione asset con validazione
    - ChartsUI: Interfaccia grafici e analytics
    - ExportUI: Esportazione dati in vari formati
    """
    
    def __init__(self):
        """Inizializza l'applicazione con architettura modulare"""
        # Finestra principale
        self.root = ctk.CTk()
        self.root.title("GAB AssetMind - Portfolio Manager (Refactored)")
        self.root.geometry(UIConfig.WINDOW_SIZES['main'])
        
        # Sistema di gestione dati
        self.portfolio_manager: Optional[PortfolioManager] = None
        self.data_cache = DataCache()
        self.current_portfolio_file = DatabaseConfig.DEFAULT_PORTFOLIO_FILE
        
        # Stato applicazione
        self.current_page = "Portfolio"
        self.page_frames: Dict[str, ctk.CTkFrame] = {}
        self.active_filter_popup: Optional[tk.Toplevel] = None
        
        # Componenti UI specializzati
        self.navbar: Optional[NavigationBar] = None
        self.portfolio_table: Optional[PortfolioTable] = None
        self.asset_form: Optional[AssetForm] = None
        self.charts_ui: Optional[ChartsUI] = None
        self.export_ui: Optional[ExportUI] = None
        
        # Inizializzazione
        self._initialize_portfolio_system()
        self._setup_ui()
        self._setup_callbacks()
        self._load_initial_data()
    
    def _initialize_portfolio_system(self):
        """Inizializza il sistema di gestione portfolio"""
        try:
            app_dir = get_application_directory()
            default_path = os.path.join(app_dir, self.current_portfolio_file)
            self.portfolio_manager = PortfolioManager(default_path)
            print(f"Portfolio system initialized: {default_path}")
            
        except Exception as e:
            error_msg = ErrorHandler.handle_file_error(e, "inizializzazione sistema portfolio")
            messagebox.showerror("Errore Critico", error_msg)
            sys.exit(1)
    
    def _setup_ui(self):
        """Configura l'interfaccia utente modulare"""
        try:
            # Navbar globale
            self.navbar = NavigationBar(self.root, self.portfolio_manager)
            navbar_frame = self.navbar.create_navbar()
            
            # Container per le pagine
            self.main_container = ctk.CTkFrame(self.root)
            self.main_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            
            # Crea le pagine
            self._create_page_frames()
            self._setup_specialized_components()
            
            # Aggiorna lista portfolio
            self._refresh_portfolio_list()
            
            # Mostra pagina di default
            self.show_page("Portfolio")
            
        except Exception as e:
            error_msg = ErrorHandler.handle_ui_error(e, "setup interfaccia")
            messagebox.showerror("Errore UI", error_msg)
    
    def _create_page_frames(self):
        """Crea i frame per le diverse pagine"""
        page_names = ["Portfolio", "Asset", "Grafici", "Export"]
        
        for page_name in page_names:
            frame = ctk.CTkFrame(self.main_container)
            self.page_frames[page_name] = frame
    
    def _setup_specialized_components(self):
        """Configura i componenti specializzati per ogni pagina"""
        # Portfolio Table Component
        self.portfolio_table = PortfolioTable(self.page_frames["Portfolio"], self.portfolio_manager)
        self.portfolio_table.create_table()
        
        # Asset Form Component  
        self.asset_form = AssetForm(self.page_frames["Asset"], self.portfolio_manager)
        self.asset_form.create_form()
        
        # Charts UI Component
        self.charts_ui = ChartsUI(self.page_frames["Grafici"], self.portfolio_manager)
        self.charts_ui.create_charts_interface()
        
        # Export UI Component
        self.export_ui = ExportUI(self.page_frames["Export"], self.portfolio_manager)
        self.export_ui.create_export_interface()
    
    def _setup_callbacks(self):
        """Configura i callback tra componenti"""
        # Navbar callbacks
        self.navbar.register_callback('page_changed', self.show_page)
        self.navbar.register_callback('portfolio_changed', self._switch_portfolio)
        self.navbar.register_callback('new_portfolio_requested', self._create_new_portfolio)
        
        # Portfolio Table callbacks
        self.portfolio_table.register_callback('view_changed', self._on_view_changed)
        self.portfolio_table.register_callback('asset_selected', self._on_asset_selected)
        self.portfolio_table.register_callback('filter_requested', self._show_column_filter)
        self.portfolio_table.register_callback('data_filtered', self._on_data_filtered)
        
        # Asset Form callbacks
        self.asset_form.register_callback('asset_saved', self._on_asset_saved)
        self.asset_form.register_callback('asset_deleted', self._on_asset_deleted)
        self.asset_form.register_callback('form_cleared', self._on_form_cleared)
        
        # Export UI callbacks
        self.export_ui.register_callback('export_completed', self._on_export_completed)
    
    def _load_initial_data(self):
        """Carica i dati iniziali dell'applicazione"""
        safe_execute(
            self._load_portfolio_data,
            error_handler=lambda e: print(f"Errore caricamento iniziale: {e}")
        )
    
    def show_page(self, page_name: str):
        """Mostra una pagina specifica nascondendo le altre"""
        try:
            # Nascondi tutte le pagine
            for frame in self.page_frames.values():
                frame.pack_forget()
            
            # Mostra la pagina richiesta
            if page_name in self.page_frames:
                self.page_frames[page_name].pack(fill="both", expand=True)
                self.current_page = page_name
                
                # Aggiorna l'evidenziazione del bottone attivo nella navbar
                if self.navbar:
                    self.navbar.update_active_button(page_name)
                
                # Refresh dei dati per pagine specifiche
                if page_name == "Portfolio":
                    self._load_portfolio_data()
                elif page_name == "Grafici":
                    self.charts_ui.refresh_charts()
                elif page_name == "Export":
                    self.export_ui.refresh_stats()
                    
        except Exception as e:
            error_msg = ErrorHandler.handle_ui_error(e, f"navigazione pagina {page_name}")
            messagebox.showerror("Errore Navigazione", error_msg)
    
    def _load_portfolio_data(self):
        """Carica i dati del portfolio e aggiorna l'interfaccia"""
        try:
            # Verifica cache
            cache_key = f"portfolio_data_{self.current_portfolio_file}"
            df = self.data_cache.get(cache_key)
            
            if df is None:
                # Carica dati in base alla modalità di visualizzazione
                if hasattr(self.portfolio_table, 'show_all_records') and self.portfolio_table.show_all_records:
                    df = self.portfolio_manager.load_data()
                else:
                    df = self.portfolio_manager.get_current_assets_only()
                
                # Cache dei dati
                self.data_cache.set(cache_key, df)
            
            # Aggiorna componenti
            if self.portfolio_table:
                self.portfolio_table.update_data(df)
                
            self._update_navbar_values()
            
        except Exception as e:
            error_msg = ErrorHandler.handle_data_error(e, "caricamento portfolio")
            print(f"Errore caricamento dati: {error_msg}")
    
    def _update_navbar_values(self):
        """Aggiorna i valori mostrati nella navbar"""
        try:
            # Calcola valore totale
            summary = self.portfolio_manager.get_portfolio_summary()
            total_value = summary.get('total_value', 0)
            
            # Calcola valore visibile se tabella disponibile
            visible_value = 0
            percentage = 0
            
            if self.portfolio_table:
                visible_value, _ = self.portfolio_table.get_visible_value()
                if total_value > 0:
                    percentage = (visible_value / total_value * 100)
            
            # Aggiorna navbar
            if self.navbar:
                if visible_value == total_value or percentage >= 99.9:
                    percentage = 100.0
                self.navbar.update_values(total_value, visible_value, percentage)
                
        except Exception as e:
            print(f"Errore aggiornamento valori navbar: {e}")
    
    def _refresh_portfolio_list(self):
        """Aggiorna la lista dei portfolio disponibili"""
        try:
            app_dir = get_application_directory()
            pattern = os.path.join(app_dir, "*.xlsx")
            excel_files = glob.glob(pattern)
            
            portfolio_files = [os.path.basename(f) for f in excel_files]
            if not portfolio_files:
                portfolio_files = [DatabaseConfig.DEFAULT_PORTFOLIO_FILE]
            
            portfolio_files.sort()
            
            if self.navbar:
                self.navbar.refresh_portfolio_list(portfolio_files, self.current_portfolio_file)
                
        except Exception as e:
            error_msg = ErrorHandler.handle_file_error(e, "refresh lista portfolio")
            print(f"Errore refresh portfolio: {error_msg}")
    
    def _switch_portfolio(self, selected_file: str):
        """Cambia il portfolio attivo"""
        try:
            if selected_file != self.current_portfolio_file:
                self.current_portfolio_file = selected_file
                
                # Costruisce il percorso completo
                app_dir = get_application_directory()
                full_path = os.path.join(app_dir, selected_file)
                
                # Aggiorna il PortfolioManager
                self.portfolio_manager = PortfolioManager(full_path)
                
                # Pulisce cache e ricarica
                self.data_cache.clear()
                
                # Aggiorna componenti con nuovo portfolio manager
                if self.portfolio_table:
                    self.portfolio_table.portfolio_manager = self.portfolio_manager
                if self.asset_form:
                    self.asset_form.portfolio_manager = self.portfolio_manager
                if self.charts_ui:
                    self.charts_ui.portfolio_manager = self.portfolio_manager
                if self.export_ui:
                    self.export_ui.portfolio_manager = self.portfolio_manager
                
                # Ricarica dati
                self._load_portfolio_data()
                
                print(f"Portfolio cambiato a: {selected_file}")
                
        except Exception as e:
            error_msg = ErrorHandler.handle_file_error(e, f"cambio portfolio {selected_file}")
            messagebox.showerror("Errore", error_msg)
            # Ripristina selezione precedente
            if self.navbar:
                self.navbar.portfolio_selector.set(self.current_portfolio_file)
    
    def _create_new_portfolio(self):
        """Crea un nuovo portfolio"""
        try:
            dialog = ctk.CTkInputDialog(text="Nome del nuovo portfolio:", title="Nuovo Portfolio")
            portfolio_name = dialog.get_input()
            
            if portfolio_name:
                if not portfolio_name.lower().endswith('.xlsx'):
                    portfolio_name += '.xlsx'
                
                app_dir = get_application_directory()
                new_file_path = os.path.join(app_dir, portfolio_name)
                
                if os.path.exists(new_file_path):
                    messagebox.showerror("Errore", f"Il portfolio '{portfolio_name}' esiste già!")
                    return
                
                # Crea nuovo portfolio
                new_portfolio_manager = PortfolioManager(new_file_path)
                self.current_portfolio_file = portfolio_name
                self.portfolio_manager = new_portfolio_manager
                
                # Aggiorna interfaccia
                self._refresh_portfolio_list()
                self.data_cache.clear()
                self._load_portfolio_data()
                
                messagebox.showinfo("Successo", f"Nuovo portfolio '{portfolio_name}' creato!")
                
        except Exception as e:
            error_msg = ErrorHandler.handle_file_error(e, "creazione nuovo portfolio")
            messagebox.showerror("Errore", error_msg)
    
    # Event handlers per callbacks componenti
    def _on_view_changed(self, view_type: str):
        """Gestisce il cambio di vista nella tabella portfolio"""
        self.data_cache.clear()  # Invalida cache
        self._load_portfolio_data()
    
    def _on_asset_selected(self, asset_id: int):
        """Gestisce la selezione di un asset"""
        if self.asset_form and self.asset_form.edit_asset(asset_id):
            self.show_page("Asset")
        else:
            messagebox.showerror("Errore", f"Impossibile caricare asset ID {asset_id}")
    
    def _on_asset_saved(self, asset_data: Dict[str, Any]):
        """Gestisce il salvataggio di un asset"""
        self.data_cache.clear()  # Invalida cache
        self._load_portfolio_data()
        
        # Refresh degli altri componenti
        if self.charts_ui:
            self.charts_ui.refresh_charts()
        if self.export_ui:
            self.export_ui.refresh_stats()
    
    def _on_asset_deleted(self, asset_id: int):
        """Gestisce l'eliminazione di un asset"""
        self.data_cache.clear()  # Invalida cache
        self._load_portfolio_data()
        
        # Refresh degli altri componenti
        if self.charts_ui:
            self.charts_ui.refresh_charts()
        if self.export_ui:
            self.export_ui.refresh_stats()
    
    def _on_form_cleared(self):
        """Gestisce la pulizia del form"""
        # Nessuna azione particolare necessaria
        pass
    
    def _on_export_completed(self, export_type: str, filename: str):
        """Gestisce il completamento di un export"""
        print(f"Export {export_type} completato: {filename}")
        # Potrebbe aggiornare statistiche o log di export in futuro
    
    def _show_column_filter(self, column: str):
        """Gestisce la richiesta di filtro per una colonna"""
        # Il filtro viene gestito direttamente dal componente PortfolioTable
        pass
    
    def _on_data_filtered(self, filtered_df: pd.DataFrame):
        """Gestisce i dati filtrati aggiornando i valori della navbar"""
        self._update_navbar_values()
    
    def run(self):
        """Avvia l'applicazione"""
        try:
            print("GAB AssetMind (Refactored) avviato con successo")
            print(f"Portfolio attivo: {self.current_portfolio_file}")
            print(f"Componenti caricati: {len([c for c in [self.navbar, self.portfolio_table, self.asset_form, self.charts_ui, self.export_ui] if c])}/5")
            
            self.root.mainloop()
            
        except KeyboardInterrupt:
            print("Applicazione interrotta dall'utente")
        except Exception as e:
            error_msg = ErrorHandler.handle_ui_error(e, "esecuzione principale")
            messagebox.showerror("Errore Critico", error_msg)
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Pulizia risorse alla chiusura"""
        try:
            if self.charts_ui:
                self.charts_ui.cleanup()
            
            if self.data_cache:
                self.data_cache.clear()
                
            print("Cleanup completato")
            
        except Exception as e:
            print(f"Errore durante cleanup: {e}")

def main():
    """Funzione principale di avvio"""
    try:
        # Verifica requisiti di sistema
        print("Avvio GAB AssetMind (Refactored Version)...")
        print(f"Python: {sys.version}")
        print(f"Working Directory: {os.getcwd()}")
        
        # Avvia applicazione
        app = GABAssetMind()
        app.run()
        
    except Exception as e:
        # Gestione errori critici
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Errore Critico GAB AssetMind", 
            f"Impossibile avviare l'applicazione:\n\n{e}\n\nContattare il supporto tecnico."
        )
        print(f"Errore critico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()