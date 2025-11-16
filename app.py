# app.py - COMPLETE GannXPro Web Version
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

# Website setup
st.set_page_config(
    page_title="GannXPro — AI-Powered Market Intelligence",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📈 GannXPro — AI-Powered Market Intelligence")
st.markdown("**Professional Option Chain, Intraday Analysis & Trading Signals**")

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

# ----------- STREAMLET UI ----------- #
st.sidebar.header("🔧 Navigation")
app_mode = st.sidebar.selectbox(
    "Choose Analysis Mode",
    ["Option Chain Pro", "Intraday Pro", "Signals & Greeks"]
)

# Global cache
if 'oc_parsed_cache' not in st.session_state:
    st.session_state.oc_parsed_cache = None
if 'oc_symbol_cache' not in st.session_state:
    st.session_state.oc_symbol_cache = None

# Option Chain Pro Tab
if app_mode == "Option Chain Pro":
    st.header("🔗 Option Chain Pro")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        ticker = st.text_input("Ticker:", "NIFTY", key="opt_ticker")
    
    with col2:
        option_type = st.radio("Type:", ["Index", "Stock"], horizontal=True)
    
    with col3:
        st.write("")  # spacer
        if st.button("Fetch Chain", type="primary"):
            with st.spinner("Fetching option chain..."):
                try:
                    is_index = (option_type == "Index")
                    if is_index:
                        oc_raw = fetch_option_chain_nse_index(ticker.upper())
                    else:
                        oc_raw = fetch_option_chain_nse_stock(ticker.upper())
                    
                    oc_parsed = parse_option_chain_response(oc_raw)
                    st.session_state.oc_parsed_cache = oc_parsed
                    st.session_state.oc_symbol_cache = ticker.upper()
                    
                    st.success("Option chain fetched successfully!")
                    
                    # Display basic info
                    col1, col2 = st.columns(2)
                    col1.metric("Underlying Price", f"₹{oc_parsed.get('underlying', 'N/A')}")
                    col2.metric("Last Updated", oc_parsed.get('lastUpdated', 'N/A'))
                    
                except Exception as e:
                    st.error(f"Error fetching chain: {e}")

    # Expiry selection and analysis
    if st.session_state.oc_parsed_cache:
        expiries = sorted(list(st.session_state.oc_parsed_cache["expiries"].keys()))
        
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_expiry = st.selectbox("Select Expiry:", expiries)
        
        with col2:
            st.write("")
            if st.button("Analyze Expiry", type="secondary"):
                with st.spinner("Analyzing expiry..."):
                    try:
                        score_data = enriched_option_buyer_score(
                            st.session_state.oc_symbol_cache, 
                            st.session_state.oc_parsed_cache, 
                            selected_expiry
                        )
                        
                        # Display analysis results
                        st.subheader("📊 Option Buyer Analysis")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Overall Score", f"{score_data.get('score', 0)}/100")
                        
                        pcr = score_data.get('components', {}).get('pcr', 0)
                        if not math.isnan(pcr):
                            col2.metric("PCR (OI)", f"{pcr:.2f}")
                        
                        maxpain = score_data.get('components', {}).get('maxpain', 0)
                        if not math.isnan(maxpain):
                            col3.metric("Max Pain", f"₹{maxpain}")
                        
                        avg_iv = score_data.get('components', {}).get('avg_iv', 0)
                        if avg_iv:
                            col4.metric("Avg IV", f"{avg_iv:.2f}%")
                        
                        # Component breakdown
                        st.subheader("Component Breakdown")
                        comps = score_data.get('components', {})
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Trend", comps.get('trend', 0))
                        col2.metric("Pattern", comps.get('pattern', 0))
                        col3.metric("Volume", comps.get('vol', 0))
                        col4.metric("Chain", comps.get('chain', 0))
                        
                        # Suggested strikes
                        st.subheader("🎯 Suggested Strikes")
                        strikes = score_data.get('suggested_strikes', [])
                        for strike in strikes:
                            st.write(f"- {strike}")
                            
                    except Exception as e:
                        st.error(f"Analyze error: {e}")

# Intraday Pro Tab
elif app_mode == "Intraday Pro":
    st.header("📊 Intraday Pro")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ticker = st.text_input("Ticker:", "BANKNIFTY", key="intra_ticker")
    
    with col2:
        period = st.selectbox("Period:", ["1d", "5d", "1mo"], index=1)
    
    with col3:
        interval = st.selectbox("Interval:", ["5m", "15m"], index=0)
    
    if st.button("Analyze Intraday", type="primary"):
        with st.spinner("Fetching intraday data..."):
            try:
                df_i = fetch_intraday(ticker, period=period, interval=interval)
                df_i = add_vwap_and_ema(df_i)
                bias = option_bias_from_intraday(df_i)
                last = df_i.iloc[-1]
                
                st.success("Intraday analysis complete!")
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Last Close", f"₹{last['Close']:.2f}")
                col2.metric("VWAP", f"₹{last['VWAP']:.2f}")
                col3.metric("EMA9", f"₹{last['EMA9']:.2f}")
                col4.metric("EMA21", f"₹{last['EMA21']:.2f}")
                
                # Display bias
                st.subheader("🎯 Intraday Bias")
                if "BUY CE" in bias:
                    st.success(f"**{bias}**")
                elif "BUY PE" in bias:
                    st.warning(f"**{bias}**")
                else:
                    st.info(f"**{bias}**")
                
                # Gann timing windows
                st.subheader("⏰ Gann Intraday Reference Windows")
                gann_windows = [
                    "• 09:15 – Open drive",
                    "• ~10:00 – First reaction window", 
                    "• ~11:15 – Secondary reaction",
                    "• ~13:30 – Major reversal / continuation",
                    "• ~14:45 – Late-day move"
                ]
                for window in gann_windows:
                    st.write(window)
                    
            except Exception as e:
                st.error(f"Intraday error: {e}")

# Signals & Greeks Tab
else:
    st.header("⚡ Signals & Greeks")
    
    tab1, tab2 = st.tabs(["Option Signals", "Greeks Calculator"])
    
    with tab1:
        st.subheader("Option Trading Signals")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            ticker = st.text_input("Ticker for Signal:", "NIFTY", key="sig_ticker")
        
        with col2:
            st.write("")
            if st.button("Generate Signal", type="primary"):
                with st.spinner("Generating signal..."):
                    try:
                        df_s = fetch_intraday(ticker, period="1d", interval="5m")
                        df_s = add_vwap_and_ema(df_s)
                        bias = option_bias_from_intraday(df_s)
                        last = df_s.iloc[-1]
                        
                        st.success("Signal generated!")
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Last Close", f"₹{last['Close']:.2f}")
                        col2.metric("VWAP", f"₹{last['VWAP']:.2f}")
                        col3.metric("EMA9/21", f"₹{last['EMA9']:.2f}/₹{last['EMA21']:.2f}")
                        
                        st.subheader("🎯 Option Bias")
                        st.info(f"**{bias}**")
                        
                        st.write("💡 **Note:** Always combine this with Option Chain + price action.")
                        
                    except Exception as e:
                        st.error(f"Signal error: {e}")
    
    with tab2:
        st.subheader("Black–Scholes Greeks Calculator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            S = st.number_input("S (Underlying):", value=20000.0, step=100.0)
            K = st.number_input("K (Strike):", value=20000.0, step=100.0)
            days = st.number_input("Days to Expiry:", value=7, min_value=0, max_value=365)
        
        with col2:
            iv_pct = st.number_input("IV %:", value=15.0, step=1.0)
            r_pct = st.number_input("Risk-free %:", value=6.0, step=0.5)
            opt_type = st.selectbox("Type:", ["CE", "PE"])
        
        if st.button("Calculate Greeks", type="primary"):
            try:
                T = max(days, 0) / 365.0
                sigma = max(iv_pct, 0.001) / 100.0
                r = r_pct / 100.0
                option_type = "call" if opt_type == "CE" else "put"

                price = bs_price(S, K, T, r, sigma, option_type=option_type)
                greeks = bs_greeks(S, K, T, r, sigma, option_type=option_type)

                st.success("Calculation complete!")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Theoretical Price", f"₹{price:.2f}")
                col2.metric("Delta", f"{greeks['delta']:.4f}")
                col3.metric("Theta/day", f"{greeks['theta']:.4f}")
                col4.metric("Vega/1% IV", f"{greeks['vega']:.4f}")
                
                st.info("💡 **Note:** Greeks are approximations. Use as guidance, not guarantee.")
                
            except Exception as e:
                st.error(f"Greeks error: {e}")

# Footer
st.markdown("---")
st.markdown("""
**📚 Educational Purpose Only**  
This tool is for learning and analysis. Not investment advice.

**🔒 Privacy First**  
We don't store your data or personal information.

**⚡ Real-time Data**  
Live market data from NSE and Yahoo Finance
""")
