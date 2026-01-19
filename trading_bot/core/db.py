import sqlite3
import os
from typing import List, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str = "trading_bot/data/trading.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            # trades_master table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades_master (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    broker TEXT NOT NULL,
                    status TEXT DEFAULT 'OPEN',
                    entry_side TEXT, -- BUY (Long), SELL (Short)
                    quantity INTEGER NOT NULL,
                    remaining_quantity INTEGER NOT NULL,
                    entry_price REAL,
                    exit_price REAL,
                    pnl REAL DEFAULT 0.0,
                    entry_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    exit_timestamp DATETIME
                )
            """)

            # orders table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    broker_order_id TEXT,
                    trade_id INTEGER,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL, -- BUY, SELL
                    quantity INTEGER NOT NULL,
                    price REAL,
                    status TEXT, -- PENDING, FILLED, CANCELLED, REJECTED
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trade_id) REFERENCES trades_master(id)
                )
            """)
            conn.commit()

    def execute_query(self, query: str, params: tuple = ()):
        with self.get_connection() as conn:
            return conn.execute(query, params).fetchall()

    def execute_update(self, query: str, params: tuple = ()):
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid
