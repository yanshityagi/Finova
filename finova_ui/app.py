# finova_ui/app.py

import os
import sys
import json
import streamlit as st
from dotenv import load_dotenv
import pandas as pd

# ======================================================
# 1. Load .env from this folder (finova_ui/.env)
# ======================================================
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

# ======================================================
# 2. Add project root to PYTHONPATH for imports
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

    client = get_mongo_client()
    db = client[DB_NAME]
    collection = db["transactions"]

    return list(collection.find({}, {"_id": 0}))


def get_gemini_client():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or Client is None:
        return None
    return Client(api_key=api_key)


def answer_question_with_llm(question: str, transactions):
    """
    Detect chart requests and generate charts locally.
    Otherwise, use Gemini for text answers.
    """

    chart_keywords = ["chart", "plot", "graph", "visualize", "trend", "monthly"]

    # ============ Detect Chart Request ============
    if any(word in question.lower() for word in chart_keywords):

        import matplotlib.pyplot as plt

        df = pd.DataFrame(transactions)

        # Robust date parsing
        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce",
            dayfirst=True,
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
            "message": "Here is your monthly grocery expense chart.",
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

# Global soft theme and spacing
st.markdown(
    """
<style>
/* App background */
body {
    background-color: #fafcff;
}

/* Main container padding */
.block-container {
    padding-top: 1.5rem;
}

/* Headings */
h1, h2, h3 {
    color: #111827;
    letter-spacing: -0.02em;
}
h1 {
    margin-bottom: 0.75rem;
}
h2, h3 {
    margin-top: 2rem;
    margin-bottom: 0.5rem;
}

/* Sidebar styling */
div[data-testid="stSidebar"] {
    background-color: #f5f5fb;
    border-right: 1px solid #e5e7eb;
}
div[data-testid="stSidebar"] .sidebar-title {
    font-weight: 700;
    font-size: 20px;
    margin-bottom: 0.5rem;
}
div[data-testid="stSidebar"] .sidebar-caption {
    font-size: 12px;
    color: #6b7280;
    margin-top: 1.5rem;
}

/* Sidebar nav buttons (nav looks like modern app, not radios) */
div[data-testid="stSidebar"] .stButton > button {
    background: none !important;
    border: none !important;
    color: #111827 !important;
    padding: 4px 0 !important;
    font-size: 15px !important;
    text-align: left !important;
    box-shadow: none !important;
}
/* Hover state – subtle text highlight */
div[data-testid="stSidebar"] .stButton > button:hover {
    background: none !important;
    border: none !important;
    color: #2563eb !important; /* blue hover */
    cursor: pointer;
}

/* Simple utility for vertical spacing between sections */
.section-gap {
    margin-top: 32px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ======================================================
# Sidebar Navigation (no radio, clickable labels)
# ======================================================
with st.sidebar:
    
    st.markdown("### Navigation")

    if "page" not in st.session_state:
        st.session_state.page = "dashboard"

    nav_dashboard = st.button("📊 Dashboard", key="nav_dashboard")
    nav_chat = st.button("💬 Chat with Finova", key="nav_chat")

    if nav_dashboard:
        st.session_state.page = "dashboard"
    if nav_chat:
        st.session_state.page = "chat"

    st.markdown("---")
    st.markdown(
        '<div class="sidebar-caption">Multi-agent AI finance assistant</div>',
        unsafe_allow_html=True,
    )

page = st.session_state.page


# ======================================================
# Helper for pretty money formatting
# ======================================================
def _fmt_inr(value: float) -> str:
    return f"₹{value:,.2f}"


def _metric_card(title: str, value: str, emoji: str = "", subtitle: str = None) -> str:
    return f"""
    <div style="
        background:#ffffff;
        border-radius:16px;
        padding:16px 18px;
        border:1px solid #e5e7eb;
        box-shadow:0 2px 6px rgba(15,23,42,0.04);
    ">
        <div style="font-size:13px;color:#6b7280;margin-bottom:4px;">
            {emoji} {title}
        </div>
        <div style="font-size:20px;font-weight:600;color:#111827;margin-bottom:2px;">
            {value}
        </div>
        {f'<div style="font-size:12px;color:#9ca3af;">{subtitle}</div>' if subtitle else ""}
    </div>
    """


# ======================================================
# PAGE: DASHBOARD
# ======================================================
if page == "dashboard":
    st.title("📊 Financial Insights Dashboard")

    with st.spinner("Loading transactions from MongoDB..."):
        transactions = get_transactions()

    if not transactions:
        st.warning("No transactions found. Run `python main.py` first.")
    else:
        # Get structured summary data and chart paths
        summary_data, chart_paths = generate_insight_charts(transactions)

        # ---------- Key Metrics as Cards ----------
        st.markdown("### Overview")

        total_credits = summary_data.get("total_credits", 0.0)
        total_debits = summary_data.get("total_debits", 0.0)
        net_cashflow = summary_data.get("net_cashflow", 0.0)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                _metric_card(
                    title="Total Credits",
                    value=_fmt_inr(total_credits),
                    emoji="💰",
                ),
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                _metric_card(
                    title="Total Debits",
                    value=_fmt_inr(total_debits),
                    emoji="💸",
                ),
                unsafe_allow_html=True,
            )

        with col3:
            net_color = "#16a34a" if net_cashflow >= 0 else "#dc2626"
            st.markdown(
                f"""
                <div style="
                    background:#ffffff;
                    border-radius:16px;
                    padding:16px 18px;
                    border:1px solid #e5e7eb;
                    box-shadow:0 2px 6px rgba(15,23,42,0.04);
                ">
                    <div style="font-size:13px;color:#6b7280;margin-bottom:4px;">
                        📈 Net Cashflow
                    </div>
                    <div style="font-size:20px;font-weight:600;color:{net_color};margin-bottom:2px;">
                        {_fmt_inr(net_cashflow)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ---------- Transactions Highlights ----------
        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        st.markdown("### Highlights")

        high_debit = summary_data.get("highest_debit")
        high_credit = summary_data.get("highest_credit")

        c1, c2 = st.columns(2)

        with c1:
            if high_debit:
                st.markdown(
                    _metric_card(
                        title="Highest Debit",
                        value=_fmt_inr(high_debit["amount"]),
                        emoji="🔻",
                        subtitle=f"{high_debit['description']} · {high_debit['date']}",
                    ),
                    unsafe_allow_html=True,
                )
            else:
                st.info("No debit transactions found.")

        with c2:
            if high_credit:
                st.markdown(
                    _metric_card(
                        title="Highest Credit",
                        value=_fmt_inr(high_credit["amount"]),
                        emoji='<span style="color:#16a34a;">▲</span>',
                        subtitle=f"{high_credit['description']} · {high_credit['date']}",
                    ),
                    unsafe_allow_html=True,
                )
            else:
                st.info("No credit transactions found.")

        # ---------- Top Categories ----------
        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        st.markdown("### Top Spending Categories")

        top_categories = summary_data.get("top_categories", [])

        if top_categories:
            cat_lines = "".join(
                f"<li>{item['category']}: <b>{_fmt_inr(item['amount'])}</b></li>"
                for item in top_categories
            )
            st.markdown(
                f"""
                <div style="
                    background:#ffffff;
                    border-radius:16px;
                    padding:16px 18px;
                    border:1px solid #e5e7eb;
                    box-shadow:0 2px 6px rgba(15,23,42,0.04);
                ">
                    <ul style="padding-left:20px;margin:0;">
                        {cat_lines}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("No spending categories available.")

        # ---------- Charts Section ----------
        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        st.markdown("### Charts")

        col_left, col_right = st.columns(2)

        with col_left:
            if "balance_trend" in chart_paths:
                st.subheader("Daily Balance Trend")
                st.image(chart_paths["balance_trend"])
        with col_right:
            if "category_spend" in chart_paths:
                st.subheader("Spending by Category")
                st.image(chart_paths["category_spend"])

        st.success("Dashboard generated from live MongoDB data ✅")


# ======================================================
# PAGE: CHAT WITH FINOVA
# ======================================================
elif page == "chat":
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
