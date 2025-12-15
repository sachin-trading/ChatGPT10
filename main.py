# main.py
import logging
import time
from datetime import datetime, time as dt_time, timedelta

import config  # :contentReference[oaicite:2]{index=2}
import fyers_auth  # :contentReference[oaicite:3]{index=3}

from data_feed import DataFeed
from strategy_manager import StrategyManager
from order_manager import OrderManager
from expiry_selector import select_expiry

LOG = logging.getLogger("multi_bot")
logging.basicConfig(filename=config.LOG_FILE, level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")


def main():
    LOG.info("Bot starting")
    token = fyers_auth.ensure_access_token()
    LOG.info("Authenticated (token obtained / read).")

    data_feed = DataFeed()
    order_mgr = OrderManager(access_token=token)
    strat_mgr = StrategyManager(order_mgr=order_mgr, data_feed=data_feed)

    # load strategies inside StrategyManager (it constructs them)
    LOG.info("Initialized strategy manager with %d strategies", len(strat_mgr.strategies))

    # Wait until TRADE_START_TIME
    def within_trading_hours():
        now = datetime.now().time()
        start = datetime.strptime(config.TRADE_START_TIME, "%H:%M").time()
        end = datetime.strptime(config.MUST_EXIT_TIME, "%H:%M").time()
        return start <= now <= end

    try:
        while True:
            now = datetime.now()
            if now.time() >= datetime.strptime(config.MUST_EXIT_TIME, "%H:%M").time():
                LOG.info("Market past MUST_EXIT_TIME - closing all positions")
                strat_mgr.close_all_positions()
                break

            if not within_trading_hours():
                LOG.debug("Outside trading hours, sleeping 30s")
                time.sleep(30)
                continue

            # Fetch latest 5m candles (data_feed returns a DataFrame with newest last)
            df = data_feed.get_latest_5m()
            if df is None or df.empty:
                LOG.warning("No data returned from data_feed")
                time.sleep(10)
                continue

            # Update indicators centrally once
            data_feed.compute_indicators(df)

            # Evaluate strategies and place orders if signals
            strat_mgr.run_strategies(df)

            # Monitor open positions for exit conditions & SL/TP
            strat_mgr.monitor_positions(df)

            # Sleep until next 5m candle approx (simple approach)
            LOG.debug("Loop complete — sleeping 10 seconds")
            time.sleep(10)
    except KeyboardInterrupt:
        LOG.info("KeyboardInterrupt received - closing positions")
        strat_mgr.close_all_positions()
    except Exception as e:
        LOG.exception("Unhandled exception in main loop: %s", e)
        strat_mgr.close_all_positions()


if __name__ == "__main__":
    main()
