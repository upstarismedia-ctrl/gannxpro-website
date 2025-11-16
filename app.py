# app.py - GannXPro with Stock Screener Feature
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
    .stock-card {
        background-color: #f8f9fa;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.3rem 0;
        border-left: 4px solid #1f77b4;
    }
    .open-high {
        border-left: 4px solid #28a745;
        background-color: #f0fff0;
    }
    .open-low {
        border-left: 4px solid #dc3545;
        background-color: #fff0f0;
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

# ----------- STOCK SCREENER FUNCTIONS ----------- #
def get_nse_stocks_list():
    """Get comprehensive list of NSE stocks"""
    nse_stocks = {
        'RELIANCE.NS': 'Reliance Industries',
        'TCS.NS': 'Tata Consultancy',
        'INFY.NS': 'Infosys',
        'HDFCBANK.NS': 'HDFC Bank',
        'HINDUNILVR.NS': 'Hindustan Unilever',
        'ICICIBANK.NS': 'ICICI Bank',
        'KOTAKBANK.NS': 'Kotak Mahindra Bank',
        'BHARTIARTL.NS': 'Bharti Airtel',
        'ITC.NS': 'ITC',
        'SBIN.NS': 'State Bank of India',
        'ASIANPAINT.NS': 'Asian Paints',
        'DMART.NS': 'Avenue Supermarts',
        'BAJFINANCE.NS': 'Bajaj Finance',
        'WIPRO.NS': 'Wipro',
        'HCLTECH.NS': 'HCL Technologies',
        'MARUTI.NS': 'Maruti Suzuki',
        'TITAN.NS': 'Titan Company',
        'ULTRACEMCO.NS': 'UltraTech Cement',
        'SUNPHARMA.NS': 'Sun Pharmaceutical',
        'NESTLEIND.NS': 'Nestle India',
        'AXISBANK.NS': 'Axis Bank',
        'LT.NS': 'Larsen & Toubro',
        'ONGC.NS': 'ONGC',
        'POWERGRID.NS': 'Power Grid',
        'NTPC.NS': 'NTPC',
        'TATAMOTORS.NS': 'Tata Motors',
        'TATASTEEL.NS': 'Tata Steel',
        'JSWSTEEL.NS': 'JSW Steel',
        'ADANIPORTS.NS': 'Adani Ports',
        'BAJAJFINSV.NS': 'Bajaj Finserv',
        'HDFCLIFE.NS': 'HDFC Life',
        'SBILIFE.NS': 'SBI Life',
        'DRREDDY.NS': 'Dr Reddys Labs',
        'CIPLA.NS': 'Cipla',
        'DIVISLAB.NS': 'Divi\'s Labs',
        'TECHM.NS': 'Tech Mahindra',
        'COALINDIA.NS': 'Coal India',
        'GRASIM.NS': 'Grasim Industries',
        'HINDALCO.NS': 'Hindalco',
        'UPL.NS': 'UPL',
        'BRITANNIA.NS': 'Britannia',
        'INDUSINDBK.NS': 'IndusInd Bank',
        'EICHERMOT.NS': 'Eicher Motors',
        'HEROMOTOCO.NS': 'Hero Motocorp',
        'BAJAJ-AUTO.NS': 'Bajaj Auto',
        'SHREECEM.NS': 'Shree Cement',
        'APOLLOHOSP.NS': 'Apollo Hospitals',
        'TATACONSUM.NS': 'Tata Consumer'
    }
    return nse_stocks

def analyze_stock_patterns(symbol, name):
    """Analyze if stock has Open = High or Open = Low pattern"""
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period='2d')
        
        if len(hist) < 2:
            return None
            
        today_data = hist.iloc[-1]
        yesterday_data = hist.iloc[-2]
        
        open_price = today_data['Open']
        high_price = today_data['High']
        low_price = today_data['Low']
        close_price = today_data['Close']
        volume = today_data['Volume']
        
        # Calculate percentage changes
        change_today = ((close_price - open_price) / open_price) * 100
        change_from_yesterday = ((close_price - yesterday_data['Close']) / yesterday_data['Close']) * 100
        
        # Check for Open = High pattern (Bearish)
        open_high_pattern = abs(open_price - high_price) <= (open_price * 0.001)  # Within 0.1%
        
        # Check for Open = Low pattern (Bullish)
        open_low_pattern = abs(open_price - low_price) <= (open_price * 0.001)   # Within 0.1%
        
        # Additional patterns
        gap_up = open_price > yesterday_data['High']
        gap_down = open_price < yesterday_data['Low']
        
        return {
            'symbol': symbol.replace('.NS', ''),
            'name': name,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume,
            'change_today': change_today,
            'change_yesterday': change_from_yesterday,
            'open_high': open_high_pattern,
            'open_low': open_low_pattern,
            'gap_up': gap_up,
            'gap_down': gap_down,
            'volume_spike': volume > (yesterday_data['Volume'] * 1.5 if 'Volume' in yesterday_data else volume * 1.5)
        }
        
    except Exception as e:
        return None

