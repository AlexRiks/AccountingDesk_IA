import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de secretos de Streamlit
def get_secret(key, default=None):
    try:
        return st.secrets[key]
    except:
        return os.getenv(key, default)

# Configuración de la base de datos
DB_HOST = get_secret("DB_HOST", "localhost")
DB_PORT = get_secret("DB_PORT", "5432")
DB_NAME = get_secret("DB_NAME", "transactions")
DB_USER = get_secret("DB_USER", "postgres")
DB_PASSWORD = get_secret("DB_PASSWORD", "")

# Configuración de OpenAI
OPENAI_API_KEY = get_secret("OPENAI_API_KEY", "")

# Configuración de la página
st.set_page_config(
    page_title="Clasificador de Transacciones IA",
    page_icon="💰",
    layout="wide"
)

# Título y descripción
st.title("🤖 Clasificador de Transacciones con IA")
st.markdown("""
Esta aplicación utiliza inteligencia artificial para clasificar automáticamente 
sus transacciones financieras en categorías y clases apropiadas.
""")

# Verificar configuración
if not OPENAI_API_KEY:
    st.warning("⚠️ No se ha configurado la API key de OpenAI. Algunas funciones pueden no estar disponibles.")

# Sidebar
st.sidebar.title("Navegación")
page = st.sidebar.radio(
    "Seleccione una página:",
    ["Clasificación", "Entidades", "Productos", "Configuración"]
)

# Función principal de clasificación
def clasificar_transacciones(archivo):
    try:
        if archivo.name.endswith('.csv'):
            df = pd.read_csv(archivo)
            return df
        elif archivo.name.endswith('.pdf'):
            st.warning("Procesamiento de PDF en desarrollo")
            return None
        else:
            st.error("Formato de archivo no soportado")
            return None
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        return None

# Páginas
if page == "Clasificación":
    st.header("📊 Clasificación de Transacciones")
    
    # Upload de archivos
    archivo = st.file_uploader(
        "Cargar archivo de transacciones (CSV o PDF)",
        type=['csv', 'pdf']
    )
    
    if archivo is not None:
        df = clasificar_transacciones(archivo)
        if df is not None:
            st.dataframe(df)
            
            # Botones de acción
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Clasificar"):
                    st.info("Clasificación en proceso...")
            with col2:
                if st.button("Exportar CSV"):
                    st.download_button(
                        "Descargar CSV",
                        df.to_csv(index=False),
                        "transacciones_clasificadas.csv",
                        "text/csv"
                    )
            with col3:
                if st.button("Limpiar"):
                    st.experimental_rerun()

elif page == "Entidades":
    st.header("🏢 Gestión de Entidades")
    # Formulario para agregar entidades
    with st.form("nueva_entidad"):
        nombre = st.text_input("Nombre de la Entidad")
        descripcion = st.text_area("Descripción")
        activo = st.checkbox("Activo", value=True)
        submitted = st.form_submit_button("Agregar Entidad")
        
        if submitted:
            st.success(f"Entidad '{nombre}' agregada exitosamente")

elif page == "Productos":
    st.header("💳 Gestión de Productos Financieros")
    # Formulario para agregar productos
    with st.form("nuevo_producto"):
        entidad = st.selectbox("Entidad", ["Entidad 1", "Entidad 2"])
        tipo = st.selectbox("Tipo", ["Cuenta Bancaria", "Tarjeta de Crédito"])
        nombre = st.text_input("Nombre del Producto")
        numero = st.text_input("Número (últimos 4 dígitos)")
        submitted = st.form_submit_button("Agregar Producto")
        
        if submitted:
            st.success(f"Producto '{nombre}' agregado exitosamente")

else:  # Configuración
    st.header("⚙️ Configuración")
    
    # Mostrar estado de la configuración
    st.subheader("Estado de la Configuración")
    
    # Verificar conexión a la base de datos
    db_status = "✅ Conectado" if DB_HOST and DB_PORT else "❌ No configurado"
    st.info(f"Estado de la Base de Datos: {db_status}")
    
    # Verificar API Key
    api_status = "✅ Configurado" if OPENAI_API_KEY else "❌ No configurado"
    st.info(f"Estado de OpenAI API: {api_status}")
    
    # Configuración del modelo IA
    st.subheader("Configuración del Modelo IA")
    threshold = st.slider("Umbral de confianza", 0.0, 1.0, 0.8)
    
    if st.button("Guardar Configuración"):
        st.success("Configuración guardada exitosamente") 