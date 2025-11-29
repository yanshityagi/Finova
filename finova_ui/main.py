import os

import pandas as pd

from Tools.mongo_tools import get_mongo_client
print("=== DEBUG: Current Working Directory ===")
print(os.getcwd())
print("=== DEBUG: Files in this directory ===")
print(os.listdir(os.getcwd()))
print("========================================")

from Tools.chart_tools import generate_insight_charts

# main.py
from dotenv import load_dotenv
load_dotenv()

import json
import asyncio

from Tools.csv_tools import parse_statement_csv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai import types

from agents.agent1_email_monitor import email_monitor_agent


APP_NAME = "finova_app"
USER_ID = "finova_user"
SESSION_ID_EMAIL = "session_email_1"
DB_NAME = os.getenv("FINOVA_DB_NAME")

# Fail fast if DB_NAME is not provided
if not DB_NAME:
    raise RuntimeError("Environment variable FINOVA_DB_NAME is required but not set or empty. Please set FINOVA_DB_NAME before running.")

def clean_json(text: str) -> str:
    """
    Removes code fences like ```json ... ``` and trims whitespace so json.loads works.
    """
    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    return text


# ============================================================
# AGENT 1 — EMAIL MONITOR
# ============================================================
async def run_agent1_email_monitor():
    print("=== Agent 1: Email Monitoring ===")

    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()

    runner = Runner(
        agent=email_monitor_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )

    await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID_EMAIL,
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text="Fetch the latest bank statement email and return JSON.")],
    )

    final_text = "(no final response received)"

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID_EMAIL,
        new_message=user_message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text

    print("\n--- Agent 1 Final JSON Output ---")
    print(final_text)
    print("---------------------------------")

    return final_text



# ============================================================
# AGENT 2 — CLASSIFIER
# ============================================================
async def run_agent2_classifier(email_json: dict):
    print("=== Agent 2: Bank + Statement Type Classifier ===")

    from agents.agent2_classifier import bank_classifier_agent

    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()

    runner = Runner(
        agent=bank_classifier_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )

    session_id = "session_classifier_1"

    await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    instruction = f"""
You are Agent 2: Classifier.

Your job:
1. Read:
   - subject: {email_json['subject']}
   - from_address: {email_json['from_address']}
   - body_snippet: {email_json.get('body_snippet', '')}

2. Determine:
   - bank_name
   - statement_type

3. Return ONLY JSON:
{{
  "bank_name": "...",
  "statement_type": "...",
  "confidence": "..."
}}
"""

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=instruction)],
    )

    final_text = "(no classifier output)"

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            final_text = event.content.parts[0].text

    print("\n--- Agent 2 Output ---")
    print(final_text)
    print("----------------------")

    return final_text


# ============================================================
# AGENT 3 — STORAGE AGENT - SAVE INTO MONGODB
# ============================================================
async def save_transactions(json_content: str, filename: str) -> bool:

    from agents.agent3_storage import storage_agent
    
    client = get_mongo_client()
    db = client[os.getenv("FINOVA_DB_NAME")]
    col = db["transactions"]
    uploads_col = db["uploaded_files"]
    txn_count = len(json_content["transactions"])

    # Insert transactions
    for tx in json_content["transactions"]:
        col.insert_one(tx)

    # Save upload info
    uploads_col.insert_one({
        "filename": filename,
        "uploaded_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transaction_count": len(json_content["transactions"]),
        "bank_name": "User Upload"
    })
    return True


# ============================================================
# AGENT 6 — TRANSACTION CATEGORIZER
# ============================================================
async def run_agent6_categorizer(csv_content: str) -> str:
    """
    Takes a CSV file as string input and returns the same CSV with an additional 'category' column.
    
    Args:
        csv_content (str): CSV file content as a string
    
    Returns:
        str: CSV content with added 'category' column
    """
    print("=== Agent 6: Transaction Categorization ===")
    
    from agents.agent6_categorizer import txn_categorizer_agent
    import pandas as pd
    from io import StringIO
    
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()
    
    runner = Runner(
        agent=txn_categorizer_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )
    
    session_id = "session_categorizer_1"
    
    await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )
    
    # Parse CSV to understand structure
    try:
        df = pd.read_csv(StringIO(csv_content))
        print(f"CSV loaded successfully. Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        return csv_content
    
    # Create instruction for the agent
    instruction = f"""
You are Agent 6: Transaction Categorizer.

Your job:
1. Analyze the CSV data below and categorize each transaction
2. Add appropriate categories based on transaction descriptions, amounts, and patterns
3. Use these standard categories when possible:
   - Groceries
   - Transport
   - Dining
   - Shopping
   - Bills & Utilities
   - Healthcare
   - Entertainment
   - Rent
   - Salary
   - Transfer
   - Investment
   - Other

4. Return the EXACT same CSV structure with one additional column called 'category' at the end
5. Do NOT include any explanations or markdown formatting
6. Return ONLY the CSV content with headers

CSV Data:
{csv_content}

Return the categorized CSV:
"""
    
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=instruction)],
    )
    
    final_text = "(no categorizer output)"
    
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=user_message,
    ):
        if event.is_final_response() and event.content:
            final_text = event.content.parts[0].text
    
    print("\n--- Agent 6 Output ---")
    print("Categorized CSV generated successfully")
    print("----------------------")
    
    # Clean up the response to ensure it's valid CSV
    cleaned_output = clean_csv_response(final_text)
    return cleaned_output


