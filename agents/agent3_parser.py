# agents/agent3_parser.py

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from . import get_model
from tools.pdf_tools import pdf_to_csv
from tools.csv_tools import parse_statement_csv

model = get_model()

instruction = """
You are Agent 3.2: Statement Parsing Agent for Finova.

You receive:
- pdf_path (unlocked PDF)
- bank_name
- account_id

Your job:
1. Call pdf_to_csv to convert the PDF to a CSV file.
2. Take the csv_path from that tool result.
3. Call parse_statement_csv with:
   - path = csv_path
   - bank_name
   - account_id
4. Return:
   - bank_name
   - account_id
   - csv_path
   - transactions (the list from parse_statement_csv)

Be concise. Don't invent transactions. Use only the tool outputs.
"""

statement_parsing_agent = LlmAgent(
    name="statement_parsing_agent",
    model=model,
    description="Converts statement PDFs into normalized transactions.",
    instruction=instruction,
    tools=[
        FunctionTool(pdf_to_csv),
        FunctionTool(parse_statement_csv),
    ],
)
