# app.py - CLEAN STREAMLIT VERSION
import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import numpy as np
from datetime import datetime

# Website setup
st.set_page_config(
    page_title="GannXPro - Market Intelligence",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📈 GannXPro - AI Powered Market Intelligence")
st.markdown("**Professional Stock & Options Analysis**")

# Sidebar
st.sidebar.header("🔧 Navigation")
app_mode = st.sidebar.selectbox(
    "Choose Analysis",
    ["Stock Analysis", "Option Chain", "Intraday Signals", "Market Overview"]
)

# Function to get stock data
def get_stock_data(ticker, period="1y"):
    try:
        if not ticker.endswith('.NS') and not ticker.startswith('^'):
            ticker += '.NS'
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        return hist
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Function to calculate simple indicators
def calculate_indicators(df):
    if df.empty:
        return df
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['EMA_12'] = df['Close'].ewm(span=12).mean()
    df['EMA_26'] = df['Close'].ewm(span=26).mean()
    return df

# Stock Analysis Page
if app_mode == "Stock Analysis":
    st.header("📊 Stock Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ticker = st.text_input("Enter Stock Symbol:", "RELIANCE")
        period = st.selectbox("Time Period", ["1mo", "3mo", "6mo", "1y", "2y"])
    
    with col2:
        st.write("")  # spacer
        st.write("")  # spacer
        if st.button("Analyze Stock", type="primary"):
            with st.spinner("Analyzing stock data..."):
                data = get_stock_data(ticker, period)
                
                if not data.empty:
                    data = calculate_indicators(data)
                    current_price = data['Close'].iloc[-1]
                    sma_20 = data['SMA_20'].iloc[-1]
                    sma_50 = data['SMA_50'].iloc[-1]
                    
                    # Display metrics
                    st.success("Analysis Complete!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Current Price", f"₹{current_price:.2f}")
                    col2.metric("SMA 20", f"₹{sma_20:.2f}")
                    col3.metric("SMA 50", f"₹{sma_50:.2f}")
                    
                    # Trend analysis
                    if sma_20 > sma_50:
                        trend = "📈 Bullish"
                        col4.metric("Trend", trend)
                    else:
                        trend = "📉 Bearish" 
                        col4.metric("Trend", trend)
                    
                    # Display chart
                    st.subheader("Price Chart")
                    st.line_chart(data[['Close', 'SMA_20', 'SMA_50']])
                    
                    # Volume chart
                    st.subheader("Volume")
                    st.bar_chart(data['Volume'])
                else:
                    st.error("No data found. Try: RELIANCE, TCS, INFY, HDFC")

# Option Chain Page
elif app_mode == "Option Chain":
    st.header("🔗 Option Chain Analysis")
    
    st.info("""
    **Option Chain Features Coming Soon:**
    - Put-Call Ratio (PCR)
    - Max Pain Theory
    - Open Interest Analysis
    - Implied Volatility
    """)
    
    st.subheader("Popular Option Symbols")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**NIFTY** - Nifty 50 Index")
        st.write("**BANKNIFTY** - Bank Nifty Index")
    
    with col2:
        st.write("**RELIANCE** - Reliance Industries")
        st.write("**TCS** - Tata Consultancy")
    
    with col3:
        st.write("**INFY** - Infosys")
        st.write("**HDFC** - HDFC Bank")

# Intraday Signals Page
elif app_mode == "Intraday Signals":
    st.header("⚡ Intraday Trading Signals")
    
    col1, col2 = st.columns(2)
    
    with col1:
        symbol = st.text_input("Symbol for Intraday:", "BANKNIFTY")
        if st.button("Generate Signal", type="primary"):
            with st.spinner("Generating intraday signal..."):
                # Simple signal logic
                data = get_stock_data(symbol, "1d")
                if not data.empty:
                    current = data['Close'].iloc[-1]
                    high = data['High'].max()
                    low = data['Low'].min()
                    
                    st.success("Signal Generated!")
                    
                    if current > (high + low) / 2:
                        signal = "🟢 BUY - Bullish Bias"
                        st.success(signal)
                    else:
                        signal = "🔴 SELL - Bearish Bias" 
                        st.warning(signal)
                    
                    st.metric("Current Price", f"₹{current:.2f}")
                    st.metric("Day Range", f"₹{low:.2f} - ₹{high:.2f}")

# Market Overview Page
else:
    st.header("🌍 Market Overview")
    
    st.subheader("Popular Indian Stocks")
    
    stocks = {
        "RELIANCE.NS": "Reliance Industries",
        "TCS.NS": "Tata Consultancy", 
        "INFY.NS": "Infosys",
        "HDFCBANK.NS": "HDFC Bank",
        "HINDUNILVR.NS": "Hindustan Unilever",
        "ITC.NS": "ITC Limited",
        "SBIN.NS": "State Bank of India"
    }
    
    for symbol, name in stocks.items():
        with st.expander(f"{name} ({symbol.replace('.NS', '')})"):
            try:
                stock_data = yf.Ticker(symbol)
                hist = stock_data.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    st.metric("Current Price", f"₹{price:.2f}")
                else:
                    st.write("Data not available")
            except:
                st.write("Loading...")

# Footer
st.markdown("---")
st.markdown("""
**📚 Educational Purpose Only**  
This tool is for learning and analysis. Not investment advice.

**🆓 Free & Open**  
No payments required. Always free to use.

**🔒 Privacy First**  
We don't store your data or personal information.
""")
