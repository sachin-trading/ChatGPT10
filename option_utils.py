# option_utils.py
from datetime import date
from expiry_selector import select_expiry

def get_atm_strike(nifty_price: float, step=50):
    return int(round(nifty_price / step) * step)

def build_option_symbol(underlying: str, nifty_price: float, step=50, reference_date=None, direction="CALL"):
    """
    Convenience builder that picks ATM strike and builds a symbol string.
    """
    strike = get_atm_strike(nifty_price, step=step)
    expiry = select_expiry(reference_date)
    cepe = "CE" if direction == "CALL" else "PE"
    expiry_s = expiry.strftime("%d%b%y").upper()
    return f"{underlying}{expiry_s}{strike}{cepe}", strike, expiry
