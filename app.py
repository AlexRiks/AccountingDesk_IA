# app.py
import streamlit as st
import pandas as pd
import database_utils
import classification_engine
import llm_service
import os

# --- Page Config ---
st.set_page_config(
    layout="wide", 
    page_title="AI Transaction Classifier", 
    initial_sidebar_state="expanded" # Allows user to collapse
)

# --- Database Initialization ---
database_utils.create_tables()
master_categories_list_from_db = database_utils.get_all_categories()

# --- Helper Functions ---
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

# --- Session State Initialization ---
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = False
if "google_api_key" not in st.session_state:
    try:
        st.session_state.google_api_key = st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        st.session_state.google_api_key = ""
        
if "transactions_df" not in st.session_state:
    st.session_state.transactions_df = None
if "edited_transactions_df" not in st.session_state:
    st.session_state.edited_transactions_df = None
if "categories_loaded" not in st.session_state:
    st.session_state.categories_loaded = bool(master_categories_list_from_db)

if "master_categories_list_for_selectbox" not in st.session_state:
    if master_categories_list_from_db:
        st.session_state.master_categories_list_for_selectbox = ["Uncategorized"] + [f"{cat} - {subcat}" for cat, subcat in master_categories_list_from_db]
    else:
        st.session_state.master_categories_list_for_selectbox = ["Uncategorized"]

# --- API Key Configuration ---
if st.session_state.google_api_key:
    if llm_service.configure_gemini(st.session_state.google_api_key):
        st.session_state.api_key_set = True
    else:
        st.session_state.api_key_set = False
else:
    st.session_state.api_key_set = False

# --- Sidebar ---
st.sidebar.header("Status & Template")

# API Key Status
if os.getenv("OPENAI_API_KEY") is None:
    st.sidebar.error("❌ OpenAI API")
else:
    st.sidebar.success("✅ OpenAI API")
    st.sidebar.markdown("Please ensure `OpenAI API` is configured in Streamlit Cloud Secrets.")

# Database/Categories Status
if st.session_state.categories_loaded:
    st.sidebar.success(f"✓ {len(master_categories_list_from_db)} categories loaded from database.")
else:
    st.sidebar.error("✗ No categories found in database. Classification may not work.")
    st.sidebar.markdown("Ensure `app_database.db` is present and populated.")

# Download Transaction Template
st.sidebar.subheader("Transaction Template")
template_file_name = "transaction_template.csv"
# Initial assumption: template is in the same directory as app.py
current_dir_template_path = template_file_name 
# Alternative common path in the sandbox home
home_dir_template_path = os.path.join("/home/ubuntu", template_file_name)

# Determine the correct path for template_path
actual_template_path_to_use = None
if os.path.exists(current_dir_template_path):
    actual_template_path_to_use = current_dir_template_path
elif os.path.exists(home_dir_template_path):
    actual_template_path_to_use = home_dir_template_path

if actual_template_path_to_use:
    with open(actual_template_path_to_use, "rb") as fp:
        st.sidebar.download_button(
            label="Download Template CSV",
            data=fp,
            file_name=template_file_name, 
            mime="text/csv"
        )
else:
    st.sidebar.error(f"✗ Template file ({template_file_name}) not found in expected locations.")

# --- Main Application Area ---
st.title("🤖 AI Transaction Classifier")
st.markdown("Upload your transactions, classify them with AI, correct as needed, and download the results.")

# Upload Transactions CSV
st.header("1. Upload and Process Transactions")
transactions_file = st.file_uploader("Upload your Transactions CSV file", type=["csv"], key="transactions_uploader")

