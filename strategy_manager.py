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
from crude_trend_strategy import CrudeTrendStrategy

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
    underlying: str = "NIFTY"


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
            "CRUDETREND": CrudeTrendStrategy(config=config),
        }

        # Default underlying for old strategies
        for name, strat in self.strategies.items():
            if not hasattr(strat, "underlying"):
                strat.underlying = "NIFTY"

    def run_strategies(self, df, underlying: str):
        """
        Run strategies that are configured for the given underlying.
        """
        for name, strat in self.strategies.items():
            if strat.underlying != underlying:
                continue

            try:
                # prevent overlapping trades per strategy
                if name in self.active_positions:
                    continue

                entry = strat.evaluate_entry(df)
                if entry:
                    LOG.info("%s: entry signal: %s", name, entry)

                    # Get instrument config
                    inst_config = config.INSTRUMENTS.get(entry.underlying, {})
                    lot_size = config.STRATEGY_LOTS.get(name, 1)

                    # calculate required margin
                    required_margin = self.order_mgr.estimate_margin(entry, lot_size)
                    avail = self.order_mgr.get_available_margin()

                    if avail < required_margin:
                        LOG.warning("%s: Not enough margin. Needed %s, Available %s", name, required_margin, avail)
                        continue

                    # build symbol
                    symbol = self.order_mgr.build_option_symbol(entry.underlying, entry.expiry, entry.strike, entry.direction)
                    qty = lot_size * inst_config.get("lot_size", 1)

                    LOG.info("%s: placing market order for %s (%s Quantity)", name, symbol, qty)
                    order_resp = self.order_mgr.place_market_order(symbol=symbol, quantity=qty, direction=entry.direction, strategy=name)

                    if order_resp.get("status") in ("FILLED", "SIMULATED", "OK"):
                        entry_price = order_resp.get("avg_price") or order_resp.get("price") or 0.0

                        # SL/TP calculation (Instrument-specific)
                        sl_pts = inst_config.get("sl_points", 25)
                        tp_pts = inst_config.get("tp_points", 35)

                        # For LONG options (BUY CALL or BUY PUT), profit is when price INCREASES
                        sl = entry_price - sl_pts
                        tp = entry_price + tp_pts

                        pos = PositionState(strategy_name=name, direction=entry.direction,
                                            symbol=symbol, quantity=qty, entry_price=entry_price,
                                            sl_price=sl, tp_price=tp,
                                            opened_at=datetime.now(),
                                            meta={"reason": entry.reason},
                                            underlying=underlying)
                        self.active_positions[name] = pos
                        LOG.info("%s: position opened: %s", name, pos)
            except Exception as e:
                LOG.exception("Error while running strategy %s: %s", name, e)

    def monitor_positions(self, df, underlying: str):
        """
        Monitor only positions belonging to the given underlying using the provided DF (index data).
        """
        for name, pos in list(self.active_positions.items()):
            if pos.underlying != underlying:
                continue

            try:
                strat = self.strategies[name]
                exit_signal = strat.evaluate_exit(df, pos)

                # Get latest market price for the OPTION symbol
                last_price = self.data_feed.get_last_price(pos.symbol)
                if last_price is None:
                    continue

                # Check SL/TP
                if last_price <= pos.sl_price:
                    self._close_position(name, pos, reason="SL")
                    continue
                if last_price >= pos.tp_price:
                    self._close_position(name, pos, reason="TP")
                    continue

                if exit_signal and exit_signal.exit_now:
                    self._close_position(name, pos, reason=exit_signal.reason)

            except Exception as e:
                LOG.exception("Error while monitoring position %s: %s", name, e)

    def close_positions_for_underlying(self, underlying: str):
        LOG.info("Closing all positions for underlying: %s", underlying)
        for name, pos in list(self.active_positions.items()):
            if pos.underlying == underlying:
                self._close_position(name, pos, reason="EOD")

    def _close_position(self, name, pos: PositionState, reason="MANUAL"):
        LOG.info("Closing position for %s (%s) reason=%s", name, pos.symbol, reason)
        # Assuming we always exit by selling what we bought
        resp = self.order_mgr.place_market_order(symbol=pos.symbol, quantity=pos.quantity, direction="SELL", strategy=name, closing=True)
        LOG.info("%s: close response: %s", name, resp)
        if name in self.active_positions:
            del self.active_positions[name]

    def close_all_positions(self):
        for name in list(self.active_positions.keys()):
            pos = self.active_positions[name]
            self._close_position(name, pos, reason="GLOBAL_EXIT")
