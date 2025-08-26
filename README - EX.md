# GAB AssetMind - Portfolio Manager

Un'applicazione Python per il monitoraggio e la gestione di portafogli diversificati con interfaccia grafica moderna.

## 📊 Caratteristiche Principali

### Tipi di Asset Supportati
- **ETF**: Fondi indicizzati/attivi quotati in borsa
- **Azioni**: Titoli azionari singoli
- **Obbligazioni**: Governative, corporate, convertibili
- **Buoni del Tesoro**: BOT, BTP, CTZ, ecc.
- **PAC**: Piani di accumulo periodici su fondi/ETF
- **Criptovalute**: Bitcoin, Ethereum, stablecoin, ecc.
- **Liquidità**: Conti correnti, conti deposito, carte prepagate
- **Immobiliare**: Proprietà fisiche e quote di società immobiliari
- **Oggetti**: Automobili, gioielli, metalli preziosi, orologi di lusso

### Funzionalità
- ✅ Aggiunta, modifica ed eliminazione asset
- ✅ Categorizzazione automatica con filtri avanzati
- ✅ Grafici professionali (distribuzione categorie, rischio, performance)
- ✅ Export CSV/PDF con report dettagliati
- ✅ Persistenza dati in formato Excel
- ✅ Calcolo automatico performance e rendimenti
- ✅ Monitoraggio piani di accumulo
- ✅ Tracking redditi da investimenti e immobiliare

## 🚀 Installazione e Avvio

### Prerequisiti
- Python 3.8 o superiore
- pip (package manager Python)

### Installazione Automatica
```bash
# Clona o scarica il progetto
cd GAB_AssetMind

# Avvia l'applicazione (installerà automaticamente le dipendenze)
python run_app.py
```

### Installazione Manuale
```bash
# Installa le dipendenze
pip install -r requirements.txt

# Avvia l'applicazione
python main.py
```

## 📁 Struttura del Progetto

```
GAB_AssetMind/
├── main.py              # Applicazione principale con GUI
├── models.py            # Modelli dati e gestione Excel
├── export_utils.py      # Utilità per export PDF/CSV
├── run_app.py          # Script di avvio con controllo dipendenze
├── requirements.txt     # Dipendenze Python
├── portfolio_data.xlsx  # Database Excel (creato automaticamente)
└── README.md           # Documentazione
```

## 💾 Gestione Dati

L'applicazione utilizza un file Excel (`portfolio_data.xlsx`) come database. Il file viene creato automaticamente alla prima esecuzione con i seguenti campi:

| Campo | Descrizione |
|-------|-------------|
| Id | Identificativo univoco |
| category | Categoria asset (ETF, Azioni, etc.) |
| assetName | Nome dell'asset |
| position | Posizione/quantità |
| riskLevel | Livello di rischio (1-5) |
| ticker | Simbolo di borsa |
| isin | Codice ISIN |
| createdAt | Data di creazione |
| createdAmount | Quantità iniziale |
| createdUnitPrice | Prezzo unitario iniziale |
| createdTotalValue | Valore totale iniziale |
| updatedAt | Data ultimo aggiornamento |
| updatedAmount | Quantità attuale |
| updatedUnitPrice | Prezzo unitario attuale |
| updatedTotalValue | Valore totale attuale |
| accumulationPlan | Piano di accumulo |
| accumulationAmount | Importo accumulo mensile |
| incomePerYear | Reddito annuale |
| rentalIncome | Reddito immobiliare |
| note | Note personali |

## 🎨 Interfaccia Utente

L'applicazione presenta 4 tab principali:

### 1. Portfolio
- Visualizzazione tabellare di tutti gli asset
- Filtri per categoria
- Doppio click per modificare asset
- Sommario con valore totale e reddito annuale

### 2. Aggiungi Asset
- Form completo per inserimento nuovo asset
- Validazione automatica dati
- Calcolo automatico valori totali

### 3. Grafici
- Distribuzione per categoria (grafico a torta)
- Distribuzione del rischio (grafico a barre)
- Performance nel tempo (grafico a barre valori)

### 4. Export
- Export CSV con dati dettagliati
- Generazione report PDF professionale
- Backup del database Excel

## 📈 Report PDF

Il report PDF include:
- Sommario esecutivo con metriche principali
- Distribuzione asset per categoria
- Tabella dettagliata dei principali asset
- Formattazione professionale

## 🔧 Personalizzazione

### Aggiungere Nuove Categorie
Modifica la lista `categories` in `models.py`:
```python
self.categories = [
    "ETF", "Azioni", "Obbligazioni", "Buoni del Tesoro", 
    "PAC", "Criptovalute", "Liquidità", "Immobiliare", 
    "Oggetti", "La_Tua_Nuova_Categoria"
]
```

### Modificare Temi Colori
Cambia il tema in `main.py`:
```python
ctk.set_appearance_mode("dark")  # "light" o "dark"
ctk.set_default_color_theme("green")  # "blue", "green", "dark-blue"
```

## 🛠️ Dipendenze

- **customtkinter**: Interfaccia grafica moderna
- **matplotlib**: Generazione grafici
- **pandas**: Manipolazione dati Excel
- **openpyxl**: Lettura/scrittura file Excel
- **reportlab**: Generazione report PDF
- **tkcalendar**: Widget calendario
- **Pillow**: Gestione immagini
- **numpy**: Calcoli matematici

## 📊 Metriche Calcolate

L'applicazione calcola automaticamente:
- **Performance**: `(Valore Attuale - Valore Iniziale) / Valore Iniziale * 100`
- **Rendimento**: `Reddito Totale / Valore Attuale * 100`
- **Valore Corrente**: Utilizza `updatedTotalValue` se disponibile, altrimenti `createdTotalValue`
- **Reddito Totale**: Somma di `incomePerYear` + `rentalIncome`

## 🚀 Creazione Eseguibile

Per creare un eseguibile standalone:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

## 🐛 Troubleshooting

### Errore "Module not found"
```bash
pip install -r requirements.txt
```

### File Excel corrotto
L'applicazione ricreerà automaticamente il file `portfolio_data.xlsx` se mancante.

### Errori di visualizzazione grafici
Assicurati che matplotlib sia installato correttamente:
```bash
pip install matplotlib --upgrade
```

## 📝 Licenza

Questo progetto è rilasciato sotto licenza libera per uso personale.

---

**Sviluppato per la gestione professionale di portafogli diversificati** 🎯