import streamlit as st
import requests
import time
import json

API_URL = st.secrets["API_URL"]
BEARER_TOKEN = st.secrets["BEARER_TOKEN"]

st.set_page_config(page_title="BioResearch Council Chat", layout="centered")
st.title("🧬 BioResearch Council — Chat Interface")
st.write("Ask a biological research question. The 11-agent council will respond.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter your research topic..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("The council is deliberating... (this may take a few minutes)"):
            headers = {
                "Authorization": f"Bearer {BEARER_TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {"inputs": {"topic": prompt}}
            
            kickoff_resp = requests.post(f"{API_URL}/kickoff", headers=headers, json=payload)
            if kickoff_resp.status_code != 200:
                st.error(f"Error starting council: {kickoff_resp.text}")
                st.stop()
            
            kickoff_id = kickoff_resp.json().get("kickoff_id")
            if not kickoff_id:
                st.error("No kickoff_id returned.")
                st.stop()

            status_url = f"{API_URL}/status/{kickoff_id}"
            max_attempts = 120
            for attempt in range(max_attempts):
                time.sleep(5)
                status_resp = requests.get(status_url, headers=headers)
                if status_resp.status_code != 200:
                    st.error(f"Error checking status: {status_resp.text}")
                    st.stop()
                status_data = status_resp.json()
                state = status_data.get("status")
                if state == "completed":
                    result = status_data.get("result", "No result returned.")
                    result_str = json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
                    st.markdown(result_str)
                    st.session_state.messages.append({"role": "assistant", "content": result_str})
                    break
                elif state == "error":
                    st.error(f"Council error: {status_data.get('error', 'Unknown error')}")
                    st.stop()
            else:
                st.error("Timeout waiting for council response.")
