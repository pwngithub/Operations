
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="COO Dashboard", layout="wide")

st.title("📊 Pioneer Broadband COO Dashboard")
st.markdown("Upload the latest CSV exports from your Streamlit apps to view consolidated summaries.")

uploaded_files = st.file_uploader("Upload CSV files", accept_multiple_files=True, type=["csv"])

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.subheader(f"Data Preview: {uploaded_file.name}")
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)

        # Display basic summary info
        with st.expander("Quick Stats"):
            st.write(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
            st.write("Columns:", list(df.columns))

        # Show simple KPI metrics if MRC or similar columns exist
        mrc_cols = [col for col in df.columns if "mrc" in col.lower()]
        if mrc_cols:
            for col in mrc_cols:
                total = df[col].sum()
                st.metric(label=f"Total {col}", value=f"${total:,.2f}")
else:
    st.info("Upload one or more CSV files to begin.")
