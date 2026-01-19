# main.py
import logging
import time
from datetime import datetime, time as dt_time, timedelta

import config
import fyers_auth

from data_feed import DataFeed
from strategy_manager import StrategyManager
from order_manager import OrderManager

LOG = logging.getLogger("multi_bot")
logging.basicConfig(filename=config.LOG_FILE, level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

def main():
    LOG.info("Bot starting")
    print("\n" + "="*40)
    print("      CRUDE OIL / NIFTY TRADING BOT")
    print("="*40)

    token = fyers_auth.ensure_access_token()
    LOG.info("Authenticated.")
    print("SUCCESS: Authenticated with Fyers API.")

    data_feed = DataFeed()
    order_mgr = OrderManager(access_token=token)
    strat_mgr = StrategyManager(order_mgr=order_mgr, data_feed=data_feed)

    LOG.info("Initialized strategy manager with %d strategies", len(strat_mgr.strategies))
    print(f"INFO: Strategy Manager initialized. active strategies: {', '.join(strat_mgr.strategies.keys())}")

    def within_trading_hours():
        now = datetime.now().time()
        start = datetime.strptime(config.TRADE_START_TIME, "%H:%M").time()
        end = datetime.strptime(config.MUST_EXIT_TIME, "%H:%M").time()
        return start <= now <= end

    print("INFO: Entering main loop...")
    try:
        while True:
            now = datetime.now()

            # Check EOD Exit
            if now.time() >= datetime.strptime(config.MUST_EXIT_TIME, "%H:%M").time():
                msg = f"[{now.strftime('%H:%M:%S')}] Market past MUST_EXIT_TIME. Closing all positions and exiting."
                LOG.info(msg)
                print("\n" + msg)
                strat_mgr.close_all_positions()
                break

            # Check Trading Hours
            if not within_trading_hours():
                msg = f"[{now.strftime('%H:%M:%S')}] Outside trading hours. Waiting for {config.TRADE_START_TIME}..."
                LOG.debug(msg)
                print(msg, end="\r", flush=True)
                time.sleep(30)
                continue

            for symbol in config.SYMBOLS:
                # Fetch Data
                print(f"[{now.strftime('%H:%M:%S')}] Fetching 5m candles for {symbol}...", end="\r", flush=True)
                df = data_feed.get_latest_5m(symbol=symbol)

                if df is None or df.empty:
                    LOG.warning("No data from Fyers for %s", symbol)
                    continue

                # Process Strategies
                data_feed.compute_indicators(df)
                strat_mgr.run_strategies(df)
                strat_mgr.monitor_positions(df)

            # Heartbeat
            LOG.debug("Loop complete")
            time.sleep(10)

    except KeyboardInterrupt:
        msg = "KeyboardInterrupt received. Closing positions..."
        LOG.info(msg)
        print("\n" + msg)
        strat_mgr.close_all_positions()
    except Exception as e:
        msg = f"FATAL ERROR: {e}"
        LOG.exception(msg)
        print("\n" + msg)
        strat_mgr.close_all_positions()

if __name__ == "__main__":
    main()
