import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import difflib
import openai
from io import StringIO

# ── Page config (with emoji)
st.set_page_config(page_title="💸 AccountingDesk IA Dashboard", layout="wide")
st.title("💸 AccountingDesk IA Dashboard")

# ── Initialize OpenAI API key
openai.api_key = st.secrets["openai"]["api_key"]

# ── Database connection
conn_uri = st.secrets["postgres"]["connection_uri"]
engine = create_engine(conn_uri)

# ── Required fields and variants for CSV import
REQUIRED_FIELDS = {
    "date": ["date", "fecha", "transaction_date"],
    "description": ["description", "memo", "detalle"],
    "amount": ["amount", "monto", "value"],
    "currency": ["currency", "moneda", "curr"],
    "account_name": ["account_name", "account", "cuenta"]
}

def map_columns(cols):
    mapping = {}
    lower_cols = [c.lower() for c in cols]
    for field, variants in REQUIRED_FIELDS.items():
        match = None
        for v in variants:
            if v.lower() in lower_cols:
                match = cols[lower_cols.index(v.lower())]
                break
        if not match:
            close = difflib.get_close_matches(field, cols, n=1, cutoff=0.6)
            if close:
                match = close[0]
        if match:
            mapping[field] = match
    return mapping

# ── Load categories and subcategories mapping
@st.cache_data
def load_category_map():
    df_cat = pd.read_sql("SELECT id, name FROM categories ORDER BY name;", engine)
    df_sub = pd.read_sql("SELECT id, category_id, name FROM subcategories ORDER BY name;", engine)
    cat_map = {row["name"]: row["id"] for _, row in df_cat.iterrows()}
    sub_map = {}
    for _, row in df_sub.iterrows():
        sub_map.setdefault(row["category_id"], []).append((row["name"], row["id"]))
    return cat_map, sub_map

# ── Data loading functions

@st.cache_data
def load_entities():
    df = pd.read_sql("SELECT DISTINCT entity FROM accounts WHERE entity IS NOT NULL ORDER BY entity;", engine)
    return ["All Entities"] + df["entity"].dropna().tolist()

@st.cache_data
def load_institutions(entity):
    if entity == "All Entities":
        df = pd.read_sql("SELECT DISTINCT institution FROM accounts WHERE institution IS NOT NULL ORDER BY institution;", engine)
    else:
        df = pd.read_sql(
            text("SELECT DISTINCT institution FROM accounts WHERE entity = :ent ORDER BY institution;"),
            engine, params={"ent": entity}
        )
    return ["All Banks"] + df["institution"].tolist()

@st.cache_data
def load_accounts(entity, institution):
    df = pd.read_sql(
        text(
            "SELECT id, name, masked_number FROM accounts "
            "WHERE (:ent = 'All Entities' OR entity = :ent) "
            "  AND (:inst = 'All Banks' OR institution = :inst) "
            "ORDER BY name;"
        ),
        engine, params={"ent": entity, "inst": institution}
    )
    df["display"] = df["name"] + " (" + df["masked_number"] + ")"
    all_row = pd.DataFrame([{"id": None, "display": "All Accounts"}])
    return pd.concat([all_row, df[["id", "display"]]], ignore_index=True)

@st.cache_data
def load_transactions(filters):
    base = """
        SELECT t.id, t.date, t.description, t.amount, t.currency,
               a.entity, a.institution,
               c.name AS category, s.name AS subcategory
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN subcategories s ON t.subcategory_id = s.id
    """
    where, params = [], {}
    if filters.get("entity") and filters["entity"] != "All Entities":
        where.append("a.entity = :ent"); params["ent"] = filters["entity"]
    if filters.get("institution") and filters["institution"] != "All Banks":
        where.append("a.institution = :inst"); params["inst"] = filters["institution"]
    if filters.get("account_id") is not None:
        where.append("a.id = :aid"); params["aid"] = filters["account_id"]
    if where:
        base += " WHERE " + " AND ".join(where)
    base += " ORDER BY t.date DESC;"
    return pd.read_sql(text(base), engine, params=params)

# ── Classification function using OpenAI
def classify_transaction(description, entity, institution, cat_map, sub_map):
    prompt = f"""You are an accounting assistant.
Transaction description: "{description}"
Entity: "{entity}", Institution: "{institution}"
Choose the best category and subcategory.
Categories: {", ".join(cat_map.keys())}
Subcategories per category:
"""
    for cat, cid in cat_map.items():
        subs = [name for name, sid in sub_map.get(cid, [])]
        prompt += f"\n- {cat}: {', '.join(subs) or 'None'}"
    prompt += "\n\nRespond in JSON: {\"category\": \"<Category>\", \"subcategory\": \"<Subcategory>\"}."
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":"Classify the transaction."},
                  {"role":"user","content":prompt}],
        temperature=0
    )
    content = resp.choices[0].message.content
    try:
        result = pd.read_json(StringIO(content), typ="series")
        return result["category"], result["subcategory"]
    except:
        return None, None

