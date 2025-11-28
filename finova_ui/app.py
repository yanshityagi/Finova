# finova_ui/app.py

import os
import sys
import json
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# ======================================================
# Load .env
# ======================================================
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

# ======================================================
# Add project root to PYTHONPATH
# ======================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# ======================================================
# Imports
# ======================================================
from Tools.mongo_tools import get_mongo_client
from Tools.chart_tools import generate_insight_charts
from Tools.csv_tools import parse_statement_csv  # <-- CSV parser

try:
    from google.genai import Client
except ImportError:
    Client = None


# ======================================================
# Helpers
# ======================================================
def get_transactions():
    """Fetch all transactions from MongoDB."""
    client = get_mongo_client()
    db = client[os.getenv("FINOVA_DB_NAME")]
    return list(db["transactions"].find({}, {"_id": 0}))


def get_gemini_client():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or Client is None:
        return None
    return Client(api_key=api_key)


# ======================================================
# LLM Logic
# ======================================================
def answer_question_with_llm(question: str, transactions):
    import matplotlib.pyplot as plt

    chart_keywords = ["chart", "plot", "graph", "visualize", "trend"]

    if any(word in question.lower() for word in chart_keywords):
        df = pd.DataFrame(transactions)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        df["month"] = df["date"].dt.to_period("M").astype(str)
        df_grouped = df.groupby("month")["debit"].sum().reset_index()

        plt.figure(figsize=(10, 4))
        plt.plot(df_grouped["month"], df_grouped["debit"])
        plt.xticks(rotation=45)
        plt.tight_layout()

        chart_path = "generated_chart.png"
        plt.savefig(chart_path)

        return {"type": "chart", "path": chart_path, "message": "Here is your chart."}

    client = get_gemini_client()
    if client is None:
        return "Gemini client not configured."

    prompt = f"""
    You are Finova, an AI assistant.
    User asked: {question}
    Transactions: {json.dumps(transactions)}
    Provide a clear answer.
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
# UI CONFIG
# ======================================================
st.set_page_config(page_title="Finova", page_icon="💸", layout="wide")

st.markdown("""
<style>
div[data-testid="stSidebar"] {
    background-color: #f5f5fb;
    border-right: 1px solid #e5e7eb;
}
div[data-testid="stSidebar"] .stButton > button {
    background: none !important;
    border: none !important;
    color: #111827 !important;
    padding: 4px 0 !important;
    text-align: left !important;
}
div[data-testid="stSidebar"] .stButton > button:hover {
    color: #2563eb !important;
}
.section-gap {
    margin-top: 32px;
}
</style>
""", unsafe_allow_html=True)


# ======================================================
# SIDEBAR NAVIGATION
# ======================================================
with st.sidebar:
    st.markdown("### Navigation")

    if "page" not in st.session_state:
        st.session_state.page = "dashboard"

    if st.button("📊 Dashboard"):
        st.session_state.page = "dashboard"

    if st.button("📤 Upload Statement"):
        st.session_state.page = "upload"

    if st.button("💬 Chat with Finova"):
        st.session_state.page = "chat"

    st.markdown("---")
    st.caption("Multi-agent AI finance assistant")

page = st.session_state.page


# ======================================================
# HELPER FOR METRICS
# ======================================================
def _fmt_inr(value: float) -> str:
    return f"₹{value:,.2f}"


def _metric_card(title, value, emoji="", subtitle=None):
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
# PAGE: UPLOAD STATEMENT (UPDATED)
# ======================================================
if page == "upload":
    st.title("📤 Upload Bank Statement")
    st.caption("Upload a CSV file. Parsed data will be added to your financial database.")

    # NEW: File uploader
    st.markdown("### Upload New File")
    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

    if uploaded_file:
        with st.spinner("Processing file..."):

            parsed = parse_statement_csv(
                path=None,
                uploaded_file=uploaded_file,
                bank_name="User Upload",
                account_id="USER001"
            )

            # Reconnect inside this block (fix)
            client = get_mongo_client()
            db = client[os.getenv("FINOVA_DB_NAME")]
            col = db["transactions"]
            uploads_col = db["uploaded_files"]

            # Insert transactions
            for tx in parsed["transactions"]:
                col.insert_one(tx)

            # Save upload info
            uploads_col.insert_one({
                "filename": uploaded_file.name,
                "uploaded_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "transaction_count": len(parsed["transactions"]),
                "bank_name": "User Upload"
            })

        st.success("File uploaded and processed successfully!")
        st.info("You can now check the Dashboard or chat with Finova.")

    # NEW: fetch upload history collection
    client = get_mongo_client()
    db = client[os.getenv("FINOVA_DB_NAME")]
    uploads_col = db["uploaded_files"]

    # NEW: show last uploaded files
    st.markdown("### 📁 Recently Uploaded Files")

    recent_uploads = list(
        uploads_col.find({}, {"_id": 0}).sort("uploaded_at", -1).limit(5)
    )

    if recent_uploads:
        for u in recent_uploads:
            st.markdown(f"""
            <div style="
                background:white;
                padding:12px 16px;
                border-radius:12px;
                border:1px solid #e5e7eb;
                margin-bottom:8px;
            ">
                <b>📄 {u['filename']}</b>
                <div style="font-size:12px;color:#6b7280;">
                    Uploaded: {u['uploaded_at']}<br>
                    Transactions: {u['transaction_count']}<br>
                    Bank: {u.get('bank_name','-')}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No files uploaded yet.")

    


