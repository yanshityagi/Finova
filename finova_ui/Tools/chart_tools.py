# Tools/chart_tools.py

import os
from typing import List, Dict, Tuple

import matplotlib.pyplot as plt
import pandas as pd


# Soft pastel theme
plt.rcParams.update({
    "font.size": 11,
    "axes.edgecolor": "#E0E0E0",
    "axes.labelcolor": "#444",
    "xtick.color": "#666",
    "ytick.color": "#666",
    "figure.facecolor": "#fafcff",
})

PASTEL_COLORS = ["#A7C7E7", "#C3E8BD", "#F7D8BA", "#E7C6FF", "#FFDEDE"]


def _to_dataframe(transactions: List[Dict]) -> pd.DataFrame:
    """Convert list of transaction dicts to a pandas DataFrame with helpers."""
    df = pd.DataFrame(transactions).copy()

    # Parse date column to datetime
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Ensure numeric debit/credit
    df["debit"] = pd.to_numeric(df["debit"], errors="coerce").fillna(0.0)
    df["credit"] = pd.to_numeric(df["credit"], errors="coerce").fillna(0.0)

    # Net flow per transaction
    df["net"] = df["credit"] - df["debit"]

    return df


def _ensure_output_dir(output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def generate_insight_charts(
    transactions: List[Dict],
    output_dir: str = "finova_ui/charts",
) -> Tuple[Dict, Dict[str, str]]:
    """
    Generate charts and structured summary data from transactions.

    Returns:
        summary_data: dict with keys:
            - total_credits
            - total_debits
            - net_cashflow
            - highest_debit: {description, amount, date} or None
            - highest_credit: {description, amount, date} or None
            - top_categories: list of {category, amount}
        chart_paths: dict with keys:
            - "category_spend"
            - "balance_trend"
          and values as file paths to the saved PNGs.
    """
    output_dir = _ensure_output_dir(output_dir)
    df = _to_dataframe(transactions)
    print(df)
    chart_paths: Dict[str, str] = {}

    # -----------------------------
    # 1. Category Spending Pie Chart (Debits only)
    # -----------------------------
    debit_only = df[df["debit"] > 0]
    if not debit_only.empty:
        cat = debit_only.groupby("category").agg(total_spend=("debit", "sum"))
        cat = cat.reset_index()

        plt.figure()
        plt.pie(
            cat["total_spend"],
            labels=cat["category"],
            autopct="%1.1f%%",
            startangle=140,
            colors=PASTEL_COLORS,
        )
        plt.title("Spending by Category (Debits)")
        plt.tight_layout()

        cat_path = os.path.join(output_dir, "category_spend.png")
        plt.savefig(cat_path)
        plt.close()
        chart_paths["category_spend"] = cat_path
        print("Cat Path: " + cat_path)

    # -----------------------------
    # 2. Daily Balance Trend Line Chart
    # -----------------------------
    if "balance" in df.columns:
        bal_df = df.dropna(subset=["date", "balance"]).copy()
        if not bal_df.empty:
            bal_df = bal_df.sort_values("date")

            plt.figure()
            plt.plot(bal_df["date"], bal_df["balance"])
            plt.xlabel("Date")
            plt.ylabel("Balance")
            plt.title("Daily Account Balance Trend")
            plt.xticks(rotation=45)
            plt.tight_layout()

            bal_path = os.path.join(output_dir, "balance_trend.png")
            plt.savefig(bal_path)
            plt.close()
            chart_paths["balance_trend"] = bal_path
            print("Bal Path: " + bal_path)

    # -----------------------------
    # 3. Build structured summary data
    # -----------------------------
    total_debits = float(df["debit"].sum())
    total_credits = float(df["credit"].sum())
    net_total = total_credits - total_debits

    highest_debit = None
    if (df["debit"] > 0).any():
        row = df.loc[df["debit"].idxmax()]
        date_str = row["date"].date().isoformat() if not pd.isna(row["date"]) else ""
        highest_debit = {
            "description": str(row["description"]),
            "amount": float(row["debit"]),
            "date": date_str,
        }

    highest_credit = None
    if (df["credit"] > 0).any():
        row = df.loc[df["credit"].idxmax()]
        date_str = row["date"].date().isoformat() if not pd.isna(row["date"]) else ""
        highest_credit = {
            "description": str(row["description"]),
            "amount": float(row["credit"]),
            "date": date_str,
        }

    top_categories_list = []
    if not debit_only.empty:
        top_cat = debit_only.groupby("category")["debit"].sum().sort_values(
            ascending=False
        )
        for cat_name, amt in top_cat.head(5).items():
            top_categories_list.append(
                {"category": str(cat_name), "amount": float(amt)}
            )

    summary_data: Dict = {
        "total_credits": total_credits,
        "total_debits": total_debits,
        "net_cashflow": net_total,
        "highest_debit": highest_debit,
        "highest_credit": highest_credit,
        "top_categories": top_categories_list,
    }

    return summary_data, chart_paths

