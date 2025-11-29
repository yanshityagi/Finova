# agents/agent1_email_monitor.py

from google.adk.agents import LlmAgent
from google.genai import types  # Not strictly needed yet, but handy later.

from agents import get_model
from Tools.email_tools import fetch_latest_statement_email


# Get a Gemini model instance from our helper
model = get_model()

# Define Agent 1 as a standard LlmAgent
email_monitor_agent = LlmAgent(
    name="email_monitor_agent",
    model=model,
    description=(
        "Agent 1. Monitors the (simulated) email inbox and returns the latest "
        "bank statement email details plus attachment path."
    ),
    instruction=(
        "You are Agent 1: Email Inbox Monitoring.\n\n"
        "You have access to a tool called `fetch_latest_statement_email` "
        "which returns metadata about the latest bank statement email and "
        "the path to the attached statement file.\n\n"
        "When you are invoked:\n"
        "1. Always call `fetch_latest_statement_email()`.\n"
        "2. Do NOT invent data. Use exactly what the tool returns.\n"
        "3. Respond with ONLY a valid JSON object representing the tool output, "
        "no extra explanation, no prose.\n"
        "4. Keys to include: status, subject, from_address, bank_name, "
        "statement_type, attachment_path.\n"
    ),
    tools=[fetch_latest_statement_email],
)
