from datetime import datetime
import streamlit as st
import openai
import os
import pandas as pd
import re
from urllib.parse import quote
import gspread
from google.oauth2.service_account import Credentials

# ---------- Email Validator ----------
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# ---------- Google Sheets Logger ----------
def log_to_google_sheet(data_row):
    creds = Credentials.from_service_account_file("credentials.json", scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ])
    gc = gspread.authorize(creds)

    # ✅ Your actual Google Sheet URL
    sheet_url = "https://docs.google.com/spreadsheets/d/1wqXlnG2EjExIZ4JhsDyfqouTtcIpY4Xw_0OGJsETeyA/edit"
    sh = gc.open_by_url(sheet_url)
    worksheet = sh.sheet1
    worksheet.append_row(data_row)

# ---------- API Key ----------
if "api_key" not in st.session_state:
    api_key = st.text_input("🔑 Enter your OpenAI API key:", type="password")
    if api_key:
        st.session_state.api_key = api_key
else:
    openai.api_key = st.session_state.api_key

    # ---------- Lead Form ----------
    with st.form("lead_form"):
        st.header("🎯 Single Lead Input")
        name = st.text_input("Lead Name")
        job_title = st.text_input("Job Title")
        company = st.text_input("Company")
        recent_activity = st.text_area("Recent Activity", "")
        sector = st.selectbox("Industry Sector", [
            "Mining", "Agriculture", "Petrochemical", "Aerospace", "Defence",
            "Food & Beverage", "Medical & Science", "Construction",
            "Transport", "Heavy Engineering", "Other"
        ])

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
        - Stainless steel and polymer fabrication
        - Sustainable, corrosion-resistant, and lightweight solutions

        End with:
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

            # Save to CSV
            log_data = {
                "Timestamp": datetime.now().isoformat(),
                "Name": name,
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

            # ✅ Log to Google Sheet (flattened email)
            log_to_google_sheet([
                datetime.now().isoformat(),
                name,
                job_title,
                company,
                sector,
                recent_activity,
                email_text.replace('\n', ' ').replace('\r', ' ')  # flatten
            ])

        except Exception as e:
            st.error(f"An error occurred: {e}")

   
