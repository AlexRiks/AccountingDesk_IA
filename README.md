# Clasificador de Transacciones con IA 🤖

Esta aplicación utiliza inteligencia artificial para clasificar automáticamente transacciones financieras en categorías y clases apropiadas.

## 🌟 Características

- Clasificación automática de transacciones usando IA
- Soporte para archivos CSV y PDF
- Gestión de entidades y productos financieros
- Panel de configuración personalizable
- Interfaz intuitiva y amigable

## 🚀 Despliegue en Streamlit Cloud

### Prerrequisitos

- Cuenta de GitHub
- Cuenta en [Streamlit Cloud](https://share.streamlit.io)
- Clave API de OpenAI

### Pasos para el Despliegue

1. **Clonar el Repositorio**
   ```bash
   git clone <URL-del-repositorio>
   cd <nombre-del-repositorio>
   ```

2. **Configurar Variables de Entorno en Streamlit Cloud**
   - Ve a tu aplicación en Streamlit Cloud
   - En la sección de Settings > Secrets, añade las siguientes variables:
     ```
     DB_HOST = "tu-host-de-base-de-datos"
     DB_PORT = "5432"
     DB_NAME = "nombre-de-base-de-datos"
     DB_USER = "usuario-db"
     DB_PASSWORD = "contraseña-db"
     OPENAI_API_KEY = "tu-api-key-de-openai"
     ```

3. **Desplegar la Aplicación**
   - Conecta tu repositorio de GitHub en Streamlit Cloud
   - Selecciona la rama principal
   - Especifica `main.py` como archivo principal
   - ¡Listo! Tu aplicación estará disponible en una URL pública

## 🛠️ Desarrollo Local

1. **Configurar Entorno Virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

2. **Instalar Dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar Variables de Entorno**
   - Crea un archivo `.env` basado en `.env.example`
   - Añade tus credenciales y configuraciones

4. **Ejecutar la Aplicación**
   ```bash
   streamlit run main.py
   ```

## 📝 Variables de Entorno Requeridas

- `DB_HOST`: Host de la base de datos
- `DB_PORT`: Puerto de la base de datos
- `DB_NAME`: Nombre de la base de datos
- `DB_USER`: Usuario de la base de datos
- `DB_PASSWORD`: Contraseña de la base de datos
- `OPENAI_API_KEY`: Clave API de OpenAI

## 🔒 Seguridad

- Nunca comitees archivos `.env` o credenciales al repositorio
- Usa siempre variables de entorno para las credenciales
- Mantén tu API key de OpenAI segura

## 📚 Documentación Adicional

- [Documentación de Streamlit](https://docs.streamlit.io)
- [Streamlit Cloud](https://streamlit.io/cloud)
- [OpenAI API](https://platform.openai.com/docs/api-reference)

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request para sugerencias y mejoras.

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles. 