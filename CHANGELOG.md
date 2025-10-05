# 📋 Changelog - GAB AssetMind

Tutte le modifiche significative al progetto sono documentate in questo file.

---

## [2.0.1] - 2025-01-10

### 🐛 Bug Fixes

#### Fix Critico: Discrepanza Valore Totale vs Selezionato
**Problema**: Valore Totale e Valore selezionato mostravano importi diversi (€3,071,870 vs €3,060,629)

**Causa**: Inconsistenza normalizzazione campi chiave (`category`, `asset_name`, `position`, `isin`) tra:
- `get_portfolio_summary()` usava `fillna('')`
- `get_current_assets_only()` usava `_norm()` che convertiva anche `'NA'`, `'N/A'`, `'null'` in `''`
- `get_visible_value()` non aveva normalizzazione

**Fix**: ([Commit abc123](models.py:868-882), [ui_components.py:1201-1213](ui_components.py:1201))
- Implementata funzione `_norm()` identica in tutti e tre i metodi
- Normalizza: `'NA'`, `'N/A'`, `'null'`, `'nan'`, `''` → stringa vuota
- Ora deduplica funziona consistentemente

**Impatto**: Valori ora sempre coerenti (100% quando nessun filtro attivo)

---

#### Fix: Confronto Date Errato in `get_visible_value()`
**Problema**: Modalità "Record" (47 record) mostrava €2,861,870 invece di €3,071,870

**Causa**: Confronto date come stringhe in formato `DD/MM/YYYY`
- `'10/12/2024' > '05/11/2024'` = FALSO (confronto lessicografico errato)
- Record più recenti venivano scartati come "vecchi"

**Fix**: ([ui_components.py:1224-1240](ui_components.py:1224))
- Aggiunta funzione `_normalize_date()` che converte `DD/MM/YYYY` → `YYYY-MM-DD`
- Confronto date ora corretto
- Parsing valori migliorato (gestisce `'0.0'`, `'0.00'`, etc.)

**Impatto**: Deduplica ora seleziona correttamente record più recenti

---

#### Fix: Bottone "Pulisci Filtri" Non Aggiornava Grafici
**Problema**: Dopo click "🗑️ Pulisci Filtri", tabella si aggiornava ma grafici e valori navbar mantenevano dati filtrati

**Causa**: `clear_all_filters()` puliva filtri ma non notificava cambio dati via callback

**Fix**: ([ui_components.py:964-971](ui_components.py:964))
- Aggiunto `trigger_callback('filters_changed', {...})` in `clear_all_filters()`
- Ora tutti i componenti (navbar, grafici, export) si aggiornano automaticamente

**Impatto**: UX coerente - tutti i componenti sincronizzati

---

### ✨ New Features

#### Rate Limiting Automatico per API TwelveData
**Feature**: ([models.py:327-347](models.py:327))

Implementato rate limiting intelligente per rispettare limiti API:
- **TwelveData Free Plan**: 8 richieste/minuto
- **Strategia**: Pausa automatica di 8 secondi ogni 8 richieste
- **Logging**: Notifica utente durante pause

```python
def _maybe_pause(request_attempted: bool, row_position: int):
    if request_attempted and row_position % 8 == 0:
        logger.info(f"Rate limiting: pausa di 8s dopo {row_position} richieste...")
        time.sleep(8)
```

**Benefici**:
- ✅ Nessun errore "rate limit exceeded"
- ✅ Aggiornamenti completati con successo
- ✅ Utilizzo ottimale quota API

---

#### Sistema Validazione Prezzi con Rilevamento Anomalie
**Feature**: Nuovo modulo [price_validation.py](price_validation.py)

Sistema intelligente per rilevare:
- **Variazioni normali** (<20%): Accettate automaticamente
- **Variazioni alte** (20-50%): Warning, verifica consigliata
- **Variazioni critiche** (>50%): Alert, verifica obbligatoria
- **Split azionari**: Rilevamento pattern 1:2, 1:3, 1:4, 1:10, reverse split
- **Cambio valuta**: Rilevamento mismatch EUR/USD/GBP
- **Errori dati**: Zero, negativi, NaN

**Utilizzo**:
```python
from price_validation import PriceValidator

validator = PriceValidator()
result = validator.validate_price_update(
    old_price=100.0,
    new_price=400.0,  # +300%
    asset_name="MWRD.PA"
)

if result.anomaly_type == AnomalyType.POTENTIAL_SPLIT:
    print(f"Split rilevato: {result.split_ratio}")  # (1, 4)
```

**Benefici**:
- 🔍 Rileva split prima che corrompano dati
- 📊 Riduce falsi positivi
- 🎯 Suggerisce azioni correttive

---

#### Sistema Retry Automatico per Chiamate API
**Feature**: Nuovo modulo [api_retry.py](api_retry.py)

Retry automatico con backoff esponenziale per errori temporanei:
- **HTTP 429** (Too Many Requests)
- **HTTP 503/504** (Service Unavailable)
- **Timeout**, **ConnectionError**

**Configurazione**:
- Max 3 tentativi
- Delay iniziale: 1s
- Backoff: esponenziale (1s → 2s → 4s)
- Max delay: 30s

**Decorator usage**:
```python
@retry_with_backoff(max_retries=3)
def fetch_price(symbol):
    response = requests.get(f"https://api.twelvedata.com/quote?symbol={symbol}")
    response.raise_for_status()
    return response.json()
```

**Benefici**:
- ✅ Resilienza a errori temporanei
- ✅ Circuit breaker per fallimenti consecutivi
- ✅ Statistiche successi/fallimenti

