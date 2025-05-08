import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# -- Streamlit page config
st.set_page_config(page_title="AccountingDesk IA Dashboard", layout="wide")

# -- Title
st.title("AccountingDesk IA Dashboard")

# -- Database connection
conn_uri = st.secrets["postgres"]["connection_uri"]
engine = create_engine(conn_uri)

# -- Helper to load distinct account names (grouping masked variants)
@st.cache_data
def load_account_names():
    df = pd.read_sql("SELECT DISTINCT name FROM accounts ORDER BY name;", engine)
    return df["name"].tolist()

# -- Display grouped account selector
account_names = load_account_names()
selected_account = st.selectbox("Select account", account_names)

# -- Helper to load transactions by account name
@st.cache_data
def load_transactions_by_name(name):
    q = """
        SELECT
            t.id,
            t.date,
            t.description,
            t.amount,
            t.currency,
            c.name AS category,
            s.name AS subcategory
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN subcategories s ON t.subcategory_id = s.id
        WHERE a.name = :name
        ORDER BY t.date DESC;
    """
    return pd.read_sql(text(q), engine, params={"name": name})

# Fetch and display all transactions for the selected account name
transactions_df = load_transactions_by_name(selected_account)

st.subheader(f"Transactions for {selected_account}")
st.dataframe(transactions_df, use_container_width=True)

# -- Sidebar: Manage Accounts
st.sidebar.header("Manage Accounts")

# --- Add new account
with st.sidebar.expander("➕ Add account", expanded=False):
    with st.form("account_form", clear_on_submit=True):
        new_name     = st.text_input("Name")
        new_type     = st.selectbox("Type", ["bank", "credit card", "paypal"])
        new_currency = st.text_input("Currency")
        new_masked   = st.text_input("Last 4 digits")
        submit_add   = st.form_submit_button("Add Account")
        if submit_add:
            if new_name and new_currency and new_masked:
                with engine.begin() as conn:
                    conn.execute(text(
                        "INSERT INTO accounts (name, type, currency, masked_number) "
                        "VALUES (:name, :type, :currency, :masked)"
                    ), {
                        "name": new_name,
                        "type": new_type,
                        "currency": new_currency,
                        "masked": new_masked
                    })
                st.sidebar.success(f"Account '{new_name}' added!")
                st.cache_data.clear()
                st.experimental_rerun()
            else:
                st.sidebar.error("Fill in all fields to add an account.")

# --- Delete existing account
# We fetch full accounts list here to allow deletion of individual entries
@st.cache_data
def load_full_accounts():
    return pd.read_sql("SELECT id, name, masked_number FROM accounts ORDER BY name;", engine)

full_accounts_df = load_full_accounts()
if not full_accounts_df.empty:
    with st.sidebar.expander("🗑️ Delete account", expanded=False):
        # Display combined label with masked_number for clarity
        full_accounts_df["display"] = full_accounts_df["name"] + " (" + full_accounts_df["masked_number"] + ")"
        to_delete = st.selectbox("Select account to delete", full_accounts_df["display"])
        if st.button("Delete account"):
            acct_id = int(full_accounts_df.loc[full_accounts_df["display"] == to_delete, "id"].iloc[0])
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM accounts WHERE id = :id"), {"id": acct_id})
            st.sidebar.success(f"Account '{to_delete}' deleted.")
            st.cache_data.clear()
            st.experimental_rerun()
else:
    st.sidebar.info("No accounts to delete.")
