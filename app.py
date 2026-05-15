"""
Mark Trading Dashboard
Live portfolio tracker + AI agent for your 17 US stock positions.
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

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mark | Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Portfolio snapshot (May 15, 2026) ─────────────────────────────────────────
# cost_basis = ref_value − unrealized_pnl (derived from screenshots)
PORTFOLIO = {
    "META":  {"cost_basis": 1088.74, "ref_value": 1110.59, "sector": "Technology"},
    "AMZN":  {"cost_basis":  872.70, "ref_value": 1068.15, "sector": "Technology"},
    "MSFT":  {"cost_basis":  987.70, "ref_value": 1036.08, "sector": "Technology"},
    "GOOGL": {"cost_basis":  335.13, "ref_value":  802.63, "sector": "Technology"},
    "NVDA":  {"cost_basis":  464.70, "ref_value":  737.85, "sector": "Technology"},
    "LLY":   {"cost_basis":  520.22, "ref_value":  735.75, "sector": "Healthcare"},
    "AMD":   {"cost_basis":  153.75, "ref_value":  497.79, "sector": "Technology"},
    "VOO":   {"cost_basis":  428.84, "ref_value":  470.13, "sector": "ETF"},
    "SGOL":  {"cost_basis":  399.36, "ref_value":  402.73, "sector": "Commodity"},
    "NFLX":  {"cost_basis":  252.63, "ref_value":  267.62, "sector": "Technology"},
    "TSM":   {"cost_basis":  199.68, "ref_value":  244.85, "sector": "Technology"},
    "QQQ":   {"cost_basis":  152.43, "ref_value":  212.78, "sector": "ETF"},
    "AVGO":  {"cost_basis":  158.66, "ref_value":  202.28, "sector": "Technology"},
    "SOFI":  {"cost_basis":  230.50, "ref_value":  177.36, "sector": "Finance"},
    "MARA":  {"cost_basis":  182.82, "ref_value":  118.90, "sector": "Crypto"},
    "ORCL":  {"cost_basis":  113.63, "ref_value":   79.12, "sector": "Technology"},
    "DUOL":  {"cost_basis":  226.24, "ref_value":   73.06, "sector": "Technology"},
}
TICKERS = list(PORTFOLIO.keys())

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #080818; }
[data-testid="stHeader"]           { background: #080818; }
[data-testid="stSidebar"]          { background: #0f0f26; }
[data-testid="stTabs"]             { background: transparent; }

.kpi-card {
    background: linear-gradient(135deg, #11112b 0%, #191935 100%);
    border: 1px solid #26265a;
    border-radius: 14px;
    padding: 18px 16px;
    text-align: center;
    margin-bottom: 4px;
}
.kpi-label { font-size: 0.7rem; color: #7878aa; letter-spacing: 0.1em; text-transform: uppercase; }
.kpi-value { font-size: 1.75rem; font-weight: 700; margin: 4px 0 2px; }
.kpi-sub   { font-size: 0.8rem; color: #9999bb; }

.green  { color: #06d6a0; }
.red    { color: #ef476f; }
.yellow { color: #ffd166; }
.muted  { color: #8888aa; }

.alert-crit {
    background: rgba(239,71,111,0.1);
    border: 1px solid rgba(239,71,111,0.45);
    border-radius: 10px;
    padding: 13px 16px;
    margin: 5px 0;
    font-size: 0.9rem;
}
.alert-warn {
    background: rgba(255,209,102,0.1);
    border: 1px solid rgba(255,209,102,0.4);
    border-radius: 10px;
    padding: 13px 16px;
    margin: 5px 0;
    font-size: 0.9rem;
}
.mark-bubble {
    background: linear-gradient(135deg, #0c1b3e 0%, #091526 100%);
    border-left: 3px solid #4361ee;
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 0.91rem;
    line-height: 1.6;
    white-space: pre-wrap;
}
.user-bubble {
    background: linear-gradient(135deg, #0c2e1c 0%, #091f11 100%);
    border-left: 3px solid #06d6a0;
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin: 8px 0;
    margin-left: 18%;
    font-size: 0.91rem;
}
.news-card {
    background: #13132f;
    border-left: 3px solid #4361ee;
    border-radius: 0 8px 8px 0;
    padding: 11px 14px;
    margin: 5px 0;
}
.news-card a        { color: #8b9dff; text-decoration: none; font-size: 0.88rem; line-height: 1.4; }
.news-card a:hover  { color: #c0ccff; }
.news-meta          { font-size: 0.7rem; color: #55558a; margin-top: 4px; }
.section-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #c8c8f0;
    margin: 16px 0 8px;
    padding-bottom: 5px;
    border-bottom: 1px solid #22224a;
}
</style>
""", unsafe_allow_html=True)


