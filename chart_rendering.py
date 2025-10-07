#!/usr/bin/env python3
"""Utility per disegnare i grafici di AssetMind su assi matplotlib."""

from __future__ import annotations

from typing import Optional, Dict, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from models import apply_global_filters
from date_utils import get_date_manager


def _draw_no_data(ax: Axes, message: str) -> None:
    ax.clear()
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=11, color="#64748b")
    ax.figure.canvas.draw_idle()


def render_value_distribution(ax: Axes, dataframe: pd.DataFrame) -> bool:
    ax.clear()
    dataframe = dataframe.copy()
    dataframe["current_value"] = (
        dataframe["updated_total_value"].fillna(dataframe["created_total_value"]).fillna(0)
    )
    category_values = dataframe.groupby("category")["current_value"].sum()
    category_values = category_values[category_values > 0]

    category_order = [
        "Immobiliare",
        "Titoli di stato",
        "Fondi di investimento",
        "Liquidita",
        "Criptovalute",
        "ETF",
        "PAC",
    ]
    ordered = [cat for cat in category_order if cat in category_values.index]
    for cat in category_values.index:
        if cat not in ordered:
            ordered.append(cat)
    category_values = category_values.reindex(ordered)

    if category_values.empty:
        _draw_no_data(ax, "Nessun valore da visualizzare")
        return False

    colors = plt_cm_set3(len(category_values))
    total_value = category_values.sum()
    percentages = (category_values / total_value * 100).round(2)

    wedges, texts, autotexts = ax.pie(
        category_values.values,
        labels=category_values.index,
        autopct="%1.2f%%",
        colors=colors,
        startangle=90,
        textprops={"fontsize": 10},
        pctdistance=0.7,
    )

    for i, (autotext, wedge) in enumerate(zip(autotexts, wedges)):
        autotext.set_color("black")
        autotext.set_weight("bold")
        angle = (wedge.theta2 + wedge.theta1) / 2
        base_distance = 0.6
        offset = (i % 3) * 0.08
        pct_distance = base_distance + offset
        x = pct_distance * np.cos(np.radians(angle))
        y = pct_distance * np.sin(np.radians(angle))
        autotext.set_position((x, y))

    ax.set_title("Distribuzione Valore per Categoria", fontsize=14, fontweight="bold", pad=20)
    legend_labels = [
        f"{percentages[cat]:.2f}% - {cat}: EUR {val:,.0f}" for cat, val in category_values.items()
    ]
    ax.legend(wedges, legend_labels, title="Categorie", loc="center left", bbox_to_anchor=(1.15, 0, 0.5, 1))
    ax.figure.canvas.draw_idle()
    return True


def render_risk_distribution(ax: Axes, dataframe: pd.DataFrame) -> bool:
    ax.clear()
    ax.grid(True, axis="y", alpha=0.3)
    risk_counts = dataframe["risk_level"].value_counts().sort_index()
    if risk_counts.empty:
        _draw_no_data(ax, "Nessun dato di rischio da visualizzare")
        return False

    colors_map = ['#16a34a', '#84cc16', '#eab308', '#f97316', '#dc2626']
    levels = []
    bar_colors = []
    for level in risk_counts.index:
        try:
            lvl_int = int(level)
        except (TypeError, ValueError):
            lvl_int = 1
        levels.append(lvl_int)
        bar_colors.append(colors_map[max(0, min(lvl_int - 1, len(colors_map) - 1))])

    bars = ax.bar(levels, risk_counts.values, color=bar_colors, alpha=0.8)
    ax.set_xlabel("Livello di rischio", fontsize=10)
    ax.set_ylabel("Numero asset", fontsize=10)
    ax.set_xticks(levels)
    ax.set_xticklabels([f"Livello {int(x)}" for x in levels])
    for bar, count in zip(bars, risk_counts.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.1,
            str(int(count)),
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )
    ax.set_title("Distribuzione del Rischio", fontsize=14, fontweight="bold", pad=20)
    ax.figure.canvas.draw_idle()
    return True


