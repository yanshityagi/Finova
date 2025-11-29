# Tools/csv_tools.py

import pandas as pd
from datetime import datetime

COLUMN_ALIASES = {
    "date": ["date", "txn date", "transaction date", "value date", "posting date"],
    "description": ["description", "narration", "details", "particulars", "payee", "desc"],
    "debit": ["debit", "withdrawal", "spent", "dr", "debits"],
    "credit": ["credit", "deposit", "received", "cr", "credits"],
    "balance": ["balance", "available balance", "closing balance"]
}

def find_column(df, possible_names):
    """Find the real column name regardless of spelling/casing."""
    df_cols = [c.lower().strip() for c in df.columns]

    for name in possible_names:
        if name in df_cols:
            return df.columns[df_cols.index(name)]

    return None


def parse_statement_csv(path=None, uploaded_file=None, bank_name="Unknown bank", account_id="Unknown"):
    # Load CSV either from path or in-memory upload
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_csv(path)

    df_original = df.copy()

    # Normalize column names
    df.columns = [c.lower().strip() for c in df.columns]

    # Detect columns
    date_col = find_column(df, COLUMN_ALIASES["date"])
    desc_col = find_column(df, COLUMN_ALIASES["description"])
    debit_col = find_column(df, COLUMN_ALIASES["debit"])
    credit_col = find_column(df, COLUMN_ALIASES["credit"])
    balance_col = find_column(df, COLUMN_ALIASES["balance"])

    # Fallbacks if missing
    if date_col is None:
        raise Exception("No date-like column found.")
    if desc_col is None:
        desc_col = df.columns[1]   # second column as fallback

    # Convert missing debit/credit formats
    if debit_col is None and credit_col is None:
        # Case: single column for amount with +/- values
        if "amount" in df.columns:
            df["debit"] = df["amount"].apply(lambda x: abs(x) if x < 0 else 0)
            df["credit"] = df["amount"].apply(lambda x: x if x > 0 else 0)
        else:
            # Create empty debit/credit
            df["debit"] = 0
            df["credit"] = 0

    # Build normalized transactions
    transactions = []
    for _, row in df.iterrows():
        # Parse date safely
        raw_date = str(row[date_col])

        try:
            parsed_date = pd.to_datetime(raw_date, errors="coerce").date()
            parsed_date = parsed_date.isoformat() if parsed_date else raw_date
        except:
            parsed_date = raw_date

        tx = {
            "date": parsed_date,
            "description": str(row.get(desc_col, "")),
            "debit": float(row[debit_col]) if debit_col and pd.notna(row.get(debit_col)) else 0,
            "credit": float(row[credit_col]) if credit_col and pd.notna(row.get(credit_col)) else 0,
            "balance": float(row[balance_col]) if balance_col and pd.notna(row.get(balance_col)) else None,
            "bank_name": bank_name,
            "account_id": account_id,
        }
        transactions.append(tx)

    return {
        "bank_name": bank_name,
        "account_id": account_id,
        "transactions": transactions,
    }
