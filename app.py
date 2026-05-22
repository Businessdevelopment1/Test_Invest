"""
Mark Trading Dashboard — Sci-Fi Dark Edition
Live portfolio tracker for 17 US stock positions.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pham's Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Portfolio snapshot (May 15, 2026) ─────────────────────────────────────────
PORTFOLIO = {
    # shares = actual count from DIME brokerage; cost_basis = total invested; snapshot_px = fallback price
    "META":  {"shares": 1.7958170, "cost_basis": 1088.74, "snapshot_px":  607.38, "sector": "Technology"},
    "AMZN":  {"shares": 3.9972687, "cost_basis":  872.70, "snapshot_px":  268.46, "sector": "Technology"},
    "MSFT":  {"shares": 2.5305418, "cost_basis":  987.70, "snapshot_px":  419.09, "sector": "Technology"},
    "GOOGL": {"shares": 2.0012137, "cost_basis":  335.13, "snapshot_px":  387.66, "sector": "Technology"},
    "NVDA":  {"shares": 3.1299373, "cost_basis":  464.71, "snapshot_px":  219.51, "sector": "Technology"},
    "LLY":   {"shares": 0.7308499, "cost_basis":  520.22, "snapshot_px": 1041.65, "sector": "Healthcare"},
    "AMD":   {"shares": 1.1069433, "cost_basis":  153.75, "snapshot_px":  449.59, "sector": "Technology"},
    "VOO":   {"shares": 0.6835977, "cost_basis":  428.84, "snapshot_px":  682.84, "sector": "ETF"},
    "SGOL":  {"shares": 9.0910788, "cost_basis":  399.36, "snapshot_px":   43.24, "sector": "Commodity"},
    "NFLX":  {"shares": 3.0782325, "cost_basis":  252.63, "snapshot_px":   89.30, "sector": "Technology"},
    "TSM":   {"shares": 0.5861632, "cost_basis":  199.68, "snapshot_px":  407.15, "sector": "Technology"},
    "QQQ":   {"shares": 0.2956201, "cost_basis":  152.43, "snapshot_px":  714.51, "sector": "ETF"},
    "AVGO":  {"shares": 0.4599534, "cost_basis":  158.66, "snapshot_px":  414.57, "sector": "Technology"},
    "SOFI":  {"shares":11.0710855, "cost_basis":  230.50, "snapshot_px":   15.65, "sector": "Finance"},
    "MARA":  {"shares": 8.9466601, "cost_basis":  182.83, "snapshot_px":   13.55, "sector": "Technology"},
    "ORCL":  {"shares": 0.4044665, "cost_basis":  113.63, "snapshot_px":  189.77, "sector": "Technology"},
    "DUOL":  {"shares": 0.6692898, "cost_basis":  226.24, "snapshot_px":  105.64, "sector": "Technology"},
}
TICKERS = list(PORTFOLIO.keys())

# ── Colour palette ────────────────────────────────────────────────────────────
CYAN   = "#00d4ff"
CYAN2  = "#00fff0"
GREEN  = "#00ff88"
RED    = "#ff3366"
YELLOW = "#ffd700"
BG     = "#020b18"
CARD   = "#041525"
BORDER = "#0a3a5a"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700&family=Rajdhani:wght@400;500;600&display=swap');

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main {{
    background: {BG} !important;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(0,60,120,0.15) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(0,100,180,0.10) 0%, transparent 50%);
}}
[data-testid="stHeader"]  {{ background: {BG} !important; }}
[data-testid="stSidebar"] {{ background: #010e1a !important; }}
* {{ font-family: 'Rajdhani', sans-serif; }}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer, [data-testid="stToolbar"] {{ visibility: hidden; }}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 4px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {CYAN}44; border-radius: 2px; }}

/* ── Dashboard title bar ── */
.dash-header {{
    text-align: center;
    padding: 18px 0 6px;
    border-bottom: 1px solid {CYAN}33;
    margin-bottom: 18px;
}}
.dash-title {{
    font-family: 'Orbitron', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: {CYAN};
    text-shadow: 0 0 20px {CYAN}88, 0 0 40px {CYAN}44;
    letter-spacing: 0.12em;
    margin: 0;
}}
.dash-subtitle {{
    font-size: 0.78rem;
    color: {CYAN}99;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    margin-top: 4px;
}}

/* ── KPI cards ── */
.kpi-card {{
    background: linear-gradient(135deg, {CARD} 0%, #031e35 100%);
    border: 1px solid {CYAN}44;
    border-top: 2px solid {CYAN}cc;
    border-radius: 6px;
    padding: 16px 14px;
    text-align: center;
    position: relative;
    box-shadow: 0 0 18px {CYAN}18, inset 0 0 20px rgba(0,212,255,0.03);
    margin-bottom: 2px;
}}
.kpi-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 10%; right: 10%;
    height: 1px;
    background: linear-gradient(90deg, transparent, {CYAN}88, transparent);
}}
.kpi-label {{
    font-size: 0.65rem;
    color: {CYAN}99;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-family: 'Orbitron', sans-serif;
}}
.kpi-value {{
    font-size: 1.65rem;
    font-weight: 700;
    margin: 6px 0 3px;
    font-family: 'Orbitron', sans-serif;
    line-height: 1;
}}
.kpi-sub {{ font-size: 0.78rem; color: #6699bb; }}

/* ── Colours ── */
.cyan   {{ color: {CYAN};   text-shadow: 0 0 8px {CYAN}88; }}
.green  {{ color: {GREEN};  text-shadow: 0 0 8px {GREEN}66; }}
.red    {{ color: {RED};    text-shadow: 0 0 8px {RED}66; }}
.yellow {{ color: {YELLOW}; text-shadow: 0 0 8px {YELLOW}66; }}

/* ── Section headers ── */
.section-title {{
    font-family: 'Orbitron', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.2em;
    color: {CYAN}cc;
    text-transform: uppercase;
    padding: 6px 0 6px 10px;
    border-left: 3px solid {CYAN};
    margin: 14px 0 10px;
    background: linear-gradient(90deg, {CYAN}0a, transparent);
}}

/* ── Alert banners ── */
.alert-crit {{
    background: linear-gradient(90deg, {RED}18, transparent);
    border: 1px solid {RED}55;
    border-left: 3px solid {RED};
    border-radius: 4px;
    padding: 10px 14px;
    margin: 4px 0;
    font-size: 0.88rem;
    color: #ffaaaa;
    box-shadow: 0 0 12px {RED}22;
}}
.alert-warn {{
    background: linear-gradient(90deg, {YELLOW}18, transparent);
    border: 1px solid {YELLOW}44;
    border-left: 3px solid {YELLOW};
    border-radius: 4px;
    padding: 10px 14px;
    margin: 4px 0;
    font-size: 0.88rem;
    color: #ffe08a;
    box-shadow: 0 0 12px {YELLOW}22;
}}

/* ── News cards ── */
.news-card {{
    background: linear-gradient(90deg, {CYAN}08, transparent);
    border: 1px solid {CYAN}22;
    border-left: 3px solid {CYAN};
    border-radius: 0 6px 6px 0;
    padding: 10px 14px;
    margin: 5px 0;
    transition: border-color 0.2s;
}}
.news-card:hover {{ border-color: {CYAN}88; }}
.news-card a {{ color: {CYAN}cc; text-decoration: none; font-size: 0.87rem; line-height: 1.45; }}
.news-card a:hover {{ color: {CYAN}; }}
.news-meta {{ font-size: 0.68rem; color: #336688; margin-top: 4px; letter-spacing: 0.05em; }}

/* ── Mark bubble ── */
.mark-bubble {{
    background: linear-gradient(135deg, #031525 0%, #020f1e 100%);
    border: 1px solid {CYAN}33;
    border-left: 3px solid {CYAN};
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 0.91rem;
    line-height: 1.6;
    white-space: pre-wrap;
    box-shadow: 0 0 20px {CYAN}0f;
    color: #b0d8f0;
}}

/* ── Dataframe overrides ── */
[data-testid="stDataFrame"] {{
    border: 1px solid {CYAN}33 !important;
    border-radius: 6px;
}}
[data-testid="stDataFrame"] th {{
    background: #031e35 !important;
    color: {CYAN} !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.12em !important;
}}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] {{
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.15em !important;
    color: {CYAN}88 !important;
    padding: 8px 16px !important;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color: {CYAN} !important;
    border-bottom: 2px solid {CYAN} !important;
}}

/* ── Buttons ── */
[data-testid="stButton"] button {{
    background: transparent !important;
    border: 1px solid {CYAN}66 !important;
    color: {CYAN} !important;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.1em !important;
    border-radius: 4px !important;
    transition: all 0.2s !important;
}}
[data-testid="stButton"] button:hover {{
    background: {CYAN}18 !important;
    border-color: {CYAN} !important;
    box-shadow: 0 0 12px {CYAN}44 !important;
}}

/* ── Selectbox / radio ── */
[data-testid="stSelectbox"] label,
[data-testid="stRadio"] label {{
    color: {CYAN}99 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
}}

/* ── Spinner ── */
[data-testid="stSpinner"] {{ color: {CYAN} !important; }}

/* ── Divider line ── */
.glow-line {{
    height: 1px;
    background: linear-gradient(90deg, transparent, {CYAN}66, transparent);
    margin: 12px 0;
    border: none;
}}
</style>
""", unsafe_allow_html=True)


