# strategy_manager.py
import logging
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime

import config
from order_manager import OrderManager
from data_feed import DataFeed

# Import TrendAlignStrategy
from trend_align_strategy import TrendAlignStrategy

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

        # Risk management state
        self.daily_pnl_points = 0.0
        self.total_trades_today = 0
        self.trading_halted = False

        # Instantiate TRENDALIGN strategy
        self.strategies = {
            "TRENDALIGN": TrendAlignStrategy(config=config),
        }

    def run_strategies(self, df):
        if self.trading_halted:
            LOG.warning("Trading halted for the day due to risk limits.")
            return

        if self.daily_pnl_points <= -config.MAX_DAILY_LOSS_POINTS:
            LOG.error("MAX_DAILY_LOSS_POINTS reached. Halting trades.")
            self.trading_halted = True
            return

        if self.total_trades_today >= config.MAX_TRADES_PER_DAY:
            LOG.warning("MAX_TRADES_PER_DAY reached. Halting trades.")
            self.trading_halted = True
            return

        for name, strat in self.strategies.items():
            try:
                # prevent overlapping trades per strategy
                if name in self.active_positions:
                    continue

                entry = strat.evaluate_entry(df)
                if entry:
                    LOG.info("%s: entry signal: %s", name, entry)

                    # calculate required margin
                    lot_size = config.STRATEGY_LOTS.get(name, 1)
                    required_margin = self.order_mgr.estimate_margin(entry, lot_size)
                    avail = self.order_mgr.get_available_margin()

                    if avail < required_margin:
                        LOG.warning("%s: Not enough margin. Needed %s, Available %s", name, required_margin, avail)
                        continue

                    # build symbol
                    symbol = self.order_mgr.build_option_symbol(entry.underlying, entry.expiry, entry.strike, entry.direction)
                    qty = lot_size * config.INSTRUMENTS.get(entry.underlying, {}).get("lot_size", 1)

                    LOG.info("%s: placing market order for %s (%s Quantity)", name, symbol, qty)
                    order_resp = self.order_mgr.place_market_order(symbol=symbol, quantity=qty, direction=entry.direction, strategy=name)

                    if order_resp.get("status") in ("FILLED", "SIMULATED", "OK"):
                        self.total_trades_today += 1
                        entry_price = order_resp.get("avg_price") or order_resp.get("price") or 0.0

                        # Stop Loss and Take Profit
                        if entry.direction == "CALL":
                            sl = entry_price - config.STOP_LOSS_POINTS
                            tp = entry_price + config.TARGET_POINTS
                        else: # PUT
                            sl = entry_price - config.STOP_LOSS_POINTS
                            tp = entry_price + config.TARGET_POINTS

                        pos = PositionState(
                            strategy_name=name,
                            direction=entry.direction,
                            symbol=symbol,
                            quantity=qty,
                            entry_price=entry_price,
                            sl_price=sl,
                            tp_price=tp,
                            opened_at=datetime.now(),
                            meta={"reason": entry.reason}
                        )
                        self.active_positions[name] = pos
                        LOG.info("%s: position opened: %s", name, pos)
            except Exception as e:
                LOG.exception("Error while running strategy %s: %s", name, e)

    def monitor_positions(self, df):
        for name, pos in list(self.active_positions.items()):
            try:
                strat = self.strategies[name]
                exit_signal = strat.evaluate_exit(df, pos)

                # In live mode, we should fetch LTP for the option symbol
                # For now, we might use data_feed.get_last_price(pos.symbol)
                # but if data_feed only returns index price, we need to handle it.
                last_price = self.data_feed.get_last_price(pos.symbol)
                if last_price is None:
                    continue

                # Check SL/TP
                hit_sl = last_price <= pos.sl_price
                hit_tp = last_price >= pos.tp_price

                if hit_sl or hit_tp or (exit_signal and exit_signal.exit_now):
                    reason = "SL" if hit_sl else ("TP" if hit_tp else exit_signal.reason)
                    self._close_position(name, pos, reason=reason, exit_price=last_price)

            except Exception as e:
                LOG.exception("Error while monitoring position %s: %s", name, e)

    def _close_position(self, name, pos: PositionState, reason="MANUAL", exit_price=0.0):
        LOG.info("Closing position for %s (%s) reason=%s", name, pos.symbol, reason)
        resp = self.order_mgr.place_market_order(symbol=pos.symbol, quantity=pos.quantity, direction="SELL", strategy=name, closing=True)

        # Calculate PnL points
        pnl = exit_price - pos.entry_price
        self.daily_pnl_points += pnl

        LOG.info("%s: closed at %s, pnl points: %s. Daily total: %s", name, exit_price, pnl, self.daily_pnl_points)
        if name in self.active_positions:
            del self.active_positions[name]

    def close_all_positions(self):
        for name in list(self.active_positions.keys()):
            pos = self.active_positions[name]
            # Try to get last price for PnL tracking
            last_price = self.data_feed.get_last_price(pos.symbol) or pos.entry_price
            self._close_position(name, pos, reason="EOD", exit_price=last_price)
