# expiry_selector.py
from datetime import date, timedelta

def _next_thursday(from_date):
    # Thursday is weekday 3.
    # (3 - weekday) % 7 gives days to next Thursday.
    days_ahead = (3 - from_date.weekday()) % 7
    if days_ahead == 0:
        # If today is Thursday, return today or next week?
        # Usually for expiry selection, if it is Thursday morning, we might still trade today's expiry.
        return from_date
    return from_date + timedelta(days=days_ahead)

def _following_thursday(from_date):
    nxt = _next_thursday(from_date)
    if nxt == from_date:
        nxt = nxt + timedelta(days=7)
    return nxt

def select_expiry(reference_date=None, prefer_next_week=False):
    """
    Monday (0) & Tuesday (1) → NEXT WEEK expiry
    Wed (2), Thu (3), Fri (4) → CURRENT WEEK expiry

    Returns a date (datetime.date) for the expiry (Thursday).
    """
    import datetime
    if reference_date is None:
        reference_date = datetime.date.today()
    wd = reference_date.weekday()  # Mon=0
    print(wd)
    if wd in (0, 1):
        # next-week expiry
        base = reference_date + timedelta(days=7)
        print(base)
        return _next_thursday(base)
    else:
        # current-week expiry (closest Thursday)
        return _next_thursday(reference_date)

def is_in_last_7_days_of_month(target_date):
    """
    Identifies if a date falls within the final seven days of its calendar month.
    Helpful for determining if an expiry is a monthly one.
    """
    import calendar
    last_day = calendar.monthrange(target_date.year, target_date.month)[1]
    return target_date.day > (last_day - 7)
