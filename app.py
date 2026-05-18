"""
================================================================================
SMART STOCK ADVISOR  v2.0  —  app.py
================================================================================
Complete rebuild. Clean architecture. Seven purposeful screens.
Built for Ryan — a beginner investor who wants guided decisions
with the ability to deep-dive into expert detail.

Run:  streamlit run app.py
Deps: pip install streamlit yfinance pandas numpy plotly
      finnhub-python requests anthropic ta
================================================================================
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sqlite3, time, datetime, requests, warnings, json, re
warnings.filterwarnings("ignore")

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

try:
    import alpaca_trade_api as alpaca
    HAS_ALPACA = True
except ImportError:
    HAS_ALPACA = False

import os, pathlib

# ── Config file — persists API keys and settings across restarts ──
CONFIG_PATH = pathlib.Path.home() / "stock-dashboard" / "advisor_config.json"

def load_config() -> dict:
    """Load saved settings from config file. Returns defaults if file missing."""
    defaults = {
        "anthropic_key": "", "finnhub_key": "",
        "alpaca_key": "", "alpaca_secret": "",
        "account_size": 10000.0, "max_risk_pct": 1.0,
        "risk_weights": {"technical":40,"fundamental":30,"sentiment":20,"performance":10},
    }
    try:
        if CONFIG_PATH.exists():
            saved = json.loads(CONFIG_PATH.read_text())
            defaults.update(saved)
    except Exception:
        pass
    return defaults

def save_config(cfg: dict):
    """Save settings to config file so they survive restarts."""
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
    except Exception as e:
        st.error(f"Could not save config: {e}")


# ─────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Stock Advisor",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────────────
#  DESIGN SYSTEM
#  Refined dark finance aesthetic — Bloomberg meets modern fintech
#  Typography: Syne (display) + IBM Plex Mono (data) + DM Sans (body)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=IBM+Plex+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #070A10;
    color: #C8D0E0;
}
.main { background: #070A10; padding: 0 !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0D1220; }
::-webkit-scrollbar-thumb { background: #1E2D45; border-radius: 2px; }

/* ── Top Navigation Bar ── */
.nav-bar {
    background: #0A0E1A;
    border-bottom: 1px solid #141E30;
    padding: 0 24px;
    display: flex;
    align-items: center;
    height: 56px;
    position: sticky;
    top: 0;
    z-index: 999;
    gap: 4px;
}
.nav-logo {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 800;
    color: #00E676;
    margin-right: 32px;
    white-space: nowrap;
    letter-spacing: -0.02em;
}
.nav-tab {
    font-family: 'Syne', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    color: #4A5568;
    padding: 6px 14px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    border: none;
    background: none;
    text-decoration: none;
}
.nav-tab:hover { color: #A0AEC0; background: #141E30; }
.nav-tab.active {
    color: #00E676;
    background: rgba(0,230,118,0.08);
    border-bottom: 2px solid #00E676;
    border-radius: 6px 6px 0 0;
}

/* ── Page wrapper ── */
.page-content { padding: 24px 28px; max-width: 1400px; margin: 0 auto; }

/* ── Section titles ── */
.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: #EDF2F7;
    letter-spacing: -0.03em;
    margin: 0 0 4px 0;
}
.page-subtitle {
    font-size: 0.83rem;
    color: #4A5568;
    margin: 0 0 24px 0;
    font-weight: 400;
}
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    color: #4A5568;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin: 24px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #141E30;
}

/* ── Cards ── */
.card {
    background: #0D1220;
    border: 1px solid #141E30;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
    transition: border-color 0.15s;
}
.card:hover { border-color: #1E2D45; }
.card-sm { padding: 14px 16px; border-radius: 8px; }

/* ── Metric tile ── */
.metric-tile {
    background: #0D1220;
    border: 1px solid #141E30;
    border-radius: 10px;
    padding: 14px 16px;
    text-align: center;
}
.metric-tile .mt-label {
    font-size: 0.65rem;
    color: #4A5568;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 6px;
    font-weight: 600;
}
.metric-tile .mt-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.15rem;
    font-weight: 500;
    color: #EDF2F7;
    line-height: 1;
}
.metric-tile .mt-sub {
    font-size: 0.7rem;
    color: #4A5568;
    margin-top: 4px;
}
.metric-tile .mt-pos { color: #00E676; }
.metric-tile .mt-neg { color: #F56565; }
.metric-tile .mt-warn { color: #F6AD55; }

/* ── Traffic light cards ── */
.tl-green {
    background: linear-gradient(135deg,#071A0F,#0A2218);
    border: 1px solid rgba(0,230,118,0.25);
    border-left: 3px solid #00E676;
    border-radius: 12px; padding: 18px; margin-bottom: 12px;
}
.tl-yellow {
    background: linear-gradient(135deg,#1A1407,#221C08);
    border: 1px solid rgba(246,173,85,0.25);
    border-left: 3px solid #F6AD55;
    border-radius: 12px; padding: 18px; margin-bottom: 12px;
}
.tl-red {
    background: linear-gradient(135deg,#1A0707,#220D0D);
    border: 1px solid rgba(245,101,101,0.25);
    border-left: 3px solid #F56565;
    border-radius: 12px; padding: 18px; margin-bottom: 12px;
}

/* ── Score badge ── */
.score-big {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    line-height: 1;
}
.score-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

/* ── Pills / badges ── */
.pill {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 20px;
    font-size: 0.68rem;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 500;
    margin: 2px 2px 2px 0;
}
.pill-green  { background:rgba(0,230,118,0.1);  color:#69F0AE; border:1px solid rgba(0,230,118,0.2); }
.pill-red    { background:rgba(245,101,101,0.1); color:#FC8181; border:1px solid rgba(245,101,101,0.2); }
.pill-amber  { background:rgba(246,173,85,0.1);  color:#F6AD55; border:1px solid rgba(246,173,85,0.2); }
.pill-blue   { background:rgba(66,153,225,0.1);  color:#63B3ED; border:1px solid rgba(66,153,225,0.2); }
.pill-gray   { background:rgba(74,85,104,0.15);  color:#718096; border:1px solid rgba(74,85,104,0.2); }

/* ── Alert boxes ── */
.alert-critical {
    background:rgba(245,101,101,0.08); border:1px solid rgba(245,101,101,0.3);
    border-left:3px solid #F56565; border-radius:8px; padding:12px 14px; margin:6px 0;
}
.alert-warn {
    background:rgba(246,173,85,0.08); border:1px solid rgba(246,173,85,0.3);
    border-left:3px solid #F6AD55; border-radius:8px; padding:12px 14px; margin:6px 0;
}
.alert-info {
    background:rgba(66,153,225,0.08); border:1px solid rgba(66,153,225,0.3);
    border-left:3px solid #4299E1; border-radius:8px; padding:12px 14px; margin:6px 0;
}
.alert-good {
    background:rgba(0,230,118,0.06); border:1px solid rgba(0,230,118,0.2);
    border-left:3px solid #00E676; border-radius:8px; padding:12px 14px; margin:6px 0;
}

/* ── Regime badges ── */
.regime-bull { background:rgba(0,230,118,0.1); border:1px solid #00E676; color:#00E676;
    padding:5px 14px; border-radius:20px; font-family:'Syne',sans-serif;
    font-size:0.75rem; font-weight:700; letter-spacing:0.08em; display:inline-block; }
.regime-bear { background:rgba(245,101,101,0.1); border:1px solid #F56565; color:#F56565;
    padding:5px 14px; border-radius:20px; font-family:'Syne',sans-serif;
    font-size:0.75rem; font-weight:700; letter-spacing:0.08em; display:inline-block; }
.regime-mixed { background:rgba(246,173,85,0.1); border:1px solid #F6AD55; color:#F6AD55;
    padding:5px 14px; border-radius:20px; font-family:'Syne',sans-serif;
    font-size:0.75rem; font-weight:700; letter-spacing:0.08em; display:inline-block; }

/* ── Advice prose ── */
.advice-prose {
    font-size: 0.88rem;
    line-height: 1.75;
    color: #A0AEC0;
}
.advice-prose strong { color: #EDF2F7; }

/* ── Portfolio P&L colours ── */
.pnl-pos { color: #00E676; font-family:'IBM Plex Mono',monospace; font-weight:500; }
.pnl-neg { color: #F56565; font-family:'IBM Plex Mono',monospace; font-weight:500; }
.pnl-neu { color: #718096; font-family:'IBM Plex Mono',monospace; font-weight:500; }

/* ── Tooltips ── */
.tooltip-wrap { position:relative; display:inline-block; cursor:help; }
.tooltip-wrap .tt {
    visibility:hidden; opacity:0; background:#1A2535; color:#A0AEC0;
    font-size:0.72rem; border-radius:6px; padding:6px 10px;
    position:absolute; z-index:999; bottom:125%; left:50%;
    transform:translateX(-50%); white-space:nowrap;
    border:1px solid #1E2D45; transition:opacity 0.2s;
    font-family:'DM Sans',sans-serif; max-width:220px; white-space:normal;
}
.tooltip-wrap:hover .tt { visibility:visible; opacity:1; }

/* ── Streamlit overrides ── */
div[data-testid="stMetric"] {
    background:#0D1220; border:1px solid #141E30;
    border-radius:10px; padding:12px 16px;
}
div[data-testid="stMetricLabel"] p {
    font-size:0.65rem !important; color:#4A5568 !important;
    text-transform:uppercase; letter-spacing:0.1em;
}
div[data-testid="stMetricValue"] {
    font-family:'IBM Plex Mono',monospace !important;
    font-size:1.1rem !important; color:#EDF2F7 !important;
}
.stTabs [data-baseweb="tab-list"] {
    gap:4px; background:transparent;
    border-bottom:1px solid #141E30;
}
.stTabs [data-baseweb="tab"] {
    background:#0D1220; border:1px solid #141E30;
    border-radius:6px 6px 0 0; padding:7px 18px;
    font-family:'Syne',sans-serif; font-size:0.75rem;
    font-weight:600; color:#4A5568; letter-spacing:0.04em;
}
.stTabs [aria-selected="true"] {
    background:#141E30 !important; color:#EDF2F7 !important;
    border-bottom:2px solid #00E676 !important;
}
.stButton button {
    font-family:'Syne',sans-serif; font-size:0.78rem;
    font-weight:600; letter-spacing:0.04em;
    border-radius:8px; border:1px solid #1E2D45;
    background:#0D1220; color:#A0AEC0;
    transition:all 0.15s;
}
.stButton button:hover {
    background:#141E30; color:#EDF2F7;
    border-color:#2D3F5A;
}
.stButton button[kind="primary"] {
    background:rgba(0,230,118,0.1);
    border-color:rgba(0,230,118,0.3);
    color:#00E676;
}
.stButton button[kind="primary"]:hover {
    background:rgba(0,230,118,0.18);
}
[data-testid="stSidebar"] { background:#070A10 !important; border-right:1px solid #141E30; }
.stDataFrame { border:1px solid #141E30 !important; border-radius:10px !important; }
div[data-testid="stExpander"] {
    background:#0D1220; border:1px solid #141E30 !important;
    border-radius:10px !important;
}
hr { border-color:#141E30 !important; }
.stSelectbox > div > div {
    background:#0D1220; border:1px solid #141E30;
    border-radius:8px; color:#A0AEC0;
}
.stTextInput > div > div > input {
    background:#0D1220; border:1px solid #141E30;
    border-radius:8px; color:#EDF2F7;
    font-family:'DM Sans',sans-serif;
}
.stNumberInput > div > div > input {
    background:#0D1220; border:1px solid #141E30;
    border-radius:8px; color:#EDF2F7;
}
.stSlider > div > div { color:#A0AEC0; }
div[data-testid="stForm"] {
    background:#0D1220; border:1px solid #141E30;
    border-radius:12px; padding:20px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  DATABASE  —  Single SQLite file, all tables
# ─────────────────────────────────────────────────────────────
DB = "advisor_v2.db"

def migrate_old_watchlist():
    """
    One-time migration: copy watchlist from old database files
    into the new advisor_v2.db so tickers don't disappear.
    """
    import os
    old_dbs = ["advisor_journal.db", "trade_journal.db"]
    for old_db in old_dbs:
        if not os.path.exists(old_db):
            continue
        try:
            old_conn = sqlite3.connect(old_db)
            old_wl   = pd.read_sql(
                "SELECT ticker FROM watchlist", old_conn
            )
            old_conn.close()
            if old_wl.empty:
                continue
            new_conn = sqlite3.connect(DB)
            for tk in old_wl["ticker"].tolist():
                new_conn.execute(
                    "INSERT OR IGNORE INTO watchlist (ticker) VALUES (?)", (tk,)
                )
            new_conn.commit()
            new_conn.close()
        except Exception:
            pass

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Portfolio positions (stocks you actually own)
    c.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            shares REAL NOT NULL,
            entry_price REAL NOT NULL,
            entry_date TEXT NOT NULL,
            stop_loss REAL,
            target_price REAL,
            notes TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Watchlist (stocks you are watching but don't own)
    c.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            ticker TEXT PRIMARY KEY,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)

    # Trade journal (closed trades with full analysis)
    c.execute("""
        CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            direction TEXT DEFAULT 'LONG',
            entry_date TEXT, exit_date TEXT,
            entry_price REAL, exit_price REAL,
            shares REAL, pnl REAL, pnl_pct REAL,
            r_multiple REAL,
            stop_price REAL, target_price REAL,
            strategy TEXT, setup_tag TEXT,
            emotional_state TEXT,
            thesis TEXT,
            deviation TEXT,
            exit_reason TEXT,
            mistake_type TEXT,
            mfe REAL, mae REAL,
            rule_violation INTEGER DEFAULT 0,
            risk_score REAL,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Alerts log
    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT, alert_type TEXT,
            message TEXT, urgency TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

init_db()
migrate_old_watchlist()

# ─────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────
# Load saved config once per session
_cfg = load_config()

DEFAULTS = {
    "page":              "briefing",
    "paused":            False,
    "refresh_interval":  60,
    "last_refresh":      0,
    "account_size":      _cfg.get("account_size", 10000.0),
    "max_risk_pct":      _cfg.get("max_risk_pct", 1.0),
    "anthropic_key":     _cfg.get("anthropic_key", ""),
    "finnhub_key":       _cfg.get("finnhub_key", ""),
    "alpaca_key":        _cfg.get("alpaca_key", ""),
    "alpaca_secret":     _cfg.get("alpaca_secret", ""),
    "risk_weights":      _cfg.get("risk_weights", {"technical":40,"fundamental":30,"sentiment":20,"performance":10}),
    "scanner_results":   [],
    "scanner_last_run":  0,
    "all_results":       [],
    "portfolio_data":    [],
    "last_full_load":    0,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────

def db():
    return sqlite3.connect(DB)

def pill(text, kind="gray"):
    return f'<span class="pill pill-{kind}">{text}</span>'

def tile(label, value, sub="", color=None):
    val_cls = f'style="color:{color}"' if color else ''
    return (f'<div class="metric-tile">'
            f'<div class="mt-label">{label}</div>'
            f'<div class="mt-value" {val_cls}>{value}</div>'
            f'{"<div class=mt-sub>"+sub+"</div>" if sub else ""}'
            f'</div>')

def fmt_pnl(val, pct=None):
    if val is None: return '<span class="pnl-neu">—</span>'
    sign = "+" if val >= 0 else ""
    cls  = "pnl-pos" if val >= 0 else "pnl-neg"
    pct_str = f' ({sign}{pct:.1f}%)' if pct is not None else ""
    return f'<span class="{cls}">{sign}${val:,.2f}{pct_str}</span>'

CHART_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="#070A10",
    plot_bgcolor="#0D1220",
    font=dict(family="IBM Plex Mono", color="#4A5568", size=10),
    margin=dict(l=48, r=16, t=36, b=32),
    xaxis=dict(gridcolor="#141E30", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#141E30", showgrid=True, zeroline=False),
)

# ─────────────────────────────────────────────────────────────
#  DATA LAYER
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=55)
def get_prices(ticker, period="6mo", interval="1d"):
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
        return df.dropna() if not df.empty else None
    except Exception:
        return None

@st.cache_data(ttl=300)
def get_info(ticker):
    try:
        info = yf.Ticker(ticker).info
        return {
            "name":         info.get("longName", ticker),
            "sector":       info.get("sector", "Unknown"),
            "industry":     info.get("industry", "Unknown"),
            "pe":           info.get("trailingPE"),
            "fwd_pe":       info.get("forwardPE"),
            "pb":           info.get("priceToBook"),
            "eps_growth":   info.get("earningsGrowth"),
            "rev_growth":   info.get("revenueGrowth"),
            "debt_equity":  info.get("debtToEquity"),
            "roe":          info.get("returnOnEquity"),
            "fcf":          info.get("freeCashflow"),
            "market_cap":   info.get("marketCap"),
            "short_pct":    info.get("shortPercentOfFloat"),
            "inst_pct":     info.get("heldPercentInstitutions"),
            "price":        info.get("currentPrice") or info.get("regularMarketPrice"),
            "52w_high":     info.get("fiftyTwoWeekHigh"),
            "52w_low":      info.get("fiftyTwoWeekLow"),
            "avg_vol":      info.get("averageVolume"),
            "beta":         info.get("beta"),
            "target":       info.get("targetMeanPrice"),
            "target_low":   info.get("targetLowPrice"),
            "target_high":  info.get("targetHighPrice"),
            "n_analysts":   info.get("numberOfAnalystOpinions"),
            "div_yield":    info.get("dividendYield"),
            "earnings_ts":  info.get("earningsTimestamp"),
        }
    except Exception:
        return {}

