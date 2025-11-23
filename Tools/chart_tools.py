# Tools/chart_tools.py

import os
from datetime import datetime
from typing import List, Dict, Tuple

import matplotlib.pyplot as plt
import pandas as pd


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


def _infer_category(description: str) -> str:
    """Very simple category inference based on keywords."""
    desc = description.lower()

    if "rent" in desc:
        return "Rent"
    if "grocery" in desc or "supermarket" in desc or "big bazaar" in desc:
        return "Groceries"
    if "uber" in desc or "ola" in desc or "transport" in desc or "fuel" in desc:
        return "Transport"
    if "restaurant" in desc or "dining" in desc or "cafe" in desc:
        return "Dining"
    if "salary" in desc or "credit" in desc or "interest" in desc:
        return "Income"
    if "electricity" in desc or "water" in desc or "gas" in desc or "bill" in desc:
        return "Utilities"
    if "shopping" in desc or "amazon" in desc or "flipkart" in desc:
        return "Shopping"

    return "Other"


def _add_category_column(df: pd.DataFrame) -> pd.DataFrame:
    df["category"] = df["description"].apply(_infer_category)
    return df


def _ensure_output_dir(output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def generate_insight_charts(
    transactions: List[Dict],
    output_dir: str = "finova_ui/charts",
) -> Tuple[str, Dict[str, str]]:
    """
    Generate charts and a text summary from transactions.

    Returns:
        summary_text: human readable summary string
        chart_paths: dict with keys:
            - "monthly_cashflow"
            - "category_spend"
            - "balance_trend"
          and values as file paths to the saved PNGs.
    """
    output_dir = _ensure_output_dir(output_dir)
    df = _to_dataframe(transactions)
    df = _add_category_column(df)

    chart_paths: Dict[str, str] = {}

    # -----------------------------
    # 1. Monthly Cashflow Chart
    # -----------------------------
    if not df["date"].isna().all():
        df["year_month"] = df["date"].dt.to_period("M").astype(str)
        monthly = df.groupby("year_month").agg(
            total_credit=("credit", "sum"),
            total_debit=("debit", "sum"),
            net=("net", "sum"),
        )
        monthly = monthly.reset_index()

        plt.figure()
        x = range(len(monthly))
        width = 0.35

        plt.bar(x, monthly["total_credit"], width=width, label="Credits")
        plt.bar(
            [i + width for i in x],
            monthly["total_debit"],
            width=width,
            label="Debits",
        )
        plt.xticks([i + width / 2 for i in x], monthly["year_month"], rotation=45)
        plt.ylabel("Amount")
        plt.title("Monthly Credits and Debits")
        plt.legend()
        plt.tight_layout()

        monthly_path = os.path.join(output_dir, "monthly_cashflow.png")
        plt.savefig(monthly_path)
        plt.close()
        chart_paths["monthly_cashflow"] = monthly_path
    else:
        monthly = None

    # -----------------------------
    # 2. Category Spending Pie Chart
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
        )
        plt.title("Spending by Category (Debits)")
        plt.tight_layout()

        cat_path = os.path.join(output_dir, "category_spend.png")
        plt.savefig(cat_path)
        plt.close()
        chart_paths["category_spend"] = cat_path

    # -----------------------------
    # 3. Daily Balance Trend Line Chart
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

    # -----------------------------
    # 4. Build summary text
    # -----------------------------
    total_debits = df["debit"].sum()
    total_credits = df["credit"].sum()
    net_total = total_credits - total_debits

    highest_debit = df.iloc[df["debit"].idxmax()] if (df["debit"] > 0).any() else None
    highest_credit = df.iloc[df["credit"].idxmax()] if (df["credit"] > 0).any() else None

    top_cat_text = ""
    if not debit_only.empty:
        top_cat = debit_only.groupby("category")["debit"].sum().sort_values(
            ascending=False
        )
        top_cat_text_lines = [
            f"  - {cat}: ₹{amt:,.2f}" for cat, amt in top_cat.head(5).items()
        ]
        top_cat_text = "\n".join(top_cat_text_lines)

    summary_lines = []
    summary_lines.append("=== Agent 4: Financial Insights Summary ===")
    summary_lines.append("")
    summary_lines.append(f"Total Credits: ₹{total_credits:,.2f}")
    summary_lines.append(f"Total Debits: ₹{total_debits:,.2f}")
    summary_lines.append(f"Net Cashflow: ₹{net_total:,.2f}")
    summary_lines.append("")

    if highest_debit is not None:
        summary_lines.append("Highest Debit Transaction:")
        summary_lines.append(f"  - Date: {highest_debit['date'].date()}")
        summary_lines.append(f"  - Description: {highest_debit['description']}")
        summary_lines.append(f"  - Amount: ₹{highest_debit['debit']:,.2f}")
        summary_lines.append("")

    if highest_credit is not None:
        summary_lines.append("Highest Credit Transaction:")
        summary_lines.append(f"  - Date: {highest_credit['date'].date()}")
        summary_lines.append(f"  - Description: {highest_credit['description']}")
        summary_lines.append(f"  - Amount: ₹{highest_credit['credit']:,.2f}")
        summary_lines.append("")

    if top_cat_text:
        summary_lines.append("Top Spending Categories (by debit):")
        summary_lines.append(top_cat_text)
        summary_lines.append("")

    if monthly is not None and not monthly.empty:
        summary_lines.append("Monthly Net Cashflow:")
        for _, row in monthly.iterrows():
            summary_lines.append(
                f"  - {row['year_month']}: ₹{row['net']:,.2f}"
            )

    summary_text = "\n".join(summary_lines)

    return summary_text, chart_paths
