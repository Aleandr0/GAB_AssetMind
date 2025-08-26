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

class BaseUIComponent:
    """Classe base per tutti i componenti UI"""
    
    def __init__(self, parent, portfolio_manager: PortfolioManager):
        self.parent = parent
        self.portfolio_manager = portfolio_manager
        self.callbacks: Dict[str, Callable] = {}
    
    def register_callback(self, event_name: str, callback: Callable):
        """Registra un callback per un evento"""
        self.callbacks[event_name] = callback
    
    def trigger_callback(self, event_name: str, *args, **kwargs):
        """Esegue un callback se registrato"""
        if event_name in self.callbacks:
            safe_execute(
                lambda: self.callbacks[event_name](*args, **kwargs),
                error_handler=lambda e: print(f"Errore callback {event_name}: {e}")
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
            btn = ctk.CTkButton(
                nav_buttons_frame,
                text=text,
                command=lambda p=page: self.trigger_callback('page_changed', p),
                **UIConfig.BUTTON_SIZES['medium'],
                font=ctk.CTkFont(**UIConfig.FONTS['button']),
                fg_color=UIConfig.COLORS['secondary'],
                hover_color=UIConfig.COLORS['secondary_hover']
            )
            btn.pack(side="left", padx=2)
    
    def _on_portfolio_changed(self, selected_file: str):
        """Gestisce il cambio di portfolio"""
        self.trigger_callback('portfolio_changed', selected_file)
    
    def _create_new_portfolio(self):
        """Crea un nuovo portfolio"""
        self.trigger_callback('new_portfolio_requested')
    
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
        
        # Controlli UI
        self.records_btn = None
        self.assets_btn = None
        self.zoom_label = None
        self.v_scrollbar = None
        self.h_scrollbar = None
    
    def create_table(self) -> ctk.CTkFrame:
        """Crea la tabella portfolio completa"""
        self.table_frame = ctk.CTkFrame(self.parent)
        self.table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self._create_controls()
        self._create_tree_view()
        self._setup_tree_style()
        
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
    
    def _configure_columns(self, columns: tuple):
        """Configura le colonne della tabella"""
        column_widths = {
            "ID": 50, "Category": 120, "Position": 100, "Asset Name": 150,
            "ISIN": 100, "Ticker": 80, "Risk Level": 80,
            "Created At": 100, "Created Amount": 100, "Created Unit Price": 120,
            "Created Total Value": 130, "Updated At": 100, "Updated Amount": 100,
            "Updated Unit Price": 120, "Updated Total Value": 130,
            "Accumulation Plan": 150, "Accumulation Amount": 130,
            "Income Per Year": 120, "Rental Income": 120, "Note": 200
        }
        
        for col in columns:
            width = column_widths.get(col, 100)
            self.portfolio_tree.heading(col, text=col, anchor="w")
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
        self.tree_style.configure(
            "Portfolio.Treeview.Heading",
            background="#f0f0f0",
            foreground="black",
            font=("TkDefaultFont", 9, "bold")
        )
        self.portfolio_tree.configure(style="Portfolio.Treeview")
    
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
        self.trigger_callback('view_changed', 'assets')
    
    def _zoom_in(self):
        """Aumenta lo zoom della tabella"""
        if self.zoom_level < 150:
            self.zoom_level += 10
            self._apply_zoom()
    
    def _zoom_out(self):
        """Diminuisce lo zoom della tabella"""
        if self.zoom_level > 70:
            self.zoom_level -= 10
            self._apply_zoom()
    
    def _apply_zoom(self):
        """Applica il livello di zoom corrente"""
        base_font_size = 9
        new_font_size = int(base_font_size * (self.zoom_level / 100))
        new_height = int(25 * (self.zoom_level / 100))
        
        self.tree_style.configure(
            "Portfolio.Treeview",
            font=("TkDefaultFont", new_font_size),
            rowheight=new_height
        )
        self.tree_style.configure(
            "Portfolio.Treeview.Heading",
            font=("TkDefaultFont", new_font_size, "bold")
        )
        
        self.zoom_label.configure(text=f"{self.zoom_level}%")
        self._update_scrollbars()
    
    def _update_scrollbars(self):
        """Aggiorna la visibilità delle scrollbar"""
        try:
            self.parent.after(50, lambda: [
                self.v_scrollbar.grid() if self.portfolio_tree.yview() != (0.0, 1.0) else self.v_scrollbar.grid_remove(),
                self.h_scrollbar.grid() if self.portfolio_tree.xview() != (0.0, 1.0) else self.h_scrollbar.grid_remove()
            ])
        except Exception as e:
            print(f"Errore aggiornamento scrollbar: {e}")
    
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
        self.trigger_callback('filter_requested', column)
    
    def update_data(self, df: pd.DataFrame):
        """Aggiorna i dati della tabella"""
        # Pulisce la tabella esistente
        for item in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(item)
        
        if df.empty:
            return
        
        # Inserisce i nuovi dati
        for _, row in df.iterrows():
            values = self._format_row_values(row)
            self.portfolio_tree.insert("", "end", values=values)
        
        # Aggiorna contatori
        self._update_button_counts(df)
        self._update_scrollbars()
    
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
            print(f"Errore aggiornamento contatori: {e}")
    
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