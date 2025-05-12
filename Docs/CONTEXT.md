# AI-Powered Transaction Classification App

## Overview
This application is a minimalistic, AI-powered financial tool built with **Streamlit**. It automates the classification of financial transactions into:

- **Expense Accounts** (using a hierarchy of categories and subcategories)
- **Classes** (based on Due To / Due From logic between multiple entities)

Users can upload transactions via **CSV** or **PDF** and the app will classify them using a trained AI model. It also allows managing entities, financial products, and tracing historical data for reconciliations and intercompany loans.

---

## 🧠 Core Features

### 1. **User Interface**
- Built in **Streamlit** with a **clean and minimalist layout**.
- Main panel shows uploaded transactions **automatically classified**.
- Sidebar or separate tab for managing **Entities** and **Products**.

### 2. **Transaction Input**
- **Upload support**:
  - CSV files (structured with date, description, amount, product)
  - PDFs (OCR extracted text)
- Once uploaded:
  - Transactions are parsed and displayed in a sortable/filterable table.
  - The classification is immediately applied using the AI engine.

### 3. **Classification Logic**

#### Expense Account
- Classification based on a **preloaded categories database**:
  - Categories
  - Subcategories
- AI classifies based on transaction description and history.

#### Class (Due To / Due From)
- Logic applied between entities using:
  - **Entity A paid for Entity B** → Class: "Entity A DF Entity B"
  - **Entity B owes Entity A** → Class: "Entity B DT Entity A"
- Only one entry (preferably DF) might be used depending on logic simplification.

---

## 🏢 Entity & Product Management

### Database Structure
A unified table structure is used to manage both accounts and cards across different entities:

- `Entity`
- `Bank / Fintech`
- `Name` (Name of the account or card)
- `AccountType` (e.g. Bank, Credit Card)
- `AccountSubType` (e.g. Checking, Savings, Visa, MasterCard)
- `Current Number` (Last 4 digits or identifier)

### Features
- **Register entities and products** directly from the interface or via code.
- Mark products **active/inactive** to track changes over time.
- Maintain **traceability** for changed cards/accounts.

---

## 🤖 AI Classification Engine

- Uses **semantic embeddings** and **similarity search** to classify:
  - Expense category
  - DT/DF class
- Learns from **user corrections**:
  - Editable predictions
  - Corrections are stored to improve future predictions

### AI Tools & Libraries (Recommended)
- `SentenceTransformers` / `OpenAI Embeddings`
- `FAISS` or `Qdrant` for semantic search
- Custom fine-tuned model if needed for domain-specific terms

---

## 🔁 Feedback Loop for Training
- When a user corrects a classification:
  - Save the corrected label with the transaction description.
  - Append to training data for fine-tuning or retraining the classifier.
  - Optionally store feedback history.

---

## 💾 Backend Requirements

- **Python**
- **Streamlit**
- **PostgreSQL** (or any SQL-compatible DB)
- **SQLAlchemy** for DB interaction
- **Pandas** for data wrangling
- **OCR** (e.g. Tesseract, AWS Textract) for PDF support
- **Supabase / Firebase** (for auth + backend-as-a-service if needed)

---

## 🛠️ Developer Setup

### Environment
```bash
python -m venv venv
source venv/bin/activate
pip install streamlit pandas sqlalchemy openai sentence-transformers faiss-cpu
```

### Folder Structure
```
/ai_transaction_app
├── main.py              # Streamlit app
├── db/                 # DB models and logic
├── ai/                 # Classification model logic
├── data/               # Sample data files and embeddings
├── utils/              # Helper functions
└── config.py           # Environment config
```

---

## 📈 Output & Reports
- Table of transactions with predicted:
  - Expense category
  - Class (DT/DF)
- Export options:
  - CSV
  - JSON
  - Summary per entity
- AI Confidence score (optional)

---

## 🔒 Optional Features
- User authentication (per user entities/products)
- Audit log of classification changes
- Entity-level summary dashboards

---

