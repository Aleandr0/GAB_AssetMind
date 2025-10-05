#!/usr/bin/env python3
"""
Sistema di retry automatico per chiamate API con backoff esponenziale
Gestisce errori temporanei (503, 504, timeout) con retry intelligente
"""

import time
import functools
from typing import Callable, Any, Optional, List, Type
from logging_config import get_logger

logger = get_logger("APIRetry")


class RetryableError(Exception):
    """Eccezione per errori che possono essere ritentati"""
    pass


class APIRetryConfig:
    """Configurazione sistema retry"""

    # Numero massimo tentativi
    MAX_RETRIES = 3

    # Delay iniziale (secondi)
    INITIAL_DELAY = 1.0

    # Moltiplicatore backoff esponenziale
    BACKOFF_MULTIPLIER = 2.0

    # Delay massimo tra retry (secondi)
    MAX_DELAY = 30.0

    # Codici HTTP che richiedono retry
    RETRYABLE_HTTP_CODES = {
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
    }

    # Eccezioni che richiedono retry
    RETRYABLE_EXCEPTIONS = (
        RetryableError,
        ConnectionError,
        TimeoutError,
    )


def should_retry_http_error(http_code: int) -> bool:
    """Verifica se un codice HTTP richiede retry"""
    return http_code in APIRetryConfig.RETRYABLE_HTTP_CODES


def should_retry_exception(exc: Exception) -> bool:
    """Verifica se un'eccezione richiede retry"""
    # Check eccezioni retryable dirette
    if isinstance(exc, APIRetryConfig.RETRYABLE_EXCEPTIONS):
        return True

    # Check requests.exceptions
    try:
        import requests
        if isinstance(exc, (requests.exceptions.ConnectionError,
                          requests.exceptions.Timeout,
                          requests.exceptions.HTTPError)):
            # Per HTTPError, check status code
            if isinstance(exc, requests.exceptions.HTTPError):
                if hasattr(exc, 'response') and exc.response:
                    return should_retry_http_error(exc.response.status_code)
            return True
    except ImportError:
        pass

    # Check per errori network generici
    exc_str = str(exc).lower()
    retryable_keywords = [
        'timeout',
        'connection',
        'network',
        'unavailable',
        'temporarily',
        'service error',
    ]

    return any(keyword in exc_str for keyword in retryable_keywords)


def retry_with_backoff(
    max_retries: int = APIRetryConfig.MAX_RETRIES,
    initial_delay: float = APIRetryConfig.INITIAL_DELAY,
    backoff_multiplier: float = APIRetryConfig.BACKOFF_MULTIPLIER,
    max_delay: float = APIRetryConfig.MAX_DELAY,
    retryable_exceptions: Optional[tuple] = None
):
    """
    Decorator per retry automatico con backoff esponenziale

    Args:
        max_retries: Numero massimo tentativi
        initial_delay: Delay iniziale in secondi
        backoff_multiplier: Moltiplicatore per backoff esponenziale
        max_delay: Delay massimo tra retry
        retryable_exceptions: Tuple di eccezioni da ritentare

    Example:
        @retry_with_backoff(max_retries=3)
        def fetch_price(symbol):
            response = requests.get(f"https://api.example.com/{symbol}")
            response.raise_for_status()
            return response.json()
    """
    if retryable_exceptions is None:
        retryable_exceptions = APIRetryConfig.RETRYABLE_EXCEPTIONS

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"{func.__name__}: successo al tentativo {attempt + 1}")
                    return result

                except Exception as exc:
                    last_exception = exc

                    # Check se errore è retryable
                    if not should_retry_exception(exc):
                        logger.debug(f"{func.__name__}: errore non retryable: {exc}")
                        raise

                    # Se ultimo tentativo, rilancia
                    if attempt >= max_retries:
                        logger.error(
                            f"{func.__name__}: fallito dopo {max_retries + 1} tentativi: {exc}"
                        )
                        raise

                    # Log retry
                    logger.warning(
                        f"{func.__name__}: tentativo {attempt + 1}/{max_retries + 1} fallito: {exc}. "
                        f"Retry tra {delay:.1f}s..."
                    )

                    # Attendi prima del prossimo tentativo
                    time.sleep(delay)

                    # Incrementa delay con backoff esponenziale
                    delay = min(delay * backoff_multiplier, max_delay)

            # Non dovrebbe mai arrivare qui, ma per sicurezza
            if last_exception:
                raise last_exception
            raise RuntimeError(f"{func.__name__}: retry loop terminato senza risultato")

        return wrapper
    return decorator


