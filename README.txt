AI MOOD QUEST — SETUP

1. Extract this ZIP to a new folder.
2. Open the .streamlit folder.
3. Create a file named secrets.toml (make sure it is NOT secrets.toml.txt).
4. Put your NEW keys in secrets.toml using these exact names:
   GEMINI_API_KEY = "your-new-gemini-key"
   HF_TOKEN = "your-new-hugging-face-token"
   Do not put real keys in app.py or config.py.
5. Open Command Prompt in the folder containing app.py and run:
   python -m pip install -r requirements.txt
   python -m streamlit run app.py
6. In the app sidebar, open API Diagnostics and test each provider.

If Credential detected is No, check that .streamlit/secrets.toml is inside the same project folder as app.py and restart Streamlit completely.
If credentials are detected but a request fails, use the displayed error to investigate permissions, quota, provider/model availability, or network issues.

SECURITY: If API keys were shared in a chat or screenshot, revoke them and create replacements. Never share real keys or commit secrets.toml to a public repository.
