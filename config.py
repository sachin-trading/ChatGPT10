# config.py
import os

# Fyers API Credentials
FYERS_CLIENT_ID = os.getenv("FYERS_CLIENT_ID", "WQPNJZHYO1-100")
FYERS_SECRET_KEY = os.getenv("FYERS_SECRET_KEY", "PUF02F01IT")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCcFFOZ2U3bnVwbm5IMUNMOFFuemxoR1BsdXM1U0NqRjYyNWMwZVpzWEVqNHp3TzVYQUpxRDB3ODhsMUd5MnkySm1TTW8tdDhDMkdqT21sLXZ0S0s5NE9DZVhpVTBfaDYzYVVaR1hxUG03VFBucTJNZz0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhsbV9rZXkiOiI2MTQxNjFhMjY0ZTg4ZjQ3Yzk4NjFkYzVlMzBiNTA1OWQ3OGM1OWQyMWMwN2JmMDkxMTJhNjgzZCIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFMwODgwNSIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzY1OTMxNDAwLCJpYXQiOjE3NjU4NTczMTAsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc2NTg1NzMxMCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.Ny8aUccXFNU1CX76E2GY5yDfybs6r0qVAacOMGs53CQ")
REDIRECT_URL = "https://www.google.com"

# Execution Mode
dRY_RUN = False
ONLY_LOG_ORDER = "N" # Set to "Y" for dry run where API is called but order isn't actually placed (if implemented in OrderManager)

# Strategy & Symbols
SYMBOLS = ["NSE:NIFTY50-INDEX"]
TIMEFRAME = "5m"

# Risk Management
STOP_LOSS_POINTS = 20
TARGET_POINTS = 40
MAX_DAILY_LOSS_POINTS = 100
MAX_TRADES_PER_DAY = 5

# Trading Hours
TRADE_START_TIME = "09:25"
MUST_EXIT_TIME = "15:25"

# Instrument Mapping
INSTRUMENTS = {
   "NIFTY": {"index_symbol": "NSE:NIFTY50-INDEX", "underlying_symbol": "NIFTY", "lot_size": 75},
   "BANKNIFTY": {"index_symbol": "NSE:NIFTYBANK-INDEX", "underlying_symbol": "BANKNIFTY", "lot_size": 30},
}

# Notional margin per lot (conservative estimate)
NOTIONAL_PER_TRADE = 10000

LOG_FILE = "bot.log"
HISTORICAL_CSV = "historical_nifty_5m.csv"

STRATEGY_LOTS = {
   "TRENDALIGN": 1,
}
