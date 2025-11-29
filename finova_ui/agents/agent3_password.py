# agents/agent3_password.py

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from . import get_model
from tools.pdf_tools import unlock_pdf

model = get_model()

instruction = """
You are Agent 3.1: Password Agent for Finova.

You help handle password-protected bank statement PDFs.

You will:
1. Decide whether the bank statement is likely password-protected based on the email context and bank name.
2. Guess the password if needed (e.g., DOB, last 4 digits, PAN, etc.) based on rules.
3. Call the unlock_pdf tool with pdf_path and the guessed password.
4. Return:
   - whether password was needed
   - what password you used (if any)
   - unlocked_path from the tool

Be concise and avoid exposing sensitive info unnecessarily in a real system.
This is a simulated environment for a student capstone.
"""

password_agent = LlmAgent(
    name="password_agent",
    model=model,
    description="Figures out passwords (simulated) and unlocks PDFs.",
    instruction=instruction,
    tools=[FunctionTool(unlock_pdf)],
)
