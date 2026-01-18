import csv
import os
import uuid
import json
from datetime import datetime, timezone

FORWARD_TEST_LOG = "forward_test_log.csv"

FIELDS = [
    "run_id",
    "trade_id",
    "timestamp",
    "mode",
    "strategy",
    "symbol",
    "underlying",
    "direction",
    "option_type",
    "expiry",
    "strike",
    "quantity",
    "signal_price",
    "assumed_fill_price",
    "exit_price",
    "pnl",
    "status",
    "reason",
    "indicators",
    "remarks"
]


def _ensure_file():
    if not os.path.exists(FORWARD_TEST_LOG):
        with open(FORWARD_TEST_LOG, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()


RUN_ID = datetime.now().strftime("FT_%Y%m%d_%H%M%S")


def log_forward_test(
    *,
    strategy: str,
    symbol: str,
    underlying: str,
    direction: str,
    quantity: int,
    signal_price: float,
    status: str,
    option_type: str,
    expiry: str,
    strike: int,
    mode: str = "PAPER",
    assumed_fill_price: float | None = None,
    exit_price: float | None = None,
    pnl: float | None = None,
    reason: str = "",
    indicators: dict | None = None,
    remarks: str = "",
    trade_id: str | None = None,
):
    _ensure_file()

    row = {
        "run_id": RUN_ID,
        "trade_id": trade_id or str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "strategy": strategy,
        "symbol": symbol,
        "underlying": underlying,
        "direction": direction,
        "option_type": option_type,
        "expiry": expiry,
        "strike": strike,
        "quantity": quantity,
        "signal_price": signal_price,
        "assumed_fill_price": assumed_fill_price,
        "exit_price": exit_price,
        "pnl": pnl,
        "status": status,
        "reason": reason,
        "indicators": json.dumps(indicators or {}),
        "remarks": remarks,
    }

    with open(FORWARD_TEST_LOG, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(row)

    return row["trade_id"]
