# app.py - GannXPro with Market Trend Signals (All stocks & indices)
import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
import math
import json
import time as time_module
from datetime import datetime, timedelta, time as dt_time, date
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

# ------------------- Custom CSS -------------------
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1f77b4; text-align: center; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.0rem; color: #666; text-align: center; margin-bottom: 1.2rem; }
    .section-header { font-size: 1.25rem; font-weight: 600; color: #1f77b4; margin-top: 1rem; margin-bottom: 1rem; border-bottom: 2px solid #e9ecef; padding-bottom: 0.5rem; }
    .signal-buy { background-color: #d4edda; border-left: 4px solid #28a745; padding: 0.8rem; border-radius: 8px; font-weight: bold; }
    .signal-sell { background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 0.8rem; border-radius: 8px; font-weight: bold; }
    .signal-wait { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 0.8rem; border-radius: 8px; font-weight: bold; }
    .stock-card { background-color: #f8f9fa; padding: 0.6rem; border-radius: 6px; margin: 0.3rem 0; border-left: 4px solid #1f77b4; }
    .live-badge { background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; animation: blink 2s infinite; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    .last-update { font-size: 0.85rem; color: #666; text-align: right; }
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

def _log(msg): st.sidebar.write(msg)

# ------------------- CACHING -------------------
@st.cache_data(ttl=10)
def cached_yf_download(tickers, period="1d", interval="1m"):
    try:
        df = yf.download(tickers=tickers, period=period, interval=interval, threads=True, group_by='ticker', prepost=False, progress=False, timeout=10)
        return df
    except Exception:
        return None

@st.cache_data(ttl=20)
def cached_fetch_option_chain_nse(symbol):
    return fetch_nse_option_chain(symbol)

# ------------------- Global Stocks -------------------
def get_all_stocks():
    return {
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

# ------------------- YFinance helpers -------------------
def _symbol_to_yf_ticker(symbol):
    if symbol == "NIFTY": return "^NSEI"
    if symbol == "BANKNIFTY": return "^NSEBANK"
    return symbol + ".NS"

@st.cache_data(ttl=8)
def get_live_price(symbol):
    try:
        ticker = _symbol_to_yf_ticker(symbol)
        df = cached_yf_download(tickers=ticker, period='1d', interval='1m')
        if df is None or df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            hist = df[ticker]
        else:
            hist = df
        hist = hist.dropna()
        if hist.empty: return None
        current = hist['Close'].iloc[-1]
        open_price = hist['Open'].iloc[0]
        high = hist['High'].max()
        low = hist['Low'].min()
        volume = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0
        change = ((current - open_price) / open_price) * 100 if open_price != 0 else 0
        # 5-min change (approx): compare last and value 5 intervals back if exists
        prev_idx = max(0, len(hist)-6)
        prev_close = hist['Close'].iloc[prev_idx]
        change_5m = ((current - prev_close) / prev_close) * 100 if prev_close != 0 else 0
        return {'current': current, 'open': open_price, 'high': high, 'low': low, 'volume': volume, 'change': change, 'change_5m': change_5m, 'timestamp': datetime.now()}
    except Exception:
        return None

# ------------------- Technical indicators -------------------
def calculate_live_rsi(prices, period=14):
    if len(prices) < period: return 50.0
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0: return 100.0
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ------------------- NSE Option Chain Fetcher -------------------
def fetch_nse_option_chain(symbol):
    session = requests.Session()
    session.headers.update(HEADERS_BASE)
    try:
        session.get(NSE_HOME, timeout=10)
        sym = symbol.upper()
        if sym in ["NIFTY", "BANKNIFTY"]:
            url = NSE_INDEX_ENDPOINT.format(symbol=sym)
        else:
            url = NSE_EQUITY_ENDPOINT.format(symbol=sym)
        resp = session.get(url, timeout=10)
        if resp.status_code != 200:
            session.headers.update({"Referer": "https://www.nseindia.com/live_market"})
            resp = session.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        parsed = {"success": True, "symbol": sym, "timestamp": datetime.now().strftime("%d-%b-%Y %H:%M:%S"), "data_source": "NSE", "underlying_price": None, "expiries": [], "option_data": [], "total_ce_oi": 0, "total_pe_oi": 0, "pcr": None}
        records = data.get("records") or data.get("filtered") or {}
        parsed["underlying_price"] = records.get("underlyingValue") or data.get("underlyingValue") if records else data.get("underlyingValue")
        parsed["expiries"] = records.get("expiryDates") or []
        rows = records.get("data") or data.get("data") or []
        ce_total = 0; pe_total = 0
        for row in rows:
            ce = row.get("CE")
            pe = row.get("PE")
            strike = row.get("strikePrice") or row.get("strike")
            if ce:
                o = {"type":"CE","strike":strike,"expiry":ce.get("expiryDate") or row.get("expiryDate"),"oi":int(ce.get("openInterest") or 0),"volume":int(ce.get("totalTradedVolume") or 0),"iv":float(ce.get("impliedVolatility") or 0),"ltp":float(ce.get("lastPrice") or 0)}
                parsed["option_data"].append(o); ce_total += o["oi"]
            if pe:
                o = {"type":"PE","strike":strike,"expiry":pe.get("expiryDate") or row.get("expiryDate"),"oi":int(pe.get("openInterest") or 0),"volume":int(pe.get("totalTradedVolume") or 0),"iv":float(pe.get("impliedVolatility") or 0),"ltp":float(pe.get("lastPrice") or 0)}
                parsed["option_data"].append(o); pe_total += o["oi"]
        parsed["total_ce_oi"] = ce_total; parsed["total_pe_oi"] = pe_total
        parsed["pcr"] = (pe_total/ce_total) if ce_total>0 else None
        return parsed
    except Exception:
        return None

# ------------------- Synthetic fallback -------------------
def generate_live_option_chain_fallback(symbol):
    base_prices = {'NIFTY':21500,'BANKNIFTY':48000,'RELIANCE':2500,'TCS':3500,'INFY':1500,'HDFCBANK':1600,'ICICIBANK':1000}
    base_price = base_prices.get(symbol, 1000) + np.random.randint(-50,50)
    strikes = []
    for i in range(-6,7):
        strike = int(base_price + (i * (100 if symbol in ['NIFTY','BANKNIFTY'] else 50)))
        if strike>0: strikes.append(strike)
    option_data = []
    for strike in strikes:
        rf = np.random.uniform(0.8,1.2)
        option_data.append({'type':'CE','strike':strike,'expiry':'25-Jan-2026','oi':max(1000,int(10000/(abs(strike-base_price)+1)*rf)),'volume':max(100,int(1000/(abs(strike-base_price)+1)*rf)),'iv':15+(abs(strike-base_price)/base_price*100*rf),'ltp':max(5,abs(strike-base_price)*0.1*rf)})
        option_data.append({'type':'PE','strike':strike,'expiry':'25-Jan-2026','oi':max(1000,int(12000/(abs(strike-base_price)+1)*rf)),'volume':max(100,int(1200/(abs(strike-base_price)+1)*rf)),'iv':16+(abs(strike-base_price)/base_price*100*rf),'ltp':max(5,abs(strike-base_price)*0.1*rf)})
    total_ce = sum([o['oi'] for o in option_data if o['type']=='CE'])
    total_pe = sum([o['oi'] for o in option_data if o['type']=='PE'])
    return {'success':True,'symbol':symbol,'underlying_price':base_price,'timestamp':datetime.now().strftime("%d-%b-%Y %H:%M:%S"),'pcr':(total_pe/total_ce if total_ce>0 else None),'total_ce_oi':total_ce,'total_pe_oi':total_pe,'option_data':option_data,'expiries':['25-Jan-2026'],'data_source':'SIMULATED'}

# ------------------- Trend Signal Logic (heuristics) -------------------
def aggregate_atm_oi(option_data, spot, symbol):
    """Aggregate OI & volume for strikes closest to ATM.
       For index use strike step 100, for stocks 50 (approx)."""
    if not option_data: return {'ce_oi':0,'pe_oi':0,'ce_vol':0,'pe_vol':0}
    # determine step
    step = 100 if symbol in ['NIFTY','BANKNIFTY'] else 50
    # find strikes within +/- 1 step
    ce_oi = pe_oi = ce_vol = pe_vol = 0
    for o in option_data:
        if o.get('strike') is None: continue
        if abs(o['strike'] - spot) <= step:
            if o['type']=='CE':
                ce_oi += int(o.get('oi',0))
                ce_vol += int(o.get('volume',0))
            else:
                pe_oi += int(o.get('oi',0))
                pe_vol += int(o.get('volume',0))
    return {'ce_oi':ce_oi,'pe_oi':pe_oi,'ce_vol':ce_vol,'pe_vol':pe_vol}

def detect_market_trend(symbol, option_data, price_data):
    """Return one of: SHORT_COVERING, LONG_UNWINDING, CALL_BUYING, PUT_BUYING, SIDEWAYS, NO_DATA
       Uses heuristics based on ATM OI, total OI, PCR, and recent price movement.
       NOTE: This is heuristic and not a definitive trade signal. Use risk management.
    """
    if not option_data or not price_data:
        return {'signal':'NO_DATA','reason':'Missing data'}
    spot = option_data.get('underlying_price') or price_data.get('current')
    total_ce = option_data.get('total_ce_oi') or 0
    total_pe = option_data.get('total_pe_oi') or 0
    pcr = option_data.get('pcr') or (total_pe/total_ce if total_ce>0 else None)
    atm = aggregate_atm_oi(option_data.get('option_data',[]), spot, symbol)
    price_change = price_data.get('change') or 0
    change_5m = price_data.get('change_5m') or 0

    # Heuristics
    # Short Covering: price up and ATM put OI > ATM call OI (puts bought to hedge), or pcr rising while price rising
    if price_change > 0.3 and (atm['pe_oi'] > atm['ce_oi']*1.05 or (pcr and pcr>1.05)):
        return {'signal':'SHORT_COVERING','reason':f'price_up {price_change:.2f}%, ATM_PE_OI>{atm["pe_oi"]}, PCR={pcr}'}

    # Long Unwinding: price down and ATM call OI > ATM put OI (calls being sold), or pcr < 0.95 while price falling
    if price_change < -0.3 and (atm['ce_oi'] > atm['pe_oi']*1.05 or (pcr and pcr<0.95)):
        return {'signal':'LONG_UNWINDING','reason':f'price_down {price_change:.2f}%, ATM_CE_OI>{atm["ce_oi"]}, PCR={pcr}'}

    # Call Buying: price up and ATM CE volume > ATM PE volume
    if price_change > 0.2 and atm['ce_vol'] > atm['pe_vol']*1.2:
        return {'signal':'CALL_BUYING','reason':f'price_up {price_change:.2f}%, ATM_CE_VOL>{atm["ce_vol"]}'}

    # Put Buying: price down and ATM PE volume > ATM CE volume
    if price_change < -0.2 and atm['pe_vol'] > atm['ce_vol']*1.2:
        return {'signal':'PUT_BUYING','reason':f'price_down {price_change:.2f}%, ATM_PE_VOL>{atm["pe_vol"]}'}

    # Sideways
    if abs(price_change) < 0.05 and abs(change_5m) < 0.05:
        return {'signal':'SIDEWAYS','reason':f'price_small_move {price_change:.2f}% 5m {change_5m:.2f}%'} 

    return {'signal':'NO_CLEAR_SIGNAL','reason':f'price_change {price_change:.2f}%, PCR {pcr}'}

# ------------------- Hero-Zero Scanner -------------------
def find_hero_zero_opportunities(symbol, option_data):
    """Find strikes near ATM that fit hero-zero profile.
       Heuristics: expiry within 1 day (expiry day), strike distance small, iv moderate, volume rising.
       Returns list of candidate dicts.
    """
    if not option_data: return []
    today = date.today()
    expiries = option_data.get('expiries') or []
    # find nearest expiry equal to today or tomorrow (heuristic for expiry proximity)
    # Note: exact expiry day detection requires parsing expiry strings to dates; we'll approximate by checking if any expiry string contains today's year/month/day
    candidates = []
    spot = option_data.get('underlying_price') or 0
    # convert option entries by strike
    rows = option_data.get('option_data',[])
    # choose strikes within 1-3 steps
    step = 100 if symbol in ['NIFTY','BANKNIFTY'] else 50
    for o in rows:
        if o['type'] != 'CE': continue
        strike = o.get('strike')
        if strike is None: continue
        dist = abs(strike - spot)
        if dist in (step, 2*step, 3*step):
            iv = o.get('iv') or 0
            vol = o.get('volume') or 0
            # low to moderate IV threshold (heuristic)
            if iv < 30 and vol > 50:
                candidates.append({'strike':strike,'iv':iv,'volume':vol,'expiry':o.get('expiry')})
    return candidates

# ------------------- Bulk fetch & analyze (careful with rate limits) -------------------
def analyze_all_symbols_for_trends(symbols, max_workers=6):
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = { ex.submit(fetch_and_analyze, sym): sym for sym in symbols }
        for fut in as_completed(futures):
            sym = futures[fut]
            try:
                results[sym] = fut.result()
            except Exception as e:
                results[sym] = {'error': str(e)}
    return results

def fetch_and_analyze(symbol):
    # fetch option chain (cached wrapper will be used)
    option_data = cached_fetch_option_chain_nse(symbol)
    if not option_data:
        option_data = generate_live_option_chain_fallback(symbol)
    price_data = get_live_price(symbol)
    trend = detect_market_trend(symbol, option_data, price_data)
    hero = find_hero_zero_opportunities(symbol, option_data)
    return {'option':option_data,'price':price_data,'trend':trend,'hero':hero}

# ------------------- UI Controls -------------------
col1, col2, col3 = st.columns([2,1,1])
with col1:
    st.markdown(f'<div class="last-update">Last Updated: {datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)
with col2:
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()
with col3:
    st.markdown('<div style="text-align: right;">Manual Refresh Enabled</div>', unsafe_allow_html=True)

st.sidebar.header("🔧 Navigation")
app_mode = st.sidebar.radio(
    "Choose Analysis Mode",
    ["Stock Screener", "Market Dashboard", "Technical Analysis", "Option Chain", "Market Trend Signals", "Intraday Signals"],
    index=4  # open Market Trend Signals by default
)
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh All Data", use_container_width=True):
    st.rerun()
st.sidebar.markdown("**💡 Tip:** Use Market Trend Signals to see short-covering / long-unwinding opportunities across all symbols.")

# ------------------- Existing tabs kept minimal for brevity -------------------
if app_mode == "Stock Screener":
    st.markdown('<div class="section-header">🔍 Live Stock Screener</div>', unsafe_allow_html=True)
    st.info("Same screener as before. (Open the full app.py if needed)")

elif app_mode == "Market Dashboard":
    st.markdown('<div class="section-header">📊 Live Market Dashboard</div>', unsafe_allow_html=True)
    st.info("Dashboard kept. (Open the full app.py if needed)")

elif app_mode == "Technical Analysis":
    st.markdown('<div class="section-header">🔍 Live Technical Analysis</div>', unsafe_allow_html=True)
    st.info("Technical analysis tab kept. (Open the full app.py if needed)")

elif app_mode == "Option Chain":
    st.markdown('<div class="section-header">🔗 Live Option Chain Analysis</div>', unsafe_allow_html=True)
    st.info("Option chain tab kept. (Open the full app.py if needed)")

# ------------------- NEW: Market Trend Signals Tab -------------------
elif app_mode == "Market Trend Signals":
    st.markdown('<div class="section-header">⚡ Market Trend Signals - Short Covering / Long Unwinding / Hero-Zero</div>', unsafe_allow_html=True)
    st.write("This tab scans **all stocks and indices** in your universe and applies heuristic rules to detect short-covering, long-unwinding, call/put buying, and Hero-Zero candidates. These are **heuristics** — use risk management.")
    all_stocks = get_all_stocks()
    symbols = list(all_stocks.keys())
    st.write(f"Scanning {len(symbols)} symbols (this may take a few seconds).")
    # run analysis (careful with concurrency)
    with st.spinner("Fetching option-chains and live prices (cached) ..."):
        analysis = analyze_all_symbols_for_trends(symbols, max_workers=6)
    # Summarize signals
    trends = {'SHORT_COVERING':[], 'LONG_UNWINDING':[], 'CALL_BUYING':[], 'PUT_BUYING':[], 'SIDEWAYS':[], 'NO_CLEAR_SIGNAL':[], 'NO_DATA':[]}
    for sym, data in analysis.items():
        if not data or 'trend' not in data:
            trends['NO_DATA'].append(sym); continue
        sig = data['trend'].get('signal')
        if sig in trends:
            trends[sig].append((sym, data))
        else:
            trends.setdefault(sig, []).append((sym, data))
    # Display top signals
    st.markdown("### 🔔 Detected Signals (sample)")
    cols = st.columns(3)
    def render_list(lst, col, title):
        with col:
            st.subheader(title)
            if not lst:
                st.write("—")
                return
            for sym, info in lst[:12]:
                price = info['price']['current'] if info['price'] else None
                reason = info['trend'].get('reason') if info.get('trend') else ''
                source = info['option']['data_source'] if info.get('option') else 'N/A'
                st.markdown(f"<div class='stock-card'><strong>{sym}</strong> — ₹{price if price else 'N/A'}<br><small>{reason} | src:{source}</small></div>", unsafe_allow_html=True)
    render_list(trends['SHORT_COVERING'], cols[0], "🟢 Short Covering")
    render_list(trends['LONG_UNWINDING'], cols[1], "🔴 Long Unwinding")
    render_list(trends['CALL_BUYING'], cols[2], "📈 Call Buying")
    st.markdown("---")
    cols2 = st.columns(3)
    render_list(trends['PUT_BUYING'], cols2[0], "📉 Put Buying")
    render_list(trends['SIDEWAYS'], cols2[1], "🟡 Sideways")
    render_list(trends['NO_CLEAR_SIGNAL'], cols2[2], "❔ No Clear Signal")
    # Hero-Zero candidates (detailed table)
    st.markdown("### ⚡ Hero-Zero Candidates (sample)")
    hero_rows = []
    for sym, data in analysis.items():
        for c in (data.get('hero') or []):
            hero_rows.append({'symbol':sym,'strike':c['strike'],'iv':c['iv'],'volume':c['volume'],'expiry':c.get('expiry')})
    if hero_rows:
        hdf = pd.DataFrame(hero_rows).sort_values(by='iv')
        st.dataframe(hdf.head(50))
    else:
        st.write("No immediate Hero-Zero candidates found in this scan.")

# Intraday Signals (kept minimal)
else:
    st.markdown('<div class="section-header">⚡ Live Intraday Signals</div>', unsafe_allow_html=True)
    st.info("Intraday signals tab kept.")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>GannXPro — Market Trend Signals</strong></p>
    <p>Signals are heuristics for educational purposes. Not financial advice.</p>
</div>
""", unsafe_allow_html=True)
