import datetime
import streamlit as st
import openai
import os
import pandas as pd
from urllib.parse import quote

st.set_page_config(page_title="AI Outreach Generator", page_icon="📧")

st.title("📧 AI-Powered Sales Outreach Generator")
st.write("Generate personalized outreach emails based on a lead's background.")

# Get API key
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
        prompt = f"""You are a professional B2B outreach assistant. Write a concise, formal, and respectful email to the following lead:

        Name: {name}
        Job Title: {job_title}
        Company: {company}
        Recent Activity: {recent_activity or 'N/A'}
        Personality Summary: {personality or 'N/A'}

        The email should:
        - Begin with a formal greeting
        - Mention the recent activity to show relevance
        - Introduce the sender’s company and value proposition
        - Suggest a professional call to action (e.g., a meeting)
        - Use a formal tone
        """

        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional B2B email assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            email_text = response.choices[0].message.content.strip()
            st.subheader("📩 Generated Outreach Email")
            st.code(email_text, language="markdown")

            # Log to CSV automatically
            log_data = {
                "Timestamp": datetime.now().isoformat(),
                "Name": name,
                "Job Title": job_title,
                "Company": company,
                "Recent Activity": recent_activity,
                "Personality Summary": personality,
                "Email": email_text
            }

            log_file = "lead_log.csv"
            if os.path.exists(log_file):
                df = pd.read_csv(log_file)
                df = pd.concat([df, pd.DataFrame([log_data])], ignore_index=True)
            else:
                df = pd.DataFrame([log_data])
            df.to_csv(log_file, index=False)

            # Send via email
            st.markdown("### ✉️ Send This Email")
            recipient = st.text_input("Recipient Email")
            if recipient:
                mail_subject = quote(email_text.split('\n')[0].replace("Subject: ", ""))
                mail_body = quote(email_text.replace("\n", "%0A"))
                mailto_link = f"mailto:{recipient}?subject={mail_subject}&body={mail_body}"
                st.markdown(f"[Click here to send](\{mailto_link})", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"An error occurred: {e}")
