
import os

# config.py
# Put your credentials and configuration here.
# It is recommended to use environment variables for sensitive data.

FYERS_CLIENT_ID = os.getenv("FYERS_CLIENT_ID", "YOUR_CLIENT_ID")
FYERS_SECRET_KEY = os.getenv("FYERS_SECRET_KEY", "YOUR_SECRET_KEY")
REDIRECT_URL = os.getenv("FYERS_REDIRECT_URL", "https://www.google.com")
ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN", "")

SYMBOLS = ["NIFTY 50", "BANKNIFTY"]
TIMEFRAME = "5m"

# Execution Mode:
# "LIVE"    - Real orders placed on exchange
# "PAPER"   - No real orders, but uses live market prices for logging
# "DRY_RUN" - No real orders, uses simulated prices (for testing without API access)
EXECUTION_MODE = "PAPER"

STOP_LOSS_POINTS = 25
TARGET_POINTS = 35
MARKET_OPEN_TIME = "09:15"
TRADE_START_TIME = "09:25"
MUST_EXIT_TIME = "15:28"

LOG_FILE = "bot.log"
HISTORICAL_CSV = "historical_nifty_5m.csv"
PCR_DATA_SOURCE = "FYERS"
FYERS_BASE_URL = "https://api.fyers.in"
NOTIONAL_PER_TRADE = 6000

INSTRUMENTS = {
   "NIFTY": {"index_symbol": "NIFTY", "underlying_symbol": "NIFTY", "lot_size": 75},
   "BANKNIFTY": {"index_symbol": "BANKNIFTY", "underlying_symbol": "BANKNIFTY", "lot_size": 35},
}

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
   "TRENDALIGN": 1,
}
