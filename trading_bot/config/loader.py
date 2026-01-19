import yaml
import os
from typing import Dict, Any

def load_config(config_path: str = "trading_bot/config/config.yaml") -> Dict[str, Any]:
    if not os.path.exists(config_path):
        # Return default config if not found
        return {
            "trading": {
                "mode": "PAPER",
                "broker": "FYERS",
                "strategy": "OPTION_BUY_VWAP_PCR"
            },
            "risk": {
                "max_daily_loss": 3000,
                "max_trades": 5,
                "risk_per_trade": 500,
                "squareoff_time": "15:15"
            },
            "instruments": [
                {"type": "OPTIDX", "underlying": "NIFTY", "symbol": "NSE:NIFTY50-INDEX"}
            ]
        }

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
