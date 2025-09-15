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
from logging_config import get_logger, set_debug_mode
from security_validation import PathSecurityValidator, SecurityError

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
        self.path_validator = PathSecurityValidator()
        
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
        
        # Centra la finestra dopo aver configurato tutto
        self._center_window()
    
    def _initialize_portfolio_system(self):
        """Inizializza il sistema di gestione portfolio"""
        try:
            app_dir = get_application_directory()
            default_path = os.path.join(app_dir, self.current_portfolio_file)
            self.portfolio_manager = PortfolioManager(default_path)
            self.logger = get_logger('main')
            self.logger.info(f"Portfolio system initialized: {default_path}")
            
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
        self.portfolio_table.register_callback('data_changed', self._on_data_changed)
        
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
        # Aggiorna i valori della navbar dopo il caricamento iniziale
        safe_execute(
            self._update_navbar_values,
            error_handler=lambda e: print(f"Errore aggiornamento navbar iniziale: {e}")
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
            self.logger.debug(f"Inizio caricamento dati portfolio")
            self.logger.debug(f"Portfolio table exists: {self.portfolio_table is not None}")
            
            # Verifica cache
            cache_key = f"portfolio_data_{self.current_portfolio_file}"
            df = self.data_cache.get(cache_key)
            
            if df is None:
                # Carica dati in base alla modalità di visualizzazione
                if hasattr(self.portfolio_table, 'show_all_records') and self.portfolio_table.show_all_records:
                    self.logger.debug("Caricando tutti i record")
                    df = self.portfolio_manager.load_data()
                else:
                    self.logger.debug("Caricando solo asset correnti")
                    df = self.portfolio_manager.get_current_assets_only()

                self.logger.debug(f"Dati caricati: {len(df)} righe")
                if not df.empty:
                    self.logger.debug(f"Colonne disponibili: {list(df.columns)}")
                
                # Cache dei dati
                self.data_cache.set(cache_key, df)
            else:
                self.logger.debug(f"Dati dalla cache: {len(df)} righe")
            
            # Aggiorna componenti
            if self.portfolio_table:
                self.logger.debug(f"Aggiornando portfolio_table con {len(df)} righe")
                self.portfolio_table.update_data(df)
                self.logger.debug("update_data() completato")

                # Refresh UI ottimizzato - solo update_idletasks
                try:
                    if hasattr(self, 'after'):  # Solo se la finestra è inizializzata
                        self.after(50, lambda: [
                            self.update_idletasks(),
                            self.logger.debug("UI refresh completato")
                        ])
                    else:
                        self.logger.debug("UI refresh skipped - finestra non inizializzata")
                except Exception as e:
                    self.logger.error(f"Errore refresh UI: {e}")
            else:
                self.logger.error("PROBLEMA - portfolio_table è None!")
                
            self._update_navbar_values()
            
        except Exception as e:
            error_msg = ErrorHandler.handle_data_error(e, "caricamento portfolio")
            self.logger.error(f"Errore caricamento dati: {error_msg}")
            import traceback
            self.logger.debug(f"Stack trace: {traceback.format_exc()}")
    
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
            self.logger.error(f"Errore aggiornamento valori navbar: {e}")
    
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
            self.logger.error(f"Errore refresh portfolio: {error_msg}")
    
    def _switch_portfolio(self, selected_file: str):
        """Cambia il portfolio attivo con validazione sicurezza"""
        try:
            if selected_file != self.current_portfolio_file:
                # Valida il path prima di procedere
                try:
                    app_dir = get_application_directory()
                    full_path = os.path.join(app_dir, selected_file)
                    validated_path = self.path_validator.validate_portfolio_path(full_path)

                    self.current_portfolio_file = selected_file
                    self.logger.info(f"Cambio portfolio validato: {validated_path}")

                    # Aggiorna il PortfolioManager con path sicuro
                    self.portfolio_manager = PortfolioManager(str(validated_path))

                except SecurityError as e:
                    self.logger.error(f"Portfolio non sicuro: {e}")
                    messagebox.showerror("Errore Sicurezza", f"Portfolio non sicuro: {e}")
                    return
                except Exception as e:
                    self.logger.error(f"Errore validazione portfolio: {e}")
                    messagebox.showerror("Errore", f"Errore validazione portfolio: {e}")
                    return
                
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
                
                self.logger.info(f"Portfolio cambiato a: {selected_file}")
                
        except Exception as e:
            error_msg = ErrorHandler.handle_file_error(e, f"cambio portfolio {selected_file}")
            messagebox.showerror("Errore", error_msg)
            # Ripristina selezione precedente
            if self.navbar:
                self.navbar.portfolio_selector.set(self.current_portfolio_file)
    
    def _create_new_portfolio(self):
        """Crea un nuovo portfolio con validazione sicurezza"""
        try:
            dialog = ctk.CTkInputDialog(text="Nome del nuovo portfolio:", title="Nuovo Portfolio")
            portfolio_name = dialog.get_input()

            if portfolio_name:
                try:
                    # Crea path sicuro per il nuovo portfolio
                    safe_path = self.path_validator.create_safe_portfolio_path(portfolio_name)

                    if safe_path.exists():
                        messagebox.showerror("Errore", f"Il portfolio '{safe_path.name}' esiste già!")
                        return

                    self.logger.info(f"Creando nuovo portfolio sicuro: {safe_path}")

                    # Crea nuovo portfolio con path validato
                    new_portfolio_manager = PortfolioManager(str(safe_path))
                    self.current_portfolio_file = safe_path.name
                    self.portfolio_manager = new_portfolio_manager

                except SecurityError as e:
                    self.logger.error(f"Nome portfolio non sicuro: {e}")
                    messagebox.showerror("Errore Sicurezza", f"Nome portfolio non sicuro: {e}")
                    return
                except Exception as e:
                    self.logger.error(f"Errore creazione portfolio sicuro: {e}")
                    messagebox.showerror("Errore", f"Errore creazione portfolio: {e}")
                    return
                
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
    
    def _on_data_changed(self):
        """Gestisce la modifica dei dati (es. dopo riordino) ricaricando tutto"""
        try:
            # Pulisce la cache per forzare il ricaricamento
            self.data_cache.clear()
            # Ricarica i dati del portfolio
            self._load_portfolio_data()
            self.logger.debug("Dati ricaricati dopo modifica")
        except Exception as e:
            self.logger.error(f"Errore nel ricaricamento dati: {e}")
    
    def _center_window(self):
        """Centra la finestra al centro dello schermo"""
        self.root.update_idletasks()
        
        # Usa direttamente le dimensioni della configurazione
        window_width = 1200
        window_height = 800
        
        # Ottieni le dimensioni dello schermo
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calcola la posizione per centrare la finestra
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        # Imposta la posizione della finestra
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def run(self):
        """Avvia l'applicazione"""
        try:
            self.logger.info("GAB AssetMind (Refactored) avviato con successo")
            self.logger.info(f"Portfolio attivo: {self.current_portfolio_file}")
            component_count = len([c for c in [self.navbar, self.portfolio_table, self.asset_form, self.charts_ui, self.export_ui] if c])
            self.logger.info(f"Componenti caricati: {component_count}/5")
            
            self.root.mainloop()
            
        except KeyboardInterrupt:
            self.logger.info("Applicazione interrotta dall'utente")
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

            if self.portfolio_table:
                self.portfolio_table.cleanup_performance_optimizers()

            if self.data_cache:
                self.data_cache.clear()

            self.logger.info("Cleanup completato")
            
        except Exception as e:
            self.logger.error(f"Errore durante cleanup: {e}")

def main():
    """Funzione principale di avvio"""
    try:
        # Inizializza logging prima di tutto
        logger = get_logger('startup')

        # Configura debug mode da variabile ambiente o argomenti
        debug_mode = (os.getenv('GAB_DEBUG', 'false').lower() == 'true' or
                     '--debug' in sys.argv or '-d' in sys.argv)
        if debug_mode:
            set_debug_mode(True)
            logger.info("Debug mode ATTIVATO")

        # Verifica requisiti di sistema
        logger.info("Avvio GAB AssetMind (Refactored Version)...")
        logger.info(f"Python: {sys.version}")
        logger.info(f"Working Directory: {os.getcwd()}")
        
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
        try:
            logger = get_logger('startup')
            logger.critical(f"Errore critico: {e}")
            import traceback
            logger.critical(f"Stack trace: {traceback.format_exc()}")
        except:
            # Fallback se anche il logging fallisce
            print(f"Errore critico: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
