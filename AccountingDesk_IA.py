import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import difflib
import openai
from io import StringIO

# ── Page config (with emoji)
st.set_page_config(page_title="💸 AccountingDesk IA Dashboard", layout="wide")
st.title("💸 AccountingDesk IA Dashboard")

# ── Initialize OpenAI API key (for auto-categorization)
openai.api_key = st.secrets["openai"]["api_key"]

# ── Database connection
conn_uri = st.secrets["postgres"]["connection_uri"]
engine = create_engine(conn_uri)

# ── Required fields & variants for CSV import
REQUIRED_FIELDS = {
    "date": ["date", "fecha", "transaction_date"],
    "description": ["description", "memo", "detalle"],
    "amount": ["amount", "monto", "value"],
    "currency": ["currency", "moneda", "curr"],
    "account_name": ["account_name", "account", "cuenta"]
}

def map_columns(cols):
    """Heuristic: substring + fuzzy match"""
    mapping = {}
    lower = [c.lower() for c in cols]
    for field, variants in REQUIRED_FIELDS.items():
        found = None
        for var in [field] + variants:
            for orig, low in zip(cols, lower):
                if var.lower() in low:
                    found = orig
                    break
            if found:
                break
        if not found:
            close = difflib.get_close_matches(field, cols, n=1, cutoff=0.6)
            if close:
                found = close[0]
        if found:
            mapping[field] = found
    return mapping

# ── Load mapping of categories/subcategories
@st.cache_data
def load_category_map():
    df_cat = pd.read_sql("SELECT id, name FROM categories ORDER BY name;", engine)
    df_sub = pd.read_sql("SELECT id, category_id, name FROM subcategories ORDER BY name;", engine)
    cat_map = {r["name"]: r["id"] for _, r in df_cat.iterrows()}
    sub_map = {}
    for _, r in df_sub.iterrows():
        sub_map.setdefault(r["category_id"], []).append((r["name"], r["id"]))
    return cat_map, sub_map

# ── Data loaders
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
    if filters["entity"] != "All Entities":
        where.append("a.entity = :ent"); params["ent"] = filters["entity"]
    if filters["institution"] != "All Banks":
        where.append("a.institution = :inst"); params["inst"] = filters["institution"]
    if filters["account_id"] is not None:
        where.append("a.id = :aid"); params["aid"] = filters["account_id"]
    if where:
        base += " WHERE " + " AND ".join(where)
    base += " ORDER BY t.date DESC;"
    return pd.read_sql(text(base), engine, params=params)

# ── Classification helper
def classify_transaction(desc, ent, inst, cat_map, sub_map):
    prompt = (
        f"You are an accounting assistant.\n"
        f"Description: \"{desc}\"\nEntity: \"{ent}\", Institution: \"{inst}\"\n"
        f"Categories: {', '.join(cat_map.keys())}\nSubcategories:\n"
    )
    for name, cid in cat_map.items():
        subs = [n for n, sid in sub_map.get(cid, [])]
        prompt += f"- {name}: {', '.join(subs) or 'None'}\n"
    prompt += "Respond JSON: {\"category\": \"<Category>\", \"subcategory\": \"<Subcategory>\"}."
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":"Classify transaction."},
                  {"role":"user","content":prompt}],
        temperature=0
    )
    content = resp.choices[0].message.content
    try:
        series = pd.read_json(StringIO(content), typ="series")
        return series["category"], series["subcategory"]
    except:
        return None, None

# ── Filters UI
mode = st.radio("Filter by", ["All Transactions","Entity","Bank/Fintech","Account"], horizontal=True)
filters = {"entity":"All Entities","institution":"All Banks","account_id":None}
if mode in ("Entity","Bank/Fintech","Account"):
    filters["entity"] = st.selectbox("Select entity", load_entities(), key="ent")
if mode in ("Bank/Fintech","Account"):
    filters["institution"] = st.selectbox("Select Bank/Fintech", load_institutions(filters["entity"]), key="inst")
if mode == "Account":
    df_acc = load_accounts(filters["entity"], filters["institution"])
    sel = st.selectbox("Select account", df_acc["display"].tolist(), key="acct")
    filters["account_id"] = None if sel=="All Accounts" else int(df_acc.loc[df_acc["display"]==sel,"id"].iloc[0])

