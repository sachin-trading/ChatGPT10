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
    print("Bot starting")
    token = fyers_auth.ensure_access_token()
    LOG.info("Authenticated (token obtained / read).")
    print("Authenticated (token obtained / read).")
    data_feed = DataFeed()
    order_mgr = OrderManager(access_token=token)
    strat_mgr = StrategyManager(order_mgr=order_mgr, data_feed=data_feed)

    # load strategies inside StrategyManager (it constructs them)
    LOG.info("Initialized strategy manager with %d strategies", len(strat_mgr.strategies))

    def get_underlying_for_symbol(symbol):
        for k, v in config.INSTRUMENTS.items():
            if v["index_symbol"] == symbol:
                return k
        return "NIFTY" # Fallback

    def within_trading_hours(symbol):
        now = datetime.now().time()
        if "MCX:" in symbol:
            start = datetime.strptime(config.MCX_TRADE_START_TIME, "%H:%M").time()
            end = datetime.strptime(config.MCX_MUST_EXIT_TIME, "%H:%M").time()
        else:
            start = datetime.strptime(config.TRADE_START_TIME, "%H:%M").time()
            end = datetime.strptime(config.MUST_EXIT_TIME, "%H:%M").time()
        return start <= now <= end

    def is_past_exit_time(symbol):
        now = datetime.now().time()
        if "MCX:" in symbol:
            exit_time = datetime.strptime(config.MCX_MUST_EXIT_TIME, "%H:%M").time()
        else:
            exit_time = datetime.strptime(config.MUST_EXIT_TIME, "%H:%M").time()
        return now >= exit_time

    symbol_closed_status = {sym: False for sym in config.SYMBOLS}

    try:
        while True:
            for symbol in config.SYMBOLS:
                underlying = get_underlying_for_symbol(symbol)

                if is_past_exit_time(symbol):
                    if not symbol_closed_status[symbol]:
                        LOG.info("Symbol %s past exit time - closing related positions", symbol)
                        strat_mgr.close_positions_for_underlying(underlying)
                        symbol_closed_status[symbol] = True
                    continue

                if not within_trading_hours(symbol):
                    LOG.debug("Symbol %s outside trading hours", symbol)
                    continue

                # Reset status if somehow we are back in trading hours (e.g. next day)
                symbol_closed_status[symbol] = False

                # Fetch latest 5m candles
                df = data_feed.get_latest_5m(symbol)
                if df is None or df.empty:
                    LOG.warning("No data returned for %s", symbol)
                    continue

                # Update indicators centrally once
                data_feed.compute_indicators(df)

                # Evaluate strategies for this underlying
                strat_mgr.run_strategies(df, underlying)

                # Monitor open positions for this underlying
                strat_mgr.monitor_positions(df, underlying)

            # Global sleep
            print(f"Loop cycle complete at {datetime.now()} — sleeping 10 seconds")
            time.sleep(10)

    except KeyboardInterrupt:
        LOG.info("KeyboardInterrupt received - closing positions")
        strat_mgr.close_all_positions()
    except Exception as e:
        LOG.exception("Unhandled exception in main loop: %s", e)
        strat_mgr.close_all_positions()


if __name__ == "__main__":
    main()
