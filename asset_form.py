#!/usr/bin/env python3
"""
Componente form per gestione asset in GAB AssetMind
Gestisce creazione, modifica e validazione degli asset
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from config import UIConfig, AssetConfig, Messages
from utils import DataValidator, DateFormatter, ErrorHandler, safe_execute
from models import Asset, PortfolioManager
from ui_components import BaseUIComponent

class FormState:
    """Gestione dello stato del form asset"""
    
    def __init__(self):
        self.mode = 'create'  # 'create', 'edit', 'historical', 'copy'
        self.editing_asset_id: Optional[int] = None
        self.historical_mode = False
    
    def set_create_mode(self):
        """Imposta modalità creazione nuovo asset"""
        self.mode = 'create'
        self.editing_asset_id = None
        self.historical_mode = False
    
    def set_edit_mode(self, asset_id: int):
        """Imposta modalità modifica asset esistente"""
        self.mode = 'edit'
        self.editing_asset_id = asset_id
        self.historical_mode = False
    
    def set_copy_mode(self, asset_id: int):
        """Imposta modalità copia asset"""
        self.mode = 'copy'
        self.editing_asset_id = asset_id
        self.historical_mode = False
    
    def set_historical_mode(self, asset_id: int):
        """Imposta modalità creazione record storico"""
        self.mode = 'historical'
        self.editing_asset_id = asset_id
        self.historical_mode = True
    
    def is_editing(self) -> bool:
        """Verifica se siamo in modalità modifica"""
        return self.editing_asset_id is not None
    
    def get_title(self) -> str:
        """Restituisce il titolo appropriato per lo stato corrente"""
        titles = {
            'create': 'Gestione Asset',
            'edit': f'Asset ID: {self.editing_asset_id} - Selezionato',
            'copy': 'Nuovo Asset (da copia)',
            'historical': f'Nuovo Record - Asset ID: {self.editing_asset_id}'
        }
        return titles.get(self.mode, 'Gestione Asset')

class AssetForm(BaseUIComponent):
    """Componente form per gestione asset"""
    
    def __init__(self, parent, portfolio_manager: PortfolioManager):
        super().__init__(parent, portfolio_manager)
        self.form_frame = None
        self.form_vars: Dict[str, ctk.StringVar] = {}
        self.form_widgets: Dict[str, ctk.CTkWidget] = {}
        self.state = FormState()
        
        # Riferimenti UI
        self.title_label = None
        self.clear_btn = None
        self.delete_btn = None
        self.copy_btn = None
        self.new_record_btn = None
        self.save_btn = None
    
    def create_form(self) -> ctk.CTkFrame:
        """Crea il form completo per la gestione asset"""
        self.form_frame = ctk.CTkFrame(self.parent)
        self.form_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self._create_header()
        self._create_form_fields()
        self._initialize_form()
        
        return self.form_frame
    
    def _create_header(self):
        """Crea l'header con titolo e bottoni"""
        header_frame = ctk.CTkFrame(self.form_frame)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        # Titolo a sinistra
        self.title_label = ctk.CTkLabel(
            header_frame,
            text=self.state.get_title(),
            font=ctk.CTkFont(**UIConfig.FONTS['header'])
        )
        self.title_label.pack(side="left", padx=20, pady=12)
        
        # Bottoni a destra
        buttons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        buttons_frame.pack(side="right", padx=20, pady=12)
        
        self._create_buttons(buttons_frame)
    
    def _create_buttons(self, parent):
        """Crea i bottoni di controllo"""
        # 1. Pulisci Form
        self.clear_btn = ctk.CTkButton(
            parent,
            text="🔄 Pulisci Form",
            command=self._clear_form,
            **UIConfig.BUTTON_SIZES['compact'],
            font=ctk.CTkFont(**UIConfig.FONTS['button']),
            fg_color=UIConfig.COLORS['secondary'],
            hover_color=UIConfig.COLORS['secondary_hover']
        )
        self.clear_btn.pack(side="left", padx=3)
        
        # 2. Elimina Asset
        self.delete_btn = ctk.CTkButton(
            parent,
            text="🗑️ Elimina Asset",
            command=self._delete_asset,
            **UIConfig.BUTTON_SIZES['compact'],
            font=ctk.CTkFont(**UIConfig.FONTS['button']),
            fg_color=UIConfig.COLORS['danger'],
            hover_color=UIConfig.COLORS['danger_hover']
        )
        self.delete_btn.pack(side="left", padx=3)
        
        # 3. Duplica Asset
        self.copy_btn = ctk.CTkButton(
            parent,
            text="📋 Duplica Asset",
            command=self._copy_asset,
            **UIConfig.BUTTON_SIZES['medium'],
            font=ctk.CTkFont(**UIConfig.FONTS['button']),
            fg_color=UIConfig.COLORS['info'],
            hover_color=UIConfig.COLORS['info_hover']
        )
        self.copy_btn.pack(side="left", padx=4)
        
        # 4. Aggiorna Valore
        self.new_record_btn = ctk.CTkButton(
            parent,
            text="📈 Aggiorna Valore",
            command=self._create_historical_record,
            **UIConfig.BUTTON_SIZES['medium'],
            font=ctk.CTkFont(**UIConfig.FONTS['button']),
            fg_color=UIConfig.COLORS['purple'],
            hover_color=UIConfig.COLORS['purple_hover']
        )
        self.new_record_btn.pack(side="left", padx=4)
        
        # 5. Salva Asset
        self.save_btn = ctk.CTkButton(
            parent,
            text="💾 Salva Asset",
            command=self._save_asset,
            **UIConfig.BUTTON_SIZES['medium'],
            font=ctk.CTkFont(**UIConfig.FONTS['button']),
            fg_color=UIConfig.COLORS['primary'],
            hover_color=UIConfig.COLORS['primary_hover']
        )
        self.save_btn.pack(side="left", padx=4)
    
    def _create_form_fields(self):
        """Crea i campi del form"""
        # Scrollable frame per il form
        form_scroll = ctk.CTkScrollableFrame(self.form_frame)
        form_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Form frame con layout 2x2
        form_container = ctk.CTkFrame(form_scroll)
        form_container.pack(fill="both", expand=True, padx=5, pady=5)
        form_container.grid_columnconfigure(0, weight=1)
        form_container.grid_columnconfigure(1, weight=1)
        
        # Definizione campi del form
        fields = [
            ("Categoria", "category", AssetConfig.CATEGORIES),
            ("Asset Name", "asset_name", None),
            ("Posizione", "position", None),
            ("Risk Level (1-5)", "risk_level", AssetConfig.RISK_LEVELS),
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
            self._create_field(form_container, i, label, key, values)
    
    def _create_field(self, parent, index: int, label: str, key: str, values: Optional[list]):
        """Crea un singolo campo del form"""
        row = index // 2  # Riga (0, 1, 2, ...)
        col = index % 2   # Colonna (0 o 1)
        
        # Frame per ogni campo
        field_frame = ctk.CTkFrame(parent)
        field_frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
        
        # Label
        label_widget = ctk.CTkLabel(
            field_frame,
            text=label,
            width=150,
            font=ctk.CTkFont(**UIConfig.FONTS['text'])
        )
        label_widget.pack(side="left", padx=10, pady=8)
        
        # Widget di input
        var = ctk.StringVar()
        
        if values:  # ComboBox per campi con valori predefiniti
            widget = ctk.CTkComboBox(
                field_frame,
                values=values,
                variable=var,
                width=180,
                font=ctk.CTkFont(**UIConfig.FONTS['text'])
            )
            # Se è la categoria, aggiungi callback
            if key == "category":
                widget.configure(command=self._on_category_change)
        else:  # Entry per campi liberi
            widget = ctk.CTkEntry(
                field_frame,
                textvariable=var,
                width=180,
                font=ctk.CTkFont(**UIConfig.FONTS['text'])
            )
        
        widget.pack(side="right", padx=10, pady=8)
        
        # Salva riferimenti
        self.form_vars[key] = var
        self.form_widgets[key] = widget
    
    def _initialize_form(self):
        """Inizializza il form con tutti i campi abilitati"""
        for widget in self.form_widgets.values():
            safe_execute(lambda w=widget: w.configure(state='normal'))
            safe_execute(lambda w=widget: w.configure(fg_color=("white", "#343638")))
        
        self._update_button_states()
    
    def _on_category_change(self, selected_category: str):
        """Gestisce il cambio di categoria abilitando/disabilitando i campi appropriati"""
        if not selected_category:
            return
        
        # Ottieni i campi rilevanti per questa categoria
        relevant_fields = (AssetConfig.ALWAYS_ACTIVE_FIELDS + 
                          AssetConfig.CATEGORY_FIELD_MAPPING.get(selected_category, []))
        
        # Abilita/disabilita i campi in base alla categoria
        for field_key, widget in self.form_widgets.items():
            if field_key in relevant_fields:
                # Campo rilevante - abilita
                safe_execute(lambda: widget.configure(state='normal'))
                safe_execute(lambda: widget.configure(fg_color=("white", "#343638")))
            else:
                # Campo non rilevante - disabilita e imposta valore di default
                safe_execute(lambda: widget.configure(state='disabled'))
                safe_execute(lambda: widget.configure(fg_color=("#D0D0D0", "#404040")))
                
                # Imposta valore di default per campi non applicabili
                if field_key in AssetConfig.NUMERIC_DEFAULT_FIELDS:
                    safe_execute(lambda: self.form_vars[field_key].set("0"))
                else:
                    safe_execute(lambda: self.form_vars[field_key].set("NA"))
    
    def _clear_form(self):
        """Pulisce tutti i campi del form"""
        for var in self.form_vars.values():
            safe_execute(lambda v=var: v.set(""))
        
        # Reset stato
        self.state.set_create_mode()
        self._update_title()
        self._initialize_form()
        self._update_button_states()
        
        self.trigger_callback('form_cleared')
    
    def _delete_asset(self):
        """Elimina l'asset correntemente selezionato"""
        if not self.state.is_editing():
            messagebox.showwarning("Avviso", Messages.WARNINGS['no_asset_selected'])
            return
        
        asset = self.portfolio_manager.get_asset(self.state.editing_asset_id)
        if not asset:
            messagebox.showerror("Errore", "Asset non trovato")
            return
        
        # Conferma eliminazione
        result = messagebox.askyesno(
            "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare l'asset:\n\n"
            f"ID: {asset.id}\n"
            f"Categoria: {asset.category}\n"
            f"Nome: {asset.asset_name}\n"
            f"Posizione: {asset.position}\n\n"
            f"Questa operazione non può essere annullata."
        )
        
        if result:
            success = self.portfolio_manager.delete_asset(self.state.editing_asset_id)
            if success:
                messagebox.showinfo("Asset Eliminato", 
                                  f"Asset ID {self.state.editing_asset_id} eliminato con successo.")
                self._clear_form()
                self.trigger_callback('asset_deleted', self.state.editing_asset_id)
            else:
                messagebox.showerror("Errore", "Impossibile eliminare l'asset. Riprova.")
    
    def _copy_asset(self):
        """Crea un nuovo asset copiando i dati dall'asset corrente"""
        if not self.state.is_editing():
            messagebox.showwarning("Avviso", Messages.WARNINGS['no_asset_selected'])
            return
        
        asset = self.portfolio_manager.get_asset(self.state.editing_asset_id)
        if asset:
            # Imposta modalità copia
            self.state.set_copy_mode(self.state.editing_asset_id)
            
            # Popola il form con i dati esistenti
            self.populate_form(asset)
            
            # Pulisce i campi che devono essere nuovi per un asset diverso
            self.form_vars['created_at'].set("")
            self.form_vars['updated_at'].set("")
            self.form_vars['created_amount'].set("0")
            self.form_vars['created_unit_price'].set("0")
            self.form_vars['updated_amount'].set("0")
            self.form_vars['updated_unit_price'].set("0")
            
            self._update_title()
            self._update_button_states()
            
            messagebox.showinfo("Copia Asset", Messages.SUCCESS['asset_copied'])
        else:
            messagebox.showwarning("Avviso", Messages.WARNINGS['no_asset_selected'])
    
    def _create_historical_record(self):
        """Crea un record storico per l'asset corrente"""
        if not self.state.is_editing():
            messagebox.showwarning("Avviso", Messages.WARNINGS['no_asset_selected'])
            return
        
        # Imposta modalità storica
        self.state.set_historical_mode(self.state.editing_asset_id)
        self._enable_historical_mode()
        self._update_title()
        self._update_button_states()
    
    def _enable_historical_mode(self):
        """Abilita la modalità storica (solo campi Updated Amount e Updated Unit Price)"""
        editable_fields = ['updated_amount', 'updated_unit_price']
        
        for key, widget in self.form_widgets.items():
            if key in editable_fields:
                # Campi editabili
                safe_execute(lambda: widget.configure(state='normal'))
                safe_execute(lambda: widget.configure(fg_color=("white", "#343638")))
            else:
                # Campi disabilitati
                safe_execute(lambda: widget.configure(state='disabled'))
                safe_execute(lambda: widget.configure(fg_color=("#D0D0D0", "#404040")))
    
    def _disable_historical_mode(self):
        """Disabilita la modalità storica"""
        if self.state.historical_mode:
            self.state.historical_mode = False
            self._initialize_form()
    
    def _save_asset(self):
        """Salva l'asset corrente"""
        try:
            # Validazione dati
            asset_data = self._collect_form_data()
            if not asset_data:
                return
            
            # Salvataggio in base alla modalità
            success = False
            
            if self.state.mode == 'create' or self.state.mode == 'copy':
                # Nuovo asset
                asset = Asset(**asset_data)
                success = self.portfolio_manager.add_asset(asset)
                action = "creato"
            
            elif self.state.mode == 'edit':
                # Modifica asset esistente
                success = self.portfolio_manager.update_asset(
                    self.state.editing_asset_id, 
                    asset_data
                )
                action = "aggiornato"
            
            elif self.state.mode == 'historical':
                # Nuovo record storico
                asset_data['updated_at'] = datetime.now().strftime("%Y-%m-%d")
                asset = Asset(**asset_data)
                success = self.portfolio_manager.add_asset(asset)
                action = "registrato (nuovo record)"
            
            # Gestione risultato
            if success:
                messagebox.showinfo("Successo", f"Asset {action} con successo!")
                self._clear_form()
                self.trigger_callback('asset_saved', asset_data)
            else:
                messagebox.showerror("Errore", f"Impossibile salvare l'asset: {Messages.ERRORS['save_failed']}")
        
        except Exception as e:
            error_msg = ErrorHandler.handle_data_error(e, "salvataggio asset")
            messagebox.showerror("Errore", error_msg)
    
    def _collect_form_data(self) -> Optional[Dict[str, Any]]:
        """Raccoglie e valida i dati dal form"""
        try:
            data = {}
            
            # Campi obbligatori
            required_fields = ['category', 'asset_name']
            for field in required_fields:
                value = self.form_vars[field].get().strip()
                if not value:
                    messagebox.showerror("Errore", f"Il campo {field} è obbligatorio")
                    return None
                data[field] = value
            
            # Campi testuali
            text_fields = ['position', 'ticker', 'isin', 'accumulation_plan', 'note']
            for field in text_fields:
                data[field] = DataValidator.clean_value(self.form_vars[field].get())
            
            # Campi numerici
            numeric_fields = [
                'risk_level', 'created_amount', 'updated_amount',
                'created_unit_price', 'updated_unit_price',
                'created_total_value', 'updated_total_value',
                'accumulation_amount', 'income_per_year', 'rental_income'
            ]
            for field in numeric_fields:
                value = self.form_vars[field].get().strip()
                data[field] = DataValidator.validate_numeric(value, field)
            
            # Campi data
            date_fields = ['created_at', 'updated_at']
            for field in date_fields:
                value = self.form_vars[field].get().strip()
                data[field] = DataValidator.validate_date(value)
            
            # Validazione ISIN se presente
            if data['isin']:
                data['isin'] = DataValidator.validate_isin(data['isin'])
            
            return data
            
        except Exception as e:
            error_msg = ErrorHandler.handle_data_error(e, "validazione dati")
            messagebox.showerror("Errore", error_msg)
            return None
    
    def _update_title(self):
        """Aggiorna il titolo del form"""
        safe_execute(lambda: self.title_label.configure(text=self.state.get_title()))
    
    def _update_button_states(self):
        """Aggiorna lo stato dei bottoni in base alla modalità corrente"""
        has_asset = self.state.is_editing()
        is_historical = self.state.historical_mode
        
        # Bottoni che richiedono un asset selezionato
        buttons_requiring_asset = [
            (self.delete_btn, UIConfig.COLORS['danger']),
            (self.copy_btn, UIConfig.COLORS['info']),
            (self.new_record_btn, UIConfig.COLORS['purple'])
        ]
        
        for button, color in buttons_requiring_asset:
            if has_asset:
                safe_execute(lambda: button.configure(state="normal", fg_color=color))
            else:
                safe_execute(lambda: button.configure(state="disabled", fg_color=UIConfig.COLORS['secondary']))
        
        # Bottone salva - cambia testo e colore in base alla modalità
        if is_historical:
            safe_execute(lambda: self.save_btn.configure(
                text="💾 Salva Valore",
                fg_color=UIConfig.COLORS['purple']
            ))
        elif self.state.mode == 'edit':
            safe_execute(lambda: self.save_btn.configure(
                text="💾 Aggiorna Asset",
                fg_color=UIConfig.COLORS['warning']
            ))
        else:
            safe_execute(lambda: self.save_btn.configure(
                text="💾 Salva Asset",
                fg_color=UIConfig.COLORS['primary']
            ))
    
    def populate_form(self, asset: Asset):
        """Popola il form con i dati di un asset"""
        def clean_value(value):
            if DataValidator.is_empty(value):
                return ""
            return str(value).strip()
        
        # Popola tutti i campi senza formattazione valuta
        field_mapping = {
            'category': asset.category,
            'asset_name': asset.asset_name,
            'position': asset.position,
            'risk_level': asset.risk_level,
            'ticker': asset.ticker,
            'isin': asset.isin,
            'created_at': asset.created_at,
            'created_amount': asset.created_amount,
            'created_unit_price': asset.created_unit_price,
            'created_total_value': asset.created_total_value,
            'updated_at': asset.updated_at,
            'updated_amount': asset.updated_amount,
            'updated_unit_price': asset.updated_unit_price,
            'updated_total_value': asset.updated_total_value,
            'accumulation_plan': asset.accumulation_plan,
            'accumulation_amount': asset.accumulation_amount,
            'income_per_year': asset.income_per_year,
            'rental_income': asset.rental_income,
            'note': asset.note
        }
        
        for field, value in field_mapping.items():
            if field in self.form_vars:
                safe_execute(lambda f=field, v=value: self.form_vars[f].set(clean_value(v)))
        
        # Abilita tutti i campi per visualizzazione completa
        self._initialize_form()
    
    def edit_asset(self, asset_id: int):
        """Imposta il form in modalità modifica per un asset specifico"""
        asset = self.portfolio_manager.get_asset(asset_id)
        if asset:
            self.state.set_edit_mode(asset_id)
            self.populate_form(asset)
            self._update_title()
            self._update_button_states()
            return True
        return False
    
    def clear_edit_mode(self):
        """Esce dalla modalità modifica"""
        self.state.set_create_mode()
        self._update_title()
        self._update_button_states()