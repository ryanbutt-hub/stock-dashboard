"""
================================================================================
SMART STOCK ADVISOR DASHBOARD  —  app.py
================================================================================
Plain-English guided dashboard for beginner-to-intermediate investors.

Install:
    pip install streamlit yfinance pandas numpy plotly pandas-ta
                finnhub-python requests

Run:
    streamlit run app.py
================================================================================
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sqlite3
import time
import datetime
import requests
import warnings
import json

warnings.filterwarnings("ignore")

# Anthropic client for AI advisor
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import finnhub
    HAS_FINNHUB = True
except ImportError:
    HAS_FINNHUB = False

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Stock Advisor",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
#  STYLING  — Clean dark finance aesthetic
#  Inspired by Bloomberg Terminal + modern fintech
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=IBM+Plex+Mono:wght@300;400;500&family=Inter:wght@300;400;500&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #080b12;
    color: #e2e8f0;
}
.main { background: #080b12; padding-top: 0.5rem; }
h1,h2,h3 { font-family: 'Syne', sans-serif; letter-spacing: -0.02em; }
code, .mono { font-family: 'IBM Plex Mono', monospace; }

/* ── Traffic Light Cards ── */
.tl-green {
    background: linear-gradient(135deg, #0a2218 0%, #0f2d1e 100%);
    border: 1px solid #00e676; border-left: 4px solid #00e676;
    border-radius: 10px; padding: 16px; margin: 6px 0;
    box-shadow: 0 0 20px rgba(0,230,118,0.08);
}
.tl-yellow {
    background: linear-gradient(135deg, #201a08 0%, #2a2208 100%);
    border: 1px solid #ffd600; border-left: 4px solid #ffd600;
    border-radius: 10px; padding: 16px; margin: 6px 0;
    box-shadow: 0 0 20px rgba(255,214,0,0.08);
}
.tl-red {
    background: linear-gradient(135deg, #200a0a 0%, #2d0f0f 100%);
    border: 1px solid #ff1744; border-left: 4px solid #ff1744;
    border-radius: 10px; padding: 16px; margin: 6px 0;
    box-shadow: 0 0 20px rgba(255,23,68,0.08);
}

/* ── Score badge ── */
.score-num {
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem; font-weight: 800;
    line-height: 1;
}
.score-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.75rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
}

/* ── Metric cards ── */
.metric-box {
    background: #0e1420; border: 1px solid #1e2840;
    border-radius: 8px; padding: 12px 14px;
    text-align: center; height: 100%;
}
.metric-box .label {
    font-size: 0.68rem; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.08em;
    margin-bottom: 4px;
}
.metric-box .value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.1rem; font-weight: 500; color: #e2e8f0;
}
.metric-box .delta-pos { color: #00e676; font-size: 0.8rem; }
.metric-box .delta-neg { color: #ff1744; font-size: 0.8rem; }
.metric-box .explain {
    font-size: 0.62rem; color: #475569; margin-top: 3px;
    font-style: italic;
}

/* ── Advice box ── */
.advice-box {
    background: #0e1420; border: 1px solid #1e2840;
    border-radius: 10px; padding: 16px; margin: 8px 0;
}
.advice-box h4 {
    font-family: 'Syne', sans-serif; font-size: 0.9rem;
    color: #94a3b8; margin: 0 0 8px 0;
    text-transform: uppercase; letter-spacing: 0.08em;
}
.advice-text {
    font-size: 0.92rem; line-height: 1.6; color: #cbd5e1;
}

/* ── Alert pill ── */
.alert-pill {
    display: inline-block; padding: 3px 10px;
    border-radius: 20px; font-size: 0.72rem;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 500; margin: 2px;
}
.pill-red   { background: rgba(255,23,68,0.15);  color: #ff6b6b; border: 1px solid rgba(255,23,68,0.3); }
.pill-green { background: rgba(0,230,118,0.12);  color: #69f0ae; border: 1px solid rgba(0,230,118,0.3); }
.pill-amber { background: rgba(255,214,0,0.12);  color: #ffd600; border: 1px solid rgba(255,214,0,0.3); }
.pill-blue  { background: rgba(41,182,246,0.12); color: #4fc3f7; border: 1px solid rgba(41,182,246,0.3); }

/* ── Section header ── */
.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.4rem; font-weight: 700;
    color: #f1f5f9; margin: 24px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e2840;
}

/* ── Regime badge ── */
.regime-bull {
    background: rgba(0,230,118,0.1); border: 1px solid #00e676;
    color: #00e676; padding: 6px 16px; border-radius: 20px;
    font-family: 'Syne', sans-serif; font-size: 0.8rem;
    font-weight: 700; letter-spacing: 0.1em; display: inline-block;
}
.regime-bear {
    background: rgba(255,23,68,0.1); border: 1px solid #ff1744;
    color: #ff1744; padding: 6px 16px; border-radius: 20px;
    font-family: 'Syne', sans-serif; font-size: 0.8rem;
    font-weight: 700; letter-spacing: 0.1em; display: inline-block;
}
.regime-neutral {
    background: rgba(255,214,0,0.1); border: 1px solid #ffd600;
    color: #ffd600; padding: 6px 16px; border-radius: 20px;
    font-family: 'Syne', sans-serif; font-size: 0.8rem;
    font-weight: 700; letter-spacing: 0.1em; display: inline-block;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px; background: transparent;
    border-bottom: 1px solid #1e2840;
}
.stTabs [data-baseweb="tab"] {
    background: #0e1420; border: 1px solid #1e2840;
    border-radius: 6px 6px 0 0; padding: 8px 20px;
    font-family: 'Syne', sans-serif; font-size: 0.82rem;
    font-weight: 600; color: #64748b;
    letter-spacing: 0.04em;
}
.stTabs [aria-selected="true"] {
    background: #1e2840 !important; color: #e2e8f0 !important;
    border-bottom: 2px solid #00e676 !important;
}

/* ── Streamlit metric override ── */
div[data-testid="stMetric"] {
    background: #0e1420; border: 1px solid #1e2840;
    border-radius: 8px; padding: 10px 14px;
}
div[data-testid="stMetricLabel"] { font-size: 0.7rem !important; color: #64748b !important; }
div[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.1rem !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0a0e18 !important;
    border-right: 1px solid #1e2840;
}
[data-testid="stSidebar"] .stButton button {
    width: 100%;
    background: #1e2840; border: 1px solid #2d3f60;
    color: #94a3b8; border-radius: 6px;
    font-family: 'Syne', sans-serif; font-size: 0.8rem;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: #2d3f60; color: #e2e8f0;
}

/* ── Dataframe ── */
.stDataFrame { border: 1px solid #1e2840 !important; border-radius: 8px !important; }

/* ── Divider ── */
hr { border-color: #1e2840 !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #0e1420 !important;
    border: 1px solid #1e2840 !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 0.88rem !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────
DB_PATH = "advisor_journal.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            direction TEXT,
            entry_date TEXT, exit_date TEXT,
            entry_price REAL, exit_price REAL,
            shares REAL, pnl REAL, pnl_pct REAL,
            r_multiple REAL,
            stop_price REAL, target_price REAL,
            strategy TEXT, setup_tag TEXT, notes TEXT,
            mistake_type TEXT,
            risk_score_at_entry REAL,
            mfe REAL, mae REAL,
            rule_violation INTEGER DEFAULT 0,
            emotional_state TEXT,
            thesis TEXT,
            deviation_from_plan TEXT,
            exit_reason TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migrate existing DB — add new columns if they don't exist yet
    for col, typedef in [
        ("emotional_state", "TEXT"),
        ("thesis", "TEXT"),
        ("deviation_from_plan", "TEXT"),
        ("exit_reason", "TEXT"),
    ]:
        try:
            c.execute(f"ALTER TABLE trades ADD COLUMN {col} {typedef}")
        except Exception:
            pass  # Column already exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            ticker TEXT PRIMARY KEY,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT, alert_type TEXT, message TEXT,
            risk_score REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
_defaults = {
    "paused": False,
    "refresh_interval": 60,
    "last_refresh": 0,
    "finnhub_key": "",
    "anthropic_key": "",
    "scanner_results": [],
    "scanner_last_run": 0,
    "risk_weights": {"technical": 40, "fundamental": 30,
                     "sentiment": 20, "performance": 10},
    "account_size": 10000.0,
    "max_risk_pct": 1.0,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p style="font-family:Syne,sans-serif;font-size:1.2rem;font-weight:800;color:#00e676;margin:0">💹 Smart Advisor</p>', unsafe_allow_html=True)
    st.caption("Your personal stock research assistant")
    st.divider()

    # Pause toggle
    paused = st.toggle("⏸  Pause all scanning", value=st.session_state.paused,
                        help="Stops all background data fetching. Saves battery.")
    st.session_state.paused = paused
    if paused:
        st.warning("🔋 Scanning paused")
    else:
        st.success("✅ Scanning active")

    st.divider()
    st.markdown("**⏱ How often to refresh**")
    refresh_sec = st.slider("Seconds between updates", 30, 300,
                             st.session_state.refresh_interval, 10)
    st.session_state.refresh_interval = refresh_sec
    if refresh_sec < 60:
        st.warning("Under 60 seconds may trigger Yahoo Finance rate limits.")

    st.divider()
    st.markdown("**📋 My Watchlist**")
    st.caption("These are the stocks you want to track.")
    new_ticker = st.text_input("Add a stock symbol:", placeholder="e.g. AAPL").upper().strip()
    if st.button("➕ Add to watchlist") and new_ticker:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT OR IGNORE INTO watchlist (ticker) VALUES (?)", (new_ticker,))
        conn.commit()
        conn.close()
        st.success(f"Added {new_ticker}")

    conn = sqlite3.connect(DB_PATH)
    wl_df = pd.read_sql("SELECT ticker FROM watchlist ORDER BY ticker", conn)
    conn.close()
    watchlist = wl_df["ticker"].tolist() if not wl_df.empty else []

    for t in watchlist:
        c1, c2 = st.columns([3, 1])
        c1.write(f"• {t}")
        if c2.button("✕", key=f"del_{t}"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM watchlist WHERE ticker=?", (t,))
            conn.commit()
            conn.close()
            st.rerun()

    st.divider()
    st.markdown("**💰 My Account**")
    st.caption("Used to calculate how many shares you should buy.")
    st.session_state.account_size = st.number_input(
        "Total account size ($)", min_value=100.0, value=st.session_state.account_size,
        step=500.0, format="%.0f")
    st.session_state.max_risk_pct = st.slider(
        "Max % to risk per trade", 0.5, 5.0,
        st.session_state.max_risk_pct, 0.25,
        help="Most professionals risk 1-2% of their account per trade.")

    st.divider()
    st.markdown("**🔑 News API Key (optional)**")
    finnhub_key = st.text_input("Finnhub key", value=st.session_state.finnhub_key,
                                 type="password", help="Free at finnhub.io")
    st.session_state.finnhub_key = finnhub_key

    st.markdown("**🤖 Anthropic API Key (for AI advisor)**")
    anthropic_key = st.text_input(
        "Anthropic key",
        value=st.session_state.anthropic_key,
        type="password",
        help="Free at console.anthropic.com — needed for AI written analysis."
    )
    st.session_state.anthropic_key = anthropic_key

    st.divider()
    st.markdown("**⚖️ Score Weights**")
    st.caption("How much each factor counts toward the final score.")
    w_t = st.slider("Chart signals %",   0, 100, st.session_state.risk_weights["technical"],   5)
    w_f = st.slider("Company health %",  0, 100, st.session_state.risk_weights["fundamental"], 5)
    w_s = st.slider("Market mood %",     0, 100, st.session_state.risk_weights["sentiment"],   5)
    w_p = st.slider("Your track record %", 0, 100, st.session_state.risk_weights["performance"], 5)
    total = w_t + w_f + w_s + w_p
    if total != 100:
        st.error(f"Weights add up to {total}% — must equal 100%")
    else:
        st.session_state.risk_weights = {
            "technical": w_t, "fundamental": w_f,
            "sentiment": w_s, "performance": w_p
        }


# ─────────────────────────────────────────────
#  DATA LAYER
# ─────────────────────────────────────────────

@st.cache_data(ttl=55)
def fetch_prices(ticker: str, period: str = "6mo", interval: str = "1d"):
    """Download price history from Yahoo Finance (free, 15-min delayed)."""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return None
        df.index = pd.to_datetime(df.index)
        return df.dropna()
    except Exception:
        return None


@st.cache_data(ttl=300)
def fetch_company_info(ticker: str) -> dict:
    """Download company financial data from Yahoo Finance."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "name":           info.get("longName", ticker),
            "sector":         info.get("sector", "Unknown"),
            "industry":       info.get("industry", "Unknown"),
            "pe":             info.get("trailingPE"),
            "forward_pe":     info.get("forwardPE"),
            "pb":             info.get("priceToBook"),
            "eps_growth":     info.get("earningsGrowth"),
            "rev_growth":     info.get("revenueGrowth"),
            "debt_equity":    info.get("debtToEquity"),
            "roe":            info.get("returnOnEquity"),
            "fcf":            info.get("freeCashflow"),
            "market_cap":     info.get("marketCap"),
            "short_pct":      info.get("shortPercentOfFloat"),
            "inst_pct":       info.get("heldPercentInstitutions"),
            "insider_pct":    info.get("heldPercentInsiders"),
            "price":          info.get("currentPrice") or info.get("regularMarketPrice"),
            "52w_high":       info.get("fiftyTwoWeekHigh"),
            "52w_low":        info.get("fiftyTwoWeekLow"),
            "avg_vol":        info.get("averageVolume"),
            "beta":           info.get("beta"),
            "earnings_date":  info.get("earningsTimestamp"),
            "dividend_yield": info.get("dividendYield"),
            "target_price":   info.get("targetMeanPrice"),
        }
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def fetch_options_ratio(ticker: str) -> dict:
    """Get the put/call ratio from options data. Shows how many people are betting up vs down."""
    try:
        tk = yf.Ticker(ticker)
        exps = tk.options
        if not exps:
            return {}
        chain = tk.option_chain(exps[0])
        calls = chain.calls["volume"].sum()
        puts  = chain.puts["volume"].sum()
        return {
            "put_call_ratio": round(puts / calls, 3) if calls > 0 else None,
            "calls": int(calls), "puts": int(puts)
        }
    except Exception:
        return {}


@st.cache_data(ttl=1800)
def fetch_vix():
    """Get the VIX fear gauge. Above 30 = panic, below 15 = calm."""
    try:
        h = yf.Ticker("^VIX").history(period="5d")
        return round(h["Close"].iloc[-1], 2) if not h.empty else None
    except Exception:
        return None


@st.cache_data(ttl=1800)
def fetch_fear_greed() -> dict:
    """Approximate market mood on a 0 (extreme fear) to 100 (extreme greed) scale."""
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
        d = r.json()["data"][0]
        return {"value": int(d["value"]), "label": d["value_classification"]}
    except Exception:
        return {"value": 50, "label": "Neutral"}


@st.cache_data(ttl=900)
def fetch_market_regime() -> dict:
    """
    Analyse the overall market health.
    Uses SPY (large stocks), QQQ (tech), IWM (small stocks) and breadth data.
    """
    try:
        results = {}
        for sym, name in [("SPY","Large stocks"),("QQQ","Tech stocks"),("IWM","Small stocks")]:
            df = fetch_prices(sym, period="1y")
            if df is not None and len(df) >= 200:
                close = df["Close"]
                ema20  = close.ewm(span=20).mean().iloc[-1]
                ema50  = close.ewm(span=50).mean().iloc[-1]
                ema200 = close.ewm(span=200).mean().iloc[-1]
                price  = close.iloc[-1]
                mo1m   = (price / close.iloc[-21] - 1) * 100 if len(close) >= 21 else 0
                mo3m   = (price / close.iloc[-63] - 1) * 100 if len(close) >= 63 else 0
                results[sym] = {
                    "name": name, "price": price,
                    "above_20ema": price > ema20,
                    "above_50ema": price > ema50,
                    "above_200ema": price > ema200,
                    "mo1m": mo1m, "mo3m": mo3m,
                }
        # Sector ETFs
        sectors = {
            "XLK":"Technology","XLF":"Finance","XLE":"Energy",
            "XLV":"Healthcare","XLI":"Industrials","XLC":"Comms",
            "XLY":"Consumer Cyclical","XLP":"Consumer Staples",
            "XLB":"Materials","XLRE":"Real Estate","XLU":"Utilities"
        }
        sector_perf = {}
        for sym, name in sectors.items():
            df = fetch_prices(sym, period="3mo")
            if df is not None and len(df) >= 21:
                mo1m = (df["Close"].iloc[-1] / df["Close"].iloc[-21] - 1) * 100
                sector_perf[name] = round(mo1m, 2)

        # Build regime label
        spy_data = results.get("SPY", {})
        if spy_data.get("above_200ema") and spy_data.get("above_50ema"):
            regime = "BULL MARKET"
            regime_class = "regime-bull"
            regime_advice = ("The overall market is healthy and trending up. "
                             "This is a good environment to look for buying opportunities, "
                             "especially in the strongest sectors shown below.")
        elif not spy_data.get("above_200ema"):
            regime = "BEAR MARKET"
            regime_class = "regime-bear"
            regime_advice = ("The overall market is in a downtrend. "
                             "Be very cautious about buying stocks. "
                             "Consider holding more cash or only trading the best setups.")
        else:
            regime = "MIXED MARKET"
            regime_class = "regime-neutral"
            regime_advice = ("The market is sending mixed signals. "
                             "It is neither clearly going up nor down. "
                             "Be selective — only take the highest-confidence opportunities.")

        return {
            "indices": results, "sectors": sector_perf,
            "regime": regime, "regime_class": regime_class,
            "regime_advice": regime_advice
        }
    except Exception as e:
        return {"regime": "UNKNOWN", "regime_class": "regime-neutral",
                "regime_advice": "Could not load market data.", "indices": {}, "sectors": {}}


@st.cache_data(ttl=1800)
def fetch_earnings_flag(ticker: str) -> dict:
    """Check if earnings (quarterly results announcement) is coming up soon."""
    try:
        info = yf.Ticker(ticker).info
        ts = info.get("earningsTimestamp")
        if ts:
            earnings_dt = datetime.datetime.fromtimestamp(ts)
            days_away   = (earnings_dt - datetime.datetime.now()).days
            return {"date": earnings_dt.strftime("%Y-%m-%d"), "days_away": days_away}
    except Exception:
        pass
    return {"date": None, "days_away": None}


def fetch_news(ticker: str) -> list:
    """Get recent news headlines for a stock via Finnhub (requires free API key)."""
    key = st.session_state.finnhub_key
    if not key or not HAS_FINNHUB:
        return []
    try:
        client = finnhub.Client(api_key=key)
        today    = datetime.date.today()
        week_ago = today - datetime.timedelta(days=7)
        news = client.company_news(ticker,
                                    _from=week_ago.strftime("%Y-%m-%d"),
                                    to=today.strftime("%Y-%m-%d"))
        return news[:8]
    except Exception:
        return []


