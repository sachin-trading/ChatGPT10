from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BrokerInterface(ABC):
    @abstractmethod
    def login(self):
        pass

    @abstractmethod
    def get_ltp(self, symbol: str) -> float:
        pass

    @abstractmethod
    def place_order(self, symbol: str, side: str, quantity: int, order_type: str, price: float = 0.0) -> str:
        """Returns broker_order_id"""
        pass

    @abstractmethod
    def modify_order(self, order_id: str, params: Dict[str, Any]):
        pass

    @abstractmethod
    def cancel_order(self, order_id: str):
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> str:
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        pass
