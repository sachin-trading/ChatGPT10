import pandas as pd
import logging
from datetime import datetime
import config
from fyers_apiv3 import fyersModel
import time
from option_utils import get_atm_strike

LOG = logging.getLogger("data_feed")

class DataFeed:
    def __init__(self, access_token: str = None):
        self._last_pcr_ts = None
        self._last_pcr = None
        token = access_token or config.ACCESS_TOKEN
        self.fyers = fyersModel.FyersModel(
            client_id=config.FYERS_CLIENT_ID,
            token=token,
            log_path=None
        )
        if self.fyers is None:
            LOG.error("Failed to initialize FyersModel in DataFeed")

    def compute_indicators(self, df):
        from indicators import add_indicators
        add_indicators(df)

    def get_latest_5m(self, symbol=None):
        """Fetch LIVE 5-minute candles for a specific symbol."""
        if symbol is None:
            symbol = config.SYMBOLS[0]

        try:
            now = int(time.time())
            start = now - (24 * 60 * 60) # Last 24 hours to ensure enough data for indicators
            data = {
                "symbol": symbol,
                "resolution": "5",
                "date_format": "0",
                "range_from": start,
                "range_to": now,
                "cont_flag": "1",
            }
            resp = self.fyers.history(data)
            if resp.get("s") != "ok":
                LOG.error("History API failed for %s: %s", symbol, resp)
                return pd.DataFrame()
            candles = resp.get("candles", [])
            if not candles:
                return pd.DataFrame()
            df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
            df["datetime"] = pd.to_datetime(df["datetime"], unit="s")
            return df
        except Exception:
            LOG.exception("Failed to fetch live 5m candles for %s", symbol)
            return pd.DataFrame()

    def get_last_price(self, symbol):
        """Fetch LTP for any symbol (Index or Option)."""
        try:
            resp = self.fyers.quotes({"symbols": symbol})
            if resp.get("s") == "ok" and resp.get("d"):
                return float(resp["d"][0]["v"]["lp"])
            return None
        except Exception:
            LOG.exception("Failed to get last price for %s", symbol)
            return None
