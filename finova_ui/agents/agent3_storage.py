# agents/agent3_storage.py

from google.adk.agents import LlmAgent, SequentialAgent
from agents import get_model
from Tools.mongo_tools import insert_transactions, save_uploaded_info

model = get_model()

storage_agent = LlmAgent(
    name="storage_agent",
    model=model,
    description="Agent 3.3: Stores parsed transactions into MongoDB.",
    tools=[insert_transactions],
)

