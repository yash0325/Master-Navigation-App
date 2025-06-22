import streamlit as st
from jira import JIRA
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

st.set_page_config(page_title="AI Effort Estimator", layout="wide")
st.title("📏 AI-Based Effort Estimator for Jira Stories")

# ---- Prompt Template ----
ESTIMATOR_PROMPT = """
You are an agile estimation agent. Given a new Jira user story and several similar stories (with known story points and outcomes), suggest a draft story point estimate range (e.g., 5–8 points) and a confidence score from 0 to 1, justifying your answer.

NEW STORY:
Summary: {summary}
Description: {description}
Component: {component}

SIMILAR STORIES:
{examples}

Output (use this format):
---
**Estimated Story Point Range:** <range>
**Confidence Score:** <score between 0–1>
**Reasoning:** <short justification>
---
"""

# ---- Utility Functions ----
def clear_connection_state():
    for k in [
        "jira_host", "jira_email", "jira_api_token", "jira_project_key",
        "openai_api_key", "connected"
    ]:
        if k in st.session_state:
            del st.session_state[k]

def get_llm(api_key):
    return ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)

def parse_estimator_output(output):
    # Robustly parse the LLM output for fields.
    import re
    range_ = ""
    confidence = ""
    reasoning = ""
    range_match = re.search(r"\*\*Estimated Story Point Range:\*\*\s*([^\n]*)", output)
    conf_match = re.search(r"\*\*Confidence Score:\*\*\s*([^\n]*)", output)
    reasoning_match = re.search(r"\*\*Reasoning:\*\*\s*([\s\S]*)", output)
    if range_match:
        range_ = range_match.group(1).strip()
    if conf_match:
        confidence = conf_match.group(1).strip()
    if reasoning_match:
        reasoning = reasoning_match.group(1).strip().split('\n---')[0].strip()
    return range_, confidence, reasoning

def get_similar_stories(jira, project_key, component, current_issue_key=None, n=5):
    # Pull most recent issues with story points, same component preferred
    jql = (
        f'project={project_key} AND "Story Points" is not EMPTY '
        f'AND component="{component}" ORDER BY updated DESC'
    )
    try:
        issues = jira.search_issues(jql, maxResults=15)
    except Exception as e:
        issues = []
    examples = []
    for issue in issues:
        if issue.key == current_issue_key:
            continue
        example = f"- Summary: {issue.fields.summary}\n  Description: {getattr(issue.fields, 'description', '') or '[No Description]'}\n  Component: {component}\n  Story Points: {getattr(issue.fields, 'customfield_10016', 'N/A')}"
        examples.append(example)
        if len(examples) >= n:
            break
    return "\n".join(examples) if examples else "[No similar stories found]"

# ---- DISCONNECT BUTTON ----
if st.session_state.get("connected", False):
    colc, cold = st.columns([10, 1])
    with cold:
        if st.button("Disconnect"):
            clear_connection_state()
            st.rerun()

# ---- Connection Form ----
if not st.session_state.get("connected", False):
    st.subheader("Connect to Jira & OpenAI")
    with st.form("connection_form"):
        jira_host = st.text_input("Jira Host URL (e.g. https://yourdomain.atlassian.net)", value=st.session_state.get("jira_host", ""))
        jira_email = st.text_input("Jira Email", value=st.session_state.get("jira_email", ""))
        jira_api_token = st.text_input("Jira API Token", type="password", value=st.session_state.get("jira_api_token", ""))
        jira_project_key = st.text_input("Jira Project Key", value=st.session_state.get("jira_project_key", ""))
        openai_api_key = st.text_input("OpenAI API Key", type="password", value=st.session_state.get("openai_api_key", ""))
        submitted = st.form_submit_button("Connect")

    if submitted:
        if not (jira_host and jira_email and jira_api_token and jira_project_key and openai_api_key):
            st.warning("Please fill in all fields to connect.")
        else:
            st.session_state["jira_host"] = jira_host.strip()
            st.session_state["jira_email"] = jira_email.strip()
            st.session_state["jira_api_token"] = jira_api_token.strip()
            st.session_state["jira_project_key"] = jira_project_key.strip()
            st.session_state["openai_api_key"] = openai_api_key.strip()
            # Test Jira connection
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