@st.cache_data(ttl=1800)
def get_vix():
    try:
        h = yf.Ticker("^VIX").history(period="5d")
        return round(float(h["Close"].iloc[-1]), 2) if not h.empty else None
    except Exception:
        return None

@st.cache_data(ttl=1800)
def get_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
        d = r.json()["data"][0]
        return {"value": int(d["value"]), "label": d["value_classification"]}
    except Exception:
        return {"value": 50, "label": "Neutral"}

@st.cache_data(ttl=3600)
def get_options(ticker):
    try:
        tk = yf.Ticker(ticker)
        exps = tk.options
        if not exps: return {}
        chain = tk.option_chain(exps[0])
        calls = chain.calls["volume"].sum()
        puts  = chain.puts["volume"].sum()
        return {"put_call": round(puts/calls, 3) if calls > 0 else None}
    except Exception:
        return {}

@st.cache_data(ttl=900)
def get_market_regime():
    try:
        results = {}
        for sym, name in [("SPY","Large Caps"),("QQQ","Tech / Growth"),("IWM","Small Caps")]:
            df = get_prices(sym, period="1y")
            if df is not None and len(df) >= 200:
                c = df["Close"]
                price = float(c.iloc[-1])
                e20   = float(c.ewm(span=20,  adjust=False).mean().iloc[-1])
                e50   = float(c.ewm(span=50,  adjust=False).mean().iloc[-1])
                e200  = float(c.ewm(span=200, adjust=False).mean().iloc[-1])
                mo1m  = float((price/c.iloc[-21]-1)*100) if len(c)>=21 else 0
                mo3m  = float((price/c.iloc[-63]-1)*100) if len(c)>=63 else 0
                results[sym] = {
                    "name": name, "price": price,
                    "above_20":  bool(price > e20),
                    "above_50":  bool(price > e50),
                    "above_200": bool(price > e200),
                    "mo1m": round(mo1m,1), "mo3m": round(mo3m,1),
                }

        sectors = {
            "XLK":"Technology","XLF":"Financials","XLE":"Energy",
            "XLV":"Healthcare","XLI":"Industrials","XLC":"Comms",
            "XLY":"Consumer Cycl","XLP":"Consumer Def",
            "XLB":"Materials","XLRE":"Real Estate","XLU":"Utilities"
        }
        sector_perf = {}
        for sym, name in sectors.items():
            df = get_prices(sym, period="3mo")
            if df is not None and len(df) >= 21:
                sector_perf[name] = round(
                    float((df["Close"].iloc[-1]/df["Close"].iloc[-21]-1)*100), 2
                )

        spy = results.get("SPY", {})
        if spy.get("above_200") and spy.get("above_50"):
            regime, cls, advice = "BULL MARKET", "regime-bull", (
                "The market is in an uptrend. Good conditions for new positions. "
                "Focus on strong momentum and quality stocks."
            )
        elif not spy.get("above_200"):
            regime, cls, advice = "BEAR MARKET", "regime-bear", (
                "The market is below its long-term average. Be defensive. "
                "Hold more cash and only take the clearest setups."
            )
        else:
            regime, cls, advice = "MIXED MARKET", "regime-mixed", (
                "Mixed signals. Be selective — only take high-conviction setups "
                "and reduce position sizes by 30-50%."
            )

        return {
            "indices": results, "sectors": sector_perf,
            "regime": regime, "regime_cls": cls, "advice": advice,
        }
    except Exception:
        return {"regime":"UNKNOWN","regime_cls":"regime-mixed","advice":"Could not load.","indices":{},"sectors":{}}

@st.cache_data(ttl=3600)
def get_gate_checks():
    checks = {}
    try:
        spy = get_prices("SPY", period="1y")
        if spy is not None and len(spy) >= 200:
            price = float(spy["Close"].iloc[-1])
            e200  = float(spy["Close"].ewm(span=200, adjust=False).mean().iloc[-1])
            above = bool(price > e200)
            checks["trend"] = {
                "name": "Market Trend",
                "pass": above,
                "value": f"SPY ${price:.0f} {'above' if above else 'below'} 200-day avg ${e200:.0f}",
                "meaning": "S&P 500 is in an uptrend" if above else "S&P 500 is below its long-term average",
            }
    except Exception:
        checks["trend"] = {"name":"Market Trend","pass":None,"value":"N/A","meaning":""}

    try:
        tlt = get_prices("TLT", period="1mo")
        shy = get_prices("SHY", period="1mo")
        if tlt is not None and shy is not None:
            tr = float((tlt["Close"].iloc[-1]/tlt["Close"].iloc[0]-1)*100)
            sr = float((shy["Close"].iloc[-1]/shy["Close"].iloc[0]-1)*100)
            h  = bool(tr >= sr - 0.5)
            checks["yield"] = {
                "name": "Yield Curve",
                "pass": h,
                "value": f"Long bonds {tr:+.1f}% vs short bonds {sr:+.1f}%",
                "meaning": "Rate structure is normal" if h else "Yield curve stress detected",
            }
    except Exception:
        checks["yield"] = {"name":"Yield Curve","pass":None,"value":"N/A","meaning":""}

    try:
        hyg = get_prices("HYG", period="1mo")
        lqd = get_prices("LQD", period="1mo")
        if hyg is not None and lqd is not None:
            hr = float((hyg["Close"].iloc[-1]/hyg["Close"].iloc[0]-1)*100)
            lr = float((lqd["Close"].iloc[-1]/lqd["Close"].iloc[0]-1)*100)
            h  = bool(hr >= lr - 0.3)
            checks["credit"] = {
                "name": "Credit Health",
                "pass": h,
                "value": f"High yield {hr:+.1f}% vs investment grade {lr:+.1f}%",
                "meaning": "Credit markets calm" if h else "Credit stress building — be cautious",
            }
    except Exception:
        checks["credit"] = {"name":"Credit Health","pass":None,"value":"N/A","meaning":""}

    try:
        vix = get_vix()
        h   = bool(vix is not None and vix < 25)
        checks["vix"] = {
            "name": "Market Fear (VIX)",
            "pass": h,
            "value": f"VIX = {vix:.1f}" if vix else "N/A",
            "meaning": "Markets are calm" if h else "Elevated fear — reduce position sizes",
        }
    except Exception:
        checks["vix"] = {"name":"Market Fear","pass":None,"value":"N/A","meaning":""}

    try:
        spy = get_prices("SPY", period="3mo")
        if spy is not None and len(spy) >= 40:
            rh = float(spy["Close"].tail(20).max())
            ph = float(spy["Close"].iloc[-40:-20].max())
            h  = bool(rh > ph)
            checks["breadth"] = {
                "name": "Market Momentum",
                "pass": h,
                "value": f"Recent high ${rh:.0f} vs prior ${ph:.0f} ({(rh/ph-1)*100:+.1f}%)",
                "meaning": "Market making higher highs — momentum intact" if h else "Market not making new highs",
            }
    except Exception:
        checks["breadth"] = {"name":"Market Momentum","pass":None,"value":"N/A","meaning":""}

    passed = sum(1 for c in checks.values() if c.get("pass") == True)
    if passed >= 4:
        label, color = "MARKETS LOOK FAVOURABLE", "#00E676"
        advice = f"{passed}/5 checks positive. Good conditions for new positions."
    elif passed >= 3:
        label, color = "PROCEED WITH CAUTION", "#F6AD55"
        advice = f"{passed}/5 checks positive. Reduce position sizes by 30-50%."
    else:
        label, color = "DEFENSIVE MODE", "#F56565"
        advice = f"Only {passed}/5 checks positive. Hold more cash, only clearest setups."

    return {"checks":checks,"passed":passed,"label":label,"color":color,"advice":advice}

@st.cache_data(ttl=3600)
def get_analyst(ticker):
    try:
        info = yf.Ticker(ticker).info
        recs = yf.Ticker(ticker).recommendations
        price  = info.get("currentPrice") or info.get("regularMarketPrice")
        target = info.get("targetMeanPrice")
        upside = ((target/price)-1)*100 if target and price else None
        sb=b=h=s=ss=0
        if recs is not None and not recs.empty:
            r = recs.tail(10)
            for col,var in [("strongBuy","sb"),("strong_buy","sb"),("buy","b"),
                             ("hold","h"),("sell","s"),("strongSell","ss"),("strong_sell","ss")]:
                if col in r.columns:
                    if var=="sb":   sb += int(r[col].sum())
                    elif var=="b":  b  += int(r[col].sum())
                    elif var=="h":  h  += int(r[col].sum())
                    elif var=="s":  s  += int(r[col].sum())
                    elif var=="ss": ss += int(r[col].sum())
        return {
            "target":target,"target_low":info.get("targetLowPrice"),
            "target_high":info.get("targetHighPrice"),
            "upside":round(upside,1) if upside else None,
            "n_analysts":info.get("numberOfAnalystOpinions",0),
            "strong_buy":sb,"buy":b,"hold":h,"sell":s,"strong_sell":ss,
        }
    except Exception:
        return {}

@st.cache_data(ttl=3600)
def get_insider(ticker):
    try:
        ins = yf.Ticker(ticker).insider_transactions
        if ins is None or ins.empty:
            return {"transactions":[],"net_shares":0,"summary":"No recent insider data."}
        ins = ins.copy()
        ins.columns = [c.lower().replace(" ","_") for c in ins.columns]
        txns, net = [], 0
        for _, row in ins.head(8).iterrows():
            try:
                shares = int(row.get("shares",0) or 0)
                val    = float(row.get("value",0) or 0)
                ttype  = str(row.get("transaction",row.get("startdate","Unknown")))
                insider = str(row.get("insider",row.get("filer_name","Unknown")))
                date   = str(row.get("startdate",row.get("date","")))[:10]
                is_buy  = any(w in ttype.lower() for w in ["buy","purchase","acquired"])
                is_sell = any(w in ttype.lower() for w in ["sell","sale","disposed"])
                txns.append({"insider":insider[:28],"type":"BUY" if is_buy else ("SELL" if is_sell else ttype[:15]),
                             "shares":shares,"value":val,"date":date,"is_buy":is_buy})
                if is_buy:  net += shares
                if is_sell: net -= shares
            except Exception:
                continue
        summary = (f"Net buying of {net:,} shares" if net > 0
                   else f"Net selling of {abs(net):,} shares" if net < 0
                   else "Balanced insider activity")
        return {"transactions":txns,"net_shares":net,"summary":summary}
    except Exception:
        return {"transactions":[],"net_shares":0,"summary":"Could not load."}

@st.cache_data(ttl=1800)
def get_news(ticker):
    key = st.session_state.finnhub_key
    headlines = []
    if key and HAS_FINNHUB:
        try:
            client = finnhub.Client(api_key=key)
            today = datetime.date.today()
            ago   = today - datetime.timedelta(days=7)
            news  = client.company_news(ticker,
                        _from=ago.strftime("%Y-%m-%d"), to=today.strftime("%Y-%m-%d"))
            headlines = [{"title":a.get("headline",""),"url":a.get("url",""),
                          "source":a.get("source","")} for a in news[:8]]
        except Exception:
            pass
    if not headlines:
        try:
            news = yf.Ticker(ticker).news or []
            for a in news[:8]:
                content = a.get("content", a) if isinstance(a, dict) else {}
                title = content.get("title","") or a.get("title","")
                headlines.append({"title":title,"url":"","source":""})
        except Exception:
            pass
    # Simple sentiment
    pos_words = ["surge","soar","beat","record","growth","upgrade","strong","gain","bullish","exceed","boost","rally"]
    neg_words = ["fall","drop","miss","loss","decline","downgrade","weak","concern","bearish","plunge","layoff","warning"]
    bull = bear = 0
    for h in headlines:
        t = h["title"].lower()
        bull += sum(1 for w in pos_words if w in t)
        bear += sum(1 for w in neg_words if w in t)
    total = bull + bear
    score = int((bull/total)*100) if total > 0 else 50
    sent  = "bullish" if score >= 65 else ("bearish" if score <= 35 else "neutral")
    return {"headlines":headlines,"sentiment":sent,"score":score,"bull":bull,"bear":bear}

@st.cache_data(ttl=3600)
def get_earnings_date(ticker):
    try:
        ts = yf.Ticker(ticker).info.get("earningsTimestamp")
        if ts:
            dt = datetime.datetime.fromtimestamp(ts)
            return {"date":dt.strftime("%Y-%m-%d"),
                    "days": (dt-datetime.datetime.now()).days}
    except Exception:
        pass
    return {"date":None,"days":None}

# ─────────────────────────────────────────────────────────────
#  TECHNICAL INDICATORS
# ─────────────────────────────────────────────────────────────

def calc_indicators(df):
    if df is None or len(df) < 26: return df
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    for span, col in [(9,"EMA9"),(20,"EMA20"),(50,"EMA50"),(200,"EMA200")]:
        df[col] = c.ewm(span=span, adjust=False).mean()
    delta = c.diff()
    gain  = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
    loss  = (-delta).clip(lower=0).ewm(com=13, adjust=False).mean()
    df["RSI"] = 100 - (100/(1+gain/loss.replace(0, np.nan)))
    e12 = c.ewm(span=12, adjust=False).mean()
    e26 = c.ewm(span=26, adjust=False).mean()
    df["MACD"]        = e12 - e26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"]   = df["MACD"] - df["MACD_Signal"]
    tp = (h+l+c)/3
    df["VWAP"] = (tp*v).cumsum()/v.replace(0,np.nan).cumsum()
    obv = [0]
    for i in range(1, len(c)):
        if c.iloc[i] > c.iloc[i-1]:   obv.append(obv[-1]+v.iloc[i])
        elif c.iloc[i] < c.iloc[i-1]: obv.append(obv[-1]-v.iloc[i])
        else:                          obv.append(obv[-1])
    df["OBV"] = obv
    sma20 = c.rolling(20).mean()
    std20 = c.rolling(20).std()
    df["BB_U"] = sma20 + 2*std20
    df["BB_L"] = sma20 - 2*std20
    df["BB_M"] = sma20
    tr = pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    df["ATR14"]    = tr.rolling(14).mean()
    df["AvgVol20"] = v.rolling(20).mean()
    df["VolRatio"] = v/df["AvgVol20"].replace(0, np.nan)
    spy_df = get_prices("SPY", period="6mo")
    if spy_df is not None and len(spy_df) >= 2:
        spy_c = spy_df["Close"].reindex(df.index, method="nearest")
        df["RS"] = (c/c.iloc[0]) / (spy_c/spy_c.iloc[0]) * 100
    else:
        df["RS"] = 100.0
    return df


# ─────────────────────────────────────────────────────────────
#  FRED — Federal Reserve Economic Data (free macro indicators)
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_fred_macro() -> dict:
    """
    Pull key macro indicators from the Federal Reserve (FRED).
    Completely free — no API key needed for these public endpoints.
    Covers: Fed Funds Rate, CPI inflation, 10yr yield, unemployment.
    """
    BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
    results = {}

    indicators = {
        "fed_rate":     ("FEDFUNDS",    "Fed Funds Rate",     "%"),
        "inflation":    ("CPIAUCSL",    "CPI Inflation",      "%"),
        "yield_10yr":   ("DGS10",       "10-Year Treasury",   "%"),
        "yield_2yr":    ("DGS2",        "2-Year Treasury",    "%"),
        "unemployment": ("UNRATE",      "Unemployment Rate",  "%"),
        "sp500_pe":     ("MULTPL/SP500_PE_RATIO_MONTH", "S&P 500 P/E Ratio", "x"),
    }

    for key, (series_id, label, unit) in indicators.items():
        try:
            url = f"{BASE}{series_id}"
            df  = pd.read_csv(url, parse_dates=["DATE"])
            df  = df.dropna()
            if df.empty:
                continue
            latest = float(df.iloc[-1, 1])
            prev   = float(df.iloc[-2, 1]) if len(df) >= 2 else latest
            change = latest - prev
            results[key] = {
                "label":  label,
                "value":  round(latest, 2),
                "change": round(change, 2),
                "unit":   unit,
            }
        except Exception:
            pass

    # Yield curve spread (10yr - 2yr) — negative = inverted = recession warning
    if "yield_10yr" in results and "yield_2yr" in results:
        spread = results["yield_10yr"]["value"] - results["yield_2yr"]["value"]
        results["yield_spread"] = {
            "label":  "Yield Curve (10yr - 2yr)",
            "value":  round(spread, 2),
            "change": 0,
            "unit":   "%",
        }

    # Plain English interpretation
    interpretations = []
    if "fed_rate" in results:
        r = results["fed_rate"]["value"]
        if r >= 5.0:
            interpretations.append(f"Fed rate at {r}% — high rates make borrowing expensive and weigh on growth stocks.")
        elif r >= 3.0:
            interpretations.append(f"Fed rate at {r}% — moderate rates, neutral impact on markets.")
        else:
            interpretations.append(f"Fed rate at {r}% — low rates support growth and risk assets.")

    if "inflation" in results:
        # CPI is a level, calculate rough YoY from series
        interpretations.append("Inflation data loaded — high inflation typically leads to higher rates which pressure valuations.")

    if "yield_spread" in results:
        s = results["yield_spread"]["value"]
        if s < 0:
            interpretations.append(f"⚠️ Yield curve is INVERTED ({s:+.2f}%) — historically a recession warning signal. Be defensive.")
        elif s < 0.5:
            interpretations.append(f"Yield curve is flat ({s:+.2f}%) — caution warranted, economy may be slowing.")
        else:
            interpretations.append(f"Yield curve is normal ({s:+.2f}%) — positive signal for economic growth.")

    results["interpretation"] = interpretations
    return results


