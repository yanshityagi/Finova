# Tools/csv_tools.py

import pandas as pd
from datetime import datetime
from typing import List, Dict


def parse_statement_csv(path: str, bank_name: str, account_id: str) -> Dict:
    """
    Parse the Agent 0 simulated bank statement CSV into normalized transactions.

    Expected columns in CSV:
      - Date
      - Description
      - Debit
      - Credit
      - Balance

    Returns:
      {
        "bank_name": str,
        "account_id": str,
        "transactions": [ { ... }, ... ]
      }
    """
    df = pd.read_csv(path)

    def parse_date(d: str) -> str:
        """
        Parse dates in multiple formats.
        CSV contains mixed formats like '1-Apr-15' and '2017-02-29'.
        2017-02-29 is invalid (non-leap year), so return raw string if parsing fails.
        """
        d = str(d).strip()

        formats = [
            "%d-%b-%y",   # 1-Apr-15
            "%Y-%m-%d",   # 2017-02-29 (but invalid date)
            "%d/%m/%Y",   # 01/04/2015
            "%m/%d/%Y",   # 04/01/2015
        ]

        for fmt in formats:
            try:
                return datetime.strptime(d, fmt).date().isoformat()
            except ValueError:
                continue

        # Fallback: return original if completely unparseable
        return d

    transactions: List[Dict] = []

    for _, row in df.iterrows():
        date_raw = str(row["Date"])
        description = str(row["Description"])
        debit = row["Debit"]
        credit = row["Credit"]
        balance = row["Balance"]

        tx = {
            "date": parse_date(date_raw),
            "description": description,
            "debit": float(debit) if pd.notna(debit) else None,
            "credit": float(credit) if pd.notna(credit) else None,
            "balance": float(balance) if pd.notna(balance) else None,
            "bank_name": bank_name,
            "account_id": account_id,
        }
        transactions.append(tx)

    return {
        "bank_name": bank_name,
        "account_id": account_id,
        "transactions": transactions,
    }
