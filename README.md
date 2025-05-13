AI Transaction Classifier Application (Enhanced Version)
Summary
This Streamlit application allows users to upload financial transactions from a CSV file, automatically classify them using AI (Gemini Pro) based on a predefined list of categories and subcategories stored permanently in a database (app_database.db), manually correct classifications, and have the application "learn" from these corrections for future transactions. The Gemini API Key is configured securely via Streamlit Cloud Secrets. The results can be downloaded.

Project File Structure
/
├── app.py                     # Main Streamlit application script
├── database_utils.py          # Utilities for SQLite database management
├── llm_service.py             # Service to interact with the Gemini API
├── classification_engine.py   # Classification logic (combines AI and learning)
├── requirements.txt           # Python dependencies
├── Categories_for_db_population.csv # Example CSV to populate the DB initially (see note below)
├── app_database.db            # SQLite database (should be populated and in the repo)
├── transaction_template.csv   # CSV template for the user to know the expected format
└── README.md                  # This file
Local Setup and Execution
Prerequisites:

Python 3.9 or higher.
pip to install packages.
Create a Virtual Environment (Recommended):

python3 -m venv venv
source venv/bin/activate  # On Linux/macOS
# venv\Scripts\activate    # On Windows
Install Dependencies: Navigate to the project root directory and run:

pip install -r requirements.txt
Prepare the Category Database (app_database.db):

The application now expects app_database.db to exist and contain the populated lista_categorias table.
For the first time / or to bulk update categories:
Ensure you have a Categories_for_db_population.csv file with your categories (columns: Category, Subcategory).
You can use the database_utils.py script directly to populate the database. Uncomment the test lines at the end of database_utils.py and run it:
# In database_utils.py, at the end, modify and uncomment:
# if __name__ == '__main__':
#     create_tables()
#     # Ensure Categories_for_db_population.csv is in the same directory or provide the correct path
#     if load_categories_from_csv('Categories_for_db_population.csv'): 
#         print("Database populated with categories.")
#     else:
#         print("Error populating the database.")
#     print(get_all_categories())
Then run: python database_utils.py
This will create/update app_database.db with categories from the CSV. Ensure this updated app_database.db is in your project directory.
Configure Google Gemini API Key (for local execution):

The application will attempt to read the API Key from Streamlit Secrets (if you run in an environment that supports them, like Streamlit Cloud or locally with a .streamlit/secrets.toml file).
For local development without secrets.toml, you can temporarily set the GOOGLE_API_KEY environment variable or modify llm_service.py to pass the key directly (not recommended for production).
A secrets.toml file in a .streamlit directory at your project root would look like this:
GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
Run the Application:

streamlit run app.py
The application will open in your web browser.

Initial Use (Local):

Ensure app_database.db is populated and the API Key is accessible (via secrets.toml or environment variable).
Download the transaction template if needed.
Upload your transaction CSV file (with an ExpenseDesc column).
The application will process the transactions. You can edit the categories.
Download the results.
Deployment on Streamlit Community Cloud
Prepare your GitHub Repository:

Create a new public GitHub repository.
Upload all project files: app.py, database_utils.py, llm_service.py, classification_engine.py, requirements.txt, transaction_template.csv, and very importantly, the app_database.db file already populated with your categories.
app_database.db: This SQLite database stores your categories and learned corrections. For categories and learning to persist, you must include app_database.db in your Git repository and commit/push changes whenever the database is updated (e.g., if you add new categories locally or if learned corrections are significant).
Connect your Repository to Streamlit Cloud:

Go to share.streamlit.io and sign up or log in.
Click "New app".
Select "Deploy from GitHub".
Choose your repository, branch (usually main or master), and the main application file (app.py).
Configure Secrets (Environment Variables):

The application requires your Google Gemini API Key via Streamlit Cloud Secrets.
In your Streamlit Cloud app settings, go to "Settings" -> "Secrets".
Add a new secret with the following format:
GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
Replace YOUR_GEMINI_API_KEY_HERE with your actual key.
The app.py application is designed to read this key from st.secrets.
Deploy:

