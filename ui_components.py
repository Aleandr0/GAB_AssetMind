#!/usr/bin/env python3
"""
Componenti UI separati per GAB AssetMind
Divide la classe monolitica in componenti specializzati e riutilizzabili
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

from config import UIConfig, FieldMapping, AssetConfig, Messages
from utils import DateFormatter, CurrencyFormatter, DataValidator, ErrorHandler, safe_execute
from models import Asset, PortfolioManager
from logging_config import get_logger
from ui_performance import UIUpdateManager, LazyColumnResizer, UIRefreshOptimizer

class BaseUIComponent:
    """Classe base per tutti i componenti UI"""
    
    def __init__(self, parent, portfolio_manager: PortfolioManager):
        self.parent = parent
        self.portfolio_manager = portfolio_manager
        self.callbacks: Dict[str, Callable] = {}
        self.logger = get_logger(self.__class__.__name__)
    
    def register_callback(self, event_name: str, callback: Callable):
        """Registra un callback per un evento"""
        self.callbacks[event_name] = callback
    
    def trigger_callback(self, event_name: str, *args, **kwargs):
        """Esegue un callback se registrato"""
        if event_name in self.callbacks:
            safe_execute(
                lambda: self.callbacks[event_name](*args, **kwargs),
                error_handler=lambda e: self.logger.error(f"Errore callback {event_name}: {e}")
            )

class NavigationBar(BaseUIComponent):
    """Barra di navigazione principale dell'applicazione"""
    
    def __init__(self, parent, portfolio_manager: PortfolioManager):
        super().__init__(parent, portfolio_manager)
        self.navbar_frame = None
        self.total_value_label = None
        self.selected_value_label = None
        self.portfolio_selector = None
        self.current_portfolio_file = "portfolio_data.xlsx"
        self.nav_buttons = {}  # Dizionario per tracciare i bottoni di navigazione
        self.current_page = "Portfolio"  # Pagina attiva corrente
        
    def create_navbar(self) -> ctk.CTkFrame:
        """Crea la barra di navigazione completa"""
        self.navbar_frame = ctk.CTkFrame(self.parent, height=80)
        self.navbar_frame.pack(fill="x", padx=10, pady=5)
        self.navbar_frame.pack_propagate(False)
        
        self._create_values_section()
        self._create_portfolio_section()
        self._create_navigation_buttons()
        
        return self.navbar_frame
    
    def _create_values_section(self):
        """Crea la sezione valori (sinistra)"""
        values_frame = ctk.CTkFrame(self.navbar_frame, fg_color="transparent")
        values_frame.pack(side="left", padx=20, pady=7)
        
        # Valore totale
        self.total_value_label = ctk.CTkLabel(
            values_frame, 
            text="Valore Totale: €0",
            font=ctk.CTkFont(**UIConfig.FONTS['header']),
            text_color=(UIConfig.COLORS['primary'], "#14375e")
        )
        self.total_value_label.pack(pady=(3, 0))
        
        # Valore selezionato
        self.selected_value_label = ctk.CTkLabel(
            values_frame,
            text="Valore selezionato: €0",
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            text_color=(UIConfig.COLORS['primary'], "#14375e")
        )
        self.selected_value_label.pack(pady=(0, 3))
    
    def _create_portfolio_section(self):
        """Crea la sezione selezione portfolio (centro)"""
        portfolio_section = ctk.CTkFrame(self.navbar_frame, fg_color="transparent")
        portfolio_section.pack(side="left", padx=20, pady=7)
        
        # Label portfolio
        portfolio_label = ctk.CTkLabel(
            portfolio_section, 
            text="Portfolio:",
            font=ctk.CTkFont(**UIConfig.FONTS['subheader']),
            text_color=(UIConfig.COLORS['primary'], "#14375e")
        )
        portfolio_label.pack(side="top", pady=(0, 2))
        
        # Container per dropdown e pulsante nuovo
        selector_frame = ctk.CTkFrame(portfolio_section, fg_color="transparent")
        selector_frame.pack(side="top")
        
        # Dropdown selezione portfolio
        self.portfolio_selector = ctk.CTkComboBox(
            selector_frame,
            command=self._on_portfolio_changed,
            width=140, 
            height=28,
            font=ctk.CTkFont(**UIConfig.FONTS['small'])
        )
        self.portfolio_selector.pack(side="left", padx=(0, 5))
        
        # Pulsante per creare nuovo portfolio
        new_portfolio_btn = ctk.CTkButton(
            selector_frame,
            text="+",
            command=self._create_new_portfolio,
            width=30,
            height=28,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=UIConfig.COLORS['success'],
            hover_color=UIConfig.COLORS['success_hover']
        )
        new_portfolio_btn.pack(side="left")
    
    def _create_navigation_buttons(self):
        """Crea i bottoni di navigazione (destra)"""
        nav_buttons_frame = ctk.CTkFrame(self.navbar_frame, fg_color="transparent")
        nav_buttons_frame.pack(side="right", padx=20, pady=7)
        
        nav_buttons = [
            ("📊 Portfolio", "Portfolio"),
            ("📝 Asset", "Asset"),
            ("📈 Grafici", "Grafici"),
            ("📄 Export", "Export")
        ]
        
        for text, page in nav_buttons:
            # Colore iniziale: attivo per Portfolio, inattivo per gli altri
            if page == self.current_page:
                fg_color = UIConfig.COLORS['primary']
                hover_color = UIConfig.COLORS['primary_hover']
            else:
                fg_color = UIConfig.COLORS['secondary']
                hover_color = UIConfig.COLORS['secondary_hover']
            
            btn = ctk.CTkButton(
                nav_buttons_frame,
                text=text,
                command=lambda p=page: self._on_page_changed(p),
                **UIConfig.BUTTON_SIZES['medium'],
                font=ctk.CTkFont(**UIConfig.FONTS['button']),
                fg_color=fg_color,
                hover_color=hover_color
            )
            btn.pack(side="left", padx=2)
            
            # Salva riferimento al bottone
            self.nav_buttons[page] = btn
    
    def _on_page_changed(self, page: str):
        """Gestisce il cambio di pagina e aggiorna l'evidenziazione dei bottoni"""
        self.current_page = page
        self.update_active_button(page)
        self.trigger_callback('page_changed', page)
    
    def _on_portfolio_changed(self, selected_file: str):
        """Gestisce il cambio di portfolio"""
        self.trigger_callback('portfolio_changed', selected_file)
    
    def _create_new_portfolio(self):
        """Crea un nuovo portfolio"""
        self.trigger_callback('new_portfolio_requested')
    
    def update_active_button(self, active_page: str):
        """Aggiorna l'evidenziazione del bottone attivo"""
        for page, button in self.nav_buttons.items():
            if page == active_page:
                # Bottone attivo - colore primario
                try:
                    button.configure(
                        fg_color=UIConfig.COLORS['primary'],
                        hover_color=UIConfig.COLORS['primary_hover']
                    )
                except Exception as e:
                    self.logger.error(f"Errore aggiornamento bottone attivo {page}: {e}")
            else:
                # Bottoni inattivi - colore secondario  
                try:
                    button.configure(
                        fg_color=UIConfig.COLORS['secondary'],
                        hover_color=UIConfig.COLORS['secondary_hover']
                    )
                except Exception as e:
                    self.logger.error(f"Errore aggiornamento bottone inattivo {page}: {e}")
    
    def update_values(self, total_value: float, selected_value: float = 0, percentage: float = 0):
        """Aggiorna i valori visualizzati"""
        safe_execute(lambda: self.total_value_label.configure(
            text=f"Valore Totale: €{total_value:,.2f}"
        ))
        
        if percentage > 0:
            safe_execute(lambda: self.selected_value_label.configure(
                text=f"Valore selezionato: €{selected_value:,.2f} ({percentage:.1f}%)"
            ))
        else:
            safe_execute(lambda: self.selected_value_label.configure(
                text=f"Valore selezionato: €{selected_value:,.2f}"
            ))
    
    def refresh_portfolio_list(self, portfolio_files: List[str], current_file: str):
        """Aggiorna la lista dei portfolio disponibili"""
        safe_execute(lambda: self.portfolio_selector.configure(values=portfolio_files))
        safe_execute(lambda: self.portfolio_selector.set(current_file))

