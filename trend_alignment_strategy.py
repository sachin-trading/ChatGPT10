# trend_alignment_strategy.py
from dataclasses import dataclass
from typing import Optional
import pandas as pd
from expiry_selector import select_expiry
from option_utils import get_atm_strike

@dataclass
class EntrySignal:
    direction: str
    underlying: str
    strike: int
    expiry: object
    reason: str

@dataclass
class ExitSignal:
    exit_now: bool
    reason: str

class TrendAlignmentStrategy:
    """
    "The Triple Alignment Breakout"
    Entry: Price > VWAP, Price > EMA20 (sloping up), RSI > 60, Volume > VOL_SMA20, and Candle breaks previous 3 candle highs.
    """
    def __init__(self, config):
        self.config = config
        self.name = "TRENDALIGN"

    def evaluate_entry(self, df: pd.DataFrame) -> Optional[EntrySignal]:
        if len(df) < 20:
            return None

        row = df.iloc[-1]
        prev = df.iloc[-2]

        # Trend and Momentum
        bullish_trend = (row["close"] > row["VWAP"]) and (row["close"] > row["EMA20"]) and (row["EMA20"] > prev["EMA20"])
        bearish_trend = (row["close"] < row["VWAP"]) and (row["close"] < row["EMA20"]) and (row["EMA20"] < prev["EMA20"])

        bullish_momentum = row["RSI"] > 65
        bearish_momentum = row["RSI"] < 35

        volume_burst = row["volume"] > row["VOL_SMA20"] * 1.2

        # Previous 3 candle highs/lows (excluding current)
        last_3 = df.iloc[-4:-1]
        prev_3_high = last_3["high"].max()
        prev_3_low = last_3["low"].min()

        # Bullish Breakout
        if bullish_trend and bullish_momentum and volume_burst and (row["close"] > prev_3_high):
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(
                direction="CALL",
                underlying="NIFTY",
                strike=atm,
                expiry=exp,
                reason=f"Triple Alignment Bullish: RSI={row['RSI']:.1f}, Vol Burst"
            )

        # Bearish Breakout
        if bearish_trend and bearish_momentum and volume_burst and (row["close"] < prev_3_low):
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(
                direction="PUT",
                underlying="NIFTY",
                strike=atm,
                expiry=exp,
                reason=f"Triple Alignment Bearish: RSI={row['RSI']:.1f}, Vol Burst"
            )

        return None

    def evaluate_exit(self, df: pd.DataFrame, position_state) -> ExitSignal:
        row = df.iloc[-1]

        # Exit if trend reverses or price crosses back over EMA20
        if position_state.direction == "CALL":
            if row["close"] < row["EMA20"]:
                return ExitSignal(exit_now=True, reason="Price closed below EMA20")
        else: # PUT
            if row["close"] > row["EMA20"]:
                return ExitSignal(exit_now=True, reason="Price closed above EMA20")

        return ExitSignal(exit_now=False, reason="Stay in trend")
