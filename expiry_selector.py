# expiry_selector.py
from datetime import date, timedelta
import calendar

def _get_thursday(from_date):
    """Returns the current or next Thursday (NSE)."""
    days_ahead = (3 - from_date.weekday()) % 7
    return from_date + timedelta(days=days_ahead)

def is_monthly_expiry(expiry_date):
    """
    Check if the given expiry_date is the last Thursday of its month (NSE).
    """
    next_thursday = expiry_date + timedelta(days=7)
    return next_thursday.month != expiry_date.month

def is_in_last_7_days_of_month(target_date):
    last_day = calendar.monthrange(target_date.year, target_date.month)[1]
    return target_date.day > (last_day - 7)

def select_expiry(reference_date=None, segment="NSE"):
    """
    Selects the expiry date based on segment.
    """
    if reference_date is None:
        reference_date = date.today()

    if segment == "MCX":
        # Crude Oil MCX options usually expire around the 15th-20th.
        # For simplicity in this bot, we pick the current month's 19th
        # or next month's 19th if 19th is passed.
        # Real implementation should fetch from an option chain API.
        if reference_date.day > 18:
            # Next month
            month = reference_date.month % 12 + 1
            year = reference_date.year + (1 if reference_date.month == 12 else 0)
            return date(year, month, 19)
        else:
            return date(reference_date.year, reference_date.month, 19)

    # Default NSE Thursday
    return _get_thursday(reference_date)
