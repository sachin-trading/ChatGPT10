import pandas as pd
import logging
from datetime import datetime
import config
from fyers_apiv3 import fyersModel
import time
from option_utils import get_atm_strike

LOG = logging.getLogger("data_feed")

class DataFeed:
    def __init__(self):
        self._last_pcr_ts = None
        self._last_pcr = None
        self.fyers = fyersModel.FyersModel(
            client_id=config.FYERS_CLIENT_ID,
            token=config.ACCESS_TOKEN,
            log_path=None
        )

    def compute_indicators(self, df):
        from indicators import add_indicators
        add_indicators(df)

    def get_latest_5m(self):
        """Fetch LIVE 5-minute candles for the Index."""
        try:
            now = int(time.time())
            start = now - (6 * 60 * 60)
            data = {
                "symbol": config.INSTRUMENTS["NIFTY"]["index_symbol"],
                "resolution": "5",
                "date_format": "0",
                "range_from": start,
                "range_to": now,
                "cont_flag": "1",
            }
            resp = self.fyers.history(data)
            if resp.get("s") != "ok":
                LOG.error("History API failed: %s", resp)
                return pd.DataFrame()
            candles = resp.get("candles", [])
            if not candles:
                return pd.DataFrame()
            df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
            df["datetime"] = pd.to_datetime(df["datetime"], unit="s")
            return df
        except Exception:
            LOG.exception("Failed to fetch live 5m candles")
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

    def get_live_pcr(self, df, expiry_date):
        # (Keeping PCR logic if needed, but not used in TRENDALIGN)
        if df is None or df.empty or expiry_date is None:
            return None
        try:
            spot = float(df["close"].iloc[-1])
            atm = get_atm_strike(spot)
            # Simplified PCR for now
            return 1.0
        except Exception:
            return 1.0
