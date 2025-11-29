# README

## Maintainer

@yanshityagi

## Requiremenrs

### **Purpose**

FINOVA delivers **deep financial insight, navigation, optimisation, verification and analysis** for individuals and businesses. It turns raw statements into organised intelligence, giving users clarity, confidence and actionable understanding of their financial activity.

### **Vision**

FINOVA aims to become a **full-scale financial interpretation and assistance platform**, powered by generative AI, data science and machine learning.
It normalises complex data, orchestrates specialised agents, validates information, and provides precise, context-aware guidance across the user’s entire financial landscape.

### **Value Proposition**

FINOVA integrates **generative AI, data science and machine learning** into a coordinated virtual-agent ecosystem.
It automates statement interpretation, normalisation, cross-ledger orchestration and data validation.
The result is a **consistent, reliable financial understanding layer** that reduces manual workload, eliminates ambiguity and delivers actionable, real-time clarity.

### **Strategic Goal**

To become the **trusted intelligence engine** that sits between financial data and financial decisions, powering analytics, compliance, forecasting and personalised guidance for every user segment.

# Problem

Finance today is fractured. People and businesses collect statements from dozens of accounts, cards, loans, wallets and investments. Everyone wants clarity, yet everything is scattered.

FINOVA was created to end that chaos.

At its core is a network of **specialised virtual agents** working together. One agent understands your statements, another normalises them, another validates entries, another surfaces insights.
As a team, they deliver **true financial intelligence**.

# Solution

With **generative AI, data science and machine learning**, FINOVA reads the raw data the way a human analyst would, except faster, consistently and without errors.
It interprets, organises, orchestrates and explains your entire financial landscape, turning noise into knowledge and confusion into direction.

FINOVA’s mission is simple:
To give every user, whether individual or enterprise, a **clear, trustworthy and actionable understanding** of their finances.


---

# How to Run & Instructions for Setup

Finova relies on a few cloud services, including Google Gemini AI models and MongoDB Atlas. Before running the app, make sure these services are configured.

To get started:

1. **Create a Google API key** using Google’s AI Studio.
2. **Set up a MongoDB Atlas cluster** and collect your connection string.

Update the environment variables listed in `.env.example`, then create a `.env` file with the same keys inside the `finova_ui` directory. Avoid changing `FINOVA_DB_NAME` unless you know what you're doing.

**`.env.example`**

```ini
GOOGLE_API_KEY="your-google-api-key"
MONGODB_URI="mongodb+srv://finova_user:finova_user_password@m0.ckgei2t.mongodb.net/?appName=M0"
FINOVA_DB_NAME=finova
```

After everything is configured, run `./run.sh` from the project root. If needed, grant it execute permission first. The script launches the Finova application in your browser.

---

## Architecture

The Finova application is a Streamlit-based web app that orchestrates a set of LLM-powered agents to process bank statements end to end: classify, parse, categorize, store, analyze, and chat over the data. Processed transactions are stored in MongoDB Atlas and exposed via an analytics dashboard and a conversational interface.

### Mermaid Diagram

```mermaid
flowchart TD
    %% Client
    U[User Browser] --> S[Streamlit Web App]

    %% Upload
    S -->|Upload Bank Statement| F[Statement File]

    %% Classification
    F --> C[agent2_classifier\nLLM Statement Classifier]
    C -->|Statement Type| P[agent3_parser\nLLM Statement Parser]

    %% Parsing → Canonical Structure
    P -->|Parsed Transactions| CAT[agent6_categorizer\nLLM Transaction Categorizer]

    %% Categorization → Database
    CAT -->|Categorized Transactions| DB[(MongoDB Atlas\ntransactions collection)]

    %% Analytics Dashboard
    S --> D[Analytics Dashboard]
    DB --> D

    %% Chatbot
    S --> CHAT_UI[Chatbot UI]
    CHAT_UI --> A5[agent5_chat\nLLM Chat Agent]
    A5 -->|Query & Context| DB
    DB -->|Relevant Data| A5
    A5 --> CHAT_UI

    %% External LLM Provider
    subgraph LLM_Provider[LLM Provider]
        LLM1[(LLM API)]
    end

    C --> LLM1
    P --> LLM1
    CAT --> LLM1
    A5 --> LLM1

```

### Component Overview

* **Streamlit Web App**

  * Hosts the web server and UI.
  * Handles file uploads, dashboard rendering, and chatbot interface.
  * Orchestrates calls to all LLM-based agents.

* **Bank Statement Upload**

  * User uploads a bank statement file (e.g. PDF/CSV).
  * The raw file is passed into the classification and parsing pipeline.

* **`agent2_classifier` – Statement Type Classifier**

  * Uses an LLM to detect the statement type (bank, card, format variant, etc.).
  * Output: a normalized statement type used to drive parsing logic.

* **`agent3_parser` – Statement Parser**

  * Uses the detected statement type plus an LLM to extract transactions from the raw file.
  * Produces a **canonical transaction structure** (date, description, amount, balance, etc.).

* **`agent6_categorizer` – Transaction Categorizer**

  * Takes each parsed transaction and assigns income/expense categories (e.g. salary, rent, groceries).
  * Uses an LLM for semantic understanding of transaction descriptions and patterns.

* **MongoDB Atlas – `transactions` Collection**

  * All categorized transactions are inserted into the `transactions` collection.
  * Serves as the single source of truth for analytics and chat.

* **Analytics Dashboard**

  * Streamlit dashboards visualize:

    * Income vs expense trends
    * Category-wise breakdowns
    * Statement-level summaries
  * Reads data directly from MongoDB Atlas.

* **Chatbot – `agent5_chat`**

  * Chat interface on top of user statements.
  * Uses an LLM plus data from MongoDB to:

    * Answer questions like *“How much did I spend on groceries last month?”*
    * Explain spending patterns and anomalies.
  * Pulls relevant transactions and aggregates from the `transactions` collection as context.

* **LLM Provider (e.g. Google Gemini)**

  * Shared LLM backend used by all agents (`agent2_classifier`, `agent3_parser`, `agent6_categorizer`, `agent5_chat`).
  * Accessed via API using the configured `GOOGLE_API_KEY`.


# demo
Video URL: 

