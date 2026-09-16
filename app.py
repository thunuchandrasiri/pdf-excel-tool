import streamlit as st
import pandas as pd
import json
from google import genai
from PIL import Image
from pypdf import PdfReader

st.set_page_config(page_title="PDF & Receipt to Excel Converter", layout="wide")
st.title("🧾 Universal Invoice & Supermarket Receipt Extractor")

# Secrets වලින් API Key එක ගැනීම
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

uploaded_file = st.file_uploader("Upload Receipt/Invoice (PDF or Image)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file and api_key:
    if st.button("Extract to Excel"):
        with st.spinner("AI Reading Itemized Receipt..."):
            try:
                client = genai.Client(api_key=api_key)
                prompt = """
                Extract invoice/receipt data into raw JSON with this exact structure:
                {
                  "vendor_name": "string",
                  "date": "string",
                  "invoice_number": "string",
                  "grand_total": number,
                  "items": [
                    {
                      "item_description": "string",
                      "quantity": number,
                      "unit_price": number,
                      "total_price": number
                    }
                  ]
                }
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
                
                # Supermarket Bill එකක Items තියෙනවා නම් Table එක Explode කර හදයි
                if "items" in data and isinstance(data["items"], list) and len(data["items"]) > 0:
                    df = pd.json_normalize(
                        data, 
                        record_path=["items"], 
                        meta=["vendor_name", "date", "invoice_number", "grand_total"],
                        errors="ignore"
                    )
                else:
                    df = pd.DataFrame([data])

                st.success("Extraction Complete!")
                st.dataframe(df)
                
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Excel/CSV", csv_data, "receipt_data.csv", "text/csv")

            except Exception as e:
                st.error(f"Error: {e}")
