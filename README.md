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

