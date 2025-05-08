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
    query = text(
        "SELECT DISTINCT institution "
        "FROM accounts "
        "WHERE entity = :ent "
        "ORDER BY institution;"
    )
    df = pd.read_sql(query, engine, params={"ent": entity})
    return df["institution"].tolist()

@st.cache_data
def load_accounts(entity=None, institution=None):
    query = text(
        "SELECT id, name, masked_number "
        "FROM accounts "
        "WHERE (:ent IS NULL OR entity = :ent) "
        "  AND (:inst IS NULL OR institution = :inst) "
        "ORDER BY name;"
    )
    df = pd.read_sql(query, engine, params={"ent": entity, "inst": institution})
    df["display"] = df["name"] + " (" + df["masked_number"] + ")"
    return df

@st.cache_data
def load_transactions(filters):
    base = (
        "SELECT "
        "  t.id, t.date, t.description, t.amount, t.currency, "
        "  a.entity, a.institution, "
        "  c.name AS category, s.name AS subcategory "
        "FROM transactions t "
        "JOIN accounts a ON t.account_id = a.id "
        "LEFT JOIN categories c ON t.category_id = c.id "
        "LEFT JOIN subcategories s ON t.subcategory_id = s.id "
    )
    where, params = [], {}
    if filters.get("entity"):
        where.append("a.entity = :ent")
        params["ent"] = filters["entity"]
    if filters.get("institution"):
        where.append("a.institution = :inst")
        params["inst"] = filters["institution"]
    if filters.get("account_id"):
        where.append("a.id = :aid")
        params["aid"] = filters["account_id"]
    if where:
        base += " WHERE " + " AND ".join(where)
    base += " ORDER BY t.date DESC;"
    return pd.read_sql(text(base), engine, params=params)

# ── Filter mode selector
mode = st.radio(
    "Filter by",
    ["Entity", "Bank/Fintech", "Account"],
    horizontal=True,
    key="filter_mode"
)

filters = {"entity": None, "institution": None, "account_id": None}

# ── Entity filter
if mode in ("Entity", "Bank/Fintech", "Account"):
    entities = load_entities()
    if not entities:
        st.error("No entities found. Please add accounts first.")
        st.stop()
    selected_entity = st.selectbox("Select entity", entities, key="sel_entity")
    filters["entity"] = selected_entity

# ── Institution filter
if mode in ("Bank/Fintech", "Account"):
    institutions = load_institutions(filters["entity"])
    if not institutions:
        st.error(f"No institutions for '{filters['entity']}'.")
        st.stop()
    selected_institution = st.selectbox("Select Bank/Fintech", institutions, key="sel_inst")
    filters["institution"] = selected_institution

# ── Account filter
if mode == "Account":
    acct_df = load_accounts(filters["entity"], filters["institution"])
    if acct_df.empty:
        st.error(f"No accounts under {filters['entity']} / {filters['institution']}.")
        st.stop()
    selected_display = st.selectbox("Select account", acct_df["display"].tolist(), key="sel_acct")
    filters["account_id"] = int(acct_df.loc[acct_df["display"] == selected_display, "id"].iloc[0])

# ── Load and display transactions
transactions_df = load_transactions(filters)
st.subheader(f"Transactions ({mode})")
st.dataframe(transactions_df, use_container_width=True)

# ── Sidebar: Manage Accounts

st.sidebar.header("Manage Accounts")

# ➕ Add account
with st.sidebar.expander("➕ Add account", expanded=False):
    with st.form("add_account", clear_on_submit=True):
        new_entity      = st.text_input("Entity")
        new_institution = st.text_input("Bank/Fintech")
        new_name        = st.text_input("Name")
        new_type        = st.selectbox("Type", ["Bank", "Credit Card"], key="new_type")
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
            full_df["name"] + " (" +
            full_df["masked_number"] + ")"
        )
        to_delete = st.selectbox("Select account to delete", full_df["display"].tolist(), key="del_acct")
        if st.button("Delete account"):
            acct_id = int(full_df.loc[full_df["display"] == to_delete, "id"].iloc[0])
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM accounts WHERE id = :id"), {"id": acct_id})
            st.sidebar.success("Account deleted.")
            st.cache_data.clear()
            st.experimental_rerun()
else:
    st.sidebar.info("No accounts found.")
