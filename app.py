# gannxpro_app.py
"""
GannXPro — AI-Powered Market Intelligence (Ultimate Desktop Version)
Features:
- Option Chain Pro (NSE indices + stocks)
- Intraday Pro (VWAP + EMA cloud bias)
- Signals & Greeks (quick CE/PE bias + Black–Scholes Greeks)
This app is for analysis/education only. It does NOT place any trades.
"""

from __future__ import annotations
import os
import time
import math
import json
from datetime import datetime
from typing import Dict, Any

import requests
import pandas as pd
import numpy as np
import yfinance as yf
from math import log, sqrt, exp
from scipy.stats import norm

import PySimpleGUI as sg

# ----------- BASIC CONFIG ----------- #

APP_NAME = "GannXPro — AI-Powered Market Intelligence"
HISTORY_YEARS = 2
SHORT_SMA = 20
LONG_SMA = 50

NSE_BASE = "https://www.nseindia.com"
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
)

# Make sure assets folder exists
os.makedirs("assets", exist_ok=True)


# ----------- NSE OPTION CHAIN HELPERS ----------- #

def nse_get(path: str, params=None, retries: int = 3, backoff: float = 1.0) -> Dict[str, Any]:
    """Call NSE endpoint with simple in-memory caching."""
    url = NSE_BASE + path
    cache_key = f"{url}::{json.dumps(params, sort_keys=True) if params else ''}"

    if not hasattr(nse_get, "_cache"):
        nse_get._cache = {}  # type: ignore
    cache = nse_get._cache  # type: ignore

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


def fetch_option_chain_nse_index(symbol: str) -> Dict[str, Any]:
    path = f"/api/option-chain-indices?symbol={symbol}"
    return nse_get(path)


def fetch_option_chain_nse_stock(symbol: str) -> Dict[str, Any]:
    path = f"/api/option-chain-equities?symbol={symbol}"
    return nse_get(path)


def parse_option_chain_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    """Convert NSE JSON into compact dict: {expiries: {exp:[rows]}, underlying, lastUpdated}"""
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

    result["lastUpdated"] = records.get("timestamp") or records.get(
        "records", {}
    ).get("timestamp")

    for r in rows:
        exp = r.get("expiryDate") or r.get("expiry") or "UNKNOWN"
        if exp not in result["expiries"]:
            result["expiries"][exp] = []
        result["expiries"][exp].append(r)
    return result


def compute_pcr_by_oi(oc: Dict[str, Any], expiry: str) -> float:
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


def compute_max_pain(oc: Dict[str, Any], expiry: str) -> float:
    rows = oc["expiries"].get(expiry, [])
    if not rows:
        return float("nan")
    strikes = sorted(
        {
            r.get("strikePrice") or r.get("strike")
            for r in rows
            if r.get("strikePrice") or r.get("strike")
        }
    )
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


def fetch_history(ticker: str, years: int = HISTORY_YEARS) -> pd.DataFrame:
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


def enriched_option_buyer_score(
    ticker: str, oc_parsed: Dict[str, Any], expiry: str | None
) -> dict:
    """Combine simple trend + patterns + volume + chain (PCR, IV) into a score 0–100."""
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

def fetch_intraday(ticker: str, period: str = "5d", interval: str = "5m") -> pd.DataFrame:
    tk = normalize_ticker_yf(ticker)
    df = yf.Ticker(tk).history(period=period, interval=interval)
    if df.empty:
        raise RuntimeError("No intraday data")
    return df


def add_vwap_and_ema(df: pd.DataFrame) -> pd.DataFrame:
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


# ----------- UI LAYOUT ----------- #

sg.theme("DarkGrey14")

# --- Option Chain Pro tab --- #
opt_layout = [
    [
        sg.Text("Ticker:"),
        sg.Input("NIFTY", key="-OPT_TICK-", size=(12, 1)),
        sg.Text("Type:"),
        sg.Radio("Index", "OPT_TYPE", key="-OPT_IDX-", default=True),
        sg.Radio("Stock", "OPT_TYPE", key="-OPT_STK-"),
        sg.Button("Fetch Chain", key="-OPT_FETCH-"),
    ],
    [
        sg.Text("Expiry:"),
        sg.Combo([], key="-OPT_EXPIRY-", size=(30, 1)),
        sg.Button("Analyze Expiry", key="-OPT_ANALYZE-"),
    ],
    [sg.Text("Summary:")],
    [sg.Multiline("", key="-OPT_SUMMARY-", size=(100, 12), disabled=True)],
]

# --- Intraday Pro tab --- #
intraday_layout = [
    [
        sg.Text("Ticker:"),
        sg.Input("BANKNIFTY", key="-INT_TICK-", size=(12, 1)),
        sg.Text("Period:"),
        sg.Combo(["1d", "5d", "1mo"], default_value="5d", key="-INT_PERIOD-", size=(6, 1)),
        sg.Text("Interval:"),
        sg.Combo(["5m", "15m"], default_value="5m", key="-INT_INTERVAL-", size=(6, 1)),
        sg.Button("Analyze Intraday", key="-INT_RUN-"),
    ],
    [sg.Text("Intraday Output:")],
    [sg.Multiline("", key="-INT_OUT-", size=(100, 16), disabled=True)],
]

