
# config.py
# Put your credentials and configuration here.

FYERS_CLIENT_ID = "WQPNJZHYO1-100"
FYERS_SECRET_KEY = "PUF02F01IT"
REDIRECT_URL = "https://www.google.com"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCcE8tcmVfT0hNWnEzZ1lCemlfUWR4dEQwNDFlRjZ2N2FodURVY2l0ak8xaV85TmhqTERIeXBlckliNjRfb0hRd3NBaXRWMVJmUGtiSExvNlNZOVU4Z0IxVDIyeDBNZ1ZzWXcwc1Z3eXBJM2VCVzJqVT0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJjZDc2NDg3OTY3NWNhYWJhZmJlZDVmNzc5NTkwMjQ1NGUzNjQzZDU3MTRlZTBmZDIxYzlmOTFhOCIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFMwODgwNSIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzY1NTg1ODAwLCJpYXQiOjE3NjU1MzQ0MzAsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc2NTUzNDQzMCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.BaM_TfLg7vL_BAZV23dnKVZju0QmdH67I4uh5MxksVU"

SYMBOLS = ["NIFTY 50", "BANKNIFTY"]
TIMEFRAME = "5m"

dRY_RUN = True

STOP_LOSS_POINTS = 25
TARGET_POINTS = 35

MARKET_OPEN_TIME = "09:15"
TRADE_START_TIME = "09:25"
MUST_EXIT_TIME = "23:15"

LOG_FILE = "bot.log"
HISTORICAL_CSV = "historical_nifty_5m.csv"
PCR_DATA_SOURCE = "DUMMY"
FYERS_BASE_URL = "https://api.fyers.in"
NOTIONAL_PER_TRADE = 15000

INSTRUMENTS = {
    "NIFTY": {"index_symbol": "NIFTY", "underlying_symbol": "NIFTY", "lot_size": 50},
    "BANKNIFTY": {"index_symbol": "BANKNIFTY", "underlying_symbol": "BANKNIFTY", "lot_size": 25},
}

# example expected content (already in config.py in your environment):
STRATEGY_LOTS = {
   "TCB": 1,
   "VWAP": 2,
   "PCR": 1,
   "ORB": 1,
   "IVCRUSH": 1,
   "MARKETPROFILE": 1,
   "MOMENTUM": 1,
   "SMC": 1,
   "LOWIV": 1,
   "DELTASCALP": 1,
}
