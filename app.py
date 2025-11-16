# app.py - GannXPro with Phase 1 Features
import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
import math
import json
import time
from datetime import datetime, timedelta
from math import log, sqrt, exp
from scipy.stats import norm

# Website setup with professional theme
st.set_page_config(
    page_title="GannXPro — AI-Powered Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .signal-buy {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 10px;
        font-weight: bold;
    }
    .signal-sell {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 10px;
        font-weight: bold;
    }
    .signal-wait {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 10px;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1f77b4;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #e9ecef;
        padding-bottom: 0.5rem;
    }
    .gann-level-up {
        background-color: #e8f5e8;
        border-left: 4px solid #28a745;
        padding: 0.5rem;
        margin: 0.2rem 0;
        border-radius: 5px;
    }
    .gann-level-down {
        background-color: #ffe8e8;
        border-left: 4px solid #dc3545;
        padding: 0.5rem;
        margin: 0.2rem 0;
        border-radius: 5px;
    }
    .gann-level-neutral {
        background-color: #fff9e8;
        border-left: 4px solid #ffc107;
        padding: 0.5rem;
        margin: 0.2rem 0;
        border-radius: 5px;
    }
    .market-up {
        color: #28a745;
        font-weight: bold;
    }
    .market-down {
        color: #dc3545;
        font-weight: bold;
    }
    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted black;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# Professional Header
st.markdown('<div class="main-header">📈 GannXPro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Market Intelligence Platform</div>', unsafe_allow_html=True)

# ----------- BASIC CONFIG ----------- #
HISTORY_YEARS = 2
SHORT_SMA = 20
LONG_SMA = 50

NSE_BASE = "https://www.nseindia.com"
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
})