# ── Data helpers ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_prices(bust: int = 0):
    try:
        raw = yf.download(
            TICKERS, period="5d", auto_adjust=True,
            progress=False,
            group_by="column",   # outer=price-type, inner=ticker → raw["Close"] works
        )
        # Extract close prices — columns are tickers
        if isinstance(raw.columns, pd.MultiIndex):
            if "Close" in raw.columns.get_level_values(0):
                closes = raw["Close"]
            else:
                closes = raw.xs("Close", axis=1, level=1)
        else:
            closes = raw[["Close"]].rename(columns={"Close": TICKERS[0]})

        closes = closes.dropna(how="all")
        if closes.empty:
            return {}, {}

        current = {str(c): float(v) for c, v in closes.iloc[-1].items() if pd.notna(v)}
        prev    = {str(c): float(v) for c, v in closes.iloc[-2].items() if pd.notna(v)} \
                  if len(closes) >= 2 else current
        return current, prev
    except Exception:
        return {}, {}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_thb_rate():
    try:
        t = yf.Ticker("USDTHB=X")
        rate = t.fast_info.last_price
        return float(rate) if rate else 32.5
    except Exception:
        return 32.5


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_news(ticker: str) -> list:
    try:
        raw = yf.Ticker(ticker).news or []
        out = []
        for n in raw[:6]:
            content = n.get("content", {})
            if content:
                title     = content.get("title", "")
                link      = content.get("canonicalUrl", {}).get("url", "#")
                publisher = content.get("provider", {}).get("displayName", "")
                pub_date  = content.get("pubDate", "")
            else:
                title     = n.get("title", "")
                link      = n.get("link", "#")
                publisher = n.get("publisher", "")
                ts        = n.get("providerPublishTime", 0)
                pub_date  = datetime.utcfromtimestamp(ts).strftime("%b %d, %H:%M") if ts else ""
            if title:
                out.append({"title": title, "link": link, "publisher": publisher, "date": pub_date})
        return out
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_history(ticker: str, period: str) -> pd.DataFrame:
    return yf.download(ticker, period=period, auto_adjust=True, progress=False)


