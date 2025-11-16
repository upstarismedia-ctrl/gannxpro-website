# app.py - GannXPro with Working Phase 1 Features
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
    .info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
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

# ----------- FIXED: SIMPLIFIED NSE API CALLS ----------- #
def safe_nse_api_call(symbol, is_index=True):
    """Safe API call with error handling"""
    try:
        if is_index:
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        else:
            url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# ----------- PHASE 1: NEW TECHNICAL INDICATORS ----------- #
def calculate_rsi(df, period=14):
    """Calculate Relative Strength Index (RSI)"""
    try:
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except:
        return pd.Series([50] * len(df))  # Return neutral RSI if error

def calculate_macd(df, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    try:
        ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    except:
        # Return zeros if error
        zeros = pd.Series([0] * len(df))
        return zeros, zeros, zeros

def calculate_bollinger_bands(df, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    try:
        sma = df['Close'].rolling(window=period).mean()
        std = df['Close'].rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    except:
        # Return simple values if error
        close = df['Close']
        return close, close, close

def get_technical_indicators(df):
    """Calculate all technical indicators with error handling"""
    try:
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
    except Exception as e:
        st.error(f"Technical indicators error: {e}")
        return df

# ----------- PHASE 1: MARKET DASHBOARD ----------- #
def get_nifty_components():
    """Get Nifty 50 components with current prices - SIMPLIFIED"""
    # Limited set of reliable stocks
    reliable_stocks = {
        'RELIANCE.NS': 'Reliance',
        'TCS.NS': 'TCS', 
        'INFY.NS': 'Infosys',
        'HDFCBANK.NS': 'HDFC Bank',
        'ICICIBANK.NS': 'ICICI Bank',
        'BHARTIARTL.NS': 'Airtel',
        'ITC.NS': 'ITC',
        'KOTAKBANK.NS': 'Kotak Bank',
        'LT.NS': 'L&T',
        'SBIN.NS': 'SBI'
    }
    
    market_data = []
    for symbol, name in reliable_stocks.items():
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='2d')  # 2 days to calculate change
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change = ((current - prev_close) / prev_close) * 100
                volume = hist['Volume'].iloc[-1]
                
                market_data.append({
                    'Symbol': symbol.replace('.NS', ''),
                    'Name': name,
                    'Price': current,
                    'Change': change,
                    'Volume': volume
                })
        except Exception as e:
            continue
    
    return pd.DataFrame(market_data)

def get_sector_performance():
    """Get sector-wise performance - SIMPLIFIED"""
    sectors = {
        '^NSEI': 'Nifty 50',
        '^NSEBANK': 'Bank Nifty', 
        '^CNXIT': 'Nifty IT',
        '^CNXAUTO': 'Nifty Auto'
    }
    
    sector_data = []
    for symbol, name in sectors.items():
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='2d')
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change = ((current - prev_close) / prev_close) * 100
                
                sector_data.append({
                    'Sector': name,
                    'Change': change
                })
        except:
            continue
    
    return pd.DataFrame(sector_data)

