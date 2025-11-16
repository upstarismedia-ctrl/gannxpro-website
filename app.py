# app.py - GannXPro COMPLETE with Live Market Updates (Optimized + Real NSE Option Chain)
import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
import math
import json
import time as time_module
from datetime import datetime, timedelta, time as dt_time
from math import log, sqrt, exp
from scipy.stats import norm
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------- Streamlit Page Setup -------------------
st.set_page_config(
    page_title="GannXPro — AI-Powered Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# (Your custom CSS kept identical; shortened here for brevity in this snippet)
st.markdown("""
<style>
/* (CSS from original file — keep exact as in your original app) */
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📈 GannXPro <span class="live-badge">LIVE</span></div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Market Intelligence Platform - Real Time Data</div>', unsafe_allow_html=True)

# ------------------- Utilities & Constants -------------------
NSE_HOME = "https://www.nseindia.com"
NSE_INDEX_ENDPOINT = "https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
NSE_EQUITY_ENDPOINT = "https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"

HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.nseindia.com/option-chain"
}

# Simple logger helper to show a message in sidebar if desired
def _log(msg):
    st.sidebar.write(msg)

# ------------------- CACHING STRATEGIES -------------------
# Cache market data short-term to reduce repeated external calls during active use
@st.cache_data(ttl=10)  # cache for 10 seconds (adjust as needed)
def cached_yf_download(tickers, period="1d", interval="1m"):
    """Batch yfinance downloads for multiple tickers to reduce API calls."""
    try:
        df = yf.download(tickers=tickers, period=period, interval=interval, threads=True, group_by='ticker', prepost=False, progress=False, timeout=10)
        return df
    except Exception as e:
        return None

@st.cache_data(ttl=15)
def cached_fetch_option_chain_nse(symbol):
    """Cached wrapper around NSE option chain fetch (short TTL)."""
    return fetch_nse_option_chain(symbol)

# ------------------- GLOBAL STOCKS -------------------
def get_all_stocks():
    all_stocks = {
        'NIFTY': 'Nifty 50 Index',
        'BANKNIFTY': 'Bank Nifty Index',
        'RELIANCE': 'Reliance Industries',
        'TCS': 'Tata Consultancy',
        'INFY': 'Infosys',
        'HDFCBANK': 'HDFC Bank',
        'HINDUNILVR': 'Hindustan Unilever',
        'ICICIBANK': 'ICICI Bank',
        'KOTAKBANK': 'Kotak Mahindra Bank',
        'BHARTIARTL': 'Bharti Airtel',
        'ITC': 'ITC',
        'SBIN': 'State Bank of India',
        'ASIANPAINT': 'Asian Paints',
        'DMART': 'Avenue Supermarts',
        'BAJFINANCE': 'Bajaj Finance',
        'WIPRO': 'Wipro',
        'HCLTECH': 'HCL Technologies',
        'MARUTI': 'Maruti Suzuki',
        'TITAN': 'Titan Company',
        'ULTRACEMCO': 'UltraTech Cement',
        'SUNPHARMA': 'Sun Pharmaceutical',
        'AXISBANK': 'Axis Bank',
        'LT': 'Larsen & Toubro',
        'ONGC': 'ONGC',
        'TATAMOTORS': 'Tata Motors',
        'TATASTEEL': 'Tata Steel',
        'JSWSTEEL': 'JSW Steel',
        'ADANIPORTS': 'Adani Ports',
        'BAJAJFINSV': 'Bajaj Finserv',
        'HDFCLIFE': 'HDFC Life',
        'DRREDDY': 'Dr Reddys Labs',
        'CIPLA': 'Cipla',
        'TECHM': 'Tech Mahindra',
        'COALINDIA': 'Coal India',
        'HINDALCO': 'Hindalco',
        'UPL': 'UPL',
        'BRITANNIA': 'Britannia',
        'INDUSINDBK': 'IndusInd Bank',
        'EICHERMOT': 'Eicher Motors',
        'HEROMOTOCO': 'Hero Motocorp',
        'BAJAJ-AUTO': 'Bajaj Auto',
        'SHREECEM': 'Shree Cement',
        'APOLLOHOSP': 'Apollo Hospitals',
        'TATACONSUM': 'Tata Consumer'
    }
    return all_stocks

# ------------------- YFINANCE & LIVE PRICES (Optimized) -------------------
def _symbol_to_yf_ticker(symbol):
    if symbol == "NIFTY":
        return "^NSEI"
    if symbol == "BANKNIFTY":
        return "^NSEBANK"
    return symbol + ".NS"

@st.cache_data(ttl=8)
def get_live_price(symbol):
    """Single symbol live price - optimized with caching."""
    try:
        ticker = _symbol_to_yf_ticker(symbol)
        # use yfinance history for 1d interval=1m (cached)
        df = cached_yf_download(tickers=ticker, period='1d', interval='1m')
        if df is None or df.empty:
            return None
        # If download returns a multiindex (when multiple tickers) handle both cases
        if isinstance(df.columns, pd.MultiIndex):
            hist = df[ticker]
        else:
            hist = df
        hist = hist.dropna()
        if hist.empty:
            return None
        current = hist['Close'].iloc[-1]
        open_price = hist['Open'].iloc[0]
        high = hist['High'].max()
        low = hist['Low'].min()
        volume = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0
        change = ((current - open_price) / open_price) * 100 if open_price != 0 else 0
        return {
            'current': current,
            'open': open_price,
            'high': high,
            'low': low,
            'volume': volume,
            'change': change,
            'timestamp': datetime.now()
        }
    except Exception as e:
        return None

def get_live_market_data():
    market_data = {}
    nifty_data = get_live_price('NIFTY')
    if nifty_data:
        market_data['nifty'] = nifty_data
    bank_data = get_live_price('BANKNIFTY')
    if bank_data:
        market_data['banknifty'] = bank_data
    return market_data

@st.cache_data(ttl=8)
def get_live_stock_data(symbols):
    """Batch get live stock data using yf.download to reduce many small requests."""
    try:
        tickers = [ _symbol_to_yf_ticker(s) for s in symbols ]
        df = cached_yf_download(tickers=" ".join(tickers), period='1d', interval='1m')
        results = {}
        for symbol, ticker in zip(symbols, tickers):
            try:
                if ticker in df:
                    hist = df[ticker].dropna()
                else:
                    hist = df
                if hist is None or hist.empty:
                    continue
                current = hist['Close'].iloc[-1]
                open_price = hist['Open'].iloc[0]
                high = hist['High'].max()
                low = hist['Low'].min()
                volume = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0
                change = ((current - open_price) / open_price) * 100 if open_price != 0 else 0
                results[symbol] = {
                    'current': current,
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'volume': volume,
                    'change': change,
                    'timestamp': datetime.now()
                }
            except Exception:
                continue
        return results
    except Exception:
        return {}

# ------------------- MARKET TIME CHECK -------------------
def is_market_open():
    """Check market open using local system time (assumes server time in same timezone).
       For absolute accuracy, consider timezone-aware checks."""
    now = datetime.now().time()
    market_open_time = dt_time(9, 15)
    market_close_time = dt_time(15, 30)
    return market_open_time <= now <= market_close_time

# ------------------- TECHNICAL INDICATORS (unchanged logic with caching) -------------------
def calculate_live_rsi(prices, period=14):
    if len(prices) < period:
        return 50.0
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_live_macd(prices, fast=12, slow=26, signal=9):
    if len(prices) < slow:
        return 0.0, 0.0
    series = pd.Series(prices)
    ema_fast = series.ewm(span=fast).mean().iloc[-1]
    ema_slow = series.ewm(span=slow).mean().iloc[-1]
    macd_line = ema_fast - ema_slow
    signal_line = pd.Series([macd_line]).ewm(span=signal).mean().iloc[-1]
    return macd_line, signal_line

def get_live_technical_analysis(symbol):
    try:
        ticker = _symbol_to_yf_ticker(symbol)
        df = cached_yf_download(tickers=ticker, period='1d', interval='5m')
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            hist = df[ticker]
        else:
            hist = df
        if len(hist) < 20:
            return None
        prices = hist['Close'].values
        rsi = calculate_live_rsi(prices)
        macd, signal = calculate_live_macd(prices)
        current_price = prices[-1]
        sma_20 = pd.Series(prices).rolling(20).mean().iloc[-1]
        return {
            'rsi': rsi,
            'macd': macd,
            'macd_signal': signal,
            'current_price': current_price,
            'sma_20': sma_20,
            'timestamp': datetime.now()
        }
    except Exception:
        return None

# ------------------- NSE Option Chain Fetcher (NEW) -------------------
def fetch_nse_option_chain(symbol):
    """
    Fetch option chain from NSE India public JSON endpoints.
    - For index symbols like NIFTY/BANKNIFTY, use option-chain-indices
    - For equities, use option-chain-equities
    NOTE: NSE may block requests without proper headers & cookies. We do:
      1) GET NSE homepage to get cookies
      2) Request option-chain endpoint with headers + session cookies
    Returns parsed dict or raises/returns None on failure.
    """
    session = requests.Session()
    session.headers.update(HEADERS_BASE)
    try:
        # 1) Hit homepage to obtain cookies / initial tokens
        homepage = session.get(NSE_HOME, timeout=10)
        # 2) Choose endpoint
        symbol_upper = symbol.upper()
        if symbol_upper in ["NIFTY", "BANKNIFTY"]:
            url = NSE_INDEX_ENDPOINT.format(symbol=symbol_upper)
        else:
            url = NSE_EQUITY_ENDPOINT.format(symbol=symbol_upper)
        resp = session.get(url, timeout=10)
        if resp.status_code != 200:
            # Try one more time with slightly modified headers (some users need Referer or Accept)
            session.headers.update({"Referer": "https://www.nseindia.com/live_market/dynaContent/live_watch/option_chain/optionKeys.jsp"})
            resp = session.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Parse key fields: underlying, expiries, optionData rows
        # The exact JSON structure differs slightly for indices vs equities; handle both.
        parsed = {
            "success": True,
            "symbol": symbol_upper,
            "timestamp": datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
            "data_source": "NSE",
            "underlying_price": None,
            "expiries": [],
            "option_data": [],
            "total_ce_oi": 0,
            "total_pe_oi": 0,
            "pcr": None
        }
        # The JSON key for underlying and records is often 'records' -> 'data'
        records = data.get("records") or data.get("filtered") or {}
        # Underlying value:
        try:
            parsed["underlying_price"] = records.get("underlyingValue") or data.get("underlyingValue")
        except Exception:
            parsed["underlying_price"] = None
        # Expiries:
        expiries = []
        try:
            expiries = records.get("expiryDates") or []
        except Exception:
            expiries = []
        parsed["expiries"] = expiries
        # Option rows
        option_rows = records.get("data") or data.get("data") or []
        ce_total = 0
        pe_total = 0
        for row in option_rows:
            # For NSE index option-chain JSON, CE and PE are keys inside each row
            ce = row.get("CE")
            pe = row.get("PE")
            strike = row.get("strikePrice") or row.get("strike")
            if ce:
                o = {
                    "type": "CE",
                    "strike": strike,
                    "expiry": ce.get("expiryDate") or row.get("expiryDate"),
                    "oi": int(ce.get("openInterest") or 0),
                    "volume": int(ce.get("totalTradedVolume") or ce.get("changeinOpenInterest") or 0),
                    "iv": float(ce.get("impliedVolatility") or 0),
                    "ltp": float(ce.get("lastPrice") or 0),
                    "change": float(ce.get("change") or 0)
                }
                parsed["option_data"].append(o)
                ce_total += o["oi"]
            if pe:
                o = {
                    "type": "PE",
                    "strike": strike,
                    "expiry": pe.get("expiryDate") or row.get("expiryDate"),
                    "oi": int(pe.get("openInterest") or 0),
                    "volume": int(pe.get("totalTradedVolume") or pe.get("changeinOpenInterest") or 0),
                    "iv": float(pe.get("impliedVolatility") or 0),
                    "ltp": float(pe.get("lastPrice") or 0),
                    "change": float(pe.get("change") or 0)
                }
                parsed["option_data"].append(o)
                pe_total += o["oi"]
        parsed["total_ce_oi"] = ce_total
        parsed["total_pe_oi"] = pe_total
        parsed["pcr"] = (pe_total / ce_total) if ce_total > 0 else None
        return parsed
    except Exception as exc:
        # If anything fails, return None for caller to fallback
        return None

# ------------------- Old random generator fallback (cleaned) -------------------
def generate_live_option_chain_fallback(symbol):
    """Fallback synthetic option chain (kept for resilience)."""
    base_prices = {
        'NIFTY': 21500 + np.random.randint(-100, 100),
        'BANKNIFTY': 48000 + np.random.randint(-200, 200),
        'RELIANCE': 2500 + np.random.randint(-20, 20),
        'TCS': 3500 + np.random.randint(-30, 30),
        'INFY': 1500 + np.random.randint(-15, 15),
        'HDFCBANK': 1600 + np.random.randint(-15, 15),
        'ICICIBANK': 1000 + np.random.randint(-10, 10)
    }
    base_price = base_prices.get(symbol, 1000)
    strikes = []
    for i in range(-5, 6):
        if symbol in ['NIFTY', 'BANKNIFTY']:
            strike = int(base_price + (i * 100))
        else:
            strike = int(base_price + (i * 50))
        if strike > 0:
            strikes.append(strike)
    option_data = []
    for strike in strikes:
        random_factor = np.random.uniform(0.8, 1.2)
        option_data.append({
            'type': 'CE',
            'strike': strike,
            'expiry': '25-Jan-2026',
            'oi': max(1000, int(10000 / (abs(strike - base_price) + 1) * random_factor)),
            'volume': max(100, int(1000 / (abs(strike - base_price) + 1) * random_factor)),
            'iv': 15 + (abs(strike - base_price) / base_price * 100 * random_factor),
            'ltp': max(5, abs(strike - base_price) * 0.1 * random_factor),
            'change': np.random.uniform(-15, 15)
        })
        option_data.append({
            'type': 'PE',
            'strike': strike,
            'expiry': '25-Jan-2026',
            'oi': max(1000, int(12000 / (abs(strike - base_price) + 1) * random_factor)),
            'volume': max(100, int(1200 / (abs(strike - base_price) + 1) * random_factor)),
            'iv': 16 + (abs(strike - base_price) / base_price * 100 * random_factor),
            'ltp': max(5, abs(strike - base_price) * 0.1 * random_factor),
            'change': np.random.uniform(-15, 15)
        })
    total_ce_oi = sum([i['oi'] for i in option_data if i['type'] == 'CE'])
    total_pe_oi = sum([i['oi'] for i in option_data if i['type'] == 'PE'])
    pcr = total_pe_oi/total_ce_oi if total_ce_oi>0 else None
    return {
        'success': True,
        'symbol': symbol,
        'underlying_price': base_price,
        'timestamp': datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
        'pcr': pcr,
        'total_ce_oi': total_ce_oi,
        'total_pe_oi': total_pe_oi,
        'option_data': option_data,
        'expiries': ['25-Jan-2026', '01-Feb-2026'],
        'data_source': 'SIMULATED'
    }

# ------------------- Intraday Signals & Screener (unchanged logic but using new get_live_price) -------------------
def analyze_live_stock_patterns(symbol, name):
    live_data = get_live_price(symbol)
    if not live_data:
        return None
    open_price = live_data['open']
    high_price = live_data['high']
    low_price = live_data['low']
    close_price = live_data['current']
    open_high_pattern = abs(open_price - high_price) <= (open_price * 0.001)
    open_low_pattern = abs(open_price - low_price) <= (open_price * 0.001)
    return {
        'symbol': symbol,
        'name': name,
        'open': open_price,
        'high': high_price,
        'low': low_price,
        'close': close_price,
        'volume': live_data['volume'],
        'change_today': live_data['change'],
        'open_high': open_high_pattern,
        'open_low': open_low_pattern,
        'timestamp': live_data['timestamp']
    }

def run_live_screener():
    all_stocks = get_all_stocks()
    results = []
    limited_stocks = dict(list(all_stocks.items())[:20])
    # Use threadpool to speed up calls responsibly
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = { ex.submit(analyze_live_stock_patterns, s, n): s for s,n in limited_stocks.items() }
        for fut in as_completed(futures):
            try:
                r = fut.result()
                if r:
                    results.append(r)
            except Exception:
                continue
    return results

def get_live_intraday_signal(symbol):
    try:
        ticker = _symbol_to_yf_ticker(symbol)
        df = cached_yf_download(tickers=ticker, period='1d', interval='5m')
        if df is None or df.empty:
            return "Signal unavailable"
        if isinstance(df.columns, pd.MultiIndex):
            hist = df[ticker]
        else:
            hist = df
        if len(hist) < 10:
            return "Insufficient data"
        current = hist.iloc[-1]
        prev = hist.iloc[-2]
        price_change = ((current['Close'] - prev['Close']) / prev['Close']) * 100
        volume_change = ((current['Volume'] - prev['Volume']) / prev['Volume']) * 100 if prev['Volume']>0 else 0
        rsi = calculate_live_rsi(hist['Close'].values)
        if price_change > 0.3 and volume_change > 25 and rsi < 70:
            return "🟢 STRONG BULLISH - Strong uptrend with volume"
        elif price_change > 0.15 and rsi < 65:
            return "🟢 BULLISH - Uptrend detected"
        elif price_change < -0.3 and volume_change > 25 and rsi > 30:
            return "🔴 STRONG BEARISH - Strong downtrend with volume"
        elif price_change < -0.15 and rsi > 35:
            return "🔴 BEARISH - Downtrend detected"
        elif abs(price_change) < 0.05:
            return "🟡 NEUTRAL - Sideways movement"
        else:
            return "🟡 WAIT - Mixed signals"
    except Exception:
        return "Signal unavailable"

# ------------------- Streamlit UI (kept structure but updated option chain flow) -------------------
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown(f'<div class="last-update">Last Updated: {datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)
with col2:
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.experimental_rerun()
with col3:
    st.markdown('<div style="text-align: right;">Manual Refresh Enabled</div>', unsafe_allow_html=True)

st.sidebar.header("🔧 Navigation")
app_mode = st.sidebar.radio(
    "Choose Analysis Mode",
    ["Stock Screener", "Market Dashboard", "Technical Analysis", "Option Chain", "Intraday Signals"],
    index=0
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh All Data", use_container_width=True):
    st.experimental_rerun()
st.sidebar.markdown("**💡 Tip:** Click refresh button to update all data with latest market prices")

# ------------------- Stock Screener -------------------
if app_mode == "Stock Screener":
    st.markdown('<div class="section-header">🔍 Live Stock Screener - Open=High / Open=Low</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 📊 Live Pattern Analysis")
        st.write("**Open = High**: Bearish pattern - Stock opened at day's high")
        st.write("**Open = Low**: Bullish pattern - Stock opened at day's low")
    with col2:
        if st.button("🔄 Scan Live Data", type="primary", use_container_width=True):
            with st.spinner("Scanning live market data..."):
                stock_data = run_live_screener()
                if stock_data:
                    categorized = {
                        'open_high': [s for s in stock_data if s['open_high']],
                        'open_low': [s for s in stock_data if s['open_low']]
                    }
                    st.session_state.screener_results = categorized
                    st.success(f"✅ Live scan complete! Found {len(categorized['open_high'])} Open=High and {len(categorized['open_low'])} Open=Low stocks")
                else:
                    st.error("No live data found. Please try again during market hours.")
    if 'screener_results' in st.session_state:
        results = st.session_state.screener_results
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"🔴 Open = High ({len(results['open_high'])} stocks)")
            st.markdown("**Bearish Pattern - Potential selling pressure**")
            for stock in results['open_high']:
                change_color = "market-up" if stock['change_today'] > 0 else "market-down"
                st.markdown(f"""
                <div class="stock-card open-high">
                    <strong>{stock['symbol']}</strong> - {stock['name']}<br>
                    Open: ₹{stock['open']:.2f} | High: ₹{stock['high']:.2f}<br>
                    Current: ₹{stock['close']:.2f} | 
                    <span class="{change_color}">{stock['change_today']:+.2f}%</span>
                </div>
                """, unsafe_allow_html=True)
        with col2:
            st.subheader(f"🟢 Open = Low ({len(results['open_low'])} stocks)")
            st.markdown("**Bullish Pattern - Potential buying opportunity**")
            for stock in results['open_low']:
                change_color = "market-up" if stock['change_today'] > 0 else "market-down"
                st.markdown(f"""
                <div class="stock-card open-low">
                    <strong>{stock['symbol']}</strong> - {stock['name']}<br>
                    Open: ₹{stock['open']:.2f} | Low: ₹{stock['low']:.2f}<br>
                    Current: ₹{stock['close']:.2f} | 
                    <span class="{change_color}">{stock['change_today']:+.2f}%</span>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Click 'Scan Live Data' to analyze stocks for Open=High and Open=Low patterns")

