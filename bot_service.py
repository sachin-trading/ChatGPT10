# bot_service.py
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

import config
import fyers_auth
from data_feed import DataFeed
from strategy_manager import StrategyManager, PositionState
from order_manager import OrderManager

LOG = logging.getLogger("bot_service")

class BotService:
    def __init__(self):
        self.data_feed: Optional[DataFeed] = None
        self.order_mgr: Optional[OrderManager] = None
        self.strat_mgr: Optional[StrategyManager] = None
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.last_run_time: Optional[datetime] = None
        self._stop_event = threading.Event()
        self.disabled_strategies: List[str] = []

    def initialize(self):
        LOG.info("Initializing Bot Service")
        token = fyers_auth.ensure_access_token()
        self.data_feed = DataFeed()
        self.order_mgr = OrderManager(access_token=token)
        self.strat_mgr = StrategyManager(order_mgr=self.order_mgr, data_feed=self.data_feed)
        LOG.info("Bot Service Initialized")

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        LOG.info("Bot Service Started")

    def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        self._stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        LOG.info("Bot Service Stopped")

    def _run_loop(self):
        LOG.info("Bot loop started")
        while not self._stop_event.is_set():
            try:
                if not self.strat_mgr:
                    time.sleep(1)
                    continue

                now = datetime.now()
                must_exit_time = datetime.strptime(config.MUST_EXIT_TIME, "%H:%M").time()

                if now.time() >= must_exit_time:
                    LOG.info("Market past MUST_EXIT_TIME - closing all positions")
                    self.strat_mgr.close_all_positions()
                    # We don't stop the loop, just wait for next day or manual stop
                    time.sleep(60)
                    continue

                def within_trading_hours():
                    now_time = datetime.now().time()
                    start = datetime.strptime(config.TRADE_START_TIME, "%H:%M").time()
                    end = datetime.strptime(config.MUST_EXIT_TIME, "%H:%M").time()
                    return start <= now_time <= end

                if not within_trading_hours():
                    time.sleep(30)
                    continue

                df = self.data_feed.get_latest_5m()
                if df is None or df.empty:
                    time.sleep(10)
                    continue

                self.data_feed.compute_indicators(df)

                # Filter out disabled strategies before running
                original_strategies = self.strat_mgr.strategies
                active_strats = {k: v for k, v in original_strategies.items() if k not in self.disabled_strategies}

                # Temporarily replace strategies for this run
                self.strat_mgr.strategies = active_strats
                self.strat_mgr.run_strategies(df)
                self.strat_mgr.monitor_positions(df)

                # Restore original strategies
                self.strat_mgr.strategies = original_strategies

                self.last_run_time = datetime.now()
                time.sleep(10)
            except Exception as e:
                LOG.exception("Error in bot loop: %s", e)
                time.sleep(10)

    def get_status(self) -> Dict:
        return {
            "is_running": self.is_running,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "active_positions_count": len(self.strat_mgr.active_positions) if self.strat_mgr else 0,
            "disabled_strategies": self.disabled_strategies
        }

    def get_positions(self) -> List[Dict]:
        if not self.strat_mgr:
            return []
        positions = []
        for name, pos in self.strat_mgr.active_positions.items():
            positions.append({
                "strategy": pos.strategy_name,
                "symbol": pos.symbol,
                "direction": pos.direction,
                "quantity": pos.quantity,
                "entry_price": pos.entry_price,
                "sl_price": pos.sl_price,
                "tp_price": pos.tp_price,
                "opened_at": pos.opened_at.isoformat(),
                "pnl": self._calculate_pnl(pos)
            })
        return positions

    def _calculate_pnl(self, pos: PositionState) -> float:
        last_price = self.data_feed.get_last_price(pos.symbol)
        if last_price is None:
            return 0.0
        if pos.direction == "CALL" or pos.direction == "BUY":
            return (last_price - pos.entry_price) * pos.quantity
        else:
            return (pos.entry_price - last_price) * pos.quantity

    def toggle_strategy(self, name: str, enabled: bool):
        if enabled:
            if name in self.disabled_strategies:
                self.disabled_strategies.remove(name)
        else:
            if name not in self.disabled_strategies:
                self.disabled_strategies.append(name)

    def get_strategies(self) -> List[Dict]:
        if not self.strat_mgr:
            return []

        strategies = []
        for name in self.strat_mgr.strategies.keys():
            strategies.append({
                "name": name,
                "enabled": name not in self.disabled_strategies,
                "active_position": name in self.strat_mgr.active_positions
            })
        return strategies

# Global instance
bot_service = BotService()
