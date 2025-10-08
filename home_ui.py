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
        header.grid(row=0, column=0, sticky="nsew", pady=(10, 12))
        header.grid_columnconfigure(0, weight=3)
        header.grid_columnconfigure((1, 2, 3), weight=1)

        title = ctk.CTkLabel(
            header,
            text="RoadMap AssetMind",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#0f172a",
        )
        title.grid(row=0, column=0, sticky="w", padx=24, pady=(16, 4))

        subtitle = ctk.CTkLabel(
            header,
            text="Visibilita immediata del patrimonio e accesso rapido alle analisi",
            font=ctk.CTkFont(size=14),
            text_color="#1e293b",
        )
        subtitle.grid(row=1, column=0, columnspan=4, sticky="w", padx=24, pady=(0, 12))

        metrics = [
            ("total", "Valore complessivo"),
            ("assets", "Asset correnti"),
            ("updated", "Ultimo aggiornamento"),
        ]

        for col, (key, label_text) in enumerate(metrics, start=1):
            wrapper = ctk.CTkFrame(header, corner_radius=12, fg_color="#ffffff")
            wrapper.grid(row=0, column=col, rowspan=1, sticky="nsew", padx=(8 if col > 1 else 16), pady=(14, 16))
            wrapper.grid_columnconfigure(0, weight=1)

            label = ctk.CTkLabel(
                wrapper,
                text=label_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#475569",
            )
            label.grid(row=0, column=0, sticky="w", padx=16, pady=(10, 0))

            value_label = ctk.CTkLabel(
                wrapper,
                text="-",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#1d4ed8",
            )
            value_label.grid(row=1, column=0, sticky="w", padx=16, pady=(4, 12))
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
            ("risk", "Distribuzione rischio", "chart", "Distribuzione Rischio"),
            ("performance", "Performance per categoria", "chart", "Performance per Categoria"),
            ("position", "Asset per posizione", "chart", "Suddivisione Asset per Posizione"),
            ("returns", "Rendimenti (anteprima)", "table", None),
        ]

        for index, (key, title, panel_type, chart_name) in enumerate(panel_specs):
            target_page = "Grafici" if panel_type == "chart" else "Portfolio"
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
            else:
                self._build_returns_table(frame)

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

        self._update_header(summary, dataframe)
        self._render_timeline(dataframe)
        self._render_value_distribution(dataframe)
        self._render_risk_distribution(dataframe)
        self._render_performance(dataframe)
        self._render_position_distribution(dataframe)
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

