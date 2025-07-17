
import streamlit as st
import openai
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from fpdf import FPDF
from datetime import datetime
import io
import zipfile
import requests
import msal
import re

st.set_page_config(page_title="QICP B2B Outreach Tool", layout="wide")
st.markdown("""
    <style>
    .stApp { font-family: 'Segoe UI', sans-serif; background-color: #f8f9fa; }
    .css-18e3th9 { background-color: #001f3f !important; }
    .css-1d391kg, .st-bb { color: #d4af37 !important; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.header("API Key Required")
api_key = st.sidebar.text_input("Enter your OpenAI API key:", type="password")
if not api_key:
    st.warning("Please enter your API key to begin.")
    st.stop()

SHEET_URL = "https://docs.google.com/spreadsheets/d/1wqXlnG2EjExIZ4JhsDyfqouTtcIpY4Xw_0OGsJETeyA/edit#gid=0"
creds = Credentials.from_service_account_file("credentials.json", scopes=["https://www.googleapis.com/auth/spreadsheets"])
gclient = gspread.authorize(creds)
worksheet = gclient.open_by_url(SHEET_URL).sheet1

client_ai = openai.OpenAI(api_key=api_key)

def sanitize_text(text):
    text = text.replace("â€™", "'").replace("â€˜", "'").replace("â€œ", '"').replace("â€", '"').replace("â€“", "-")
    return re.sub(r'[^ -Ã¿]', '', text)

st.title("ðŸ“§ QICP B2B Outreach Tool")
industry = st.selectbox("Select Industry", ["Mining", "Construction", "Agriculture", "Healthcare"])
contact = st.text_input("Contact Info (email / phone)")

if st.button("ðŸ“¤ Generate Email"):
    try:
        prompt = f"Write a concise B2B outreach email to a {industry.lower()} client."
        response = client_ai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        email_text = response.choices[0].message.content.strip()
        clean = sanitize_text(email_text)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in clean.split("\n"):
            pdf.multi_cell(0, 10, line)
        pdf_bytes = pdf.output(dest="S").encode("latin-1", "replace")
        pdf_output = io.BytesIO(pdf_bytes)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.append_row([timestamp, industry, contact, email_text])
        st.success("âœ… Email logged to Google Sheet.")

        st.subheader("ðŸ“¨ Generated Email")
        with st.expander("ðŸ“„ View Email Text"):
            st.code(email_text)
        st.download_button("ðŸ“¥ Download Email as PDF", data=pdf_output, file_name="outreach_email.pdf")

        st.subheader("ðŸ“¤ Send Email via Outlook")
        if "outlook" in st.secrets:
            if st.button("Send via Outlook"):
                outlook = st.secrets["outlook"]
                authority = f"https://login.microsoftonline.com/{outlook['tenant_id']}"
                app = msal.ConfidentialClientApplication(
                    client_id=outlook["client_id"],
                    client_credential=outlook["client_secret"],
                    authority=authority
                )
                token_result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

                if "access_token" in token_result:
                    email_payload = {
                        "message": {
                            "subject": "QICP B2B Outreach",
                            "body": {"contentType": "Text", "content": email_text},
                            "toRecipients": [{"emailAddress": {"address": contact}}]
                        },
                        "saveToSentItems": "true"
                    }
                    graph_url = f"https://graph.microsoft.com/v1.0/users/{outlook['sender_email']}/sendMail"
                    response = requests.post(
                        graph_url,
                        headers={
                            "Authorization": f"Bearer {token_result['access_token']}",
                            "Content-Type": "application/json"
                        },
                        json=email_payload
                    )
                    if response.status_code == 202:
                        st.success("âœ… Email sent via Outlook!")
                    else:
                        st.error(f"âŒ Send failed: {response.status_code}")
                        st.text(response.text)
                else:
                    st.error("âŒ Microsoft authentication failed.")
        else:
            st.info("â„¹ï¸ Outlook integration not configured in secrets.toml.")

        st.subheader("ðŸ” Generate Follow-Up Email")
        if st.button("Generate Follow-Up"):
            follow_prompt = f"Write a polite follow-up to this email:\n\n{email_text}"
            follow_response = client_ai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": follow_prompt}]
            )
            follow_email = follow_response.choices[0].message.content.strip()
            worksheet.append_row([timestamp, industry, contact, follow_email, "Follow-Up"])
            st.success("ðŸ” Follow-up logged.")
            with st.expander("ðŸ“„ Follow-Up Text"):
                st.code(follow_email)

    except Exception as e:
        st.error(f"âŒ Error: {e}")

st.markdown("---")
st.header("ðŸ“ Bulk Upload CSV & Generate Outreach Emails")
bulk_file = st.file_uploader("Upload CSV with 'Industry' and 'Contact' columns", type="csv")

if bulk_file is not None:
    try:
        df = pd.read_csv(bulk_file)
        if not {"Industry", "Contact"}.issubset(df.columns):
            st.error("âŒ CSV must contain 'Industry' and 'Contact' columns.")
        else:
            st.dataframe(df)

            if st.button("ðŸ“¤ Generate Bulk Emails"):
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zipf:
                    for idx, row in df.iterrows():
                        industry = row["Industry"]
                        contact = row["Contact"]
                        prompt = f"Write a concise B2B outreach email to a {industry.lower()} client."
                        response = client_ai.chat.completions.create(
                            model="gpt-4",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        email_text = response.choices[0].message.content.strip()
                        clean = sanitize_text(email_text)

                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        for line in clean.split("\n"):
                            pdf.multi_cell(0, 10, line)
                        pdf_bytes = pdf.output(dest="S").encode("latin-1", "replace")

                        filename = f"{industry}_{contact.replace('@','_at_').replace('.', '_')}.pdf"
                        zipf.writestr(filename, pdf_bytes)

                        worksheet.append_row([
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            industry,
                            contact,
                            email_text
                        ])

                zip_buffer.seek(0)
                st.download_button("ðŸ“¥ Download All PDFs as ZIP", data=zip_buffer, file_name="qicp_bulk_emails.zip")

    except Exception as e:
        st.error(f"âŒ Bulk generation failed: {e}")
