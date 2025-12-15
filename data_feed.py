# data_feed.py
import pandas as pd
import logging
from datetime import datetime
import config

LOG = logging.getLogger("data_feed")

class DataFeed:
    def __init__(self):
        # use HISTORICAL_CSV as fallback for testing
        self.csv = config.HISTORICAL_CSV

    def get_latest_5m(self):
        try:
            df = pd.read_csv(self.csv, parse_dates=["datetime"])
            df = df.sort_values("datetime").reset_index(drop=True)
            return df
        except Exception as e:
            LOG.exception("Failed to read historical CSV: %s", e)
            return pd.DataFrame()

    def compute_indicators(self, df):
        from indicators import add_indicators
        add_indicators(df)

    def get_last_price(self, symbol):
        # For simulation, return last 'close' from csv
        try:
            df = self.get_latest_5m()
            if df.empty:
                return None
            return float(df["close"].iloc[-1])
        except Exception as e:
            LOG.exception("get_last_price error: %s", e)
            return None

    def fetch_pcr(self):
        # If PCR_DATA_SOURCE is 'DUMMY' return dummy value
        if config.PCR_DATA_SOURCE == "DUMMY":
            return 1.0
        # otherwise implement fetch from URL (omitted)
        return 1.0
