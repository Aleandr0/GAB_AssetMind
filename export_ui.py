#!/usr/bin/env python3
"""
Componente interfaccia export per GAB AssetMind
Gestisce l'esportazione di dati in vari formati (CSV, PDF, Excel backup)
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
from datetime import datetime
import os
from typing import Optional

from config import UIConfig, Messages
from utils import ErrorHandler, safe_execute
from models import PortfolioManager
from ui_components import BaseUIComponent

class ExportUI(BaseUIComponent):
    """Componente per l'esportazione di dati"""
    
    def __init__(self, parent, portfolio_manager: PortfolioManager):
        super().__init__(parent, portfolio_manager)
        self.export_frame = None
    
    def create_export_interface(self) -> ctk.CTkFrame:
        """Crea l'interfaccia completa per l'export"""
        self.export_frame = ctk.CTkFrame(self.parent)
        self.export_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self._create_header()
        self._create_export_options()
        self._create_info_section()
        
        return self.export_frame
    
    def _create_header(self):
        """Crea l'header della pagina export"""
        header_frame = ctk.CTkFrame(self.export_frame, height=80)
        header_frame.pack(fill="x", padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        # Titolo
        title_label = ctk.CTkLabel(
            header_frame,
            text="📄 Esportazione Dati",
            font=ctk.CTkFont(**UIConfig.FONTS['title'])
        )
        title_label.pack(expand=True)
        
        # Sottotitolo
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Esporta i dati del portfolio in diversi formati",
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            text_color=UIConfig.COLORS['secondary']
        )
        subtitle_label.pack()
    
    def _create_export_options(self):
        """Crea le opzioni di esportazione"""
        options_frame = ctk.CTkFrame(self.export_frame)
        options_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Grid layout per le opzioni
        options_frame.grid_columnconfigure(0, weight=1)
        options_frame.grid_columnconfigure(1, weight=1)
        options_frame.grid_columnconfigure(2, weight=1)
        
        # Opzione 1: Export CSV
        self._create_export_card(
            options_frame, 0, 0,
            "📊 Export CSV",
            "Esporta tutti i dati in formato CSV\nCompatibile con Excel e altri software",
            "Esporta CSV",
            self._export_csv,
            UIConfig.COLORS['success']
        )
        
        # Opzione 2: Export PDF (placeholder per future implementation)
        self._create_export_card(
            options_frame, 0, 1,
            "📑 Report PDF",
            "Genera un report professionale\ncon grafici e analisi dettagliate",
            "Genera PDF",
            self._export_pdf,
            UIConfig.COLORS['primary']
        )
        
        # Opzione 3: Backup Excel
        self._create_export_card(
            options_frame, 0, 2,
            "💾 Backup Excel",
            "Crea una copia di sicurezza\ndel database Excel completo",
            "Backup",
            self._backup_excel,
            UIConfig.COLORS['warning']
        )
        
        # Opzione 4: Export Asset Correnti
        self._create_export_card(
            options_frame, 1, 0,
            "🎯 Asset Attuali",
            "Esporta solo gli asset più recenti\n(senza storico duplicati)",
            "Export Attuali",
            self._export_current_assets,
            UIConfig.COLORS['info']
        )
        
        # Opzione 5: Export per Categoria
        self._create_export_card(
            options_frame, 1, 1,
            "🏷️ Per Categoria",
            "Esporta dati filtrati\nper una categoria specifica",
            "Export Categoria",
            self._export_by_category,
            UIConfig.COLORS['purple']
        )
        
        # Opzione 6: Import Dati (future feature)
        self._create_export_card(
            options_frame, 1, 2,
            "📥 Import Dati",
            "Importa dati da file CSV\n(Funzionalità futura)",
            "Import",
            self._import_data,
            UIConfig.COLORS['secondary'],
            enabled=False
        )
    
    def _create_export_card(self, parent, row: int, col: int, title: str, 
                           description: str, button_text: str, command: callable,
                           color: str, enabled: bool = True):
        """Crea una card per un'opzione di export"""
        card_frame = ctk.CTkFrame(parent, corner_radius=10)
        card_frame.grid(row=row, column=col, padx=15, pady=15, sticky="nsew", ipadx=20, ipady=20)
        
        # Titolo
        title_label = ctk.CTkLabel(
            card_frame,
            text=title,
            font=ctk.CTkFont(**UIConfig.FONTS['subheader'])
        )
        title_label.pack(pady=(10, 5))
        
        # Descrizione
        desc_label = ctk.CTkLabel(
            card_frame,
            text=description,
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            text_color=UIConfig.COLORS['secondary'],
            justify="center"
        )
        desc_label.pack(pady=(0, 15))
        
        # Bottone
        button = ctk.CTkButton(
            card_frame,
            text=button_text,
            command=command if enabled else None,
            **UIConfig.BUTTON_SIZES['medium'],
            font=ctk.CTkFont(**UIConfig.FONTS['button']),
            fg_color=color if enabled else UIConfig.COLORS['secondary'],
            hover_color=f"{color}_hover" if enabled else UIConfig.COLORS['secondary_hover'],
            state="normal" if enabled else "disabled"
        )
        button.pack(pady=(0, 10))
    
    def _create_info_section(self):
        """Crea la sezione informativa"""
        info_frame = ctk.CTkFrame(self.export_frame, height=100)
        info_frame.pack(fill="x", padx=10, pady=10)
        info_frame.pack_propagate(False)
        
        # Statistiche portfolio
        self._update_portfolio_stats(info_frame)
    
    def _update_portfolio_stats(self, parent):
        """Aggiorna le statistiche del portfolio"""
        try:
            # Carica statistiche
            summary = self.portfolio_manager.get_portfolio_summary()
            current_assets_count = len(self.portfolio_manager.get_current_assets_only())
            total_records_count = len(self.portfolio_manager.load_data())
            
            # Layout orizzontale per le stats
            stats_container = ctk.CTkFrame(parent, fg_color="transparent")
            stats_container.pack(expand=True, fill="both", padx=20, pady=20)
            
            stats = [
                ("📊 Asset Attuali", f"{current_assets_count}"),
                ("📈 Record Totali", f"{total_records_count}"),
                ("💰 Valore Totale", f"€{summary.get('total_value', 0):,.2f}"),
                ("📅 Ultimo Export", self._get_last_export_time())
            ]
            
            for i, (label, value) in enumerate(stats):
                stat_frame = ctk.CTkFrame(stats_container)
                stat_frame.pack(side="left", expand=True, fill="both", padx=5)
                
                label_widget = ctk.CTkLabel(
                    stat_frame,
                    text=label,
                    font=ctk.CTkFont(**UIConfig.FONTS['text'])
                )
                label_widget.pack(pady=(10, 0))
                
                value_widget = ctk.CTkLabel(
                    stat_frame,
                    text=value,
                    font=ctk.CTkFont(**UIConfig.FONTS['subheader'])
                )
                value_widget.pack(pady=(0, 10))
                
        except Exception as e:
            print(f"Errore aggiornamento statistiche: {e}")
    
    def _get_last_export_time(self) -> str:
        """Restituisce l'ora dell'ultimo export (placeholder)"""
        # In una versione futura, questo potrebbe essere salvato in un file di configurazione
        return "Mai"
    
    def _export_csv(self):
        """Esporta tutti i dati in formato CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Salva Export CSV",
                defaultextension=".csv",
                filetypes=[("File CSV", "*.csv"), ("Tutti i file", "*.*")],
                initialname=f"portfolio_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            if filename:
                df = self.portfolio_manager.load_data()
                if df.empty:
                    messagebox.showwarning("Avviso", "Nessun dato da esportare")
                    return
                
                # Esporta con encoding UTF-8 per supportare caratteri speciali
                df.to_csv(filename, index=False, encoding='utf-8-sig', sep=';')
                
                messagebox.showinfo("Successo", 
                                  f"Dati esportati con successo!\n\nFile: {os.path.basename(filename)}\n"
                                  f"Record esportati: {len(df)}\n"
                                  f"Percorso: {filename}")
                
                self.trigger_callback('export_completed', 'CSV', filename)
                
        except Exception as e:
            error_msg = ErrorHandler.handle_file_error(e, "export CSV")
            messagebox.showerror("Errore Export", error_msg)
    
    def _export_current_assets(self):
        """Esporta solo gli asset più recenti"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Salva Asset Attuali",
                defaultextension=".csv",
                filetypes=[("File CSV", "*.csv"), ("Tutti i file", "*.*")],
                initialname=f"asset_attuali_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            if filename:
                df = self.portfolio_manager.get_current_assets_only()
                if df.empty:
                    messagebox.showwarning("Avviso", "Nessun asset attuale da esportare")
                    return
                
                df.to_csv(filename, index=False, encoding='utf-8-sig', sep=';')
                
                messagebox.showinfo("Successo",
                                  f"Asset attuali esportati con successo!\n\n"
                                  f"File: {os.path.basename(filename)}\n"
                                  f"Asset esportati: {len(df)}")
                
                self.trigger_callback('export_completed', 'Current Assets', filename)
                
        except Exception as e:
            error_msg = ErrorHandler.handle_file_error(e, "export asset attuali")
            messagebox.showerror("Errore Export", error_msg)
    
    def _export_by_category(self):
        """Esporta dati filtrati per categoria"""
        try:
            # Dialog per selezione categoria
            from config import AssetConfig
            
            dialog = ctk.CTkInputDialog(
                text=f"Inserisci categoria da esportare:\n{', '.join(AssetConfig.CATEGORIES)}",
                title="Export per Categoria"
            )
            category = dialog.get_input()
            
            if not category:
                return
                
            if category not in AssetConfig.CATEGORIES:
                messagebox.showerror("Errore", f"Categoria '{category}' non valida")
                return
            
            filename = filedialog.asksaveasfilename(
                title=f"Salva Export {category}",
                defaultextension=".csv",
                filetypes=[("File CSV", "*.csv"), ("Tutti i file", "*.*")],
                initialname=f"{category.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            if filename:
                df = self.portfolio_manager.load_data()
                filtered_df = df[df['category'] == category]
                
                if filtered_df.empty:
                    messagebox.showwarning("Avviso", f"Nessun asset trovato per la categoria '{category}'")
                    return
                
                filtered_df.to_csv(filename, index=False, encoding='utf-8-sig', sep=';')
                
                messagebox.showinfo("Successo",
                                  f"Export categoria '{category}' completato!\n\n"
                                  f"File: {os.path.basename(filename)}\n"
                                  f"Asset esportati: {len(filtered_df)}")
                
                self.trigger_callback('export_completed', f'Category {category}', filename)
                
        except Exception as e:
            error_msg = ErrorHandler.handle_data_error(e, "export per categoria")
            messagebox.showerror("Errore Export", error_msg)
    
    def _backup_excel(self):
        """Crea un backup del database Excel"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = filedialog.asksaveasfilename(
                title="Salva Backup Excel",
                defaultextension=".xlsx",
                filetypes=[("File Excel", "*.xlsx"), ("Tutti i file", "*.*")],
                initialname=f"portfolio_backup_{timestamp}.xlsx"
            )
            
            if filename:
                df = self.portfolio_manager.load_data()
                if df.empty:
                    messagebox.showwarning("Avviso", "Nessun dato da fare backup")
                    return
                
                # Salva usando il metodo del PortfolioManager per mantenere le formule
                backup_manager = PortfolioManager(filename)
                backup_manager.save_data(df)
                
                messagebox.showinfo("Successo",
                                  f"Backup creato con successo!\n\n"
                                  f"File: {os.path.basename(filename)}\n"
                                  f"Record inclusi: {len(df)}\n"
                                  f"Include formule Excel originali")
                
                self.trigger_callback('export_completed', 'Excel Backup', filename)
                
        except Exception as e:
            error_msg = ErrorHandler.handle_file_error(e, "backup Excel")
            messagebox.showerror("Errore Backup", error_msg)
    
    def _export_pdf(self):
        """Genera un report PDF (funzionalità futura)"""
        messagebox.showinfo(
            "Funzionalità Futura",
            "La generazione di report PDF sarà implementata in una versione futura.\n\n"
            "Il report includerà:\n"
            "• Sommario esecutivo con metriche principali\n"
            "• Grafici di distribuzione per categoria\n"
            "• Tabelle dettagliate degli asset principali\n"
            "• Analisi di performance e rischio"
        )
    
    def _import_data(self):
        """Importa dati da file esterno (funzionalità futura)"""
        messagebox.showinfo(
            "Funzionalità Futura",
            "L'importazione di dati da file esterni sarà implementata in una versione futura.\n\n"
            "Supporterà:\n"
            "• Import da file CSV con mapping automatico\n"
            "• Validazione dati durante l'import\n"
            "• Preview e conferma prima dell'inserimento\n"
            "• Merge intelligente con dati esistenti"
        )
    
    def refresh_stats(self):
        """Aggiorna le statistiche visualizzate"""
        # Rimuove e ricrea la sezione info
        for widget in self.export_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                children = widget.winfo_children()
                if len(children) > 0 and any("Asset Attuali" in str(child) for child in children if hasattr(child, 'cget')):
                    widget.destroy()
                    self._create_info_section()
                    break