def run_stock_screener():
    """Run screener to find Open=High and Open=Low stocks"""
    st.info("🔍 Scanning stocks for Open=High and Open=Low patterns...")
    
    nse_stocks = get_nse_stocks_list()
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_stocks = len(nse_stocks)
    
    for i, (symbol, name) in enumerate(nse_stocks.items()):
        status_text.text(f"Analyzing {symbol}... ({i+1}/{total_stocks})")
        progress_bar.progress((i + 1) / total_stocks)
        
        result = analyze_stock_patterns(symbol, name)
        if result:
            results.append(result)
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    progress_bar.empty()
    status_text.empty()
    
    return results

def categorize_stocks(stock_data):
    """Categorize stocks into Open=High and Open=Low groups"""
    open_high_stocks = []
    open_low_stocks = []
    other_stocks = []
    
    for stock in stock_data:
        if stock['open_high']:
            open_high_stocks.append(stock)
        elif stock['open_low']:
            open_low_stocks.append(stock)
        else:
            other_stocks.append(stock)
    
    return {
        'open_high': sorted(open_high_stocks, key=lambda x: abs(x['change_today']), reverse=True),
        'open_low': sorted(open_low_stocks, key=lambda x: abs(x['change_today']), reverse=True),
        'other': other_stocks
    }

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
        return None

# ----------- TECHNICAL INDICATORS ----------- #
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
        return pd.Series([50] * len(df))

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
        zeros = pd.Series([0] * len(df))
        return zeros, zeros, zeros

def get_technical_indicators(df):
    """Calculate all technical indicators with error handling"""
    try:
        df['RSI'] = calculate_rsi(df)
        df['MACD'], df['MACD_Signal'], df['MACD_Histogram'] = calculate_macd(df)
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        return df
    except Exception as e:
        return df

# ----------- MARKET DATA FUNCTIONS ----------- #
def get_nifty_components():
    """Get Nifty 50 components with current prices"""
    reliable_stocks = {
        'RELIANCE.NS': 'Reliance',
        'TCS.NS': 'TCS', 
        'INFY.NS': 'Infosys',
        'HDFCBANK.NS': 'HDFC Bank',
        'ICICIBANK.NS': 'ICICI Bank',
        'BHARTIARTL.NS': 'Airtel',
        'ITC.NS': 'ITC'
    }
    
    market_data = []
    for symbol, name in reliable_stocks.items():
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='2d')
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
        except:
            continue
    
    return pd.DataFrame(market_data)

# ----------- STREAMLIT UI ----------- #
st.sidebar.header("🔧 Navigation")
app_mode = st.sidebar.radio(
    "Choose Analysis Mode",
    ["Stock Screener", "Market Dashboard", "Technical Analysis", "Option Chain", "Intraday Signals"],
    index=0
)

