import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# =========================
# 페이지 설정
# =========================
st.set_page_config(
    page_title="GLOBAL MACRO DASHBOARD",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# CSS
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
    max-width: 1200px;
    padding-left: 1rem;
    padding-right: 1rem;
}

/* 공통 글자색 강제 */
.header-box, .metric-card, .safe-card, .safe-box, .event-card {
    color: #22313f !important;
}
.header-box *, .metric-card *, .safe-card *, .safe-box *, .event-card * {
    color: #22313f !important;
}

/* 헤더 */
.header-box {
    background: linear-gradient(135deg, #d8f0ea 0%, #d4eef8 100%);
    border: 2px solid #a8c7cf;
    border-radius: 22px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.header-title {
    font-size: 30px;
    font-weight: 900;
    color: #253746 !important;
}

.header-date {
    font-size: 14px;
    font-weight: 700;
    color: #4c6472 !important;
    margin-top: 6px;
}

/* 메인 카드 */
.metric-card {
    background: #f4fbfd;
    border: 2px solid #b9d5dd;
    border-radius: 18px;
    padding: 14px 16px;
    min-height: 180px;
    margin-bottom: 14px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
}

.metric-title {
    font-size: 15px;
    font-weight: 800;
    color: #355165 !important;
    margin-bottom: 10px;
}

.metric-value {
    font-size: 30px;
    font-weight: 900;
    line-height: 1.2;
    word-break: break-word;
}

.metric-sub {
    font-size: 12px;
    color: #6a7f8d !important;
    margin-top: 6px;
}

.metric-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 8px;
    font-size: 14px;
    font-weight: 700;
}

/* 소형 카드 */
.safe-card {
    background: #f4fbfd;
    border: 2px solid #b9d5dd;
    border-radius: 16px;
    padding: 12px 14px;
    min-height: 118px;
    margin-bottom: 12px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
}

.small-title {
    font-size: 14px;
    font-weight: 800;
    color: #355165 !important;
    margin-bottom: 8px;
}

.small-value {
    font-size: 24px;
    font-weight: 900;
    line-height: 1.2;
    word-break: break-word;
}

.small-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 8px;
    font-size: 13px;
    font-weight: 700;
}

/* 섹션 박스 */
.safe-box {
    background: rgba(255,255,255,0.45);
    border: 1px solid #b9d5dd;
    border-radius: 16px;
    padding: 16px;
    margin-top: 18px;
    margin-bottom: 18px;
}

/* 이벤트 카드 */
.event-card {
    background: #f4fbfd;
    border: 2px solid #b9d5dd;
    border-radius: 18px;
    padding: 14px 16px;
    margin-bottom: 12px;
    line-height: 1.8;
}

