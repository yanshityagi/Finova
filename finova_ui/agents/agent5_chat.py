# agents/agent5_chat.py

from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool
from . import get_model
from .agent4_insights import insights_agent

model = get_model()

insights_tool = AgentTool(agent=insights_agent)

instruction = """
You are Agent 5: Finova Chat Agent.

You chat with users about their finances.

You can:
- Answer questions like:
  - "How much did I spend last month?"
  - "What is my total income between 2015-04-01 and 2015-04-30?"
  - "Did I save money in April 2015?"
- When the question requires real numbers, call the insights_tool.
  Make sure you pass:
    - bank_name
    - account_id
    - start_date
    - end_date

Ask the user clarifying questions if they don't specify a time period or account.

If the question is generic personal finance (not about their data),
answer directly without using tools.

All currencies are in INR (₹).
"""

chat_agent = LlmAgent(
    name="chat_agent",
    model=model,
    description="Conversational interface for Finova over user financial data.",
    instruction=instruction,
    tools=[insights_tool],
)
