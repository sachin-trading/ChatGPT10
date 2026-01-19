from .base import StrategyInterface, Signal
from typing import Dict, Any

class OptionBuyVwapPcr(StrategyInterface):
    def generate_signal(self, market_data: Dict[str, Any]) -> Signal:
        symbol = market_data.get('symbol')
        ltp = market_data.get('ltp', 0)
        vwap = market_data.get('vwap', 0)
        pcr = market_data.get('pcr', 1.0)

        # Simple Logic: LTP > VWAP and PCR > 1.0 -> BUY Call (or just Entry)
        # If we are in a trade, maybe some exit logic too?
        # But the strategy should be stateless.
        # So it should probably receive position info too?
        # "Strategy code must never call broker APIs or databases."
        # So market_data should include everything it needs.

        is_open = market_data.get('is_open', False)

        if not is_open:
            if ltp > vwap and pcr > 1.1:
                return Signal(action="ENTRY", side="BUY", symbol=symbol, quantity=market_data.get('default_qty', 1))
        else:
            # Exit logic
            if ltp < vwap:
                return Signal(action="EXIT", side="SELL", symbol=symbol, quantity=market_data.get('open_qty', 0))

        return Signal(action="HOLD", symbol=symbol, quantity=0)
