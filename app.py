# app.py
import streamlit as st
import pandas as pd
import database_utils
import classification_engine
import llm_service
import os

# --- Page Config ---
st.set_page_config(layout="wide", page_title="Clasificador de Transacciones con IA")

# --- Database Initialization ---
# Crear tablas si no existen al inicio de la app
database_utils.create_tables()
# Cargar categorías desde la base de datos al inicio
# Se asume que app_database.db está presente y poblada (ej. incluida en el repo de Git)
master_categories_list_from_db = database_utils.get_all_categories()

# --- Helper Functions ---
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

# --- Session State Initialization ---
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = False
if "google_api_key" not in st.session_state:
    # Intentar cargar desde st.secrets al inicio
    try:
        st.session_state.google_api_key = st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        st.session_state.google_api_key = "" # Fallback si st.secrets no está disponible (ej. localmente sin secrets.toml)
        
if "transactions_df" not in st.session_state:
    st.session_state.transactions_df = None
if "edited_transactions_df" not in st.session_state:
    st.session_state.edited_transactions_df = None
if "categories_loaded" not in st.session_state:
    st.session_state.categories_loaded = bool(master_categories_list_from_db)

if "master_categories_list" not in st.session_state:
    if master_categories_list_from_db:
        st.session_state.master_categories_list = ["No Categorizada"] + [f"{cat} - {subcat}" for cat, subcat in master_categories_list_from_db]
    else:
        st.session_state.master_categories_list = ["No Categorizada"]

# --- API Key Configuration (Automática desde Secrets) ---
if st.session_state.google_api_key:
    if llm_service.configure_gemini(st.session_state.google_api_key):
        st.session_state.api_key_set = True
    else:
        st.session_state.api_key_set = False # Error en configuración
else:
    st.session_state.api_key_set = False # No hay API Key

# --- Sidebar ---
st.sidebar.header("Información")

if not st.session_state.api_key_set:
    st.sidebar.error("API Key de Google Gemini no configurada en los Secrets de Streamlit Cloud. La clasificación IA no funcionará.")
    st.sidebar.markdown("Por favor, asegúrate de configurar `GOOGLE_API_KEY` en los Secrets de tu aplicación en Streamlit Cloud.")
else:
    st.sidebar.success("API Key de Gemini cargada desde Secrets.")

if not st.session_state.categories_loaded:
    st.sidebar.warning("No se encontraron categorías en la base de datos (`app_database.db`). La clasificación podría no funcionar como se espera. Asegúrate de que `app_database.db` esté presente y poblada con tus categorías.")
else:
    st.sidebar.info(f"{len(master_categories_list_from_db)} categorías cargadas desde la base de datos.")

# Download Transaction Template
st.sidebar.subheader("Plantilla de Transacciones")
# Asegurarse que el archivo template_transacciones.csv existe en la ruta correcta.
# Si se ejecuta desde el directorio donde está app.py y template_transacciones.csv está ahí:
template_path = "template_transacciones.csv"
if not os.path.exists(template_path):
    # Intentar una ruta absoluta si es necesario, o manejar el error
    template_path = "/home/ubuntu/template_transacciones.csv"

if os.path.exists(template_path):
    with open(template_path, "rb") as fp:
        st.sidebar.download_button(
            label="Descargar Plantilla CSV",
            data=fp,
            file_name="template_transacciones.csv",
            mime="text/csv"
        )
else:
    st.sidebar.error("Archivo de plantilla no encontrado.")

# --- Main Application Area ---
st.title("🤖 Clasificador Automático de Transacciones con IA")
st.markdown("Sube tus transacciones, clasifícalas con IA, corrige si es necesario y descarga los resultados.")

# Upload Transactions CSV
st.header("1. Cargar y Procesar Transacciones")
transactions_file = st.file_uploader("Sube tu archivo CSV de Transacciones", type=["csv"], key="transactions_uploader")

