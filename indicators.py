# indicators.py
import pandas as pd
import numpy as np

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def bbands(df, period=20, mult=2):
    ma = df["close"].rolling(period).mean()
    std = df["close"].rolling(period).std()
    return ma, ma + mult * std, ma - mult * std

def kc(df, period=20, mult=1.5):
    ma = df["close"].rolling(period).mean()
    tr = atr(df, period)
    return ma, ma + mult * tr, ma - mult * tr

def add_indicators(df):
    # assumes df has 'open','high','low','close','volume'
    df["EMA20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ATR14"] = atr(df, 14)
    df["BB_M"], df["BB_H"], df["BB_L"] = bbands(df, 20, 2)
    df["KC_M"], df["KC_H"], df["KC_L"] = kc(df, 20, 1.5)

    # VWAP calculation (resets daily for better intraday accuracy)
    if "datetime" in df.columns:
        df["date_internal"] = pd.to_datetime(df["datetime"]).dt.date
        df["VWAP"] = df.groupby("date_internal").apply(
            lambda x: (x["close"] * x["volume"]).cumsum() / (x["volume"].cumsum() + 1e-9)
        ).reset_index(level=0, drop=True)
        df.drop(columns=["date_internal"], inplace=True)
    else:
        df["VWAP"] = (df["close"] * df["volume"]).cumsum() / (df["volume"].cumsum() + 1e-9)

    df["RSI"] = compute_rsi(df["close"], 14)
    df["VOL_SMA20"] = df["volume"].rolling(window=20).mean()

def compute_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/period, adjust=False).mean()
    ma_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = ma_up / (ma_down + 1e-9)
    return 100 - (100 / (1 + rs))
