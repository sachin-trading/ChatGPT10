# low_iv_rank_strategy.py
from dataclasses import dataclass
from typing import Optional
import pandas as pd
from expiry_selector import select_expiry
from option_utils import get_atm_strike
from data_feed import DataFeed

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

class LowIVRankStrategy:
    def __init__(self, config):
        self.config = config
        self.name = "LOWIV"

    def evaluate_entry(self, df: pd.DataFrame) -> Optional[EntrySignal]:
        # IV Rank not available -> use dummy low IV condition
        data_feed = DataFeed()
        pcr = data_feed.fetch_pcr()  # not IV rank but placeholder
        row = df.iloc[-1]
        if pcr < 0.9 and row["EMA20"] > row["EMA50"]:
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(direction="CALL", underlying="NIFTY", strike=atm, expiry=exp, reason="Low IV rank trend")
        if pcr < 0.9 and row["EMA20"] < row["EMA50"]:
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(direction="PUT", underlying="NIFTY", strike=atm, expiry=exp, reason="Low IV rank trend")
        return None

    def evaluate_exit(self, df, position_state):
        row = df.iloc[-1]
        if position_state.direction == "CALL" and row["close"] < row["EMA20"]:
            return ExitSignal(exit_now=True, reason="EMA20 cross")
        if position_state.direction == "PUT" and row["close"] > row["EMA20"]:
            return ExitSignal(exit_now=True, reason="EMA20 cross")
        return ExitSignal(exit_now=False, reason="none")