# ── Data helpers ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_prices(bust: int = 0):
    """Batch-download latest and previous close for all tickers."""
    try:
        raw = yf.download(
            TICKERS, period="5d", auto_adjust=True,
            progress=False, threads=True, group_by="ticker",
        )
        # raw["Close"] is a DataFrame: index=date, columns=tickers
        closes = raw["Close"].dropna(how="all")
        current = closes.iloc[-1].to_dict()
        prev    = closes.iloc[-2].to_dict() if len(closes) >= 2 else current
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
def fetch_news(ticker: str) -> list[dict]:
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


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_all_news() -> dict:
    return {t: fetch_news(t) for t in TICKERS}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_history(ticker: str, period: str) -> pd.DataFrame:
    return yf.download(ticker, period=period, auto_adjust=True, progress=False)


# ── Portfolio calculations ────────────────────────────────────────────────────
def build_df(prices: dict, prev: dict, thb_rate: float) -> pd.DataFrame:
    rows = []
    for ticker, info in PORTFOLIO.items():
        cur_px  = prices.get(ticker) or info["ref_value"]
        prv_px  = prev.get(ticker)   or cur_px
        # Estimate shares: ref_value was the dollar amount on snapshot day at cur_px
        shares      = info["ref_value"] / cur_px if cur_px > 0 else 1.0
        cur_val     = shares * cur_px
        cost        = info["cost_basis"]
        pnl_usd     = cur_val - cost
        pnl_pct     = pnl_usd / cost * 100 if cost > 0 else 0.0
        day_usd     = shares * (cur_px - prv_px)
        day_pct     = (cur_px - prv_px) / prv_px * 100 if prv_px > 0 else 0.0

        alert = "crit" if pnl_pct <= -30 else ("warn" if pnl_pct <= -7 else "ok")

        rows.append({
            "Ticker":      ticker,
            "Sector":      info["sector"],
            "Shares":      round(shares, 4),
            "Price":       round(cur_px, 2),
            "Value_USD":   round(cur_val, 2),
            "Value_THB":   round(cur_val * thb_rate, 0),
            "Cost":        round(cost, 2),
            "PnL_USD":     round(pnl_usd, 2),
            "PnL_pct":     round(pnl_pct, 2),
            "Day_USD":     round(day_usd, 2),
            "Day_pct":     round(day_pct, 2),
            "Alert":       alert,
        })
    return pd.DataFrame(rows).sort_values("Value_USD", ascending=False).reset_index(drop=True)


# ── Mark AI ──────────────────────────────────────────────────────────────────
def _get_client(api_key: str):
    if not ANTHROPIC_AVAILABLE or not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def mark_chat(user_msg: str, df: pd.DataFrame, api_key: str) -> str:
    client = _get_client(api_key)
    if not client:
        return (
            "Mark is offline — add your **ANTHROPIC_API_KEY** to Streamlit secrets "
            "to enable AI-powered chat. See the README for instructions."
        )
    portfolio_txt = df[["Ticker", "Sector", "Value_USD", "PnL_pct", "Day_pct"]].to_string(index=False)
    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=f"""You are Mark, a sharp and concise AI portfolio analyst.

Current portfolio ({datetime.now().strftime('%b %d, %Y')}):
{portfolio_txt}

Rules:
- Be direct and concise — no fluff
- Flag positions with PnL_pct ≤ -7% as needing attention
- Use USD values; include THB in parentheses only when relevant
- Give actionable commentary, not generic advice
- If asked about news, say you're using Yahoo Finance data""",
            messages=[{"role": "user", "content": user_msg}],
        )
        return resp.content[0].text
    except Exception as e:
        return f"Mark hit an error: {e}"


def mark_brief(df: pd.DataFrame, all_news: dict, api_key: str) -> str:
    client = _get_client(api_key)
    if not client:
        return _fallback_brief(df)

    news_lines = ""
    for ticker in TICKERS[:10]:
        items = all_news.get(ticker, [])
        if items:
            news_lines += f"\n{ticker}: {items[0]['title']}"

    portfolio_txt = df[["Ticker", "Value_USD", "PnL_pct", "Day_pct"]].to_string(index=False)
    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": f"""Write a sharp, under-200-word portfolio brief as Mark.

Portfolio:
{portfolio_txt}

Latest headlines:
{news_lines}

