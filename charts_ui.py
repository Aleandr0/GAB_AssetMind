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
        """Crea grafico dell'evoluzione temporale del valore"""
        try:
            # Carica tutti i dati storici per l'evoluzione temporale
            all_data = self.portfolio_manager.load_data()
            
            if all_data.empty:
                self._show_no_data_message("Nessun dato storico disponibile")
                return
            
            # Prepara i dati temporali
            all_data['date'] = pd.to_datetime(all_data['updated_at'].fillna(all_data['created_at']), 
                                            format='%Y-%m-%d', errors='coerce')
            all_data['total_value'] = all_data['updated_total_value'].fillna(all_data['created_total_value']).fillna(0)
            
            # Filtra dati validi
            valid_data = all_data.dropna(subset=['date', 'total_value'])
            valid_data = valid_data[valid_data['total_value'] > 0]
            
            if valid_data.empty:
                self._show_no_data_message("Dati temporali insufficienti")
                return
            
            # Raggruppa per data e calcola valore totale
            daily_values = valid_data.groupby('date')['total_value'].sum().reset_index()
            daily_values = daily_values.sort_values('date')
            
            # Crea il grafico
            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.plot(daily_values['date'], daily_values['total_value'], 
                   marker='o', linewidth=2, markersize=4, 
                   color=UIConfig.COLORS['primary'], alpha=0.8)
            
            # Personalizzazione
            ax.set_xlabel("Data", fontsize=12, fontweight='bold')
            ax.set_ylabel("Valore Totale (€)", fontsize=12, fontweight='bold')
            ax.set_title("Evoluzione Temporale del Portfolio", fontsize=14, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3)
            
            # Formattazione asse x
            ax.tick_params(axis='x', rotation=45)
            
            # Formattazione asse y
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'€{x:,.0f}'))
            
            plt.tight_layout()
            self._display_chart(fig)
            
        except Exception as e:
            self._show_error_message(f"Errore nel grafico temporale: {e}")
    
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