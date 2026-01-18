# expiry_selector.py
from datetime import date, timedelta
import datetime

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

def select_expiry(reference_date=None):
    """
    Selects the nearest Thursday.
    If today is Thursday and past 3:30 PM (not handled here, but could be),
    it might still return today. Usually, the main loop should handle trading hours.
    """
    if reference_date is None:
        reference_date = date.today()

    expiry = _get_thursday(reference_date)

    # If today is Thursday but we want to avoid same-day expiry volatility or
    # it's already past some time, we could shift to next week.
    # For now, we return the nearest Thursday.
    return expiry