# ── CSV Importer with currency selector & manual override
st.sidebar.header("Import Transactions from CSV")
uploaded = st.sidebar.file_uploader("Upload CSV", type="csv")
if uploaded:
    df_csv = pd.read_csv(uploaded)
    st.sidebar.write("Detected columns:", df_csv.columns.tolist())

    # Default currency dropdown
    default_currency = st.sidebar.selectbox("Default currency", ["USD","EUR","GBP","MXN","CAD"], index=0)

    # Heuristic mapping
    mapping = map_columns(df_csv.columns.tolist())

    # Manual override
    final_map = {}
    st.sidebar.write("Adjust mapping if needed:")
    for field in REQUIRED_FIELDS:
        opts = [""] + df_csv.columns.tolist()
        default = mapping.get(field, "")
        idx = opts.index(default) if default in opts else 0
        choice = st.sidebar.selectbox(f"{field} ←", opts, index=idx, key=f"map_{field}")
        if choice:
            final_map[field] = choice

    missing = [f for f in REQUIRED_FIELDS if f not in final_map]
    if missing:
        st.sidebar.error(f"Missing fields: {missing}")
    else:
        df_mapped = df_csv.rename(columns=final_map)[list(final_map.values())]
        df_mapped.columns = list(final_map.keys())
        if "currency" not in final_map:
            df_mapped["currency"] = default_currency
        st.sidebar.write("Preview:", df_mapped.head())

        if st.sidebar.button("Import to DB"):
            with engine.begin() as conn:
                doc_id = conn.execute(text(
                    "INSERT INTO documents(file_name,source_type,uploaded_by) VALUES(:fn,'csv','user') RETURNING id"
                ), {"fn": uploaded.name}).scalar()
                for _, row in df_mapped.iterrows():
                    acct = conn.execute(text(
                        "SELECT id FROM accounts WHERE name=:nm LIMIT 1"
                    ), {"nm": row["account_name"]}).scalar()
                    if acct:
                        conn.execute(text(
                            "INSERT INTO transactions "
                            "(account_id,date,description,amount,currency,source_type,document_id) "
                            "VALUES(:aid,:dt,:desc,:amt,:cur,'csv',:doc)"
                        ), {
                            "aid": acct,
                            "dt": row["date"],
                            "desc": row["description"],
                            "amt": row["amount"],
                            "cur": row["currency"],
                            "doc": doc_id
                        })
            st.sidebar.success("Imported successfully!")
            st.cache_data.clear()
            st.experimental_rerun()

# ── Auto-categorize button
if st.sidebar.button("Auto-categorize uncategorized"):
    cat_map, sub_map = load_category_map()
    df_tx = load_transactions(filters)
    unc = df_tx[df_tx["category"].isna()]
    for _, r in unc.iterrows():
        cat, sub = classify_transaction(r["description"], r["entity"], r["institution"], cat_map, sub_map)
        if cat and sub:
            cid = cat_map.get(cat)
            sid = next((sid for n,sid in sub_map.get(cid,[]) if n==sub), None)
            if cid and sid:
                engine.execute(text(
                    "UPDATE transactions SET category_id=:cid,subcategory_id=:sid WHERE id=:tid"
                ), {"cid": cid, "sid": sid, "tid": r["id"]})
    st.sidebar.success("Auto-categorization complete!")
    st.cache_data.clear()
    st.experimental_rerun()

# ── Display transactions
df_tx = load_transactions(filters)
st.subheader(f"Transactions ({mode})")
st.dataframe(df_tx, use_container_width=True)

# ── Manage Accounts
st.sidebar.header("Manage Accounts")
with st.sidebar.expander("➕ Add account", expanded=False):
    with st.form("add_account", clear_on_submit=True):
        ne = st.text_input("Entity")
        ni = st.text_input("Bank/Fintech")
        nn = st.text_input("Name")
        nt = st.selectbox("Type", ["Bank","Credit Card"], key="nt")
        nc = st.text_input("Currency", value="USD")
        nm = st.text_input("Last 4 digits")
        if st.form_submit_button("Add Account"):
            if all([ne,ni,nn,nt,nc,nm]):
                with engine.begin() as conn:
                    conn.execute(text(
                        "INSERT INTO accounts(entity,institution,name,type,currency,masked_number) "
                        "VALUES(:e,:i,:n,:t,:c,:m)"
                    ), {"e":ne,"i":ni,"n":nn,"t":nt,"c":nc,"m":nm})
                st.sidebar.success("Account added!")
                st.cache_data.clear()
                st.experimental_rerun()

with st.sidebar.expander("🗑️ Delete account", expanded=False):
    full = pd.read_sql("SELECT id,entity,institution,name,masked_number FROM accounts ORDER BY entity,institution,name;", engine)
    if not full.empty:
        full["display"] = full["entity"]+" | "+full["institution"]+" | "+full["name"]+" ("+full["masked_number"]+")"
        to_del = st.selectbox("Select account", full["display"].tolist(), key="del")
        if st.sidebar.button("Delete account"):
            aid = int(full.loc[full["display"]==to_del,"id"].iloc[0])
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM accounts WHERE id=:id"), {"id": aid})
            st.sidebar.success("Deleted.")
            st.cache_data.clear()
            st.experimental_rerun()
