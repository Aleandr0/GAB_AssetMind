#!/usr/bin/env python3
"""
Componente interfaccia grafici per GAB AssetMind
Gestisce la visualizzazione di grafici e analytics del portfolio
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from typing import Optional, Dict, Any
import numpy as np

from config import UIConfig
from utils import ErrorHandler, safe_execute
from models import PortfolioManager
from ui_components import BaseUIComponent

class ChartsUI(BaseUIComponent):
    """Componente per la visualizzazione di grafici e analytics"""
    
    def __init__(self, parent, portfolio_manager: PortfolioManager):
        super().__init__(parent, portfolio_manager)
        self.charts_frame = None
        self.chart_frame = None
        self.chart_type = None
        self.current_chart = None
        
        # Configurazione matplotlib per CustomTkinter
        plt.style.use('default')
        plt.rcParams.update({
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'axes.edgecolor': 'black',
            'axes.labelcolor': 'black',
            'text.color': 'black',
            'xtick.color': 'black',
            'ytick.color': 'black'
        })
    
    def create_charts_interface(self) -> ctk.CTkFrame:
        """Crea l'interfaccia completa per i grafici"""
        self.charts_frame = ctk.CTkFrame(self.parent)
        self.charts_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self._create_controls()
        self._create_chart_area()
        
        # Carica il grafico di default
        self.chart_type.set("Distribuzione Valore per Categoria")
        self._update_chart()
        
        return self.charts_frame
    
    def _create_controls(self):
        """Crea i controlli per la selezione del tipo di grafico"""
        controls_frame = ctk.CTkFrame(self.charts_frame, height=60)
        controls_frame.pack(fill="x", padx=10, pady=5)
        controls_frame.pack_propagate(False)
        
        # Label
        ctk.CTkLabel(
            controls_frame,
            text="Tipo Grafico:",
            font=ctk.CTkFont(**UIConfig.FONTS['subheader'])
        ).pack(side="left", padx=20, pady=15)
        
        # Dropdown selezione grafico
        chart_types = [
            "Distribuzione Valore per Categoria",
            "Distribuzione Rischio", 
            "Performance per Categoria",
            "Evoluzione Temporale"
        ]
        
        self.chart_type = ctk.StringVar(value=chart_types[0])
        
        chart_selector = ctk.CTkComboBox(
            controls_frame,
            values=chart_types,
            variable=self.chart_type,
            command=self._on_chart_type_changed,
            width=250,
            font=ctk.CTkFont(**UIConfig.FONTS['text'])
        )
        chart_selector.pack(side="left", padx=20, pady=15)
        
        # Pulsante refresh
        refresh_btn = ctk.CTkButton(
            controls_frame,
            text="🔄 Aggiorna",
            command=self._update_chart,
            **UIConfig.BUTTON_SIZES['medium'],
            font=ctk.CTkFont(**UIConfig.FONTS['button']),
            fg_color=UIConfig.COLORS['primary'],
            hover_color=UIConfig.COLORS['primary_hover']
        )
        refresh_btn.pack(side="left", padx=10, pady=15)
    
    def _create_chart_area(self):
        """Crea l'area per la visualizzazione dei grafici"""
        self.chart_frame = ctk.CTkFrame(self.charts_frame)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    def _on_chart_type_changed(self, selected_type: str):
        """Gestisce il cambio di tipo di grafico"""
        self._update_chart()
    
    def _update_chart(self):
        """Aggiorna il grafico corrente"""
        # Pulisce il grafico precedente
        for widget in self.chart_frame.winfo_children():
            safe_execute(lambda: widget.destroy())
        
        try:
            # Carica i dati (solo asset più recenti per coerenza)
            df = self.portfolio_manager.get_current_assets_only()
            
            if df.empty:
                self._show_no_data_message()
                return
            
            # Crea il grafico in base al tipo selezionato
            chart_type = self.chart_type.get()
            
            if chart_type == "Distribuzione Valore per Categoria":
                self._create_value_distribution_chart(df)
            elif chart_type == "Distribuzione Rischio":
                self._create_risk_distribution_chart(df)
            elif chart_type == "Performance per Categoria":
                self._create_performance_chart(df)
            elif chart_type == "Evoluzione Temporale":
                self._create_temporal_chart(df)
            
        except Exception as e:
            self._show_error_message(f"Errore nella creazione del grafico: {e}")
    
    def _create_value_distribution_chart(self, df: pd.DataFrame):
        """Crea grafico a torta della distribuzione valore per categoria"""
        try:
            # Calcola i valori per categoria usando la stessa logica del Portfolio Summary
            df['current_value'] = df['updated_total_value'].fillna(df['created_total_value']).fillna(0)
            category_values = df.groupby('category')['current_value'].sum()
            
            # Filtra categorie con valore > 0
            category_values = category_values[category_values > 0]
            
            if category_values.empty:
                self._show_no_data_message("Nessun valore da visualizzare")
                return
            
            # Crea il grafico
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Colori personalizzati
            colors = plt.cm.Set3(np.linspace(0, 1, len(category_values)))
            
            wedges, texts, autotexts = ax.pie(
                category_values.values,
                labels=category_values.index,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                textprops={'fontsize': 10}
            )
            
            # Migliora l'aspetto del testo
            for autotext in autotexts:
                autotext.set_color('black')
                autotext.set_weight('bold')
            
            ax.set_title("Distribuzione Valore per Categoria", 
                        fontsize=14, fontweight='bold', pad=20)
            
            # Aggiungi legenda con valori
            legend_labels = [f"{cat}: €{val:,.0f}" 
                           for cat, val in category_values.items()]
            ax.legend(wedges, legend_labels, title="Categorie", 
                     loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            
            self._display_chart(fig)
            
        except Exception as e:
            self._show_error_message(f"Errore nel grafico distribuzione valore: {e}")
    
    def _create_risk_distribution_chart(self, df: pd.DataFrame):
        """Crea grafico a barre della distribuzione del rischio"""
        try:
            # Conta gli asset per livello di rischio
            risk_counts = df['risk_level'].value_counts().sort_index()
            
            if risk_counts.empty:
                self._show_no_data_message("Nessun dato di rischio da visualizzare")
                return
            
            # Crea il grafico
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Colori dal verde (basso rischio) al rosso (alto rischio)
            colors = ['#16a34a', '#84cc16', '#eab308', '#f97316', '#dc2626']
            bar_colors = [colors[min(int(level)-1, 4)] for level in risk_counts.index]
            
            bars = ax.bar(risk_counts.index, risk_counts.values, color=bar_colors, alpha=0.8)
            
            # Personalizzazione
            ax.set_xlabel("Livello di Rischio", fontsize=12, fontweight='bold')
            ax.set_ylabel("Numero di Asset", fontsize=12, fontweight='bold')
            ax.set_title("Distribuzione del Rischio", fontsize=14, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3, axis='y')
            
            # Aggiungi etichette sulle barre
            for bar, count in zip(bars, risk_counts.values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{count}', ha='center', va='bottom', fontweight='bold')
            
            # Imposta i tick dell'asse x
            ax.set_xticks(risk_counts.index)
            ax.set_xticklabels([f"Livello {int(x)}" for x in risk_counts.index])
            
            plt.tight_layout()
            self._display_chart(fig)
            
        except Exception as e:
            self._show_error_message(f"Errore nel grafico distribuzione rischio: {e}")
    
    def _create_performance_chart(self, df: pd.DataFrame):
        """Crea grafico a barre delle performance per categoria"""
        try:
            # Calcola le performance (differenza tra updated e created)
            df['created_value'] = df['created_total_value'].fillna(0)
            df['updated_value'] = df['updated_total_value'].fillna(df['created_total_value']).fillna(0)
            df['performance'] = df['updated_value'] - df['created_value']
            
            # Raggruppa per categoria
            category_performance = df.groupby('category')['performance'].sum()
            
            # Filtra categorie con performance significativa
            category_performance = category_performance[category_performance.abs() > 1]
            
            if category_performance.empty:
                self._show_no_data_message("Nessuna performance da visualizzare")
                return
            
            # Crea il grafico
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Colori: verde per guadagni, rosso per perdite
            colors = ['#16a34a' if x >= 0 else '#dc2626' for x in category_performance.values]
            
            bars = ax.bar(range(len(category_performance)), category_performance.values, 
                         color=colors, alpha=0.8)
            
            # Personalizzazione
            ax.set_xlabel("Categoria", fontsize=12, fontweight='bold')
            ax.set_ylabel("Performance (€)", fontsize=12, fontweight='bold')
            ax.set_title("Performance per Categoria", fontsize=14, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3, axis='y')
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            
            # Etichette asse x
            ax.set_xticks(range(len(category_performance)))
            ax.set_xticklabels(category_performance.index, rotation=45, ha='right')
            
            # Etichette sulle barre
            for bar, value in zip(bars, category_performance.values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., 
                       height + (50 if height >= 0 else -100),
                       f'€{value:,.0f}', ha='center', 
                       va='bottom' if height >= 0 else 'top',
                       fontweight='bold', fontsize=9)
            
            plt.tight_layout()
            self._display_chart(fig)
            
        except Exception as e:
            self._show_error_message(f"Errore nel grafico performance: {e}")
    
    def _create_temporal_chart(self, df: pd.DataFrame):
        """Crea grafico dell'evoluzione del patrimonio nel tempo per categoria"""
        try:
            # Carica TUTTI i dati SENZA deduplicazione per mantenere la storia
            all_data = self.portfolio_manager.load_data()
            
            # VERIFICA: Confronta con il file Excel direttamente
            try:
                import pandas as pd
                excel_data = pd.read_excel(self.portfolio_manager.excel_file)
                excel_records = len(excel_data)
                loaded_records = len(all_data)
                
                print(f"DEBUG CONFRONTO CARICAMENTO:")
                print(f"  - Record nel file Excel: {excel_records}")
                print(f"  - Record caricati in memoria: {loaded_records}")
                print(f"  - Tutti i record caricati: {'✓ SÌ' if excel_records == loaded_records else '✗ NO'}")
                
                if excel_records != loaded_records:
                    print(f"  - ATTENZIONE: Mancano {excel_records - loaded_records} record!")
                    print(f"  - ID nel Excel: {sorted(excel_data['id'].tolist())}")
                    print(f"  - ID caricati: {sorted(all_data['id'].tolist())}")
                    
                    # Trova record mancanti
                    excel_ids = set(excel_data['id'].tolist())
                    loaded_ids = set(all_data['id'].tolist())
                    missing_ids = excel_ids - loaded_ids
                    if missing_ids:
                        print(f"  - Record mancanti (ID): {sorted(missing_ids)}")
                        
                        # Mostra info sui record mancanti
                        for missing_id in sorted(missing_ids):
                            missing_record = excel_data[excel_data['id'] == missing_id]
                            if not missing_record.empty:
                                created_at = missing_record['created_at'].iloc[0]
                                category = missing_record['category'].iloc[0] 
                                asset_name = missing_record['asset_name'].iloc[0]
                                print(f"    ID {missing_id}: {created_at} | {category} | {asset_name}")
                
            except Exception as e:
                print(f"DEBUG: Errore nel confronto con Excel: {e}")
            
            print(f"DEBUG: Record caricati: {len(all_data)}")
            
            if all_data.empty:
                self._show_no_data_message("Nessun dato disponibile")
                return
            
            # 1. RACCOLTA DI TUTTE LE DATE UNICHE da created_at e updated_at
            print(f"DEBUG: Analisi formati date:")
            print(f"  - Prime 5 created_at grezze: {all_data['created_at'].head().tolist()}")
            print(f"  - Ultime 5 created_at grezze: {all_data['created_at'].tail().tolist()}")
            
            # PARSING FLESSIBILE delle date - prova più formati
            def parse_flexible_dates(date_series, column_name):
                parsed_dates = []
                failed_dates = []
                
                for i, date_str in enumerate(date_series.dropna()):
                    parsed = None
                    original_str = str(date_str)
                    
                    # Prova diversi formati
                    formats_to_try = [
                        '%Y-%m-%d',     # 2004-05-21
                        '%d-%m-%Y',     # 21-05-2004  
                        '%d/%m/%Y',     # 21/05/2004
                        '%Y/%m/%d',     # 2004/05/21
                        '%m/%d/%Y',     # 05/21/2004
                        '%d.%m.%Y',     # 21.05.2004
                        '%Y.%m.%d'      # 2004.05.21
                    ]
                    
                    for fmt in formats_to_try:
                        try:
                            parsed = pd.to_datetime(original_str, format=fmt)
                            break
                        except:
                            continue
                    
                    if parsed is None:
                        # Ultimo tentativo: parsing automatico
                        try:
                            parsed = pd.to_datetime(original_str, infer_datetime_format=True)
                        except:
                            failed_dates.append((i, original_str))
                            continue
                    
                    parsed_dates.append(parsed)
                
                print(f"  - {column_name}: {len(parsed_dates)} valide, {len(failed_dates)} fallite")
                if failed_dates:
                    print(f"    Date fallite: {failed_dates}")
                    
                return pd.Series(parsed_dates)
            
            created_dates = parse_flexible_dates(all_data['created_at'], 'created_at')
            updated_dates = parse_flexible_dates(all_data['updated_at'], 'updated_at')
            
            print(f"DEBUG: Date created_at: {len(created_dates)} valide")
            print(f"DEBUG: Date updated_at: {len(updated_dates)} valide")
            if len(created_dates) > 0:
                print(f"DEBUG: Range created_at: {created_dates.min()} - {created_dates.max()}")
            if len(updated_dates) > 0:
                print(f"DEBUG: Range updated_at: {updated_dates.min()} - {updated_dates.max()}")
            
            # Lista univoca di date senza duplicati
            all_dates = sorted(set(created_dates.tolist() + updated_dates.tolist()))
            all_dates = [d for d in all_dates if not pd.isna(d)]
            
            print(f"DEBUG: Date univoche totali: {len(all_dates)}")
            print(f"DEBUG: Prima data: {all_dates[0] if all_dates else 'N/A'}")
            print(f"DEBUG: Ultima data: {all_dates[-1] if all_dates else 'N/A'}")
            
            if not all_dates:
                self._show_no_data_message("Nessuna data valida trovata")
                return
            
            # 2. CALCOLO PATRIMONIO PER OGNI DATA E CATEGORIA
            # Crea chiave univoca per identificare asset duplicati (stessa logica della navbar)
            all_data['asset_key'] = (all_data['category'].fillna('') + '|' + 
                                    all_data['asset_name'].fillna('') + '|' + 
                                    all_data['position'].fillna('') + '|' + 
                                    all_data['isin'].fillna(''))
            
            categories = all_data['category'].dropna().unique()
            timeline_data = {}
            
            # Per ogni data nella lista univoca
            for date in all_dates:
                date_values = {}
                
                # Per ogni categoria
                for category in categories:
                    category_value = 0
                    category_assets = all_data[all_data['category'] == category]
                    
                    # Per ogni asset unico di questa categoria
                    for asset_key in category_assets['asset_key'].unique():
                        asset_records = category_assets[category_assets['asset_key'] == asset_key]
                        
                        # Trova il record più appropriato per questa data
                        valid_records = []
                        for _, asset in asset_records.iterrows():
                            # Usa parsing flessibile anche qui
                            created_date = self._parse_single_date(asset['created_at'])
                            updated_date = self._parse_single_date(asset['updated_at'])
                            
                            # L'asset esiste solo se è già stato creato a questa data
                            if pd.notna(created_date) and date >= created_date:
                                # Determinare quale valore usare in base alla data
                                if pd.notna(updated_date) and date >= updated_date:
                                    # Usa valore aggiornato
                                    amount = asset['updated_amount'] if pd.notna(asset['updated_amount']) else 0
                                    price = asset['updated_unit_price'] if pd.notna(asset['updated_unit_price']) else 0
                                    record_date = updated_date
                                else:
                                    # Usa valore iniziale
                                    amount = asset['created_amount'] if pd.notna(asset['created_amount']) else 0
                                    price = asset['created_unit_price'] if pd.notna(asset['created_unit_price']) else 0
                                    record_date = created_date
                                
                                value = amount * price
                                valid_records.append((record_date, value))
                        
                        # Prendi l'ultimo valore valido per questo asset unico a questa data
                        if valid_records:
                            # Ordina per data e prendi il più recente
                            valid_records.sort(key=lambda x: x[0])
                            latest_value = valid_records[-1][1]
                            category_value += latest_value
                    
                    date_values[category] = category_value
                
                timeline_data[date] = date_values
            
            # DEBUG: Salva tabella debug nel file Excel
            self._save_debug_table_to_excel(timeline_data, categories)
            
            # VERIFICA: Confronta l'ultimo valore totale con quello della navbar
            self._verify_total_value(timeline_data)
            
            # 3. PREPARAZIONE DATI PER IL GRAFICO
            dates = sorted(timeline_data.keys())
            
            # Crea DataFrame per il grafico
            chart_data = pd.DataFrame(timeline_data).T
            chart_data = chart_data.fillna(0)
            
            # 4. CREAZIONE DEL GRAFICO
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Pulisci l'asse per evitare sovrapposizioni
            ax.clear()
            
            # Colori per le categorie
            colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
            
            # Una linea per ogni categoria
            lines_added = []
            for i, category in enumerate(categories):
                if category in chart_data.columns:
                    # Filtra solo le date dove la categoria ha valore > 0
                    category_data = chart_data[category]
                    category_data = category_data[category_data > 0]
                    
                    if len(category_data) > 0:
                        line = ax.plot(category_data.index, category_data.values, 
                                     marker='o', label=category, color=colors[i], 
                                     linewidth=2, markersize=4)
                        lines_added.append(f"Categoria: {category}")
            
            # UNA SOLA linea del totale
            total_values = chart_data.sum(axis=1)
            # Mostra totale solo dove c'è almeno una categoria con valore
            total_values = total_values[total_values > 0]
            
            print(f"DEBUG GRAFICO:")
            print(f"  - Linee categorie: {len(lines_added)}")
            print(f"  - Punti totale: {len(total_values)}")
            print(f"  - Valore finale totale: €{total_values.iloc[-1]:,.2f}" if len(total_values) > 0 else "  - Nessun valore totale")
            
            if len(total_values) > 0:
                ax.plot(total_values.index, total_values.values, 
                       marker='s', label='TOTALE', color='black', 
                       linewidth=3, markersize=6)
                lines_added.append("TOTALE")
            
            print(f"  - Linee totali nel grafico: {lines_added}")
            
            # 5. FORMATTAZIONE DEL GRAFICO
            ax.set_title('Evoluzione Patrimonio per Categoria', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Anno', fontsize=12)
            ax.set_ylabel('Valore (€)', fontsize=12)
            
            # Tutti gli anni interi sull'asse X
            years = sorted(set([d.year for d in dates]))
            if len(years) > 0:
                # Genera tutti gli anni dal primo all'ultimo
                year_range = list(range(min(years), max(years) + 1))
                year_dates = [pd.Timestamp(f'{year}-01-01') for year in year_range]
                ax.set_xticks(year_dates)
                ax.set_xticklabels(year_range)
                
                # Assicurati che tutti i tick siano visibili
                ax.tick_params(axis='x', rotation=0)
            
            # Formattazione asse Y con valuta
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'€{x:,.0f}'))
            
            # Griglia e legenda
            ax.grid(True, alpha=0.3)
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            self._display_chart(fig)
            
        except Exception as e:
            self._show_error_message(f"Errore nella creazione del grafico temporale: {e}")
    
    def _save_debug_table_to_excel(self, timeline_data, categories):
        """Salva tabella debug con date e categorie nel file Excel"""
        try:
            import openpyxl
            from openpyxl import Workbook, load_workbook
            import os
            
            excel_file = self.portfolio_manager.excel_file
            
            # Carica il workbook esistente o ne crea uno nuovo
            if os.path.exists(excel_file):
                wb = load_workbook(excel_file)
            else:
                wb = Workbook()
            
            # Rimuovi foglio debug se esiste
            if 'Debug_Timeline' in wb.sheetnames:
                del wb['Debug_Timeline']
            
            # Crea nuovo foglio debug
            ws_debug = wb.create_sheet('Debug_Timeline')
            
            # Prepara i dati per il foglio
            dates = sorted(timeline_data.keys())
            
            # Header: Data | Categoria1 | Categoria2 | ... | TOTALE
            headers = ['Data'] + list(categories) + ['TOTALE']
            ws_debug.append(headers)
            
            # Righe di dati
            for date in dates:
                row = [date.strftime('%Y-%m-%d')]
                date_total = 0
                
                for category in categories:
                    value = timeline_data[date].get(category, 0)
                    row.append(value)
                    date_total += value
                
                row.append(date_total)
                ws_debug.append(row)
            
            # Formattazione
            # Intestazioni in grassetto
            for cell in ws_debug[1]:
                cell.font = openpyxl.styles.Font(bold=True)
            
            # Formato valuta per le colonne dei valori
            from openpyxl.styles import NamedStyle
            currency_style = NamedStyle(name="currency", number_format="€#,##0.00")
            
            for row in ws_debug.iter_rows(min_row=2, min_col=2):
                for cell in row:
                    if cell.value and isinstance(cell.value, (int, float)):
                        cell.style = currency_style
            
            # Auto-width per le colonne
            for column in ws_debug.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                ws_debug.column_dimensions[column_letter].width = min(max_length + 2, 20)
            
            # Salva il file
            wb.save(excel_file)
            print(f"DEBUG: Salvata tabella debug nel foglio 'Debug_Timeline' di {excel_file}")
            
        except Exception as e:
            print(f"Errore nel salvare tabella debug: {e}")
    
    def _verify_total_value(self, timeline_data):
        """Verifica che l'ultimo valore totale corrisponda a quello della navbar"""
        try:
            if not timeline_data:
                return
                
            # Calcola il totale dell'ultima data
            last_date = max(timeline_data.keys())
            last_values = timeline_data[last_date]
            chart_total = sum(last_values.values())
            
            # Ottieni il valore dalla navbar (get_portfolio_summary)
            navbar_summary = self.portfolio_manager.get_portfolio_summary()
            navbar_total = navbar_summary['total_value']
            
            print(f"DEBUG VERIFICA:")
            print(f"  - Data più recente: {last_date.strftime('%Y-%m-%d')}")
            print(f"  - Totale grafico: €{chart_total:,.2f}")
            print(f"  - Totale navbar: €{navbar_total:,.2f}")
            print(f"  - Differenza: €{abs(chart_total - navbar_total):,.2f}")
            print(f"  - Corrispondenza: {'✓ SÌ' if abs(chart_total - navbar_total) < 0.01 else '✗ NO'}")
            
        except Exception as e:
            print(f"Errore nella verifica del valore totale: {e}")
    
    def _parse_single_date(self, date_str):
        """Parsing flessibile di una singola data"""
        if pd.isna(date_str) or date_str == '':
            return pd.NaT
            
        original_str = str(date_str)
        
        # Prova diversi formati
        formats_to_try = [
            '%Y-%m-%d',     # 2004-05-21
            '%d-%m-%Y',     # 21-05-2004  
            '%d/%m/%Y',     # 21/05/2004
            '%Y/%m/%d',     # 2004/05/21
            '%m/%d/%Y',     # 05/21/2004
            '%d.%m.%Y',     # 21.05.2004
            '%Y.%m.%d'      # 2004.05.21
        ]
        
        for fmt in formats_to_try:
            try:
                return pd.to_datetime(original_str, format=fmt)
            except:
                continue
        
        # Ultimo tentativo: parsing automatico
        try:
            return pd.to_datetime(original_str, infer_datetime_format=True)
        except:
            return pd.NaT
    
    def _display_chart(self, fig):
        """Visualizza il grafico nel frame"""
        try:
            plt.tight_layout()
            
            # Crea il canvas per CustomTkinter
            canvas = FigureCanvasTkAgg(fig, self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            
            # Salva riferimento per cleanup
            self.current_chart = canvas
            
        except Exception as e:
            self._show_error_message(f"Errore nella visualizzazione: {e}")
        finally:
            # Chiudi la figure per liberare memoria
            plt.close(fig)
    
    def _show_no_data_message(self, message: str = "Nessun dato disponibile per i grafici"):
        """Mostra un messaggio quando non ci sono dati"""
        label = ctk.CTkLabel(
            self.chart_frame,
            text=message,
            font=ctk.CTkFont(**UIConfig.FONTS['header']),
            text_color=UIConfig.COLORS['secondary']
        )
        label.pack(expand=True)
    
    def _show_error_message(self, message: str):
        """Mostra un messaggio di errore"""
        label = ctk.CTkLabel(
            self.chart_frame,
            text=f"❌ {message}",
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            text_color=UIConfig.COLORS['danger']
        )
        label.pack(expand=True)
    
    def refresh_charts(self):
        """Aggiorna i grafici con i dati più recenti"""
        safe_execute(self._update_chart)
    
    def cleanup(self):
        """Pulisce le risorse utilizzate dai grafici"""
        if self.current_chart:
            safe_execute(lambda: self.current_chart.get_tk_widget().destroy())
        plt.close('all')