# ─────────────────────────────────────────────
#  TECHNICAL INDICATORS
# ─────────────────────────────────────────────

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all chart-based signals on the price data.
    These are the lines and shapes you see on stock charts.
    """
    if df is None or len(df) < 26:
        return df
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]

    # Moving averages — smooth out day-to-day noise to reveal the trend
    for span, col in [(9,"EMA9"),(20,"EMA20"),(50,"EMA50"),(200,"EMA200")]:
        df[col] = c.ewm(span=span, adjust=False).mean()

    # RSI — measures if a stock is being bought too aggressively (overbought) or sold too hard (oversold)
    delta = c.diff()
    gain  = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
    loss  = (-delta).clip(lower=0).ewm(com=13, adjust=False).mean()
    df["RSI"] = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))

    # MACD — compares two moving averages to show momentum direction
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    df["MACD"]         = ema12 - ema26
    df["MACD_Signal"]  = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"]    = df["MACD"] - df["MACD_Signal"]

    # VWAP — the average price weighted by how much was traded; institutions use this as a benchmark
    tp = (h + l + c) / 3
    df["VWAP"] = (tp * v).cumsum() / v.replace(0, np.nan).cumsum()

    # OBV — tracks whether volume is flowing into or out of a stock
    obv = [0]
    for i in range(1, len(c)):
        if c.iloc[i] > c.iloc[i-1]:   obv.append(obv[-1] + v.iloc[i])
        elif c.iloc[i] < c.iloc[i-1]: obv.append(obv[-1] - v.iloc[i])
        else:                          obv.append(obv[-1])
    df["OBV"] = obv

    # Bollinger Bands — show when a stock is unusually high or low relative to recent history
    sma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    df["BB_Upper"] = sma20 + 2 * std20
    df["BB_Lower"] = sma20 - 2 * std20
    df["BB_Mid"]   = sma20

    # ATR — average daily range; used to set sensible stop-loss levels
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    df["ATR14"] = tr.rolling(14).mean()

    # Volume ratio — how today's volume compares to the 20-day average
    df["AvgVol20"] = v.rolling(20).mean()
    df["VolRatio"]  = v / df["AvgVol20"].replace(0, np.nan)

    # Relative Strength vs SPY — shows if stock is stronger or weaker than the overall market
    spy_df = fetch_prices("SPY", period="6mo")
    if spy_df is not None and len(spy_df) >= len(df):
        spy_close = spy_df["Close"].reindex(df.index, method="nearest")
        spy_norm  = spy_close / spy_close.iloc[0]
        stk_norm  = c / c.iloc[0]
        df["RS_SPY"] = (stk_norm / spy_norm) * 100
    else:
        df["RS_SPY"] = 100.0

    return df


# ─────────────────────────────────────────────
#  SCORING ENGINE
# ─────────────────────────────────────────────

"""
HOW THE SCORE WORKS — PLAIN ENGLISH

Your score is a number from 0 to 100 built from 4 parts:

  1. CHART SIGNALS (default 40%):
     We look at the stock's price chart. Is it trending up?
     Is buying pressure building? Are the chart "health checks" positive?

  2. COMPANY HEALTH (default 30%):
     We look at the company's finances. Is it profitable?
     Is it growing? Does it have manageable debt?

  3. MARKET MOOD (default 20%):
     We look at investor sentiment. Is the overall market calm or panicking?
     Are there more buyers or sellers right now?

  4. YOUR TRACK RECORD (default 10%):
     We look at your personal trade history. Have you done well
     with this type of setup before?

RESULT:
  Score 80–100 → 🟢 LOW RISK / LOWER POTENTIAL RETURN  (safer bet)
  Score 50–79  → 🟡 MEDIUM RISK / MEDIUM RETURN         (balanced)
  Score 0–49   → 🔴 HIGH RISK / HIGHER POTENTIAL RETURN (speculative)