# ─────────────────────────────────────────────────────────────
#  ALPACA — Portfolio sync (read-only, analysis only)
# ─────────────────────────────────────────────────────────────

def get_alpaca_portfolio() -> list:
    """
    Fetch current positions from Alpaca account.
    Read-only — used for portfolio sync only, not for placing trades.
    Returns list of positions in the same format as get_portfolio_positions().
    """
    key    = st.session_state.get("alpaca_key", "")
    secret = st.session_state.get("alpaca_secret", "")
    if not key or not secret:
        return []
    if not HAS_ALPACA:
        return []
    try:
        api = alpaca.REST(key, secret, base_url="https://paper-api.alpaca.markets")
        positions = api.list_positions()
        results = []
        for p in positions:
            results.append({
                "ticker":        p.symbol,
                "shares":        float(p.qty),
                "entry_price":   float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "market_value":  float(p.market_value),
                "pnl":           float(p.unrealized_pl),
                "pnl_pct":       float(p.unrealized_plpc) * 100,
                "source":        "alpaca",
            })
        return results
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────
#  ETORO CSV IMPORTER
# ─────────────────────────────────────────────────────────────

def parse_etoro_csv(uploaded_file) -> list:
    """
    Parse an eToro portfolio export CSV and return a list of positions.
    eToro export columns vary — this handles the most common formats.

    How to export from eToro:
    1. Open eToro app or website
    2. Go to Portfolio
    3. Tap the three dots (⋯) menu top right
    4. Select 'Export' or 'Download statement'
    5. Choose 'Positions' and download as CSV
    """
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]

        positions = []
        # Map common eToro column names
        ticker_cols  = ["ticker","symbol","instrument","asset","stock"]
        shares_cols  = ["units","shares","quantity","amount","qty"]
        price_cols   = ["open_rate","avg_open","entry_price","open_price","avg_price"]
        date_cols    = ["open_date","entry_date","date","opened"]

        def find_col(df, candidates):
            for c in candidates:
                if c in df.columns: return c
            return None

        tc = find_col(df, ticker_cols)
        sc = find_col(df, shares_cols)
        pc = find_col(df, price_cols)
        dc = find_col(df, date_cols)

        if not tc:
            return []

        for _, row in df.iterrows():
            try:
                ticker = str(row[tc]).upper().strip()
                # Skip non-stock rows
                if not ticker or ticker in ["NAN","TOTAL","","BALANCE"]:
                    continue
                # Clean ticker — remove eToro suffixes like /USD
                ticker = ticker.split("/")[0].split(".")[0]

                shares = float(row[sc]) if sc and pd.notna(row[sc]) else 1.0
                price  = float(row[pc]) if pc and pd.notna(row[pc]) else 0.0
                date   = str(row[dc])[:10] if dc and pd.notna(row[dc]) else str(datetime.date.today())

                if price > 0 and shares > 0:
                    positions.append({
                        "ticker":      ticker,
                        "shares":      shares,
                        "entry_price": price,
                        "entry_date":  date,
                        "source":      "etoro_import",
                    })
            except Exception:
                continue

        return positions
    except Exception as e:
        st.error(f"Could not parse eToro CSV: {e}")
        return []

# ─────────────────────────────────────────────────────────────
#  SCORING ENGINE
# ─────────────────────────────────────────────────────────────

def _tech_score(df, info):
    if df is None or df.empty: return 0, {}
    bd, score = {}, 0
    last  = df.iloc[-1]
    price = float(last["Close"])
    # Trend (25 pts)
    ts = 0
    if "EMA9"   in df.columns and price > float(last["EMA9"]):   ts += 4
    if "EMA20"  in df.columns and price > float(last["EMA20"]):  ts += 5
    if "EMA50"  in df.columns and price > float(last["EMA50"]):  ts += 7
    if "EMA200" in df.columns and price > float(last["EMA200"]): ts += 9
    bd["Trend direction"] = ts; score += ts
    # RSI (20 pts)
    rs = 0
    if "RSI" in df.columns:
        rsi = float(last["RSI"])
        if 45<=rsi<=60:   rs = 20
        elif 40<=rsi<=65: rs = 13
        elif 35<=rsi<=70: rs = 7
        bd[f"Momentum — RSI = {rsi:.0f}"] = rs
    score += rs
    # MACD (20 pts)
    ms = 0
    if "MACD" in df.columns:
        m = float(last["MACD"]); s = float(last["MACD_Signal"])
        hist = float(last.get("MACD_Hist", 0))
        if m > s and hist > 0: ms = 20
        elif m > s:            ms = 12
        elif m > 0:            ms = 6
        bd["Momentum direction — MACD"] = ms
    score += ms
    # Volume (20 pts)
    vs = 0
    if "VolRatio" in df.columns:
        vr = float(last["VolRatio"])
        if 1.3<=vr<=3.0: vs = 20
        elif vr >= 1.0:  vs = 13
        else:            vs = 5
        bd[f"Volume = {vr:.1f}× average"] = vs
    score += vs
    # Relative strength (15 pts)
    rss = 0
    if "RS" in df.columns:
        rs_vals = df["RS"].dropna()
        if len(rs_vals) >= 20:
            rn = float(rs_vals.iloc[-1]); r20 = float(rs_vals.iloc[-20])
            if rn > r20 and rn > 100:   rss = 15
            elif rn > 100:              rss = 9
            elif rn > r20:              rss = 5
        bd["Strength vs market"] = rss
    score += rss
    return min(int(score), 100), bd

def _fund_score(info):
    if not info: return 0, {}
    bd, score = {}, 0
    sector = info.get("sector","")
    hi_pe  = ["Technology","Consumer Cyclical","Healthcare","Communication Services"]
    pe_lim = 35 if sector in hi_pe else 20
    pe = info.get("pe"); pe_s = 0
    if pe and pe > 0:
        if pe < pe_lim*0.6:   pe_s = 20
        elif pe < pe_lim:     pe_s = 13
        elif pe < pe_lim*1.5: pe_s = 6
        else:                 pe_s = 2
    bd[f"Valuation — P/E = {pe:.1f} (limit {pe_lim})" if pe else "Valuation — P/E N/A"] = pe_s
    score += pe_s
    gr = info.get("eps_growth") or info.get("rev_growth"); gs = 0
    if gr:
        if gr > 0.25:   gs = 25
        elif gr > 0.10: gs = 17
        elif gr > 0:    gs = 9
    bd[f"Profit growth = {gr*100:.1f}%" if gr else "Profit growth N/A"] = gs
    score += gs
    de = info.get("debt_equity"); ds = 0
    hi_d = ["Utilities","Real Estate","Financials"]
    de_lim = 200 if sector in hi_d else 80
    if de is not None:
        if de < de_lim*0.4:  ds = 20
        elif de < de_lim:    ds = 12
        elif de < de_lim*2:  ds = 5
    bd[f"Debt — D/E = {de:.0f}" if de else "Debt N/A"] = ds
    score += ds
    roe = info.get("roe"); rs = 0
    if roe:
        if roe > 0.25:   rs = 20
        elif roe > 0.15: rs = 13
        elif roe > 0.05: rs = 6
    bd[f"Profitability — ROE = {roe*100:.1f}%" if roe else "ROE N/A"] = rs
    score += rs
    fcf = info.get("fcf"); fs = 15 if fcf and fcf > 0 else 0
    bd[f"Cash flow — {'positive ✓' if fcf and fcf>0 else 'negative ✗'}"] = fs
    score += fs
    return min(int(score), 100), bd

def _sent_score(info, opts, fg, vix):
    bd, score = {}, 0
    fgv = fg.get("value", 50)
    fgs = 28 if fgv>=60 else (18 if fgv>=40 else (10 if fgv>=25 else 4))
    bd[f"Market mood — Fear & Greed = {fgv}"] = fgs; score += fgs
    vs = 0
    if vix:
        if vix < 15:   vs = 28
        elif vix < 20: vs = 20
        elif vix < 25: vs = 12
        elif vix < 30: vs = 6
    bd[f"Market fear — VIX = {vix}"] = vs; score += vs
    pc = opts.get("put_call"); pcs = 0
    if pc:
        if pc < 0.6:   pcs = 24
        elif pc < 0.8: pcs = 18
        elif pc < 1.0: pcs = 12
        elif pc < 1.2: pcs = 5
        bd[f"Options bets — Put/Call = {pc:.2f}"] = pcs
    score += pcs
    sp = info.get("short_pct") or 0; sis = 0
    if sp < 0.03:   sis = 20
    elif sp < 0.08: sis = 13
    elif sp < 0.15: sis = 6
    bd[f"Short sellers = {sp*100:.1f}%"] = sis; score += sis
    return min(int(score), 100), bd

def _perf_score(ticker):
    try:
        conn = db()
        trades = pd.read_sql(
            "SELECT * FROM journal WHERE ticker=? AND pnl IS NOT NULL", conn, params=(ticker,)
        )
        conn.close()
        if trades.empty: return 50, {"No history yet — neutral score": 50}
        wr = (trades["pnl"] > 0).mean()
        aw = trades[trades["pnl"]>0]["pnl_pct"].mean() or 0
        al = trades[trades["pnl"]<0]["pnl_pct"].mean() or 0
        exp = wr*aw + (1-wr)*al
        n   = len(trades)
        pts = (90 if wr>0.65 and exp>0.02 else
               70 if wr>0.5 and exp>0 else
               55 if exp>0 else
               15 if exp<-0.03 else 40)
        return pts, {f"Win rate {wr*100:.0f}% over {n} trades": pts}
    except Exception:
        return 50, {"Error": 50}

def score_stock(ticker, df, info, opts, fg, vix):
    W = st.session_state.risk_weights
    t, tbd = _tech_score(df, info)
    f, fbd = _fund_score(info)
    s, sbd = _sent_score(info, opts, fg, vix)
    p, pbd = _perf_score(ticker)
    final  = t*W["technical"]/100 + f*W["fundamental"]/100 + s*W["sentiment"]/100 + p*W["performance"]/100
    final  = round(final, 1)
    if final >= 80:
        label, color, css, emoji = "LOW RISK",    "#00E676", "tl-green",  "🟢"
    elif final >= 50:
        label, color, css, emoji = "MEDIUM RISK", "#F6AD55", "tl-yellow", "🟡"
    else:
        label, color, css, emoji = "HIGH RISK",   "#F56565", "tl-red",    "🔴"
    return {
        "score":final,"label":label,"color":color,"css":css,"emoji":emoji,
        "t":t,"f":f,"s":s,"p":p,
        "breakdowns":{"Chart Signals":tbd,"Company Health":fbd,
                      "Market Mood":sbd,"Your Track Record":pbd}
    }

# ─────────────────────────────────────────────────────────────
#  SELL SIGNAL DETECTOR
# ─────────────────────────────────────────────────────────────

def detect_sell_signals(ticker, df, info, analyst, insider):
    alerts = []
    if df is None or df.empty: return alerts
    last  = df.iloc[-1]; prev = df.iloc[-2] if len(df) > 1 else last
    price = float(last["Close"])
    if "EMA50" in df.columns:
        e50n = float(last["EMA50"]); e50p = float(prev["EMA50"])
        if float(prev["Close"]) > e50p and price < e50n:
            alerts.append({"type":"📉 Trend broken","urgency":"HIGH","pillar":"Technical",
                "msg":"Price just crossed below its 50-day average — medium-term uptrend may be ending."})
    if "EMA200" in df.columns:
        e200 = float(last["EMA200"])
        if float(prev["Close"]) > float(prev["EMA200"]) and price < e200:
            alerts.append({"type":"🚨 Major trend broken","urgency":"CRITICAL","pillar":"Technical",
                "msg":f"Price crossed below the 200-day average (${e200:.2f}). This is serious."})
    if "RSI" in df.columns and len(df) >= 5:
        rn = float(last["RSI"]); r5 = float(df["RSI"].iloc[-5])
        if r5 > 68 and rn < 55:
            alerts.append({"type":"📉 Momentum fading","urgency":"MEDIUM","pillar":"Technical",
                "msg":f"RSI dropped from {r5:.0f} to {rn:.0f} in 5 days — buying momentum fading."})
    if "MACD" in df.columns and len(df) >= 2:
        cd = float(df["MACD"].iloc[-1]) - float(df["MACD_Signal"].iloc[-1])
        pd_ = float(df["MACD"].iloc[-2]) - float(df["MACD_Signal"].iloc[-2])
        if pd_ > 0 and cd < 0:
            alerts.append({"type":"⚡ Momentum turning down","urgency":"MEDIUM","pillar":"Technical",
                "msg":"MACD just crossed below its signal line — momentum turning negative."})
    if "VolRatio" in df.columns:
        vr = float(last["VolRatio"]); chg = (price/float(prev["Close"])-1)*100
        if vr > 2.5 and chg < -2.0:
            alerts.append({"type":"🔊 Heavy selling","urgency":"HIGH","pillar":"Technical",
                "msg":f"Price fell {abs(chg):.1f}% on {vr:.1f}× normal volume — institutional selling likely."})
    if analyst.get("upside") is not None and analyst["upside"] < -10:
        alerts.append({"type":"🏦 Analysts think it's overvalued","urgency":"MEDIUM","pillar":"Thesis",
            "msg":f"Average analyst target is {analyst['upside']:.1f}% below current price."})
    if insider.get("net_shares", 0) < -50000:
        alerts.append({"type":"🏛 Heavy insider selling","urgency":"MEDIUM","pillar":"Thesis",
            "msg":f"Insiders net sold {abs(insider['net_shares']):,} shares recently."})
    if (info.get("short_pct") or 0) > 0.15:
        sp = info["short_pct"]*100
        alerts.append({"type":"🐻 High short interest","urgency":"MEDIUM","pillar":"Thesis",
            "msg":f"{sp:.1f}% of shares are shorted — many professionals betting it falls."})
    return sorted(alerts, key=lambda x: {"CRITICAL":0,"HIGH":1,"MEDIUM":2}.get(x["urgency"],3))

# ─────────────────────────────────────────────────────────────
#  AI ANALYSIS
# ─────────────────────────────────────────────────────────────

def run_ai_analysis(ticker, info, risk, analyst, insider, news, regime, context="stock"):
    key = st.session_state.anthropic_key
    if not key:
        return "Add your Anthropic API key in ⚙️ Settings to enable AI analysis."
    if not HAS_ANTHROPIC:
        return "Run: pip install anthropic — then restart the app."
    try:
        client = anthropic.Anthropic(api_key=key)
        name   = info.get("name", ticker)
        price  = info.get("price","N/A")
        target = analyst.get("target")
        upside = analyst.get("upside")
        headlines = [h["title"] for h in news.get("headlines",[])[:5] if h.get("title")]

        if context == "briefing":
            prompt = f"""You are a plain-English stock advisor giving a morning briefing for a beginner investor.
Analyse {name} ({ticker}) with:
- Price: ${price} | Risk score: {risk['score']}/100 ({risk['label']})
- Chart signals: {risk['t']}/100 | Finances: {risk['f']}/100 | Market mood: {risk['s']}/100
- Market regime: {regime.get('regime','Unknown')}
- Analyst target: ${target} ({upside:+.1f}% upside)" if target and upside else "No analyst target"
- Insider activity: {insider.get('summary','N/A')}
- News sentiment: {news.get('sentiment','neutral')} | Headlines: {'; '.join(headlines[:3]) if headlines else 'None'}

Write 2-3 sentences maximum. Be direct. Start with the most important thing to know today about this position.
No jargon. If there are sell signals, say so clearly."""
        else:
            prompt = f"""You are a plain-English stock advisor helping a beginner investor understand {name} ({ticker}).

DATA:
- Price: ${price} | Risk score: {risk['score']}/100 ({risk['label']})
- Chart signals: {risk['t']}/100 | Company health: {risk['f']}/100 | Market mood: {risk['s']}/100
- Market: {regime.get('regime','Unknown')} | Sector: {info.get('sector','Unknown')}
- P/E: {info.get('pe','N/A')} | EPS growth: {f"{info.get('eps_growth',0)*100:.1f}%" if info.get('eps_growth') else 'N/A'}
- Analyst target: ${target} ({upside:+.1f}% upside)" if target and upside else "None"
- Insiders: {insider.get('summary','N/A')}
- News: {news.get('sentiment','neutral')} | {'; '.join(headlines[:3]) if headlines else 'No headlines'}

Write 4-5 paragraphs in plain English covering:
1. What this company does (one sentence)
2. What the data says — strongest positives and biggest concerns
3. What analysts and insiders are signalling
4. Bottom line — buy, wait, or avoid? Why?
5. What one thing would change your view?

Be honest. If there are real risks, name them. No jargon without explanation."""

        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[{"role":"user","content":prompt}]
        )
        return resp.content[0].text
    except Exception as e:
        err = str(e)
        if "401" in err or "auth" in err.lower():
            return "❌ Invalid API key — check Settings."
        if "429" in err:
            return "⏳ Rate limit — wait a minute and try again."
        if "404" in err:
            return "❌ Model not found — check your Anthropic account has credits."
        return f"❌ Error: {err[:100]}"

