from abc import ABC, abstractmethod
from typing import Dict, Any

class Signal:
    def __init__(self, action: str, symbol: str, quantity: int, price: float = 0.0, side: str = "BUY"):
        self.action = action  # ENTRY, EXIT, HOLD
        self.side = side      # BUY, SELL
        self.symbol = symbol
        self.quantity = quantity
        self.price = price

    def __repr__(self):
        return f"Signal({self.action}, {self.side}, {self.symbol}, {self.quantity}, {self.price})"

class StrategyInterface(ABC):
    @abstractmethod
    def generate_signal(self, market_data: Dict[str, Any]) -> Signal:
        pass
