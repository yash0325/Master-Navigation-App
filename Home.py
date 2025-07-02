import streamlit as st

st.set_page_config(page_title="Agile AI Toolkit", layout="centered")
st.title("🧠 Agile AI Toolkit Launcher")

st.markdown("### What would you like to do today?")

st.markdown("""
### 🚀 Select a Tool from the Sidebar
Use the menu on the **left** to access one of the tools:

- 📘 **Refine User Story** – Rewrite Jira stories using AI with INVEST criteria.
- 📏 **Effort Estimator** – Suggest story point ranges and confidence scores.
- 💼 **Business Value Assessor** – Assess business value and suggest priority with AI.
- 🔬 **Granularity Checker** – Check if a user story is granular enough for a sprint and get splitting suggestions.


No need to launch — just click from the sidebar!
""")
