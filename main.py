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
        
        # Creazione interfaccia utente
        self.setup_ui()
        
        # Caricamento automatico dei dati esistenti
        self.root.after(100, self.load_portfolio_data)
    
    def setup_ui(self):
        # Main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(self.main_frame)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(header_frame, text="GAB AssetMind", 
                                 font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(side="left", padx=20, pady=10)
        
        # Summary frame
        summary_frame = ctk.CTkFrame(header_frame)
        summary_frame.pack(side="right", padx=20, pady=10)
        
        self.total_value_label = ctk.CTkLabel(summary_frame, text="Valore Totale: €0", 
                                            font=ctk.CTkFont(size=16, weight="bold"))
        self.total_value_label.pack(side="left", padx=10)
        
        self.total_income_label = ctk.CTkLabel(summary_frame, text="Reddito Annuale: €0", 
                                             font=ctk.CTkFont(size=16, weight="bold"))
        self.total_income_label.pack(side="right", padx=10)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Portfolio Tab
        self.portfolio_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.portfolio_frame, text="Portfolio")
        self.setup_portfolio_tab()
        
        # Add Asset Tab
        self.add_asset_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.add_asset_frame, text="Aggiungi Asset")
        self.setup_add_asset_tab()
        
        # Analytics Tab
        self.analytics_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.analytics_frame, text="Grafici")
        self.setup_analytics_tab()
        
        # Export Tab
        self.export_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.export_frame, text="Export")
        self.setup_export_tab()
    
    def setup_portfolio_tab(self):
        # Filter frame
        filter_frame = ctk.CTkFrame(self.portfolio_frame)
        filter_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(filter_frame, text="Filtro Categoria:").pack(side="left", padx=10)
        
        self.category_filter = ctk.CTkComboBox(filter_frame, 
                                             values=["Tutti"] + self.portfolio_manager.categories,
                                             command=self.filter_by_category)
        self.category_filter.pack(side="left", padx=10)
        self.category_filter.set("Tutti")
        
        # Refresh button
        refresh_btn = ctk.CTkButton(filter_frame, text="Aggiorna", 
                                  command=self.load_portfolio_data)
        refresh_btn.pack(side="right", padx=10)
        
        # Treeview for portfolio
        tree_frame = ctk.CTkFrame(self.portfolio_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # TUTTI i 20 campi del database
        columns = ("ID", "Categoria", "Asset", "Posizione", "Rischio", "Ticker", "ISIN", 
                  "Data Creazione", "Qty Iniziale", "Prezzo Iniziale", "Valore Iniziale",
                  "Data Aggiorn.", "Qty Attuale", "Prezzo Attuale", "Valore Attuale", 
                  "Piano Accumulo", "Accumulo €", "Reddito/Anno", "Affitto/Anno", "Note")
        
        self.portfolio_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configurazione colonne con larghezze ottimizzate per tutti i campi
        column_widths = {
            "ID": 40, "Categoria": 90, "Asset": 150, "Posizione": 80, "Rischio": 60, 
            "Ticker": 70, "ISIN": 100, "Data Creazione": 90, "Qty Iniziale": 80, 
            "Prezzo Iniziale": 90, "Valore Iniziale": 90, "Data Aggiorn.": 90, 
            "Qty Attuale": 80, "Prezzo Attuale": 90, "Valore Attuale": 90, 
            "Piano Accumulo": 100, "Accumulo €": 80, "Reddito/Anno": 80, 
            "Affitto/Anno": 80, "Note": 120
        }
        
        for col in columns:
            self.portfolio_tree.heading(col, text=col)
            self.portfolio_tree.column(col, width=column_widths.get(col, 80), minwidth=60)
        
        # Scrollbar verticale
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.portfolio_tree.yview)
        self.portfolio_tree.configure(yscrollcommand=v_scrollbar.set)
        
        # Scrollbar orizzontale per gestire tutte le colonne
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.portfolio_tree.xview)
        self.portfolio_tree.configure(xscrollcommand=h_scrollbar.set)
        
        self.portfolio_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configura il grid per espansione
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Context menu
        self.portfolio_tree.bind("<Double-1>", self.edit_asset)
        self.portfolio_tree.bind("<Button-3>", self.show_context_menu)
    
    def setup_add_asset_tab(self):
        # Frame principale senza scroll (tutto visibile in una schermata)
        main_frame = ctk.CTkFrame(self.add_asset_frame)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header con titolo e pulsanti sulla stessa riga
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        # Titolo a sinistra
        title_label = ctk.CTkLabel(header_frame, text="Nuovo Asset", 
                                 font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(side="left", padx=20, pady=10)
        
        # Pulsanti a destra
        save_btn = ctk.CTkButton(header_frame, text="💾 SALVA", 
                               command=self.save_new_asset, width=120, height=40,
                               font=ctk.CTkFont(size=14, weight="bold"),
                               fg_color="green", hover_color="darkgreen")
        save_btn.pack(side="right", padx=10)
        
        clear_btn = ctk.CTkButton(header_frame, text="🗑️ PULISCI", 
                                command=self.clear_form, width=120, height=40,
                                font=ctk.CTkFont(size=14, weight="bold"),
                                fg_color="orange", hover_color="darkorange")
        clear_btn.pack(side="right", padx=10)
        
        # Asset form con layout 2 colonne
        self.form_vars = {}
        
        # Frame per il form con grid (non expand per lasciare spazio ai pulsanti)
        form_frame = ctk.CTkFrame(main_frame)
        form_frame.pack(fill="x", padx=10, pady=10)
        
        # Configurazione grid per 2 colonne
        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)
        
        fields = [
            ("Categoria", "category", self.portfolio_manager.categories),
            ("Nome Asset", "assetName", None),
            ("Posizione", "position", None),
            ("Livello Rischio (1-5)", "riskLevel", ["1", "2", "3", "4", "5"]),
            ("Ticker", "ticker", None),
            ("ISIN", "isin", None),
            ("Data Creazione (YYYY-MM-DD)", "createdAt", None),
            ("Quantità Iniziale", "createdAmount", None),
            ("Prezzo Unitario Iniziale", "createdUnitPrice", None),
            ("Valore Totale Iniziale (auto)", "createdTotalValue", None),
            ("Data Aggiornamento (YYYY-MM-DD)", "updatedAt", None),
            ("Quantità Attuale", "updatedAmount", None),
            ("Prezzo Unitario Attuale", "updatedUnitPrice", None),
            ("Valore Totale Attuale (auto)", "updatedTotalValue", None),
            ("Piano Accumulo", "accumulationPlan", None),
            ("Importo Accumulo Mensile", "accumulationAmount", None),
            ("Reddito Annuale", "incomePerYear", None),
            ("Reddito Immobiliare", "rentalIncome", None),
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
    
    def setup_analytics_tab(self):
        # Control frame
        control_frame = ctk.CTkFrame(self.analytics_frame)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        chart_types = ["Distribuzione per Categoria", "Distribuzione Rischio", "Performance nel Tempo"]
        self.chart_type = ctk.CTkComboBox(control_frame, values=chart_types, 
                                        command=self.update_chart)
        self.chart_type.pack(side="left", padx=10)
        self.chart_type.set(chart_types[0])
        
        # Chart frame
        self.chart_frame = ctk.CTkFrame(self.analytics_frame)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.update_chart()
    
    def setup_export_tab(self):
        export_frame = ctk.CTkFrame(self.export_frame)
        export_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(export_frame, text="Esporta Portfolio", 
                   font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        # Export options
        csv_btn = ctk.CTkButton(export_frame, text="Esporta CSV", 
                              command=self.export_csv, width=200, height=40)
        csv_btn.pack(pady=10)
        
        pdf_btn = ctk.CTkButton(export_frame, text="Esporta PDF Report", 
                              command=self.export_pdf, width=200, height=40)
        pdf_btn.pack(pady=10)
        
        backup_btn = ctk.CTkButton(export_frame, text="Backup Excel", 
                                 command=self.backup_excel, width=200, height=40)
        backup_btn.pack(pady=10)
    
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
            current_value = row['updatedTotalValue'] if pd.notna(row['updatedTotalValue']) else row['createdTotalValue']
            initial_value = row['createdTotalValue'] if pd.notna(row['createdTotalValue']) else 0
            total_income = (row['incomePerYear'] if pd.notna(row['incomePerYear']) else 0) + \
                          (row['rentalIncome'] if pd.notna(row['rentalIncome']) else 0)
            
            # Calcola performance percentuale
            performance = 0
            if pd.notna(initial_value) and initial_value > 0 and pd.notna(current_value):
                performance = ((current_value - initial_value) / initial_value) * 100
            
            self.portfolio_tree.insert("", "end", values=(
                row['Id'],  # ID
                row['category'],  # Categoria
                str(row['assetName'])[:20] + "..." if len(str(row['assetName'])) > 20 else str(row['assetName']),  # Asset
                str(row['position']) if pd.notna(row['position']) else "-",  # Posizione
                row['riskLevel'],  # Rischio
                str(row['ticker']) if pd.notna(row['ticker']) else "-",  # Ticker
                str(row['isin']) if pd.notna(row['isin']) else "-",  # ISIN
                str(row['createdAt']) if pd.notna(row['createdAt']) else "-",  # Data Creazione
                f"{row['createdAmount']:,.2f}" if pd.notna(row['createdAmount']) else "0",  # Qty Iniziale
                f"€{row['createdUnitPrice']:,.2f}" if pd.notna(row['createdUnitPrice']) else "€0",  # Prezzo Iniziale
                f"€{initial_value:,.0f}" if pd.notna(initial_value) else "€0",  # Valore Iniziale
                str(row['updatedAt']) if pd.notna(row['updatedAt']) else "-",  # Data Aggiorn.
                f"{row['updatedAmount']:,.2f}" if pd.notna(row['updatedAmount']) else "0",  # Qty Attuale
                f"€{row['updatedUnitPrice']:,.2f}" if pd.notna(row['updatedUnitPrice']) else "€0",  # Prezzo Attuale
                f"€{current_value:,.0f}" if pd.notna(current_value) else "€0",  # Valore Attuale
                str(row['accumulationPlan']) if pd.notna(row['accumulationPlan']) else "-",  # Piano Accumulo
                f"€{row['accumulationAmount']:,.0f}" if pd.notna(row['accumulationAmount']) else "€0",  # Accumulo €
                f"€{row['incomePerYear']:,.0f}" if pd.notna(row['incomePerYear']) else "€0",  # Reddito/Anno
                f"€{row['rentalIncome']:,.0f}" if pd.notna(row['rentalIncome']) else "€0",  # Affitto/Anno
                str(row['note'])[:15] + "..." if pd.notna(row['note']) and len(str(row['note'])) > 15 else (str(row['note']) if pd.notna(row['note']) else "-")  # Note
            ))
        
        # Aggiorna il sommario con i totali
        self.update_summary()
    
    def update_summary(self):
        summary = self.portfolio_manager.get_portfolio_summary()
        self.total_value_label.configure(text=f"Valore Totale: €{summary['total_value']:,.2f}")
        self.total_income_label.configure(text=f"Reddito Annuale: €{summary['total_income']:,.2f}")
    
    def filter_by_category(self, category):
        df = self.portfolio_manager.load_data()
        
        # Clear existing data
        for item in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(item)
        
        # Filter data
        if category != "Tutti":
            df = df[df['category'] == category]
        
        # Load filtered data
        for _, row in df.iterrows():
            current_value = row['updatedTotalValue'] if pd.notna(row['updatedTotalValue']) else row['createdTotalValue']
            initial_value = row['createdTotalValue'] if pd.notna(row['createdTotalValue']) else 0
            total_income = (row['incomePerYear'] if pd.notna(row['incomePerYear']) else 0) + \
                          (row['rentalIncome'] if pd.notna(row['rentalIncome']) else 0)
            
            # Calcola performance percentuale
            performance = 0
            if pd.notna(initial_value) and initial_value > 0 and pd.notna(current_value):
                performance = ((current_value - initial_value) / initial_value) * 100
            
            self.portfolio_tree.insert("", "end", values=(
                row['Id'],  # ID
                row['category'],  # Categoria
                str(row['assetName'])[:20] + "..." if len(str(row['assetName'])) > 20 else str(row['assetName']),  # Asset
                str(row['position']) if pd.notna(row['position']) else "-",  # Posizione
                row['riskLevel'],  # Rischio
                str(row['ticker']) if pd.notna(row['ticker']) else "-",  # Ticker
                str(row['isin']) if pd.notna(row['isin']) else "-",  # ISIN
                str(row['createdAt']) if pd.notna(row['createdAt']) else "-",  # Data Creazione
                f"{row['createdAmount']:,.2f}" if pd.notna(row['createdAmount']) else "0",  # Qty Iniziale
                f"€{row['createdUnitPrice']:,.2f}" if pd.notna(row['createdUnitPrice']) else "€0",  # Prezzo Iniziale
                f"€{initial_value:,.0f}" if pd.notna(initial_value) else "€0",  # Valore Iniziale
                str(row['updatedAt']) if pd.notna(row['updatedAt']) else "-",  # Data Aggiorn.
                f"{row['updatedAmount']:,.2f}" if pd.notna(row['updatedAmount']) else "0",  # Qty Attuale
                f"€{row['updatedUnitPrice']:,.2f}" if pd.notna(row['updatedUnitPrice']) else "€0",  # Prezzo Attuale
                f"€{current_value:,.0f}" if pd.notna(current_value) else "€0",  # Valore Attuale
                str(row['accumulationPlan']) if pd.notna(row['accumulationPlan']) else "-",  # Piano Accumulo
                f"€{row['accumulationAmount']:,.0f}" if pd.notna(row['accumulationAmount']) else "€0",  # Accumulo €
                f"€{row['incomePerYear']:,.0f}" if pd.notna(row['incomePerYear']) else "€0",  # Reddito/Anno
                f"€{row['rentalIncome']:,.0f}" if pd.notna(row['rentalIncome']) else "€0",  # Affitto/Anno
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
                if key in ['createdAmount', 'createdUnitPrice', 'createdTotalValue', 
                          'updatedAmount', 'updatedUnitPrice', 'updatedTotalValue',
                          'accumulationAmount', 'incomePerYear', 'rentalIncome']:
                    asset_data[key] = float(value) if value else 0.0
                
                # Campi Integer
                elif key == 'riskLevel':
                    asset_data[key] = int(value) if value else 1
                
                # Campi Text (incluso position che ora è Text)
                else:
                    asset_data[key] = value if value else ""
            
            # Gestisce date automatiche se non inserite
            from datetime import datetime
            if not asset_data.get('createdAt'):
                asset_data['createdAt'] = datetime.now().strftime("%Y-%m-%d")
            if not asset_data.get('updatedAt'):
                asset_data['updatedAt'] = datetime.now().strftime("%Y-%m-%d")
            
            # Calcola automaticamente i valori totali
            if asset_data.get('createdAmount') and asset_data.get('createdUnitPrice'):
                asset_data['createdTotalValue'] = asset_data['createdAmount'] * asset_data['createdUnitPrice']
            else:
                asset_data['createdTotalValue'] = 0.0
            
            if asset_data.get('updatedAmount') and asset_data.get('updatedUnitPrice'):
                asset_data['updatedTotalValue'] = asset_data['updatedAmount'] * asset_data['updatedUnitPrice']
            else:
                asset_data['updatedTotalValue'] = asset_data.get('createdTotalValue', 0.0)
            
            # Mappa i nomi dei campi da camelCase a snake_case
            mapped_data = {
                'asset_id': None,  # Sarà assegnato automaticamente
                'category': asset_data.get('category', ''),
                'asset_name': asset_data.get('assetName', ''),
                'position': asset_data.get('position', ''),  # Ora è text
                'risk_level': asset_data.get('riskLevel', 1),
                'ticker': asset_data.get('ticker', ''),
                'isin': asset_data.get('isin', ''),
                'created_at': asset_data.get('createdAt', ''),
                'created_amount': asset_data.get('createdAmount', 0.0),
                'created_unit_price': asset_data.get('createdUnitPrice', 0.0),
                'created_total_value': asset_data.get('createdTotalValue', 0.0),
                'updated_at': asset_data.get('updatedAt', ''),
                'updated_amount': asset_data.get('updatedAmount', 0.0),
                'updated_unit_price': asset_data.get('updatedUnitPrice', 0.0),
                'updated_total_value': asset_data.get('updatedTotalValue', 0.0),
                'accumulation_plan': asset_data.get('accumulationPlan', ''),
                'accumulation_amount': asset_data.get('accumulationAmount', 0.0),
                'income_per_year': asset_data.get('incomePerYear', 0.0),
                'rental_income': asset_data.get('rentalIncome', 0.0),
                'note': asset_data.get('note', '')
            }
            
            # Crea l'oggetto Asset con i dati mappati
            asset = Asset(**mapped_data)
            
            # Salva l'asset nel database Excel
            if self.portfolio_manager.add_asset(asset):
                messagebox.showinfo("Successo", "Asset aggiunto con successo!")
                self.clear_form()
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
                # Switch to add asset tab and populate form
                self.notebook.select(1)  # Add Asset tab
                
                # Populate form with asset data
                self.form_vars['category'].set(asset.category)
                self.form_vars['assetName'].set(asset.asset_name)
                self.form_vars['position'].set(str(asset.position))
                self.form_vars['riskLevel'].set(str(asset.risk_level))
                self.form_vars['ticker'].set(asset.ticker)
                self.form_vars['isin'].set(asset.isin)
                self.form_vars['createdAmount'].set(str(asset.created_amount))
                self.form_vars['createdUnitPrice'].set(str(asset.created_unit_price))
                self.form_vars['updatedAmount'].set(str(asset.updated_amount))
                self.form_vars['updatedUnitPrice'].set(str(asset.updated_unit_price))
                self.form_vars['accumulationPlan'].set(asset.accumulation_plan)
                self.form_vars['accumulationAmount'].set(str(asset.accumulation_amount))
                self.form_vars['incomePerYear'].set(str(asset.income_per_year))
                self.form_vars['rentalIncome'].set(str(asset.rental_income))
                self.form_vars['note'].set(asset.note)
    
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
            risk_counts = df['riskLevel'].value_counts().sort_index()
            ax.bar(risk_counts.index, risk_counts.values, color=['green', 'lightgreen', 'yellow', 'orange', 'red'])
            ax.set_xlabel("Livello di Rischio")
            ax.set_ylabel("Numero di Asset")
            ax.set_title("Distribuzione del Rischio")
            
        elif current_chart == "Performance nel Tempo":
            # Simple value visualization
            categories = df.groupby('category')['updatedTotalValue'].sum().fillna(0)
            ax.bar(categories.index, categories.values)
            ax.set_xlabel("Categoria")
            ax.set_ylabel("Valore Totale (€)")
            ax.set_title("Valore per Categoria")
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
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