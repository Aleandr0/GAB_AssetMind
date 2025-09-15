#!/usr/bin/env python3
"""
Ottimizzazioni performance UI per GAB AssetMind
Sistema di debounce per aggiornamenti costosi e gestione ottimizzata dei refresh
"""

import time
from typing import Callable, Optional, Dict, Any
from logging_config import get_logger

class UIDebouncer:
    """
    Sistema di debounce per ritardare esecuzioni costose fino a quando
    non si stabilizzano gli input (es. resize finestra, aggiornamenti frequenti)
    """

    def __init__(self, delay_ms: int = 300):
        """
        Args:
            delay_ms: Ritardo in millisecondi prima di eseguire la funzione
        """
        self.delay_ms = delay_ms
        self.pending_calls: Dict[str, Any] = {}
        self.logger = get_logger('UIDebouncer')

    def debounce(self, parent_widget, key: str, func: Callable, *args, **kwargs):
        """
        Esegue una funzione dopo un ritardo, cancellando chiamate precedenti

        Args:
            parent_widget: Widget tkinter per scheduling (deve avere .after())
            key: Identificativo unico per la funzione da debounceare
            func: Funzione da eseguire
            args, kwargs: Argomenti per la funzione
        """
        # Cancella chiamata precedente se esiste
        if key in self.pending_calls:
            try:
                parent_widget.after_cancel(self.pending_calls[key])
                self.logger.debug(f"Cancellata chiamata precedente per {key}")
            except:
                pass  # Timer già scaduto

        # Programma nuova chiamata
        def execute():
            try:
                self.logger.debug(f"Eseguendo funzione debounced: {key}")
                func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Errore nell'esecuzione di {key}: {e}")
            finally:
                # Rimuove dalla lista pending
                self.pending_calls.pop(key, None)

        timer_id = parent_widget.after(self.delay_ms, execute)
        self.pending_calls[key] = timer_id
        self.logger.debug(f"Programmata chiamata debounced per {key} in {self.delay_ms}ms")

    def cancel_all(self, parent_widget):
        """Cancella tutti i timer pending"""
        for key, timer_id in list(self.pending_calls.items()):
            try:
                parent_widget.after_cancel(timer_id)
                self.logger.debug(f"Cancellato timer per {key}")
            except:
                pass
        self.pending_calls.clear()


class UIUpdateManager:
    """
    Gestisce gli aggiornamenti UI in modo efficiente evitando refresh eccessivi
    """

    def __init__(self, parent_widget):
        self.parent_widget = parent_widget
        self.debouncer = UIDebouncer(delay_ms=250)  # 250ms di debounce
        self.logger = get_logger('UIUpdateManager')
        self.last_update_time = 0
        self.min_update_interval = 0.1  # Minimo 100ms tra aggiornamenti

    def schedule_update(self, update_key: str, update_func: Callable,
                       immediate: bool = False, *args, **kwargs):
        """
        Programma un aggiornamento UI con debouncing automatico

        Args:
            update_key: Identificativo unico dell'aggiornamento
            update_func: Funzione di aggiornamento da eseguire
            immediate: Se True, esegue subito se è passato abbastanza tempo
            args, kwargs: Argomenti per update_func
        """
        if immediate:
            current_time = time.time()
            if current_time - self.last_update_time >= self.min_update_interval:
                # Esegui immediatamente
                try:
                    self.logger.debug(f"Aggiornamento immediato: {update_key}")
                    update_func(*args, **kwargs)
                    self.last_update_time = current_time
                    return
                except Exception as e:
                    self.logger.error(f"Errore aggiornamento immediato {update_key}: {e}")

        # Altrimenti usa debouncing
        self.debouncer.debounce(
            self.parent_widget,
            update_key,
            self._tracked_update,
            update_key, update_func, args, kwargs
        )

    def _tracked_update(self, update_key: str, update_func: Callable, args, kwargs):
        """Wrapper per tracciare il tempo dell'ultimo aggiornamento"""
        try:
            update_func(*args, **kwargs)
            self.last_update_time = time.time()
        except Exception as e:
            self.logger.error(f"Errore nell'aggiornamento {update_key}: {e}")

    def force_update(self, update_key: str, update_func: Callable, *args, **kwargs):
        """Forza un aggiornamento immediato bypassando debouncing"""
        try:
            self.logger.debug(f"Aggiornamento forzato: {update_key}")
            update_func(*args, **kwargs)
            self.last_update_time = time.time()
        except Exception as e:
            self.logger.error(f"Errore aggiornamento forzato {update_key}: {e}")

    def cleanup(self):
        """Pulisce tutti i timer pending"""
        self.debouncer.cancel_all(self.parent_widget)


