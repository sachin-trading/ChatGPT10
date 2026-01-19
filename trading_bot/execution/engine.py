import time
import logging
from typing import Dict, Any, List
from ..core.trade_manager import TradeManager
from ..risk.risk_manager import RiskManager
from ..execution.data_layer import DataLayer
from ..strategies.base import StrategyInterface, Signal
from ..brokers.base import BrokerInterface

class ExecutionEngine:
    def __init__(
        self,
        config: Dict[str, Any],
        broker: BrokerInterface,
        trade_manager: TradeManager,
        risk_manager: RiskManager,
        data_layer: DataLayer,
        strategy: StrategyInterface
    ):
        self.config = config
        self.broker = broker
        self.tm = trade_manager
        self.rm = risk_manager
        self.dl = data_layer
        self.strategy = strategy
        self.is_running = False

    def run_once(self):
        instruments = self.config.get('instruments', [])
        for inst in instruments:
            symbol = inst.get('symbol')

            # 1. Check for Pending orders for this symbol
            pending_orders = [o for o in self.tm.get_pending_orders() if o['symbol'] == symbol]
            if pending_orders:
                logging.debug(f"Skipping {symbol}: Pending order {pending_orders[0]['broker_order_id']} exists.")
                # In real world, we might poll status here
                for po in pending_orders:
                    status = self.broker.get_order_status(po['broker_order_id'])
                    if status != po['status']:
                        self.tm.update_order_status(po['broker_order_id'], status)
                continue

            # 2. Get Open Trades for this symbol
            open_trades = [t for t in self.tm.get_open_trades() if t['symbol'] == symbol]
            is_open = len(open_trades) > 0
            open_qty = sum(t['remaining_quantity'] for t in open_trades)

            # 3. Get Market Data
            market_data = self.dl.get_market_snapshot(symbol)
            market_data['is_open'] = is_open
            market_data['open_qty'] = open_qty
            market_data['default_qty'] = 50 # Example

            # 4. Generate Signal
            signal = self.strategy.generate_signal(market_data)

            if signal.action == "HOLD":
                continue

            # 5. Handle Signal
            if signal.action == "ENTRY":
                # Check Global Risk
                can_trade, reason = self.rm.can_place_order()
                if not can_trade:
                    logging.info(f"Risk Block: {reason}")
                    continue

                # Check Risk per Trade
                # Simple heuristic: 10% of position value as risk
                risk_amount = (signal.quantity * market_data['ltp']) * 0.1
                if not self.rm.check_risk_per_trade(risk_amount):
                    logging.info(f"Risk Block: Risk per trade {risk_amount:.2f} too high.")
                    continue

                # Place Order
                try:
                    order_id = self.broker.place_order(
                        symbol=signal.symbol,
                        side=signal.side,
                        quantity=signal.quantity,
                        order_type="MARKET"
                    )
                    # Create Trade
                    trade_id = self.tm.create_trade(
                        symbol=signal.symbol,
                        strategy=self.config['trading']['strategy'],
                        broker=self.config['trading']['broker'],
                        quantity=signal.quantity,
                        entry_side=signal.side
                    )
                    # Add Order (Initially PENDING if not Paper)
                    mode = self.config.get('trading', {}).get('mode', 'PAPER')
                    initial_status = "FILLED" if mode == "PAPER" else "PENDING"

                    self.tm.add_order(
                        trade_id=trade_id,
                        broker_order_id=order_id,
                        symbol=signal.symbol,
                        side=signal.side,
                        quantity=signal.quantity,
                        price=market_data['ltp'],
                        status=initial_status
                    )
                    if initial_status == "FILLED":
                        self.tm.update_order_status(order_id, "FILLED", market_data['ltp'])

                    logging.info(f"Entry Order Placed: {order_id} for Trade: {trade_id}")
                except Exception as e:
                    logging.error(f"Error placing entry order: {e}")

            elif signal.action == "EXIT":
                for trade in open_trades:
                    try:
                        exit_side = "SELL" if trade['entry_side'] == "BUY" else "BUY"
                        order_id = self.broker.place_order(
                            symbol=signal.symbol,
                            side=exit_side,
                            quantity=trade['remaining_quantity'],
                            order_type="MARKET"
                        )
                        mode = self.config.get('trading', {}).get('mode', 'PAPER')
                        initial_status = "FILLED" if mode == "PAPER" else "PENDING"

                        self.tm.add_order(
                            trade_id=trade['id'],
                            broker_order_id=order_id,
                            symbol=signal.symbol,
                            side=exit_side,
                            quantity=trade['remaining_quantity'],
                            price=market_data['ltp'],
                            status=initial_status
                        )
                        if initial_status == "FILLED":
                            self.tm.update_order_status(order_id, "FILLED", market_data['ltp'])

                        logging.info(f"Exit Order Placed: {order_id} for Trade: {trade['id']}")
                    except Exception as e:
                        logging.error(f"Error placing exit order: {e}")

    def start(self):
        self.is_running = True
        logging.info("Execution Engine Started")
        while self.is_running:
            try:
                self.run_once()
            except Exception as e:
                logging.error(f"Error in execution loop: {e}")
            time.sleep(1)

    def stop(self):
        self.is_running = False
