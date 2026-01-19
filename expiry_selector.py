# expiry_selector.py
from datetime import date, timedelta
import datetime
import calendar

def _get_thursday(from_date):
    """Returns the current or next Thursday."""
    days_ahead = (3 - from_date.weekday()) % 7
    return from_date + timedelta(days=days_ahead)

def is_monthly_expiry(expiry_date):
    """
    Check if the given expiry_date is the last Thursday of its month.
    """
    # Get next Thursday from expiry_date + 7 days
    next_thursday = expiry_date + timedelta(days=7)
    # If next Thursday is in a different month, then expiry_date is the last Thursday
    return next_thursday.month != expiry_date.month

def is_in_last_7_days_of_month(target_date):
    """
    Returns True if the target_date is within the last 7 days of its month.
    For example, if a month has 31 days, it returns True for days 25 to 31.
    """
    last_day = calendar.monthrange(target_date.year, target_date.month)[1]
    return target_date.day > (last_day - 7)

def select_expiry(reference_date=None):
    """
    Selects the nearest Thursday.
    """
    if reference_date is None:
        reference_date = date.today()

    expiry = _get_thursday(reference_date)
    return expiry