Click "Deploy!". Streamlit Cloud will install dependencies and run your application.
Using the Deployed Application
Access your Streamlit Cloud application's public URL.
The API Key will be taken from Secrets. Categories will be loaded from app_database.db in your repository.
Upload your transactions.
Review, correct, and download.
Additional Notes
Category Management: To add, remove, or bulk-modify categories, you will need to update your Categories_for_db_population.csv file locally, re-populate app_database.db using database_utils.py (as described in local setup), and then commit and push the updated app_database.db to your GitHub repository.
Description Column: The application expects an ExpenseDesc column in your transaction file. If different, modify description_column in app.py.
Learning: Corrections are saved in app_database.db. For this learning to persist in Streamlit Cloud, remember to include and commit this file in Git.
Enjoy your enhanced transaction classification application!

## Spanish Version

# Aplicación de Clasificación de Transacciones con IA (Versión Mejorada)

## Resumen

Esta aplicación Streamlit permite a los usuarios cargar transacciones financieras desde un archivo CSV, clasificarlas automáticamente usando IA (Gemini Pro) basada en una lista de categorías y subcategorías almacenada permanentemente en una base de datos (`app_database.db`), corregir manualmente las clasificaciones y que la aplicación "aprenda" de estas correcciones para futuras transacciones. La API Key de Gemini se configura de forma segura a través de los "Secrets" de Streamlit Cloud. Los resultados pueden ser descargados.

## Estructura de Archivos del Proyecto

```
/
├── app.py                     # Script principal de la aplicación Streamlit
├── database_utils.py          # Utilidades para la gestión de la base de datos SQLite
├── llm_service.py             # Servicio para interactuar con la API de Gemini
├── classification_engine.py   # Lógica de clasificación (combina IA y aprendizaje)
├── requirements.txt           # Dependencias de Python
├── Categories.csv             # Archivo CSV de ejemplo para poblar la BD la primera vez (ver nota abajo)
├── app_database.db            # Base de datos SQLite (debe estar poblada y en el repo)
├── template_transacciones.csv # Plantilla CSV para que el usuario sepa el formato esperado
└── README.md                  # Este archivo
```

## Configuración y Ejecución Local

1.  **Prerrequisitos:**
    *   Python 3.9 o superior.
    *   `pip` para instalar paquetes.

