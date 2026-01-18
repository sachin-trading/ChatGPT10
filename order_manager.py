import logging
from typing import Dict
from dataclasses import dataclass
import config
from fyers_apiv3 import fyersModel
from expiry_selector import is_monthly_expiry

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

    def get_available_margin(self) -> float:
        if config.dRY_RUN:
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

    def estimate_margin(self, entry, lot_size: int) -> float:
        try:
            return float(config.NOTIONAL_PER_TRADE * lot_size)
        except Exception:
            return float("inf")

    def build_option_symbol(self, underlying: str, expiry_date, strike: int, direction: str) -> str:
        """
        Fyers V3 Symbology:
        Weekly: {Exchange}:{Underlying}{YY}{M}{DD}{Strike}{Type}
        Monthly: {Exchange}:{Underlying}{YY}{MMM}{Strike}{Type}
        M (Weekly Month Code): 1-9, O, N, D
        MMM (Monthly): JAN, FEB, ...
        """
        yy = expiry_date.strftime("%y")
        cepe = "CE" if direction == "CALL" else "PE"

        if is_monthly_expiry(expiry_date):
            mmm = expiry_date.strftime("%b").upper()
            symbol = f"NSE:{underlying}{yy}{mmm}{int(strike)}{cepe}"
        else:
            month = expiry_date.month
            m_code = str(month) if month < 10 else ("O" if month == 10 else ("N" if month == 11 else "D"))
            dd = expiry_date.strftime("%d")
            symbol = f"NSE:{underlying}{yy}{m_code}{dd}{int(strike)}{cepe}"

        LOG.info("Built option symbol: %s", symbol)
        return symbol

    def place_market_order(self, symbol, quantity, direction, strategy, closing=False) -> Dict:
        if config.dRY_RUN:
            self._simulate_order_id += 1
            price = 100.0 # Dummy price for simulation
            LOG.info("Simulated Order: %s %s %s @ %s", "SELL" if closing else "BUY", quantity, symbol, price)
            return {
                "status": "SIMULATED",
                "order_id": f"SIM{self._simulate_order_id}",
                "avg_price": price,
                "price": price
            }

        try:
            # For option buying bot, we always BUY to open and SELL to close
            side = 1 if not closing else -1

            payload = {
                "symbol": symbol,
                "qty": quantity,
                "type": 2, # Market order
                "side": side,
                "productType": "INTRADAY",
                "limitPrice": 0,
                "stopPrice": 0,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": "False",
            }

            # Default to placing order unless ONLY_LOG_ORDER is 'Y'
            if getattr(config, "ONLY_LOG_ORDER", "N") == "Y":
                LOG.info("ONLY_LOG_ORDER is Y. Skipping API call for %s", payload)
                return {"status": "OK", "order_id": "LOGGED_ONLY", "avg_price": 0.0}

            resp = self.fyers.place_order(payload)
            LOG.info("Fyers place_order response: %s", resp)

            if resp.get("s") != "ok":
                return {"status": "ERROR", "raw": resp}

            return {"status": "OK", "order_id": resp.get("id")}

        except Exception as e:
            LOG.exception("Order placement exception")
            return {"status": "ERROR", "error": str(e)}
