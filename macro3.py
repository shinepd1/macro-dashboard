import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="GLOBAL MACRO DASHBOARD", layout="wide")

# =========================
# CSS 스타일
# =========================
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Arial, sans-serif;
}

.main {
    background: linear-gradient(135deg, #dff5ef 0%, #d9eef8 100%);
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1300px;
}

.top-board {
    background: linear-gradient(135deg, #d8f0ea 0%, #d4eef8 100%);
    border: 3px solid #a8c7cf;
    border-radius: 24px;
    padding: 22px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    margin-bottom: 28px;
}

.board-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
}

.board-title {
    font-size: 30px;
    font-weight: 900;
    color: #253746;
}

.board-date {
    font-size: 14px;
    font-weight: 700;
    color: #4c6472;
}

.card-wrap {
    background: #f4fbfd;
    border: 2px solid #b9d5dd;
    border-radius: 18px;
    padding: 12px 14px;
    min-height: 175px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
}

.card-wrap-small {
    background: #f4fbfd;
    border: 2px solid #b9d5dd;
    border-radius: 18px;
    padding: 12px 14px;
    min-height: 120px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
}

.card-title {
    font-size: 15px;
    font-weight: 800;
    color: #355165;
    margin-bottom: 10px;
}

.card-value {
    font-size: 34px;
    font-weight: 900;
    line-height: 1.1;
}

.card-value-small {
    font-size: 26px;
    font-weight: 900;
    line-height: 1.1;
}

.card-sub {
    font-size: 12px;
    color: #6a7f8d;
    margin-top: 4px;
}

.card-bottom {
    display: flex;
    justify-content: space-between;
    margin-top: 8px;
    font-size: 14px;
    font-weight: 700;
}

.up { color: #d9463b; }
.down { color: #2f7ed8; }
.flat { color: #778899; }

.section-box {
    background: rgba(255,255,255,0.35);
    border: 1px solid #b9d5dd;
    border-radius: 16px;
    padding: 18px;
    margin-top: 18px;
    margin-bottom: 18px;
}

.chart-box {
    background: rgba(255,255,255,0.55);
    border: 1px solid #b9d5dd;
    border-radius: 16px;
    padding: 16px;
    margin-top: 18px;
    margin-bottom: 18px;
}

.small-note {
    font-size: 12px;
    color: #5f6f79;
    margin-top: 6px;
}

.footer-note {
    text-align: center;
    margin-top: 18px;
    font-size: 11px;
    color: #61717b;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 기본 티커
# =========================
tickers = {
    "Dow": "^DJI",
    "Nasdaq": "^IXIC",
    "S&P500": "^GSPC",
    "SOX": "^SOX",
    "VIX": "^VIX",
    "USD/KRW": "KRW=X",
    "US 2Y": "^IRX",
    "US 10Y": "^TNX",
    "WTI": "CL=F",
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Copper": "HG=F",
    "Bitcoin": "BTC-USD"
}

# =========================
# Yahoo Finance 데이터
# =========================
@st.cache_data(ttl=3600)
def load_yf_data(ticker, period="10d"):
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=False)
        if df is None or df.empty:
            return None
        return df
    except Exception:
        return None

def extract_close_series(df):
    if df is None or df.empty:
        return None

    try:
        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        close = pd.to_numeric(close, errors="coerce").dropna()

        if close.empty:
            return None
        return close
    except Exception:
        return None

def get_last_data(df):
    close = extract_close_series(df)

    if close is None or len(close) < 2:
        return None, None

    try:
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2])

        if prev == 0:
            return round(last, 2), 0.0

        pct = ((last - prev) / prev) * 100
        return round(last, 2), round(pct, 2)
    except Exception:
        return None, None

def get_last_data_with_trend(df):
    close = extract_close_series(df)

    if close is None or len(close) < 2:
        return None, None, None

    try:
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2])

        if prev == 0:
            pct = 0.0
        else:
            pct = ((last - prev) / prev) * 100

        trend = close.tail(7).tolist()
        return round(last, 2), round(pct, 2), trend
    except Exception:
        return None, None, None

