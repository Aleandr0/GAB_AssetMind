# 📘 GAB AssetMind - Guida Utente Completa

**Versione**: 2.0 (Refactored)
**Data ultimo aggiornamento**: 2025-01-10

---

## 📑 Indice

1. [Introduzione](#introduzione)
2. [Installazione e Setup](#installazione-e-setup)
3. [Interfaccia Principale](#interfaccia-principale)
4. [Gestione Portfolio](#gestione-portfolio)
5. [Aggiornamento Prezzi](#aggiornamento-prezzi)
6. [Filtri e Ricerca](#filtri-e-ricerca)
7. [Grafici e Analisi](#grafici-e-analisi)
8. [Export e Report](#export-e-report)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

---

## 🎯 Introduzione

**GAB AssetMind** è un'applicazione professionale per la gestione del portfolio finanziario personale con:

✅ **Tracking Multi-Asset**: ETF, Azioni, Fondi, Criptovalute, Immobili, Liquidità
✅ **Aggiornamento Automatico Prezzi**: TwelveData + Yahoo Finance + BlackRock NAV
✅ **Analisi Visuale**: Grafici interattivi con allocazione e performance
✅ **Storico Completo**: Tracking evoluzione temporale asset
✅ **Export Avanzato**: PDF, Excel, CSV con report dettagliati

---

## 🚀 Installazione e Setup

### Requisiti Sistema

- **Python**: 3.9 o superiore
- **Sistema Operativo**: Windows 10/11, macOS, Linux
- **RAM**: Minimo 4GB (consigliato 8GB)
- **Spazio disco**: 500MB

### Installazione

```bash
# 1. Clona o scarica il repository
cd GAB_AssetMind

# 2. Installa dipendenze
pip install -r requirements.txt

# 3. (Opzionale) Configura API key TwelveData
# Crea file TWELVE_DATA_API_KEY.txt con la tua chiave
echo "your_api_key_here" > TWELVE_DATA_API_KEY.txt

# 4. Avvia l'applicazione
python main.py
# Oppure su Windows:
pythonw GAB_AssetMind.pyw
```

### Configurazione API TwelveData

Per aggiornamenti prezzi automatici:

1. Registrati su [TwelveData](https://twelvedata.com/) (piano gratuito: 8 req/min)
2. Copia la tua API key
3. Inserisci in `TWELVE_DATA_API_KEY.txt` o variabile ambiente `TWELVE_DATA_API_KEY`

**Nota**: Senza API key, puoi comunque inserire prezzi manualmente.

---

## 🖥️ Interfaccia Principale

### Barra Superiore (Navbar)

```
┌─────────────────────────────────────────────────────────────────┐
│ Valore Totale: €3,071,870.13                 Portfolio: ▼       │
│ Valore selezionato: €3,071,870.13 (100%)     [📊 Portfolio]    │
│ Record Totali: 47 — Asset Correnti: 41       [📝 Asset]        │
│                                                [📈 Grafici]      │
│                                                [📄 Export]       │
└─────────────────────────────────────────────────────────────────┘
```

#### Indicatori

- **Valore Totale**: Somma asset correnti (deduplicati)
- **Valore selezionato**: Somma elementi visibili (con filtri applicati)
- **Record Totali**: Numero record Excel (inclusi storici)
- **Asset Correnti**: Numero asset unici (deduplica automatica)

#### Navigazione

- **📊 Portfolio**: Tabella principale con asset
- **📝 Asset**: Form inserimento/modifica asset
- **📈 Grafici**: Visualizzazioni allocazione e performance
- **📄 Export**: Esportazione dati e report

---

## 💼 Gestione Portfolio

### Vista Portfolio

#### Toggle Record vs Asset

```
┌─────────────────────────────────────────────┐
│ [Record 47] [Asset 41] [🗑️ Pulisci Filtri]  │
└─────────────────────────────────────────────┘
```

- **Record**: Mostra TUTTI i record (inclusi storici) - utile per audit
- **Asset**: Mostra solo asset correnti (un record per asset) - vista standard

**Differenza**:
- Record 47 = Tutti gli aggiornamenti storici salvati
- Asset 41 = Numero effettivo asset in portfolio (alcuni hanno versioni multiple)

#### Colonne Tabella

| Colonna | Descrizione |
|---------|-------------|
| **ID** | Identificatore univoco record |
| **Category** | ETF, Azioni, Fondi, Crypto, Immobiliare, Liquidità |
| **Position** | Posizione/settore (Tech, Finance, Healthcare, etc.) |
| **Asset Name** | Nome completo asset |
| **ISIN** | Codice ISIN (identificatore internazionale) |
| **Ticker** | Simbolo mercato |
| **Risk Level** | Livello rischio 1-5 (1=basso, 5=alto) |
| **Created At** | Data creazione record |
| **Created Amount** | Quantità iniziale |
| **Created Unit Price** | Prezzo unitario iniziale |
| **Created Total Value** | Valore totale iniziale |
| **Updated At** | Data ultimo aggiornamento |
| **Updated Amount** | Quantità corrente |
| **Updated Unit Price** | Prezzo unitario corrente |
| **Updated Total Value** | Valore totale corrente |
| **Accumulation Plan** | Piano accumulo (PAC) |
| **Accumulation Amount** | Importo mensile PAC |
| **Income Per Year** | Reddito annuale (dividendi, cedole) |
| **Rental Income** | Rendita immobiliare |
| **Note** | Note libere |

#### Colorazione Record

- **Bianco**: Record corrente (più recente)
- **Azzurro chiaro**: Record storico (versione precedente)
- **Giallo**: Alert variazione prezzo >20%
- **Rosso**: Errore aggiornamento

### Inserimento Nuovo Asset

1. Click **📝 Asset** nella navbar
2. Compila form:
   - **Category** (obbligatorio): Seleziona tipo asset
   - **Asset Name** (obbligatorio): Nome descrittivo
   - **ISIN**: Codice ISIN (consigliato per aggiornamenti automatici)
   - **Ticker**: Simbolo mercato
   - **Amount**: Quantità posseduta
   - **Unit Price**: Prezzo unitario corrente
3. Click **💾 Salva Asset**

**Tip**: Per asset con aggiornamento prezzi automatico, inserisci sempre ISIN o Ticker valido.

### Modifica Asset Esistente

1. Nella tabella Portfolio, **doppio-click** sulla riga asset
2. Form si apre con dati correnti precompilati
3. Modifica campi desiderati
4. Click **💾 Salva Asset**

**Importante**: La modifica crea un NUOVO record (storico), mantenendo il vecchio per audit.

### Duplica Asset

1. Seleziona asset nella tabella
2. Click **📋 Duplica Asset**
3. Modifica dati nel form
4. Salva

**Uso tipico**: Stesso ETF acquistato in date diverse a prezzi diversi.

### Elimina Asset

1. Seleziona asset nella tabella
2. Click **🗑️ Elimina Asset**
3. Conferma eliminazione

**ATTENZIONE**: Elimina SOLO il record selezionato, non tutti i record storici.

---

## 🔄 Aggiornamento Prezzi

### Aggiornamento Automatico

```
┌─────────────────────────────────────────┐
│ [🔁 Aggiorna Prezzi]                    │
└─────────────────────────────────────────┘
```

1. Click **🔁 Aggiorna Prezzi**
2. Il sistema aggiorna automaticamente:
   - ETF (via TwelveData/Yahoo)
   - Azioni (via TwelveData/Yahoo)
   - Fondi (via BlackRock NAV/TwelveData)
   - Crypto (via TwelveData)
3. Visualizza report dettagliato con:
   - ✅ Successi
   - ⚠️ Alert variazioni significative
   - ❌ Errori

#### Alert Variazioni

Il sistema rileva automaticamente:

- **🟡 Warning**: Variazione >20% <50%
  - Azione: Verifica consigliata

- **🔴 Critico**: Variazione >50%
  - Azione: **Verifica obbligatoria** - probabile split o errore

- **🔄 Split**: Pattern split rilevato (es. 1:4, 2:1)
  - Azione: Conferma su sito emittente, aggiorna record storici

#### Rate Limiting

✅ **Implementato automaticamente** (v2.0+)

- Piano Free TwelveData: 8 richieste/minuto
- Sistema fa pausa automatica ogni 8 asset
- Evita errori "rate limit exceeded"

### Aggiornamento Manuale

Se aggiornamento automatico non disponibile:

1. Doppio-click su asset
2. Aggiorna manualmente:
   - **Updated Unit Price**: Nuovo prezzo
   - **Updated Amount**: Quantità corrente
   - **Updated At**: Data aggiornamento
3. Salva

**Nota**: Il sistema calcola automaticamente `Updated Total Value = Amount × Unit Price`.

---

## 🔍 Filtri e Ricerca

### Filtri Colonna

```
Click su header colonna → Apre popup filtro
┌──────────────────────┐
│ Filter by Category   │
├──────────────────────┤
│ Search...            │
├──────────────────────┤
│ ☑ ETF                │
│ ☑ Azioni             │
│ ☐ Fondi investimento │
│ ☑ Criptovalute       │
├──────────────────────┤
│ [Applica]  [Annulla] │
└──────────────────────┘
```

#### Come Usare

1. **Click header colonna** (es. "Category")
2. Seleziona valori da visualizzare
3. Click **Applica**
4. Header mostra `**` per indicare filtro attivo

#### Filtri Multipli

Puoi applicare filtri su **colonne diverse contemporaneamente**:

- Category = "ETF"
- **AND** Position = "Tech"
- **AND** Risk Level = "3"

Tutti i filtri sono in **AND logic**.

#### Pulisci Filtri

Click **🗑️ Pulisci Filtri** per rimuovere tutti i filtri attivi.

**Importante Fix (v2.0)**: Ora pulendo filtri si aggiornano automaticamente anche grafici e valori navbar!

### Zoom Tabella

```
┌────────────────────┐
│ Zoom: [-] 100% [+] │
└────────────────────┘
```

- **-**: Riduci dimensione font (min 70%)
- **+**: Aumenta dimensione font (max 150%)

Utile per:
- Schermi piccoli → Zoom out per vedere più colonne
- Presentazioni → Zoom in per leggibilità

---

## 📊 Grafici e Analisi

### Grafici Disponibili

#### 1. Allocazione per Categoria

Torta che mostra % valore per categoria:

```
ETF: 45%
Azioni: 25%
Fondi: 15%
Crypto: 10%
Liquidità: 5%
```

#### 2. Allocazione per Posizione

Torta che mostra % valore per settore/posizione:

```
Tech: 30%
Finance: 20%
Healthcare: 15%
Energy: 10%
...
```

#### 3. Distribuzione Rischio

Barre che mostrano valore per livello rischio:

```
Rischio 1 (Basso): €500K
Rischio 2: €800K
Rischio 3 (Medio): €1.2M
Rischio 4: €400K
Rischio 5 (Alto): €170K
```

#### 4. Top 10 Asset

Barre orizzontali con asset più grandi:

```
Asset A: €500K ████████████
Asset B: €450K ███████████
Asset C: €400K ██████████
...
```

#### 5. Evoluzione Temporale

Grafico linea che mostra valore portfolio nel tempo (basato su record storici).

### Interazione Grafici

- **Hover**: Mostra valori esatti
- **Filtri attivi**: Grafici si aggiornano automaticamente con dati filtrati
- **Export**: Click **📄 Export** → Salva grafici in PDF

---

## 📄 Export e Report

### Export Excel

```
┌─────────────────────────────────────┐
│ [📊 Esporta Excel]                  │
└─────────────────────────────────────┘
```

Crea file Excel con:
- **Sheet "Portfolio"**: Tutti gli asset correnti
- **Sheet "Summary"**: Statistiche aggregate
- **Sheet "Categories"**: Breakdown per categoria
- Formattazione professionale con colori

### Export PDF

```
┌─────────────────────────────────────┐
│ [📄 Esporta PDF Report]             │
└─────────────────────────────────────┘
```

Report PDF completo con:
- **Copertina** con logo e data
- **Summary**: Valore totale, numero asset, diversificazione
- **Grafici**: Tutti i 5 grafici embedded
- **Tabella dettagliata**: Asset ordinati per valore
- **Footer**: Paginazione e timestamp

**Perfetto per**: Condivisione con consulenti, presentazioni, archivio annuale.

### Export CSV

Esporta dati grezzi in CSV per analisi esterna (Excel, Python, R).

---

## 🔧 Troubleshooting

### Problema: Valore Totale ≠ Valore Selezionato

**Sintomo**: Nella navbar, "Valore selezionato" diverso da "Valore Totale"

**Causa**: Filtri attivi o visualizzazione Record vs Asset

**Soluzione**:
1. Verifica se ci sono filtri attivi (header con `**`)
2. Click **🗑️ Pulisci Filtri**
3. Assicurati di essere in modalità **Asset** (non Record)

### Problema: Aggiornamento Prezzi Fallisce

**Sintomo**: Errore "rate limit exceeded" o "HTTP 503"

**Soluzioni**:

#### Rate Limit (8 req/min superato)
- ✅ **Fix v2.0**: Rate limiting automatico implementato
- Riprova dopo 1 minuto
- Se persiste, verifica API key TwelveData

#### HTTP 503 (Servizio temporaneamente non disponibile)
- Attendi 5-10 minuti
- Riprova aggiornamento
- Se persiste >1 ora, controlla stato servizio su [TwelveData Status](https://status.twelvedata.com/)

#### Simbolo non trovato
- Verifica ISIN/Ticker su Google Finance
- Provider potrebbe aver cambiato simbolo
- Usa aggiornamento manuale temporaneamente

### Problema: Variazione Prezzo Anomala

**Sintomo**: Alert "Variazione +310%" o simile

**Cause comuni**:
1. **Split azionario**: Azione divisa (es. 1:4 split)
2. **Cambio valuta**: Provider cambiato da EUR a USD
3. **Errore dati**: Provider restituito dato errato

**Azione**:
1. Verifica su [Google Finance](https://www.google.com/finance)
2. Controlla corporate actions su sito emittente
3. Se split confermato:
   - Accetta nuovo prezzo
   - Considera aggiornare record storici manualmente
4. Se errore:
   - Modifica manualmente asset
   - Inserisci prezzo corretto
   - Aggiungi nota "PRICE CORRECTED MANUALLY"

### Problema: File Excel Corrotto

**Sintomo**: Errore all'avvio o al salvataggio

**Soluzione**:
1. Chiudi l'applicazione
2. Vai nella cartella `backups/`
3. Trova backup più recente (formato: `portfolio_data_backup_YYYYMMDD_HHMMSS.xlsx`)
4. Copia e rinomina in `portfolio_data.xlsx`
5. Riavvia applicazione

**Prevenzione**: I backup sono automatici ad ogni salvataggio.

### Problema: Grafico Non Si Aggiorna

**Sintomo**: Dopo pulire filtri, grafico mostra ancora dati vecchi

**Soluzione**:
- ✅ **Risolto in v2.0**: Callback `filters_changed` ora notifica correttamente
- Se persiste: Cambia pagina e torna a "Grafici"

---

## ❓ FAQ

### Domande Generali

**Q: Posso gestire più portfolio?**
A: Sì! Usa il dropdown "Portfolio:" nella navbar per:
- Selezionare portfolio esistente
- Click **+** per creare nuovo portfolio
- Ogni portfolio è un file Excel separato

**Q: I dati sono sicuri?**
A: Sì:
- Dati salvati localmente sul tuo computer
- Backup automatici in `backups/`
- Nessun dato inviato a server esterni (eccetto API prezzi)
- File Excel può essere protetto con password (Excel feature)

**Q: Posso usare senza connessione internet?**
A: Parzialmente:
- ✅ Visualizzazione portfolio: Sì
- ✅ Inserimento/modifica manuale: Sì
- ✅ Grafici e report: Sì
- ❌ Aggiornamento automatico prezzi: No (richiede API)

### Domande Tecniche

**Q: Quale Python version è supportata?**
A: Python 3.9+ (consigliato 3.10 o 3.11)

**Q: Posso personalizzare le categorie?**
A: Sì, modifica `AssetConfig.ASSET_CATEGORIES` in `config.py`

**Q: Come cambio threshold alert variazioni?**
A: Modifica `WARNING_THRESHOLD` e `CRITICAL_THRESHOLD` in `price_validation.py`

**Q: Posso aggiungere nuove valute?**
A: Sì, il sistema supporta qualsiasi valuta restituita da provider API

### Domande Avanzate

**Q: Come calcolo rendimento asset specifico?**
A: Usa il modulo `price_history.py`:
```python
from price_history import PriceHistoryTracker
tracker = PriceHistoryTracker(portfolio_manager)
report = tracker.generate_performance_report(asset_id=1)
print(report)
```

**Q: Posso schedulare aggiornamenti automatici?**
A: Non ancora implementato nativamente. Workaround:
- Windows: Task Scheduler
- macOS/Linux: cron job
- Script: `python -c "from models import PortfolioManager; pm = PortfolioManager(); pm.update_market_prices()"`

**Q: Come esporto dati per analisi Python/R?**
A: Usa `pandas` direttamente:
```python
import pandas as pd
df = pd.read_excel('portfolio_data.xlsx')
# Analizza con pandas, matplotlib, seaborn, etc.
```

---

## 📞 Supporto

### Documentazione

- **ARCHITECTURE.md**: Architettura tecnica
- **PRICE_UPDATE_ALERTS.md**: Gestione alert aggiornamenti
- **README.md**: Overview progetto

### Log e Debug

Log salvati in: `logs/assetmind.log`

Per debug dettagliato:
```bash
export GAB_DEBUG=true  # Linux/macOS
set GAB_DEBUG=true     # Windows
python main.py
```

### Segnalazione Bug

1. Verifica log in `logs/assetmind.log`
2. Annota:
   - Versione Python
   - Sistema operativo
   - Passi per riprodurre bug
3. Crea issue su repository GitHub (se disponibile)

---

## 🎓 Best Practices

### Gestione Quotidiana

✅ **DO**:
- Aggiorna prezzi 1 volta al giorno (sera, mercati chiusi)
- Verifica sempre alert >20% prima di accettare
- Usa backup regolari (già automatici)
- Annota modifiche manuali nel campo Note

❌ **DON'T**:
- Aggiornare prezzi più volte al giorno (stress API, dati poco utili)
- Ignorare alert critici (>50%)
- Modificare direttamente Excel (usa sempre l'app)
- Eliminare backup vecchi (<30 giorni)

### Organizzazione Portfolio

**Naming Convention Assets**:
- ETF: `[Emittente] [Indice] [Classe]` (es. "iShares MSCI World USD Acc")
- Azioni: `[Company Name]` o `[Ticker]` (es. "Apple Inc." o "AAPL")
- Crypto: `[Symbol]/[Fiat]` (es. "BTC/EUR")

**Uso Position Field**:
- Per ETF/Azioni: Settore (Tech, Finance, Healthcare, Consumer, Energy)
- Per Immobili: Città/Zona (Milano Centro, Roma EUR)
- Per Fondi: Strategia (Growth, Value, Income)

**Risk Level Guidelines**:
- **1**: Liquidità, Titoli di Stato AAA
- **2**: Obbligazioni Corporate IG, ETF Bond
- **3**: ETF Equity Large Cap, Blue Chips
- **4**: Azioni Mid/Small Cap, ETF Settoriali
- **5**: Crypto, Azioni speculative, Derivati

---

## 🔮 Roadmap Future Features

### In Sviluppo

- [ ] Scheduling automatico aggiornamenti (cron-like)
- [ ] Email/Push notifications per alert critici
- [ ] Mobile companion app (read-only)
- [ ] Cloud sync (opzionale, Dropbox/Google Drive)

### Pianificate

- [ ] Multi-currency con conversione automatica
- [ ] Tax report automatico (Capital Gains)
- [ ] Portfolio optimization suggestions (AI)
- [ ] Social features (confronto anonimo con altri utenti)

### Considerate

- [ ] Web app (alternativa desktop)
- [ ] Plugin marketplace
- [ ] API pubblica per integrazioni

---

**© 2025 GAB AssetMind v2.0**
*Gestione Portfolio Finanziario Professionale*

📧 Feedback: [Crea issue su GitHub]
⭐ Se ti piace il progetto, lascia una stella!
