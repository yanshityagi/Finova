# agents/agent0_sample_data.py

from typing import Dict
import pandas as pd

def load_sample_statement() -> Dict:
    """
    Load the Agent 0 simulated bank statement CSV and return
    a preview plus the path.

    Update 'data/Agent0_simulated_bank_statement.csv' to match your file.
    """
    csv_path = "data/Agent0_simulated_bank_statement.csv"
    df = pd.read_csv(csv_path)
    preview = df.head(5).to_dict(orient="records")
    return {
        "csv_path": csv_path,
        "preview_rows": preview,
        "row_count": len(df),
    }