# ---- Main Effort Estimator Logic ----
if st.session_state.get("connected", False):
    jira_host = st.session_state["jira_host"]
    jira_email = st.session_state["jira_email"]
    jira_api_token = st.session_state["jira_api_token"]
    jira_project_key = st.session_state["jira_project_key"]
    openai_api_key = st.session_state["openai_api_key"]

    try:
        jira = JIRA(server=jira_host, basic_auth=(jira_email, jira_api_token))
        # Find stories that do not have "Story Points" assigned
        jql = f'project={jira_project_key} AND issuetype=Story AND "Story Points" is EMPTY ORDER BY created ASC'
        issues = jira.search_issues(jql, maxResults=20)
    except Exception as e:
        st.error(f"Failed to load issues: {e}")
        issues = []

    if issues:
        issue_titles = [f"{i.key}: {i.fields.summary}" for i in issues]
        selected = st.selectbox("Select a user story for estimation:", issue_titles)
        selected_issue = issues[issue_titles.index(selected)]

        summary = selected_issue.fields.summary or ""
        description = getattr(selected_issue.fields, "description", "") or ""
        component = (selected_issue.fields.components[0].name if selected_issue.fields.components else "General")

        st.subheader("📝 User Story Details")
        st.markdown(f"**Summary:** {summary}")
        st.markdown(f"**Description:** {description}")
        st.markdown(f"**Component:** {component}")

        with st.form("estimate_form", clear_on_submit=True):
            st.subheader("🤖 AI Effort Estimation")
            if st.form_submit_button("Estimate Story Points"):
                with st.spinner("Fetching similar stories and estimating..."):
                    similar_examples = get_similar_stories(jira, jira_project_key, component, current_issue_key=selected_issue.key, n=5)
                    chain = LLMChain(
                        llm=get_llm(openai_api_key),
                        prompt=PromptTemplate.from_template(ESTIMATOR_PROMPT)
                    )
                    try:
                        result = chain.run({
                            "summary": summary,
                            "description": description,
                            "component": component,
                            "examples": similar_examples
                        })
                        est_range, conf, reasoning = parse_estimator_output(result)
                        st.session_state["last_est_range"] = est_range
                        st.session_state["last_confidence"] = conf
                        st.session_state["last_reasoning"] = reasoning
                    except Exception as e:
                        st.error(f"OpenAI Error: {e}")

            # Show results if available
            if st.session_state.get("last_est_range"):
                st.markdown(f"**Suggested Story Point Range:** `{st.session_state['last_est_range']}`")
                st.markdown(f"**Confidence Score:** `{st.session_state['last_confidence']}`")
                st.markdown(f"**Reasoning:** {st.session_state['last_reasoning']}")
                final_estimate = st.text_input(
                    "Edit Final Estimate (enter a single number, required):",
                    value=st.session_state['last_est_range'].split('-')[0].strip() if '-' in st.session_state['last_est_range'] else st.session_state['last_est_range']
                )
                if st.form_submit_button("Save to Jira"):
                    try:
                        # Find the "Story Points" customfield key in your Jira instance. Often it's customfield_10016.
                        story_points_field = "customfield_10016"
                        selected_issue.update(fields={story_points_field: float(final_estimate)})
                        st.success(f"Story points updated to {final_estimate} for {selected_issue.key}!")
                        # Clear state for next use
                        for k in ["last_est_range", "last_confidence", "last_reasoning"]:
                            if k in st.session_state:
                                del st.session_state[k]
                    except Exception as e:
                        st.error(f"Failed to update Jira: {e}")

    else:
        st.warning("No unestimated user stories found in the selected project.")
