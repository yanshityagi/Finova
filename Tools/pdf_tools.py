# tools/pdf_tools.py

import shutil
from typing import Dict

def unlock_pdf(path: str, password: str = "") -> Dict:
    """
    Simulate unlocking a password-protected PDF.

    For now we just return the same path.
    In a real app, you'd use pikepdf or pypdf here.
    """
    return {"unlocked_path": path}

def pdf_to_csv(pdf_path: str, output_csv_path: str) -> Dict:
    """
    Simulate converting a bank statement PDF to a CSV.

    For the capstone demo, we copy a template CSV
    (for example the Agent 0 output CSV) to the output path.
    """
    # You can point this to your Agent 0 CSV file
    template_csv = "data/Agent0_simulated_bank_statement.csv"

    shutil.copy(template_csv, output_csv_path)
    return {"csv_path": output_csv_path}
