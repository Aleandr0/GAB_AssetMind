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
import sys
import glob

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
        
        # Gestore del portfolio (interfaccia con Excel) - inizializza con file default
        # Il percorso completo verrà impostato dopo l'inizializzazione del sistema multi-portfolio
        self.portfolio_manager = None
        
        # Inizializza attributi per la navigazione
        self.current_page = "Portfolio"
        self.historical_mode = False  # Modalità creazione record storico
        self.page_frames = {}
        self.nav_buttons = {}
        
        # Attributi per la modifica asset
        self.editing_asset_id = None
        
        # Inizializza il sistema multi-portfolio prima di creare l'interfaccia
        self.current_portfolio_file = "portfolio_data.xlsx"  # File di default
        app_dir = self.get_application_directory()
        default_path = os.path.join(app_dir, self.current_portfolio_file)
        self.portfolio_manager = PortfolioManager(default_path)
        
        # Creazione interfaccia utente
        self.setup_ui()
        
        # Caricamento automatico dei dati esistenti
        self.root.after(100, self.load_portfolio_data)
    
    def setup_ui(self):
        """Configura l'interfaccia utente con barra di navigazione globale"""
        # Container principale
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Barra di navigazione globale sempre visibile
        self.create_global_navbar()
        
        # Container per il contenuto delle pagine
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=(5, 10))
        
        # Inizializza le pagine
        self.setup_all_pages()
        
        # Aggiorna la lista dei portfolio disponibili
        self.refresh_portfolio_list()
        
        # Mostra la pagina Portfolio per default
        self.show_page("Portfolio")
    
    def get_application_directory(self):
        """Ottiene la directory dell'applicazione (per .exe o script)"""
        if hasattr(sys, '_MEIPASS'):
            # Se eseguito come PyInstaller bundle
            return sys._MEIPASS
        else:
            # Se eseguito come script Python
            return os.path.dirname(os.path.abspath(__file__))
    
    def refresh_portfolio_list(self):
        """Aggiorna la lista dei file portfolio disponibili nella directory"""
        try:
            app_dir = self.get_application_directory()
            # Cerca tutti i file .xlsx nella directory dell'applicazione
            pattern = os.path.join(app_dir, "*.xlsx")
            excel_files = glob.glob(pattern)
            
            # Estrae solo i nomi dei file (senza percorso)
            portfolio_files = [os.path.basename(f) for f in excel_files]
            
            # Se non ci sono file, crea quello di default
            if not portfolio_files:
                portfolio_files = ["portfolio_data.xlsx"]
            
            # Ordina alfabeticamente
            portfolio_files.sort()
            
            # Aggiorna la dropdown
            if hasattr(self, 'portfolio_selector'):
                self.portfolio_selector.configure(values=portfolio_files)
                # Imposta il file corrente se è nella lista
                if self.current_portfolio_file in portfolio_files:
                    self.portfolio_selector.set(self.current_portfolio_file)
                elif portfolio_files:
                    # Imposta il primo file disponibile
                    self.current_portfolio_file = portfolio_files[0]
                    self.portfolio_selector.set(self.current_portfolio_file)
                    
        except Exception as e:
            print(f"Errore nel refresh lista portfolio: {e}")
            # Fallback al file di default
            if hasattr(self, 'portfolio_selector'):
                self.portfolio_selector.configure(values=["portfolio_data.xlsx"])
                self.portfolio_selector.set("portfolio_data.xlsx")
    
    def switch_portfolio(self, selected_file):
        """Cambia il portfolio attivo"""
        try:
            if selected_file != self.current_portfolio_file:
                self.current_portfolio_file = selected_file
                
                # Costruisce il percorso completo del file
                app_dir = self.get_application_directory()
                full_path = os.path.join(app_dir, selected_file)
                
                # Aggiorna il PortfolioManager con il nuovo file
                self.portfolio_manager = PortfolioManager(full_path)
                
                # Pulisce i filtri attivi
                if hasattr(self, 'column_filters'):
                    self.column_filters.clear()
                
                # Reset visualizzazione alla modalità Asset (non Record)
                if hasattr(self, 'show_all_records'):
                    self.show_all_records = False
                    if hasattr(self, 'assets_btn'):
                        self.assets_btn.configure(fg_color="#3b82f6", hover_color="#2563eb")
                        self.records_btn.configure(fg_color="#6b7280", hover_color="#4b5563")
                
                # Ricarica i dati del nuovo portfolio
                self.load_portfolio_data()
                
                print(f"Cambiato portfolio a: {selected_file}")
                
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile cambiare portfolio: {e}")
            # Ripristina la selezione precedente
            self.portfolio_selector.set(self.current_portfolio_file)
    
    def create_new_portfolio(self):
        """Crea un nuovo portfolio con nome personalizzato"""
        try:
            # Dialog per il nome del nuovo portfolio
            dialog = ctk.CTkInputDialog(text="Nome del nuovo portfolio:", title="Nuovo Portfolio")
            portfolio_name = dialog.get_input()
            
            if portfolio_name:
                # Assicura che abbia estensione .xlsx
                if not portfolio_name.lower().endswith('.xlsx'):
                    portfolio_name += '.xlsx'
                
                # Costruisce il percorso completo
                app_dir = self.get_application_directory()
                new_file_path = os.path.join(app_dir, portfolio_name)
                
                # Verifica che il file non esista già
                if os.path.exists(new_file_path):
                    messagebox.showerror("Errore", f"Il portfolio '{portfolio_name}' esiste già!")
                    return
                
                # Crea il nuovo PortfolioManager che creerà automaticamente il file
                new_portfolio_manager = PortfolioManager(new_file_path)
                
                # Aggiorna la lista e cambia al nuovo portfolio
                self.current_portfolio_file = portfolio_name
                self.portfolio_manager = new_portfolio_manager
                
                # Refresh la lista e seleziona il nuovo file
                self.refresh_portfolio_list()
                self.portfolio_selector.set(portfolio_name)
                
                # Pulisce filtri e ricarica
                if hasattr(self, 'column_filters'):
                    self.column_filters.clear()
                
                self.load_portfolio_data()
                
                messagebox.showinfo("Successo", f"Nuovo portfolio '{portfolio_name}' creato!")
                
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile creare nuovo portfolio: {e}")
    
    def create_global_navbar(self):
        """Crea la barra di navigazione globale sempre visibile"""
        # Barra principale
        navbar_frame = ctk.CTkFrame(self.main_frame, height=65)
        navbar_frame.pack(fill="x", padx=5, pady=(5, 5))
        navbar_frame.pack_propagate(False)  # Mantiene altezza fissa
        
        # Logo/Nome applicazione (sinistra)
        logo_label = ctk.CTkLabel(navbar_frame, text="GAB AssetMind", 
                                font=ctk.CTkFont(size=26, weight="bold"),
                                text_color=("#1f538d", "#14375e"))
        logo_label.pack(side="left", padx=20, pady=12)
        
        # Container per valori (centro)
        values_frame = ctk.CTkFrame(navbar_frame, fg_color="transparent")
        values_frame.pack(side="left", padx=40, pady=7)
        
        # Valore totale portfolio
        self.total_value_label = ctk.CTkLabel(values_frame, text="Valore Totale: €0", 
                                            font=ctk.CTkFont(size=18, weight="bold"),
                                            text_color=("#2d5016", "#4a7c59"))
        self.total_value_label.pack(pady=(3, 0))
        
        # Valore selezionato
        self.selected_value_label = ctk.CTkLabel(values_frame, text="Valore selezionato: €0", 
                                               font=ctk.CTkFont(size=14),
                                               text_color=("#1f538d", "#14375e"))
        self.selected_value_label.pack(pady=(0, 3))
        
        # Container per selezione portfolio (centro-destra)
        portfolio_section = ctk.CTkFrame(navbar_frame, fg_color="transparent")
        portfolio_section.pack(side="left", padx=20, pady=7)
        
        # Label portfolio
        portfolio_label = ctk.CTkLabel(portfolio_section, text="Portfolio:", 
                                     font=ctk.CTkFont(size=12, weight="bold"),
                                     text_color=("#1f538d", "#14375e"))
        portfolio_label.pack(side="top", pady=(0, 2))
        
        # Container per dropdown e pulsante nuovo
        selector_frame = ctk.CTkFrame(portfolio_section, fg_color="transparent")
        selector_frame.pack(side="top")
        
        # Dropdown selezione portfolio
        self.portfolio_selector = ctk.CTkComboBox(selector_frame, 
                                                command=self.switch_portfolio,
                                                width=140, height=28,
                                                font=ctk.CTkFont(size=11))
        self.portfolio_selector.pack(side="left", padx=(0, 5))
        
        # Pulsante per creare nuovo portfolio
        new_portfolio_btn = ctk.CTkButton(selector_frame, text="+", 
                                        command=self.create_new_portfolio,
                                        width=30, height=28,
                                        font=ctk.CTkFont(size=14, weight="bold"),
                                        fg_color="#16a34a", hover_color="#15803d")
        new_portfolio_btn.pack(side="left")
        
        # Container per i bottoni di navigazione (destra)
        nav_buttons_frame = ctk.CTkFrame(navbar_frame, fg_color="transparent")
        nav_buttons_frame.pack(side="right", padx=20, pady=7)
        
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
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Filter info section - Just show active filters and clear button
        filter_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        filter_frame.pack(side="left", fill="x", expand=True, padx=10)
        
        # Filter status label
        self.filter_status_label = ctk.CTkLabel(filter_frame, text="Click column headers to filter ▼", 
                                              font=ctk.CTkFont(size=12))
        self.filter_status_label.pack(side="left", padx=(0,15))
        
        # Clear filters button
        self.clear_filters_btn = ctk.CTkButton(filter_frame, text="Clear All Filters", 
                                             command=self.clear_all_filters, width=120,
                                             font=ctk.CTkFont(size=12, weight="bold"))
        self.clear_filters_btn.pack(side="left", padx=10)
        
        # Middle section - View toggle buttons (Record vs Asset view)
        view_section = ctk.CTkFrame(control_frame, fg_color="transparent")
        view_section.pack(side="left", padx=20)
        
        # Inizializza modalità visualizzazione (True = tutti i record, False = solo asset attuali)
        self.show_all_records = False  # Default: mostra solo asset attuali
        
        # Pulsanti per cambiare visualizzazione
        self.records_btn = ctk.CTkButton(view_section, text="Record 0", 
                                       command=self.show_all_records_view, width=100, height=30,
                                       font=ctk.CTkFont(size=11, weight="bold"),
                                       fg_color="#6b7280", hover_color="#4b5563")
        self.records_btn.pack(side="left", padx=2)
        
        self.assets_btn = ctk.CTkButton(view_section, text="Asset 0", 
                                      command=self.show_assets_only_view, width=100, height=30,
                                      font=ctk.CTkFont(size=11, weight="bold"),
                                      fg_color="#3b82f6", hover_color="#2563eb")  # Blu = attivo inizialmente
        self.assets_btn.pack(side="left", padx=2)
        
        # Right side - Zoom and info controls
        zoom_section = ctk.CTkFrame(control_frame, fg_color="transparent")
        zoom_section.pack(side="right", padx=10)
        
        # Asset count label rimosso - ora è nei pulsanti Record/Asset
        
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
        
        # Force container geometry update
        tree_container.update_idletasks()
        
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
        
        # Initialize column filters
        self.column_filters = {}  # Dizionario per mantenere i filtri attivi per colonna
        self.active_filter_popup = None  # Riferimento al popup attualmente aperto
        self.column_names = columns  # Salva i nomi delle colonne per aggiornare le intestazioni
        
        # Configurare le colonne con intestazioni cliccabili
        for col in columns:
            # Aggiunge freccia per indicare possibilità di filtro
            header_text = f"{col} ▼"
            self.portfolio_tree.heading(col, text=header_text, 
                                      command=lambda c=col: self.show_column_filter(c))
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
        
        # Force the tree to be visible and update
        self.portfolio_tree.update()
        self.portfolio_tree.update_idletasks()
        
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
                                    rowheight=new_height,
                                    background="white",
                                    foreground="black",
                                    fieldbackground="white")
            self.tree_style.configure("Portfolio.Treeview.Heading", 
                                    font=("TkDefaultFont", new_font_size, "bold"),
                                    background="#f0f0f0",
                                    foreground="black")
            
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
        """Configura la pagina Asset con menu fisso compatto"""
        frame = self.page_frames["Asset"]
        
        # Header unico con titolo e bottoni sulla stessa riga
        header_frame = ctk.CTkFrame(frame)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        # Titolo a sinistra
        self.asset_title_label = ctk.CTkLabel(header_frame, text="Gestione Asset", 
                                             font=ctk.CTkFont(size=18, weight="bold"))
        self.asset_title_label.pack(side="left", padx=20, pady=12)
        
        # Frame bottoni a destra, nell'ordine specificato
        buttons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        buttons_frame.pack(side="right", padx=20, pady=12)
        
        # 1. Pulisci Form
        self.clear_btn = ctk.CTkButton(buttons_frame, text="🔄 Pulisci Form", 
                                      command=self.clear_form, width=110, height=32,
                                      font=ctk.CTkFont(size=11, weight="bold"),
                                      fg_color="#6b7280", hover_color="#4b5563")
        self.clear_btn.pack(side="left", padx=3)
        
        # 2. Elimina Asset
        self.delete_btn = ctk.CTkButton(buttons_frame, text="🗑️ Elimina Asset", 
                                       command=self.delete_current_asset, width=110, height=32,
                                       font=ctk.CTkFont(size=11, weight="bold"),
                                       fg_color="#dc2626", hover_color="#b91c1c")
        self.delete_btn.pack(side="left", padx=3)
        
        # 3. Duplica Asset (ex Copia Asset)
        self.copy_asset_btn = ctk.CTkButton(buttons_frame, text="📋 Duplica Asset", 
                                           command=self.copy_asset_mode, width=120, height=32,
                                           font=ctk.CTkFont(size=11, weight="bold"),
                                           fg_color="#0891b2", hover_color="#0e7490")
        self.copy_asset_btn.pack(side="left", padx=4)
        
        # 4. Aggiorna Valore (ex Nuovo Record)
        self.new_record_btn = ctk.CTkButton(buttons_frame, text="📈 Aggiorna Valore", 
                                           command=self.create_historical_record_mode, width=120, height=32,
                                           font=ctk.CTkFont(size=11, weight="bold"),
                                           fg_color="#7c3aed", hover_color="#6d28d9")
        self.new_record_btn.pack(side="left", padx=4)
        
        # 5. Salva Asset
        self.save_btn = ctk.CTkButton(buttons_frame, text="💾 Salva Asset", 
                                     command=self.save_new_asset, width=120, height=32,
                                     font=ctk.CTkFont(size=11, weight="bold"))
        self.save_btn.pack(side="left", padx=4)
        
        # Scrollable frame per il form
        form_scroll = ctk.CTkScrollableFrame(frame)
        form_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Form frame con layout 2x2
        form_frame = ctk.CTkFrame(form_scroll)
        form_frame.pack(fill="both", expand=True, padx=5, pady=5)
        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Inizializza il form
        self.form_vars = {}
        self.form_widgets = {}  # Per poter disabilitare i campi
        
        # Mappatura campi rilevanti per categoria
        self.category_field_mapping = {
            "ETF": ["ticker", "isin", "income_per_year"],
            "Azioni": ["ticker", "isin", "income_per_year"], 
            "Fondi di investimento": ["ticker", "isin", "income_per_year"],
            "Buoni del Tesoro": ["isin", "income_per_year"],
            "PAC": ["ticker", "isin", "accumulation_plan", "accumulation_amount", "income_per_year"],
            "Criptovalute": ["ticker"],
            "Liquidità": ["income_per_year"],
            "Immobiliare": ["rental_income"],
            "Oggetti": []
        }
        
        # Mappatura campi numerici (riceveranno "0" quando non applicabili)
        self.numeric_fields = {
            "income_per_year", "rental_income", "accumulation_amount"
        }
        
        # Campi sempre attivi (per tutte le categorie)
        self.always_active_fields = [
            "category", "asset_name", "position", "risk_level", 
            "created_at", "created_amount", "created_unit_price", "created_total_value",
            "updated_at", "updated_amount", "updated_unit_price", "updated_total_value", 
            "note"
        ]
        
        self.create_asset_form(form_frame)
        
        # Inizializza con tutti i campi abilitati (nessuna categoria selezionata inizialmente)
        self.initialize_form_fields()
        
        # Inizializza lo stato dei bottoni
        self.update_asset_buttons_state()
    
    def setup_analytics_page(self):
        """Configura la pagina Grafici"""
        frame = self.page_frames["Grafici"]
        
        # Control frame
        control_frame = ctk.CTkFrame(frame)
        control_frame.pack(fill="x", padx=10, pady=5)
        
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
            ("Created Unit Price (€)", "created_unit_price", None),
            ("Created Total Value (auto) (€)", "created_total_value", None),
            ("Updated At (YYYY-MM-DD)", "updated_at", None),
            ("Updated Amount", "updated_amount", None),
            ("Updated Unit Price (€)", "updated_unit_price", None),
            ("Updated Total Value (auto) (€)", "updated_total_value", None),
            ("Accumulation Plan", "accumulation_plan", None),
            ("Accumulation Amount (€)", "accumulation_amount", None),
            ("Income Per Year (€)", "income_per_year", None),
            ("Rental Income (€)", "rental_income", None),
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
                # Se è la categoria, aggiungi callback per cambiare campi attivi
                if key == "category":
                    widget.configure(command=self.on_category_change)
            else:  # Entry per campi liberi
                var = ctk.StringVar()
                widget = ctk.CTkEntry(field_frame, textvariable=var, width=180)
            
            widget.pack(side="right", padx=10, pady=8)
            self.form_vars[key] = var
            self.form_widgets[key] = widget  # Salva il widget per poterlo disabilitare
    
    def on_category_change(self, selected_category):
        """Gestisce il cambio di categoria abilitando/disabilitando i campi appropriati"""
        if not hasattr(self, 'category_field_mapping'):
            return
            
        # Ottieni i campi rilevanti per questa categoria
        relevant_fields = self.always_active_fields + self.category_field_mapping.get(selected_category, [])
        
        # Abilita/disabilita i campi in base alla categoria
        for field_key, widget in self.form_widgets.items():
            if field_key in relevant_fields:
                # Campo rilevante - abilita
                widget.configure(state='normal')
                try:
                    widget.configure(fg_color=("white", "#343638"))  # Colore normale
                except:
                    pass
            else:
                # Campo non rilevante - disabilita e imposta valore di default
                widget.configure(state='disabled') 
                try:
                    widget.configure(fg_color=("#D0D0D0", "#404040"))  # Grigio
                except:
                    pass
                # Imposta valore di default per campi non applicabili
                if field_key in self.numeric_fields:
                    self.form_vars[field_key].set("0")
                else:
                    self.form_vars[field_key].set("NA")
    
    def initialize_form_fields(self):
        """Inizializza i campi del form (tutti abilitati di default)"""
        for widget in self.form_widgets.values():
            widget.configure(state='normal')
            try:
                widget.configure(fg_color=("white", "#343638"))  # Colore normale
            except:
                pass
    
    
        
    
    def save_new_asset(self):
        """Salva un nuovo asset dal form di input"""
        self.save_asset()
    
    
    
    def load_portfolio_data(self):
        """Carica i dati del portfolio dal file Excel e aggiorna la visualizzazione"""
        # Carica dati in base alla modalità di visualizzazione
        if hasattr(self, 'show_all_records') and self.show_all_records:
            # Mostra tutti i record (inclusi storici)
            df = self.portfolio_manager.load_data()
        else:
            # Mostra solo asset più recenti (default)
            df = self.portfolio_manager.get_current_assets_only()
        
        # Aggiorna i contatori dei pulsanti
        if hasattr(self, 'records_btn'):
            self.update_view_button_counts()
        
        if df.empty:
            self.update_summary()
            return
        
        # Usa il nuovo metodo unified per aggiornare la tabella
        self.update_portfolio_table(df)
        
        # Aggiorna scrollbar dopo caricamento dati
        self.root.after(100, self.update_scrollbars)
    
    def update_summary(self):
        """Aggiorna il sommario del portfolio (metodo legacy, ora usa update_portfolio_value)"""
        summary = self.portfolio_manager.get_portfolio_summary()
        self.total_value_label.configure(text=f"Valore Totale: €{summary['total_value']:,.2f}")
        
        # Conteggio asset ora gestito nei pulsanti Record/Asset
    
    
    def show_column_filter(self, column):
        """Mostra il filtro per una specifica colonna"""
        try:
            # Chiudi popup precedente se aperto
            if self.active_filter_popup:
                self.active_filter_popup.destroy()
                self.active_filter_popup = None
            
            # Ottieni i valori unici per questa colonna
            df = self.portfolio_manager.get_current_assets_only()
            if df.empty:
                return
            
            # Converti il nome colonna display in nome DataFrame
            column_mapping = {
                "ID": "id", "Category": "category", "Position": "position", 
                "Asset Name": "asset_name", "ISIN": "isin", "Ticker": "ticker",
                "Risk Level": "risk_level", "Created At": "created_at", 
                "Created Amount": "created_amount", "Created Unit Price": "created_unit_price",
                "Created Total Value": "created_total_value", "Updated At": "updated_at",
                "Updated Amount": "updated_amount", "Updated Unit Price": "updated_unit_price", 
                "Updated Total Value": "updated_total_value", "Accumulation Plan": "accumulation_plan",
                "Accumulation Amount": "accumulation_amount", "Income Per Year": "income_per_year",
                "Rental Income": "rental_income", "Note": "note"
            }
            
            df_column = column_mapping.get(column, column.lower().replace(" ", "_"))
            if df_column not in df.columns:
                return
            
            # Ottieni valori unici (escludendo NaN)
            unique_values = df[df_column].dropna().unique()
            
            # Ordina i valori
            if df[df_column].dtype in ['int64', 'float64']:
                unique_values = sorted(unique_values)
            else:
                unique_values = sorted([str(v) for v in unique_values])
            
            # Crea popup filter
            self.create_filter_popup(column, df_column, unique_values)
            
        except Exception as e:
            print(f"Errore nella creazione filtro colonna: {e}")
            import traceback
            traceback.print_exc()
    
    def create_filter_popup(self, display_column, df_column, unique_values):
        """Crea il popup di filtro per una colonna"""
        # Crea finestra popup
        popup = ctk.CTkToplevel(self.root)
        popup.title(f"Filter: {display_column}")
        popup.geometry("250x400")
        popup.transient(self.root)
        popup.grab_set()
        
        self.active_filter_popup = popup
        
        # Header
        header_label = ctk.CTkLabel(popup, text=f"Filter by {display_column}", 
                                   font=ctk.CTkFont(size=14, weight="bold"))
        header_label.pack(pady=10)
        
        # Search box per filtri di testo
        if df_column in ['asset_name', 'position', 'note', 'isin', 'ticker', 'accumulation_plan']:
            search_frame = ctk.CTkFrame(popup, fg_color="transparent")
            search_frame.pack(fill="x", padx=10, pady=5)
            
            search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search...")
            search_entry.pack(fill="x")
            
            def on_search(*args):
                search_text = search_entry.get().lower()
                for item in checkbox_frame.winfo_children():
                    if isinstance(item, ctk.CTkCheckBox):
                        item_text = item.cget("text").lower()
                        if search_text in item_text:
                            item.pack(fill="x", padx=5, pady=2)
                        else:
                            item.pack_forget()
            
            search_entry.bind('<KeyRelease>', on_search)
        
        # Scrollable frame per checkboxes
        checkbox_frame = ctk.CTkScrollableFrame(popup, height=250)
        checkbox_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # "All" option
        all_var = ctk.BooleanVar(value=df_column not in self.column_filters)
        all_checkbox = ctk.CTkCheckBox(checkbox_frame, text="(All)", variable=all_var)
        all_checkbox.pack(fill="x", padx=5, pady=2)
        
        # Checkboxes per ogni valore unico
        value_vars = {}
        current_filter = self.column_filters.get(df_column, set())
        
        for value in unique_values:
            display_value = str(value)[:30] + "..." if len(str(value)) > 30 else str(value)
            is_checked = len(current_filter) == 0 or value in current_filter
            
            var = ctk.BooleanVar(value=is_checked)
            checkbox = ctk.CTkCheckBox(checkbox_frame, text=display_value, variable=var)
            checkbox.pack(fill="x", padx=5, pady=2)
            value_vars[value] = var
        
        # Funzione per gestire "All"
        def toggle_all():
            select_all = all_var.get()
            for var in value_vars.values():
                var.set(select_all)
        
        all_checkbox.configure(command=toggle_all)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(popup, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        def apply_filter():
            selected_values = set()
            for value, var in value_vars.items():
                if var.get():
                    selected_values.add(value)
            
            if len(selected_values) == len(unique_values) or len(selected_values) == 0:
                # Tutti selezionati = nessun filtro
                if df_column in self.column_filters:
                    del self.column_filters[df_column]
            else:
                self.column_filters[df_column] = selected_values
            
            self.apply_column_filters()
            popup.destroy()
            self.active_filter_popup = None
        
        def clear_filter():
            if df_column in self.column_filters:
                del self.column_filters[df_column]
            self.apply_column_filters()
            popup.destroy()
            self.active_filter_popup = None
        
        # Apply e Clear buttons
        apply_btn = ctk.CTkButton(buttons_frame, text="Apply", command=apply_filter, width=100)
        apply_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(buttons_frame, text="Clear", command=clear_filter, width=100)
        clear_btn.pack(side="right", padx=5)
    
    def apply_column_filters(self):
        """Applica tutti i filtri di colonna attivi"""
        try:
            df = self.portfolio_manager.get_current_assets_only()
            
            # Applica ogni filtro di colonna
            for df_column, values in self.column_filters.items():
                if len(values) > 0:
                    df = df[df[df_column].isin(values)]
            
            # Aggiorna la tabella
            self.update_portfolio_table(df)
            
            # Aggiorna status label
            if len(self.column_filters) > 0:
                filter_text = f"{len(self.column_filters)} filter(s) active"
                self.filter_status_label.configure(text=filter_text)
            else:
                self.filter_status_label.configure(text="Click column headers to filter ▼")
            
            # Aggiorna le intestazioni delle colonne per mostrare i filtri attivi
            self.update_column_headers()
            
            # Aggiorna il valore delle righe visibili dopo aver applicato i filtri
            self.update_visible_value()
                
        except Exception as e:
            print(f"Errore nell'applicazione filtri colonna: {e}")
            import traceback
            traceback.print_exc()
    
    def clear_all_filters(self):
        """Rimuove tutti i filtri attivi"""
        try:
            self.column_filters.clear()
            self.apply_column_filters()
            
        except Exception as e:
            print(f"Errore nella pulizia filtri: {e}")
    
    def show_all_records_view(self):
        """Mostra tutti i record (inclusi i duplicati storici)"""
        self.show_all_records = True
        # Aggiorna colori pulsanti
        self.records_btn.configure(fg_color="#3b82f6", hover_color="#2563eb")  # Blu = attivo
        self.assets_btn.configure(fg_color="#6b7280", hover_color="#4b5563")   # Grigio = inattivo
        # Ricarica la visualizzazione
        self.load_portfolio_data()
    
    def show_assets_only_view(self):
        """Mostra solo gli asset più recenti (un record per asset)"""
        self.show_all_records = False
        # Aggiorna colori pulsanti
        self.records_btn.configure(fg_color="#6b7280", hover_color="#4b5563")   # Grigio = inattivo
        self.assets_btn.configure(fg_color="#3b82f6", hover_color="#2563eb")    # Blu = attivo
        # Ricarica la visualizzazione
        self.load_portfolio_data()
    
    def update_view_button_counts(self):
        """Aggiorna i contatori nei pulsanti Record/Asset"""
        try:
            # Carica tutti i dati per contare
            all_records_df = self.portfolio_manager.load_data()
            current_assets_df = self.portfolio_manager.get_current_assets_only()
            
            total_records = len(all_records_df)
            unique_assets = len(current_assets_df)
            
            # Aggiorna testi pulsanti
            self.records_btn.configure(text=f"Record {total_records}")
            self.assets_btn.configure(text=f"Asset {unique_assets}")
            
        except Exception as e:
            print(f"Errore nell'aggiornamento contatori: {e}")
            self.records_btn.configure(text="Record 0")
            self.assets_btn.configure(text="Asset 0")
    
    def update_visible_value(self):
        """Calcola e aggiorna il valore delle righe visibili nella tabella"""
        try:
            visible_value = 0.0
            visible_count = 0
            
            # Scorre tutte le righe visibili nella tabella
            for child in self.portfolio_tree.get_children():
                item_values = self.portfolio_tree.item(child)['values']
                if len(item_values) >= 15:
                    current_total = item_values[14]  # "Updated Total Value"
                    try:
                        # Rimuovi simboli di valuta e formattazione
                        current_total_str = str(current_total).replace('€', '').replace(',', '').strip()
                        if current_total_str and current_total_str != 'N/A':
                            value = float(current_total_str)
                            visible_value += value
                            visible_count += 1
                    except (ValueError, TypeError):
                        continue
            
            # Calcola la percentuale sul valore totale
            summary = self.portfolio_manager.get_portfolio_summary()
            total_value = summary.get('total_value', 0)
            percentage = (visible_value / total_value * 100) if total_value > 0 else 0
            
            # Aggiorna l'etichetta con percentuale
            self.selected_value_label.configure(text=f"Valore selezionato: €{visible_value:,.2f} ({percentage:.1f}%)")
            print(f"DEBUG: Aggiornato valore visibile: €{visible_value:,.2f} ({visible_count} righe)")
            
        except Exception as e:
            print(f"Errore nell'aggiornamento valore visibile: {e}")
            self.selected_value_label.configure(text="Valore selezionato: €0")
    
    def update_selected_value_with_total(self):
        """Aggiorna il valore selezionato con il totale del portfolio quando non c'è selezione"""
        try:
            summary = self.portfolio_manager.get_portfolio_summary()
            total_value = summary.get('total_value', 0)
            # Quando è selezionato tutto, la percentuale è 100%
            self.selected_value_label.configure(text=f"Valore selezionato: €{total_value:,.2f} (100.0%)")
        except Exception as e:
            self.selected_value_label.configure(text="Valore selezionato: €0")
    
    def update_column_headers(self):
        """Aggiorna le intestazioni delle colonne per mostrare i filtri attivi"""
        try:
            # Mappa per i nomi delle colonne display -> dataframe
            column_mapping = {
                "Asset Type": "asset_type",
                "Asset Name": "asset_name", 
                "Asset Symbol": "asset_symbol",
                "Country": "country",
                "Currency": "currency",
                "Created Date": "created_date",
                "Created Amount": "created_amount",
                "Created Unit Price": "created_unit_price",
                "Created Total": "created_total",
                "Current Date": "current_date",
                "Current Amount": "current_amount",
                "Current Unit Price": "current_unit_price", 
                "Current Total": "current_total",
                "Profit/Loss": "profit_loss",
                "P&L %": "profit_loss_percentage",
                "Sector": "sector",
                "ISIN": "isin",
                "Notes": "notes",
                "Exchange": "exchange",
                "Rating": "rating"
            }
            
            for display_col in self.column_names:
                df_column = column_mapping.get(display_col, display_col.lower().replace(" ", "_"))
                
                # Controlla se questa colonna ha un filtro attivo
                if df_column in self.column_filters:
                    # Intestazione per colonna filtrata (effetto grafico visibile)
                    header_text = f"★ {display_col} ▼"
                else:
                    # Intestazione normale
                    header_text = f"{display_col} ▼"
                
                self.portfolio_tree.heading(display_col, text=header_text,
                                          command=lambda c=display_col: self.show_column_filter(c))
            
        except Exception as e:
            print(f"Errore nell'aggiornamento intestazioni: {e}")
    
    def update_portfolio_table(self, df):
        """Aggiorna la tabella Portfolio con i dati forniti"""
        # Clear existing data
        for item in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(item)
        
        # Load new data
        for _, row in df.iterrows():
            # Calcola i valori totali in Python (le formule Excel potrebbero non essere valutate)
            created_total_calc = (row['created_amount'] if pd.notna(row['created_amount']) else 0) * \
                                (row['created_unit_price'] if pd.notna(row['created_unit_price']) else 0)
            updated_total_calc = (row['updated_amount'] if pd.notna(row['updated_amount']) else 0) * \
                                (row['updated_unit_price'] if pd.notna(row['updated_unit_price']) else 0)
            
            # Usa i valori calcolati se le formule Excel non sono disponibili
            current_value = row['updated_total_value'] if pd.notna(row['updated_total_value']) else updated_total_calc
            initial_value = row['created_total_value'] if pd.notna(row['created_total_value']) else created_total_calc
            
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
                str(row['isin']) if pd.notna(row['isin']) and str(row['isin']) != '' else "-",  # ISIN
                str(row['ticker']) if pd.notna(row['ticker']) and str(row['ticker']) != '' else "-",  # Ticker
                row['risk_level'],  # Risk Level
                self.format_date_for_display(row['created_at']),  # Created At
                f"{row['created_amount']:,.2f}" if pd.notna(row['created_amount']) else "0",  # Created Amount
                f"€{row['created_unit_price']:,.2f}" if pd.notna(row['created_unit_price']) else "€0",  # Created Unit Price
                f"€{created_total_calc:,.0f}" if created_total_calc > 0 else "€0",  # Created Total Value
                self.format_date_for_display(row['updated_at']),  # Updated At
                f"{row['updated_amount']:,.2f}" if pd.notna(row['updated_amount']) else "0",  # Updated Amount
                f"€{row['updated_unit_price']:,.2f}" if pd.notna(row['updated_unit_price']) else "€0",  # Updated Unit Price
                f"€{updated_total_calc:,.0f}" if updated_total_calc > 0 else "€0",  # Updated Total Value
                str(row['accumulation_plan']) if pd.notna(row['accumulation_plan']) and row['accumulation_plan'] != "" else "-",  # Accumulation Plan
                f"€{row['accumulation_amount']:,.0f}" if pd.notna(row['accumulation_amount']) and row['accumulation_amount'] > 0 else "-",  # Accumulation Amount
                f"€{row['income_per_year']:,.0f}" if pd.notna(row['income_per_year']) and row['income_per_year'] > 0 else "€0",  # Income Per Year
                f"€{row['rental_income']:,.0f}" if pd.notna(row['rental_income']) and row['rental_income'] > 0 else "€0",  # Rental Income
                str(row['note']) if pd.notna(row['note']) and row['note'] != "" else "-"  # Note
            ))
        
        # Aggiorna il sommario
        self.update_summary()
        
        # Inizializza il valore delle righe visibili
        self.update_visible_value()
    
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
        # Riabilita tutti i campi dopo aver pulito il form
        self.initialize_form_fields()
        # Esce dalla modalità modifica
        self.clear_edit_mode()
        self.disable_historical_mode()
        # Aggiorna lo stato dei bottoni
        self.update_asset_buttons_state()
    
    def edit_asset(self, event):
        selection = self.portfolio_tree.selection()
        if selection:
            asset_id = int(self.portfolio_tree.item(selection[0])['values'][0])
            asset = self.portfolio_manager.get_asset(asset_id)
            
            if asset:
                # Imposta modalità modifica
                self.editing_asset_id = asset_id
                
                # Switch to Asset page
                self.show_page("Asset")
                
                # POPOLA IL FORM con i dati dell'asset
                self.populate_form_with_asset(asset)
                
                # Aggiorna titolo per indicare modifica
                self.asset_title_label.configure(text=f"Asset ID: {asset_id} - Selezionato")
                
                # Aggiorna lo stato dei bottoni
                self.update_asset_buttons_state()
    
    def update_asset_form_title(self, title):
        """Aggiorna il titolo del form Asset"""
        if hasattr(self, 'asset_title_label'):
            self.asset_title_label.configure(text=title)
    
    def clear_edit_mode(self):
        """Esce dalla modalità modifica e torna alla creazione nuovo asset"""
        self.editing_asset_id = None
        self.asset_title_label.configure(text="Gestione Asset")
    
    
    def copy_asset_mode(self):
        """Crea un nuovo asset copiando i dati dall'asset corrente"""
        if self.editing_asset_id is not None:
            # Carica l'asset corrente
            asset = self.portfolio_manager.get_asset(self.editing_asset_id)
            if asset:
                # Esce dalla modalità modifica per entrare in modalità creazione nuovo asset
                self.clear_edit_mode()
                
                # Popola il form con i dati esistenti (escluso ID)
                self.populate_form_with_asset(asset)
                
                # Pulisce i campi che devono essere nuovi per un asset diverso
                self.form_vars['created_at'].set("")
                self.form_vars['updated_at'].set("")
                self.form_vars['created_amount'].set("0")
                self.form_vars['created_unit_price'].set("0")
                self.form_vars['updated_amount'].set("0") 
                self.form_vars['updated_unit_price'].set("0")
                
                # Abilita tutti i campi per la modifica
                self.disable_historical_mode()
                
                # Aggiorna titolo e stato bottoni
                self.asset_title_label.configure(text="Nuovo Asset (da copia)")
                self.update_asset_buttons_state()
                
                messagebox.showinfo("Copia Asset", "Asset copiato! Modifica i dati e clicca 'Salva Asset' per creare un nuovo asset.")
        else:
            messagebox.showwarning("Avviso", "Nessun asset selezionato per la copia. Seleziona un asset dalla tabella Portfolio.")
    
    
    def delete_current_asset(self):
        """Elimina l'asset correntemente selezionato"""
        if self.editing_asset_id is not None:
            asset = self.portfolio_manager.get_asset(self.editing_asset_id)
            if asset:
                # Conferma eliminazione
                result = messagebox.askyesno("Conferma Eliminazione", 
                                           f"Sei sicuro di voler eliminare l'asset:\n\n"
                                           f"ID: {asset.id}\n"
                                           f"Categoria: {asset.category}\n" 
                                           f"Nome: {asset.asset_name}\n"
                                           f"Posizione: {asset.position}\n\n"
                                           f"Questa operazione non può essere annullata.")
                
                if result:
                    # Elimina l'asset
                    success = self.portfolio_manager.delete_asset(self.editing_asset_id)
                    if success:
                        messagebox.showinfo("Asset Eliminato", f"Asset ID {self.editing_asset_id} eliminato con successo.")
                        
                        # Pulisce il form e torna alla modalità nuovo asset
                        self.clear_form()
                        self.clear_edit_mode()
                        self.disable_historical_mode()
                        
                        # Ricarica i dati nella tabella Portfolio
                        self.load_portfolio_data()
                        self.update_asset_buttons_state()
                    else:
                        messagebox.showerror("Errore", "Impossibile eliminare l'asset. Riprova.")
        else:
            messagebox.showwarning("Avviso", "Nessun asset selezionato per l'eliminazione.")
    
    def update_asset_buttons_state(self):
        """Aggiorna lo stato dei bottoni in base alla modalità corrente"""
        has_selected_asset = self.editing_asset_id is not None
        in_historical_mode = hasattr(self, 'historical_mode') and self.historical_mode
        
        # Bottoni sempre attivi: save_btn, clear_btn
        
        # Bottoni che richiedono un asset selezionato
        if has_selected_asset:
            self.delete_btn.configure(state="normal", fg_color="#dc2626")
            self.copy_asset_btn.configure(state="normal", fg_color="#0891b2")
            self.new_record_btn.configure(state="normal", fg_color="#7c3aed")
        else:
            self.delete_btn.configure(state="disabled", fg_color="#6b7280") 
            self.copy_asset_btn.configure(state="disabled", fg_color="#6b7280")
            self.new_record_btn.configure(state="disabled", fg_color="#6b7280")
        
        # Modifica testo e colore salva in base alla modalità
        if in_historical_mode:
            self.save_btn.configure(text="💾 Salva Valore", fg_color="#7c3aed")
        elif has_selected_asset:
            self.save_btn.configure(text="💾 Aggiorna Asset", fg_color="#f59e0b")
        else:
            self.save_btn.configure(text="💾 Salva Asset", fg_color="#3b82f6")
    
    def create_historical_record_mode(self):
        """Modalità creazione nuovo record storico: copia dati correnti e disabilita tutto tranne Updated Amount/Price"""
        if self.editing_asset_id is not None:
            # Copia tutti i dati dell'asset corrente
            asset = self.portfolio_manager.get_asset(self.editing_asset_id)
            if asset:
                # Esce dalla modalità modifica per entrare in modalità creazione
                self.clear_edit_mode()
                
                # Popola il form con i dati esistenti
                self.populate_form_with_asset(asset)
                
                # Aggiorna immediatamente la data Updated At
                from datetime import datetime
                current_date = datetime.now().strftime("%Y-%m-%d")
                self.form_vars['updated_at'].set(current_date)
                
                # Abilita la modalità storico
                self.enable_historical_mode()
                
                # Aggiorna il titolo
                self.update_asset_form_title("Nuovo Record Storico")
    
    def populate_form_with_asset(self, asset):
        """Popola il form con i dati di un asset - COPIA DIRETTA SENZA CONTROLLI"""
        
        # Copia diretta di tutti i valori - se è None/NaN usa stringa vuota
        def clean_value(value):
            if value is None:
                return ""
            value_str = str(value)
            if value_str.lower() in ['nan', 'none']:
                return ""
            return value_str
        
        # Formatta i valori monetari con simbolo euro e separatori
        def format_currency(value):
            if value is None:
                return ""
            value_str = str(value)
            if value_str.lower() in ['nan', 'none']:
                return ""
            try:
                # Converte in float e formatta come valuta
                num_value = float(value)
                if num_value == 0:
                    return "€0.00"
                return f"€{num_value:,.2f}"
            except:
                return value_str
        
        # COPIA DIRETTA tutti i campi
        self.form_vars['category'].set(clean_value(asset.category))
        self.form_vars['asset_name'].set(clean_value(asset.asset_name))
        self.form_vars['position'].set(clean_value(asset.position))
        self.form_vars['risk_level'].set(clean_value(asset.risk_level))
        self.form_vars['ticker'].set(clean_value(asset.ticker))
        self.form_vars['isin'].set(clean_value(asset.isin))
        
        # Date
        self.form_vars['created_at'].set(clean_value(asset.created_at))
        self.form_vars['updated_at'].set(clean_value(asset.updated_at))
        
        # Importi - ora senza formattazione valuta (simbolo € nelle etichette dei campi)
        self.form_vars['created_amount'].set(clean_value(asset.created_amount))  # Quantità
        self.form_vars['created_unit_price'].set(clean_value(asset.created_unit_price))  # Prezzo
        
        # Valori totali - senza formattazione valuta
        self.form_vars['created_total_value'].set(clean_value(asset.created_total_value))
        self.form_vars['updated_amount'].set(clean_value(asset.updated_amount))  # Quantità
        self.form_vars['updated_unit_price'].set(clean_value(asset.updated_unit_price))  # Prezzo
        self.form_vars['updated_total_value'].set(clean_value(asset.updated_total_value))
        
        # Altri campi monetari - senza formattazione valuta
        self.form_vars['accumulation_plan'].set(clean_value(asset.accumulation_plan))
        self.form_vars['accumulation_amount'].set(clean_value(asset.accumulation_amount))  # Importo mensile
        self.form_vars['income_per_year'].set(clean_value(asset.income_per_year))  # Importo annuale
        self.form_vars['rental_income'].set(clean_value(asset.rental_income))  # Importo annuale
        self.form_vars['note'].set(clean_value(asset.note))
        
        # Abilita tutti i campi per visualizzazione completa
        for widget in self.form_widgets.values():
            widget.configure(state='normal')
            try:
                widget.configure(fg_color=("white", "#343638"))  # Colore normale
            except:
                pass
    
    def enable_historical_mode(self):
        """Disabilita tutti i campi tranne Updated Amount e Updated Unit Price"""
        self.historical_mode = True
        
        # Disabilita tutti i campi tranne Updated Amount e Updated Unit Price
        for key, widget in self.form_widgets.items():
            if key not in ['updated_amount', 'updated_unit_price']:
                # Disabilita e rende grigio il campo
                widget.configure(state='disabled')
                # Per CustomTkinter, cambia anche il colore di sfondo per renderlo più grigio
                try:
                    widget.configure(fg_color=("#D0D0D0", "#404040"))  # Grigio chiaro/scuro per light/dark mode
                except:
                    pass  # Alcuni widget potrebbero non supportare fg_color
            else:
                # Assicurati che i campi editabili siano abilitati
                widget.configure(state='normal')
                try:
                    widget.configure(fg_color=("white", "#343638"))  # Colore normale per campi editabili
                except:
                    pass
        
        # Nascondi il pulsante "Nuovo Record" e mostra il pulsante per uscire
        self.historical_btn.pack_forget()
        
        # Aggiungiamo un pulsante per uscire dalla modalità storico
        exit_historical_btn = ctk.CTkButton(self.historical_btn.master, text="❌ Esci Storico", 
                                          command=self.disable_historical_mode, width=140, height=40,
                                          font=ctk.CTkFont(size=14, weight="bold"),
                                          fg_color="#dc2626", hover_color="#b91c1c")
        exit_historical_btn.pack(side="left", padx=5)
        self.exit_historical_btn = exit_historical_btn
    
    def disable_historical_mode(self):
        """Esce dalla modalità storico e riabilita tutti i campi"""
        self.historical_mode = False
        
        # Riabilita tutti i campi e ripristina i colori normali
        for widget in self.form_widgets.values():
            widget.configure(state='normal')
            try:
                widget.configure(fg_color=("white", "#343638"))  # Ripristina colore normale
            except:
                pass
        
        # Nascondi il pulsante "Esci Storico" se esiste
        if hasattr(self, 'exit_historical_btn'):
            self.exit_historical_btn.pack_forget()
            delattr(self, 'exit_historical_btn')
        
        # Mostra di nuovo il pulsante "Nuovo Record" se siamo in modalità modifica
        if self.editing_asset_id is not None:
            self.historical_btn.pack(side="left", padx=5)
    
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
        
        # Usa solo gli asset più recenti per coerenza con Portfolio
        df = self.portfolio_manager.get_current_assets_only()
        
        if df.empty:
            ctk.CTkLabel(self.chart_frame, text="Nessun dato disponibile per i grafici").pack(pady=50)
            return
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        current_chart = self.chart_type.get()
        
        if current_chart == "Distribuzione per Categoria":
            # Calcola i valori per categoria usando la stessa logica del Portfolio Summary
            df['current_value'] = df['updated_total_value'].fillna(df['created_total_value']).fillna(0)
            category_values = df.groupby('category')['current_value'].sum()
            ax.pie(category_values.values, labels=category_values.index, autopct='%1.1f%%')
            ax.set_title("Distribuzione Valore per Categoria")
            
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