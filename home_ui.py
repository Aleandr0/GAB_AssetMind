#!/usr/bin/env python3
"""RoadMap Dashboard UI for GAB AssetMind."""

from __future__ import annotations

import customtkinter as ctk
import pandas as pd
from typing import Any, Callable, Dict, List, Optional

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils import CurrencyFormatter, DateFormatter


class RoadMapDashboard:
    """Struttura compatta che funge da cruscotto di lancio."""

    def __init__(
        self,
        container: ctk.CTkFrame,
        portfolio_manager,
        charts_ui_instance=None,
        on_navigate: Optional[Callable[[str, Optional[str]], None]] = None,
    ) -> None:
        self.container = container
        self.portfolio_manager = portfolio_manager
        self.charts_ui = charts_ui_instance
        self.on_navigate = on_navigate

        self.summary_labels: Dict[str, ctk.CTkLabel] = {}
        self.chart_objects: Dict[str, Dict[str, Any]] = {}
        self.returns_rows: List[Dict[str, ctk.CTkLabel]] = []

        self._build_layout()

    # ------------------------------------------------------------------
    # Costruzione interfaccia
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        self.container.configure(fg_color="transparent")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=0)
        self.container.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_panels_grid()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self.container, corner_radius=18, fg_color="#e9efff")
        header.grid(row=0, column=0, sticky="nsew", pady=(6, 8))
        header.grid_columnconfigure(0, weight=3)
        header.grid_columnconfigure((1, 2, 3), weight=1)

        # Container per titolo e filtri sulla stessa riga
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=16, pady=8)

        title = ctk.CTkLabel(
            title_frame,
            text="RoadMap AssetMind",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#0f172a",
        )
        title.pack(side="left")

        # Label per mostrare selezione attiva o "Patrimonio Complessivo"
        self.filter_label = ctk.CTkLabel(
            title_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#64748b",
        )
        self.filter_label.pack(side="left", padx=(12, 0))

        metrics = [
            ("total", "Valore complessivo"),
            ("assets", "Asset correnti"),
            ("updated", "Ultimo aggiornamento"),
        ]

        for col, (key, label_text) in enumerate(metrics, start=1):
            wrapper = ctk.CTkFrame(header, corner_radius=12, fg_color="#ffffff")
            wrapper.grid(row=0, column=col, rowspan=1, sticky="nsew", padx=(8 if col > 1 else 12), pady=8)
            wrapper.grid_columnconfigure(0, weight=1)

            label = ctk.CTkLabel(
                wrapper,
                text=label_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#475569",
            )
            label.grid(row=0, column=0, sticky="w", padx=12, pady=(6, 0))

            value_label = ctk.CTkLabel(
                wrapper,
                text="-",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#1d4ed8",
            )
            value_label.grid(row=1, column=0, sticky="w", padx=12, pady=(2, 6))
            self._make_clickable(wrapper, "Portfolio", None)
            self._make_clickable(label, "Portfolio", None)
            self._make_clickable(value_label, "Portfolio", None)
            self.summary_labels[key] = value_label

    def _build_panels_grid(self) -> None:
        grid = ctk.CTkFrame(self.container, fg_color="transparent")
        grid.grid(row=1, column=0, sticky="nsew")
        grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="roadmap_col")
        grid.grid_rowconfigure((0, 1), weight=1, uniform="roadmap_row")

        panel_specs = [
            ("timeline", "Evoluzione temporale", "chart", "Evoluzione Temporale"),
            ("category", "Valore per categoria", "chart", "Distribuzione Valore per Categoria"),
            ("position", "Asset per posizione", "chart", "Suddivisione Asset per Posizione"),
            ("performance", "Performance per categoria", "chart", "Performance per Categoria"),
            ("risk", "Distribuzione rischio", "chart", "Distribuzione Rischio"),
            ("returns", "Analisi Rendimenti", "analisi_rendimenti", "Analisi Rendimenti"),
        ]

        for index, (key, title, panel_type, chart_name) in enumerate(panel_specs):
            target_page = "Grafici" if panel_type in ["chart", "analisi_rendimenti"] else "Portfolio"
            row, col = divmod(index, 3)
            frame = ctk.CTkFrame(grid, corner_radius=16, fg_color="#ffffff")
            frame.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)  # Modificato: riga 0 invece di 1

            # Titolo rimosso per dare più spazio ai grafici
            # (i titoli sono già presenti nei grafici stessi)

            if panel_type == "chart":
                fig = Figure(figsize=(4.0, 2.5), dpi=100)
                ax = fig.add_subplot(111)
                ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.35)
                canvas = FigureCanvasTkAgg(fig, master=frame)
                widget = canvas.get_tk_widget()
                widget.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)  # Modificato: row=0 e padding simmetrico
                self.chart_objects[key] = {"figure": fig, "axis": ax, "canvas": canvas}
                self._make_clickable(frame, target_page, chart_name)
                self._make_clickable(widget, target_page, chart_name)
            elif panel_type == "analisi_rendimenti":
                # Card speciale per Analisi Rendimenti
                self._build_analisi_rendimenti_card(frame, target_page, chart_name)
            else:
                self._build_returns_table(frame)

    def _build_analisi_rendimenti_card(self, frame: ctk.CTkFrame, target_page: str, chart_name: str) -> None:
        """Crea una card compatta per Analisi Rendimenti nella RoadMap"""
        container = ctk.CTkFrame(frame, fg_color="#fef3c7")
        container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        container.grid_columnconfigure(0, weight=1)

        # Rendi tutta la card cliccabile
        self._make_clickable(frame, target_page, chart_name)
        self._make_clickable(container, target_page, chart_name)

        # Titolo più compatto
        title = ctk.CTkLabel(
            container,
            text="📈 Analisi Rendimenti",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#0f172a"
        )
        title.pack(padx=12, pady=(8, 2), anchor="w")
        self._make_clickable(title, target_page, chart_name)

        # Frame Portfolio Complessivo (più compatto)
        portfolio_frame = ctk.CTkFrame(container, fg_color="#e0f2fe", corner_radius=4)
        portfolio_frame.pack(fill="x", padx=12, pady=(0, 3))
        self._make_clickable(portfolio_frame, target_page, chart_name)

        portfolio_title = ctk.CTkLabel(
            portfolio_frame,
            text="💼 Portfolio",
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color="#0369a1"
        )
        portfolio_title.pack(padx=6, pady=(3, 0), anchor="w")
        self._make_clickable(portfolio_title, target_page, chart_name)

        self.rendimento_portfolio_label = ctk.CTkLabel(
            portfolio_frame,
            text="0.00%",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#16a34a"
        )
        self.rendimento_portfolio_label.pack(padx=6, pady=(0, 3), anchor="w")
        self._make_clickable(self.rendimento_portfolio_label, target_page, chart_name)

        # Frame Selezione (inizialmente nascosto, più compatto)
        self.selezione_frame_roadmap = ctk.CTkFrame(container, fg_color="#fef9c3", corner_radius=4)
        # Pack will be called dynamically when there's a selection
        self._make_clickable(self.selezione_frame_roadmap, target_page, chart_name)

        selezione_title = ctk.CTkLabel(
            self.selezione_frame_roadmap,
            text="🎯 Selezione",
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color="#a16207"
        )
        selezione_title.pack(padx=6, pady=(3, 0), anchor="w")
        self._make_clickable(selezione_title, target_page, chart_name)

        # Label descrizione selezione (più piccola)
        self.selezione_desc_label = ctk.CTkLabel(
            self.selezione_frame_roadmap,
            text="",
            font=ctk.CTkFont(size=7),
            text_color="#78716c",
            justify="left",
            wraplength=280
        )
        self.selezione_desc_label.pack(padx=6, pady=(0, 1), anchor="w", fill="x")
        self._make_clickable(self.selezione_desc_label, target_page, chart_name)

        self.rendimento_selezione_label = ctk.CTkLabel(
            self.selezione_frame_roadmap,
            text="0.00%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#16a34a"
        )
        self.rendimento_selezione_label.pack(padx=6, pady=(0, 3), anchor="w")
        self._make_clickable(self.rendimento_selezione_label, target_page, chart_name)

        # Call to action più piccolo
        cta = ctk.CTkLabel(
            container,
            text="→ Clicca per dettagli",
            font=ctk.CTkFont(size=8),
            text_color="#1d4ed8"
        )
        cta.pack(padx=12, pady=(4, 8), anchor="w")
        self._make_clickable(cta, target_page, chart_name)

    def _build_returns_table(self, frame: ctk.CTkFrame) -> None:
        table = ctk.CTkFrame(frame, fg_color="#f8fafc")
        table.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)  # Modificato: row=0 e padding simmetrico
        table.grid_columnconfigure((0, 1, 2), weight=1)
        self._make_clickable(frame, "Portfolio")
        self._make_clickable(table, "Portfolio")

        headers = ["Asset", "Gain EUR", "Gain %"]
        for col, header_text in enumerate(headers):
            lbl = ctk.CTkLabel(
                table,
                text=header_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#475569",
            )
            lbl.grid(row=0, column=col, sticky="w", padx=(16 if col == 0 else 8), pady=(8, 4))

        for row_idx in range(1, 6):
            asset_label = ctk.CTkLabel(
                table,
                text="-",
                font=ctk.CTkFont(size=12),
                text_color="#0f172a",
                anchor="w",
            )
            asset_label.grid(row=row_idx, column=0, sticky="w", padx=16, pady=2)

            gain_label = ctk.CTkLabel(
                table,
                text="-",
                font=ctk.CTkFont(size=12),
                text_color="#1d4ed8",
            )
            gain_label.grid(row=row_idx, column=1, sticky="w", padx=8, pady=2)

            pct_label = ctk.CTkLabel(
                table,
                text="-",
                font=ctk.CTkFont(size=12),
                text_color="#1d4ed8",
            )
            pct_label.grid(row=row_idx, column=2, sticky="w", padx=8, pady=2)

            self.returns_rows.append({"asset": asset_label, "gain": gain_label, "pct": pct_label})

    # ------------------------------------------------------------------
    # Aggiornamento dati
    # ------------------------------------------------------------------
    def refresh(
        self,
        summary: Optional[Dict[str, Any]] = None,
        dataframe: Optional[pd.DataFrame] = None,
        filter_state: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self.portfolio_manager:
            return

        if summary is None:
            try:
                summary = self.portfolio_manager.get_portfolio_summary()
            except Exception:
                summary = {}

        if dataframe is None:
            try:
                dataframe = self.portfolio_manager.get_current_assets_only()
            except Exception:
                dataframe = None

        self._update_header(summary, dataframe, filter_state)
        self._render_timeline(dataframe)
        self._render_value_distribution(dataframe)
        self._render_risk_distribution(dataframe)
        self._render_performance(dataframe)
        self._render_position_distribution(dataframe)
        self._update_analisi_rendimenti_preview(dataframe, filter_state)
        self._update_returns_preview(dataframe)

    def set_portfolio_manager(self, portfolio_manager) -> None:
        self.portfolio_manager = portfolio_manager

    def _make_clickable(self, widget: Any, target_page: str, chart_name: Optional[str] = None) -> None:
        if not self.on_navigate or widget is None:
            return

        def _callback(_event):
            self.on_navigate(target_page, chart_name)

        try:
            widget.bind("<Button-1>", _callback)
            widget.configure(cursor="hand2")
        except Exception:
            return

    # ------------------------------------------------------------------
    # Helper UI
    # ------------------------------------------------------------------
    def _update_header(
        self,
        summary: Dict[str, Any],
        dataframe: Optional[pd.DataFrame],
        filter_state: Optional[Dict[str, Any]] = None,
    ) -> None:
        total_value = summary.get("total_value", 0)
        total_label = self.summary_labels.get("total")
        if total_label:
            total_label.configure(text=CurrencyFormatter.format_for_display(total_value))

        asset_count = 0
        if dataframe is not None and not dataframe.empty:
            # Conta asset unici, non le righe - usa get_current_assets_only per deduplica
            asset_count = len(self.portfolio_manager.get_current_assets_only())
        assets_label = self.summary_labels.get("assets")
        if assets_label:
            assets_label.configure(text=str(asset_count))

        last_update = "-"
        if dataframe is not None and not dataframe.empty:
            date_series = dataframe.get("updated_at")
            if date_series is not None:
                fallback = dataframe.get("created_at")
                date_series = date_series.replace("", pd.NA)
                if fallback is not None:
                    date_series = date_series.fillna(fallback)
                parsed = pd.to_datetime(date_series, errors="coerce")
                if parsed.notna().any():
                    last_dt = parsed.max()
                    if pd.notna(last_dt):
                        last_update = DateFormatter.format_for_display(last_dt.date())
        updated_label = self.summary_labels.get("updated")
        if updated_label:
            updated_label.configure(text=last_update)

        # Aggiorna label filtri/selezione
        self._update_filter_label(filter_state)

    def _update_filter_label(self, filter_state: Optional[Dict[str, Any]] = None) -> None:
        """Aggiorna la label che mostra la selezione attiva"""
        if not hasattr(self, 'filter_label') or not self.filter_label:
            return

        # Se non ci sono filtri, mostra "Patrimonio Complessivo"
        if not filter_state or not filter_state.get('column_filters'):
            self.filter_label.configure(text="- Patrimonio Complessivo")
            return

        # Altrimenti formatta i filtri attivi
        from config import FieldMapping
        col_filters = filter_state.get('column_filters', {})

        parts = []
        for col, values in col_filters.items():
            disp = FieldMapping.DB_TO_DISPLAY.get(col, col)
            vals = list(sorted({str(v) for v in values}))
            shown = ', '.join(vals)  # Mostra tutti i valori come in Grafici/Export
            parts.append(f"{disp}: {shown}")

        if parts:
            self.filter_label.configure(text="- " + " | ".join(parts))
        else:
            self.filter_label.configure(text="- Patrimonio Complessivo")

    # ------------------------------------------------------------------
    # Rendering grafici
    # ------------------------------------------------------------------
    def _render_timeline(self, selection: Optional[pd.DataFrame]) -> None:
        """Usa ChartsUI per rendering coerente con schermata Grafici"""
        if not self.charts_ui:
            return
        chart = self.chart_objects.get("timeline")
        if not chart or not chart.get("axis"):
            return
        df = selection if selection is not None else self.portfolio_manager.get_current_assets_only()
        try:
            self.charts_ui._create_temporal_chart(df, ax=chart["axis"])
        except Exception as e:
            print(f"Errore rendering timeline: {e}")

    def _render_value_distribution(self, dataframe: Optional[pd.DataFrame]) -> None:
        """Usa ChartsUI per rendering coerente"""
        if not self.charts_ui:
            return
        chart = self.chart_objects.get("category")
        if not chart or not chart.get("axis"):
            return
        df = dataframe if dataframe is not None else self.portfolio_manager.get_current_assets_only()
        try:
            self.charts_ui._create_value_distribution_chart(df, ax=chart["axis"])
        except Exception as e:
            print(f"Errore rendering distribution: {e}")

    def _render_risk_distribution(self, dataframe: Optional[pd.DataFrame]) -> None:
        """Usa ChartsUI per rendering coerente"""
        if not self.charts_ui:
            return
        chart = self.chart_objects.get("risk")
        if not chart or not chart.get("axis"):
            return
        df = dataframe if dataframe is not None else self.portfolio_manager.get_current_assets_only()
        try:
            self.charts_ui._create_risk_distribution_chart(df, ax=chart["axis"])
        except Exception as e:
            print(f"Errore rendering risk: {e}")

    def _render_performance(self, dataframe: Optional[pd.DataFrame]) -> None:
        """Usa ChartsUI per rendering coerente"""
        if not self.charts_ui:
            return
        chart = self.chart_objects.get("performance")
        if not chart or not chart.get("axis"):
            return
        df = dataframe if dataframe is not None else self.portfolio_manager.get_current_assets_only()
        try:
            self.charts_ui._create_performance_chart(df, ax=chart["axis"])
        except Exception as e:
            print(f"Errore rendering performance: {e}")

    def _render_position_distribution(self, dataframe: Optional[pd.DataFrame]) -> None:
        """Usa ChartsUI per rendering coerente"""
        if not self.charts_ui:
            return
        chart = self.chart_objects.get("position")
        if not chart or not chart.get("axis"):
            return
        df = dataframe if dataframe is not None else self.portfolio_manager.get_current_assets_only()
        try:
            self.charts_ui._create_position_distribution_chart(df, ax=chart["axis"])
        except Exception as e:
            print(f"Errore rendering position: {e}")

    # ------------------------------------------------------------------
    # Analisi Rendimenti
    # ------------------------------------------------------------------
    def _update_analisi_rendimenti_preview(self, dataframe: Optional[pd.DataFrame], filter_state: Optional[Dict[str, Any]] = None) -> None:
        """Aggiorna la card Analisi Rendimenti nella RoadMap con Portfolio e Selezione"""
        if not hasattr(self, 'rendimento_portfolio_label') or not self.rendimento_portfolio_label:
            return

        # SEMPRE calcola rendimento portfolio complessivo (TUTTI gli asset)
        try:
            df_completo = self.portfolio_manager.get_current_assets_only()

            if df_completo.empty:
                self.rendimento_portfolio_label.configure(text="0.00%", text_color="#64748b")
            else:
                rendimento = self._calcola_rendimento_aggregato(df_completo)
                color = "#16a34a" if rendimento >= 0 else "#dc2626"
                self.rendimento_portfolio_label.configure(
                    text=f"{rendimento:.2f}%",
                    text_color=color
                )

        except Exception as e:
            print(f"Errore aggiornamento rendimento portfolio: {e}")
            self.rendimento_portfolio_label.configure(text="N/A", text_color="#64748b")

        # Gestione Selezione
        has_filters = False
        if filter_state and filter_state.get('column_filters'):
            col_filters = filter_state['column_filters']
            has_filters = any(bool(values) for values in col_filters.values())

        if not has_filters:
            # Nascondi frame selezione se non ci sono filtri
            if hasattr(self, 'selezione_frame_roadmap'):
                self.selezione_frame_roadmap.pack_forget()
        else:
            # Mostra frame selezione (con padding ridotto)
            if hasattr(self, 'selezione_frame_roadmap'):
                self.selezione_frame_roadmap.pack(fill="x", padx=12, pady=(0, 3))

                # Formatta descrizione filtri COMPLETA
                from config import FieldMapping
                parts = []
                for col, values in col_filters.items():
                    disp = FieldMapping.DB_TO_DISPLAY.get(col, col)
                    vals = list(sorted({str(v) for v in values}))  # TUTTI i valori
                    shown = ', '.join(vals)
                    parts.append(f"{disp}: {shown}")

                desc_text = " | ".join(parts)
                self.selezione_desc_label.configure(text=desc_text)

                # Calcola rendimento selezione
                if dataframe is not None and not dataframe.empty:
                    try:
                        rendimento_sel = self._calcola_rendimento_aggregato(dataframe)
                        color = "#16a34a" if rendimento_sel >= 0 else "#dc2626"
                        self.rendimento_selezione_label.configure(
                            text=f"{rendimento_sel:.2f}%",
                            text_color=color
                        )
                    except Exception as e:
                        print(f"Errore calcolo rendimento selezione: {e}")
                        self.rendimento_selezione_label.configure(text="N/A", text_color="#64748b")

    def _calcola_rendimento_aggregato(self, df: pd.DataFrame) -> float:
        """Calcola rendimento aggregato ponderato per valore"""
        valore_corrente_totale = df['updated_total_value'].fillna(df['created_total_value']).fillna(0).sum()

        if valore_corrente_totale <= 0:
            return 0.0

        rendimento_aggregato = 0.0
        for _, asset in df.iterrows():
            peso = asset['updated_total_value'] if pd.notna(asset['updated_total_value']) else asset['created_total_value']
            peso = peso if pd.notna(peso) else 0
            peso = peso / valore_corrente_totale if valore_corrente_totale > 0 else 0

            rend_asset = asset.get('return_percentage', 0)
            rend_asset = rend_asset if pd.notna(rend_asset) else 0

            rendimento_aggregato += peso * rend_asset

        return rendimento_aggregato

    # ------------------------------------------------------------------
    # Tabella rendimenti
    # ------------------------------------------------------------------
    def _update_returns_preview(self, dataframe: Optional[pd.DataFrame]) -> None:
        if not self.returns_rows:
            return

        rows = []
        if dataframe is not None and not dataframe.empty:
            df = dataframe.copy()
            df["cost_basis"] = pd.to_numeric(df.get("created_total_value"), errors="coerce").fillna(0)
            df["current_value"] = pd.to_numeric(df.get("updated_total_value"), errors="coerce")
            df["current_value"].fillna(df["cost_basis"], inplace=True)
            df["gain_value"] = df["current_value"] - df["cost_basis"]
            df["gain_pct"] = df.apply(
                lambda row: (row["gain_value"] / row["cost_basis"] * 100) if row["cost_basis"] else 0,
                axis=1,
            )
            df.sort_values("gain_value", ascending=False, inplace=True)
            rows = df.head(len(self.returns_rows)).to_dict("records")

        for idx, widgets in enumerate(self.returns_rows):
            if idx < len(rows):
                row = rows[idx]
                name = str(row.get("asset_name") or row.get("category") or "-")[:26]
                gain_value = CurrencyFormatter.format_for_display(row.get("gain_value", 0))
                gain_pct = f"{row.get('gain_pct', 0):.1f}%"
            else:
                name, gain_value, gain_pct = "-", "-", "-"

            widgets["asset"].configure(text=name)
            widgets["gain"].configure(text=gain_value)
            widgets["pct"].configure(text=gain_pct)

