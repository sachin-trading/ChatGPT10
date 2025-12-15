# tcb_strategy.py
from dataclasses import dataclass
from typing import Optional
import pandas as pd

@dataclass
class EntrySignal:
    direction: str  # "CALL" or "PUT"
    underlying: str
    strike: int
    expiry: object
    reason: str

@dataclass
class ExitSignal:
    exit_now: bool
    reason: str

class TCBStrategy:
    def __init__(self, config):
        self.config = config
        self.name = "TCB"

    def evaluate_entry(self, df: pd.DataFrame) -> Optional[EntrySignal]:
        # require last row indicators
        row = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else row
        # Squeeze: BB inside KC
        squeeze = (row["BB_H"] < row["KC_H"]) and (row["BB_L"] > row["KC_L"])
        trend_up = row["EMA20"] > row["EMA50"]
        breakout_up = row["close"] > row["BB_H"]
        vol_ok = row["volume"] > df["volume"].rolling(20).mean().iloc[-1]
        if squeeze and trend_up and breakout_up and vol_ok:
            # build ATM
            from option_utils import get_atm_strike
            atm = get_atm_strike(row["close"])
            from expiry_selector import select_expiry
            exp = select_expiry()
            return EntrySignal(direction="CALL", underlying="NIFTY", strike=atm, expiry=exp, reason="TCB breakout up")
        # down side
        trend_down = row["EMA20"] < row["EMA50"]
        breakout_dn = row["close"] < row["BB_L"]
        if squeeze and trend_down and breakout_dn and vol_ok:
            from option_utils import get_atm_strike
            atm = get_atm_strike(row["close"])
            from expiry_selector import select_expiry
            exp = select_expiry()
            return EntrySignal(direction="PUT", underlying="NIFTY", strike=atm, expiry=exp, reason="TCB breakout down")
        return None

    def evaluate_exit(self, df, position_state):
        # lightweight exit: if EMA cross opposite or time-based
        row = df.iloc[-1]
        if position_state.strategy_name != self.name:
            return ExitSignal(exit_now=False, reason="not mine")
        if position_state.direction == "CALL" and row["EMA20"] < row["EMA50"]:
            return ExitSignal(exit_now=True, reason="EMA cross")
        if position_state.direction == "PUT" and row["EMA20"] > row["EMA50"]:
            return ExitSignal(exit_now=True, reason="EMA cross")
        return ExitSignal(exit_now=False, reason="none")
