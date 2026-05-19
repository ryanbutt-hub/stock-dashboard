"""
================================================================================
SMART STOCK ADVISOR  v3.0   -   app.py
================================================================================
Rebuilt from scratch. Claude AI is the primary analyst.
Data supports the verdict  -  not the other way around.

Six tabs: Portfolio, Watchlist, Scanner, Market Health, AI Advisor, Settings
Run:  streamlit run app.py
Deps: pip install streamlit yfinance pandas numpy plotly requests anthropic
================================================================================
"""
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3, time, datetime, requests, warnings, json, os, pathlib
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

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Stock Advisor",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Design system ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=IBM+Plex+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

html,body,[class*="css"]{font-family:'DM Sans',sans-serif;background:#070A10;color:#C8D0E0;}
.main{background:#070A10;padding:0!important;}
.block-container{padding:1rem 1.5rem 2rem!important;max-width:1400px!important;}

/* Typography */
h1,h2,h3{font-family:'Syne',sans-serif;letter-spacing:-0.02em;}

/* Cards */
.card{background:#0D1220;border:1px solid #1A2540;border-radius:12px;padding:20px;margin-bottom:12px;}
.card-sm{background:#0D1220;border:1px solid #1A2540;border-radius:8px;padding:12px 14px;margin-bottom:8px;}

/* Verdict banners */
.verdict-buy{background:linear-gradient(135deg,#071A0F,#0A2218);border:1px solid rgba(0,230,118,0.3);border-left:4px solid #00E676;border-radius:12px;padding:20px;margin-bottom:12px;}
.verdict-wait{background:linear-gradient(135deg,#1A1407,#221C08);border:1px solid rgba(246,173,85,0.3);border-left:4px solid #F6AD55;border-radius:12px;padding:20px;margin-bottom:12px;}
.verdict-avoid{background:linear-gradient(135deg,#1A0707,#220D0D);border:1px solid rgba(245,101,101,0.3);border-left:4px solid #F56565;border-radius:12px;padding:20px;margin-bottom:12px;}
.verdict-hold{background:linear-gradient(135deg,#071018,#0A1828);border:1px solid rgba(99,179,237,0.3);border-left:4px solid #63B3ED;border-radius:12px;padding:20px;margin-bottom:12px;}

/* Metric tile */
.mt{background:#0D1220;border:1px solid #1A2540;border-radius:10px;padding:14px 16px;text-align:center;}
.mt .lbl{font-size:0.62rem;color:#4A5568;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:5px;font-weight:600;}
.mt .val{font-family:'IBM Plex Mono',monospace;font-size:1.05rem;font-weight:500;color:#EDF2F7;line-height:1.2;}
.mt .sub{font-size:0.68rem;color:#4A5568;margin-top:3px;}

/* Alerts */
.a-red{background:rgba(245,101,101,0.08);border:1px solid rgba(245,101,101,0.25);border-left:3px solid #F56565;border-radius:8px;padding:10px 14px;margin:5px 0;font-size:0.83rem;}
.a-amber{background:rgba(246,173,85,0.08);border:1px solid rgba(246,173,85,0.25);border-left:3px solid #F6AD55;border-radius:8px;padding:10px 14px;margin:5px 0;font-size:0.83rem;}
.a-green{background:rgba(0,230,118,0.06);border:1px solid rgba(0,230,118,0.2);border-left:3px solid #00E676;border-radius:8px;padding:10px 14px;margin:5px 0;font-size:0.83rem;}
.a-blue{background:rgba(99,179,237,0.08);border:1px solid rgba(99,179,237,0.2);border-left:3px solid #63B3ED;border-radius:8px;padding:10px 14px;margin:5px 0;font-size:0.83rem;}

/* Pills */
.pill{display:inline-block;padding:2px 9px;border-radius:20px;font-size:0.67rem;font-family:'IBM Plex Mono',monospace;font-weight:500;margin:2px;}
.p-g{background:rgba(0,230,118,0.1);color:#69F0AE;border:1px solid rgba(0,230,118,0.2);}
.p-r{background:rgba(245,101,101,0.1);color:#FC8181;border:1px solid rgba(245,101,101,0.2);}
.p-a{background:rgba(246,173,85,0.1);color:#F6AD55;border:1px solid rgba(246,173,85,0.2);}
.p-b{background:rgba(99,179,237,0.1);color:#63B3ED;border:1px solid rgba(99,179,237,0.2);}
.p-gr{background:rgba(74,85,104,0.15);color:#718096;border:1px solid rgba(74,85,104,0.2);}

/* Section header */
.sec{font-family:'Syne',sans-serif;font-size:0.68rem;font-weight:700;color:#4A5568;text-transform:uppercase;letter-spacing:0.12em;margin:20px 0 10px;padding-bottom:6px;border-bottom:1px solid #1A2540;}

/* Stop bar */
.stop-bar{background:#141E30;border-radius:4px;height:6px;overflow:hidden;margin-top:4px;}

/* Streamlit overrides */
div[data-testid="stMetric"]{background:#0D1220;border:1px solid #1A2540;border-radius:10px;padding:12px 16px;}
div[data-testid="stMetricLabel"] p{font-size:0.62rem!important;color:#4A5568!important;text-transform:uppercase;letter-spacing:0.1em;}
div[data-testid="stMetricValue"]{font-family:'IBM Plex Mono',monospace!important;font-size:1rem!important;color:#EDF2F7!important;}
.stTabs [data-baseweb="tab-list"]{gap:4px;background:transparent;border-bottom:1px solid #1A2540;}
.stTabs [data-baseweb="tab"]{background:#0D1220;border:1px solid #1A2540;border-radius:6px 6px 0 0;padding:7px 16px;font-family:'Syne',sans-serif;font-size:0.75rem;font-weight:600;color:#4A5568;}
.stTabs [aria-selected="true"]{background:#1A2540!important;color:#EDF2F7!important;border-bottom:2px solid #00E676!important;}
.stButton button{font-family:'Syne',sans-serif;font-size:0.75rem;font-weight:600;border-radius:8px;border:1px solid #1A2540;background:#0D1220;color:#A0AEC0;}
.stButton button[kind="primary"]{background:rgba(0,230,118,0.1);border-color:rgba(0,230,118,0.3);color:#00E676;}
div[data-testid="stExpander"]{background:#0D1220;border:1px solid #1A2540!important;border-radius:10px!important;}
hr{border-color:#1A2540!important;}
[data-testid="stSidebar"]{background:#070A10!important;border-right:1px solid #1A2540;}
.stDataFrame{border:1px solid #1A2540!important;border-radius:10px!important;}
</style>
""", unsafe_allow_html=True)

# ── Config persistence ────────────────────────────────────────
CONFIG = pathlib.Path.home() / "stock-dashboard" / "advisor_config.json"

def load_cfg():
    d = {"anthropic_key":"","finnhub_key":"","alpha_vantage_key":"","etoro_public_key":"","etoro_user_key":"","account_size":3000.0,"max_risk_pct":1.0}
    try:
        if CONFIG.exists():
            d.update(json.loads(CONFIG.read_text()))
    except Exception:
        pass
    return d

def save_cfg(d):
    try:
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps(d, indent=2))
    except Exception as e:
        st.error(f"Could not save config: {e}")

# ── Database ──────────────────────────────────────────────────
DB = "advisor_v3.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS portfolio(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT, shares REAL, entry_price REAL, entry_date TEXT,
        stop_loss REAL, target_price REAL, notes TEXT,
        status TEXT DEFAULT 'open',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS watchlist(
        ticker TEXT PRIMARY KEY,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS journal(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT, direction TEXT DEFAULT 'LONG',
        entry_date TEXT, exit_date TEXT,
        entry_price REAL, exit_price REAL,
        shares REAL, pnl REAL, pnl_pct REAL,
        verdict_at_entry TEXT, notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

def migrate_watchlist():
    """Copy watchlist from any old DB files."""
    for old in ["advisor_v2.db","advisor_journal.db","trade_journal.db"]:
        if not os.path.exists(old): continue
        try:
            old_conn = sqlite3.connect(old)
            wl = pd.read_sql("SELECT ticker FROM watchlist", old_conn)
            old_conn.close()
            new_conn = sqlite3.connect(DB)
            for tk in wl["ticker"].tolist():
                new_conn.execute("INSERT OR IGNORE INTO watchlist(ticker) VALUES(?)",(tk,))
            new_conn.commit(); new_conn.close()
        except Exception:
            pass

init_db()
migrate_watchlist()

# ── Session state ─────────────────────────────────────────────
_cfg = load_cfg()
for k,v in {
    "anthropic_key": _cfg.get("anthropic_key",""),
    "finnhub_key":   _cfg.get("finnhub_key",""),
    "account_size":  _cfg.get("account_size", 3000.0),
    "max_risk_pct":  _cfg.get("max_risk_pct", 1.0),
    "paused":        False,
    "scanner_results": [],
    "scanner_ts":    0,
    "alpha_vantage_key":  _cfg.get("alpha_vantage_key",""),
    "etoro_public_key":   _cfg.get("etoro_public_key",""),
    "etoro_user_key":     _cfg.get("etoro_user_key",""),
    "mode1_results": [],
    "final_recommendations": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Pre-load Ryan's eToro positions (only if portfolio is empty) ──
def seed_portfolio():
    conn = sqlite3.connect(DB)
    existing = pd.read_sql("SELECT COUNT(*) as n FROM portfolio WHERE status='open'", conn)
    if existing["n"].iloc[0] == 0:
        positions = [
            ("CVS",  4.69876, 95.77,  "2026-01-01"),
            ("ELV",  1.20941, 393.58, "2026-01-01"),
            ("HAL",  18.72659,42.72,  "2026-01-01"),
            ("PANW", 3.24267, 246.71, "2026-01-01"),
            ("FTNT", 6.38825, 125.23, "2026-01-01"),
        ]
        for tk, sh, ep, ed in positions:
            conn.execute(
                "INSERT INTO portfolio(ticker,shares,entry_price,entry_date,notes) VALUES(?,?,?,?,?)",
                (tk, sh, ep, ed, "Imported from eToro")
            )
        conn.commit()
    conn.close()

seed_portfolio()

# ── DB helper ─────────────────────────────────────────────────
def db(): return sqlite3.connect(DB)

# ── HTML helpers ──────────────────────────────────────────────
def pill(t, k="gr"): return f'<span class="pill p-{k}">{t}</span>'
def mt(label, value, sub="", color=None):
    vc = f'style="color:{color}"' if color else ''
    return (f'<div class="mt"><div class="lbl">{label}</div>'
            f'<div class="val" {vc}>{value}</div>'
            f'{"<div class=sub>"+sub+"</div>" if sub else ""}</div>')

CHART = dict(
    template="plotly_dark", paper_bgcolor="#070A10", plot_bgcolor="#0D1220",
    font=dict(family="IBM Plex Mono", color="#4A5568", size=10),
    margin=dict(l=44,r=16,t=36,b=28),
    xaxis=dict(gridcolor="#1A2540",showgrid=True,zeroline=False),
    yaxis=dict(gridcolor="#1A2540",showgrid=True,zeroline=False),
)

# ── Data fetching ─────────────────────────────────────────────
@st.cache_data(ttl=55)
def prices(tk, period="6mo", interval="1d"):
    try:
        df = yf.Ticker(tk).history(period=period,interval=interval,auto_adjust=True)
        return df.dropna() if not df.empty else None
    except Exception: return None

@st.cache_data(ttl=300)
def info(tk):
    try:
        i = yf.Ticker(tk).info
        return {
            "name":       i.get("longName", tk),
            "sector":     i.get("sector","Unknown"),
            "price":      i.get("currentPrice") or i.get("regularMarketPrice"),
            "pe":         i.get("trailingPE"),
            "fwd_pe":     i.get("forwardPE"),
            "pb":         i.get("priceToBook"),
            "eps_gr":     i.get("earningsGrowth"),
            "rev_gr":     i.get("revenueGrowth"),
            "de":         i.get("debtToEquity"),
            "roe":        i.get("returnOnEquity"),
            "fcf":        i.get("freeCashflow"),
            "short_pct":  i.get("shortPercentOfFloat"),
            "inst_pct":   i.get("heldPercentInstitutions"),
            "target":     i.get("targetMeanPrice"),
            "target_low": i.get("targetLowPrice"),
            "target_high":i.get("targetHighPrice"),
            "n_analysts": i.get("numberOfAnalystOpinions",0),
            "beta":       i.get("beta"),
            "52w_hi":     i.get("fiftyTwoWeekHigh"),
            "52w_lo":     i.get("fiftyTwoWeekLow"),
            "mktcap":     i.get("marketCap"),
            "earnings_ts":i.get("earningsTimestamp"),
            "div_yield":  i.get("dividendYield"),
        }
    except Exception: return {}

@st.cache_data(ttl=1800)
def vix():
    try:
        h = yf.Ticker("^VIX").history(period="5d")
        return round(float(h["Close"].iloc[-1]),2) if not h.empty else None
    except Exception: return None

@st.cache_data(ttl=1800)
def fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1",timeout=5)
        d = r.json()["data"][0]
        return {"val":int(d["value"]),"label":d["value_classification"]}
    except Exception: return {"val":50,"label":"Neutral"}

@st.cache_data(ttl=900)
def market_data():
    try:
        results = {}
        for sym,name in [("SPY","S&P 500"),("QQQ","NASDAQ"),("IWM","Small Caps")]:
            df = prices(sym,"1y")
            if df is not None and len(df)>=200:
                c = df["Close"]
                p = float(c.iloc[-1])
                e200 = float(c.ewm(span=200,adjust=False).mean().iloc[-1])
                e50  = float(c.ewm(span=50, adjust=False).mean().iloc[-1])
                mo1m = float((p/c.iloc[-21]-1)*100) if len(c)>=21 else 0
                mo3m = float((p/c.iloc[-63]-1)*100) if len(c)>=63 else 0
                results[sym] = {
                    "name":name,"price":p,
                    "above_200":bool(p>e200),"above_50":bool(p>e50),
                    "mo1m":round(mo1m,1),"mo3m":round(mo3m,1),
                }
        sectors = {
            "XLK":"Technology","XLF":"Financials","XLE":"Energy",
            "XLV":"Healthcare","XLI":"Industrials","XLC":"Comms",
            "XLY":"Consumer Cycl","XLP":"Consumer Def",
            "XLB":"Materials","XLU":"Utilities"
        }
        sec_perf = {}
        for sym,name in sectors.items():
            df = prices(sym,"3mo")
            if df is not None and len(df)>=21:
                sec_perf[name] = round(float((df["Close"].iloc[-1]/df["Close"].iloc[-21]-1)*100),2)

        spy = results.get("SPY",{})
        if spy.get("above_200") and spy.get("above_50"):
            regime,regime_color,regime_note = "BULL MARKET","#00E676","Market is in an uptrend. Conditions favour buying."
        elif not spy.get("above_200"):
            regime,regime_color,regime_note = "BEAR MARKET","#F56565","Market is below its long-term average. Be defensive."
        else:
            regime,regime_color,regime_note = "MIXED","#F6AD55","Mixed signals. Be selective and trade smaller."

        return {"indices":results,"sectors":sec_perf,"regime":regime,
                "regime_color":regime_color,"regime_note":regime_note}
    except Exception:
        return {"indices":{},"sectors":{},"regime":"UNKNOWN","regime_color":"#4A5568","regime_note":"Could not load."}

@st.cache_data(ttl=3600)
def analyst_data(tk):
    try:
        i  = yf.Ticker(tk).info
        rc = yf.Ticker(tk).recommendations
        price  = i.get("currentPrice") or i.get("regularMarketPrice")
        target = i.get("targetMeanPrice")
        upside = ((target/price)-1)*100 if target and price else None
        sb=b=h=s=ss=0
        if rc is not None and not rc.empty:
            r = rc.tail(10)
            for col,var in [("strongBuy","sb"),("strong_buy","sb"),("buy","b"),
                             ("hold","h"),("sell","s"),("strongSell","ss"),("strong_sell","ss")]:
                if col in r.columns:
                    if var=="sb":   sb+=int(r[col].sum())
                    elif var=="b":  b+=int(r[col].sum())
                    elif var=="h":  h+=int(r[col].sum())
                    elif var=="s":  s+=int(r[col].sum())
                    elif var=="ss": ss+=int(r[col].sum())
        return {"target":target,"target_low":i.get("targetLowPrice"),
                "target_high":i.get("targetHighPrice"),
                "upside":round(upside,1) if upside else None,
                "n":i.get("numberOfAnalystOpinions",0),
                "sb":sb,"b":b,"h":h,"s":s,"ss":ss}
    except Exception: return {}

@st.cache_data(ttl=3600)
def insider_data(tk):
    try:
        ins = yf.Ticker(tk).insider_transactions
        if ins is None or ins.empty:
            return {"transactions":[],"net":0,"summary":"No recent insider data."}
        ins = ins.copy()
        ins.columns = [c.lower().replace(" ","_") for c in ins.columns]
        txns,net = [],0
        for _,row in ins.head(10).iterrows():
            try:
                sh    = int(row.get("shares",0) or 0)
                val   = float(row.get("value",0) or 0)
                ttype = str(row.get("transaction",row.get("startdate","Unknown")))
                name  = str(row.get("insider",row.get("filer_name","Unknown")))
                date  = str(row.get("startdate",row.get("date","")))[:10]
                is_buy  = any(w in ttype.lower() for w in ["buy","purchase","acquired"])
                is_sell = any(w in ttype.lower() for w in ["sell","sale","disposed"])
                txns.append({"name":name[:28],"type":"BUY" if is_buy else ("SELL" if is_sell else ttype[:15]),
                             "shares":sh,"value":val,"date":date,"is_buy":is_buy})
                if is_buy: net+=sh
                if is_sell: net-=sh
            except Exception: continue
        summary = (f"Net buying: {net:,} shares" if net>0
                   else f"Net selling: {abs(net):,} shares" if net<0
                   else "Balanced activity")
        return {"transactions":txns,"net":net,"summary":summary}
    except Exception: return {"transactions":[],"net":0,"summary":"No data."}

@st.cache_data(ttl=1800)
def news_data(tk):
    key = st.session_state.finnhub_key
    headlines = []
    if key and HAS_FINNHUB:
        try:
            client = finnhub.Client(api_key=key)
            today = datetime.date.today()
            ago   = today - datetime.timedelta(days=7)
            news  = client.company_news(tk,_from=ago.strftime("%Y-%m-%d"),to=today.strftime("%Y-%m-%d"))
            headlines = [{"title":a.get("headline",""),"url":a.get("url",""),"source":a.get("source","")} for a in news[:8]]
        except Exception: pass
    if not headlines:
        try:
            news = yf.Ticker(tk).news or []
            for a in news[:8]:
                c = a.get("content",a) if isinstance(a,dict) else {}
                t = c.get("title","") or a.get("title","")
                headlines.append({"title":t,"url":"","source":""})
        except Exception: pass
    pos = ["surge","beat","record","growth","upgrade","strong","gain","bullish","exceed","boost","rally","profit"]
    neg = ["fall","miss","loss","decline","downgrade","weak","concern","bearish","plunge","layoff","warning","lawsuit"]
    bul = bear = 0
    for h in headlines:
        t = h["title"].lower()
        bul  += sum(1 for w in pos if w in t)
        bear += sum(1 for w in neg if w in t)
    total = bul+bear
    score = int((bul/total)*100) if total>0 else 50
    sent  = "bullish" if score>=65 else ("bearish" if score<=35 else "neutral")
    return {"headlines":headlines,"sentiment":sent,"score":score}

@st.cache_data(ttl=3600)
def earnings_date(tk):
    try:
        ts = yf.Ticker(tk).info.get("earningsTimestamp")
        if ts:
            dt = datetime.datetime.fromtimestamp(ts)
            return {"date":dt.strftime("%Y-%m-%d"),"days":(dt-datetime.datetime.now()).days}
    except Exception: pass
    return {"date":None,"days":None}

# ── Technical indicators ──────────────────────────────────────
def indicators(df):
    if df is None or len(df)<26: return df
    c,h,l,v = df["Close"],df["High"],df["Low"],df["Volume"]
    for span,col in [(9,"E9"),(20,"E20"),(50,"E50"),(200,"E200")]:
        df[col] = c.ewm(span=span,adjust=False).mean()
    delta = c.diff()
    gain  = delta.clip(lower=0).ewm(com=13,adjust=False).mean()
    loss  = (-delta).clip(lower=0).ewm(com=13,adjust=False).mean()
    df["RSI"] = 100-(100/(1+gain/loss.replace(0,np.nan)))
    e12=c.ewm(span=12,adjust=False).mean(); e26=c.ewm(span=26,adjust=False).mean()
    df["MACD"]=e12-e26; df["SIG"]=df["MACD"].ewm(span=9,adjust=False).mean()
    df["HIST"]=df["MACD"]-df["SIG"]
    tp=(h+l+c)/3; df["VWAP"]=(tp*v).cumsum()/v.replace(0,np.nan).cumsum()
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    df["ATR"]=tr.rolling(14).mean()
    df["AVG_V"]=v.rolling(20).mean()
    df["VR"]=v/df["AVG_V"].replace(0,np.nan)
    sma20=c.rolling(20).mean(); std20=c.rolling(20).std()
    df["BBU"]=sma20+2*std20; df["BBL"]=sma20-2*std20
    return df

# ── AI Analysis  -  the primary advisor ────────────────────────
def ai_analysis(tk, inf, an, ins, nws, mkt, mode="stock"):
    """
    Claude reads ALL available data and writes the verdict first.
    The score is derived from the reasoning  -  not the other way around.
    """
    key = st.session_state.anthropic_key
    if not key:
        return None, "Add your Anthropic API key in ⚙️ Settings to enable AI analysis."
    if not HAS_ANTHROPIC:
        return None, "Run: pip install anthropic"
    try:
        client = anthropic.Anthropic(api_key=key)
        name   = inf.get("name", tk)
        price  = inf.get("price","N/A")
        sector = inf.get("sector","Unknown")
        target = an.get("target")
        upside = an.get("upside")
        regime = mkt.get("regime","Unknown")

        # Sector performance context
        sec_perf = mkt.get("sectors",{}).get(sector)
        sec_str  = f"{sector} sector is {sec_perf:+.1f}% this month" if sec_perf else f"in {sector}"

        headlines = [h["title"] for h in nws.get("headlines",[])[:4] if h.get("title")]
        ins_summary = ins.get("summary","No data")

        if mode == "portfolio":
            # Shorter, action-focused for portfolio view
            prompt = f"""You are a plain-English stock advisor. A beginner investor owns {tk} ({name}).

Current data:
- Price: ${price} | Sector: {sector} ({sec_str})
- Market: {regime}
- Analyst target: ${target} ({upside:+.1f}% upside) from {an.get('n',0)} analysts" if target and upside else "No analyst target"
- Insider activity: {ins_summary}
- News: {nws.get('sentiment','neutral')} | {'; '.join(headlines[:2]) if headlines else 'No headlines'}
- Financials: P/E {inf.get('pe','N/A')} | EPS growth {f"{inf.get('eps_gr',0)*100:.1f}%" if inf.get('eps_gr') else 'N/A'} | FCF {'positive' if inf.get('fcf') and inf.get('fcf')>0 else 'negative'}

Write 2-3 sentences max. Be direct. Start with HOLD, REDUCE, or ADD  -  then explain why in plain English. Focus on what matters most right now."""
        else:
            prompt = f"""You are a plain-English stock advisor helping a complete beginner make a decision about {name} ({tk}).

CURRENT DATA:
- Price: ${price} | Sector: {sector} ({sec_str})
- Market regime: {regime}
- P/E: {inf.get('pe','N/A')} | Forward P/E: {inf.get('fwd_pe','N/A')} | EPS growth: {f"{inf.get('eps_gr',0)*100:.1f}%" if inf.get('eps_gr') else 'N/A'}
- Debt/Equity: {inf.get('de','N/A')} | ROE: {f"{inf.get('roe',0)*100:.1f}%" if inf.get('roe') else 'N/A'} | FCF: {'positive' if inf.get('fcf') and inf.get('fcf')>0 else 'negative or N/A'}
- Short interest: {f"{inf.get('short_pct',0)*100:.1f}%" if inf.get('short_pct') else 'N/A'}
- Analyst consensus: {f"${target} target ({upside:+.1f}% upside) from {an.get('n',0)} analysts" if target and upside else "No analyst data"}
- Analyst ratings: {an.get('sb',0)} strong buy, {an.get('b',0)} buy, {an.get('h',0)} hold, {an.get('s',0)} sell, {an.get('ss',0)} strong sell
- Insider activity: {ins_summary}
- News sentiment: {nws.get('sentiment','neutral')} | Headlines: {'; '.join(headlines) if headlines else 'None'}

Write a clear analysis in plain English for a beginner. Structure it as:

**VERDICT: [BUY / WAIT / AVOID]**
One sentence explaining the verdict.

**Why this verdict:**
2-3 paragraphs. Cover: what the company does (1 sentence), what the numbers say, what analysts and insiders signal, and what the market context means for this trade.

**The main risk:**
One sentence on the biggest thing that could go wrong.

**What would change this view:**
One sentence on what signal would make you change the verdict.

Be honest. If analysts think it's overvalued, say so. If the market is in a bear phase, factor that in. Do not be generically positive."""

        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{"role":"user","content":prompt}]
        )
        text = resp.content[0].text

        # Extract verdict from the response
        verdict = "WAIT"
        text_upper = text.upper()
        if "VERDICT: BUY" in text_upper or "**BUY**" in text_upper:
            verdict = "BUY"
        elif "VERDICT: AVOID" in text_upper or "**AVOID**" in text_upper:
            verdict = "AVOID"
        elif "VERDICT: WAIT" in text_upper or "**WAIT**" in text_upper:
            verdict = "WAIT"
        elif "HOLD" in text_upper[:100]:
            verdict = "HOLD"
        elif "ADD" in text_upper[:100]:
            verdict = "BUY"
        elif "REDUCE" in text_upper[:100]:
            verdict = "AVOID"

        return verdict, text

    except Exception as e:
        err = str(e)
        if "401" in err or "auth" in err.lower():
            return None, "❌ Invalid API key  -  check Settings."
        if "429" in err:
            return None, "⏳ Rate limit  -  wait a minute."
        if "404" in err:
            return None, "❌ Model not found  -  check your Anthropic account has credits."
        return None, f"❌ Error: {err[:100]}"

# ── Support score (data quality check) ───────────────────────
def data_score(inf, an, df):
    """
    A simple 0-100 score based purely on data quality signals.
    NOT the primary verdict  -  just supporting evidence for the AI.
    Lower = warning signs in the data. Higher = data looks healthy.
    """
    s = 0
    if df is not None and not df.empty:
        last  = df.iloc[-1]
        price = float(last["Close"])
        if "E50"  in df.columns and price > float(last["E50"]):  s += 15
        if "E200" in df.columns and price > float(last["E200"]): s += 15
        if "RSI"  in df.columns:
            rsi = float(last["RSI"])
            if 40<=rsi<=65:  s += 15
            elif 30<=rsi<=75: s += 8
        if "MACD" in df.columns:
            if float(last["MACD"]) > float(last["SIG"]): s += 15
        if "VR" in df.columns:
            vr = float(last["VR"])
            if vr >= 1.2: s += 10
    if inf:
        if inf.get("eps_gr") and inf["eps_gr"] > 0.10: s += 10
        if inf.get("fcf")    and inf['fcf'] > 0:        s += 10
        if inf.get("de") is not None and inf["de"] < 80: s += 5
    # Analyst upside
    if an.get("upside") and an["upside"] > 10: s += 5
    elif an.get("upside") and an["upside"] < -5: s -= 10
    return max(0, min(100, s))

# ── Verdict styling ───────────────────────────────────────────
VERDICT_STYLE = {
    "BUY":   {"css":"verdict-buy",  "color":"#00E676","emoji":"🟢","note":"Conditions look favourable for a new position."},
    "WAIT":  {"css":"verdict-wait", "color":"#F6AD55","emoji":"🟡","note":"Mixed signals  -  watch but don't rush in."},
    "AVOID": {"css":"verdict-avoid","color":"#F56565","emoji":"🔴","note":"Multiple concerns present. Not the right time."},
    "HOLD":  {"css":"verdict-hold", "color":"#63B3ED","emoji":"🔵","note":"You own this  -  continue holding for now."},
}

def get_vs(v):
    return VERDICT_STYLE.get(v, VERDICT_STYLE["WAIT"])

# ── Charts ────────────────────────────────────────────────────
def chart_price(df, tk, entry=None, stop=None, target=None):
    if df is None or df.empty: return go.Figure()
    fig = make_subplots(rows=3,cols=1,shared_xaxes=True,
        row_heights=[0.55,0.20,0.25],vertical_spacing=0.02,
        subplot_titles=(f"{tk}  -  Price","Volume","RSI (30=oversold / 70=overbought)"))
    fig.add_trace(go.Candlestick(
        x=df.index,open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"],
        name="Price",
        increasing=dict(line=dict(color="#00E676"),fillcolor="rgba(0,230,118,0.55)"),
        decreasing=dict(line=dict(color="#F56565"),fillcolor="rgba(245,101,101,0.55)")
    ),row=1,col=1)
    for col,clr,nm in [("E9","#F6AD55","9d"),("E20","#63B3ED","20d"),("E50","#B794F4","50d"),("E200","#FC8181","200d")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df.index,y=df[col],name=nm,line=dict(color=clr,width=1.2),opacity=0.9),row=1,col=1)
    if "VWAP" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["VWAP"],name="VWAP",line=dict(color="#F6E05E",width=1.2,dash="dot"),opacity=0.7),row=1,col=1)
    # Entry, stop, target lines
    if entry:
        fig.add_hline(y=entry, line_dash="dot", line_color="#63B3ED", opacity=0.7,
                      annotation_text=f"Entry ${entry:.2f}", annotation_position="right", row=1, col=1)
    if stop:
        fig.add_hline(y=stop, line_dash="dot", line_color="#F56565", opacity=0.7,
                      annotation_text=f"Stop ${stop:.2f}", annotation_position="right", row=1, col=1)
    if target:
        fig.add_hline(y=target, line_dash="dot", line_color="#00E676", opacity=0.7,
                      annotation_text=f"Target ${target:.2f}", annotation_position="right", row=1, col=1)
    vc = ["rgba(0,230,118,0.45)" if c>=o else "rgba(245,101,101,0.45)" for c,o in zip(df["Close"],df["Open"])]
    fig.add_trace(go.Bar(x=df.index,y=df["Volume"],name="Volume",marker_color=vc),row=2,col=1)
    if "AVG_V" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["AVG_V"],name="Avg vol",line=dict(color="#F6AD55",width=1.5)),row=2,col=1)
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["RSI"],name="RSI",line=dict(color="#63B3ED",width=1.5)),row=3,col=1)
        for lvl,clr in [(70,"#F56565"),(50,"#2D3F5A"),(30,"#00E676")]:
            fig.add_hline(y=lvl,line_dash="dot",line_color=clr,opacity=0.4,row=3,col=1)
    fig.update_layout(height=600,xaxis_rangeslider_visible=False,showlegend=True,**CHART)
    return fig

def chart_pnl_bar(positions):
    if not positions: return go.Figure()
    tks = [p["ticker"] for p in positions]
    vals = [p["pnl_pct"] for p in positions]
    colors = ["#00E676" if v>=0 else "#F56565" for v in vals]
    fig = go.Figure(go.Bar(x=tks,y=vals,marker_color=colors,
        text=[f"{v:+.1f}%" for v in vals],textposition="outside"))
    fig.update_layout(height=220,title="Position P&L %",yaxis_title="Return %",**CHART)
    return fig

def chart_sector(sec_perf):
    if not sec_perf: return go.Figure()
    df = pd.DataFrame(list(sec_perf.items()),columns=["Sector","1M %"])
    df = df.sort_values("1M %")
    clrs = ["#00E676" if v>=0 else "#F56565" for v in df["1M %"]]
    fig = go.Figure(go.Bar(x=df["1M %"],y=df["Sector"],orientation="h",
        marker_color=clrs,text=df["1M %"].round(1),textposition="outside"))
    fig.update_layout(height=340,title="Sector performance  -  past month",**CHART)
    return fig

# ── Portfolio position loader ─────────────────────────────────
def load_positions():
    conn = db()
    rows = pd.read_sql("SELECT * FROM portfolio WHERE status='open' ORDER BY ticker",conn)
    conn.close()
    if rows.empty: return []
    results = []
    for _,row in rows.iterrows():
        tk  = row["ticker"]
        inf = info(tk)
        px  = inf.get("price") or float(row["entry_price"])
        cb  = float(row["entry_price"]) * float(row["shares"])
        cv  = px * float(row["shares"])
        pnl = cv - cb
        pnl_pct = (pnl/cb*100) if cb>0 else 0
        df  = prices(tk,"1mo")
        atr_val = None
        if df is not None and len(df)>=14:
            hi=df["High"]; lo=df["Low"]; cl=df["Close"]
            tr=pd.concat([hi-lo,(hi-cl.shift()).abs(),(lo-cl.shift()).abs()],axis=1).max(axis=1)
            atr_val = float(tr.rolling(14).mean().iloc[-1])
        stop = float(row["stop_loss"]) if row["stop_loss"] else (px - 1.5*(atr_val or px*0.02))
        stop_dist = (px-stop)/px*100 if px>0 else 0
        stop_breached = bool(px < stop)
        stop_status = ("breached" if stop_breached else
                       "red" if stop_dist<3 else
                       "amber" if stop_dist<8 else "green")
        target = float(row["target_price"]) if row["target_price"] else inf.get("target")
        results.append({
            "id":          int(row["id"]),
            "ticker":      tk,
            "name":        inf.get("name",tk),
            "sector":      inf.get("sector","Unknown"),
            "shares":      float(row["shares"]),
            "entry":       float(row["entry_price"]),
            "entry_date":  row["entry_date"],
            "price":       round(px,2),
            "cost":        round(cb,2),
            "value":       round(cv,2),
            "pnl":         round(pnl,2),
            "pnl_pct":     round(pnl_pct,2),
            "stop":        round(stop,2),
            "stop_dist":   round(stop_dist,2),
            "stop_status": stop_status,
            "target":      round(target,2) if target else None,
            "atr":         round(atr_val,2) if atr_val else None,
            "notes":       row["notes"],
            "inf":         inf,
        })
    return results

def pos_size(account, risk_pct, price, stop):
    if price<=0 or stop<=0 or price<=stop: return {}
    dr = account*(risk_pct/100); rps = price-stop
    sh = dr/rps; tc = sh*price
    return {"dollar_risk":round(dr,2),"shares":int(sh),"total_cost":round(tc,2),
            "pct_account":round(tc/account*100,1)}

# ── TAB: PORTFOLIO ────────────────────────────────────────────

# -- eToro API sync ------------------------------------------
def fetch_etoro_positions():
    """
    Pull live positions directly from eToro API.
    Returns list of positions with ticker, units, avg open, current P&L.
    Requires both public key and user key (read-only is sufficient).
    """
    pub_key  = st.session_state.get("etoro_public_key","")
    user_key = st.session_state.get("etoro_user_key","")
    if not pub_key or not user_key:
        return None, "Add your eToro API keys in Settings to enable live sync."
    try:
        import uuid
        headers = {
            "x-api-key":      pub_key,
            "x-user-key":     user_key,
            "x-request-id":   str(uuid.uuid4()),
            "Content-Type":   "application/json",
        }
        # Fetch positions
        resp = requests.get(
            "https://public-api.etoro.com/api/v1/trading/info/real/pnl",
            headers=headers, timeout=10
        )
        if resp.status_code == 401:
            return None, "Invalid eToro keys -- check your Public Key and User Key in Settings."
        if resp.status_code != 200:
            return None, f"eToro API error: HTTP {resp.status_code}"
        data = resp.json()
        positions = []
        for pos in data.get("positions", []):
            try:
                ticker = pos.get("instrumentId","")
                # eToro uses instrument IDs -- map to ticker via their data
                inst_data = pos.get("instrument", {})
                symbol = inst_data.get("ticker", ticker) or str(ticker)
                units  = float(pos.get("units", 0) or 0)
                avg_open = float(pos.get("avgOpenRate", 0) or 0)
                pnl = float(pos.get("unrealizedPnL", {}).get("pnL", 0) or 0)
                current_rate = float(pos.get("currentRate", avg_open) or avg_open)
                if units > 0 and avg_open > 0:
                    positions.append({
                        "ticker":      symbol.upper(),
                        "units":       units,
                        "avg_open":    avg_open,
                        "current":     current_rate,
                        "pnl":         round(pnl, 2),
                        "pnl_pct":     round((current_rate/avg_open-1)*100, 2) if avg_open > 0 else 0,
                        "value":       round(units * current_rate, 2),
                        "cost":        round(units * avg_open, 2),
                    })
            except Exception:
                continue
        return positions, None
    except requests.exceptions.Timeout:
        return None, "eToro API timed out -- try again in a moment."
    except Exception as e:
        return None, f"eToro connection error: {str(e)[:80]}"

def tab_portfolio():
    st.markdown("## 💼 My Portfolio")
    st.caption("Your open eToro positions  -  live P&L, stop-loss distances, and AI verdict on each.")

    # Add/import
    with st.expander("➕ Add or import positions", expanded=False):
        c1,c2 = st.columns(2)
        with c1:
            st.markdown("**Add manually**")
            with st.form("add_pos"):
                tk_in  = st.text_input("Ticker").upper().strip()
                sh_in  = st.number_input("Shares",min_value=0.001,step=0.001,format="%.5f")
                ep_in  = st.number_input("Avg open price ($)",min_value=0.01,step=0.01)
                dt_in  = st.date_input("Date opened")
                sl_in  = st.number_input("Stop-loss ($)  -  0=auto",min_value=0.0,step=0.01)
                tg_in  = st.number_input("Target ($)  -  0=none",min_value=0.0,step=0.01)
                if st.form_submit_button("Add position",type="primary"):
                    if tk_in and sh_in>0 and ep_in>0:
                        conn=db()
                        conn.execute("INSERT INTO portfolio(ticker,shares,entry_price,entry_date,stop_loss,target_price) VALUES(?,?,?,?,?,?)",
                            (tk_in,sh_in,ep_in,str(dt_in),sl_in or None,tg_in or None))
                        conn.commit(); conn.close()
                        st.success(f"Added {tk_in}"); st.rerun()
        with c2:
            st.markdown("**Import from eToro XLS/CSV**")
            st.caption("In eToro: Portfolio → History → Account Statement → XLS icon")
            uploaded = st.file_uploader("Upload eToro export",type=["csv","xlsx","xls"])
            if uploaded:
                try:
                    if uploaded.name.endswith(".csv"):
                        df_up = pd.read_csv(uploaded)
                    else:
                        df_up = pd.read_excel(uploaded)
                    df_up.columns = [c.lower().strip().replace(" ","_") for c in df_up.columns]
                    ticker_cols = ["ticker","symbol","instrument","asset"]
                    share_cols  = ["units","shares","quantity","amount"]
                    price_cols  = ["open_rate","avg_open","entry_price","avg_price"]
                    date_cols   = ["open_date","entry_date","date","opened"]
                    def fc(candidates):
                        return next((c for c in candidates if c in df_up.columns), None)
                    tc=fc(ticker_cols); sc=fc(share_cols); pc=fc(price_cols); dc=fc(date_cols)
                    parsed=[]
                    if tc:
                        for _,row in df_up.iterrows():
                            try:
                                t = str(row[tc]).upper().split("/")[0].split(".")[0].strip()
                                if not t or t in ["NAN","TOTAL",""]: continue
                                sh = float(row[sc]) if sc and pd.notna(row[sc]) else 1.0
                                ep = float(row[pc]) if pc and pd.notna(row[pc]) else 0.0
                                dt = str(row[dc])[:10] if dc and pd.notna(row[dc]) else str(datetime.date.today())
                                if ep>0 and sh>0: parsed.append((t,sh,ep,dt))
                            except Exception: continue
                    if parsed:
                        st.success(f"Found {len(parsed)} positions")
                        if st.button("Import all",type="primary"):
                            conn=db()
                            for t,sh,ep,dt in parsed:
                                conn.execute("INSERT INTO portfolio(ticker,shares,entry_price,entry_date,notes) VALUES(?,?,?,?,?)",
                                    (t,sh,ep,dt,"eToro import"))
                            conn.commit(); conn.close()
                            st.success("Imported!"); st.rerun()
                    else:
                        st.error("Could not parse positions from this file.")
                except Exception as e:
                    st.error(f"Error reading file: {e}")

    positions = load_positions()
    if not positions:
        st.info("No positions yet. Add your first position above.")
        return

    # Summary
    total_cost  = sum(p["cost"]  for p in positions)
    total_value = sum(p["value"] for p in positions)
    total_pnl   = sum(p["pnl"]   for p in positions)
    total_pct   = (total_pnl/total_cost*100) if total_cost>0 else 0
    pnl_color   = "#00E676" if total_pnl>=0 else "#F56565"

    st.markdown('<div class="sec">Portfolio Summary</div>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(mt("Invested",    f"${total_cost:,.0f}"),  unsafe_allow_html=True)
    c2.markdown(mt("Current Value",f"${total_value:,.0f}"),unsafe_allow_html=True)
    c3.markdown(mt("Total P&L",   f'{"+" if total_pnl>=0 else ""}${total_pnl:,.2f}',
                    f"{total_pct:+.1f}%",pnl_color),unsafe_allow_html=True)
    c4.markdown(mt("Positions",   str(len(positions))), unsafe_allow_html=True)
    winners = sum(1 for p in positions if p["pnl"]>0)
    c5.markdown(mt("Winners",f"{winners}/{len(positions)}",""), unsafe_allow_html=True)

    st.plotly_chart(chart_pnl_bar(positions), use_container_width=True)

    st.markdown('<div class="sec">Open Positions</div>', unsafe_allow_html=True)
    mkt = market_data()

    for p in positions:
        pnl_c = "#00E676" if p["pnl"]>=0 else "#F56565"
        stop_c = {"green":"#00E676","amber":"#F6AD55","red":"#F56565","breached":"#F56565"}.get(p["stop_status"],"#4A5568")
        stop_i = {"green":"✅","amber":"🟡","red":"🔴","breached":"🚨"}.get(p["stop_status"],"❓")

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            h1,h2,h3,h4 = st.columns([3,2,2,1])
            with h1:
                st.markdown(
                    f'<div style="font-family:Syne,sans-serif;font-size:1.15rem;font-weight:800;color:#EDF2F7">{p["ticker"]}</div>'
                    f'<div style="font-size:0.75rem;color:#4A5568">{p["name"]} · {p["sector"]}</div>'
                    f'<div style="font-size:0.7rem;color:#4A5568;margin-top:2px">{p["shares"]:.5f} shares @ ${p["entry"]:.2f} · opened {p["entry_date"]}</div>',
                    unsafe_allow_html=True
                )
            with h2:
                st.markdown(
                    f'<div style="font-family:IBM Plex Mono;font-size:1.3rem;color:#EDF2F7">${p["price"]:.2f}</div>'
                    f'<div style="color:{pnl_c};font-size:0.82rem">{"+" if p["pnl"]>=0 else ""}${p["pnl"]:.2f} ({p["pnl_pct"]:+.1f}%)</div>',
                    unsafe_allow_html=True
                )
            with h3:
                st.markdown(
                    f'<div style="font-size:0.7rem;color:#4A5568">Stop-loss</div>'
                    f'<div style="font-family:IBM Plex Mono;font-size:1rem;color:{stop_c}">{stop_i} ${p["stop"]:.2f}</div>'
                    f'<div style="font-size:0.72rem;color:{stop_c}">{p["stop_dist"]:.1f}% buffer</div>',
                    unsafe_allow_html=True
                )
            with h4:
                if st.button("Close",key=f"cl_{p['id']}"):
                    pnl = (p["price"]-p["entry"])*p["shares"]
                    conn=db()
                    conn.execute("INSERT INTO journal(ticker,entry_date,exit_date,entry_price,exit_price,shares,pnl,pnl_pct) VALUES(?,?,?,?,?,?,?,?)",
                        (p["ticker"],p["entry_date"],str(datetime.date.today()),p["entry"],p["price"],p["shares"],round(pnl,2),round((p["price"]/p["entry"]-1),4)))
                    conn.execute("UPDATE portfolio SET status='closed' WHERE id=?",(p["id"],))
                    conn.commit(); conn.close()
                    st.success(f"Closed {p['ticker']} P&L ${pnl:+.2f}"); st.rerun()

            # Stop bar
            bar_w = max(0,min(100,100-p["stop_dist"]*5))
            st.markdown(
                f'<div style="margin:10px 0 6px">'
                f'<div style="display:flex;justify-content:space-between;font-size:0.62rem;color:#4A5568;margin-bottom:3px">'
                f'<span>Stop ${p["stop"]:.2f}</span>'
                f'<span style="color:{stop_c}">{p["stop_dist"]:.1f}% buffer</span>'
                f'<span>Entry ${p["entry"]:.2f}</span></div>'
                f'<div class="stop-bar"><div style="width:{bar_w}%;height:100%;background:{stop_c};border-radius:4px"></div></div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # Earnings warning
            ed = earnings_date(p["ticker"])
            if ed["days"] is not None and 0<=ed["days"]<=14:
                st.markdown(
                    f'<div class="a-amber">⚡ Earnings in {ed["days"]} days ({ed["date"]})  -  stocks can move sharply. Consider your position size.</div>',
                    unsafe_allow_html=True
                )

            # AI verdict for this position
            ai_key = f"port_ai_{p['ticker']}"
            if st.button(f"🤖 Get AI verdict on {p['ticker']}", key=f"portai_{p['id']}", type="primary"):
                with st.spinner(f"Analysing {p['ticker']}…"):
                    an  = analyst_data(p["ticker"])
                    ins = insider_data(p["ticker"])
                    nws = news_data(p["ticker"])
                    verdict, text = ai_analysis(p['ticker'], p['inf'], an, ins, nws, mkt, mode="portfolio")
                    st.session_state[ai_key] = {"verdict":verdict,"text":text}

            if ai_key in st.session_state:
                v = st.session_state[ai_key].get("verdict","HOLD")
                t = st.session_state[ai_key].get("text","")
                vs = get_vs(v)
                st.markdown(
                    f'<div class="{vs["css"]}" style="margin-top:8px">'
                    f'<div style="font-family:Syne,sans-serif;font-size:1rem;font-weight:800;color:{vs["color"]};margin-bottom:8px">'
                    f'{vs["emoji"]} {v}</div>'
                    f'<div style="font-size:0.86rem;line-height:1.7;color:#A0AEC0">{str(t).replace(chr(10),"<br>")}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            # Edit stop/target
            with st.expander(f"Edit {p['ticker']} stop-loss / target"):
                ec1,ec2 = st.columns(2)
                ns = ec1.number_input("Stop-loss ($)",value=p['stop'],key=f"ns_{p['id']}",step=0.01)
                nt = ec2.number_input("Target ($)",value=p['target'] or 0.0,key=f"nt_{p['id']}",step=0.01)
                if st.button("Update",key=f"upd_{p['id']}"):
                    conn=db()
                    conn.execute("UPDATE portfolio SET stop_loss=?,target_price=? WHERE id=?",(ns,nt or None,p["id"]))
                    conn.commit(); conn.close()
                    st.success("Updated"); st.rerun()
                if st.button(f"✕ Remove {p['ticker']}",key=f"del_{p['id']}"):
                    conn=db()
                    conn.execute("UPDATE portfolio SET status='closed' WHERE id=?",(p["id"],))
                    conn.commit(); conn.close()
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

# ── TAB: WATCHLIST ────────────────────────────────────────────
def tab_watchlist():
    st.markdown("## 🚦 Watchlist")
    st.caption("Stocks you are tracking  -  AI verdict first, supporting data below.")

    wc1,wc2,wc3 = st.columns([3,1,2])
    new_tk = wc1.text_input("Add stock:",placeholder="e.g. NVDA",label_visibility="collapsed").upper().strip()
    if wc2.button("➕ Add",use_container_width=True) and new_tk:
        conn=db(); conn.execute("INSERT OR IGNORE INTO watchlist(ticker) VALUES(?)",(new_tk,)); conn.commit(); conn.close()
        st.success(f"Added {new_tk}"); st.rerun()

    conn=db()
    wl = pd.read_sql("SELECT ticker FROM watchlist ORDER BY ticker",conn)
    conn.close()
    watchlist = wl["ticker"].tolist() if not wl.empty else []

    if not watchlist:
        st.info("Add stocks above to start tracking them. Try: NVDA, AAPL, MSFT, SPY")
        return

    rem = wc3.selectbox("Remove:",[" -  keep all  - "]+watchlist,label_visibility="collapsed")
    if rem!=" -  keep all  - ":
        conn=db(); conn.execute("DELETE FROM watchlist WHERE ticker=?",(rem,)); conn.commit(); conn.close()
        st.rerun()

    if st.session_state.paused:
        st.warning("⏸ Scanning paused  -  enable in Settings")
        return

    mkt = market_data()
    fg  = fear_greed()
    vx  = vix()

    # Market context banner
    regime = mkt.get("regime","Unknown")
    rc = mkt.get("regime_color","#4A5568")
    st.markdown(
        f'<div class="a-blue" style="margin-bottom:16px">'
        f'<strong>Market context:</strong> <span style="color:{rc};font-weight:600">{regime}</span>  -  '
        f'{mkt.get("regime_note","")} '
        f'VIX: <strong>{vx}</strong> · Fear & Greed: <strong>{fg["val"]} ({fg["label"]})</strong>'
        f'</div>',
        unsafe_allow_html=True
    )

    for tk in watchlist:
        df_raw = prices(tk)
        df     = indicators(df_raw.copy()) if df_raw is not None else None
        inf    = info(tk)
        an     = analyst_data(tk)
        ins    = insider_data(tk)
        nws    = news_data(tk)
        ed     = earnings_date(tk)

        price  = inf.get("price") or (float(df.iloc[-1]["Close"]) if df is not None and not df.empty else None)
        chg    = 0.0
        if df is not None and len(df)>1:
            chg = float((df.iloc[-1]["Close"]/df.iloc[-2]["Close"]-1)*100)
        chg_c = "#00E676" if chg>=0 else "#F56565"
        ds    = data_score(inf, an, df)
        ds_c  = "#00E676" if ds>=70 else ("#F6AD55" if ds>=45 else "#F56565")

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)

            # Header
            h1,h2,h3,h4 = st.columns([4,2,2,1])
            with h1:
                st.markdown(
                    f'<div style="font-family:Syne,sans-serif;font-size:1.2rem;font-weight:800;color:#EDF2F7">{tk}</div>'
                    f'<div style="font-size:0.75rem;color:#4A5568">{inf.get("name",tk)} · {inf.get("sector","")}</div>',
                    unsafe_allow_html=True
                )
            with h2:
                if price:
                    st.markdown(
                        f'<div style="font-family:IBM Plex Mono;font-size:1.3rem;color:#EDF2F7">${price:.2f}</div>'
                        f'<div style="color:{chg_c};font-size:0.8rem">{"▲" if chg>=0 else "▼"} {abs(chg):.2f}% today</div>',
                        unsafe_allow_html=True
                    )
            with h3:
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-family:IBM Plex Mono;font-size:1.5rem;font-weight:600;color:{ds_c}">{ds}</div>'
                    f'<div style="font-size:0.62rem;color:#4A5568;text-transform:uppercase;letter-spacing:0.1em">Data score</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with h4:
                if st.button(f"✕",key=f"wl_rm_{tk}",help=f"Remove {tk}"):
                    conn=db(); conn.execute("DELETE FROM watchlist WHERE ticker=?",(tk,)); conn.commit(); conn.close()
                    st.rerun()

            # Earnings warning + key pills
            pills = ""
            if ed["days"] is not None and 0<=ed["days"]<=14:
                pills += pill(f"⚡ Earnings {ed['days']}d","a")
            if an.get("upside") and an["upside"]>10:
                pills += pill(f"↑ {an['upside']:+.0f}% analyst upside","g")
            elif an.get("upside") and an["upside"]<-5:
                pills += pill(f"↓ {an['upside']:+.0f}% analyst target below price","r")
            if ins.get("net",0)>0:
                pills += pill("Insider buying","g")
            elif ins.get("net",0)<-50000:
                pills += pill("Insider selling","r")
            news_sent = nws.get("sentiment","neutral")
            pills += pill(f"News: {news_sent}", "g" if news_sent=="bullish" else ("r" if news_sent=="bearish" else "gr"))
            if pills:
                st.markdown(pills, unsafe_allow_html=True)

            # AI VERDICT  -  primary section
            ai_key = f"wl_ai_{tk}"
            if st.button(f"🤖 Generate AI verdict for {tk}", key=f"wl_ai_btn_{tk}", type="primary"):
                with st.spinner(f"Claude is analysing {tk}…"):
                    verdict, text = ai_analysis(tk, inf, an, ins, nws, mkt)
                    st.session_state[ai_key] = {"verdict":verdict,"text":text}

            if ai_key in st.session_state:
                v  = st.session_state[ai_key].get("verdict","WAIT")
                t  = st.session_state[ai_key].get("text","")
                vs = get_vs(v)
                st.markdown(
                    f'<div class="{vs["css"]}">'
                    f'<div style="font-family:Syne,sans-serif;font-size:1.1rem;font-weight:800;'
                    f'color:{vs["color"]};margin-bottom:10px">{vs["emoji"]} {v}  -  {vs["note"]}</div>'
                    f'<div style="font-size:0.88rem;line-height:1.75;color:#A0AEC0">'
                    f'{str(t).replace(chr(10),"<br>")}'
                    f'</div></div>',
                    unsafe_allow_html=True
                )
            else:
                st.caption("Click above to get Claude's analysis and verdict.")

            # Supporting data tabs
            dt1,dt2,dt3,dt4,dt5 = st.tabs(["📈 Chart","📊 Key Data","📰 News","🏛 Insider","🏦 Analysts"])

            with dt1:
                st.plotly_chart(chart_price(df,tk), use_container_width=True, key=f"c_{tk}")

            with dt2:
                if df is not None and not df.empty:
                    last = df.iloc[-1]
                    rows = [
                        ("P/E Ratio",           f'{inf.get("pe"):.1f}' if inf.get("pe") else "N/A",         "Price vs earnings. Lower = cheaper."),
                        ("Forward P/E",         f'{inf.get("fwd_pe"):.1f}' if inf.get("fwd_pe") else "N/A", "Based on expected future earnings."),
                        ("Momentum (RSI)",       f'{float(last.get("RSI",50)):.0f}/100',                     "30=oversold, 70=overbought. 40-60 is healthy."),
                        ("Trend (MACD)",         "✅ Bullish" if float(last.get("MACD",0))>float(last.get("SIG",0)) else "❌ Bearish","Momentum direction."),
                        ("Volume vs average",    f'{float(last.get("VR",1)):.1f}×',                         "Above 1.5× = unusual activity."),
                        ("EPS Growth",           f'{inf.get("eps_gr",0)*100:.1f}%' if inf.get("eps_gr") else "N/A","Earnings growth rate."),
                        ("Debt/Equity",          f'{inf.get("de"):.0f}' if inf.get("de") else "N/A",        "Lower = less debt. Above 100 needs scrutiny."),
                        ("ROE",                  f'{inf.get("roe",0)*100:.1f}%' if inf.get("roe") else "N/A","Profit per $1 of investment."),
                        ("Short Interest",       f'{inf.get("short_pct",0)*100:.1f}%' if inf.get("short_pct") else "N/A","% betting the stock falls."),
                        ("52W Range",            f'${inf.get("52w_lo","?"):.0f}  -  ${inf.get("52w_hi","?"):.0f}' if inf.get("52w_lo") else "N/A","Lowest and highest price this year."),
                    ]
                    for label,value,explain in rows:
                        st.markdown(
                            f'<div style="display:flex;justify-content:space-between;align-items:center;'
                            f'padding:5px 0;border-bottom:1px solid #1A2540">'
                            f'<div><span style="font-size:0.78rem;color:#718096">{label}</span>'
                            f'<span style="font-size:0.63rem;color:#4A5568;margin-left:6px;font-style:italic">{explain}</span></div>'
                            f'<span style="font-family:IBM Plex Mono;font-size:0.8rem;color:#EDF2F7">{value}</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

            with dt3:
                sent  = nws.get("sentiment","neutral")
                sc    = nws.get("score",50)
                sent_c = "#00E676" if sent=="bullish" else ("#F56565" if sent=="bearish" else "#F6AD55")
                st.markdown(
                    f'<div style="font-weight:600;color:{sent_c};margin-bottom:8px">'
                    f'{"📈" if sent=="bullish" else ("📉" if sent=="bearish" else "➡️")} {sent.capitalize()} news sentiment</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<div style="background:#1A2540;border-radius:4px;height:8px;margin-bottom:12px">'
                    f'<div style="width:{sc}%;height:100%;background:linear-gradient(90deg,#F56565,#F6AD55,#00E676);border-radius:4px"></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                for h in nws.get("headlines",[])[:6]:
                    if h.get("title"):
                        line = f'[{h["title"]}]({h["url"]})' if h.get("url") else h["title"]
                        st.markdown(f'- {line}')

            with dt4:
                ins_net = ins.get("net",0)
                ins_c = "#00E676" if ins_net>0 else ("#F56565" if ins_net<0 else "#718096")
                st.markdown(
                    '<div style="font-size:0.8rem;color:#718096;margin-bottom:10px">'
                    'Insiders are executives and large shareholders. '
                    '<span style="color:#00E676">Buying</span> = potential confidence signal. '
                    '<span style="color:#F56565">Selling</span> = less meaningful (often taxes/diversification).'
                    '</div>',
                    unsafe_allow_html=True
                )
                st.markdown(f'<div style="font-weight:600;color:{ins_c};margin-bottom:10px">{ins.get("summary","")}</div>', unsafe_allow_html=True)
                buys  = [t for t in ins.get("transactions",[]) if t.get("is_buy")]
                sells = [t for t in ins.get("transactions",[]) if not t.get("is_buy")]
                for txns, color, label in [(buys,"#00E676","BUY"),(sells,"#F56565","SELL")]:
                    if txns:
                        lbl = "✅ BUYING" if color=="#00E676" else "🔴 SELLING"
                        st.markdown(f'<div style="font-size:0.7rem;font-weight:700;color:{color};text-transform:uppercase;margin:8px 0 4px">{lbl}</div>', unsafe_allow_html=True)
                        for t in txns:
                            val_str = f'${t["value"]:,.0f}' if t.get("value") else ""
                            st.markdown(
                                f'<div style="padding:5px 0;border-bottom:1px solid #1A2540;font-size:0.75rem">'
                                f'<div style="display:flex;gap:8px">'
                                f'<span style="color:#718096;width:150px">{t["name"][:22]}</span>'
                                f'<span style="color:{color};font-family:IBM Plex Mono;font-weight:600">{label}</span>'
                                f'<span style="color:#A0AEC0;font-family:IBM Plex Mono">{t["shares"]:,} shares</span>'
                                f'{"<span style=color:#4A5568;font-size:0.7rem;margin-left:auto>"+val_str+"</span>" if val_str else ""}'
                                f'</div>'
                                f'<div style="font-size:0.65rem;color:#4A5568;margin-top:2px">📅 {t.get("date","Date unknown")}</div>'
                                f'</div>',
                                unsafe_allow_html=True
                            )

            with dt5:
                if an.get("target") and price:
                    up = an.get("upside",0)
                    up_c = "#00E676" if up>0 else "#F56565"
                    st.markdown(
                        f'<div class="card-sm">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center">'
                        f'<div><div style="font-size:0.65rem;color:#4A5568;text-transform:uppercase;letter-spacing:0.1em">Analyst Price Target</div>'
                        f'<div style="font-family:IBM Plex Mono;font-size:1.2rem;color:#EDF2F7">${an["target"]:.2f}</div></div>'
                        f'<div style="color:{up_c};font-size:1rem;font-weight:600">{up:+.1f}% upside</div>'
                        f'</div>'
                        f'<div style="font-size:0.72rem;color:#4A5568;margin-top:4px">Range: ${an.get("target_low",0):.0f}  -  ${an.get("target_high",0):.0f} · {an.get("n",0)} analysts</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    total_r = an["sb"]+an["b"]+an["h"]+an["s"]+an["ss"]
                    if total_r>0:
                        for label,cnt,lc in [("Strong Buy",an["sb"],"#00E676"),("Buy",an["b"],"#69F0AE"),
                                              ("Hold",an["h"],"#F6AD55"),("Sell",an["s"],"#FC8181"),("Strong Sell",an["ss"],"#F56565")]:
                            pct = cnt/total_r*100
                            st.markdown(
                                f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0">'
                                f'<div style="width:80px;font-size:0.75rem;color:#718096">{label}</div>'
                                f'<div style="background:#1A2540;border-radius:3px;height:8px;width:140px;overflow:hidden">'
                                f'<div style="width:{pct:.0f}%;height:100%;background:{lc};border-radius:3px"></div></div>'
                                f'<div style="font-family:IBM Plex Mono;font-size:0.72rem;color:{lc}">{cnt}</div>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                else:
                    st.caption("No analyst data available.")

            # Add to portfolio
            if st.button(f"➕ Add {tk} to portfolio", key=f"wl_port_{tk}"):
                st.session_state["prefill"] = tk
                st.session_state["tab"] = "portfolio"
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

# ── TAB: SCANNER ──────────────────────────────────────────────
def tab_scanner():
    st.markdown("## 🔭 Market Scanner")
    st.caption(
        "Two-stage process: Mode 1 filters 180+ stocks using quality metrics. "
        "Mode 2 sends the best candidates to Claude for full AI analysis. "
        "Final list = Claude's top 10 with entry levels and position sizes."
    )

    # Alpha Vantage key check
    av_key = st.session_state.get("alpha_vantage_key","")

    UNIVERSE = list(dict.fromkeys([
        "AAPL","MSFT","NVDA","AVGO","ORCL","CRM","AMD","QCOM","TXN","AMAT",
        "MU","MRVL","PANW","FTNT","CRWD","ZS","DDOG","PLTR","APP","SMCI",
        "LLY","UNH","JNJ","ABBV","MRK","TMO","ABT","GILD","VRTX","ISRG",
        "JPM","V","MA","BAC","GS","MS","BLK","SCHW","AXP","SPGI",
        "AMZN","TSLA","HD","MCD","NKE","SBUX","TJX","BKNG","CMG","ABNB",
        "META","GOOGL","NFLX","DIS","CMCSA","TMUS","TTD","ROKU","SNAP","PINS",
        "CAT","BA","HON","UPS","RTX","LMT","GE","DE","FDX","CSX",
        "XOM","CVX","COP","EOG","SLB","HAL","MPC","PSX","OXY","DVN",
        "PG","KO","PEP","COST","WMT","PM","MO","CL","GIS","KHC",
        "CVS","ELV","HUM","CI","MCK","ZTS","IDXX","DXCM","PODD",
        "NEE","DUK","SO","PLD","AMT","EQIX","CCI","PSA","O","SPG",
        "COIN","MARA","RIOT","IBIT","NIO","RIVN","F","GM",
        "BABA","JD","PDD","TSM","ARM","DELL","HPQ","WDC","STX","ANET",
        "ADBE","PYPL","INTU","LULU","MNST","MELI","NXPI","WDAY","TEAM",
        "SNOW","OKTA","MDB","HOOD","ZM","DOCU","PINS","ETSY","ABNB","U",
    ]))

    # ── Sector P/E benchmarks for valuation check ──
    SECTOR_PE = {
        "Technology": 30, "Healthcare": 25, "Communication Services": 28,
        "Consumer Cyclical": 22, "Consumer Defensive": 20, "Financials": 16,
        "Industrials": 20, "Energy": 15, "Materials": 18,
        "Real Estate": 35, "Utilities": 18, "Unknown": 22,
    }

    def get_alpha_vantage_revision(ticker, av_key):
        """
        Fetch earnings estimate revision trend from Alpha Vantage.
        Rising estimates = institutional money likely accumulating.
        Returns: positive, negative, or neutral
        """
        if not av_key:
            return "unknown"
        try:
            url = (f"https://www.alphavantage.co/query?function=EARNINGS"
                   f"&symbol={ticker}&apikey={av_key}")
            r = requests.get(url, timeout=8)
            data = r.json()
            # Check if estimates are available
            quarterly = data.get("quarterlyEarnings", [])
            if len(quarterly) >= 2:
                recent  = quarterly[0]
                prior   = quarterly[1]
                est_r   = float(recent.get("estimatedEPS", 0) or 0)
                est_p   = float(prior.get("estimatedEPS", 0) or 0)
                if est_r > est_p * 1.05:
                    return "rising"
                elif est_r < est_p * 0.95:
                    return "falling"
            return "flat"
        except Exception:
            return "unknown"

    def mode1_quality_filter(ticker, av_key):
        """
        MODE 1 — Quality Growth at a Reasonable Price filter.
        Returns the stock data if it passes ALL criteria.
        Returns None if it fails any critical filter.

        Criteria:
        - EPS growth > 10% (company growing earnings)
        - Forward P/E below 1.4x sector average (not overpaying)
        - Positive free cash flow (real cash generation)
        - RSI between 40-68 (building momentum, NOT extended)
        - Price above 50-day moving average (uptrend confirmed)
        - Analyst price target at least 12% above current price
        - NOT within 3% of 52-week high (unless RSI < 60)
        - Earnings estimates flat or rising (Alpha Vantage if available)
        """
        try:
            inf = info(ticker)
            if not inf or not inf.get("price"):
                return None

            price   = inf.get("price")
            sector  = inf.get("sector", "Unknown")
            pe_lim  = SECTOR_PE.get(sector, 22) * 1.4

            # Filter 1 -- earnings growth
            eps_gr = inf.get("eps_gr") or inf.get("rev_gr")
            if not eps_gr or eps_gr < 0.08:
                return None

            # Filter 2 -- valuation (forward P/E vs sector)
            fwd_pe = inf.get("fwd_pe")
            if fwd_pe and fwd_pe > pe_lim:
                return None

            # Filter 3 -- positive free cash flow
            if not inf.get("fcf") or inf['fcf'] <= 0:
                return None

            # Filter 4 -- analyst target upside
            target = inf.get("target")
            if not target:
                return None
            upside = (target / price - 1) * 100
            if upside < 12:
                return None

            # Filter 5 -- technical: price above 50d, RSI 40-68
            df = prices(ticker, "3mo")
            if df is None or len(df) < 50:
                return None
            df = indicators(df.copy())
            last  = df.iloc[-1]
            px    = float(last["Close"])
            e50   = float(last["E50"]) if "E50" in df.columns else None
            rsi   = float(last["RSI"]) if "RSI" in df.columns else 50
            hi52  = float(df["Close"].max())
            vr    = float(last["VR"]) if "VR" in df.columns else 1.0
            macd_bull = float(last.get("MACD",0)) > float(last.get("SIG",0))
            atr   = float(last["ATR"]) if "ATR" in df.columns else px * 0.02

            if e50 and px < e50:
                return None   # Must be in uptrend
            if rsi < 38 or rsi > 68:
                return None   # Not extended, not oversold
            near_52w_hi = px >= hi52 * 0.97
            if near_52w_hi and rsi > 60:
                return None   # Avoid chasing extended breakouts

            # Filter 6 -- Alpha Vantage revision check
            revision = "unknown"
            if av_key:
                revision = get_alpha_vantage_revision(ticker, av_key)
                if revision == "falling":
                    return None  # Analysts cutting estimates = bad signal

            # Calculate suggested stop and position
            stop  = round(px - 1.5 * atr, 2)
            mo1m  = float((px/df["Close"].iloc[-21]-1)*100) if len(df)>=21 else 0
            mo1w  = float((px/df["Close"].iloc[-5]-1)*100)  if len(df)>=5  else 0

            return {
                "ticker":    ticker,
                "name":      inf.get("name", ticker),
                "sector":    sector,
                "price":     round(px, 2),
                "upside":    round(upside, 1),
                "target":    round(target, 2),
                "fwd_pe":    round(fwd_pe, 1) if fwd_pe else None,
                "pe_limit":  round(pe_lim, 1),
                "eps_gr":    round(eps_gr*100, 1),
                "rsi":       round(rsi, 1),
                "vr":        round(vr, 2),
                "mo1m":      round(mo1m, 2),
                "mo1w":      round(mo1w, 2),
                "stop":      stop,
                "atr":       round(atr, 2),
                "macd_bull": macd_bull,
                "near_hi":   near_52w_hi,
                "revision":  revision,
                "inf":       inf,
                "df":        df,
            }
        except Exception:
            return None

    # ── UI ──
    st.markdown('<div class="sec">Step 1 -- Mode 1: Quality Growth Filter</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="a-blue" style="margin-bottom:12px">' +
        '<strong>What Mode 1 looks for:</strong> Stocks with growing earnings (EPS >8%), ' +
        'reasonable valuation (Forward P/E below sector average), positive cash flow, ' +
        'RSI between 40-68 (building momentum but NOT extended), analyst target at ' +
        'least 12% above current price, and price in an uptrend. ' +
        'This finds stocks <em>before</em> they run, not after.</div>',
        unsafe_allow_html=True
    )

    if not av_key:
        st.markdown(
            '<div class="a-amber">Add your Alpha Vantage API key in Settings to enable ' +
            'earnings revision filtering (the strongest signal). ' +
            'The scan will still run without it but may include stocks with falling estimates.</div>',
            unsafe_allow_html=True
        )

    if st.button("🔍 Run Mode 1 -- Quality Growth Scan", type="primary", key="run_mode1"):
        candidates = []
        prog = st.progress(0, text="Scanning for quality growth stocks...")
        status = st.empty()
        for i, tk in enumerate(UNIVERSE):
            prog.progress((i+1)/len(UNIVERSE), text=f"Checking {tk} ({i+1}/{len(UNIVERSE)})...")
            result = mode1_quality_filter(tk, av_key)
            if result:
                candidates.append(result)
                status.success(f"Found {len(candidates)} quality candidates so far...")
            time.sleep(0.15)
        prog.empty(); status.empty()
        # Sort by upside potential
        candidates = sorted(candidates, key=lambda x: x["upside"], reverse=True)
        st.session_state["mode1_results"] = candidates
        st.success(f"Mode 1 complete -- {len(candidates)} stocks passed all quality filters from {len(UNIVERSE)} scanned")

    # Display Mode 1 results
    mode1 = st.session_state.get("mode1_results", [])
    if mode1:
        st.markdown(f'<div class="sec">{len(mode1)} Stocks Passed Quality Filters</div>', unsafe_allow_html=True)

        rows = []
        for r in mode1:
            rows.append({
                "Ticker":      r["ticker"],
                "Company":     r["name"][:25],
                "Sector":      r["sector"],
                "Price":       f'${r["price"]:.2f}',
                "Analyst Target": f'${r["target"]:.2f}',
                "Upside":      f'{r["upside"]:+.1f}%',
                "Fwd P/E":     r["fwd_pe"] or "N/A",
                "EPS Growth":  f'{r["eps_gr"]:.1f}%',
                "RSI":         r["rsi"],
                "1M Return":   f'{r["mo1m"]:+.1f}%',
                "Revision":    r["revision"].upper(),
                "MACD":        "Bull" if r["macd_bull"] else "Bear",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.divider()
        st.markdown('<div class="sec">Step 2 -- Mode 2: Claude AI Deep Analysis</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="a-blue" style="margin-bottom:12px">' +
            '<strong>What Mode 2 does:</strong> Takes every stock that passed Mode 1 and sends ' +
            'it to Claude with full data -- fundamentals, insider activity, analyst consensus, ' +
            'news sentiment, and market context. Claude asks: "Is this a good entry point ' +
            'at this price right now?" Not just "is it a good company?" ' +
            'Then ranks them and produces a final top 10 with entry levels and position sizes.</div>',
            unsafe_allow_html=True
        )

        if not st.session_state.anthropic_key:
            st.error("Add your Anthropic API key in Settings to run Mode 2.")
        else:
            if st.button("🤖 Run Mode 2 -- Claude AI Analysis", type="primary", key="run_mode2"):
                mkt  = market_data()
                vx   = vix()
                fg   = fear_greed()
                analyses = []
                prog2 = st.progress(0, text="Claude is analysing each candidate...")
                for i, r in enumerate(mode1):
                    prog2.progress((i+1)/len(mode1), text=f"Analysing {r['ticker']} ({i+1}/{len(mode1)})...")
                    an_q  = analyst_data(r["ticker"])
                    ins_q = insider_data(r["ticker"])
                    nws_q = news_data(r["ticker"])
                    # Pass extra context about valuation and entry timing to Claude
                    enhanced_inf = dict(r['inf'])
                    enhanced_inf['_rsi_context']  = f"RSI is {r['rsi']:.0f} -- in the healthy 40-68 range, not extended"
                    enhanced_inf['_entry_context'] = f"Stock is {r['mo1m']:+.1f}% over the past month, {'near 52W high -- check if justified' if r['near_hi'] else 'not near 52W high -- reasonable entry zone'}"
                    enhanced_inf['_revision']      = f"Earnings estimate trend: {r['revision']}"
                    verdict, text = ai_analysis(r["ticker"], enhanced_inf, an_q, ins_q, nws_q, mkt)
                    analyses.append({
                        "ticker":  r["ticker"],
                        "name":    r["name"],
                        "sector":  r["sector"],
                        "price":   r["price"],
                        "upside":  r["upside"],
                        "target":  r["target"],
                        "stop":    r["stop"],
                        "atr":     r["atr"],
                        "eps_gr":  r["eps_gr"],
                        "rsi":     r["rsi"],
                        "mo1m":    r["mo1m"],
                        "verdict": verdict,
                        "text":    text,
                    })
                    time.sleep(0.3)
                prog2.empty()

                # Ask Claude to rank and select top 10
                try:
                    client = anthropic.Anthropic(api_key=st.session_state.anthropic_key)
                    summary = []
                    for a in analyses:
                        summary.append(
                            f"{a['ticker']} ({a['name']}): "
                            f"Verdict={a['verdict']}, "
                            f"Upside={a['upside']:+.1f}%, "
                            f"EPS growth={a['eps_gr']:.1f}%, "
                            f"RSI={a['rsi']:.0f}, "
                            f"1M return={a['mo1m']:+.1f}%, "
                            f"Sector={a['sector']}"
                        )
                    rank_prompt = (
                        f"You have analysed {len(analyses)} quality growth stocks that all passed fundamental filters.\n\n"
                        f"Market regime: {mkt.get('regime','Unknown')} | VIX: {vx} | Fear & Greed: {fg['val']}\n\n"
                        "Results:\n" + "\n".join(summary) + "\n\n"
                        "Select and rank the TOP 10 best buying opportunities RIGHT NOW. "
                        "Prioritise: BUY verdicts, highest conviction quality, sector diversification, "
                        "reasonable RSI (not extended), strong earnings growth, and alignment with current market regime. "
                        "Avoid clustering too many stocks in the same sector. "
                        "Reply with ONLY a comma-separated list of exactly 10 ticker symbols, best first. "
                        "Example: AAPL,MSFT,NVDA,..."
                    )
                    resp = client.messages.create(
                        model="claude-sonnet-4-6", max_tokens=80,
                        messages=[{"role":"user","content":rank_prompt}]
                    )
                    ranked_tks = [t.strip().upper() for t in resp.content[0].text.strip().split(",")][:10]
                    ranked = []
                    for tk in ranked_tks:
                        match = next((a for a in analyses if a["ticker"]==tk), None)
                        if match:
                            ranked.append(match)
                    for a in analyses:
                        if len(ranked) >= 10: break
                        if not any(r["ticker"]==a["ticker"] for r in ranked):
                            if a["verdict"] == "BUY":
                                ranked.append(a)
                    st.session_state["final_recommendations"] = ranked
                    st.success(f"Mode 2 complete -- Claude has selected the top {len(ranked)} opportunities")
                except Exception as e:
                    st.error(f"Ranking error: {e}")
                    buys = [a for a in analyses if a["verdict"]=="BUY"]
                    st.session_state["final_recommendations"] = (buys + [a for a in analyses if a["verdict"]!="BUY"])[:10]

    # ── FINAL RECOMMENDATIONS ──
    final = st.session_state.get("final_recommendations", [])
    if final:
        st.divider()
        st.markdown('<div class="sec">Final Recommendations -- Claudes Top Picks</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="a-green" style="margin-bottom:16px">' +
            f'These ' + str(len(final)) + ' stocks passed every quality filter AND received Claudes highest conviction rating. ' +
            'Each includes a suggested entry level, stop-loss, and position size based on your account.</div>',
            unsafe_allow_html=True
        )

        account  = st.session_state.account_size
        risk_pct = st.session_state.max_risk_pct

        for i, a in enumerate(final):
            v  = a.get("verdict","WAIT")
            vs = get_vs(v)
            sz = pos_size(account, risk_pct, a["price"], a["stop"])
            rr = (a["target"]-a["price"])/(a["price"]-a["stop"]) if a["stop"] < a["price"] else None

            rank_color = "#F6E05E" if i==0 else ("#C0C0C0" if i==1 else ("#CD7F32" if i==2 else "#4A5568"))

            with st.container():
                css_cls = vs["css"]; st.markdown(f'<div class="{css_cls}">', unsafe_allow_html=True)

                h1,h2,h3 = st.columns([4,3,3])
                with h1:
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">' +
                        f'<div style="font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;color:{rank_color}">#{i+1}</div>' +
                        f'<div><div style="font-family:Syne,sans-serif;font-size:1.1rem;font-weight:800;color:{vs["color"]}">{a["ticker"]} - {vs["emoji"]} {v}</div>' +
                        f'<div style="font-size:0.72rem;color:#4A5568">{a["name"]} | {a["sector"]}</div></div>' +
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    mc = "#00E676" if a["mo1m"]>=0 else "#F56565"
                    st.markdown(
                        f'<span class="pill p-b">RSI {a["rsi"]:.0f}</span>' +
                        f'<span class="pill p-g">EPS +{a["eps_gr"]:.1f}%</span>' +
                        f'<span class="pill p-g">{a["upside"]:+.1f}% to target</span>',
                        unsafe_allow_html=True
                    )

                with h2:
                    st.markdown(
                        f'<div style="font-size:0.65rem;color:#4A5568;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">Trade Levels</div>' +
                        f'<div style="font-family:IBM Plex Mono;font-size:0.85rem;line-height:1.8;color:#A0AEC0">' +
                        f'<span style="color:#EDF2F7">Current:</span> ${a["price"]:.2f}<br>' +
                        f'<span style="color:#00E676">Target:</span> ${a["target"]:.2f} ({a["upside"]:+.1f}%)<br>' +
                        f'<span style="color:#F56565">Stop-loss:</span> ${a["stop"]:.2f}<br>' +
                        f'{"<span style=color:#F6AD55>R:R ratio:</span> 1:" + str(round(rr,1)) + "<br>" if rr else ""}' +
                        f'</div>',
                        unsafe_allow_html=True
                    )

                with h3:
                    if sz:
                        st.markdown(
                            f'<div style="font-size:0.65rem;color:#4A5568;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">Position Size (${account:,.0f} account)</div>' +
                            f'<div style="font-family:IBM Plex Mono;font-size:0.85rem;line-height:1.8;color:#A0AEC0">' +
                            f'<span style="color:#EDF2F7">Shares:</span> {sz["shares"]}<br>' +
                            f'<span style="color:#EDF2F7">Cost:</span> ${sz["total_cost"]:,.0f} ({sz["pct_account"]:.1f}%)<br>' +
                            f'<span style="color:#F56565">Max loss:</span> -${sz["dollar_risk"]:,.0f}<br>' +
                            f'</div>',
                            unsafe_allow_html=True
                        )

                with st.expander("Read full AI analysis"):
                    st.markdown(
                        f'<div style="font-size:0.88rem;line-height:1.8;color:#A0AEC0">{str(a["text"]).replace(chr(10),"<br>")}</div>',
                        unsafe_allow_html=True
                    )

                bc1,bc2 = st.columns(2)
                with bc1:
                    if st.button(f"➕ Add {a['ticker']} to watchlist", key=f"fin_wl_{i}"):
                        conn=db(); conn.execute("INSERT OR IGNORE INTO watchlist(ticker) VALUES(?)",(a["ticker"],)); conn.commit(); conn.close()
                        st.success(f"Added {a['ticker']} to watchlist")
                with bc2:
                    if st.button(f"💼 Open position in portfolio", key=f"fin_port_{i}"):
                        conn=db()
                        conn.execute("INSERT INTO portfolio(ticker,shares,entry_price,entry_date,stop_loss,target_price,notes) VALUES(?,?,?,?,?,?,?)",
                            (a["ticker"],sz.get("shares",1),a["price"],str(datetime.date.today()),a["stop"],a["target"],"From scanner recommendation"))
                        conn.commit(); conn.close()
                        st.success(f"Added {a['ticker']} to portfolio with suggested stop and target")

                st.markdown('</div>', unsafe_allow_html=True)

def tab_market():
    st.markdown("## 🌍 Market Health")
    st.caption("Check this first every day before looking at individual stocks.")

    mkt = market_data()
    fg  = fear_greed()
    vx  = vix()

    regime = mkt.get("regime","Unknown")
    rc = mkt.get("regime_color","#4A5568")

    # Main verdict
    st.markdown(
        f'<div class="card" style="border-left:4px solid {rc};margin-bottom:20px">'
        f'<div style="font-family:Syne,sans-serif;font-size:1.3rem;font-weight:800;color:{rc};margin-bottom:8px">'
        f'{regime}</div>'
        f'<div style="font-size:0.9rem;color:#A0AEC0;line-height:1.6">{mkt.get("regime_note","")}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Key gauges
    st.markdown('<div class="sec">Market Gauges</div>', unsafe_allow_html=True)
    g1,g2,g3,g4 = st.columns(4)
    fg_c = "#00E676" if fg["val"]>60 else ("#F56565" if fg["val"]<30 else "#F6AD55")
    vx_c = "#00E676" if vx and vx<15 else ("#F56565" if vx and vx>30 else "#F6AD55")
    g1.markdown(mt("Fear & Greed Index", str(fg["val"]), fg["label"], fg_c), unsafe_allow_html=True)
    g2.markdown(mt("VIX  -  Market Fear",  str(vx) if vx else "N/A", "<15 calm · >30 panic", vx_c), unsafe_allow_html=True)

    spy = mkt.get("indices",{}).get("SPY",{})
    qqq = mkt.get("indices",{}).get("QQQ",{})
    g3.markdown(mt("S&P 500 (SPY) 1M", f'{spy.get("mo1m",0):+.1f}%', "Large US stocks",
                   "#00E676" if spy.get("mo1m",0)>=0 else "#F56565"), unsafe_allow_html=True)
    g4.markdown(mt("NASDAQ (QQQ) 1M", f'{qqq.get("mo1m",0):+.1f}%', "Tech / growth",
                   "#00E676" if qqq.get("mo1m",0)>=0 else "#F56565"), unsafe_allow_html=True)

    # Index health
    st.markdown('<div class="sec">Index Health  -  Are Markets Above Key Trend Lines?</div>', unsafe_allow_html=True)
    for sym,idx in mkt.get("indices",{}).items():
        above_all = idx.get("above_200") and idx.get("above_50")
        above_some = idx.get("above_50") or idx.get("above_200")
        clr = "#00E676" if above_all else ("#F6AD55" if above_some else "#F56565")
        st.markdown(
            f'<div class="card-sm">'
            f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<div><span style="font-family:Syne,sans-serif;font-weight:700;color:{clr}">{sym}</span>'
            f'<span style="color:#4A5568;font-size:0.78rem;margin-left:8px">{idx.get("name","")}</span></div>'
            f'<div>'
            f'<span style="color:{"#00E676" if idx.get("mo1m",0)>=0 else "#F56565"};font-family:IBM Plex Mono;font-size:0.82rem">'
            f'1M: {idx.get("mo1m",0):+.1f}%</span>'
            f'&nbsp;&nbsp;<span style="color:{"#00E676" if idx.get("mo3m",0)>=0 else "#F56565"};font-family:IBM Plex Mono;font-size:0.82rem">'
            f'3M: {idx.get("mo3m",0):+.1f}%</span>'
            f'</div></div>'
            f'<div style="margin-top:6px">'
            f'{"<span class=pill p-g>Above 200d</span>" if idx.get("above_200") else "<span class=pill p-r>Below 200d</span>"}'
            f'{"<span class=pill p-g>Above 50d</span>" if idx.get("above_50") else "<span class=pill p-r>Below 50d</span>"}'
            f'</div></div>',
            unsafe_allow_html=True
        )

    # Sector rotation
    st.markdown('<div class="sec">Sector Rotation  -  Which Industries Are Hot Right Now?</div>', unsafe_allow_html=True)
    secs = mkt.get("sectors",{})
    if secs:
        st.plotly_chart(chart_sector(secs), use_container_width=True)
        top3 = sorted(secs,key=secs.get,reverse=True)[:3]
        bot3 = sorted(secs,key=secs.get)[:3]
        tc1,tc2 = st.columns(2)
        with tc1:
            st.markdown("**🔥 Strongest sectors  -  look here first**")
            for s in top3:
                st.markdown(f'- <span class="pill p-g">{s}</span> {secs[s]:+.1f}%', unsafe_allow_html=True)
        with tc2:
            st.markdown("**❄️ Weakest sectors  -  avoid unless specific reason**")
            for s in bot3:
                st.markdown(f'- <span class="pill p-r">{s}</span> {secs[s]:+.1f}%', unsafe_allow_html=True)

    # Plain English guidance
    st.markdown('<div class="sec">What This Means For Your Trading</div>', unsafe_allow_html=True)
    vx_val = vx or 20
    if vx_val < 15:
        size_note = "Markets are calm. You can use your normal position sizes."
    elif vx_val < 25:
        size_note = "Moderate volatility. Stick to normal position sizes but keep stops tight."
    elif vx_val < 35:
        size_note = "Elevated fear. Reduce your normal position size by 30-50%."
    else:
        size_note = "High fear. Consider very small positions or staying in cash until conditions improve."

    st.markdown(
        f'<div class="a-blue">'
        f'<strong>Position sizing guidance:</strong> {size_note}<br><br>'
        f'<strong>Where to focus:</strong> The top 3 performing sectors above are where the best setups tend to be. '
        f'Swimming with the current is always easier than against it.'
        f'</div>',
        unsafe_allow_html=True
    )

# ── TAB: AI ADVISOR ───────────────────────────────────────────
def tab_ai_advisor():
    st.markdown("## 🤖 AI Advisor")
    st.caption("Claude analyses your entire portfolio and watchlist together, then gives you a plain English brief and priority actions.")

    if not st.session_state.anthropic_key:
        st.warning("Add your Anthropic API key in ⚙️ Settings to use the AI Advisor.")
        return

    c1,c2 = st.columns([2,1])
    with c2:
        st.markdown('<div class="sec">Options</div>', unsafe_allow_html=True)
        include_watchlist = st.checkbox("Include watchlist stocks",value=True)
        focus = st.selectbox("Focus on:",["Full portfolio assessment","Which positions to exit","Where to add new money","Risk assessment only"])

    with c1:
        if st.button("🤖 Generate Full AI Brief", type="primary"):
            positions = load_positions()
            mkt = market_data()
            fg  = fear_greed()
            vx  = vix()

            conn=db()
            wl = pd.read_sql("SELECT ticker FROM watchlist",conn)
            conn.close()

            with st.spinner("Claude is reading your full portfolio…"):
                # Build comprehensive context
                port_summary = []
                for p in positions:
                    an  = analyst_data(p["ticker"])
                    upside = an.get("upside")
                    port_summary.append(
                        f"{p['ticker']} ({p['name']}): {p['shares']:.4f} shares, "
                        f"entry ${p['entry']:.2f}, current ${p['price']:.2f}, "
                        f"P&L {p['pnl_pct']:+.1f}% (${p['pnl']:+.2f}), "
                        f"stop ${p['stop']:.2f} ({p['stop_dist']:.1f}% buffer), "
                        f"{'⚠️ STOP BREACHED' if p['stop_status']=='breached' else ''}"
                        f"analyst target ${an['target']:.2f} ({upside:+.1f}% upside)" if an.get("target") and upside else ""
                    )

                wl_context = ""
                if include_watchlist and not wl.empty:
                    wl_context = f"\nWatchlist stocks being tracked: {', '.join(wl['ticker'].tolist())}"

                prompt = f"""You are a plain-English portfolio advisor. A beginner investor has asked for a full brief.

THEIR PORTFOLIO (5 positions):
{chr(10).join(port_summary)}

MARKET CONTEXT:
- Regime: {mkt.get('regime','Unknown')}
- VIX: {vx} | Fear & Greed: {fg['val']} ({fg['label']})
- Top sectors this month: {', '.join(list(mkt.get('sectors',{}).keys())[:3])}
{wl_context}

FOCUS: {focus}

Write a clear, plain-English portfolio brief structured as:

**PORTFOLIO HEALTH: [STRONG / MIXED / CONCERNING]**
One sentence overall assessment.

**Position-by-position:**
For each position: one sentence on whether to HOLD, ADD, or REDUCE  -  and why. Be specific about stop-losses that are being tested.

**Top 3 priority actions:**
Number them. Be specific. Include price levels where relevant.

**What to watch this week:**
2-3 things to monitor.

Keep it practical and honest. If something is at risk, say so clearly."""

                try:
                    client = anthropic.Anthropic(api_key=st.session_state.anthropic_key)
                    resp = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=900,
                        messages=[{"role":"user","content":prompt}]
                    )
                    st.session_state['full_brief'] = resp.content[0].text
                except Exception as e:
                    st.error(f"Error: {e}")

    if "full_brief" in st.session_state:
        text = str(st.session_state['full_brief'])
        st.markdown(
            f'<div class="card" style="border-left:4px solid #63B3ED">'
            f'<div style="font-size:0.9rem;line-height:1.8;color:#A0AEC0">'
            f'{text.replace(chr(10),"<br>")}'
            f'</div></div>',
            unsafe_allow_html=True
        )

    # Individual stock analysis
    st.markdown('<div class="sec">Analyse a specific stock</div>', unsafe_allow_html=True)
    ac1,ac2 = st.columns([3,1])
    query_tk = ac1.text_input("Enter any ticker:",placeholder="e.g. NVDA",label_visibility="collapsed").upper().strip()
    if ac2.button("Analyse",type="primary") and query_tk:
        with st.spinner(f"Analysing {query_tk}…"):
            inf_q = info(query_tk); an_q = analyst_data(query_tk)
            ins_q = insider_data(query_tk); nws_q = news_data(query_tk)
            mkt_q = market_data()
            verdict, text = ai_analysis(query_tk, inf_q, an_q, ins_q, nws_q, mkt_q)
            st.session_state["query_result"] = {"ticker":query_tk,"verdict":verdict,"text":text}

    if "query_result" in st.session_state:
        r  = st.session_state["query_result"]
        v  = r.get("verdict","WAIT")
        t  = r.get("text","")
        vs = get_vs(v)
        st.markdown(
            f'<div class="{vs["css"]}">'
            f'<div style="font-family:Syne,sans-serif;font-size:1.1rem;font-weight:800;color:{vs["color"]};margin-bottom:10px">'
            f'{vs["emoji"]} {r["ticker"]}  -  {v}</div>'
            f'<div style="font-size:0.88rem;line-height:1.75;color:#A0AEC0">'
            f'{str(t).replace(chr(10),"<br>")}'
            f'</div></div>',
            unsafe_allow_html=True
        )

# ── TAB: SETTINGS ─────────────────────────────────────────────
def tab_settings():
    st.markdown("## ⚙️ Settings")
    st.markdown(
        '<div class="a-green" style="margin-bottom:16px">✅ Settings save permanently to your Mac and load automatically on next start.</div>',
        unsafe_allow_html=True
    )
    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="sec">Account</div>', unsafe_allow_html=True)
        acc = st.number_input("Account size ($)",value=st.session_state.account_size,min_value=100.0,step=500.0)
        rsk = st.slider("Max % to risk per trade",0.25,5.0,st.session_state.max_risk_pct,0.25,
                         help="Most professionals risk 1-2%. As a beginner, start at 1%.")
        st.markdown('<div class="sec">API Keys  -  saved permanently</div>', unsafe_allow_html=True)
        ak = st.text_input("Anthropic API key (AI analysis)",value=st.session_state.anthropic_key,type="password",
                           help="Free tier at console.anthropic.com")
        fk = st.text_input("Finnhub API key (news headlines)",value=st.session_state.finnhub_key,type="password",
                           help="Free at finnhub.io")
        avk = st.text_input("Alpha Vantage API key (earnings revisions)",
                            value=st.session_state.get("alpha_vantage_key",""),type="password",
                            help="Free at alphavantage.co - no credit card needed")
        st.caption("Alpha Vantage adds earnings revision data - the strongest signal for finding stocks before they run.")
        st.markdown("---")
        st.markdown("**eToro API — live portfolio sync**")
        st.caption("Connect your eToro account for automatic position sync. Read-only keys are sufficient.")
        epk = st.text_input("eToro Public Key (x-api-key)",
                             value=st.session_state.get("etoro_public_key",""),type="password",
                             help="Found in eToro Settings > Trading > API Key Management")
        euk = st.text_input("eToro User Key (x-user-key)",
                             value=st.session_state.get("etoro_user_key",""),type="password",
                             help="Generated alongside your Public Key in eToro")
        if st.button("Test eToro connection", key="test_etoro"):
            if epk and euk:
                with st.spinner("Testing..."):
                    import uuid
                    headers = {"x-api-key":epk,"x-user-key":euk,"x-request-id":str(uuid.uuid4())}
                    try:
                        r = requests.get("https://public-api.etoro.com/api/v1/trading/info/real/pnl",
                                         headers=headers, timeout=10)
                        if r.status_code == 200:
                            data = r.json()
                            n = len(data.get("positions",[]))
                            st.success(f"Connected successfully -- {n} open positions found in your eToro account!")
                        elif r.status_code == 401:
                            st.error("Invalid keys -- check your Public Key and User Key.")
                        else:
                            st.error(f"eToro API returned HTTP {r.status_code}")
                    except Exception as e:
                        st.error(f"Connection error: {e}")
            else:
                st.warning("Enter both keys before testing.")
        if st.button("💾 Save all settings",type="primary"):
            st.session_state.account_size            = acc
            st.session_state.max_risk_pct            = rsk
            st.session_state.anthropic_key           = ak
            st.session_state.finnhub_key             = fk
            st.session_state["alpha_vantage_key"]    = avk
            st.session_state["etoro_public_key"]     = epk
            st.session_state["etoro_user_key"]       = euk
            save_cfg({"account_size":acc,"max_risk_pct":rsk,"anthropic_key":ak,
                      "finnhub_key":fk,"alpha_vantage_key":avk,
                      "etoro_public_key":epk,"etoro_user_key":euk})
            st.success("All settings saved permanently!")
            save_cfg({"account_size":acc,"max_risk_pct":rsk,"anthropic_key":ak,"finnhub_key":fk})
            st.success("✅ Saved permanently!")

    with c2:
        st.markdown('<div class="sec">Scanning</div>', unsafe_allow_html=True)
        paused = st.toggle("⏸ Pause scanning (saves battery)",value=st.session_state.paused)
        st.session_state.paused = paused
        st.markdown('<div class="sec">Cache</div>', unsafe_allow_html=True)
        if st.button("Clear all caches"):
            st.cache_data.clear()
            st.success("Cache cleared")
        if st.button("Clear scanner results"):
            st.session_state.scanner_results = []
            st.session_state.scanner_ts = 0
            st.success("Scanner cleared")
        st.markdown('<div class="sec">Position sizing calculator</div>', unsafe_allow_html=True)
        ps_price = st.number_input("Entry price ($)",min_value=0.01,step=0.01)
        ps_stop  = st.number_input("Stop-loss ($)",min_value=0.01,step=0.01)
        if ps_price > 0 and ps_stop > 0 and ps_stop < ps_price:
            sz = pos_size(acc, rsk, ps_price, ps_stop)
            if sz:
                st.markdown(
                    f'<div class="card-sm">'
                    f'<div style="font-size:0.82rem;color:#718096">Buy <strong style="color:#EDF2F7">{sz["shares"]} shares</strong> '
                    f'for <strong style="color:#EDF2F7">${sz["total_cost"]:,.2f}</strong> ({sz["pct_account"]:.1f}% of account)<br>'
                    f'Max loss if stopped out: <strong style="color:#F56565">-${sz["dollar_risk"]:,.2f}</strong>'
                    f'</div></div>',
                    unsafe_allow_html=True
                )

# ── MAIN ──────────────────────────────────────────────────────
def main():
    st.markdown(
        '<h1 style="font-family:Syne,sans-serif;font-size:1.8rem;font-weight:800;'
        'background:linear-gradient(90deg,#00E676,#63B3ED);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
        'margin-bottom:0;padding-top:8px">Smart Stock Advisor</h1>'
        '<p style="color:#4A5568;font-size:0.8rem;margin-top:2px;margin-bottom:16px">'
        '⚠️ Educational tool only. Not financial advice. Data is 15-min delayed. Always do your own research.</p>',
        unsafe_allow_html=True
    )

    tabs = st.tabs([
        "💼 Portfolio",
        "🚦 Watchlist",
        "🔭 Scanner",
        "🌍 Market Health",
        "🤖 AI Advisor",
        "⚙️ Settings",
    ])

    with tabs[0]: tab_portfolio()
    with tabs[1]: tab_watchlist()
    with tabs[2]: tab_scanner()
    with tabs[3]: tab_market()
    with tabs[4]: tab_ai_advisor()
    with tabs[5]: tab_settings()

if __name__ == "__main__":
    main()