# ------------------- Market Dashboard -------------------
elif app_mode == "Market Dashboard":
    st.markdown('<div class="section-header">📊 Live Market Dashboard</div>', unsafe_allow_html=True)
    st.subheader("🏦 Live Market Overview")
    market_data = get_live_market_data()
    if market_data:
        col1, col2, col3, col4 = st.columns(4)
        if 'nifty' in market_data:
            nifty = market_data['nifty']
            col1.metric("Nifty 50", f"₹{nifty['current']:.2f}", f"{nifty['change']:.2f}%")
        if 'banknifty' in market_data:
            banknifty = market_data['banknifty']
            col2.metric("Bank Nifty", f"₹{banknifty['current']:.2f}", f"{banknifty['change']:.2f}%")
        market_status = "🟢 OPEN" if is_market_open() else "🔴 CLOSED"
        col3.metric("Market Status", market_status)
        col4.metric("Last Updated", datetime.now().strftime("%H:%M:%S"))
    st.subheader("📈 Live Stock Performance")
    top_stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'BHARTIARTL']
    live_stock_data = get_live_stock_data(top_stocks)
    if live_stock_data:
        gainers = {k: v for k, v in live_stock_data.items() if v['change'] > 0}
        losers = {k: v for k, v in live_stock_data.items() if v['change'] < 0}
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📈 Top Gainers**")
            for symbol, data in list(gainers.items())[:3]:
                st.metric(f"{symbol}", f"₹{data['current']:.2f}", f"+{data['change']:.2f}%")
        with col2:
            st.markdown("**📉 Top Losers**")
            for symbol, data in list(losers.items())[:3]:
                st.metric(f"{symbol}", f"₹{data['current']:.2f}", f"{data['change']:.2f}%")

