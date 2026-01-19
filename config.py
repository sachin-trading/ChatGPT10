
# config.py
# Put your credentials and configuration here.

FYERS_CLIENT_ID = "WQPNJZHYO1-100"
FYERS_SECRET_KEY = "PUF02F01IT"
REDIRECT_URL = "https://www.google.com"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCcFFOZ2U3bnVwbm5IMUNMOFFuemxoR1BsdXM1U0NqRjYyNWMwZVpzWEVqNHp3TzVYQUpxRDB3ODhsMUd5MnkySm1TTW8tdDhDMkdqT21sLXZ0S0s5NE9DZVhpVTBfaDYzYVVaR1hxUG03VFBucTJNZz0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhsbV9rZXkiOiI2MTQxNjFhMjY0ZTg4ZjQ3Yzk4NjFkYzVlMzBiNTA1OWQ3OGM1OWQyMWMwN2JmMDkxMTJhNjgzZCIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFMwODgwNSIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzY1OTMxNDAwLCJpYXQiOjE3NjU4NTczMTAsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc2NTg1NzMxMCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.Ny8aUccXFNU1CX76E2GY5yDfybs6r0qVAacOMGs53CQ"

SYMBOLS = ["NSE:NIFTY50-INDEX", "MCX:CRUDEOIL24DECFUT"]
TIMEFRAME = "5m"

dRY_RUN = True
ONLY_LOG_ORDER = "Y" # 'Y' to only log, 'N' to actually place

# Trading hours
MARKET_OPEN_TIME = "09:15"
TRADE_START_TIME = "09:25"
MUST_EXIT_TIME = "15:28"

MCX_TRADE_START_TIME = "09:00"
MCX_MUST_EXIT_TIME = "23:25"

LOG_FILE = "bot.log"
HISTORICAL_CSV = "historical_nifty_5m.csv"
PCR_DATA_SOURCE = "FYERS" #"DUMMY"
FYERS_BASE_URL = "https://api.fyers.in"
NOTIONAL_PER_TRADE = 6000

INSTRUMENTS = {
   "NIFTY": {
       "index_symbol": "NSE:NIFTY50-INDEX",
       "underlying_symbol": "NIFTY",
       "lot_size": 75,
       "sl_points": 25,
       "tp_points": 45
   },
   "BANKNIFTY": {
       "index_symbol": "NSE:NIFTYBANK-INDEX",
       "underlying_symbol": "BANKNIFTY",
       "lot_size": 30,
       "sl_points": 40,
       "tp_points": 80
   },
   "CRUDEOIL": {
       "index_symbol": "MCX:CRUDEOIL24DECFUT",
       "underlying_symbol": "CRUDEOIL",
       "lot_size": 100,
       "sl_points": 15,
       "tp_points": 30
   },
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
   "CRUDETREND": 1,
}

MAX_DAILY_LOSS_POINTS = 100
MAX_TRADES_PER_DAY = 10
