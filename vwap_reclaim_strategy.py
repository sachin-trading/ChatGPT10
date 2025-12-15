# vwap_reclaim_strategy.py
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

class VWAPReclaimStrategy:
    def __init__(self, config):
        self.config = config
        self.name = "VWAP"

    def evaluate_entry(self, df: pd.DataFrame) -> Optional[EntrySignal]:
        row = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else row
        # price crosses above VWAP and holds above for 2 candles, trend EMA align
        if prev["close"] < prev["VWAP"] and row["close"] > row["VWAP"]:
            if row["EMA20"] > row["EMA50"]:
                atm = get_atm_strike(row["close"])
                exp = select_expiry()
                return EntrySignal(direction="CALL", underlying="NIFTY", strike=atm, expiry=exp, reason="VWAP reclaim bullish")
        if prev["close"] > prev["VWAP"] and row["close"] < row["VWAP"]:
            if row["EMA20"] < row["EMA50"]:
                atm = get_atm_strike(row["close"])
                exp = select_expiry()
                return EntrySignal(direction="PUT", underlying="NIFTY", strike=atm, expiry=exp, reason="VWAP reclaim bearish")
        return None

    def evaluate_exit(self, df, position_state):
        row = df.iloc[-1]
        if position_state.direction == "CALL" and row["close"] < row["VWAP"]:
            return ExitSignal(exit_now=True, reason="VWAP cross")
        if position_state.direction == "PUT" and row["close"] > row["VWAP"]:
            return ExitSignal(exit_now=True, reason="VWAP cross")
        return ExitSignal(exit_now=False, reason="none")
