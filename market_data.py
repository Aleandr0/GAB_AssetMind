#!/usr/bin/env python3
"""Integrazione con Twelve Data per il recupero dei prezzi di mercato."""

from __future__ import annotations

import os
from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Optional, Any, List

from config import get_application_directory

try:
    import requests  # type: ignore
    REQUESTS_AVAILABLE = True
except ImportError:  # pragma: no cover - gestito dinamicamente nei test
    requests = None  # type: ignore
    REQUESTS_AVAILABLE = False

from logging_config import get_logger

try:
    import yfinance as yf  # type: ignore
    YFINANCE_AVAILABLE = True
except ImportError:  # pragma: no cover - opzionale
    yf = None  # type: ignore
    YFINANCE_AVAILABLE = False


DEFAULT_PROVIDER_CONFIG: Dict[str, Dict[str, Any]] = {
    "manual_override": {"enabled": True, "priority": 0},
    "twelvedata": {"enabled": True, "priority": 1},
    "yahoo": {"enabled": True, "priority": 2},
    "issuer_nav": {"enabled": True, "priority": 3},
}

ISSUER_NAV_CONFIG: Dict[str, Dict[str, Any]] = {
    "LU0171310955": {
        "provider": "blackrock",
        "fund_id": "253114",
        "currency": "EUR",
        "name": "BGF World Technology E2 EUR",
        "fallback_symbol": "0P0001LZU2.F",
    },
}

YAHOO_SYMBOL_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "IE00B0M62X26": {
        "symbols": ["IBCI.L", "IBCI.AS"],
        "name": "iShares EUR Inflation Linked Govt Bond UCITS ETF EUR Acc",
    },
    "IE00B4L5Y983": {
        "symbols": ["SWDA.MI", "IWDA.L"],  # Milano EUR prima
        "name": "iShares Core MSCI World UCITS ETF USD Acc",
    },
    "IE00B3XXRP09": {
        "symbols": ["VUSA.L", "VUSA.MI"],
        "name": "Vanguard S&P 500 UCITS ETF USD Dist",
    },
    "IE00B5BMR087": {
        "symbols": ["CSSPX.MI", "SXR8.DE", "CSPX.L"],  # Milano/Xetra EUR prima, London GBP dopo
        "name": "iShares Core S&P 500 UCITS ETF USD Acc",
    },
    "IE00BFZXGZ54": {
        "symbols": ["EQAC.MI", "EQAC.DE", "EQQQ.L"],  # Milano EUR (migliore match)
        "name": "Invesco EQQQ Nasdaq-100 UCITS ETF Acc",
    },
    "IE00BK5BR626": {
        "symbols": ["VGWE.DE", "VHYA.L", "VHYL.L"],
        "name": "Vanguard FTSE All-World High Dividend Yield UCITS ETF USD Acc",
    },
    "IE00BDBRDM35": {
        "symbols": ["0GGH.L", "AGGH.MI"],
        "name": "iShares Global Aggregate Bond UCITS ETF EUR Hedged Acc",
    },
    "IE000BI8OT95": {
        "symbols": ["CW8.PA", "CW8.MI", "CW8.DE"],
        "name": "Amundi Core MSCI World UCITS ETF Acc",
    },
    "IE000QU8JEH5": {
        "symbols": ["AI4U.MI"],
        "name": "Fineco AM MarketVector Artificial Intelligence Sustainable UCITS ETF",
    },
    "LU1900066033": {
        "symbols": ["CHIP.MI", "CHIP.SW"],  # Milano EUR prima, Swiss dopo
        "name": "Amundi MSCI Semiconductors UCITS ETF Acc",
    },
    "LU1437015735": {
        "symbols": ["CEU2.PA"],
        "name": "Amundi Core MSCI Europe UCITS ETF DR",
    },
    "LU1046235815": {
        "symbols": ["0P00012U2R.F"],
        "name": "Schroder ISF Strategic Credit B Acc EUR Hedged",
    },
    "LU1915690595": {
        "symbols": ["NDJX.MU", "0P0001FLOK.F"],
        "name": "Nordea 1 European Covered Bond Opportunities BP-EUR",
    },
}


@dataclass
class QuoteResult:
    success: bool
    payload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    provider_used: Optional[str] = None


class MarketDataError(Exception):
    """Errore generico per il servizio di dati di mercato."""