# ----------- PHASE 1: NEW TECHNICAL INDICATORS ----------- #
def calculate_rsi(df, period=14):
    """Calculate Relative Strength Index (RSI)"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(df, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma = df['Close'].rolling(window=period).mean()
    std = df['Close'].rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band

def get_technical_indicators(df):
    """Calculate all technical indicators"""
    # RSI
    df['RSI'] = calculate_rsi(df)
    
    # MACD
    df['MACD'], df['MACD_Signal'], df['MACD_Histogram'] = calculate_macd(df)
    
    # Bollinger Bands
    df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = calculate_bollinger_bands(df)
    
    # Moving Averages
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['EMA_12'] = df['Close'].ewm(span=12).mean()
    df['EMA_26'] = df['Close'].ewm(span=26).mean()
    
    return df

# ----------- PHASE 1: MARKET DASHBOARD ----------- #
def get_nifty_components():
    """Get Nifty 50 components with current prices"""
    # Sample Nifty 50 components (you can expand this)
    nifty_stocks = {
        'RELIANCE.NS': 'Reliance',
        'TCS.NS': 'TCS',
        'HDFCBANK.NS': 'HDFC Bank',
        'INFY.NS': 'Infosys',
        'HINDUNILVR.NS': 'HUL',
        'ICICIBANK.NS': 'ICICI Bank',
        'KOTAKBANK.NS': 'Kotak Bank',
        'BHARTIARTL.NS': 'Airtel',
        'ITC.NS': 'ITC',
        'SBIN.NS': 'SBI',
        'ASIANPAINT.NS': 'Asian Paints',
        'DMART.NS': 'DMart',
        'BAJFINANCE.NS': 'Bajaj Finance',
        'WIPRO.NS': 'Wipro',
        'HCLTECH.NS': 'HCL Tech'
    }
    
    market_data = []
    for symbol, name in nifty_stocks.items():
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='1d')
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                prev_close = stock.info.get('previousClose', current)
                change = ((current - prev_close) / prev_close) * 100
                
                market_data.append({
                    'Symbol': symbol.replace('.NS', ''),
                    'Name': name,
                    'Price': current,
                    'Change': change,
                    'Volume': hist['Volume'].iloc[-1] if 'Volume' in hist else 0
                })
        except:
            continue
    
    return pd.DataFrame(market_data)

def get_sector_performance():
    """Get sector-wise performance"""
    sectors = {
        'BANKNIFTY': 'Banking',
        'NIFTY IT': 'IT',
        'NIFTY AUTO': 'Auto',
        'NIFTY FMCG': 'FMCG',
        'NIFTY PHARMA': 'Pharma',
        'NIFTY REALTY': 'Realty',
        'NIFTY METAL': 'Metal'
    }
    
    sector_data = []
    for symbol, name in sectors.items():
        try:
            ticker = symbol.replace(' ', '') + '.NS'
            stock = yf.Ticker(ticker)
            hist = stock.history(period='1d')
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                prev_close = stock.info.get('previousClose', current)
                change = ((current - prev_close) / prev_close) * 100
                
                sector_data.append({
                    'Sector': name,
                    'Change': change
                })
        except:
            continue
    
    return pd.DataFrame(sector_data)

# ----------- PHASE 1: EDUCATIONAL TOOLTIPS ----------- #
EDUCATIONAL_CONTENT = {
    'rsi': {
        'title': 'RSI (Relative Strength Index)',
        'description': 'Measures speed and change of price movements. Range: 0-100',
        'interpretation': '>70: Overbought, <30: Oversold, 50: Neutral'
    },
    'macd': {
        'title': 'MACD (Moving Average Convergence Divergence)',
        'description': 'Trend-following momentum indicator',
        'interpretation': 'MACD > Signal: Bullish, MACD < Signal: Bearish'
    },
    'bollinger': {
        'title': 'Bollinger Bands',
        'description': 'Volatility bands placed above and below moving average',
        'interpretation': 'Price near upper band: Overbought, near lower band: Oversold'
    },
    'pcr': {
        'title': 'Put-Call Ratio (PCR)',
        'description': 'Ratio of put volume to call volume',
        'interpretation': '>1: Bearish sentiment, <1: Bullish sentiment'
    },
    'vwap': {
        'title': 'VWAP (Volume Weighted Average Price)',
        'description': 'Average price weighted by volume',
        'interpretation': 'Price > VWAP: Bullish, Price < VWAP: Bearish'
    },
    'gann': {
        'title': 'Gann Analysis',
        'description': 'Technical analysis method using geometry and time cycles',
        'interpretation': 'Based on W.D. Gann theories of price and time relationships'
    }
}

def create_tooltip(term, text):
    """Create educational tooltip"""
    content = EDUCATIONAL_CONTENT.get(term, {})
    tooltip_html = f"""
    <div class="tooltip">
        {text}
        <span class="tooltiptext">
            <strong>{content.get('title', term)}</strong><br>
            {content.get('description', '')}<br>
            <em>{content.get('interpretation', '')}</em>
        </span>
    </div>
    """
    return tooltip_html

# ----------- GANN ANALYSIS FUNCTIONS ----------- #
def calculate_gann_levels(high, low, close):
    """Calculate Gann support and resistance levels"""
    pivot = (high + low + close) / 3
    r1 = (2 * pivot) - low
    s1 = (2 * pivot) - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    r3 = high + 2 * (pivot - low)
    s3 = low - 2 * (high - pivot)
    
    return {
        'pivot': pivot,
        'resistance': [r1, r2, r3],
        'support': [s1, s2, s3]
    }

def calculate_gann_angles(price, time_units=1):
    """Calculate Gann angles (1x1, 2x1, 1x2, etc.)"""
    angles = {
        '1x1': price * (1 + 1/8 * time_units/100),  # 45 degrees
        '2x1': price * (1 + 1/4 * time_units/100),  # 63.75 degrees
        '1x2': price * (1 + 1/16 * time_units/100), # 26.25 degrees
        '3x1': price * (1 + 3/8 * time_units/100),  # 71.25 degrees
        '1x3': price * (1 + 1/24 * time_units/100), # 18.75 degrees
    }
    return angles

def gann_square_of_nine(price):
    """Calculate Gann Square of Nine levels"""
    sqrt_price = math.sqrt(price)
    levels = []
    
    for i in range(-4, 5):
        level = (sqrt_price + i/2) ** 2
        levels.append(level)
    
    return sorted(levels)

def gann_time_cycles(current_date=None):
    """Calculate Gann time cycles and important dates"""
    if current_date is None:
        current_date = datetime.now()
    
    cycles = {
        'daily_important_times': [
            "09:15 - Market Open (Key Direction)",
            "10:00 - First Gann Time Window",
            "11:30 - Mid-day Reversal Point", 
            "13:30 - Major Gann Time Window",
            "14:45 - Late Day Movement",
            "15:15 - Last 15min (Settlement)"
        ],
        'weekly_cycles': [
            "Monday - Trend Setter Day",
            "Tuesday - Confirmation Day", 
            "Wednesday - Mid-week Reversal",
            "Thursday - Pre-Friday Movement",
            "Friday - Settlement & Close"
        ],
        'monthly_cycles': [
            "1st-7th: New Month Energy",
            "8th-15th: Mid-month Consolidation",
            "16th-23rd: Trend Continuation",
            "24th-EOM: Final Week Volatility"
        ]
    }
    return cycles

def gann_trading_signal(price_data, current_price):
    """Generate Gann-based trading signals"""
    if len(price_data) < 20:
        return "Insufficient data for Gann analysis"
    
    high_20 = max(price_data[-20:])
    low_20 = min(price_data[-20:])
    close = current_price
    
    gann_levels = calculate_gann_levels(high_20, low_20, close)
    
    # Check current price against Gann levels
    support_levels = gann_levels['support']
    resistance_levels = gann_levels['resistance']
    
    if close >= resistance_levels[0]:
        return "🟢 STRONG BULLISH - Above R1"
    elif close <= support_levels[0]:
        return "🔴 STRONG BEARISH - Below S1" 
    elif close > gann_levels['pivot']:
        return "🟡 MILD BULLISH - Above Pivot"
    elif close < gann_levels['pivot']:
        return "🟡 MILD BEARISH - Below Pivot"
    else:
        return "⚪ NEUTRAL - At Pivot Point"

# ----------- EXISTING NSE OPTION CHAIN HELPERS ----------- #
def nse_get(path: str, params=None, retries: int = 3, backoff: float = 1.0):
    """Call NSE endpoint with caching."""
    url = NSE_BASE + path
    cache_key = f"{url}::{json.dumps(params, sort_keys=True) if params else ''}"

    if not hasattr(nse_get, "_cache"):
        nse_get._cache = {}
    cache = nse_get._cache

    if cache_key in cache:
        data, ts = cache[cache_key]
        if time.time() - ts < 60:
            return data

    for i in range(retries):
        try:
            r = SESSION.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                cache[cache_key] = (data, time.time())
                return data
            time.sleep(backoff * (i + 1))
        except Exception:
            time.sleep(backoff * (i + 1))

    raise RuntimeError(f"NSE GET failed for {path}")

def fetch_option_chain_nse_index(symbol: str):
    path = f"/api/option-chain-indices?symbol={symbol}"
    return nse_get(path)

def fetch_option_chain_nse_stock(symbol: str):
    path = f"/api/option-chain-equities?symbol={symbol}"
    return nse_get(path)

def parse_option_chain_response(resp):
    """Convert NSE JSON into compact dict."""
    result = {"expiries": {}, "underlying": None, "lastUpdated": None}
    records = resp.get("records") or resp

    try:
        underlying = (
            records.get("underlyingValue")
            or records.get("underlyingVal")
            or records.get("underlying")
        )
        result["underlying"] = underlying
    except Exception:
        result["underlying"] = None

    if "data" in records:
        rows = records["data"]
    else:
        rows = records.get("records", {}).get("data", [])

    result["lastUpdated"] = records.get("timestamp") or records.get("records", {}).get("timestamp")

    for r in rows:
        exp = r.get("expiryDate") or r.get("expiry") or "UNKNOWN"
        if exp not in result["expiries"]:
            result["expiries"][exp] = []
        result["expiries"][exp].append(r)
    return result

def compute_pcr_by_oi(oc, expiry: str) -> float:
    rows = oc["expiries"].get(expiry, [])
    if not rows:
        return float("nan")
    call_oi, put_oi = 0.0, 0.0
    for r in rows:
        ce = r.get("CE") or r.get("call")
        pe = r.get("PE") or r.get("put")
        if ce and isinstance(ce, dict):
            call_oi += float(ce.get("openInterest") or 0)
        if pe and isinstance(pe, dict):
            put_oi += float(pe.get("openInterest") or 0)
    return (put_oi / call_oi) if call_oi > 0 else float("nan")

def compute_max_pain(oc, expiry: str) -> float:
    rows = oc["expiries"].get(expiry, [])
    if not rows:
        return float("nan")
    strikes = sorted({
        r.get("strikePrice") or r.get("strike")
        for r in rows
        if r.get("strikePrice") or r.get("strike")
    })
    candidate_scores = {}
    for s in strikes:
        total = 0.0
        for r in rows:
            strike = r.get("strikePrice") or r.get("strike")
            ce = r.get("CE") or r.get("call")
            pe = r.get("PE") or r.get("put")
            oi_call = float(ce.get("openInterest") or 0) if ce else 0.0
            oi_put = float(pe.get("openInterest") or 0) if pe else 0.0
            total += abs(strike - s) * (oi_call + oi_put)
        candidate_scores[s] = total
    if not candidate_scores:
        return float("nan")
    return min(candidate_scores.items(), key=lambda x: x[1])[0]

# ----------- PRICE / HISTORY HELPERS ----------- #
def normalize_ticker_yf(t: str) -> str:
    t = t.strip().upper()
    if t in ("NIFTY", "NIFTY50"):
        return "^NSEI"
    if t in ("BANKNIFTY", "BANK NIFTY"):
        return "^NSEBANK"
    if "." not in t and not t.startswith("^"):
        t = t + ".NS"
    return t

def fetch_history(ticker: str, years: int = HISTORY_YEARS):
    tk = normalize_ticker_yf(ticker)
    df = yf.Ticker(tk).history(period=f"{int(years * 365)}d", auto_adjust=False)
    if df.empty:
        raise RuntimeError("No history from yfinance")
    df.index = pd.to_datetime(df.index).normalize()
    return df

def detect_candle_patterns(df: pd.DataFrame):
    out = []
    if len(df) < 3:
        return out
    last = df.tail(3)
    c, o, h, l = (
        last["Close"].iloc[-1],
        last["Open"].iloc[-1],
        last["High"].iloc[-1],
        last["Low"].iloc[-1],
    )
    body = abs(c - o)
    rng = h - l
    if rng > 0 and (body / rng) < 0.12:
        out.append("Doji")
    if min(o, c) - l > 2 * body:
        out.append("Hammer")
    a = last.iloc[-2]
    b = last.iloc[-1]
    if (
        (a["Close"] < a["Open"])
        and (b["Close"] > b["Open"])
        and ((b["Close"] - b["Open"]) > (a["Open"] - a["Close"]))
    ):
        out.append("Bullish Engulfing")
    return out

def suggest_strikes(price: float, ticker: str):
    raw = ticker.upper()
    step = 0.005 if "NIFTY" in raw else 0.02
    out = [f"ATM ~ {round(price, 2)}"]
    for k in (1, 2):
        out.append(f"+{k} OTM ~ {round(price * (1 + step * k), 2)}")
    return out

def enriched_option_buyer_score(ticker: str, oc_parsed, expiry: str | None):
    """Combine trend + patterns + volume + chain into score 0–100."""
    out = {"ticker": ticker, "score": 0, "components": {}, "expiry": expiry}
    try:
        df = fetch_history(ticker)
    except Exception as e:
        out["error"] = f"no-data:{e}"
        return out

    # Trend
    try:
        s_short = df["Close"].rolling(window=SHORT_SMA).mean().iloc[-1]
        s_long = df["Close"].rolling(window=LONG_SMA).mean().iloc[-1]
        trend_comp = 25 if s_short > s_long else (10 if s_short == s_long else 0)
    except Exception:
        trend_comp = 10

    # Candle patterns
    pats = detect_candle_patterns(df)
    pat_comp = 12 if "Bullish Engulfing" in pats else (8 if "Hammer" in pats else 0)

    # Volume
    vol_ratio = (
        df["Volume"].iloc[-1] / max(1.0, df["Volume"].tail(50).mean())
        if "Volume" in df.columns
        else 1.0
    )
    vol_comp = min(15, int((vol_ratio - 1.0) * 10)) if vol_ratio > 1.0 else 0

    # Chain
    chain_comp = 0
    pcr = None
    maxpain = None
    avg_iv = None

    if oc_parsed and expiry:
        try:
            pcr = compute_pcr_by_oi(oc_parsed, expiry)
            if not math.isnan(pcr):
                pcr_clamped = min(max(pcr, 0.1), 5.0)
                chain_comp += int((1 - min(pcr_clamped / 5.0, 1.0)) * 20)
            maxpain = compute_max_pain(oc_parsed, expiry)
            rows = oc_parsed["expiries"].get(expiry, [])
            ivs = []
            for r in rows:
                ce = r.get("CE") or r.get("call")
                pe = r.get("PE") or r.get("put")
                if ce and isinstance(ce, dict):
                    v = ce.get("impliedVolatility") or ce.get("iv")
                    if v:
                        ivs.append(float(v))
                if pe and isinstance(pe, dict):
                    v = pe.get("impliedVolatility") or pe.get("iv")
                    if v:
                        ivs.append(float(v))
            if ivs:
                avg_iv = float(np.nanmean(ivs))
                iv_score = int((1 - min(avg_iv / 100.0, 1.0)) * 20)
                chain_comp += iv_score
        except Exception:
            pass

    total = trend_comp + pat_comp + vol_comp + chain_comp
    out["score"] = min(100, int(total))
    out["components"] = {
        "trend": trend_comp,
        "pattern": pat_comp,
        "vol": vol_comp,
        "chain": chain_comp,
        "pcr": pcr,
        "maxpain": maxpain,
        "avg_iv": avg_iv,
    }
    try:
        cur = float(df["Close"].iloc[-1])
        out["suggested_strikes"] = suggest_strikes(cur, ticker)
    except Exception:
        out["suggested_strikes"] = []
    return out

# ----------- INTRADAY HELPERS ----------- #
def fetch_intraday(ticker: str, period: str = "5d", interval: str = "5m"):
    tk = normalize_ticker_yf(ticker)
    df = yf.Ticker(tk).history(period=period, interval=interval)
    if df.empty:
        raise RuntimeError("No intraday data")
    return df

def add_vwap_and_ema(df: pd.DataFrame):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    df["VWAP"] = (tp * df["Volume"]).cumsum() / df["Volume"].cumsum()
    df["EMA9"] = df["Close"].ewm(span=9, adjust=False).mean()
    df["EMA21"] = df["Close"].ewm(span=21, adjust=False).mean()
    return df

def option_bias_from_intraday(df: pd.DataFrame) -> str:
    last = df.iloc[-1]
    price = last["Close"]
    vwap = last["VWAP"]
    ema9 = last["EMA9"]
    ema21 = last["EMA21"]

    up_trend = (price > vwap) and (ema9 > ema21)
    down_trend = (price < vwap) and (ema9 < ema21)

    if up_trend:
        return "BUY CE (Bullish intraday bias)"
    elif down_trend:
        return "BUY PE (Bearish intraday bias)"
    return "WAIT / NO CLEAR EDGE"

# ----------- BLACK–SCHOLES GREEKS ----------- #
def bs_price(S, K, T, r, sigma, option_type="call"):
    if T <= 0 or sigma <= 0:
        return max(0.0, (S - K) if option_type == "call" else (K - S))
    d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    if option_type == "call":
        return S * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
    else:
        return K * exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def bs_greeks(S, K, T, r, sigma, option_type="call"):
    if T <= 0 or sigma <= 0:
        return {"delta": 0, "theta": 0, "vega": 0}
    d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    delta = norm.cdf(d1) if option_type == "call" else (norm.cdf(d1) - 1)
    vega = S * norm.pdf(d1) * sqrt(T)
    theta = -(
        S * norm.pdf(d1) * sigma
    ) / (2 * sqrt(T)) - r * K * exp(-r * T) * (
        norm.cdf(d2) if option_type == "call" else -norm.cdf(-d2)
    )
    return {"delta": delta, "theta": theta / 365.0, "vega": vega / 100.0}

# ----------- STREAMLIT UI ----------- #
st.sidebar.header("🔧 Navigation")
app_mode = st.sidebar.radio(
    "Choose Analysis Mode",
    ["Market Dashboard", "Gann Analysis", "Option Chain Pro", "Intraday Pro", "Signals & Greeks"],
    index=0
)

# Sidebar Info
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Quick Stats")
st.sidebar.info("""
**Live Features:**
- Market Dashboard
- Gann Technical Analysis
- Real-time Option Chains
- Intraday Analysis  
- Trading Signals
- Greeks Calculator
""")

# Global cache
if 'oc_parsed_cache' not in st.session_state:
    st.session_state.oc_parsed_cache = None
if 'oc_symbol_cache' not in st.session_state:
    st.session_state.oc_symbol_cache = None

# ----------- PHASE 1: MARKET DASHBOARD TAB ----------- #
if app_mode == "Market Dashboard":
    st.markdown('<div class="section-header">📊 Live Market Dashboard</div>', unsafe_allow_html=True)
    
    # Market Overview
    st.subheader("🏦 Nifty 50 Overview")
    
    # Get market data
    with st.spinner("Loading market data..."):
        nifty_data = get_nifty_components()
        sector_data = get_sector_performance()
    
    if not nifty_data.empty:
        # Market Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_change = nifty_data['Change'].mean()
        advancers = len(nifty_data[nifty_data['Change'] > 0])
        decliners = len(nifty_data[nifty_data['Change'] < 0])
        volume = nifty_data['Volume'].sum()
        
        col1.metric("**Avg Change**", f"{total_change:.2f}%")
        col2.metric("**Advancers**", advancers)
        col3.metric("**Decliners**", decliners)
        col4.metric("**Total Volume**", f"{volume:,.0f}")
        
        # Top Gainers & Losers
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Top Gainers")
            gainers = nifty_data.nlargest(5, 'Change')[['Symbol', 'Name', 'Change', 'Price']]
            for _, stock in gainers.iterrows():
                change_color = "market-up" if stock['Change'] > 0 else "market-down"
                st.markdown(f"""
                <div class="metric-card">
                    <strong>{stock['Symbol']}</strong> - {stock['Name']}<br>
                    ₹{stock['Price']:.2f} | 
                    <span class="{change_color}">{stock['Change']:.2f}%</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.subheader("📉 Top Losers")
            losers = nifty_data.nsmallest(5, 'Change')[['Symbol', 'Name', 'Change', 'Price']]
            for _, stock in losers.iterrows():
                change_color = "market-up" if stock['Change'] > 0 else "market-down"
                st.markdown(f"""
                <div class="metric-card">
                    <strong>{stock['Symbol']}</strong> - {stock['Name']}<br>
                    ₹{stock['Price']:.2f} | 
                    <span class="{change_color}">{stock['Change']:.2f}%</span>
                </div>
                """, unsafe_allow_html=True)
        
        # Sector Performance
        st.subheader("🏭 Sector Performance")
        if not sector_data.empty:
            cols = st.columns(len(sector_data))
            for idx, (_, sector) in enumerate(sector_data.iterrows()):
                with cols[idx]:
                    change_color = "market-up" if sector['Change'] > 0 else "market-down"
                    st.metric(
                        sector['Sector'],
                        f"{sector['Change']:.2f}%",
                        delta_color="normal"
                    )
        
        # Technical Analysis for Nifty
        st.subheader("🔍 Nifty Technical Analysis")
        try:
            nifty_df = fetch_history('NIFTY', 0.5)  # 6 months data
            nifty_df = get_technical_indicators(nifty_df)
            
            last_row = nifty_df.iloc[-1]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                rsi = last_row['RSI']
                rsi_status = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
                st.metric(
                    st.markdown(create_tooltip('rsi', "**RSI**"), unsafe_allow_html=True),
                    f"{rsi:.1f}",
                    rsi_status
                )
            
            with col2:
                macd = last_row['MACD']
                macd_signal = last_row['MACD_Signal']
                macd_status = "Bullish" if macd > macd_signal else "Bearish"
                st.metric(
                    st.markdown(create_tooltip('macd', "**MACD**"), unsafe_allow_html=True),
                    f"{macd:.2f}",
                    macd_status
                )
            
            with col3:
                price = last_row['Close']
                bb_upper = last_row['BB_Upper']
                bb_lower = last_row['BB_Lower']
                bb_status = "High" if price > bb_upper else "Low" if price < bb_lower else "Normal"
                st.metric(
                    st.markdown(create_tooltip('bollinger', "**Bollinger**"), unsafe_allow_html=True),
                    bb_status
                )
            
            with col4:
                # Add option chain PCR if available
                try:
                    oc_data = fetch_option_chain_nse_index('NIFTY')
                    oc_parsed = parse_option_chain_response(oc_data)
                    expiries = sorted(list(oc_parsed["expiries"].keys()))
                    if expiries:
                        pcr = compute_pcr_by_oi(oc_parsed, expiries[0])
                        pcr_status = "Bullish" if pcr < 1 else "Bearish"
                        st.metric(
                            st.markdown(create_tooltip('pcr', "**PCR**"), unsafe_allow_html=True),
                            f"{pcr:.2f}",
                            pcr_status
                        )
                except:
                    st.metric("PCR", "N/A")
                    
        except Exception as e:
            st.error(f"Technical analysis error: {e}")

