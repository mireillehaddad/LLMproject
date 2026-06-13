build a simple Streamlit web interface for your chatbot.

This gives you a real app, not only command line.

1. Install Streamlit
uv pip install streamlit --link-mode=copy
2. Create
app.py

The app will:

User question → retrieve chunks → Gemini answer → show sources
3. Run it
streamlit run app.py

Then your browser opens with the chatbot UI.

After that, you can document:

Interface: Streamlit web app

which improves your project evaluation score.


streamlit run app_gemini.py