# ── Portfolio build ───────────────────────────────────────────────────────────
def build_df(prices: dict, prev: dict, thb_rate: float) -> pd.DataFrame:
    rows = []
    for ticker, info in PORTFOLIO.items():
        cur_px   = prices.get(ticker) or info["snapshot_px"]
        raw_prev = prev.get(ticker)
        # Only use prev price if it is genuinely different from today
        prv_px   = raw_prev if (raw_prev and raw_prev != cur_px) else None
        shares   = info["shares"]
        cur_val  = shares * cur_px
        prv_val  = shares * prv_px if prv_px else None
        cost     = info["cost_basis"]
        pnl_usd  = cur_val - cost
        pnl_pct  = pnl_usd / cost * 100 if cost > 0 else 0.0
        day_usd  = (cur_val - prv_val) if prv_val is not None else 0.0
        day_pct  = (cur_px - prv_px) / prv_px * 100 if prv_px else 0.0
        alert    = "crit" if pnl_pct <= -30 else ("warn" if pnl_pct <= -7 else "ok")
        rows.append({
            "Ticker":    ticker,
            "Sector":    info["sector"],
            "Shares":    round(shares, 4),
            "Price":     round(cur_px, 2),
            "Value_USD": round(cur_val, 2),
            "Value_THB": round(cur_val * thb_rate, 0),
            "Prev_Val":  round(prv_val, 2) if prv_val is not None else round(cur_val, 2),
            "Cost":      round(cost, 2),
            "PnL_USD":   round(pnl_usd, 2),
            "PnL_pct":   round(pnl_pct, 2),
            "Day_USD":   round(day_usd, 2),
            "Day_pct":   round(day_pct, 2),
            "Alert":     alert,
        })
    return pd.DataFrame(rows).sort_values("Value_USD", ascending=False).reset_index(drop=True)


