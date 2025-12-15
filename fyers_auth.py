import logging
import webbrowser
import urllib.parse as urlparse
import config
from fyers_apiv3 import fyersModel
import os

logger = logging.getLogger(__name__)


def _save_tokens_to_config(access_token, refresh_token=None):
    cfg_path = os.path.join(os.path.dirname(__file__), "config.py")

    with open(cfg_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.strip().startswith("ACCESS_TOKEN"):
            new_lines.append(f'ACCESS_TOKEN = "{access_token}"\n')
        elif line.strip().startswith("REFRESH_TOKEN"):
            new_lines.append(f'REFRESH_TOKEN = "{refresh_token or ""}"\n')
        else:
            new_lines.append(line)

    with open(cfg_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("Tokens saved to config.py")


def get_login_url():
    session = fyersModel.SessionModel(
        client_id=config.FYERS_CLIENT_ID,
        secret_key=config.FYERS_SECRET_KEY,
        redirect_uri=config.REDIRECT_URL,
        response_type="code",
        grant_type="authorization_code",
        state="sample"
    )
    return session.generate_authcode()


def exchange_code_for_token(auth_code):
    session = fyersModel.SessionModel(
        client_id=config.FYERS_CLIENT_ID,
        secret_key=config.FYERS_SECRET_KEY,
        redirect_uri=config.REDIRECT_URL,
        response_type="code",
        grant_type="authorization_code",
        state="sample"
    )

    session.set_token(auth_code)
    return session.generate_token()


def ensure_access_token() -> str:
    """
    Ensure access token exists; if not, run interactive auth and save tokens to config.py.

    Robust parsing: prefers 'auth_code' param (long JWT-like) if present,
    otherwise falls back to 'code'. Accepts pasted URL even if line-wrapped.
    """
    print("New")
    if getattr(config, "ACCESS_TOKEN", None):
        print("Using existing ACCESS_TOKEN from config.py")
        return config.ACCESS_TOKEN

    # Open browser for login
    url = get_login_url()
    print("Open this URL and complete login (browser will open):")
    print(url)
    try:
        webbrowser.open(url, new=1)
    except Exception:
        logger.exception("Failed to open browser; please open the URL manually")

    redirected = input("After login, paste the full redirect URL here: ").strip()

    # CLEANUP: remove stray backslashes, newlines and leading/trailing whitespace inserted by wrapping
    redirected = redirected.replace("\\", "").replace("\n", "").replace("\r", "").strip()

    # Parse both query and fragment (some providers put tokens in fragment)
    parsed = urlparse.urlparse(redirected)
    query_params = urlparse.parse_qs(parsed.query)
    frag_params = urlparse.parse_qs(parsed.fragment)

    # helper to get first value from dict
    def _first(d, key):
        v = d.get(key)
        if not v:
            return None
        return v[0]

    # Prefer 'auth_code', then 'code'
    auth_code = _first(query_params, "auth_code") or _first(frag_params, "auth_code")
    if not auth_code:
        auth_code = _first(query_params, "code") or _first(frag_params, "code")

    # If still missing, try to parse raw query-like string if user pasted only query
    if not auth_code and ("auth_code=" in redirected or "code=" in redirected):
        # naive fallback parsing
        for part in redirected.split("&"):
            if part.startswith("auth_code="):
                auth_code = part.split("auth_code=", 1)[1]
                break
            if part.startswith("code=") and not auth_code:
                auth_code = part.split("code=", 1)[1]

    if not auth_code:
        raise RuntimeError("No auth code found in the pasted URL. Make sure you pasted the full redirect URL.")

    # Basic sanity check: auth_code should not be a short numeric value like '200'
    if len(auth_code) < 10 or auth_code.isdigit():
        print("Warning: extracted auth code looks short/numeric (value: {!r}).".format(auth_code))
        print("This usually means the URL contained a 'code' parameter (HTTP code) instead of the real auth token.")
        print("Please paste the full redirect URL that contains the long 'auth_code' value (JWT-like).")
        # give user a chance to re-paste
        maybe = input("Press Enter to continue with this code, or paste the full redirect URL again: ").strip()
        if maybe:
            maybe = maybe.replace("\\", "").replace("\n", "").replace("\r", "").strip()
            parsed2 = urlparse.urlparse(maybe)
            qp2 = urlparse.parse_qs(parsed2.query)
            fp2 = urlparse.parse_qs(parsed2.fragment)
            auth_code = _first(qp2, "auth_code") or _first(fp2, "auth_code") or _first(qp2, "code") or _first(fp2, "code")
            if not auth_code:
                raise RuntimeError("No auth code found after re-paste. Aborting.")

    print("Using auth code (first 60 chars):", (auth_code[:60] + '...') if len(auth_code) > 60 else auth_code)

    # Now exchange the auth_code for tokens. Use your exchange_code_for_token() or session.generate_token()
    token_resp = exchange_code_for_token(auth_code)

    # Token response sanity checks
    if not isinstance(token_resp, dict):
        raise RuntimeError(f"Unexpected token response type: {type(token_resp)} -- {token_resp}")

    # The SDK usually returns {"s":"ok", "code":200, "access_token": "...", "refresh_token": "..."}
    if token_resp.get("s") == "error" or token_resp.get("access_token") is None:
        # print the whole response for debugging
        raise RuntimeError(f"Token error: {token_resp}")

    access_token = token_resp.get("access_token")
    refresh_token = token_resp.get("refresh_token")

    # save tokens
    _save_tokens_to_config(access_token, refresh_token)

    print("Access token saved to config.py")
    return access_token

