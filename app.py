import streamlit as st
import requests
import time
import json

# Load secrets from Streamlit Cloud
API_URL = st.secrets["API_URL"]
BEARER_TOKEN = st.secrets["BEARER_TOKEN"]

st.set_page_config(page_title="BioResearch Council Chat", layout="centered")
st.title("🧬 BioResearch Council — Chat Interface")
st.write("Ask a biological research question. The 11-agent council will respond.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Enter your research topic..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call CrewAI API
    with st.chat_message("assistant"):
        with st.spinner("The council is deliberating... (this may take a few minutes)"):
            headers = {
                "Authorization": f"Bearer {BEARER_TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {"inputs": {"topic": prompt}}
            
            # Start kickoff
            kickoff_resp = requests.post(f"{API_URL}/kickoff", headers=headers, json=payload)
            if kickoff_resp.status_code != 200:
                st.error(f"Error starting council: {kickoff_resp.text}")
                st.stop()
            
            kickoff_id = kickoff_resp.json().get("kickoff_id")
            if not kickoff_id:
                st.error("No kickoff_id returned.")
                st.stop()

            # Poll for status
            status_url = f"{API_URL}/status/{kickoff_id}"
            max_attempts = 120  # 10 minutes max (5s interval)
            for attempt in range(max_attempts):
                time.sleep(2)
                status_resp = requests.get(status_url, headers=headers)
                if status_resp.status_code != 200:
                    st.error(f"Error checking status: {status_resp.text}")
                    st.stop()
                status_data = status_resp.json()
                state = status_data.get("status")
                if state == "completed":
                    result = status_data.get("result", "No result returned.")
                    if isinstance(result, dict):
                        result_str = json.dumps(result, indent=2)
                    else:
                        result_str = str(result)
                    st.markdown(result_str)
                    st.session_state.messages.append({"role": "assistant", "content": result_str})
                    break
                elif state == "error":
                    st.error(f"Council error: {status_data.get('error', 'Unknown error')}")
                    st.stop()
                # else still running, continue polling
            else:
                st.error("Timeout waiting for council response.")