# --- Signals & Greeks tab --- #
signals_layout = [
    [
        sg.Text("Ticker for Signal:"),
        sg.Input("NIFTY", key="-SIG_TICK-", size=(12, 1)),
        sg.Button("Generate Option Signal", key="-SIG_RUN-"),
    ],
    [sg.Text("Signal Output:")],
    [sg.Multiline("", key="-SIG_OUT-", size=(100, 8), disabled=True)],
    [sg.HorizontalSeparator()],
    [sg.Text("Quick Greeks Calculator (Black–Scholes)")],
    [
        sg.Text("S (Underlying):"),
        sg.Input("20000", key="-GR_S-", size=(10, 1)),
        sg.Text("K (Strike):"),
        sg.Input("20000", key="-GR_K-", size=(10, 1)),
        sg.Text("Days to Expiry:"),
        sg.Input("7", key="-GR_DAYS-", size=(5, 1)),
    ],
    [
        sg.Text("IV %:"),
        sg.Input("15", key="-GR_IV-", size=(6, 1)),
        sg.Text("Risk-free %:"),
        sg.Input("6", key="-GR_R-", size=(6, 1)),
        sg.Text("Type:"),
        sg.Combo(["CE", "PE"], default_value="CE", key="-GR_TYPE-", size=(4, 1)),
        sg.Button("Calc Greeks", key="-GR_RUN-"),
    ],
    [sg.Multiline("", key="-GR_OUT-", size=(100, 8), disabled=True)],
]

# --- Header (Logo + Title) --- #

header_row = [
    sg.Image("assets/gannx_logo.png", size=(80, 80), pad=((10, 20), (10, 5))),
    sg.Column(
        [
            [sg.Text("GannXPro", font=("Helvetica", 20, "bold"))],
            [sg.Text("AI-Powered Market Intelligence", font=("Helvetica", 11))],
        ],
        vertical_alignment="center",
        pad=(0, 0),
    ),
]

tab_group = sg.TabGroup(
    [
        [
            sg.Tab("Option Chain Pro", opt_layout),
            sg.Tab("Intraday Pro", intraday_layout),
            sg.Tab("Signals & Greeks", signals_layout),
        ]
    ]
)

layout = [
    header_row,
    [sg.HorizontalSeparator()],
    [tab_group],
]

icon_path = "assets/gannx_logo.ico"
if not os.path.exists(icon_path):
    icon_path = None

window = sg.Window(APP_NAME, layout, size=(1100, 650), finalize=True, icon=icon_path)
# ----------- EVENT LOOP ----------- #

oc_parsed_cache = None
oc_symbol_cache = None

