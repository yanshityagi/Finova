import os
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
# MAIN PIPELINE
# ============================================================
async def main():

    # ---------------------------------------
    # Agent 1 — Email Monitor
    # ---------------------------------------
    # email_json_text = await run_agent1_email_monitor()
    # email_json = json.loads(email_json_text)

    # ---------------------------------------
    # Agent 2 — Classifier
    # ---------------------------------------
    classifier_json_text = await run_agent2_classifier(email_json)
    classifier_clean = clean_json(classifier_json_text)
    classifier_json = json.loads(classifier_clean)

    # ---------------------------------------
    # Agent 3 — CSV Parsing
    # ---------------------------------------
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




# ============================================================
# RUN MAIN
# ============================================================
if __name__ == "__main__":
    asyncio.run(main())
