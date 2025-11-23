# agents/agent3_storage.py

from google.adk.agents import LlmAgent
from agents import get_model

model = get_model()

storage_agent = LlmAgent(
    name="storage_agent",
    model=model,
    description="Agent 3.3: Stores parsed transactions into MongoDB.",
    tools=[],
)