Start with: "📊 Mark's Portfolio Brief — {datetime.now().strftime('%b %d, %Y')}"
Cover: top risks, biggest movers, any positions needing action.
End with one sentence on what to watch next.
Be direct. No fluff."""}],
        )
        return resp.content[0].text
    except Exception as e:
        return _fallback_brief(df)


def _fallback_brief(df: pd.DataFrame) -> str:
    total    = df["Value_USD"].sum()
    total_pl = df["PnL_USD"].sum()
    best     = df.loc[df["PnL_pct"].idxmax()]
    worst    = df.loc[df["PnL_pct"].idxmin()]
    alerts   = df[df["Alert"] != "ok"]

    lines = [
        f"📊 Mark's Portfolio Brief — {datetime.now().strftime('%b %d, %Y')}",
        "",
        f"Total: ${total:,.2f}  |  Total P&L: ${total_pl:+,.2f}",
        f"Best: {best['Ticker']} ({best['PnL_pct']:+.1f}%)  |  Worst: {worst['Ticker']} ({worst['PnL_pct']:+.1f}%)",
    ]
    if len(alerts):
        lines.append(f"\n⚠️ {len(alerts)} position(s) need attention:")
        for _, r in alerts.iterrows():
            lines.append(f"  • {r['Ticker']}: {r['PnL_pct']:+.1f}%")
    lines.append("\n_Add ANTHROPIC_API_KEY to Streamlit secrets for AI-powered insights._")
    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    # Session state init
    for key, default in [
        ("chat",           []),
        ("mark_brief",     None),
        ("brief_time",     None),
        ("bust",           0),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # API key from secrets
    api_key = ""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass

    # ── Fetch data ──────────────────────────────────────────────────────────
    with st.spinner(""):
        prices, prev = fetch_prices(st.session_state.bust)
        thb_rate     = fetch_thb_rate()
        df           = build_df(prices, prev, thb_rate)

    total_val  = df["Value_USD"].sum()
    total_cost = df["Cost"].sum()
    total_pl   = df["PnL_USD"].sum()
    total_pl_p = total_pl / total_cost * 100 if total_cost else 0
    day_pl     = df["Day_USD"].sum()
    day_pl_p   = day_pl / total_val * 100 if total_val else 0
    alerts_df  = df[df["Alert"] != "ok"]

    # ── Header ──────────────────────────────────────────────────────────────
    h1, h2, h3 = st.columns([5, 3, 1])
    with h1:
        st.markdown("## 📊 Mark — Trading Dashboard")
    with h2:
        st.caption(f"🕐 {datetime.now().strftime('%b %d, %Y  %H:%M')}  ·  Prices refresh every 5 min")
    with h3:
        if st.button("🔄", help="Force refresh prices"):
            st.session_state.bust += 1
            st.rerun()

    # ── KPI row ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)

    def kpi_html(label, val, sub, cls):
        return f"""<div class='kpi-card'>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-value {cls}'>{val}</div>
            <div class='kpi-sub'>{sub}</div>
        </div>"""

    with c1:
        st.markdown(kpi_html(
            "Total Portfolio",
            f"${total_val:,.0f}",
            f"฿{total_val * thb_rate:,.0f}",
            "muted",
        ), unsafe_allow_html=True)
    with c2:
        cls = "green" if total_pl >= 0 else "red"
        st.markdown(kpi_html(
            "Total P&L",
            f"{total_pl_p:+.1f}%",
            f"${total_pl:+,.0f}",
            cls,
        ), unsafe_allow_html=True)
    with c3:
        cls = "green" if day_pl >= 0 else "red"
        st.markdown(kpi_html(
            "Today's P&L",
            f"{day_pl_p:+.2f}%",
            f"${day_pl:+,.0f}",
            cls,
        ), unsafe_allow_html=True)
    with c4:
        cls = "yellow" if len(alerts_df) else "muted"
        st.markdown(kpi_html(
            "Positions",
            f"{len(df)}",
            f"{len(alerts_df)} need attention" if len(alerts_df) else "All clear",
            cls,
        ), unsafe_allow_html=True)
    with c5:
        st.markdown(kpi_html(
            "USD / THB",
            f"{thb_rate:.2f}",
            "Live rate",
            "muted",
        ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Alert banners ────────────────────────────────────────────────────────
    crit_df = alerts_df[alerts_df["Alert"] == "crit"]
    warn_df = alerts_df[alerts_df["Alert"] == "warn"]

    if len(crit_df):
        names = ", ".join(f"{r.Ticker} ({r.PnL_pct:+.1f}%)" for r in crit_df.itertuples())
        st.markdown(
            f"<div class='alert-crit'>🚨 <strong>Critical positions (≤ −30%):</strong> {names}</div>",
            unsafe_allow_html=True,
        )
    if len(warn_df):
        names = ", ".join(f"{r.Ticker} ({r.PnL_pct:+.1f}%)" for r in warn_df.itertuples())
        st.markdown(
            f"<div class='alert-warn'>⚠️ <strong>Watch list (≤ −7%):</strong> {names}</div>",
            unsafe_allow_html=True,
        )

    # ── Tabs ────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "📋 Holdings", "📰 Mark's News", "💬 Chat with Mark"])

    # ── Tab 1: Overview ──────────────────────────────────────────────────────
    with tab1:
        left, right = st.columns([3, 2])

        with left:
            st.markdown("<div class='section-title'>Portfolio Allocation</div>", unsafe_allow_html=True)
            fig_pie = px.pie(
                df, values="Value_USD", names="Ticker",
                hole=0.52,
                color_discrete_sequence=px.colors.sequential.Plasma_r,
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label", textfont_size=11)
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#c8c8f0", margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(font_size=10), height=360,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with right:
            st.markdown("<div class='section-title'>P&L by Position</div>", unsafe_allow_html=True)
            sorted_df = df.sort_values("PnL_pct")
            fig_bar = go.Figure(go.Bar(
                x=sorted_df["PnL_pct"],
                y=sorted_df["Ticker"],
                orientation="h",
                marker_color=["#ef476f" if v < 0 else "#06d6a0" for v in sorted_df["PnL_pct"]],
                text=[f"{v:+.1f}%" for v in sorted_df["PnL_pct"]],
                textposition="outside",
                textfont_size=10,
            ))
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#c8c8f0",
                xaxis=dict(showgrid=False, zeroline=True, zerolinecolor="#33335a"),
                yaxis=dict(showgrid=False),
                margin=dict(t=10, b=10, l=10, r=55), height=360,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("<div class='section-title'>Sector Breakdown</div>", unsafe_allow_html=True)
        sector = df.groupby("Sector").agg(
            Value=("Value_USD", "sum"),
            PnL=("PnL_USD", "sum"),
            Cost=("Cost", "sum"),
        ).reset_index()
        sector["PnL_pct"] = sector["PnL"] / sector["Cost"] * 100

        fig_sec = px.bar(
            sector, x="Sector", y="Value",
            color="PnL_pct",
            color_continuous_scale=["#ef476f", "#ffd166", "#06d6a0"],
            color_continuous_midpoint=0,
            text=[f"${v:,.0f}" for v in sector["Value"]],
            labels={"Value": "Value (USD)", "PnL_pct": "P&L %"},
        )
        fig_sec.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c8c8f0",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#18183a"),
            margin=dict(t=10, b=10), height=280,
            coloraxis_colorbar=dict(title="P&L %", len=0.7),
        )
        st.plotly_chart(fig_sec, use_container_width=True)

    # ── Tab 2: Holdings ──────────────────────────────────────────────────────
    with tab2:
        st.markdown("<div class='section-title'>All Positions — Live Prices</div>", unsafe_allow_html=True)

        display = df.rename(columns={
            "Price":     "Price (USD)",
            "Value_USD": "Value (USD)",
            "Value_THB": "Value (THB)",
            "PnL_USD":   "P&L (USD)",
            "PnL_pct":   "P&L %",
            "Day_USD":   "Day P&L (USD)",
            "Day_pct":   "Day %",
        })[["Ticker", "Sector", "Shares", "Price (USD)", "Value (USD)", "Value (THB)",
            "P&L (USD)", "P&L %", "Day P&L (USD)", "Day %"]]

        st.dataframe(
            display,
            use_container_width=True,
            height=560,
            hide_index=True,
            column_config={
                "Price (USD)":   st.column_config.NumberColumn(format="$%.2f"),
                "Value (USD)":   st.column_config.NumberColumn(format="$%.2f"),
                "Value (THB)":   st.column_config.NumberColumn(format="฿%.0f"),
                "P&L (USD)":     st.column_config.NumberColumn(format="$%+.2f"),
                "P&L %":         st.column_config.NumberColumn(format="%+.2f%%"),
                "Day P&L (USD)": st.column_config.NumberColumn(format="$%+.2f"),
                "Day %":         st.column_config.NumberColumn(format="%+.2f%%"),
            },
        )

        st.markdown("<div class='section-title'>Price Chart</div>", unsafe_allow_html=True)
        sel_col, per_col = st.columns([2, 3])
        with sel_col:
            selected = st.selectbox("Ticker:", TICKERS)
        with per_col:
            period = st.radio("Period:", ["1mo", "3mo", "6mo", "1y", "2y"], horizontal=True, index=2)

        hist = fetch_history(selected, period)
        if not hist.empty:
            close = hist["Close"].squeeze()
            fig_line = go.Figure()
            start_price = float(close.iloc[0])
            color = "#06d6a0" if float(close.iloc[-1]) >= start_price else "#ef476f"
            fig_line.add_trace(go.Scatter(
                x=hist.index, y=close,
                mode="lines",
                line=dict(color=color, width=2),
                fill="tozeroy", fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
                name=selected,
                hovertemplate="$%{y:.2f}<extra></extra>",
            ))
            fig_line.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#c8c8f0",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#18183a"),
                margin=dict(t=10, b=10), height=300, hovermode="x unified",
            )
            st.plotly_chart(fig_line, use_container_width=True)

    # ── Tab 3: Mark's News ───────────────────────────────────────────────────
    with tab3:
        brief_col, news_col = st.columns([2, 3])

        with brief_col:
            st.markdown("<div class='section-title'>🤖 Mark's Portfolio Brief</div>", unsafe_allow_html=True)

            needs_refresh = (
                st.session_state.brief_time is None
                or (datetime.now() - st.session_state.brief_time) > timedelta(days=2)
            )

            if st.button("⚡ Generate Brief", use_container_width=True) or (
                needs_refresh and st.session_state.mark_brief is None
            ):
                with st.spinner("Mark is reading the markets..."):
                    all_news = fetch_all_news()
                    st.session_state.mark_brief = mark_brief(df, all_news, api_key)
                    st.session_state.brief_time = datetime.now()

            if st.session_state.mark_brief:
                st.markdown(
                    f"<div class='mark-bubble'>{st.session_state.mark_brief}</div>",
                    unsafe_allow_html=True,
                )
                if st.session_state.brief_time:
                    next_refresh = st.session_state.brief_time + timedelta(days=2)
                    st.caption(
                        f"Generated: {st.session_state.brief_time.strftime('%b %d %H:%M')}  ·  "
                        f"Next: {next_refresh.strftime('%b %d')}"
                    )
            else:
                st.info("Click **Generate Brief** to get Mark's portfolio intelligence update.")

        with news_col:
            st.markdown("<div class='section-title'>📰 Latest News</div>", unsafe_allow_html=True)
            news_sel = st.selectbox("Ticker news:", TICKERS, key="news_ticker")

            items = fetch_news(news_sel)
            if items:
                for item in items:
                    st.markdown(
                        f"""<div class='news-card'>
                            <a href='{item['link']}' target='_blank'>📄 {item['title']}</a>
                            <div class='news-meta'>{item['publisher']} · {item['date']}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
            else:
                st.info(f"No recent news for {news_sel}.")

    # ── Tab 4: Chat with Mark ────────────────────────────────────────────────
    with tab4:
        st.markdown("<div class='section-title'>💬 Chat with Mark</div>", unsafe_allow_html=True)

        if not api_key:
            st.warning(
                "Mark's AI chat needs an Anthropic API key. "
                "Add `ANTHROPIC_API_KEY` to your Streamlit secrets — see the README."
            )

        # Chat history display
        if not st.session_state.chat:
            st.markdown("""<div class='mark-bubble'>
👋 Hi, I'm <strong>Mark</strong> — your AI portfolio analyst.

I'm watching all 17 of your positions in real time. Try asking me:
• "Which positions should I cut?"
• "What's the latest news on DUOL?"
• "Analyse my tech sector concentration"
• "How is my portfolio doing today?"
</div>""", unsafe_allow_html=True)

        for msg in st.session_state.chat:
            if msg["role"] == "user":
                st.markdown(
                    f"<div class='user-bubble'>🧑 {msg['content']}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='mark-bubble'>🤖 {msg['content']}</div>",
                    unsafe_allow_html=True,
                )

        # Input form (stays at bottom)
        with st.form("chat_form", clear_on_submit=True):
            in_col, btn_col = st.columns([6, 1])
            with in_col:
                user_input = st.text_input(
                    "Message",
                    placeholder="Ask Mark about your portfolio...",
                    label_visibility="collapsed",
                )
            with btn_col:
                send = st.form_submit_button("Send →", use_container_width=True)

        if send and user_input.strip():
            st.session_state.chat.append({"role": "user", "content": user_input.strip()})
            with st.spinner("Mark is thinking..."):
                reply = mark_chat(user_input.strip(), df, api_key)
            st.session_state.chat.append({"role": "assistant", "content": reply})
            st.rerun()

        if st.session_state.chat:
            if st.button("🗑️ Clear chat"):
                st.session_state.chat = []
                st.rerun()


if __name__ == "__main__":
    main()