def render_performance(ax: Axes, dataframe: pd.DataFrame) -> bool:
    ax.clear()
    ax.grid(True, axis="y", alpha=0.3)

    df = dataframe.copy()
    df["created_value"] = pd.to_numeric(df.get("created_total_value"), errors="coerce").fillna(0)
    df["updated_value"] = pd.to_numeric(df.get("updated_total_value"), errors="coerce")
    df["updated_value"].fillna(df["created_value"], inplace=True)
    df["performance"] = df["updated_value"] - df["created_value"]
    category_perf = df.groupby("category")["performance"].sum()

    if category_perf.empty:
        _draw_no_data(ax, "Nessuna performance da visualizzare")
        return False

    categories = list(category_perf.index)
    values = category_perf.values
    colors = ['#16a34a' if val >= 0 else '#dc2626' for val in values]
    bars = ax.bar(categories, values, color=colors, alpha=0.85)
    ax.set_xlabel("Categoria", fontsize=10)
    ax.set_ylabel("Performance", fontsize=10)
    ax.tick_params(axis="x", rotation=25)
    ax.axhline(y=0, color="#0f172a", linewidth=0.8, alpha=0.7)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + (0.01 * max(1, abs(value))),
            f"{value:,.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    ax.set_title("Performance per Categoria", fontsize=14, fontweight="bold", pad=20)
    ax.figure.canvas.draw_idle()
    return True


def render_position_distribution(ax: Axes, dataframe: pd.DataFrame) -> bool:
    ax.clear()
    df = dataframe.copy()
    df["position_clean"] = df.get("position", "").fillna("").astype(str).str.strip()
    df["current_value"] = (
        pd.to_numeric(df.get("updated_total_value"), errors="coerce")
        .fillna(pd.to_numeric(df.get("created_total_value"), errors="coerce"))
        .fillna(0)
    )
    value_by_position = (
        df[df["position_clean"] != ""]
        .groupby("position_clean")["current_value"]
        .sum()
        .sort_values(ascending=False)
    )
    if value_by_position.empty:
        _draw_no_data(ax, "Nessuna posizione")
        return False

    positions = list(value_by_position.index)[:6]
    values = value_by_position.loc[positions].values
    ax.pie(
        values,
        labels=positions,
        autopct="%1.0f%%",
        startangle=90,
        colors=["#0ea5e9", "#38bdf8", "#22d3ee", "#2dd4bf", "#34d399", "#a3e635"],
        textprops={"fontsize": 10},
    )
    ax.axis("equal")
    ax.set_title("Asset per Posizione", fontsize=14, fontweight="bold", pad=20)
    ax.figure.canvas.draw_idle()
    return True