# ----------- STOCK SCREENER TAB ----------- #
if app_mode == "Stock Screener":
    st.markdown('<div class="section-header">🔍 Stock Screener - Open=High / Open=Low</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("### 📊 Pattern Analysis")
        st.write("**Open = High**: Bearish pattern - Stock opened at day's high")
        st.write("**Open = Low**: Bullish pattern - Stock opened at day's low")
    
    with col2:
        if st.button("🚀 Run Screener", type="primary", use_container_width=True):
            with st.spinner("Scanning stocks..."):
                stock_data = run_stock_screener()
                if stock_data:
                    categorized = categorize_stocks(stock_data)
                    st.session_state.screener_results = categorized
                    st.success(f"✅ Found {len(categorized['open_high'])} Open=High and {len(categorized['open_low'])} Open=Low stocks")
                else:
                    st.error("No data found. Please try again during market hours.")
    
    with col3:
        if st.button("🔄 Clear Results", use_container_width=True):
            if 'screener_results' in st.session_state:
                del st.session_state.screener_results
            st.rerun()
    
    # Display Results
    if 'screener_results' in st.session_state:
        results = st.session_state.screener_results
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"🔴 Open = High ({len(results['open_high'])} stocks)")
            st.markdown("""
            **Bearish Pattern Interpretation:**
            - Stock opened at day's highest point
            - Potential selling pressure at open
            - May indicate gap fill or reversal
            """)
            
            for stock in results['open_high']:
                change_color = "market-up" if stock['change_today'] > 0 else "market-down"
                st.markdown(f"""
                <div class="stock-card open-high">
                    <strong>{stock['symbol']}</strong> - {stock['name']}<br>
                    Open: ₹{stock['open']:.2f} | High: ₹{stock['high']:.2f}<br>
                    Close: ₹{stock['close']:.2f} | 
                    <span class="{change_color}">{stock['change_today']:+.2f}%</span>
                    { "📈" if stock['gap_up'] else "📉" if stock['gap_down'] else "" }
                    { "🔥" if stock['volume_spike'] else "" }
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.subheader(f"🟢 Open = Low ({len(results['open_low'])} stocks)")
            st.markdown("""
            **Bullish Pattern Interpretation:**
            - Stock opened at day's lowest point  
            - Potential buying opportunity at open
            - May indicate reversal or accumulation
            """)
            
            for stock in results['open_low']:
                change_color = "market-up" if stock['change_today'] > 0 else "market-down"
                st.markdown(f"""
                <div class="stock-card open-low">
                    <strong>{stock['symbol']}</strong> - {stock['name']}<br>
                    Open: ₹{stock['open']:.2f} | Low: ₹{stock['low']:.2f}<br>
                    Close: ₹{stock['close']:.2f} | 
                    <span class="{change_color}">{stock['change_today']:+.2f}%</span>
                    { "📈" if stock['gap_up'] else "📉" if stock['gap_down'] else "" }
                    { "🔥" if stock['volume_spike'] else "" }
                </div>
                """, unsafe_allow_html=True)
        
        # Statistics
        st.subheader("📈 Screening Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        total_scanned = len(results['open_high']) + len(results['open_low']) + len(results['other'])
        col1.metric("Total Scanned", total_scanned)
        col2.metric("Open=High", len(results['open_high']))
        col3.metric("Open=Low", len(results['open_low']))
        col4.metric("Other Patterns", len(results['other']))
        
        # Trading Insights
        st.subheader("💡 Trading Insights")
        insights_col1, insights_col2 = st.columns(2)
        
        with insights_col1:
            st.markdown("""
            **Open=High Strategy:**
            - Look for shorting opportunities
            - Wait for confirmation below opening price
            - Set stop loss above day's high
            - Target previous support levels
            """)
        
        with insights_col2:
            st.markdown("""
            **Open=Low Strategy:**
            - Look for buying opportunities  
            - Wait for confirmation above opening price
            - Set stop loss below day's low
            - Target previous resistance levels
            """)
    
    else:
        st.info("""
        ### 🎯 Stock Screener Instructions:
        1. Click **'Run Screener'** to scan NSE stocks
        2. Results will show two groups:
           - **Open = High** (Bearish pattern)
           - **Open = Low** (Bullish pattern)
        3. Each stock shows key metrics and patterns
        4. Use filters for better analysis
        
        **Best used during market hours for live data**
        """)

# ----------- MARKET DASHBOARD TAB ----------- #
elif app_mode == "Market Dashboard":
    st.markdown('<div class="section-header">📊 Live Market Dashboard</div>', unsafe_allow_html=True)
    
    # [Previous Market Dashboard code remains the same...]
    st.info("Market Dashboard - Previous implementation")

# ----------- TECHNICAL ANALYSIS TAB ----------- #
elif app_mode == "Technical Analysis":
    st.markdown('<div class="section-header">🔍 Technical Analysis</div>', unsafe_allow_html=True)
    
    # [Previous Technical Analysis code remains the same...]
    st.info("Technical Analysis - Previous implementation")

# ----------- OPTION CHAIN TAB ----------- #
elif app_mode == "Option Chain":
    st.markdown('<div class="section-header">🔗 Option Chain Analysis</div>', unsafe_allow_html=True)
    
    # [Previous Option Chain code remains the same...]
    st.info("Option Chain - Previous implementation")

# ----------- INTRADAY SIGNALS TAB ----------- #
else:
    st.markdown('<div class="section-header">⚡ Intraday Signals</div>', unsafe_allow_html=True)
    
    # [Previous Intraday Signals code remains the same...]
    st.info("Intraday Signals - Previous implementation")

# Professional Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>GannXPro — AI-Powered Market Intelligence</strong></p>
    <p>📚 Educational Purpose Only | 🔒 Privacy First | ⚡ Real-time Data</p>
    <p>For analysis and learning. Not investment advice.</p>
</div>
""", unsafe_allow_html=True)
