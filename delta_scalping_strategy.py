# delta_scalping_strategy.py
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

class DeltaScalpingStrategy:
    def __init__(self, config):
        self.config = config
        self.name = "DELTASCALP"

    def _approx_delta(self, strike, spot):
        # rough approximation: ATM ~0.5, moves by 0.01 per (step/100)
        diff = abs(spot - strike)
        return max(0.0, min(1.0, 0.5 - (diff / max(1, strike)) * 10))

    def evaluate_entry(self, df: pd.DataFrame) -> Optional[EntrySignal]:
        row = df.iloc[-1]
        atm = get_atm_strike(row["close"])
        delta = self._approx_delta(atm, row["close"])
        if 0.4 <= delta <= 0.6 and row["EMA20"] > row["EMA50"]:
            exp = select_expiry()
            return EntrySignal(direction="CALL", underlying="NIFTY", strike=atm, expiry=exp, reason=f"Delta scalp buy delta={delta:.2f}")
        if 0.4 <= delta <= 0.6 and row["EMA20"] < row["EMA50"]:
            exp = select_expiry()
            return EntrySignal(direction="PUT", underlying="NIFTY", strike=atm, expiry=exp, reason=f"Delta scalp sell delta={delta:.2f}")
        return None

    def evaluate_exit(self, df, position_state):
        row = df.iloc[-1]
        # super tight exit based on small move of underlying
        last_price = row["close"]
        entry_index = position_state.meta.get("entry_index_price", last_price)

        if position_state.direction == "CALL" and last_price >= entry_index + 20:
            return ExitSignal(exit_now=True, reason="scalp TP underlying")
        if position_state.direction == "PUT" and last_price <= entry_index - 20:
            return ExitSignal(exit_now=True, reason="scalp TP underlying")
        return ExitSignal(exit_now=False, reason="none")
