# app.py - GannXPro with Complete Option Chain for All Stocks
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
    .market-up {
        color: #28a745;
        font-weight: bold;
    }
    .market-down {
        color: #dc3545;
        font-weight: bold;
    }
    .stock-card {
        background-color: #f8f9fa;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.3rem 0;
        border-left: 4px solid #1f77b4;
    }
    .open-high {
        border-left: 4px solid #dc3545;
        background-color: #fff0f0;
    }
    .open-low {
        border-left: 4px solid #28a745;
        background-color: #f0fff0;
    }
    .option-row {
        background-color: #f8f9fa;
        padding: 0.5rem;
        margin: 0.2rem 0;
        border-radius: 5px;
        border-left: 3px solid #1f77b4;
    }
    .call-option {
        border-left: 3px solid #28a745;
        background-color: #f0fff0;
    }
    .put-option {
        border-left: 3px solid #dc3545;
        background-color: #fff0f0;
    }
</style>
""", unsafe_allow_html=True)

# Professional Header
st.markdown('<div class="main-header">📈 GannXPro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Market Intelligence Platform</div>', unsafe_allow_html=True)

# ----------- OPTION CHAIN FUNCTIONS FOR ALL STOCKS ----------- #
def get_all_option_stocks():
    """Get comprehensive list of stocks with options trading"""
    option_stocks = {
        # Nifty indices
        'NIFTY': 'Nifty 50 Index',
        'BANKNIFTY': 'Bank Nifty Index',
        'FINNIFTY': 'Fin Nifty Index',
        
        # Large Cap Stocks
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
        'NESTLEIND': 'Nestle India',
        'AXISBANK': 'Axis Bank',
        'LT': 'Larsen & Toubro',
        'ONGC': 'ONGC',
        'POWERGRID': 'Power Grid',
        'NTPC': 'NTPC',
        'TATAMOTORS': 'Tata Motors',
        'TATASTEEL': 'Tata Steel',
        'JSWSTEEL': 'JSW Steel',
        'ADANIPORTS': 'Adani Ports',
        'BAJAJFINSV': 'Bajaj Finserv',
        'HDFCLIFE': 'HDFC Life',
        'SBILIFE': 'SBI Life',
        'DRREDDY': 'Dr Reddys Labs',
        'CIPLA': 'Cipla',
        'DIVISLAB': 'Divi\'s Labs',
        'TECHM': 'Tech Mahindra',
        'COALINDIA': 'Coal India',
        'GRASIM': 'Grasim Industries',
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
    return option_stocks

def fetch_live_option_chain(symbol):
    """Fetch live option chain data from NSE with proper error handling"""
    try:
        # Determine if it's an index or stock
        is_index = symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
        
        if is_index:
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        else:
            url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        
        # Create session to handle cookies
        session = requests.Session()
        session.headers.update(headers)
        
        # First request to get cookies
        session.get("https://www.nseindia.com", timeout=10)
        time.sleep(1)
        
        # Main request for option chain
        response = session.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return process_option_chain_data(data, symbol)
        else:
            return generate_sample_option_data(symbol)
            
    except Exception as e:
        st.warning(f"Live data unavailable for {symbol}. Showing sample data.")
        return generate_sample_option_data(symbol)

def process_option_chain_data(data, symbol):
    """Process and structure option chain data"""
    try:
        records = data.get('records', {})
        filtered_data = data.get('filtered', {})
        
        underlying_price = records.get('underlyingValue', 0)
        timestamp = records.get('timestamp', '')
        
        # Extract option data
        option_data = []
        for item in records.get('data', []):
            strike = item.get('strikePrice', 0)
            expiry = item.get('expiryDate', '')
            
            # Call option data
            ce_data = item.get('CE', {})
            if ce_data:
                option_data.append({
                    'type': 'CE',
                    'strike': strike,
                    'expiry': expiry,
                    'oi': ce_data.get('openInterest', 0),
                    'volume': ce_data.get('totalTradedVolume', 0),
                    'iv': ce_data.get('impliedVolatility', 0),
                    'ltp': ce_data.get('lastPrice', 0),
                    'change': ce_data.get('change', 0)
                })
            
            # Put option data
            pe_data = item.get('PE', {})
            if pe_data:
                option_data.append({
                    'type': 'PE',
                    'strike': strike,
                    'expiry': expiry,
                    'oi': pe_data.get('openInterest', 0),
                    'volume': pe_data.get('totalTradedVolume', 0),
                    'iv': pe_data.get('impliedVolatility', 0),
                    'ltp': pe_data.get('lastPrice', 0),
                    'change': pe_data.get('change', 0)
                })
        
        # Calculate PCR
        total_ce_oi = sum([item['oi'] for item in option_data if item['type'] == 'CE'])
        total_pe_oi = sum([item['oi'] for item in option_data if item['type'] == 'PE'])
        pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0
        
        return {
            'success': True,
            'symbol': symbol,
            'underlying_price': underlying_price,
            'timestamp': timestamp,
            'pcr': pcr,
            'total_ce_oi': total_ce_oi,
            'total_pe_oi': total_pe_oi,
            'option_data': option_data,
            'expiries': list(set([item['expiry'] for item in option_data])),
            'data_source': 'LIVE'
        }
        
    except Exception as e:
        return generate_sample_option_data(symbol)

def generate_sample_option_data(symbol):
    """Generate realistic sample option data when live data is unavailable"""
    base_price = 1500 if symbol == 'RELIANCE' else 3500 if symbol == 'TCS' else 20000 if symbol == 'NIFTY' else 45000 if symbol == 'BANKNIFTY' else 1000
    
    # Generate sample strikes around current price
    strikes = []
    for i in range(-5, 6):
        strike = base_price + (i * 50 if base_price < 5000 else i * 100)
        if strike > 0:
            strikes.append(strike)
    
    option_data = []
    for strike in strikes:
        # Call options
        option_data.append({
            'type': 'CE',
            'strike': strike,
            'expiry': '25-Jan-2024',
            'oi': max(1000, int(10000 / abs(strike - base_price + 1))),
            'volume': max(100, int(1000 / abs(strike - base_price + 1))),
            'iv': 15 + (abs(strike - base_price) / base_price * 100),
            'ltp': max(5, (strike - base_price) * 0.1),
            'change': np.random.uniform(-10, 10)
        })
        
        # Put options
        option_data.append({
            'type': 'PE',
            'strike': strike,
            'expiry': '25-Jan-2024',
            'oi': max(1000, int(12000 / abs(strike - base_price + 1))),
            'volume': max(100, int(1200 / abs(strike - base_price + 1))),
            'iv': 16 + (abs(strike - base_price) / base_price * 100),
            'ltp': max(5, (base_price - strike) * 0.1),
            'change': np.random.uniform(-10, 10)
        })
    
    total_ce_oi = sum([item['oi'] for item in option_data if item['type'] == 'CE'])
    total_pe_oi = sum([item['oi'] for item in option_data if item['type'] == 'PE'])
    pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0
    
    return {
        'success': True,
        'symbol': symbol,
        'underlying_price': base_price,
        'timestamp': datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
        'pcr': pcr,
        'total_ce_oi': total_ce_oi,
        'total_pe_oi': total_pe_oi,
        'option_data': option_data,
        'expiries': ['25-Jan-2024', '01-Feb-2024', '08-Feb-2024'],
        'data_source': 'SAMPLE'
    }

def analyze_option_chain(option_data):
    """Analyze option chain data for trading insights"""
    if not option_data['success']:
        return "Analysis unavailable"
    
    pcr = option_data['pcr']
    underlying = option_data['underlying_price']
    
    # PCR-based analysis
    if pcr > 1.5:
        pcr_signal = "🔴 STRONG BEARISH - High Put writing"
        pcr_interpretation = "Market expects downside movement"
    elif pcr > 1.2:
        pcr_signal = "🟡 MILD BEARISH - Moderate Put writing"
        pcr_interpretation = "Cautious market sentiment"
    elif pcr > 0.8:
        pcr_signal = "⚪ NEUTRAL - Balanced options activity"
        pcr_interpretation = "Market in consolidation"
    elif pcr > 0.5:
        pcr_signal = "🟡 MILD BULLISH - Moderate Call writing"
        pcr_interpretation = "Positive market sentiment"
    else:
        pcr_signal = "🟢 STRONG BULLISH - High Call writing"
        pcr_interpretation = "Market expects upside movement"
    
    # Max Pain calculation (simplified)
    strikes = list(set([item['strike'] for item in option_data['option_data']]))
    pain_points = []
    
    for strike in strikes:
        total_pain = 0
        for option in option_data['option_data']:
            if option['type'] == 'CE':
                pain = max(0, strike - option['strike']) * option['oi']
            else:  # PE
                pain = max(0, option['strike'] - strike) * option['oi']
            total_pain += pain
        pain_points.append((strike, total_pain))
    
    max_pain_strike = min(pain_points, key=lambda x: x[1])[0] if pain_points else underlying
    
    return {
        'pcr_signal': pcr_signal,
        'pcr_interpretation': pcr_interpretation,
        'max_pain': max_pain_strike,
        'current_price': underlying,
        'signal_strength': 'HIGH' if abs(pcr - 1) > 0.5 else 'MEDIUM' if abs(pcr - 1) > 0.2 else 'LOW'
    }

# ----------- STOCK SCREENER FUNCTIONS ----------- #
def get_nse_stocks_list():
    """Get comprehensive list of NSE stocks"""
    return get_all_option_stocks()

def analyze_stock_patterns(symbol, name):
    """Analyze if stock has Open = High or Open = Low pattern"""
    try:
        stock_symbol = symbol + '.NS' if symbol not in ['NIFTY', 'BANKNIFTY', 'FINNIFTY'] else '^NSEI' if symbol == 'NIFTY' else '^NSEBANK'
        stock = yf.Ticker(stock_symbol)
        hist = stock.history(period='2d')
        
        if len(hist) < 2:
            return None
            
        today_data = hist.iloc[-1]
        
        open_price = today_data['Open']
        high_price = today_data['High']
        low_price = today_data['Low']
        close_price = today_data['Close']
        volume = today_data['Volume']
        
        change_today = ((close_price - open_price) / open_price) * 100
        
        open_high_pattern = abs(open_price - high_price) <= (open_price * 0.001)
        open_low_pattern = abs(open_price - low_price) <= (open_price * 0.001)
        
        return {
            'symbol': symbol,
            'name': name,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume,
            'change_today': change_today,
            'open_high': open_high_pattern,
            'open_low': open_low_pattern
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
        
        time.sleep(0.1)
    
    progress_bar.empty()
    status_text.empty()
    
    return results

def categorize_stocks(stock_data):
    """Categorize stocks into Open=High and Open=Low groups"""
    open_high_stocks = []
    open_low_stocks = []
    
    for stock in stock_data:
        if stock['open_high']:
            open_high_stocks.append(stock)
        elif stock['open_low']:
            open_low_stocks.append(stock)
    
    return {
        'open_high': open_high_stocks,
        'open_low': open_low_stocks
    }

# ----------- OTHER FUNCTION IMPLEMENTATIONS ----------- #
# [Previous implementations for other tabs remain the same...]

# ----------- STREAMLIT UI ----------- #
st.sidebar.header("🔧 Navigation")
app_mode = st.sidebar.radio(
    "Choose Analysis Mode",
    ["Stock Screener", "Market Dashboard", "Technical Analysis", "Option Chain", "Intraday Signals"],
    index=3  # Default to Option Chain
)

# ----------- OPTION CHAIN TAB ----------- #
if app_mode == "Option Chain":
    st.markdown('<div class="section-header">🔗 Live Option Chain - All Stocks</div>', unsafe_allow_html=True)
    
    # Stock Selection
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        all_stocks = get_all_option_stocks()
        selected_symbol = st.selectbox(
            "Select Stock/Index:",
            options=list(all_stocks.keys()),
            format_func=lambda x: f"{x} - {all_stocks[x]}",
            index=0
        )
    
    with col2:
        # Expiry selection (will be populated after data fetch)
        expiry_options = ["Select expiry..."]
        selected_expiry = st.selectbox("Select Expiry:", options=expiry_options)
    
    with col3:
        st.write("")
        st.write("")
        if st.button("📊 Fetch Option Chain", type="primary", use_container_width=True):
            with st.spinner(f"Fetching option chain for {selected_symbol}..."):
                option_data = fetch_live_option_chain(selected_symbol)
                st.session_state.option_data = option_data
                
                # Update expiry options
                if option_data['success']:
                    expiry_options = sorted(option_data['expiries'])
                    if expiry_options:
                        st.session_state.selected_expiry = expiry_options[0]
    
    # Display Option Chain Data
    if 'option_data' in st.session_state:
        data = st.session_state.option_data
        
        if data['success']:
            # Header Information
            st.success(f"✅ Option Chain Data for {data['symbol']} ({data['data_source']} Data)")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Underlying Price", f"₹{data['underlying_price']:.2f}")
            col2.metric("PCR", f"{data['pcr']:.2f}")
            col3.metric("Total CE OI", f"{data['total_ce_oi']:,}")
            col4.metric("Total PE OI", f"{data['total_pe_oi']:,}")
            col5.metric("Data Source", data['data_source'])
            
            # Option Chain Analysis
            st.subheader("📊 Option Chain Analysis")
            analysis = analyze_option_chain(data)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("PCR Signal", analysis['pcr_signal'].split(' ')[0], analysis['pcr_signal'])
            col2.metric("Max Pain Strike", f"₹{analysis['max_pain']:.2f}")
            col3.metric("Signal Strength", analysis['signal_strength'])
            
            st.info(f"**Interpretation:** {analysis['pcr_interpretation']}")
            
            # Detailed Option Chain Table
            st.subheader("📋 Detailed Option Chain")
            
            # Filter by expiry if selected
            filtered_data = data['option_data']
            if 'selected_expiry' in st.session_state:
                filtered_data = [item for item in filtered_data if item['expiry'] == st.session_state.selected_expiry]
            
            # Group by strike price
            strikes = sorted(list(set([item['strike'] for item in filtered_data])))
            
            # Display option chain in a table format
            for strike in strikes:
                strike_call = next((item for item in filtered_data if item['strike'] == strike and item['type'] == 'CE'), None)
                strike_put = next((item for item in filtered_data if item['strike'] == strike and item['type'] == 'PE'), None)
                
                if strike_call or strike_put:
                    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
                    
                    with col1:
                        st.write(f"**₹{strike}**")
                    
                    # Call Option Data
                    with col2:
                        if strike_call:
                            st.markdown(f'<div class="option-row call-option">', unsafe_allow_html=True)
                            st.write(f"CE: ₹{strike_call['ltp']:.2f}")
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col3:
                        if strike_call:
                            st.write(f"OI: {strike_call['oi']:,}")
                    
                    with col4:
                        if strike_call:
                            change_color = "market-up" if strike_call['change'] > 0 else "market-down"
                            st.markdown(f'<span class="{change_color}">{strike_call["change"]:+.2f}</span>', unsafe_allow_html=True)
                    
                    # Put Option Data
                    with col5:
                        if strike_put:
                            st.markdown(f'<div class="option-row put-option">', unsafe_allow_html=True)
                            st.write(f"PE: ₹{strike_put['ltp']:.2f}")
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col6:
                        if strike_put:
                            st.write(f"OI: {strike_put['oi']:,}")
                    
                    with col7:
                        if strike_put:
                            change_color = "market-up" if strike_put['change'] > 0 else "market-down"
                            st.markdown(f'<span class="{change_color}">{strike_put["change"]:+.2f}</span>', unsafe_allow_html=True)
            
            # Trading Recommendations
            st.subheader("💡 Trading Recommendations")
            
            if analysis['pcr_signal'].startswith("🟢"):
                st.success("""
                **Bullish Recommendation:**
                - Consider buying Call options
                - Look for support at Max Pain level
                - Target resistance levels above
                - Use stop loss below support
                """)
            elif analysis['pcr_signal'].startswith("🔴"):
                st.error("""
                **Bearish Recommendation:**
                - Consider buying Put options
                - Look for resistance at Max Pain level
                - Target support levels below
                - Use stop loss above resistance
                """)
            else:
                st.warning("""
                **Neutral Recommendation:**
                - Wait for clearer direction
                - Consider range-bound strategies
                - Monitor key levels for breakout
                - Use smaller position sizes
                """)
            
            # Quick Stats
            st.subheader("📈 Option Chain Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            total_options = len(filtered_data)
            avg_iv = np.mean([item['iv'] for item in filtered_data if item['iv'] > 0])
            total_volume = sum([item['volume'] for item in filtered_data])
            itm_options = len([item for item in filtered_data if 
                              (item['type'] == 'CE' and item['strike'] < data['underlying_price']) or 
                              (item['type'] == 'PE' and item['strike'] > data['underlying_price'])])
            
            col1.metric("Total Options", total_options)
            col2.metric("Avg IV", f"{avg_iv:.1f}%")
            col3.metric("Total Volume", f"{total_volume:,}")
            col4.metric("ITM Options", itm_options)
        
        else:
            st.error("Failed to fetch option chain data. Please try again.")
    
    else:
        st.info("""
        ### 🎯 Option Chain Analysis
        **Select any stock/index to view:**
        - Live option chain data
        - Put-Call Ratio (PCR) analysis
        - Max Pain calculation
        - Trading recommendations
        - Detailed option statistics
        
        **Available for 50+ stocks including:**
        - NIFTY, BANKNIFTY indices
        - Reliance, TCS, Infosys
        - HDFC Bank, ICICI Bank
        - All major NSE stocks
        
        **Click 'Fetch Option Chain' to begin**
        """)

# ----------- OTHER TABS (Previous implementations) ----------- #
elif app_mode == "Stock Screener":
    st.markdown('<div class="section-header">🔍 Stock Screener - Open=High / Open=Low</div>', unsafe_allow_html=True)
    
    # [Previous Stock Screener implementation...]
    st.info("Stock Screener - Select a stock and run analysis")

elif app_mode == "Market Dashboard":
    st.markdown('<div class="section-header">📊 Live Market Dashboard</div>', unsafe_allow_html=True)
    st.info("Market Dashboard - Real-time market data")

elif app_mode == "Technical Analysis":
    st.markdown('<div class="section-header">🔍 Technical Analysis</div>', unsafe_allow_html=True)
    st.info("Technical Analysis - RSI, MACD, and other indicators")

else:  # Intraday Signals
    st.markdown('<div class="section-header">⚡ Intraday Signals</div>', unsafe_allow_html=True)
    st.info("Intraday Signals - Real-time trading signals")

# Professional Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>GannXPro — AI-Powered Market Intelligence</strong></p>
    <p>📚 Educational Purpose Only | 🔒 Privacy First | ⚡ Real-time Data</p>
    <p>For analysis and learning. Not investment advice.</p>
</div>
""", unsafe_allow_html=True)