NOTE: High risk does not mean "don't buy." It means go in smaller,
set a tighter stop-loss, and be prepared to exit quickly.
"""

def _score_chart_signals(df, info) -> tuple:
    """
    Score the chart (technical) signals out of 100.
    Checks: trend direction, momentum, volume, and price patterns.
    """
    bd = {}
    score = 0
    if df is None or df.empty:
        return 0, {"No chart data": 0}

    last = df.iloc[-1]
    price = last["Close"]

    # Trend direction — is price above its moving averages?
    ema_pts = 0
    labels  = []
    for col, pts, label in [("EMA9",5,"9-day trend"),("EMA20",5,"20-day trend"),
                              ("EMA50",8,"50-day trend"),("EMA200",7,"200-day trend")]:
        if col in df.columns:
            if price > last[col]:
                ema_pts += pts
                labels.append(f"✓ {label}")
            else:
                labels.append(f"✗ {label}")
    bd[f"Trend direction ({', '.join(labels[:2])})"] = ema_pts
    score += ema_pts

    # Momentum — is buying or selling pressure stronger?
    rsi_pts = 0
    if "RSI" in df.columns:
        rsi = last["RSI"]
        if 45 <= rsi <= 60:   rsi_pts = 20  # Sweet spot
        elif 40 <= rsi <= 65: rsi_pts = 14
        elif 35 <= rsi <= 70: rsi_pts = 8
        else:                  rsi_pts = 0   # Too extreme
        bd[f"Momentum — RSI (Relative Strength Index) = {rsi:.0f}"] = rsi_pts
    score += rsi_pts

    # MACD signal — is momentum turning up or down?
    macd_pts = 0
    if "MACD" in df.columns:
        macd = last["MACD"]
        sig  = last["MACD_Signal"]
        hist = last.get("MACD_Hist", 0)
        if macd > sig and hist > 0:  macd_pts = 25
        elif macd > sig:             macd_pts = 15
        elif macd > 0:               macd_pts = 8
        bd["Momentum direction (MACD)"] = macd_pts
    score += macd_pts

    # Volume — is there real buying interest?
    vol_pts = 0
    if "VolRatio" in df.columns:
        vr = last["VolRatio"]
        if 1.3 <= vr <= 3.0: vol_pts = 30
        elif 1.0 <= vr:      vol_pts = 20
        else:                vol_pts = 8
        bd[f"Trading volume ({vr:.1f}x average)"] = vol_pts
    score += vol_pts

    # Relative strength vs the market
    rs_pts = 0
    if "RS_SPY" in df.columns:
        rs_vals = df["RS_SPY"].dropna()
        if len(rs_vals) >= 20:
            rs_now  = rs_vals.iloc[-1]
            rs_20da = rs_vals.iloc[-20]
            if rs_now > rs_20da and rs_now > 100:  rs_pts = 20
            elif rs_now > 100:                      rs_pts = 12
            elif rs_now > rs_20da:                  rs_pts = 8
        bd["Strength vs overall market"] = rs_pts
    score += rs_pts

    return min(int(score), 100), bd


def _score_company_health(info: dict) -> tuple:
    """
    Score the company's financial health out of 100.
    Checks: valuation, growth, debt, profitability, cash flow.
    """
    bd = {}
    score = 0
    if not info:
        return 0, {"No company data": 0}

    sector = info.get("sector", "")

    # Price vs earnings — are you paying a fair price?
    pe = info.get("pe")
    pe_pts = 0
    if pe and pe > 0:
        # Tech companies can justify higher P/E ratios than banks
        high_pe_sectors = ["Technology", "Consumer Cyclical", "Healthcare", "Communication Services"]
        limit = 35 if sector in high_pe_sectors else 20
        if pe < limit * 0.6:   pe_pts = 20
        elif pe < limit:       pe_pts = 14
        elif pe < limit * 1.5: pe_pts = 7
        else:                  pe_pts = 2
        bd[f"Valuation — Price-to-Earnings (P/E) = {pe:.1f} (sector limit: {limit})"] = pe_pts
    else:
        bd["Valuation — P/E not available"] = 0
    score += pe_pts

    # Earnings growth — is the company growing profits?
    growth = info.get("eps_growth") or info.get("rev_growth")
    gr_pts = 0
    if growth is not None:
        if growth > 0.25:   gr_pts = 20
        elif growth > 0.10: gr_pts = 14
        elif growth > 0:    gr_pts = 7
        else:               gr_pts = 0
        bd[f"Profit growth = {growth*100:.1f}%"] = gr_pts
    score += gr_pts

    # Debt level — does the company owe too much?
    de = info.get("debt_equity")
    de_pts = 0
    if de is not None:
        heavy_debt_ok = ["Utilities", "Real Estate", "Financials"]
        limit = 200 if sector in heavy_debt_ok else 80
        if de < limit * 0.4:  de_pts = 20
        elif de < limit:      de_pts = 12
        elif de < limit * 2:  de_pts = 5
        else:                 de_pts = 0
        bd[f"Debt level — Debt/Equity = {de:.0f} (sector limit: {limit})"] = de_pts
    score += de_pts

    # Return on equity — how efficiently does it use investor money?
    roe = info.get("roe")
    roe_pts = 0
    if roe:
        if roe > 0.25:   roe_pts = 20
        elif roe > 0.15: roe_pts = 14
        elif roe > 0.05: roe_pts = 7
        else:            roe_pts = 0
        bd[f"Profitability — Return on Equity (ROE) = {roe*100:.1f}%"] = roe_pts
    score += roe_pts

    # Free cash flow — does the company actually generate real cash?
    fcf = info.get("fcf")
    fcf_pts = 0
    if fcf is not None:
        fcf_pts = 20 if fcf > 0 else 0
        bd[f"Cash generation — Free Cash Flow (FCF) = {'positive ✓' if fcf > 0 else 'negative ✗'}"] = fcf_pts
    score += fcf_pts

    return min(int(score), 100), bd


def _score_market_mood(info: dict, opts: dict, fear_greed: dict, vix) -> tuple:
    """
    Score current market sentiment out of 100.
    Checks: overall market mood, fear levels, options bets, short selling pressure.
    """
    bd = {}
    score = 0

    # Fear & Greed index
    fg = fear_greed.get("value", 50)
    fg_label = fear_greed.get("label", "Neutral")
    if fg >= 60:   fg_pts = 28
    elif fg >= 40: fg_pts = 18
    elif fg >= 25: fg_pts = 10
    else:          fg_pts = 4
    bd[f"Market mood — Fear & Greed Index = {fg} ({fg_label})"] = fg_pts
    score += fg_pts

    # VIX — market fear gauge
    vix_pts = 0
    if vix:
        if vix < 15:   vix_pts = 28
        elif vix < 20: vix_pts = 20
        elif vix < 25: vix_pts = 12
        elif vix < 30: vix_pts = 6
        else:          vix_pts = 0
        bd[f"Market fear level — VIX (Volatility Index) = {vix}"] = vix_pts
    score += vix_pts

    # Put/call ratio — are more people betting up or down?
    pc = opts.get("put_call_ratio")
    pc_pts = 0
    if pc:
        if pc < 0.6:   pc_pts = 24
        elif pc < 0.8: pc_pts = 18
        elif pc < 1.0: pc_pts = 12
        elif pc < 1.2: pc_pts = 5
        bd[f"Options bets — Put/Call Ratio = {pc:.2f} (below 1.0 = more buyers)"] = pc_pts
    score += pc_pts

    # Short interest — how many people are betting the stock will fall?
    sp = info.get("short_pct") or 0
    si_pts = 0
    if sp < 0.03:   si_pts = 20
    elif sp < 0.08: si_pts = 14
    elif sp < 0.15: si_pts = 7
    else:           si_pts = 0
    bd[f"Short sellers — {sp*100:.1f}% of shares are short (below 8% = healthy)"] = si_pts
    score += si_pts

    return min(int(score), 100), bd


def _score_track_record(ticker: str, setup_tag: str = None) -> tuple:
    """
    Score based on YOUR personal trading history with similar setups.
    If you have no history yet, returns a neutral 50.
    """
    bd = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        q = "SELECT * FROM trades WHERE pnl IS NOT NULL"
        params = []
        if ticker:
            q += " AND ticker=?"
            params.append(ticker)
        trades = pd.read_sql(q, conn, params=params)

        # Also look at setup-level history
        all_trades = pd.read_sql("SELECT * FROM trades WHERE pnl IS NOT NULL", conn)
        conn.close()

        if trades.empty:
            bd["No trade history yet — using neutral score"] = 50
            return 50, bd

        wr    = (trades["pnl"] > 0).mean()
        avgw  = trades[trades["pnl"] > 0]["pnl_pct"].mean() or 0
        avgl  = trades[trades["pnl"] < 0]["pnl_pct"].mean() or 0
        exp   = (wr * avgw) + ((1 - wr) * avgl)
        n     = len(trades)

        if wr > 0.65 and exp > 0.02:  pts = 90
        elif wr > 0.5 and exp > 0:    pts = 70
        elif exp > 0:                  pts = 55
        elif exp < -0.03:              pts = 15
        else:                          pts = 40

        bd[f"Your win rate with {ticker} = {wr*100:.0f}% over {n} trades"] = pts
        bd[f"Average outcome per trade = {exp*100:+.1f}%"] = ""
    except Exception as e:
        bd["Error reading history"] = 50
        pts = 50

    return pts, bd


def calculate_score(ticker, df, info, opts, fear_greed, vix) -> dict:
    """
    Combine all four sub-scores into a final verdict with advice.
    This is the main 'brain' of the advisor.
    """
    W = st.session_state.risk_weights

    t_raw, t_bd = _score_chart_signals(df, info)
    f_raw, f_bd = _score_company_health(info)
    s_raw, s_bd = _score_market_mood(info, opts, fear_greed, vix)
    p_raw, p_bd = _score_track_record(ticker)

    final = (
        t_raw * W["technical"]    / 100 +
        f_raw * W["fundamental"]  / 100 +
        s_raw * W["sentiment"]    / 100 +
        p_raw * W["performance"]  / 100
    )
    final = round(final, 1)

    if final >= 80:
        label = "LOW RISK"
        color = "#00e676"
        css   = "tl-green"
        emoji = "🟢"
        return_profile = "Lower potential return, but higher probability of success"
        advice = _build_advice(ticker, "LOW", final, t_raw, f_raw, s_raw, info, df)
    elif final >= 50:
        label = "MEDIUM RISK"
        color = "#ffd600"
        css   = "tl-yellow"
        emoji = "🟡"
        return_profile = "Moderate return potential with moderate uncertainty"
        advice = _build_advice(ticker, "MEDIUM", final, t_raw, f_raw, s_raw, info, df)
    else:
        label = "HIGH RISK"
        color = "#ff1744"
        css   = "tl-red"
        emoji = "🔴"
        return_profile = "Higher potential return, but higher chance of loss"
        advice = _build_advice(ticker, "HIGH", final, t_raw, f_raw, s_raw, info, df)

    return {
        "score": final, "label": label, "color": color, "css": css,
        "emoji": emoji, "return_profile": return_profile, "advice": advice,
        "t_score": t_raw, "f_score": f_raw, "s_score": s_raw, "p_score": p_raw,
        "breakdowns": {"Chart Signals": t_bd, "Company Health": f_bd,
                       "Market Mood": s_bd, "Your Track Record": p_bd}
    }


def _build_advice(ticker, level, score, t, f, s, info, df) -> str:
    """
    Generate plain-English advisor commentary based on the scores.
    This is your 'financial advisor' summary.
    """
    lines = []
    name = info.get("name", ticker)
    sector = info.get("sector", "")
    price = info.get("price")
    target = info.get("target_price")

    # Opening verdict
    if level == "LOW":
        lines.append(f"<strong>{name} ({ticker}) looks like a relatively safe opportunity right now.</strong>")
        lines.append(f"Most of the signals we check are pointing in the right direction. "
                     f"This does not mean it is risk-free — all investing carries risk — "
                     f"but the conditions are more favourable than average.")
    elif level == "MEDIUM":
        lines.append(f"<strong>{name} ({ticker}) is a mixed picture — proceed carefully.</strong>")
        lines.append(f"Some signals are positive but others are not. "
                     f"This is the kind of trade you should size smaller than usual "
                     f"and watch closely after entering.")
    else:
        lines.append(f"<strong>{name} ({ticker}) is showing several warning signs right now.</strong>")
        lines.append(f"High risk does not mean 'never buy this.' It means the current "
                     f"conditions are stacked against you. If you do trade it, use a "
                     f"very tight stop-loss and keep your position size small.")

    # What's driving the score
    weakest = min(t, f, s)
    if weakest == t and t < 50:
        lines.append("⚠️ The chart signals are weak — the stock may not be in a clear uptrend yet. "
                     "Consider waiting for a better entry point.")
    if weakest == f and f < 50:
        lines.append("⚠️ The company's finances need attention — this could be a structurally weak business "
                     "or one going through a difficult period. Check the breakdown below for specifics.")
    if weakest == s and s < 50:
        lines.append("⚠️ Market mood is working against this trade — when the overall market is nervous, "
                     "even good stocks can fall. Make sure you have a plan if it drops.")

    # Analyst target
    if target and price:
        upside = (target / price - 1) * 100
        if upside > 15:
            upside_str = f"{upside:.0f}"
            lines.append(f"📊 Analyst consensus price target is ${target:.2f} — that is {upside_str}% above the current price of ${price:.2f}.")
        elif upside < -5:
            lines.append(f"📊 Analyst consensus target of ${target:.2f} is below the current price — analysts may think it is overvalued.")

    # Earnings warning
    earnings = fetch_earnings_flag(ticker)
    if earnings.get("days_away") is not None:
        da = earnings["days_away"]
        if 0 <= da <= 14:
            lines.append(f"⚡ EARNINGS WARNING: This company reports quarterly results in "
                         f"{da} day(s) (around {earnings['date']}). Stocks can move sharply — "
                         f"up or down — after earnings. Consider waiting until after the announcement "
                         f"unless you are comfortable with that risk.")
        elif 0 <= da <= 30:
            lines.append(f"📅 Earnings announcement expected in about {da} days ({earnings['date']}). "
                         f"Keep this in mind when deciding how long to hold.")

    # ATR-based stop suggestion
    if df is not None and "ATR14" in df.columns and price:
        atr = df["ATR14"].iloc[-1]
        stop = price - 1.5 * atr
        lines.append(f"🛡 Suggested stop-loss level: ${stop:.2f} (1.5× the Average True Range below current price). "
                     f"This gives the trade room to breathe without risking too much.")

    return "<br><br>".join(lines)


# ─────────────────────────────────────────────
#  POSITION SIZING CALCULATOR
# ─────────────────────────────────────────────

def calculate_position_size(account: float, risk_pct: float,
                              price: float, stop: float) -> dict:
    """
    Work out exactly how many shares to buy and what your maximum dollar loss is.

    The formula:
      Dollar risk  = account size × max risk %
      Shares       = dollar risk ÷ (entry price − stop price)
      Total cost   = shares × entry price
    """
    if price <= 0 or stop <= 0 or price <= stop:
        return {}
    dollar_risk   = account * (risk_pct / 100)
    risk_per_share = price - stop
    shares        = dollar_risk / risk_per_share
    total_cost    = shares * price
    pct_of_account = (total_cost / account) * 100
    return {
        "dollar_risk": round(dollar_risk, 2),
        "risk_per_share": round(risk_per_share, 2),
        "shares": int(shares),
        "total_cost": round(total_cost, 2),
        "pct_of_account": round(pct_of_account, 1),
    }


# ─────────────────────────────────────────────
#  ANOMALY DETECTION
# ─────────────────────────────────────────────

def detect_anomalies(ticker, df, info) -> list:
    """Look for unusual patterns that need attention."""
    flags = []
    if df is None or df.empty:
        return flags

    last = df.iloc[-1]

    if "VolRatio" in df.columns and last["VolRatio"] > 3:
        flags.append({"type": "🔊 Unusual trading volume",
                      "msg": f"Volume is {last['VolRatio']:.1f}× the 20-day average — something may be happening.",
                      "level": "WARN"})
    if "RSI" in df.columns:
        rsi = last["RSI"]
        if rsi > 75:
            flags.append({"type": "📈 Overbought",
                          "msg": f"RSI = {rsi:.0f} — the stock may have risen too fast and could pull back.",
                          "level": "WARN"})
        elif rsi < 25:
            flags.append({"type": "📉 Oversold",
                          "msg": f"RSI = {rsi:.0f} — the stock may have fallen too fast and could bounce.",
                          "level": "INFO"})
    if "MACD" in df.columns and len(df) > 2:
        curr = df["MACD"].iloc[-1] - df["MACD_Signal"].iloc[-1]
        prev = df["MACD"].iloc[-2] - df["MACD_Signal"].iloc[-2]
        if prev < 0 and curr > 0:
            flags.append({"type": "⚡ Momentum turning up",
                          "msg": "MACD just crossed above its signal line — a potential buy signal.",
                          "level": "BUY"})
        elif prev > 0 and curr < 0:
            flags.append({"type": "⚡ Momentum turning down",
                          "msg": "MACD just crossed below its signal line — a potential warning sign.",
                          "level": "SELL"})
    hi52 = info.get("52w_high")
    price = last["Close"]
    if hi52 and price >= hi52 * 0.98:
        flags.append({"type": "🏔 Near 52-week high",
                      "msg": f"Within 2% of its highest price in a year (${hi52:.2f}).",
                      "level": "WARN"})
    return flags

# ─────────────────────────────────────────────
#  CHARTS
# ─────────────────────────────────────────────

CHART_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="#080b12",
    plot_bgcolor="#0d1117",
    font=dict(family="IBM Plex Mono", color="#64748b", size=10),
    margin=dict(l=44, r=16, t=36, b=24),
    legend=dict(orientation="h", yanchor="bottom", y=1.01,
                xanchor="right", x=1, font=dict(size=9)),
    xaxis=dict(gridcolor="#1e2840", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#1e2840", showgrid=True, zeroline=False),
)


def build_price_chart(df, ticker) -> go.Figure:
    """Main chart: candlesticks + moving averages + volume + RSI + MACD."""
    if df is None or df.empty:
        return go.Figure()

    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True,
        row_heights=[0.50, 0.15, 0.18, 0.17],
        vertical_spacing=0.02,
        subplot_titles=(
            f"{ticker} — Price & Moving Averages",
            "Volume (how much was traded)",
            "RSI — Momentum (30=oversold, 70=overbought)",
            "MACD — Momentum direction"
        )
    )

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="Price",
        increasing=dict(line=dict(color="#00e676"), fillcolor="rgba(0,230,118,0.6)"),
        decreasing=dict(line=dict(color="#ff1744"), fillcolor="rgba(255,23,68,0.6)")
    ), row=1, col=1)

    # Bollinger Bands
    if "BB_Upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"], name="Upper Band",
            line=dict(color="#334155", width=1, dash="dot"), showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"], name="Lower Band",
            line=dict(color="#334155", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(51,65,85,0.08)", showlegend=False), row=1, col=1)

    # EMAs
    ema_cfg = [("EMA9","#f97316","9-day avg"),("EMA20","#38bdf8","20-day avg"),
               ("EMA50","#a78bfa","50-day avg"),("EMA200","#fb7185","200-day avg")]
    for col, clr, nm in ema_cfg:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[col], name=nm,
                line=dict(color=clr, width=1.3), opacity=0.9), row=1, col=1)

    # VWAP
    if "VWAP" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["VWAP"], name="VWAP avg",
            line=dict(color="#fbbf24", width=1.2, dash="dot"), opacity=0.7), row=1, col=1)

    # Volume
    vol_colors = ["rgba(0,230,118,0.5)" if c >= o else "rgba(255,23,68,0.5)"
                  for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume",
        marker_color=vol_colors), row=2, col=1)
    if "AvgVol20" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["AvgVol20"], name="Avg volume",
            line=dict(color="#ffd600", width=1.5)), row=2, col=1)

    # RSI
    if "RSI" in df.columns:
        rsi_colors = []
        for r in df["RSI"].fillna(50):
            if r >= 70:   rsi_colors.append("#ff1744")
            elif r <= 30: rsi_colors.append("#00e676")
            else:         rsi_colors.append("#38bdf8")
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI",
            line=dict(color="#38bdf8", width=1.5)), row=3, col=1)
        for lvl, clr in [(70,"#ff1744"),(50,"#334155"),(30,"#00e676")]:
            fig.add_hline(y=lvl, line_dash="dot", line_color=clr,
                          opacity=0.4, row=3, col=1)

    # MACD
    if "MACD" in df.columns:
        hist_clrs = ["rgba(0,230,118,0.6)" if v >= 0 else "rgba(255,23,68,0.6)"
                     for v in df["MACD_Hist"].fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], name="MACD histogram",
            marker_color=hist_clrs), row=4, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD",
            line=dict(color="#38bdf8", width=1.5)), row=4, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"], name="Signal line",
            line=dict(color="#f97316", width=1.5)), row=4, col=1)

    fig.update_layout(height=720, xaxis_rangeslider_visible=False, **CHART_THEME)
    return fig


def build_obv_chart(df) -> go.Figure:
    """OBV chart showing whether money is flowing in or out."""
    if df is None or "OBV" not in df.columns:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["OBV"], name="OBV",
        line=dict(color="#00e676", width=1.8),
        fill="tozeroy", fillcolor="rgba(0,230,118,0.06)"))
    fig.update_layout(height=220, title="Money flow — rising line means more buying than selling (OBV)",
                      **CHART_THEME)
    return fig


def build_rs_chart(df) -> go.Figure:
    """Relative Strength vs SPY chart."""
    if df is None or "RS_SPY" not in df.columns:
        return go.Figure()
    rs = df["RS_SPY"].dropna()
    above = rs >= 100
    fig = go.Figure()
    fig.add_hline(y=100, line_dash="dot", line_color="#ffd600", opacity=0.5)
    fig.add_trace(go.Scatter(x=df.index, y=rs, name="Strength vs market",
        line=dict(color="#a78bfa", width=1.8),
        fill="tozeroy", fillcolor="rgba(167,139,250,0.06)"))
    fig.update_layout(height=200,
        title="Strength vs overall market — above 100 = stronger than average",
        **CHART_THEME)
    return fig


def build_sector_chart(sector_perf: dict) -> go.Figure:
    """Bar chart of sector performance — shows which areas of the market are hot."""
    if not sector_perf:
        return go.Figure()
    df = pd.DataFrame(list(sector_perf.items()), columns=["Sector", "1-Month Return %"])
    df = df.sort_values("1-Month Return %")
    colors = ["#00e676" if v >= 0 else "#ff1744" for v in df["1-Month Return %"]]
    fig = go.Figure(go.Bar(x=df["1-Month Return %"], y=df["Sector"],
        orientation="h", marker_color=colors, text=df["1-Month Return %"].round(1),
        textposition="outside"))
    fig.update_layout(height=380,
        title="Sector performance — past month (which industries are gaining or losing)",
        **CHART_THEME)
    return fig


def build_equity_curve(trades_df: pd.DataFrame) -> go.Figure:
    """Chart of your cumulative profit/loss over time."""
    if trades_df.empty:
        return go.Figure()
    ts = trades_df.sort_values("exit_date")
    ts["equity"] = ts["pnl"].cumsum()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts["exit_date"], y=ts["equity"],
        mode="lines+markers", name="Your profit/loss",
        line=dict(color="#00e676", width=2.2),
        fill="tozeroy", fillcolor="rgba(0,230,118,0.08)"))
    fig.add_hline(y=0, line_dash="dot", line_color="#ff1744", opacity=0.3)
    fig.update_layout(height=300,
        title="Your equity curve — total profit or loss over time",
        **CHART_THEME)
    return fig


def build_pnl_by_month(trades_df: pd.DataFrame) -> go.Figure:
    """Monthly profit/loss bar chart."""
    if trades_df.empty:
        return go.Figure()
    try:
        ts = trades_df.copy()
        ts["month"] = pd.to_datetime(ts["exit_date"]).dt.to_period("M").astype(str)
        monthly = ts.groupby("month")["pnl"].sum().reset_index()
        clrs = ["#00e676" if v >= 0 else "#ff1744" for v in monthly["pnl"]]
        fig = go.Figure(go.Bar(x=monthly["month"], y=monthly["pnl"],
            marker_color=clrs))
        fig.update_layout(height=260,
            title="Profit/Loss by month — green = profitable month",
            **CHART_THEME)
        return fig
    except Exception:
        return go.Figure()


def build_mfe_mae(trades_df: pd.DataFrame) -> go.Figure:
    """Scatter plot of best vs worst point reached in each trade."""
    if trades_df.empty or "mfe" not in trades_df.columns:
        return go.Figure()
    valid = trades_df[trades_df["mfe"].notna() & trades_df["mae"].notna()]
    if valid.empty:
        return go.Figure()
    fig = go.Figure(go.Scatter(
        x=valid["mae"], y=valid["mfe"],
        mode="markers",
        marker=dict(color=valid["pnl"], colorscale="RdYlGn",
                    size=9, colorbar=dict(title="P&L $")),
        text=valid["ticker"], hoverinfo="text+x+y"
    ))
    fig.update_layout(height=320,
        title="Best vs worst point of each trade — MFE/MAE analysis",
        xaxis_title="Worst point reached (MAE %)",
        yaxis_title="Best point reached (MFE %)",
        **CHART_THEME)
    return fig


# ─────────────────────────────────────────────
#  HELPER: metric box HTML
# ─────────────────────────────────────────────

def mbox(label, value, explain="", delta=None):
    """Render a compact metric card with plain English label."""
    delta_html = ""
    if delta is not None:
        cls = "delta-pos" if str(delta).startswith("+") or (
            isinstance(delta, (int,float)) and delta >= 0) else "delta-neg"
        delta_html = f'<div class="{cls}">{delta}</div>'
    return (f'<div class="metric-box">'
            f'<div class="label">{label}</div>'
            f'<div class="value">{value}</div>'
            f'{delta_html}'
            f'<div class="explain">{explain}</div>'
            f'</div>')


def pill(text, kind="blue"):
    return f'<span class="alert-pill pill-{kind}">{text}</span>'


# ─────────────────────────────────────────────
#  TRAFFIC LIGHT LIST
# ─────────────────────────────────────────────


# ─────────────────────────────────────────────
#  ADVISOR LAYER — Four new data sources
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_analyst_consensus(ticker: str) -> dict:
    """
    Pull Wall Street analyst ratings and price targets from Yahoo Finance.
    Shows: buy/hold/sell counts, average price target, upside/downside.
    """
    try:
        tk = yf.Ticker(ticker)
        info = tk.info
        recs = tk.recommendations
        target = info.get("targetMeanPrice")
        target_low  = info.get("targetLowPrice")
        target_high = info.get("targetHighPrice")
        price = info.get("currentPrice") or info.get("regularMarketPrice")

        # Count recent analyst ratings
        buy_count  = info.get("recommendationKey", "")
        num_analysts = info.get("numberOfAnalystOpinions", 0)

        # Rating breakdown from recommendations df
        strong_buy = hold = sell = strong_sell = buy = 0
        if recs is not None and not recs.empty:
            recent = recs.tail(10)
            for col in ["strongBuy", "strong_buy"]:
                if col in recent.columns:
                    strong_buy = int(recent[col].sum())
            for col in ["buy"]:
                if col in recent.columns:
                    buy = int(recent[col].sum())
            for col in ["hold"]:
                if col in recent.columns:
                    hold = int(recent[col].sum())
            for col in ["sell"]:
                if col in recent.columns:
                    sell = int(recent[col].sum())
            for col in ["strongSell", "strong_sell"]:
                if col in recent.columns:
                    strong_sell = int(recent[col].sum())

        upside = ((target / price) - 1) * 100 if target and price else None

        return {
            "target":       target,
            "target_low":   target_low,
            "target_high":  target_high,
            "price":        price,
            "upside":       upside,
            "num_analysts": num_analysts,
            "strong_buy":   strong_buy,
            "buy":          buy,
            "hold":         hold,
            "sell":         sell,
            "strong_sell":  strong_sell,
            "rating_key":   buy_count,
        }
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def fetch_insider_activity(ticker: str) -> dict:
    """
    Pull recent insider buying and selling from Yahoo Finance.
    Insiders = company executives, directors, and major shareholders.
    When insiders buy with their own money, it is often a positive signal.
    """
    try:
        tk = yf.Ticker(ticker)
        ins = tk.insider_transactions
        if ins is None or ins.empty:
            return {"transactions": [], "net_shares": 0, "summary": "No recent insider data available."}

        ins = ins.copy()
        # Standardise column names (yfinance changes these occasionally)
        ins.columns = [c.lower().replace(" ", "_") for c in ins.columns]

        transactions = []
        net_shares = 0

        for _, row in ins.head(10).iterrows():
            try:
                shares = int(row.get("shares", 0) or 0)
                value  = float(row.get("value", 0) or 0)
                ttype  = str(row.get("transaction", row.get("startdate", "Unknown")))
                insider = str(row.get("insider", row.get("filer_name", "Unknown")))
                date   = str(row.get("startdate", row.get("date", "")))[:10]
                is_buy = any(w in ttype.lower() for w in ["buy", "purchase", "acquired"])
                is_sell= any(w in ttype.lower() for w in ["sell", "sale", "disposed"])

                transactions.append({
                    "insider": insider[:30],
                    "type":    "BUY" if is_buy else ("SELL" if is_sell else ttype[:20]),
                    "shares":  shares,
                    "value":   value,
                    "date":    date,
                    "is_buy":  is_buy,
                })
                if is_buy:  net_shares += shares
                if is_sell: net_shares -= shares
            except Exception:
                continue

        if net_shares > 0:
            summary = f"Net insider BUYING of {net_shares:,} shares recently — insiders are putting their own money in."
        elif net_shares < 0:
            summary = f"Net insider SELLING of {abs(net_shares):,} shares recently — insiders are taking money off the table."
        else:
            summary = "Insider activity is roughly balanced between buying and selling."

        return {
            "transactions": transactions,
            "net_shares":   net_shares,
            "summary":      summary,
        }
    except Exception as e:
        return {"transactions": [], "net_shares": 0, "summary": "Could not load insider data."}


@st.cache_data(ttl=1800)
def fetch_news_sentiment(ticker: str, finnhub_key: str) -> dict:
    """
    Fetch recent news headlines and analyse their tone (bullish/bearish/neutral).
    Uses Finnhub for headlines if key provided, otherwise falls back to yfinance news.
    """
    headlines = []

    # Try Finnhub first (better quality)
    if finnhub_key and HAS_FINNHUB:
        try:
            import finnhub
            client = finnhub.Client(api_key=finnhub_key)
            today    = datetime.date.today()
            week_ago = today - datetime.timedelta(days=7)
            news = client.company_news(
                ticker,
                _from=week_ago.strftime("%Y-%m-%d"),
                to=today.strftime("%Y-%m-%d")
            )
            headlines = [{"title": a.get("headline",""), "source": a.get("source",""), "url": a.get("url","")} for a in news[:10]]
        except Exception:
            pass

    # Fallback: yfinance news
    if not headlines:
        try:
            tk = yf.Ticker(ticker)
            news = tk.news or []
            for a in news[:10]:
                title = ""
                if isinstance(a, dict):
                    # yfinance v0.2+ nests under content
                    content = a.get("content", a)
                    title = content.get("title", "") or a.get("title", "")
                headlines.append({"title": title, "source": "", "url": ""})
        except Exception:
            pass

    if not headlines:
        return {
            "headlines": [],
            "sentiment": "neutral",
            "sentiment_score": 50,
            "summary": "No recent news found.",
            "bullish_count": 0,
            "bearish_count": 0,
        }

    # Simple keyword-based sentiment scoring
    bullish_words = [
        "surge", "soar", "rally", "beat", "record", "growth", "profit",
        "upgrade", "outperform", "buy", "strong", "gain", "rise", "positive",
        "bullish", "breakthrough", "exceed", "opportunity", "boost"
    ]
    bearish_words = [
        "fall", "drop", "miss", "loss", "decline", "downgrade", "sell",
        "weak", "concern", "risk", "cut", "layoff", "lawsuit", "investigation",
        "bearish", "crash", "plunge", "fail", "disappoint", "warning", "debt"
    ]

    bullish_count = bearish_count = 0
    for h in headlines:
        title_lower = h["title"].lower()
        b = sum(1 for w in bullish_words if w in title_lower)
        s = sum(1 for w in bearish_words if w in title_lower)
        bullish_count += b
        bearish_count += s

    total = bullish_count + bearish_count
    if total == 0:
        sentiment_score = 50
        sentiment = "neutral"
    else:
        sentiment_score = int((bullish_count / total) * 100)
        if sentiment_score >= 65:   sentiment = "bullish"
        elif sentiment_score <= 35: sentiment = "bearish"
        else:                        sentiment = "neutral"

    sentiment_labels = {
        "bullish": "📈 Bullish — recent news is mostly positive",
        "bearish": "📉 Bearish — recent news is mostly negative",
        "neutral": "➡️ Neutral — mixed or low-signal news",
    }

    return {
        "headlines":       headlines,
        "sentiment":       sentiment,
        "sentiment_score": sentiment_score,
        "summary":         sentiment_labels[sentiment],
        "bullish_count":   bullish_count,
        "bearish_count":   bearish_count,
    }


def fetch_ai_analysis(ticker: str, info: dict, risk: dict,
                      analyst: dict, insider: dict,
                      news_sent: dict, regime_data: dict) -> str:
    """
    Send all available data to Claude and get a genuine plain-English
    investment analysis back. This is the AI advisor brain.
    """
    key = st.session_state.get("anthropic_key", "")
    if not key:
        return "Add your Anthropic API key in the sidebar to enable AI analysis."
    if not HAS_ANTHROPIC:
        return "Run:  pip install anthropic  then restart the app."

    try:
        client = anthropic.Anthropic(api_key=key)

        # Build a rich context prompt
        name    = info.get("name", ticker)
        sector  = info.get("sector", "Unknown")
        price   = info.get("price", "N/A")
        regime  = regime_data.get("regime", "Unknown")
        sector_perf = regime_data.get("sectors", {})
        sector_mo   = sector_perf.get(sector, None)

        analyst_summary = ""
        if analyst.get("target"):
            analyst_summary = (
                f"Wall Street analyst consensus: {analyst.get('num_analysts', '?')} analysts, "
                f"average price target ${analyst.get('target', 'N/A'):.2f} "
                f"({analyst.get('upside', 0):+.1f}% from current price). "
                f"Ratings: {analyst.get('strong_buy',0)} strong buy, "
                f"{analyst.get('buy',0)} buy, {analyst.get('hold',0)} hold, "
                f"{analyst.get('sell',0)} sell, {analyst.get('strong_sell',0)} strong sell."
            )

        insider_summary = insider.get("summary", "No insider data.")
        news_summary    = news_sent.get("summary", "No news data.")
        headlines       = [h["title"] for h in news_sent.get("headlines", [])[:5] if h["title"]]

        prompt = f"""You are a plain-English stock market advisor helping a complete beginner make informed decisions. 
Analyse the following data for {name} ({ticker}) and give a clear, honest assessment.

CURRENT DATA:
- Stock: {name} ({ticker}), Sector: {sector}
- Current price: ${price}
- Overall risk score: {risk["score"]}/100 ({risk["label"]})
- Chart signals score: {risk["t_score"]}/100
- Company financial health score: {risk["f_score"]}/100
- Market mood score: {risk["s_score"]}/100

MARKET CONTEXT:
- Overall market regime: {regime}
- {sector} sector 1-month performance: {f"{sector_mo:+.1f}%" if sector_mo else "N/A"}

WALL STREET ANALYSTS:
{analyst_summary if analyst_summary else "No analyst data available."}

INSIDER ACTIVITY (company executives buying/selling their own shares):
{insider_summary}

NEWS SENTIMENT:
{news_summary}
Recent headlines: {"; ".join(headlines) if headlines else "None available"}

KEY FINANCIALS:
- P/E ratio: {info.get("pe", "N/A")}
- EPS growth: {f"{info.get('eps_growth', 0)*100:.1f}%" if info.get("eps_growth") else "N/A"}
- Debt/Equity: {info.get("debt_equity", "N/A")}
- ROE: {f"{info.get('roe', 0)*100:.1f}%" if info.get("roe") else "N/A"}
- Free cash flow: {"Positive" if info.get("fcf") and info.get("fcf") > 0 else "Negative or N/A"}
- Short interest: {f"{info.get('short_pct', 0)*100:.1f}%" if info.get("short_pct") else "N/A"}

Write a 4-6 paragraph analysis for a beginner investor. Use plain English — no jargon without explanation. Cover:
1. What this stock is and what it does (one sentence)
2. What the data says — the strongest positive signals and the biggest concerns
3. What Wall Street analysts and company insiders are signalling
4. What the news and market mood suggest
5. A clear bottom line: is now a good time to consider buying, waiting, or avoiding? Why?

Be honest. Do not be overly positive. If there are real risks, say so clearly. 
End with one sentence on what to watch for that would change your assessment."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    except Exception as e:
        err = str(e)
        if "401" in err or "auth" in err.lower():
            return "❌ Invalid API key — check your Anthropic key in the sidebar."
        if "429" in err or "rate" in err.lower():
            return "⏳ API rate limit reached — wait a minute and try again."
        return f"❌ AI analysis unavailable: {err[:120]}"


