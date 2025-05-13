# app.py
import streamlit as st
import pandas as pd
import database_utils
import classification_engine
import llm_service # To configure the API key if necessary directly
import os

# --- Page Config ---
st.set_page_config(layout="wide", page_title="AI Transaction Classifier")

# --- Database Initialization ---
# Create tables if they don't exist at app startup
database_utils.create_tables()
# Load categories from the database at startup
# Assumes app_database.db is present and populated (e.g., included in the Git repo)
master_categories_list_from_db = database_utils.get_all_categories() # This will be list of (cat, subcat) tuples

# --- Helper Functions ---
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

# --- Session State Initialization ---
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = False
if "google_api_key" not in st.session_state:
    # Try to load from st.secrets at startup
    try:
        st.session_state.google_api_key = st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        st.session_state.google_api_key = "" # Fallback if st.secrets is not available (e.g., locally without secrets.toml)
        
if "transactions_df" not in st.session_state:
    st.session_state.transactions_df = None
if "edited_transactions_df" not in st.session_state:
    st.session_state.edited_transactions_df = None
if "categories_loaded" not in st.session_state:
    st.session_state.categories_loaded = bool(master_categories_list_from_db)

if "master_categories_list_for_selectbox" not in st.session_state:
    if master_categories_list_from_db:
        # Format for selectbox: "Category - Subcategory"
        st.session_state.master_categories_list_for_selectbox = ["Uncategorized"] + [f"{cat} - {subcat}" for cat, subcat in master_categories_list_from_db]
    else:
        st.session_state.master_categories_list_for_selectbox = ["Uncategorized"]

# --- API Key Configuration (Automatic from Secrets) ---
if st.session_state.google_api_key:
    if llm_service.configure_gemini(st.session_state.google_api_key):
        st.session_state.api_key_set = True
    else:
        st.session_state.api_key_set = False # Error in configuration
else:
    st.session_state.api_key_set = False # No API Key

# --- Sidebar ---
st.sidebar.header("Information")

if not st.session_state.api_key_set:
    st.sidebar.error("Google Gemini API Key not configured in Streamlit Cloud Secrets. AI classification will not work.")
    st.sidebar.markdown("Please ensure `GOOGLE_API_KEY` is configured in your Streamlit Cloud application Secrets.")
else:
    st.sidebar.success("Gemini API Key loaded from Secrets.")

if not st.session_state.categories_loaded:
    st.sidebar.warning("No categories found in the database (`app_database.db`). Classification may not work as expected. Ensure `app_database.db` is present and populated with your categories.")
else:
    st.sidebar.info(f"{len(master_categories_list_from_db)} categories loaded from the database.")

# Download Transaction Template
st.sidebar.subheader("Transaction Template")
# Ensure the template_transacciones.csv file exists in the correct path.
# If run from the directory where app.py is and template_transacciones.csv is there:
template_path = "template_transacciones.csv" # This filename can be kept or changed to English too
if not os.path.exists(template_path):
    # Try an absolute path if necessary, or handle the error
    template_path = "/home/ubuntu/template_transacciones.csv"

if os.path.exists(template_path):
    with open(template_path, "rb") as fp:
        st.sidebar.download_button(
            label="Download Template CSV",
            data=fp,
            file_name="transaction_template.csv", # Changed filename for download to English
            mime="text/csv"
        )
else:
    st.sidebar.error("Template file not found.")

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
            st.session_state.transactions_df = df.copy() # Save original copy
            
            description_column = "ExpenseDesc" # From user's file structure
            if description_column not in df.columns:
                st.error(f"The transactions CSV file must contain the column: 	{description_column}")
                st.session_state.transactions_df = None # Reset to prevent processing
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                classified_categories = []

                total_rows = len(df)
                for i, row in df.iterrows():
                    desc = str(row[description_column]) if pd.notna(row[description_column]) else ""
                    status_text.text(f"Processing transaction {i+1}/{total_rows}: 	{desc[:50]}...")
                    
                    # Assuming classification_engine returns English strings or "Uncategorized"
                    assigned_category = classification_engine.get_category_for_transaction(desc, st.session_state.google_api_key)
                    classified_categories.append(assigned_category)
                    progress_bar.progress((i + 1) / total_rows)
                
                status_text.success(f"Initial classification completed for {total_rows} transactions!")
                df["AI_Category"] = classified_categories # New column for the category
                st.session_state.edited_transactions_df = df.copy()

        except Exception as e:
            st.error(f"Error processing the transaction file: {e}")
            st.session_state.transactions_df = None
            st.session_state.edited_transactions_df = None

