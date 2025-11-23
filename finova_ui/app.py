# finova_ui/app.py

import os
import sys
import json
import streamlit as st
from dotenv import load_dotenv

# ======================================================
# 1️⃣ Load .env from this folder (finova_ui/.env)
# ======================================================
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
print("🔍 Loading .env from:", ENV_PATH)
load_dotenv(ENV_PATH)

print("🔍 MONGODB_URI loaded:", os.getenv("MONGODB_URI"))
print("🔍 FINOVA_DB_NAME loaded:", os.getenv("FINOVA_DB_NAME"))


# ======================================================
# 2️⃣ Add project root to PYTHONPATH for imports
# ======================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


# ======================================================
# Imports AFTER sys.path fix
# ======================================================
from Tools.mongo_tools import get_mongo_client
from Tools.chart_tools import generate_insight_charts

try:
    from google.genai import Client
except ImportError:
    Client = None


# ======================================================
# Helpers
# ======================================================
def get_transactions():
    """Fetch all transactions from MongoDB."""

    load_dotenv(ENV_PATH)

    MONGO_URI = os.getenv("MONGODB_URI")
    DB_NAME = os.getenv("FINOVA_DB_NAME", "finova")

    if not MONGO_URI:
        raise Exception("❌ MONGODB_URI not found. Make sure .env exists in finova_ui/")

    client = get_mongo_client()  # Tools.mongo_tools uses this too
    db = client[DB_NAME]
    collection = db["transactions"]

    return list(collection.find({}, {"_id": 0}))


def get_gemini_client():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or Client is None:
        return None
    return Client(api_key=api_key)


# ======================================================
# Chart + LLM Handler
# ======================================================
def answer_question_with_llm(question: str, transactions):
    """
    Detect chart requests & generate charts locally.
    Otherwise, use Gemini for text answers.
    """

    chart_keywords = ["chart", "plot", "graph", "visualize", "trend", "monthly"]

    # ============ Detect Chart Request ============
    if any(word in question.lower() for word in chart_keywords):

        import pandas as pd
        import matplotlib.pyplot as plt

        df = pd.DataFrame(transactions)

        # Robust date parsing
        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce",
            dayfirst=True,
            format="mixed"
        )

        df = df.dropna(subset=["date"])

        # Detect grocery category
        is_grocery = "grocery" in question.lower() or "groceries" in question.lower()
        if is_grocery:
            df = df[df["description"].str.contains("grocery", case=False, na=False)]

        df["month"] = df["date"].dt.to_period("M").astype(str)
        df_grouped = df.groupby("month")["debit"].sum().reset_index()

        # Plot
        plt.figure(figsize=(10, 4))
        plt.plot(df_grouped["month"], df_grouped["debit"])
        plt.xticks(rotation=45)
        plt.title("Monthly Grocery Expenses")
        plt.xlabel("Month")
        plt.ylabel("Amount (₹)")
        plt.tight_layout()

        chart_path = "grocery_monthly_chart.png"
        plt.savefig(chart_path)

        return {
            "type": "chart",
            "path": chart_path,
            "message": "Here is your monthly grocery expense chart."
        }

    # =============== Gemini Text Answer ===============
    client = get_gemini_client()
    if client is None:
        return "Gemini client is not configured."

    tx_json = json.dumps(transactions, default=str)

    prompt = f"""
    You are Finova, an AI financial assistant.
    User question: {question}
    Transaction data: {tx_json}
    Provide a clear, concise financial answer.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt],
        )
        return getattr(response, "text", str(response))
    except Exception as e:
        return str(e)


# ======================================================
# Streamlit UI Setup
# ======================================================
st.set_page_config(
    page_title="Finova – AI Financial Insights",
    page_icon="💸",
    layout="wide",
)

st.sidebar.title("Finova")
page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "💬 Chat with Finova"],
)

st.sidebar.markdown("---")
st.sidebar.caption("Multi-agent AI finance assistant")


# ======================================================
# PAGE: DASHBOARD
# ======================================================
if page == "📊 Dashboard":
    st.title("📊 Financial Insights Dashboard")

    with st.spinner("Loading transactions from MongoDB..."):
        transactions = get_transactions()

    if not transactions:
        st.warning("No transactions found. Run `python main.py` first.")
    else:
        summary_text, chart_paths = generate_insight_charts(transactions)

        st.subheader("Summary")
        st.markdown(f"```text\n{summary_text}\n```")

        col1, col2 = st.columns(2)

        with col1:
            if "monthly_cashflow" in chart_paths:
                st.subheader("Monthly Credits vs Debits")
                st.image(chart_paths["monthly_cashflow"])
            if "balance_trend" in chart_paths:
                st.subheader("Daily Balance Trend")
                st.image(chart_paths["balance_trend"])

        with col2:
            if "category_spend" in chart_paths:
                st.subheader("Spending by Category")
                st.image(chart_paths["category_spend"])

        st.success("Dashboard generated from live MongoDB data ✅")


# ======================================================
# PAGE: CHAT WITH FINOVA
# ======================================================
elif page == "💬 Chat with Finova":
    st.title("💬 Chat with Finova")
    st.caption("Ask anything about your transactions or spending patterns.")

    with st.spinner("Loading transactions from MongoDB..."):
        transactions = get_transactions()

    if not transactions:
        st.warning("No transactions found. Run `python main.py` first.")
    else:

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # --------------- Show previous messages ---------------
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                if isinstance(msg["content"], dict) and msg["content"].get("type") == "chart":
                    st.markdown(msg["content"]["message"])
                    st.image(msg["content"]["path"])
                else:
                    st.markdown(msg["content"])

        # ------------------- User Input -------------------
        user_input = st.chat_input("Ask Finova something...")

        if user_input:
            # Save and show user message
            st.session_state.chat_history.append(
                {"role": "user", "content": user_input}
            )
            with st.chat_message("user"):
                st.markdown(user_input)

            # Assistant response
            with st.chat_message("assistant"):
                with st.spinner("Finova is thinking..."):
                    answer = answer_question_with_llm(user_input, transactions)

                    if isinstance(answer, dict) and answer.get("type") == "chart":
                        st.markdown(answer["message"])
                        st.image(answer["path"])
                    else:
                        st.markdown(answer)

            # Save assistant message
            st.session_state.chat_history.append(
                {"role": "assistant", "content": answer}
            )
