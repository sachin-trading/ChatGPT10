# main.py
import logging
import time
from datetime import datetime

import config
from bot_service import bot_service

LOG = logging.getLogger("multi_bot")
logging.basicConfig(filename=config.LOG_FILE, level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

def main():
    LOG.info("Bot starting as standalone")
    print("Bot starting as standalone")
    bot_service.initialize()
    bot_service.start()

    try:
        while True:
            time.sleep(1)
            if not bot_service.is_running:
                break
    except KeyboardInterrupt:
        LOG.info("KeyboardInterrupt received - stopping bot")
        bot_service.stop()
    except Exception as e:
        LOG.exception("Unhandled exception: %s", e)
        bot_service.stop()

if __name__ == "__main__":
    main()