class PortfolioTable(BaseUIComponent):
    """Componente tabella portfolio con filtri e controlli"""
    
    def __init__(self, parent, portfolio_manager: PortfolioManager):
        super().__init__(parent, portfolio_manager)
        self.table_frame = None
        self.portfolio_tree = None
        self.column_filters = {}
        self.show_all_records = False
        self.tree_style = None
        self.zoom_level = 100
        self.active_filter_popup = None

        # Controlli UI
        self.records_btn = None
        self.assets_btn = None
        self.zoom_label = None
        self.v_scrollbar = None
        self.h_scrollbar = None

        # Performance optimizers
        self.update_manager = None
        self.column_resizer = None
        self.refresh_optimizer = None
    
    def create_table(self) -> ctk.CTkFrame:
        """Crea la tabella portfolio completa"""
        self.table_frame = ctk.CTkFrame(self.parent)
        self.table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self._create_controls()
        self._create_tree_view()
        self._setup_tree_style()
        self._initialize_performance_optimizers()
        
        return self.table_frame
    
    def _create_controls(self):
        """Crea i controlli sopra la tabella"""
        controls_frame = ctk.CTkFrame(self.table_frame, height=50)
        controls_frame.pack(fill="x", padx=5, pady=5)
        controls_frame.pack_propagate(False)
        
        # Toggle Record/Asset (sinistra)
        toggle_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        toggle_frame.pack(side="left", padx=10, pady=10)
        
        self.records_btn = ctk.CTkButton(
            toggle_frame,
            text="Record 0",
            command=self._toggle_to_records,
            **UIConfig.BUTTON_SIZES['medium'],
            font=ctk.CTkFont(**UIConfig.FONTS['button']),
            fg_color=UIConfig.COLORS['secondary'],
            hover_color=UIConfig.COLORS['secondary_hover']
        )
        self.records_btn.pack(side="left", padx=(0, 5))
        
        self.assets_btn = ctk.CTkButton(
            toggle_frame,
            text="Asset 0",
            command=self._toggle_to_assets,
            **UIConfig.BUTTON_SIZES['medium'],
            font=ctk.CTkFont(**UIConfig.FONTS['button']),
            fg_color=UIConfig.COLORS['primary'],
            hover_color=UIConfig.COLORS['primary_hover']
        )
        self.assets_btn.pack(side="left")
        
        # Controlli zoom (centro)
        zoom_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        zoom_frame.pack(side="right", padx=10, pady=10)
        
        ctk.CTkLabel(
            zoom_frame,
            text="Zoom:",
            font=ctk.CTkFont(**UIConfig.FONTS['text'])
        ).pack(side="left", padx=(0, 5))
        
        zoom_out_btn = ctk.CTkButton(
            zoom_frame,
            text="-",
            command=self._zoom_out,
            width=30,
            height=28,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        zoom_out_btn.pack(side="left", padx=2)
        
        self.zoom_label = ctk.CTkLabel(
            zoom_frame,
            text="100%",
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            width=50
        )
        self.zoom_label.pack(side="left", padx=5)
        
        zoom_in_btn = ctk.CTkButton(
            zoom_frame,
            text="+",
            command=self._zoom_in,
            width=30,
            height=28,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        zoom_in_btn.pack(side="left", padx=2)
        
        # Bottone pulisci filtri (accanto ai controlli Record/Asset)
        clear_filters_btn = ctk.CTkButton(
            toggle_frame,
            text="🗑️ Pulisci Filtri",
            command=self.clear_all_filters,
            **UIConfig.BUTTON_SIZES['medium'],
            font=ctk.CTkFont(**UIConfig.FONTS['button']),
            fg_color=UIConfig.COLORS['warning'],
            hover_color=UIConfig.COLORS['warning_hover']
        )
        clear_filters_btn.pack(side="left", padx=(10, 0))
        
        # Pulsante Riordino 
        sort_btn = ctk.CTkButton(
            toggle_frame,
            text="📊 Riordino",
            command=self._sort_records,
            **UIConfig.BUTTON_SIZES['medium'],
            font=ctk.CTkFont(**UIConfig.FONTS['button']),
            fg_color=UIConfig.COLORS['info'],
            hover_color=UIConfig.COLORS['info_hover']
        )
        sort_btn.pack(side="left", padx=(10, 0))
        
        # Pulsante Colora Storici 
        color_btn = ctk.CTkButton(
            toggle_frame,
            text="🎨 Colora Storici",
            command=self._color_historical_records,
            **UIConfig.BUTTON_SIZES['medium'],
            font=ctk.CTkFont(**UIConfig.FONTS['button']),
            fg_color=UIConfig.COLORS['success'],
            hover_color=UIConfig.COLORS['success_hover']
        )
        color_btn.pack(side="left", padx=(10, 0))
        
        # Testo istruzioni filtri (sulla stessa linea)
        instruction_label = ctk.CTkLabel(
            toggle_frame,
            text="Click column header to filter",
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            text_color=UIConfig.COLORS['secondary']
        )
        instruction_label.pack(side="left", padx=(20, 0))
    
    def _create_tree_view(self):
        """Crea il TreeView per la tabella"""
        tree_container = ctk.CTkFrame(self.table_frame)
        tree_container.pack(fill="both", expand=True, padx=5, pady=5)
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Definizione colonne
        columns = (
            "ID", "Category", "Position", "Asset Name", "ISIN", "Ticker", "Risk Level",
            "Created At", "Created Amount", "Created Unit Price", "Created Total Value",
            "Updated At", "Updated Amount", "Updated Unit Price", "Updated Total Value",
            "Accumulation Plan", "Accumulation Amount", "Income Per Year", "Rental Income", "Note"
        )
        
        # TreeView
        self.portfolio_tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            height=15
        )
        self.portfolio_tree.grid(row=0, column=0, sticky="nsew")
        
        # Configurazione colonne
        self._configure_columns(columns)
        
        # Scrollbars
        self.v_scrollbar = ttk.Scrollbar(
            tree_container,
            orient="vertical",
            command=self.portfolio_tree.yview
        )
        self.portfolio_tree.configure(yscrollcommand=self.v_scrollbar.set)
        
        self.h_scrollbar = ttk.Scrollbar(
            tree_container,
            orient="horizontal",
            command=self.portfolio_tree.xview
        )
        self.portfolio_tree.configure(xscrollcommand=self.h_scrollbar.set)
        
        # Posizionamento scrollbars
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Eventi
        self.portfolio_tree.bind("<Double-1>", self._on_double_click)
        
        # Bind click su header per filtri
        for col in columns:
            self.portfolio_tree.heading(col, command=lambda c=col: self._show_column_filter(c))
        
        # Inizializza gli header senza filtri
        self._update_column_headers()
    
    def _configure_columns(self, columns: tuple):
        """Configura le colonne della tabella"""
        # Larghezze aumentate per garantire leggibilità completa dei titoli
        column_widths = {
            "ID": 60, "Category": 120, "Position": 120, "Asset Name": 200,
            "ISIN": 80, "Ticker": 80, "Risk Level": 120,
            "Created At": 120, "Created Amount": 160, "Created Unit Price": 140,
            "Created Total Value": 150, "Updated At": 120, "Updated Amount": 160,
            "Updated Unit Price": 140, "Updated Total Value": 150,
            "Accumulation Plan": 180, "Accumulation Amount": 180,
            "Income Per Year": 160, "Rental Income": 140, "Note": 250
        }
        
        # Titoli su una riga ma abbreviati per garantire leggibilità
        column_headers = {
            "ID": "ID ▼",
            "Category": "Category ▼",
            "Position": "Position ▼", 
            "Asset Name": "Asset Name ▼",
            "ISIN": "ISIN ▼",
            "Ticker": "Ticker ▼",
            "Risk Level": "Risk Level ▼",
            "Created At": "Created At ▼",
            "Created Amount": "Created Amount ▼",
            "Created Unit Price": "Created Price ▼",
            "Created Total Value": "Created Total ▼",
            "Updated At": "Updated At ▼",
            "Updated Amount": "Updated Amount ▼",
            "Updated Unit Price": "Updated Price ▼",
            "Updated Total Value": "Updated Total ▼",
            "Accumulation Plan": "Accumulation Plan ▼",
            "Accumulation Amount": "Accumulation Amount ▼",
            "Income Per Year": "Income Per Year ▼",
            "Rental Income": "Rental Income ▼",
            "Note": "Note ▼"
        }
        
        for col in columns:
            width = column_widths.get(col, 120)
            header_text = column_headers.get(col, f"{col}\n▼")
            self.portfolio_tree.heading(col, text=header_text, anchor="w")
            self.portfolio_tree.column(col, width=width, anchor="w")
    
    def _setup_tree_style(self):
        """Configura lo stile del TreeView"""
        self.tree_style = ttk.Style()
        self.tree_style.configure(
            "Portfolio.Treeview",
            background="white",
            foreground="black",
            fieldbackground="white",
            font=("TkDefaultFont", 9),
            rowheight=25
        )
        
        # Stile per record storici (azzurro)
        self.tree_style.configure(
            "Historical.Treeview",
            background="white",
            foreground="#0066CC",  # Azzurro
            fieldbackground="white",
            font=("TkDefaultFont", 9),
            rowheight=25
        )
        
        # Configurazione header con altezza aumentata
        self.tree_style.configure(
            "Portfolio.Treeview.Heading",
            background="#f0f0f0",
            foreground="black",
            font=("TkDefaultFont", 9, "bold"),
            relief="raised",
            borderwidth=1,
            # Forza altezza minima per due righe
            minsize=50,
            padding=[5, 15, 5, 15]  # left, top, right, bottom
        )
        
        # Configurazione diretta dell'altezza dell'header
        try:
            # Imposta altezza fissa agli header
            self.portfolio_tree.tk.call('style', 'configure', 'Portfolio.Treeview.Heading', '-rowheight', 50)
        except:
            pass
            
        self.portfolio_tree.configure(style="Portfolio.Treeview")

    def _initialize_performance_optimizers(self):
        """Inizializza i sistemi di ottimizzazione performance"""
        try:
            self.update_manager = UIUpdateManager(self.parent)
            self.column_resizer = LazyColumnResizer(self.portfolio_tree, self.parent)
            self.refresh_optimizer = UIRefreshOptimizer(self.parent)

            self.logger.info("Performance optimizers inizializzati")
        except Exception as e:
            self.logger.error(f"Errore inizializzazione performance optimizers: {e}")
    
    def _toggle_to_records(self):
        """Passa alla vista record (tutti)"""
        self.show_all_records = True
        self.records_btn.configure(
            fg_color=UIConfig.COLORS['primary'],
            hover_color=UIConfig.COLORS['primary_hover']
        )
        self.assets_btn.configure(
            fg_color=UIConfig.COLORS['secondary'],
            hover_color=UIConfig.COLORS['secondary_hover']
        )
        # Ricarica i dati per la nuova vista
        self._apply_filters()
        self.trigger_callback('view_changed', 'records')
    
    def _toggle_to_assets(self):
        """Passa alla vista asset (solo attuali)"""
        self.show_all_records = False
        self.assets_btn.configure(
            fg_color=UIConfig.COLORS['primary'],
            hover_color=UIConfig.COLORS['primary_hover']
        )
        self.records_btn.configure(
            fg_color=UIConfig.COLORS['secondary'],
            hover_color=UIConfig.COLORS['secondary_hover']
        )
        # Ricarica i dati per la nuova vista
        self._apply_filters()
        self.trigger_callback('view_changed', 'assets')
    
    def _zoom_in(self):
        """Aumenta lo zoom della tabella"""
        if self.zoom_level < 150:
            self.zoom_level += 10
            self._apply_zoom_optimized()

    def _zoom_out(self):
        """Diminuisce lo zoom della tabella"""
        if self.zoom_level > 70:
            self.zoom_level -= 10
            self._apply_zoom_optimized()
    
    def _apply_zoom_optimized(self):
        """Applica il livello di zoom corrente con ottimizzazioni"""
        if not self.update_manager:
            self._apply_zoom()  # Fallback
            return

        # Usa update manager per debounce dello zoom
        self.update_manager.schedule_update(
            "apply_zoom",
            self._apply_zoom_immediate
        )

    def _apply_zoom_immediate(self):
        """Applica zoom senza debouncing - versione ottimizzata"""
        base_font_size = 9
        new_font_size = int(base_font_size * (self.zoom_level / 100))
        new_height = int(25 * (self.zoom_level / 100))

        self.tree_style.configure(
            "Portfolio.Treeview",
            font=("TkDefaultFont", new_font_size),
            rowheight=new_height
        )

        # Ricalcola altezza header con zoom
        zoom_padding_v = max(15, int(15 * (self.zoom_level / 100)))
        zoom_height = max(50, int(50 * (self.zoom_level / 100)))

        self.tree_style.configure(
            "Portfolio.Treeview.Heading",
            font=("TkDefaultFont", new_font_size, "bold"),
            padding=[5, zoom_padding_v, 5, zoom_padding_v]
        )

        try:
            self.portfolio_tree.tk.call('style', 'configure', 'Portfolio.Treeview.Heading', '-rowheight', zoom_height)
        except:
            pass

        # Notifica column resizer del nuovo zoom
        if self.column_resizer:
            self.column_resizer.update_zoom_factor(self.zoom_level)

        self.zoom_label.configure(text=f"{self.zoom_level}%")

        # Usa refresh ottimizzato
        if self.refresh_optimizer:
            self.refresh_optimizer.smart_refresh()

    def _apply_zoom(self):
        """Metodo fallback per zoom senza ottimizzazioni"""
        base_font_size = 9
        new_font_size = int(base_font_size * (self.zoom_level / 100))
        new_height = int(25 * (self.zoom_level / 100))

        self.tree_style.configure(
            "Portfolio.Treeview",
            font=("TkDefaultFont", new_font_size),
            rowheight=new_height
        )

        self.zoom_label.configure(text=f"{self.zoom_level}%")
        self._update_scrollbars()
    
    def _update_column_widths(self):
        """Aggiorna le larghezze delle colonne proporzionalmente al zoom"""
        try:
            # Larghezze base delle colonne (aggiornate per leggibilità)
            base_column_widths = {
                "ID": 60, "Category": 120, "Position": 120, "Asset Name": 200,
                "ISIN": 80, "Ticker": 80, "Risk Level": 120,
                "Created At": 120, "Created Amount": 160, "Created Unit Price": 140,
                "Created Total Value": 150, "Updated At": 120, "Updated Amount": 160,
                "Updated Unit Price": 140, "Updated Total Value": 150,
                "Accumulation Plan": 180, "Accumulation Amount": 180,
                "Income Per Year": 160, "Rental Income": 140, "Note": 250
            }
            
            # Calcola il fattore di zoom
            zoom_factor = self.zoom_level / 100
            
            # Aggiorna le larghezze di tutte le colonne
            for col in self.portfolio_tree['columns']:
                base_width = base_column_widths.get(col, 120)
                new_width = int(base_width * zoom_factor)
                self.portfolio_tree.column(col, width=new_width)
                
        except Exception as e:
            self.logger.error(f"Errore aggiornamento larghezza colonne: {e}")
    
    def _update_scrollbars(self):
        """Aggiorna la visibilità delle scrollbar"""
        try:
            self.parent.after(50, lambda: [
                self.v_scrollbar.grid() if self.portfolio_tree.yview() != (0.0, 1.0) else self.v_scrollbar.grid_remove(),
                self.h_scrollbar.grid() if self.portfolio_tree.xview() != (0.0, 1.0) else self.h_scrollbar.grid_remove()
            ])
        except Exception as e:
            self.logger.error(f"Errore aggiornamento scrollbar: {e}")
    
    def _on_double_click(self, event):
        """Gestisce il doppio click su una riga"""
        item = self.portfolio_tree.selection()[0] if self.portfolio_tree.selection() else None
        if item:
            values = self.portfolio_tree.item(item, "values")
            if values:
                asset_id = int(values[0])
                self.trigger_callback('asset_selected', asset_id)
    
    def _show_column_filter(self, column: str):
        """Mostra il filtro per una colonna specifica"""
        try:
            # Chiudi popup precedente se aperto
            if hasattr(self, 'active_filter_popup') and self.active_filter_popup:
                self.active_filter_popup.destroy()
                self.active_filter_popup = None
            
            # Ottieni i dati appropriati per i valori unici
            if self.show_all_records:
                df = self.portfolio_manager.load_data()
            else:
                df = self.portfolio_manager.get_current_assets_only()
            if df.empty:
                return
            
            # Converti il nome colonna display in nome DataFrame
            from config import FieldMapping
            db_column = FieldMapping.DISPLAY_TO_DB.get(column, column.lower().replace(' ', '_'))
            
            if db_column not in df.columns:
                return
            
            # Ottieni valori unici per la colonna
            unique_values = df[db_column].fillna('N/A').astype(str).unique()
            unique_values = sorted([v for v in unique_values if v != ''])
            
            if not unique_values:
                return
            
            # Crea popup filtro
            self._create_filter_popup(column, db_column, unique_values)
            
        except Exception as e:
            self.logger.error(f"Errore nel filtro colonna {column}: {e}")
    
    def _create_filter_popup(self, display_column: str, db_column: str, values: list):
        """Crea il popup per il filtro colonna (stile legacy semplificato)"""
        import customtkinter as ctk
        
        # Crea finestra popup CTk per consistenza
        popup = ctk.CTkToplevel(self.parent)
        popup.title(f"Filter: {display_column}")
        popup.geometry("280x450")
        popup.transient(self.parent)
        popup.grab_set()
        
        self.active_filter_popup = popup
        
        # Header
        header_label = ctk.CTkLabel(popup, text=f"Filter by {display_column}",
                                   font=ctk.CTkFont(**UIConfig.FONTS['subheader']))
        header_label.pack(pady=(15, 10))
        
        # Search box per filtri di testo (solo per campi testuali)
        if db_column in ['asset_name', 'position', 'note', 'isin', 'ticker', 'accumulation_plan']:
            search_entry = ctk.CTkEntry(popup, placeholder_text="Search...", width=240)
            search_entry.pack(pady=(0, 10), padx=20)
        else:
            search_entry = None
        
        # Frame scrollabile per i checkbox
        checkbox_frame = ctk.CTkScrollableFrame(popup, width=240, height=280)
        checkbox_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Ottieni filtri attivi per questa colonna
        active_filters = self.column_filters.get(db_column, set())
        
        # Crea checkbox per ogni valore unico
        checkboxes = {}
        for value in values:
            # Determina se deve essere selezionato (se non ci sono filtri, seleziona tutti)
            is_selected = len(active_filters) == 0 or value in active_filters
            
            checkbox = ctk.CTkCheckBox(
                checkbox_frame,
                text=str(value),
                font=ctk.CTkFont(**UIConfig.FONTS['text'])
            )
            checkbox.pack(anchor="w", pady=2, padx=5)
            
            if is_selected:
                checkbox.select()
            else:
                checkbox.deselect()
                
            checkboxes[value] = checkbox
        
        # Funzione ricerca in tempo reale
        def on_search(*args):
            if search_entry:
                search_text = search_entry.get().lower()
                for value, checkbox in checkboxes.items():
                    value_text = str(value).lower()
                    if search_text in value_text:
                        checkbox.pack(anchor="w", pady=2, padx=5)
                    else:
                        checkbox.pack_forget()
        
        if search_entry:
            search_entry.bind('<KeyRelease>', on_search)
        
        # Frame bottoni
        button_frame = ctk.CTkFrame(popup, fg_color="transparent")
        button_frame.pack(fill="x", pady=10, padx=20)
        
        # Bottone Select All
        def select_all():
            for checkbox in checkboxes.values():
                checkbox.select()
        
        select_all_btn = ctk.CTkButton(
            button_frame, text="Select All", command=select_all,
            width=80, height=28, font=ctk.CTkFont(**UIConfig.FONTS['text'])
        )
        select_all_btn.pack(side="left", padx=(0, 5))
        
        # Bottone Clear All
        def clear_all():
            for checkbox in checkboxes.values():
                checkbox.deselect()
        
        clear_all_btn = ctk.CTkButton(
            button_frame, text="Clear All", command=clear_all,
            width=80, height=28, font=ctk.CTkFont(**UIConfig.FONTS['text']),
            fg_color=UIConfig.COLORS['secondary']
        )
        clear_all_btn.pack(side="left", padx=5)
        
        # Bottone Apply
        def apply_filter():
            # Raccogli valori selezionati
            selected_values = set()
            for value, checkbox in checkboxes.items():
                if checkbox.get():
                    selected_values.add(str(value))
            
            # Applica o rimuovi filtro
            if len(selected_values) == len(checkboxes) or len(selected_values) == 0:
                # Se tutti selezionati o nessuno, rimuovi filtro
                self.column_filters.pop(db_column, None)
            else:
                self.column_filters[db_column] = selected_values
            
            # Aggiorna visualizzazione
            self._apply_filters()
            self._update_column_headers()
            
            popup.destroy()
            self.active_filter_popup = None
        
        apply_btn = ctk.CTkButton(
            button_frame, text="Apply", command=apply_filter,
            width=80, height=28, font=ctk.CTkFont(**UIConfig.FONTS['text']),
            fg_color=UIConfig.COLORS['success']
        )
        apply_btn.pack(side="right")
        
        # Chiusura popup
        def on_close():
            self.active_filter_popup = None
            popup.destroy()
        
        popup.protocol("WM_DELETE_WINDOW", on_close)
    
    def _apply_filters(self):
        """Applica i filtri attivi ai dati"""
        try:
            # Carica dati base
            if self.show_all_records:
                df = self.portfolio_manager.load_data()
            else:
                df = self.portfolio_manager.get_current_assets_only()
            
            # Applica filtri colonna
            for column, filter_values in self.column_filters.items():
                if column in df.columns and filter_values:
                    # Converte i valori della colonna in stringa per il confronto
                    df_values = df[column].fillna('N/A').astype(str)
                    df = df[df_values.isin(filter_values)]
            
            # Aggiorna la tabella con i dati filtrati
            self.update_data(df)
            
            # Notifica il cambiamento per aggiornare i valori
            self.trigger_callback('data_filtered', df)
            
        except Exception as e:
            self.logger.error(f"Errore nell'applicazione filtri: {e}")
    
    def _update_column_headers(self):
        """Aggiorna le intestazioni delle colonne per mostrare i filtri attivi con asterisco più grande"""
        try:
            # Mappa per i nomi delle colonne display -> dataframe
            from config import FieldMapping
            
            # Titoli su una riga con mapping per filtri
            column_headers_base = {
                "ID": "ID",
                "Category": "Category",
                "Position": "Position", 
                "Asset Name": "Asset Name",
                "ISIN": "ISIN",
                "Ticker": "Ticker",
                "Risk Level": "Risk Level",
                "Created At": "Created At",
                "Created Amount": "Created Amount",
                "Created Unit Price": "Created Price",
                "Created Total Value": "Created Total",
                "Updated At": "Updated At",
                "Updated Amount": "Updated Amount",
                "Updated Unit Price": "Updated Price",
                "Updated Total Value": "Updated Total",
                "Accumulation Plan": "Accumulation Plan",
                "Accumulation Amount": "Accumulation Amount",
                "Income Per Year": "Income Per Year",
                "Rental Income": "Rental Income",
                "Note": "Note"
            }
            
            for display_name, db_name in FieldMapping.DISPLAY_TO_DB.items():
                base_header = column_headers_base.get(display_name, display_name)
                
                if db_name in self.column_filters:
                    # Mostra asterisco doppio più visibile per indicare filtro attivo
                    header_text = f"{base_header} ▼ **"
                else:
                    # Intestazione normale con triangolo
                    header_text = f"{base_header} ▼"
                
                # Aggiorna header (se la colonna esiste nella TreeView)
                try:
                    self.portfolio_tree.heading(display_name, text=header_text)
                except:
                    pass  # Colonna non esistente nel TreeView, ignora
                    
        except Exception as e:
            self.logger.error(f"Errore aggiornamento headers: {e}")
    
    def clear_all_filters(self):
        """Pulisce tutti i filtri attivi"""
        self.column_filters.clear()
        self._apply_filters()
        self._update_column_headers()
        
        if hasattr(self, 'active_filter_popup') and self.active_filter_popup:
            self.active_filter_popup.destroy()
            self.active_filter_popup = None

    def cleanup_performance_optimizers(self):
        """Pulisce i sistemi di ottimizzazione performance alla chiusura"""
        try:
            if self.update_manager:
                self.update_manager.cleanup()

            if self.column_resizer:
                self.column_resizer.cached_widths.clear()

            self.logger.debug("Performance optimizers cleanup completato")
        except Exception as e:
            self.logger.error(f"Errore cleanup performance optimizers: {e}")
    
    def update_data(self, df: pd.DataFrame):
        """Aggiorna i dati della tabella"""
        self.logger.debug(f"update_data() chiamato con DataFrame: {len(df)} righe, vuoto: {df.empty}")
        self.logger.debug(f"portfolio_tree exists: {self.portfolio_tree is not None}")
        
        # Pulisce la tabella esistente
        try:
            children_count = len(self.portfolio_tree.get_children())
            self.logger.debug(f"Cancellando {children_count} righe esistenti dalla tabella")
            for item in self.portfolio_tree.get_children():
                self.portfolio_tree.delete(item)
            self.logger.debug("Tabella pulita con successo")
        except Exception as e:
            self.logger.error(f"Errore durante la pulizia della tabella: {e}")
        
        if df.empty:
            self.logger.debug("DataFrame vuoto, esco senza aggiungere righe")
            return
        
        # Identifica i record storici se stiamo mostrando tutti i record
        historical_ids = set()
        if self.show_all_records:
            current_df = self.portfolio_manager.get_current_assets_only()
            current_ids = set(current_df['id'].astype(int))
            all_ids = set(df['id'].astype(int))
            historical_ids = all_ids - current_ids
        
        # Inserisce i nuovi dati con colorazione appropriata
        self.logger.debug(f"Iniziando inserimento {len(df)} righe nella tabella")
        rows_inserted = 0
        for _, row in df.iterrows():
            try:
                values = self._format_row_values(row)
                if rows_inserted < 3:  # Log solo prime 3 righe per evitare spam
                    self.logger.debug(f"Inserendo riga {rows_inserted + 1}: ID={row['id']}, Asset={row.get('asset_name', 'N/A')}")
                item_id = self.portfolio_tree.insert("", "end", values=values)

                # Colora di azzurro i record storici
                if int(row['id']) in historical_ids:
                    self.portfolio_tree.item(item_id, tags=('historical',))

                rows_inserted += 1
            except Exception as e:
                self.logger.error(f"Errore inserimento riga {rows_inserted}: {e}")
        
        self.logger.debug(f"Inserimento completato: {rows_inserted} righe inserite su {len(df)} totali")
        
        # Verifica che le righe siano effettivamente visibili
        children = self.portfolio_tree.get_children()
        self.logger.debug(f"Righe nella tabella dopo inserimento: {len(children)}")
        if len(children) > 0:
            # Mostra solo la prima riga per verifica
            child = children[0]
            values = self.portfolio_tree.item(child, "values")
            self.logger.debug(f"Prima riga visibile - ID: {values[0] if values else 'N/A'}")
        
        # Configura il tag per record storici
        self.portfolio_tree.tag_configure('historical', foreground='#0066CC')
        
        # Aggiorna contatori
        self._update_button_counts(df)
        
        # Auto-ridimensiona le colonne con sistema ottimizzato
        if self.column_resizer:
            self.column_resizer.invalidate_cache()
            self.column_resizer.schedule_resize()
        else:
            self._auto_resize_columns()  # Fallback

        # Aggiorna scrollbar con debouncing
        if self.update_manager:
            self.update_manager.schedule_update("update_scrollbars", self._update_scrollbars)
        else:
            self._update_scrollbars()
        
        # Refresh ottimizzato dell'interfaccia
        try:
            self.portfolio_tree.update_idletasks()
            self.parent.update_idletasks()
            self.logger.debug("Refresh interfaccia completato")
        except Exception as e:
            self.logger.error(f"Errore durante refresh: {e}")

        self.logger.debug("update_data() COMPLETATO")
    
    def _auto_resize_columns(self):
        """Auto-ridimensiona le colonne in base al contenuto (come Excel)"""
        try:
            import tkinter.font as tkfont
            
            # Font corrente per calcoli
            current_font = tkfont.nametofont("TkDefaultFont")
            font_size = int(9 * (self.zoom_level / 100))
            current_font.configure(size=font_size)
            
            for col in self.portfolio_tree['columns']:
                # Calcola larghezza header (su due righe)
                header_text = self.portfolio_tree.heading(col, "text")
                if isinstance(header_text, str):
                    # Trova la riga più lunga nell'header
                    header_lines = header_text.split('\n')
                    max_header_width = max([current_font.measure(line) for line in header_lines]) if header_lines else 0
                else:
                    max_header_width = current_font.measure(str(header_text))
                
                # Calcola larghezza massima del contenuto
                max_content_width = 0
                for item in self.portfolio_tree.get_children():
                    item_values = self.portfolio_tree.item(item, 'values')
                    if item_values:
                        col_index = list(self.portfolio_tree['columns']).index(col)
                        if col_index < len(item_values):
                            cell_text = str(item_values[col_index])
                            content_width = current_font.measure(cell_text)
                            max_content_width = max(max_content_width, content_width)
                
                # Larghezza finale: maggiore tra header e contenuto + padding
                final_width = max(max_header_width, max_content_width) + 20  # 20px padding
                
                # Limiti min e max per evitare colonne troppo strette o troppo larghe
                min_width = 60
                max_width = 300
                final_width = max(min_width, min(max_width, final_width))
                
                # Applica la nuova larghezza
                self.portfolio_tree.column(col, width=final_width)
                
        except Exception as e:
            self.logger.error(f"Errore auto-resize colonne: {e}")
    
    def _format_row_values(self, row: pd.Series) -> tuple:
        """Formatta i valori di una riga per la visualizzazione"""
        return (
            row['id'],
            row['category'],
            str(row['position']) if pd.notna(row['position']) else "-",
            str(row['asset_name'])[:20] + "..." if len(str(row['asset_name'])) > 20 else str(row['asset_name']),
            str(row['isin']) if pd.notna(row['isin']) and str(row['isin']) != '' else "-",
            str(row['ticker']) if pd.notna(row['ticker']) and str(row['ticker']) != '' else "-",
            row['risk_level'],
            DateFormatter.format_for_display(row['created_at']),
            f"{row['created_amount']:,.2f}" if pd.notna(row['created_amount']) else "0",
            CurrencyFormatter.format_for_display(row['created_unit_price']),
            CurrencyFormatter.format_for_display(row['created_total_value']),
            DateFormatter.format_for_display(row['updated_at']),
            f"{row['updated_amount']:,.2f}" if pd.notna(row['updated_amount']) else "0",
            CurrencyFormatter.format_for_display(row['updated_unit_price']),
            CurrencyFormatter.format_for_display(row['updated_total_value']),
            str(row['accumulation_plan']) if pd.notna(row['accumulation_plan']) else "-",
            CurrencyFormatter.format_for_display(row['accumulation_amount']),
            CurrencyFormatter.format_for_display(row['income_per_year']),
            CurrencyFormatter.format_for_display(row['rental_income']),
            str(row['note']) if pd.notna(row['note']) else "-"
        )
    
    def _update_button_counts(self, df: pd.DataFrame):
        """Aggiorna i contatori sui bottoni Record/Asset"""
        try:
            total_records = len(self.portfolio_manager.load_data())
            current_assets = len(self.portfolio_manager.get_current_assets_only())
            
            safe_execute(lambda: self.records_btn.configure(text=f"Record {total_records}"))
            safe_execute(lambda: self.assets_btn.configure(text=f"Asset {current_assets}"))
        except Exception as e:
            self.logger.error(f"Errore aggiornamento contatori: {e}")
    
    def get_visible_value(self) -> tuple[float, int]:
        """Calcola il valore delle righe visibili"""
        visible_value = 0.0
        visible_count = 0
        
        for child in self.portfolio_tree.get_children():
            item_values = self.portfolio_tree.item(child)['values']
            if len(item_values) >= 15:
                current_total = item_values[14]  # "Updated Total Value"
                try:
                    current_total_str = str(current_total).replace('€', '').replace(',', '').strip()
                    if current_total_str and current_total_str != 'N/A':
                        value = float(current_total_str)
                        visible_value += value
                        visible_count += 1
                except (ValueError, TypeError):
                    continue
        
        return visible_value, visible_count
    
    def _sort_records(self):
        """Riordina i record del file Excel per categoria, posizione, nome asset, ISIN e data update"""
        try:
            # Conferma utente
            result = messagebox.askyesno(
                "Riordino Record", 
                "Vuoi riordinare tutti i record del file Excel?\n\n"
                "I record verranno ordinati per:\n"
                "1. Categoria\n"
                "2. Posizione\n"
                "3. Nome Asset\n"
                "4. ISIN\n"
                "5. Data Update\n\n"
                "Questa operazione modificherà permanentemente il file Excel."
            )
            
            if not result:
                return
            
            # Carica tutti i dati dal file Excel
            import pandas as pd
            df = pd.read_excel(self.portfolio_manager.excel_file)
            
            if df.empty:
                messagebox.showinfo("Info", "Nessun record da riordinare.")
                return
            
            self.logger.info(f"Riordinamento di {len(df)} record...")
            
            # Converte le date in formato datetime per ordinamento corretto
            for date_col in ['updated_at', 'created_at']:
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            
            # Riordina i record secondo l'ordine specificato
            # Usa fillna per gestire valori mancanti nell'ordinamento
            df_sorted = df.sort_values(
                by=['category', 'position', 'asset_name', 'isin', 'updated_at'],
                na_position='last',
                ascending=True
            ).copy()
            
            self.logger.info("Record riordinati con successo")
            if not df_sorted.empty:
                first_row = df_sorted.iloc[0]
                self.logger.debug(f"Primo record: {first_row.get('category', 'N/A')} | {first_row.get('asset_name', 'N/A')}")
            
            # Salva il file Excel riordinato
            df_sorted.to_excel(self.portfolio_manager.excel_file, index=False)
            
            # Ricarica i dati nell'applicazione
            self.trigger_callback('data_changed')
            
            messagebox.showinfo(
                "Riordino Completato", 
                f"Record riordinati con successo!\n\n"
                f"Totale record: {len(df_sorted)}\n"
                f"File aggiornato: {self.portfolio_manager.excel_file}"
            )
            
            self.logger.info("File Excel aggiornato e ricaricato")
            
        except Exception as e:
            error_msg = ErrorHandler.handle_file_error(e, "riordino record")
            messagebox.showerror("Errore Riordino", f"Errore durante il riordino:\n\n{error_msg}")
            self.logger.error(f"Errore riordino record: {e}")
            import traceback
            self.logger.debug(f"Stack trace: {traceback.format_exc()}")
    
    def _color_historical_records(self):
        """Colora i record storici di azzurro nel file Excel"""
        try:
            # Conferma utente
            result = messagebox.askyesno(
                "Colora Record Storici", 
                "Vuoi colorare i record storici di azzurro nel file Excel?\n\n"
                "I record storici sono quelli che non rappresentano più\n"
                "lo stato attuale di un asset (sostituiti da versioni più recenti).\n\n"
                "Questa operazione modificherà permanentemente il file Excel."
            )
            
            if not result:
                return
            
            # Esegui la colorazione
            self.portfolio_manager.color_historical_records()
            
            messagebox.showinfo(
                "Colorazione Completata", 
                "I record storici sono stati colorati di azzurro!\n\n"
                "Riapri il file Excel per vedere le modifiche."
            )
            
        except Exception as e:
            from utils import ErrorHandler
            error_msg = ErrorHandler.handle_file_error(e, "colorazione record storici")
            messagebox.showerror("Errore Colorazione", f"Errore durante la colorazione:\n\n{error_msg}")
            self.logger.error(f"Errore colorazione record storici: {e}")
            import traceback
            self.logger.debug(f"Stack trace: {traceback.format_exc()}")