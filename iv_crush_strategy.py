# iv_crush_strategy.py
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

class IVCrushStrategy:
    def __init__(self, config):
        self.config = config
        self.name = "IVCRUSH"

    def evaluate_entry(self, df: pd.DataFrame) -> Optional[EntrySignal]:
        # For simplicity, detect a strong candle with drop in implied volatility
        # Since we don't have IV in DF, use ATR drop as proxy for IV crush moment after event
        row = df.iloc[-1]
        atr_now = row.get("ATR14", 0.0)
        atr_prev = df["ATR14"].iloc[-2] if len(df) >= 2 else atr_now
        if atr_now < atr_prev * 0.7 and row["close"] > row["VWAP"]:
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(direction="CALL", underlying="NIFTY", strike=atm, expiry=exp, reason="Post-event IV crush bullish (ATR proxy)")
        if atr_now < atr_prev * 0.7 and row["close"] < row["VWAP"]:
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(direction="PUT", underlying="NIFTY", strike=atm, expiry=exp, reason="Post-event IV crush bearish (ATR proxy)")
        return None

    def evaluate_exit(self, df, position_state):
        row = df.iloc[-1]
        # quick exit on reversal across VWAP
        if position_state.direction == "CALL" and row["close"] < row["VWAP"]:
            return ExitSignal(exit_now=True, reason="VWAP reverse")
        if position_state.direction == "PUT" and row["close"] > row["VWAP"]:
            return ExitSignal(exit_now=True, reason="VWAP reverse")
        return ExitSignal(exit_now=False, reason="none")
