import streamlit as st
from jira import JIRA
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

st.set_page_config(page_title="Jira User Story Granularity Checker", layout="wide")
st.title("🧩 Jira User Story Granularity Checker AI")

# ---- AGENTIC PROMPT ----
GRANULARITY_AGENT_PROMPT = """
You are an Agile requirements analyst and user story coach.

Your job is to:
- Decide if the following user story is granular (i.e., focused, specific, and achievable within a single sprint by one team).
- If granular, reply only with "Yes" and a brief rationale.
- If not granular, reply with "No", then explain why not, and suggest how to split or rewrite the story into smaller, granular stories if possible.

User Story:
{user_story}
"""

def clear_connection_state():
    for k in [
        "jira_host", "jira_email", "jira_api_token", "jira_project_key",
        "connected",
        "last_checked_issue_key", "last_granularity_result"
    ]:
        if k in st.session_state:
            del st.session_state[k]

# --- Disconnect Button (top right if connected) ---
if st.session_state.get("connected", False):
    colc, cold = st.columns([10, 1])
    with cold:
        if st.button("Disconnect"):
            clear_connection_state()
            st.rerun()

# ---- Step 1: Jira Connection Form ----
if not st.session_state.get("connected", False):
    st.subheader("Connect to Jira")
    with st.form("connection_form"):
        jira_host = st.text_input("Jira Host URL (e.g. https://yourdomain.atlassian.net)", value=st.session_state.get("jira_host", ""))
        jira_email = st.text_input("Jira Email", value=st.session_state.get("jira_email", ""))
        jira_api_token = st.text_input("Jira API Token", type="password", value=st.session_state.get("jira_api_token", ""))
        jira_project_key = st.text_input("Jira Project Key", value=st.session_state.get("jira_project_key", ""))
        submitted = st.form_submit_button("Connect")

    if submitted:
        if not (jira_host and jira_email and jira_api_token and jira_project_key):
            st.warning("Please fill in all fields to connect.")
        else:
            st.session_state["jira_host"] = jira_host.strip()
            st.session_state["jira_email"] = jira_email.strip()
            st.session_state["jira_api_token"] = jira_api_token.strip()
            st.session_state["jira_project_key"] = jira_project_key.strip()
            try:
                jira = JIRA(server=jira_host, basic_auth=(jira_email, jira_api_token))
                st.session_state["connected"] = True
                st.success(f"Connected as {jira_email} to JIRA: {jira_project_key}")
            except Exception as e:
                st.session_state["connected"] = False
                st.error(f"Failed to connect to Jira: {e}")
else:
    st.success(
        f"Connected as {st.session_state['jira_email']} to JIRA: {st.session_state['jira_project_key']}",
        icon="🔗"
    )

def get_llm():
    return ChatOpenAI(model="gpt-4o", temperature=0, api_key=st.secrets["OPENAI_API_KEY"])

def run_granularity_agent(user_story):
    prompt = PromptTemplate.from_template(GRANULARITY_AGENT_PROMPT)
    llm = get_llm()
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run({"user_story": user_story})

# -- Main App (after Jira connection) --
if st.session_state.get("connected", False):
    jira_host = st.session_state["jira_host"]
    jira_email = st.session_state["jira_email"]
    jira_api_token = st.session_state["jira_api_token"]
    jira_project_key = st.session_state["jira_project_key"]

    try:
        jira = JIRA(server=jira_host, basic_auth=(jira_email, jira_api_token))
        jql = f'project={jira_project_key} ORDER BY created ASC'
        issues = jira.search_issues(jql, maxResults=20)
    except Exception as e:
        st.error(f"Failed to load issues: {e}")
        issues = []

    if issues:
        st.subheader("Select a User Story")
        issue_titles = []
        filtered_issues = []
        for i in issues:
            label = f"{i.key}: {i.fields.summary}"
            issue_titles.append(label)
            filtered_issues.append(i)

        selected = st.selectbox("Choose a user story for granularity check:", issue_titles)
        selected_issue = filtered_issues[issue_titles.index(selected)]
        summary = selected_issue.fields.summary
        description = selected_issue.fields.description or ""
        user_story_text = description.strip()   # <---- ONLY DESCRIPTION

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📝 Original Story")
            st.markdown(f"**Summary:** {summary}")
            st.markdown(f"**Description:** {description}")

        with col2:
            st.subheader("🔍 Granularity Check")
            if st.button("Check Granularity", key="granularity_btn"):
                with st.spinner("Analyzing granularity with AI..."):
                    result = run_granularity_agent(user_story_text)
                st.session_state["last_checked_issue_key"] = selected_issue.key
                st.session_state["last_granularity_result"] = result

            # Show the result if exists and matches current issue
            if (
                st.session_state.get("last_granularity_result")
                and st.session_state.get("last_checked_issue_key") == selected_issue.key
            ):
                result = st.session_state["last_granularity_result"]
                if result.lower().startswith("yes"):
                    st.success(result)
                else:
                    st.error(result)

    else:
        st.warning("No issues found in the selected project.")

st.markdown("---")
st.caption("Built with Streamlit · Powered by GPT-4o · [YourOrg]")
