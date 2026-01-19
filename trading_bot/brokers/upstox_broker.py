import upstox_client
from upstox_client.rest import ApiException
from typing import Dict, Any, List
from .base import BrokerInterface

class UpstoxBroker(BrokerInterface):
    def __init__(self, api_key: str, access_token: str):
        self.api_key = api_key
        self.access_token = access_token
        self.configuration = upstox_client.Configuration()
        self.configuration.access_token = access_token
        self.api_client = upstox_client.ApiClient(self.configuration)

    def login(self):
        try:
            api_instance = upstox_client.UserApi(self.api_client)
            api_response = api_instance.get_profile('2.0')
            print(f"Upstox logged in: {api_response.data.user_name}")
            return True
        except ApiException as e:
            print(f"Exception when calling UserApi->get_profile: {e}")
            return False

    def get_ltp(self, symbol: str) -> float:
        try:
            api_instance = upstox_client.MarketQuoteApi(self.api_client)
            api_response = api_instance.get_full_market_quote(symbol, '2.0')
            # Extract LTP from response
            if api_response.data:
                return api_response.data[symbol].last_price
            return 0.0
        except Exception as e:
            print(f"Error fetching LTP from Upstox: {e}")
            return 0.0

    def place_order(self, symbol: str, side: str, quantity: int, order_type: str, price: float = 0.0) -> str:
        try:
            api_instance = upstox_client.OrderApi(self.api_client)
            # Map side and order_type
            body = {
                "quantity": quantity,
                "product": "I", # Intraday
                "validity": "DAY",
                "price": price if order_type.upper() == "LIMIT" else 0,
                "tag": "trading_bot",
                "instrument_token": symbol,
                "order_type": "MARKET" if order_type.upper() == "MARKET" else "LIMIT",
                "transaction_type": "BUY" if side.upper() == "BUY" else "SELL"
            }
            api_response = api_instance.place_order(body, '2.0')
            return api_response.data.order_id
        except ApiException as e:
            raise Exception(f"Upstox order placement failed: {e.body}")

    def modify_order(self, order_id: str, params: Dict[str, Any]):
        try:
            api_instance = upstox_client.OrderApi(self.api_client)
            api_response = api_instance.modify_order(params, '2.0')
            return api_response
        except ApiException as e:
            print(f"Error modifying Upstox order: {e}")

    def cancel_order(self, order_id: str):
        try:
            api_instance = upstox_client.OrderApi(self.api_client)
            api_response = api_instance.cancel_order(order_id, '2.0')
            return api_response
        except ApiException as e:
            print(f"Error cancelling Upstox order: {e}")

    def get_order_status(self, order_id: str) -> str:
        try:
            api_instance = upstox_client.OrderApi(self.api_client)
            api_response = api_instance.get_order_details(order_id=order_id, api_version='2.0')
            status = api_response.data.status
            if status == "completed": return "FILLED"
            if status == "open": return "PENDING"
            if status == "cancelled": return "CANCELLED"
            if status == "rejected": return "REJECTED"
            return status.upper()
        except Exception:
            return "UNKNOWN"

    def get_positions(self) -> List[Dict[str, Any]]:
        try:
            api_instance = upstox_client.PortfolioApi(self.api_client)
            api_response = api_instance.get_positions('2.0')
            # Normalize to include 'symbol' and 'netQty'
            positions = []
            for p in api_response.data:
                positions.append({
                    "symbol": p.trading_symbol,
                    "netQty": int(p.quantity)
                })
            return positions
        except ApiException:
            return []
