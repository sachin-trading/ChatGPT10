# crude_trend_strategy.py
from dataclasses import dataclass
from typing import Optional
import pandas as pd
import logging
from datetime import datetime

LOG = logging.getLogger("crude_trend")

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

class CrudeTrendStrategy:
    def __init__(self, config):
        self.config = config
        self.name = "CRUDETREND"
        self.underlying = "CRUDEOIL"

    def evaluate_entry(self, df: pd.DataFrame) -> Optional[EntrySignal]:
        if len(df) < 21:
            return None

        row = df.iloc[-1]

        # Time filter: MCX Crude is best after 17:00 IST
        current_time = row["datetime"].time()
        if current_time < datetime.strptime("17:00", "%H:%M").time():
            return None

        # 1. VWAP Alignment
        vwap_call = row["close"] > row["VWAP"]
        vwap_put = row["close"] < row["VWAP"]

        # 2. EMA 9/21 Crossover/Alignment
        ema_call = row["EMA9"] > row["EMA21"]
        ema_put = row["EMA9"] < row["EMA21"]

        # 3. RSI Momentum (Stronger filters for crude)
        rsi_call = row["RSI"] > 60
        rsi_put = row["RSI"] < 40

        # CALL Signal
        if vwap_call and ema_call and rsi_call:
            from option_utils import get_atm_strike
            # Crude Oil step is usually 100 or 50
            atm = get_atm_strike(row["close"], step=50)
            from expiry_selector import select_expiry
            exp = select_expiry(underlying="CRUDEOIL")
            return EntrySignal(
                direction="CALL",
                underlying="CRUDEOIL",
                strike=atm,
                expiry=exp,
                reason="Crude Trend Alignment (CALL)"
            )

        # PUT Signal
        if vwap_put and ema_put and rsi_put:
            from option_utils import get_atm_strike
            atm = get_atm_strike(row["close"], step=50)
            from expiry_selector import select_expiry
            exp = select_expiry(underlying="CRUDEOIL")
            return EntrySignal(
                direction="PUT",
                underlying="CRUDEOIL",
                strike=atm,
                expiry=exp,
                reason="Crude Trend Alignment (PUT)"
            )

        return None

    def evaluate_exit(self, df: pd.DataFrame, position_state) -> ExitSignal:
        if position_state.strategy_name != self.name:
            return ExitSignal(exit_now=False, reason="not mine")

        row = df.iloc[-1]

        # Exit on EMA crossover or if price crosses back over VWAP
        if position_state.direction == "CALL":
            if row["EMA9"] < row["EMA21"] or row["close"] < row["VWAP"]:
                return ExitSignal(exit_now=True, reason="EMA cross/VWAP breach")
        else: # PUT
            if row["EMA9"] > row["EMA21"] or row["close"] > row["VWAP"]:
                return ExitSignal(exit_now=True, reason="EMA cross/VWAP breach")

        return ExitSignal(exit_now=False, reason="Hold")
