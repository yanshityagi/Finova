# agents/__init__.py
from google.adk.models.google_llm import Gemini

def get_model():
    """
    Returns a Gemini model instance for use with ADK LlmAgent.
    ADK will pick up GOOGLE_API_KEY / GOOGLE_GENAI_USE_VERTEXAI from env.
    """
    # You can switch model_id to "gemini-1.5-flash" if your course uses that.
    return Gemini(model_id="gemini-2.0-flash")