def render_advisor_panel(ticker: str, info: dict, risk: dict,
                         analyst: dict, insider: dict,
                         news_sent: dict, regime_data: dict):
    """
    The full AI advisor panel rendered under each stock card.
    Four sections: AI analysis, news sentiment, analyst consensus, insider activity.
    """
    with st.expander(f"🤖 AI Advisor Panel — {ticker}", expanded=False):

        adv_tab1, adv_tab2, adv_tab3, adv_tab4 = st.tabs([
            "🤖 AI Analysis",
            "📰 News Sentiment",
            "🏦 Analyst Consensus",
            "🏛 Insider Activity",
        ])

        # ── TAB 1: AI WRITTEN ANALYSIS ──
        with adv_tab1:
            st.markdown(
                '<div style="font-size:0.78rem;color:#64748b;margin-bottom:10px">'
                'Claude AI reads all available data and writes a plain-English assessment. '
                'This takes 5–10 seconds to generate.'
                '</div>',
                unsafe_allow_html=True
            )
            if st.button(f"Generate AI analysis for {ticker}", key=f"ai_btn_{ticker}"):
                with st.spinner("Claude is analysing the data..."):
                    analysis = fetch_ai_analysis(
                        ticker, info, risk, analyst, insider, news_sent, regime_data
                    )
                    st.session_state[f"ai_analysis_{ticker}"] = analysis

            if f"ai_analysis_{ticker}" in st.session_state:
                st.markdown(
                    f'<div class="advice-box">'
                    f'<div class="advice-text" style="font-size:0.9rem;line-height:1.75">'
                    f'{st.session_state[f"ai_analysis_{ticker}"].replace(chr(10), "<br>")}'
                    f'</div></div>',
                    unsafe_allow_html=True
                )
            else:
                st.info("Click the button above to generate your AI analysis.")

        # ── TAB 2: NEWS SENTIMENT ──
        with adv_tab2:
            sent = news_sent.get("sentiment", "neutral")
            score = news_sent.get("sentiment_score", 50)
            sent_color = "#00e676" if sent == "bullish" else ("#ff1744" if sent == "bearish" else "#ffd600")
            bull = news_sent.get("bullish_count", 0)
            bear = news_sent.get("bearish_count", 0)

            st.markdown(
                f'<div class="metric-box" style="text-align:left;margin-bottom:12px">'
                f'<div style="font-family:Syne,sans-serif;font-size:1.1rem;'
                f'font-weight:700;color:{sent_color}">{news_sent.get("summary","")}</div>'
                f'<div style="margin-top:8px;font-size:0.82rem;color:#64748b">'
                f'Positive signals in headlines: {bull} &nbsp;|&nbsp; '
                f'Negative signals: {bear}'
                f'</div></div>',
                unsafe_allow_html=True
            )

            # Sentiment bar
            bar_w = score
            st.markdown(
                f'<div style="margin:8px 0 16px 0">'
                f'<div style="display:flex;justify-content:space-between;'
                f'font-size:0.72rem;color:#64748b;margin-bottom:4px">'
                f'<span>Bearish</span><span>Neutral</span><span>Bullish</span></div>'
                f'<div style="background:#1e2840;border-radius:6px;height:12px;'
                f'position:relative;overflow:hidden">'
                f'<div style="width:{bar_w}%;height:100%;background:linear-gradient('
                f'90deg,#ff1744,#ffd600,#00e676);border-radius:6px"></div>'
                f'<div style="position:absolute;top:0;left:50%;width:2px;'
                f'height:100%;background:#0d1117;opacity:0.5"></div>'
                f'</div></div>',
                unsafe_allow_html=True
            )

            headlines = news_sent.get("headlines", [])
            if headlines:
                st.markdown("**Recent headlines:**")
                for h in headlines[:8]:
                    if h.get("title"):
                        url = h.get("url", "")
                        src = h.get("source", "")
                        if url:
                            st.markdown(f'- [{h["title"]}]({url}){f" — *{src}*" if src else ""}')
                        else:
                            st.markdown(f'- {h["title"]}')
            else:
                st.info("No headlines found. Add a Finnhub key in the sidebar for better news coverage.")

        # ── TAB 3: ANALYST CONSENSUS ──
        with adv_tab3:
            if not analyst or not analyst.get("target"):
                st.info("No analyst data available for this stock.")
            else:
                target  = analyst.get("target")
                t_low   = analyst.get("target_low")
                t_high  = analyst.get("target_high")
                upside  = analyst.get("upside")
                n       = analyst.get("num_analysts", 0)
                up_color = "#00e676" if upside and upside > 0 else "#ff1744"

                # Upside metric
                st.markdown(
                    f'<div style="display:flex;gap:12px;margin-bottom:16px">'
                    f'<div class="metric-box" style="flex:1;text-align:center">'
                    f'<div class="label">Average price target</div>'
                    f'<div class="value" style="font-size:1.6rem">${target:.2f}</div>'
                    f'<div style="color:{up_color};font-size:0.9rem;margin-top:4px">'
                    f'{"▲" if upside and upside>0 else "▼"} {abs(upside):.1f}% from current price</div>'
                    f'</div>'
                    f'<div class="metric-box" style="flex:1;text-align:center">'
                    f'<div class="label">Target range</div>'
                    f'<div class="value">${t_low:.0f} – ${t_high:.0f}</div>'
                    f'<div class="explain">{n} analysts covering this stock</div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # Rating bar chart
                sb = analyst.get("strong_buy", 0)
                b  = analyst.get("buy", 0)
                h  = analyst.get("hold", 0)
                s  = analyst.get("sell", 0)
                ss = analyst.get("strong_sell", 0)
                total_r = sb + b + h + s + ss

                if total_r > 0:
                    st.markdown("**Analyst ratings breakdown:**")
                    for label, count, color in [
                        ("Strong Buy",  sb, "#00e676"),
                        ("Buy",         b,  "#69f0ae"),
                        ("Hold",        h,  "#ffd600"),
                        ("Sell",        s,  "#ff7043"),
                        ("Strong Sell", ss, "#ff1744"),
                    ]:
                        pct = (count / total_r * 100) if total_r > 0 else 0
                        st.markdown(
                            f'<div style="display:flex;align-items:center;gap:10px;margin:4px 0">'
                            f'<div style="width:90px;font-size:0.8rem;color:#94a3b8">{label}</div>'
                            f'<div style="background:#1e2840;border-radius:4px;height:10px;'
                            f'width:200px;overflow:hidden">'
                            f'<div style="width:{pct:.0f}%;height:100%;background:{color};'
                            f'border-radius:4px"></div></div>'
                            f'<div style="font-family:IBM Plex Mono;font-size:0.8rem;'
                            f'color:{color}">{count}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                # Plain English interpretation
                if total_r > 0:
                    bullish_r = sb + b
                    bearish_r = s + ss
                    if bullish_r > total_r * 0.6:
                        interp = f"The majority of Wall Street analysts ({bullish_r} out of {total_r}) rate this stock a Buy or Strong Buy."
                    elif bearish_r > total_r * 0.4:
                        interp = f"A significant number of analysts ({bearish_r} out of {total_r}) are cautious — Sell or Strong Sell."
                    else:
                        interp = f"Analyst opinion is mixed — {h} analysts say Hold, with disagreement on direction."
                    st.markdown(
                        f'<div class="advice-box" style="margin-top:12px">'
                        f'<div class="advice-text">{interp}</div></div>',
                        unsafe_allow_html=True
                    )

        # ── TAB 4: INSIDER ACTIVITY ──
        with adv_tab4:
            st.markdown(
                '<div style="font-size:0.82rem;color:#64748b;margin-bottom:10px">'
                'Insiders are company executives, directors, and large shareholders. '
                'When they buy stock with their own money, it can signal confidence. '
                'Selling is less meaningful — they sell for many reasons (taxes, diversification).'
                '</div>',
                unsafe_allow_html=True
            )

            net = insider.get("net_shares", 0)
            summary = insider.get("summary", "No data available.")
            net_color = "#00e676" if net > 0 else ("#ff1744" if net < 0 else "#ffd600")

            st.markdown(
                f'<div class="metric-box" style="text-align:left;margin-bottom:12px">'
                f'<div style="font-family:Syne,sans-serif;font-size:1rem;'
                f'font-weight:700;color:{net_color}">{summary}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            transactions = insider.get("transactions", [])
            if transactions:
                st.markdown("**Recent insider transactions:**")
                for t in transactions[:8]:
                    t_color = "#00e676" if t.get("is_buy") else "#ff6b6b"
                    t_label = "BUY" if t.get("is_buy") else t.get("type", "SELL")
                    val = t.get("value", 0)
                    val_str = f"${val:,.0f}" if val else "N/A"
                    shares = t.get("shares", 0)
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;'
                        f'align-items:center;padding:6px 0;'
                        f'border-bottom:1px solid #1e2840;font-size:0.82rem">'
                        f'<div style="color:#94a3b8;width:160px">{t.get("insider","Unknown")[:25]}</div>'
                        f'<div style="color:{t_color};font-family:IBM Plex Mono;'
                        f'font-weight:600;width:60px">{t_label}</div>'
                        f'<div style="color:#e2e8f0;font-family:IBM Plex Mono;'
                        f'width:90px">{shares:,} shares</div>'
                        f'<div style="color:#64748b;width:80px">{val_str}</div>'
                        f'<div style="color:#475569;width:80px">{t.get("date","")}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("No recent insider transactions found.")



# ─────────────────────────────────────────────
#  PILLAR I — MARKET GATE (5 pre-entry checks)
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_market_gate_data() -> dict:
    """
    The five non-negotiable market health checks from the Quantum Titan framework.
    None of these hard-block trading — they are a guide to your aggression level.

    Check 1: Market regime — is SPY above its 200-day average?
    Check 2: Yield curve — is the 10yr above the 2yr? (uninverted = healthier)
    Check 3: Credit spread proxy — HYG (high yield bonds) vs LQD (investment grade)
    Check 4: VIX level — is market fear elevated?
    Check 5: Market breadth — is SPY making higher highs recently?
    """
    checks = {}

    try:
        # Check 1 — Market regime (SPY vs 200 EMA)
        spy = fetch_prices("SPY", period="1y")
        if spy is not None and len(spy) >= 200:
            price  = spy["Close"].iloc[-1]
            ema200 = spy["Close"].ewm(span=200, adjust=False).mean().iloc[-1]
            above  = bool(price > ema200)
            checks["regime"] = {
                "name":    "Market Trend",
                "detail":  "S&P 500 (SPY) vs its 200-day average",
                "pass":    above,
                "value":   f"SPY ${price:.0f} {'above' if above else 'below'} 200-day avg (${ema200:.0f})",
                "meaning": "Market is in an uptrend — conditions favour buying" if above
                           else "Market is below its long-term average — be defensive",
            }
    except Exception:
        checks["regime"] = {"name": "Market Trend", "pass": None,
                            "value": "Could not load", "detail": "", "meaning": ""}

    try:
        # Check 2 — Yield curve (10yr vs 2yr via ETF proxies TLT/SHY ratio)
        tlt = fetch_prices("TLT", period="1mo")  # 20yr treasury
        shy = fetch_prices("SHY", period="1mo")  # 1-3yr treasury
        if tlt is not None and shy is not None:
            tlt_ret = (tlt["Close"].iloc[-1] / tlt["Close"].iloc[0] - 1) * 100
            shy_ret = (shy["Close"].iloc[-1] / shy["Close"].iloc[0] - 1) * 100
            # TLT outperforming SHY = long rates rising relative to short = healthier curve
            healthy = bool(tlt_ret >= shy_ret - 0.5)
            checks["yield_curve"] = {
                "name":    "Interest Rate Shape",
                "detail":  "Long-term rates vs short-term rates (TLT vs SHY, 1-month)",
                "pass":    healthy,
                "value":   f"Long bonds: {tlt_ret:+.1f}% | Short bonds: {shy_ret:+.1f}%",
                "meaning": "Rate structure is normal — not signalling recession stress" if healthy
                           else "Short rates rising faster than long rates — yield curve stress",
            }
    except Exception:
        checks["yield_curve"] = {"name": "Interest Rate Shape", "pass": None,
                                 "value": "Could not load", "detail": "", "meaning": ""}

    try:
        # Check 3 — Credit spread proxy (HYG = high yield, LQD = investment grade)
        # If HYG is outperforming LQD, credit stress is low — risk appetite is healthy
        hyg = fetch_prices("HYG", period="1mo")
        lqd = fetch_prices("LQD", period="1mo")
        if hyg is not None and lqd is not None:
            hyg_ret = (hyg["Close"].iloc[-1] / hyg["Close"].iloc[0] - 1) * 100
            lqd_ret = (lqd["Close"].iloc[-1] / lqd["Close"].iloc[0] - 1) * 100
            healthy = bool(hyg_ret >= lqd_ret - 0.3)
            checks["credit"] = {
                "name":    "Credit Market Health",
                "detail":  "High-yield bonds (HYG) vs investment-grade bonds (LQD)",
                "pass":    healthy,
                "value":   f"High yield: {hyg_ret:+.1f}% | Investment grade: {lqd_ret:+.1f}%",
                "meaning": "Credit markets are calm — investors are not fleeing risky assets" if healthy
                           else "High-yield bonds underperforming — credit stress building, equity risk is elevated",
            }
    except Exception:
        checks["credit"] = {"name": "Credit Market Health", "pass": None,
                            "value": "Could not load", "detail": "", "meaning": ""}

    try:
        # Check 4 — VIX fear gauge
        vix_val = fetch_vix()
        healthy = bool(vix_val is not None and vix_val < 25)
        checks["vix"] = {
            "name":    "Market Fear Level",
            "detail":  "VIX — the market volatility index",
            "pass":    healthy,
            "value":   f"VIX = {vix_val:.1f}" if vix_val else "Could not load",
            "meaning": "Fear is low — markets are calm and conditions are stable" if healthy
                       else "Fear is elevated — markets are volatile. Reduce position sizes.",
        }
    except Exception:
        checks["vix"] = {"name": "Market Fear Level", "pass": None,
                         "value": "Could not load", "detail": "", "meaning": ""}

    try:
        # Check 5 — Market breadth (SPY making higher highs over last 20 days)
        spy = fetch_prices("SPY", period="3mo")
        if spy is not None and len(spy) >= 20:
            recent_high  = spy["Close"].tail(20).max()
            prior_high   = spy["Close"].iloc[-40:-20].max() if len(spy) >= 40 else spy["Close"].iloc[0]
            healthy      = bool(recent_high > prior_high)
            pct_diff     = float((recent_high / prior_high - 1) * 100)
            checks["breadth"] = {
                "name":    "Market Momentum",
                "detail":  "Is the S&P 500 making higher highs? (last 20 days vs prior 20)",
                "pass":    healthy,
                "value":   f"Recent high ${recent_high:.0f} vs prior high ${prior_high:.0f} ({pct_diff:+.1f}%)",
                "meaning": "Market is making higher highs — upward momentum is intact" if healthy
                           else "Market is not making new highs — momentum may be stalling",
            }
    except Exception:
        checks["breadth"] = {"name": "Market Momentum", "pass": None,
                             "value": "Could not load", "detail": "", "meaning": ""}

    # Overall gate score
    passed   = sum(1 for c in checks.values() if c.get("pass") == True)
    failed   = sum(1 for c in checks.values() if c.get("pass") == False)
    total    = len(checks)

    if passed >= 4:
        gate_label  = "MARKETS LOOK FAVOURABLE"
        gate_color  = "#00e676"
        gate_advice = (f"{passed}/{total} checks are positive. "
                       "Conditions are generally good for new positions. "
                       "Use standard position sizes and focus on green-scored stocks.")
    elif passed >= 3:
        gate_label  = "PROCEED WITH CAUTION"
        gate_color  = "#ffd600"
        gate_advice = (f"{passed}/{total} checks are positive. "
                       "Mixed conditions — reduce your normal position size by 30-50%. "
                       "Only take the highest-conviction setups.")
    else:
        gate_label  = "DEFENSIVE MODE RECOMMENDED"
        gate_color  = "#ff1744"
        gate_advice = (f"Only {passed}/{total} checks are positive. "
                       "Multiple warning signs across the market. "
                       "Consider holding more cash. If you trade, use very small positions "
                       "and only the clearest setups.")

    return {
        "checks":      checks,
        "passed":      passed,
        "failed":      failed,
        "total":       total,
        "gate_label":  gate_label,
        "gate_color":  gate_color,
        "gate_advice": gate_advice,
    }


def render_market_gate(gate_data: dict):
    """
    Renders the Pillar I market gate as a collapsible panel at the top
    of the stock list. Shows all five checks with plain English explanations.
    """
    color  = gate_data.get("gate_color", "#ffd600")
    label  = gate_data.get("gate_label", "LOADING...")
    advice = gate_data.get("gate_advice", "")
    passed = gate_data.get("passed", 0)
    total  = gate_data.get("total", 5)

    with st.expander(
        f"📋 Pre-Entry Market Checklist — {passed}/{total} checks passed  |  {label}",
        expanded=True
    ):
        # Overall verdict banner
        st.markdown(
            f'<div style="background:rgba(0,0,0,0.2);border-left:4px solid {color};'
            f'border-radius:6px;padding:12px 16px;margin-bottom:16px">'
            f'<div style="font-family:Syne,sans-serif;font-size:1rem;font-weight:700;'
            f'color:{color};margin-bottom:6px">{label}</div>'
            f'<div style="font-size:0.88rem;color:#cbd5e1;line-height:1.6">{advice}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Five check rows
        checks = gate_data.get("checks", {})
        for key, chk in checks.items():
            passed_chk = chk.get("pass")
            if passed_chk == True:
                icon, chk_color, bg = "✅", "#00e676", "rgba(0,230,118,0.06)"
            elif passed_chk == False:
                icon, chk_color, bg = "⚠️", "#ffd600", "rgba(255,214,0,0.06)"
            else:
                icon, chk_color, bg = "❓", "#64748b", "rgba(100,116,139,0.06)"

            st.markdown(
                f'<div style="background:{bg};border:1px solid {chk_color}33;'
                f'border-radius:8px;padding:10px 14px;margin:6px 0;'
                f'display:flex;align-items:flex-start;gap:12px">'
                f'<div style="font-size:1.2rem;margin-top:2px">{icon}</div>'
                f'<div style="flex:1">'
                f'<div style="font-family:Syne,sans-serif;font-size:0.88rem;'
                f'font-weight:700;color:{chk_color}">{chk.get("name","")}</div>'
                f'<div style="font-size:0.78rem;color:#64748b;margin:2px 0">'
                f'{chk.get("detail","")}</div>'
                f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.78rem;'
                f'color:#94a3b8;margin:2px 0">{chk.get("value","")}</div>'
                f'<div style="font-size:0.82rem;color:#cbd5e1;margin-top:4px">'
                f'{chk.get("meaning","")}</div>'
                f'</div></div>',
                unsafe_allow_html=True
            )

        st.caption(
            "This checklist is a GUIDE, not a hard block. "
            "Even in poor market conditions, individual stocks can present great opportunities. "
            "Use this to calibrate your position sizes and aggression level, not to make binary decisions."
        )


# ─────────────────────────────────────────────
#  SELL SIGNAL DETECTOR
# ─────────────────────────────────────────────

def detect_sell_signals(ticker: str, df, info: dict,
                         analyst: dict, insider: dict) -> list:
    """
    Checks a watchlist stock for conditions that suggest it may be time to exit.

    Two types of sell signal (as per the framework):
    1. Technical deterioration — chart signals turning negative
    2. Thesis breakdown — the fundamental or sentiment reason to own it is changing

    Returns a list of sell alerts, each with a type, message, and urgency level.
    """
    alerts = []
    if df is None or df.empty:
        return alerts

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    price = last["Close"]

    # ── TECHNICAL SELL SIGNALS ──

    # 1. Price crossed below 50-day average (medium-term trend broken)
    if "EMA50" in df.columns:
        ema50_now  = last["EMA50"]
        ema50_prev = prev["EMA50"]
        if prev["Close"] > ema50_prev and price < ema50_now:
            alerts.append({
                "type":    "📉 Trend broken",
                "message": f"Price just crossed BELOW its 50-day average (${ema50_now:.2f}). "
                           f"The medium-term uptrend may be ending.",
                "urgency": "HIGH",
                "pillar":  "Technical",
            })

    # 2. Price crossed below 200-day average (major trend broken)
    if "EMA200" in df.columns:
        ema200 = last["EMA200"]
        if prev["Close"] > prev["EMA200"] and price < ema200:
            alerts.append({
                "type":    "🚨 Major trend broken",
                "message": f"Price just crossed BELOW the 200-day average (${ema200:.2f}). "
                           f"This is a serious warning — many funds use this as an automatic exit.",
                "urgency": "CRITICAL",
                "pillar":  "Technical",
            })

    # 3. RSI turned sharply down from overbought
    if "RSI" in df.columns and len(df) >= 5:
        rsi_now  = last["RSI"]
        rsi_5d   = df["RSI"].iloc[-5]
        if rsi_5d > 68 and rsi_now < 55:
            alerts.append({
                "type":    "📉 Momentum fading",
                "message": f"RSI has dropped from {rsi_5d:.0f} to {rsi_now:.0f} in 5 days. "
                           f"Buying momentum (RSI) is fading fast.",
                "urgency": "MEDIUM",
                "pillar":  "Technical",
            })

    # 4. MACD bearish cross
    if "MACD" in df.columns and len(df) >= 2:
        curr_diff = df["MACD"].iloc[-1] - df["MACD_Signal"].iloc[-1]
        prev_diff = df["MACD"].iloc[-2] - df["MACD_Signal"].iloc[-2]
        if prev_diff > 0 and curr_diff < 0:
            alerts.append({
                "type":    "⚡ Momentum turning down",
                "message": "The MACD line just crossed BELOW its signal line. "
                           "This is a classic sell/exit signal — momentum is turning negative.",
                "urgency": "MEDIUM",
                "pillar":  "Technical",
            })

    # 5. High volume sell-off (price down + volume spike)
    if "VolRatio" in df.columns:
        vr = last["VolRatio"]
        day_chg = (price / prev["Close"] - 1) * 100
        if vr > 2.5 and day_chg < -2.0:
            alerts.append({
                "type":    "🔊 Heavy selling",
                "message": f"Price fell {abs(day_chg):.1f}% today on {vr:.1f}× normal volume. "
                           f"Institutions may be distributing (selling) this stock.",
                "urgency": "HIGH",
                "pillar":  "Technical",
            })

    # ── THESIS BREAKDOWN SIGNALS ──

    # 6. Analyst downgrade (mean target moved significantly lower)
    if analyst.get("upside") is not None:
        upside = analyst["upside"]
        if upside < -10:
            alerts.append({
                "type":    "🏦 Analyst target below price",
                "message": f"The average Wall Street price target is now {upside:.1f}% BELOW "
                           f"the current price. Analysts collectively think this stock is overvalued.",
                "urgency": "MEDIUM",
                "pillar":  "Thesis",
            })

    # 7. Heavy insider selling
    if insider.get("net_shares", 0) < -50000:
        net = insider["net_shares"]
        alerts.append({
            "type":    "🏛 Heavy insider selling",
            "message": f"Company insiders have net sold {abs(net):,} shares recently. "
                       f"While insiders sell for many reasons, heavy selling can signal "
                       f"reduced confidence in near-term prospects.",
            "urgency": "MEDIUM",
            "pillar":  "Thesis",
        })

    # 8. Short interest spiking (bears building positions)
    short_pct = info.get("short_pct", 0) or 0
    if short_pct > 0.15:
        alerts.append({
            "type":    "🐻 High short interest",
            "message": f"{short_pct*100:.1f}% of shares are being shorted — "
                       f"a large number of professional investors are betting this stock will fall.",
            "urgency": "MEDIUM",
            "pillar":  "Thesis",
        })

    # 9. Near 52-week low (structural weakness)
    lo52 = info.get("52w_low")
    if lo52 and price <= lo52 * 1.05:
        alerts.append({
            "type":    "🕳 Near 52-week low",
            "message": f"Price is within 5% of its 52-week low (${lo52:.2f}). "
                       f"The stock is showing significant structural weakness.",
            "urgency": "HIGH",
            "pillar":  "Thesis",
        })

    return alerts


def render_sell_signals_panel(ticker: str, sell_signals: list, price: float):
    """
    Renders the sell signal panel under a watchlist stock card.
    Shows all detected exit conditions with urgency levels and explanations.
    """
    if not sell_signals:
        st.markdown(
            f'<div style="background:rgba(0,230,118,0.06);border:1px solid rgba(0,230,118,0.2);'
            f'border-radius:8px;padding:10px 14px;margin:6px 0">'
            f'<span style="color:#00e676;font-size:0.85rem">✅ No exit signals detected — '
            f'no reason to sell based on current data</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        return

    urgency_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
    sell_signals  = sorted(sell_signals,
                           key=lambda x: urgency_order.get(x["urgency"], 3))

    for sig in sell_signals:
        urgency = sig["urgency"]
        if urgency == "CRITICAL":
            bg, border, urg_color = "rgba(255,23,68,0.12)", "#ff1744", "#ff1744"
        elif urgency == "HIGH":
            bg, border, urg_color = "rgba(255,112,67,0.1)", "#ff7043", "#ff7043"
        else:
            bg, border, urg_color = "rgba(255,214,0,0.08)", "#ffd600", "#ffd600"

        pillar_badge = (
            f'<span style="background:rgba(41,182,246,0.15);color:#4fc3f7;'
            f'font-size:0.65rem;padding:2px 7px;border-radius:10px;'
            f'font-family:IBM Plex Mono,monospace;margin-left:8px">'
            f'{sig["pillar"]} signal</span>'
        )

        st.markdown(
            f'<div style="background:{bg};border:1px solid {border};'
            f'border-radius:8px;padding:12px 14px;margin:6px 0">'
            f'<div style="display:flex;align-items:center;margin-bottom:6px">'
            f'<span style="font-family:Syne,sans-serif;font-size:0.88rem;'
            f'font-weight:700;color:{urg_color}">{sig["type"]}</span>'
            f'{pillar_badge}'
            f'<span style="margin-left:auto;font-family:IBM Plex Mono;'
            f'font-size:0.7rem;color:{urg_color};font-weight:600">{urgency}</span>'
            f'</div>'
            f'<div style="font-size:0.84rem;color:#cbd5e1;line-height:1.6">'
            f'{sig["message"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────
#  EARNINGS REVISION TRACKER
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_earnings_revision(ticker: str) -> dict:
    """
    Check whether analyst EPS estimates have been revised UP or DOWN recently.
    Rising estimates = institutional money likely accumulating.
    Falling estimates = funds may be reducing positions.
    This is the Pillar II earnings revision cycle signal.
    """
    try:
        tk = yf.Ticker(ticker)
        # yfinance earnings estimate data
        analysis = tk.analyst_price_targets if hasattr(tk, "analyst_price_targets") else None

        # Use eps trend data
        trend = tk.earnings_estimate if hasattr(tk, "earnings_estimate") else None
        if trend is None:
            trend = getattr(tk, "eps_trend", None)

        info = tk.info
        # Current vs prior year EPS growth as a proxy
        eps_curr    = info.get("trailingEps")
        eps_forward = info.get("forwardEps")
        eps_growth  = info.get("earningsGrowth")
        rev_growth  = info.get("revenueGrowth")

        # Analyst revision direction
        curr_target = info.get("targetMeanPrice")
        low_target  = info.get("targetLowPrice")
        high_target = info.get("targetHighPrice")
        price       = info.get("currentPrice") or info.get("regularMarketPrice")

        if eps_forward and eps_curr and eps_curr != 0:
            fwd_growth = (eps_forward / abs(eps_curr) - 1) * 100
        else:
            fwd_growth = None

        if eps_growth and eps_growth > 0.10:
            revision_signal = "RISING"
            revision_color  = "#00e676"
            revision_text   = f"Earnings estimates are growing at {eps_growth*100:.1f}% — analysts are revising UP. Institutional accumulation likely."
        elif eps_growth and eps_growth > 0:
            revision_signal = "SLIGHTLY POSITIVE"
            revision_color  = "#69f0ae"
            revision_text   = f"Earnings estimates are slightly positive ({eps_growth*100:.1f}%). Modest upward revision trend."
        elif eps_growth and eps_growth < -0.05:
            revision_signal = "FALLING"
            revision_color  = "#ff1744"
            revision_text   = f"Earnings estimates are being revised DOWN ({eps_growth*100:.1f}%). Funds may be reducing positions."
        else:
            revision_signal = "FLAT"
            revision_color  = "#ffd600"
            revision_text   = "Earnings estimates are flat — no strong revision trend in either direction."

        return {
            "signal":        revision_signal,
            "color":         revision_color,
            "text":          revision_text,
            "eps_current":   eps_curr,
            "eps_forward":   eps_forward,
            "eps_growth":    eps_growth,
            "rev_growth":    rev_growth,
            "fwd_growth":    fwd_growth,
        }
    except Exception:
        return {
            "signal": "UNKNOWN", "color": "#64748b",
            "text": "Could not load earnings revision data.",
        }


def render_earnings_revision_badge(revision: dict):
    """Small inline badge showing earnings revision direction."""
    color  = revision.get("color", "#64748b")
    signal = revision.get("signal", "UNKNOWN")
    text   = revision.get("text", "")
    eps_g  = revision.get("eps_growth")
    eps_badge = ("<span style=\"font-family:IBM Plex Mono;font-size:0.75rem;color:#64748b\">" +
                  str(round(eps_g * 100, 1)) + "%" +
                  "</span>") if eps_g else ""
    return (
        f'<div style="background:rgba(0,0,0,0.2);border:1px solid {color}44;'
        f'border-radius:6px;padding:8px 12px;margin:6px 0">'
        f'<div style="display:flex;align-items:center;gap:8px">'
        f'<span style="font-family:Syne,sans-serif;font-size:0.78rem;font-weight:700;'
        f'color:{color}">Earnings Revision: {signal}</span>'
        f'{eps_badge}'
        f'</div>'
        f'<div style="font-size:0.78rem;color:#94a3b8;margin-top:3px">{text}</div>'
        f'</div>'
    )


# ─────────────────────────────────────────────
#  FACTOR REGIME LABELLER
# ─────────────────────────────────────────────

def get_factor_regime_label(regime: str, vix: float, sector_perf: dict) -> dict:
    """
    Based on the current market regime and sector rotation,
    identifies which investment FACTOR is most likely to outperform.

    Factors (from Fama-French and AQR research):
    - MOMENTUM: stocks trending up continue trending up (works in calm bull markets)
    - QUALITY: high ROE, low debt companies hold up best in late cycle / uncertainty
    - VALUE: cheap stocks outperform in early recovery and inflationary environments
    - LOW VOL: defensive stocks outperform when volatility is high (risk-off)
    """
    vix_high = vix and vix > 22

    if regime == "BULL MARKET" and not vix_high:
        factor       = "MOMENTUM"
        factor_color = "#00e676"
        factor_desc  = ("In a calm bull market, stocks that are already rising tend to keep rising. "
                        "Focus on stocks making new highs with strong volume and upward momentum. "
                        "This is the best environment for breakout trades.")
        what_to_buy  = "Stocks scoring high on Chart Signals, near 52-week highs, with strong volume."

    elif regime == "BULL MARKET" and vix_high:
        factor       = "QUALITY"
        factor_color = "#38bdf8"
        factor_desc  = ("Bull market but with elevated fear. Quality companies — high ROE, "
                        "low debt, consistent cash flow — hold up best here. "
                        "Avoid speculative or heavily indebted companies.")
        what_to_buy  = "Stocks with high Company Health scores, positive FCF, low debt."

    elif regime == "MIXED MARKET":
        factor       = "QUALITY"
        factor_color = "#38bdf8"
        factor_desc  = ("In a mixed or late-cycle market, quality companies outperform. "
                        "Earnings consistency and balance sheet strength matter most. "
                        "Be selective — only take the cleanest setups.")
        what_to_buy  = "Stocks with strong fundamentals, rising earnings estimates, defensive sectors."

    elif regime == "BEAR MARKET" and vix_high:
        factor       = "LOW VOLATILITY"
        factor_color = "#ffd600"
        factor_desc  = ("In a bear market with high fear, low-volatility defensive stocks "
                        "lose less than the overall market. Consumer Staples, Utilities, "
                        "and Healthcare tend to outperform. Capital preservation is the priority.")
        what_to_buy  = "Defensive stocks (XLP, XLU, XLV sectors), low Beta, high dividend yield."

    else:
        factor       = "VALUE"
        factor_color = "#ff9800"
        factor_desc  = ("Bear market or recovery environment. Value stocks — companies trading "
                        "cheaply relative to their earnings and assets — tend to outperform "
                        "as the market bottoms and recovers.")
        what_to_buy  = "Stocks with low P/E, positive FCF, trading below analyst targets."

    return {
        "factor":       factor,
        "color":        factor_color,
        "description":  factor_desc,
        "what_to_buy":  what_to_buy,
    }

def render_traffic_light_list(results: list, regime_data: dict = {}):
    """
    The main advisor panel — a sorted list of all your stocks
    colour-coded by risk level with plain English advice.
    """
    if not results:
        st.info("Add stocks to your watchlist in the sidebar to see your traffic light list.")
        return

    green  = [r for r in results if r["risk"]["score"] >= 80]
    yellow = [r for r in results if 50 <= r["risk"]["score"] < 80]
    red    = [r for r in results if r["risk"]["score"] < 50]

    # Sort each group by score descending
    green  = sorted(green,  key=lambda x: x["risk"]["score"], reverse=True)
    yellow = sorted(yellow, key=lambda x: x["risk"]["score"], reverse=True)
    red    = sorted(red,    key=lambda x: x["risk"]["score"], reverse=True)

    # ── Summary row ──
    st.markdown(
        f'<div style="display:flex;gap:12px;margin-bottom:20px">'
        f'<div style="background:rgba(0,230,118,0.1);border:1px solid #00e676;border-radius:8px;'
        f'padding:12px 20px;text-align:center;flex:1">'
        f'<div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;color:#00e676">{len(green)}</div>'
        f'<div style="font-size:0.72rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em">LOW RISK</div></div>'
        f'<div style="background:rgba(255,214,0,0.1);border:1px solid #ffd600;border-radius:8px;'
        f'padding:12px 20px;text-align:center;flex:1">'
        f'<div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;color:#ffd600">{len(yellow)}</div>'
        f'<div style="font-size:0.72rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em">MEDIUM RISK</div></div>'
        f'<div style="background:rgba(255,23,68,0.1);border:1px solid #ff1744;border-radius:8px;'
        f'padding:12px 20px;text-align:center;flex:1">'
        f'<div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;color:#ff1744">{len(red)}</div>'
        f'<div style="font-size:0.72rem;color:#64748b;text-spacing:0.1em;text-transform:uppercase;letter-spacing:0.1em">HIGH RISK</div></div>'
        f'</div>',
        unsafe_allow_html=True
    )

    def render_group(group, css, color, icon, title_text, risk_note):
        if not group:
            return
        st.markdown(f'<div class="section-header" style="color:{color}">{icon} {title_text}</div>',
                    unsafe_allow_html=True)
        st.caption(risk_note)
        for r in group:
            tk   = r["ticker"]
            risk = r["risk"]
            info = r["info"]
            df   = r["df"]
            name = info.get("name", tk)
            price = info.get("price") or (df.iloc[-1]["Close"] if df is not None and not df.empty else None)
            sector = info.get("sector", "")

            with st.container():
                st.markdown(f'<div class="{css}">', unsafe_allow_html=True)

                # Header row
                hc1, hc2, hc3 = st.columns([4, 2, 2])
                with hc1:
                    st.markdown(
                        f'<span style="font-family:Syne,sans-serif;font-size:1.3rem;'
                        f'font-weight:800;color:{color}">{tk}</span> '
                        f'<span style="color:#64748b;font-size:0.85rem">{name}</span><br>'
                        f'<span style="font-size:0.72rem;color:#475569">{sector}</span>',
                        unsafe_allow_html=True
                    )
                with hc2:
                    st.markdown(
                        f'<div style="text-align:center">'
                        f'<div class="score-num" style="color:{color}">{risk["score"]:.0f}</div>'
                        f'<div class="score-label" style="color:{color}">{risk["label"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                with hc3:
                    if price:
                        chg_pct = 0
                        if df is not None and len(df) > 1:
                            chg_pct = (df.iloc[-1]["Close"] / df.iloc[-2]["Close"] - 1) * 100
                        chg_color = "#00e676" if chg_pct >= 0 else "#ff1744"
                        st.markdown(
                            f'<div style="text-align:right">'
                            f'<div style="font-family:IBM Plex Mono,monospace;font-size:1.4rem;'
                            f'color:#e2e8f0">${price:.2f}</div>'
                            f'<div style="color:{chg_color};font-size:0.85rem">'
                            f'{"▲" if chg_pct >= 0 else "▼"} {abs(chg_pct):.2f}% today</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                # Return profile
                st.markdown(
                    f'<div style="font-size:0.8rem;color:#64748b;margin:6px 0 10px 0;'
                    f'font-style:italic">{risk["return_profile"]}</div>',
                    unsafe_allow_html=True
                )

                # Sub-scores as inline pills
                t_lbl = f"Chart: {risk['t_score']:.0f}/100"
                f_lbl = f"Finances: {risk['f_score']:.0f}/100"
                s_lbl = f"Mood: {risk['s_score']:.0f}/100"
                p_lbl = f"Track record: {risk['p_score']:.0f}/100"
                pill_html = (
                    pill(t_lbl, "blue") +
                    pill(f_lbl, "blue") +
                    pill(s_lbl, "blue") +
                    pill(p_lbl, "blue")
                )
                st.markdown(pill_html, unsafe_allow_html=True)

                # Anomaly flags
                anomalies = r.get("anomalies", [])
                if anomalies:
                    flag_html = " ".join([
                        f'{pill(a["type"], "amber" if a["level"]=="WARN" else ("green" if a["level"]=="BUY" else "red"))}'
                        for a in anomalies
                    ])
                    st.markdown(flag_html, unsafe_allow_html=True)

                # Advice
                st.markdown(
                    f'<div class="advice-box"><h4>💬 Advisor Summary</h4>'
                    f'<div class="advice-text">{risk["advice"]}</div></div>',
                    unsafe_allow_html=True
                )

                # Position sizing suggestion
                if price and df is not None and "ATR14" in df.columns:
                    atr   = df["ATR14"].iloc[-1]
                    stop  = price - 1.5 * atr
                    sizing = calculate_position_size(
                        st.session_state.account_size,
                        st.session_state.max_risk_pct,
                        price, stop
                    )
                    if sizing:
                        st.markdown(
                            f'<div class="advice-box">'
                            f'<h4>📐 Suggested Position Size</h4>'
                            f'<div class="advice-text">'
                            f'Based on your ${st.session_state.account_size:,.0f} account '
                            f'and {st.session_state.max_risk_pct}% max risk per trade:<br><br>'
                            f'• Buy <strong>{sizing["shares"]} shares</strong> at ~${price:.2f} '
                            f'(total cost: <strong>${sizing["total_cost"]:,.0f}</strong> = '
                            f'{sizing["pct_of_account"]:.1f}% of your account)<br>'
                            f'• Set your stop-loss at <strong>${stop:.2f}</strong> '
                            f'(1.5× ATR below entry)<br>'
                            f'• Maximum loss if stopped out: <strong>${sizing["dollar_risk"]:,.2f}</strong>'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )

                # Earnings revision badge
                revision = fetch_earnings_revision(tk)
                st.markdown(render_earnings_revision_badge(revision),
                            unsafe_allow_html=True)

                # Sell signals
                sell_sigs = detect_sell_signals(
                    tk, df, info,
                    r.get("analyst", {}),
                    r.get("insider", {})
                )
                if sell_sigs:
                    st.markdown(
                        f'<div style="font-family:Syne,sans-serif;font-size:0.8rem;' +
                        f'font-weight:700;color:#ff7043;margin:10px 0 4px 0">' +
                        f'🚨 EXIT ALERTS ({len(sell_sigs)} signal{"s" if len(sell_sigs)>1 else ""})</div>',
                        unsafe_allow_html=True
                    )
                    render_sell_signals_panel(tk, sell_sigs, price or 0)
                else:
                    st.markdown(
                        '<div style="background:rgba(0,230,118,0.05);border:1px solid ' +
                        'rgba(0,230,118,0.15);border-radius:6px;padding:8px 12px;margin:6px 0">' +
                        '<span style="color:#00e676;font-size:0.82rem">✅ No exit signals — ' +
                        'hold thesis is intact</span></div>',
                        unsafe_allow_html=True
                    )

                # AI Advisor Panel
                render_advisor_panel(
                    tk, info, risk,
                    r.get("analyst", {}),
                    r.get("insider", {}),
                    r.get("news_sent", {}),
                    regime_data if "regime_data" in dir() else {}
                )

                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

    render_group(green,  "tl-green",  "#00e676", "🟢",
                 "LOW RISK STOCKS",
                 "These stocks have the most favourable conditions right now. Lower risk, but also typically lower short-term reward. Good for cautious investors or larger position sizes.")
    render_group(yellow, "tl-yellow", "#ffd600", "🟡",
                 "MEDIUM RISK STOCKS",
                 "Mixed signals — some things look good, others don't. Trade these with a smaller position size than your green list. Watch them closely.")
    render_group(red,    "tl-red",    "#ff1744", "🔴",
                 "HIGH RISK STOCKS",
                 "Multiple warning signs present. Higher potential reward if they work out, but higher chance of loss. If you trade these, use a tight stop-loss and a small position size. Never put a large portion of your account into a red stock.")


# ─────────────────────────────────────────────
#  DETAILED STOCK VIEW
# ─────────────────────────────────────────────

def render_stock_detail(ticker, df, info, risk, opts, fear_greed, vix, anomalies):
    """Full deep-dive view for one stock."""
    st.markdown(f'<div class="section-header">{ticker} — Full Analysis</div>',
                unsafe_allow_html=True)

    # Key metrics
    price = info.get("price") or (df.iloc[-1]["Close"] if df is not None and not df.empty else None)
    cols = st.columns(8)
    metric_data = [
        ("Current price",       f'${price:.2f}' if price else "N/A",       "", "What the stock costs per share right now"),
        ("P/E ratio",           f'{info["pe"]:.1f}' if info.get("pe") else "N/A",   "", "Price-to-Earnings: how much you pay per $1 of profit"),
        ("Forward P/E",         f'{info["forward_pe"]:.1f}' if info.get("forward_pe") else "N/A", "", "Expected P/E based on next year's earnings"),
        ("Price-to-Book (P/B)", f'{info["pb"]:.1f}' if info.get("pb") else "N/A",   "", "How much above its accounting value you're paying"),
        ("Debt vs Equity (D/E)",f'{info["debt_equity"]:.0f}' if info.get("debt_equity") else "N/A","","Lower = less debt. Above 100 needs scrutiny"),
        ("ROE",                 f'{info["roe"]*100:.1f}%' if info.get("roe") else "N/A",           "", "Return on Equity: profit generated per $ of shareholder investment"),
        ("Short sellers",       f'{info["short_pct"]*100:.1f}%' if info.get("short_pct") else "N/A","","% of shares being bet against"),
        ("Institutions own",    f'{info["inst_pct"]*100:.1f}%' if info.get("inst_pct") else "N/A", "","% held by big professional funds"),
    ]
    for col, (lbl, val, dlt, exp) in zip(cols, metric_data):
        col.markdown(mbox(lbl, val, exp, dlt or None), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Sentiment row
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    sc1.markdown(mbox("Market Mood (F&G)", f'{fear_greed.get("value","?")}',
                       "0=extreme fear, 100=extreme greed"), unsafe_allow_html=True)
    sc2.markdown(mbox("Market Fear (VIX)", str(vix) if vix else "N/A",
                       "Below 15=calm, above 30=panic"), unsafe_allow_html=True)
    pc = opts.get("put_call_ratio")
    sc3.markdown(mbox("Bets down vs up (P/C)", f'{pc:.2f}' if pc else "N/A",
                       "Below 0.8 = more bullish bets"), unsafe_allow_html=True)
    sc4.markdown(mbox("Beta (volatility vs market)", f'{info["beta"]:.2f}' if info.get("beta") else "N/A",
                       "1.0=moves with market, 2.0=twice as volatile"), unsafe_allow_html=True)
    target = info.get("target_price")
    upside = f'{(target/price-1)*100:+.1f}%' if target and price else "N/A"
    sc5.markdown(mbox("Analyst target", f'${target:.2f}' if target else "N/A",
                       f"Upside from here: {upside}"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Technical row
    if df is not None and not df.empty:
        last = df.iloc[-1]
        tc1, tc2, tc3, tc4, tc5, tc6 = st.columns(6)
        tc1.markdown(mbox("Momentum (RSI)",  f'{last.get("RSI",0):.1f}',
                            "30=oversold, 70=overbought"), unsafe_allow_html=True)
        tc2.markdown(mbox("Trend strength (MACD)", f'{last.get("MACD",0):.3f}',
                            "Positive = upward momentum"), unsafe_allow_html=True)
        tc3.markdown(mbox("20-day avg price (EMA20)", f'${last.get("EMA20",0):.2f}',
                            "Price above = short uptrend"), unsafe_allow_html=True)
        tc4.markdown(mbox("50-day avg price (EMA50)", f'${last.get("EMA50",0):.2f}',
                            "Price above = medium uptrend"), unsafe_allow_html=True)
        tc5.markdown(mbox("Fair-value avg (VWAP)", f'${last.get("VWAP",0):.2f}',
                            "Institutions' reference price"), unsafe_allow_html=True)
        tc6.markdown(mbox("Volume vs average", f'{last.get("VolRatio",0):.1f}×',
                            "Above 1.5x = unusual activity"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    ct1, ct2, ct3 = st.tabs(["📈 Price Chart", "💰 Money Flow (OBV)", "📊 Market Strength (RS)"])
    with ct1:
        st.plotly_chart(build_price_chart(df, ticker), use_container_width=True,
                        key=f"pc_{ticker}")
    with ct2:
        st.plotly_chart(build_obv_chart(df), use_container_width=True, key=f"obv_{ticker}")
        st.caption("Rising line = more money flowing IN than out. Falling = more flowing out.")
    with ct3:
        st.plotly_chart(build_rs_chart(df), use_container_width=True, key=f"rs_{ticker}")
        st.caption("Above 100 = this stock is outperforming the overall market (S&P 500 / SPY).")

    # Score breakdown
    with st.expander("🔍 Full score breakdown — see exactly why it got this score"):
        for cat, bd in risk["breakdowns"].items():
            st.markdown(f"**{cat}**")
            for item, val in bd.items():
                if isinstance(val, (int, float)):
                    bar_w = int(val)
                    bar_color = "#00e676" if val >= 15 else ("#ffd600" if val >= 8 else "#ff1744")
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:10px;margin:3px 0">'
                        f'<div style="font-size:0.8rem;color:#94a3b8;width:400px">{item}</div>'
                        f'<div style="background:#1e2840;border-radius:4px;height:8px;width:180px;overflow:hidden">'
                        f'<div style="width:{bar_w}%;height:100%;background:{bar_color};border-radius:4px"></div>'
                        f'</div>'
                        f'<div style="font-family:IBM Plex Mono;font-size:0.8rem;color:{bar_color}">{val:.0f} pts</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

    # News
    news = fetch_news(ticker)
    if news:
        st.markdown("**📰 Recent news headlines**")
        for a in news[:5]:
            st.markdown(f'- [{a.get("headline","")}]({a.get("url","#")}) — *{a.get("source","")}*')
    elif not st.session_state.finnhub_key:
        st.caption("Add a free Finnhub API key in the sidebar to see news for this stock.")


# ─────────────────────────────────────────────
#  MARKET REGIME TAB
# ─────────────────────────────────────────────

def render_market_regime_tab(regime_data):
    st.markdown('<div class="section-header">🌍 Overall Market Health</div>', unsafe_allow_html=True)
    st.caption("Before picking individual stocks, always check the overall market direction. "
               "Swimming against the current is very hard.")

    # Regime badge + advice
    st.markdown(
        f'<span class="{regime_data["regime_class"]}">{regime_data["regime"]}</span>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="advice-box" style="margin-top:12px">'
        f'<div class="advice-text">{regime_data["regime_advice"]}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Index health
    st.markdown("**Three key market barometers**")
    idx = regime_data.get("indices", {})
    for sym, data in idx.items():
        above_all = data.get("above_200ema") and data.get("above_50ema") and data.get("above_20ema")
        above_some = data.get("above_50ema") or data.get("above_200ema")
        color = "#00e676" if above_all else ("#ffd600" if above_some else "#ff1744")
        mo1 = data.get("mo1m", 0)
        mo3 = data.get("mo3m", 0)
        st.markdown(
            f'<div class="metric-box" style="text-align:left;padding:14px;margin-bottom:8px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<div>'
            f'<span style="font-family:Syne,sans-serif;font-size:1rem;font-weight:700;color:{color}">'
            f'{sym}</span>'
            f'<span style="color:#64748b;font-size:0.8rem;margin-left:8px">{data.get("name","")}</span>'
            f'</div>'
            f'<div style="text-align:right">'
            f'<span style="font-family:IBM Plex Mono;font-size:0.85rem;'
            f'color:{"#00e676" if mo1>=0 else "#ff1744"}">'
            f'1mo: {mo1:+.1f}%</span>'
            f'&nbsp;&nbsp;'
            f'<span style="font-family:IBM Plex Mono;font-size:0.85rem;'
            f'color:{"#00e676" if mo3>=0 else "#ff1744"}">'
            f'3mo: {mo3:+.1f}%</span>'
            f'</div></div>'
            f'<div style="margin-top:8px;display:flex;gap:6px">'
            f'{pill("Above 20-day trend" if data.get("above_20ema") else "Below 20-day trend", "green" if data.get("above_20ema") else "red")}'
            f'{pill("Above 50-day trend" if data.get("above_50ema") else "Below 50-day trend", "green" if data.get("above_50ema") else "red")}'
            f'{pill("Above 200-day trend" if data.get("above_200ema") else "Below 200-day trend", "green" if data.get("above_200ema") else "red")}'
            f'</div></div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Sector performance
    st.markdown("**Which industries are winning and losing right now?**")
    st.caption("Focus your stock searches on the green sectors. Avoid buying in deeply red sectors.")
    secs = regime_data.get("sectors", {})
    if secs:
        st.plotly_chart(build_sector_chart(secs), use_container_width=True)
        top3 = sorted(secs, key=secs.get, reverse=True)[:3]
        bot3 = sorted(secs, key=secs.get)[:3]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**🔥 Strongest sectors (look here first)**")
            for s in top3:
                st.markdown(f'- {pill(s, "green")} {secs[s]:+.1f}%', unsafe_allow_html=True)
        with c2:
            st.markdown("**❄️ Weakest sectors (avoid unless specific reason)**")
            for s in bot3:
                st.markdown(f'- {pill(s, "red")} {secs[s]:+.1f}%', unsafe_allow_html=True)

    st.divider()

    # Correlation warning
    st.markdown("**⚠️ Are you over-concentrated?**")
    st.caption("If many of your stocks are in the same sector, you are not as diversified as you think.")
    conn = sqlite3.connect(DB_PATH)
    wl = pd.read_sql("SELECT ticker FROM watchlist", conn)
    conn.close()
    if not wl.empty:
        sector_counts = {}
        for tk in wl["ticker"].tolist():
            inf = fetch_company_info(tk)
            sec = inf.get("sector", "Unknown")
            sector_counts[sec] = sector_counts.get(sec, 0) + 1
        for sec, cnt in sorted(sector_counts.items(), key=lambda x: -x[1]):
            pct = cnt / len(wl) * 100
            bar_color = "#ff1744" if pct > 40 else ("#ffd600" if pct > 25 else "#00e676")
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin:4px 0">'
                f'<div style="width:180px;font-size:0.82rem;color:#94a3b8">{sec}</div>'
                f'<div style="background:#1e2840;border-radius:4px;height:10px;width:200px">'
                f'<div style="width:{pct:.0f}%;height:100%;background:{bar_color};border-radius:4px"></div>'
                f'</div>'
                f'<div style="font-family:IBM Plex Mono;font-size:0.8rem;color:{bar_color}">'
                f'{cnt} stock(s) — {pct:.0f}%</div>'
                f'</div>',
                unsafe_allow_html=True
            )


# ─────────────────────────────────────────────
#  POSITION SIZING TAB
# ─────────────────────────────────────────────

def render_position_sizing_tab():
    st.markdown('<div class="section-header">📐 Position Sizing Calculator</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="advice-box"><div class="advice-text">'
        '<strong>Why this matters:</strong> Knowing which stock to buy is only half the job. '
        'The other half is knowing <em>how much</em> to buy. Most beginners lose money not because '
        'they picked bad stocks, but because they put too much money into a single trade. '
        'This calculator tells you exactly how many shares to buy based on your account size '
        'and how much you are willing to lose if the trade goes wrong.'
        '</div></div>',
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Enter your trade details")
        ps_ticker = st.text_input("Stock symbol", placeholder="e.g. AAPL").upper().strip()
        ps_account = st.number_input("Your account size ($)",
            value=st.session_state.account_size, min_value=100.0, step=500.0)
        ps_risk_pct = st.slider("Max % of account to risk on this trade",
            0.25, 5.0, st.session_state.max_risk_pct, 0.25)
        ps_price = st.number_input("Entry price ($)", min_value=0.01, step=0.01)
        ps_stop = st.number_input("Stop-loss price ($) — where you'll exit if wrong",
            min_value=0.01, step=0.01)
        ps_target = st.number_input("Target price ($) — where you plan to take profit",
            min_value=0.01, step=0.01)

        if ps_price > 0 and ps_stop > 0 and ps_stop < ps_price:
            sizing = calculate_position_size(ps_account, ps_risk_pct, ps_price, ps_stop)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f'<div class="tl-green">'
                f'<div style="font-family:Syne,sans-serif;font-size:1.1rem;font-weight:700;'
                f'color:#00e676;margin-bottom:12px">Your recommended trade</div>'
                f'<table style="width:100%;font-size:0.9rem;border-collapse:collapse">'
                f'<tr><td style="color:#64748b;padding:4px 0">Shares to buy</td>'
                f'<td style="font-family:IBM Plex Mono;color:#e2e8f0;text-align:right">'
                f'<strong>{sizing["shares"]}</strong></td></tr>'
                f'<tr><td style="color:#64748b;padding:4px 0">Total you will spend</td>'
                f'<td style="font-family:IBM Plex Mono;color:#e2e8f0;text-align:right">'
                f'${sizing["total_cost"]:,.2f}</td></tr>'
                f'<tr><td style="color:#64748b;padding:4px 0">% of your account used</td>'
                f'<td style="font-family:IBM Plex Mono;color:#e2e8f0;text-align:right">'
                f'{sizing["pct_of_account"]:.1f}%</td></tr>'
                f'<tr><td style="color:#64748b;padding:4px 0">Max dollar loss if stopped out</td>'
                f'<td style="font-family:IBM Plex Mono;color:#ff6b6b;text-align:right">'
                f'${sizing["dollar_risk"]:,.2f}</td></tr>'
                f'</table></div>',
                unsafe_allow_html=True
            )

            if ps_target > ps_price:
                rr = (ps_target - ps_price) / (ps_price - ps_stop)
                profit_if_target = sizing["shares"] * (ps_target - ps_price)
                rr_color = "#00e676" if rr >= 2 else ("#ffd600" if rr >= 1.5 else "#ff1744")
                rr_advice = ("Excellent — you stand to make at least 2× what you risk." if rr >= 2
                             else "Acceptable — but aim for 2:1 or better." if rr >= 1.5
                             else "⚠️ Poor — you risk more than you stand to gain. Reconsider.")
                st.markdown(
                    f'<div class="metric-box" style="margin-top:10px">'
                    f'<div class="label">Risk-to-Reward Ratio</div>'
                    f'<div class="value" style="color:{rr_color};font-size:2rem">1:{rr:.1f}</div>'
                    f'<div class="explain">{rr_advice}</div>'
                    f'<div style="font-size:0.82rem;color:#64748b;margin-top:6px">'
                    f'Profit if target hit: ${profit_if_target:,.2f}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    with c2:
        st.subheader("How position sizing works")
        st.markdown(
            '<div class="advice-box"><div class="advice-text">'
            '<strong>The formula (plain English):</strong><br><br>'
            '1. Decide the most you are willing to lose on this trade.<br>'
            '   Example: Account = $10,000, risk 1% = $100 max loss.<br><br>'
            '2. Decide where you will exit if the trade goes wrong (stop-loss).<br>'
            '   Example: Buy at $50, stop at $47 = $3 risk per share.<br><br>'
            '3. Divide: $100 ÷ $3 = 33 shares.<br><br>'
            '4. Total cost: 33 × $50 = $1,650 (16.5% of account).<br><br>'
            '<strong>Golden rules:</strong><br>'
            '• Never risk more than 1-2% of your account on one trade.<br>'
            '• Never put more than 20-25% of your account in one stock.<br>'
            '• Always set a stop-loss BEFORE you buy.<br>'
            '• Always know your Risk-to-Reward before entering — aim for 1:2 or better.<br>'
            '</div></div>',
            unsafe_allow_html=True
        )

        st.markdown("**What the numbers mean:**")
        glossary = [
            ("Stop-loss", "The price where you admit you were wrong and sell to limit your loss."),
            ("R-to-R ratio (Risk:Reward)", "How much you stand to gain vs how much you risk. 1:2 = risk $1 to potentially make $2."),
            ("Position size", "How many shares you buy — calculated to keep your risk within your limit."),
            ("ATR (Average True Range)", "The stock's average daily price swing. Used to set stop-losses that aren't too tight."),
        ]
        for term, defn in glossary:
            st.markdown(
                f'<div class="metric-box" style="text-align:left;margin-bottom:6px">'
                f'<div style="font-weight:600;color:#94a3b8;font-size:0.82rem">{term}</div>'
                f'<div style="font-size:0.8rem;color:#64748b;margin-top:3px">{defn}</div>'
                f'</div>',
                unsafe_allow_html=True
            )


# ─────────────────────────────────────────────
#  JOURNAL TAB (condensed, kept from v1 + improved)
# ─────────────────────────────────────────────

def render_journal_tab():
    st.markdown('<div class="section-header">📓 My Trade Journal</div>', unsafe_allow_html=True)

    with st.expander("➕ Record a new trade", expanded=False):
        with st.form("trade_form"):
            r1c1, r1c2, r1c3 = st.columns(3)
            tk_in  = r1c1.text_input("Stock symbol").upper()
            dir_in = r1c2.selectbox("Direction", ["LONG (bought to rise)", "SHORT (betting to fall)"])
            strat  = r1c3.text_input("Strategy name", placeholder="e.g. Breakout")

            r2c1, r2c2 = st.columns(2)
            ed = r2c1.date_input("Entry date (when you bought)")
            xd = r2c2.date_input("Exit date (when you sold)")

            r3c1, r3c2, r3c3 = st.columns(3)
            ep = r3c1.number_input("Entry price ($)", min_value=0.01, step=0.01)
            xp = r3c2.number_input("Exit price ($)", min_value=0.01, step=0.01)
            sh = r3c3.number_input("Number of shares", min_value=0.1, step=1.0)

            r4c1, r4c2, r4c3 = st.columns(3)
            sp_in  = r4c1.number_input("Stop-loss you used ($)", min_value=0.0, step=0.01)
            tgt_in = r4c2.number_input("Target you aimed for ($)", min_value=0.0, step=0.01)
            tag    = r4c3.text_input("Setup type", placeholder="e.g. EMA bounce")

            r5c1, r5c2, r5c3 = st.columns(3)
            mfe_in  = r5c1.number_input("Best % the trade reached (MFE)", step=0.1)
            mae_in  = r5c2.number_input("Worst % the trade reached (MAE)", step=0.1)
            mistake = r5c3.selectbox("Mistake type (if any)", [
                "None", "Wrong direction", "Right idea wrong timing",
                "Too big a position", "Emotional exit", "No stop-loss", "Other"
            ])
            viol = st.checkbox("⚠️ I broke one of my trading rules on this trade")

            st.markdown("**Behavioural log (Pillar IV — the most important section)**")
            st.caption("Honest answers here are what separates improving traders from stuck ones.")
            emotional_state = st.selectbox("How were you feeling when you entered this trade?", [
                "Calm and disciplined",
                "Excited / over-confident",
                "Fearful / hesitant",
                "Impatient — felt like I was missing out",
                "Recovering from a recent loss",
                "Bored / traded out of habit",
                "Other",
            ])
            thesis_in = st.text_area(
                "What was your original thesis? (Why did you buy this?)",
                placeholder="e.g. Breaking out above 50-day EMA with strong volume, earnings revision turning positive, sector in favour"
            )
            deviation_in = st.text_area(
                "Did you deviate from your plan? If yes, how and why?",
                placeholder="e.g. Held past my stop-loss because I was convinced it would recover"
            )
            exit_reason_in = st.selectbox("Why did you exit?", [
                "Hit my pre-planned target",
                "Hit my stop-loss",
                "Thesis broke down (fundamentals changed)",
                "Technical signal reversed",
                "Emotional exit — I panicked",
                "Emotional exit — I got greedy and held too long",
                "Position too large, reduced stress",
                "Other",
            ])
            notes_in = st.text_area("Additional notes and lessons learned")

            if st.form_submit_button("💾 Save trade"):
                direction = "LONG" if "LONG" in dir_in else "SHORT"
                pnl = (xp - ep) * sh if direction=="LONG" else (ep - xp) * sh
                pnl_pct = (xp/ep-1) if direction=="LONG" else (ep/xp-1)
                stop_dist = ep - sp_in if sp_in > 0 else None
                r_mult = (pnl / (stop_dist * sh)) if stop_dist and stop_dist > 0 else None
                conn = sqlite3.connect(DB_PATH)
                conn.execute("""
                    INSERT INTO trades
                    (ticker,direction,entry_date,exit_date,entry_price,exit_price,
                     shares,pnl,pnl_pct,r_multiple,stop_price,target_price,
                     strategy,setup_tag,notes,mistake_type,mfe,mae,rule_violation,
                     emotional_state,thesis,deviation_from_plan,exit_reason)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (tk_in, direction, str(ed), str(xd), ep, xp, sh,
                      round(pnl,2), round(pnl_pct,4), r_mult, sp_in or None,
                      tgt_in or None, strat, tag, notes_in,
                      mistake if mistake != "None" else None,
                      mfe_in, mae_in, int(viol),
                      emotional_state, thesis_in, deviation_in, exit_reason_in))
                conn.commit()
                conn.close()
                st.success(f"Saved! P&L: ${pnl:+.2f} ({pnl_pct*100:+.1f}%)")
                st.rerun()

    conn = sqlite3.connect(DB_PATH)
    tdf = pd.read_sql("SELECT * FROM trades ORDER BY exit_date DESC", conn)
    conn.close()

    if tdf.empty:
        st.info("Your journal is empty. Start logging trades above to track your performance.")
        return

    wins = (tdf["pnl"] > 0).sum()
    n    = len(tdf)
    wr   = wins / n
    avg_w = tdf[tdf["pnl"]>0]["pnl_pct"].mean() or 0
    avg_l = tdf[tdf["pnl"]<0]["pnl_pct"].mean() or 0
    exp   = wr*avg_w + (1-wr)*avg_l
    total_pnl = tdf["pnl"].sum()

    ts = tdf.sort_values("exit_date")
    ts["equity"] = ts["pnl"].cumsum()
    dd = (ts["equity"] - ts["equity"].cummax()).min()

    rm = tdf["r_multiple"].dropna()
    avg_r = rm.mean() if not rm.empty else None

    ret_std = tdf["pnl_pct"].std()
    ret_mean = tdf["pnl_pct"].mean()
    sharpe = (ret_mean / ret_std * np.sqrt(252)) if ret_std > 0 else 0

    # Stats row
    st.markdown('<div class="section-header" style="font-size:1rem">Your performance at a glance</div>',
                unsafe_allow_html=True)
    m_cols = st.columns(8)
    stats = [
        ("Total trades", n, ""),
        ("Win rate", f"{wr*100:.1f}%", "% of trades profitable"),
        ("Total profit/loss", f"${total_pnl:+,.0f}", ""),
        ("Average winner", f"{avg_w*100:+.1f}%", ""),
        ("Average loser", f"{avg_l*100:+.1f}%", ""),
        ("Expectancy per trade", f"{exp*100:+.2f}%", "Average outcome per trade"),
        ("Max drawdown", f"${dd:,.0f}", "Worst losing streak"),
        ("Sharpe ratio", f"{sharpe:.2f}", ">1 = good risk-adjusted return"),
    ]
    for col, (lbl, val, exp_txt) in zip(m_cols, stats):
        col.markdown(mbox(lbl, val, exp_txt), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    chart_c1, chart_c2 = st.columns(2)
    with chart_c1:
        st.plotly_chart(build_equity_curve(tdf), use_container_width=True)
    with chart_c2:
        st.plotly_chart(build_pnl_by_month(tdf), use_container_width=True)

    # MFE/MAE
    st.plotly_chart(build_mfe_mae(tdf), use_container_width=True)

    # By setup tag
    if tdf["setup_tag"].notna().any():
        st.markdown('<div class="section-header" style="font-size:1rem">Which setups work best for you?</div>',
                    unsafe_allow_html=True)
        tag_stats = tdf.groupby("setup_tag").agg(
            Trades=("pnl","count"),
            Win_Rate=("pnl", lambda x: f"{(x>0).mean()*100:.0f}%"),
            Avg_PnL=("pnl","mean"),
            Total_PnL=("pnl","sum")
        ).round(2).reset_index()
        st.dataframe(tag_stats, use_container_width=True, hide_index=True)

    # Mistakes
    if "mistake_type" in tdf.columns and tdf["mistake_type"].notna().any():
        mistakes = tdf[tdf["mistake_type"].notna()]
        if not mistakes.empty:
            st.markdown('<div class="section-header" style="font-size:1rem">Your most common mistakes</div>',
                        unsafe_allow_html=True)
            mc = mistakes["mistake_type"].value_counts().reset_index()
            mc.columns = ["Mistake", "Times"]
            st.dataframe(mc, use_container_width=True, hide_index=True)

    # Behavioural pattern report (Pillar IV)
    st.markdown('<div class="section-header" style="font-size:1rem">🧠 Behavioural Pattern Report (Pillar IV)</div>',
                unsafe_allow_html=True)
    st.caption("This is where real improvement happens. Your patterns, mapped honestly.")

    if "emotional_state" in tdf.columns and tdf["emotional_state"].notna().any():
        emo_df = tdf[tdf["emotional_state"].notna()]

        # Emotional state vs outcome
        emo_pnl = emo_df.groupby("emotional_state")["pnl"].agg(
            Trades="count",
            Win_Rate=lambda x: f"{(x>0).mean()*100:.0f}%",
            Avg_PnL="mean",
        ).round(2).reset_index()
        emo_pnl.columns = ["Emotional State at Entry", "Trades", "Win Rate", "Avg P&L ($)"]

        st.markdown("**How your emotional state affects your results:**")
        st.dataframe(emo_pnl, use_container_width=True, hide_index=True)

        # Best and worst emotional states
        emo_numeric = emo_df.groupby("emotional_state")["pnl"].mean()
        if len(emo_numeric) >= 2:
            best_state  = emo_numeric.idxmax()
            worst_state = emo_numeric.idxmin()
            st.markdown(
                f'<div class="advice-box"><div class="advice-text">' +
                f'<strong>Your best results come when you feel: {best_state}</strong><br>' +
                f'<strong>Your worst results come when you feel: {worst_state}</strong><br><br>' +
                f'If you notice you are in the "{worst_state}" state before a trade, ' +
                f'that is your trigger to pause, wait 30 minutes, and re-evaluate.' +
                f'</div></div>',
                unsafe_allow_html=True
            )
    else:
        st.info("Start logging your emotional state on trades to unlock this analysis.")

    # Exit reason analysis
    if "exit_reason" in tdf.columns and tdf["exit_reason"].notna().any():
        exit_df = tdf[tdf["exit_reason"].notna()]
        exit_pnl = exit_df.groupby("exit_reason")["pnl"].agg(
            Trades="count",
            Win_Rate=lambda x: f"{(x>0).mean()*100:.0f}%",
            Avg_PnL="mean",
        ).round(2).reset_index()
        exit_pnl.columns = ["Exit Reason", "Trades", "Win Rate", "Avg P&L ($)"]
        st.markdown("**Your exit reason analysis — are you exiting for the right reasons?**")
        st.dataframe(exit_pnl, use_container_width=True, hide_index=True)

    # Rule violations
    viols = tdf[tdf["rule_violation"]==1]
    if not viols.empty:
        st.error(f"⚠️ {len(viols)} trades where you broke your own rules. "
                 f"Average P&L on those trades: ${viols['pnl'].mean():+.2f}")


# ─────────────────────────────────────────────
#  GLOSSARY TAB
# ─────────────────────────────────────────────

def render_glossary():
    st.markdown('<div class="section-header">📖 Plain English Glossary</div>',
                unsafe_allow_html=True)
    st.caption("Every term used in this dashboard, explained without jargon.")

    terms = [
        ("Moving Average (EMA — Exponential Moving Average)",
         "An average of past prices that smooths out daily ups and downs to show the underlying trend. "
         "EMA9 = 9-day average, EMA20 = 20-day, EMA50 = 50-day, EMA200 = 200-day. "
         "When the current price is above the average, the trend is up. When below, the trend is down."),
        ("RSI — Relative Strength Index",
         "A number from 0 to 100 that measures how fast a stock has been moving. "
         "Above 70 means it may have risen too quickly (overbought — could fall back). "
         "Below 30 means it may have fallen too hard (oversold — could bounce back). "
         "Between 40–60 is the healthy zone."),
        ("MACD — Moving Average Convergence Divergence",
         "A tool that compares two moving averages to show whether momentum is building up or fading. "
         "When the MACD line crosses above its signal line — a potential buy signal. "
         "When it crosses below — a potential warning. When both are above zero — generally positive."),
        ("VWAP — Volume-Weighted Average Price",
         "The average price for the day, but weighted by how much was traded at each price. "
         "Professional fund managers use it as a benchmark. Price above VWAP = positive. Below = negative."),
        ("OBV — On-Balance Volume",
         "Tracks whether buying volume is exceeding selling volume over time. "
         "A rising OBV alongside a rising price confirms a healthy uptrend. "
         "If OBV falls while price rises, it can be a warning sign."),
        ("Bollinger Bands",
         "Two lines drawn above and below a moving average, representing the normal range of price movement. "
         "When price touches the upper band, it may be getting overextended. "
         "When it touches the lower band, it may be due for a bounce."),
        ("ATR — Average True Range",
         "The stock's average daily price movement over the past 14 days. "
         "A high ATR means the stock is volatile (big daily swings). "
         "Used to set sensible stop-losses that give the trade room to breathe."),
        ("VIX — CBOE Volatility Index",
         "The market's 'fear gauge.' Measures how much uncertainty there is in the overall market. "
         "Below 15 = calm and confident. 15–25 = normal. Above 30 = fear and panic."),
        ("Fear & Greed Index",
         "A 0–100 score measuring overall investor emotion. "
         "0 = extreme fear (everyone is selling). 100 = extreme greed (everyone is buying). "
         "Contrarian investors often buy near extreme fear and sell near extreme greed."),
        ("P/E Ratio — Price-to-Earnings",
         "How much you're paying for every $1 of profit the company makes. "
         "A P/E of 15 means you pay $15 for each $1 of annual earnings. "
         "Lower generally means cheaper, but growth companies can justify higher P/E ratios."),
        ("Forward P/E",
         "Same as P/E but uses expected future earnings instead of past earnings. "
         "If forward P/E is lower than trailing P/E, the company is expected to grow earnings."),
        ("P/B Ratio — Price-to-Book",
         "Compares the stock price to the company's accounting value (its assets minus liabilities). "
         "Below 1 can mean the stock is cheap relative to what it owns. Above 3 is considered expensive."),
        ("D/E — Debt-to-Equity",
         "How much debt the company has compared to shareholder equity. "
         "A ratio of 50 means for every $100 of equity, it has $50 of debt. "
         "Higher = more financial risk, especially if interest rates rise."),
        ("ROE — Return on Equity",
         "How much profit the company generates from each dollar of shareholder investment. "
         "15% or above is generally considered good. Above 25% is excellent."),
        ("FCF — Free Cash Flow",
         "The actual cash left over after paying operating costs and capital expenses. "
         "Positive FCF = the company generates real money. Negative FCF = it's burning cash."),
        ("Short Interest / Short Sellers",
         "The percentage of shares that investors are 'shorting' — betting the price will fall. "
         "Very high short interest (above 15%) can cause a 'short squeeze' if the price rises, "
         "forcing shorts to buy back shares and drive the price up rapidly."),
        ("Put/Call Ratio (P/C Ratio)",
         "Compares the number of options bets placed on a stock falling (puts) vs rising (calls). "
         "Below 0.7 = mostly bullish bets. Above 1.2 = mostly bearish bets."),
        ("Institutional Ownership",
         "The percentage of shares held by large professional investors (pension funds, hedge funds, mutual funds). "
         "High institutional ownership generally indicates confidence from professionals."),
        ("Beta",
         "How much the stock moves relative to the overall market (S&P 500). "
         "Beta 1.0 = moves exactly with the market. Beta 2.0 = moves twice as much, in both directions. "
         "High beta = more volatile = more risk and more potential reward."),
        ("R-Multiple",
         "Measures a trade's result in units of risk. "
         "If you risked $100 and made $200, that's a 2R trade. "
         "Good traders aim for a positive average R-multiple over many trades."),
        ("Sharpe Ratio",
         "Measures return relative to risk taken. Above 1.0 is good, above 2.0 is excellent. "
         "A high Sharpe means you're making good returns without taking unnecessary risks."),
        ("MFE — Maximum Favorable Excursion",
         "The furthest a trade went in your favour before you exited. "
         "If your MFE was much higher than your actual exit, you may be exiting too early."),
        ("MAE — Maximum Adverse Excursion",
         "The furthest a trade went against you before recovering (or before you stopped out). "
         "Helps you set smarter stop-losses that aren't too tight."),
        ("Stop-loss",
         "A pre-set price where you will automatically sell and accept a small loss "
         "rather than letting a bad trade become a catastrophic one. "
         "Always set this BEFORE you buy."),
        ("Risk-to-Reward Ratio (R:R)",
         "How much you stand to gain versus how much you risk. "
         "1:2 means if you risk $100, you are aiming to make $200. "
         "Never take a trade with less than 1:1.5. Aim for 1:2 or better."),
        ("Expectancy",
         "Your average profit or loss per trade when calculated over many trades. "
         "Positive expectancy = your system makes money over time, even if some trades lose."),
        ("Market Regime",
         "Whether the overall market is in an uptrend (bull), downtrend (bear), or sideways (mixed). "
         "Knowing the regime helps you decide how aggressive to be. "
         "In a bull market, buying pullbacks works well. In a bear market, patience is key."),
        ("Relative Strength (RS vs SPY)",
         "How the stock is performing compared to the overall S&P 500 index. "
         "A stock showing relative strength is outperforming the market — a positive sign. "
         "Look for stocks that go up more than the market does, and fall less when the market drops."),
    ]

    for term, defn in terms:
        with st.expander(term):
            st.markdown(f'<div style="font-size:0.9rem;color:#94a3b8;line-height:1.7">{defn}</div>',
                        unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────


# ─────────────────────────────────────────────
#  MARKET SCANNER — Universe + Opportunity Finder
# ─────────────────────────────────────────────

# The full universe of stocks to scan across three lists
def get_scan_universe() -> list:
    """
    Returns the combined list of tickers to scan.
    S&P 500 leaders + NASDAQ 100 + Top 50 most traded.
    Deduplicated so we never scan the same stock twice.
    """
    # S&P 500 representative sample by sector (top 10 per sector = ~110 stocks)
    sp500_sample = [
        # Technology
        "AAPL","MSFT","NVDA","AVGO","ORCL","CRM","AMD","INTC","QCOM","TXN",
        "AMAT","MU","KLAC","LRCX","ADI","MRVL","CDNS","SNPS","FTNT","PANW",
        # Healthcare
        "LLY","UNH","JNJ","ABBV","MRK","TMO","ABT","DHR","BMY","AMGN",
        "GILD","VRTX","REGN","ISRG","SYK","ELV","CI","HUM","CVS","MDT",
        # Financials
        "BRK-B","JPM","V","MA","BAC","WFC","GS","MS","BLK","SCHW",
        "AXP","SPGI","MCO","ICE","CME","PGR","TRV","AFL","MET","PRU",
        # Consumer Discretionary
        "AMZN","TSLA","HD","MCD","NKE","SBUX","TJX","LOW","BKNG","CMG",
        "ABNB","EBAY","ETSY","ROST","DG","DLTR","YUM","DRI","HLT","MAR",
        # Communication Services
        "META","GOOGL","GOOG","NFLX","DIS","CMCSA","T","VZ","TMUS","ATVI",
        "EA","TTWO","WBD","PARA","FOX","OMC","IPG","NWSA","LYV","ZG",
        # Industrials
        "CAT","BA","HON","UPS","RTX","LMT","GE","MMM","DE","FDX",
        "CSX","UNP","NSC","EMR","ETN","PH","ROK","IR","XYL","FAST",
        # Consumer Staples
        "PG","KO","PEP","COST","WMT","PM","MO","MDLZ","CL","GIS",
        "K","CPB","HSY","SJM","CAG","MKC","HRL","TSN","KHC","STZ",
        # Energy
        "XOM","CVX","COP","EOG","SLB","MPC","PSX","VLO","OXY","PXD",
        "HES","DVN","FANG","APA","HAL","BKR","MRO","NOV","RIG","CVI",
        # Utilities
        "NEE","DUK","SO","AEP","EXC","SRE","XEL","ED","WEC","ES",
        # Real Estate
        "PLD","AMT","EQIX","CCI","PSA","O","WELL","AVB","EQR","DLR",
        # Materials
        "LIN","APD","ECL","SHW","FCX","NEM","NUE","VMC","MLM","CE",
    ]

    # NASDAQ 100 additions not already in SP500 sample
    nasdaq100_extra = [
        "ADBE","PYPL","INTU","ISRG","LULU","MNST","MELI","NXPI","WDAY",
        "TEAM","ZS","DDOG","CRWD","SNOW","OKTA","MDB","COIN","RBLX",
        "HOOD","RIVN","LCID","ZM","DOCU","PTON","U","ROKU","TTD","APP",
        "PLTR","SOUN","IONQ","SMCI","ARM","DELL","HPQ","ANET","FFIV",
    ]

    # Top 50 highest volume / most traded (retail favourites)
    top_volume = [
        "SPY","QQQ","IWM","GLD","SLV","USO","TLT","HYG","EEM","VXX",
        "SQQQ","TQQQ","SPXU","SPXL","UVXY","SVXY","ARKK","ARKG","ARKW",
        "GME","AMC","BBBY","SOFI","MARA","RIOT","CLSK","HUT","BTBT",
        "IBIT","BITO","GBTC","ETHE","F","GM","RIVN","NIO","XPEV","LI",
        "BABA","JD","PDD","KWEB","FXI","EWZ","GDX","GDXJ","SIL","SILJ",
    ]

    all_tickers = list(dict.fromkeys(sp500_sample + nasdaq100_extra + top_volume))
    return all_tickers


def quick_screen(ticker: str) -> dict:
    """
    Fast pre-filter: only download 1-month daily data.
    Checks the six opportunity signals quickly without full scoring.
    Returns a dict with signal flags and basic metrics.
    """
    try:
        df = fetch_prices(ticker, period="3mo", interval="1d")
        if df is None or len(df) < 20:
            return None

        close  = df["Close"]
        volume = df["Volume"]
        price  = close.iloc[-1]
        hi52   = close.max()
        lo52   = close.min()

        # Moving averages
        ema20  = close.ewm(span=20, adjust=False).mean().iloc[-1]
        ema50  = close.ewm(span=50, adjust=False).mean()
        ema50_last = ema50.iloc[-1]

        # RSI
        delta  = close.diff()
        gain   = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
        loss   = (-delta).clip(lower=0).ewm(com=13, adjust=False).mean()
        rsi    = (100 - (100 / (1 + gain / loss.replace(0, np.nan)))).iloc[-1]

        # MACD
        ema12  = close.ewm(span=12, adjust=False).mean()
        ema26  = close.ewm(span=26, adjust=False).mean()
        macd   = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        macd_cross_up = (macd.iloc[-2] < signal.iloc[-2]) and (macd.iloc[-1] > signal.iloc[-1])
        macd_bullish  = macd.iloc[-1] > signal.iloc[-1]

        # Volume spike
        avg_vol   = volume.rolling(20).mean().iloc[-1]
        vol_ratio = volume.iloc[-1] / avg_vol if avg_vol > 0 else 1

        # Momentum
        mo1m = (price / close.iloc[-21] - 1) * 100 if len(close) >= 21 else 0
        mo1w = (price / close.iloc[-5]  - 1) * 100 if len(close) >= 5  else 0

        # Near 52-week high (within 5%)
        near_52w_high = price >= hi52 * 0.95

        # Breakout — price just crossed above 50 EMA
        breakout = (df["Close"].iloc[-2] < ema50.iloc[-2]) and (price > ema50_last)

        # Uptrend — price above both EMAs
        uptrend = price > ema20 and price > ema50_last

        # Signals
        signals = []
        signal_score = 0

        if uptrend and rsi > 50 and macd_bullish:
            signals.append("🟢 Breaking out upward")
            signal_score += 30

        if vol_ratio > 2.0:
            signals.append(f"🔊 Volume spike ({vol_ratio:.1f}×)")
            signal_score += 20

        if near_52w_high and mo1m > 5:
            signals.append("🏔 Near 52-week high with momentum")
            signal_score += 20

        if macd_cross_up:
            signals.append("⚡ MACD just turned bullish")
            signal_score += 15

        if mo1m > 15:
            signals.append(f"🚀 Strong momentum (+{mo1m:.1f}% this month)")
            signal_score += 15

        if mo1w > 5:
            signals.append(f"📈 Strong this week (+{mo1w:.1f}%)")
            signal_score += 10

        # Only return if at least one signal fired
        if signal_score == 0:
            return None

        return {
            "ticker":       ticker,
            "price":        round(price, 2),
            "rsi":          round(rsi, 1),
            "vol_ratio":    round(vol_ratio, 2),
            "mo1m":         round(mo1m, 2),
            "mo1w":         round(mo1w, 2),
            "near_52w_high":near_52w_high,
            "uptrend":      uptrend,
            "macd_bullish": macd_bullish,
            "signals":      signals,
            "signal_score": signal_score,
        }
    except Exception:
        return None


def render_market_scanner_tab(fear_greed: dict, vix: float, regime_data: dict):
    """
    The full market opportunity scanner tab.
    Scans the entire universe, surfaces the best setups,
    and presents them as a ranked table + expandable top-10 cards.
    """
    st.markdown(
        '<div class="section-header">🔭 Market Opportunity Scanner</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="advice-box"><div class="advice-text">' +
        '<strong>What this does:</strong> Scans ' +
        str(len(get_scan_universe())) +
        ' stocks across the S&P 500, NASDAQ 100, and top-traded ETFs/stocks. ' +
        'It finds the ones showing the strongest signals right now — breakouts, ' +
        'volume spikes, momentum, and 52-week strength. ' +
        'The full scan takes 5–15 minutes. Results are cached for 4 hours so you ' +
        'only wait once per session.' +
        '</div></div>',
        unsafe_allow_html=True
    )

    # Show last run time
    last_run = st.session_state.get("scanner_last_run", 0)
    cache_age = (time.time() - last_run) / 3600 if last_run else None

    col1, col2 = st.columns([2, 1])
    with col1:
        if last_run:
            run_time = datetime.datetime.fromtimestamp(last_run).strftime("%H:%M:%S")
            st.caption(f"Last scan: {run_time} — cache valid for 4 hours")
        else:
            st.caption("No scan run yet this session.")

    with col2:
        run_scan = st.button(
            "🔭 Run Full Market Scan",
            type="primary",
            help="Scans all stocks — takes 5–15 minutes"
        )

    # Filters
    st.markdown("<br>", unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        min_score = st.slider(
            "Minimum signal score", 10, 60, 20, 5,
            help="Higher = only show stocks with multiple strong signals"
        )
    with fc2:
        sort_by = st.selectbox(
            "Sort results by",
            ["Signal Score", "1-Month Return %", "Volume Spike", "RSI"]
        )
    with fc3:
        max_results = st.slider("Max results to show", 10, 100, 50, 10)

    st.divider()

    # ── Run the scan ──
    if run_scan:
        universe = get_scan_universe()
        total    = len(universe)
        results  = []

        prog     = st.progress(0, text="Starting scan…")
        status   = st.empty()
        found_box = st.empty()

        for i, tk in enumerate(universe):
            pct = (i + 1) / total
            prog.progress(pct, text=f"Scanning {tk} ({i+1}/{total})…")
            status.caption(f"Found {len(results)} opportunities so far…")

            result = quick_screen(tk)
            if result:
                results.append(result)
                # Show live running count
                found_box.success(f"✅ {len(results)} opportunities found so far — still scanning…")

            time.sleep(0.15)  # Polite delay to avoid rate limits

        prog.empty()
        status.empty()
        found_box.empty()

        st.session_state["scanner_results"] = results
        st.session_state["scanner_last_run"] = time.time()
        st.success(f"✅ Scan complete — found {len(results)} opportunities across {total} stocks")

    # ── Display results ──
    results = st.session_state.get("scanner_results", [])

    if not results:
        st.info(
            "Click **🔭 Run Full Market Scan** above to find opportunities across the market. "
            "First run takes 5–15 minutes. After that, results are cached for 4 hours."
        )
        return

    # Filter and sort
    filtered = [r for r in results if r["signal_score"] >= min_score]

    sort_map = {
        "Signal Score":      lambda x: x["signal_score"],
        "1-Month Return %":  lambda x: x["mo1m"],
        "Volume Spike":      lambda x: x["vol_ratio"],
        "RSI":               lambda x: x["rsi"],
    }
    filtered = sorted(filtered, key=sort_map[sort_by], reverse=True)[:max_results]

    if not filtered:
        st.warning(f"No stocks met the minimum signal score of {min_score}. Try lowering the filter.")
        return

    st.markdown(
        f'<div class="section-header">Found {len(filtered)} opportunities</div>',
        unsafe_allow_html=True
    )

    # ── SUMMARY TABLE ──
    st.markdown("### 📋 Ranked Summary Table")
    st.caption("All opportunities at a glance — sorted by your chosen metric. Click a row to explore.")

    table_rows = []
    for r in filtered:
        signals_short = " · ".join(r["signals"][:2])  # Show first 2 signals
        table_rows.append({
            "Ticker":          r["ticker"],
            "Price ($)":       r["price"],
            "Signal Score":    r["signal_score"],
            "1M Return (%)":   r["mo1m"],
            "1W Return (%)":   r["mo1w"],
            "Volume Spike":    f'{r["vol_ratio"]:.1f}×',
            "RSI":             r["rsi"],
            "Near 52W High":   "✅" if r["near_52w_high"] else "",
            "Uptrend":         "✅" if r["uptrend"] else "",
            "Key Signals":     signals_short,
        })

    table_df = pd.DataFrame(table_rows)
    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Signal Score": st.column_config.ProgressColumn(
                "Signal Score", min_value=0, max_value=80, format="%d"
            ),
            "1M Return (%)": st.column_config.NumberColumn(
                "1M Return (%)", format="%.1f%%"
            ),
        }
    )

    # Export to watchlist
    st.markdown("<br>", unsafe_allow_html=True)
    ec1, ec2 = st.columns([3, 1])
    with ec1:
        add_ticker = st.selectbox(
            "Add a scanner result to your watchlist for deeper analysis:",
            ["— select —"] + [r["ticker"] for r in filtered]
        )
    with ec2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Add to Watchlist") and add_ticker != "— select —":
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "INSERT OR IGNORE INTO watchlist (ticker) VALUES (?)",
                (add_ticker,)
            )
            conn.commit()
            conn.close()
            st.success(f"Added {add_ticker} to your watchlist!")

    st.divider()

    # ── TOP 10 DETAILED CARDS ──
    st.markdown("### 🏆 Top 10 Opportunities — Detailed View")
    st.caption(
        "The strongest setups from the scan. For each one you can run a full "
        "AI analysis or add it to your watchlist."
    )

    top10 = filtered[:10]

    for r in top10:
        tk    = r["ticker"]
        score = r["signal_score"]
        mo1m  = r["mo1m"]
        mo1w  = r["mo1w"]

        # Score colour
        if score >= 50:   card_css, score_color = "tl-green",  "#00e676"
        elif score >= 30: card_css, score_color = "tl-yellow", "#ffd600"
        else:             card_css, score_color = "tl-red",    "#ff1744"

        mo_color = "#00e676" if mo1m >= 0 else "#ff1744"

        with st.container():
            st.markdown(f'<div class="{card_css}">', unsafe_allow_html=True)

            # Header
            hc1, hc2, hc3 = st.columns([3, 2, 2])
            with hc1:
                st.markdown(
                    f'<span style="font-family:Syne,sans-serif;font-size:1.3rem;' +
                    f'font-weight:800;color:{score_color}">{tk}</span>',
                    unsafe_allow_html=True
                )
            with hc2:
                st.markdown(
                    f'<div style="text-align:center">' +
                    f'<div class="score-num" style="color:{score_color}">{score}</div>' +
                    f'<div class="score-label" style="color:{score_color}">SIGNAL SCORE</div>' +
                    f'</div>',
                    unsafe_allow_html=True
                )
            with hc3:
                st.markdown(
                    f'<div style="text-align:right">' +
                    f'<div style="font-family:IBM Plex Mono;font-size:1.3rem;color:#e2e8f0">' +
                    f'${r["price"]:.2f}</div>' +
                    f'<div style="color:{mo_color};font-size:0.85rem">' +
                    f'{"▲" if mo1m >= 0 else "▼"} {abs(mo1m):.1f}% this month</div>' +
                    f'</div>',
                    unsafe_allow_html=True
                )

            # Signal pills
            pills_html = " ".join([
                f'<span class="alert-pill pill-green">{s}</span>'
                for s in r["signals"]
            ])
            st.markdown(pills_html, unsafe_allow_html=True)

            # Quick metrics
            qc1, qc2, qc3, qc4 = st.columns(4)
            qc1.metric("RSI", f'{r["rsi"]:.0f}',
                        help="30=oversold, 70=overbought. 40-60 is the healthy zone.")
            qc2.metric("Volume spike", f'{r["vol_ratio"]:.1f}×',
                        help="How much more volume than the 20-day average")
            qc3.metric("1-week return", f'{r["mo1w"]:+.1f}%')
            qc4.metric("Near 52W high", "Yes ✅" if r["near_52w_high"] else "No")

            # Action buttons
            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button(f"➕ Add {tk} to watchlist", key=f"scan_add_{tk}"):
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute(
                        "INSERT OR IGNORE INTO watchlist (ticker) VALUES (?)", (tk,)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Added {tk} to your watchlist!")

            with bc2:
                if st.button(f"🤖 Quick AI take on {tk}", key=f"scan_ai_{tk}"):
                    with st.spinner("Claude is analysing…"):
                        # Fetch minimal data for quick AI take
                        info_q   = fetch_company_info(tk)
                        df_q     = fetch_prices(tk, period="3mo")
                        df_q     = add_indicators(df_q.copy()) if df_q is not None else None
                        opts_q   = fetch_options_ratio(tk)
                        risk_q   = calculate_score(tk, df_q, info_q, opts_q, fear_greed, vix)
                        analyst_q = fetch_analyst_consensus(tk)
                        insider_q = fetch_insider_activity(tk)
                        news_q   = fetch_news_sentiment(tk, st.session_state.finnhub_key)
                        ai_text  = fetch_ai_analysis(
                            tk, info_q, risk_q, analyst_q, insider_q, news_q, regime_data
                        )
                        st.session_state[f"scan_ai_text_{tk}"] = ai_text

            if f"scan_ai_text_{tk}" in st.session_state:
                st.markdown(
                    f'<div class="advice-box"><div class="advice-text" ' +
                    f'style="font-size:0.88rem;line-height:1.7">' +
                    f'{st.session_state[f"scan_ai_text_{tk}"].replace(chr(10), "<br>")}' +
                    f'</div></div>',
                    unsafe_allow_html=True
                )

            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

def main():
    # Title
    st.markdown(
        '<h1 style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;'
        'background:linear-gradient(90deg,#00e676,#38bdf8);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
        'margin-bottom:0">Smart Stock Advisor Dashboard</h1>'
        '<p style="color:#475569;font-size:0.85rem;margin-top:4px">'
        '⚠️ Educational tool only. Not financial advice. '
        'Yahoo Finance data is 15-minute delayed. Always do your own research.</p>',
        unsafe_allow_html=True
    )

    # Refresh status bar
    now = time.time()
    interval = st.session_state.refresh_interval
    elapsed  = now - st.session_state.last_refresh

    if not st.session_state.paused:
        remaining = max(0, interval - elapsed)
        rc1, rc2 = st.columns([5, 1])
        rc1.caption(
            f"🔄 Refreshing every {interval}s — next update in ~{remaining:.0f}s  |  "
            f"Last updated: {datetime.datetime.fromtimestamp(st.session_state.last_refresh).strftime('%H:%M:%S') if st.session_state.last_refresh else 'not yet'}"
        )
        if rc2.button("↺ Update now"):
            st.session_state.last_refresh = 0
            st.rerun()
    else:
        st.warning("⏸ Scanning is paused. Toggle it back on in the sidebar to resume.")

    # Shared market data (fetched once, reused everywhere)
    fear_greed  = fetch_fear_greed()
    vix         = fetch_vix()
    regime_data = fetch_market_regime()

    # Market summary bar
    watchlist = [row[0] for row in
                 sqlite3.connect(DB_PATH).execute("SELECT ticker FROM watchlist").fetchall()]
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    mc1.metric("Market mood (F&G)", f'{fear_greed.get("value","?")} — {fear_greed.get("label","")}')
    mc2.metric("Market fear (VIX)", str(vix) if vix else "N/A")
    mc3.metric("Market regime", regime_data.get("regime", "Unknown"))
    mc4.metric("Stocks tracked", len(watchlist))
    mc5.metric("Scanning", "PAUSED 🔋" if st.session_state.paused else "LIVE ✅")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TABS ──
    tab_tl, tab_detail, tab_scanner, tab_regime, tab_size, tab_journal, tab_glossary = st.tabs([
        "🚦 My Stock List",
        "🔬 Deep Dive",
        "🔭 Market Scanner",
        "🌍 Market Health",
        "📐 Position Sizing",
        "📓 Journal",
        "📖 Glossary"
    ])

    # Pre-load all watchlist data
    all_results = []
    if watchlist and not st.session_state.paused:
        prog = st.progress(0, text="Loading your watchlist…")
        for i, tk in enumerate(watchlist):
            prog.progress((i+1)/len(watchlist), text=f"Analysing {tk}…")
            df_raw = fetch_prices(tk)
            df     = add_indicators(df_raw.copy()) if df_raw is not None else None
            info   = fetch_company_info(tk)
            opts   = fetch_options_ratio(tk)
            risk   = calculate_score(tk, df, info, opts, fear_greed, vix)
            anom   = detect_anomalies(tk, df, info)
            analyst  = fetch_analyst_consensus(tk)
            insider  = fetch_insider_activity(tk)
            news_sent = fetch_news_sentiment(tk, st.session_state.finnhub_key)
            all_results.append({
                "ticker": tk, "df": df, "info": info,
                "opts": opts, "risk": risk, "anomalies": anom,
                "analyst": analyst, "insider": insider, "news_sent": news_sent,
            })
            # Save anomaly alerts
            if anom:
                conn = sqlite3.connect(DB_PATH)
                for a in anom:
                    conn.execute(
                        "INSERT INTO alerts (ticker,alert_type,message,risk_score) VALUES (?,?,?,?)",
                        (tk, a["type"], a["msg"], risk["score"])
                    )
                conn.commit()
                conn.close()
            time.sleep(0.2)
        prog.empty()

    # ── TAB: Traffic Light List ──
    with tab_tl:
        # Fetch gate and factor data for this render
        gate_data    = fetch_market_gate_data()
        vix_now      = fetch_vix()
        factor_data  = get_factor_regime_label(
            regime_data.get("regime", "MIXED MARKET"),
            vix_now or 20,
            regime_data.get("sectors", {})
        )

        # Factor regime banner
        fc = factor_data["color"]
        st.markdown(
            f'<div style="background:rgba(0,0,0,0.2);border:1px solid {fc}44;' +
            f'border-radius:8px;padding:12px 16px;margin-bottom:12px">' +
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">' +
            f'<span style="font-family:Syne,sans-serif;font-size:0.78rem;font-weight:700;' +
            f'color:#64748b;text-transform:uppercase;letter-spacing:0.1em">Current Market Factor</span>' +
            f'<span style="font-family:Syne,sans-serif;font-size:1rem;font-weight:800;' +
            f'color:{fc}">{factor_data["factor"]}</span></div>' +
            f'<div style="font-size:0.83rem;color:#94a3b8;margin-bottom:4px">{factor_data["description"]}</div>' +
            f'<div style="font-size:0.8rem;color:{fc}"><strong>What to look for:</strong> {factor_data["what_to_buy"]}</div>' +
            f'</div>',
            unsafe_allow_html=True
        )

        # Pillar I gate
        render_market_gate(gate_data)

        render_traffic_light_list(all_results, regime_data)

    # ── TAB: Deep Dive ──
    with tab_detail:
        st.markdown('<div class="section-header">🔬 Deep Dive — Full Stock Analysis</div>',
                    unsafe_allow_html=True)
        if not watchlist:
            st.info("Add stocks to your watchlist in the sidebar.")
        else:
            sel_ticker = st.selectbox("Choose a stock to analyse in depth:", watchlist)
            sel_result = next((r for r in all_results if r["ticker"] == sel_ticker), None)
            if sel_result:
                render_stock_detail(
                    sel_result["ticker"], sel_result["df"], sel_result["info"],
                    sel_result["risk"], sel_result["opts"], fear_greed, vix,
                    sel_result["anomalies"]
                )
            elif st.session_state.paused:
                st.info("Scanning is paused. Resume scanning to see data.")

    # ── TAB: Market Scanner ──
    with tab_scanner:
        render_market_scanner_tab(fear_greed, vix, regime_data)

    # ── TAB: Market Health ──
    with tab_regime:
        render_market_regime_tab(regime_data)

    # ── TAB: Position Sizing ──
    with tab_size:
        render_position_sizing_tab()

    # ── TAB: Journal ──
    with tab_journal:
        render_journal_tab()

    # ── TAB: Glossary ──
    with tab_glossary:
        render_glossary()

    # ── Auto-refresh ──
    if not st.session_state.paused:
        if elapsed >= interval:
            st.session_state.last_refresh = time.time()
            time.sleep(0.5)
            st.rerun()
        else:
            time.sleep(8)
            st.rerun()


if __name__ == "__main__":
    main()
