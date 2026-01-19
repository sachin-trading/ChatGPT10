import time
import random
from typing import Dict, Any, List
from .base import BrokerInterface

class PaperBroker(BrokerInterface):
    def __init__(self):
        self.orders = {}
        self.positions = []
        # Mock LTPs for common symbols
        self.mock_prices = {
            "NSE:NIFTY50-INDEX": 22000.0,
            "NSE:SBIN-EQ": 750.0,
            "MCX:CRUDEOIL24FEB": 6200.0
        }

    def login(self):
        print("Paper Broker logged in successfully.")
        return True

    def get_ltp(self, symbol: str) -> float:
        # Simulate some price movement or return fixed price
        base_price = self.mock_prices.get(symbol, 100.0)
        return base_price + random.uniform(-1, 1)

    def place_order(self, symbol: str, side: str, quantity: int, order_type: str, price: float = 0.0) -> str:
        order_id = f"PAPER_{int(time.time() * 1000)}"
        self.orders[order_id] = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "order_type": order_type,
            "price": price if price > 0 else self.get_ltp(symbol),
            "status": "FILLED"
        }
        return order_id

    def modify_order(self, order_id: str, params: Dict[str, Any]):
        if order_id in self.orders:
            self.orders[order_id].update(params)
            return True
        return False

    def cancel_order(self, order_id: str):
        if order_id in self.orders:
            self.orders[order_id]["status"] = "CANCELLED"
            return True
        return False

    def get_order_status(self, order_id: str) -> str:
        return self.orders.get(order_id, {}).get("status", "REJECTED")

    def get_positions(self) -> List[Dict[str, Any]]:
        # Mock positions based on filled orders
        # Real implementation would aggregate
        return self.positions