# ======================================================
# PAGE: DASHBOARD (UNCHANGED)
# ======================================================
elif page == "dashboard":
    st.title("📊 Financial Insights Dashboard")

    with st.spinner("Loading transactions from MongoDB..."):
        transactions = get_transactions()

    if not transactions:
        st.warning("No transactions found. Run `python main.py` first.")
    else:
        summary_data, chart_paths = generate_insight_charts(transactions)

        st.markdown("### Overview")
        total_credits = summary_data.get("total_credits", 0.0)
        total_debits = summary_data.get("total_debits", 0.0)
        net_cashflow = summary_data.get("net_cashflow", 0.0)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(_metric_card("Total Credits", _fmt_inr(total_credits), "💰"), unsafe_allow_html=True)
        with col2:
            st.markdown(_metric_card("Total Debits", _fmt_inr(total_debits), "💸"), unsafe_allow_html=True)
        with col3:
            net_color = "#16a34a" if net_cashflow >= 0 else "#dc2626"
            st.markdown(
                _metric_card(
                    "Net Cashflow",
                    f'<span style="color:{net_color};">{_fmt_inr(net_cashflow)}</span>',
                    "📈",
                ),
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        st.markdown("### Highlights")

        high_debit = summary_data.get("highest_debit")
        high_credit = summary_data.get("highest_credit")

        c1, c2 = st.columns(2)

        with c1:
            if high_debit:
                st.markdown(
                    _metric_card("Highest Debit", _fmt_inr(high_debit["amount"]), "🔻",
                                 f"{high_debit['description']} · {high_debit['date']}"),
                    unsafe_allow_html=True,
                )

        with c2:
            if high_credit:
                st.markdown(
                    _metric_card("Highest Credit", _fmt_inr(high_credit["amount"]),
                                 '<span style="color:#16a34a;">▲</span>',
                                 f"{high_credit['description']} · {high_credit['date']}"),
                    unsafe_allow_html=True,
                )

        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        st.markdown("### Top Spending Categories")

        top_categories = summary_data.get("top_categories", [])
        if top_categories:
            items = "".join(
                f"<li>{item['category']}: <b>{_fmt_inr(item['amount'])}</b></li>"
                for item in top_categories
            )
            st.markdown(
                f"""
                <div style="background:white;padding:16px;border-radius:12px;border:1px solid #e5e7eb;">
                    <ul>{items}</ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        st.markdown("### Charts")

        cL, cR = st.columns(2)
        with cL:
            if "balance_trend" in chart_paths:
                st.image(chart_paths["balance_trend"])
        with cR:
            if "category_spend" in chart_paths:
                st.image(chart_paths["category_spend"])

        st.success("Dashboard generated from live MongoDB data ✔️")


# ======================================================
# PAGE: CHAT (UNCHANGED)
# ======================================================
elif page == "chat":
    st.title("💬 Chat with Finova")

    transactions = get_transactions()

    if not transactions:
        st.warning("Upload a CSV first.")
    else:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                if isinstance(msg["content"], dict):
                    st.image(msg["content"]["path"])
                else:
                    st.markdown(msg["content"])

        user_input = st.chat_input("Ask Finova...")

        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                reply = answer_question_with_llm(user_input, transactions)
                if isinstance(reply, dict):
                    st.image(reply["path"])
                else:
                    st.markdown(reply)

            st.session_state.chat_history.append({"role": "assistant", "content": reply})