/* 색상 */
.up { color: #d9463b !important; }
.down { color: #2f7ed8 !important; }
.flat { color: #778899 !important; }

.footer-note {
    text-align: center;
    margin-top: 18px;
    font-size: 11px;
    color: #61717b !important;
    font-weight: 700;
}

/* 모바일 */
@media (max-width: 768px) {
    .header-title {
        font-size: 24px;
    }

    .metric-value {
        font-size: 24px;
    }

    .small-value {
        font-size: 20px;
    }

    .block-container {
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }
}
</style>
""", unsafe_allow_html=True)

# =========================
# 티커
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
# 모바일 모드
# 링크 뒤에 ?mobile=1 붙이면 모바일 전용 2열
# =========================
def is_mobile_mode():
    try:
        return st.query_params.get("mobile", "0") == "1"
    except Exception:
        return False

MOBILE = is_mobile_mode()

# =========================
# 데이터 로드
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

        pct = 0.0 if prev == 0 else ((last - prev) / prev) * 100
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

        pct = 0.0 if prev == 0 else ((last - prev) / prev) * 100
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
# 스파크라인
# =========================
def sparkline_svg(values, width=180, height=46, color="#7f8c8d"):
    if not values or len(values) < 2:
        return ""

    min_v = min(values)
    max_v = max(values)

    if max_v == min_v:
        max_v += 1

    points = []
    for i, v in enumerate(values):
        x = i * (width / (len(values) - 1))
        y = height - ((v - min_v) / (max_v - min_v)) * (height - 10) - 5
        points.append(f"{x:.1f},{y:.1f}")

    return f"""
    <svg width="100%" height="{height}" viewBox="0 0 {width} {height}" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
        <polyline fill="none" stroke="{color}" stroke-width="3" points="{' '.join(points)}" />
    </svg>
    """

# =========================
# 카드 렌더링
# =========================
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
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value_html}</div>
        <div class="metric-sub">{subtitle}</div>
        <div style="margin-top:8px;">{spark}</div>
        <div class="metric-bottom">
            <span>변동</span>
            <span>{delta_html}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_small_card(title, value, pct, suffix=""):
    if value is not None and pct is not None:
        value_class = get_value_class(pct)

        if pct > 0:
            delta_html = f'<span class="up">▲ +{pct:.2f}%</span>'
        elif pct < 0:
            delta_html = f'<span class="down">▼ {pct:.2f}%</span>'
        else:
            delta_html = f'<span class="flat">{pct:.2f}%</span>'

        value_html = f'<span class="{value_class}">{value:,.2f}{suffix}</span>'
    else:
        value_html = '<span class="flat">데이터 없음</span>'
        delta_html = '<span class="flat">-</span>'

    st.markdown(f"""
    <div class="safe-card">
        <div class="small-title">{title}</div>
        <div class="small-value">{value_html}</div>
        <div class="small-bottom">
            <span>변동</span>
            <span>{delta_html}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_section(title, keys, mobile_cols=2, desktop_cols=4):
    st.subheader(title)

    col_count = mobile_cols if MOBILE else desktop_cols
    rows = [keys[i:i + col_count] for i in range(0, len(keys), col_count)]

    for row in rows:
        cols = st.columns(len(row))
        for col, key in zip(cols, row):
            df = load_yf_data(tickers[key])
            value, pct = get_last_data(df)

            suffix = ""
            if key == "USD/KRW":
                suffix = " 원"
            elif key in ["US 2Y", "US 10Y"]:
                suffix = "%"

            with col:
                render_small_card(key, value, pct, suffix=suffix)

# =========================
# FED 주요 경제지표
# =========================
def render_fed_indicators():
    st.markdown('<div class="safe-box">', unsafe_allow_html=True)
    st.subheader("🏦 FED 주요 경제지표")

    st.markdown("""
    <div class="event-card">
        <b>주요 체크 항목</b><br>
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
    st.markdown('<div class="safe-box">', unsafe_allow_html=True)
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
        <div class="event-card">
            <b>{flag(e['country'])} {e['name']}</b><br>
            중요도: {star(e['importance'])}<br>
            날짜: {event_date}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 헤더
# =========================
today_str = datetime.now().strftime("%Y.%m.%d")

st.markdown(f"""
<div class="header-box">
    <div class="header-title">🌍 GLOBAL MACRO DASHBOARD</div>
    <div class="header-date">DATE: {today_str}</div>
</div>
""", unsafe_allow_html=True)

# =========================
# 상단 메인 카드
# =========================
top_items = [
    ("🇺🇸 다우존스", "Dow", "", "", "%"),
    ("📘 나스닥", "Nasdaq", "", "", "%"),
    ("💱 원/달러 환율", "USD/KRW", "", " 원", "%"),
    ("🇺🇸 미국 국채 10Y", "US 10Y", "", "%", "%"),
    ("🛢 WTI 유가", "WTI", "$", "", "%"),
    ("🟡 국제 금", "Gold", "$", "", "%"),
    ("🪙 비트코인", "Bitcoin", "$", "", "%"),
    ("📈 S&P500", "S&P500", "", "", "%"),
]

top_col_count = 2 if MOBILE else 4
top_rows = [top_items[i:i + top_col_count] for i in range(0, len(top_items), top_col_count)]

for row in top_rows:
    cols = st.columns(len(row))
    for col, item in zip(cols, row):
        title, key, value_prefix, value_suffix, delta_suffix = item
        df = load_yf_data(tickers[key])
        price, pct, trend = get_last_data_with_trend(df)

        with col:
            render_top_card(
                title=title,
                value=price,
                delta=pct,
                trend=trend,
                value_prefix=value_prefix,
                value_suffix=value_suffix,
                delta_suffix=delta_suffix
            )

# =========================
# 하단 섹션
# =========================
st.markdown('<div class="safe-box">', unsafe_allow_html=True)
display_section("📈 글로벌 지수", ["Dow", "Nasdaq", "S&P500", "SOX", "VIX"], mobile_cols=2, desktop_cols=4)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="safe-box">', unsafe_allow_html=True)
display_section("💱 환율", ["USD/KRW"], mobile_cols=1, desktop_cols=1)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="safe-box">', unsafe_allow_html=True)
display_section("🇺🇸 미국 금리", ["US 2Y", "US 10Y"], mobile_cols=2, desktop_cols=2)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="safe-box">', unsafe_allow_html=True)
display_section("🛢️ 원자재 / Crypto", ["WTI", "Gold", "Silver", "Copper", "Bitcoin"], mobile_cols=2, desktop_cols=4)
st.markdown('</div>', unsafe_allow_html=True)

render_fed_indicators()
render_smart_calendar_no_api()

st.caption("데이터: Yahoo Finance")
st.markdown(
    '<div class="footer-note">AI GENERATED REPORT FOR YOUR DAILY MARKET REVIEW</div>',
    unsafe_allow_html=True
)

