# crude_oil_strategy.py
from dataclasses import dataclass
from typing import Optional
import pandas as pd
import logging
from datetime import datetime

LOG = logging.getLogger("crude_strategy")

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

class CrudeTrendStrategy:
    def __init__(self, config):
        self.config = config
        self.name = "CRUDETREND"

    def evaluate_entry(self, df: pd.DataFrame) -> Optional[EntrySignal]:
        if len(df) < 25:
            return None

        row = df.iloc[-1]

        # Crude Oil is most volatile and trends best during US session (Evening in India)
        now = datetime.now().time()
        is_evening_session = now >= datetime.strptime("17:00", "%H:%M").time()

        if not is_evening_session:
            return None

        # Indicators
        # Assuming indicators.py adds EMA9, EMA21, VWAP, RSI, VOL_SMA20
        # I will use EMA20 and EMA50 which are already in indicators.py for now

        vwap_call = row["close"] > row["VWAP"]
        vwap_put = row["close"] < row["VWAP"]

        ema_call = row["EMA20"] > row["EMA50"]
        ema_put = row["EMA20"] < row["EMA50"]

        rsi_call = row["RSI"] > 60
        rsi_put = row["RSI"] < 40

        vol_ok = row["volume"] > (1.5 * row["VOL_SMA20"])

        if vwap_call and ema_call and rsi_call and vol_ok:
            from option_utils import get_atm_strike
            # Crude Oil strike step is usually 50 or 100.
            atm = get_atm_strike(row["close"], step=100)
            from expiry_selector import select_expiry
            exp = select_expiry() # Needs adjustment for MCX
            return EntrySignal(
                direction="CALL",
                underlying="CRUDEOIL",
                strike=atm,
                expiry=exp,
                reason="Crude Evening Momentum (CALL)"
            )

        if vwap_put and ema_put and rsi_put and vol_ok:
            from option_utils import get_atm_strike
            atm = get_atm_strike(row["close"], step=100)
            from expiry_selector import select_expiry
            exp = select_expiry()
            return EntrySignal(
                direction="PUT",
                underlying="CRUDEOIL",
                strike=atm,
                expiry=exp,
                reason="Crude Evening Momentum (PUT)"
            )

        return None

    def evaluate_exit(self, df: pd.DataFrame, position_state) -> ExitSignal:
        row = df.iloc[-1]

        # Exit if trend weakens (EMA cross back or RSI neutral)
        if position_state.direction == "CALL":
            if row["close"] < row["EMA20"] or row["RSI"] < 50:
                return ExitSignal(exit_now=True, reason="Trend weakening")
        else: # PUT
            if row["close"] > row["EMA20"] or row["RSI"] > 50:
                return ExitSignal(exit_now=True, reason="Trend weakening")

        return ExitSignal(exit_now=False, reason="Hold")
