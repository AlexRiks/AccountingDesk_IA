import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# -- Streamlit page config
st.set_page_config(page_title="AccountingDesk IA Dashboard", layout="wide")

# -- Title
st.title("AccountingDesk IA Dashboard")

# -- Load connection URI from Streamlit secrets
conn_uri = st.secrets["postgres"]["CONNECTION_URI"]
engine = create_engine(conn_uri)

# -- Helper to load accounts
@st.cache_data
def load_accounts():
    query = "SELECT id, name FROM accounts ORDER BY name;"
    return pd.read_sql(query, engine)

# -- Display account selector
accounts_df = load_accounts()
selected_account = st.selectbox("Select account", accounts_df["name"].tolist())

# -- Helper to load transactions for a given account
@st.cache_data
def load_transactions(account_id):
    query = f"""
        SELECT
            t.id,
            t.date,
            t.description,
            t.amount,
            t.currency,
            c.name AS category,
            s.name AS subcategory
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN subcategories s ON t.subcategory_id = s.id
        WHERE t.account_id = {account_id}
        ORDER BY t.date DESC;
    """
    return pd.read_sql(query, engine)

# -- Fetch and display transactions
account_id = int(accounts_df.loc[accounts_df["name"] == selected_account, "id"].iloc[0])
transactions_df = load_transactions(account_id)
st.subheader(f"Transactions for {selected_account}")
st.dataframe(transactions_df, use_container_width=True)