# Rest of the tabs remain the same but with added tooltips...
# [Gann Analysis, Option Chain Pro, Intraday Pro, Signals & Greeks tabs]

# For brevity, I'll show how to add tooltips to existing tabs:
elif app_mode == "Gann Analysis":
    st.markdown('<div class="section-header">🎯 Gann Technical Analysis</div>', unsafe_allow_html=True)
    
    # Add tooltip to Gann section
    st.markdown(create_tooltip('gann', "**Gann Analysis** - Advanced technical analysis using geometry and time cycles"), unsafe_allow_html=True)
    
    # [Rest of Gann Analysis code remains the same...]

elif app_mode == "Option Chain Pro":
    st.markdown('<div class="section-header">🔗 Option Chain Pro</div>', unsafe_allow_html=True)
    
    # Add tooltip to PCR
    st.markdown(create_tooltip('pcr', "**Put-Call Ratio Analysis**"), unsafe_allow_html=True)
    
    # [Rest of Option Chain code remains the same...]

elif app_mode == "Intraday Pro":
    st.markdown('<div class="section-header">📊 Intraday Pro</div>', unsafe_allow_html=True)
    
    # Add tooltip to VWAP
    st.markdown(create_tooltip('vwap', "**VWAP Analysis** - Volume Weighted Average Price"), unsafe_allow_html=True)
    
    # [Rest of Intraday code remains the same...]

else:  # Signals & Greeks
    st.markdown('<div class="section-header">⚡ Signals & Greeks</div>', unsafe_allow_html=True)
    
    # [Signals & Greeks code remains the same...]

# Professional Footer with educational links
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>GannXPro — AI-Powered Market Intelligence</strong></p>
    <p>📚 <strong>Educational Resources:</strong> 
    <em>Hover over technical terms for explanations</em> | 
    🔒 Privacy First | ⚡ Real-time Data</p>
    <p>For analysis and learning. Not investment advice.</p>
</div>
""", unsafe_allow_html=True)