def get_value_class(delta):
    if delta is None:
        return "flat"
    if delta > 0:
        return "up"
    if delta < 0:
        return "down"
    return "flat"

# =========================
# 카드용 스파크라인
# =========================
def sparkline_svg(values, width=210, height=52, color="#b85c4f"):
    if not values or len(values) < 2:
        return ""

    min_v = min(values)
    max_v = max(values)

    if max_v == min_v:
        max_v += 1

    points = []
    for i, v in enumerate(values):
        x = i * (width / (len(values) - 1))
        y = height - ((v - min_v) / (max_v - min_v)) * (height - 8) - 4
        points.append(f"{x:.1f},{y:.1f}")

    points_str = " ".join(points)

    return f"""
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <polyline fill="none" stroke="{color}" stroke-width="3" points="{points_str}" />
    </svg>
    """

def render_top_card(title, value, delta, trend, value_prefix="", value_suffix="", delta_suffix="", subtitle="Daily Change / 7D Trend"):
    if value is None:
        value_html = '<span class="flat">데이터 없음</span>'
        delta_html = '<span class="flat">-</span>'
        spark = ""
    else:
        value_class = get_value_class(delta)
        value_html = f'<span class="{value_class}">{value_prefix}{value:,.2f}{value_suffix}</span>'

        if delta is None:
            delta_html = '<span class="flat">-</span>'
            spark = sparkline_svg(trend, color="#7f8c8d") if trend else ""
        elif delta > 0:
            delta_html = f'<span class="up">▲ +{delta:.2f}{delta_suffix}</span>'
            spark = sparkline_svg(trend, color="#c96d5c") if trend else ""
        elif delta < 0:
            delta_html = f'<span class="down">▼ {delta:.2f}{delta_suffix}</span>'
            spark = sparkline_svg(trend, color="#6a9ccf") if trend else ""
        else:
            delta_html = f'<span class="flat">{delta:.2f}{delta_suffix}</span>'
            spark = sparkline_svg(trend, color="#7f8c8d") if trend else ""

    st.markdown(f"""
    <div class="card-wrap">
        <div class="card-title">{title}</div>
        <div class="card-value">{value_html}</div>
        <div class="card-sub">{subtitle}</div>
        <div style="margin-top:8px;">{spark}</div>
        <div class="card-bottom">
            <span>변동</span>
            <span>{delta_html}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_section(title, keys):
    st.subheader(title)
    cols = st.columns(len(keys))

    for col, key in zip(cols, keys):
        df = load_yf_data(tickers[key])
        value, pct = get_last_data(df)

        with col:
            if value is not None and pct is not None:
                suffix = " 원" if key == "USD/KRW" else ""
                suffix = "%" if key in ["US 2Y", "US 10Y"] else suffix

                value_class = get_value_class(pct)

                if pct > 0:
                    delta_html = f'<span class="up">▲ +{pct:.2f}%</span>'
                elif pct < 0:
                    delta_html = f'<span class="down">▼ {pct:.2f}%</span>'
                else:
                    delta_html = f'<span class="flat">{pct:.2f}%</span>'

                st.markdown(f"""
                <div class="card-wrap-small">
                    <div class="card-title">{key}</div>
                    <div class="card-value-small">
                        <span class="{value_class}">{value:,.2f}{suffix}</span>
                    </div>
                    <div class="card-bottom">
                        <span>변동</span>
                        <span>{delta_html}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="card-wrap-small">
                    <div class="card-title">{key}</div>
                    <div class="card-value-small">
                        <span class="flat">데이터 없음</span>
                    </div>
                    <div class="card-bottom">
                        <span>변동</span>
                        <span class="flat">-</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# =========================
# FED 주요 경제지표
# =========================
def render_fed_indicators():
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.subheader("🏦 FED 주요 경제지표")

    st.markdown("""
    <div class="card-wrap" style="min-height:auto; line-height:1.9;">
    - CPI / Core CPI<br>
    - PCE (Fed 핵심 지표)<br>
    - Nonfarm Payrolls<br>
    - ISM 제조업 / 서비스업<br>
    - Retail Sales<br>
    - FOMC 금리결정
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 이번주 주요 경제 이벤트
# =========================
def render_smart_calendar_no_api():
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.subheader("📅 이번주 주요 경제 이벤트")

    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())

    events = [
        {"day": 0, "name": "ISM 서비스업", "country": "US", "importance": 2},
        {"day": 2, "name": "CPI", "country": "US", "importance": 3},
        {"day": 2, "name": "Core CPI", "country": "US", "importance": 3},
        {"day": 3, "name": "소매판매", "country": "US", "importance": 2},
        {"day": 4, "name": "고용지표 (Nonfarm Payrolls)", "country": "US", "importance": 3},
        {"day": 1, "name": "한국 실업률", "country": "KR", "importance": 1},
        {"day": 3, "name": "금통위 금리결정", "country": "KR", "importance": 3},
    ]

    def star(x):
        return "⭐" * x

    def flag(c):
        return "🇺🇸" if c == "US" else "🇰🇷"

    for e in events:
        event_date = (start_of_week + timedelta(days=e["day"])).strftime("%m-%d")

        st.markdown(f"""
        <div class="card-wrap" style="min-height:auto; margin-bottom:12px; line-height:1.8;">
        <b>{flag(e['country'])} {e['name']}</b><br>
        중요도: {star(e['importance'])}<br>
        날짜: {event_date}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 상단 대시보드
# =========================
today_str = datetime.now().strftime("%Y.%m.%d")

st.markdown(f"""
<div class="top-board">
    <div class="board-header">
        <div class="board-title">🌍 GLOBAL MACRO DASHBOARD</div>
        <div class="board-date">DATE: {today_str}</div>
    </div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    price, pct, trend = get_last_data_with_trend(load_yf_data(tickers["Dow"]))
    render_top_card("🇺🇸 다우존스", price, pct, trend, delta_suffix="%")

with c2:
    price, pct, trend = get_last_data_with_trend(load_yf_data(tickers["Nasdaq"]))
    render_top_card("📘 나스닥", price, pct, trend, delta_suffix="%")

with c3:
    price, pct, trend = get_last_data_with_trend(load_yf_data(tickers["USD/KRW"]))
    render_top_card("💱 원/달러 환율", price, pct, trend, value_suffix=" 원", delta_suffix="%")

with c4:
    price, pct, trend = get_last_data_with_trend(load_yf_data(tickers["US 10Y"]))
    render_top_card("🇺🇸 미국 국채 10Y", price, pct, trend, value_suffix="%", delta_suffix="%")

c5, c6, c7, c8 = st.columns(4)

with c5:
    price, pct, trend = get_last_data_with_trend(load_yf_data(tickers["WTI"]))
    render_top_card("🛢 WTI 유가", price, pct, trend, value_prefix="$", delta_suffix="%")

with c6:
    price, pct, trend = get_last_data_with_trend(load_yf_data(tickers["Gold"]))
    render_top_card("🟡 국제 금", price, pct, trend, value_prefix="$", delta_suffix="%")

with c7:
    price, pct, trend = get_last_data_with_trend(load_yf_data(tickers["Bitcoin"]))
    render_top_card("🪙 비트코인", price, pct, trend, value_prefix="$", delta_suffix="%")

with c8:
    price, pct, trend = get_last_data_with_trend(load_yf_data(tickers["S&P500"]))
    render_top_card("📈 S&P500", price, pct, trend, delta_suffix="%")

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# 하단 섹션
# =========================
st.markdown('<div class="section-box">', unsafe_allow_html=True)

display_section("📈 글로벌 지수", ["Dow", "Nasdaq", "S&P500", "SOX", "VIX"])
display_section("💱 환율", ["USD/KRW"])
display_section("🇺🇸 미국 금리", ["US 2Y", "US 10Y"])
display_section("🛢️ 원자재 / Crypto", ["WTI", "Gold", "Silver", "Copper", "Bitcoin"])

render_fed_indicators()
render_smart_calendar_no_api()

st.caption("데이터: Yahoo Finance")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="footer-note">AI GENERATED REPORT FOR YOUR DAILY MARKET REVIEW</div>',
    unsafe_allow_html=True
)
