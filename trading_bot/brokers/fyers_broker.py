import os
from typing import Dict, Any, List
from fyers_apiv3 import fyersModel
from .base import BrokerInterface

class FyersBroker(BrokerInterface):
    def __init__(self, client_id: str, access_token: str):
        self.client_id = client_id
        self.access_token = access_token
        self.fyers = None

    def login(self):
        self.fyers = fyersModel.FyersModel(
            client_id=self.client_id,
            token=self.access_token,
            is_async=False,
            log_path=os.getcwd()
        )
        # Verify login
        profile = self.fyers.get_profile()
        if profile.get('code') == 200:
            print(f"Fyers logged in: {profile.get('data', {}).get('name')}")
            return True
        else:
            print(f"Fyers login failed: {profile}")
            return False

    def get_ltp(self, symbol: str) -> float:
        data = {"symbols": symbol}
        response = self.fyers.quotes(data=data)
        if response.get('code') == 200:
            return response.get('d', [{}])[0].get('v', {}).get('lp', 0.0)
        return 0.0

    def place_order(self, symbol: str, side: str, quantity: int, order_type: str, price: float = 0.0) -> str:
        # Map side: BUY=1, SELL=-1
        fyers_side = 1 if side.upper() == "BUY" else -1
        # Map order type: MARKET=2, LIMIT=1
        fyers_type = 2 if order_type.upper() == "MARKET" else 1

        data = {
            "symbol": symbol,
            "qty": quantity,
            "type": fyers_type,
            "side": fyers_side,
            "productType": "INTRADAY",
            "limitPrice": price if fyers_type == 1 else 0,
            "stopPrice": 0,
            "validity": "DAY",
            "disclosedQty": 0,
            "offlineOrder": "False"
        }
        response = self.fyers.place_order(data=data)
        if response.get('code') == 200:
            return response.get('id')
        else:
            raise Exception(f"Order failed: {response}")

    def modify_order(self, order_id: str, params: Dict[str, Any]):
        response = self.fyers.modify_order(data={"id": order_id, **params})
        return response

    def cancel_order(self, order_id: str):
        response = self.fyers.cancel_order(data={"id": order_id})
        return response

    def get_order_status(self, order_id: str) -> str:
        response = self.fyers.orderbook()
        if response.get('code') == 200:
            orders = response.get('orderBook', [])
            for order in orders:
                if order.get('id') == order_id:
                    # Map Fyers status to common status
                    status = order.get('status')
                    if status == 2: return "FILLED"
                    if status == 1: return "PENDING"
                    if status == 5: return "CANCELLED"
                    if status == 6: return "REJECTED"
                    return f"OTHER({status})"
        return "UNKNOWN"

    def get_positions(self) -> List[Dict[str, Any]]:
        response = self.fyers.positions()
        if response.get('code') == 200:
            return response.get('netPositions', [])
        return []
