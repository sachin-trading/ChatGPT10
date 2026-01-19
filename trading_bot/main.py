import logging
import os
from trading_bot.config.loader import load_config
from trading_bot.core.db import DatabaseManager
from trading_bot.core.trade_manager import TradeManager
from trading_bot.risk.risk_manager import RiskManager
from trading_bot.execution.data_layer import DataLayer
from trading_bot.execution.engine import ExecutionEngine
from trading_bot.strategies.example_strategy import OptionBuyVwapPcr
from trading_bot.brokers.fyers_broker import FyersBroker
from trading_bot.brokers.upstox_broker import UpstoxBroker
from trading_bot.brokers.paper_broker import PaperBroker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trading_bot/logs/app.log"),
        logging.StreamHandler()
    ]
)

def main():
    logging.info("Starting Trading Bot...")

    # 1. Load Config
    config = load_config()
    trading_conf = config.get('trading', {})

    # 2. Init Core
    db = DatabaseManager()
    tm = TradeManager(db)
    rm = RiskManager(config, tm)

    # 3. Select Broker
    broker_type = trading_conf.get('broker', 'PAPER').upper()
    mode = trading_conf.get('mode', 'PAPER').upper()

    if mode == "PAPER":
        broker = PaperBroker()
    elif broker_type == "FYERS":
        broker = FyersBroker(
            client_id=os.getenv("FYERS_CLIENT_ID"),
            access_token=os.getenv("FYERS_ACCESS_TOKEN")
        )
    elif broker_type == "UPSTOX":
        broker = UpstoxBroker(
            api_key=os.getenv("UPSTOX_API_KEY"),
            access_token=os.getenv("UPSTOX_ACCESS_TOKEN")
        )
    else:
        broker = PaperBroker()

    broker.login()

    # 4. Reconciliation
    open_trades = tm.get_open_trades()
    logging.info(f"Reconciliation: Found {len(open_trades)} open trades in database.")

    try:
        broker_positions = broker.get_positions()
        # Create a map of net positions by symbol
        # Note: Fyers netPositions key is 'symbol' and 'netQty'
        pos_map = {p.get('symbol'): p for p in broker_positions}

        for trade in open_trades:
            symbol = trade['symbol']
            broker_pos = pos_map.get(symbol)

            # Simple reconciliation: if net quantity is 0 or symbol not found, close it in DB
            if not broker_pos or broker_pos.get('netQty', 0) == 0:
                logging.warning(f"Reconciliation: Trade {trade['id']} for {symbol} has no broker position. Closing locally.")
                tm.close_trade_locally(trade['id'])
            else:
                logging.info(f"Reconciliation: Trade {trade['id']} for {symbol} verified. Qty: {broker_pos.get('netQty')}")
    except Exception as e:
        logging.error(f"Reconciliation failed: {e}")

    # 5. Init Strategy and Engine
    strategy_name = trading_conf.get('strategy')
    if strategy_name == "OPTION_BUY_VWAP_PCR":
        strategy = OptionBuyVwapPcr()
    else:
        strategy = OptionBuyVwapPcr() # Default

    dl = DataLayer(broker)

    engine = ExecutionEngine(config, broker, tm, rm, dl, strategy)

    try:
        engine.start()
    except KeyboardInterrupt:
        logging.info("Stopping Bot...")
        engine.stop()

if __name__ == "__main__":
    main()