# ── UI Filters
mode = st.radio("Filter by", ["All Transactions", "Entity", "Bank/Fintech", "Account"], horizontal=True)
filters = {"entity":"All Entities","institution":"All Banks","account_id":None}
if mode in ("Entity","Bank/Fintech","Account"):
    filters["entity"] = st.selectbox("Select entity", load_entities(), key="ent")
if mode in ("Bank/Fintech","Account"):
    filters["institution"] = st.selectbox("Select Bank/Fintech", load_institutions(filters["entity"]), key="inst")
if mode == "Account":
    acct_df = load_accounts(filters["entity"], filters["institution"])
    disp = st.selectbox("Select account", acct_df["display"].tolist(), key="acct")
    filters["account_id"] = None if disp == "All Accounts" else int(acct_df.loc[acct_df["display"]==disp,"id"].iloc[0])

# ── Sidebar CSV Import
st.sidebar.header("Import Transactions from CSV")
uploaded = st.sidebar.file_uploader("Upload CSV", type="csv")
if uploaded:
    df_csv = pd.read_csv(uploaded)
    mapping = map_columns(df_csv.columns.tolist())
    missing = [f for f in REQUIRED_FIELDS if f not in mapping]
    if missing:
        st.sidebar.error(f"Missing fields: {missing}")
    else:
        df_mapped = df_csv.rename(columns=mapping)[list(mapping.values())]
        df_mapped.columns = list(mapping.keys())
        st.sidebar.write("Preview:", df_mapped.head())
        if st.sidebar.button("Import to DB"):
            with engine.begin() as conn:
                doc_id = conn.execute(text(
                    "INSERT INTO documents(file_name, source_type, uploaded_by) VALUES(:fn,'csv','user') RETURNING id"
                ),{"fn":uploaded.name}).scalar()
                for _, row in df_mapped.iterrows():
                    acct_id = conn.execute(text("SELECT id FROM accounts WHERE name=:nm LIMIT 1"),{"nm":row["account_name"]}).scalar()
                    if acct_id:
                        conn.execute(text(
                            "INSERT INTO transactions(account_id,date,description,amount,currency,source_type,document_id) "
                            "VALUES(:aid,:dt,:desc,:amt,:cur,'csv',:doc)"
                        ),{
                            "aid":acct_id, "dt":row["date"], "desc":row["description"],
                            "amt":row["amount"], "cur":row["currency"], "doc":doc_id
                        })
            st.sidebar.success("Imported successfully!")
            st.cache_data.clear()
            st.experimental_rerun()

# ── Auto-categorization button
if st.sidebar.button("Auto-categorize uncategorized"):
    cat_map, sub_map = load_category_map()
    tx_df = load_transactions(filters)
    unc = tx_df[tx_df["category"].isna()]
    for _, row in unc.iterrows():
        cat, sub = classify_transaction(row["description"], row["entity"], row["institution"], cat_map, sub_map)
        if cat and sub:
            cid = cat_map.get(cat)
            sid = next((sid for name,sid in sub_map.get(cid,[]) if name==sub), None)
            if cid and sid:
                engine.execute(text(
                    "UPDATE transactions SET category_id=:cid, subcategory_id=:sid WHERE id=:tid"
                ),{"cid":cid,"sid":sid,"tid":row["id"]})
    st.sidebar.success("Auto-categorization complete!")
    st.cache_data.clear()
    st.experimental_rerun()

# ── Display transactions
transactions_df = load_transactions(filters)
st.subheader(f"Transactions ({mode})")
st.dataframe(transactions_df, use_container_width=True)

# ── Sidebar: Manage Accounts
st.sidebar.header("Manage Accounts")
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
with st.sidebar.expander("🗑️ Delete account", expanded=False):
    full_df = pd.read_sql("SELECT id, entity, institution, name, masked_number FROM accounts ORDER BY entity, institution, name;", engine)
    if not full_df.empty:
        full_df["display"] = full_df["entity"] + " | " + full_df["institution"] + " | " + full_df["name"] + " (" + full_df["masked_number"] + ")"
        to_delete = st.selectbox("Select account to delete", full_df["display"].tolist(), key="del_acct")
        if st.sidebar.button("Delete account"):
            acct_id = int(full_df.loc[full_df["display"] == to_delete, "id"].iloc[0])
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM accounts WHERE id = :id"), {"id": acct_id})
            st.sidebar.success("Account deleted.")
            st.cache_data.clear()
            st.experimental_rerun()
    else:
        st.sidebar.info("No accounts found.")
