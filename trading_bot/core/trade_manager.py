import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from .db import DatabaseManager

class TradeManager:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_trade(self, symbol: str, strategy: str, broker: str, quantity: int, entry_side: str) -> int:
        query = """
            INSERT INTO trades_master (symbol, strategy, broker, quantity, remaining_quantity, entry_side, status, entry_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, 'OPEN', CURRENT_TIMESTAMP)
        """
        return self.db.execute_update(query, (symbol, strategy, broker, quantity, quantity, entry_side.upper()))

    def add_order(self, trade_id: int, broker_order_id: str, symbol: str, side: str, quantity: int, price: float, status: str) -> int:
        query = """
            INSERT INTO orders (trade_id, broker_order_id, symbol, side, quantity, price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        return self.db.execute_update(query, (trade_id, broker_order_id, symbol, side, quantity, price, status))

    def get_trade(self, trade_id: int) -> Dict[str, Any]:
        result = self.db.execute_query("SELECT * FROM trades_master WHERE id = ?", (trade_id,))
        return dict(result[0]) if result else None

    def update_order_status(self, broker_order_id: str, status: str, fill_price: float = None):
        query = "UPDATE orders SET status = ?"
        params = [status]
        if fill_price is not None:
            query += ", price = ?"
            params.append(fill_price)
        query += " WHERE broker_order_id = ?"
        params.append(broker_order_id)
        self.db.execute_update(query, tuple(params))

        if status == "FILLED":
            order_data = self.db.execute_query("SELECT * FROM orders WHERE broker_order_id = ?", (broker_order_id,))
            if order_data:
                order = dict(order_data[0])
                self._handle_fill(order['trade_id'], order['side'], order['quantity'], order['price'])

    def _handle_fill(self, trade_id: int, side: str, quantity: int, price: float):
        trade = self.get_trade(trade_id)
        if not trade:
            return

        entry_side = trade['entry_side']

        if side.upper() == entry_side:
            # Updating entry (Average Price)
            # Find total filled entry quantity so far
            entry_orders = self.db.execute_query(
                "SELECT quantity, price FROM orders WHERE trade_id = ? AND side = ? AND status = 'FILLED'",
                (trade_id, entry_side)
            )
            total_entry_qty = sum(o['quantity'] for o in entry_orders)
            total_entry_val = sum(o['quantity'] * o['price'] for o in entry_orders)
            avg_entry_price = total_entry_val / total_entry_qty if total_entry_qty > 0 else 0

            self.db.execute_update(
                "UPDATE trades_master SET entry_price = ? WHERE id = ?",
                (avg_entry_price, trade_id)
            )
        else:
            # Exit (Opposite of entry side)
            exit_side = "SELL" if entry_side == "BUY" else "BUY"

            exit_orders = self.db.execute_query(
                "SELECT quantity, price FROM orders WHERE trade_id = ? AND side = ? AND status = 'FILLED'",
                (trade_id, exit_side)
            )
            total_exit_qty = sum(o['quantity'] for o in exit_orders)
            total_exit_val = sum(o['quantity'] * o['price'] for o in exit_orders)
            avg_exit_price = total_exit_val / total_exit_qty if total_exit_qty > 0 else 0

            new_remaining = trade['quantity'] - total_exit_qty
            status = 'CLOSED' if new_remaining <= 0 else 'OPEN'
            exit_timestamp = datetime.now() if status == 'CLOSED' else None

            pnl = 0
            if status == 'CLOSED':
                if entry_side == "BUY":
                    pnl = (avg_exit_price - trade['entry_price']) * trade['quantity']
                else: # Short Entry (SELL)
                    pnl = (trade['entry_price'] - avg_exit_price) * trade['quantity']

            self.db.execute_update(
                """UPDATE trades_master
                   SET remaining_quantity = ?, exit_price = ?, status = ?, pnl = ?, exit_timestamp = ?
                   WHERE id = ?""",
                (max(0, new_remaining), avg_exit_price, status, pnl, exit_timestamp, trade_id)
            )

    def close_trade_locally(self, trade_id: int, reason: str = "Reconciliation"):
        # Force close a trade (e.g. if position not found on broker)
        self.db.execute_update(
            "UPDATE trades_master SET status = 'CLOSED', exit_timestamp = CURRENT_TIMESTAMP WHERE id = ?",
            (trade_id,)
        )

    def get_open_trades(self) -> List[Dict[str, Any]]:
        results = self.db.execute_query("SELECT * FROM trades_master WHERE status = 'OPEN'")
        return [dict(r) for r in results]

    def get_pending_orders(self) -> List[Dict[str, Any]]:
        results = self.db.execute_query("SELECT * FROM orders WHERE status = 'PENDING'")
        return [dict(r) for r in results]

    def get_daily_pnl(self) -> float:
        today = datetime.now().strftime('%Y-%m-%d')
        result = self.db.execute_query(
            "SELECT SUM(pnl) as total_pnl FROM trades_master WHERE status = 'CLOSED' AND date(exit_timestamp) = ?",
            (today,)
        )
        return result[0]['total_pnl'] or 0.0

    def get_trade_count_today(self) -> int:
        today = datetime.now().strftime('%Y-%m-%d')
        result = self.db.execute_query(
            "SELECT COUNT(*) as count FROM trades_master WHERE date(entry_timestamp) = ?",
            (today,)
        )
        return result[0]['count'] or 0
