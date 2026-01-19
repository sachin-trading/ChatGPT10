from datetime import datetime
from typing import Dict, Any

class RiskManager:
    def __init__(self, config: Dict[str, Any], trade_manager):
        self.config = config
        self.tm = trade_manager

    def can_place_order(self) -> (bool, str):
        # 1. Check Max Trades per Day
        max_trades = self.config.get('risk', {}).get('max_trades', 5)
        current_trades = self.tm.get_trade_count_today()
        if current_trades >= max_trades:
            return False, f"Max trades reached ({current_trades}/{max_trades})"

        # 2. Check Daily MTM Loss
        max_loss = self.config.get('risk', {}).get('max_daily_loss', 3000)
        current_pnl = self.tm.get_daily_pnl()
        if current_pnl <= -max_loss:
            return False, f"Max daily loss reached ({current_pnl})"

        # 3. Check Square-off Time
        sq_off_str = self.config.get('risk', {}).get('squareoff_time', "15:15")
        now = datetime.now().time()
        sq_off_time = datetime.strptime(sq_off_str, "%H:%M").time()
        if now >= sq_off_time:
            return False, f"After square-off time ({sq_off_str})"

        return True, "Success"

    def check_risk_per_trade(self, risk_amount: float) -> bool:
        allowed_risk = self.config.get('risk', {}).get('risk_per_trade', 500)
        return risk_amount <= allowed_risk
