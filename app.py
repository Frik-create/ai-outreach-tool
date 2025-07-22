import streamlit as st
from io import BytesIO
import zipfile
import openai
import datetime
import gspread
import pdfkit
import pytz
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIG ---
st.set_page_config(page_title="QICP B2B Outreach Tool", page_icon="📧", layout="wide")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1wqxXlnG2EjExIZ4JhsDyfqquTtcIpY4Xw_0OGJsETeyA/edit#gid=0"
WORKSHEET_NAME = "Sheet1"
PDF_OPTIONS = {"encoding": "UTF-8"}
COMPANY_PROFILE_URL = "https://outreach.qicp.co.za/QICP_Company_Summary.pdf"
LOCAL_PDF_PATH = "QICP_Company_Summary.pdf"

# --- SIDEBAR ---
st.sidebar.header("🔐 API Key Required")
api_key = st.sidebar.text_input("Enter your OpenAI API key:", type="password")

if st.sidebar.button("📄 View Company Profile"):
    st.markdown("### QICP Company Profile")
    st.markdown(f"[Click to view full PDF]({COMPANY_PROFILE_URL})", unsafe_allow_html=True)
    st.components.v1.iframe(COMPANY_PROFILE_URL, height=600)

# --- MAIN APP ---
st.title("📨 QICP B2B Outreach Tool")

industry = st.selectbox("Select Industry", ["Mining", "Manufacturing", "Energy", "Logistics", "Construction"])
contact = st.text_input("Contact Info (email / phone)", placeholder="you@yourcompany.com")

if st.button("🎯 Generate Email"):
    if not api_key or not contact:
        st.error("Please provide both your API key and contact info.")
    else:
        openai.api_key = api_key
        prompt = f"Write a personalized B2B sales outreach email to a {industry.lower()} company, from QICP. Include value proposition, short intro, and call to action. Contact: {contact}."

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        email_text = response['choices'][0]['message']['content']
        email_text += f"\n\n📄 [View our full company profile]({COMPANY_PROFILE_URL})"

        # Display
        st.subheader("📧 Generated Email")
        with st.expander("📄 View Email Text"):
            st.code(email_text)

        # Convert to PDF
        html_content = f"<html><body><pre>{email_text}</pre></body></html>"
        pdf_bytes = pdfkit.from_string(html_content, False, options=PDF_OPTIONS)
        st.download_button("📥 Download Email as PDF", data=pdf_bytes, file_name="qicp_outreach_email.pdf")

        # Google Sheets Logging
        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
            client = gspread.authorize(creds)
            sheet = client.open_by_url(SHEET_URL).worksheet(WORKSHEET_NAME)
            timestamp = datetime.datetime.now(pytz.timezone("Africa/Johannesburg")).strftime("%Y-%m-%d %H:%M")
            sheet.append_row([timestamp, contact, industry, email_text, "initial"])
            st.success("✅ Email logged to Google Sheet.")
        except Exception as e:
            st.warning(f"⚠️ Logging to Google Sheets failed: {e}")

# --- BULK MODE ---
uploaded_file = st.file_uploader("📤 Upload CSV with Leads", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    pdf_zip = BytesIO()
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
    sheet = gspread.authorize(creds).open_by_url(SHEET_URL).worksheet(WORKSHEET_NAME)

    with zipfile.ZipFile(pdf_zip, "w") as zipf:
        for index, row in df.iterrows():
            contact_info = row.get("contact", "")
            industry_row = row.get("industry", industry)

            prompt = f"Write a B2B sales outreach email to a {industry_row.lower()} company from QICP. Contact: {contact_info}."
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            email_text = response['choices'][0]['message']['content']
            email_text += f"\n\n📄 [View our full company profile]({COMPANY_PROFILE_URL})"

            html = f"<html><body><pre>{email_text}</pre></body></html>"
            pdf = pdfkit.from_string(html, False, options=PDF_OPTIONS)
            filename = f"email_{index+1}_{contact_info.replace('@','_at_').replace('.', '_')}.pdf"
            zipf.writestr(filename, pdf)

            try:
                timestamp = datetime.datetime.now(pytz.timezone("Africa/Johannesburg")).strftime("%Y-%m-%d %H:%M")
                sheet.append_row([timestamp, contact_info, industry_row, email_text, "bulk"])
            except:
                pass

        # Attach profile
        try:
            with open(LOCAL_PDF_PATH, "rb") as f:
                zipf.writestr("QICP_Company_Summary.pdf", f.read())
        except:
            st.warning("⚠️ Could not attach company profile to ZIP.")

    pdf_zip.seek(0)
    st.download_button("📦 Download All Emails as ZIP", data=pdf_zip, file_name="qicp_bulk_outreach.zip")
