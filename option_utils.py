# option_utils.py
from datetime import date, timedelta
import calendar
from expiry_selector import select_expiry

def get_atm_strike(nifty_price: float, step=50):
    return int(round(nifty_price / step) * step)

def build_option_symbol(underlying: str, expiry_date, strike: int, direction: str) -> str:
    """
    Fyers V3 Symbology:
    Monthly: NSE:NIFTY23OCT19500CE
    Weekly:  NSE:NIFTY23O1919500CE
    """
    year = expiry_date.strftime("%y")
    month = expiry_date.month
    day = expiry_date.day

    # Check if it's monthly expiry (last Thursday of the month)
    last_day = calendar.monthrange(expiry_date.year, expiry_date.month)[1]
    last_date = date(expiry_date.year, expiry_date.month, last_day)
    offset = (last_date.weekday() - 3) % 7
    last_thursday = (last_date - timedelta(days=offset)).day

    is_monthly = (day == last_thursday)

    if is_monthly:
        month_str = expiry_date.strftime("%b").upper()
        expiry_part = f"{year}{month_str}"
    else:
        month_map = {1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: 'O', 11: 'N', 12: 'D'}
        month_str = month_map[month]
        day_str = f"{day:02d}"
        expiry_part = f"{year}{month_str}{day_str}"

    cepe = "CE" if direction == "CALL" else "PE"
    return f"NSE:{underlying}{expiry_part}{int(strike)}{cepe}"
