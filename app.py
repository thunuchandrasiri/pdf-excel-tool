import streamlit as st
import pandas as pd
import json
from google import genai
from PIL import Image
from pypdf import PdfReader

st.set_page_config(page_title="PDF Invoice to Excel", layout="wide")
st.title("🧾 SME Invoice & Receipt to Excel Converter")

# Streamlit Secrets වලින් auto API Key එක ගැනීම හෝ Sidebar එකෙන් Input කිරීම
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

uploaded_file = st.file_uploader("Upload Receipt/Invoice (PDF or Image)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file and api_key:
    if st.button("Extract to Excel"):
        with st.spinner("AI Reading Document..."):
            try:
                client = genai.Client(api_key=api_key)
                prompt = """
                Extract invoice data into raw JSON with keys:
                - invoice_number (string), date (string), vendor_name (string), total_amount (number), tax_amount (number)
                Return ONLY valid JSON without markdown formatting or code blocks.
                """

                if uploaded_file.type == "application/pdf":
                    reader = PdfReader(uploaded_file)
                    text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=f"{prompt}\n\nInvoice Content:\n{text}"
                    )
                else:
                    image = Image.open(uploaded_file)
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=[image, prompt]
                    )

                clean_json = response.text.strip().replace("```json", "").replace("```", "")
                data = json.loads(clean_json)
                df = pd.DataFrame([data])
                
                st.success("Extraction Complete!")
                st.dataframe(df)
                
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Excel/CSV", csv_data, "invoice.csv", "text/csv")

            except Exception as e:
                st.error(f"Error: {e}")
