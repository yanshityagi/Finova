# agents/agent6_categorizer.py

from google.adk.agents import LlmAgent
from agents import get_model

model = get_model()

# No instructions here — instructions will come dynamically in main.py
txn_categorizer_agent = LlmAgent(
    name="txn_categorizer_agent",
    model=model,
    description="Agent 6: Categorize the statement entries and transactions",
    tools=[],
)