def render_timeline(
    ax: Axes,
    portfolio_manager,
    selection: Optional[pd.DataFrame],
    filter_info: Optional[Dict[str, Any]] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    logger=None,
) -> bool:
    ax.clear()
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.35)
    try:
        all_data = portfolio_manager.load_data()
    except Exception:
        all_data = pd.DataFrame()

    if all_data.empty:
        _draw_no_data(ax, "Dati non disponibili")
        return False

    for col in ("category", "asset_name", "position", "isin"):
        if col not in all_data.columns:
            all_data[col] = ''
    for col in ("created_total_value", "updated_total_value"):
        if col not in all_data.columns:
            all_data[col] = 0
    for col in ("created_at", "updated_at"):
        if col not in all_data.columns:
            all_data[col] = ''

    if isinstance(filter_info, dict):
        col_filters = filter_info.get('column_filters')
        if col_filters:
            try:
                all_data = apply_global_filters(all_data, col_filters)
            except Exception:
                pass

    if selection is not None and isinstance(selection, pd.DataFrame) and not selection.empty:
        sel = selection.copy()

        def _norm(series: pd.Series) -> pd.Series:
            return series.fillna('').astype(str).str.strip().str.lower()

        for col in ("category", "asset_name", "position", "isin"):
            if col not in sel.columns:
                sel[col] = ''
            if col not in all_data.columns:
                all_data[col] = ''

        sel_keys = (
            _norm(sel["category"]) + '|' +
            _norm(sel["asset_name"]) + '|' +
            _norm(sel["position"]) + '|' +
            _norm(sel["isin"])
        )
        all_data_keys = (
            _norm(all_data["category"]) + '|' +
            _norm(all_data["asset_name"]) + '|' +
            _norm(all_data["position"]) + '|' +
            _norm(all_data["isin"])
        )
        selected_set = set(sel_keys.tolist())
        all_data = all_data[all_data_keys.isin(selected_set)]

    if all_data.empty:
        _draw_no_data(ax, "Dati non disponibili")
        return False

    date_series = pd.to_datetime(all_data.get('updated_at'), errors='coerce')
    fallback = pd.to_datetime(all_data.get('created_at'), errors='coerce')
    if fallback is not None:
        date_series = date_series.fillna(fallback)
    all_data['date'] = date_series
    all_data = all_data.dropna(subset=['date'])

    if start_year is not None:
        try:
            start_year = int(start_year)
            all_data = all_data[all_data['date'].dt.year >= start_year]
        except ValueError:
            pass
    if end_year is not None:
        try:
            end_year = int(end_year)
            all_data = all_data[all_data['date'].dt.year <= end_year]
        except ValueError:
            pass

    if all_data.empty:
        _draw_no_data(ax, "Nessuna data nel periodo selezionato")
        return False

    all_data["current_value"] = (
        pd.to_numeric(all_data.get("updated_total_value"), errors="coerce")
        .fillna(pd.to_numeric(all_data.get("created_total_value"), errors="coerce"))
        .fillna(0)
    )
    all_data["category"] = all_data.get("category", "").fillna("").astype(str)

    timeline_df = (
        all_data.groupby(['date', 'category'])["current_value"].sum().reset_index()
    )
    pivot = (
        timeline_df.pivot(index='date', columns='category', values='current_value')
        .fillna(0)
        .sort_index()
    )

    if pivot.empty:
        _draw_no_data(ax, "Nessun dato temporale")
        return False

    total_series = pivot.sum(axis=1)
    colors = plt_cm_set3(len(pivot.columns))
    ax.fill_between(pivot.index, total_series, color="#bfdbfe", alpha=0.4, label="Totale")
    ax.plot(pivot.index, total_series, color="#2563eb", linewidth=2)

    for color, column in zip(colors, pivot.columns):
        ax.plot(pivot.index, pivot[column], linewidth=1.2, alpha=0.7, label=column, color=color)

    ax.set_xlabel("Data", fontsize=10)
    ax.set_ylabel("Valore", fontsize=10)
    ax.legend(loc="upper left", fontsize=8)
    ax.figure.autofmt_xdate(rotation=20)
    ax.figure.canvas.draw_idle()
    return True

def _select_record_for_date(asset_records: pd.DataFrame, target_date, date_manager) -> Optional[float]:
    best_record = None
    closest_diff = None
    for _, asset in asset_records.iterrows():
        created_date = date_manager.parse_date(asset.get('created_at'), strict=False)
        updated_date = date_manager.parse_date(asset.get('updated_at'), strict=False)
        effective_date = updated_date or created_date
        if effective_date is None:
            continue
        if effective_date <= target_date:
            diff = (target_date - effective_date).days
            value = asset.get('updated_total_value')
            if pd.isna(value) or value in (None, ""):
                value = asset.get('created_total_value', 0)
            value = float(value or 0)
            if best_record is None or diff < closest_diff:
                best_record = value
                closest_diff = diff
    return best_record


def plt_cm_set3(length: int):
    import matplotlib.pyplot as plt

    return plt.cm.Set3(np.linspace(0, 1, max(length, 1)))
