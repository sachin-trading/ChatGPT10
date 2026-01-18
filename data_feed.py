import pandas as pd
import logging
from datetime import datetime
import config

from fyers_apiv3 import fyersModel
import time
from option_utils import get_atm_strike, build_option_symbol
from indicators import add_indicators

LOG = logging.getLogger("data_feed")


class DataFeed:
    def __init__(self):
        self.csv = config.HISTORICAL_CSV
        self._last_pcr_ts = None
        self._last_pcr = None

        self.fyers = fyersModel.FyersModel(
            client_id=config.FYERS_CLIENT_ID,
            token=config.ACCESS_TOKEN,
            log_path=None
        )

    def compute_indicators(self, df):
        add_indicators(df)

    def get_live_pcr(self, df, expiry_date):
        """
        Calculate LIVE PCR from Fyers Option OI.
        Cached per candle.
        """
        if df is None or df.empty or expiry_date is None:
            return None

        candle_ts = df["datetime"].iloc[-1]

        # PCR cache per candle
        if self._last_pcr_ts == candle_ts:
            return self._last_pcr

        try:
            spot = float(df["close"].iloc[-1])
            atm = get_atm_strike(spot)

            strikes = [atm + i * 50 for i in range(-2, 3)]

            symbols = []
            for strike in strikes:
                symbols.append(build_option_symbol("NIFTY", expiry_date, strike, "CALL"))
                symbols.append(build_option_symbol("NIFTY", expiry_date, strike, "PUT"))

            resp = self.fyers.quotes({"symbols": ",".join(symbols)})

            if resp.get("s") != "ok":
                LOG.warning("PCR API failed, using fallback")
                return self._fallback_pcr()

            data = resp.get("d", [])

            call_oi = 0
            put_oi = 0

            for item in data:
                oi = item.get("v", {}).get("oi", 0)
                sym = item.get("n", "")

                if sym.endswith("CE"):
                    call_oi += oi
                elif sym.endswith("PE"):
                    put_oi += oi

            if call_oi == 0:
                return self._fallback_pcr()

            pcr = round(put_oi / call_oi, 2)

            # cache
            self._last_pcr_ts = candle_ts
            self._last_pcr = pcr

            LOG.info("LIVE PCR computed: %s", pcr)
            return pcr

        except Exception:
            LOG.exception("Live PCR computation failed")
            return self._fallback_pcr()

    def _fallback_pcr(self):
        # Neutral PCR when API fails
        return 1.0


    def get_latest_5m(self):
        """
        Fetch LIVE 5-minute candles from Fyers History API.
        This is REAL market data (not CSV).
        """
        try:
            now = int(time.time())
            start = now - (6 * 60 * 60)  # last 6 hours

            data = {
                "symbol": "NSE:NIFTY50-INDEX",
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

            df = pd.DataFrame(
                candles,
                columns=["datetime", "open", "high", "low", "close", "volume"]
            )

            df["datetime"] = pd.to_datetime(df["datetime"], unit="s")
            return df

        except Exception:
            LOG.exception("Failed to fetch live 5m candles")
            return pd.DataFrame()


    def get_last_price(self, symbol):
        try:
            resp = self.fyers.quotes({"symbols": symbol})
            if resp.get("s") == "ok" and resp.get("d"):
                return float(resp["d"][0]["v"]["lp"])

            # Fallback to index price if quote fails
            df = self.get_latest_5m()
            if not df.empty:
                return float(df["close"].iloc[-1])
            return None
        except Exception as e:
            LOG.exception("get_last_price error for %s: %s", symbol, e)
            return None
