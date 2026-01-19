# config.py
import os

# Fyers API Credentials
FYERS_CLIENT_ID = os.getenv("FYERS_CLIENT_ID", "WQPNJZHYO1-100")
FYERS_SECRET_KEY = os.getenv("FYERS_SECRET_KEY", "PUF02F01IT")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "dummy_token")
REDIRECT_URL = "https://www.google.com"

# Execution Mode
dRY_RUN = False
ONLY_LOG_ORDER = "N"

# Strategy & Symbols
SYMBOLS = ["MCX:CRUDEOIL-NEAR-FUT"] # Using Fyers continuous futures symbol if available
TIMEFRAME = "5m"

# Risk Management
STOP_LOSS_POINTS = 30
TARGET_POINTS = 60
MAX_DAILY_LOSS_POINTS = 150
MAX_TRADES_PER_DAY = 3

# Trading Hours (Crude Oil MCX trades until 11:30/11:55 PM)
TRADE_START_TIME = "09:05"
MUST_EXIT_TIME = "23:20"

# Instrument Mapping
INSTRUMENTS = {
   "NIFTY": {"index_symbol": "NSE:NIFTY50-INDEX", "underlying_symbol": "NIFTY", "lot_size": 75},
   "BANKNIFTY": {"index_symbol": "NSE:NIFTYBANK-INDEX", "underlying_symbol": "BANKNIFTY", "lot_size": 30},
   "CRUDEOIL": {"index_symbol": "MCX:CRUDEOIL-NEAR-FUT", "underlying_symbol": "CRUDEOIL", "lot_size": 100},
}

# Notional margin per lot
NOTIONAL_PER_TRADE = 50000 # Crude Oil options can be expensive

LOG_FILE = "crude_bot.log"
HISTORICAL_CSV = "historical_crude_5m.csv"

STRATEGY_LOTS = {
   "CRUDETREND": 1,
}
