import logging
from typing import Dict
from dataclasses import dataclass
import config
import forward_test_log

from fyers_apiv3 import fyersModel

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
        if config.DRY_RUN:
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
        from expiry_selector import is_in_last_7_days_of_month

        yy = expiry_date.strftime("%y")
        mm = expiry_date.strftime("%b").upper()
        dd = expiry_date.strftime("%d")
        cepe = "CE" if direction == "CALL" else "PE"

        if is_in_last_7_days_of_month(expiry_date):
            # Monthly format: NSE:NIFTY24OCT25000CE
            return f"NSE:{underlying}{yy}{mm}{int(strike)}{cepe}"
        else:
            # Weekly format: NSE:NIFTY24O3125000CE
            # Month code: 1-9 for Jan-Sep, O for Oct, N for Nov, D for Dec
            month_map = {
                1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6",
                7: "7", 8: "8", 9: "9", 10: "O", 11: "N", 12: "D"
            }
            m_code = month_map[expiry_date.month]
            return f"NSE:{underlying}{yy}{m_code}{dd}{int(strike)}{cepe}"

    # ==========================================================
    # PLACE MARKET ORDER
    # ==========================================================
    def place_market_order(self, symbol, quantity, direction, strategy, closing=False) -> Dict:
        if config.DRY_RUN:
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
            
            if config.ONLY_LOG_ORDER == "N":
                resp = self.fyers.place_order(payload)

            if resp.get("s") != "ok":
                return {"status": "ERROR", "raw": resp}

            return {"status": "OK", "order_id": resp.get("id")}

        except Exception as e:
            LOG.exception("Order placement exception")
            return {"status": "ERROR", "error": str(e)}

    def _simulate_price_for_symbol(self, symbol):
        import re
        m = re.search(r"(\d{4,6})", symbol)
        return float(m.group(1)) + 1 if m else 100.0