if transactions_file is not None:
    if not st.session_state.api_key_set:
        st.error("Error: API Key de Gemini no configurada. Revisa los Secrets de Streamlit Cloud.")
    elif not st.session_state.categories_loaded:
        st.error("Error: No hay categorías cargadas en la base de datos. La aplicación no puede clasificar.")
    else:
        try:
            df = pd.read_csv(transactions_file)
            st.session_state.transactions_df = df.copy() # Guardar copia original
            
            description_column = "ExpenseDesc"
            if description_column not in df.columns:
                st.error(f"El archivo CSV de transacciones debe contener la columna 	{description_column}")
                st.session_state.transactions_df = None
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                classified_categories = []

                total_rows = len(df)
                for i, row in df.iterrows():
                    desc = str(row[description_column]) if pd.notna(row[description_column]) else ""
                    status_text.text(f"Procesando transacción {i+1}/{total_rows}: 	{desc[:50]}...")
                    
                    assigned_category = classification_engine.get_category_for_transaction(desc, st.session_state.google_api_key)
                    classified_categories.append(assigned_category)
                    progress_bar.progress((i + 1) / total_rows)
                
                status_text.success(f"¡Clasificación inicial completada para {total_rows} transacciones!")
                df["Categoria_IA"] = classified_categories
                st.session_state.edited_transactions_df = df.copy()

        except Exception as e:
            st.error(f"Error al procesar el archivo de transacciones: {e}")
            st.session_state.transactions_df = None
            st.session_state.edited_transactions_df = None

# Display and Edit Transactions
if st.session_state.edited_transactions_df is not None:
    st.header("2. Revisar y Corregir Categorías")
    st.markdown("Puedes editar la columna `Categoria_IA` directamente. Tus cambios se guardarán para futuras clasificaciones.")
    
    category_options = st.session_state.master_categories_list
    
    cols_to_display = [col for col in st.session_state.edited_transactions_df.columns if col != "Categoria_IA"]
    try:
        desc_idx = cols_to_display.index("ExpenseDesc")
        cols_to_display.insert(desc_idx + 1, "Categoria_IA")
    except ValueError:
        cols_to_display.append("Categoria_IA")

    column_config = {
        "Categoria_IA": st.column_config.SelectboxColumn(
            "Categoría (Editable)",
            help="Selecciona la categoría correcta. Tus cambios se aprenderán.",
            options=category_options,
            required=False,
        )
    }
    for col in st.session_state.edited_transactions_df.columns:
        if col != "Categoria_IA":
            column_config[col] = st.column_config.TextColumn(disabled=True)

    # Usar una clave diferente para el data_editor si se recarga para evitar problemas de estado
    edited_df = st.data_editor(
        st.session_state.edited_transactions_df[cols_to_display],
        column_config=column_config,
        num_rows="dynamic",
        key=f"data_editor_{transactions_file.id if transactions_file else 'no_file'}", # Cambiar key si el archivo cambia
        height=600
    )

    if edited_df is not None:
        changes_detected_count = 0
        # Crear una copia para comparar, ya que edited_df puede ser modificado por el usuario
        df_before_edit = st.session_state.edited_transactions_df.copy()

        for i, edited_row_series in edited_df.iterrows():
            # Asegurarse de que el índice exista en el dataframe original (df_before_edit)
            if i in df_before_edit.index:
                original_row_series = df_before_edit.loc[i]
                original_category_ia = original_row_series.get("Categoria_IA", "")
                edited_category_ia = edited_row_series.get("Categoria_IA", "")
                
                description_column = "ExpenseDesc"
                current_description = original_row_series.get(description_column, "")

                if pd.notna(edited_category_ia) and edited_category_ia != original_category_ia and current_description:
                    cat_parts = edited_category_ia.split(" - ", 1)
                    main_cat = cat_parts[0].strip() if len(cat_parts) > 0 else "No Categorizada"
                    sub_cat = cat_parts[1].strip() if len(cat_parts) > 1 else ""
                    if main_cat == "No Categorizada":
                        sub_cat = ""
                    
                    if database_utils.save_correction(current_description, main_cat, sub_cat):
                        changes_detected_count +=1
                    else:
                        st.warning(f"No se pudo guardar la corrección para: 	{current_description[:30]}...")
            else:
                # El índice no existe, podría ser una nueva fila si num_rows="dynamic" y se permite añadir
                # Por ahora, la lógica de guardado se enfoca en filas existentes.
                pass # O manejar la adición de nuevas filas si es una funcionalidad deseada
        
        if changes_detected_count > 0:
            st.toast(f"{changes_detected_count} correcciones guardadas y aprendidas!", icon="🧠")
        
        # Actualizar el dataframe en session_state para la descarga
        st.session_state.edited_transactions_df = edited_df.copy()

        st.header("3. Descargar Transacciones Procesadas")
        csv_to_download = convert_df_to_csv(st.session_state.edited_transactions_df) # Usar el DF actualizado
        st.download_button(
            label="Descargar CSV con Categorías Corregidas",
            data=csv_to_download,
            file_name="transacciones_categorizadas_corregidas.csv",
            mime="text/csv",
        )

st.sidebar.markdown("---_---")
st.sidebar.info("Desarrollado por Manus AI Agent")

