import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import re
import html
from datetime import datetime, timedelta

st.set_page_config(page_title="나효정의 매크로 대시보드", layout="wide")

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

.title-box {
    text-align: center;
    margin-bottom: 24px;
}

.main-title {
    font-size: 38px;
    font-weight: 900;
    color: #253746;
    margin-bottom: 8px;
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

.card-value-small {
    font-size: 26px;
    font-weight: 900;
    line-height: 1.1;
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
    "달러/원": "KRW=X",
    "미국 2년": "^IRX",
    "미국 10년": "^TNX",
    "WTI": "CL=F",
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Copper": "HG=F",
    "Bitcoin": "BTC-USD",
    "KOSPI": "^KS11",
    "KOSDAQ": "^KQ11",
}

INVESTING_KOSPI_NIGHT_URL = "https://www.investing.com/indices/kospi-200-future"

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

@st.cache_data(ttl=600)
def load_investing_kospi_night():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
        "Referer": "https://www.investing.com/",
    }

    try:
        response = requests.get(INVESTING_KOSPI_NIGHT_URL, headers=headers, timeout=10)
        response.raise_for_status()

        text = html.unescape(response.text)
        text = re.sub(r"<script.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        price_match = re.search(
            r"KOSPI 200 Future live stock price is ([0-9,]+(?:\.[0-9]+)?)",
            text
        )
        prev_close_match = re.search(
            r"Prev\. Close\s*([0-9,]+(?:\.[0-9]+)?)",
            text
        )

        if not price_match:
            watchlist_match = re.search(
                r"Add to Watchlist\s*([0-9,]+(?:\.[0-9]+)?)\s*([+-]?[0-9,]+(?:\.[0-9]+)?)\(([+-]?[0-9]+(?:\.[0-9]+)?)%\)",
                text
            )
            if watchlist_match:
                price = float(watchlist_match.group(1).replace(",", ""))
                pct = float(watchlist_match.group(3))
                return round(price, 2), round(pct, 2)

        if not price_match or not prev_close_match:
            return None, None

        price = float(price_match.group(1).replace(",", ""))
        prev_close = float(prev_close_match.group(1).replace(",", ""))

        if prev_close == 0:
            pct = 0.0
        else:
            pct = ((price - prev_close) / prev_close) * 100

        return round(price, 2), round(pct, 2)

    except Exception:
        return None, None

def get_value_class(delta):
    if delta is None:
        return "flat"
    if delta > 0:
        return "up"
    if delta < 0:
        return "down"
    return "flat"

def render_card(key, value, pct):
    if value is not None and pct is not None:
        suffix = " 원" if key == "달러/원" else ""
        suffix = "%" if key in ["미국 2년", "미국 10년"] else suffix

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

def display_section(title, keys):
    st.subheader(title)
    cols = st.columns(len(keys))

    for col, key in zip(cols, keys):
        with col:
            if key == "KOSPI 야간선물":
                value, pct = load_investing_kospi_night()
            else:
                df = load_yf_data(tickers[key])
                value, pct = get_last_data(df)

            render_card(key, value, pct)

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

    def flag(c):
        return "미국" if c == "US" else "한국"

    def star(x):
        return "⭐" * x

    rows = []
    for e in events:
        event_date = (start_of_week + timedelta(days=e["day"])).strftime("%m-%d")
        rows.append({
            "국가": flag(e["country"]),
            "이벤트": e["name"],
            "중요도": star(e["importance"]),
            "날짜": event_date
        })

    df_events = pd.DataFrame(rows)
    st.table(df_events)

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="title-box">
    <div class="main-title">나효정의 매크로 대시보드</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-box">', unsafe_allow_html=True)

display_section("📈 글로벌 지수", ["Dow", "Nasdaq", "S&P500", "SOX", "VIX"])
display_section("💱 환율 / 국채금리", ["달러/원", "미국 2년", "미국 10년"])
display_section("🛢️ 원자재 / 비트코인", ["WTI", "Gold", "Silver", "Copper", "Bitcoin"])
display_section("🇰🇷 한국 증시", ["KOSPI", "KOSDAQ", "KOSPI 야간선물"])

render_smart_calendar_no_api()

st.caption("데이터: Yahoo Finance / KOSPI 야간선물: Investing")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="footer-note">AI GENERATED REPORT FOR YOUR DAILY MARKET REVIEW</div>',
    unsafe_allow_html=True
)


