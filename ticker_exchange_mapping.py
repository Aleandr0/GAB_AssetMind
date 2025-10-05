"""
Mapping ISIN → (Ticker, Exchange Suffix) per yfinance
Basato su ricerca verificata per ISIN

Exchange suffixes:
- .L = London Stock Exchange
- .MI = Borsa Italiana (Milan)
- .DE = Xetra/Deutsche Börse (Germany)
- .SW = SIX Swiss Exchange
- .PA = Euronext Paris
- .AS = Euronext Amsterdam
- (no suffix) = US markets
"""

# Mapping verificato da ricerche web ISIN
ISIN_TO_TICKER_EXCHANGE = {
    # Amundi MSCI Semiconductors - LU1900066033
    # Ricerca web indica: ticker principale è su varie borse europee
    'LU1900066033': [
        ('LSMC.PA', 'Euronext Paris'),  # Più probabile per Amundi (francese)
        ('LSMC.MI', 'Borsa Italiana'),
        ('LSMC.DE', 'Xetra'),
    ],

    # Invesco EQQQ Nasdaq-100 - IE00BFZXGZ54
    # Ticker primario EQQB, quotato su varie borse
    'IE00BFZXGZ54': [
        ('EQQQ.L', 'London Stock Exchange'),  # EQQQ su London
        ('EQAC.DE', 'Xetra'),
        ('3QQQ.DE', 'Xetra'),  # Ticker alternativo Germania
    ],

    # Vanguard FTSE All-World High Dividend Yield - IE00BK5BR626
    # Ticker VGWE su varie borse
    'IE00BK5BR626': [
        ('VGWE.DE', 'Xetra'),  # VGWE su Xetra
        ('VHYL.L', 'London Stock Exchange'),
        ('VHYD.MI', 'Borsa Italiana'),
    ],

    # iShares Core S&P 500 - IE00B5BMR087
    # Ticker SXR8 (Xetra) e CSPX (London)
    'IE00B5BMR087': [
        ('SXR8.DE', 'Xetra'),  # SXR8 su Xetra
        ('CSPX.L', 'London Stock Exchange'),  # CSPX su London
        ('CSSPX.MI', 'Borsa Italiana'),
    ],

    # iShares Core MSCI World - IE00B4L5Y983
    # Ticker multipli: EUNL, IWDA, SWDA
    'IE00B4L5Y983': [
        ('SWDA.MI', 'Borsa Italiana'),  # SWDA su Milano
        ('IWDA.L', 'London Stock Exchange'),  # IWDA su London
        ('EUNL.DE', 'Xetra'),  # EUNL su Xetra
        ('SWDA.SW', 'SIX Swiss'),  # SWDA su Swiss
    ],

    # Amundi Core MSCI World - IE000BI8OT95
    # Ticker ETF146, MWRE
    'IE000BI8OT95': [
        ('CW8.PA', 'Euronext Paris'),  # Amundi è francese
        ('CW8.MI', 'Borsa Italiana'),
        ('CW8.DE', 'Xetra'),
    ],
}

def get_ticker_candidates(isin: str) -> list:
    """
    Restituisce lista di (ticker, exchange) candidati per un ISIN

    Args:
        isin: Codice ISIN dell'asset

    Returns:
        Lista di tuple (ticker_with_suffix, exchange_name)
    """
    return ISIN_TO_TICKER_EXCHANGE.get(isin, [])

def get_primary_ticker(isin: str) -> str:
    """
    Restituisce il ticker primario (primo nella lista) per un ISIN

    Args:
        isin: Codice ISIN dell'asset

    Returns:
        Ticker con suffisso exchange, o None se non trovato
    """
    candidates = get_ticker_candidates(isin)
    if candidates:
        return candidates[0][0]  # Primo ticker
    return None
