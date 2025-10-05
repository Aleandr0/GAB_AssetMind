# 🚨 Gestione Alert Aggiornamento Prezzi

## Alert Rilevati nell'Ultimo Aggiornamento

### ⚠️ **VARIAZIONI ANOMALE DA VERIFICARE MANUALMENTE**

#### 1. **ID 15 (MWRD.PA) - Amundi MSCI World**
- **Variazione**: 33.04 → 135.66 EUR (+310.6%) 🔴 **CRITICO**
- **Probabile causa**:
  - Split azionario (1:4) o reverse split
  - Errore cambio valuta
  - Provider ha cambiato simbolo/classe
- **Azione consigliata**:
  1. Verifica su [Google Finance](https://www.google.com/finance/quote/MWRD:EPA)
  2. Controlla corporate actions su sito Amundi
  3. Se split confermato, aggiorna retroattivamente i record storici
  4. Se errore, ripristina valore precedente

#### 2. **ID 3 (VWCE.DE) - Vanguard FTSE All-World**
- **Variazione**: 323.13 → 140.5 EUR (-56.52%) 🔴 **CRITICO**
- **Probabile causa**:
  - Reverse split o cambio valuta EUR → USD
  - Errore provider (dato incompleto)
- **Azione consigliata**:
  1. Verifica su [Vanguard website](https://www.vanguard.de/)
  2. Confronta con [JustETF](https://www.justetf.com/de-en/etf-profile.html?isin=IE00BFZXGZ54)
  3. Correggi manualmente se errore confermato

#### 3. **ID 2 (CHIP.SW) - Amundi MSCI Semiconductors**
- **Variazione**: 49.15 → 75.13 USD (+52.86%) 🟡 **ATTENZIONE**
- **Probabile causa**:
  - Rally settore semiconductors (plausibile dato NVIDIA, AMD performance)
  - Cambio valuta CHF → USD
- **Azione consigliata**:
  1. Verifica se currency è cambiata (dovrebbe essere CHF)
  2. Confronta con indice MSCI Semiconductors

#### 4. **ID 11 (CSPX.L) - iShares Core S&P 500**
- **Variazione**: 562.05 → 715.08 USD (+27.23%) 🟡 **ATTENZIONE**
- **Probabile causa**:
  - Cambio valuta GBX (pence) → USD o GBP → USD
  - S&P 500 non è salito del 27% in breve periodo
- **Azione consigliata**:
  1. Verifica valuta corretta (dovrebbe essere GBP o GBX)
  2. Controlla se provider restituisce USD invece di GBP

---

## ❌ **ERRORI API DA RISOLVERE**

### 1. **ID 16 (LU0171310955) - BlackRock NAV HTTP 503**
- **Errore**: Servizio temporaneamente non disponibile
- **Soluzione**:
  - Retry automatico nel prossimo aggiornamento
  - Se persiste, verificare se BlackRock ha cambiato endpoint API

### 2. **ID 46 - TwelveData Rate Limit Exceeded**
- **Errore**: "You have run out of API credits for the current minute. 18 API credits were used, with the current limit being 8"
- **Causa**: Troppi asset aggiornati contemporaneamente
- **Soluzione IMPLEMENTATA**: ✅
  - Rate limiting ora attivo in `_maybe_pause()`
  - Pausa automatica di 8 secondi ogni 8 richieste
  - Nel prossimo aggiornamento non dovrebbe ripetersi

---

## 🔧 **CONFIGURAZIONE RATE LIMITING**

### Implementazione Corrente
```python
# models.py:327-347
REQUESTS_PER_MINUTE = 8  # TwelveData Free Plan limit
PAUSE_SECONDS = 8        # Pausa sicura tra batch

# Pausa automatica ogni 8 asset aggiornati
if row_position % 8 == 0:
    time.sleep(8)  # Attende 8 secondi
```

### Piani TwelveData
- **Free**: 8 req/min (480/ora) - **ATTUALE**
- **Basic**: 54 req/min ($7.99/mese)
- **Grow**: 300 req/min ($29.99/mese)
- **Pro**: 800 req/min ($79.99/mese)

---

## 📊 **BEST PRACTICES**

### Prima di Aggiornare
1. ✅ Controlla connessione internet
2. ✅ Verifica che non ci siano aggiornamenti recenti (<1 ora)
3. ✅ Fai backup del file Excel (automatico, ma verifica)

### Durante Aggiornamento
1. ✅ Non chiudere l'app durante il processo
2. ✅ Monitora gli alert in real-time
3. ✅ Annotare ID con variazioni >20%

### Dopo Aggiornamento
1. ✅ **VERIFICA SEMPRE alert variazioni >20%**
2. ✅ Controlla grafici per anomalie visive
3. ✅ Confronta valore portfolio totale con giorno precedente
4. ✅ Per variazioni sospette:
   - Cerca simbolo su Google Finance
   - Verifica corporate actions (split, dividendi)
   - Confronta con altre fonti (Bloomberg, Yahoo Finance)

---

## 🛠️ **COME CORREGGERE MANUALMENTE UN PREZZO ERRATO**

Se confermi che un prezzo è errato:

1. **Nella tabella Portfolio**, doppio-click sulla riga dell'asset
2. **Nel form modifica**, aggiorna:
   - `Updated Unit Price`: inserisci prezzo corretto
   - `Updated At`: mantieni data odierna
   - `Note`: aggiungi "PRICE CORRECTED MANUALLY - [motivo]"
3. **Salva**: Il sistema ricalcola automaticamente il `Updated Total Value`

---

## 📈 **MONITORING CONSIGLIATO**

### Alert da Monitorare
- ✅ Variazioni > ±20% → Verifica sempre
- ✅ Variazioni > ±50% → **CRITICO** - probabilmente errore o corporate action
- ✅ HTTP 503/504 → Retry dopo 5 minuti
- ✅ Rate limit → **ORA RISOLTO** con rate limiting automatico

### Frequenza Aggiornamenti Consigliata
- **ETF/Azioni**: 1 volta al giorno (mercati chiusi)
- **Criptovalute**: 2-4 volte al giorno (mercato 24/7)
- **Fondi**: 1 volta a settimana (NAV aggiornato lentamente)

---

## 🔄 **PROSSIMI MIGLIORAMENTI SUGGERITI**

1. ⏳ **Scheduling automatico** (aggiornamento notturno)
2. 📧 **Email alert** per variazioni >20%
3. 📊 **Storico prezzi** con grafici temporali
4. 🔄 **Retry automatico** per errori HTTP temporanei
5. 💾 **Cache prezzi** su database per analisi storiche

---

**Generato da**: GAB AssetMind v2.0
**Data**: 2025-01-10
**Rate Limiting**: ✅ ATTIVO (8 req/min)
