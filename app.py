
import streamlit as st
import openai
import os

st.set_page_config(page_title="AI Outreach Generator", page_icon="🤖")

st.title("🤖 AI-Powered Sales Outreach Generator")
st.write("Generate personalized outreach emails based on a lead's background.")

# Get API key securely (enter it once, store via Streamlit secrets)
if "api_key" not in st.session_state:
    api_key = st.text_input("🔑 Enter your OpenAI API key:", type="password")
    if api_key:
        st.session_state.api_key = api_key
else:
    openai.api_key = st.session_state.api_key

    with st.form("lead_form"):
        name = st.text_input("Lead Name")
        job_title = st.text_input("Job Title")
        company = st.text_input("Company")
        recent_activity = st.text_area("Recent Activity (e.g. LinkedIn post, article)", "")
        personality = st.text_area("Personality Summary (optional)", "")
        submitted = st.form_submit_button("Generate Email")

    if submitted:
        prompt = f"""
        You are a helpful B2B sales assistant. Write a personalized cold email to the following lead:

        Name: {name}
        Job Title: {job_title}
        Company: {company}
        Recent Activity: {recent_activity or 'N/A'}
        Personality Summary: {personality or 'N/A'}

        The email should:
        - Open with a custom hook
        - Mention your company offers AI-powered plastics engineering solutions
        - Relate benefits to their role/company
        - End with a friendly call-to-action (e.g. intro call)
        Tone: Friendly, professional, to the point.
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert sales email writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            email_text = response.choices[0].message['content'].strip()
            st.subheader("📩 Generated Outreach Email")
            st.code(email_text, language="markdown")
        except Exception as e:
            st.error(f"⚠️ Error: {e}")
