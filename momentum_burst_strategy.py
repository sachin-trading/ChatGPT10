# momentum_burst_strategy.py
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

class MomentumBurstStrategy:
    def __init__(self, config):
        self.config = config
        self.name = "MOMENTUM"

    def evaluate_entry(self, df: pd.DataFrame) -> Optional[EntrySignal]:
        row = df.iloc[-1]
        # RSI + large candle
        if row["RSI"] < 30:
            return None
        body = abs(row["close"] - row["open"])
        avg_body = (df["close"] - df["open"]).abs().rolling(20).mean().iloc[-1]
        if body > avg_body * 2 and row["close"] > row["open"] and row["EMA20"] > row["EMA50"]:
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(direction="CALL", underlying="NIFTY", strike=atm, expiry=exp, reason="Momentum burst up")
        if body > avg_body * 2 and row["close"] < row["open"] and row["EMA20"] < row["EMA50"]:
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(direction="PUT", underlying="NIFTY", strike=atm, expiry=exp, reason="Momentum burst down")
        return None

    def evaluate_exit(self, df, position_state):
        row = df.iloc[-1]
        # quick profit taking if RSI extreme or EMA cross
        if position_state.direction == "CALL" and (row["RSI"] > 75 or row["EMA20"] < row["EMA50"]):
            return ExitSignal(exit_now=True, reason="RSI/EMA exit")
        if position_state.direction == "PUT" and (row["RSI"] < 25 or row["EMA20"] > row["EMA50"]):
            return ExitSignal(exit_now=True, reason="RSI/EMA exit")
        return ExitSignal(exit_now=False, reason="none")