## ✅ Future Improvements
- Train a **multi-label transformer** model for better DT/DF classification.
- Integrate with accounting systems (e.g. QuickBooks, Wave, Xero).
- Real-time notification for unclassified or suspicious transactions.

---

## 🌐 Language
- **Entire interface in English**, including error messages, buttons, and labels.

---

## 📌 Summary
This app is a smart, adaptive financial assistant for categorizing and reconciling transactions across entities using modern AI techniques. It balances automation with human-in-the-loop feedback, making it an ideal internal tool for financial operations in multi-entity environments.

---

## 📊 Database Schema

### Tables Structure

#### 1. `entidades` (Entities)
```sql
CREATE TABLE entidades (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(500),
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. `productos` (Products)
```sql
CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    entidad_id INTEGER REFERENCES entidades(id),
    tipo VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    numero VARCHAR(20),
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. `categorias` (Categories)
```sql
CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(500),
    categoria_padre_id INTEGER REFERENCES categorias(id)
);
```

#### 4. `transacciones` (Transactions)
```sql
CREATE TABLE transacciones (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP NOT NULL,
    descripcion VARCHAR(500) NOT NULL,
    monto FLOAT NOT NULL,
    entidad_id INTEGER REFERENCES entidades(id),
    producto_id INTEGER REFERENCES productos(id),
    categoria_id INTEGER REFERENCES categorias(id),
    clase VARCHAR(100),
    confianza_ia FLOAT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Relationships
- `entidades` ← 1:N → `productos`
- `entidades` ← 1:N → `transacciones`
- `productos` ← 1:N → `transacciones`
- `categorias` ← 1:N → `categorias` (self-referential for hierarchy)
- `categorias` ← 1:N → `transacciones`

---

## 📁 Project Structure

```
accounting_desk/
├── main.py                 # Aplicación principal Streamlit
├── requirements.txt        # Dependencias del proyecto
├── README.md              # Documentación principal
├── .env                   # Variables de entorno (no en control de versiones)
├── .env.example           # Ejemplo de variables de entorno
│
├── ai/                    # Módulo de Inteligencia Artificial
│   ├── __init__.py
│   ├── classifier.py      # Clasificador de transacciones
│   └── models/           # Modelos pre-entrenados y checkpoints
│
├── db/                    # Módulo de Base de Datos
│   ├── __init__.py
│   ├── models.py         # Modelos SQLAlchemy
│   └── migrations/       # Migraciones de la base de datos
│
├── data/                  # Datos y recursos
│   ├── categories.json   # Categorías predefinidas
│   └── embeddings/       # Embeddings pre-calculados
│
├── utils/                 # Utilidades y helpers
│   ├── __init__.py
│   ├── pdf_processor.py  # Procesamiento de PDFs
│   └── csv_processor.py  # Procesamiento de CSVs
│
├── static/               # Archivos estáticos
│   ├── css/
│   └── js/
│
├── templates/            # Plantillas HTML (si se necesitan)
│
├── tests/                # Tests unitarios y de integración
│   ├── __init__.py
│   ├── test_classifier.py
│   └── test_models.py
│
└── Docs/                 # Documentación adicional
    ├── CONTEXT.md        # Contexto y estructura del proyecto
    ├── API.md           # Documentación de la API
    └── SETUP.md         # Instrucciones de instalación
```

### Key Directories Explanation

- `ai/`: Contains all AI-related code and models
- `db/`: Database models and migrations
- `data/`: Static data and resources
- `utils/`: Helper functions and utilities
- `static/`: Static files (CSS, JS, images)
- `templates/`: HTML templates if needed
- `tests/`: All test files
- `Docs/`: Project documentation

---

## 🔄 Data Flow

1. User uploads transaction file (CSV/PDF)
2. File is processed by respective processor (csv_processor.py/pdf_processor.py)
3. Transactions are extracted and normalized
4. AI classifier processes each transaction
5. Results are stored in database
6. User interface displays results and allows corrections
7. Corrections are fed back to AI model for continuous learning