2.  **Crear un Entorno Virtual (Recomendado):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # En Linux/macOS
    # venv\Scripts\activate    # En Windows
    ```

3.  **Instalar Dependencias:**
    Navega al directorio raíz del proyecto y ejecuta:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Preparar la Base de Datos de Categorías (`app_database.db`):**
    *   La aplicación ahora espera que `app_database.db` exista y contenga la tabla `lista_categorias` poblada.
    *   **Para la primera vez / o para actualizar masivamente las categorías:**
        1.  Asegúrate de tener un archivo `Categories.csv` con tus categorías (columnas: `Category`, `Subcategory`).
        2.  Puedes usar el script `database_utils.py` directamente para poblar la base de datos. Descomenta las líneas de prueba al final de `database_utils.py` y ejecútalo:
            ```python
            # En database_utils.py, al final, modifica y descomenta:
            # if __name__ == '__main__':
            #     create_tables()
            #     # Asegúrate que Categories.csv esté en el mismo directorio o proporciona la ruta correcta
            #     if load_categories_from_csv('Categories.csv'): 
            #         print("Base de datos poblada con categorías.")
            #     else:
            #         print("Error poblando la base de datos.")
            #     print(get_all_categories())
            ```
            Luego ejecuta: `python database_utils.py`
        3.  Esto creará/actualizará `app_database.db` con las categorías del CSV. **Asegúrate de que este `app_database.db` actualizado esté en tu directorio de proyecto.**

5.  **Configurar API Key de Google Gemini (para ejecución local):**
    *   La aplicación intentará leer la API Key desde los "Secrets" de Streamlit (si ejecutas en un entorno que los soporte, como Streamlit Cloud o localmente con un archivo `.streamlit/secrets.toml`).
    *   Para desarrollo local sin `secrets.toml`, puedes temporalmente establecer la variable de entorno `GOOGLE_API_KEY` o modificar `llm_service.py` para pasar la clave directamente (no recomendado para producción).
    *   Un archivo `secrets.toml` en un directorio `.streamlit` en la raíz de tu proyecto se vería así:
        ```toml
        GOOGLE_API_KEY = "TU_API_KEY_DE_GEMINI_AQUI"
        ```

6.  **Ejecutar la Aplicación:**
    ```bash
    streamlit run app.py
    ```
    La aplicación se abrirá en tu navegador web.

7.  **Uso Inicial (Local):**
    *   Asegúrate que `app_database.db` esté poblada y la API Key esté accesible (vía `secrets.toml` o variable de entorno).
    *   Descarga la plantilla de transacciones si es necesario.
    *   Sube tu archivo CSV de transacciones (con columna `ExpenseDesc`).
    *   La aplicación procesará las transacciones. Puedes editar las categorías.
    *   Descarga los resultados.

## Despliegue en Streamlit Community Cloud

1.  **Prepara tu Repositorio en GitHub:**
    *   Crea un nuevo repositorio público en GitHub.
    *   Sube todos los archivos del proyecto: `app.py`, `database_utils.py`, `llm_service.py`, `classification_engine.py`, `requirements.txt`, `template_transacciones.csv`, y **muy importante, el archivo `app_database.db` ya poblado con tus categorías.**
    *   `app_database.db`: Esta base de datos SQLite almacena tus categorías y las correcciones aprendidas. Para que las categorías y el aprendizaje persistan, **debes incluir `app_database.db` en tu repositorio Git y hacer commit/push de los cambios** cada vez que la base de datos se actualice (por ejemplo, si añades nuevas categorías localmente o si las correcciones aprendidas son significativas).

2.  **Conecta tu Repositorio a Streamlit Cloud:**
    *   Ve a [share.streamlit.io](https://share.streamlit.io/) y regístrate o inicia sesión.
    *   Haz clic en "New app".
    *   Selecciona "Deploy from GitHub".
    *   Elige tu repositorio, la rama (usualmente `main` o `master`) y el archivo principal (`app.py`).

3.  **Configura los Secrets (Variables de Entorno):**
    *   La aplicación **requiere** tu API Key de Google Gemini a través de los "Secrets" de Streamlit Cloud.
    *   En la configuración de tu app en Streamlit Cloud, ve a "Settings" -> "Secrets".
    *   Añade un nuevo secret con el siguiente formato:
        ```toml
        GOOGLE_API_KEY = "TU_API_KEY_DE_GEMINI_AQUI"
        ```
        Reemplaza `TU_API_KEY_DE_GEMINI_AQUI` con tu clave real.
    *   La aplicación `app.py` está diseñada para leer esta clave desde `st.secrets`.

4.  **Despliega:**
    *   Haz clic en "Deploy!". Streamlit Cloud instalará las dependencias y ejecutará tu aplicación.

## Uso de la Aplicación Desplegada

*   Accede a la URL pública de tu aplicación Streamlit Cloud.
*   La API Key se tomará de los Secrets. Las categorías se cargarán desde `app_database.db` en tu repositorio.
*   Sube tus transacciones.
*   Revisa, corrige y descarga.

## Notas Adicionales

*   **Gestión de Categorías:** Para añadir, eliminar o modificar masivamente categorías, deberás actualizar tu archivo `Categories.csv` localmente, repoblar `app_database.db` usando `database_utils.py` (como se describe en la configuración local), y luego hacer commit y push del `app_database.db` actualizado a tu repositorio de GitHub.
*   **Columna de Descripción:** La aplicación espera una columna `ExpenseDesc` en tu archivo de transacciones. Si es diferente, modifica `description_column` en `app.py`.
*   **Aprendizaje:** Las correcciones se guardan en `app_database.db`. Para que este aprendizaje persista en Streamlit Cloud, recuerda incluir y commitear este archivo en Git.

¡Disfruta de tu aplicación de clasificación de transacciones mejorada!

