from typing import Dict, Any, List
from ..brokers.base import BrokerInterface

class DataLayer:
    def __init__(self, broker: BrokerInterface):
        self.broker = broker

    def get_market_snapshot(self, symbol: str) -> Dict[str, Any]:
        """Unified market data snapshot"""
        ltp = self.broker.get_ltp(symbol)

        # Mocking VWAP and PCR for this example
        # In a real system, these would be calculated from candles or fetched
        return {
            "symbol": symbol,
            "ltp": ltp,
            "vwap": ltp * 0.99, # Mock VWAP
            "pcr": 1.2,        # Mock PCR
        }

    def get_historical_candles(self, symbol: str, interval: str, days: int) -> List[Dict[str, Any]]:
        # This would call broker.get_candles if we added it to interface
        return []
