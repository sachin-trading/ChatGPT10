# trend_align_strategy.py
from dataclasses import dataclass
from typing import Optional
import pandas as pd
import logging

LOG = logging.getLogger("trend_align")

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

class TrendAlignStrategy:
    def __init__(self, config):
        self.config = config
        self.name = "TRENDALIGN"

    def evaluate_entry(self, df: pd.DataFrame) -> Optional[EntrySignal]:
        if len(df) < 21:
            return None

        row = df.iloc[-1]
        prev = df.iloc[-2]

        # 1. VWAP Alignment
        vwap_call = row["close"] > row["VWAP"]
        vwap_put = row["close"] < row["VWAP"]

        # 2. 20 EMA Slope/Position
        ema20_slope = row["EMA20"] - prev["EMA20"]
        ema_call = (row["close"] > row["EMA20"]) and (ema20_slope > 0)
        ema_put = (row["close"] < row["EMA20"]) and (ema20_slope < 0)

        # 3. RSI Momentum
        rsi_call = row["RSI"] > 65
        rsi_put = row["RSI"] < 35

        # 4. Volume Confirmation (> 1.2x its 20-period SMA)
        vol_ok = row["volume"] > (1.2 * row["VOL_SMA20"])

        # CALL Signal
        if vwap_call and ema_call and rsi_call and vol_ok:
            from option_utils import get_atm_strike
            atm = get_atm_strike(row["close"])
            from expiry_selector import select_expiry
            exp = select_expiry()
            return EntrySignal(
                direction="CALL",
                underlying="NIFTY",
                strike=atm,
                expiry=exp,
                reason="Triple Alignment Breakout (CALL)"
            )

        # PUT Signal
        if vwap_put and ema_put and rsi_put and vol_ok:
            from option_utils import get_atm_strike
            atm = get_atm_strike(row["close"])
            from expiry_selector import select_expiry
            exp = select_expiry()
            return EntrySignal(
                direction="PUT",
                underlying="NIFTY",
                strike=atm,
                expiry=exp,
                reason="Triple Alignment Breakout (PUT)"
            )

        return None

    def evaluate_exit(self, df: pd.DataFrame, position_state) -> ExitSignal:
        if position_state.strategy_name != self.name:
            return ExitSignal(exit_now=False, reason="not mine")

        row = df.iloc[-1]

        # Simple exit if price crosses back over EMA20 or VWAP
        if position_state.direction == "CALL":
            if row["close"] < row["EMA20"] or row["close"] < row["VWAP"]:
                return ExitSignal(exit_now=True, reason="Price below EMA20/VWAP")
        else: # PUT
            if row["close"] > row["EMA20"] or row["close"] > row["VWAP"]:
                return ExitSignal(exit_now=True, reason="Price above EMA20/VWAP")

        return ExitSignal(exit_now=False, reason="Hold")
