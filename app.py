# app_gannxpro_full.py - GannXPro COMPLETE (Merged + Index Trend Signals)
# This file merges the full application: Market Dashboard, Stock Screener, Technical Analysis,
# Date-wise Option Chain, Intraday Signals, and Market Trend Signals (Index Only, Advanced).
# Real NSE option-chain fetcher (with fallback), optimized yfinance usage, caching, and UI grouping.
import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
from datetime import datetime, timedelta, date
import time as time_module
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------- Page setup -------------------
st.set_page_config(page_title="GannXPro — Live Market Intelligence", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# ------------------- Styles -------------------
st.markdown("""
<style>
    .main-header { font-size: 2.0rem; font-weight:700; color:#1f77b4; text-align:center; }
    .sub-header { font-size:1.0rem; color:#666; text-align:center; margin-bottom:10px; }
    .section-header { font-size:1.1rem; font-weight:600; color:#1f77b4; margin-top:10px; margin-bottom:8px; }
    .stock-card { background:#f8f9fa; padding:8px; border-radius:8px; margin-bottom:6px; border-left:4px solid #1f77b4; }
    .live-badge { background:#dc3545; color:white; padding:4px 8px; border-radius:12px; font-weight:700; }
    .signal-box { padding:10px; border-radius:8px; margin-bottom:8px; }
    .sig-bull { background:#d4edda; border-left:6px solid #28a745; }
    .sig-bear { background:#f8d7da; border-left:6px solid #dc3545; }
    .sig-neutral { background:#fff3cd; border-left:6px solid #ffc107; }
    .small { font-size:0.85rem; color:#444; }
    .expiry-badge { background:#6c757d; color:white; padding:4px 10px; border-radius:12px; display:inline-block; margin:2px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📈 GannXPro <span class="live-badge">LIVE</span></div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Merged app — Dashboard · Screener · Options · Index Trend Signals</div>', unsafe_allow_html=True)

# ------------------- Constants & Config -------------------
NSE_HOME = "https://www.nseindia.com"
NSE_INDEX_ENDPOINT = "https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
NSE_EQUITY_ENDPOINT = "https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.nseindia.com/option-chain"
}

# ------------------- Utilities -------------------
def _symbol_to_yf_ticker(symbol):
    if symbol == "NIFTY": return "^NSEI"
    if symbol == "BANKNIFTY": return "^NSEBANK"
    return symbol + ".NS"

@st.cache_data(ttl=8)
def cached_yf_download(tickers, period="1d", interval="1m"):
    try:
        df = yf.download(tickers=tickers, period=period, interval=interval, threads=True, progress=False, timeout=10)
        return df
    except Exception:
        return None

@st.cache_data(ttl=10)
def get_live_price(symbol):
    try:
        ticker = _symbol_to_yf_ticker(symbol)
        df = cached_yf_download(tickers=ticker, period='1d', interval='1m')
        if df is None or df.empty: return None
        if isinstance(df.columns, pd.MultiIndex) and ticker in df.columns.levels[0]:
            hist = df[ticker].dropna()
        else:
            hist = df.dropna()
        if hist.empty: return None
        current = float(hist['Close'].iloc[-1])
        openp = float(hist['Open'].iloc[0])
        high = float(hist['High'].max())
        low = float(hist['Low'].min())
        volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0
        change_today = ((current - openp)/openp)*100 if openp!=0 else 0.0
        prev_idx = max(0, len(hist)-6)
        prev_close = float(hist['Close'].iloc[prev_idx])
        change_5m = ((current - prev_close)/prev_close)*100 if prev_close!=0 else 0.0
        prev_idx15 = max(0, len(hist)-16)
        prev_close15 = float(hist['Close'].iloc[prev_idx15])
        change_15m = ((current - prev_close15)/prev_close15)*100 if prev_close15!=0 else 0.0
        return {'current':current,'open':openp,'high':high,'low':low,'volume':volume,'change':change_today,'change_5m':change_5m,'change_15m':change_15m,'timestamp':datetime.now(),'hist':hist}
    except Exception:
        return None

# ------------------- Stocks Universe -------------------
def get_all_stocks():
    return {
        'NIFTY':'Nifty 50 Index','BANKNIFTY':'Bank Nifty Index','RELIANCE':'Reliance Industries','TCS':'Tata Consultancy',
        'INFY':'Infosys','HDFCBANK':'HDFC Bank','HINDUNILVR':'Hindustan Unilever','ICICIBANK':'ICICI Bank',
        'KOTAKBANK':'Kotak Mahindra Bank','BHARTIARTL':'Bharti Airtel','ITC':'ITC','SBIN':'State Bank of India',
        'ASIANPAINT':'Asian Paints','DMART':'Avenue Supermarts','BAJFINANCE':'Bajaj Finance','WIPRO':'Wipro',
        'HCLTECH':'HCL Technologies','MARUTI':'Maruti Suzuki','TITAN':'Titan Company','ULTRACEMCO':'UltraTech Cement',
        'SUNPHARMA':'Sun Pharmaceutical','AXISBANK':'Axis Bank','LT':'Larsen & Toubro','ONGC':'ONGC','TATAMOTORS':'Tata Motors',
        'TATASTEEL':'Tata Steel','JSWSTEEL':'JSW Steel','ADANIPORTS':'Adani Ports','BAJAJFINSV':'Bajaj Finserv','HDFCLIFE':'HDFC Life',
        'DRREDDY':'Dr Reddys Labs','CIPLA':'Cipla','TECHM':'Tech Mahindra','COALINDIA':'Coal India','HINDALCO':'Hindalco',
        'UPL':'UPL','BRITANNIA':'Britannia','INDUSINDBK':'IndusInd Bank','EICHERMOT':'Eicher Motors','HEROMOTOCO':'Hero Motocorp',
        'BAJAJ-AUTO':'Bajaj Auto','SHREECEM':'Shree Cement','APOLLOHOSP':'Apollo Hospitals','TATACONSUM':'Tata Consumer'
    }

# ------------------- Option chain fetchers -------------------
@st.cache_data(ttl=12)
def fetch_nse_option_chain_index(symbol):
    session = requests.Session()
    session.headers.update(HEADERS_BASE)
    try:
        session.get(NSE_HOME, timeout=10)
        url = NSE_INDEX_ENDPOINT.format(symbol=symbol)
        resp = session.get(url, timeout=10)
        if resp.status_code != 200:
            session.headers.update({"Referer":"https://www.nseindia.com/live_market/dynaContent/live_watch/option_chain/optionKeys.jsp"})
            resp = session.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        parsed = {'success':True,'symbol':symbol,'timestamp':datetime.now().strftime("%d-%b-%Y %H:%M:%S"),'option_data':[],'underlying':None,'expiries':[]}
        records = data.get('records',{})
        parsed['underlying'] = records.get('underlyingValue') or data.get('underlyingValue')
        parsed['expiries'] = records.get('expiryDates') or []
        rows = records.get('data') or []
        total_ce=total_pe=0
        for row in rows:
            ce=row.get('CE'); pe=row.get('PE'); strike=row.get('strikePrice') or row.get('strike')
            if ce:
                parsed['option_data'].append({**ce,'type':'CE','strike':strike})
                total_ce += int(ce.get('openInterest') or 0)
            if pe:
                parsed['option_data'].append({**pe,'type':'PE','strike':strike})
                total_pe += int(pe.get('openInterest') or 0)
        parsed['total_ce_oi']=total_ce; parsed['total_pe_oi']=total_pe
        parsed['pcr']=(total_pe/total_ce) if total_ce>0 else None
        return parsed
    except Exception:
        return None

@st.cache_data(ttl=12)
def fetch_nse_option_chain_equity(symbol):
    session = requests.Session()
    session.headers.update(HEADERS_BASE)
    try:
        session.get(NSE_HOME, timeout=10)
        url = NSE_EQUITY_ENDPOINT.format(symbol=symbol)
        resp = session.get(url, timeout=10)
        if resp.status_code != 200:
            session.headers.update({"Referer":"https://www.nseindia.com/live_market"})
            resp = session.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        parsed = {'success':True,'symbol':symbol,'timestamp':datetime.now().strftime("%d-%b-%Y %H:%M:%S"),'option_data':[],'underlying':None,'expiries':[]}
        records = data.get('records',{})
        parsed['underlying'] = records.get('underlyingValue') or data.get('underlyingValue')
        parsed['expiries'] = records.get('expiryDates') or []
        rows = records.get('data') or []
        total_ce=total_pe=0
        for row in rows:
            ce=row.get('CE'); pe=row.get('PE'); strike=row.get('strikePrice') or row.get('strike')
            if ce:
                parsed['option_data'].append({**ce,'type':'CE','strike':strike})
                total_ce += int(ce.get('openInterest') or 0)
            if pe:
                parsed['option_data'].append({**pe,'type':'PE','strike':strike})
                total_pe += int(pe.get('openInterest') or 0)
        parsed['total_ce_oi']=total_ce; parsed['total_pe_oi']=total_pe
        parsed['pcr']=(total_pe/total_ce) if total_ce>0 else None
        return parsed
    except Exception:
        return None

# synthetic fallback generator for equities & indices
def generate_option_chain_fallback(symbol, is_index=False):
    base_prices = {'NIFTY':21500,'BANKNIFTY':48000,'RELIANCE':2500,'TCS':3500,'INFY':1500,'HDFCBANK':1600}
    base = base_prices.get(symbol, 1000) + np.random.randint(-50,50)
    step = 100 if is_index else 50
    strikes = [base + i*step for i in range(-8,9)]
    option_data=[]
    for s in strikes:
        dist=abs(s-base)
        iv = max(8, 12 + (dist/base)*100 + np.random.uniform(-2,2))
        option_data.append({'type':'CE','strike':s,'expiry':(date.today()+timedelta(days=7)).strftime("%d-%b-%Y"),'oi':int(max(400,20000/(dist+100)*np.random.uniform(0.8,1.2))),'volume':int(max(50,2000/(dist+100)*np.random.uniform(0.6,1.4))),'iv':round(iv,1),'ltp':round(max(1,dist*0.1*np.random.uniform(0.8,1.2)),2)})
        option_data.append({'type':'PE','strike':s,'expiry':(date.today()+timedelta(days=7)).strftime("%d-%b-%Y"),'oi':int(max(400,23000/(dist+100)*np.random.uniform(0.8,1.2))),'volume':int(max(50,2500/(dist+100)*np.random.uniform(0.6,1.4))),'iv':round(iv+1,1),'ltp':round(max(1,dist*0.1*np.random.uniform(0.8,1.2)),2)})
    total_ce=sum([o['oi'] for o in option_data if o['type']=='CE']); total_pe=sum([o['oi'] for o in option_data if o['type']=='PE'])
    return {'success':True,'symbol':symbol,'option_data':option_data,'underlying':base,'total_ce_oi':total_ce,'total_pe_oi':total_pe,'pcr':(total_pe/total_ce if total_ce>0 else None),'expiries':[(date.today()+timedelta(days=7)).strftime("%d-%b-%Y")]}

# ------------------- Trend detection for indices -------------------
def aggregate_atm(option_rows, spot):
    if not option_rows: return {'ce_oi':0,'pe_oi':0,'ce_vol':0,'pe_vol':0,'atm_strike':None}
    strikes = sorted(set([r['strike'] for r in option_rows if r.get('strike') is not None]))
    atm = min(strikes, key=lambda x: abs(x-spot))
    ce_oi=pe_oi=ce_vol=pe_vol=0
    for r in option_rows:
        if r.get('strike')==atm:
            if r.get('type')=='CE':
                ce_oi += int(r.get('openInterest') or r.get('oi') or 0)
                ce_vol += int(r.get('totalTradedVolume') or r.get('volume') or 0)
            else:
                pe_oi += int(r.get('openInterest') or r.get('oi') or 0)
                pe_vol += int(r.get('totalTradedVolume') or r.get('volume') or 0)
    return {'ce_oi':ce_oi,'pe_oi':pe_oi,'ce_vol':ce_vol,'pe_vol':pe_vol,'atm_strike':atm}

def detect_index_trend(option_payload, price_payload):
    if not option_payload or not price_payload: return {'signal':'NO_DATA','reason':'Missing data'}
    spot = option_payload.get('underlying') or price_payload.get('current')
    rows = option_payload.get('option_data') or []
    atm = aggregate_atm(rows, spot)
    total_ce = option_payload.get('total_ce_oi') or 0
    total_pe = option_payload.get('total_pe_oi') or 0
    pcr = option_payload.get('pcr')
    change_5m = price_payload.get('change_5m') or 0
    change_15m = price_payload.get('change_15m') or 0
    change_today = price_payload.get('change') or 0
    if change_5m > 0.35 and (atm['pe_oi'] > atm['ce_oi']*1.05 or (pcr and pcr>1.05)):
        return {'signal':'SHORT_COVERING','reason':f'5m {change_5m:.2f}% up; ATM_PE_OI {atm["pe_oi"]} > ATM_CE_OI {atm["ce_oi"]}; PCR {pcr}','atm':atm,'pcr':pcr}
    if change_5m < -0.35 and (atm['ce_oi'] > atm['pe_oi']*1.05 or (pcr and pcr<0.95)):
        return {'signal':'LONG_UNWINDING','reason':f'5m {change_5m:.2f}% down; ATM_CE_OI {atm["ce_oi"]} > ATM_PE_OI {atm["pe_oi"]}; PCR {pcr}','atm':atm,'pcr':pcr}
    if change_15m > 0.5 and atm['ce_vol'] > atm['pe_vol']*1.3:
        return {'signal':'CALL_BUYING','reason':f'15m {change_15m:.2f}% up; ATM_CE_VOL {atm["ce_vol"]} > ATM_PE_VOL {atm["pe_vol"]}','atm':atm,'pcr':pcr}
    if change_15m < -0.5 and atm['pe_vol'] > atm['ce_vol']*1.3:
        return {'signal':'PUT_BUYING','reason':f'15m {change_15m:.2f}% down; ATM_PE_VOL {atm["pe_vol"]} > ATM_CE_VOL {atm["ce_vol"]}','atm':atm,'pcr':pcr}
    if abs(change_today) < 0.05 and abs(change_5m) < 0.1:
        return {'signal':'SIDEWAYS','reason':f'Little movement: today {change_today:.2f}%, 5m {change_5m:.2f}%','atm':atm,'pcr':pcr}
    return {'signal':'NO_CLEAR_SIGNAL','reason':f'5m {change_5m:.2f}%, 15m {change_15m:.2f}%, PCR {pcr}','atm':atm,'pcr':pcr}

def hero_zero_candidates_index(option_payload, spot):
    if not option_payload: return []
    rows = option_payload.get('option_data',[])
    strikes = sorted(set([r['strike'] for r in rows if r.get('strike') is not None]))
    atm = min(strikes, key=lambda x: abs(x-spot))
    candidates=[]
    for step in [100,200,300]:
        for s in [atm+step, atm-step]:
            ce = next((r for r in rows if r['strike']==s and r.get('type')=='CE'), None)
            if ce:
                iv = float(ce.get('impliedVolatility') or ce.get('iv') or 0)
                vol = int(ce.get('totalTradedVolume') or ce.get('volume') or 0)
                if iv < 28 and vol > 80:
                    candidates.append({'strike':s,'iv':iv,'volume':vol,'ltp':ce.get('lastPrice') or ce.get('ltp')})
    return candidates

# ------------------- Screener & technical analysis (simplified) -------------------
def analyze_live_stock_patterns(symbol, name):
    live_data = get_live_price(symbol)
    if not live_data: return None
    open_price = live_data['open']; high_price = live_data['high']; low_price = live_data['low']; close_price = live_data['current']
    open_high_pattern = abs(open_price - high_price) <= (open_price * 0.001)
    open_low_pattern = abs(open_price - low_price) <= (open_price * 0.001)
    return {'symbol':symbol,'name':name,'open':open_price,'high':high_price,'low':low_price,'close':close_price,'volume':live_data['volume'],'change_today':live_data['change'],'open_high':open_high_pattern,'open_low':open_low_pattern,'timestamp':live_data['timestamp']}

def run_live_screener(limit=20):
    all_stocks = get_all_stocks()
    results=[]; limited_stocks = dict(list(all_stocks.items())[:limit])
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures={ ex.submit(analyze_live_stock_patterns,s,n): s for s,n in limited_stocks.items() }
        for fut in as_completed(futures):
            try:
                r=fut.result(); 
                if r: results.append(r)
            except Exception:
                continue
    return results

def calculate_live_rsi(prices, period=14):
    if len(prices) < period: return 50.0
    deltas = np.diff(prices); gains = np.where(deltas > 0, deltas, 0); losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:]); avg_loss = np.mean(losses[-period:])
    if avg_loss == 0: return 100.0
    rs = avg_gain / avg_loss; rsi = 100 - (100/(1+rs)); return rsi

def calculate_live_macd(prices, fast=12, slow=26, signal=9):
    if len(prices) < slow: return 0.0,0.0
    s = pd.Series(prices); ema_fast = s.ewm(span=fast).mean().iloc[-1]; ema_slow = s.ewm(span=slow).mean().iloc[-1]
    macd = ema_fast - ema_slow; sig = pd.Series([macd]).ewm(span=signal).mean().iloc[-1]; return macd, sig

def get_live_technical_analysis(symbol):
    try:
        ticker = _symbol_to_yf_ticker(symbol)
        df = cached_yf_download(tickers=ticker, period='1d', interval='5m')
        if df is None or df.empty: return None
        if isinstance(df.columns, pd.MultiIndex) and ticker in df.columns.levels[0]:
            hist = df[ticker].dropna()
        else:
            hist = df.dropna()
        if len(hist) < 20: return None
        prices = hist['Close'].values
        rsi = calculate_live_rsi(prices); macd, sig = calculate_live_macd(prices)
        current = prices[-1]; sma_20 = pd.Series(prices).rolling(20).mean().iloc[-1]
        return {'rsi':rsi,'macd':macd,'macd_signal':sig,'current_price':current,'sma_20':sma_20,'timestamp':datetime.now()}
    except Exception:
        return None

def get_live_intraday_signal(symbol):
    try:
        ticker=_symbol_to_yf_ticker(symbol)
        df = cached_yf_download(tickers=ticker, period='1d', interval='5m')
        if df is None or df.empty: return "Signal unavailable"
        if isinstance(df.columns, pd.MultiIndex) and ticker in df.columns.levels[0]:
            hist = df[ticker].dropna()
        else:
            hist = df.dropna()
        if len(hist) < 10: return "Insufficient data"
        current=hist.iloc[-1]; prev=hist.iloc[-2]
        price_change = ((current['Close']-prev['Close'])/prev['Close'])*100
        volume_change = ((current['Volume']-prev['Volume'])/prev['Volume'])*100 if prev['Volume']>0 else 0
        rsi = calculate_live_rsi(hist['Close'].values)
        if price_change > 0.3 and volume_change > 25 and rsi < 70: return "🟢 STRONG BULLISH - Strong uptrend with volume"
        if price_change > 0.15 and rsi < 65: return "🟢 BULLISH - Uptrend detected"
        if price_change < -0.3 and volume_change > 25 and rsi > 30: return "🔴 STRONG BEARISH - Strong downtrend with volume"
        if price_change < -0.15 and rsi > 35: return "🔴 BEARISH - Downtrend detected"
        if abs(price_change) < 0.05: return "🟡 NEUTRAL - Sideways movement"
        return "🟡 WAIT - Mixed signals"
    except Exception:
        return "Signal unavailable"

# ------------------- UI Layout (Left Sidebar Sections) -------------------
st.sidebar.header("📊 Markets")
market_section = st.sidebar.selectbox("Markets", ["Market Dashboard","Index Trend Signals (Index Only)"])
st.sidebar.header("🔍 Analysis")
analysis_section = st.sidebar.selectbox("Analysis", ["Stock Screener","Technical Analysis"])
st.sidebar.header("🔗 Derivatives")
deriv_section = st.sidebar.selectbox("Derivatives", ["Option Chain","Intraday Signals"])

# global refresh controls
col1, col2 = st.columns([3,1])
with col2:
    if st.button("🔄 Refresh All Data"):
        st.rerun()

# ------------------- Market Dashboard -------------------
if market_section == "Market Dashboard":
    st.markdown('<div class="section-header">🏦 Live Market Dashboard</div>', unsafe_allow_html=True)
    market_data = {}
    for idx in ['NIFTY','BANKNIFTY']:
        market_data[idx.lower()] = get_live_price(idx)
    cols = st.columns(3)
    if market_data.get('nifty'):
        cols[0].metric("Nifty 50", f"₹{market_data['nifty']['current']:.2f}", f"{market_data['nifty']['change']:.2f}%")
    if market_data.get('banknifty'):
        cols[1].metric("Bank Nifty", f"₹{market_data['banknifty']['current']:.2f}", f"{market_data['banknifty']['change']:.2f}%")
    cols[2].metric("Last Updated", datetime.now().strftime("%H:%M:%S"))
    st.markdown("### 📈 Live Top Stocks")
    top = ['RELIANCE','TCS','INFY','HDFCBANK','ICICIBANK','BHARTIARTL']
    live = {}
    with st.spinner("Fetching top stock prices..."):
        live = get_live_price('RELIANCE') and get_live_price('TCS') and get_live_price('INFY')  # quick check (individual shown below)
    cols = st.columns(3)
    for i,sym in enumerate(top):
        data = get_live_price(sym)
        if data:
            cols[i%3].metric(sym, f"₹{data['current']:.2f}", f"{data['change']:.2f}%")
        else:
            cols[i%3].metric(sym, "N/A", "")

# ------------------- Index Trend Signals (Index Only) -------------------
elif market_section == "Index Trend Signals (Index Only)":
    st.markdown('<div class="section-header">⚡ Market Trend Signals — Index Only</div>', unsafe_allow_html=True)
    st.write("Advanced signals for NIFTY & BANKNIFTY (short-covering, long-unwinding, call/put buying, hero-zero).")
    indices = ['NIFTY','BANKNIFTY']
    view = st.selectbox("View", ["Summary","Detailed - NIFTY","Detailed - BANKNIFTY"], index=0)
    data = {}
    with st.spinner("Fetching option chains and prices for indices..."):
        for idx in indices:
            opt = fetch_nse_option_chain_index(idx)
            if not opt:
                opt = generate_option_chain_fallback(idx, is_index=True)
            price = get_live_price(idx)
            trend = detect_index_trend(opt, price)
            hero = hero_zero_candidates_index(opt, opt.get('underlying') if opt else (price.get('current') if price else None))
            data[idx] = {'option':opt,'price':price,'trend':trend,'hero':hero}
    if view == "Summary":
        cols = st.columns(2)
        for i,idx in enumerate(indices):
            with cols[i]:
                d = data[idx]; trend = d['trend']['signal']; reason=d['trend']['reason']; atm=d['trend'].get('atm') or {}; pcr=d['trend'].get('pcr') or (d['option'].get('pcr') if d.get('option') else None)
                if trend=='SHORT_COVERING': cl='sig-bull'; title='🟢 SHORT COVERING'
                elif trend=='LONG_UNWINDING': cl='sig-bear'; title='🔴 LONG UNWINDING'
                elif trend=='CALL_BUYING': cl='sig-bull'; title='📈 CALL BUYING'
                elif trend=='PUT_BUYING': cl='sig-bear'; title='📉 PUT BUYING'
                elif trend=='SIDEWAYS': cl='sig-neutral'; title='🟡 SIDEWAYS'
                else: cl='sig-neutral'; title='❔ NO CLEAR SIGNAL'
                st.markdown(f"<div class='signal-box {cl}'><strong>{idx} — {title}</strong><div class='small'>{reason}</div></div>", unsafe_allow_html=True)
                st.write(f"Price: ₹{d['price']['current'] if d['price'] else 'N/A'} | PCR: {pcr if pcr else 'N/A'}")
                st.write(f"ATM Strike: {atm.get('atm_strike')} | ATM CE OI: {atm.get('ce_oi')} | ATM PE OI: {atm.get('pe_oi')}")
                if d['hero']:
                    st.write("Hero-Zero CE candidates:"); st.dataframe(pd.DataFrame(d['hero']))
                else:
                    st.write("No Hero-Zero CE candidates found.")
    else:
        idx = "NIFTY" if view.endswith("NIFTY") else "BANKNIFTY"
        d = data[idx]; price=d.get('price'); opt=d.get('option'); trend=d.get('trend'); hero=d.get('hero')
        st.markdown(f"## Detailed — {idx}")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Live Price", f"₹{price['current']:.2f}" if price else "N/A")
        c2.metric("PCR", f"{opt.get('pcr'):.2f}" if opt else "N/A")
        c3.metric("ATM CE OI", f"{trend.get('atm')['ce_oi'] if trend.get('atm') else 'N/A'}")
        c4.metric("ATM PE OI", f"{trend.get('atm')['pe_oi'] if trend.get('atm') else 'N/A'}")
        st.markdown("### Trend Signal"); st.write(f"**{trend['signal']}** — {trend['reason']}")
        st.markdown("### ATM Summary"); atm=trend.get('atm') or {}; st.table(pd.DataFrame([{'ATM Strike':atm.get('atm_strike'),'CE OI':atm.get('ce_oi'),'PE OI':atm.get('pe_oi'),'CE Vol':atm.get('ce_vol'),'PE Vol':atm.get('pe_vol')}])) 
        # OI heatmap pivot
        rows = opt.get('option_data') if opt else []
        if rows:
            df = pd.DataFrame(rows)
            if 'openInterest' in df.columns: df['oi']=df['openInterest']
            if 'totalTradedVolume' in df.columns: df['vol']=df['totalTradedVolume']
            pivot = df.pivot_table(index='strike', columns='type', values='oi', aggfunc='sum').fillna(0)
            st.markdown("### OI Heatmap (sample)"); st.dataframe(pivot.sort_index(ascending=False).head(40))
        st.markdown("### Hero-Zero Candidates (detailed)"); st.dataframe(pd.DataFrame(hero) if hero else pd.DataFrame())

# ------------------- Analysis: Stock Screener -------------------
if analysis_section == "Stock Screener":
    st.markdown('<div class="section-header">🔍 Live Stock Screener</div>', unsafe_allow_html=True)
    if st.button("🔄 Scan Live Data (Top 20)"):
        with st.spinner("Scanning..."):
            results = run_live_screener(limit=20)
            st.session_state.screener_results = results
    if 'screener_results' in st.session_state:
        res = st.session_state.screener_results
        col1,col2 = st.columns(2)
        with col1:
            st.subheader("Open = High")
            for r in res:
                if r['open_high']:
                    st.markdown(f"<div class='stock-card'><strong>{r['symbol']}</strong> {r['name']} | Open: ₹{r['open']:.2f} | High: ₹{r['high']:.2f} | Current: ₹{r['close']:.2f}</div>", unsafe_allow_html=True)
        with col2:
            st.subheader("Open = Low")
            for r in res:
                if r['open_low']:
                    st.markdown(f"<div class='stock-card'><strong>{r['symbol']}</strong> {r['name']} | Open: ₹{r['open']:.2f} | Low: ₹{r['low']:.2f} | Current: ₹{r['close']:.2f}</div>", unsafe_allow_html=True)
    else:
        st.info("Click 'Scan Live Data' to run the screener.")

# ------------------- Analysis: Technical Analysis -------------------
if analysis_section == "Technical Analysis":
    st.markdown('<div class="section-header">🔍 Technical Analysis</div>', unsafe_allow_html=True)
    stocks = get_all_stocks()
    sel = st.selectbox("Select Stock", options=list(stocks.keys()), format_func=lambda x: f"{x} - {stocks[x]}", index=3)
    if st.button("🔄 Update Analysis (selected)"):
        st.rerun()
    tech = get_live_technical_analysis(sel)
    if tech:
        st.metric("RSI", f"{tech['rsi']:.1f}"); st.metric("MACD", f"{tech['macd']:.3f}"); st.metric("SMA20", f"₹{tech['sma_20']:.2f}")
    else:
        st.warning("Technical data unavailable.")

# ------------------- Derivatives: Option Chain -------------------
if deriv_section == "Option Chain":
    st.markdown('<div class="section-header">🔗 Date-wise Option Chain</div>', unsafe_allow_html=True)
    stocks = get_all_stocks(); sel = st.selectbox("Select Symbol", options=list(stocks.keys()), format_func=lambda x: f"{x} - {stocks[x]}", index=0)
    if st.button("🔄 Update Chain"):
        st.rerun()
    # Try real NSE equity fetch for symbols (if index use index fetch)
    if sel in ['NIFTY','BANKNIFTY']:
        opt = fetch_nse_option_chain_index(sel)
        if not opt: opt = generate_option_chain_fallback(sel, is_index=True)
    else:
        opt = fetch_nse_option_chain_equity(sel)
        if not opt: opt = generate_option_chain_fallback(sel, is_index=False)
    if opt:
        st.success(f"Option Chain for {sel} (source: {'NSE' if opt.get('success') else 'SIMULATED'})")
        expiries = opt.get('expiries') or opt.get('expiries') or []
        if expiries:
            st.write("Expiries: " + ", ".join(expiries[:6]))
        # show top sample rows pivot table
        rows = opt.get('option_data') or opt.get('option_data') or []
        if rows:
            df = pd.DataFrame(rows)
            if 'openInterest' in df.columns: df['oi']=df['openInterest']
            if 'lastPrice' in df.columns: df['ltp']=df['lastPrice']
            st.dataframe(df[['type','strike','oi','ltp']].head(100))
    else:
        st.error("Option chain unavailable.")

# ------------------- Derivatives: Intraday Signals -------------------
if deriv_section == "Intraday Signals":
    st.markdown('<div class="section-header">⚡ Live Intraday Signals</div>', unsafe_allow_html=True)
    stocks = get_all_stocks(); sel = st.selectbox("Select Symbol for Signal", options=list(stocks.keys()), format_func=lambda x: f"{x} - {stocks[x]}", index=3)
    if st.button("🔄 Get Live Signal"):
        st.rerun()
    sig = get_live_intraday_signal(sel)
    if sig:
        if "BULLISH" in sig: st.markdown(f"<div class='signal-box sig-bull'><strong>{sig}</strong></div>", unsafe_allow_html=True)
        elif "BEARISH" in sig: st.markdown(f"<div class='signal-box sig-bear'><strong>{sig}</strong></div>", unsafe_allow_html=True)
        else: st.markdown(f"<div class='signal-box sig-neutral'><strong>{sig}</strong></div>", unsafe_allow_html=True)
    tech = get_live_technical_analysis(sel)
    if tech:
        st.write("Additional:"); st.write(f"RSI: {tech['rsi']:.1f}, MACD: {tech['macd']:.3f}, SMA20: ₹{tech['sma_20']:.2f}")

# ------------------- Footer -------------------
st.markdown("---")
st.markdown("<div style='text-align:center;color:#666;'><p><strong>GannXPro — Live Market Intelligence</strong></p><p>Educational purposes only. Not financial advice.</p></div>", unsafe_allow_html=True)