def clean_csv_response(text: str) -> str:
    """
    Cleans the LLM response to extract valid CSV content.
    """
    text = text.strip()
    
    # Remove code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line if it starts with ```
        if lines[0].startswith("```"):
            lines = lines[1:]
        # Remove last line if it's just ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    
    return text.strip()


# ============================================================
# CATEGORIZE CSV FILE FUNCTION
# ============================================================
def categorize_csv_file(input_csv_path: str, output_csv_path: str = None) -> str:
    """
    Public function to categorize transactions in a CSV file.
    
    Args:
        input_csv_path (str): Path to input CSV file
        output_csv_path (str, optional): Path for output CSV file. If None, returns content as string.
    
    Returns:
        str: Categorized CSV content
    """
    # Read the CSV file
    with open(input_csv_path, 'r', encoding='utf-8') as file:
        csv_content = file.read()
    
    # Run the categorization
    categorized_csv = asyncio.run(run_agent6_categorizer(csv_content))
    
    # Save to output file if path provided
    if output_csv_path:
        with open(output_csv_path, 'w', encoding='utf-8') as file:
            file.write(categorized_csv)
        print(f"Categorized CSV saved to: {output_csv_path}")
    
    return categorized_csv


# ============================================================
# Parse file
# ============================================================
def parse_file(email_json, classifier_json):
    attachment_path = email_json["attachment_path"]
    bank_name = classifier_json["bank_name"]
    account_id = "ACC123"

    parsed = parse_statement_csv(
        path=attachment_path,
        bank_name=bank_name,
        account_id=account_id,
    )

    transactions = parsed["transactions"]

    print("\n=== Parsed Transactions (Agent 3 step) ===")
    print(f"Bank: {parsed['bank_name']}")
    print(f"Account: {parsed['account_id']}")
    print(f"Total transactions parsed: {len(transactions)}")
    print("Sample first 3:")
    for tx in transactions[:3]:
        print(tx)
    return transactions


# ============================================================
# MAIN PIPELINE
# ============================================================
async def main():

    # ---------------------------------------
    # Agent 1 — Email Monitor
    # ---------------------------------------
    email_json_text = await run_agent1_email_monitor()
    email_json = json.loads(email_json_text)

    # ---------------------------------------
    # Agent 2 — Classifier
    # ---------------------------------------
    classifier_json_text = await run_agent2_classifier(email_json)
    classifier_clean = clean_json(classifier_json_text)
    classifier_json = json.loads(classifier_clean)

    # ---------------------------------------
    # Agent 3 — CSV Parsing
    # ---------------------------------------
    transactions = parse_file(email_json, classifier_json)

    # ---------------------------------------
    # Agent 3.3 — MongoDB Insert
    # ---------------------------------------
    print("\n=== Agent 3.3: Storing Transactions into MongoDB ===")
    from Tools.mongo_tools import insert_transactions, list_transactions
 
    result = insert_transactions(
        db_name=DB_NAME,
        collection_name="transactions",
        transactions=transactions,
    )

    print(result)

    print("\n=== Sample from Mongo ===")
    sample = list_transactions(DB_NAME, "transactions", limit=3)
    for doc in sample:
        print(doc)

        # ---------------------------------------
    # Agent 4 — Charts and Insights
    # ---------------------------------------
    print("\n=== Agent 4: Generating charts and insights ===")
    summary_text, chart_paths = generate_insight_charts(transactions)

    print(summary_text)
    print("\nCharts saved:")
    for name, path in chart_paths.items():
        print(f"  - {name}: {path}")

    # ---------------------------------------
    # Agent 6 — Transaction Categorization (Optional Demo)
    # ---------------------------------------
    print("\n=== Agent 6: Transaction Categorization Demo ===")
    
    # Convert transactions to CSV format for demonstration
    import pandas as pd
    df_transactions = pd.DataFrame(transactions)
    csv_content = df_transactions.to_csv(index=False)
    
    # Categorize the transactions
    categorized_csv = await run_agent6_categorizer(csv_content)
    
    # Save categorized results
    output_path = "categorized_transactions.csv"
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(categorized_csv)
    
    print(f"Categorized transactions saved to: {output_path}")


# ============================================================
# STANDALONE CATEGORIZATION FUNCTION
# ============================================================
async def categorize_csv_standalone(csv_file_path: str, output_file_path: str = None):
    """
    Standalone function to categorize any CSV file containing financial transactions.
    
    Args:
        csv_file_path (str): Path to the input CSV file
        output_file_path (str, optional): Path for the output file. If None, uses input filename with '_categorized' suffix
    
    Returns:
        str: Path to the categorized CSV file
    """
    if not output_file_path:
        base_name = os.path.splitext(csv_file_path)[0]
        output_file_path = f"{base_name}_categorized.csv"
    
    # Read input CSV
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_content = file.read()
    
    print(f"Processing CSV file: {csv_file_path}")
    
    # Categorize using Agent 6
    categorized_csv = await run_agent6_categorizer(csv_content)
    
    # Save categorized result
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(categorized_csv)
    
    print(f"Categorized CSV saved to: {output_file_path}")
    return output_file_path


# ============================================================
# RUN MAIN
# ============================================================
if __name__ == "__main__":
    asyncio.run(main())