if transactions_file is not None:
    if not st.session_state.api_key_set:
        st.error("Error: Gemini API Key not configured. Check Streamlit Cloud Secrets.")
    elif not st.session_state.categories_loaded:
        st.error("Error: No categories loaded in the database. The application cannot classify.")
    else:
        try:
            df = pd.read_csv(transactions_file)
            st.session_state.transactions_df = df.copy()
            
            description_column = "ExpenseDesc"
            if description_column not in df.columns:
                st.error(f"The transactions CSV file must contain the column: 	{description_column}")
                st.session_state.transactions_df = None
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                classified_categories = []
                total_rows = len(df)

                for i, row in df.iterrows():
                    desc = str(row[description_column]) if pd.notna(row[description_column]) else ""
                    status_text.text(f"Processing transaction {i+1}/{total_rows}: 	{desc[:50]}...")
                    assigned_category = classification_engine.get_category_for_transaction(desc, st.session_state.google_api_key)
                    classified_categories.append(assigned_category)
                    progress_bar.progress((i + 1) / total_rows)
                
                status_text.success(f"Initial classification completed for {total_rows} transactions!")
                df["AI_Category"] = classified_categories
                st.session_state.edited_transactions_df = df.copy()

        except Exception as e:
            st.error(f"Error processing the transaction file: {e}")
            st.session_state.transactions_df = None
            st.session_state.edited_transactions_df = None

if st.session_state.edited_transactions_df is not None:
    st.header("2. Review and Correct Categories")
    st.markdown("You can edit the `AI_Category` column directly. Your changes will be saved for future classifications.")
    
    category_options_for_selectbox = st.session_state.master_categories_list_for_selectbox
    cols_to_display = [col for col in st.session_state.edited_transactions_df.columns if col != "AI_Category"]
    try:
        desc_idx = cols_to_display.index("ExpenseDesc")
        cols_to_display.insert(desc_idx + 1, "AI_Category")
    except ValueError:
        cols_to_display.append("AI_Category")

    column_config = {
        "AI_Category": st.column_config.SelectboxColumn(
            "AI Category (Editable)",
            help="Select the correct category. Your changes will be learned.",
            options=category_options_for_selectbox,
            required=False,
        )
    }
    for col in st.session_state.edited_transactions_df.columns:
        if col != "AI_Category":
            column_config[col] = st.column_config.TextColumn(disabled=True)

    editor_key = "data_editor_no_file"
    if transactions_file:
        # Use a combination of name and size as a more robust key if file_id is not always available
        editor_key = f"data_editor_{transactions_file.name}_{transactions_file.size}"

    edited_df = st.data_editor(
        st.session_state.edited_transactions_df[cols_to_display],
        column_config=column_config,
        num_rows="dynamic",
        key=editor_key,
        height=600
    )

    if edited_df is not None:
        changes_detected_count = 0
        df_before_edit = st.session_state.edited_transactions_df.copy()

        for i, edited_row_series in edited_df.iterrows():
            if i in df_before_edit.index:
                original_row_series = df_before_edit.loc[i]
                original_category_value = original_row_series.get("AI_Category", "")
                edited_category_value = edited_row_series.get("AI_Category", "")
                current_description = original_row_series.get("ExpenseDesc", "")

                if pd.notna(edited_category_value) and edited_category_value != original_category_value and current_description:
                    cat_parts = edited_category_value.split(" - ", 1)
                    main_cat_corrected = cat_parts[0].strip() if len(cat_parts) > 0 else "Uncategorized"
                    sub_cat_corrected = cat_parts[1].strip() if len(cat_parts) > 1 else ""
                    if main_cat_corrected == "Uncategorized":
                        sub_cat_corrected = ""
                    
                    if database_utils.save_correction(current_description, main_cat_corrected, sub_cat_corrected):
                        changes_detected_count +=1
                    else:
                        st.warning(f"Could not save correction for: 	{current_description[:30]}...")
        
        if changes_detected_count > 0:
            st.toast(f"{changes_detected_count} corrections saved and learned!", icon="🧠")
        
        st.session_state.edited_transactions_df = edited_df.copy()

        st.header("3. Download Processed Transactions")
        csv_to_download = convert_df_to_csv(st.session_state.edited_transactions_df)
        st.download_button(
            label="Download CSV with Corrected Categories",
            data=csv_to_download,
            file_name="classified_transactions_corrected.csv",
            mime="text/csv",
        )

st.sidebar.markdown("------")
st.sidebar.info("Developed by BSCH")

