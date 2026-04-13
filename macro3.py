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
.main-title {font-size:38px;font-weight:900;text-align:center;margin-bottom:20px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">나효정의 매크로 대시보드</div>', unsafe_allow_html=True)

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

@st.cache_data(ttl=3600)
def load_data(ticker):
    try:
        df = yf.download(ticker, period="5d", progress=False)
        if df is None or df.empty:
            return None
        return df
    except:
        return None

def get_last(df):
    if df is None or len(df) < 2:
        return None, None
    last = df["Close"].iloc[-1]
    prev = df["Close"].iloc[-2]
    pct = (last - prev) / prev * 100 if prev != 0 else 0
    return round(last,2), round(pct,2)

def display_section(title, keys):
    st.subheader(title)
    cols = st.columns(len(keys))
    for col, key in zip(cols, keys):
        df = load_data(tickers[key])
        val, pct = get_last(df)
        with col:
            if val:
                color = "red" if pct>0 else "blue" if pct<0 else "gray"
                st.metric(key, f"{val:,.2f}", f"{pct:.2f}%")
            else:
                st.metric(key, "데이터없음", "-")

# =========================
# 미국 거래대금 상위 종목
# =========================
@st.cache_data(ttl=600)
def get_us_top_traded():
    symbols = ["AAPL","MSFT","NVDA","AMZN","TSLA","GOOGL","META","AMD","NFLX","AVGO",
               "INTC","TSM","CRM","ADBE","ORCL","QCOM","PLTR","COIN","SMCI","PYPL"]

    data = []
    for s in symbols:
        try:
            df = yf.download(s, period="1d", progress=False)
            if df.empty:
                continue
            price = df["Close"].iloc[-1]
            volume = df["Volume"].iloc[-1]
            value = price * volume
            prev = df["Open"].iloc[-1]
            pct = (price-prev)/prev*100 if prev!=0 else 0
            data.append([s, round(value/1e9,2), round(pct,2)])
        except:
            continue

    df = pd.DataFrame(data, columns=["티커","거래대금(억달러)","등락률(%)"])
    df = df.sort_values(by="거래대금(억달러)", ascending=False).head(20)
    return df

# =========================
# 화면
# =========================
display_section("📈 글로벌 지수", ["Dow","Nasdaq","S&P500","SOX","VIX"])
display_section("💱 환율 / 국채금리", ["달러/원","미국 2년","미국 10년"])
display_section("🛢️ 원자재 / 비트코인", ["WTI","Gold","Silver","Copper","Bitcoin"])

st.subheader("🇰🇷 한국 증시")
display_section("", ["KOSPI","KOSDAQ"])

st.subheader("🇺🇸 미국 거래대금 상위 종목 (TOP20)")
st.dataframe(get_us_top_traded(), use_container_width=True)



