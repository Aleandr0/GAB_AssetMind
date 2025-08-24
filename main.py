#!/usr/bin/env python3
"""
GAB AssetMind - Portfolio Manager
Applicazione GUI per la gestione di portafogli diversificati con database Excel

Autori: Alessandro + Claude Code
Repository: https://github.com/Aleandr0/GAB_AssetMind
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from models import Asset, PortfolioManager
import os

# Configurazione tema dell'applicazione
ctk.set_appearance_mode("light")  # Modalità chiara
ctk.set_default_color_theme("blue")  # Tema blu

class GABAssetMind:
    """
    Applicazione principale GAB AssetMind per la gestione portfolio
    
    Gestisce 9 tipi di asset: ETF, Azioni, Obbligazioni, Buoni del Tesoro, 
    PAC, Criptovalute, Liquidità, Immobiliare, Oggetti
    
    Funzionalità principali:
    - Form di input per nuovi asset (20 campi)
    - Visualizzazione portfolio in tabella
    - Grafici di analisi
    - Export CSV/PDF
    - Persistenza dati in Excel
    """
    
    def __init__(self):
        """Inizializza l'applicazione e configura l'interfaccia"""
        # Finestra principale
        self.root = ctk.CTk()
        self.root.title("GAB AssetMind - Portfolio Manager")
        self.root.geometry("1200x800")
        
        # Gestore del portfolio (interfaccia con Excel)
        self.portfolio_manager = PortfolioManager()
        
        # Inizializza attributi per la navigazione
        self.current_page = "Portfolio"
        self.page_frames = {}
        self.nav_buttons = {}
        
        # Attributi per la modifica asset
        self.editing_asset_id = None
        
        # Creazione interfaccia utente
        self.setup_ui()
        
        # Caricamento automatico dei dati esistenti
        self.root.after(100, self.load_portfolio_data)
    
    def setup_ui(self):
        """Configura l'interfaccia utente con barra di navigazione globale"""
        # Container principale
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Barra di navigazione globale sempre visibile
        self.create_global_navbar()
        
        # Container per il contenuto delle pagine
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=(10, 20))
        
        # Inizializza le pagine
        self.setup_all_pages()
        
        # Mostra la pagina Portfolio per default
        self.show_page("Portfolio")
    
    def create_global_navbar(self):
        """Crea la barra di navigazione globale sempre visibile"""
        # Barra principale
        navbar_frame = ctk.CTkFrame(self.main_frame, height=80)
        navbar_frame.pack(fill="x", padx=5, pady=(5, 15))
        navbar_frame.pack_propagate(False)  # Mantiene altezza fissa
        
        # Logo/Nome applicazione (sinistra)
        logo_label = ctk.CTkLabel(navbar_frame, text="GAB AssetMind", 
                                font=ctk.CTkFont(size=26, weight="bold"),
                                text_color=("#1f538d", "#14375e"))
        logo_label.pack(side="left", padx=20, pady=20)
        
        # Valore totale portfolio (centro)
        self.total_value_label = ctk.CTkLabel(navbar_frame, text="Valore Totale: €0", 
                                            font=ctk.CTkFont(size=18, weight="bold"),
                                            text_color=("#2d5016", "#4a7c59"))
        self.total_value_label.pack(side="left", padx=40, pady=20)
        
        # Container per i bottoni di navigazione (destra)
        nav_buttons_frame = ctk.CTkFrame(navbar_frame, fg_color="transparent")
        nav_buttons_frame.pack(side="right", padx=20, pady=10)
        
        # Bottoni di navigazione
        self.nav_buttons = {}
        pages = ["Portfolio", "Asset", "Grafici", "Export"]
        
        for i, page in enumerate(pages):
            btn = ctk.CTkButton(nav_buttons_frame, text=page, 
                              command=lambda p=page: self.show_page(p),
                              width=120, height=45,
                              font=ctk.CTkFont(size=16, weight="bold"))
            btn.pack(side="left", padx=8)
            self.nav_buttons[page] = btn
        
        # Evidenzia il bottone attivo
        self.update_nav_highlight()
    
    def update_nav_highlight(self):
        """Aggiorna l'evidenziazione del bottone di navigazione attivo"""
        for page, btn in self.nav_buttons.items():
            if page == self.current_page:
                # Bottone attivo - colore evidenziato
                btn.configure(fg_color=("#3b82f6", "#2563eb"), 
                            hover_color=("#2563eb", "#1d4ed8"))
            else:
                # Bottoni inattivi - colori standard
                btn.configure(fg_color=("#3a3a3a", "#212121"), 
                            hover_color=("#4a4a4a", "#2a2a2a"))
    
    def show_page(self, page_name):
        """Mostra la pagina specificata e aggiorna la navigazione"""
        try:
            self.current_page = page_name
            self.update_nav_highlight()
            
            # Nascondi tutti i frame delle pagine
            for frame in self.page_frames.values():
                frame.pack_forget()
            
            # Mostra il frame della pagina selezionata
            if page_name in self.page_frames:
                self.page_frames[page_name].pack(fill="both", expand=True, padx=10, pady=10)
                
                # Ricarica i dati del portfolio se necessario
                if page_name == "Portfolio":
                    self.load_portfolio_data()
                
                # Aggiorna il valore totale del portfolio nella navbar
                self.update_portfolio_value()
        except Exception as e:
            print(f"Errore nel cambio pagina {page_name}: {e}")
            messagebox.showerror("Errore", f"Errore nel cambio pagina {page_name}: {e}")
    
    def setup_all_pages(self):
        """Inizializza tutti i frame delle pagine"""
        self.page_frames = {}
        
        # Crea i frame per ogni pagina
        self.page_frames["Portfolio"] = ctk.CTkFrame(self.content_frame)
        self.page_frames["Asset"] = ctk.CTkFrame(self.content_frame)
        self.page_frames["Grafici"] = ctk.CTkFrame(self.content_frame)
        self.page_frames["Export"] = ctk.CTkFrame(self.content_frame)
        
        # Configura ogni pagina
        self.setup_portfolio_page()
        self.setup_asset_page()
        self.setup_analytics_page()
        self.setup_export_page()
    
    def setup_portfolio_page(self):
        """Configura la pagina Portfolio"""
        frame = self.page_frames["Portfolio"]
        
        # Top control frame (filter + zoom controls)
        control_frame = ctk.CTkFrame(frame)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Left side - Filter
        filter_section = ctk.CTkFrame(control_frame, fg_color="transparent")
        filter_section.pack(side="left", padx=10)
        
        ctk.CTkLabel(filter_section, text="Filter by Category:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(0,10))
        
        categories = ["All"] + self.portfolio_manager.categories
        self.category_filter = ctk.CTkComboBox(filter_section, values=categories, 
                                             command=self.filter_portfolio, width=120)
        self.category_filter.pack(side="left")
        self.category_filter.set("All")
        
        # Right side - Zoom and info controls
        zoom_section = ctk.CTkFrame(control_frame, fg_color="transparent")
        zoom_section.pack(side="right", padx=10)
        
        # Asset count label
        self.assets_count_label = ctk.CTkLabel(zoom_section, text="Assets: 0",
                                             font=ctk.CTkFont(size=14, weight="bold"))
        self.assets_count_label.pack(side="left", padx=(0,20))
        
        # Zoom controls
        ctk.CTkLabel(zoom_section, text="Zoom:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0,5))
        
        zoom_out_btn = ctk.CTkButton(zoom_section, text="-", command=self.zoom_out_table,
                                   width=30, height=30, font=ctk.CTkFont(size=16, weight="bold"))
        zoom_out_btn.pack(side="left", padx=2)
        
        self.zoom_label = ctk.CTkLabel(zoom_section, text="100%", width=50,
                                     font=ctk.CTkFont(size=12, weight="bold"))
        self.zoom_label.pack(side="left", padx=5)
        
        zoom_in_btn = ctk.CTkButton(zoom_section, text="+", command=self.zoom_in_table,
                                  width=30, height=30, font=ctk.CTkFont(size=16, weight="bold"))
        zoom_in_btn.pack(side="left", padx=2)
        
        reset_zoom_btn = ctk.CTkButton(zoom_section, text="Reset", command=self.reset_zoom_table,
                                     width=60, height=30, font=ctk.CTkFont(size=11, weight="bold"))
        reset_zoom_btn.pack(side="left", padx=(10,0))
        
        # Refresh button
        refresh_btn = ctk.CTkButton(zoom_section, text="🔄 Refresh", 
                                  command=self.load_portfolio_data,
                                  width=100, height=30,
                                  font=ctk.CTkFont(size=11, weight="bold"))
        refresh_btn.pack(side="left", padx=(10,0))
        
        # TreeView container frame (NO ScrollableFrame - uses native scrollbars)
        tree_container = ctk.CTkFrame(frame)
        tree_container.pack(fill="both", expand=True, padx=10, pady=(0,10))
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # TUTTI i 20 campi del database - CAMPI IDENTIFICATIVI: Category, Position, Asset Name, ISIN
        columns = ("ID", "Category", "Position", "Asset Name", "ISIN", "Ticker", "Risk Level",
                  "Created At", "Created Amount", "Created Unit Price", "Created Total Value",
                  "Updated At", "Updated Amount", "Updated Unit Price", "Updated Total Value", 
                  "Accumulation Plan", "Accumulation Amount", "Income Per Year", "Rental Income", "Note")
        
        # TreeView columns and styling
        
        # Configurazione colonne - ORDINE IDENTIFICATIVO: Category, Position, Asset Name, ISIN
        column_widths = {
            "ID": 40, "Category": 100, "Position": 120, "Asset Name": 180, "ISIN": 120,
            "Ticker": 70, "Risk Level": 80, "Created At": 100, "Created Amount": 100, 
            "Created Unit Price": 120, "Created Total Value": 120, "Updated At": 100, 
            "Updated Amount": 100, "Updated Unit Price": 120, "Updated Total Value": 120, 
            "Accumulation Plan": 120, "Accumulation Amount": 120, "Income Per Year": 100, 
            "Rental Income": 100, "Note": 120
        }
        
        # Colonne numeriche che devono essere allineate a destra
        numeric_columns = {
            "Risk Level", "Created Amount", "Created Unit Price", "Created Total Value",
            "Updated Amount", "Updated Unit Price", "Updated Total Value", 
            "Accumulation Amount", "Income Per Year", "Rental Income"
        }
        
        # TreeView with scrollbars - PRIMA creare l'oggetto
        self.portfolio_tree = ttk.Treeview(tree_container, columns=columns, show='headings')
        
        # POI configurare le colonne
        for col in columns:
            self.portfolio_tree.heading(col, text=col)
            # Allineamento a destra per campi numerici, a sinistra per gli altri
            anchor = "e" if col in numeric_columns else "w"  # "e" = east (destra), "w" = west (sinistra)
            self.portfolio_tree.column(col, width=column_widths.get(col, 80), minwidth=60, anchor=anchor)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.portfolio_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient="horizontal", command=self.portfolio_tree.xview)
        
        self.portfolio_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout for full expansion with scrollbars
        self.portfolio_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Salva riferimenti alle scrollbar per controllo dinamico
        self.v_scrollbar = v_scrollbar
        self.h_scrollbar = h_scrollbar
        
        # Configura gestione automatica scrollbar
        def on_v_scrollbar_set(first, last):
            if float(first) <= 0.0 and float(last) >= 1.0:
                self.v_scrollbar.grid_remove()
            else:
                self.v_scrollbar.grid(row=0, column=1, sticky="ns")
            
        def on_h_scrollbar_set(first, last):
            if float(first) <= 0.0 and float(last) >= 1.0:
                self.h_scrollbar.grid_remove()
            else:
                self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Collega le funzioni di controllo scrollbar
        self.portfolio_tree.configure(
            yscrollcommand=lambda f, l: [v_scrollbar.set(f, l), on_v_scrollbar_set(f, l)],
            xscrollcommand=lambda f, l: [h_scrollbar.set(f, l), on_h_scrollbar_set(f, l)]
        )
        
        # Initialize zoom
        self.zoom_factor = 1.0
        self.base_row_height = 25
        
        # Context menu and mouse wheel zoom
        self.portfolio_tree.bind("<Double-1>", self.edit_asset)
        self.portfolio_tree.bind("<Button-3>", self.show_context_menu)
        self.portfolio_tree.bind("<Control-MouseWheel>", self.on_mouse_wheel_zoom)
        
        # Applica lo zoom iniziale per impostare lo stile
        self.apply_zoom()
    
    def zoom_in_table(self):
        """Aumenta il zoom della tabella"""
        if self.zoom_factor < 2.0:
            self.zoom_factor += 0.1
            self.apply_zoom()
    
    def zoom_out_table(self):
        """Diminuisce il zoom della tabella"""
        if self.zoom_factor > 0.5:
            self.zoom_factor -= 0.1
            self.apply_zoom()
    
    def reset_zoom_table(self):
        """Reimposta il zoom della tabella al 100%"""
        self.zoom_factor = 1.0
        self.apply_zoom()
    
    def on_mouse_wheel_zoom(self, event):
        """Gestisce lo zoom con rotella del mouse + Ctrl"""
        if event.delta > 0:
            self.zoom_in_table()
        else:
            self.zoom_out_table()
    
    def apply_zoom(self):
        """Applica il fattore di zoom alla tabella"""
        try:
            # Calcola nuovi valori
            new_height = int(self.base_row_height * self.zoom_factor)
            base_font_size = 10
            new_font_size = max(8, int(base_font_size * self.zoom_factor))
            
            # Crea o aggiorna stile TreeView
            if not hasattr(self, 'tree_style'):
                self.tree_style = ttk.Style()
            
            # Configura lo stile personalizzato
            self.tree_style.configure("Portfolio.Treeview", 
                                    font=("TkDefaultFont", new_font_size), 
                                    rowheight=new_height)
            self.tree_style.configure("Portfolio.Treeview.Heading", 
                                    font=("TkDefaultFont", new_font_size, "bold"))
            
            # Applica lo stile al TreeView
            self.portfolio_tree.configure(style="Portfolio.Treeview")
            
            # Aggiorna anche le larghezze delle colonne proporzionalmente
            if not hasattr(self, 'base_column_widths'):
                self.base_column_widths = {}
                for col in self.portfolio_tree["columns"]:
                    self.base_column_widths[col] = self.portfolio_tree.column(col, "width")
            
            total_width = 0
            for col in self.portfolio_tree["columns"]:
                base_width = self.base_column_widths[col]
                new_width = int(base_width * self.zoom_factor)
                # Imposta larghezza minima e massima per evitare problemi
                new_width = max(50, min(new_width, 500))
                self.portfolio_tree.column(col, width=new_width, minwidth=new_width)
                total_width += new_width
            
            # Se la larghezza totale supera la vista disponibile, le scrollbar dovrebbero apparire
            print(f"Total columns width: {total_width}px at zoom {int(self.zoom_factor * 100)}%")
            
            # Aggiorna label zoom
            zoom_percent = int(self.zoom_factor * 100)
            if hasattr(self, 'zoom_label'):
                self.zoom_label.configure(text=f"{zoom_percent}%")
            
            # Forza aggiornamento scrollbar dopo zoom
            self.update_scrollbars()
                
            print(f"Zoom applicato: {zoom_percent}% (font: {new_font_size}px, row height: {new_height}px)")
            
        except Exception as e:
            print(f"Errore nell'applicazione zoom: {e}")
            import traceback
            traceback.print_exc()
    
    def update_scrollbars(self):
        """Forza l'aggiornamento delle scrollbar"""
        try:
            # Forza l'aggiornamento della geometria
            self.portfolio_tree.update_idletasks()
            
            # Trigger manuale degli eventi scrollbar
            if hasattr(self, 'v_scrollbar') and hasattr(self, 'h_scrollbar'):
                # Simula un piccolo movimento per triggerare l'update
                current_y = self.portfolio_tree.yview()
                current_x = self.portfolio_tree.xview()
                
                # Se il contenuto si estende oltre la vista, mostra le scrollbar
                if current_y[1] - current_y[0] < 1.0:  # Contenuto verticale più grande della vista
                    self.v_scrollbar.grid(row=0, column=1, sticky="ns")
                else:
                    self.v_scrollbar.grid_remove()
                
                if current_x[1] - current_x[0] < 1.0:  # Contenuto orizzontale più grande della vista
                    self.h_scrollbar.grid(row=1, column=0, sticky="ew")
                else:
                    self.h_scrollbar.grid_remove()
                    
        except Exception as e:
            print(f"Errore aggiornamento scrollbar: {e}")
    
    def setup_asset_page(self):
        """Configura la pagina Asset (Aggiungi Asset)"""
        frame = self.page_frames["Asset"]
        
        # Header con titolo e bottoni
        header_frame = ctk.CTkFrame(frame)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        # Titolo (salviamo reference per poterlo aggiornare)
        self.asset_title_label = ctk.CTkLabel(header_frame, text="Nuovo Asset", 
                                             font=ctk.CTkFont(size=20, weight="bold"))
        self.asset_title_label.pack(side="left", padx=20, pady=15)
        
        # Bottoni Salva e Pulisci
        button_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        button_frame.pack(side="right", padx=20, pady=15)
        
        save_btn = ctk.CTkButton(button_frame, text="💾 Salva Asset", 
                               command=self.save_new_asset, width=140, height=40,
                               font=ctk.CTkFont(size=14, weight="bold"))
        save_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(button_frame, text="🗑️ Pulisci Form", 
                                command=self.clear_form, width=140, height=40,
                                font=ctk.CTkFont(size=14, weight="bold"),
                                fg_color="#dc2626", hover_color="#b91c1c")
        clear_btn.pack(side="left", padx=5)
        
        new_btn = ctk.CTkButton(button_frame, text="🆕 Nuovo Asset", 
                              command=self.new_asset_mode, width=140, height=40,
                              font=ctk.CTkFont(size=14, weight="bold"),
                              fg_color="#16a34a", hover_color="#15803d")
        new_btn.pack(side="left", padx=5)
        
        # Scrollable frame per il form
        form_scroll = ctk.CTkScrollableFrame(frame)
        form_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Form frame con layout 2x2
        form_frame = ctk.CTkFrame(form_scroll)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Inizializza il form
        self.form_vars = {}
        self.create_asset_form(form_frame)
    
    def setup_analytics_page(self):
        """Configura la pagina Grafici"""
        frame = self.page_frames["Grafici"]
        
        # Control frame
        control_frame = ctk.CTkFrame(frame)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        chart_types = ["Distribuzione per Categoria", "Distribuzione Rischio", "Performance nel Tempo"]
        self.chart_type = ctk.CTkComboBox(control_frame, values=chart_types, 
                                        command=self.update_chart)
        self.chart_type.pack(side="left", padx=10)
        self.chart_type.set(chart_types[0])
        
        # Chart frame
        self.chart_frame = ctk.CTkFrame(frame)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Inizializza il primo grafico
        self.root.after(200, self.update_chart)
    
    def setup_export_page(self):
        """Configura la pagina Export"""
        frame = self.page_frames["Export"]
        
        export_frame = ctk.CTkFrame(frame)
        export_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Titolo
        title_label = ctk.CTkLabel(export_frame, text="Esporta Portfolio", 
                                  font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=20)
        
        # Bottoni export
        buttons_frame = ctk.CTkFrame(export_frame, fg_color="transparent")
        buttons_frame.pack(pady=30)
        
        pdf_btn = ctk.CTkButton(buttons_frame, text="📄 Esporta PDF", 
                              command=self.safe_export_pdf, 
                              width=200, height=50,
                              font=ctk.CTkFont(size=16, weight="bold"))
        pdf_btn.pack(pady=10)
        
        csv_btn = ctk.CTkButton(buttons_frame, text="📊 Esporta CSV", 
                              command=self.safe_export_csv, 
                              width=200, height=50,
                              font=ctk.CTkFont(size=16, weight="bold"))
        csv_btn.pack(pady=10)
        
        # Area di feedback
        self.export_feedback = ctk.CTkLabel(export_frame, text="", 
                                          font=ctk.CTkFont(size=14))
        self.export_feedback.pack(pady=20)
    
    def update_portfolio_value(self):
        """Aggiorna il valore totale del portfolio nella navbar"""
        try:
            summary = self.portfolio_manager.get_portfolio_summary()
            total_value = summary.get('total_value', 0)
            self.total_value_label.configure(text=f"Valore Totale: €{total_value:,.2f}")
        except Exception as e:
            self.total_value_label.configure(text="Valore Totale: €0")
    
    
    def create_asset_form(self, form_frame):
        """Crea il form per l'inserimento/modifica asset"""
        # Definizione campi con labels, chiavi e valori predefiniti
        fields = [
            ("Categoria", "category", self.portfolio_manager.categories),
            ("Asset Name", "asset_name", None),
            ("Posizione", "position", None),
            ("Risk Level (1-5)", "risk_level", ["1", "2", "3", "4", "5"]),
            ("Ticker", "ticker", None),
            ("ISIN", "isin", None),
            ("Created At (YYYY-MM-DD)", "created_at", None),
            ("Created Amount", "created_amount", None),
            ("Created Unit Price", "created_unit_price", None),
            ("Created Total Value (auto)", "created_total_value", None),
            ("Updated At (YYYY-MM-DD)", "updated_at", None),
            ("Updated Amount", "updated_amount", None),
            ("Updated Unit Price", "updated_unit_price", None),
            ("Updated Total Value (auto)", "updated_total_value", None),
            ("Accumulation Plan", "accumulation_plan", None),
            ("Accumulation Amount", "accumulation_amount", None),
            ("Income Per Year", "income_per_year", None),
            ("Rental Income", "rental_income", None),
            ("Note", "note", None)
        ]
        
        # Crea i campi in layout 2x2
        for i, (label, key, values) in enumerate(fields):
            row = i // 2  # Riga (0, 1, 2, ...)
            col = i % 2   # Colonna (0 o 1)
            
            # Frame per ogni campo
            field_frame = ctk.CTkFrame(form_frame)
            field_frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
            
            # Label
            label_widget = ctk.CTkLabel(field_frame, text=label, width=150)
            label_widget.pack(side="left", padx=10, pady=8)
            
            # Widget di input
            if values:  # ComboBox per campi con valori predefiniti
                var = ctk.StringVar()
                widget = ctk.CTkComboBox(field_frame, values=values, variable=var, width=180)
            else:  # Entry per campi liberi
                var = ctk.StringVar()
                widget = ctk.CTkEntry(field_frame, textvariable=var, width=180)
            
            widget.pack(side="right", padx=10, pady=8)
            self.form_vars[key] = var
    
    
        
    
    def save_new_asset(self):
        """Salva un nuovo asset dal form di input"""
        self.save_asset()
    
    
    
    def load_portfolio_data(self):
        """Carica i dati del portfolio dal file Excel e aggiorna la visualizzazione"""
        df = self.portfolio_manager.load_data()
        
        if df.empty:
            self.update_summary()
            return
        
        # Clear existing data
        for item in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(item)
        
        # Load new data
        for _, row in df.iterrows():
            current_value = row['updated_total_value'] if pd.notna(row['updated_total_value']) else row['created_total_value']
            initial_value = row['created_total_value'] if pd.notna(row['created_total_value']) else 0
            total_income = (row['income_per_year'] if pd.notna(row['income_per_year']) else 0) + \
                          (row['rental_income'] if pd.notna(row['rental_income']) else 0)
            
            # Calcola performance percentuale
            performance = 0
            if pd.notna(initial_value) and initial_value > 0 and pd.notna(current_value):
                performance = ((current_value - initial_value) / initial_value) * 100
            
            self.portfolio_tree.insert("", "end", values=(
                row['id'],  # ID
                row['category'],  # Category
                str(row['position']) if pd.notna(row['position']) else "-",  # Position
                str(row['asset_name'])[:20] + "..." if len(str(row['asset_name'])) > 20 else str(row['asset_name']),  # Asset Name
                str(row['isin']) if pd.notna(row['isin']) else "-",  # ISIN
                str(row['ticker']) if pd.notna(row['ticker']) else "-",  # Ticker
                row['risk_level'],  # Risk Level
                self.format_date_for_display(row['created_at']),  # Created At
                f"{row['created_amount']:,.2f}" if pd.notna(row['created_amount']) else "0",  # Created Amount
                f"€{row['created_unit_price']:,.2f}" if pd.notna(row['created_unit_price']) else "€0",  # Created Unit Price
                f"€{initial_value:,.0f}" if pd.notna(initial_value) else "€0",  # Created Total Value
                self.format_date_for_display(row['updated_at']),  # Updated At
                f"{row['updated_amount']:,.2f}" if pd.notna(row['updated_amount']) else "0",  # Updated Amount
                f"€{row['updated_unit_price']:,.2f}" if pd.notna(row['updated_unit_price']) else "€0",  # Updated Unit Price
                f"€{current_value:,.0f}" if pd.notna(current_value) else "€0",  # Updated Total Value
                str(row['accumulation_plan']) if pd.notna(row['accumulation_plan']) else "-",  # Accumulation Plan
                f"€{row['accumulation_amount']:,.0f}" if pd.notna(row['accumulation_amount']) else "€0",  # Accumulation Amount
                f"€{row['income_per_year']:,.0f}" if pd.notna(row['income_per_year']) else "€0",  # Income Per Year
                f"€{row['rental_income']:,.0f}" if pd.notna(row['rental_income']) else "€0",  # Rental Income
                str(row['note'])[:15] + "..." if pd.notna(row['note']) and len(str(row['note'])) > 15 else (str(row['note']) if pd.notna(row['note']) else "-")  # Note
            ))
        
        # Aggiorna il sommario con i totali
        self.update_summary()
        
        # Aggiorna scrollbar dopo caricamento dati
        self.root.after(100, self.update_scrollbars)
    
    def update_summary(self):
        """Aggiorna il sommario del portfolio (metodo legacy, ora usa update_portfolio_value)"""
        summary = self.portfolio_manager.get_portfolio_summary()
        self.total_value_label.configure(text=f"Valore Totale: €{summary['total_value']:,.2f}")
        
        # Aggiorna conteggio asset
        df = self.portfolio_manager.load_data()
        self.assets_count_label.configure(text=f"Assets: {len(df)}")
    
    def filter_portfolio(self, category=None):
        """Filtra il portfolio per categoria"""
        if category is None:
            category = self.category_filter.get()
        self.filter_by_category(category)
    
    def filter_by_category(self, category):
        df = self.portfolio_manager.load_data()
        
        # Clear existing data
        for item in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(item)
        
        # Filter data
        if category != "All":
            df = df[df['category'] == category]
        
        # Load filtered data
        for _, row in df.iterrows():
            current_value = row['updated_total_value'] if pd.notna(row['updated_total_value']) else row['created_total_value']
            initial_value = row['created_total_value'] if pd.notna(row['created_total_value']) else 0
            total_income = (row['income_per_year'] if pd.notna(row['income_per_year']) else 0) + \
                          (row['rental_income'] if pd.notna(row['rental_income']) else 0)
            
            # Calcola performance percentuale
            performance = 0
            if pd.notna(initial_value) and initial_value > 0 and pd.notna(current_value):
                performance = ((current_value - initial_value) / initial_value) * 100
            
            self.portfolio_tree.insert("", "end", values=(
                row['id'],  # ID
                row['category'],  # Category
                str(row['position']) if pd.notna(row['position']) else "-",  # Position
                str(row['asset_name'])[:20] + "..." if len(str(row['asset_name'])) > 20 else str(row['asset_name']),  # Asset Name
                str(row['isin']) if pd.notna(row['isin']) else "-",  # ISIN
                str(row['ticker']) if pd.notna(row['ticker']) else "-",  # Ticker
                row['risk_level'],  # Risk Level
                self.format_date_for_display(row['created_at']),  # Created At
                f"{row['created_amount']:,.2f}" if pd.notna(row['created_amount']) else "0",  # Created Amount
                f"€{row['created_unit_price']:,.2f}" if pd.notna(row['created_unit_price']) else "€0",  # Created Unit Price
                f"€{initial_value:,.0f}" if pd.notna(initial_value) else "€0",  # Created Total Value
                self.format_date_for_display(row['updated_at']),  # Updated At
                f"{row['updated_amount']:,.2f}" if pd.notna(row['updated_amount']) else "0",  # Updated Amount
                f"€{row['updated_unit_price']:,.2f}" if pd.notna(row['updated_unit_price']) else "€0",  # Updated Unit Price
                f"€{current_value:,.0f}" if pd.notna(current_value) else "€0",  # Updated Total Value
                str(row['accumulation_plan']) if pd.notna(row['accumulation_plan']) else "-",  # Accumulation Plan
                f"€{row['accumulation_amount']:,.0f}" if pd.notna(row['accumulation_amount']) else "€0",  # Accumulation Amount
                f"€{row['income_per_year']:,.0f}" if pd.notna(row['income_per_year']) else "€0",  # Income Per Year
                f"€{row['rental_income']:,.0f}" if pd.notna(row['rental_income']) else "€0",  # Rental Income
                str(row['note'])[:15] + "..." if pd.notna(row['note']) and len(str(row['note'])) > 15 else (str(row['note']) if pd.notna(row['note']) else "-")  # Note
            ))
    
    def save_asset(self):
        """Salva un asset dal form nella base dati Excel"""
        try:
            asset_data = {}
            
            # Estrae e valida i dati dal form
            for key, var in self.form_vars.items():
                value = var.get().strip()
                
                # Campi Real (float)
                if key in ['created_amount', 'created_unit_price', 'created_total_value', 
                          'updated_amount', 'updated_unit_price', 'updated_total_value',
                          'accumulation_amount', 'income_per_year', 'rental_income']:
                    asset_data[key] = float(value) if value else 0.0
                
                # Campi Integer
                elif key == 'risk_level':
                    asset_data[key] = int(value) if value else 1
                
                # Campi Text (incluso position che ora è Text)
                else:
                    asset_data[key] = value if value else ""
            
            # Gestisce date automatiche SOLO se non inserite dall'utente
            from datetime import datetime
            if not asset_data.get('created_at') or asset_data.get('created_at').strip() == "":
                asset_data['created_at'] = datetime.now().strftime("%Y-%m-%d")
            
            # Per updated_at, rispetta SEMPRE l'input dell'utente (sia in creazione che modifica)
            if not asset_data.get('updated_at') or asset_data.get('updated_at').strip() == "":
                # Solo se il campo è vuoto, usa la data odierna
                asset_data['updated_at'] = datetime.now().strftime("%Y-%m-%d")
            
            # I valori totali vengono calcolati automaticamente dalle formule Excel
            # Non calcoliamo qui per evitare conflitti con le formule
            
            # I dati sono già nel formato corretto snake_case
            mapped_data = {
                'asset_id': None,  # Sarà assegnato automaticamente
                'category': asset_data.get('category', ''),
                'asset_name': asset_data.get('asset_name', ''),
                'position': asset_data.get('position', ''),
                'risk_level': asset_data.get('risk_level', 1),
                'ticker': asset_data.get('ticker', ''),
                'isin': asset_data.get('isin', ''),
                'created_at': asset_data.get('created_at', ''),
                'created_amount': asset_data.get('created_amount', 0.0),
                'created_unit_price': asset_data.get('created_unit_price', 0.0),
                'created_total_value': asset_data.get('created_total_value', 0.0),
                'updated_at': asset_data.get('updated_at', ''),
                'updated_amount': asset_data.get('updated_amount', 0.0),
                'updated_unit_price': asset_data.get('updated_unit_price', 0.0),
                'updated_total_value': asset_data.get('updated_total_value', 0.0),
                'accumulation_plan': asset_data.get('accumulation_plan', ''),
                'accumulation_amount': asset_data.get('accumulation_amount', 0.0),
                'income_per_year': asset_data.get('income_per_year', 0.0),
                'rental_income': asset_data.get('rental_income', 0.0),
                'note': asset_data.get('note', '')
            }
            
            # Crea l'oggetto Asset con i dati mappati
            asset = Asset(**mapped_data)
            
            # Salva l'asset nel database Excel - CREAZIONE o AGGIORNAMENTO
            if self.editing_asset_id is not None:
                # MODALITÀ MODIFICA - Aggiorna asset esistente con nomi snake_case (Excel format)
                excel_data = asset_data.copy()  # Usa i nomi snake_case
                excel_data['id'] = self.editing_asset_id  # Mantiene l'ID esistente
                if self.portfolio_manager.update_asset(self.editing_asset_id, excel_data):
                    messagebox.showinfo("Successo", f"Asset ID {self.editing_asset_id} aggiornato con successo!")
                    self.clear_form()
                    self.clear_edit_mode()  # Torna in modalità creazione
                    # Ricarica i dati e torna alla pagina Portfolio per vedere l'aggiornamento
                    self.load_portfolio_data()
                    self.show_page("Portfolio")
                else:
                    messagebox.showerror("Errore", "Errore nell'aggiornamento dell'asset")
            else:
                # MODALITÀ CREAZIONE - Nuovo asset
                if self.portfolio_manager.add_asset(asset):
                    messagebox.showinfo("Successo", "Nuovo asset aggiunto con successo!")
                    self.clear_form()
                    # Ricarica i dati del portfolio solo se siamo nella pagina Portfolio
                    if self.current_page == "Portfolio":
                        self.load_portfolio_data()
                else:
                    messagebox.showerror("Errore", "Errore nel salvataggio dell'asset")
                
        except ValueError as e:
            messagebox.showerror("Errore nei Dati", 
                               f"Errore nei dati numerici:\n\n{e}\n\n" + 
                               "Controlla che i campi numerici contengano solo numeri:\n" +
                               "• Quantità (es: 100)\n" + 
                               "• Prezzi (es: 25.50)\n" +
                               "• Importi (es: 1500.00)")
    
    def clear_form(self):
        for var in self.form_vars.values():
            var.set("")
    
    def edit_asset(self, event):
        selection = self.portfolio_tree.selection()
        if selection:
            asset_id = int(self.portfolio_tree.item(selection[0])['values'][0])
            asset = self.portfolio_manager.get_asset(asset_id)
            
            if asset:
                # Imposta modalità modifica
                self.editing_asset_id = asset_id
                
                # Switch to Asset page and populate form
                self.show_page("Asset")
                
                # Aggiorna titolo per indicare modifica
                self.update_asset_form_title("Modifica Asset")
                
                # Populate form with asset data
                self.form_vars['category'].set(asset.category)
                self.form_vars['asset_name'].set(asset.asset_name)
                self.form_vars['position'].set(str(asset.position))
                self.form_vars['risk_level'].set(str(asset.risk_level))
                self.form_vars['ticker'].set(asset.ticker)
                self.form_vars['isin'].set(asset.isin)
                self.form_vars['created_amount'].set(str(asset.created_amount))
                self.form_vars['created_unit_price'].set(str(asset.created_unit_price))
                self.form_vars['updated_amount'].set(str(asset.updated_amount))
                self.form_vars['updated_unit_price'].set(str(asset.updated_unit_price))
                self.form_vars['accumulation_plan'].set(asset.accumulation_plan)
                self.form_vars['accumulation_amount'].set(str(asset.accumulation_amount))
                self.form_vars['income_per_year'].set(str(asset.income_per_year))
                self.form_vars['rental_income'].set(str(asset.rental_income))
                self.form_vars['note'].set(asset.note)
                
                # Campi data (se esistenti) - convertiti in formato standard per il form
                if 'created_at' in self.form_vars and asset.created_at:
                    self.form_vars['created_at'].set(self.format_date_for_form(asset.created_at))
                if 'updated_at' in self.form_vars and asset.updated_at:
                    self.form_vars['updated_at'].set(self.format_date_for_form(asset.updated_at))
    
    def update_asset_form_title(self, title):
        """Aggiorna il titolo del form Asset"""
        if hasattr(self, 'asset_title_label'):
            self.asset_title_label.configure(text=title)
    
    def clear_edit_mode(self):
        """Esce dalla modalità modifica e torna alla creazione nuovo asset"""
        self.editing_asset_id = None
        self.update_asset_form_title("Nuovo Asset")
    
    def new_asset_mode(self):
        """Passa alla modalità Nuovo Asset (esce dalla modifica)"""
        self.clear_form()
        self.clear_edit_mode()
    
    def format_date_for_display(self, date_value):
        """Formatta le date in modo consistente per la visualizzazione (solo giorno)"""
        if pd.isna(date_value) or date_value == "" or date_value is None:
            return "-"
        
        date_str = str(date_value)
        
        # Prova diversi formati di parsing
        try:
            from datetime import datetime
            
            # Formato YYYY-MM-DD HH:MM:SS (da pandas/Excel)
            if " " in date_str and (":" in date_str):
                # Rimuove la parte dell'ora
                date_part = date_str.split(" ")[0]
                parsed_date = datetime.strptime(date_part, "%Y-%m-%d")
                return parsed_date.strftime("%d/%m/%Y")
            
            # Formato YYYY-MM-DD
            elif "-" in date_str and len(date_str.split()[0]) == 10:
                date_part = date_str.split()[0]  # Prende solo la parte data
                parsed_date = datetime.strptime(date_part, "%Y-%m-%d")
                return parsed_date.strftime("%d/%m/%Y")
                
            # Formato DD/MM/YYYY (già corretto)
            elif "/" in date_str and len(date_str.split()[0]) == 10:
                date_part = date_str.split()[0]  # Prende solo la parte data
                return date_part
                
            # Timestamp pandas (formato come '2024-08-24 00:00:00')
            elif isinstance(date_value, pd.Timestamp):
                return date_value.strftime("%d/%m/%Y")
                
            # Altri formati - prova a parsare come data ISO
            else:
                # Prova parsing generale
                parsed_date = pd.to_datetime(date_value)
                return parsed_date.strftime("%d/%m/%Y")
                
        except (ValueError, TypeError):
            # Se non riesce a parsare, ritorna solo la parte prima dello spazio (rimuove ora)
            if " " in date_str:
                return date_str.split()[0]
            return date_str
    
    def format_date_for_form(self, date_value):
        """Formatta le date per l'inserimento nel form (formato YYYY-MM-DD)"""
        if pd.isna(date_value) or date_value == "" or date_value is None:
            return ""
        
        date_str = str(date_value)
        
        try:
            # Formato DD/MM/YYYY -> YYYY-MM-DD
            if "/" in date_str and len(date_str) == 10:
                from datetime import datetime
                parsed_date = datetime.strptime(date_str, "%d/%m/%Y")
                return parsed_date.strftime("%Y-%m-%d")
            # Formato YYYY-MM-DD (già corretto)
            elif "-" in date_str:
                return date_str
            # Altri formati
            else:
                return date_str
        except ValueError:
            # Se non riesce a parsare, ritorna il valore originale
            return date_str
    
    def show_context_menu(self, event):
        # Context menu for delete functionality
        pass
    
    def update_chart(self, chart_type=None):
        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        df = self.portfolio_manager.load_data()
        
        if df.empty:
            ctk.CTkLabel(self.chart_frame, text="Nessun dato disponibile per i grafici").pack(pady=50)
            return
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        current_chart = self.chart_type.get()
        
        if current_chart == "Distribuzione per Categoria":
            category_counts = df['category'].value_counts()
            ax.pie(category_counts.values, labels=category_counts.index, autopct='%1.1f%%')
            ax.set_title("Distribuzione Asset per Categoria")
            
        elif current_chart == "Distribuzione Rischio":
            risk_counts = df['risk_level'].value_counts().sort_index()
            ax.bar(risk_counts.index, risk_counts.values, color=['green', 'lightgreen', 'yellow', 'orange', 'red'])
            ax.set_xlabel("Livello di Rischio")
            ax.set_ylabel("Numero di Asset")
            ax.set_title("Distribuzione del Rischio")
            
        elif current_chart == "Performance nel Tempo":
            # Simple value visualization
            categories = df.groupby('category')['updated_total_value'].sum().fillna(0)
            ax.bar(categories.index, categories.values)
            ax.set_xlabel("Categoria")
            ax.set_ylabel("Valore Totale (€)")
            ax.set_title("Valore per Categoria")
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def safe_export_pdf(self):
        """Wrapper sicuro per export PDF"""
        try:
            self.export_pdf()
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nell'esportazione PDF: {e}")
    
    def safe_export_csv(self):
        """Wrapper sicuro per export CSV"""
        try:
            self.export_csv()
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nell'esportazione CSV: {e}")

    def export_csv(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if filename:
                df = self.portfolio_manager.load_data()
                df.to_csv(filename, index=False)
                messagebox.showinfo("Successo", f"Portfolio esportato in {filename}")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nell'esportazione: {e}")
    
    def export_pdf(self):
        messagebox.showinfo("Info", "Funzionalità PDF in sviluppo")
    
    def backup_excel(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"portfolio_backup_{timestamp}.xlsx"
            
            df = self.portfolio_manager.load_data()
            df.to_excel(backup_filename, index=False)
            
            messagebox.showinfo("Successo", f"Backup creato: {backup_filename}")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel backup: {e}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = GABAssetMind()
        app.run()
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Errore GAB AssetMind", f"Errore critico: {e}")
        import traceback
        traceback.print_exc()