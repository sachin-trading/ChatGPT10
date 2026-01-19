# expiry_selector.py
from datetime import date, timedelta
import datetime

def _next_thursday(from_date):
    days_ahead = (3 - from_date.weekday()) % 7 # Thursday is 3
    if days_ahead == 0:
        return from_date
    return from_date + timedelta(days=days_ahead)

def select_expiry(reference_date=None, underlying="NIFTY"):
    """
    Returns a date (datetime.date) for the expiry.
    For NIFTY/BANKNIFTY: Closest Thursday.
    For CRUDEOIL: Approx 15-17th of the current month (simplified as monthly).
    """
    if reference_date is None:
        reference_date = date.today()

    if underlying == "CRUDEOIL":
        # Simplified: MCX Crude Oil options expire around middle of the month
        # We'll just return the 16th of the current or next month.
        if reference_date.day <= 15:
            return date(reference_date.year, reference_date.month, 16)
        else:
            # next month
            nm = reference_date.month + 1
            yr = reference_date.year
            if nm > 12:
                nm = 1
                yr += 1
            return date(yr, nm, 16)

    # NIFTY / BANKNIFTY weekly logic
    wd = reference_date.weekday()  # Mon=0, Thu=3
    if wd in (0, 1): # Mon, Tue -> Next Thursday
        return _next_thursday(reference_date + timedelta(days=7))
    else: # Wed, Thu, Fri, Sat, Sun -> This or Next Thursday
        return _next_thursday(reference_date)

def is_in_last_7_days_of_month(target_date):
    # Helpful utility mentioned in memory
    import calendar
    last_day = calendar.monthrange(target_date.year, target_date.month)[1]
    return target_date.day > (last_day - 7)