class MarketDataService:
    """Client minimale per l'API Twelve Data.

    L'implementazione privilegia semplicità e robustezza:
    - gestione della chiave API tramite variabile di ambiente ``TWELVE_DATA_API_KEY``
    - caching in memoria di lookup simboli e quote per ridurre il numero di richieste
    - normalizzazione delle risposte per restituire un payload coerente
    """

    BASE_URL = "https://api.twelvedata.com"
    API_KEY_FILENAME = "TWELVE_DATA_API_KEY.txt"

    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
        timeout: float = 10.0,
        provider_config: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        if not REQUESTS_AVAILABLE:
            raise MarketDataError(
                "La dipendenza 'requests' è necessaria per MarketDataService. "
                "Esegui 'pip install -r requirements.txt' per installarla."
            )

        self.logger = get_logger("MarketDataService")
        self.api_key = api_key or os.getenv("TWELVE_DATA_API_KEY", "")
        if not self.api_key:
            self.api_key = self._load_api_key_from_file()

        self.session = session or requests.Session()
        self.timeout = timeout
        self.provider_config = deepcopy(provider_config) if provider_config else deepcopy(DEFAULT_PROVIDER_CONFIG)
        self._symbol_cache: Dict[str, Dict[str, Any]] = {}
        self._quote_cache: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # API pubblica
    # ------------------------------------------------------------------
    def is_configured(self) -> bool:
        """Restituisce True se è configurata una API key valida."""

        return bool(self.api_key)

    def get_latest_price(
        self,
        ticker: Optional[str] = None,
        isin: Optional[str] = None,
        asset_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Recupera l'ultima quotazione disponibile per l'asset indicato.

        Args:
            ticker: simbolo di mercato (prioritario se presente)
            isin: codice ISIN utilizzato come fallback
            asset_name: nome dell'asset (aiuta l'heuristica di ricerca simbolo)
        Returns:
            Dizionario con almeno ``symbol`` e ``price``
        Raises:
            MarketDataError: problemi di configurazione, rete o risposta API
        """

        if not self.api_key:
            raise MarketDataError(
                "Chiave API Twelve Data non configurata. "
                "Imposta la variabile d'ambiente TWELVE_DATA_API_KEY."
            )

        symbol_info = self._resolve_symbol(ticker, isin, asset_name)
        if not symbol_info or not symbol_info.get("symbol"):
            raise MarketDataError(
                "Impossibile determinare un simbolo valido per l'asset selezionato."
            )

        quote_result = self._resolve_quote(symbol_info)
        if not quote_result.success or not quote_result.payload:
            raise MarketDataError(quote_result.error or "Impossibile recuperare la quotazione selezionata.")

        quote = quote_result.payload
        resolved_symbol = quote.get("symbol") or symbol_info.get("symbol")

        payload = {
            "symbol": resolved_symbol,
            "price": quote["price"],
            "currency": quote.get("currency"),
            "name": symbol_info.get("name") or quote.get("name"),
            "exchange": symbol_info.get("exchange") or quote.get("exchange"),
            "source": symbol_info.get("source", "ticker" if ticker else "lookup"),
            "provider": quote_result.provider_used or quote.get("provider", "twelvedata"),
        }
        if resolved_symbol:
            symbol_info["symbol"] = resolved_symbol
        return payload

    def _load_api_key_from_file(self) -> str:
        """Legge la chiave API da un file locale se presente."""

        candidates = []
        try:
            candidates.append(os.path.join(get_application_directory(), self.API_KEY_FILENAME))
        except Exception as exc:  # pragma: no cover - fallback ambiente runtime
            self.logger.debug(f"Impossibile determinare la cartella applicativa: {exc}")
        candidates.append(os.path.join(os.getcwd(), self.API_KEY_FILENAME))

        for path_str in candidates:
            if not path_str or not os.path.isfile(path_str):
                continue
            try:
                with open(path_str, "r", encoding="utf-8") as handle:
                    content = handle.readline().strip()
                    if content:
                        self.logger.debug("Chiave Twelve Data caricata da file locale: %s", path_str)
                        return content
            except OSError as exc:
                self.logger.warning("Impossibile leggere %s: %s", path_str, exc)
        return ""

    # ------------------------------------------------------------------
    # Metodi interni
    # ------------------------------------------------------------------
    def _resolve_symbol(
        self,
        ticker: Optional[str],
        isin: Optional[str],
        asset_name: Optional[str],
    ) -> Dict[str, Any]:
        if ticker:
            normalized = ticker.strip().upper()
            if not normalized:
                raise MarketDataError("Ticker non valido fornito per l'asset selezionato.")

            info: Dict[str, Any] = {
                "symbol": normalized,
                "name": asset_name,
                "source": "ticker",
                "allow_yahoo_fallback": True,
            }

            override_info = self._get_override_for_isin(isin) if isin else None
            if override_info:
                symbols = self._normalize_symbol_list(override_info.get("symbols"))
                if not symbols and override_info.get("symbol"):
                    symbols = self._normalize_symbol_list([override_info.get("symbol")])
                if symbols:
                    info["candidate_symbols"] = self._prioritize_symbols(normalized, symbols)
                if override_info.get("name") and not asset_name:
                    info["name"] = override_info.get("name")
                preferred = override_info.get("preferred_provider")
                if preferred:
                    info["preferred_provider"] = preferred

            issuer_config = self._get_issuer_nav_config(isin) if isin else None
            if issuer_config:
                issuer_data = dict(issuer_config)
                issuer_data.setdefault("isin", (isin or "").upper())
                info["preferred_provider"] = "issuer_blackrock"
                info["issuer_config"] = issuer_data
                fallback_symbols = self._normalize_symbol_list([issuer_data.get("fallback_symbol")]) if issuer_data.get("fallback_symbol") else []
                if fallback_symbols:
                    info["candidate_symbols"] = self._prioritize_symbols(normalized, fallback_symbols)
                info["allow_yahoo_fallback"] = False

            return info

        if not isin:
            raise MarketDataError(
                "Per questo asset non sono disponibili ticker o ISIN aggiornabili."
            )

        cache_key = f"isin:{isin.upper()}"
        issuer_cache_cfg = self._get_issuer_nav_config(isin)
        if issuer_cache_cfg and cache_key in self._symbol_cache:
            cached_entry = self._symbol_cache.get(cache_key)
            if cached_entry and cached_entry.get('preferred_provider') != 'issuer_blackrock':
                self._symbol_cache.pop(cache_key, None)
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]

        override_info = self._get_override_for_isin(isin)
        if override_info:
            symbols = self._normalize_symbol_list(override_info.get("symbols", []))
            if not symbols and override_info.get("symbol"):
                symbols = self._normalize_symbol_list([override_info.get("symbol")])
            if symbols:
                info = {
                    "symbol": symbols[0],
                    "name": override_info.get("name") or asset_name,
                    "exchange": override_info.get("exchange"),
                    "currency": override_info.get("currency"),
                    "source": "manual_override",
                    "preferred_provider": "yahoo",
                    "candidate_symbols": symbols,
                    "allow_yahoo_fallback": True,
                }
                self._symbol_cache[cache_key] = info
                self.logger.debug("Uso override Yahoo per ISIN %s -> %s", isin, symbols[0])
                return info
            else:
                self.logger.debug("Override Yahoo per ISIN %s ignorato: nessun simbolo valido", isin)

        issuer_config = self._get_issuer_nav_config(isin)
        if issuer_config:
            candidate_symbols = self._normalize_symbol_list([issuer_config.get("fallback_symbol")]) if issuer_config.get("fallback_symbol") else []
            issuer_data = dict(issuer_config)
            issuer_data.setdefault("isin", (isin or "").upper())
            info = {
                "symbol": (isin or "").upper(),
                "isin": (isin or "").upper(),
                "name": issuer_data.get("name") or asset_name,
                "exchange": issuer_data.get("exchange", "NAV"),
                "currency": issuer_data.get("currency"),
                "source": "issuer_nav",
                "preferred_provider": "issuer_blackrock",
                "issuer_config": issuer_data,
                "candidate_symbols": candidate_symbols,
                "allow_yahoo_fallback": bool(candidate_symbols),
            }
            self._symbol_cache[cache_key] = info
            self.logger.debug("Uso configurazione NAV emittente per ISIN %s", isin)
            return info

        data = self._request("/symbol_search", {"symbol": isin})
        candidates = data.get("data", []) if isinstance(data, dict) else []
        if not candidates:
            raise MarketDataError(
                f"Nessun simbolo Twelve Data trovato per l'ISIN {isin}."
            )

        chosen = self._select_best_candidate(candidates, isin, asset_name)
        if not chosen or not chosen.get("symbol"):
            raise MarketDataError(
                f"Risposta Twelve Data incompleta per l'ISIN {isin}: simbolo mancante."
            )

        info = {
            "symbol": chosen.get("symbol", "").upper(),
            "name": chosen.get("instrument_name")
            or chosen.get("name")
            or asset_name,
            "exchange": chosen.get("exchange"),
            "currency": chosen.get("currency"),
            "source": "isin_lookup",
        }
        self._symbol_cache[cache_key] = info
        return info

    def _resolve_quote(self, symbol_info: Dict[str, Any]) -> QuoteResult:
        symbol = (symbol_info.get("symbol") or "").strip()
        if not symbol:
            return QuoteResult(False, error="Simbolo non determinato per il recupero del prezzo.")

        preferred_provider = symbol_info.get("preferred_provider")
        if preferred_provider == "yahoo":
            if not self._is_provider_enabled("yahoo"):
                return QuoteResult(False, error="Provider Yahoo disabilitato dalla configurazione.")
            return self._quote_from_yahoo_candidates(symbol_info)
        if preferred_provider == "issuer_blackrock":
            return self._quote_from_issuer_nav(symbol_info)

        try:
            quote = self._fetch_quote(symbol)
            return QuoteResult(True, payload=quote, provider_used="twelvedata")
        except MarketDataError as exc:
            message = str(exc)
            if self._should_use_yahoo(symbol_info, message):
                self.logger.info("Fallback yfinance per %s: %s", symbol, message)
                yahoo_result = self._quote_from_yahoo_candidates(symbol_info)
                if yahoo_result.success:
                    return yahoo_result
                combined_error = message
                if yahoo_result.error:
                    combined_error = f"{message} | {yahoo_result.error}"
                return QuoteResult(False, error=combined_error, provider_used="yfinance")
            return QuoteResult(False, error=message)

    def _quote_from_yahoo_candidates(self, symbol_info: Dict[str, Any]) -> QuoteResult:
        if not self._is_provider_enabled("yahoo"):
            return QuoteResult(False, error="Provider Yahoo disabilitato dalla configurazione.")

        candidates = symbol_info.get("candidate_symbols") or []
        base_symbol = symbol_info.get("symbol")
        if not candidates and base_symbol:
            candidates = [base_symbol]

        errors: List[str] = []
        for candidate in candidates:
            candidate = (candidate or "").strip()
            if not candidate:
                continue
            try:
                quote = self._fetch_quote_yfinance(candidate)
                normalized = (quote.get("symbol") or candidate).upper()
                symbol_info["symbol"] = normalized
                symbol_info["preferred_provider"] = "yahoo"
                symbol_info["candidate_symbols"] = self._prioritize_symbols(normalized, candidates)
                return QuoteResult(True, payload=quote, provider_used="yfinance")
            except MarketDataError as exc:
                errors.append(str(exc))

        unique_errors = " | ".join(dict.fromkeys(err for err in errors if err))
        provider = "yfinance" if YFINANCE_AVAILABLE else None
        return QuoteResult(False, error=unique_errors or "yfinance non ha fornito dati disponibili.", provider_used=provider)

    def _quote_from_issuer_nav(self, symbol_info: Dict[str, Any]) -> QuoteResult:
        if not self._is_provider_enabled("issuer_nav"):
            return QuoteResult(False, error="Provider NAV emittente disabilitato dalla configurazione.")

        issuer_config = symbol_info.get("issuer_config") or {}
        isin = (issuer_config.get("isin") or symbol_info.get("isin") or symbol_info.get("symbol") or "").upper()
        if not isin:
            return QuoteResult(False, error="ISIN non disponibile per la risoluzione NAV emittente.")

        error_message = None
        try:
            nav_quote = self._fetch_blackrock_nav(isin, issuer_config)
            if nav_quote:
                nav_quote.setdefault('symbol', isin)
                return QuoteResult(True, payload=nav_quote, provider_used='blackrock_nav')
        except MarketDataError as exc:
            error_message = (str(exc) or "").strip() or None

        base_message = "NAV emittente non disponibile"
        if error_message:
            lowered = error_message.lower()
            if "nav" in lowered:
                base_message = error_message
            else:
                base_message = f"{base_message}: {error_message}"
        return QuoteResult(False, error=base_message, provider_used="issuer_nav")

    def _prioritize_symbols(self, primary: str, candidates: List[str]) -> List[str]:
        ordered: List[str] = []
        seen = set()
        for candidate in [primary] + list(candidates):
            normalized = (candidate or "").strip().upper()
            if normalized and normalized not in seen:
                ordered.append(normalized)
                seen.add(normalized)
        return ordered

    def _normalize_symbol_list(self, symbols: Any) -> List[str]:
        if isinstance(symbols, str):
            symbols = [symbols]
        normalized: List[str] = []
        seen = set()
        for symbol in symbols or []:
            clean = (symbol or "").strip().upper()
            if clean and clean not in seen:
                normalized.append(clean)
                seen.add(clean)
        return normalized

    def _is_provider_enabled(self, provider_name: str) -> bool:
        try:
            config = self.provider_config.get(provider_name, {})
        except AttributeError:
            return True
        if not isinstance(config, dict):
            return True
        return bool(config.get("enabled", True))

    def _should_use_yahoo(self, symbol_info: Dict[str, Any], message: str) -> bool:
        if not self._is_provider_enabled("yahoo"):
            return False

        message_lower = (message or "").lower()
        fallback_tokens = (
            "missing or invalid",
            "not available",
            "not supported",
            "not found",
            "not provided",
            "invalid symbol",
        )

        if self._is_grow_plan_error(message):
            return True
        if any(token in message_lower for token in fallback_tokens):
            return True
        return bool(symbol_info.get("allow_yahoo_fallback"))

    def _get_issuer_nav_config(self, isin: Optional[str]) -> Optional[Dict[str, Any]]:
        if not isin:
            return None
        if not self._is_provider_enabled("issuer_nav"):
            return None
        return ISSUER_NAV_CONFIG.get(isin.upper())

    def _get_override_for_isin(self, isin: Optional[str]) -> Optional[Dict[str, Any]]:
        if not isin:
            return None
        if not self._is_provider_enabled("manual_override"):
            return None
        return YAHOO_SYMBOL_OVERRIDES.get(isin.upper())

    def _select_best_candidate(
        self, candidates: Any, isin: str, asset_name: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        normalized_isin = (isin or "").upper()
        normalized_name = (asset_name or "").lower()

        # 1) Match diretto su campo ISIN se disponibile
        for entry in candidates:
            entry_isin = (entry.get("isin") or "").upper()
            if entry_isin == normalized_isin:
                return entry

        # 2) Fallback su nome che contiene l'asset name
        if normalized_name:
            for entry in candidates:
                candidate_name = (
                    entry.get("instrument_name")
                    or entry.get("name")
                    or ""
                ).lower()
                if normalized_name in candidate_name:
                    return entry

        # 3) Ultimo fallback: primo risultato utile
        return candidates[0] if candidates else None

    def _fetch_quote(self, symbol: str) -> Dict[str, Any]:
        normalized = symbol.upper()
        if normalized in self._quote_cache:
            return self._quote_cache[normalized]

        data = self._request("/quote", {"symbol": normalized})
        if not isinstance(data, dict):
            raise MarketDataError(
                f"Risposta Twelve Data non valida per il simbolo {symbol}."
            )

        if data.get("status") == "error" or "message" in data and not data.get("price"):
            message = data.get("message", "Errore sconosciuto dalla API Twelve Data")
            raise MarketDataError(message)

        price_value = data.get("price") or data.get("close")
        try:
            price = float(price_value)
        except (TypeError, ValueError):
            raise MarketDataError(
                f"La quotazione per {symbol} non è disponibile o non è numerica."
            )

        quote = {
            "symbol": normalized,
            "price": price,
            "currency": data.get("currency"),
            "name": data.get("name"),
            "exchange": data.get("exchange"),
            "provider": "twelvedata",
        }
        self._quote_cache[normalized] = quote
        return quote

    def _fetch_quote_yfinance(self, symbol: str) -> Dict[str, Any]:

        if not YFINANCE_AVAILABLE:
            raise MarketDataError("Il fallback yfinance non è disponibile: installa il pacchetto 'yfinance'.")

        normalized = symbol.upper()
        import math

        try:
            ticker = yf.Ticker(symbol)
            price = None
            currency = None
            exchange = None
            name = None

            try:
                fast_info = getattr(ticker, 'fast_info', None)
            except Exception as fi_exc:
                self.logger.debug("yfinance fast_info non disponibile per %s: %s", symbol, fi_exc)
                fast_info = None

            def _fi_get(obj: Any, key: str) -> Any:
                if obj is None:
                    return None
                if isinstance(obj, dict):
                    return obj.get(key)
                return getattr(obj, key, None)

            if fast_info:
                price = _fi_get(fast_info, 'last_price') or _fi_get(fast_info, 'last_close')
                currency = _fi_get(fast_info, 'currency') or _fi_get(fast_info, 'last_price_currency')
                exchange = _fi_get(fast_info, 'exchange')

            if price is None:
                history = ticker.history(period='1d', interval='1d')
                if not history.empty:
                    price = float(history['Close'].iloc[-1])

            if price is None:
                raise MarketDataError(f"yfinance: prezzo non disponibile per {symbol}")

            info: Dict[str, Any] = {}
            try:
                raw_info = getattr(ticker, 'info', {})
                if isinstance(raw_info, dict):
                    info = raw_info
            except Exception as info_exc:
                self.logger.debug("yfinance info non disponibile per %s: %s", symbol, info_exc)
                info = {}

            if not currency:
                currency = info.get('currency')
            if not exchange:
                exchange = info.get('exchange') or info.get('fullExchangeName')
            name = info.get('shortName') or info.get('longName') or symbol

            price = float(price)
            if math.isnan(price) or price <= 0:
                raise MarketDataError(f"yfinance: prezzo non valido per {symbol}")

        except Exception as exc:
            raise MarketDataError(f"Errore yfinance per {symbol}: {exc}") from exc


        quote = {
            "symbol": normalized,
            "price": price,
            "currency": currency,
            "name": name,
            "exchange": exchange,
            "provider": "yfinance",
        }
        self._quote_cache[normalized] = quote
        return quote

    def _fetch_blackrock_nav(self, isin: str, issuer_config: Dict[str, Any]) -> Dict[str, Any]:
        url = "https://www.blackrock.com/tools/hackathon/performance"
        params = {"identifiers": isin}
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as exc:
            raise MarketDataError(f"NAV BlackRock HTTP {exc.response.status_code}") from exc
        except requests.exceptions.RequestException as exc:
            raise MarketDataError("NAV BlackRock non disponibile (errore di rete)") from exc
        except ValueError as exc:
            raise MarketDataError("NAV BlackRock risposta non JSON valida") from exc

        returns = data.get("resultMap", {}).get("RETURNS") or []
        if not returns:
            raise MarketDataError("NAV BlackRock non presente nella risposta")

        entry = returns[0]
        nav_value = entry.get("latestNAV") or entry.get("nav")
        if nav_value is None:
            raise MarketDataError("NAV BlackRock non indicato")

        try:
            price = float(nav_value)
        except (TypeError, ValueError) as exc:
            raise MarketDataError("NAV BlackRock non numerico") from exc

        currency = entry.get("currency") or issuer_config.get("currency") or ""
        as_of = entry.get("latestPerformanceDate") or entry.get("navDate")

        quote = {
            "symbol": isin,
            "price": price,
            "currency": currency,
            "name": entry.get("productName") or issuer_config.get("name"),
            "exchange": "NAV",
            "provider": "blackrock_nav",
            "asof": as_of,
            "meta": entry,
        }
        cache_key = f"BLACKROCK:{isin}"
        self._quote_cache[cache_key] = quote
        return quote

    def _is_grow_plan_error(self, message: str) -> bool:
        lowered = (message or '').lower()
        return (
            'grow plan' in lowered
            or 'pro plan' in lowered
            or 'available starting with grow' in lowered
            or 'available starting with pro' in lowered
        )

    def _request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        request_params = dict(params)
        request_params["apikey"] = self.api_key

        try:
            response = self.session.get(url, params=request_params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as exc:
            message = (
                f"Errore HTTP Twelve Data ({exc.response.status_code}): "
                f"{exc.response.text.strip()}"
            )
            raise MarketDataError(message) from exc
        except requests.exceptions.RequestException as exc:
            raise MarketDataError(
                "Errore di rete durante la chiamata a Twelve Data."
            ) from exc
        except ValueError as exc:
            raise MarketDataError("Risposta Twelve Data non in formato JSON valido.") from exc

        if isinstance(data, dict) and data.get("status") == "error":
            raise MarketDataError(data.get("message", "Errore Twelve Data sconosciuto"))

        # L'API usa spesso chiavi "code"/"message" anche con status 200.
        if isinstance(data, dict) and data.get("code") not in (None, 200):
            raise MarketDataError(data.get("message", "Errore Twelve Data"))

        return data


