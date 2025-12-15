# smc_liquidity_sweep_strategy.py
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

class SMCLiquiditySweepStrategy:
    def __init__(self, config):
        self.config = config
        self.name = "SMC"

    def evaluate_entry(self, df: pd.DataFrame) -> Optional[EntrySignal]:
        # Sweep detection: wick beyond recent highs followed by BOS (break of structure)
        highs = df["high"].rolling(5).max()
        lows = df["low"].rolling(5).min()
        row = df.iloc[-1]
        prev_high = highs.iloc[-2] if len(highs) >= 2 else highs.iloc[-1]
        prev_low = lows.iloc[-2] if len(lows) >= 2 else lows.iloc[-1]
        # buy sweep: price makes a lower wick below prev low and then closes above prev_low
        if row["low"] < prev_low and row["close"] > prev_low and row["EMA20"] > row["EMA50"]:
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(direction="CALL", underlying="NIFTY", strike=atm, expiry=exp, reason="Liquidity sweep buy")
        if row["high"] > prev_high and row["close"] < prev_high and row["EMA20"] < row["EMA50"]:
            atm = get_atm_strike(row["close"])
            exp = select_expiry()
            return EntrySignal(direction="PUT", underlying="NIFTY", strike=atm, expiry=exp, reason="Liquidity sweep sell")
        return None

    def evaluate_exit(self, df, position_state):
        row = df.iloc[-1]
        if position_state.direction == "CALL" and row["close"] < row["EMA20"]:
            return ExitSignal(exit_now=True, reason="EMA exit")
        if position_state.direction == "PUT" and row["close"] > row["EMA20"]:
            return ExitSignal(exit_now=True, reason="EMA exit")
        return ExitSignal(exit_now=False, reason="none")
