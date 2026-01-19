import pandas as pd
import os
from datetime import datetime
from ..core.db import DatabaseManager

class ReportGenerator:
    def __init__(self, db: DatabaseManager):
        self.db = db
        os.makedirs("trading_bot/reports", exist_ok=True)

    def generate_monthly_report(self, month: int = None, year: int = None):
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year

        query = """
            SELECT * FROM trades_master
            WHERE status = 'CLOSED'
            AND strftime('%m', exit_timestamp) = ?
            AND strftime('%Y', exit_timestamp) = ?
        """
        # SQLite strftime %m returns 01-12
        month_str = f"{month:02d}"
        year_str = str(year)

        with self.db.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=(month_str, year_str))

        if df.empty:
            print(f"No closed trades found for {month_str}/{year_str}")
            return None

        report_path = f"trading_bot/reports/pnl_report_{year_str}_{month_str}.csv"
        df.to_csv(report_path, index=False)
        print(f"Report generated: {report_path}")

        # Summary
        summary = {
            "Total PnL": df['pnl'].sum(),
            "Total Trades": len(df),
            "Winning Trades": len(df[df['pnl'] > 0]),
            "Losing Trades": len(df[df['pnl'] < 0])
        }
        return summary

if __name__ == "__main__":
    db = DatabaseManager()
    rg = ReportGenerator(db)
    rg.generate_monthly_report()