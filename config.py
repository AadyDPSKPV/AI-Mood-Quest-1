"""Central configuration for AI Mood Quest. Never put real API keys in this file."""
import os
import streamlit as st


def get_secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, "").strip()


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
HF_TOKEN = get_secret("HF_TOKEN")
GEMINI_MODEL = "gemini-3.8-flash"
HF_MODEL = "j-hartmann/emotion-english-distilroberta-base"
APP_NAME = "AI Mood Quest"