while True:
    event, values = window.read(timeout=100)
    if event in (sg.WIN_CLOSED, "Exit"):
        break

    # ----- Option Chain Pro ----- #
    if event == "-OPT_FETCH-":
        tk = values.get("-OPT_TICK-", "").strip().upper()
        if not tk:
            window["-OPT_SUMMARY-"].update("Enter a ticker (e.g. NIFTY, BANKNIFTY, RELIANCE)")
            continue
        try:
            is_index = values.get("-OPT_IDX-", True)
            window["-OPT_SUMMARY-"].update(f"Fetching option chain for {tk} ...")
            window.refresh()
            if is_index:
                oc_raw = fetch_option_chain_nse_index(tk)
            else:
                oc_raw = fetch_option_chain_nse_stock(tk)
            oc_parsed = parse_option_chain_response(oc_raw)
            oc_symbol_cache = tk
            oc_parsed_cache = oc_parsed
            exps = sorted(list(oc_parsed["expiries"].keys()))
            window["-OPT_EXPIRY-"].update(values=exps)
            summary_lines = [
                f"Symbol: {tk}",
                f"Underlying: {oc_parsed.get('underlying')}",
                f"Last Updated: {oc_parsed.get('lastUpdated')}",
                "",
                f"Available Expiries ({len(exps)}):",
                *exps,
            ]
            window["-OPT_SUMMARY-"].update("\n".join(summary_lines))
        except Exception as e:
            window["-OPT_SUMMARY-"].update(f"Error fetching chain: {e}")

    if event == "-OPT_ANALYZE-":
        if not oc_parsed_cache:
            window["-OPT_SUMMARY-"].update("No chain cached. Fetch first.")
            continue
        expiry = values.get("-OPT_EXPIRY-")
        if not expiry:
            window["-OPT_SUMMARY-"].update("Select expiry from dropdown")
            continue
        try:
            score = enriched_option_buyer_score(oc_symbol_cache, oc_parsed_cache, expiry)
            comps = score.get("components", {})
            pcr = comps.get("pcr", None)
            maxpain = comps.get("maxpain", None)
            avg_iv = comps.get("avg_iv", None)

            lines = [
                f"Symbol: {oc_symbol_cache}",
                f"Expiry: {expiry}",
                "",
                f"Combined Option Buyer Score: {score.get('score')} / 100",
                "",
                "Components:",
                f"  Trend: {comps.get('trend')}",
                f"  Pattern: {comps.get('pattern')}",
                f"  Volume: {comps.get('vol')}",
                f"  Chain Score: {comps.get('chain')}",
                "",
                f"PCR (OI): {pcr:.2f}" if isinstance(pcr, (int, float)) and not math.isnan(pcr) else "PCR (OI): N/A",
                f"Max Pain Strike: {maxpain}" if isinstance(maxpain, (int, float)) and not math.isnan(maxpain) else "Max Pain Strike: N/A",
                f"Avg IV: {avg_iv:.2f} %" if isinstance(avg_iv, (int, float)) else "Avg IV: N/A",
                "",
                "Suggested Buyer Strikes:",
                ", ".join(score.get("suggested_strikes", [])) or "No suggestions",
            ]
            window["-OPT_SUMMARY-"].update("\n".join(lines))
        except Exception as e:
            window["-OPT_SUMMARY-"].update(f"Analyze error: {e}")

    # ----- Intraday Pro ----- #
    if event == "-INT_RUN-":
        tk = values.get("-INT_TICK-", "").strip()
        if not tk:
            window["-INT_OUT-"].update("Enter ticker first")
            continue
        period = values.get("-INT_PERIOD-", "5d")
        interval = values.get("-INT_INTERVAL-", "5m")
        try:
            window["-INT_OUT-"].update("Fetching intraday data...\n")
            window.refresh()
            df_i = fetch_intraday(tk, period=period, interval=interval)
            df_i = add_vwap_and_ema(df_i)
            bias = option_bias_from_intraday(df_i)
            last = df_i.iloc[-1]
            lines = [
                f"Ticker: {tk}",
                f"Period: {period}, Interval: {interval}",
                "",
                f"Last Close: {last['Close']:.2f}",
                f"VWAP: {last['VWAP']:.2f}",
                f"EMA9: {last['EMA9']:.2f}",
                f"EMA21: {last['EMA21']:.2f}",
                "",
                f"Intraday Bias: {bias}",
                "",
                "Gann Intraday Reference Windows:",
                "  • 09:15 – Open drive",
                "  • ~10:00 – First reaction window",
                "  • ~11:15 – Secondary reaction",
                "  • ~13:30 – Major reversal / continuation",
                "  • ~14:45 – Late-day move",
            ]
            window["-INT_OUT-"].update("\n".join(lines))
        except Exception as e:
            window["-INT_OUT-"].update(f"Intraday error: {e}")

    # ----- Signals & Greeks ----- #
    if event == "-SIG_RUN-":
        tk = values.get("-SIG_TICK-", "").strip()
        if not tk:
            window["-SIG_OUT-"].update("Enter ticker first")
            continue
        try:
            df_s = fetch_intraday(tk, period="1d", interval="5m")
            df_s = add_vwap_and_ema(df_s)
            bias = option_bias_from_intraday(df_s)
            last = df_s.iloc[-1]
            lines = [
                f"Ticker: {tk}",
                f"Last Close: {last['Close']:.2f}",
                f"VWAP: {last['VWAP']:.2f}",
                f"EMA9: {last['EMA9']:.2f}, EMA21: {last['EMA21']:.2f}",
                "",
                f"Option Bias: {bias}",
                "",
                "Note: Always combine this with Option Chain + price action.",
            ]
            window["-SIG_OUT-"].update("\n".join(lines))
        except Exception as e:
            window["-SIG_OUT-"].update(f"Signal error: {e}")

    if event == "-GR_RUN-":
        try:
            S = float(values.get("-GR_S-", "0") or 0)
            K = float(values.get("-GR_K-", "0") or 0)
            days = float(values.get("-GR_DAYS-", "0") or 0)
            iv_pct = float(values.get("-GR_IV-", "0") or 0)
            r_pct = float(values.get("-GR_R-", "0") or 0)
            opt_type = values.get("-GR_TYPE-", "CE")

            T = max(days, 0) / 365.0
            sigma = max(iv_pct, 0.001) / 100.0
            r = r_pct / 100.0
            option_type = "call" if opt_type == "CE" else "put"

            price = bs_price(S, K, T, r, sigma, option_type=option_type)
            greeks = bs_greeks(S, K, T, r, sigma, option_type=option_type)

            lines = [
                f"Inputs: S={S}, K={K}, Days={days}, IV={iv_pct}%, r={r_pct}%, Type={opt_type}",
                "",
                f"Theoretical Price: {price:.2f}",
                f"Delta: {greeks['delta']:.4f}",
                f"Theta (per day): {greeks['theta']:.4f}",
                f"Vega (per 1% IV): {greeks['vega']:.4f}",
                "",
                "Note: Greeks are approximations. Use as guidance, not guarantee.",
            ]
            window["-GR_OUT-"].update("\n".join(lines))
        except Exception as e:
            window["-GR_OUT-"].update(f"Greeks error: {e}")

window.close()
