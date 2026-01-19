import unittest
import os
from trading_bot.core.db import DatabaseManager
from trading_bot.core.trade_manager import TradeManager

class TestTradeManager(unittest.TestCase):
    def setUp(self):
        self.db_path = "trading_bot/data/test_trading.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = DatabaseManager(self.db_path)
        self.tm = TradeManager(self.db)

    def test_long_trade_lifecycle(self):
        trade_id = self.tm.create_trade("TEST_SYMBOL", "TEST_STRAT", "PAPER", 100, "BUY")
        order_id = "ORDER_ENTRY_1"
        self.tm.add_order(trade_id, order_id, "TEST_SYMBOL", "BUY", 100, 100.0, "PENDING")
        self.tm.update_order_status(order_id, "FILLED", 100.0)

        exit_order_id = "ORDER_EXIT_1"
        self.tm.add_order(trade_id, exit_order_id, "TEST_SYMBOL", "SELL", 100, 110.0, "PENDING")
        self.tm.update_order_status(exit_order_id, "FILLED", 110.0)

        trade = self.tm.get_trade(trade_id)
        self.assertEqual(trade['status'], 'CLOSED')
        self.assertEqual(trade['pnl'], 1000.0)

    def test_short_trade_lifecycle(self):
        trade_id = self.tm.create_trade("TEST_SYMBOL", "TEST_STRAT", "PAPER", 100, "SELL")
        order_id = "ORDER_ENTRY_S"
        self.tm.add_order(trade_id, order_id, "TEST_SYMBOL", "SELL", 100, 200.0, "PENDING")
        self.tm.update_order_status(order_id, "FILLED", 200.0)

        exit_order_id = "ORDER_EXIT_B"
        self.tm.add_order(trade_id, exit_order_id, "TEST_SYMBOL", "BUY", 100, 190.0, "PENDING")
        self.tm.update_order_status(exit_order_id, "FILLED", 190.0)

        trade = self.tm.get_trade(trade_id)
        self.assertEqual(trade['status'], 'CLOSED')
        self.assertEqual(trade['pnl'], 1000.0)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

if __name__ == "__main__":
    unittest.main()
