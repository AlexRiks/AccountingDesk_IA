import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# ── Page config
st.set_page_config(page_title="AccountingDesk IA Dashboard", layout="wide")
st.title("AccountingDesk IA Dashboard")

# ── DB connection
conn_uri = st.secrets["postgres"]["connection_uri"]
engine = create_engine(conn_uri)

# ── Data loaders

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
        "SELECT id, name, masked_number FROM accounts "
        "WHERE entity = :ent AND institution = :inst "
        "ORDER BY name;",
        engine,
        params={"ent": entity, "inst": institution}
    )
    # prepare display "Name (####)"
    df["display"] = df["name"] + " (" + df["masked_number"] + ")"
    return df

@st.cache_data
def load_transactions_by_entity(entity):
    q = """
        SELECT
            t.id, t.date, t.description, t.amount, t.currency,
            a.entity, a.institution,
            c.name AS category, s.name AS subcategory
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN subcategories s ON t.subcategory_id = s.id
        WHERE a.entity = :ent
        ORDER BY t.date DESC;
    """
    return pd.read_sql(text(q), engine, params={"ent": entity})

@st.cache_data
def load_transactions_by_institution(entity, institution):
    q = """
        SELECT
            t.id, t.date, t.description, t.amount, t.currency,
            a.entity, a.institution,
            c.name AS category, s.name AS subcategory
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN subcategories s ON t.subcategory_id = s.id
        WHERE a.entity = :ent AND a.institution = :inst
        ORDER BY t.date DESC;
    """
    return pd.read_sql(text(q), engine, params={"ent": entity, "inst": institution})

@st.cache_data
def load_transactions_by_account_id(account_id):
    q = """
        SELECT
            t.id, t.date, t.description, t.amount, t.currency,
            a.entity, a.institution,
            c.name AS category, s.name AS subcategory
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN subcategories s ON t.subcategory_id = s.id
        WHERE a.id = :id
        ORDER BY t.date DESC;
    """
    return pd.read_sql(text(q), engine, params={"id": account_id})

# ── Choose filter mode
mode = st.radio("Filter by", ["Entity", "Bank/Fintech", "Account"], horizontal=True)

# ── Apply filters
if mode == "Entity":
    entities = load_entities()
    if not entities:
        st.error("No entities found.")
        st.stop()
    sel_entity = st.selectbox("Select entity", entities)
    df = load_transactions_by_entity(sel_entity)

elif mode == "Bank/Fintech":
    entities = load_entities()
    if not entities:
        st.error("No entities found.")
        st.stop()
    sel_entity = st.selectbox("Select entity", entities)
    insts = load_institutions(sel_entity)
    if not insts:
        st.error(f"No institutions for '{sel_entity}'.")
        st.stop()
    sel_inst = st.selectbox("Select Bank/Fintech", insts)
    df = load_transactions_by_institution(sel_entity, sel_inst)

else:  # Account mode
    entities = load_entities()
    if not entities:
        st.error("No entities found.")
        st.stop()
    sel_entity = st.selectbox("Select entity", entities)
    insts = load_institutions(sel_entity)
    if not insts:
        st.error(f"No institutions for '{sel_entity}'.")
        st.stop()
    sel_inst = st.selectbox("Select Bank/Fintech", insts)
    acct_df = load_accounts(sel_entity, sel_inst)
    if acct_df.empty:
        st.error(f"No accounts under {sel_entity} / {sel_inst}.")
        st.stop()
    sel_disp = st.selectbox("Select account", acct_df["display"].tolist())
    acct_id = int(acct_df.loc[acct_df["display"] == sel_disp, "id"].iloc[0])
    df = load_transactions_by_account_id(acct_id)

# ── Display results
st.subheader(f"Transactions ({mode})")
st.dataframe(df, use_container_width=True)

# ── Sidebar: Manage Accounts (unchanged)
st.sidebar.header("Manage Accounts")
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

full_df = pd.read_sql(
    "SELECT id, entity, institution, name, masked_number FROM accounts "
    "ORDER BY entity, institution, name;",
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
