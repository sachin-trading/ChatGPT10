# strategy_manager.py
import logging
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime

import config
from order_manager import OrderManager
from data_feed import DataFeed

# Import strategy classes
from tcb_strategy import TCBStrategy
from vwap_reclaim_strategy import VWAPReclaimStrategy
from pcr_extreme_strategy import PCRExtremeStrategy
from orb_strategy import ORBStrategy
from iv_crush_strategy import IVCrushStrategy
from market_profile_strategy import MarketProfileStrategy
from momentum_burst_strategy import MomentumBurstStrategy
from smc_liquidity_sweep_strategy import SMCLiquiditySweepStrategy
from low_iv_rank_strategy import LowIVRankStrategy
from delta_scalping_strategy import DeltaScalpingStrategy

LOG = logging.getLogger("strategy_manager")


@dataclass
class PositionState:
    strategy_name: str
    direction: str
    symbol: str
    quantity: int
    entry_price: float
    sl_price: float
    tp_price: float
    opened_at: datetime
    meta: dict


class StrategyManager:
    def __init__(self, order_mgr: OrderManager, data_feed: DataFeed):
        self.order_mgr = order_mgr
        self.data_feed = data_feed
        self.active_positions: Dict[str, PositionState] = {}  # keyed by strategy name

        # instantiate strategies
        self.strategies = {
            "TCB": TCBStrategy(config=config),
            "VWAP": VWAPReclaimStrategy(config=config),
            "PCR": PCRExtremeStrategy(config=config, data_feed=self.data_feed),
            "ORB": ORBStrategy(config=config),
            "IVCRUSH": IVCrushStrategy(config=config),
            "MARKETPROFILE": MarketProfileStrategy(config=config),
            "MOMENTUM": MomentumBurstStrategy(config=config),
            "SMC": SMCLiquiditySweepStrategy(config=config),
            "LOWIV": LowIVRankStrategy(config=config, data_feed=self.data_feed),
            "DELTASCALP": DeltaScalpingStrategy(config=config),
        }

    def run_strategies(self, df):
        for name, strat in self.strategies.items():
            try:
                # prevent overlapping trades per strategy
                if name in self.active_positions:
                    LOG.debug("%s: active position exists; skipping new entry check", name)
                    continue

                entry = strat.evaluate_entry(df)
                if entry:
                    LOG.info("%s: entry signal: %s", name, entry)
                    # calculate required margin
                    lot_size = config.STRATEGY_LOTS.get(name, 1)
                    required_margin = self.order_mgr.estimate_margin(entry, lot_size)
                    avail = self.order_mgr.get_available_margin()
                    LOG.debug("%s: required_margin=%s available=%s", name, required_margin, avail)
                    if avail < required_margin:
                        LOG.warning("%s: Not enough margin. Needed %s, Available %s", name, required_margin, avail)
                        continue

                    # build symbol
                    symbol = self.order_mgr.build_option_symbol(entry.underlying, entry.expiry, entry.strike, entry.direction)
                    qty = lot_size * config.INSTRUMENTS.get(entry.underlying, {}).get("lot_size", 1)
                    print("%s: placing market order for %s (%s Quantity)",name, symbol, qty)
                    order_resp = self.order_mgr.place_market_order(symbol=symbol, quantity=qty, direction=entry.direction, strategy=name)
                    print(order_resp)
                    if order_resp.get("status") in ("FILLED", "SIMULATED", "OK"):
                        # Create PositionState
                        entry_price = order_resp.get("avg_price") or order_resp.get("price") or 0.0
                        sl = entry_price - config.STOP_LOSS_POINTS if entry.direction == "PUT" else entry_price - config.STOP_LOSS_POINTS
                        tp = entry_price + config.TARGET_POINTS if entry.direction == "PUT" else entry_price + config.TARGET_POINTS
                        pos = PositionState(strategy_name=name, direction=entry.direction,
                                            symbol=symbol, quantity=qty, entry_price=entry_price,
                                            sl_price=entry_price - config.STOP_LOSS_POINTS if entry.direction == "CALL" else entry_price + config.STOP_LOSS_POINTS,
                                            tp_price=entry_price + config.TARGET_POINTS if entry.direction == "CALL" else entry_price - config.TARGET_POINTS,
                                            opened_at=datetime.now(),
                                            meta={"reason": entry.reason})
                        self.active_positions[name] = pos
                        LOG.info("%s: position opened: %s", name, pos)
            except Exception as e:
                LOG.exception("Error while running strategy %s: %s", name, e)

    def monitor_positions(self, df):
        for name, pos in list(self.active_positions.items()):
            try:
                strat = self.strategies[name]
                exit_signal = strat.evaluate_exit(df, pos)
                # check SL/TP with latest market price
                last_price = self.data_feed.get_last_price(pos.symbol)
                if last_price is None:
                    continue
                # SL hit
                if pos.direction == "CALL":
                    if last_price <= pos.sl_price or exit_signal and exit_signal.exit_now:
                        self._close_position(name, pos, reason="SL/ExitSignal")
                        continue
                    if last_price >= pos.tp_price:
                        self._close_position(name, pos, reason="TP")
                        continue
                else:  # PUT or SELL direction semantics (we assume same numeric comparison for simplicity)
                    if last_price >= pos.sl_price or exit_signal and exit_signal.exit_now:
                        self._close_position(name, pos, reason="SL/ExitSignal")
                        continue
                    if last_price <= pos.tp_price:
                        self._close_position(name, pos, reason="TP")
                        continue
            except Exception as e:
                LOG.exception("Error while monitoring position %s: %s", name, e)

    def _close_position(self, name, pos: PositionState, reason="MANUAL"):
        LOG.info("Closing position for %s (%s) reason=%s", name, pos.symbol, reason)
        resp = self.order_mgr.place_market_order(symbol=pos.symbol, quantity=pos.quantity, direction="SELL" if pos.direction == "CALL" else "BUY", strategy=name, closing=True)
        LOG.info("%s: close response: %s", name, resp)
        del self.active_positions[name]

    def close_all_positions(self):
        for name in list(self.active_positions.keys()):
            pos = self.active_positions[name]
            self._close_position(name, pos, reason="EOD")
