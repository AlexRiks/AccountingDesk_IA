import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# ── Configuración de página
st.set_page_config(page_title="AccountingDesk IA Dashboard", layout="wide")
st.title("AccountingDesk IA Dashboard")

# ── Conexión a la BD
conn_uri = st.secrets["postgres"]["connection_uri"]
engine = create_engine(conn_uri)

# ── Funciones de carga
@st.cache_data
def load_account_names():
    df = pd.read_sql("SELECT DISTINCT name FROM accounts ORDER BY name;", engine)
    return df["name"].tolist()

@st.cache_data
def load_full_accounts():
    return pd.read_sql("SELECT id, entity, institution, name, masked_number FROM accounts ORDER BY name;", engine)

@st.cache_data
def load_transactions_by_name(name):
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
        WHERE a.name = :name
        ORDER BY t.date DESC;
    """
    return pd.read_sql(text(q), engine, params={"name": name})

# ── Selector agrupado por nombre
account_names = load_account_names()
selected_account = st.selectbox("Select account", account_names)

# ── Mostrar transacciones
transactions_df = load_transactions_by_name(selected_account)
st.subheader(f"Transactions for {selected_account}")
st.dataframe(transactions_df, use_container_width=True)

# ── Sidebar: gestionar cuentas
st.sidebar.header("Manage Accounts")

# ➕ Agregar cuenta
with st.sidebar.expander("➕ Add account", expanded=False):
    with st.form("add_account", clear_on_submit=True):
        new_entity     = st.text_input("Entity")
        new_institution= st.text_input("Bank/Fintech")
        new_name       = st.text_input("Name")
        new_type       = st.selectbox("Type", ["bank", "credit card", "paypal"])
        new_currency   = st.text_input("Currency", value="USD")
        new_masked     = st.text_input("Last 4 digits")
        if st.form_submit_button("Add Account"):
            if all([new_entity, new_institution, new_name, new_currency, new_masked]):
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

# 🗑️ Eliminar cuenta
full_accounts_df = load_full_accounts()
if not full_accounts_df.empty:
    with st.sidebar.expander("🗑️ Delete account", expanded=False):
        # Mostrar entidad, institución, nombre y dígitos para diferenciar
        full_accounts_df["display"] = (
            full_accounts_df["entity"] + " | " +
            full_accounts_df["institution"] + " | " +
            full_accounts_df["name"] + " (" +
            full_accounts_df["masked_number"] + ")"
        )
        to_delete = st.selectbox("Select account to delete", full_accounts_df["display"])
        if st.button("Delete account"):
            acct_id = int(full_accounts_df.loc[full_accounts_df["display"] == to_delete, "id"].iloc[0])
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM accounts WHERE id = :id"), {"id": acct_id})
            st.sidebar.success(f"Account deleted.")
            st.cache_data.clear()
            st.experimental_rerun()
else:
    st.sidebar.info("No accounts found.")