# ─────────────────────────────────────────────────────────────
#  PORTFOLIO HELPERS
# ─────────────────────────────────────────────────────────────

def get_portfolio_positions():
    conn = db()
    positions = pd.read_sql(
        "SELECT * FROM portfolio WHERE status='open' ORDER BY entry_date DESC", conn
    )
    conn.close()
    if positions.empty:
        return []
    results = []
    for _, row in positions.iterrows():
        ticker = row["ticker"]
        info   = get_info(ticker)
        price  = info.get("price") or row["entry_price"]
        cost_basis = row["entry_price"] * row["shares"]
        current_val= price * row["shares"]
        pnl        = current_val - cost_basis
        pnl_pct    = (pnl / cost_basis * 100) if cost_basis > 0 else 0
        atr_df     = get_prices(ticker, period="1mo")
        if atr_df is not None and len(atr_df) >= 14:
            hi = atr_df["High"]; lo = atr_df["Low"]; cl = atr_df["Close"]
            tr = pd.concat([hi-lo,(hi-cl.shift()).abs(),(lo-cl.shift()).abs()],axis=1).max(axis=1)
            atr = float(tr.rolling(14).mean().iloc[-1])
        else:
            atr = price * 0.02
        stop = row["stop_loss"] or (row["entry_price"] - 1.5*atr)
        stop_dist_pct = ((price - stop) / price * 100) if price > 0 else 0
        stop_breached  = bool(price < stop)
        if stop_dist_pct > 8:   stop_status = "green"
        elif stop_dist_pct > 3: stop_status = "amber"
        else:                    stop_status = "red"
        if stop_breached:        stop_status = "breached"
        results.append({
            "id":          int(row["id"]),
            "ticker":      ticker,
            "name":        info.get("name", ticker),
            "sector":      info.get("sector","Unknown"),
            "shares":      float(row["shares"]),
            "entry_price": float(row["entry_price"]),
            "entry_date":  row["entry_date"],
            "current_price": float(price),
            "cost_basis":  round(cost_basis, 2),
            "current_val": round(current_val, 2),
            "pnl":         round(pnl, 2),
            "pnl_pct":     round(pnl_pct, 2),
            "stop":        round(stop, 2),
            "stop_dist_pct": round(stop_dist_pct, 2),
            "stop_status": stop_status,
            "target":      row["target_price"],
            "notes":       row["notes"],
            "beta":        info.get("beta"),
        })
    return results

def position_size(account, risk_pct, price, stop):
    if price <= 0 or stop <= 0 or price <= stop: return {}
    dollar_risk    = account * (risk_pct/100)
    risk_per_share = price - stop
    shares         = dollar_risk / risk_per_share
    total_cost     = shares * price
    pct_account    = (total_cost/account)*100
    return {
        "dollar_risk":   round(dollar_risk,2),
        "risk_per_share":round(risk_per_share,2),
        "shares":        int(shares),
        "total_cost":    round(total_cost,2),
        "pct_account":   round(pct_account,1),
    }

# ─────────────────────────────────────────────────────────────
#  CHARTS
# ─────────────────────────────────────────────────────────────

def chart_price(df, ticker):
    if df is None or df.empty: return go.Figure()
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
        row_heights=[0.50,0.15,0.18,0.17], vertical_spacing=0.02,
        subplot_titles=(f"{ticker} — Price","Volume","RSI (30=oversold / 70=overbought)","MACD"))
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="Price",
        increasing=dict(line=dict(color="#00E676"), fillcolor="rgba(0,230,118,0.55)"),
        decreasing=dict(line=dict(color="#F56565"), fillcolor="rgba(245,101,101,0.55)")
    ), row=1, col=1)
    if "BB_U" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["BB_U"],name="Upper band",
            line=dict(color="#2D3F5A",width=1,dash="dot"),showlegend=False),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["BB_L"],name="Lower band",
            line=dict(color="#2D3F5A",width=1,dash="dot"),
            fill="tonexty",fillcolor="rgba(45,63,90,0.06)",showlegend=False),row=1,col=1)
    for col,clr,nm in [("EMA9","#F6AD55","9d"),("EMA20","#63B3ED","20d"),
                        ("EMA50","#B794F4","50d"),("EMA200","#FC8181","200d")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df.index,y=df[col],name=nm,
                line=dict(color=clr,width=1.2),opacity=0.9),row=1,col=1)
    if "VWAP" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["VWAP"],name="VWAP",
            line=dict(color="#F6E05E",width=1.2,dash="dot"),opacity=0.7),row=1,col=1)
    vc = ["rgba(0,230,118,0.45)" if c>=o else "rgba(245,101,101,0.45)"
          for c,o in zip(df["Close"],df["Open"])]
    fig.add_trace(go.Bar(x=df.index,y=df["Volume"],name="Volume",
        marker_color=vc),row=2,col=1)
    if "AvgVol20" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["AvgVol20"],name="Avg vol",
            line=dict(color="#F6AD55",width=1.5)),row=2,col=1)
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["RSI"],name="RSI",
            line=dict(color="#63B3ED",width=1.5)),row=3,col=1)
        for lvl,clr in [(70,"#F56565"),(50,"#2D3F5A"),(30,"#00E676")]:
            fig.add_hline(y=lvl,line_dash="dot",line_color=clr,opacity=0.4,row=3,col=1)
    if "MACD" in df.columns:
        hc = ["rgba(0,230,118,0.55)" if v>=0 else "rgba(245,101,101,0.55)"
              for v in df["MACD_Hist"].fillna(0)]
        fig.add_trace(go.Bar(x=df.index,y=df["MACD_Hist"],name="Histogram",
            marker_color=hc),row=4,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["MACD"],name="MACD",
            line=dict(color="#63B3ED",width=1.5)),row=4,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["MACD_Signal"],name="Signal",
            line=dict(color="#F6AD55",width=1.5)),row=4,col=1)
    fig.update_layout(height=680, xaxis_rangeslider_visible=False,
                      showlegend=True, **CHART_THEME)
    return fig

def chart_portfolio_equity(positions):
    if not positions: return go.Figure()
    conn = db()
    journal = pd.read_sql("SELECT * FROM journal ORDER BY exit_date", conn)
    conn.close()
    if journal.empty: return go.Figure()
    journal["equity"] = journal["pnl"].cumsum()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=journal["exit_date"], y=journal["equity"],
        mode="lines+markers", name="Cumulative P&L",
        line=dict(color="#00E676",width=2),
        fill="tozeroy", fillcolor="rgba(0,230,118,0.07)"
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="#F56565", opacity=0.3)
    fig.update_layout(height=250, title="Portfolio equity curve — closed trades",
                      **CHART_THEME)
    return fig

def chart_portfolio_heatmap(positions):
    if not positions: return go.Figure()
    tickers = [p["ticker"] for p in positions]
    pnl_pcts = [p["pnl_pct"] for p in positions]
    vals     = [p["current_val"] for p in positions]
    colors   = ["#00E676" if v >= 0 else "#F56565" for v in pnl_pcts]
    fig = go.Figure(go.Bar(
        x=tickers, y=pnl_pcts,
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in pnl_pcts],
        textposition="outside",
    ))
    fig.update_layout(height=220, title="Position P&L — % gain or loss per stock",
                      yaxis_title="Return %", **CHART_THEME)
    return fig

def chart_sector_rotation(sector_perf):
    if not sector_perf: return go.Figure()
    df = pd.DataFrame(list(sector_perf.items()), columns=["Sector","1M Return %"])
    df = df.sort_values("1M Return %")
    colors = ["#00E676" if v>=0 else "#F56565" for v in df["1M Return %"]]
    fig = go.Figure(go.Bar(
        x=df["1M Return %"], y=df["Sector"],
        orientation="h", marker_color=colors,
        text=df["1M Return %"].round(1), textposition="outside"
    ))
    fig.update_layout(height=360,
        title="Sector performance — past month (which industries are hot or cold)",
        **CHART_THEME)
    return fig

def chart_pnl_calendar(journal_df):
    if journal_df.empty: return go.Figure()
    try:
        j = journal_df.copy()
        j["month"] = pd.to_datetime(j["exit_date"]).dt.to_period("M").astype(str)
        monthly = j.groupby("month")["pnl"].sum().reset_index()
        colors  = ["#00E676" if v>=0 else "#F56565" for v in monthly["pnl"]]
        fig = go.Figure(go.Bar(x=monthly["month"],y=monthly["pnl"],marker_color=colors))
        fig.update_layout(height=220, title="Monthly P&L — green = profitable month",
                          **CHART_THEME)
        return fig
    except Exception:
        return go.Figure()

# ─────────────────────────────────────────────────────────────
#  NAVIGATION
# ─────────────────────────────────────────────────────────────

PAGES = [
    ("briefing",   "🌅 Morning Briefing"),
    ("portfolio",  "💼 My Portfolio"),
    ("watchlist",  "🚦 Watchlist"),
    ("scanner",    "🔭 Scanner"),
    ("settings",   "⚙️ Settings"),
]

def render_nav():
    current = st.session_state.page
    tabs_html = ""
    for key, label in PAGES:
        active = "active" if key == current else ""
        tabs_html += f'<span class="nav-tab {active}" id="nav_{key}">{label}</span>'

    st.markdown(
        f'<div class="nav-bar">'
        f'<div class="nav-logo">💹 Smart Advisor</div>'
        f'{tabs_html}'
        f'</div>',
        unsafe_allow_html=True
    )

    # Use columns as nav buttons (Streamlit limitation workaround)
    cols = st.columns(len(PAGES))
    for i, (key, label) in enumerate(PAGES):
        if cols[i].button(label, key=f"nav_btn_{key}",
                          use_container_width=True,
                          type="primary" if key==current else "secondary"):
            st.session_state.page = key
            st.rerun()

# ─────────────────────────────────────────────────────────────
#  PAGE: MORNING BRIEFING
# ─────────────────────────────────────────────────────────────