class APIRetryWrapper:
    """
    Wrapper per chiamate API con retry e monitoraggio

    Features:
    - Retry automatico con backoff
    - Statistiche successi/fallimenti
    - Circuit breaker pattern (opzionale)
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        enable_circuit_breaker: bool = False,
        failure_threshold: int = 5
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.enable_circuit_breaker = enable_circuit_breaker
        self.failure_threshold = failure_threshold

        # Statistiche
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.retried_calls = 0
        self.consecutive_failures = 0

        # Circuit breaker
        self.circuit_open = False
        self.circuit_opened_at: Optional[float] = None
        self.circuit_reset_timeout = 60.0  # secondi

        self.logger = get_logger(self.__class__.__name__)

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Esegue chiamata con retry automatico

        Args:
            func: Funzione da chiamare
            *args, **kwargs: Argomenti per func

        Returns:
            Risultato di func

        Raises:
            Exception: Se tutti i retry falliscono
        """
        self.total_calls += 1

        # Check circuit breaker
        if self._is_circuit_open():
            self.failed_calls += 1
            raise RetryableError("Circuit breaker aperto - troppe chiamate fallite di recente")

        delay = self.initial_delay
        last_exception = None
        retry_count = 0

        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)

                # Successo!
                self.successful_calls += 1
                self.consecutive_failures = 0

                if retry_count > 0:
                    self.retried_calls += 1
                    self.logger.info(f"Chiamata riuscita dopo {retry_count} retry")

                # Chiudi circuit breaker se era aperto
                if self.circuit_open:
                    self._close_circuit()

                return result

            except Exception as exc:
                last_exception = exc
                retry_count += 1

                if not should_retry_exception(exc):
                    self.failed_calls += 1
                    self.consecutive_failures += 1
                    self._check_circuit_breaker()
                    raise

                if attempt >= self.max_retries:
                    self.failed_calls += 1
                    self.consecutive_failures += 1
                    self._check_circuit_breaker()
                    self.logger.error(f"Chiamata fallita dopo {self.max_retries + 1} tentativi")
                    raise

                self.logger.warning(f"Tentativo {attempt + 1} fallito: {exc}. Retry tra {delay:.1f}s...")
                time.sleep(delay)
                delay = min(delay * APIRetryConfig.BACKOFF_MULTIPLIER, APIRetryConfig.MAX_DELAY)

        if last_exception:
            raise last_exception

    def _is_circuit_open(self) -> bool:
        """Verifica se circuit breaker è aperto"""
        if not self.enable_circuit_breaker:
            return False

        if not self.circuit_open:
            return False

        # Check timeout per reset automatico
        if self.circuit_opened_at:
            elapsed = time.time() - self.circuit_opened_at
            if elapsed >= self.circuit_reset_timeout:
                self._close_circuit()
                return False

        return True

    def _check_circuit_breaker(self):
        """Apre circuit breaker se soglia fallimenti superata"""
        if not self.enable_circuit_breaker:
            return

        if self.consecutive_failures >= self.failure_threshold:
            self._open_circuit()

    def _open_circuit(self):
        """Apre il circuit breaker"""
        if not self.circuit_open:
            self.circuit_open = True
            self.circuit_opened_at = time.time()
            self.logger.warning(
                f"Circuit breaker APERTO dopo {self.consecutive_failures} fallimenti consecutivi. "
                f"Reset automatico tra {self.circuit_reset_timeout}s"
            )

    def _close_circuit(self):
        """Chiude il circuit breaker"""
        if self.circuit_open:
            self.circuit_open = False
            self.circuit_opened_at = None
            self.consecutive_failures = 0
            self.logger.info("Circuit breaker CHIUSO - servizio ripristinato")

    def get_stats(self) -> dict:
        """Restituisce statistiche chiamate"""
        success_rate = (
            (self.successful_calls / self.total_calls * 100)
            if self.total_calls > 0 else 0
        )

        return {
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'retried_calls': self.retried_calls,
            'success_rate': success_rate,
            'consecutive_failures': self.consecutive_failures,
            'circuit_open': self.circuit_open,
        }

    def reset_stats(self):
        """Reset statistiche"""
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.retried_calls = 0
        self.consecutive_failures = 0


# Esempio utilizzo
if __name__ == '__main__':
    # Test con decorator
    @retry_with_backoff(max_retries=3, initial_delay=0.5)
    def unreliable_api_call(fail_count=2):
        """Simula API che fallisce le prime N volte"""
        if not hasattr(unreliable_api_call, 'attempts'):
            unreliable_api_call.attempts = 0

        unreliable_api_call.attempts += 1

        if unreliable_api_call.attempts <= fail_count:
            print(f"  Tentativo {unreliable_api_call.attempts}: FALLITO")
            raise RetryableError("Service temporarily unavailable")

        print(f"  Tentativo {unreliable_api_call.attempts}: SUCCESSO")
        return {"data": "success"}

    print("Test retry decorator:")
    try:
        result = unreliable_api_call(fail_count=2)
        print(f"✅ Risultato: {result}")
    except Exception as e:
        print(f"❌ Errore: {e}")

    # Test con wrapper
    print("\nTest retry wrapper:")
    wrapper = APIRetryWrapper(max_retries=3)

    def another_api_call():
        raise RetryableError("Network error")

    try:
        wrapper.call(another_api_call)
    except Exception as e:
        print(f"❌ Errore: {e}")

    print(f"\nStatistiche: {wrapper.get_stats()}")
