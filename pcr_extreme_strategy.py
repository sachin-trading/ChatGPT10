# pcr_extreme_strategy.py
from dataclasses import dataclass
from typing import Optional
import pandas as pd
from data_feed import DataFeed
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

class PCRExtremeStrategy:
    def __init__(self, config):
        self.config = config
        self.name = "PCR"
        self.df = None

    def evaluate_entry(self, df: pd.DataFrame) -> Optional[EntrySignal]:
        # fetch PCR
        data_feed = DataFeed()
        pcr = data_feed.fetch_pcr()
        row = df.iloc[-1]
        if pcr < 0.75 and row["close"] < row["VWAP"]:
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(direction="PUT", underlying="NIFTY", strike=atm, expiry=exp, reason=f"PCR low {pcr}")
        if pcr > 1.25 and row["close"] > row["VWAP"]:
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(direction="CALL", underlying="NIFTY", strike=atm, expiry=exp, reason=f"PCR high {pcr}")
        return None

    def evaluate_exit(self, df, position_state):
        row = df.iloc[-1]
        if position_state.direction == "CALL" and row["close"] < row["VWAP"]:
            return ExitSignal(exit_now=True, reason="VWAP flip")
        if position_state.direction == "PUT" and row["close"] > row["VWAP"]:
            return ExitSignal(exit_now=True, reason="VWAP flip")
        return ExitSignal(exit_now=False, reason="none")
