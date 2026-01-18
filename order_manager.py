import logging
from typing import Dict
from dataclasses import dataclass
from datetime import datetime, date, timedelta
import re
import config
import forward_test_log

from fyers_apiv3 import fyersModel
from option_utils import build_option_symbol

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

        self.fyers = fyersModel.FyersModel(
            client_id=config.FYERS_CLIENT_ID,
            token=access_token,
            log_path=None
        )

        self._simulate_order_id = 0

    # ==========================================================
    # MARGIN – FYERS API V3
    # ==========================================================
    def get_available_margin(self) -> float:
        mode = getattr(config, "EXECUTION_MODE", "PAPER")
        if mode != "LIVE":
            return 10_000_000.0

        try:
            resp = self.fyers.funds()

            if resp.get("s") != "ok":
                LOG.error("Margin API failed: %s", resp)
                return 0.0

            fund_limit = resp.get("fund_limit", [])
            available = 0.0

            for item in fund_limit:
                if item.get("title") == "Available Balance":
                    available = float(item.get("equityAmount", 0.0))
                    break

            return available

        except Exception:
            LOG.exception("Exception while fetching margin")
            return 0.0

    # ==========================================================
    # MARGIN ESTIMATION (USED BY STRATEGY MANAGER)
    # ==========================================================
    def estimate_margin(self, entry, lot_size: int) -> float:
        """
        Conservative margin estimation for option buying.
        """
        try:
            return float(config.NOTIONAL_PER_TRADE * lot_size)
        except Exception:
            return float("inf")

    # ==========================================================
    # OPTION SYMBOL BUILDER
    # ==========================================================
    def build_option_symbol(self, underlying: str, expiry_date, strike: int, direction: str) -> str:
        return build_option_symbol(underlying, expiry_date, strike, direction)

    # ==========================================================
    # PLACE MARKET ORDER
    # ==========================================================
    def place_market_order(self, symbol, quantity, direction, strategy, closing=False) -> Dict:
        mode = getattr(config, "EXECUTION_MODE", "PAPER")

        if mode == "DRY_RUN":
            self._simulate_order_id += 1
            price = self._simulate_price_for_symbol(symbol)
            return {
                "status": "SIMULATED",
                "order_id": f"SIM{self._simulate_order_id}",
                "avg_price": price,
                "price": price
            }

        try:
            side = 1 if not closing else -1

            payload = {
                "symbol": symbol,
                "qty": quantity,
                "type": 2,
                "side": side,
                "productType": "INTRADAY",
                "validity": "DAY",
            }

            if mode == "LIVE":
                resp = self.fyers.place_order(payload)
            else:
                # PAPER mode
                resp = {"s": "ok", "id": "PAPER_ORDER"}

            if resp.get("s") != "ok":
                return {"status": "ERROR", "raw": resp}

            order_id = resp.get("id")

            # Approximation of avg_price for market order
            avg_price = 0.0
            try:
                q_resp = self.fyers.quotes({"symbols": symbol})
                if q_resp.get("s") == "ok" and q_resp.get("d"):
                    avg_price = float(q_resp["d"][0]["v"]["lp"])
            except:
                pass

            return {"status": "OK", "order_id": order_id, "avg_price": avg_price}

        except Exception as e:
            LOG.exception("Order placement exception")
            return {"status": "ERROR", "error": str(e)}

    def _simulate_price_for_symbol(self, symbol):
        m = re.search(r"(\d{4,6})", symbol)
        return float(m.group(1)) * 0.01 # Better simulation: 1% of strike
