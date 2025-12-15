# order_manager.py
import logging
import requests
from typing import Dict, Any
from dataclasses import dataclass
import config
from datetime import datetime

LOG = logging.getLogger("order_manager")


@dataclass
class OrderResponse:
    status: str
    order_id: str = ""
    avg_price: float = 0.0
    price: float = 0.0
    raw: Dict = None


class OrderManager:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base = config.FYERS_BASE_URL.rstrip("/")
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
        self._simulate_order_id = 0

    def get_available_margin(self) -> float:
        """Call Fyers margin API. If dRY_RUN, return a large margin for simulation."""
        if config.dRY_RUN:
            return 10_000_000.0
        try:
            url = f"{self.base}/api/v2/accounts"  # Example endpoint (adjust if needed)
            r = requests.get(url, headers=self.headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            # extract available margin from response - this is SDK-specific
            avail = float(data.get("available_margin", 0) or data.get("cash_balance", 0) or 0.0)
            return avail
        except Exception as e:
            LOG.exception("Failed to fetch margin: %s", e)
            return 0.0

    def estimate_margin(self, entry, lot_count: int):
        # conservative estimation: use notional per trade if provided
        try:
            notional = config.NOTIONAL_PER_TRADE
            return notional * lot_count
        except Exception:
            return 10000 * lot_count

    def build_option_symbol(self, underlying: str, expiry_date, strike: int, direction: str) -> str:
        """Create an option symbol for Fyers-like format. expiry_date is datetime.date."""
        # Use ddmmmyy format for expiry e.g., 19DEC25
        expiry_str = expiry_date.strftime("%d%b%y").upper()
        cepe = "CE" if direction == "CALL" else "PE"
        # typical Fyers symbol example: NIFTY19DEC22400CE (user can adjust to exact formatting)
        return f"{underlying}{expiry_str}{int(strike)}{cepe}"

    def place_market_order(self, symbol: str, quantity: int, direction: str, strategy: str, closing: bool = False) -> Dict:
        """
        Place a market order. If config.dRY_RUN is True, simulate fill.
        direction: "CALL"/"PUT" for entry; for actual order direction for options we treat CALL=BUY, PUT=BUY etc.
        closing: True when we are closing (so reverse side)
        """
        LOG.info("Placing market order symbol=%s qty=%s dir=%s strategy=%s closing=%s", symbol, quantity, direction, strategy, closing)
        if config.dRY_RUN:
            self._simulate_order_id += 1
            simulated_price = self._simulate_price_for_symbol(symbol)
            resp = {"status": "SIMULATED", "order_id": f"SIM{self._simulate_order_id}", "avg_price": simulated_price, "price": simulated_price}
            LOG.info("Simulated order placed: %s", resp)
            return resp

        try:
            # This is a placeholder. Replace path/payload with actual Fyers order endpoint if you want to send real orders.
            url = f"{self.base}/api/v2/orders"
            side = "BUY" if not closing else "SELL"
            payload = {
                "symbol": symbol,
                "qty": quantity,
                "type": "market",
                "side": side,
                "productType": "INTRADAY",
                "limitPrice": 0,
                "stopPrice": 0
            }
            r = requests.post(url, json=payload, headers=self.headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            return {"status": "OK", "order_id": data.get("id"), "raw": data}
        except Exception as e:
            LOG.exception("Order placement failed: %s", e)
            return {"status": "ERROR", "error": str(e)}

    def _simulate_price_for_symbol(self, symbol):
        # very simple price simulator: parse strike from symbol, fallback to 100
        import re
        m = re.search(r"(\d{2,6})", symbol)
        if m:
            return float(m.group(1)) + 1.0
        # fallback: return 100.0
        return 100.0