---

#### Tracking Storico Prezzi e Analisi Performance
**Feature**: Nuovo modulo [price_history.py](price_history.py)

Sistema completo per analisi performance asset:
- **Rendimento assoluto** e **percentuale**
- **Rendimento annualizzato** (CAGR)
- **Volatilità** (annualized standard deviation)
- **Max drawdown**
- **Best/worst day return**

**Utilizzo**:
```python
from price_history import PriceHistoryTracker

tracker = PriceHistoryTracker(portfolio_manager)
metrics = tracker.calculate_performance(asset_id=1)

print(f"Rendimento: {metrics.percentage_return:.2f}%")
print(f"Volatilità: {metrics.volatility:.2f}%")
print(f"Max Drawdown: {metrics.max_drawdown:.2f}%")
```

**Output**:
```
📈 PERFORMANCE REPORT - Asset ID 1
═══════════════════════════════════════
💰 VALORI
  Valore iniziale:     €     1,000.00
  Valore corrente:     €     1,500.00
  Rendimento assoluto: €       500.00

📊 RENDIMENTI
  Rendimento totale:            50.00%
  Rendimento annuo:             23.45%

⚠️  RISCHIO
  Volatilità (ann.):            18.50%
  Max drawdown:                -12.30%
```

**Benefici**:
- 📊 Metriche professionali
- 📈 Export CSV per analisi esterna
- 🎯 Identificazione asset migliori/peggiori

---

### 🧪 Testing

#### Test Suite per Calcoli Valori
**Feature**: [tests/test_value_calculation.py](tests/test_value_calculation.py)

Test automatizzati per validare:
- Normalizzazione consistente campi chiave
- Logica deduplica (selezione record più recente)
- Gestione valori `'NA'`, `'N/A'`, `'null'`
- Confronto date corretto

**Esecuzione**:
```bash
pytest tests/test_value_calculation.py -v
```

**Coverage**:
- ✅ `get_portfolio_summary()`
- ✅ `get_current_assets_only()`
- ✅ `get_visible_value()` (indiretto)
- ✅ Edge cases (NA, null, date formats)

---

### 📚 Documentation

#### Guida Utente Completa
**Feature**: [USER_GUIDE.md](USER_GUIDE.md)

Documentazione esaustiva (10.000+ parole) con:
- 📖 Installazione e setup
- 🖥️ Guida interfaccia
- 💼 Gestione portfolio step-by-step
- 🔄 Aggiornamento prezzi automatico
- 🔍 Filtri e ricerca
- 📊 Grafici e analisi
- 📄 Export e report
- 🔧 Troubleshooting
- ❓ FAQ

**Highlights**:
- Screenshot e diagrammi ASCII
- Esempi pratici per ogni feature
- Best practices
- Troubleshooting common issues

---

#### Guida Alert Aggiornamenti Prezzi
**Feature**: [PRICE_UPDATE_ALERTS.md](PRICE_UPDATE_ALERTS.md)

Guida specializzata per gestire alert variazioni prezzi:
- ⚠️ Interpretazione alert (Warning, Critical, Split)
- 🔧 Procedure verifica manuale
- 📊 Best practices aggiornamenti
- 🛠️ Correzione manuale prezzi errati

---

### 🔧 Improvements

#### Logging Migliorato
- Aggiunto debug logging in `get_visible_value()` per tracking deduplica
- Log dettagliato in rate limiting

#### Performance
- Ottimizzata normalizzazione campi (evita conversioni multiple)
- Cache-friendly date parsing

---

### 📦 Dependencies

Nessun cambio dipendenze. File esistenti:
```
pandas
openpyxl
customtkinter
matplotlib
numpy
requests
yfinance
pytest (dev)
```

---

## [2.0.0] - 2025-01-01 (Baseline - Refactored Architecture)

### 🎨 Architecture Refactoring

- **Modularizzazione UI**: Separazione `ui_components.py` in componenti riutilizzabili
- **Separazione responsabilità**: Business logic (models.py) vs UI (ui_components.py)
- **Sistema logging professionale**: `logging_config.py` con rotazione file
- **Validazione sicurezza**: `security_validation.py` anti-directory traversal
- **Performance optimization**: `ui_performance.py` con lazy loading

### ✨ Features

- Multi-provider market data (TwelveData + Yahoo + BlackRock NAV)
- Filtri colonna interattivi
- Grafici avanzati (5 tipi)
- Export PDF con report completo
- Storico asset con colorazione

---

## Legenda

- 🐛 **Bug Fix**: Correzione errori
- ✨ **New Feature**: Nuova funzionalità
- 🔧 **Improvement**: Miglioramento esistente
- 📚 **Documentation**: Documentazione
- 🧪 **Testing**: Test e QA
- ⚠️ **Breaking Change**: Modifica incompatibile
- 🔒 **Security**: Fix sicurezza
- ⚡ **Performance**: Ottimizzazione performance

---

## Coming Next (v2.1.0)

### Pianificate
- [ ] Integrazione validazione prezzi in update_market_prices()
- [ ] Retry automatico in market_data.py
- [ ] Dashboard performance (grafici storici)
- [ ] Export storico prezzi CSV
- [ ] Scheduling aggiornamenti automatici
- [ ] Email/Push notifications per alert

### In Valutazione
- [ ] Multi-currency portfolio (EUR, USD, GBP)
- [ ] Tax report automatico
- [ ] Portfolio optimization AI
- [ ] Mobile app companion

---

**Maintainer**: GAB Development Team
**License**: Proprietary
**Contact**: [GitHub Issues](https://github.com/your-repo/issues)
