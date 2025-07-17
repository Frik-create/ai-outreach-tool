# QICP B2B Outreach Tool

This is a Streamlit-based AI outreach generator for personalized B2B emails, integrated with:
- OpenAI GPT-4
- Google Sheets CRM logging
- Outlook email sending
- PDF download
- Bulk CSV uploads

## Deployment Steps

1. Push this repo to GitHub.
2. Log into [Render.com](https://render.com/) and create a new Web Service.
3. Connect to this repo.
4. Set environment variables using the values from `.streamlit/secrets.toml`:
   - `OPENAI_API_KEY`
   - `OUTLOOK_CLIENT_ID`
   - `OUTLOOK_CLIENT_SECRET`
   - `OUTLOOK_TENANT_ID`
   - `OUTLOOK_SENDER_EMAIL`
5. Upload your `credentials.json` in the root of the project.
6. Click deploy. Done!

For help, contact frik@qicp.co.za