class LazyColumnResizer:
    """
    Gestisce il ridimensionamento ottimizzato delle colonne TreeView
    Ridimensiona solo quando necessario e con debouncing
    """

    def __init__(self, treeview, parent_widget):
        self.treeview = treeview
        self.parent_widget = parent_widget
        self.debouncer = UIDebouncer(delay_ms=500)  # Debounce più lungo per resize
        self.logger = get_logger('LazyColumnResizer')

        self.last_row_count = 0
        self.last_zoom_level = 100
        self.cached_widths: Dict[str, int] = {}
        self.resize_needed = False

    def mark_resize_needed(self):
        """Segna che è necessario un resize (chiamata da eventi esterni)"""
        self.resize_needed = True
        self.schedule_resize()

    def schedule_resize(self, force: bool = False):
        """
        Programma un ridimensionamento delle colonne con debouncing

        Args:
            force: Se True, forza il ridimensionamento anche se non sembrava necessario
        """
        if not force and not self._should_resize():
            return

        self.debouncer.debounce(
            self.parent_widget,
            "column_resize",
            self._perform_resize
        )

    def _should_resize(self) -> bool:
        """Determina se è necessario ridimensionare"""
        current_row_count = len(self.treeview.get_children())

        # Resize se:
        # 1. Marcato come necessario esplicitamente
        # 2. Numero righe cambiato significativamente (>10% o >20 righe)
        # 3. Non ci sono larghezze cached

        if self.resize_needed:
            return True

        if not self.cached_widths:
            return True

        if current_row_count == 0 and self.last_row_count == 0:
            return False

        row_change = abs(current_row_count - self.last_row_count)
        if row_change > 20 or (self.last_row_count > 0 and row_change / self.last_row_count > 0.1):
            return True

        return False

    def _perform_resize(self):
        """Esegue il ridimensionamento effettivo delle colonne"""
        try:
            self.logger.debug("Iniziando ridimensionamento colonne ottimizzato")

            current_row_count = len(self.treeview.get_children())

            # Campiona solo prime N righe per calcolare larghezza
            sample_size = min(50, current_row_count)  # Massimo 50 righe campione
            sampled_children = list(self.treeview.get_children())[:sample_size]

            import tkinter.font as tkfont

            try:
                current_font = tkfont.nametofont("TkDefaultFont")
                font_size = int(9 * (getattr(self, 'zoom_factor', 100) / 100))
                current_font.configure(size=font_size)
            except:
                current_font = tkfont.Font(family="TkDefaultFont", size=9)

            columns_resized = 0

            for col in self.treeview['columns']:
                try:
                    # Calcola larghezza header
                    header_text = self.treeview.heading(col, "text")
                    if isinstance(header_text, str):
                        header_lines = header_text.split('\n')
                        max_header_width = max([current_font.measure(line) for line in header_lines]) if header_lines else 0
                    else:
                        max_header_width = current_font.measure(str(header_text))

                    # Calcola larghezza contenuto (solo campione)
                    max_content_width = 0
                    for item in sampled_children:
                        item_values = self.treeview.item(item, 'values')
                        if item_values:
                            col_index = list(self.treeview['columns']).index(col)
                            if col_index < len(item_values):
                                cell_text = str(item_values[col_index])[:50]  # Tronca testo lungo
                                content_width = current_font.measure(cell_text)
                                max_content_width = max(max_content_width, content_width)

                    # Calcola larghezza finale
                    calculated_width = max(max_header_width, max_content_width) + 20

                    # Limiti e cache
                    min_width = 60
                    max_width = 300
                    final_width = max(min_width, min(max_width, calculated_width))

                    # Applica solo se differenza significativa (>10px o >20%)
                    current_width = self.treeview.column(col, 'width')
                    cached_width = self.cached_widths.get(col, 0)

                    if (abs(final_width - cached_width) > 10 and
                        (cached_width == 0 or abs(final_width - cached_width) / cached_width > 0.2)):

                        self.treeview.column(col, width=final_width)
                        self.cached_widths[col] = final_width
                        columns_resized += 1

                except Exception as e:
                    self.logger.error(f"Errore ridimensionamento colonna {col}: {e}")
                    continue

            # Aggiorna stato
            self.last_row_count = current_row_count
            self.resize_needed = False

            self.logger.debug(f"Ridimensionamento completato: {columns_resized} colonne aggiornate")

        except Exception as e:
            self.logger.error(f"Errore durante ridimensionamento colonne: {e}")

    def update_zoom_factor(self, zoom_factor: int):
        """Aggiorna il fattore di zoom e segna resize come necessario"""
        if zoom_factor != self.last_zoom_level:
            self.last_zoom_level = zoom_factor
            self.zoom_factor = zoom_factor
            self.cached_widths.clear()  # Invalida cache
            self.mark_resize_needed()

    def invalidate_cache(self):
        """Invalida la cache delle larghezze (da chiamare quando cambia contenuto)"""
        self.cached_widths.clear()
        self.mark_resize_needed()


class UIRefreshOptimizer:
    """
    Ottimizza i refresh dell'interfaccia utente evitando chiamate eccessive
    """

    def __init__(self, parent_widget):
        self.parent_widget = parent_widget
        self.logger = get_logger('UIRefreshOptimizer')
        self.last_refresh_time = 0
        self.min_refresh_interval = 0.05  # 50ms minimo tra refresh

    def smart_refresh(self, force: bool = False):
        """
        Esegue un refresh intelligente dell'UI

        Args:
            force: Se True, forza il refresh anche se recente
        """
        current_time = time.time()

        if not force and (current_time - self.last_refresh_time) < self.min_refresh_interval:
            self.logger.debug("Refresh troppo recente, skipping")
            return

        try:
            self.logger.debug("Eseguendo smart refresh UI")

            # Refresh ottimizzato: solo update_idletasks invece di update completo
            self.parent_widget.update_idletasks()

            self.last_refresh_time = current_time

        except Exception as e:
            self.logger.error(f"Errore durante smart refresh: {e}")

    def batch_refresh(self, widgets_to_refresh: list):
        """
        Esegue refresh in batch su una lista di widget per efficienza

        Args:
            widgets_to_refresh: Lista di widget da aggiornare
        """
        try:
            self.logger.debug(f"Eseguendo batch refresh su {len(widgets_to_refresh)} widget")

            for widget in widgets_to_refresh:
                if hasattr(widget, 'update_idletasks'):
                    widget.update_idletasks()

            self.last_refresh_time = time.time()

        except Exception as e:
            self.logger.error(f"Errore durante batch refresh: {e}")