# ------------------- Technical Analysis -------------------
elif app_mode == "Technical Analysis":
    st.markdown('<div class="section-header">🔍 Live Technical Analysis</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        all_stocks = get_all_stocks()
        selected_symbol = st.selectbox(
            "Select Stock:",
            options=list(all_stocks.keys()),
            format_func=lambda x: f"{x} - {all_stocks[x]}",
            index=3
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("🔄 Update Analysis", type="primary", use_container_width=True):
            st.experimental_rerun()
    tech_data = get_live_technical_analysis(selected_symbol)
    if tech_data:
        st.success(f"Live Technical Analysis for {selected_symbol} - {all_stocks[selected_symbol]}")
        st.subheader("📊 Live Technical Indicators")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            rsi = tech_data['rsi']
            rsi_status = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
            st.metric("RSI", f"{rsi:.1f}", rsi_status)
        with col2:
            macd = tech_data['macd']
            macd_signal = tech_data['macd_signal']
            macd_status = "Bullish" if macd > macd_signal else "Bearish"
            st.metric("MACD", f"{macd:.3f}", macd_status)
        with col3:
            price = tech_data['current_price']
            sma_20 = tech_data['sma_20']
            trend = "Bullish" if price > sma_20 else "Bearish"
            st.metric("Trend", trend, f"₹{sma_20:.2f}")
        with col4:
            st.metric("Live Price", f"₹{tech_data['current_price']:.2f}")

# ------------------- Option Chain (NEW: real NSE fetch with fallback) -------------------
elif app_mode == "Option Chain":
    st.markdown('<div class="section-header">🔗 Live Option Chain Analysis</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        all_stocks = get_all_stocks()
        selected_symbol = st.selectbox(
            "Select Stock/Index:",
            options=list(all_stocks.keys()),
            format_func=lambda x: f"{x} - {all_stocks[x]}",
            index=0
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("🔄 Update Chain", type="primary", use_container_width=True):
            st.experimental_rerun()
    # Try NSE fetch (cached wrapper)
    option_data = None
    try:
        # Use cached wrapper to reduce rapid repeated hits
        option_data = cached_fetch_option_chain_nse(selected_symbol)
    except Exception:
        option_data = None
    # Fallback to synthetic if NSE failed
    if not option_data:
        option_data = generate_live_option_chain_fallback(selected_symbol)
    if option_data and option_data.get('success', True):
        st.success(f"Live Option Chain for {selected_symbol} - {all_stocks[selected_symbol]} (Source: {option_data.get('data_source')})")
        col1, col2, col3, col4 = st.columns(4)
        up = option_data.get('underlying_price') or 0
        pcr = option_data.get('pcr') or 0
        col1.metric("Underlying Price", f"₹{up:.2f}")
        col2.metric("PCR", f"{pcr:.2f}" if pcr is not None else "N/A")
        col3.metric("Total CE OI", f"{option_data.get('total_ce_oi'):,}")
        col4.metric("Total PE OI", f"{option_data.get('total_pe_oi'):,}")
        # Show top 10 strikes
        st.markdown("### Top strikes (sample)")
        df_rows = []
        for r in option_data.get('option_data', [])[:40]:
            df_rows.append({
                "type": r['type'],
                "strike": r['strike'],
                "expiry": r['expiry'],
                "oi": r['oi'],
                "volume": r.get('volume', 0),
                "iv": r.get('iv', 0),
                "ltp": r.get('ltp', 0)
            })
        if df_rows:
            df = pd.DataFrame(df_rows)
            st.dataframe(df)
    else:
        st.error("Option chain unavailable. Try again or check your network/headers.")

# ------------------- Intraday Signals -------------------
else:
    st.markdown('<div class="section-header">⚡ Live Intraday Signals</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        all_stocks = get_all_stocks()
        selected_symbol = st.selectbox(
            "Select Stock for Analysis:",
            options=list(all_stocks.keys()),
            format_func=lambda x: f"{x} - {all_stocks[x]}",
            index=3
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("🔄 Get Live Signal", type="primary", use_container_width=True):
            st.experimental_rerun()
    live_signal = get_live_intraday_signal(selected_symbol)
    if live_signal:
        st.subheader("🎯 Live Trading Signal")
        if "BULLISH" in live_signal:
            st.markdown(f'<div class="signal-buy">{live_signal}</div>', unsafe_allow_html=True)
        elif "BEARISH" in live_signal:
            st.markdown(f'<div class="signal-sell">{live_signal}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="signal-wait">{live_signal}</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>GannXPro — Live Market Intelligence Platform</strong></p>
    <p>📚 Educational Purpose Only | 🔒 Privacy First | ⚡ Real-time Live Data</p>
    <p>Click Refresh button for latest data | For analysis and learning. Not investment advice.</p>
</div>
""", unsafe_allow_html=True)
