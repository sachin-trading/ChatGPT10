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
    found_token = False
    for line in lines:
        if line.strip().startswith("ACCESS_TOKEN"):
            new_lines.append(f'ACCESS_TOKEN = "{access_token}"\n')
            found_token = True
        elif line.strip().startswith("REFRESH_TOKEN"):
            new_lines.append(f'REFRESH_TOKEN = "{refresh_token or ""}"\n')
        else:
            new_lines.append(line)

    if not found_token:
        new_lines.append(f'ACCESS_TOKEN = "{access_token}"\n')

    with open(cfg_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    # Update in-memory config module
    config.ACCESS_TOKEN = access_token
    if refresh_token:
        config.REFRESH_TOKEN = refresh_token

    print("Tokens updated in config.py and in-memory.")

def get_login_url():
    session = fyersModel.SessionModel(
        client_id=config.FYERS_CLIENT_ID,
        secret_key=config.FYERS_SECRET_KEY,
        redirect_uri=config.REDIRECT_URL,
        response_type="code",
        grant_type="authorization_code"
    )
    return session.generate_authcode()

def exchange_code_for_token(auth_code):
    session = fyersModel.SessionModel(
        client_id=config.FYERS_CLIENT_ID,
        secret_key=config.FYERS_SECRET_KEY,
        redirect_uri=config.REDIRECT_URL,
        response_type="code",
        grant_type="authorization_code"
    )
    session.set_token(auth_code)
    return session.generate_token()

def ensure_access_token() -> str:
    """
    Ensure access token exists. If config.ACCESS_TOKEN is dummy or missing,
    starts the login flow.
    """
    token = getattr(config, "ACCESS_TOKEN", "")

    # Check if token looks like a real JWT (long)
    if len(token) > 100:
        print("INFO: Found existing ACCESS_TOKEN in config.py.")
        choice = input("Do you want to use this token? (y/n): ").lower()
        if choice == 'y':
            return token

    # Start new login flow
    url = get_login_url()
    print("\n" + "="*60)
    print("ACTION REQUIRED: AUTHENTICATION")
    print("="*60)
    print("1. Open this URL in your browser:")
    print(f"\n{url}\n")
    print("2. Login and authorize the app.")
    print("3. After redirection, paste the FULL URL from the browser address bar below.")
    print("="*60)

    try:
        webbrowser.open(url)
    except:
        pass

    redirected = input("\nPaste Redirect URL here: ").strip()

    # Extract auth_code from URL
    parsed = urlparse.urlparse(redirected)
    query_params = urlparse.parse_qs(parsed.query)
    auth_code = query_params.get("auth_code", [None])[0] or query_params.get("code", [None])[0]

    if not auth_code:
        # Try to see if they just pasted the code
        if len(redirected) > 20 and "&" not in redirected:
            auth_code = redirected
        else:
            raise RuntimeError("Could not find auth_code in the provided URL.")

    print("INFO: Exchanging auth_code for Access Token...")
    token_resp = exchange_code_for_token(auth_code)

    if token_resp.get("s") != "ok":
        raise RuntimeError(f"Token Exchange Failed: {token_resp}")

    access_token = token_resp.get("access_token")
    _save_tokens_to_config(access_token)

    return access_token
