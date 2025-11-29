# agents/agent2_classifier.py

from google.adk.agents import LlmAgent
from agents import get_model

model = get_model()

# No instructions here — instructions will come dynamically in main.py
bank_classifier_agent = LlmAgent(
    name="bank_classifier_agent",
    model=model,
    description="Agent 2: Classifies bank name and statement type from email metadata.",
    tools=[],
)
