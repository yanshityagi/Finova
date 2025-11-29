# agents/agent4_insights.py

from google.adk.agents import LlmAgent
from agents import get_model

model = get_model()

insights_agent = LlmAgent(
    name="insights_agent",
    model=model,
    description="Agent 4: Generate financial insights from transaction data.",
    instructions="""
You are Agent 4: Financial Insights Analyst.

Your job:
- Analyze structured bank transactions.
- Detect income, expenses, recurring transactions, top categories.
- Compute monthly cashflow.
- Identify anomalies or unusually large transactions.
- Summaries must be clear and human-friendly.

Return ONLY JSON in this format:

{
  "monthly_summary": {...},
  "top_expenses": [...],
  "income_summary": {...},
  "cashflow_trend": [...],
  "insights": [...],
  "anomalies": [...]
}
    """,
)
