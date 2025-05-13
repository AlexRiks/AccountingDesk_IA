import streamlit as st
import pandas as pd
from utils.ai import classify_transaction
from utils.firebase import init_firebase, save_transaction
from utils.parsers import parse_csv

st.set_page_config(page_title="AI Transaction Classifier", layout="wide")
st.title("💸 AI Transaction Classifier")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded_file:
    df = parse_csv(uploaded_file)
    st.dataframe(df)

    if st.button("Classify Transactions with AI"):
        with st.spinner("Classifying..."):
            classified_df = classify_transaction(df)
            st.dataframe(classified_df)

            if st.button("Save to Firebase"):
                for _, row in classified_df.iterrows():
                    save_transaction(row.to_dict())
                st.success("Transactions saved successfully.")