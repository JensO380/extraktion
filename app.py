import streamlit as st
import pdfplumber
import pandas as pd
import io
import re

st.set_page_config(page_title="PDF Angebotsdaten Extraktion", layout="wide")
st.title("📄 PDF-Angebotsdaten Extraktion")

uploaded_files = st.file_uploader("PDF-Dateien hochladen", type="pdf", accept_multiple_files=True)

def extract_data_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    quote_match = re.search(r'Quotation #[:\s]*([0-9.]+)', text)
    quote = quote_match.group(1) if quote_match else ""

    exchange_match = re.search(r'Exchange Rate[:\s]*([^\n]+)', text)
    exchange_rate = exchange_match.group(1).strip() if exchange_match else ""

    org_match = re.search(r'Organization[:\s]*(.+)', text)
    organization = org_match.group(1).strip() if org_match else ""

    pattern = re.compile(
        r'Mfr Part #[:\s]*(?P<sku>\S+).*?Description[:\s]*(?P<desc>.*?)\n.*?Qty[:\s]*(?P<qty>\d+).*?List Price[:\s]*([€$])?(?P<list_price>[\d.,]+).*?Discount[:\s]*(?P<discount>[\d.,]+%)?.*?Unit Price[:\s]*([€$])?(?P<unit_price>[\d.,]+).*?Ext Price[:\s]*([€$])?(?P<ext_price>[\d.,]+)',
        re.DOTALL
    )

    rows = []
    for match in pattern.finditer(text):
        rows.append({
            "Kunde": organization,
            "Quote": quote,
            "Exchange Rate": exchange_rate,
            "SKU": match.group("sku"),
            "Beschreibung": match.group("desc").strip(),
            "Menge": match.group("qty"),
            "List Price": match.group("list_price"),
            "Discount": match.group("discount"),
            "Unit Price": match.group("unit_price"),
            "Ext Price": match.group("ext_price")
        })

    return pd.DataFrame(rows)

if uploaded_files:
    all_data = pd.concat([extract_data_from_pdf(file) for file in uploaded_files], ignore_index=True)
    st.success(f"{len(all_data)} Artikelpositionen extrahiert.")
    st.dataframe(all_data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        all_data.to_excel(writer, index=False, sheet_name="Angebotsdaten")
    st.download_button("📥 Excel-Datei herunterladen", output.getvalue(), file_name="Angebotsdaten.xlsx")
