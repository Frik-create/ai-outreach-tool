from datetime import datetime
import streamlit as st
import openai
import os
import pandas as pd
import re
from urllib.parse import quote

st.set_page_config(page_title="QICP AI Outreach Generator", page_icon="📧")
st.title("📧 AI-Powered Sales Outreach Generator")
st.write("Craft tailored emails that highlight QICP’s sustainable engineering plastic solutions.")

# Email validator
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# API Key setup
if "api_key" not in st.session_state:
    api_key = st.text_input("🔑 Enter your OpenAI API key:", type="password")
    if api_key:
        st.session_state.api_key = api_key
else:
    openai.api_key = st.session_state.api_key

    with st.form("lead_form"):
        st.header("🎯 Lead Information")
        name = st.text_input("Lead Name")
        job_title = st.text_input("Job Title")
        company = st.text_input("Company")
        recent_activity = st.text_area("Recent Activity (e.g. LinkedIn post, company announcement)", "")
        sector = st.selectbox("Industry Sector", [
            "Mining", "Agriculture", "Petrochemical", "Aerospace", "Defence", 
            "Food & Beverage", "Medical & Science", "Construction", 
            "Transport", "Heavy Engineering", "Other"
        ])

        st.header("✍️ Your Info")
        your_name = st.text_input("Your Name", value="Frederick Kahts")
        your_position = st.text_input("Your Position", value="Director")
        your_company = st.text_input("Your Company", value="QUALITY INDUSTRIAL AND COMMERCIAL PRODUCTS PTY Ltd")
        contact_info = st.text_input("Contact Info", value="frik@qicp.co.za / +27 73 163 1077")

        submitted = st.form_submit_button("Generate Email")

    if submitted:
        prompt = f"""
        You are a professional sales outreach assistant writing on behalf of QUALITY INDUSTRIAL AND COMMERCIAL PRODUCTS PTY Ltd (QICP).
        Compose a concise and professional B2B outreach email tailored to the following lead:

        Lead Info:
        - Name: {name}
        - Job Title: {job_title}
        - Company: {company}
        - Sector: {sector}
        - Recent Activity: {recent_activity or 'N/A'}

        QICP provides:
        - Semi-finished engineering plastic stock (rods, sheets, tubes)
        - CNC machined components (bushes, gears, enclosures, seals)
        - Injection molded parts
        - Thermoplastic piping and fittings
        - Stainless steel and polymer fabrication for industries like {sector}
        - Sustainable, corrosion-resistant, lightweight solutions

        Use a formal tone, mention our commitment to sustainability and tailored solutions. Conclude with this signature:

        Warm regards,  
        {your_name}  
        {your_position}, {your_company}  
        {contact_info}
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
            st.markdown(email_text)

            # Log email
            log_data = {
                "Timestamp": datetime.now().isoformat(),
                "Lead Name": name,
                "Job Title": job_title,
                "Company": company,
                "Sector": sector,
                "Recent Activity": recent_activity,
                "Email": email_text
            }

            log_file = "lead_log.csv"
            if os.path.exists(log_file):
                df = pd.read_csv(log_file)
                df = pd.concat([df, pd.DataFrame([log_data])], ignore_index=True)
            else:
                df = pd.DataFrame([log_data])
            df.to_csv(log_file, index=False)

            # Email delivery
            st.subheader("📤 Send This Email")
            recipient = st.text_input("Recipient Email")
            if recipient:
                if is_valid_email(recipient):
                    subject_guess = "Exploring Engineering Plastic Solutions from QICP"
                    subject = st.text_input("Edit Subject Line", value=subject_guess)
                    body = quote(email_text.replace("\n", "%0A"))
                    mailto_link = f"mailto:{recipient}?subject={quote(subject)}&body={body}"
                    st.markdown(f"[📬 Click here to send the email]({mailto_link})", unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Invalid email format. Please check the recipient email.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

