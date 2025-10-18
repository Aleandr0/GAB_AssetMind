#!/usr/bin/env python3
"""
Componente interfaccia Analisi Rendimenti per GAB AssetMind
Calcola e visualizza i rendimenti aggregati pesati per valore di:
- Portfolio complessivo
- Categorie
- Posizioni
- Selezione attiva (se presente)
"""

import customtkinter as ctk
import pandas as pd
from typing import Optional, Dict, Any
import numpy as np

from config import UIConfig, FieldMapping
from utils import ErrorHandler, safe_execute
from models import PortfolioManager
from ui_components import BaseUIComponent
from logging_config import get_logger


class AnalisiRendimentiUI(BaseUIComponent):
    """Componente per l'analisi dei rendimenti aggregati"""

    def __init__(self, parent, portfolio_manager: PortfolioManager):
        super().__init__(parent, portfolio_manager)
        self.rendimenti_frame = None
        self.logger = get_logger('AnalisiRendimentiUI')
        self._external_filtered_df = None
        self._filter_info = None

        # Container per le card dei rendimenti
        self.portfolio_card_labels = {}
        self.categorie_cards = []
        self.posizioni_cards = []
        self.selezione_card_labels = {}

    def create_analisi_interface(self) -> ctk.CTkFrame:
        """Crea l'interfaccia completa per l'analisi rendimenti"""
        self.rendimenti_frame = ctk.CTkFrame(self.parent)
        self.rendimenti_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self._create_header()
        self._create_content_area()

        return self.rendimenti_frame

    def _create_header(self):
        """Crea l'header della pagina"""
        header_frame = ctk.CTkFrame(self.rendimenti_frame, height=60)
        header_frame.pack(fill="x", padx=10, pady=10)
        header_frame.pack_propagate(False)

        # Titolo centrato
        title_label = ctk.CTkLabel(
            header_frame,
            text="📈 Analisi Rendimenti",
            font=ctk.CTkFont(**UIConfig.FONTS['title'])
        )
        title_label.pack(pady=(10, 5))

        # Sottotitolo
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Rendimenti aggregati pesati per valore corrente",
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            text_color=UIConfig.COLORS['secondary']
        )
        subtitle_label.pack(pady=(0, 10))

    def _create_content_area(self):
        """Crea l'area principale con le card dei rendimenti"""
        # Scrollable frame per contenere tutte le sezioni
        self.scrollable = ctk.CTkScrollableFrame(self.rendimenti_frame)
        self.scrollable.pack(fill="both", expand=True, padx=10, pady=10)

        # Uso grid per avere controllo preciso sull'ordine
        self.scrollable.grid_columnconfigure(0, weight=1)

        # ROW 0: Sezione Portfolio Complessivo
        self._create_portfolio_section(self.scrollable)

        # ROW 1: Sezione Selezione Attiva (SUBITO DOPO Portfolio Complessivo)
        self.selezione_section = ctk.CTkFrame(self.scrollable, corner_radius=15)
        self._create_selezione_section(self.selezione_section)
        # Grid alla row 1, nascosta inizialmente
        self.selezione_section.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.selezione_section.grid_remove()  # Nascosta inizialmente

        # ROW 2: Sezione Categorie
        self._create_categorie_section(self.scrollable)

        # ROW 3: Sezione Posizioni
        self._create_posizioni_section(self.scrollable)

    def _create_portfolio_section(self, parent):
        """Crea la sezione rendimento portfolio complessivo"""
        section_frame = ctk.CTkFrame(parent, corner_radius=15)
        section_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # Titolo sezione
        title_label = ctk.CTkLabel(
            section_frame,
            text="💼 Portfolio Complessivo",
            font=ctk.CTkFont(**UIConfig.FONTS['subheader']),
            text_color=UIConfig.COLORS['primary']
        )
        title_label.pack(pady=(15, 10), padx=20, anchor="w")

        # Card rendimento
        card_frame = ctk.CTkFrame(section_frame, corner_radius=10, fg_color="#f0f9ff")
        card_frame.pack(fill="x", padx=20, pady=(0, 15))

        # Grid layout
        card_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Valore iniziale
        ctk.CTkLabel(
            card_frame,
            text="Valore Iniziale",
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            text_color=UIConfig.COLORS['secondary']
        ).grid(row=0, column=0, padx=15, pady=(10, 0), sticky="w")

        self.portfolio_card_labels['valore_iniziale'] = ctk.CTkLabel(
            card_frame,
            text="€ 0,00",
            font=ctk.CTkFont(size=18, weight='bold'),
            text_color="#0f172a"
        )
        self.portfolio_card_labels['valore_iniziale'].grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        # Valore corrente
        ctk.CTkLabel(
            card_frame,
            text="Valore Corrente",
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            text_color=UIConfig.COLORS['secondary']
        ).grid(row=0, column=1, padx=15, pady=(10, 0), sticky="w")

        self.portfolio_card_labels['valore_corrente'] = ctk.CTkLabel(
            card_frame,
            text="€ 0,00",
            font=ctk.CTkFont(size=18, weight='bold'),
            text_color="#0f172a"
        )
        self.portfolio_card_labels['valore_corrente'].grid(row=1, column=1, padx=15, pady=(0, 10), sticky="w")

        # Guadagno assoluto
        ctk.CTkLabel(
            card_frame,
            text="Guadagno/Perdita",
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            text_color=UIConfig.COLORS['secondary']
        ).grid(row=0, column=2, padx=15, pady=(10, 0), sticky="w")

        self.portfolio_card_labels['guadagno'] = ctk.CTkLabel(
            card_frame,
            text="€ 0,00",
            font=ctk.CTkFont(size=18, weight='bold'),
            text_color=UIConfig.COLORS['success']
        )
        self.portfolio_card_labels['guadagno'].grid(row=1, column=2, padx=15, pady=(0, 10), sticky="w")

        # Rendimento percentuale
        ctk.CTkLabel(
            card_frame,
            text="Rendimento %",
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            text_color=UIConfig.COLORS['secondary']
        ).grid(row=0, column=3, padx=15, pady=(10, 0), sticky="w")

        self.portfolio_card_labels['rendimento'] = ctk.CTkLabel(
            card_frame,
            text="0.00%",
            font=ctk.CTkFont(size=24, weight='bold'),
            text_color=UIConfig.COLORS['success']
        )
        self.portfolio_card_labels['rendimento'].grid(row=1, column=3, padx=15, pady=(0, 10), sticky="w")

    def _create_selezione_section(self, parent):
        """Crea la sezione rendimento selezione attiva"""
        # Titolo sezione
        title_label = ctk.CTkLabel(
            parent,
            text="🎯 Selezione Attiva",
            font=ctk.CTkFont(**UIConfig.FONTS['subheader']),
            text_color=UIConfig.COLORS['info']
        )
        title_label.pack(pady=(15, 10), padx=20, anchor="w")

        # Descrizione selezione (font aumentato del 50%)
        base_size = UIConfig.FONTS['text'].get('size', 12)
        increased_size = int(base_size * 1.5)

        self.selezione_card_labels['descrizione'] = ctk.CTkLabel(
            parent,
            text="",
            font=ctk.CTkFont(family=UIConfig.FONTS['text'].get('family', 'Arial'), size=increased_size),
            text_color=UIConfig.COLORS['secondary'],
            justify="left",
            wraplength=1100  # Larghezza ampia per evitare troppi a capo
        )
        self.selezione_card_labels['descrizione'].pack(padx=20, pady=(0, 10), anchor="w", fill="x")

        # Card rendimento
        card_frame = ctk.CTkFrame(parent, corner_radius=10, fg_color="#fef3c7")
        card_frame.pack(fill="x", padx=20, pady=(0, 15))

        # Grid layout
        card_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Valore iniziale
        ctk.CTkLabel(
            card_frame,
            text="Valore Iniziale",
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            text_color=UIConfig.COLORS['secondary']
        ).grid(row=0, column=0, padx=15, pady=(10, 0), sticky="w")

        self.selezione_card_labels['valore_iniziale'] = ctk.CTkLabel(
            card_frame,
            text="€ 0,00",
            font=ctk.CTkFont(size=18, weight='bold'),
            text_color="#0f172a"
        )
        self.selezione_card_labels['valore_iniziale'].grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        # Valore corrente
        ctk.CTkLabel(
            card_frame,
            text="Valore Corrente",
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            text_color=UIConfig.COLORS['secondary']
        ).grid(row=0, column=1, padx=15, pady=(10, 0), sticky="w")

        self.selezione_card_labels['valore_corrente'] = ctk.CTkLabel(
            card_frame,
            text="€ 0,00",
            font=ctk.CTkFont(size=18, weight='bold'),
            text_color="#0f172a"
        )
        self.selezione_card_labels['valore_corrente'].grid(row=1, column=1, padx=15, pady=(0, 10), sticky="w")

        # Guadagno assoluto
        ctk.CTkLabel(
            card_frame,
            text="Guadagno/Perdita",
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            text_color=UIConfig.COLORS['secondary']
        ).grid(row=0, column=2, padx=15, pady=(10, 0), sticky="w")

        self.selezione_card_labels['guadagno'] = ctk.CTkLabel(
            card_frame,
            text="€ 0,00",
            font=ctk.CTkFont(size=18, weight='bold'),
            text_color=UIConfig.COLORS['success']
        )
        self.selezione_card_labels['guadagno'].grid(row=1, column=2, padx=15, pady=(0, 10), sticky="w")

        # Rendimento percentuale
        ctk.CTkLabel(
            card_frame,
            text="Rendimento %",
            font=ctk.CTkFont(**UIConfig.FONTS['text']),
            text_color=UIConfig.COLORS['secondary']
        ).grid(row=0, column=3, padx=15, pady=(10, 0), sticky="w")

        self.selezione_card_labels['rendimento'] = ctk.CTkLabel(
            card_frame,
            text="0.00%",
            font=ctk.CTkFont(size=24, weight='bold'),
            text_color=UIConfig.COLORS['success']
        )
        self.selezione_card_labels['rendimento'].grid(row=1, column=3, padx=15, pady=(0, 10), sticky="w")

    def _create_categorie_section(self, parent):
        """Crea la sezione rendimenti per categoria"""
        section_frame = ctk.CTkFrame(parent, corner_radius=15)
        section_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        # Titolo sezione
        title_label = ctk.CTkLabel(
            section_frame,
            text="📊 Rendimenti per Categoria",
            font=ctk.CTkFont(**UIConfig.FONTS['subheader']),
            text_color=UIConfig.COLORS['primary']
        )
        title_label.pack(pady=(15, 10), padx=20, anchor="w")

        # Container per le card (sarà popolato dinamicamente)
        self.categorie_container = ctk.CTkFrame(section_frame, fg_color="transparent")
        self.categorie_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _create_posizioni_section(self, parent):
        """Crea la sezione rendimenti per posizione"""
        section_frame = ctk.CTkFrame(parent, corner_radius=15)
        section_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)

        # Titolo sezione
        title_label = ctk.CTkLabel(
            section_frame,
            text="🏷️ Rendimenti per Posizione",
            font=ctk.CTkFont(**UIConfig.FONTS['subheader']),
            text_color=UIConfig.COLORS['primary']
        )
        title_label.pack(pady=(15, 10), padx=20, anchor="w")

        # Container per le card (sarà popolato dinamicamente)
        self.posizioni_container = ctk.CTkFrame(section_frame, fg_color="transparent")
        self.posizioni_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _calcola_rendimento_aggregato(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcola rendimento aggregato di una selezione di asset
        ponderando i rendimenti individuali per il valore corrente

        Returns:
            Dict con valore_iniziale, valore_corrente, guadagno, rendimento_pct
        """
        if df.empty:
            return {
                'valore_iniziale': 0.0,
                'valore_corrente': 0.0,
                'guadagno': 0.0,
                'rendimento_pct': 0.0
            }

        # Calcola valori
        valore_iniziale = df['created_total_value'].fillna(0).sum()
        valore_corrente = df['updated_total_value'].fillna(df['created_total_value']).fillna(0).sum()
        guadagno = valore_corrente - valore_iniziale

        # Calcola rendimento percentuale ponderato
        if valore_corrente > 0:
            # Media ponderata dei rendimenti per valore corrente
            rendimento_pct = 0.0
            for _, asset in df.iterrows():
                peso = asset['updated_total_value'] if pd.notna(asset['updated_total_value']) else asset['created_total_value']
                peso = peso if pd.notna(peso) else 0
                peso = peso / valore_corrente if valore_corrente > 0 else 0

                # Rendimento asset (dalla colonna già calcolata)
                rend_asset = asset.get('return_percentage', 0)
                rend_asset = rend_asset if pd.notna(rend_asset) else 0

                rendimento_pct += peso * rend_asset
        else:
            rendimento_pct = 0.0

        return {
            'valore_iniziale': valore_iniziale,
            'valore_corrente': valore_corrente,
            'guadagno': guadagno,
            'rendimento_pct': rendimento_pct
        }

    def _format_currency(self, value: float) -> str:
        """Formatta un valore come valuta"""
        return f"€ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    def _format_percentage(self, value: float) -> str:
        """Formatta un valore come percentuale"""
        return f"{value:.2f}%"

    def _update_portfolio_rendimento(self, df: pd.DataFrame):
        """Aggiorna la card del portfolio complessivo"""
        risultato = self._calcola_rendimento_aggregato(df)

        # Aggiorna labels
        self.portfolio_card_labels['valore_iniziale'].configure(
            text=self._format_currency(risultato['valore_iniziale'])
        )
        self.portfolio_card_labels['valore_corrente'].configure(
            text=self._format_currency(risultato['valore_corrente'])
        )

        # Colore guadagno/perdita
        guadagno_color = UIConfig.COLORS['success'] if risultato['guadagno'] >= 0 else UIConfig.COLORS['danger']
        self.portfolio_card_labels['guadagno'].configure(
            text=self._format_currency(risultato['guadagno']),
            text_color=guadagno_color
        )

        # Colore rendimento
        rend_color = UIConfig.COLORS['success'] if risultato['rendimento_pct'] >= 0 else UIConfig.COLORS['danger']
        self.portfolio_card_labels['rendimento'].configure(
            text=self._format_percentage(risultato['rendimento_pct']),
            text_color=rend_color
        )

    def _update_selezione_rendimento(self, df: pd.DataFrame, filter_info: Optional[Dict[str, Any]]):
        """Aggiorna la sezione selezione attiva"""
        # Verifica se ci sono filtri attivi
        has_filters = False
        if filter_info and filter_info.get('column_filters'):
            col_filters = filter_info['column_filters']
            has_filters = any(bool(values) for values in col_filters.values())

        if not has_filters:
            # Nascondi la sezione se non ci sono filtri (mantiene la posizione nel grid)
            self.selezione_section.grid_remove()
            return

        # Mostra la sezione (è già alla row 1, subito dopo Portfolio)
        self.selezione_section.grid()

        # Formatta descrizione filtri
        descrizione = self._format_filter_description(filter_info)
        self.selezione_card_labels['descrizione'].configure(text=descrizione)

        # Calcola rendimento
        risultato = self._calcola_rendimento_aggregato(df)

        # Aggiorna labels
        self.selezione_card_labels['valore_iniziale'].configure(
            text=self._format_currency(risultato['valore_iniziale'])
        )
        self.selezione_card_labels['valore_corrente'].configure(
            text=self._format_currency(risultato['valore_corrente'])
        )

        # Colore guadagno/perdita
        guadagno_color = UIConfig.COLORS['success'] if risultato['guadagno'] >= 0 else UIConfig.COLORS['danger']
        self.selezione_card_labels['guadagno'].configure(
            text=self._format_currency(risultato['guadagno']),
            text_color=guadagno_color
        )

        # Colore rendimento
        rend_color = UIConfig.COLORS['success'] if risultato['rendimento_pct'] >= 0 else UIConfig.COLORS['danger']
        self.selezione_card_labels['rendimento'].configure(
            text=self._format_percentage(risultato['rendimento_pct']),
            text_color=rend_color
        )

    def _format_filter_description(self, filter_info: Dict[str, Any]) -> str:
        """Formatta la descrizione dei filtri attivi"""
        if not filter_info or not filter_info.get('column_filters'):
            return ""

        col_filters = filter_info['column_filters']
        parts = []

        for col, values in col_filters.items():
            disp = FieldMapping.DB_TO_DISPLAY.get(col, col)
            vals = list(sorted({str(v) for v in values}))
            shown = ', '.join(vals)
            parts.append(f"{disp}: {shown}")

        return "Filtri attivi: " + " | ".join(parts)

    def _update_categorie_rendimenti(self, df: pd.DataFrame):
        """Aggiorna le card dei rendimenti per categoria"""
        # Pulisci container
        for widget in self.categorie_container.winfo_children():
            widget.destroy()
        self.categorie_cards.clear()

        if df.empty or 'category' not in df.columns:
            no_data_label = ctk.CTkLabel(
                self.categorie_container,
                text="Nessuna categoria disponibile",
                font=ctk.CTkFont(**UIConfig.FONTS['text']),
                text_color=UIConfig.COLORS['secondary']
            )
            no_data_label.pack(pady=20)
            return

        # Raggruppa per categoria e calcola rendimenti
        categorie = df['category'].dropna().unique()
        rendimenti_categorie = []

        for categoria in categorie:
            df_cat = df[df['category'] == categoria]
            risultato = self._calcola_rendimento_aggregato(df_cat)
            risultato['nome'] = categoria
            rendimenti_categorie.append(risultato)

        # Ordina per rendimento percentuale decrescente
        rendimenti_categorie.sort(key=lambda x: x['rendimento_pct'], reverse=True)

        # Crea card per ogni categoria
        for risultato in rendimenti_categorie:
            self._create_categoria_card(self.categorie_container, risultato)

    def _create_categoria_card(self, parent, risultato: Dict[str, Any]):
        """Crea una card per una categoria"""
        card_frame = ctk.CTkFrame(parent, corner_radius=10, fg_color="#f8fafc")
        card_frame.pack(fill="x", pady=5)

        # Grid layout
        card_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Nome categoria
        nome_label = ctk.CTkLabel(
            card_frame,
            text=risultato['nome'],
            font=ctk.CTkFont(size=14, weight='bold'),
            text_color="#0f172a"
        )
        nome_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        # Valore corrente
        valore_label = ctk.CTkLabel(
            card_frame,
            text=self._format_currency(risultato['valore_corrente']),
            font=ctk.CTkFont(size=14),
            text_color="#0f172a"
        )
        valore_label.grid(row=0, column=1, padx=15, pady=10, sticky="w")

        # Guadagno
        guadagno_color = UIConfig.COLORS['success'] if risultato['guadagno'] >= 0 else UIConfig.COLORS['danger']
        guadagno_label = ctk.CTkLabel(
            card_frame,
            text=self._format_currency(risultato['guadagno']),
            font=ctk.CTkFont(size=14),
            text_color=guadagno_color
        )
        guadagno_label.grid(row=0, column=2, padx=15, pady=10, sticky="w")

        # Rendimento
        rend_color = UIConfig.COLORS['success'] if risultato['rendimento_pct'] >= 0 else UIConfig.COLORS['danger']
        rend_label = ctk.CTkLabel(
            card_frame,
            text=self._format_percentage(risultato['rendimento_pct']),
            font=ctk.CTkFont(size=16, weight='bold'),
            text_color=rend_color
        )
        rend_label.grid(row=0, column=3, padx=15, pady=10, sticky="e")

        self.categorie_cards.append(card_frame)

    def _update_posizioni_rendimenti(self, df: pd.DataFrame):
        """Aggiorna le card dei rendimenti per posizione"""
        # Pulisci container
        for widget in self.posizioni_container.winfo_children():
            widget.destroy()
        self.posizioni_cards.clear()

        if df.empty or 'position' not in df.columns:
            no_data_label = ctk.CTkLabel(
                self.posizioni_container,
                text="Nessuna posizione disponibile",
                font=ctk.CTkFont(**UIConfig.FONTS['text']),
                text_color=UIConfig.COLORS['secondary']
            )
            no_data_label.pack(pady=20)
            return

        # Raggruppa per posizione e calcola rendimenti
        df_work = df.copy()
        df_work['position'] = df_work['position'].fillna('Non specificata')
        posizioni = df_work['position'].unique()
        rendimenti_posizioni = []

        for posizione in posizioni:
            df_pos = df_work[df_work['position'] == posizione]
            risultato = self._calcola_rendimento_aggregato(df_pos)
            risultato['nome'] = posizione
            rendimenti_posizioni.append(risultato)

        # Ordina per rendimento percentuale decrescente
        rendimenti_posizioni.sort(key=lambda x: x['rendimento_pct'], reverse=True)

        # Crea card per ogni posizione
        for risultato in rendimenti_posizioni:
            self._create_posizione_card(self.posizioni_container, risultato)

    def _create_posizione_card(self, parent, risultato: Dict[str, Any]):
        """Crea una card per una posizione"""
        card_frame = ctk.CTkFrame(parent, corner_radius=10, fg_color="#fef9f5")
        card_frame.pack(fill="x", pady=5)

        # Grid layout
        card_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Nome posizione (troncato se troppo lungo)
        nome = risultato['nome']
        if len(nome) > 40:
            nome = nome[:37] + "..."

        nome_label = ctk.CTkLabel(
            card_frame,
            text=nome,
            font=ctk.CTkFont(size=14, weight='bold'),
            text_color="#0f172a"
        )
        nome_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        # Valore corrente
        valore_label = ctk.CTkLabel(
            card_frame,
            text=self._format_currency(risultato['valore_corrente']),
            font=ctk.CTkFont(size=14),
            text_color="#0f172a"
        )
        valore_label.grid(row=0, column=1, padx=15, pady=10, sticky="w")

        # Guadagno
        guadagno_color = UIConfig.COLORS['success'] if risultato['guadagno'] >= 0 else UIConfig.COLORS['danger']
        guadagno_label = ctk.CTkLabel(
            card_frame,
            text=self._format_currency(risultato['guadagno']),
            font=ctk.CTkFont(size=14),
            text_color=guadagno_color
        )
        guadagno_label.grid(row=0, column=2, padx=15, pady=10, sticky="w")

        # Rendimento
        rend_color = UIConfig.COLORS['success'] if risultato['rendimento_pct'] >= 0 else UIConfig.COLORS['danger']
        rend_label = ctk.CTkLabel(
            card_frame,
            text=self._format_percentage(risultato['rendimento_pct']),
            font=ctk.CTkFont(size=16, weight='bold'),
            text_color=rend_color
        )
        rend_label.grid(row=0, column=3, padx=15, pady=10, sticky="e")

        self.posizioni_cards.append(card_frame)

    def refresh_analisi(self):
        """Aggiorna tutti i dati dell'analisi"""
        try:
            # SEMPRE carica il portfolio complessivo (TUTTI gli asset)
            df_completo = self.portfolio_manager.get_current_assets_only()

            if df_completo.empty:
                self.logger.warning("Nessun dato disponibile per analisi rendimenti")
                return

            # Portfolio Complessivo: SEMPRE tutti gli asset
            self._update_portfolio_rendimento(df_completo)

            # Selezione Attiva: solo se ci sono filtri
            if isinstance(self._external_filtered_df, pd.DataFrame) and not self._external_filtered_df.empty:
                df_filtrato = self._external_filtered_df.copy()
                self._update_selezione_rendimento(df_filtrato, self._filter_info)
                # Per categorie e posizioni usa la selezione filtrata
                self._update_categorie_rendimenti(df_filtrato)
                self._update_posizioni_rendimenti(df_filtrato)
            else:
                # Nessuna selezione: nascondi sezione selezione
                self._update_selezione_rendimento(df_completo, None)
                # Per categorie e posizioni usa tutti gli asset
                self._update_categorie_rendimenti(df_completo)
                self._update_posizioni_rendimenti(df_completo)

            self.logger.debug(f"Analisi rendimenti aggiornata - Portfolio: {len(df_completo)} asset")

        except Exception as e:
            self.logger.error(f"Errore aggiornamento analisi rendimenti: {e}")
            import traceback
            self.logger.debug(f"Stack trace: {traceback.format_exc()}")

    def refresh_with_filtered_data(self, df: pd.DataFrame, filter_info: Optional[Dict[str, Any]] = None):
        """Aggiorna l'analisi usando un DataFrame filtrato"""
        try:
            self._external_filtered_df = df.copy() if isinstance(df, pd.DataFrame) else None
            if isinstance(filter_info, dict):
                self._filter_info = filter_info
        except Exception:
            self._external_filtered_df = None
        finally:
            safe_execute(self.refresh_analisi)