GRID_COLOR = "#0a2a40"

def _base_layout(height, **kwargs):
    """Return a clean plotly layout dict compatible with all Plotly versions."""
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=kwargs.pop("showlegend", True),
    )
    layout.update(kwargs)
    return layout


# ── Main app ──────────────────────────────────────────────────────────────────
def main():
    # Auto-refresh every 5 minutes so P&L and Day % stay live
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=5 * 60 * 1000, key="price_refresh")

    for key, default in [("chat", []), ("mark_brief", None),
                          ("brief_time", None), ("bust", 0)]:
        if key not in st.session_state:
            st.session_state[key] = default

    api_key = ""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass

    # ── Fetch ────────────────────────────────────────────────────────────────
    with st.spinner(""):
        prices, prev = fetch_prices(st.session_state.bust)
        thb_rate     = fetch_thb_rate()
        df           = build_df(prices, prev, thb_rate)

    total_val  = df["Value_USD"].sum()
    total_cost = df["Cost"].sum()
    total_pl   = df["PnL_USD"].sum()
    total_pl_p = total_pl / total_cost * 100 if total_cost else 0
    day_pl     = df["Day_USD"].sum()
    # Use yesterday's total portfolio value as denominator (correct weighting)
    prev_total = df["Prev_Val"].sum()
    day_pl_p   = day_pl / prev_total * 100 if prev_total > 0 else 0
    alerts_df  = df[df["Alert"] != "ok"]

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class='dash-header'>
        <div class='dash-title'>📊 PHAM'S TRADING DASHBOARD</div>
        <div class='dash-subtitle'>
            Live Portfolio Intelligence &nbsp;·&nbsp;
            {datetime.now().strftime('%b %d, %Y  %H:%M')} &nbsp;·&nbsp;
            17 Positions
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    def kpi(label, value, sub, cls):
        return f"""<div class='kpi-card'>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-value {cls}'>{value}</div>
            <div class='kpi-sub'>{sub}</div>
        </div>"""

    with c1:
        st.markdown(kpi("Portfolio Value", f"${total_val:,.0f}",
                        f"฿{total_val*thb_rate:,.0f}", "cyan"), unsafe_allow_html=True)
    with c2:
        cls = "green" if total_pl >= 0 else "red"
        st.markdown(kpi("Total P&L", f"{total_pl_p:+.1f}%",
                        f"${total_pl:+,.0f}", cls), unsafe_allow_html=True)
    with c3:
        cls = "green" if day_pl >= 0 else "red"
        st.markdown(kpi("Today P&L", f"{day_pl_p:+.2f}%",
                        f"${day_pl:+,.0f}", cls), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi("Positions", "17",
                        f"{len(alerts_df)} need attention", "yellow"), unsafe_allow_html=True)
    with c5:
        st.markdown(kpi("USD / THB", f"{thb_rate:.2f}",
                        "Live rate", "cyan"), unsafe_allow_html=True)
    with c6:
        st.markdown(kpi("Cost Basis", f"${total_cost:,.0f}",
                        "Original invested", "cyan"), unsafe_allow_html=True)

    # Refresh button (small, top right)
    _, rbtn = st.columns([11, 1])
    with rbtn:
        if st.button("⟳", help="Refresh prices"):
            st.session_state.bust += 1
            st.rerun()

    st.markdown("<div class='glow-line'></div>", unsafe_allow_html=True)

    # ── Alert banners ─────────────────────────────────────────────────────────
    crit_df = alerts_df[alerts_df["Alert"] == "crit"]
    warn_df = alerts_df[alerts_df["Alert"] == "warn"]
    if len(crit_df):
        names = "  ·  ".join(f"{r.Ticker} ({r.PnL_pct:+.1f}%)" for r in crit_df.itertuples())
        st.markdown(f"<div class='alert-crit'>🚨 CRITICAL &nbsp;|&nbsp; {names}</div>",
                    unsafe_allow_html=True)
    if len(warn_df):
        names = "  ·  ".join(f"{r.Ticker} ({r.PnL_pct:+.1f}%)" for r in warn_df.itertuples())
        st.markdown(f"<div class='alert-warn'>⚠ WATCH LIST &nbsp;|&nbsp; {names}</div>",
                    unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["  OVERVIEW  ", "  HOLDINGS  ", "  NEWS FEED  ", "  MARK AI  "])

    # ══ TAB 1 — OVERVIEW ═════════════════════════════════════════════════════
    with tab1:
        col_l, col_r = st.columns([3, 2])

        with col_l:
            st.markdown("<div class='section-title'>Portfolio Allocation</div>", unsafe_allow_html=True)
            cyan_seq = [
                "#00d4ff","#00b8d9","#009cb3","#00808c","#006466",
                "#004d4d","#003333","#001a1a","#00fff0","#00e8d8",
                "#00d1c0","#00baa8","#00a390","#008c78","#007560",
                "#005e48","#004730",
            ]
            fig_pie = go.Figure(go.Pie(
                labels=df["Ticker"],
                values=df["Value_USD"],
                hole=0.55,
                marker=dict(
                    colors=cyan_seq,
                    line=dict(color=BG, width=2),
                ),
                textposition="inside",
                textinfo="percent+label",
                textfont=dict(size=10, color="white"),
                hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
            ))
            fig_pie.add_annotation(
                text=f"<b>${total_val:,.0f}</b>",
                x=0.5, y=0.5, font=dict(size=15, color=CYAN, family="Orbitron"),
                showarrow=False,
            )
            fig_pie.update_layout(**_base_layout(350,
                                  legend=dict(orientation="v")))
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_r:
            st.markdown("<div class='section-title'>Unrealized P&L by Position</div>", unsafe_allow_html=True)
            sd = df.sort_values("PnL_pct")
            bar_colors = [RED if v < 0 else GREEN for v in sd["PnL_pct"]]
            fig_bar = go.Figure(go.Bar(
                x=sd["PnL_pct"], y=sd["Ticker"],
                orientation="h",
                marker=dict(color=bar_colors,
                            line=dict(color="rgba(0,0,0,0)", width=0)),
                text=[f"{v:+.1f}%" for v in sd["PnL_pct"]],
                textposition="outside",
                textfont=dict(size=9),
                hovertemplate="<b>%{y}</b>: %{x:+.2f}%<extra></extra>",
            ))
            fig_bar.update_layout(**_base_layout(350,
                showlegend=False,
                xaxis=dict(showgrid=False, zeroline=True,
                           zerolinecolor="rgba(0,212,255,0.27)", zerolinewidth=1),
                yaxis=dict(showgrid=False),
            ))
            st.plotly_chart(fig_bar, use_container_width=True)

        # Sector breakdown
        st.markdown("<div class='section-title'>Sector Breakdown</div>", unsafe_allow_html=True)
        sec = df.groupby("Sector").agg(
            Value=("Value_USD","sum"), PnL=("PnL_USD","sum"), Cost=("Cost","sum")
        ).reset_index()
        sec["PnL_pct"] = sec["PnL"] / sec["Cost"] * 100

        fig_sec = go.Figure()
        sec_colors = [RED if v < 0 else CYAN for v in sec["PnL_pct"]]
        fig_sec.add_trace(go.Bar(
            x=sec["Sector"], y=sec["Value"],
            marker=dict(
                color=sec_colors,
                opacity=0.8,
                line=dict(color="rgba(0,212,255,0.27)", width=1),
            ),
            text=[f"${v:,.0f}" for v in sec["Value"]],
            textposition="outside",
            textfont=dict(size=10, color=CYAN),
            customdata=sec["PnL_pct"],
            hovertemplate="<b>%{x}</b><br>Value: $%{y:,.0f}<br>P&L: %{customdata:+.1f}%<extra></extra>",
        ))
        fig_sec.update_layout(**_base_layout(260,
            showlegend=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        ))
        st.plotly_chart(fig_sec, use_container_width=True)

    # ══ TAB 2 — HOLDINGS ═════════════════════════════════════════════════════
    with tab2:
        st.markdown("<div class='section-title'>Live Positions — All 17 Stocks</div>", unsafe_allow_html=True)

        display = df.rename(columns={
            "Price":"Price (USD)", "Value_USD":"Value (USD)", "Value_THB":"Value (THB)",
            "PnL_USD":"P&L ($)", "PnL_pct":"P&L %",
            "Day_USD":"Day ($)", "Day_pct":"Day %",
        })[["Ticker","Sector","Shares","Price (USD)","Value (USD)","Value (THB)",
            "P&L ($)","P&L %","Day ($)","Day %"]]

        st.dataframe(
            display, use_container_width=True, height=560, hide_index=True,
            column_config={
                "Price (USD)": st.column_config.NumberColumn(format="$%.2f"),
                "Value (USD)": st.column_config.NumberColumn(format="$%.2f"),
                "Value (THB)": st.column_config.NumberColumn(format="฿%.0f"),
                "P&L ($)":     st.column_config.NumberColumn(format="$%+.2f"),
                "P&L %":       st.column_config.NumberColumn(format="%+.2f%%"),
                "Day ($)":     st.column_config.NumberColumn(format="$%+.2f"),
                "Day %":       st.column_config.NumberColumn(format="%+.2f%%"),
            },
        )

        st.markdown("<div class='section-title'>Price Chart</div>", unsafe_allow_html=True)
        s_col, p_col = st.columns([2, 4])
        with s_col:
            selected = st.selectbox("Ticker:", TICKERS)
        with p_col:
            period = st.radio("Period:", ["1mo","3mo","6mo","1y","2y"], horizontal=True, index=2)

        hist = fetch_history(selected, period)
        if not hist.empty:
            close = hist["Close"].squeeze()
            is_up = float(close.iloc[-1]) >= float(close.iloc[0])
            line_color = GREEN if is_up else RED
            fill_color = "rgba(0,255,136,0.06)" if is_up else "rgba(255,51,102,0.06)"

            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=hist.index, y=close,
                mode="lines",
                line=dict(color=line_color, width=1.8),
                fill="tozeroy", fillcolor=fill_color,
                name=selected,
                hovertemplate="$%{y:.2f}<extra></extra>",
            ))
            fig_line.update_layout(**_base_layout(300,
                hovermode="x unified",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
            ))
            st.plotly_chart(fig_line, use_container_width=True)

    # ══ TAB 3 — NEWS ═════════════════════════════════════════════════════════
    with tab3:
        brief_col, news_col = st.columns([2, 3])

        with brief_col:
            st.markdown("<div class='section-title'>Mark's Portfolio Brief</div>", unsafe_allow_html=True)
            needs = (st.session_state.brief_time is None or
                     (datetime.now() - st.session_state.brief_time) > timedelta(days=2))

            if st.button("⚡  Generate Brief", use_container_width=True) or (
                needs and st.session_state.mark_brief is None
            ):
                with st.spinner("Analysing portfolio..."):
                    st.session_state.mark_brief = _fallback_brief(df, alerts_df)
                    st.session_state.brief_time = datetime.now()

            if st.session_state.mark_brief:
                st.markdown(
                    f"<div class='mark-bubble'>{st.session_state.mark_brief}</div>",
                    unsafe_allow_html=True,
                )
                if st.session_state.brief_time:
                    next_r = st.session_state.brief_time + timedelta(days=2)
                    st.caption(f"Generated {st.session_state.brief_time.strftime('%b %d %H:%M')} · Next {next_r.strftime('%b %d')}")
            else:
                st.info("Click Generate Brief for your portfolio snapshot.")

        with news_col:
            st.markdown("<div class='section-title'>Latest News by Ticker</div>", unsafe_allow_html=True)
            news_sel = st.selectbox("Select ticker:", TICKERS, key="news_t")
            items = fetch_news(news_sel)
            if items:
                for item in items:
                    st.markdown(
                        f"""<div class='news-card'>
                            <a href='{item['link']}' target='_blank'>▸ {item['title']}</a>
                            <div class='news-meta'>{item['publisher']} · {item['date']}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
            else:
                st.info(f"No recent news for {news_sel}.")

    # ══ TAB 4 — MARK AI ══════════════════════════════════════════════════════
    with tab4:
        st.markdown("<div class='section-title'>Chat with Mark — AI Portfolio Analyst</div>",
                    unsafe_allow_html=True)
        if not api_key:
            st.warning("Mark's AI chat requires an ANTHROPIC_API_KEY in Streamlit secrets.")

        if not st.session_state.chat:
            st.markdown("""<div class='mark-bubble'>
👋 Hi, I'm <b>Mark</b> — your AI portfolio analyst.

Ask me anything:
  · "Which positions should I review?"
  · "What's happening with DUOL?"
  · "Analyse my tech sector exposure"
  · "How is my portfolio performing today?"
</div>""", unsafe_allow_html=True)

        for msg in st.session_state.chat:
            css = "user-bubble" if msg["role"] == "user" else "mark-bubble"
            icon = "🧑" if msg["role"] == "user" else "🤖"
            st.markdown(
                f"<div class='{css}'>{icon} {msg['content']}</div>",
                unsafe_allow_html=True,
            )

        with st.form("chat_form", clear_on_submit=True):
            ic, bc = st.columns([6, 1])
            with ic:
                user_input = st.text_input("Message", placeholder="Ask Mark...",
                                           label_visibility="collapsed")
            with bc:
                send = st.form_submit_button("Send", use_container_width=True)

        if send and user_input.strip():
            st.session_state.chat.append({"role": "user", "content": user_input.strip()})
            with st.spinner("Mark is thinking..."):
                reply = _mark_chat(user_input.strip(), df, api_key)
            st.session_state.chat.append({"role": "assistant", "content": reply})
            st.rerun()

        if st.session_state.chat:
            if st.button("🗑  Clear chat"):
                st.session_state.chat = []
                st.rerun()


# ── Mark helpers ──────────────────────────────────────────────────────────────
def _fallback_brief(df, alerts):
    total = df["Value_USD"].sum()
    pl    = df["PnL_USD"].sum()
    best  = df.loc[df["PnL_pct"].idxmax()]
    worst = df.loc[df["PnL_pct"].idxmin()]
    lines = [
        f"📊 Mark's Portfolio Brief — {datetime.now().strftime('%b %d, %Y')}",
        "",
        f"Total Value : ${total:,.2f}",
        f"Total P&L   : ${pl:+,.2f}",
        f"Best        : {best['Ticker']} ({best['PnL_pct']:+.1f}%)",
        f"Worst       : {worst['Ticker']} ({worst['PnL_pct']:+.1f}%)",
    ]
    if len(alerts):
        lines += ["", f"⚠ {len(alerts)} position(s) need attention:"]
        for _, r in alerts.iterrows():
            lines.append(f"  · {r['Ticker']}: {r['PnL_pct']:+.1f}%")
    return "\n".join(lines)


def _mark_chat(user_msg, df, api_key):
    if not ANTHROPIC_AVAILABLE or not api_key:
        return "Mark is offline — add ANTHROPIC_API_KEY to Streamlit secrets."
    try:
        client = anthropic.Anthropic(api_key=api_key)
        ctx = df[["Ticker","Sector","Value_USD","PnL_pct","Day_pct"]].to_string(index=False)
        resp = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=1024,
            system=f"You are Mark, a concise AI portfolio analyst. Portfolio:\n{ctx}\nDate: {datetime.now().strftime('%b %d, %Y')}. Be direct, no fluff.",
            messages=[{"role": "user", "content": user_msg}],
        )
        return resp.content[0].text
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    main()