# ----------- PHASE 1: EDUCATIONAL CONTENT ----------- #
def show_educational_tooltip(term):
    """Show educational information for technical terms"""
    educational_content = {
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
    
    content = educational_content.get(term, {})
    with st.expander(f"📚 {content.get('title', term)}"):
        st.write(f"**Description:** {content.get('description', '')}")
        st.write(f"**Interpretation:** {content.get('interpretation', '')}")

# ----------- SIMPLIFIED GANN ANALYSIS ----------- #
def calculate_gann_levels(high, low, close):
    """Calculate Gann support and resistance levels"""
    try:
        pivot = (high + low + close) / 3
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        
        return {
            'pivot': pivot,
            'resistance': [r1, r2],
            'support': [s1, s2]
        }
    except:
        return {'pivot': close, 'resistance': [close, close], 'support': [close, close]}

def gann_trading_signal(price_data, current_price):
    """Generate Gann-based trading signals"""
    try:
        if len(price_data) < 5:
            return "Insufficient data"
        
        high_10 = max(price_data[-10:])
        low_10 = min(price_data[-10:])
        
        gann_levels = calculate_gann_levels(high_10, low_10, current_price)
        
        if current_price >= gann_levels['resistance'][0]:
            return "🟢 BULLISH - Above R1"
        elif current_price <= gann_levels['support'][0]:
            return "🔴 BEARISH - Below S1" 
        elif current_price > gann_levels['pivot']:
            return "🟡 MILD BULLISH - Above Pivot"
        else:
            return "🟡 MILD BEARISH - Below Pivot"
    except:
        return "⚪ NEUTRAL - Analysis unavailable"

# ----------- SIMPLIFIED OPTION CHAIN ----------- #
def get_option_chain_data(symbol):
    """Get basic option chain data with fallback"""
    try:
        data = safe_nse_api_call(symbol, True)
        if data and 'records' in data:
            underlying = data['records'].get('underlyingValue', 0)
            timestamp = data['records'].get('timestamp', 'N/A')
            
            # Simple PCR calculation
            total_ce_oi = 0
            total_pe_oi = 0
            
            if 'data' in data['records']:
                for item in data['records']['data']:
                    if 'CE' in item and item['CE']:
                        total_ce_oi += item['CE'].get('openInterest', 0)
                    if 'PE' in item and item['PE']:
                        total_pe_oi += item['PE'].get('openInterest', 0)
            
            pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0
            
            return {
                'underlying': underlying,
                'timestamp': timestamp,
                'pcr': pcr,
                'success': True
            }
    except:
        pass
    
    # Fallback data
    return {
        'underlying': 0,
        'timestamp': 'N/A',
        'pcr': 0,
        'success': False
    }

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

def fetch_history(ticker: str, months: int = 6):
    """Fetch historical data with error handling"""
    try:
        tk = normalize_ticker_yf(ticker)
        df = yf.Ticker(tk).history(period=f"{months}mo")
        if df.empty:
            # Fallback to 1 month if empty
            df = yf.Ticker(tk).history(period="1mo")
        return df
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

def fetch_intraday(ticker: str, period: str = "5d", interval: str = "5m"):
    """Fetch intraday data with error handling"""
    try:
        tk = normalize_ticker_yf(ticker)
        df = yf.Ticker(tk).history(period=period, interval=interval)
        if df.empty:
            raise RuntimeError("No intraday data")
        return df
    except Exception as e:
        st.error(f"Intraday data error: {e}")
        return pd.DataFrame()

def add_vwap_and_ema(df: pd.DataFrame):
    """Add VWAP and EMA with error handling"""
    try:
        if df.empty:
            return df
            
        tp = (df["High"] + df["Low"] + df["Close"]) / 3
        df["VWAP"] = (tp * df["Volume"]).cumsum() / df["Volume"].cumsum()
        df["EMA9"] = df["Close"].ewm(span=9, adjust=False).mean()
        df["EMA21"] = df["Close"].ewm(span=21, adjust=False).mean()
        return df
    except:
        return df

# ----------- STREAMLIT UI ----------- #
st.sidebar.header("🔧 Navigation")
app_mode = st.sidebar.radio(
    "Choose Analysis Mode",
    ["Market Dashboard", "Technical Analysis", "Option Chain", "Intraday Signals"],
    index=0
)

# Sidebar Info
st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 Tips")
st.sidebar.info("""
- **Market Hours:** Data is most accurate during market hours (9:15 AM - 3:30 PM IST)
- **Reliable Symbols:** Use NIFTY, BANKNIFTY, RELIANCE, TCS for best results
- **Data Source:** Yahoo Finance + NSE India
""")

# ----------- MARKET DASHBOARD TAB ----------- #
if app_mode == "Market Dashboard":
    st.markdown('<div class="section-header">📊 Live Market Dashboard</div>', unsafe_allow_html=True)
    
    # Quick Actions
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    # Market Overview
    st.subheader("🏦 Market Overview")
    
    try:
        # Get Nifty data for overview
        nifty = yf.Ticker("^NSEI")
        nifty_hist = nifty.history(period="2d")
        
        if len(nifty_hist) >= 2:
            nifty_current = nifty_hist['Close'].iloc[-1]
            nifty_prev = nifty_hist['Close'].iloc[-2]
            nifty_change = ((nifty_current - nifty_prev) / nifty_prev) * 100
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Nifty 50", f"₹{nifty_current:.2f}", f"{nifty_change:.2f}%")
            
            # Get Bank Nifty
            banknifty = yf.Ticker("^NSEBANK")
            bank_hist = banknifty.history(period="2d")
            if len(bank_hist) >= 2:
                bank_current = bank_hist['Close'].iloc[-1]
                bank_prev = bank_hist['Close'].iloc[-2]
                bank_change = ((bank_current - bank_prev) / bank_prev) * 100
                col2.metric("Bank Nifty", f"₹{bank_current:.2f}", f"{bank_change:.2f}%")
    except:
        st.warning("Market data temporarily unavailable")
    
    # Stock Performance
    st.subheader("📈 Stock Performance")
    
    with st.spinner("Loading stock data..."):
        market_data = get_nifty_components()
    
    if not market_data.empty:
        # Top Performers
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top Gainers**")
            gainers = market_data.nlargest(5, 'Change')
            for _, stock in gainers.iterrows():
                emoji = "📈" if stock['Change'] > 0 else "📉"
                st.write(f"{emoji} **{stock['Symbol']}**: ₹{stock['Price']:.2f} ({stock['Change']:+.2f}%)")
        
        with col2:
            st.markdown("**Top Losers**")
            losers = market_data.nsmallest(5, 'Change')
            for _, stock in losers.iterrows():
                emoji = "📈" if stock['Change'] > 0 else "📉"
                st.write(f"{emoji} **{stock['Symbol']}**: ₹{stock['Price']:.2f} ({stock['Change']:+.2f}%)")
        
        # Sector Performance
        st.subheader("🏭 Sector Performance")
        sector_data = get_sector_performance()
        
        if not sector_data.empty:
            cols = st.columns(len(sector_data))
            for idx, (_, sector) in enumerate(sector_data.iterrows()):
                with cols[idx]:
                    delta_color = "normal" if sector['Change'] >= 0 else "inverse"
                    st.metric(
                        sector['Sector'],
                        f"{sector['Change']:.2f}%",
                        delta_color=delta_color
                    )

# ----------- TECHNICAL ANALYSIS TAB ----------- #
elif app_mode == "Technical Analysis":
    st.markdown('<div class="section-header">🔍 Technical Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        symbol = st.text_input("Enter Symbol:", "NIFTY")
        period = st.selectbox("Time Period:", ["1mo", "3mo", "6mo", "1y"], index=2)
    
    with col2:
        st.write("")
        st.write("")
        if st.button("Analyze", type="primary", use_container_width=True):
            with st.spinner("Performing technical analysis..."):
                try:
                    # Convert period to months for history
                    months_map = {"1mo": 1, "3mo": 3, "6mo": 6, "1y": 12}
                    df = fetch_history(symbol, months_map[period])
                    
                    if not df.empty:
                        df = get_technical_indicators(df)
                        last_row = df.iloc[-1]
                        
                        st.session_state.tech_data = {
                            'symbol': symbol,
                            'data': df,
                            'last_row': last_row,
                            'success': True
                        }
                    else:
                        st.session_state.tech_data = {'success': False}
                        
                except Exception as e:
                    st.error(f"Analysis error: {e}")
                    st.session_state.tech_data = {'success': False}
    
    # Display Technical Analysis Results
    if 'tech_data' in st.session_state and st.session_state.tech_data['success']:
        data = st.session_state.tech_data
        last = data['last_row']
        
        st.success(f"Technical Analysis for {data['symbol']}")
        
        # Key Indicators
        st.subheader("📊 Key Technical Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # RSI
            rsi = last['RSI']
            rsi_status = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
            st.metric("RSI", f"{rsi:.1f}", rsi_status)
            show_educational_tooltip('rsi')
        
        with col2:
            # MACD
            macd = last['MACD']
            macd_signal = last['MACD_Signal']
            macd_status = "Bullish" if macd > macd_signal else "Bearish"
            st.metric("MACD", f"{macd:.2f}", macd_status)
            show_educational_tooltip('macd')
        
        with col3:
            # Bollinger Bands
            price = last['Close']
            bb_upper = last['BB_Upper']
            bb_position = (price - last['BB_Lower']) / (bb_upper - last['BB_Lower']) * 100
            bb_status = "High" if bb_position > 80 else "Low" if bb_position < 20 else "Mid"
            st.metric("Bollinger Position", bb_status)
            show_educational_tooltip('bollinger')
        
        with col4:
            # Current Price
            st.metric("Current Price", f"₹{last['Close']:.2f}")
        
        # Gann Analysis
        st.subheader("🎯 Gann Analysis")
        try:
            price_data = data['data']['Close'].tolist()
            current_price = last['Close']
            gann_signal = gann_trading_signal(price_data, current_price)
            
            if "BULLISH" in gann_signal:
                st.markdown(f'<div class="signal-buy">{gann_signal}</div>', unsafe_allow_html=True)
            elif "BEARISH" in gann_signal:
                st.markdown(f'<div class="signal-sell">{gann_signal}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="signal-wait">{gann_signal}</div>', unsafe_allow_html=True)
                
            show_educational_tooltip('gann')
                
        except Exception as e:
            st.info("Gann analysis unavailable for this symbol")

# ----------- OPTION CHAIN TAB ----------- #
elif app_mode == "Option Chain":
    st.markdown('<div class="section-header">🔗 Option Chain Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        symbol = st.selectbox("Select Symbol:", ["NIFTY", "BANKNIFTY"], index=0)
    
    with col2:
        st.write("")
        st.write("")
        if st.button("Fetch Option Data", type="primary", use_container_width=True):
            with st.spinner("Fetching option chain..."):
                option_data = get_option_chain_data(symbol)
                st.session_state.option_data = option_data
    
    # Display Option Data
    if 'option_data' in st.session_state:
        data = st.session_state.option_data
        
        if data['success']:
            st.success("Option data fetched successfully!")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Underlying Price", f"₹{data['underlying']:.2f}")
            col2.metric("PCR", f"{data['pcr']:.2f}")
            col3.metric("Last Updated", data['timestamp'][:19] if data['timestamp'] != 'N/A' else 'N/A')
            
            # PCR Interpretation
            st.subheader("📊 PCR Analysis")
            pcr = data['pcr']
            if pcr > 1.2:
                st.warning("**High PCR (>1.2):** Bearish sentiment - More Put buying")
            elif pcr < 0.8:
                st.success("**Low PCR (<0.8):** Bullish sentiment - More Call buying") 
            else:
                st.info("**Neutral PCR (0.8-1.2):** Balanced market sentiment")
                
            show_educational_tooltip('pcr')
            
        else:
            st.error("Could not fetch option chain data. Please try again later.")

# ----------- INTRADAY SIGNALS TAB ----------- #
else:
    st.markdown('<div class="section-header">⚡ Intraday Signals</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        symbol = st.selectbox("Symbol:", ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS"], index=0)
    
    with col2:
        interval = st.selectbox("Interval:", ["5m", "15m", "1h"], index=0)
    
    with col3:
        st.write("")
        st.write("")
        if st.button("Generate Signal", type="primary", use_container_width=True):
            with st.spinner("Analyzing intraday data..."):
                try:
                    df = fetch_intraday(symbol, "1d", interval)
                    if not df.empty:
                        df = add_vwap_and_ema(df)
                        last = df.iloc[-1]
                        
                        # Simple intraday signal
                        price = last['Close']
                        vwap = last['VWAP']
                        ema9 = last['EMA9']
                        ema21 = last['EMA21']
                        
                        bullish = (price > vwap) and (ema9 > ema21)
                        bearish = (price < vwap) and (ema9 < ema21)
                        
                        if bullish:
                            signal = "🟢 BUY - Bullish intraday bias"
                        elif bearish:
                            signal = "🔴 SELL - Bearish intraday bias"
                        else:
                            signal = "🟡 WAIT - No clear bias"
                        
                        st.session_state.intraday_signal = {
                            'signal': signal,
                            'price': price,
                            'vwap': vwap,
                            'ema9': ema9,
                            'ema21': ema21,
                            'success': True
                        }
                    else:
                        st.session_state.intraday_signal = {'success': False}
                        
                except Exception as e:
                    st.error(f"Intraday analysis error: {e}")
                    st.session_state.intraday_signal = {'success': False}
    
    # Display Intraday Signal
    if 'intraday_signal' in st.session_state:
        data = st.session_state.intraday_signal
        
        if data['success']:
            st.success("Intraday analysis complete!")
            
            # Display Metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Current Price", f"₹{data['price']:.2f}")
            col2.metric("VWAP", f"₹{data['vwap']:.2f}")
            col3.metric("EMA 9", f"₹{data['ema9']:.2f}")
            col4.metric("EMA 21", f"₹{data['ema21']:.2f}")
            
            # Display Signal
            st.subheader("🎯 Trading Signal")
            signal = data['signal']
            if "BUY" in signal:
                st.markdown(f'<div class="signal-buy">{signal}</div>', unsafe_allow_html=True)
            elif "SELL" in signal:
                st.markdown(f'<div class="signal-sell">{signal}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="signal-wait">{signal}</div>', unsafe_allow_html=True)
            
            show_educational_tooltip('vwap')
            
            # Intraday Tips
            st.subheader("💡 Intraday Trading Tips")
            st.markdown("""
            - **Risk Management:** Never risk more than 2% of your capital on a single trade
            - **Stop Loss:** Always use stop loss to protect your capital
            - **Market Hours:** Best trading times: 9:30-11:00 AM and 2:00-3:00 PM
            - **Volume:** Confirm signals with volume analysis
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
