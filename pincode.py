import streamlit as st
import pandas as pd
import requests
import time
from tqdm import tqdm
import io

# === Page Config ===
st.set_page_config(page_title="Sleep Company Store Finder", layout="centered")
st.title("🛏️ The Sleep Company - Nearest Stores Finder")
st.markdown("Upload a CSV file with pincodes to get the 10 nearest stores for each pincode.")

# === API Details ===
API_URL = "https://api.thesleepcompany.in/stores"
HEADERS = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'origin': 'https://thesleepcompany.in',
    'referer': 'https://thesleepcompany.in/',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36',
    'x-api-key': 'KPwkS7MFb71KXrezuxUYJaf4EnFGvgkK9kgWaf7q'
}

DESIRED_FIELDS = {
    "storeName": "Store Name",
    "storeId": "Store ID",
    "address": "Address",
    "contact": "Contact",
    "mapLink": "Map Link",
    "distance": "Distance (km)",
    "city": "City"
}

def fetch_stores(pincode):
    params = {"pincode": str(pincode).strip()}
    try:
        response = requests.get(API_URL, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("stores", [])[:10]  # Top 10 only
    except:
        pass
    return []

# === Sidebar - File Upload ===
with st.sidebar:
    st.header("Upload File")
    uploaded_file = st.file_uploader("Choose Pincodes.csv", type=["csv"])
    st.info("CSV should have a column like: Pincodes, pincode, Pincode, etc.")

if uploaded_file is None:
    st.stop()

# === Read and Process File ===
@st.cache_data
def load_pincodes(file):
    df = pd.read_csv(file)
    # Find pincode column
    pin_col = next((col for col in df.columns if "pin" in col.lower() or "code" in col.lower()), df.columns[0])
    pincodes = df[pin_col].dropna().astype(str).str.strip()
    pincodes = pincodes[pincodes.str.isdigit()].unique().tolist()
    return pincodes

pincodes = load_pincodes(uploaded_file)
total = len(pincodes)

st.write(f"**Found {total} unique pincodes** in your file.")

if st.button("🚀 Start Finding Nearest Stores", type="primary"):
    if total == 0:
        st.error("No valid pincodes found!")
        st.stop()

    all_stores = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    result_placeholder = st.empty()

    for i, pincode in enumerate(pincodes):
        status_text.text(f"Processing pincode: {pincode} ({i+1}/{total})")
        
        stores = fetch_stores(pincode)
        for store in stores:
            row = {"Input Pincode": pincode}
            for api_key, display_name in DESIRED_FIELDS.items():
                row[display_name] = store.get(api_key, "")
            all_stores.append(row)
        
        progress_bar.progress((i + 1) / total)
        time.sleep(0.5)  # Be kind to the API

    # === Create Final DataFrame ===
    if all_stores:
        df_output = pd.DataFrame(all_stores)
        column_order = ["Input Pincode"] + list(DESIRED_FIELDS.values())
        df_output = df_output[column_order]

        # Convert to Excel in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_output.to_excel(writer, index=False, sheet_name='Nearest Stores')
        output.seek(0)

        st.success(f"✅ Done! Found {len(all_stores)} stores across {total} pincodes.")
        
        st.download_button(
            label="📥 Download Results as Excel",
            data=output,
            file_name="Nearest_Sleep_Company_Stores.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.balloons()  # Fun celebration!
    else:
        st.error("No stores found for any pincode. Try different areas.")

else:
    st.info("Click the button above to start processing.")