# Display and Edit Transactions
if st.session_state.edited_transactions_df is not None:
    st.header("2. Review and Correct Categories")
    st.markdown("You can edit the `AI_Category` column directly. Your changes will be saved for future classifications.")
    
    category_options_for_selectbox = st.session_state.master_categories_list_for_selectbox
    
    cols_to_display = [col for col in st.session_state.edited_transactions_df.columns if col != "AI_Category"]
    try:
        desc_idx = cols_to_display.index("ExpenseDesc") # User's description column
        cols_to_display.insert(desc_idx + 1, "AI_Category")
    except ValueError:
        cols_to_display.append("AI_Category") # If not found, append at the end

    column_config = {
        "AI_Category": st.column_config.SelectboxColumn(
            "AI Category (Editable)",
            help="Select the correct category. Your changes will be learned.",
            options=category_options_for_selectbox,
            required=False, # Allows it to be empty if "Uncategorized" is chosen or nothing selected
        )
    }
    # Disable editing of other columns for safety and focus
    for col in st.session_state.edited_transactions_df.columns:
        if col != "AI_Category":
            column_config[col] = st.column_config.TextColumn(disabled=True)

    # Use a different key for data_editor if it reloads to prevent state issues
    edited_df = st.data_editor(
        st.session_state.edited_transactions_df[cols_to_display],
        column_config=column_config,
        num_rows="dynamic", # or "fixed"
        key=f"data_editor_{transactions_file.id if transactions_file else 'no_file'}", # Change key if file changes
        height=600 # Adjust height as needed
    )

    if edited_df is not None:
        changes_detected_count = 0
        # Create a copy to compare, as edited_df can be modified by the user
        df_before_edit = st.session_state.edited_transactions_df.copy()

        for i, edited_row_series in edited_df.iterrows():
            # Ensure the index exists in the original dataframe (df_before_edit)
            if i in df_before_edit.index:
                original_row_series = df_before_edit.loc[i]
                original_category_value = original_row_series.get("AI_Category", "")
                edited_category_value = edited_row_series.get("AI_Category", "")
                
                description_column = "ExpenseDesc" # User's description column
                current_description = original_row_series.get(description_column, "")

                if pd.notna(edited_category_value) and edited_category_value != original_category_value and current_description:
                    # Category was changed and is not NaN
                    # Save the correction
                    cat_parts = edited_category_value.split(" - ", 1)
                    main_cat_corrected = cat_parts[0].strip() if len(cat_parts) > 0 else "Uncategorized"
                    sub_cat_corrected = cat_parts[1].strip() if len(cat_parts) > 1 else ""
                    if main_cat_corrected == "Uncategorized": # If user explicitly selects "Uncategorized"
                        sub_cat_corrected = ""
                    
                    if database_utils.save_correction(current_description, main_cat_corrected, sub_cat_corrected):
                        changes_detected_count +=1
                    else:
                        st.warning(f"Could not save correction for: 	{current_description[:30]}...")
            else:
                # Index does not exist, could be a new row if num_rows="dynamic" and adding is allowed
                # For now, saving logic focuses on existing rows.
                pass # Or handle adding new rows if it's a desired feature
        
        if changes_detected_count > 0:
            st.toast(f"{changes_detected_count} corrections saved and learned!", icon="🧠")
        
        # Update the dataframe in session_state for download
        st.session_state.edited_transactions_df = edited_df.copy()

        st.header("3. Download Processed Transactions")
        csv_to_download = convert_df_to_csv(st.session_state.edited_transactions_df) # Use the updated DF
        st.download_button(
            label="Download CSV with Corrected Categories",
            data=csv_to_download,
            file_name="classified_transactions_corrected.csv",
            mime="text/csv",
        )

st.sidebar.markdown("---_---")
st.sidebar.info("Developed by Manus AI Agent")

