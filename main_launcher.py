import streamlit as st
import subprocess
import os
import sys

st.set_page_config(page_title="Agile AI Toolkit", layout="centered")
st.title("🧠 Agile AI Toolkit Launcher")

st.markdown("### What would you like to do today?")

# Dropdown for selecting task
task = st.selectbox(
    "Choose your action:",
    ["Select an option", "📝 Refine User Story", "📏 Estimate Effort"]
)

# Optional: Add a description or info box
if task == "📝 Refine User Story":
    st.info("Launches the User Story Refiner AI tool connected to your Jira board.")
elif task == "📏 Estimate Effort":
    st.info("Launches the Effort Estimation Assistant for your Jira stories.")

# Launch respective app based on selection
if st.button("🚀 Launch Selected App"):
    if task == "📝 Refine User Story":
        subprocess.Popen(["streamlit", "run", "Dynamic_UI3.py"])
        st.success("Launching Refiner App...")
    elif task == "📏 Estimate Effort":
        subprocess.Popen(["streamlit", "run", "Effort_estimator.py"])
        st.success("Launching Effort Estimator App...")
    else:
        st.warning("Please select an action to launch an app.")
