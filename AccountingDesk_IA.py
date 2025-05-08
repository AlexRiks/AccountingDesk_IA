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

# -- Helper to load accounts
@st.cache_data
def load_accounts():
    df = pd.read_sql("SELECT id, name FROM accounts ORDER BY name;", engine)
    return df

# -- Account management in sidebar
st.sidebar.header("Manage Accounts")

# --- 1) Add new account
with st.sidebar.expander("➕ Add account", expanded=True):
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

# --- 2) Delete existing account
accounts_df = load_accounts()
if not accounts_df.empty:
    with st.sidebar.expander("🗑️ Delete account"):
        to_delete = st.selectbox("Select account to delete", accounts_df["name"])
        if st.button("Delete account"):
            # confirm deletion
            confirm = st.confirm(f"Are you sure you want to delete '{to_delete}'? This cannot be undone.")
            if confirm:
                acct_id = int(accounts_df.loc[accounts_df["name"] == to_delete, "id"].iloc[0])
                with engine.begin() as conn:
                    conn.execute(text("DELETE FROM accounts WHERE id = :id"), {"id": acct_id})
                st.sidebar.success(f"Account '{to_delete}' deleted.")
                st.cache_data.clear()
                st.experimental_rerun()
else:
    st.sidebar.info("No accounts to delete.")

# -- Main dashboard: list transactions
accounts_df = load_accounts()
if accounts_df.empty:
    st.error("No accounts found. Please add one via the sidebar.")
    st.stop()

selected_account = st.selectbox("Select account", accounts_df["name"].tolist())

# -- Helper to load transactions
@st.cache_data
def load_transactions(account_id):
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
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN subcategories s ON t.subcategory_id = s.id
        WHERE t.account_id = :acct
        ORDER BY t.date DESC;
    """
    return pd.read_sql(text(q), engine, params={"acct": account_id})

acct_id = int(accounts_df.loc[accounts_df["name"] == selected_account, "id"].iloc[0])
transactions_df = load_transactions(acct_id)

st.subheader(f"Transactions for {selected_account}")
st.dataframe(transactions_df, use_container_width=True)