def page_briefing():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    now = datetime.datetime.now()
    st.markdown(
        f'<div class="page-title">Good {"morning" if now.hour < 12 else "afternoon"}, Ryan 👋</div>'
        f'<div class="page-subtitle">{now.strftime("%A, %d %B %Y")} — Here is everything you need to know before trading today</div>',
        unsafe_allow_html=True
    )

    # Load all shared data
    fg      = get_fear_greed()
    vix     = get_vix()
    regime  = get_market_regime()
    gate    = get_gate_checks()
    positions = get_portfolio_positions()

    # ── Market pulse row ──
    st.markdown('<div class="section-title">Market Pulse</div>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(tile("Market Regime", f'<span class="{regime["regime_cls"]}">{regime["regime"]}</span>',
                     regime["advice"][:60]+"..."), unsafe_allow_html=True)
    fg_color = "#00E676" if fg["value"]>60 else ("#F56565" if fg["value"]<30 else "#F6AD55")
    c2.markdown(tile("Fear & Greed", str(fg["value"]),
                     fg["label"], fg_color), unsafe_allow_html=True)
    vix_color = "#00E676" if vix and vix<15 else ("#F56565" if vix and vix>30 else "#F6AD55")
    c3.markdown(tile("VIX — Fear Gauge", str(vix) if vix else "N/A",
                     "Calm <15 | Caution 15-25 | Fear >30", vix_color), unsafe_allow_html=True)
    gate_color = gate["color"]
    c4.markdown(tile("Pre-Entry Gate", f'{gate["passed"]}/5 checks',
                     gate["label"], gate_color), unsafe_allow_html=True)
    total_pnl = sum(p["pnl"] for p in positions)
    pnl_color = "#00E676" if total_pnl >= 0 else "#F56565"
    c5.markdown(tile("Portfolio P&L",
                     f'{"+" if total_pnl>=0 else ""}${total_pnl:,.0f}',
                     f"{len(positions)} open positions", pnl_color), unsafe_allow_html=True)

    # ── Gate checks ──
    st.markdown('<div class="section-title">Pre-Entry Checklist — Is It Safe To Trade Today?</div>',
                unsafe_allow_html=True)
    st.caption("These five checks tell you how aggressive to be. A guide — not a hard block.")
    gcols = st.columns(5)
    for i, (key, chk) in enumerate(gate["checks"].items()):
        passed = chk.get("pass")
        icon   = "✅" if passed==True else ("⚠️" if passed==False else "❓")
        color  = "#00E676" if passed==True else ("#F56565" if passed==False else "#4A5568")
        gcols[i].markdown(
            f'<div class="metric-tile">'
            f'<div style="font-size:1.4rem;margin-bottom:4px">{icon}</div>'
            f'<div class="mt-label">{chk["name"]}</div>'
            f'<div style="font-size:0.72rem;color:{color};margin-top:4px">{chk["meaning"]}</div>'
            f'<div style="font-family:IBM Plex Mono;font-size:0.65rem;color:#4A5568;margin-top:3px">{chk["value"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── Exit alerts on portfolio ──
    if positions:
        exit_alerts = []
        for p in positions:
            df = get_prices(p["ticker"])
            df = calc_indicators(df.copy()) if df is not None else None
            info     = get_info(p["ticker"])
            analyst  = get_analyst(p["ticker"])
            insider  = get_insider(p["ticker"])
            sigs     = detect_sell_signals(p["ticker"], df, info, analyst, insider)
            if p["stop_status"] in ("red","breached"):
                sigs.insert(0, {
                    "type": "🛑 Near stop-loss" if p["stop_status"]=="red" else "🛑 STOP LOSS BREACHED",
                    "urgency": "HIGH" if p["stop_status"]=="red" else "CRITICAL",
                    "pillar": "Risk",
                    "msg": f"{p['ticker']} is {'within 3% of' if p['stop_status']=='red' else 'below'} your stop loss of ${p['stop']:.2f}. Current price: ${p['current_price']:.2f}."
                })
            for s in sigs:
                s["ticker"] = p["ticker"]
                exit_alerts.append(s)

        if exit_alerts:
            st.markdown('<div class="section-title">⚠️ Exit Alerts — Action Required</div>',
                        unsafe_allow_html=True)
            for a in sorted(exit_alerts, key=lambda x: {"CRITICAL":0,"HIGH":1,"MEDIUM":2}.get(x["urgency"],3)):
                urg = a["urgency"]
                cls = "alert-critical" if urg=="CRITICAL" else ("alert-warn" if urg in ("HIGH","MEDIUM") else "alert-info")
                u_color = "#F56565" if urg=="CRITICAL" else ("#F6AD55" if urg=="HIGH" else "#F6AD55")
                st.markdown(
                    f'<div class="{cls}">'
                    f'<div style="display:flex;justify-content:space-between;margin-bottom:4px">'
                    f'<span style="font-family:Syne,sans-serif;font-size:0.82rem;font-weight:700;color:{u_color}">'
                    f'{a["ticker"]} — {a["type"]}</span>'
                    f'<span style="font-family:IBM Plex Mono;font-size:0.68rem;color:{u_color}">{urg}</span>'
                    f'</div>'
                    f'<div style="font-size:0.83rem;color:#A0AEC0">{a["msg"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                '<div class="alert-good">✅ No exit alerts — all positions look stable right now.</div>',
                unsafe_allow_html=True
            )

    # ── FRED Macro Panel ──
    st.markdown('<div class="section-title">📊 Macro Environment — Federal Reserve Data</div>',
                unsafe_allow_html=True)
    st.caption("Big-picture economic conditions that affect all stocks. Updated daily from the US Federal Reserve.")
    fred = get_fred_macro()
    if fred:
        fred_keys = ["fed_rate","yield_10yr","yield_2yr","yield_spread","unemployment"]
        visible = [k for k in fred_keys if k in fred]
        n_cols  = max(1, len(visible))
        fred_cols = st.columns(n_cols)
        col_i = 0
        for key in fred_keys:
            if key not in fred: continue
            d = fred[key]
            chg_c = "#00E676" if d["change"] >= 0 else "#F56565"
            fred_cols[col_i].markdown(
                f'<div class="metric-tile">' +
                f'<div class="mt-label">{d["label"]}</div>' +
                f'<div class="mt-value">{d["value"]}{d["unit"]}</div>' +
                (f'<div style="font-size:0.7rem;color:{chg_c};margin-top:3px">{d["change"]:+.2f}{d["unit"]} vs prior</div>' if d["change"] != 0 else "") +
                f'</div>',
                unsafe_allow_html=True
            )
            col_i += 1
        for interp in fred.get("interpretation", []):
            cls = "alert-warn" if "⚠️" in interp else "alert-info"
            st.markdown(f'<div class="{cls}" style="margin:4px 0;font-size:0.82rem">{interp}</div>',
                        unsafe_allow_html=True)
    else:
        st.caption("Macro data temporarily unavailable — will retry on next refresh.")

    # ── Earnings calendar ──
    st.markdown('<div class="section-title">📅 Earnings Coming Up</div>', unsafe_allow_html=True)
    st.caption("Stocks can move sharply after earnings announcements — be prepared.")
    conn = db()
    wl = pd.read_sql("SELECT ticker FROM watchlist", conn)
    conn.close()
    all_tickers = list(set([p["ticker"] for p in positions] + wl["ticker"].tolist()))
    earnings_events = []
    for tk in all_tickers:
        ed = get_earnings_date(tk)
        if ed["days"] is not None and 0 <= ed["days"] <= 30:
            earnings_events.append({"ticker":tk,"date":ed["date"],"days":ed["days"],
                                     "in_portfolio": tk in [p["ticker"] for p in positions]})
    if earnings_events:
        earnings_events.sort(key=lambda x: x["days"])
        ec = st.columns(min(len(earnings_events), 4))
        for i, ev in enumerate(earnings_events[:4]):
            urgency = "#F56565" if ev["days"]<=7 else "#F6AD55"
            ec[i].markdown(
                f'<div class="metric-tile">'
                f'<div class="mt-label">{ev["ticker"]} {"💼 owned" if ev["in_portfolio"] else "👁 watching"}</div>'
                f'<div class="mt-value" style="color:{urgency}">{ev["date"]}</div>'
                f'<div class="mt-sub">In {ev["days"]} days</div>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.caption("No earnings announcements in the next 30 days for your stocks.")

    # ── AI Morning Briefing ──
    st.markdown('<div class="section-title">🤖 AI Morning Briefing</div>', unsafe_allow_html=True)
    if positions:
        if st.button("Generate AI briefing for all my positions", type="primary"):
            with st.spinner("Claude is reading your portfolio..."):
                briefings = []
                for p in positions:
                    info    = get_info(p["ticker"])
                    df      = get_prices(p["ticker"])
                    df      = calc_indicators(df.copy()) if df is not None else None
                    opts    = get_options(p["ticker"])
                    risk    = score_stock(p["ticker"], df, info, opts, fg, vix)
                    analyst = get_analyst(p["ticker"])
                    insider = get_insider(p["ticker"])
                    news    = get_news(p["ticker"])
                    text    = run_ai_analysis(p["ticker"], info, risk, analyst,
                                              insider, news, regime, "briefing")
                    briefings.append(f"**{p['ticker']}** — {text}")
                st.session_state["briefing_text"] = "\n\n".join(briefings)

        if "briefing_text" in st.session_state:
            st.markdown(
                '<div class="card"><div class="advice-prose">' +
                st.session_state["briefing_text"].replace("\n", "<br>") +
                '</div></div>',
                unsafe_allow_html=True
            )
    else:
        st.caption("Add positions in 💼 My Portfolio to get an AI morning briefing.")

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  PAGE: MY PORTFOLIO
# ─────────────────────────────────────────────────────────────

def page_portfolio():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.markdown('<div class="page-title">💼 My Portfolio</div>'
                '<div class="page-subtitle">Your open positions — live P&L, stop distances, and risk exposure</div>',
                unsafe_allow_html=True)

    # Add position form
    with st.expander("➕ Add a new position", expanded=False):
        with st.form("add_position"):
            c1,c2,c3 = st.columns(3)
            tk_in    = c1.text_input("Stock symbol", placeholder="e.g. NVDA").upper().strip()
            shares_in = c2.number_input("Number of shares", min_value=0.01, step=1.0)
            price_in = c3.number_input("Price you paid ($)", min_value=0.01, step=0.01)
            c4,c5,c6 = st.columns(3)
            date_in  = c4.date_input("Date you bought")
            stop_in  = c5.number_input("Stop-loss price ($) — 0 = auto-calculate", min_value=0.0, step=0.01)
            target_in = c6.number_input("Target price ($) — 0 = none", min_value=0.0, step=0.01)
            notes_in = st.text_input("Notes (optional)")
            if st.form_submit_button("💾 Add position", type="primary"):
                if tk_in and shares_in > 0 and price_in > 0:
                    conn = db()
                    conn.execute("""
                        INSERT INTO portfolio
                        (ticker,shares,entry_price,entry_date,stop_loss,target_price,notes)
                        VALUES (?,?,?,?,?,?,?)
                    """, (tk_in, shares_in, price_in, str(date_in),
                          stop_in if stop_in > 0 else None,
                          target_in if target_in > 0 else None, notes_in))
                    conn.commit(); conn.close()
                    st.success(f"Added {tk_in} — {shares_in} shares at ${price_in:.2f}")
                    st.rerun()

    # ── eToro CSV Import ──
    with st.expander("📥 Import from eToro (CSV)", expanded=False):
        st.markdown(
            '<div class="advice-prose">' +
            '<strong>How to export from eToro:</strong><br>' +
            '1. Open eToro app or website<br>' +
            '2. Go to <strong>Portfolio</strong><br>' +
            '3. Tap the <strong>⋯ menu</strong> (top right)<br>' +
            '4. Select <strong>Export positions</strong> or <strong>Download statement</strong><br>' +
            '5. Choose <strong>Positions</strong> and download as CSV<br>' +
            '6. Upload that file below</div>',
            unsafe_allow_html=True
        )
        uploaded = st.file_uploader("Upload eToro CSV", type=["csv"], key="etoro_upload")
        if uploaded:
            parsed = parse_etoro_csv(uploaded)
            if parsed:
                st.success(f"Found {len(parsed)} positions in your eToro export:")
                preview_df = pd.DataFrame([{"Ticker":p["ticker"],"Shares":p["shares"],
                    "Entry Price":f'${p["entry_price"]:.2f}',"Date":p["entry_date"]} for p in parsed])
                st.dataframe(preview_df, use_container_width=True, hide_index=True)
                if st.button("✅ Import all these positions", type="primary"):
                    conn = db()
                    imported = 0
                    for p in parsed:
                        try:
                            conn.execute("""
                                INSERT INTO portfolio
                                (ticker,shares,entry_price,entry_date,notes,status)
                                VALUES (?,?,?,?,?,'open')
                            """, (p["ticker"], p["shares"], p["entry_price"],
                                  p["entry_date"], "Imported from eToro"))
                            imported += 1
                        except Exception:
                            pass
                    conn.commit(); conn.close()
                    st.success(f"Imported {imported} positions successfully!")
                    st.rerun()
            else:
                st.error("Could not read positions from this file. Make sure it is the eToro positions export (not statement).")

    # ── Alpaca sync (if connected) ──
    alpaca_positions = get_alpaca_portfolio()
    if alpaca_positions:
        with st.expander(f"🔗 Alpaca Portfolio ({len(alpaca_positions)} positions)", expanded=False):
            st.caption("Live positions from your Alpaca account (read-only)")
            ap_df = pd.DataFrame([{
                "Ticker": p["ticker"],
                "Shares": p["shares"],
                "Entry": f'${p["entry_price"]:.2f}',
                "Current": f'${p["current_price"]:.2f}',
                "P&L": f'{"+" if p["pnl"]>=0 else ""}${p["pnl"]:.2f} ({p["pnl_pct"]:+.1f}%)',
            } for p in alpaca_positions])
            st.dataframe(ap_df, use_container_width=True, hide_index=True)
            if st.button("Sync Alpaca positions to portfolio tracker"):
                conn = db()
                synced = 0
                for p in alpaca_positions:
                    existing = pd.read_sql(
                        "SELECT id FROM portfolio WHERE ticker=? AND status='open'",
                        conn, params=(p["ticker"],)
                    )
                    if existing.empty:
                        conn.execute("""
                            INSERT INTO portfolio
                            (ticker,shares,entry_price,entry_date,notes,status)
                            VALUES (?,?,?,?,?,'open')
                        """, (p["ticker"], p["shares"], p["entry_price"],
                              str(datetime.date.today()), "Synced from Alpaca"))
                        synced += 1
                conn.commit(); conn.close()
                st.success(f"Synced {synced} new positions")
                st.rerun()

    positions = get_portfolio_positions()
    if not positions:
        st.info("No open positions yet. Add your first position above, or import from eToro.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── Summary stats ──
    total_cost = sum(p["cost_basis"] for p in positions)
    total_val  = sum(p["current_val"] for p in positions)
    total_pnl  = sum(p["pnl"] for p in positions)
    total_pct  = (total_pnl/total_cost*100) if total_cost > 0 else 0
    max_loss   = sum(max(0, (p["current_price"]-p["stop"])*p["shares"]) for p in positions)
    sectors    = {}
    for p in positions:
        sectors[p["sector"]] = sectors.get(p["sector"],0) + p["current_val"]

    pnl_color = "#00E676" if total_pnl >= 0 else "#F56565"
    st.markdown('<div class="section-title">Portfolio Summary</div>', unsafe_allow_html=True)
    s1,s2,s3,s4,s5 = st.columns(5)
    s1.markdown(tile("Total Invested", f"${total_cost:,.0f}",""), unsafe_allow_html=True)
    s2.markdown(tile("Current Value",  f"${total_val:,.0f}",""), unsafe_allow_html=True)
    s3.markdown(tile("Total P&L",
                     f'{"+" if total_pnl>=0 else ""}${total_pnl:,.0f}',
                     f"{total_pct:+.1f}%", pnl_color), unsafe_allow_html=True)
    s4.markdown(tile("Max Loss if Stops Hit", f"-${max_loss:,.0f}",
                     "If all stop-losses trigger", "#F6AD55"), unsafe_allow_html=True)
    s5.markdown(tile("Open Positions", str(len(positions)),""), unsafe_allow_html=True)

    # ── P&L heatmap chart ──
    st.markdown('<div class="section-title">Position Performance</div>', unsafe_allow_html=True)
    st.plotly_chart(chart_portfolio_heatmap(positions), use_container_width=True)

    # ── Individual position cards ──
    st.markdown('<div class="section-title">Open Positions</div>', unsafe_allow_html=True)
    for p in positions:
        pnl_color = "#00E676" if p["pnl"] >= 0 else "#F56565"
        stop_colors = {"green":"#00E676","amber":"#F6AD55","red":"#F56565","breached":"#F56565"}
        stop_icons  = {"green":"🟢","amber":"🟡","red":"🔴","breached":"🚨"}
        stop_c = stop_colors.get(p["stop_status"],"#4A5568")
        stop_i = stop_icons.get(p["stop_status"],"❓")

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            h1,h2,h3,h4 = st.columns([3,2,2,1])
            with h1:
                st.markdown(
                    f'<div style="font-family:Syne,sans-serif;font-size:1.2rem;font-weight:800;color:#EDF2F7">{p["ticker"]}</div>'
                    f'<div style="font-size:0.78rem;color:#4A5568">{p["name"]} · {p["sector"]}</div>'
                    f'<div style="font-size:0.72rem;color:#4A5568;margin-top:2px">Bought {p["entry_date"]} · {p["shares"]:.0f} shares @ ${p["entry_price"]:.2f}</div>',
                    unsafe_allow_html=True
                )
            with h2:
                st.markdown(
                    f'<div style="font-family:IBM Plex Mono;font-size:1.4rem;color:#EDF2F7">${p["current_price"]:.2f}</div>'
                    f'<div style="font-size:0.75rem;color:#4A5568">Current price</div>'
                    f'<div style="font-size:0.8rem;color:{pnl_color};margin-top:2px">{"+" if p["pnl"]>=0 else ""}${p["pnl"]:.2f} ({p["pnl_pct"]:+.1f}%)</div>',
                    unsafe_allow_html=True
                )
            with h3:
                st.markdown(
                    f'<div style="font-size:0.75rem;color:#4A5568">Stop-loss</div>'
                    f'<div style="font-family:IBM Plex Mono;font-size:1.1rem;color:{stop_c}">{stop_i} ${p["stop"]:.2f}</div>'
                    f'<div style="font-size:0.75rem;color:{stop_c}">{p["stop_dist_pct"]:.1f}% away</div>',
                    unsafe_allow_html=True
                )
            with h4:
                if st.button("Close", key=f"close_{p['id']}", help="Mark as closed"):
                    conn = db()
                    exit_price = p["current_price"]
                    pnl = (exit_price - p["entry_price"]) * p["shares"]
                    pnl_pct = (exit_price/p["entry_price"]-1)
                    conn.execute("""
                        INSERT INTO journal
                        (ticker,direction,entry_date,exit_date,entry_price,exit_price,
                         shares,pnl,pnl_pct)
                        VALUES (?,?,?,?,?,?,?,?,?)
                    """, (p["ticker"],"LONG",p["entry_date"],
                          datetime.date.today().strftime("%Y-%m-%d"),
                          p["entry_price"],exit_price,p["shares"],
                          round(pnl,2),round(pnl_pct,4)))
                    conn.execute("UPDATE portfolio SET status='closed' WHERE id=?", (p["id"],))
                    conn.commit(); conn.close()
                    st.success(f"Closed {p['ticker']} — P&L ${pnl:+.2f}")
                    st.rerun()

            # Stop loss distance bar
            bar_w = max(0, min(100, 100 - p["stop_dist_pct"]*5))
            st.markdown(
                f'<div style="margin:10px 0 6px 0">'
                f'<div style="display:flex;justify-content:space-between;font-size:0.65rem;color:#4A5568;margin-bottom:3px">'
                f'<span>Stop ${p["stop"]:.2f}</span>'
                f'<span style="color:{stop_c}">{p["stop_dist_pct"]:.1f}% buffer</span>'
                f'<span>Entry ${p["entry_price"]:.2f}</span>'
                f'</div>'
                f'<div style="background:#141E30;border-radius:4px;height:6px;overflow:hidden">'
                f'<div style="width:{bar_w}%;height:100%;background:{stop_c};border-radius:4px"></div>'
                f'</div></div>',
                unsafe_allow_html=True
            )

            # Earnings warning
            ed = get_earnings_date(p["ticker"])
            if ed["days"] is not None and 0 <= ed["days"] <= 14:
                st.markdown(
                    f'<div class="alert-warn" style="margin-top:8px">'
                    f'⚡ Earnings in {ed["days"]} days ({ed["date"]}) — consider reducing position size before the announcement.</div>',
                    unsafe_allow_html=True
                )

            # Edit stop/target
            with st.expander("Edit stop-loss / target / notes"):
                ec1,ec2 = st.columns(2)
                new_stop   = ec1.number_input("New stop-loss ($)", value=p["stop"], key=f"ns_{p['id']}", step=0.01)
                new_target = ec2.number_input("New target ($)", value=p["target"] or 0.0, key=f"nt_{p['id']}", step=0.01)
                new_notes  = st.text_input("Notes", value=p["notes"] or "", key=f"nn_{p['id']}")
                if st.button("Update", key=f"upd_{p['id']}"):
                    conn = db()
                    conn.execute("UPDATE portfolio SET stop_loss=?,target_price=?,notes=? WHERE id=?",
                                 (new_stop, new_target or None, new_notes, p["id"]))
                    conn.commit(); conn.close()
                    st.success("Updated"); st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

    # ── Sector concentration ──
    st.markdown('<div class="section-title">Sector Concentration — Are You Over-Diversified?</div>',
                unsafe_allow_html=True)
    total_v = sum(sectors.values())
    for sec, val in sorted(sectors.items(), key=lambda x: -x[1]):
        pct = val/total_v*100 if total_v > 0 else 0
        bar_c = "#F56565" if pct>40 else ("#F6AD55" if pct>25 else "#00E676")
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:12px;margin:4px 0">'
            f'<div style="width:160px;font-size:0.8rem;color:#718096">{sec}</div>'
            f'<div style="background:#141E30;border-radius:4px;height:8px;width:200px;overflow:hidden">'
            f'<div style="width:{pct:.0f}%;height:100%;background:{bar_c};border-radius:4px"></div></div>'
            f'<div style="font-family:IBM Plex Mono;font-size:0.78rem;color:{bar_c}">{pct:.0f}%</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    if max((v/total_v*100 for v in sectors.values()), default=0) > 40:
        st.markdown('<div class="alert-warn">⚠️ Over 40% in one sector — you are more concentrated than you may realise. Consider diversifying.</div>',
                    unsafe_allow_html=True)

    # ── Equity curve ──
    st.markdown('<div class="section-title">Closed Trade Performance</div>', unsafe_allow_html=True)
    st.plotly_chart(chart_portfolio_equity(positions), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  PAGE: OPPORTUNITIES (Traffic Light List)
# ─────────────────────────────────────────────────────────────

def page_watchlist():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-title">🚦 Watchlist</div>'
        '<div class="page-subtitle">Your tracked stocks — scored, analysed, and explained in plain English</div>',
        unsafe_allow_html=True
    )

    # ── Add / remove tickers ──
    wc1, wc2, wc3 = st.columns([3, 1, 2])
    new_tk = wc1.text_input("Add a stock:", placeholder="e.g. AAPL", label_visibility="collapsed").upper().strip()
    if wc2.button("➕ Add", use_container_width=True) and new_tk:
        conn = db()
        conn.execute("INSERT OR IGNORE INTO watchlist (ticker) VALUES (?)", (new_tk,))
        conn.commit(); conn.close()
        st.success(f"Added {new_tk}"); st.rerun()

    conn = db()
    wl = pd.read_sql("SELECT ticker FROM watchlist ORDER BY ticker", conn)
    conn.close()
    watchlist = wl["ticker"].tolist() if not wl.empty else []

    if not watchlist:
        st.info("Add stocks above to begin. Try: NVDA, AAPL, MSFT, SPY")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    remove_tk = wc3.selectbox("Remove:", ["— keep all —"] + watchlist, label_visibility="collapsed")
    if remove_tk != "— keep all —":
        conn = db()
        conn.execute("DELETE FROM watchlist WHERE ticker=?", (remove_tk,))
        conn.commit(); conn.close()
        st.rerun()

    if st.session_state.paused:
        st.warning("⏸ Scanning paused — enable in ⚙️ Settings")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    fg     = get_fear_greed()
    vix    = get_vix()
    regime = get_market_regime()

    # ── Load all stocks ──
    results = []
    prog = st.progress(0, text="Loading watchlist…")
    for i, tk in enumerate(watchlist):
        prog.progress((i+1)/len(watchlist), text=f"Analysing {tk}…")
        df_raw  = get_prices(tk)
        df      = calc_indicators(df_raw.copy()) if df_raw is not None else None
        info    = get_info(tk)
        opts    = get_options(tk)
        analyst = get_analyst(tk)
        insider = get_insider(tk)
        news    = get_news(tk)
        risk    = score_stock(tk, df, info, opts, fg, vix)
        sigs    = detect_sell_signals(tk, df, info, analyst, insider)
        ed      = get_earnings_date(tk)
        results.append({
            "ticker": tk, "df": df, "info": info, "opts": opts,
            "analyst": analyst, "insider": insider, "news": news,
            "risk": risk, "sell_sigs": sigs, "earnings": ed
        })
        time.sleep(0.15)
    prog.empty()

    # ── Traffic light summary ──
    green  = sorted([r for r in results if r["risk"]["score"] >= 80],  key=lambda x: -x["risk"]["score"])
    yellow = sorted([r for r in results if 50 <= r["risk"]["score"] < 80], key=lambda x: -x["risk"]["score"])
    red    = sorted([r for r in results if r["risk"]["score"] < 50],   key=lambda x: -x["risk"]["score"])

    st.markdown(
        f'<div style="display:flex;gap:10px;margin-bottom:20px">'
        f'<div style="flex:1;background:rgba(0,230,118,0.07);border:1px solid rgba(0,230,118,0.2);'
        f'border-radius:10px;padding:14px;text-align:center">'
        f'<div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;color:#00E676">{len(green)}</div>'
        f'<div style="font-size:0.68rem;color:#4A5568;text-transform:uppercase;letter-spacing:0.1em">Low Risk</div></div>'
        f'<div style="flex:1;background:rgba(246,173,85,0.07);border:1px solid rgba(246,173,85,0.2);'
        f'border-radius:10px;padding:14px;text-align:center">'
        f'<div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;color:#F6AD55">{len(yellow)}</div>'
        f'<div style="font-size:0.68rem;color:#4A5568;text-transform:uppercase;letter-spacing:0.1em">Medium Risk</div></div>'
        f'<div style="flex:1;background:rgba(245,101,101,0.07);border:1px solid rgba(245,101,101,0.2);'
        f'border-radius:10px;padding:14px;text-align:center">'
        f'<div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;color:#F56565">{len(red)}</div>'
        f'<div style="font-size:0.68rem;color:#4A5568;text-transform:uppercase;letter-spacing:0.1em">High Risk</div></div>'
        f'</div>',
        unsafe_allow_html=True
    )

    def render_cards(group, header_color, header_label, note):
        if not group: return
        st.markdown(
            f'<div style="font-family:Syne,sans-serif;font-size:1rem;font-weight:700;'
            f'color:{header_color};margin:24px 0 4px 0">{header_label}</div>'
            f'<div style="font-size:0.78rem;color:#4A5568;margin-bottom:14px">{note}</div>',
            unsafe_allow_html=True
        )

        for r in group:
            tk      = r["ticker"]
            risk    = r["risk"]
            info    = r["info"]
            df      = r["df"]
            analyst = r["analyst"]
            insider = r["insider"]
            news    = r["news"]
            sigs    = r["sell_sigs"]
            ed      = r["earnings"]
            name    = info.get("name", tk)
            price   = info.get("price") or (float(df.iloc[-1]["Close"]) if df is not None and not df.empty else None)
            chg_pct = 0.0
            if df is not None and len(df) > 1:
                chg_pct = float((df.iloc[-1]["Close"] / df.iloc[-2]["Close"] - 1) * 100)
            chg_color = "#00E676" if chg_pct >= 0 else "#F56565"
            color = risk["color"]

            with st.container():
                st.markdown(f'<div class="{risk["css"]}">', unsafe_allow_html=True)

                # ── TOP BAR: ticker, score, price ──
                top1, top2, top3 = st.columns([4, 2, 2])
                with top1:
                    st.markdown(
                        f'<div style="font-family:Syne,sans-serif;font-size:1.25rem;'
                        f'font-weight:800;color:{color}">{tk}</div>'
                        f'<div style="font-size:0.78rem;color:#4A5568;margin-top:1px">'
                        f'{name} · {info.get("sector","")}</div>',
                        unsafe_allow_html=True
                    )
                with top2:
                    st.markdown(
                        f'<div style="text-align:center">'
                        f'<div class="score-big" style="color:{color}">{risk["score"]:.0f}</div>'
                        f'<div class="score-label" style="color:{color}">{risk["label"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                with top3:
                    if price:
                        st.markdown(
                            f'<div style="text-align:right">'
                            f'<div style="font-family:IBM Plex Mono;font-size:1.3rem;color:#EDF2F7">${price:.2f}</div>'
                            f'<div style="color:{chg_color};font-size:0.8rem">'
                            f'{"▲" if chg_pct>=0 else "▼"} {abs(chg_pct):.2f}% today</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                # ── SUB-SCORE PILLS ──
                t_lbl = f"Chart {risk['t']}/100"
                f_lbl = f"Finances {risk['f']}/100"
                s_lbl = f"Mood {risk['s']}/100"
                p_lbl = f"Track rec {risk['p']}/100"
                pills_html = (pill(t_lbl,"blue") + pill(f_lbl,"blue") +
                              pill(s_lbl,"blue") + pill(p_lbl,"blue"))
                if ed["days"] is not None and 0 <= ed["days"] <= 14:
                    earn_txt = f"⚡ Earnings {ed['days']}d"
                    pills_html += pill(earn_txt, "amber")
                st.markdown(pills_html, unsafe_allow_html=True)

                # ── SELL ALERTS ──
                if sigs:
                    st.markdown(
                        f'<div style="font-family:Syne,sans-serif;font-size:0.72rem;'
                        f'font-weight:700;color:#F6AD55;text-transform:uppercase;'
                        f'letter-spacing:0.08em;margin:8px 0 4px 0">'
                        f'⚠️ {len(sigs)} exit signal{"s" if len(sigs)>1 else ""} detected</div>',
                        unsafe_allow_html=True
                    )
                    for sig in sigs[:2]:
                        uc = "#F56565" if sig["urgency"]=="CRITICAL" else "#F6AD55"
                        st.markdown(
                            f'<div class="alert-warn" style="padding:7px 11px;margin:3px 0">'
                            f'<span style="color:{uc};font-weight:600;font-size:0.78rem">'
                            f'{sig["type"]}</span>'
                            f' — <span style="font-size:0.78rem">{sig["msg"]}</span></div>',
                            unsafe_allow_html=True
                        )

                st.markdown("<br>", unsafe_allow_html=True)

                # ── TWO-COLUMN DETAIL LAYOUT ──
                left_col, right_col = st.columns([5, 5])

                with left_col:
                    st.markdown('<div style="font-size:0.68rem;color:#4A5568;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px">Key Metrics</div>', unsafe_allow_html=True)

                    if df is not None and not df.empty:
                        last = df.iloc[-1]
                        metric_rows = [
                            ("P/E Ratio",        f'{info.get("pe"):.1f}' if info.get("pe") else "N/A",       "Price vs earnings — lower = cheaper"),
                            ("Forward P/E",      f'{info.get("fwd_pe"):.1f}' if info.get("fwd_pe") else "N/A","Based on expected earnings"),
                            ("Momentum (RSI)",   f'{float(last.get("RSI",50)):.0f}',                          "30=oversold, 70=overbought"),
                            ("MACD",             f'{"✅ Bullish" if float(last.get("MACD",0))>float(last.get("MACD_Signal",0)) else "❌ Bearish"}', "Momentum direction"),
                            ("Volume",           f'{float(last.get("VolRatio",1)):.1f}× avg',                 "Trading activity vs normal"),
                            ("EPS Growth",       f'{info.get("eps_growth")*100:.1f}%' if info.get("eps_growth") else "N/A", "Earnings growth rate"),
                            ("Debt/Equity",      f'{info.get("debt_equity"):.0f}' if info.get("debt_equity") else "N/A", "Debt level — lower is safer"),
                            ("ROE",              f'{info.get("roe")*100:.1f}%' if info.get("roe") else "N/A", "Profitability per $ invested"),
                            ("Short Interest",   f'{info.get("short_pct")*100:.1f}%' if info.get("short_pct") else "N/A", "% betting the stock falls"),
                            ("Beta",             f'{info.get("beta"):.2f}' if info.get("beta") else "N/A",    "Volatility vs market"),
                        ]
                        for label, value, explain in metric_rows:
                            st.markdown(
                                f'<div style="display:flex;justify-content:space-between;'
                                f'align-items:center;padding:5px 0;border-bottom:1px solid #141E30">'
                                f'<div>'
                                f'<span style="font-size:0.78rem;color:#718096">{label}</span>'
                                f'<span style="font-size:0.65rem;color:#4A5568;margin-left:6px;font-style:italic">{explain}</span>'
                                f'</div>'
                                f'<span style="font-family:IBM Plex Mono;font-size:0.8rem;color:#EDF2F7">{value}</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )

                    # Analyst target
                    if analyst.get("target") and price:
                        up = analyst["upside"] or 0
                        up_c = "#00E676" if up > 0 else "#F56565"
                        st.markdown(
                            f'<div style="margin-top:12px;background:#141E30;border-radius:8px;padding:10px 12px">'
                            f'<div style="font-size:0.68rem;color:#4A5568;text-transform:uppercase;letter-spacing:0.1em">Analyst consensus</div>'
                            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px">'
                            f'<span style="font-family:IBM Plex Mono;font-size:1rem;color:#EDF2F7">Target ${analyst["target"]:.2f}</span>'
                            f'<span style="color:{up_c};font-weight:600">{up:+.1f}% upside</span>'
                            f'</div>'
                            f'<div style="font-size:0.72rem;color:#4A5568;margin-top:3px">'
                            f'Based on {analyst.get("n_analysts",0)} analyst{"s" if analyst.get("n_analysts",0)!=1 else ""}'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )

                with right_col:
                    # ── TABBED DETAIL ──
                    detail_tabs = st.tabs(["📈 Chart", "🤖 AI Analysis", "📰 News", "🏛 Insider", "📊 Score"])

                    with detail_tabs[0]:
                        st.plotly_chart(chart_price(df, tk),
                                        use_container_width=True, key=f"chart_{tk}")

                    with detail_tabs[1]:
                        ai_key = f"ai_{tk}"
                        if st.button(f"Generate analysis", key=f"ai_btn_{tk}", type="primary"):
                            with st.spinner("Claude is analysing…"):
                                reg2  = get_market_regime()
                                opts2 = get_options(tk)
                                risk2 = score_stock(tk, df, info, opts2, fg, vix)
                                text  = run_ai_analysis(tk, info, risk2, analyst,
                                                        insider, news, reg2)
                                st.session_state[ai_key] = text
                        if ai_key in st.session_state:
                            st.markdown(
                                '<div class="advice-prose">' +
                                st.session_state[ai_key].replace("\n", "<br>") +
                                '</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            st.caption("Click above to generate a plain English analysis from Claude AI.")

                    with detail_tabs[2]:
                        sent = news.get("sentiment","neutral")
                        sc   = news.get("score", 50)
                        sent_color = "#00E676" if sent=="bullish" else ("#F56565" if sent=="bearish" else "#F6AD55")
                        st.markdown(
                            f'<div style="font-family:Syne,sans-serif;font-weight:700;'
                            f'color:{sent_color};margin-bottom:8px">'
                            f'{"📈 Bullish" if sent=="bullish" else ("📉 Bearish" if sent=="bearish" else "➡️ Neutral")} news sentiment</div>',
                            unsafe_allow_html=True
                        )
                        # Sentiment bar
                        st.markdown(
                            f'<div style="background:#141E30;border-radius:4px;height:8px;margin-bottom:12px">'
                            f'<div style="width:{sc}%;height:100%;background:linear-gradient(90deg,#F56565,#F6AD55,#00E676);border-radius:4px"></div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        headlines = news.get("headlines", [])
                        if headlines:
                            for h in headlines[:6]:
                                if h.get("title"):
                                    url = h.get("url","")
                                    src = h.get("source","")
                                    line = f'[{h["title"]}]({url})' if url else h["title"]
                                    st.markdown(f'- {line}' + (f' — *{src}*' if src else ""))
                        else:
                            st.caption("No headlines found. Add a Finnhub key in ⚙️ Settings for better coverage.")

                    with detail_tabs[3]:
                        ins_net  = insider.get("net_shares", 0)
                        ins_c    = "#00E676" if ins_net > 0 else ("#F56565" if ins_net < 0 else "#718096")
                        all_txns = insider.get("transactions", [])
                        buys     = [t for t in all_txns if t.get("is_buy")]
                        sells    = [t for t in all_txns if not t.get("is_buy")]
                        st.markdown(
                            '<div class="advice-prose" style="font-size:0.8rem;margin-bottom:10px">'
                            '<strong>What does this mean?</strong> Insiders are company executives and large shareholders. '
                            'When they <span style="color:#00E676">BUY</span> with their own money it can signal confidence. '
                            'When they <span style="color:#F56565">SELL</span> it is less meaningful — '
                            'they often sell for personal reasons like taxes or diversification.'
                            '</div>',
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            f'<div style="background:#141E30;border-radius:8px;padding:10px 14px;'
                            f'margin-bottom:12px;font-weight:600;font-size:0.85rem;color:{ins_c}">'
                            f'{insider.get("summary","No insider data.")}</div>',
                            unsafe_allow_html=True
                        )
                        if buys:
                            buy_count = len(buys)
                            st.markdown(
                                f'<div style="font-family:Syne,sans-serif;font-size:0.72rem;font-weight:700;'
                                f'color:#00E676;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px">'
                                f'BUYING — {buy_count} transaction{"s" if buy_count>1 else ""}</div>',
                                unsafe_allow_html=True
                            )
                            for t in buys:
                                val_str = f'${t["value"]:,.0f}' if t.get("value") else ""
                                st.markdown(
                                    f'<div style="display:flex;gap:8px;font-size:0.75rem;padding:5px 0;'
                                    f'border-bottom:1px solid #141E30">'
                                    f'<span style="color:#718096;width:150px">{t["insider"][:22]}</span>'
                                    f'<span style="color:#00E676;font-family:IBM Plex Mono;width:40px;font-weight:600">BUY</span>'
                                    f'<span style="color:#69F0AE;font-family:IBM Plex Mono;width:110px">{t["shares"]:,} shares</span>'
                                    f'<span style="color:#4A5568;font-size:0.7rem">{val_str}</span>'
                                    f'</div>'
                                    f'<div style="font-size:0.68rem;color:#4A5568;margin-top:3px">'
                                    f'Traded: {t.get("date","Date unknown")}'
                                    f'</div>'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                        else:
                            st.markdown('<div style="color:#4A5568;font-size:0.78rem;margin-bottom:8px">No insider buying recently.</div>', unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        if sells:
                            sell_count = len(sells)
                            st.markdown(
                                f'<div style="font-family:Syne,sans-serif;font-size:0.72rem;font-weight:700;'
                                f'color:#F56565;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px">'
                                f'SELLING — {sell_count} transaction{"s" if sell_count>1 else ""}</div>',
                                unsafe_allow_html=True
                            )
                            for t in sells:
                                val_str = f'${t["value"]:,.0f}' if t.get("value") else ""
                                st.markdown(
                                    f'<div style="display:flex;gap:8px;font-size:0.75rem;padding:5px 0;'
                                    f'border-bottom:1px solid #141E30">'
                                    f'<span style="color:#718096;width:150px">{t["insider"][:22]}</span>'
                                    f'<span style="color:#F56565;font-family:IBM Plex Mono;width:40px;font-weight:600">SELL</span>'
                                    f'<span style="color:#FC8181;font-family:IBM Plex Mono;width:110px">{t["shares"]:,} shares</span>'
                                    f'<span style="color:#4A5568;font-size:0.7rem">{val_str}</span>'
                                    f'</div>'
                                    f'<div style="font-size:0.68rem;color:#4A5568;margin-top:3px">'
                                    f'Traded: {t.get("date","Date unknown")}'
                                    f'</div>'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )
                        else:
                            st.markdown('<div style="color:#4A5568;font-size:0.78rem">No insider selling recently.</div>', unsafe_allow_html=True)

                    with detail_tabs[4]:
                        st.markdown("**Score breakdown — why it got this rating:**")
                        for cat, bd in risk["breakdowns"].items():
                            st.markdown(f"**{cat}**")
                            for item, val in bd.items():
                                if isinstance(val, (int, float)):
                                    bc = "#00E676" if val>=15 else ("#F6AD55" if val>=8 else "#F56565")
                                    st.markdown(
                                        f'<div style="display:flex;align-items:center;gap:10px;margin:3px 0">'
                                        f'<div style="font-size:0.75rem;color:#718096;width:300px">{item}</div>'
                                        f'<div style="background:#141E30;border-radius:3px;height:6px;width:120px;overflow:hidden">'
                                        f'<div style="width:{int(val)}%;height:100%;background:{bc};border-radius:3px"></div></div>'
                                        f'<div style="font-family:IBM Plex Mono;font-size:0.72rem;color:{bc}">{val:.0f}pts</div>'
                                        f'</div>',
                                        unsafe_allow_html=True
                                    )

                # Add to portfolio
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"✕ Remove {tk}", key=f"rm_{tk}"):
                        conn = db()
                        conn.execute("DELETE FROM watchlist WHERE ticker=?", (tk,))
                        conn.commit(); conn.close()
                        st.rerun()
                if st.button(f"➕ Add {tk} to portfolio", key=f"port_{tk}"):
                    st.session_state["prefill_ticker"] = tk
                    st.session_state["page"] = "portfolio"
                    st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)

    render_cards(green,  "#00E676", "🟢 LOW RISK",
                 "Conditions are relatively favourable. Good starting point for new positions.")
    render_cards(yellow, "#F6AD55", "🟡 MEDIUM RISK",
                 "Mixed signals. Trade smaller than usual. Watch closely after entering.")
    render_cards(red,    "#F56565", "🔴 HIGH RISK",
                 "Multiple warning signs. Small position only, tight stop-loss required.")

    st.markdown('</div>', unsafe_allow_html=True)



# ─────────────────────────────────────────────────────────────
#  SCANNER UNIVERSE + QUICK SCREEN
# ─────────────────────────────────────────────────────────────

def get_scan_universe():
    sp500 = [
        "AAPL","MSFT","NVDA","AVGO","ORCL","CRM","AMD","INTC","QCOM","TXN",
        "AMAT","MU","KLAC","LRCX","ADI","MRVL","CDNS","SNPS","FTNT","PANW",
        "LLY","UNH","JNJ","ABBV","MRK","TMO","ABT","DHR","BMY","AMGN",
        "GILD","VRTX","REGN","ISRG","SYK","ELV","CI","HUM","CVS","MDT",
        "BRK-B","JPM","V","MA","BAC","WFC","GS","MS","BLK","SCHW",
        "AXP","SPGI","MCO","ICE","CME","PGR","TRV","AFL","MET","PRU",
        "AMZN","TSLA","HD","MCD","NKE","SBUX","TJX","LOW","BKNG","CMG",
        "ABNB","ETSY","ROST","DG","DLTR","YUM","DRI","HLT","MAR","F",
        "META","GOOGL","NFLX","DIS","CMCSA","T","VZ","TMUS","EA","TTWO",
        "CAT","BA","HON","UPS","RTX","LMT","GE","MMM","DE","FDX",
        "PG","KO","PEP","COST","WMT","PM","MO","MDLZ","CL","GIS",
        "XOM","CVX","COP","EOG","SLB","MPC","PSX","VLO","OXY","HAL",
        "NEE","DUK","SO","AEP","EXC","PLD","AMT","EQIX","CCI","PSA",
    ]
    nasdaq_extra = [
        "ADBE","PYPL","INTU","LULU","MNST","MELI","NXPI","WDAY","TEAM",
        "ZS","DDOG","CRWD","SNOW","OKTA","MDB","COIN","RBLX","HOOD",
        "RIVN","ZM","DOCU","ROKU","TTD","APP","PLTR","SMCI","ARM","DELL",
        "HPQ","ANET","FFIV","WDC","STX","PSTG",
    ]
    top_vol = [
        "SPY","QQQ","IWM","GLD","SLV","TLT","HYG","EEM","ARKK",
        "SQQQ","TQQQ","UVXY","GME","AMC","MARA","RIOT","CLSK",
        "IBIT","BITO","NIO","XPEV","LI","BABA","JD","PDD","GDX","GDXJ",
    ]
    return list(dict.fromkeys(sp500 + nasdaq_extra + top_vol))


def quick_screen(ticker):
    try:
        df = get_prices(ticker, period="3mo")
        if df is None or len(df) < 20: return None
        c = df["Close"]; v = df["Volume"]
        price = float(c.iloc[-1])
        e20   = float(c.ewm(span=20, adjust=False).mean().iloc[-1])
        e50   = float(c.ewm(span=50, adjust=False).mean().iloc[-1])
        ema50 = c.ewm(span=50, adjust=False).mean()
        delta = c.diff()
        gain  = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
        loss  = (-delta).clip(lower=0).ewm(com=13, adjust=False).mean()
        rsi   = float((100-(100/(1+gain/loss.replace(0,np.nan)))).iloc[-1])
        e12 = c.ewm(span=12, adjust=False).mean()
        e26 = c.ewm(span=26, adjust=False).mean()
        macd = e12 - e26; sig = macd.ewm(span=9, adjust=False).mean()
        macd_bull     = bool(macd.iloc[-1] > sig.iloc[-1])
        macd_cross_up = bool(macd.iloc[-2] < sig.iloc[-2] and macd.iloc[-1] > sig.iloc[-1])
        avg_vol = float(v.rolling(20).mean().iloc[-1])
        vr      = float(v.iloc[-1]/avg_vol) if avg_vol > 0 else 1.0
        mo1m = float((price/c.iloc[-21]-1)*100) if len(c)>=21 else 0
        mo1w = float((price/c.iloc[-5]-1)*100)  if len(c)>=5  else 0
        hi52     = float(c.max())
        near_hi  = bool(price >= hi52*0.95)
        uptrend  = bool(price > e20 and price > e50)
        breakout = bool(len(c)>=2 and float(c.iloc[-2]) < float(ema50.iloc[-2]) and price > e50)
        signals = []; ss = 0
        if uptrend and rsi > 50 and macd_bull: signals.append("🟢 Uptrend confirmed"); ss += 30
        if vr > 2.0:                           signals.append(f"🔊 Volume {vr:.1f}× avg"); ss += 20
        if near_hi and mo1m > 5:               signals.append("🏔 Near 52W high"); ss += 20
        if macd_cross_up:                      signals.append("⚡ MACD bullish cross"); ss += 15
        if mo1m > 15:                          signals.append(f"🚀 +{mo1m:.1f}% this month"); ss += 15
        if breakout:                           signals.append("📈 Breaking above 50d avg"); ss += 10
        if ss == 0: return None
        return {
            "ticker": ticker, "price": round(price,2), "rsi": round(rsi,1),
            "vr": round(vr,2), "mo1m": round(mo1m,2), "mo1w": round(mo1w,2),
            "near_hi": near_hi, "uptrend": uptrend, "macd_bull": macd_bull,
            "signals": signals, "score": ss
        }
    except Exception:
        return None

def page_scanner():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.markdown('<div class="page-title">🔭 Market Scanner</div>'
                '<div class="page-subtitle">Scan 200+ stocks to find the best setups right now — runs on demand, cached for 4 hours</div>',
                unsafe_allow_html=True)

    universe = get_scan_universe()
    last_run = st.session_state.scanner_last_run
    if last_run:
        age_h = (time.time()-last_run)/3600
        st.caption(f"Last scan: {datetime.datetime.fromtimestamp(last_run).strftime('%H:%M:%S')} — {age_h:.1f}h ago — cache valid for 4h")

    fc1,fc2,fc3 = st.columns(3)
    min_score   = fc1.slider("Min signal score",10,60,20,5)
    sort_by     = fc2.selectbox("Sort by",["Signal Score","1M Return %","Volume Spike","RSI"])
    max_results = fc3.slider("Max results",10,100,50,10)

    if st.button("🔭 Run Full Market Scan", type="primary"):
        results = []; prog = st.progress(0)
        status  = st.empty(); found  = st.empty()
        for i, tk in enumerate(universe):
            prog.progress((i+1)/len(universe), text=f"Scanning {tk} ({i+1}/{len(universe)})…")
            r = quick_screen(tk)
            if r: results.append(r)
            found.info(f"✅ {len(results)} opportunities found…")
            time.sleep(0.12)
        prog.empty(); status.empty(); found.empty()
        st.session_state.scanner_results  = results
        st.session_state.scanner_last_run = time.time()
        st.success(f"Scan complete — {len(results)} opportunities found across {len(universe)} stocks")

    results = st.session_state.scanner_results
    if not results:
        st.info("Click **Run Full Market Scan** to find opportunities. First run takes 5–15 minutes.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    filtered = [r for r in results if r["score"] >= min_score]
    sort_map = {"Signal Score":lambda x:x["score"],"1M Return %":lambda x:x["mo1m"],
                "Volume Spike":lambda x:x["vr"],"RSI":lambda x:x["rsi"]}
    filtered = sorted(filtered, key=sort_map[sort_by], reverse=True)[:max_results]

    if not filtered:
        st.warning(f"No results with score ≥ {min_score}. Lower the filter.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    st.markdown(f'<div class="section-title">{len(filtered)} Opportunities Found</div>',
                unsafe_allow_html=True)

    # Summary table
    rows = [{"Ticker":r["ticker"],"Price ($)":r["price"],"Signal Score":r["score"],
             "1M Return (%)":r["mo1m"],"1W Return (%)":r["mo1w"],
             "Volume Spike":f'{r["vr"]:.1f}×',"RSI":r["rsi"],
             "Near 52W High":"✅" if r["near_hi"] else "","Uptrend":"✅" if r["uptrend"] else "",
             "Key Signal":r["signals"][0] if r["signals"] else ""} for r in filtered]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                 column_config={"Signal Score":st.column_config.ProgressColumn(
                     "Signal Score",min_value=0,max_value=80,format="%d")})

    # Add to watchlist
    ac1,ac2 = st.columns([3,1])
    add_tk = ac1.selectbox("Add to watchlist:", ["—"]+[r["ticker"] for r in filtered])
    ac2.markdown("<br>",unsafe_allow_html=True)
    if ac2.button("➕ Add") and add_tk != "—":
        conn = db()
        conn.execute("INSERT OR IGNORE INTO watchlist (ticker) VALUES (?)", (add_tk,))
        conn.commit(); conn.close()
        st.success(f"Added {add_tk} to watchlist")

    # Top 10 cards
    st.markdown('<div class="section-title">Top 10 — Detailed View</div>', unsafe_allow_html=True)
    fg = get_fear_greed(); vix = get_vix(); regime = get_market_regime()
    for r in filtered[:10]:
        tk    = r["ticker"]
        color = "#00E676" if r["score"]>=50 else ("#F6AD55" if r["score"]>=30 else "#F56565")
        css   = "tl-green" if r["score"]>=50 else ("tl-yellow" if r["score"]>=30 else "tl-red")
        with st.container():
            st.markdown(f'<div class="{css}">', unsafe_allow_html=True)
            h1,h2,h3 = st.columns([3,2,2])
            with h1:
                st.markdown(f'<div style="font-family:Syne,sans-serif;font-size:1.2rem;font-weight:800;color:{color}">{tk}</div>',
                            unsafe_allow_html=True)
                st.markdown(" ".join([f'<span class="pill pill-green">{s}</span>' for s in r["signals"]]),
                            unsafe_allow_html=True)
            with h2:
                st.markdown(f'<div class="score-big" style="color:{color};text-align:center">{r["score"]}</div>'
                            f'<div class="score-label" style="color:{color};text-align:center">SIGNAL SCORE</div>',
                            unsafe_allow_html=True)
            with h3:
                mc = "#00E676" if r["mo1m"]>=0 else "#F56565"
                st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:1.3rem;color:#EDF2F7;text-align:right">${r["price"]:.2f}</div>'
                            f'<div style="color:{mc};font-size:0.82rem;text-align:right">{"▲" if r["mo1m"]>=0 else "▼"} {abs(r["mo1m"]):.1f}% 1M</div>',
                            unsafe_allow_html=True)
            bc1,bc2 = st.columns(2)
            with bc1:
                if st.button(f"➕ Add {tk} to watchlist", key=f"scan_wl_{tk}"):
                    conn = db(); conn.execute("INSERT OR IGNORE INTO watchlist (ticker) VALUES (?)",(tk,)); conn.commit(); conn.close()
                    st.success(f"Added {tk}")
            with bc2:
                if st.button(f"🤖 AI take on {tk}", key=f"scan_ai_{tk}", type="primary"):
                    with st.spinner("Analysing…"):
                        info_q   = get_info(tk); df_q = get_prices(tk)
                        df_q     = calc_indicators(df_q.copy()) if df_q is not None else None
                        opts_q   = get_options(tk)
                        risk_q   = score_stock(tk, df_q, info_q, opts_q, fg, vix)
                        analyst_q = get_analyst(tk); insider_q = get_insider(tk); news_q = get_news(tk)
                        st.session_state[f"scan_ai_{tk}"] = run_ai_analysis(
                            tk, info_q, risk_q, analyst_q, insider_q, news_q, regime)
            if f"scan_ai_{tk}" in st.session_state:
                st.markdown(
                    '<div class="card" style="margin-top:8px"><div class="advice-prose">' +
                    st.session_state[f"scan_ai_{tk}"].replace("\n","<br>") + '</div></div>',
                    unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  PAGE: TRADE PLANNER
# ─────────────────────────────────────────────────────────────

def page_planner():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.markdown('<div class="page-title">📐 Trade Planner</div>'
                '<div class="page-subtitle">Calculate exact position size, stop-loss, and risk-to-reward before every trade</div>',
                unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-title">Your Trade Details</div>', unsafe_allow_html=True)
        tk_in      = st.text_input("Stock symbol", placeholder="e.g. NVDA",
                                    value=st.session_state.get("prefill_ticker","")).upper().strip()
        entry_p    = st.number_input("Entry price ($)", min_value=0.01, step=0.01)
        stop_p     = st.number_input("Stop-loss price ($) — where you exit if wrong", min_value=0.01, step=0.01)
        target_p   = st.number_input("Target price ($) — where you take profit", min_value=0.01, step=0.01)
        account    = st.number_input("Account size ($)", value=st.session_state.account_size, step=500.0)
        risk_pct   = st.slider("Max % of account to risk", 0.25, 5.0, st.session_state.max_risk_pct, 0.25)

        if entry_p > 0 and stop_p > 0 and stop_p < entry_p:
            sizing = position_size(account, risk_pct, entry_p, stop_p)
            if sizing:
                rr = (target_p-entry_p)/(entry_p-stop_p) if target_p > entry_p and entry_p > stop_p else None
                profit_if_hit = sizing["shares"]*(target_p-entry_p) if target_p > entry_p else None
                rr_color = "#00E676" if rr and rr>=2 else ("#F6AD55" if rr and rr>=1.5 else "#F56565")

                st.markdown('<div class="section-title">Your Recommended Trade</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="tl-green">'
                    f'<table style="width:100%;border-collapse:collapse;font-size:0.88rem">'
                    f'<tr><td style="color:#4A5568;padding:5px 0">Shares to buy</td>'
                    f'<td style="font-family:IBM Plex Mono;color:#EDF2F7;text-align:right"><strong>{sizing["shares"]}</strong></td></tr>'
                    f'<tr><td style="color:#4A5568;padding:5px 0">Total cost</td>'
                    f'<td style="font-family:IBM Plex Mono;color:#EDF2F7;text-align:right">${sizing["total_cost"]:,.2f} ({sizing["pct_account"]:.1f}% of account)</td></tr>'
                    f'<tr><td style="color:#4A5568;padding:5px 0">Max loss if stopped out</td>'
                    f'<td style="font-family:IBM Plex Mono;color:#F56565;text-align:right">-${sizing["dollar_risk"]:,.2f}</td></tr>'
                    f'{"<tr><td style=color:#4A5568;padding:5px_0>Profit if target hit</td><td style=font-family:IBM_Plex_Mono;color:#00E676;text-align:right>+$"+str(round(profit_if_hit,2))+"</td></tr>" if profit_if_hit else ""}'
                    f'</table>'
                    f'{"<div style=margin-top:12px;text-align:center><div style=font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;color:"+rr_color+">1:" + str(round(rr,1))+"</div><div style=font-size:0.72rem;color:#4A5568;text-transform:uppercase;letter-spacing:0.1em>Risk to Reward</div></div>" if rr else ""}'
                    f'</div>',
                    unsafe_allow_html=True
                )

                if rr:
                    if rr >= 2:
                        st.markdown('<div class="alert-good">✅ Excellent R:R — risk $1 to potentially make ${:.1f}. Take this trade.</div>'.format(rr), unsafe_allow_html=True)
                    elif rr >= 1.5:
                        st.markdown('<div class="alert-warn">⚠️ Acceptable R:R but not ideal. Only proceed if the setup score is green.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="alert-critical">❌ Poor R:R — you risk more than you stand to gain. Reconsider.</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="section-title">How Position Sizing Works</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="card"><div class="advice-prose">'
            '<strong>The formula in plain English:</strong><br><br>'
            '1. Decide the most you are willing to lose on this trade.<br>'
            '   Example: Account = $10,000 × 1% = $100 max loss.<br><br>'
            '2. Decide where you exit if wrong (stop-loss).<br>'
            '   Example: Buy at $50, stop at $47 = $3 risk per share.<br><br>'
            '3. Divide: $100 ÷ $3 = 33 shares to buy.<br><br>'
            '4. Total cost: 33 × $50 = $1,650.<br><br>'
            '<strong>Rules to never break:</strong><br>'
            '• Never risk more than 1-2% of your account per trade.<br>'
            '• Never put more than 20-25% of your account in one stock.<br>'
            '• Always set a stop-loss BEFORE you buy.<br>'
            '• Aim for Risk-to-Reward of 1:2 or better.<br>'
            '• If the R:R is under 1:1.5, skip the trade.<br>'
            '</div></div>',
            unsafe_allow_html=True
        )

        if tk_in:
            st.markdown('<div class="section-title">Current Risk Score</div>', unsafe_allow_html=True)
            with st.spinner(f"Loading {tk_in}…"):
                df   = get_prices(tk_in); df = calc_indicators(df.copy()) if df is not None else None
                info = get_info(tk_in); opts = get_options(tk_in)
                fg   = get_fear_greed(); vix = get_vix()
                risk = score_stock(tk_in, df, info, opts, fg, vix)
                color = risk["color"]
                st.markdown(
                    f'<div class="{risk["css"]}" style="text-align:center;padding:20px">'
                    f'<div class="score-big" style="color:{color}">{risk["score"]:.0f}</div>'
                    f'<div class="score-label" style="color:{color}">{risk["label"]}</div>'
                    f'<div style="margin-top:8px">'
                    + pill(f"Chart {risk['t']}/100","blue") + pill(f"Finances {risk['f']}/100","blue")
                    + pill(f"Mood {risk['s']}/100","blue") +
                    f'</div></div>',
                    unsafe_allow_html=True
                )
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  PAGE: JOURNAL
# ─────────────────────────────────────────────────────────────

def page_journal():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.markdown('<div class="page-title">📓 Trade Journal</div>'
                '<div class="page-subtitle">Log every trade, track your performance, and discover your behavioural patterns</div>',
                unsafe_allow_html=True)

    with st.expander("➕ Log a new trade", expanded=False):
        with st.form("journal_form"):
            r1c1,r1c2,r1c3 = st.columns(3)
            tk_in   = r1c1.text_input("Stock symbol").upper().strip()
            dir_in  = r1c2.selectbox("Direction",["LONG (bought to rise)","SHORT (bet to fall)"])
            strat   = r1c3.text_input("Strategy name", placeholder="e.g. EMA Breakout")
            r2c1,r2c2 = st.columns(2)
            ed = r2c1.date_input("Entry date"); xd = r2c2.date_input("Exit date")
            r3c1,r3c2,r3c3 = st.columns(3)
            ep = r3c1.number_input("Entry price ($)",min_value=0.01,step=0.01)
            xp = r3c2.number_input("Exit price ($)", min_value=0.01,step=0.01)
            sh = r3c3.number_input("Shares",        min_value=0.1,  step=1.0)
            r4c1,r4c2,r4c3 = st.columns(3)
            sp_in  = r4c1.number_input("Stop-loss used ($)",  min_value=0.0,step=0.01)
            tgt_in = r4c2.number_input("Target aimed for ($)",min_value=0.0,step=0.01)
            tag    = r4c3.text_input("Setup tag", placeholder="e.g. EMA bounce")
            r5c1,r5c2 = st.columns(2)
            mfe_in = r5c1.number_input("Best % the trade reached (MFE)",step=0.1)
            mae_in = r5c2.number_input("Worst % it went against you (MAE)",step=0.1)
            mistake = st.selectbox("Mistake type (if any)",["None","Wrong direction",
                "Right idea wrong timing","Position too large","Emotional exit",
                "No stop-loss set","Held past stop","Other"])
            viol = st.checkbox("⚠️ I broke one of my trading rules")
            st.markdown("**🧠 Behavioural log — the most important section**")
            emotional = st.selectbox("How were you feeling at entry?",["Calm and disciplined",
                "Excited / overconfident","Fearful / hesitant","FOMO — felt I was missing out",
                "Recovering from a recent loss","Bored / traded out of habit","Other"])
            thesis_in = st.text_area("Your original thesis (why did you buy this?)",
                placeholder="e.g. Breaking above 50d EMA with strong volume, analyst upgrade this week")
            deviation_in = st.text_area("Did you deviate from your plan? How and why?",
                placeholder="e.g. Held past my stop because I was convinced it would recover")
            exit_reason = st.selectbox("Why did you exit?",["Hit planned target","Hit stop-loss",
                "Thesis broke down","Technical signal reversed","Emotional exit — panicked",
                "Emotional exit — got greedy","Position too large, reduced stress","Other"])
            notes_in = st.text_area("Notes and lessons learned")

            if st.form_submit_button("💾 Save trade", type="primary"):
                direction = "LONG" if "LONG" in dir_in else "SHORT"
                pnl       = (xp-ep)*sh if direction=="LONG" else (ep-xp)*sh
                pnl_pct   = (xp/ep-1) if direction=="LONG" else (ep/xp-1)
                stop_d    = ep-sp_in if sp_in > 0 else None
                r_mult    = (pnl/(stop_d*sh)) if stop_d and stop_d > 0 else None
                conn = db()
                conn.execute("""
                    INSERT INTO journal
                    (ticker,direction,entry_date,exit_date,entry_price,exit_price,
                     shares,pnl,pnl_pct,r_multiple,stop_price,target_price,
                     strategy,setup_tag,mfe,mae,rule_violation,mistake_type,
                     emotional_state,thesis,deviation,exit_reason,notes)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (tk_in,direction,str(ed),str(xd),ep,xp,sh,
                      round(pnl,2),round(pnl_pct,4),r_mult,sp_in or None,tgt_in or None,
                      strat,tag,mfe_in,mae_in,int(viol),
                      mistake if mistake!="None" else None,
                      emotional,thesis_in,deviation_in,exit_reason,notes_in))
                conn.commit(); conn.close()
                st.success(f"Saved — P&L: ${pnl:+.2f} ({pnl_pct*100:+.1f}%)")
                st.rerun()

    conn = db()
    tdf = pd.read_sql("SELECT * FROM journal ORDER BY exit_date DESC", conn)
    conn.close()

    if tdf.empty:
        st.info("No trades logged yet. Add your first trade above.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Stats
    wins = (tdf["pnl"]>0).sum(); n = len(tdf); wr = wins/n
    aw = tdf[tdf["pnl"]>0]["pnl_pct"].mean() or 0
    al = tdf[tdf["pnl"]<0]["pnl_pct"].mean() or 0
    exp = wr*aw+(1-wr)*al; total_pnl = tdf["pnl"].sum()
    ts  = tdf.sort_values("exit_date"); ts["eq"] = ts["pnl"].cumsum()
    dd  = (ts["eq"]-ts["eq"].cummax()).min()
    ret_std = tdf["pnl_pct"].std()
    sharpe  = (tdf["pnl_pct"].mean()/ret_std*np.sqrt(252)) if ret_std > 0 else 0
    rm = tdf["r_multiple"].dropna()
    avg_r = rm.mean() if not rm.empty else None

    st.markdown('<div class="section-title">Performance Summary</div>', unsafe_allow_html=True)
    m_cols = st.columns(8)
    stats = [
        ("Trades",str(n),""),
        ("Win Rate",f"{wr*100:.0f}%","% of profitable trades"),
        ("Total P&L",f'{"+" if total_pnl>=0 else ""}${total_pnl:,.0f}',""),
        ("Avg Winner",f"{aw*100:+.1f}%",""),
        ("Avg Loser", f"{al*100:+.1f}%",""),
        ("Expectancy",f"{exp*100:+.2f}%","Avg outcome per trade"),
        ("Max Drawdown",f"${dd:,.0f}","Worst losing run"),
        ("Sharpe Ratio",f"{sharpe:.2f}",">1 = good"),
    ]
    for col,(lbl,val,sub) in zip(m_cols,stats):
        col.markdown(tile(lbl,val,sub), unsafe_allow_html=True)

    if avg_r is not None:
        st.markdown(f'<div class="alert-info" style="margin-top:8px">Average R-Multiple: <strong>{avg_r:+.2f}R</strong> — {"Positive edge ✅" if avg_r>0 else "Negative edge ⚠️ — review your setups"}</div>',
                    unsafe_allow_html=True)

    # Charts
    ch1,ch2 = st.columns(2)
    with ch1:
        st.plotly_chart(chart_portfolio_equity(get_portfolio_positions()), use_container_width=True)
    with ch2:
        st.plotly_chart(chart_pnl_calendar(tdf), use_container_width=True)

    # Setup analysis
    if tdf["setup_tag"].notna().any():
        st.markdown('<div class="section-title">Which Setups Work Best For You?</div>',unsafe_allow_html=True)
        tag_stats = tdf.groupby("setup_tag").agg(
            Trades=("pnl","count"),
            Win_Rate=("pnl",lambda x:f"{(x>0).mean()*100:.0f}%"),
            Avg_PnL=("pnl","mean"),
            Total=("pnl","sum")
        ).round(2).reset_index()
        st.dataframe(tag_stats, use_container_width=True, hide_index=True)

    # Behavioural analysis
    st.markdown('<div class="section-title">🧠 Behavioural Pattern Report (Pillar IV)</div>',unsafe_allow_html=True)
    if "emotional_state" in tdf.columns and tdf["emotional_state"].notna().any():
        emo_df = tdf[tdf["emotional_state"].notna()]
        emo_pnl = emo_df.groupby("emotional_state")["pnl"].agg(
            Trades="count",
            Win_Rate=lambda x:f"{(x>0).mean()*100:.0f}%",
            Avg_PnL="mean"
        ).round(2).reset_index()
        emo_pnl.columns = ["Emotional State","Trades","Win Rate","Avg P&L ($)"]
        st.markdown("**How your emotional state affects your results:**")
        st.dataframe(emo_pnl, use_container_width=True, hide_index=True)
        emo_num = emo_df.groupby("emotional_state")["pnl"].mean()
        if len(emo_num) >= 2:
            best = emo_num.idxmax(); worst = emo_num.idxmin()
            st.markdown(
                f'<div class="alert-info">'
                f'<strong>Your best results come when: {best}</strong><br>'
                f'<strong>Your worst results come when: {worst}</strong><br><br>'
                f'When you notice you are feeling "{worst}" before a trade — pause for 30 minutes before acting.'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.caption("Start logging your emotional state to unlock this analysis.")

    # Rule violations
    viols = tdf[tdf["rule_violation"]==1]
    if not viols.empty:
        st.markdown(f'<div class="alert-warn">⚠️ {len(viols)} trades where you broke your own rules. Avg P&L on those trades: ${viols["pnl"].mean():+.2f}</div>',
                    unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  PAGE: SETTINGS
# ─────────────────────────────────────────────────────────────

def page_settings():
    st.markdown('<div class="page-content">', unsafe_allow_html=True)
    st.markdown('<div class="page-title">⚙️ Settings</div>'
                '<div class="page-subtitle">Configure your account, API keys, and scoring preferences — saved permanently to your Mac</div>',
                unsafe_allow_html=True)

    st.markdown(
        '<div class="alert-good" style="margin-bottom:16px">' +
        '✅ Settings are saved to your Mac and load automatically every time you start the app. ' +
        'You only need to enter your API keys once.' +
        '</div>',
        unsafe_allow_html=True
    )

    c1,c2 = st.columns(2)

    with c1:
        st.markdown('<div class="section-title">Account</div>', unsafe_allow_html=True)
        acc = st.number_input("Total account size ($)", value=st.session_state.account_size,
                               min_value=100.0, step=500.0)
        rsk = st.slider("Max % to risk per trade", 0.25, 5.0,
                         st.session_state.max_risk_pct, 0.25,
                         help="Professionals use 1-2%. Start at 1% as a beginner.")

        st.markdown('<div class="section-title">API Keys — saved permanently</div>', unsafe_allow_html=True)
        ak = st.text_input("Anthropic API key (AI analysis)",
                            value=st.session_state.anthropic_key, type="password",
                            help="Free tier at console.anthropic.com")
        fk = st.text_input("Finnhub API key (news headlines)",
                            value=st.session_state.finnhub_key, type="password",
                            help="Free at finnhub.io")

        st.markdown('<div class="section-title">Alpaca (optional — for portfolio sync)</div>',
                    unsafe_allow_html=True)
        st.caption("Free at alpaca.markets — connects your Alpaca portfolio to the dashboard")
        al_key = st.text_input("Alpaca API key",
                                value=st.session_state.get("alpaca_key",""), type="password")
        al_sec = st.text_input("Alpaca secret key",
                                value=st.session_state.get("alpaca_secret",""), type="password")

        if st.button("💾 Save all settings", type="primary"):
            st.session_state.account_size  = acc
            st.session_state.max_risk_pct  = rsk
            st.session_state.anthropic_key = ak
            st.session_state.finnhub_key   = fk
            st.session_state.alpaca_key    = al_key
            st.session_state.alpaca_secret = al_sec
            save_config({
                "account_size":  acc,
                "max_risk_pct":  rsk,
                "anthropic_key": ak,
                "finnhub_key":   fk,
                "alpaca_key":    al_key,
                "alpaca_secret": al_sec,
                "risk_weights":  st.session_state.risk_weights,
            })
            st.success("✅ All settings saved permanently to your Mac!")

        st.markdown('<div class="section-title">Scanning</div>', unsafe_allow_html=True)
        paused = st.toggle("⏸ Pause all scanning (saves battery)",
                            value=st.session_state.paused)
        st.session_state.paused = paused
        ri = st.slider("Refresh interval (seconds)", 30, 300,
                        st.session_state.refresh_interval, 10)
        st.session_state.refresh_interval = ri
        if ri < 60:
            st.warning("Under 60s may hit Yahoo Finance rate limits.")

    with c2:
        st.markdown('<div class="section-title">Risk Score Weights</div>', unsafe_allow_html=True)
        st.caption("How much each factor counts toward the final score. Must add up to 100%.")
        wt = st.slider("Chart signals %",     0,100,st.session_state.risk_weights["technical"],5)
        wf = st.slider("Company health %",    0,100,st.session_state.risk_weights["fundamental"],5)
        ws = st.slider("Market mood %",       0,100,st.session_state.risk_weights["sentiment"],5)
        wp = st.slider("Your track record %", 0,100,st.session_state.risk_weights["performance"],5)
        total = wt+wf+ws+wp
        if total != 100:
            st.error(f"Weights total {total}% — must equal 100%")
        else:
            if st.button("Save weights", type="primary"):
                new_weights = {"technical":wt,"fundamental":wf,"sentiment":ws,"performance":wp}
                st.session_state.risk_weights = new_weights
                save_config({
                    "account_size":  st.session_state.account_size,
                    "max_risk_pct":  st.session_state.max_risk_pct,
                    "anthropic_key": st.session_state.anthropic_key,
                    "finnhub_key":   st.session_state.finnhub_key,
                    "alpaca_key":    st.session_state.get("alpaca_key",""),
                    "alpaca_secret": st.session_state.get("alpaca_secret",""),
                    "risk_weights":  new_weights,
                })
                st.success("Weights saved")

        st.markdown('<div class="section-title">Data & Cache</div>', unsafe_allow_html=True)
        if st.button("Clear all caches (force fresh data)"):
            st.cache_data.clear()
            st.success("Cache cleared — next load will fetch fresh data")
        if st.button("Clear scanner results"):
            st.session_state.scanner_results  = []
            st.session_state.scanner_last_run = 0
            st.success("Scanner cleared")

        st.markdown('<div class="section-title">About</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="card card-sm"><div class="advice-prose">'
            '<strong>Smart Stock Advisor v2.0</strong><br>'
            'Built on: Streamlit, yfinance, Plotly, Claude AI<br>'
            'Data: Yahoo Finance (15-min delayed), Finnhub (free tier)<br><br>'
            '⚠️ This is an educational tool. Not financial advice. '
            'Always do your own research before investing real money.'
            '</div></div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────

def main():
    render_nav()

    page = st.session_state.page
    if page == "briefing":   page_briefing()
    elif page == "portfolio": page_portfolio()
    elif page == "watchlist": page_watchlist()
    elif page == "scanner":   page_scanner()
    elif page == "settings":  page_settings()

    # Auto-refresh
    if not st.session_state.paused and page in ("briefing","watchlist"):
        elapsed = time.time() - st.session_state.last_refresh
        if elapsed >= st.session_state.refresh_interval:
            st.session_state.last_refresh = time.time()
            time.sleep(0.5)
            st.rerun()

if __name__ == "__main__":
    main()
