# orb_strategy.py
from dataclasses import dataclass
from typing import Optional
import pandas as pd
from expiry_selector import select_expiry
from option_utils import get_atm_strike
import datetime

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

class ORBStrategy:
    def __init__(self, config):
        self.config = config
        self.name = "ORB"
        self.orb_high = None
        self.orb_low = None
        self.orb_computed_date = None

    def _compute_orb(self, df):
        # first 15 minutes: find first 3 x 5m candles (15 minutes)
        first_3 = df.iloc[:3]
        self.orb_high = float(first_3["high"].max())
        self.orb_low = float(first_3["low"].min())
        self.orb_computed_date = df["datetime"].iloc[0].date()

    def evaluate_entry(self, df: pd.DataFrame):
        if self.orb_computed_date != df["datetime"].iloc[0].date():
            self._compute_orb(df)
        row = df.iloc[-1]
        if row["close"] > self.orb_high and row["EMA20"] > row["EMA50"]:
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(direction="CALL", underlying="NIFTY", strike=atm, expiry=exp, reason="ORB breakout up")
        if row["close"] < self.orb_low and row["EMA20"] < row["EMA50"]:
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(direction="PUT", underlying="NIFTY", strike=atm, expiry=exp, reason="ORB breakout down")
        return None

    def evaluate_exit(self, df, position_state):
        # time based or VWAP cross
        row = df.iloc[-1]
        if position_state.direction == "CALL" and row["close"] < row["VWAP"]:
            return ExitSignal(exit_now=True, reason="VWAP cross")
        if position_state.direction == "PUT" and row["close"] > row["VWAP"]:
            return ExitSignal(exit_now=True, reason="VWAP cross")
        # EOD handled by manager
        return ExitSignal(exit_now=False, reason="none")
