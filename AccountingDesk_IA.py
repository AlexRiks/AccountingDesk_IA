import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# ── Page config
st.set_page_config(page_title="AccountingDesk IA Dashboard", layout="wide")
st.title("AccountingDesk IA Dashboard")

# ── Database connection
conn_uri = st.secrets["postgres"]["connection_uri"]
engine = create_engine(conn_uri)

# ── Data loading functions

@st.cache_data
def load_entities():
    df = pd.read_sql(
        "SELECT DISTINCT entity FROM accounts WHERE entity IS NOT NULL ORDER BY entity;",
        engine
    )
    return df["entity"].tolist()

@st.cache_data
def load_institutions(entity):
    df = pd.read_sql(
        "SELECT DISTINCT institution FROM accounts WHERE entity = :ent ORDER BY institution;",
        engine,
        params={"ent": entity}
    )
    return df["institution"].tolist()

@st.cache_data
def load_accounts(entity, institution):
    df = pd.read_sql(
        "SELECT id, name, masked_number FROM accounts WHERE entity = :ent AND institution = :inst ORDER BY name;",
        engine,
        params={"ent": entity, "inst": institution}
    )
    return df

@st.cache_data
def load_transactions_by_account_id(account_id):
    q = """
        SELECT
            t.id,
            t.date,
            t.description,
            t.amount,
            t.currency,
            a.entity,
            a.institution,
            c.name AS category,
            s.name AS subcategory
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN subcategories s ON t.subcategory_id = s.id
        WHERE a.id = :id
        ORDER BY t.date DESC;
    """
    return pd.read_sql(text(q), engine, params={"id": account_id})

# ── Main selectors

entities = load_entities()
if not entities:
    st.error("No entities found. Please add accounts first.")
    st.stop()
selected_entity = st.selectbox("Select entity", entities)

institutions = load_institutions(selected_entity)
if not institutions:
    st.error(f"No institutions for entity '{selected_entity}'.")
    st.stop()
selected_institution = st.selectbox("Select Bank/Fintech", institutions)

accounts_df = load_accounts(selected_entity, selected_institution)
if accounts_df.empty:
    st.error(f"No accounts for {selected_entity} / {selected_institution}.")
    st.stop()

# build display labels: "Name (####)"
accounts_df["display"] = (
    accounts_df["name"] + " (" + accounts_df["masked_number"] + ")"
)
selected_display = st.selectbox("Select account", accounts_df["display"].tolist())

# get the corresponding id
account_id = int(
    accounts_df.loc[accounts_df["display"] == selected_display, "id"].iloc[0]
)

# ── Show transactions
transactions_df = load_transactions_by_account_id(account_id)
st.subheader(f"Transactions for {selected_entity} / {selected_institution} / {selected_display}")
st.dataframe(transactions_df, use_container_width=True)

# ── Sidebar: Manage Accounts

st.sidebar.header("Manage Accounts")

# ➕ Add account
with st.sidebar.expander("➕ Add account", expanded=False):
    with st.form("add_account", clear_on_submit=True):
        new_entity      = st.text_input("Entity")
        new_institution = st.text_input("Bank/Fintech")
        new_name        = st.text_input("Name")
        new_type        = st.selectbox("Type", ["Bank", "Credit Card"])
        new_currency    = st.text_input("Currency", value="USD")
        new_masked      = st.text_input("Last 4 digits")
        if st.form_submit_button("Add Account"):
            if all([new_entity, new_institution, new_name, new_type, new_currency, new_masked]):
                with engine.begin() as conn:
                    conn.execute(text(
                        "INSERT INTO accounts (entity, institution, name, type, currency, masked_number) "
                        "VALUES (:entity, :inst, :name, :type, :curr, :masked)"
                    ), {
                        "entity": new_entity,
                        "inst": new_institution,
                        "name": new_name,
                        "type": new_type,
                        "curr": new_currency,
                        "masked": new_masked
                    })
                st.sidebar.success(f"Account '{new_name}' added!")
                st.cache_data.clear()
                st.experimental_rerun()
            else:
                st.sidebar.error("Fill in all fields to add an account.")

# 🗑️ Delete account
full_df = pd.read_sql(
    "SELECT id, entity, institution, name, masked_number FROM accounts ORDER BY entity, institution, name;",
    engine
)
if not full_df.empty:
    with st.sidebar.expander("🗑️ Delete account", expanded=False):
        full_df["display"] = (
            full_df["entity"] + " | " +
            full_df["institution"] + " | " +
            full_df["name"] + " (" + full_df["masked_number"] + ")"
        )
        to_delete = st.selectbox("Select account to delete", full_df["display"].tolist())
        if st.button("Delete account"):
            acct_id = int(full_df.loc[full_df["display"] == to_delete, "id"].iloc[0])
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM accounts WHERE id = :id"), {"id": acct_id})
            st.sidebar.success("Account deleted.")
            st.cache_data.clear()
            st.experimental_rerun()
else:
    st.sidebar.info("No accounts found.")
