# market_profile_strategy.py
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

class MarketProfileStrategy:
    def __init__(self, config):
        self.config = config
        self.name = "MARKETPROFILE"

    def evaluate_entry(self, df: pd.DataFrame) -> Optional[EntrySignal]:
        # Simplified market profile imbalance detection:
        # If recent candles show single prints (gaps) and break in value area high/low
        last = df.tail(20)
        vah = last["high"].quantile(0.7)
        val = last["low"].quantile(0.3)
        row = df.iloc[-1]
        if row["close"] > vah:
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(direction="CALL", underlying="NIFTY", strike=atm, expiry=exp, reason="MP break VAH")
        if row["close"] < val:
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(direction="PUT", underlying="NIFTY", strike=atm, expiry=exp, reason="MP break VAL")
        return None

    def evaluate_exit(self, df, position_state):
        row = df.iloc[-1]
        if position_state.direction == "CALL" and row["close"] < row["EMA20"]:
            return ExitSignal(exit_now=True, reason="EMA20 cross")
        if position_state.direction == "PUT" and row["close"] > row["EMA20"]:
            return ExitSignal(exit_now=True, reason="EMA20 cross")
        return ExitSignal(exit_now=False, reason="none")
