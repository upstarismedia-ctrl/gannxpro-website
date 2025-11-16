# app.py - PROFESSIONAL GannXPro Web Version
import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
import math
import json
import time
from datetime import datetime
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

# ----------- NSE OPTION CHAIN HELPERS ----------- #
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
    ["Option Chain Pro", "Intraday Pro", "Signals & Greeks"],
    index=0
)

# Sidebar Info
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Quick Stats")
st.sidebar.info("""
**Live Features:**
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

# Option Chain Pro Tab
if app_mode == "Option Chain Pro":
    st.markdown('<div class="section-header">🔗 Option Chain Pro</div>', unsafe_allow_html=True)
    
    # Input Section
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            ticker = st.text_input("**Ticker Symbol**", "NIFTY", key="opt_ticker", 
                                 help="Enter NSE symbol like NIFTY, BANKNIFTY, RELIANCE")
        
        with col2:
            option_type = st.radio("**Instrument Type**", ["Index", "Stock"], horizontal=True)
        
        with col3:
            st.write("")  # spacer
            st.write("")  # spacer
            if st.button("📥 Fetch Chain", type="primary", use_container_width=True):
                with st.spinner("Fetching option chain data..."):
                    try:
                        is_index = (option_type == "Index")
                        if is_index:
                            oc_raw = fetch_option_chain_nse_index(ticker.upper())
                        else:
                            oc_raw = fetch_option_chain_nse_stock(ticker.upper())
                        
                        oc_parsed = parse_option_chain_response(oc_raw)
                        st.session_state.oc_parsed_cache = oc_parsed
                        st.session_state.oc_symbol_cache = ticker.upper()
                        
                        st.success("✅ Option chain data fetched successfully!")
                        
                    except Exception as e:
                        st.error(f"❌ Error fetching chain: {e}")

    # Display Basic Info
    if st.session_state.oc_parsed_cache:
        oc_data = st.session_state.oc_parsed_cache
        
        # Key Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("**Underlying Price**", f"₹{oc_data.get('underlying', 'N/A')}")
        with col2:
            st.metric("**Last Updated**", oc_data.get('lastUpdated', 'N/A')[:19] if oc_data.get('lastUpdated') else 'N/A')
        with col3:
            exp_count = len(oc_data["expiries"])
            st.metric("**Available Expiries**", exp_count)

        # Expiry Selection and Analysis
        expiries = sorted(list(oc_data["expiries"].keys()))
        
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_expiry = st.selectbox("**Select Expiry for Analysis**", expiries)
        
        with col2:
            st.write("")
            if st.button("🔍 Analyze Expiry", type="secondary", use_container_width=True):
                with st.spinner("Analyzing expiry data..."):
                    try:
                        score_data = enriched_option_buyer_score(
                            st.session_state.oc_symbol_cache, 
                            st.session_state.oc_parsed_cache, 
                            selected_expiry
                        )
                        
                        st.session_state.score_data = score_data

                    except Exception as e:
                        st.error(f"❌ Analyze error: {e}")

        # Display Analysis Results
        if 'score_data' in st.session_state:
            score_data = st.session_state.score_data
            
            st.markdown('<div class="section-header">📊 Option Buyer Analysis</div>', unsafe_allow_html=True)
            
            # Main Score Card
            col1, col2, col3, col4 = st.columns(4)
            score = score_data.get('score', 0)
            with col1:
                st.metric("**Overall Score**", f"{score}/100", 
                         delta="Strong" if score > 70 else "Moderate" if score > 50 else "Weak", 
                         delta_color="normal")
            
            pcr = score_data.get('components', {}).get('pcr', 0)
            with col2:
                if not math.isnan(pcr):
                    st.metric("**PCR (OI)**", f"{pcr:.2f}", 
                             delta="Bullish" if pcr < 0.7 else "Bearish" if pcr > 1.3 else "Neutral")
            
            maxpain = score_data.get('components', {}).get('maxpain', 0)
            with col3:
                if not math.isnan(maxpain):
                    st.metric("**Max Pain**", f"₹{maxpain:,.0f}")
            
            avg_iv = score_data.get('components', {}).get('avg_iv', 0)
            with col4:
                if avg_iv:
                    st.metric("**Avg IV**", f"{avg_iv:.1f}%")

            # Component Breakdown
            st.markdown("#### 📈 Component Breakdown")
            comps = score_data.get('components', {})
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Trend Score", comps.get('trend', 0), "/25")
            col2.metric("Pattern Score", comps.get('pattern', 0), "/12")
            col3.metric("Volume Score", comps.get('vol', 0), "/15")
            col4.metric("Chain Score", comps.get('chain', 0), "/20")

            # Suggested Strikes
            st.markdown("#### 🎯 Suggested Strikes")
            strikes = score_data.get('suggested_strikes', [])
            for strike in strikes:
                st.write(f"• {strike}")

# Intraday Pro Tab
elif app_mode == "Intraday Pro":
    st.markdown('<div class="section-header">📊 Intraday Pro</div>', unsafe_allow_html=True)
    
    # Input Section
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            ticker = st.text_input("**Ticker Symbol**", "BANKNIFTY", key="intra_ticker")
        
        with col2:
            period = st.selectbox("**Period**", ["1d", "5d", "1mo"], index=1)
        
        with col3:
            interval = st.selectbox("**Interval**", ["5m", "15m", "1h"], index=0)
        
        with col4:
            st.write("")
            st.write("")
            if st.button("📊 Analyze Intraday", type="primary", use_container_width=True):
                with st.spinner("Analyzing intraday data..."):
                    try:
                        df_i = fetch_intraday(ticker, period=period, interval=interval)
                        df_i = add_vwap_and_ema(df_i)
                        bias = option_bias_from_intraday(df_i)
                        last = df_i.iloc[-1]
                        
                        st.session_state.intraday_data = {
                            'bias': bias,
                            'last': last,
                            'ticker': ticker
                        }
                        
                    except Exception as e:
                        st.error(f"❌ Intraday error: {e}")

    # Display Results
    if 'intraday_data' in st.session_state:
        data = st.session_state.intraday_data
        
        # Key Metrics
        st.markdown("#### 📈 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("**Last Close**", f"₹{data['last']['Close']:.2f}")
        col2.metric("**VWAP**", f"₹{data['last']['VWAP']:.2f}")
        col3.metric("**EMA 9**", f"₹{data['last']['EMA9']:.2f}")
        col4.metric("**EMA 21**", f"₹{data['last']['EMA21']:.2f}")

        # Trading Signal
        st.markdown("#### 🎯 Trading Signal")
        bias = data['bias']
        if "BUY CE" in bias:
            st.markdown(f'<div class="signal-buy">🟢 {bias}</div>', unsafe_allow_html=True)
            st.info("**Interpretation:** Bullish trend detected. Consider long positions or call options.")
        elif "BUY PE" in bias:
            st.markdown(f'<div class="signal-sell">🔴 {bias}</div>', unsafe_allow_html=True)
            st.warning("**Interpretation:** Bearish trend detected. Consider short positions or put options.")
        else:
            st.markdown(f'<div class="signal-wait">🟡 {bias}</div>', unsafe_allow_html=True)
            st.info("**Interpretation:** Market is consolidating. Wait for clearer direction.")

        # Gann Timing Windows
        st.markdown("#### ⏰ Gann Intraday Reference Windows")
        gann_windows = [
            "• **09:15 – 09:45** | Open drive & initial trend",
            "• **10:00 – 10:30** | First reaction window", 
            "• **11:15 – 11:45** | Secondary reaction phase",
            "• **13:30 – 14:00** | Major reversal/continuation",
            "• **14:45 – 15:15** | Late-day momentum move"
        ]
        for window in gann_windows:
            st.write(window)

# Signals & Greeks Tab
else:
    st.markdown('<div class="section-header">⚡ Signals & Greeks</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🎯 Option Signals", "📊 Greeks Calculator"])
    
    with tab1:
        st.markdown("#### Generate Option Trading Signals")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            ticker = st.text_input("**Ticker Symbol**", "NIFTY", key="sig_ticker")
        
        with col2:
            st.write("")
            st.write("")
            if st.button("⚡ Generate Signal", type="primary", use_container_width=True):
                with st.spinner("Generating trading signal..."):
                    try:
                        df_s = fetch_intraday(ticker, period="1d", interval="5m")
                        df_s = add_vwap_and_ema(df_s)
                        bias = option_bias_from_intraday(df_s)
                        last = df_s.iloc[-1]
                        
                        st.session_state.signal_data = {
                            'bias': bias,
                            'last': last,
                            'ticker': ticker
                        }
                        
                    except Exception as e:
                        st.error(f"❌ Signal error: {e}")

        if 'signal_data' in st.session_state:
            data = st.session_state.signal_data
            
            st.success("✅ Signal generated successfully!")
            
            # Display Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("**Last Close**", f"₹{data['last']['Close']:.2f}")
            col2.metric("**VWAP**", f"₹{data['last']['VWAP']:.2f}")
            col3.metric("**EMA 9/21**", f"₹{data['last']['EMA9']:.2f}/₹{data['last']['EMA21']:.2f}")

            # Display Signal
            st.markdown("#### 🎯 Option Bias Signal")
            bias = data['bias']
            if "BUY CE" in bias:
                st.markdown(f'<div class="signal-buy">🟢 {bias}</div>', unsafe_allow_html=True)
            elif "BUY PE" in bias:
                st.markdown(f'<div class="signal-sell">🔴 {bias}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="signal-wait">🟡 {bias}</div>', unsafe_allow_html=True)
            
            st.info("""
            **💡 Trading Tip:** 
            - Combine this signal with option chain analysis for better accuracy
            - Consider market sentiment and news events
            - Always use proper risk management
            """)
    
    with tab2:
        st.markdown("#### Black-Scholes Greeks Calculator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Option Parameters**")
            S = st.number_input("**Underlying Price (S)**", value=20000.0, step=100.0, format="%.2f")
            K = st.number_input("**Strike Price (K)**", value=20000.0, step=100.0, format="%.2f")
            days = st.number_input("**Days to Expiry**", value=7, min_value=0, max_value=365, step=1)
        
        with col2:
            st.markdown("**Market Parameters**")
            iv_pct = st.number_input("**Implied Volatility %**", value=15.0, step=0.5, format="%.1f")
            r_pct = st.number_input("**Risk-Free Rate %**", value=6.0, step=0.1, format="%.1f")
            opt_type = st.selectbox("**Option Type**", ["CE", "PE"])
        
        if st.button("🧮 Calculate Greeks", type="primary", use_container_width=True):
            try:
                T = max(days, 0) / 365.0
                sigma = max(iv_pct, 0.001) / 100.0
                r = r_pct / 100.0
                option_type = "call" if opt_type == "CE" else "put"

                price = bs_price(S, K, T, r, sigma, option_type=option_type)
                greeks = bs_greeks(S, K, T, r, sigma, option_type=option_type)

                st.session_state.greeks_data = {
                    'price': price,
                    'greeks': greeks,
                    'inputs': {'S': S, 'K': K, 'days': days, 'iv': iv_pct, 'r': r_pct, 'type': opt_type}
                }

            except Exception as e:
                st.error(f"❌ Calculation error: {e}")

        if 'greeks_data' in st.session_state:
            data = st.session_state.greeks_data
            
            st.success("✅ Greeks calculated successfully!")
            
            # Display Results
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("**Theoretical Price**", f"₹{data['price']:.2f}")
            col2.metric("**Delta**", f"{data['greeks']['delta']:.4f}")
            col3.metric("**Theta/day**", f"{data['greeks']['theta']:.4f}")
            col4.metric("**Vega/1% IV**", f"{data['greeks']['vega']:.4f}")
            
            # Greeks Explanation
            st.markdown("#### 📖 Greeks Explanation")
            st.info("""
            **Delta:** Price change for ₹1 change in underlying  
            **Theta:** Daily time decay value  
            **Vega:** Price change for 1% change in IV  
            *Note: Calculations use Black-Scholes model approximations*
            """)

# Professional Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>GannXPro — AI-Powered Market Intelligence</strong></p>
    <p>📚 Educational Purpose Only | 🔒 Privacy First | ⚡ Real-time Data</p>
    <p>For analysis and learning. Not investment advice.</p>
</div>
""", unsafe_allow_html=True)
